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

    def test_parse_input_preserves_case(self):
        """Test that parse_input preserves case in IDs."""
        data_type, data_id = tu.parse_input("P%:C215SS_JV")
        assert data_type == "PROCESS"
        assert data_id == "C215SS_JV"  # parse_input preserves case

        data_type, data_id = tu.parse_input("S%:ABC123xyz")
        assert data_type == "SAMPLE"
        assert data_id == "ABC123xyz"  # Case preserved
