"""Tests for populate_uwl.py script."""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path

import pytest

# Add scripts and src directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from uwl_utils import (  # noqa: E402
    _parse_timestamp,
    _next_uwl_id,
    _make_time_and_place_item,
    load_matching_records,
    locate_uwl,
    find_section,
    find_item_by_name,
    get_uwl_sample_id,
    validate_sample_id_match,
    apply_populators,
    FIELD_POPULATORS,
)
from populate_uwl import main  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
FIXTURE_UWL = DATA_DIR / "test_sample.uwl"
FIXTURE_CSV = DATA_DIR / "test_scan_log.csv"


def _read_time_and_place(uwl_path: Path, section_name: str) -> dict:
    """Return the Time & Place parameter-value dict for a given section."""
    data = json.loads(uwl_path.read_text(encoding="utf-8"))
    for obj in data["Objects"].values():
        if obj.get("Type") == "Section" and obj.get("Name") == section_name:
            for item in obj.get("Objects", {}).values():
                if item.get("Name") == "Time & Place":
                    return dict(zip(item["Parameters"], item["Values"]))
    raise KeyError(
        f"Section '{section_name}' or 'Time & Place' missing from {uwl_path}"
    )


def _read_action_values(uwl_path: Path, section_name: str, action_name: str) -> list:
    """Return Action.Values for a named action inside a section."""
    data = json.loads(uwl_path.read_text(encoding="utf-8"))
    for obj in data["Objects"].values():
        if obj.get("Type") == "Section" and obj.get("Name") == section_name:
            for item in obj.get("Objects", {}).values():
                if item.get("Type") == "Action" and item.get("Name") == action_name:
                    return item.get("Values", [])
    raise KeyError(
        f"Action '{action_name}' missing in section '{section_name}' ({uwl_path})"
    )


class TestTimestampParsing:
    """Tests for _parse_timestamp()."""

    def test_iso_format_with_seconds(self):
        ts = _parse_timestamp("2026-03-06 16:50:00")
        assert ts == datetime(2026, 3, 6, 16, 50, 0)

    def test_iso_format_without_seconds(self):
        ts = _parse_timestamp("2026-03-06 16:50")
        assert ts == datetime(2026, 3, 6, 16, 50)

    def test_us_format_short(self):
        ts = _parse_timestamp("3/6/2026 16:50")
        assert ts == datetime(2026, 3, 6, 16, 50)

    def test_us_format_with_seconds(self):
        ts = _parse_timestamp("3/6/2026 16:50:00")
        assert ts == datetime(2026, 3, 6, 16, 50, 0)

    def test_strips_whitespace(self):
        ts = _parse_timestamp("  2026-03-06 09:00:00  ")
        assert ts == datetime(2026, 3, 6, 9, 0, 0)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Cannot parse timestamp"):
            _parse_timestamp("not-a-date")


class TestLocateUWL:
    """Tests for locate_uwl()."""

    def test_finds_valid_formatted_filename(self, tmp_path):
        """Should locate a file with valid 5-segment tokenized format."""
        uwl_file = tmp_path / "UWL_uid_pid_bid_exact-match.uwl"
        uwl_file.write_text("{}", encoding="utf-8")
        result = locate_uwl(tmp_path, "exact-match")
        assert result == uwl_file

    def test_raises_on_malformed_filename(self, tmp_path):
        """Should raise ValueError when .uwl file has malformed filename.

        Filename must have exactly 5+ segments (not 5+ segments).
        """
        (tmp_path / "malformed.uwl").write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match="Malformed UWL filename"):
            locate_uwl(tmp_path, "test_sample")

    def test_raises_when_not_found(self, tmp_path):
        """Should raise FileNotFoundError when no file matches sample_id."""
        uwl_file = tmp_path / "UWL_uid_pid_bid_other-sample.uwl"
        uwl_file.write_text("{}", encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="nonexistent-sample"):
            locate_uwl(tmp_path, "nonexistent-sample")

    def test_raises_includes_dir_in_message(self, tmp_path):
        """Error message should include the directory path."""
        uwl_file = tmp_path / "UWL_uid_pid_bid_other-sample.uwl"
        uwl_file.write_text("{}", encoding="utf-8")
        with pytest.raises(FileNotFoundError, match=re.escape(str(tmp_path))):
            locate_uwl(tmp_path, "missing")


class TestFindSection:
    """Tests for find_section()."""

    def _make_objects(self):
        return {
            "0": {"Type": "Item", "Name": "Sample", "Parameters": [], "Values": []},
            "1": {"Type": "Section", "ID": "1", "Name": "TargetSection", "Objects": {}},
            "2": {"Type": "Section", "ID": "2", "Name": "OtherSection", "Objects": {}},
        }

    def test_finds_section_by_name(self):
        result = find_section(self._make_objects(), "TargetSection")
        assert result is not None
        assert result["Name"] == "TargetSection"

    def test_returns_none_for_missing_section(self):
        result = find_section(self._make_objects(), "MissingSection")
        assert result is None

    def test_does_not_return_non_section_type(self):
        # "Sample" is an Item, not a Section
        result = find_section(self._make_objects(), "Sample")
        assert result is None


class TestFindItemByName:
    """Tests for find_item_by_name()."""

    def _make_objects(self):
        return {
            "2": {
                "Type": "Item",
                "Name": "Time & Place",
                "Parameters": ["Time", "Date", "Location"],
                "Values": ["", "", "LAB"],
            },
            "3": {
                "Type": "Item",
                "Name": "Researcher",
                "Parameters": ["Worker ID"],
                "Values": [""],
            },
        }

    def test_finds_item_by_name(self):
        result = find_item_by_name(self._make_objects(), "Time & Place")
        assert result is not None
        assert result["Name"] == "Time & Place"

    def test_returns_none_for_missing_item(self):
        result = find_item_by_name(self._make_objects(), "Nonexistent")
        assert result is None

    def test_returns_none_on_empty_objects(self):
        result = find_item_by_name({}, "Time & Place")
        assert result is None


class TestApplyPopulators:
    """Tests for apply_populators()."""

    def _make_record(self, year=2026, month=3, day=6, hour=16, minute=50):
        return {"_parsed_ts": datetime(year, month, day, hour, minute)}

    def _make_item(self, values=None):
        return {
            "Type": "Item",
            "Name": "Time & Place",
            "Parameters": ["Time", "Date", "Location"],
            "Values": values if values is not None else ["", "", "TESTLAB"],
        }

    def test_populates_time(self):
        item = self._make_item()
        apply_populators(item, self._make_record(), {})
        assert item["Values"][0] == "16:50"

    def test_populates_date(self):
        item = self._make_item()
        apply_populators(item, self._make_record(), {})
        assert item["Values"][1] == "3/6/2026"

    def test_leaves_location_unchanged(self):
        item = self._make_item(["", "", "MYLAB"])
        apply_populators(item, self._make_record(), {})
        assert item["Values"][2] == "MYLAB"

    def test_pads_short_values_list(self):
        """Values shorter than Parameters must be extended before populating."""
        item = {
            "Parameters": ["Time", "Date", "Location"],
            "Values": [],
        }
        apply_populators(item, self._make_record(), {})
        assert item["Values"][0] == "16:50"
        assert item["Values"][1] == "3/6/2026"
        assert len(item["Values"]) == 3

    def test_single_digit_month_and_day_no_leading_zeros(self):
        item = self._make_item()
        apply_populators(item, self._make_record(month=3, day=6), {})
        assert item["Values"][1] == "3/6/2026"

    def test_zero_minute_formats_correctly(self):
        item = self._make_item()
        apply_populators(item, self._make_record(hour=9, minute=0), {})
        assert item["Values"][0] == "09:00"


class TestSampleIdValidation:
    """Tests for embedded Sample ID extraction and validation."""

    def test_get_uwl_sample_id(self):
        data = json.loads(FIXTURE_UWL.read_text(encoding="utf-8"))
        assert get_uwl_sample_id(data) == "test_sample"

    def test_validate_sample_id_match_accepts_hyphen_underscore(self):
        data = json.loads(FIXTURE_UWL.read_text(encoding="utf-8"))
        validate_sample_id_match(data, "test-sample")

    def test_validate_sample_id_match_raises_on_mismatch(self):
        data = json.loads(FIXTURE_UWL.read_text(encoding="utf-8"))
        with pytest.raises(ValueError, match="Sample ID mismatch"):
            validate_sample_id_match(data, "wrong-sample")


class TestCSVLoading:
    """Tests for load_matching_records()."""

    def test_returns_matching_row(self):
        records = load_matching_records(FIXTURE_CSV, "test-sample", "TestProcess")
        assert len(records) == 1
        assert records[0]["SampleID"] == "test-sample"
        assert records[0]["ProcessName"] == "TestProcess"

    def test_returns_empty_for_no_match(self):
        records = load_matching_records(FIXTURE_CSV, "nonexistent", "TestProcess")
        assert records == []

    def test_parses_iso_timestamp(self):
        records = load_matching_records(FIXTURE_CSV, "test-sample", "TestProcess")
        assert records[0]["_parsed_ts"] == datetime(2026, 3, 6, 16, 50, 0)

    def test_parses_us_timestamp(self):
        records = load_matching_records(FIXTURE_CSV, "test-sample", "Beta_Process")
        assert len(records) == 1
        assert records[0]["_parsed_ts"] == datetime(2026, 3, 6, 17, 0)

    def test_skips_blank_rows(self):
        """Blank rows must not appear as matches for empty strings."""
        records = load_matching_records(FIXTURE_CSV, "", "")
        assert records == []

    def test_returns_multiple_matches(self):
        """dup-sample has two rows with TestProcess."""
        records = load_matching_records(FIXTURE_CSV, "dup-sample", "TestProcess")
        assert len(records) == 2

    def test_filters_by_both_sample_and_process(self):
        """other-sample has a TestProcess row but must not appear for test-sample."""
        records = load_matching_records(FIXTURE_CSV, "test-sample", "TestProcess")
        for r in records:
            assert r["SampleID"] == "test-sample"

    def test_parsed_ts_key_added(self):
        records = load_matching_records(FIXTURE_CSV, "test-sample", "TestProcess")
        assert "_parsed_ts" in records[0]
        assert isinstance(records[0]["_parsed_ts"], datetime)


class TestNextUwlId:
    """Tests for _next_uwl_id() and _make_time_and_place_item()."""

    def test_returns_string_int(self):
        data = {"Objects": {"0": {}, "1": {}, "2": {}}}
        assert _next_uwl_id(data) == "3"

    def test_scans_nested_objects(self):
        data = {
            "Objects": {
                "0": {
                    "Objects": {"5": {}}
                }
            }
        }
        assert _next_uwl_id(data) == "6"

    def test_empty_uwl_starts_at_zero(self):
        assert _next_uwl_id({"Objects": {}}) == "0"

    def test_make_item_structure(self):
        item = _make_time_and_place_item("99")
        assert item["ID"] == "99"
        assert item["Type"] == "Item"
        assert item["Name"] == "Time & Place"
        assert item["Parameters"] == ["Time", "Date", "Location"]
        assert item["Values"] == ["", "", ""]


class TestFieldPopulatorsDict:
    """Smoke tests for the FIELD_POPULATORS module-level dict."""

    def test_time_key_present(self):
        assert "Time" in FIELD_POPULATORS

    def test_date_key_present(self):
        assert "Date" in FIELD_POPULATORS

    def test_time_is_callable(self):
        assert callable(FIELD_POPULATORS["Time"])

    def test_date_is_callable(self):
        assert callable(FIELD_POPULATORS["Date"])


class TestIntegration:
    """End-to-end tests calling main() via monkeypatched sys.argv."""

    def test_single_section_populated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        output = tmp_path / "test_sample_populated.uwl"
        assert output.exists()
        tp = _read_time_and_place(output, "TestProcess")
        assert tp["Time"] == "16:50"
        assert tp["Date"] == "3/6/2026"

    def test_unrelated_sections_unchanged(self, tmp_path, monkeypatch):
        """Sections not targeted should have their Time & Place left empty."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        output = tmp_path / "test_sample_populated.uwl"
        tp = _read_time_and_place(output, "Beta_Process")
        assert tp["Time"] == ""
        assert tp["Date"] == ""

    def test_zero_match_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "nonexistent-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        with pytest.raises(SystemExit):
            main()

    def test_multi_match_warns_and_uses_earliest(self, tmp_path, monkeypatch):
        """Multiple CSV rows: warn and use the earliest timestamp."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "dup-sample",
            "--process", "TestProcess",
            "--skip-sample-id-check",
            "--output-dir", str(tmp_path),
        ])
        with pytest.warns(UserWarning, match="2 records"):
            main()
        output = tmp_path / "test_sample_populated.uwl"
        tp = _read_time_and_place(output, "TestProcess")
        assert tp["Time"] == "09:00"  # earlier of 09:00 and 10:00

    def test_original_file_unchanged(self, tmp_path, monkeypatch):
        """Running the script must never modify the source UWL file."""
        original_text = FIXTURE_UWL.read_text(encoding="utf-8")
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        assert FIXTURE_UWL.read_text(encoding="utf-8") == original_text

    def test_output_is_populated_copy(self, tmp_path, monkeypatch):
        """Output filename must be {stem}_populated.uwl."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        assert (tmp_path / "test_sample_populated.uwl").exists()
        assert not (tmp_path / "test_sample.uwl").exists()

    def test_uwl_dir_autolocate(self, tmp_path, monkeypatch):
        """--uwl-dir should find .uwl file using 5-segment tokenized format."""
        uwl_dir = tmp_path / "uwl"
        uwl_dir.mkdir()
        uwl_filename = "UWL_repps_demos1_taskmeeting031825_test-sample.uwl"
        (uwl_dir / uwl_filename).write_text(
            FIXTURE_UWL.read_text(encoding="utf-8"), encoding="utf-8"
        )
        out = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl-dir", str(uwl_dir),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(out),
        ])
        main()
        output_filename = "UWL_repps_demos1_taskmeeting031825_test-sample_populated.uwl"
        assert (out / output_filename).exists()

    def test_missing_section_warns_and_exits(self, tmp_path, monkeypatch):
        """A process name with no matching UWL section warns and exits."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "unknown_process",  # in CSV, no matching section in UWL
            "--output-dir", str(tmp_path),
        ])
        with pytest.warns(UserWarning, match="not in UWL"):
            with pytest.raises(SystemExit):
                main()

    def test_output_is_valid_json(self, tmp_path, monkeypatch):
        """Output file must be valid JSON that can be reloaded."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        output = tmp_path / "test_sample_populated.uwl"
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["Format"] == "uwl"
        assert "Objects" in data

    def test_sample_id_mismatch_exits_by_default(self, tmp_path, monkeypatch):
        """Default behavior should fail if --sample-id mismatches UWL Sample ID."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "other-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        with pytest.raises(SystemExit, match="Sample ID mismatch"):
            main()

    def test_skip_sample_id_check_allows_mismatch(self, tmp_path, monkeypatch):
        """--skip-sample-id-check should permit processing with mismatched IDs."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "other-sample",
            "--process", "TestProcess",
            "--skip-sample-id-check",
            "--output-dir", str(tmp_path),
        ])
        main()
        assert (tmp_path / "test_sample_populated.uwl").exists()

    def test_non_abstract_action_node_unchanged(self, tmp_path, monkeypatch):
        """Action nodes should remain unchanged after Time & Place updates."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "TestProcess",
            "--output-dir", str(tmp_path),
        ])
        main()
        output = tmp_path / "test_sample_populated.uwl"
        assert _read_action_values(output, "TestProcess", "Spin") == ["3000", "30"]

    def test_auto_creates_time_and_place_when_missing(self, tmp_path, monkeypatch):
        """If a section has no 'Time & Place' item, the script creates it."""
        monkeypatch.setattr(sys, "argv", [
            "populate_uwl",
            "--uwl", str(FIXTURE_UWL),
            "--csv", str(FIXTURE_CSV),
            "--sample-id", "test-sample",
            "--process", "NoTimePlace_Section",
            "--skip-sample-id-check",
            "--output-dir", str(tmp_path),
        ])
        main()
        output = tmp_path / "test_sample_populated.uwl"
        assert output.exists()
        tp = _read_time_and_place(output, "NoTimePlace_Section")
        assert tp["Time"] == "16:50"
        assert tp["Date"] == "3/6/2026"
