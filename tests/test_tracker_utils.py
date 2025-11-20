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
    validate_process,
    PROCESS_COLORS,
    get_process_display_name,
    get_tool_display_name,
    get_process_info
)


class TestProcessValidation:
    """Test cases for process validation."""

    def test_valid_process_names(self):
        """Test that all valid process names pass validation without errors."""
        for process_name in PROCESS_COLORS.keys():
            # Should not raise any exception
            validate_process(process_name)

    @pytest.mark.parametrize("invalid_process", [
        "INVALID_PROCESS",
        "NotAProcess",
        "XYZ123",
        "random_name",
        ""
    ])
    def test_invalid_process_name(self, invalid_process):
        """Test that invalid process names raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_process(invalid_process)

        # Check that error message contains useful information
        error_message = str(exc_info.value)
        assert invalid_process in error_message
        assert "not implemented" in error_message.lower()
        assert "Rajiv.Daxini@nrel.gov" in error_message

    def test_error_message_includes_available_processes(self):
        """Test that error message lists available processes."""
        with pytest.raises(ValueError) as exc_info:
            validate_process("INVALID_PROCESS")

        error_message = str(exc_info.value)
        # Check that at least some of the valid processes are listed (lowercase versions)
        assert "Available processes:" in error_message
        assert "c215ss_jv" in error_message
        assert "bd8_xrd" in error_message

    @pytest.mark.parametrize("invalid_case", [
        "C215SS_JV",  # uppercase
        "C215ss_jv",  # mixed case
        "BD8_XRD",    # uppercase
    ])
    def test_case_sensitive_validation(self, invalid_case):
        """Test that process validation is case-insensitive."""
        validate_process(invalid_case)

    def test_valid_lowercase_process_names(self):
        """Test that lowercase abbreviated names are valid."""
        # These should pass
        validate_process("c215ss_jv")
        validate_process("bd8_xrd")
        validate_process("ftlb234_spinbox")


class TestProcessDisplayNames:
    """Test cases for process display name functions."""

    def test_get_process_display_name_valid(self):
        """Test getting display name for valid process."""
        display_name = get_process_display_name("c215ss_jv")
        assert display_name == "JV"

    def test_get_process_display_name_invalid(self):
        """Test getting display name for invalid process returns abbreviated name."""
        display_name = get_process_display_name("invalid_process")
        assert display_name == "invalid_process"

    @pytest.mark.parametrize("abbreviated,expected_display", [
        ("c215ss_jv", "JV"),
        ("bd8_xrd", "XRD"),
        ("hsem_sem", "SEM Imaging"),
        ("ftlb234_spinbox", "Spincoating"),
        ("pdil_blade", "Blade Coating"),
    ])
    def test_multiple_process_display_names(self, abbreviated, expected_display):
        """Test display names for multiple processes."""
        display_name = get_process_display_name(abbreviated)
        assert display_name == expected_display

    def test_get_tool_display_name_valid(self):
        """Test getting tool display name for valid process."""
        tool_name = get_tool_display_name("c215ss_jv")
        assert tool_name == "C215 Solar Simulator"

    def test_get_tool_display_name_invalid(self):
        """Test getting tool display name for invalid process returns abbreviated name."""
        tool_name = get_tool_display_name("invalid_process")
        assert tool_name == "invalid_process"

    @pytest.mark.parametrize("abbreviated,expected_tool", [
        ("c215ss_jv", "C215 Solar Simulator"),
        ("bd8_xrd", "BD8 X-Ray Diffractometer"),
        ("hsem_sem", "HSEM Scanning Electron Microscope"),
        ("ftlb234_spinbox", "FTLB 234 spincoating glovebox"),
        ("pdil_pct", "PDIL Perovskite Cluster Tool (PCT)"),
    ])
    def test_multiple_tool_display_names(self, abbreviated, expected_tool):
        """Test tool display names for multiple processes."""
        tool_name = get_tool_display_name(abbreviated)
        assert tool_name == expected_tool


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

    def test_color_format_valid(self):
        """Test that all colors are valid hex codes."""
        for process, color in PROCESS_COLORS.items():
            # Should be able to convert hex to RGB
            assert color.startswith("#")
            hex_part = color[1:]
            assert len(hex_part) == 6
            # Should not raise ValueError
            int(hex_part, 16)


class TestJSONDataLoading:
    """Test cases for JSON data loading."""

    def test_process_colors_loaded(self):
        """Test that PROCESS_COLORS is populated from JSON."""
        assert len(PROCESS_COLORS) > 0

    def test_expected_processes_exist(self):
        """Test that expected processes are loaded."""
        expected_processes = [
            "c215ss_jv",
            "bd8_xrd",
            "hsem_sem",
            "oeqe_eqe",
            "supss_jv",
            "pxt10_jv",
            "opprof_profil",
            "pae_evap",
            "ftlb234_spinbox",
            "pdil_pct",
        ]
        for process in expected_processes:
            assert process in PROCESS_COLORS

    def test_all_abbreviations_are_lowercase(self):
        """Test that all abbreviated names are lowercase."""
        for abbreviated in PROCESS_COLORS.keys():
            assert abbreviated == abbreviated.lower(), f"'{abbreviated}' is not lowercase"

    def test_case_insensitive_validation(self):
        """Test that process validation is case-insensitive."""
        # These should all pass (converted to lowercase internally)
        validate_process("c215ss_jv")
        validate_process("C215SS_JV")
        validate_process("C215ss_Jv")

    def test_parse_input_normalizes_process_names(self):
        """Test that parse_input converts PROCESS names to lowercase."""
        data_type, data_id = tu.parse_input("PROCESS:C215SS_JV")
        assert data_type == "PROCESS"
        assert data_id == "c215ss_jv"  # Should be lowercase

        data_type, data_id = tu.parse_input("PROCESS:Bd8_XRD")
        assert data_type == "PROCESS"
        assert data_id == "bd8_xrd"  # Should be lowercase

        # Sample IDs should preserve case
        data_type, data_id = tu.parse_input("SAMPLE:ABC123xyz")
        assert data_type == "SAMPLE"
        assert data_id == "ABC123xyz"  # Should preserve case


class TestLogFilename:
    """Test cases for log filename generation."""

    def test_log_filename_format(self):
        """Test log filename format."""
        from tracker_utils import get_log_filename

        filename = get_log_filename("c215ss_jv")
        assert filename == "scan_log_c215ss_jv.csv"

        filename = get_log_filename("bd8_xrd")
        assert filename == "scan_log_bd8_xrd.csv"

    def test_log_filename_preserves_abbreviation(self):
        """Test that log filename uses abbreviated name."""
        from tracker_utils import get_log_filename

        # Should use abbreviated name, not display name
        filename = get_log_filename("c215ss_jv")
        assert "c215ss_jv" in filename
        assert "JV Measurement" not in filename
