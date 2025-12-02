"""
Unit tests for tracker_utils module using pytest.
"""
import sys
import os
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tracker_utils as tu
from tracker_utils import (
    PROCESS_COLORS,
    get_process_display_name,
    get_tool_display_name,
    get_process_info
)


class TestProcessValidation:
    """Test cases for process validation."""

    def test_all_processes_in_colors_dict(self):
        """Test that PROCESS_COLORS contains expected processes."""
        assert len(PROCESS_COLORS) > 0

    def test_process_lookup_valid(self):
        """Test that valid process names can be looked up in PROCESS_COLORS."""
        assert "c215ss_jv" in PROCESS_COLORS
        assert "bd8_xrd" in PROCESS_COLORS
        assert "ftlb234_spinbox" in PROCESS_COLORS

    def test_validate_and_normalize_valid_process(self):
        """Test validating and normalizing valid processes."""
        is_valid, normalized, error = tu.validate_and_normalize_process("c215ss_jv")
        assert is_valid
        assert normalized == "c215ss_jv"
        assert error == ""

    def test_validate_and_normalize_invalid_process(self):
        """Test validating and normalizing invalid processes."""
        is_valid, normalized, error = tu.validate_and_normalize_process("INVALID_PROC")
        assert not is_valid
        assert normalized == "invalid_proc"
        assert "not implemented" in error
        assert "quarantined" in error
        assert "Rajiv.Daxini@nrel.gov" in error

    def test_validate_and_normalize_case_insensitive(self):
        """Test that validation is case-insensitive."""
        is_valid1, norm1, _ = tu.validate_and_normalize_process("C215SS_JV")
        is_valid2, norm2, _ = tu.validate_and_normalize_process("c215ss_jv")

        assert is_valid1 == is_valid2
        assert norm1 == norm2 == "c215ss_jv"


class TestProcessDisplayNames:
    """Test cases for process display name functions."""

    @pytest.mark.parametrize("abbreviated,expected_display,expected_tool", [
        ("c215ss_jv", "JV", "C215 Solar Simulator"),
        ("bd8_xrd", "XRD", "BD8 X-Ray Diffractometer"),
        ("hsem_sem", "SEM Imaging", "HSEM Scanning Electron Microscope"),
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
        info = get_process_info("c215ss_jv")
        assert isinstance(info, dict)
        assert "tool" in info
        assert "process" in info
        assert "color" in info
        assert info["tool"] == "C215 Solar Simulator"
        assert info["process"] == "JV"

    def test_get_process_info_invalid(self):
        """Test getting process info for invalid process returns empty dict."""
        info = get_process_info("invalid_process")
        assert info == {}

    def test_process_info_has_required_fields(self):
        """Test that process info contains all required fields."""
        for abbreviated in PROCESS_COLORS.keys():
            info = get_process_info(abbreviated)
            assert "tool" in info
            assert "process" in info
            assert "color" in info

    def test_process_info_color_matches(self):
        """Test that color in process info matches PROCESS_COLORS."""
        for abbreviated in PROCESS_COLORS.keys():
            info = get_process_info(abbreviated)
            assert info["color"] == PROCESS_COLORS[abbreviated]


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
            'Operator': 'TestOp',
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
        assert cmd_type == tu.RESET_OPERATOR_CMD

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


class TestRuntimeEnvironment:
    """Test cases for runtime environment detection."""


class TestOperatorValidation:
    """Test cases for operator name validation."""

    def test_validate_operator_name_valid(self):
        """Test valid operator names."""
        is_valid, msg = tu.validate_operator_name("John Doe")
        assert is_valid
        assert msg == ""

    def test_validate_operator_name_empty(self):
        """Test empty operator name."""
        is_valid, msg = tu.validate_operator_name("")
        assert not is_valid
        assert "empty" in msg.lower()

    def test_validate_operator_name_too_short(self):
        """Test operator name too short."""
        is_valid, msg = tu.validate_operator_name("A")
        assert not is_valid
        assert "2 characters" in msg

    def test_validate_operator_name_too_long(self):
        """Test operator name too long."""
        long_name = "A" * 51
        is_valid, msg = tu.validate_operator_name(long_name)
        assert not is_valid
        assert "50 characters" in msg

    def test_validate_operator_name_whitespace(self):
        """Test operator name with only whitespace."""
        is_valid, msg = tu.validate_operator_name("   ")
        assert not is_valid
        assert "empty" in msg.lower()


class TestJSONDataLoading:
    """Test cases for JSON data loading."""

    def test_expected_processes_exist(self):
        """Test that expected processes are loaded from JSON."""
        expected_processes = [
            "c215ss_jv",
            "bd8_xrd",
            "hsem_sem",
            "ftlb234_spinbox",
            "pdil_pct",
        ]
        assert len(PROCESS_COLORS) >= len(expected_processes), "PROCESS_COLORS appears empty or incomplete"
        for process in expected_processes:
            assert process in PROCESS_COLORS, f"Process '{process}' not found in PROCESS_COLORS. JSON may not be loaded."

    def test_all_abbreviations_are_lowercase(self):
        """Test that all abbreviated names are lowercase."""
        for abbreviated in PROCESS_COLORS.keys():
            assert abbreviated == abbreviated.lower(), f"'{abbreviated}' is not lowercase"

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
        ("P%:testing", "PROCESS", "testing"),
        ("S%:999", "SAMPLE", "999"),
        ("2511-09", "SAMPLE_LEGACY", "2511-09"),
        ("9999-99", "SAMPLE_LEGACY", "9999-99"),
    ])
    def test_multiple_valid_inputs(self, input_str, expected_type, expected_id):
        """Test multiple valid input combinations."""
        data_type, data_id = tu.parse_input(input_str)
        assert data_type == expected_type
        assert data_id == expected_id


class TestAutoSaveLogic:
    """Test cases for auto-save on process switch logic."""

    def test_should_auto_save_first_process(self):
        """Test that auto-save doesn't trigger for first process."""
        # No current tool, so should not auto-save
        should_save = tu.should_auto_save_on_process_switch(None, "c215ss_jv", True)
        assert not should_save

    def test_should_auto_save_same_process(self):
        """Test that auto-save doesn't trigger when same process rescanned."""
        # Same process, should not auto-save
        should_save = tu.should_auto_save_on_process_switch("c215ss_jv", "c215ss_jv", True)
        assert not should_save

    def test_should_auto_save_no_records(self):
        """Test that auto-save doesn't trigger if no records exist."""
        # Different process but no records, should not auto-save
        should_save = tu.should_auto_save_on_process_switch("c212_sonicator", "c215ss_jv", False)
        assert not should_save

    def test_should_auto_save_different_process_with_records(self):
        """Test that auto-save triggers when switching process with records."""
        # Different process with records, SHOULD auto-save
        should_save = tu.should_auto_save_on_process_switch("c212_sonicator", "c215ss_jv", True)
        assert should_save

    def test_should_auto_save_case_insensitive(self):
        """Test that process comparison is case-sensitive (normalized)."""
        # These should be treated as same process (already normalized to lowercase)
        should_save = tu.should_auto_save_on_process_switch("c215ss_jv", "c215ss_jv", True)
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
        assert tu.is_process_valid("c215ss_jv") is True
        assert tu.is_process_valid("bd8_xrd") is True

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
        output_dir = tu.get_output_dir("c215ss_jv", base)
        assert output_dir == base
        assert "unapproved" not in output_dir

    def test_get_output_dir_invalid_process(self):
        """Test output dir for invalid process uses quarantine folder."""
        base = "/test/outputs"
        output_dir = tu.get_output_dir("invalid_proc", base)
        assert "unapproved" in output_dir
        assert output_dir == os.path.join(base, "unapproved")
