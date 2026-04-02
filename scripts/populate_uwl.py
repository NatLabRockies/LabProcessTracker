"""
populate_uwl.py - Populate UWL file fields from a process tracker scan log.

Given a sample ID, process name, and scan log path, finds the matching scan
record
and writes timestamp data (Date, Time) into the corresponding UWL section's
"Time & Place" Item, saving a copy of the UWL file.

UWL files are JSON with this structure:
    {
      "Objects": {
        "<id>": {
          "Type": "Section",
          "Name": "<section_name>",
          "Objects": {
            "<id>": {
              "Type": "Item",
              "Name": "Time & Place",
              "Parameters": ["Time", "Date", "Location"],
              "Values": ["", "", "SC212"]
            }
          }
        }
      }
    }

Usage examples:
    python populate_uwl.py --uwl path/to/2603_015.uwl --scan-log scan_log.csv \\
        --sample-id 2503-015 --process 1p68MHP_BC

    python populate_uwl.py --uwl-dir path/to/uwl_files/ --scan-log scan_log.csv \\
        --sample-id 2503-015 --process bcp_ag_evap --output-dir ./populated/

"""

import argparse
import csv
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

_TIMESTAMP_FORMATS = [
    "%m/%d/%Y %H:%M:%S",  # US with seconds:   3/6/2026 16:50:00
    "%Y-%m-%d %H:%M:%S",  # ISO with seconds:  2026-02-05 12:43:57
    "%Y-%m-%d %H:%M",     # ISO no seconds:    2026-02-05 12:43
    "%m/%d/%Y %H:%M",     # US short:          3/6/2026 16:50
    "%d/%m/%Y %H:%M:%S",  # EU with seconds:   6/3/2026 16:50:00
    "%d/%m/%Y %H:%M",     # EU short:          6/3/2026 16:50
]


def _parse_timestamp(ts_str: str) -> datetime:
    """Try multiple formats to parse a timestamp string."""
    for fmt in _TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(ts_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Cannot parse timestamp {ts_str!r}. "
        f"Tried formats: {_TIMESTAMP_FORMATS}"
    )


# ---------------------------------------------------------------------------
# FIELD POPULATORS
#
# Maps UWL parameter name -> resolver function:
#   f(record: dict, context: dict) -> str
#
# `record`  - a row dict from the CSV, with an extra "_parsed_ts" datetime key.
# `context` - dict with extra info (sample_id, process_name, etc.)
#
# To add a new field (e.g. Location, Researcher), add an entry here.
# ---------------------------------------------------------------------------

def _populate_time(record: dict, context: dict) -> str:
    return record["_parsed_ts"].strftime("%H:%M")


def _populate_date(record: dict, context: dict) -> str:
    ts = record["_parsed_ts"]
    return f"{ts.month}/{ts.day}/{ts.year}"


FIELD_POPULATORS = {
    "Time": _populate_time,
    "Date": _populate_date,
    # --- Uncomment / extend as needed ---
    # "Location": lambda record, ctx: ctx.get("process_location", ""),
    # "Worker ID": lambda record, ctx: ctx.get("operator_id", ""),
    # "Name": lambda record, ctx: ctx.get("operator_name", ""),
}


# ---------------------------------------------------------------------------
# Scan log loading
# ---------------------------------------------------------------------------

def load_matching_records(
    csv_path: Path, sample_id: str, process_name: str
) -> list:
    """Read scan log CSV and return rows matching sample_id and process_name.

    Adds a '_parsed_ts' key (datetime) to each returned row.
    Blank/empty rows are silently skipped.
    """
    matches = []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not any(v.strip() for v in row.values() if v):
                continue  # skip blank rows
            row_sample = row.get("SampleID", "").strip()
            row_process = row.get("ProcessName", "").strip()
            if row_sample == sample_id.strip() and row_process == process_name.strip():
                ts_str = row.get("Timestamp", "")
                row["_parsed_ts"] = _parse_timestamp(ts_str)
                matches.append(row)
    return matches


# ---------------------------------------------------------------------------
# UWL traversal helpers
# ---------------------------------------------------------------------------

def find_section(root_objects: dict, section_name: str) -> Optional[dict]:
    """Return the first Section whose Name matches section_name, or None."""
    for obj in root_objects.values():
        if obj.get("Type") == "Section" and obj.get("Name") == section_name:
            return obj
    return None


def find_item_by_name(section_objects: dict, item_name: str) -> Optional[dict]:
    """Return the first Item in section_objects with the given Name, or None."""
    for obj in section_objects.values():
        if obj.get("Type") == "Item" and obj.get("Name") == item_name:
            return obj
    return None


def _next_uwl_id(uwl_data: dict) -> str:
    """Return the next unused integer ID (as a string) across the whole UWL. Required
       to add new Items (eg Time & Date) without ID conflicts."""
    max_id = -1

    def _scan(objects: dict) -> None:
        nonlocal max_id
        for k, v in objects.items():
            try:
                max_id = max(max_id, int(k))
            except (ValueError, TypeError):
                pass
            if isinstance(v, dict) and "Objects" in v:
                _scan(v["Objects"])

    _scan(uwl_data.get("Objects", {}))
    return str(max_id + 1)


def _make_time_and_place_item(item_id: str) -> dict:
    """Return a blank 'Time & Place' Item node ready for insertion."""
    return {
        "ID": item_id,
        "Type": "Item",
        "Subtype": "Abstract",
        "Name": "Time & Place",
        "Notes": "",
        "Parameters": ["Time", "Date", "Location"],
        "Values": ["", "", ""],
        "position": [90, 90],
        "Link": False,
    }


def _normalize_sample_id(value: str) -> str:
    """Normalize sample IDs for tolerant comparison.

    Treat hyphen/underscore variants and case differences as equivalent.
    """
    return value.strip().replace("-", "_").lower()


def get_uwl_sample_id(uwl_data: dict) -> Optional[str]:
    """Extract Sample ID from root-level 'Sample' item, if present."""
    root_objects = uwl_data.get("Objects", {})
    for obj in root_objects.values():
        if obj.get("Type") != "Item" or obj.get("Name") != "Sample":
            continue
        params = obj.get("Parameters", [])
        values = obj.get("Values", [])
        if "Sample ID" not in params:
            return None
        sample_idx = params.index("Sample ID")
        if sample_idx >= len(values):
            return None
        sample_val = values[sample_idx]
        return sample_val.strip() if isinstance(sample_val, str) else str(sample_val)
    return None


def validate_sample_id_match(uwl_data: dict, requested_sample_id: str) -> None:
    """Raise ValueError if requested sample ID does not match UWL Sample ID."""
    uwl_sample_id = get_uwl_sample_id(uwl_data)
    if uwl_sample_id is None:
        warnings.warn(
            "Could not read 'Sample ID' from UWL 'Sample' item. "
            "Skipping sample ID consistency check.",
            stacklevel=1,
        )
        return

    if _normalize_sample_id(uwl_sample_id) != _normalize_sample_id(requested_sample_id):
        raise ValueError(
            "Sample ID mismatch: "
            f"requested '{requested_sample_id}' but UWL contains '{uwl_sample_id}'."
        )


def apply_populators(item: dict, record: dict, context: dict) -> None:
    """Mutate the item's Values list in-place using FIELD_POPULATORS.

    Parameters not in FIELD_POPULATORS are left unchanged.
    """
    params = item.get("Parameters", [])
    values = item.get("Values", [])

    # Ensure Values list is at least as long as Parameters
    while len(values) < len(params):
        values.append("")

    for i, param in enumerate(params):
        if param in FIELD_POPULATORS:
            values[i] = FIELD_POPULATORS[param](record, context)

    item["Values"] = values


# ---------------------------------------------------------------------------
# UWL file location helper
# ---------------------------------------------------------------------------

def locate_uwl(uwl_dir: Path, sample_id: str) -> Path:
    """Find a .uwl file in uwl_dir whose stem matches sample_id.

    Tries direct match, hyphen-to-underscore normalization, and
    case-insensitive fallback.
    """
    normalized = sample_id.replace("-", "_")

    for candidate in [uwl_dir / f"{sample_id}.uwl", uwl_dir / f"{normalized}.uwl"]:
        if candidate.exists():
            return candidate

    # Case-insensitive scan
    for path in uwl_dir.glob("*.uwl"):
        if path.stem.replace("-", "_").lower() == normalized.lower():
            return path

    raise FileNotFoundError(
        f"No .uwl file found for sample '{sample_id}' in: {uwl_dir}\n"
        f"Tried stems '{sample_id}' and '{normalized}' (case-insensitive)."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Populate UWL file Time & Place fields from a process tracker scan log. "
            "Writes a copy {stem}_populated.uwl; the original is never modified."
        )
    )

    uwl_group = parser.add_mutually_exclusive_group(required=True)
    uwl_group.add_argument(
        "--uwl", type=Path, metavar="PATH",
        help="Path to the input .uwl file.",
    )
    uwl_group.add_argument(
        "--uwl-dir", type=Path, metavar="DIR",
        help=(
            "Directory containing .uwl files. The script locates the correct "
            "file automatically using the sample ID "
            "(supports hyphen/underscore name variants)."
        ),
    )

    parser.add_argument(
        "--scan-log", "--csv", type=Path, required=True, metavar="PATH",
        dest="scan_log",
        help="Path to the process tracker scan log file.",
    )
    parser.add_argument(
        "--sample-id", required=True, metavar="ID",
        help="Sample ID as it appears in the scan log (e.g. '2503-015').",
    )
    parser.add_argument(
        "--process", required=True, metavar="NAME",
        help="Process name as it appears in the scan log (e.g. 'bcp_ag_evap').",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None, metavar="DIR",
        help=(
            "Directory to write the output .uwl file. "
            "Defaults to the input file's directory."
        ),
    )
    parser.add_argument(
        "--skip-sample-id-check",
        action="store_true",
        help=(
            "Skip validating that --sample-id matches the UWL file's embedded "
            "Sample ID value."
        ),
    )

    args = parser.parse_args()

    # --- Validate inputs ---
    if not args.scan_log.exists():
        sys.exit(f"Error: Scan log not found: {args.scan_log}")

    # --- Resolve UWL path ---
    if args.uwl:
        uwl_path = args.uwl
        if not uwl_path.exists():
            sys.exit(f"Error: UWL file not found: {uwl_path}")
    else:
        if not args.uwl_dir.is_dir():
            sys.exit(f"Error: --uwl-dir is not a directory: {args.uwl_dir}")
        try:
            uwl_path = locate_uwl(args.uwl_dir, args.sample_id)
        except FileNotFoundError as exc:
            sys.exit(f"Error: {exc}")

    print(f"UWL file:  {uwl_path}")

    # --- Load and filter scan log ---
    records = load_matching_records(args.scan_log, args.sample_id, args.process)

    if not records:
        sys.exit(
            f"Error: No scan log records found for "
            f"sample='{args.sample_id}', process='{args.process}' in {args.scan_log}"
        )
    if len(records) > 1:
        records.sort(key=lambda r: r["_parsed_ts"])
        warnings.warn(
            f"Found {len(records)} records for sample='{args.sample_id}' / "
            f"process='{args.process}'. "
            f"Using the earliest timestamp: {records[0]['Timestamp']}.",
            stacklevel=1,
        )

    record = records[0]
    print(
        f"Scan log record: {record.get('Timestamp')} | "
        f"sample={record.get('SampleID')} | process={record.get('ProcessName')}"
    )

    # --- Load UWL ---
    with uwl_path.open(encoding="utf-8") as f:
        uwl_data = json.load(f)

    # --- Validate requested sample ID vs UWL embedded sample ID ---
    if not args.skip_sample_id_check:
        try:
            validate_sample_id_match(uwl_data, args.sample_id)
        except ValueError as exc:
            sys.exit(f"Error: {exc}")

    # --- Resolve target section names ---
    section_names = [args.process]

    # Build context dict (extensible for future FIELD_POPULATORS)
    context = {
        "sample_id": args.sample_id,
        "process_name": args.process,
    }

    modified = []
    not_found = []

    for section_name in section_names:
        section = find_section(uwl_data["Objects"], section_name)
        if section is None:
            not_found.append(section_name)
            continue

        section.setdefault("Objects", {})
        tp_item = find_item_by_name(section["Objects"], "Time & Place")
        if tp_item is None:
            new_id = _next_uwl_id(uwl_data)
            tp_item = _make_time_and_place_item(new_id)
            section["Objects"][new_id] = tp_item
            print(f"  Created 'Time & Place' in section '{section_name}'")

        apply_populators(tp_item, record, context)
        modified.append(section_name)
        print(f"  Updated 'Time & Place' in section '{section_name}'")

    if not_found:
        warnings.warn(
            f"Section(s) not in UWL: {not_found}. "
            "Check that the process name matches a section name in the UWL file.",
            stacklevel=1,
        )

    if not modified:
        sys.exit(
            "Error: No sections were modified. Nothing written. "
            "Check that --process name matches a section in the UWL file."
        )

    # --- Write output ---
    output_dir = args.output_dir or uwl_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uwl_path.stem}_populated.uwl"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(uwl_data, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Output: {output_path}")


if __name__ == "__main__":
    main()
