"""
uwl_utils.py - Reusable utilities for reading and populating UWL files.
"""

import csv
import re
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional


_TIMESTAMP_FORMATS = [
    "%m/%d/%Y %H:%M:%S",  # US with seconds:   3/6/2026 16:50:00
    "%Y-%m-%d %H:%M:%S",  # ISO with seconds:  2026-02-05 12:43:57
    "%Y-%m-%d %H:%M",     # ISO no seconds:    2026-02-05 12:43
    "%m/%d/%Y %H:%M",     # US short:          3/6/2026 16:50
    "%d/%m/%Y %H:%M:%S",  # EU with seconds:   6/3/2026 16:50:00
    "%d/%m/%Y %H:%M",     # EU short:          6/3/2026 16:50
]

# UWL filename format pattern: 5 required segments + optional suffix
# Format: <file_type>_<user_id>_<project_id>_<batch_id>_<sample_id>_<optional>
_UWL_FILENAME_PATTERN = re.compile(
    r"^(?P<file_type>[^_]+)_(?P<user_id>[^_]+)_(?P<project_id>[^_]+)_"
    r"(?P<batch_id>[^_]+)_(?P<sample_id>[^_]+)(?:_(?P<additional>.+))?$"
)


def _extract_sample_id_from_filename_stem(stem: str) -> Optional[str]:
    """Parse UWL filename stem and extract sample_id from 5th position.

    Returns the sample_id string if filename matches the required format,
    or None if the filename is malformed.
    """
    match = _UWL_FILENAME_PATTERN.match(stem)
    if match:
        return match.group("sample_id")
    return None


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


def _populate_time(record: dict, context: dict) -> str:
    return record["_parsed_ts"].strftime("%H:%M")


def _populate_date(record: dict, context: dict) -> str:
    ts = record["_parsed_ts"]
    return f"{ts.month}/{ts.day}/{ts.year}"


FIELD_POPULATORS = {
    "Time": _populate_time,
    "Date": _populate_date,
}


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


# UWL file location helper
def locate_uwl(uwl_dir: Path, sample_id: str) -> Path:
    """Find a .uwl file in uwl_dir whose filename contains the requested sample_id.

    Enforces strict format: <file_type>_<user_id>_<project_id>_<batch_id>_
    <sample_id>_<optional>.uwl where sample_id is extracted from the 5th
    filename segment.

    Raises:
        ValueError: If any .uwl file in the directory has a malformed filename.
        FileNotFoundError: If no matching .uwl file is found.
    """
    # Scan all .uwl files in the directory
    uwl_files = list(uwl_dir.glob("*.uwl"))

    if not uwl_files:
        raise FileNotFoundError(
            f"No .uwl files found in: {uwl_dir}\n"
            f"Expected format: <file_type>_<user_id>_<project_id>_"
            f"<batch_id>_<sample_id>_<optional>.uwl"
        )

    # Validate all filenames and extract sample IDs
    malformed_example = None
    matches = []

    for uwl_file in uwl_files:
        stem = uwl_file.stem
        extracted_id = _extract_sample_id_from_filename_stem(stem)

        if extracted_id is None:
            if malformed_example is None:
                malformed_example = stem
        elif extracted_id == sample_id:
            matches.append(uwl_file)

    # If we found malformed filenames, raise ValueError with first example
    if malformed_example is not None:
        raise ValueError(
            f"Malformed UWL filename in {uwl_dir}: '{malformed_example}.uwl'\n"
            f"Expected format: <file_type>_<user_id>_<project_id>_"
            f"<batch_id>_<sample_id>_<optional>.uwl"
        )

    # Return the match if exactly one found
    if len(matches) == 1:
        return matches[0]

    if len(matches) == 0:
        raise FileNotFoundError(
            f"No .uwl file found for sample '{sample_id}' in: {uwl_dir}\n"
            f"Expected format: <file_type>_<user_id>_<project_id>_"
            f"<batch_id>_<sample_id>_<optional>.uwl"
        )

    # Multiple matches (ambiguous)
    raise FileNotFoundError(
        f"Multiple .uwl files found for sample '{sample_id}' in: {uwl_dir}\n"
        f"Matched: {[f.name for f in matches]}"
    )
