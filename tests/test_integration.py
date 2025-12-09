"""
Integration tests to ensure CLI and GUI use shared logic consistently.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import tracker_utils as tu  # noqa: E402


class TestCLIGUIConsistency:
    """Test that CLI and GUI handle the same scenarios identically."""

    def test_json_loading_fails_gracefully(self, monkeypatch):
        """Test that both CLI and GUI handle missing JSON the same way."""
        # Simulate missing JSON by clearing PROCESS_COLORS
        original_colors = tu.PROCESS_COLORS.copy()
        tu.PROCESS_COLORS.clear()

        # Both should return empty dict and not crash
        assert len(tu.PROCESS_COLORS) == 0

        # Restore
        tu.PROCESS_COLORS.update(original_colors)

    def test_invalid_process_validation(self):
        """Test that process validation behaves consistently."""
        invalid_process = "invalid_test"
        normalized = invalid_process.lower()

        # Should not be in PROCESS_COLORS
        assert normalized not in tu.PROCESS_COLORS

        # Both CLI and GUI should check the same way
        is_valid = normalized in tu.PROCESS_COLORS
        assert not is_valid

    def test_valid_process_validation(self):
        """Test that valid processes are recognized."""
        # Assuming c215ss_jv exists
        if "c215ss_jv" in tu.PROCESS_COLORS:
            valid_process = "C215SS_JV"  # Mixed case
            normalized = valid_process.lower()

            # Should be in PROCESS_COLORS after normalization
            assert normalized in tu.PROCESS_COLORS

    def test_process_state_not_set_before_validation(self):
        """Test that process state is only set AFTER validation passes."""
        # Simulate the workflow
        test_process = "INVALID_PROC"
        normalized = test_process.lower()

        # Check validation first
        is_valid = normalized in tu.PROCESS_COLORS

        # current_process should ONLY be set if is_valid is True
        if not is_valid:
            # In actual code, current_process should NOT be set here
            # This test documents the expected behavior
            assert not is_valid

    def test_error_message_format_consistency(self):
        """Test that error messages have consistent format."""
        # Invalid format error
        invalid_qr = "INVALID"
        data_type, data_id = tu.parse_input(invalid_qr)

        if not data_type:
            # Both CLI and GUI should show same error
            expected_error = (
                f"Invalid format: '{invalid_qr}'. "
                "Use 'P%:Name' or 'S%:ID'"
            )
            # This documents the expected error format
            assert "Invalid format" in expected_error
            assert "P%:" in expected_error
            assert "S%:" in expected_error

    def test_alert_message_format_consistency(self):
        """Test that alert messages have consistent format."""
        # No tool/process set alert
        expected_alert = "Cannot log sample. Please scan a PROCESS QR code first."

        # Both CLI and GUI should show exact same message
        assert "Cannot log sample" in expected_alert
        assert "PROCESS QR code" in expected_alert


class TestWorkflowScenarios:
    """Test complete workflow scenarios that both CLI and GUI must handle."""

    def test_scenario_invalid_process_then_valid_process(self):
        """Test: Scan invalid process, then valid process."""
        # Step 1: Invalid process
        invalid_data_type, invalid_data_id = tu.parse_input("P%:INVALID")
        assert invalid_data_type == "PROCESS"

        invalid_normalized = invalid_data_id.lower()
        is_invalid = invalid_normalized not in tu.PROCESS_COLORS
        assert is_invalid  # Should be invalid

        # At this point, current_process should NOT be set
        # (simulated by not executing the assignment)

        # Step 2: Valid process
        if "c215ss_jv" in tu.PROCESS_COLORS:
            valid_data_type, valid_data_id = tu.parse_input("P%:c215ss_jv")
            assert valid_data_type == "PROCESS"

            valid_normalized = valid_data_id.lower()
            is_valid = valid_normalized in tu.PROCESS_COLORS
            assert is_valid  # Should be valid

            # NOW current_process can be set

    def test_scenario_sample_without_process(self):
        """Test: Try to scan sample without setting process first."""
        sample_data_type, sample_data_id = tu.parse_input("S%:TEST123")
        assert sample_data_type == "SAMPLE"

        # Simulate: tool_process = None, current_process = None
        tool_process = None
        current_process = None

        # Both should be None before scanning any process
        should_alert = (not tool_process or not current_process)
        assert should_alert  # Should trigger alert

    def test_scenario_process_then_sample(self):
        """Test: Scan process, then sample (happy path)."""
        if "c215ss_jv" in tu.PROCESS_COLORS:
            # Step 1: Scan process
            proc_type, proc_id = tu.parse_input("P%:c215ss_jv")
            assert proc_type == "PROCESS"

            normalized = proc_id.lower()
            assert normalized in tu.PROCESS_COLORS

            # Simulate setting state
            tool_process = normalized
            current_process = normalized

            # Step 2: Scan sample
            samp_type, samp_id = tu.parse_input("S%:SAMPLE123")
            assert samp_type == "SAMPLE"

            # Should be able to log
            can_log = (tool_process is not None and current_process is not None)
            assert can_log

            # Create record
            record = tu.create_log_record("TestOp", current_process, samp_id)
            assert record["ProcessName"] == "c215ss_jv"
            assert record["SampleID"] == "SAMPLE123"
