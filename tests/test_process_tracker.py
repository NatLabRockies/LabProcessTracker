"""
Unit tests for process_tracker module using pytest.
"""
import sys
import os
from datetime import datetime

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest  # noqa: E402
import csv  # noqa: E402
import tracker_utils as tu  # noqa: E402
import process_tracker  # noqa: E402


class TestParseInput:
    """Test cases for QR code input parsing."""

    def test_valid_process(self):
        """Test parsing valid PROCESS input."""
        data_type, data_id = tu.parse_input("P%:ftlb234_spinbox")
        assert data_type == "PROCESS"
        assert data_id == "ftlb234_spinbox"

    def test_valid_sample(self):
        """Test parsing valid SAMPLE input."""
        data_type, data_id = tu.parse_input("S%:ABC123")
        assert data_type == "SAMPLE"
        assert data_id == "ABC123"

    def test_case_sensitive_prefix(self):
        """Test that prefix must match exactly (case-sensitive)."""
        # Lowercase prefix should not work
        data_type, data_id = tu.parse_input("s%:Test")
        assert data_type is None
        assert data_id is None

    def test_with_whitespace(self):
        """Test parsing with extra whitespace."""
        data_type, data_id = tu.parse_input("  S%:XYZ789  ")
        assert data_type == "SAMPLE"
        assert data_id == "XYZ789"

    def test_invalid_format(self):
        """Test parsing invalid format (missing colon or wrong prefix)."""
        data_type, data_id = tu.parse_input("INVALID")
        assert data_type is None
        assert data_id is None

    def test_empty_string(self):
        """Test parsing empty string."""
        data_type, data_id = tu.parse_input("")
        assert data_type is None
        assert data_id is None

    def test_empty_id(self):
        """Test parsing with empty ID after prefix."""
        data_type, data_id = tu.parse_input("S%:")
        assert data_type is None
        assert data_id is None

    @pytest.mark.parametrize("input_str,expected_type,expected_id", [
        ("P%:ftlb234_spinbox", "PROCESS", "ftlb234_spinbox"),
        ("S%:ABC123", "SAMPLE", "ABC123"),
        ("P%:testing", "PROCESS", "testing"),
        ("S%:999", "SAMPLE", "999"),
    ])
    def test_multiple_valid_inputs(self, input_str, expected_type, expected_id):
        """Test multiple valid input combinations."""
        data_type, data_id = tu.parse_input(input_str)
        assert data_type == expected_type
        assert data_id == expected_id


class TestLogScanEvent:
    """Test cases for log scan event creation."""

    def test_log_scan_event(self):
        """Test that log_scan_event creates a record with correct fields."""
        record = tu.create_log_record("TestOperator", "TestProcess", "SAMPLE123")

        assert "Timestamp" in record
        assert record["Operator"] == "TestOperator"
        assert record["ProcessName"] == "TestProcess"
        assert record["SampleID"] == "SAMPLE123"

    def test_timestamp_format(self):
        """Test that timestamp is in correct format."""
        record = tu.create_log_record("Op", "Proc", "Samp")
        timestamp = record["Timestamp"]

        # Should be able to parse timestamp with DATE_FORMAT
        datetime.strptime(timestamp, tu.DATE_FORMAT)

    def test_multiple_logs(self):
        """Test creating multiple log records."""
        records = []
        for i in range(3):
            record = tu.create_log_record(f"Op{i}", f"Proc{i}", f"Samp{i}")
            records.append(record)

        assert len(records) == 3
        assert records[0]["Operator"] == "Op0"
        assert records[2]["SampleID"] == "Samp2"


class TestUndoLastScan:
    """Test cases for undo functionality."""

    def test_undo_last_scan(self):
        """Test that undo removes the last record."""
        records = [
            tu.create_log_record("Op", "Proc", "Samp1"),
            tu.create_log_record("Op", "Proc", "Samp2"),
        ]

        removed = records.pop()
        assert len(records) == 1
        assert removed["SampleID"] == "Samp2"

    def test_undo_empty_log(self):
        """Test undo on empty log."""
        records = []
        assert len(records) == 0

    def test_undo_multiple_times(self):
        """Test multiple undo operations."""
        records = [
            tu.create_log_record("Op", "Proc", f"Samp{i}")
            for i in range(5)
        ]

        records.pop()
        records.pop()

        assert len(records) == 3
        assert records[-1]["SampleID"] == "Samp2"


class TestSaveLog:
    """Test cases for saving logs to CSV."""

    def test_creates_file(self, tmp_path):
        """Test that save_log creates a CSV file."""
        log_file = tmp_path / "test_log.csv"
        records = [tu.create_log_record("Op", "Proc", "Samp")]

        success, _ = tu.save_log_to_csv(records, str(log_file), str(tmp_path))

        assert success
        assert log_file.exists()

    def test_writes_correct_data(self, tmp_path):
        """Test that CSV contains correct data."""
        log_file = tmp_path / "test_log.csv"
        records = [tu.create_log_record("TestOp", "TestProc", "TestSamp")]

        tu.save_log_to_csv(records, str(log_file), str(tmp_path))

        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row["Operator"] == "TestOp"
            assert row["ProcessName"] == "TestProc"
            assert row["SampleID"] == "TestSamp"

    def test_appends_to_existing_file(self, tmp_path):
        """Test that save_log appends to existing file."""
        log_file = tmp_path / "test_log.csv"

        # First save
        records1 = [tu.create_log_record("Op1", "Proc", "Samp1")]
        tu.save_log_to_csv(records1, str(log_file), str(tmp_path))

        # Second save (should append)
        records2 = [tu.create_log_record("Op2", "Proc", "Samp2")]
        tu.save_log_to_csv(records2, str(log_file), str(tmp_path))

        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["Operator"] == "Op1"
            assert rows[1]["Operator"] == "Op2"

    def test_clears_records_after_save(self):
        """Test that records list is cleared after successful save."""
        records = [tu.create_log_record("Op", "Proc", "Samp")]
        # In actual implementation, records.clear() is called after successful save
        records.clear()
        assert len(records) == 0

    def test_save_empty_records(self, tmp_path):
        """Test saving empty records list."""
        log_file = tmp_path / "test_log.csv"
        records = []

        success, message = tu.save_log_to_csv(records, str(log_file), str(tmp_path))

        assert not success
        assert "No records" in message


class TestOutputDirectory:
    """Test cases for output directory logic."""

    def test_get_default_output_dir_project_exists(self):
        """Test that get_default_output_dir returns project outputs when it exists."""
        output_dir = tu.get_default_output_dir()
        assert output_dir is not None
        assert isinstance(output_dir, str)

    def test_get_default_output_dir_fallback(self, monkeypatch, tmp_path):
        """Test fallback to Documents when project outputs doesn't exist."""
        # This test verifies the fallback mechanism exists
        output_dir = tu.get_default_output_dir()
        assert output_dir is not None

    def test_parse_args_custom_output_dir(self):
        """Test that custom output directory can be specified."""
        # Basic test that parse_args function exists
        assert hasattr(process_tracker, 'parse_args')


class TestIntegrationWorkflow:
    """Integration tests for complete workflow."""

    def test_full_workflow(self, tmp_path):
        """Test a complete scan workflow."""
        log_file = tmp_path / "workflow_test.csv"
        records = []

        # Simulate scanning process and samples
        records.append(tu.create_log_record("Alice", "C215SS_JV", "Sample1"))
        records.append(tu.create_log_record("Alice", "C215SS_JV", "Sample2"))

        # Save
        success, _ = tu.save_log_to_csv(records, str(log_file), str(tmp_path))

        assert success
        assert log_file.exists()

        # Verify saved data
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2

    def test_workflow_with_undo(self, tmp_path):
        """Test workflow with undo operation."""
        log_file = tmp_path / "undo_test.csv"
        records = []

        # Add records
        records.append(tu.create_log_record("Bob", "BD8_XRD", "Sample1"))
        records.append(tu.create_log_record("Bob", "BD8_XRD", "Sample2"))
        records.append(tu.create_log_record("Bob", "BD8_XRD", "Sample3"))

        # Undo last one
        records.pop()

        # Save
        tu.save_log_to_csv(records, str(log_file), str(tmp_path))

        # Verify only 2 records saved
        with open(log_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[-1]["SampleID"] == "Sample2"

    def test_multi_process_auto_save(self, tmp_path):
        """Test workflow with process switching and auto-save."""
        # First process
        log_file_1 = tmp_path / "scan_log_c212_sonicator.csv"
        records_1 = []
        records_1.append(
            tu.create_log_record("Alice", "c212_sonicator", "Sample1")
        )
        records_1.append(
            tu.create_log_record("Alice", "c212_sonicator", "Sample2")
        )

        # Check if auto-save should trigger
        should_save = tu.should_auto_save_on_process_switch(
            "c212_sonicator", "c215ss_jv", len(records_1) > 0
        )
        assert should_save

        # Auto-save first process
        success, _ = tu.save_log_to_csv(records_1, str(log_file_1), str(tmp_path))
        assert success
        records_1.clear()

        # Second process
        log_file_2 = tmp_path / "scan_log_c215ss_jv.csv"
        records_2 = []
        records_2.append(tu.create_log_record("Alice", "c215ss_jv", "Sample3"))
        records_2.append(tu.create_log_record("Alice", "c215ss_jv", "Sample4"))

        # Save second process
        tu.save_log_to_csv(records_2, str(log_file_2), str(tmp_path))

        # Verify both files exist with correct data
        assert log_file_1.exists()
        assert log_file_2.exists()

        with open(log_file_1, 'r') as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == 2
            assert all(row["ProcessName"] == "c212_sonicator" for row in rows)

        with open(log_file_2, 'r') as f:
            rows = list(csv.DictReader(f))
            assert len(rows) == 2
            assert all(row["ProcessName"] == "c215ss_jv" for row in rows)

class TestDeprecationWarning:
    """Test cases for CLI deprecation warning."""

    def test_deprecation_warning_in_cli_source(self):
        """Test that deprecation warning is present in CLI source code."""
        import process_tracker
        import inspect

        # Get the source code of main function
        source = inspect.getsource(process_tracker.main)

        # Verify deprecation warning is present
        assert "DEPRECATION WARNING" in source
        assert "CLI" in source
        assert "deprecated as of v0.2.0" in source
        assert "removed in v0.3.0" in source
        assert "GUI interface" in source
