"""
Shared utilities for process tracking applications.
Contains common functions and constants used by both CLI and GUI versions.
"""
import datetime
import csv
import os
import sys

# --- Constants ---
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATA_SEPARATOR = ':'
EXIT_CMD = 'EXIT'
SAVE_CMD = 'SAVE'
UNDO_CMD = 'UNDO'
RESET_OPERATOR_CMD = 'RESET'

# --- Process Color Mappings ---
# Default color for unknown processes
DEFAULT_PROCESS_COLOR = "#95a5a6"  # Grey

# Map process names to colors (hex codes for GUI)
PROCESS_COLORS = {
    "C215SS_JV": "#e74c3c",         # Red
    "BD8_XRD": "#f39c12",           # Orange
    "HSEM_SEM": "#9b59b6",          # Purple
    "OEQE_EQE": "#3498db",          # Blue
    "SUPSS_JV": "#1abc9c",          # Turquoise
    "PXT10_JV": "#2ecc71",          # Green
    "OpProf_PROFIL": "#fdca24",     # Yellow
    "PAE_EVAP": "#fe27ba",          # Pink

}

def get_process_color(process_name: str) -> str:
    """Get the color assigned to a specific process.

    Args:
        process_name: Name of the process

    Returns:
        Hex color code for the process
    """
    return PROCESS_COLORS.get(process_name, DEFAULT_PROCESS_COLOR)

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

    Args:
        process_name: Name of the process to validate

    Raises:
        ValueError: If the process name is not in PROCESS_COLORS
    """
    if process_name not in PROCESS_COLORS:
        error_msg = (
            f"Process '{process_name}' is not implemented in this system.\n"
            f"Available processes: {', '.join(PROCESS_COLORS.keys())}\n"
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

    Args:
        qr_text: The QR code text in format 'TYPE:ID'

    Returns:
        Tuple of (data_type, data_id) or (None, None) if invalid
    """
    try:
        parts = qr_text.strip().split(DATA_SEPARATOR, 1)
        if len(parts) == 2:
            data_type = parts[0].strip().upper()
            data_id = parts[1].strip()
            return data_type, data_id
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
        f"Use 'TYPE{DATA_SEPARATOR}ID' "
        "(e.g., PROCESS:Name or SAMPLE:ID)."
    )

def get_unknown_type_error(data_type: str) -> str:
    """Get error message for unknown data type.

    Args:
        data_type: The unknown data type

    Returns:
        Formatted error message
    """
    return f"Unknown data type scanned: '{data_type}'. Must be 'PROCESS' or 'SAMPLE'."
