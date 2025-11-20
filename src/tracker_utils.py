"""
Shared utilities for process tracking applications.
Contains common functions and constants used by both CLI and GUI versions.
"""
import datetime
import csv
import os
import sys
import json

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

def load_process_data():
    """Load process and tool data from JSON file."""
    global PROCESS_COLORS, PROCESS_INFO

    # JSON file is always in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(project_root, "tools_processes.json")

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

def get_process_color(process_name: str) -> str:
    """Get the color assigned to a specific process.

    Args:
        process_name: Name of the process

    Returns:
        Hex color code for the process
    """
    return PROCESS_COLORS.get(process_name, DEFAULT_PROCESS_COLOR)

def get_process_info(process_name: str) -> dict:
    """Get full information for a specific process.

    Args:
        process_name: Name of the process

    Returns:
        Dictionary containing process information, or empty dict if not found
    """
    return PROCESS_INFO.get(process_name, {})

def get_log_filename(process_name: str) -> str:
    """Generate the log filename for a specific process.

    Args:
        process_name: Name of the process

    Returns:
        Filename in format 'scan_log_PROCESSNAME.csv'
    """
    return f"scan_log_{process_name}.csv"

def parse_tool_process(process_name: str) -> tuple[str, str]:
    """Parse a process name into tool and process components.

    Args:
        process_name: Full process name (e.g., 'C215SS_JV' or 'BD8_XRD')

    Returns:
        Tuple of (tool_name, process_name)
        If no underscore found, returns (process_name, process_name)
    """
    if '_' in process_name:
        parts = process_name.split('_', 1)
        return parts[0], parts[1]
    return process_name, process_name

def get_tool_name(process_name: str) -> str:
    """Extract the tool name from a full process identifier.

    Args:
        process_name: Full process name (e.g., 'C215SS_JV')

    Returns:
        Tool name (e.g., 'C215SS')
    """
    tool, _ = parse_tool_process(process_name)
    return tool

def get_process_name(process_name: str) -> str:
    """Extract the process name from a full process identifier.

    Args:
        process_name: Full process name (e.g., 'C215SS_JV')

    Returns:
        Process name (e.g., 'JV')
    """
    _, process = parse_tool_process(process_name)
    return process

def validate_process(process_name: str) -> None:
    """Validate that a process name is in the approved list.

    Validation is case-insensitive - input is converted to lowercase.

    Args:
        process_name: Name of the process to validate

    Raises:
        ValueError: If the process name is not in PROCESS_COLORS
    """
    # Convert to lowercase for case-insensitive comparison
    process_name_lower = process_name.lower()

    if process_name_lower not in PROCESS_COLORS:
        error_msg = (
            f"Process '{process_name}' is not implemented in this system.\n"
            f"Available processes: {', '.join(sorted(PROCESS_COLORS.keys()))}\n"
            f"If you need to add this process, please contact Dax (Rajiv.Daxini@nrel.gov)"
        )
        raise ValueError(error_msg)

# --- Output Directory Logic ---
def get_default_output_dir():
    """Determine the appropriate output directory for log files."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_outputs = os.path.join(project_root, "outputs")
    # Check if running from a temp directory (PyInstaller .exe)
    temp_dirs = [os.environ.get('TEMP'), os.environ.get('TMP')]
    is_temp = any(project_root.lower().startswith(td.lower()) for td in temp_dirs if td)
    if os.path.isdir(project_outputs) and not is_temp:
        return project_outputs
    # Fallback to user's Documents
    user_docs = os.path.expanduser(r"~\Documents\process_tracking_outputs")
    return user_docs

# --- Input Parsing ---
def parse_input(qr_text: str) -> tuple[str, str] | tuple[None, None]:
    """Parse QR code text to determine type and ID.

    Supports compact QR format (S%:ID, P%:ID).

    Args:
        qr_text: The QR code text in format 'TYPE:ID', where TYPE is one of 'S%' or 'P%'

    Returns:
        Tuple of ('SAMPLE', sample_id) or ('PROCESS', process_id) or (None, None) if
        invalid
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

def save_log_to_csv(log_records: list, log_file: str, outputs_folder: str) -> tuple[bool, str]:
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

        return True, f"Successfully saved {len(log_records)} records to {log_file}."
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
def has_unsaved_data(log_records: list) -> bool:
    """Check if there are unsaved log records.

    Args:
        log_records: List of log record dictionaries

    Returns:
        True if there are unsaved records, False otherwise
    """
    return len(log_records) > 0

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

# --- Error Messages ---
def get_no_tool_alert() -> str:
    """Get the alert message for when no tool is set.

    Returns:
        Alert message string
    """
    return "Cannot log sample. Please scan a **PROCESS QR code** first to set the tool."

def get_no_process_alert() -> str:
    """Get the alert message for when no process is active.

    Returns:
        Alert message string
    """
    return "Cannot log sample. Please scan a **PROCESS QR code** first to define the current step."

def get_invalid_format_error(qr_text: str) -> str:
    """Get error message for invalid QR code format.

    Args:
        qr_text: The invalid QR code text

    Returns:
        Formatted error message
    """
    return (
        f"Invalid format: '{qr_text}'. "
        f"Use '{QR_PROCESS_PREFIX}Name' or '{QR_SAMPLE_PREFIX}ID' "
        f"(e.g., {QR_PROCESS_PREFIX}ftlb234_spinbox or {QR_SAMPLE_PREFIX}ABC123)."
    )

def get_unknown_type_error(data_type: str) -> str:
    """Get error message for unknown data type.

    Args:
        data_type: The unknown data type

    Returns:
        Formatted error message
    """
    return f"Unknown data type scanned: '{data_type}'. Must be 'PROCESS' or 'SAMPLE'."

def get_process_display_name(abbreviated_name: str) -> str:
    """Get the human-readable process name for display.

    Args:
        abbreviated_name: The abbreviated process name (e.g., 'ftlb234_spinbox')

    Returns:
        Human-readable process name (e.g., 'Spincoating') or abbreviated name if not found
    """
    info = PROCESS_INFO.get(abbreviated_name, {})
    return info.get('process', abbreviated_name)

def get_tool_display_name(abbreviated_name: str) -> str:
    """Get the human-readable tool name for display.

    Args:
        abbreviated_name: The abbreviated process name (e.g., 'ftlb234_spinbox')

    Returns:
        Human-readable tool name (e.g., 'FTLB 234 spincoating glovebox') or abbreviated name if not found
    """
    info = PROCESS_INFO.get(abbreviated_name, {})
    return info.get('tool', abbreviated_name)
