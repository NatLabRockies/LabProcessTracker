import pytest
import os
import sys
import tempfile
import shutil
import csv
import datetime
from unittest.mock import patch

# Add src directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import process_tracker


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    test_dir = tempfile.mkdtemp()
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def setup_tracker(temp_dir):
    """Set up process tracker with test configuration."""
    test_log_file = os.path.join(temp_dir, "test_scan_log.csv")

    # Reset global state
    process_tracker.operator_name = "TestOperator"
    process_tracker.current_process = None
    process_tracker.log_records = []
    process_tracker.LOG_FILE = test_log_file
    process_tracker.OUTPUTS_FOLDER = temp_dir

    yield temp_dir, test_log_file

    # Cleanup
    process_tracker.operator_name = None
    process_tracker.current_process = None
    process_tracker.log_records = []


class TestParseInput:
    """Test suite for parse_input function."""

    def test_valid_process(self):
        """Test parsing valid PROCESS QR code."""
        data_type, data_id = process_tracker.parse_input("PROCESS:Example Process")
        assert data_type == "PROCESS"
        assert data_id == "Example Process"

    def test_valid_sample(self):
        """Test parsing valid SAMPLE QR code."""
        data_type, data_id = process_tracker.parse_input("SAMPLE:12345")
        assert data_type == "SAMPLE"
        assert data_id == "12345"

    def test_case_insensitive(self):
        """Test that data type is case-insensitive."""
        data_type, data_id = process_tracker.parse_input("process:Test")
        assert data_type == "PROCESS"
        assert data_id == "Test"

    def test_with_whitespace(self):
        """Test parsing with extra whitespace."""
        data_type, data_id = process_tracker.parse_input("  SAMPLE : 67890  ")
        assert data_type == "SAMPLE"
        assert data_id == "67890"

    def test_invalid_format(self):
        """Test parsing invalid format returns None."""
        data_type, data_id = process_tracker.parse_input("InvalidFormat")
        assert data_type is None
        assert data_id is None

    def test_empty_string(self):
        """Test parsing empty string returns None."""
        data_type, data_id = process_tracker.parse_input("")
        assert data_type is None
        assert data_id is None

    def test_with_colon_in_id(self):
        """Test parsing with colon in the ID part."""
        data_type, data_id = process_tracker.parse_input("PROCESS:Test:With:Colons")
        assert data_type == "PROCESS"
        assert data_id == "Test:With:Colons"

    @pytest.mark.parametrize("input_str,expected_type,expected_id", [
        ("PROCESS:Coating", "PROCESS", "Coating"),
        ("SAMPLE:ABC123", "SAMPLE", "ABC123"),
        ("process:testing", "PROCESS", "testing"),
        ("SAMPLE:999", "SAMPLE", "999"),
    ])
    def test_multiple_valid_inputs(self, input_str, expected_type, expected_id):
        """Test multiple valid input scenarios."""
        data_type, data_id = process_tracker.parse_input(input_str)
        assert data_type == expected_type
        assert data_id == expected_id


class TestLogScanEvent:
    """Test suite for log_scan_event function."""

    def test_log_scan_event(self, setup_tracker):
        """Test logging a scan event."""
        temp_dir, _ = setup_tracker
        process_tracker.operator_name = "TestOp"
        process_tracker.log_scan_event("Test Process", "SAMPLE001")

        assert len(process_tracker.log_records) == 1
        record = process_tracker.log_records[0]
        assert record['Operator'] == "TestOp"
        assert record['ProcessName'] == "Test Process"
        assert record['SampleID'] == "SAMPLE001"
        assert 'Timestamp' in record

    def test_timestamp_format(self, setup_tracker):
        """Test that timestamp is in correct format."""
        temp_dir, _ = setup_tracker
        process_tracker.log_scan_event("Process", "Sample")
        record = process_tracker.log_records[0]

        # Should not raise exception if format is correct
        datetime.datetime.strptime(record['Timestamp'], process_tracker.DATE_FORMAT)

    def test_multiple_logs(self, setup_tracker):
        """Test logging multiple events."""
        temp_dir, _ = setup_tracker
        process_tracker.log_scan_event("Process1", "Sample1")
        process_tracker.log_scan_event("Process2", "Sample2")
        process_tracker.log_scan_event("Process3", "Sample3")

        assert len(process_tracker.log_records) == 3
        assert process_tracker.log_records[0]['SampleID'] == "Sample1"
        assert process_tracker.log_records[2]['SampleID'] == "Sample3"


class TestUndoLastScan:
    """Test suite for undo_last_scan function."""

    def test_undo_last_scan(self, setup_tracker):
        """Test undoing the last scan."""
        temp_dir, _ = setup_tracker
        process_tracker.log_scan_event("Process1", "Sample1")
        process_tracker.log_scan_event("Process2", "Sample2")

        assert len(process_tracker.log_records) == 2

        process_tracker.undo_last_scan()
        assert len(process_tracker.log_records) == 1
        assert process_tracker.log_records[0]['SampleID'] == "Sample1"

    def test_undo_empty_log(self, setup_tracker):
        """Test undo when no records exist."""
        temp_dir, _ = setup_tracker
        process_tracker.undo_last_scan()
        assert len(process_tracker.log_records) == 0

    def test_undo_multiple_times(self, setup_tracker):
        """Test undoing multiple times."""
        temp_dir, _ = setup_tracker
        process_tracker.log_scan_event("P1", "S1")
        process_tracker.log_scan_event("P2", "S2")
        process_tracker.log_scan_event("P3", "S3")

        process_tracker.undo_last_scan()
        process_tracker.undo_last_scan()

        assert len(process_tracker.log_records) == 1
        assert process_tracker.log_records[0]['SampleID'] == "S1"


class TestSaveLog:
    """Test suite for save_log function."""

    def test_creates_file(self, setup_tracker):
        """Test that save_log creates a CSV file."""
        temp_dir, test_log_file = setup_tracker
        process_tracker.log_scan_event("Process1", "Sample1")
        process_tracker.save_log()

        assert os.path.exists(test_log_file)

    def test_writes_correct_data(self, setup_tracker):
        """Test that save_log writes correct data to CSV."""
        temp_dir, test_log_file = setup_tracker
        process_tracker.log_scan_event("TestProcess", "TestSample")
        process_tracker.save_log()

        with open(test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]['ProcessName'] == "TestProcess"
        assert rows[0]['SampleID'] == "TestSample"
        assert rows[0]['Operator'] == "TestOperator"

    def test_appends_to_existing_file(self, setup_tracker):
        """Test that save_log appends to existing file."""
        temp_dir, test_log_file = setup_tracker
        process_tracker.log_scan_event("Process1", "Sample1")
        process_tracker.save_log()

        process_tracker.log_scan_event("Process2", "Sample2")
        process_tracker.save_log()

        with open(test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2

    def test_clears_records_after_save(self, setup_tracker):
        """Test that save_log clears in-memory records."""
        temp_dir, test_log_file = setup_tracker
        process_tracker.log_scan_event("Process1", "Sample1")
        process_tracker.save_log()

        assert len(process_tracker.log_records) == 0

    def test_save_empty_records(self, setup_tracker):
        """Test save_log with no records."""
        temp_dir, test_log_file = setup_tracker
        process_tracker.save_log()
        assert len(process_tracker.log_records) == 0


class TestOutputDirectory:
    """Test suite for output directory functions."""

    def test_get_default_output_dir_project_exists(self):
        """Test get_default_output_dir when project outputs exists."""
        with patch('os.path.isdir', return_value=True):
            with patch('os.path.dirname') as mock_dirname:
                mock_dirname.return_value = "/fake/project"
                result = process_tracker.get_default_output_dir()
                assert "outputs" in result

    def test_get_default_output_dir_fallback(self):
        """Test get_default_output_dir fallback to Documents."""
        with patch('os.path.isdir', return_value=False):
            result = process_tracker.get_default_output_dir()
            assert "Documents" in result
            assert "process_tracking_outputs" in result

    @patch('sys.argv', ['process_tracker.py', '--output-dir', '/custom/path'])
    def test_parse_args_custom_output_dir(self):
        """Test parsing command line arguments for custom output directory."""
        args = process_tracker.parse_args()
        assert args.output_dir == '/custom/path'


class TestIntegrationWorkflow:
    """Integration tests simulating complete user workflows."""

    def test_full_workflow(self, setup_tracker):
        """Test a complete workflow: set process, log samples, save."""
        temp_dir, test_log_file = setup_tracker

        # Set process and log samples
        process_tracker.current_process = "Coating"
        process_tracker.log_scan_event("Coating", "S001")
        process_tracker.log_scan_event("Coating", "S002")
        process_tracker.log_scan_event("Coating", "S003")

        # Change process
        process_tracker.current_process = "Testing"
        process_tracker.log_scan_event("Testing", "S001")

        # Save
        process_tracker.save_log()

        # Verify file contents
        with open(test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 4
        assert rows[0]['ProcessName'] == "Coating"
        assert rows[3]['ProcessName'] == "Testing"

    def test_workflow_with_undo(self, setup_tracker):
        """Test workflow with undo operations."""
        temp_dir, test_log_file = setup_tracker

        process_tracker.current_process = "Process1"
        process_tracker.log_scan_event("Process1", "S001")
        process_tracker.log_scan_event("Process1", "S002")
        process_tracker.log_scan_event("Process1", "S003")

        # Undo last scan
        process_tracker.undo_last_scan()

        # Save
        process_tracker.save_log()

        # Verify only 2 records saved
        with open(test_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[-1]['SampleID'] == "S002"
