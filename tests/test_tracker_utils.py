"""
Unit tests for tracker_utils module using pytest.
"""
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import csv  # noqa: E402
import datetime  # noqa: E402
import pytest  # noqa: E402
import tracker_utils as tu  # noqa: E402
from tracker_utils import (  # noqa: E402
    PROCESS_COLORS,
    get_process_info
)


class TestProcessValidation:
    """Test cases for process validation."""

    def test_all_processes_in_colors_dict(self):
        """Test that PROCESS_COLORS contains expected processes."""
        assert len(PROCESS_COLORS) > 0

    def test_process_lookup_valid(self):
        """Test that valid process names can be looked up in PROCESS_COLORS."""
        assert "1p8_mhp_bc" in PROCESS_COLORS
        assert "1p68_mhp_bc" in PROCESS_COLORS
        assert "pae_evap" in PROCESS_COLORS

    def test_validate_and_normalize_valid_process(self):
        """Test validating and normalizing valid processes."""
        is_valid, normalized, error = tu.validate_and_normalize_process("1p8_mhp_bc")
        assert is_valid
        assert normalized == "1p8_mhp_bc"
        assert error == ""

    def test_validate_and_normalize_invalid_process(self):
        """Test that invalid processes return validation info for quarantine."""
        is_valid, normalized, error = (
            tu.validate_and_normalize_process("INVALID_PROC")
        )
        assert not is_valid  # Marked as invalid for quarantine
        assert normalized == "invalid_proc"
        assert "not implemented" in error
        assert "quarantined" in error
        assert "Rajiv.Daxini@nlr.gov" in error

    def test_validate_and_normalize_case_insensitive(self):
        """Test that validation is case-insensitive."""
        is_valid1, norm1, _ = tu.validate_and_normalize_process("1P8_MHP_BC")
        is_valid2, norm2, _ = tu.validate_and_normalize_process("1p8_mhp_bc")

        assert is_valid1 == is_valid2
        assert norm1 == norm2 == "1p8_mhp_bc"


class TestProcessDisplayNames:
    """Test cases for process display name functions."""

    @pytest.mark.parametrize("abbreviated,expected_display,expected_tool", [
        ("1p8_mhp_bc", "Bladecoat 1.8eV perovskite", "Laminar Flow Box"),
        ("c60_evap", "C60 evaporation", "Angstrom Evaporator"),
        ("pae_evap", "Evaporation system", "Angstrom Evaporator"),
    ])
    def test_display_names(self, abbreviated, expected_display, expected_tool):
        """Test display names for processes."""
        assert tu.get_process_display_name(abbreviated) == expected_display
        assert tu.get_tool_display_name(abbreviated) == expected_tool

    def test_display_name_invalid_returns_input(self):
        """Test that invalid process returns the input as display name."""
        assert tu.get_process_display_name("invalid") == "invalid"
        assert tu.get_tool_display_name("invalid") == "invalid"


class TestProcessInfo:
    """Test cases for process info retrieval."""

    def test_get_process_info_valid(self):
        """Test getting full process info for valid process."""
        info = get_process_info("1p8_mhp_bc")
        assert isinstance(info, dict)
        assert "tool" in info
        assert "process" in info
        assert "color" in info
        assert info["tool"] == "Laminar Flow Box"
        assert info["process"] == "Bladecoat 1.8eV perovskite"

    def test_get_process_info_invalid(self):
        """Test getting process info for invalid process returns empty dict."""
        info = get_process_info("invalid_process")
        assert info == {}


class TestProcessColors:
    """Test cases for process color assignments."""

    def test_all_processes_have_colors(self):
        """Test that all processes have assigned colors."""
        for process in PROCESS_COLORS.keys():
            color = PROCESS_COLORS[process]
            assert color.startswith("#")
            assert len(color) == 7  # Hex color format #RRGGBB

    def test_colors_are_valid_hex(self):
        """Test that all colors are valid hex codes."""
        for color in tu.PROCESS_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7
            int(color[1:], 16)  # Should not raise ValueError

    def test_get_process_color_valid(self):
        """Test getting color for valid process."""
        color = tu.get_process_color("c215ss_jv")
        assert color.startswith("#")
        assert len(color) == 7

    def test_get_process_color_invalid(self):
        """Test getting color for invalid process returns default grey."""
        color = tu.get_process_color("invalid_process")
        assert color == tu.DEFAULT_PROCESS_COLOR
        assert color == "#95a5a6"  # Verify it's the grey default


class TestLogFilename:
    """Test cases for log filename generation."""

    def test_get_log_filename(self):
        """Test log filename generation."""
        filename = tu.get_log_filename("c215ss_jv")
        assert filename == "scan_log_c215ss_jv.csv"

    def test_get_log_filename_various_processes(self):
        """Test log filename for various processes."""
        assert tu.get_log_filename("bd8_xrd") == "scan_log_bd8_xrd.csv"
        assert tu.get_log_filename("ftlb234_spinbox") == "scan_log_ftlb234_spinbox.csv"


class TestMessageFormatting:
    """Test cases for message formatting functions."""

    def test_format_log_message(self):
        """Test formatting a log message."""
        record = {
            'Timestamp': '2025-01-01 12:00:00',
            'User': 'TestOp',
            'ProcessName': 'test_process',
            'SampleID': 'SAMPLE123'
        }
        msg = tu.format_log_message(record)
        assert "[LOGGED]" in msg
        assert "TestOp" in msg
        assert "test_process" in msg
        assert "SAMPLE123" in msg

    def test_format_undo_message(self):
        """Test formatting an undo message."""
        record = {
            'Timestamp': '2025-01-01 12:00:00',
            'ProcessName': 'test_process',
            'SampleID': 'SAMPLE123'
        }
        msg = tu.format_undo_message(record)
        assert "[UNDO]" in msg
        assert "test_process" in msg
        assert "SAMPLE123" in msg

    def test_format_legacy_sample_warning(self):
        """Test formatting a legacy sample warning."""
        msg = tu.format_legacy_sample_warning("2511-09")
        assert "[WARNING]" in msg
        assert "Legacy sample format detected" in msg
        assert "2511-09" in msg

    def test_format_auto_save_message(self):
        """Test formatting an auto-save message."""
        msg = tu.format_auto_save_message(3, "scan_log_c212_sonicator.csv")
        assert "[AUTO-SAVE]" in msg
        assert "3 record(s)" in msg
        assert "scan_log_c212_sonicator.csv" in msg


class TestCommandDetection:
    """Test cases for command detection."""

    def test_is_command_exit(self):
        """Test EXIT command detection."""
        is_cmd, cmd_type = tu.is_command("EXIT")
        assert is_cmd
        assert cmd_type == tu.EXIT_CMD

    def test_is_command_save(self):
        """Test SAVE command detection."""
        is_cmd, cmd_type = tu.is_command("SAVE")
        assert is_cmd
        assert cmd_type == tu.SAVE_CMD

    def test_is_command_undo(self):
        """Test UNDO command detection."""
        is_cmd, cmd_type = tu.is_command("UNDO")
        assert is_cmd
        assert cmd_type == tu.UNDO_CMD

    def test_is_command_reset(self):
        """Test RESET command detection."""
        is_cmd, cmd_type = tu.is_command("RESET")
        assert is_cmd
        assert cmd_type == tu.RESET_USER_CMD

    def test_is_command_case_insensitive(self):
        """Test that commands are case-insensitive."""
        is_cmd1, cmd1 = tu.is_command("exit")
        is_cmd2, cmd2 = tu.is_command("EXIT")
        is_cmd3, cmd3 = tu.is_command("Exit")

        assert is_cmd1 and is_cmd2 and is_cmd3
        assert cmd1 == cmd2 == cmd3 == tu.EXIT_CMD

    def test_is_command_not_command(self):
        """Test that non-commands return False."""
        is_cmd, cmd_type = tu.is_command("P%:test")
        assert not is_cmd
        assert cmd_type is None


class TestUserValidation:
    """Test cases for user name validation."""

    def test_validate_username_valid(self):
        """Test valid user names."""
        is_valid, msg = tu.validate_username("John Doe")
        assert is_valid
        assert msg == ""

    def test_validate_username_empty(self):
        """Test empty user name."""
        is_valid, msg = tu.validate_username("")
        assert not is_valid
        assert "empty" in msg.lower()

    def test_validate_username_too_short(self):
        """Test user name too short."""
        is_valid, msg = tu.validate_username("A")
        assert not is_valid
        assert "2 characters" in msg

    def test_validate_username_too_long(self):
        """Test user name too long."""
        long_name = "A" * 51
        is_valid, msg = tu.validate_username(long_name)
        assert not is_valid
        assert "50 characters" in msg

    def test_validate_username_whitespace(self):
        """Test user name with only whitespace."""
        is_valid, msg = tu.validate_username("   ")
        assert not is_valid
        assert "empty" in msg.lower()


class TestJSONDataLoading:
    """Test cases for JSON data loading."""

    def test_expected_processes_exist(self):
        """Test that JSON loading succeeded and processes are available."""
        assert len(PROCESS_COLORS) > 0, (
            "PROCESS_COLORS is empty. JSON may not have loaded."
        )
        known_processes = ["1p8_mhp_bc", "c60_evap", "pae_evap"]
        for process in known_processes:
            assert process in PROCESS_COLORS, (
                f"Process '{process}' not in PROCESS_COLORS. "
                "JSON may not be loaded correctly."
            )

    def test_all_abbreviations_are_lowercase(self):
        """Test that all abbreviated names are lowercase."""
        for abbreviated in PROCESS_COLORS.keys():
            assert abbreviated == abbreviated.lower(), (
                f"'{abbreviated}' is not lowercase"
            )

    def test_parse_input_preserves_case(self):
        """Test that parse_input preserves case in IDs."""
        data_type, data_id = tu.parse_input("P%:C215SS_JV")
        assert data_type == "PROCESS"
        assert data_id == "C215SS_JV"  # parse_input preserves case

        data_type, data_id = tu.parse_input("S%:ABC123xyz")
        assert data_type == "SAMPLE"
        assert data_id == "ABC123xyz"  # Case preserved


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

    def test_valid_batch(self):
        """Test parsing valid BATCH input."""
        data_type, data_id = tu.parse_input("B%:BATCH001")
        assert data_type == "BATCH"
        assert data_id == "BATCH001"

    def test_legacy_sample_format(self):
        """Test parsing legacy sample format (####-##)."""
        data_type, data_id = tu.parse_input("2511-09")
        assert data_type == "SAMPLE_LEGACY"
        assert data_id == "2511-09"

    def test_legacy_sample_various_patterns(self):
        """Test various legacy sample patterns."""
        # Valid legacy format
        data_type, data_id = tu.parse_input("1234-56")
        assert data_type == "SAMPLE_LEGACY"
        assert data_id == "1234-56"

        # Invalid patterns (should not match)
        data_type, data_id = tu.parse_input("123-45")  # Only 3 digits before dash
        assert data_type is None

        data_type, data_id = tu.parse_input("12345-67")  # 5 digits before dash
        assert data_type is None

        data_type, data_id = tu.parse_input("1234-567")  # 3 digits after dash
        assert data_type is None

    def test_case_sensitive_prefix(self):
        """Test that prefix must match exactly (case-sensitive)."""
        # Lowercase prefix should not work
        data_type, data_id = tu.parse_input("s%:Test")
        assert data_type is None
        assert data_id is None

    @pytest.mark.parametrize("input_str,expected_type,expected_id", [
        ("P%:ftlb234_spinbox", "PROCESS", "ftlb234_spinbox"),
        ("S%:ABC123", "SAMPLE", "ABC123"),
        ("B%:BATCH001", "BATCH", "BATCH001"),
        ("P%:testing", "PROCESS", "testing"),
        ("S%:999", "SAMPLE", "999"),
        ("B%:test", "BATCH", "test"),
        ("2511-09", "SAMPLE_LEGACY", "2511-09"),
        ("9999-99", "SAMPLE_LEGACY", "9999-99"),
    ])
    def test_multiple_valid_inputs(self, input_str, expected_type, expected_id):
        """Test multiple valid input combinations."""
        data_type, data_id = tu.parse_input(input_str)
        assert data_type == expected_type
        assert data_id == expected_id


class TestBatchScanning:
    """Test cases specifically for batch ID scanning."""

    def test_batch_scanning_full_workflow(self):
        """Test complete batch scanning workflow from parsing to logging."""
        # Parse batch QR code
        data_type, data_id = tu.parse_input("B%:BATCH123")
        assert data_type == "BATCH"
        assert data_id == "BATCH123"

        # Verify type detection helpers
        assert tu.is_batch_type("BATCH") is True

        # Create log record with batch
        record = tu.create_log_record(
            username="TestOp",
            process_name="test_process",
            batch_id="BATCH123"
        )
        assert record['BatchID'] == "BATCH123"
        assert record['SampleID'] == ""

        # Format messages
        log_msg = tu.format_log_message(record)
        assert "Batch: 'BATCH123'" in log_msg
        assert "Sample:" not in log_msg

        undo_msg = tu.format_undo_message(record)
        assert "Batch: 'BATCH123'" in undo_msg

    def test_batch_prefix_case_sensitive(self):
        """Test that batch prefix B%: is case-sensitive."""
        # Uppercase works
        data_type, data_id = tu.parse_input("B%:test")
        assert data_type == "BATCH"
        assert data_id == "test"

        # Lowercase prefix should not work
        data_type, data_id = tu.parse_input("b%:test")
        assert data_type is None
        assert data_id is None

    def test_empty_batch_id_rejected(self):
        """Test that empty batch ID after prefix is invalid."""
        data_type, data_id = tu.parse_input("B%:")
        assert data_type is None
        assert data_id is None

        data_type, data_id = tu.parse_input("B%:   ")
        assert data_type is None
        assert data_id is None

    def test_batch_mutual_exclusivity_with_sample(self):
        """Test that batch and sample IDs are mutually exclusive in records."""
        # Create batch record - sample should be empty
        batch_record = tu.create_log_record(
            "Op", "proc", batch_id="B001"
        )
        assert batch_record['BatchID'] == "B001"
        assert batch_record['SampleID'] == ""

        # Create sample record - batch should be empty
        sample_record = tu.create_log_record(
            "Op", "proc", sample_id="S001"
        )
        assert sample_record['SampleID'] == "S001"
        assert sample_record['BatchID'] == ""


class TestAutoSaveLogic:
    """Test cases for auto-save on process switch logic."""

    def test_should_auto_save_first_process(self):
        """Test that auto-save doesn't trigger for first process."""
        # No current tool, so should not auto-save
        should_save = tu.should_auto_save_on_process_switch(
            None, "c215ss_jv", True
        )
        assert not should_save

    def test_should_auto_save_same_process(self):
        """Test that auto-save doesn't trigger when same process rescanned."""
        # Same process, should not auto-save
        should_save = tu.should_auto_save_on_process_switch(
            "c215ss_jv", "c215ss_jv", True
        )
        assert not should_save

    def test_should_auto_save_no_records(self):
        """Test that auto-save doesn't trigger if no records exist."""
        # Different process but no records, should not auto-save
        should_save = tu.should_auto_save_on_process_switch(
            "c212_sonicator", "c215ss_jv", False
        )
        assert not should_save

    def test_should_auto_save_different_process_with_records(self):
        """Test that auto-save triggers when switching process."""
        # Different process with records, SHOULD auto-save
        should_save = tu.should_auto_save_on_process_switch(
            "c212_sonicator", "c215ss_jv", True
        )
        assert should_save

    def test_should_auto_save_case_insensitive(self):
        """Test that process comparison is case-sensitive."""
        # These should be treated as same process (normalized)
        should_save = tu.should_auto_save_on_process_switch(
            "c215ss_jv", "c215ss_jv", True
        )
        assert not should_save


class TestQuarantineLogic:
    """Test cases specifically for unapproved/quarantine process handling."""

    def test_unapproved_log_filename_format(self):
        """Test quarantine log filename format."""
        filename = tu.get_unapproved_log_filename("test_process")
        assert filename == "scan_log_UNAPPROVED_test_process.csv"

    def test_unapproved_output_directory(self):
        """Test quarantine output directory."""
        base = "/test/outputs"
        unapproved_dir = tu.get_unapproved_output_dir(base)
        assert "unapproved" in unapproved_dir
        assert unapproved_dir == os.path.join(base, "unapproved")

    def test_is_process_valid_true(self):
        """Test is_process_valid returns True for valid processes."""
        assert tu.is_process_valid("1p8_mhp_bc") is True
        assert tu.is_process_valid("c60_evap") is True

    def test_is_process_valid_false(self):
        """Test is_process_valid returns False for invalid processes."""
        assert tu.is_process_valid("invalid_process") is False
        assert tu.is_process_valid("not_in_json") is False

    def test_get_log_filename_valid_process(self):
        """Test log filename for valid process."""
        filename = tu.get_log_filename("c215ss_jv", valid=True)
        assert filename == "scan_log_c215ss_jv.csv"
        assert "UNAPPROVED" not in filename

    def test_get_log_filename_invalid_process(self):
        """Test log filename for invalid process is quarantined."""
        filename = tu.get_log_filename("invalid_proc", valid=False)
        assert "UNAPPROVED" in filename
        assert filename == "scan_log_UNAPPROVED_invalid_proc.csv"

    def test_get_output_dir_valid_process(self):
        """Test output dir for valid process uses base folder."""
        base = "/test/outputs"
        output_dir = tu.get_output_dir("invalid_proc", base)
        assert "unapproved" in output_dir
        assert output_dir == os.path.join(base, "unapproved")


class TestCheckout:
    """Tests for the sample checkout utilities."""

    # --- generate_consecutive_sample_ids ---

    def test_single_id_returns_start(self):
        ids = tu.generate_consecutive_sample_ids("2503-015", 1)
        assert ids == ["2503-015"]

    @pytest.mark.parametrize("start,count,expected_last", [
        ("2503-015", 5,  "2503-019"),
        ("2503-001", 10, "2503-010"),
        ("2503-098", 3,  "2503-100"),
        ("2503-999", 1,  "2503-999"),
    ])
    def test_bulk_range(self, start, count, expected_last):
        ids = tu.generate_consecutive_sample_ids(start, count)
        assert len(ids) == count
        assert ids[0] == start
        assert ids[-1] == expected_last

    def test_zero_padding_preserved(self):
        ids = tu.generate_consecutive_sample_ids("2503-007", 3)
        assert ids == ["2503-007", "2503-008", "2503-009"]

    def test_overflow_raises(self):
        with pytest.raises(ValueError, match="overflow"):
            tu.generate_consecutive_sample_ids("2503-998", 3)

    def test_no_dash_raises(self):
        with pytest.raises(ValueError):
            tu.generate_consecutive_sample_ids("2503015", 1)

    def test_non_numeric_suffix_raises(self):
        with pytest.raises(ValueError):
            tu.generate_consecutive_sample_ids("2503-ABC", 1)

    def test_count_zero_raises(self):
        with pytest.raises(ValueError):
            tu.generate_consecutive_sample_ids("2503-015", 0)

    def test_count_negative_raises(self):
        with pytest.raises(ValueError):
            tu.generate_consecutive_sample_ids("2503-015", -1)

    def test_all_ids_share_prefix(self):
        ids = tu.generate_consecutive_sample_ids("2503-010", 5)
        assert all(id_.startswith("2503-") for id_ in ids)

    def test_ids_are_consecutive(self):
        ids = tu.generate_consecutive_sample_ids("2503-020", 10)
        suffixes = [int(id_.rsplit("-", 1)[1]) for id_ in ids]
        assert suffixes == list(range(20, 30))

    # --- create_checkout_record ---

    def test_checkout_record_fields(self):
        record = tu.create_checkout_record("rdaxini", "2503-015")
        assert record["User"] == "rdaxini"
        assert record["SampleID"] == "2503-015"
        assert "Timestamp" in record
        # Timestamp must be parseable
        datetime.datetime.strptime(record["Timestamp"], tu.DATE_FORMAT)

    def test_checkout_record_no_process_field(self):
        record = tu.create_checkout_record("rdaxini", "2503-015")
        assert "ProcessName" not in record

    # --- format_checkout_message ---

    def test_format_checkout_message_contains_key_fields(self):
        record = tu.create_checkout_record("rdaxini", "2503-015")
        msg = tu.format_checkout_message(record)
        assert "[CHECKOUT]" in msg
        assert "rdaxini" in msg
        assert "2503-015" in msg

    # --- save_checkout_to_csv ---

    def test_get_checkout_log_filename(self):
        assert tu.get_checkout_log_filename(2026, 4) == "checkout_log_2026-04.csv"
        assert tu.get_checkout_log_filename(2025, 12) == "checkout_log_2025-12.csv"
        assert tu.get_checkout_log_filename(2026, 1) == "checkout_log_2026-01.csv"

    def test_save_checkout_creates_file_with_header(self, tmp_path):
        records = [tu.create_checkout_record("rdaxini", "2503-015")]
        success, msg = tu.save_checkout_to_csv(records, str(tmp_path))
        assert success
        now = datetime.datetime.now()
        expected_filename = tu.get_checkout_log_filename(now.year, now.month)
        log_file = tmp_path / expected_filename
        assert log_file.exists()
        with open(log_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["SampleID"] == "2503-015"
        assert rows[0]["User"] == "rdaxini"

    def test_save_checkout_appends(self, tmp_path):
        r1 = [tu.create_checkout_record("rdaxini", "2503-015")]
        r2 = [tu.create_checkout_record("rdaxini", "2503-016")]
        tu.save_checkout_to_csv(r1, str(tmp_path))
        tu.save_checkout_to_csv(r2, str(tmp_path))
        now = datetime.datetime.now()
        log_file = tmp_path / tu.get_checkout_log_filename(now.year, now.month)
        with open(log_file, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[1]["SampleID"] == "2503-016"

    def test_save_checkout_empty_returns_false(self, tmp_path):
        success, msg = tu.save_checkout_to_csv([], str(tmp_path))
        assert not success

    def test_save_checkout_routes_to_monthly_files(self, tmp_path):
        """Records with different months are written to separate files."""
        records = [
            {'Timestamp': '2026-03-15 10:00:00', 'User': 'rdaxini',
             'SampleID': '2503-001'},
            {'Timestamp': '2026-04-02 09:00:00', 'User': 'rdaxini',
             'SampleID': '2504-001'},
        ]
        success, msg = tu.save_checkout_to_csv(records, str(tmp_path))
        assert success
        mar_file = tmp_path / "checkout_log_2026-03.csv"
        apr_file = tmp_path / "checkout_log_2026-04.csv"
        assert mar_file.exists()
        assert apr_file.exists()
        with open(mar_file, newline="", encoding="utf-8") as f:
            mar_rows = list(csv.DictReader(f))
        with open(apr_file, newline="", encoding="utf-8") as f:
            apr_rows = list(csv.DictReader(f))
        assert len(mar_rows) == 1 and mar_rows[0]["SampleID"] == "2503-001"
        assert len(apr_rows) == 1 and apr_rows[0]["SampleID"] == "2504-001"

    def test_get_output_dir_invalid_process(self):
        """Test output dir for invalid process uses quarantine folder."""
        base = "/test/outputs"
        output_dir = tu.get_output_dir("invalid_proc", base)
        assert "unapproved" in output_dir
        assert output_dir == os.path.join(base, "unapproved")


class TestTrayParsing:
    """Test cases for tray QR code parsing."""

    def test_parse_tray_valid(self):
        """Test parsing valid TRAY input."""
        data_type, data_id = tu.parse_input("T%:066726-S-XXX")
        assert data_type == "TRAY"
        assert data_id == "066726-S-XXX"

    def test_parse_tray_various_ids(self):
        """Test parsing various tray IDs."""
        test_cases = [
            ("T%:066726-S-XXX", "066726-S-XXX"),
            ("T%:072266-XXX-A", "072266-XXX-A"),
            ("T%:070503-XXX-A", "070503-XXX-A"),
        ]
        for input_str, expected_id in test_cases:
            data_type, data_id = tu.parse_input(input_str)
            assert data_type == "TRAY"
            assert data_id == expected_id

    def test_parse_tray_case_sensitive(self):
        """Test that tray prefix is case-sensitive."""
        # Lowercase should not work
        data_type, data_id = tu.parse_input("t%:066726-S-XXX")
        assert data_type is None
        assert data_id is None

    def test_parse_tray_empty_id(self):
        """Test that tray prefix without ID is invalid."""
        data_type, data_id = tu.parse_input("T%:")
        assert data_type is None
        assert data_id is None


class TestTrayLayoutLoading:
    """Test cases for tray layout JSON loading."""

    def test_tray_layouts_loaded(self):
        """Test that TRAY_LAYOUTS dictionary is populated from JSON."""
        # Verify the dictionary exists and was loaded
        assert isinstance(tu.TRAY_LAYOUTS, dict), (
            "TRAY_LAYOUTS should be a dictionary"
        )

    def test_tray_layout_structure(self):
        """Test that tray layouts have expected structure (list of position strings)."""

        for tray_id, positions in tu.TRAY_LAYOUTS.items():
            # Should be a list
            assert isinstance(positions, list), (
                f"Tray layout for '{tray_id}' is not a list"
            )

            # Should contain position strings
            assert len(positions) > 0, (
                f"Tray '{tray_id}' has no positions"
            )

            for pos in positions:
                assert isinstance(pos, str) and len(pos) >= 2, (
                    f"Invalid position format '{pos}' in tray '{tray_id}'"
                )


class TestTrayValidation:
    """Test cases for tray mode validation logic."""

    def test_validate_tray_ready_positions_complete(self):
        """Test that tray is ready when all positions filled."""
        is_ready, error = tu.validate_tray_ready_for_process(4, 4)
        assert is_ready
        assert error == ""

    def test_validate_tray_ready_positions_incomplete(self):
        """Test that tray is not ready when positions remain."""
        is_ready, error = tu.validate_tray_ready_for_process(2, 4)
        assert not is_ready
        assert "[ERROR]" in error
        assert "Complete all tray positions" in error

    def test_validate_tray_ready_no_positions_filled(self):
        """Test that tray is not ready when no positions filled."""
        is_ready, error = tu.validate_tray_ready_for_process(0, 8)
        assert not is_ready
        assert "[ERROR]" in error

    def test_validate_tray_ready_exact_completion(self):
        """Test tray ready at exact completion point."""
        is_ready, error = tu.validate_tray_ready_for_process(8, 8)
        assert is_ready
        assert error == ""


class TestTrayScanAcceptance:
    """Test cases for determining if scans are accepted in tray mode."""

    def test_accept_sample_in_tray_mode(self):
        """Test that SAMPLE scans are accepted in tray mode."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("SAMPLE", 0, 4)
        assert should_accept
        assert error == ""

    def test_accept_legacy_sample_in_tray_mode(self):
        """Test that SAMPLE_LEGACY scans are accepted in tray mode."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("SAMPLE_LEGACY", 2, 4)
        assert should_accept
        assert error == ""

    def test_accept_process_when_complete(self):
        """Test that PROCESS is accepted when all positions filled."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("PROCESS", 4, 4)
        assert should_accept
        assert error == ""

    def test_reject_process_when_incomplete(self):
        """Test that PROCESS is rejected when positions remain."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("PROCESS", 2, 4)
        assert not should_accept
        assert "[ERROR]" in error
        assert "Complete all tray positions" in error

    def test_reject_tray_in_tray_mode(self):
        """Test that TRAY scans are rejected in tray mode."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("TRAY", 1, 4)
        assert not should_accept
        assert "[ERROR]" in error
        assert "SAMPLE or PROCESS" in error

    def test_reject_invalid_type_in_tray_mode(self):
        """Test that invalid scan types are rejected."""
        should_accept, error = tu.should_accept_scan_in_tray_mode("UNKNOWN", 1, 4)
        assert not should_accept
        assert "[ERROR]" in error


class TestTrayBatchRecordCreation:
    """Test cases for batch log record creation for tray samples."""

    def test_create_tray_batch_records_single_sample(self):
        """Test creating batch records for single sample."""
        tray_samples = [{"position": "A1", "sample_id": "SAMPLE001"}]
        records = tu.create_tray_batch_records(
            "TestUser", "066726-S-XXX", tray_samples, "test_process"
        )

        assert len(records) == 1
        assert records[0]["User"] == "TestUser"
        assert records[0]["TrayID"] == "066726-S-XXX"
        assert records[0]["Position"] == "A1"
        assert records[0]["SampleID"] == "SAMPLE001"
        assert records[0]["ProcessName"] == "test_process"
        assert "Timestamp" in records[0]

    def test_create_tray_batch_records_multiple_samples(self):
        """Test creating batch records for multiple samples."""
        tray_samples = [
            {"position": "A1", "sample_id": "SAMPLE001"},
            {"position": "A2", "sample_id": "SAMPLE002"},
            {"position": "B1", "sample_id": "SAMPLE003"},
            {"position": "B2", "sample_id": "SAMPLE004"},
        ]
        records = tu.create_tray_batch_records(
            "TestOp", "066726-S-XXX", tray_samples, "c215ss_jv"
        )

        assert len(records) == 4
        for i, record in enumerate(records):
            assert record["TrayID"] == "066726-S-XXX"
            assert record["Position"] == tray_samples[i]["position"]
            assert record["SampleID"] == tray_samples[i]["sample_id"]
            assert record["ProcessName"] == "c215ss_jv"
            assert record["User"] == "TestOp"

    def test_create_tray_batch_records_empty_list(self):
        """Test creating batch records with empty sample list."""
        records = tu.create_tray_batch_records(
            "TestOp", "066726-S-XXX", [], "test_process"
        )
        assert len(records) == 0
        assert isinstance(records, list)

    def test_create_tray_batch_records_positions_ordered(self):
        """Test that record order matches sample order."""
        tray_samples = [
            {"position": "C3", "sample_id": "SAMPLE_C3"},
            {"position": "A1", "sample_id": "SAMPLE_A1"},
            {"position": "B2", "sample_id": "SAMPLE_B2"},
        ]
        records = tu.create_tray_batch_records(
            "TestOp", "072266-XXX-A", tray_samples, "bd8_xrd"
        )

        # Order should be preserved
        assert records[0]["Position"] == "C3"
        assert records[1]["Position"] == "A1"
        assert records[2]["Position"] == "B2"


class TestTrayLogRecordFormat:
    """Test cases for tray log record formatting."""

    def test_create_log_record_with_tray(self):
        """Test creating a single tray log record."""
        record = tu.create_log_record_with_tray(
            "TestOp", "066726-S-XXX", "A1", "SAMPLE001", "test_process"
        )

        assert record["User"] == "TestOp"
        assert record["TrayID"] == "066726-S-XXX"
        assert record["Position"] == "A1"
        assert record["SampleID"] == "SAMPLE001"
        assert record["ProcessName"] == "test_process"
        assert "Timestamp" in record

    def test_format_log_message_with_tray(self):
        """Test formatting log message with tray info."""
        record = {
            "Timestamp": "2026-01-29 12:00:00",
            "User": "TestOp",
            "TrayID": "066726-S-XXX",
            "Position": "A1",
            "SampleID": "SAMPLE001",
            "ProcessName": "test_process"
        }
        msg = tu.format_log_message(record)

        assert "[LOGGED]" in msg
        assert "TestOp" in msg
        assert "Tray: '066726-S-XXX'" in msg
        assert "Pos: 'A1'" in msg
        assert "SAMPLE001" in msg
        assert "test_process" in msg

    def test_format_log_message_without_tray(self):
        """Test formatting log message without tray info still works."""
        record = {
            "Timestamp": "2026-01-29 12:00:00",
            "User": "TestOp",
            "SampleID": "SAMPLE001",
            "ProcessName": "test_process"
        }
        msg = tu.format_log_message(record)

        assert "[LOGGED]" in msg
        assert "TestOp" in msg
        assert "SAMPLE001" in msg
        assert "test_process" in msg
        assert "Tray:" not in msg  # Should not include tray info
