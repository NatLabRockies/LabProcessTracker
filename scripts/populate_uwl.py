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
import json
import os
import sys
import warnings
from pathlib import Path

# Allow running directly from scripts/ or via the installed package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from uwl_utils import (  # noqa: E402
    _make_time_and_place_item,
    _next_uwl_id,
    apply_populators,
    find_item_by_name,
    find_section,
    load_matching_records,
    locate_uwl,
    validate_sample_id_match,
)


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
            "file automatically using the sample ID. Expected filename format: "
            "<file_type>_<user_id>_<project_id>_<batch_id>_<sample_id>_"
            "<optional>.uwl"
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
        except (FileNotFoundError, ValueError) as exc:
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
