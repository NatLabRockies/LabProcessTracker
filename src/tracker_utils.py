"""
Shared utilities for process tracking applications.
Contains common functions and constants used by both CLI and GUI versions.
"""
import datetime
import csv
import os
import sys
import json
import re

# --- Constants ---
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
# QR Code Prefixes (compact format for easier printing)
QR_SAMPLE_PREFIX = 'S%:'
QR_PROCESS_PREFIX = 'P%:'
EXIT_CMD = 'EXIT'
SAVE_CMD = 'SAVE'
UNDO_CMD = 'UNDO'
RESET_OPERATOR_CMD = 'RESET'

# --- Process Color Mappings ---
# Default color for unknown processes
DEFAULT_PROCESS_COLOR = "#95a5a6"  # Grey

# Map process names to colors (hex codes for GUI) - loaded from JSON
PROCESS_COLORS = {}
PROCESS_INFO = {}  # Full process information

UNAPPROVED_FOLDER_NAME = "unapproved"


def load_process_data():
    """Load process and tool data from JSON file."""
    global PROCESS_COLORS, PROCESS_INFO

    # Determine base path - handles both script and PyInstaller .exe
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    json_path = os.path.join(base_path, "tools_processes.json")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for tool in data.get('tools', []):
            abbreviated = tool.get('abbreviated', '')
            if abbreviated:
                PROCESS_COLORS[abbreviated] = tool.get('color', DEFAULT_PROCESS_COLOR)
                PROCESS_INFO[abbreviated] = {
                    'tool': tool.get('tool', ''),
                    'process': tool.get('process', ''),
                    'color': tool.get('color', DEFAULT_PROCESS_COLOR)
                }
    except FileNotFoundError:
        print(f"Warning: tools_processes.json not found at {json_path}")
        print("Using default/empty process configuration.")
    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing tools_processes.json: {e}")
        print("Using default/empty process configuration.")

# Load process data at module import
load_process_data()


def get_unapproved_log_filename(process_name: str) -> str:
    """Generate the quarantine log filename for unapproved processes."""
    return f"scan_log_UNAPPROVED_{process_name}.csv"


def get_unapproved_output_dir(base_outputs: str) -> str:
    """Get the quarantine folder for unapproved process logs."""
    return os.path.join(base_outputs, UNAPPROVED_FOLDER_NAME)


def is_process_valid(process_name: str) -> bool:
    """Check if a process is valid (exists in JSON)."""
    return process_name in PROCESS_COLORS


def get_process_color(process_name: str) -> str:
    """Get color for process, default if invalid."""
    if is_process_valid(process_name):
        return PROCESS_COLORS.get(process_name, DEFAULT_PROCESS_COLOR)
    else:
        return DEFAULT_PROCESS_COLOR


def get_process_info(process_name: str) -> dict:
    """Get info for process, empty dict if invalid."""
    if is_process_valid(process_name):
        return PROCESS_INFO.get(process_name, {})
    else:
        return {}


def get_log_filename(process_name: str, valid: bool = True) -> str:
    """Get log filename, quarantine if invalid."""
    if valid:
        return f"scan_log_{process_name}.csv"
    else:
        return get_unapproved_log_filename(process_name)


def get_output_dir(process_name: str, base_outputs: str) -> str:
    """Get output dir, quarantine if invalid."""
    if is_process_valid(process_name):
        return base_outputs
    else:
        return get_unapproved_output_dir(base_outputs)


# --- Output Directory Logic ---
def get_default_output_dir():
    """Determine the appropriate output directory for log files."""
    project_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    project_outputs = os.path.join(project_root, "outputs")
    # Check if running from a temp directory (PyInstaller .exe)
    temp_dirs = [os.environ.get('TEMP'), os.environ.get('TMP')]
    is_temp = any(
        project_root.lower().startswith(td.lower())
        for td in temp_dirs if td
    )
    if os.path.isdir(project_outputs) and not is_temp:
        return project_outputs
    # Fallback to user's Documents
    user_docs = os.path.expanduser(
        r"~\Documents\process_tracking_outputs"
    )
    return user_docs


# --- Input Parsing ---
def parse_input(qr_text: str) -> tuple[str, str] | tuple[None, None]:
    """Parse QR code text to determine type and ID.

    Supports compact QR prefixes (S%:ID, P%:ID) and legacy format
    (####-##).

    Args:
        qr_text: The QR code text in format 'TYPE:ID', where TYPE is
                 one of 'S%' or 'P%'
                 OR legacy format ####-## (4 digits, dash, 2 digits)

    Returns:
        Tuple of ('SAMPLE', sample_id) or ('PROCESS', process_id) or
        (None, None) if invalid
    """
    try:
        qr_text = qr_text.strip()

        # Check for compact QR prefixes (include colon for uniqueness)
        if qr_text.startswith(QR_SAMPLE_PREFIX):
            data_id = qr_text[len(QR_SAMPLE_PREFIX):].strip()
            if data_id:  # Ensure there's an ID after the prefix
                return "SAMPLE", data_id
        elif qr_text.startswith(QR_PROCESS_PREFIX):
            data_id = qr_text[len(QR_PROCESS_PREFIX):].strip()
            if data_id:  # Ensure there's an ID after the prefix
                return "PROCESS", data_id

        # Legacy format: ####-## (4 digits, dash, 2 digits)
        # This supports old sample QR codes that don't have the S%: prefix
        if re.match(r'^\d{4}-\d{2}$', qr_text):
            return "SAMPLE_LEGACY", qr_text

        return None, None
    except Exception:
        return None, None


# --- Logging Functions ---
def create_log_record(operator_name: str, process_name: str, sample_id: str) -> dict:
    """Create a log record dictionary with current timestamp.

    Args:
        operator_name: Name of the operator
        process_name: Name of the process
        sample_id: ID of the sample

    Returns:
        Dictionary containing the log record
    """
    scan_time = datetime.datetime.now().strftime(DATE_FORMAT)
    return {
        'Timestamp': scan_time,
        'Operator': operator_name,
        'ProcessName': process_name,
        'SampleID': sample_id,
    }


def save_log_to_csv(
    log_records: list, log_file: str, outputs_folder: str
) -> tuple[bool, str]:
    """Save log records to CSV file.

    Args:
        log_records: List of log record dictionaries
        log_file: Path to the log file
        outputs_folder: Path to the outputs folder

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not log_records:
        return False, "No records to save."

    # Ensure the outputs folder exists
    os.makedirs(outputs_folder, exist_ok=True)

    # Check if file exists to decide whether to write headers
    file_exists = os.path.exists(log_file)
    fieldnames = list(log_records[0].keys())

    try:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerows(log_records)

        return (
            True,
            f"Successfully saved {len(log_records)} records to {log_file}."
        )
    except Exception as e:
        return False, f"Could not save log to file: {e}"


# --- Operator Management ---
def validate_operator_name(name: str) -> tuple[bool, str]:
    """Validate an operator name.

    Args:
        name: The operator name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str or empty string)
    """
    name = name.strip()
    if not name:
        return False, "Operator name cannot be empty."
    if len(name) < 2:
        return False, "Operator name must be at least 2 characters."
    if len(name) > 50:
        return False, "Operator name must be less than 50 characters."
    return True, ""


# --- Session State Helpers ---
def get_unsaved_count(log_records: list) -> int:
    """Get count of unsaved log records.

    Args:
        log_records: List of log record dictionaries

    Returns:
        Number of unsaved records
    """
    return len(log_records)


# --- Runtime Environment ---
def is_running_as_exe() -> bool:
    """Check if the script is running as a compiled executable.

    Returns:
        True if running as .exe, False if running as .py script
    """
    return getattr(sys, 'frozen', False)


def format_log_message(record: dict) -> str:
    """Format a log record into a human-readable message.

    Args:
        record: Log record dictionary

    Returns:
        Formatted log message string
    """
    return (
        f"[LOGGED] {record['Timestamp']} | "
        f"Operator: '{record['Operator']}' | "
        f"Process: '{record['ProcessName']}' | "
        f"Sample: '{record['SampleID']}'"
    )


def format_undo_message(record: dict) -> str:
    """Format an undo message for a log record.

    Args:
        record: Log record dictionary that was undone

    Returns:
        Formatted undo message string
    """
    return (
        f"[UNDO] Removed last scan: {record['Timestamp']} | "
        f"Process: '{record['ProcessName']}' | "
        f"Sample: '{record['SampleID']}'"
    )


def format_legacy_sample_warning(sample_id: str) -> str:
    """Format a warning message for legacy sample format detection.

    Args:
        sample_id: The legacy sample ID that was detected

    Returns:
        Formatted warning message string
    """
    return f"[WARNING] Legacy sample format detected: {sample_id}"


def should_auto_save_on_process_switch(
    current_tool: str, new_process: str, has_records: bool
) -> bool:
    """Check if auto-save should occur when switching processes.

    Args:
        current_tool: The currently active tool/process (tool_process)
        new_process: The new process being switched to
        has_records: Whether there are unsaved records

    Returns:
        True if auto-save should occur, False otherwise
    """
    # Only auto-save if:
    # 1. We have a current tool set (not first process)
    # 2. The new process is different from current tool
    # 3. We have unsaved records
    return (
        current_tool is not None
        and new_process != current_tool
        and has_records
    )


def format_auto_save_message(count: int, filename: str) -> str:
    """Format message for auto-save notification.

    Args:
        count: Number of records that were auto-saved
        filename: Name of the file records were saved to

    Returns:
        Formatted auto-save notification message
    """
    return f"[AUTO-SAVE] Saved {count} record(s) to {filename}"


# --- Error Messages ---
def get_process_display_name(abbreviated_name: str) -> str:
    """Get the human-readable process name for display.

    Args:
        abbreviated_name: The abbreviated process name
                          (e.g., 'ftlb234_spinbox')

    Returns:
        Human-readable process name (e.g., 'Spincoating') or
        abbreviated name if not found
    """
    info = PROCESS_INFO.get(abbreviated_name, {})
    return info.get('process', abbreviated_name)


def get_tool_display_name(abbreviated_name: str) -> str:
    """Get the human-readable tool name for display.

    Args:
        abbreviated_name: The abbreviated process name
                          (e.g., 'ftlb234_spinbox')

    Returns:
        Human-readable tool name (e.g., 'FTLB 234 spincoating glovebox')
        or abbreviated name if not found
    """
    info = PROCESS_INFO.get(abbreviated_name, {})
    return info.get('tool', abbreviated_name)


def validate_and_normalize_process(
    process_input: str
) -> tuple[bool, str, str]:
    """Validate process input and normalize to lowercase.

    This function centralizes the validation logic used by both CLI
    and GUI.

    Args:
        process_input: Raw process input from QR code

    Returns:
        Tuple of (is_valid, normalized_process, error_message)
        - is_valid: True if process exists in PROCESS_COLORS
        - normalized_process: Lowercase normalized process name
        - error_message: Error message if invalid, empty string if valid
    """
    normalized = process_input.lower()
    if normalized not in PROCESS_COLORS:
        error_msg = (
            f"[WARNING] Process '{process_input}' is not implemented "
            "and will be quarantined.\n"
            "Records will be saved to a separate quarantine log file.\n"
            "Contact Rajiv.Daxini@nrel.gov to add this process to "
            "the database."
        )
        return False, normalized, error_msg
    return True, normalized, ""


def is_command(qr_text: str) -> tuple[bool, str | None]:
    """Check if input is a command and return the command type.

    Args:
        qr_text: Input text to check

    Returns:
        Tuple of (is_command, command_type)
        - is_command: True if text is a valid command
        - command_type: One of EXIT_CMD, SAVE_CMD, UNDO_CMD, RESET_OPERATOR_CMD, or None
    """
    qr_upper = qr_text.upper()

    if qr_upper == EXIT_CMD:
        return True, EXIT_CMD
    elif qr_upper == SAVE_CMD:
        return True, SAVE_CMD
    elif qr_upper == UNDO_CMD:
        return True, UNDO_CMD
    elif qr_upper == RESET_OPERATOR_CMD:
        return True, RESET_OPERATOR_CMD
    else:
        return False, None
