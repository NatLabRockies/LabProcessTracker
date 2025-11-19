"""
Unit tests for tracker_utils module using pytest.
"""
import sys
import os
import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tracker_utils import validate_process, PROCESS_COLORS


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
        # Check that at least some of the valid processes are listed
        assert "Available processes:" in error_message
        assert "C215SS_JV" in error_message
        assert "BD8_XRD" in error_message

    @pytest.mark.parametrize("invalid_case", [
        "c215ss_jv",  # lowercase
        "C215SS_jv",  # mixed case
        "bd8_xrd",    # lowercase
    ])
    def test_case_sensitive_validation(self, invalid_case):
        """Test that process names are case-sensitive."""
        # These should fail because they're not exact matches
        with pytest.raises(ValueError):
            validate_process(invalid_case)
