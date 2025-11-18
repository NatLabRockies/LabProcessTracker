"""
Shared utilities for process tracking applications.
Contains common functions and constants used by both CLI and GUI versions.
"""
import datetime
import csv
import os

# --- Constants ---
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATA_SEPARATOR = ':'
EXIT_CMD = 'EXIT'
SAVE_CMD = 'SAVE'
UNDO_CMD = 'UNDO'

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
