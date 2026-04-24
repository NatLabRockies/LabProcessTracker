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
QR_BATCH_PREFIX = 'B%:'
EXIT_CMD = 'EXIT'
SAVE_CMD = 'SAVE'
UNDO_CMD = 'UNDO'
RESET_USER_CMD = 'RESET'

# --- Process Color Mappings ---
# Default color for unknown processes
DEFAULT_PROCESS_COLOR = "#95a5a6"  # Grey

# Map process names to colors (hex codes for GUI) - loaded from JSON
PROCESS_COLORS = {}
PROCESS_INFO = {}  # Full process information
TRAY_LAYOUTS = {}  # Tray position mappings - loaded from JSON

UNAPPROVED_FOLDER_NAME = "unapproved"


def load_process_data():
    """Load process and tool data from JSON file."""
    global PROCESS_COLORS, PROCESS_INFO

    # Determine base path - handles both script and PyInstaller .exe
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
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
                    'process': tool.get('notes', ''),
                    'color': tool.get('color', DEFAULT_PROCESS_COLOR),
                    'is_batch_operation': tool.get('is_batch_operation', False)
                }
    except FileNotFoundError:
        print(f"Warning: tools_processes.json not found at {json_path}")
        print("Using default/empty process configuration.")
    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing tools_processes.json: {e}")
        print("Using default/empty process configuration.")


def load_tray_data():
    """Load tray layout data from JSON file."""
    global TRAY_LAYOUTS

    # Determine base path - handles both script and PyInstaller .exe
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # Running as script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    json_path = os.path.join(base_path, "tray_layouts.json")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for tray in data.get('trays', []):
            tray_id = tray.get('tray_id', '')
            if tray_id:
                TRAY_LAYOUTS[tray_id] = tray.get('positions', [])
    except FileNotFoundError:
        print(f"Warning: tray_layouts.json not found at {json_path}")
        print("Tray tracking will not be available.")
    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing tray_layouts.json: {e}")
        print("Tray tracking will not be available.")


# Load process and tray data at module import
load_process_data()
load_tray_data()


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


def is_batch_operation_process(process_name: str) -> bool:
    """Check if a process is a batch operation (applies to multiple trays).

    Args:
        process_name: The abbreviated process name

    Returns:
        True if process is marked as batch operation
    """
    info = PROCESS_INFO.get(process_name, {})
    return info.get('is_batch_operation', False)


def generate_session_id() -> str:
    """Generate a unique session ID for batch operations.

    Returns:
        Session ID string in format YYYYMMDD_HHMMSS
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


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

    Supports compact QR prefixes (S%:ID, P%:ID, B%:ID) and legacy format
    (####-##).

    Args:
        qr_text: The QR code text in format 'TYPE:ID', where TYPE is
                 one of 'S%', 'P%', or 'B%'
                 OR legacy format ####-## (4 digits, dash, 2 digits)

    Returns:
        Tuple of ('SAMPLE', sample_id) or ('PROCESS', process_id) or
        ('BATCH', batch_id) or (None, None) if invalid
    """
    try:
        qr_text = qr_text.strip()

        # Check for compact QR prefixes (include colon for uniqueness)
        if qr_text.startswith(QR_SAMPLE_PREFIX):
            data_id = qr_text[len(QR_SAMPLE_PREFIX):]
            if data_id:  # Ensure there's an ID after the prefix
                return "SAMPLE", data_id
        elif qr_text.startswith(QR_PROCESS_PREFIX):
            data_id = qr_text[len(QR_PROCESS_PREFIX):]
            if data_id:  # Ensure there's an ID after the prefix
                return "PROCESS", data_id
        elif qr_text.startswith(QR_BATCH_PREFIX):
            data_id = qr_text[len(QR_BATCH_PREFIX):].strip()
            if data_id:  # Ensure there's an ID after the prefix
                return "BATCH", data_id
        elif qr_text.startswith("T%:"):
            data_id = qr_text[len("T%:"):]
            if data_id:
                return "TRAY", data_id

        # Legacy format: ####-## (4 digits, dash, 2 digits)
        # This supports old sample QR codes that don't have the S%: prefix
        if re.match(r'^\d{4}-\d{2}$', qr_text):
            return "SAMPLE_LEGACY", qr_text

        return None, None
    except Exception:
        return None, None


# --- Logging Functions ---
def create_log_record(
    username: str,
    process_name: str,
    sample_id: str = "",
    batch_id: str = ""
) -> dict:
    """Create a log record dictionary with current timestamp.

    Args:
        username: Name of the user
        process_name: Name of the process
        sample_id: ID of the sample (empty if batch)
        batch_id: ID of the batch (empty if sample)

    Returns:
        Dictionary containing the log record
    """
    scan_time = datetime.datetime.now().strftime(DATE_FORMAT)
    return {
        'Timestamp': scan_time,
        'User': username,
        'ProcessName': process_name,
        'SampleID': sample_id,
        'BatchID': batch_id,
    }


def create_log_record_with_tray(
    username: str,
    tray_id: str,
    position: str,
    sample_id: str,
    process_name: str,
    session_id: str = ""
) -> dict:
    """Create a log record with tray and position info.

    Args:
        username: Name of the user
        tray_id: ID of the tray
        position: Position in the tray (e.g., 'A1', 'B2')
        sample_id: ID of the sample
        process_name: Name of the process
        session_id: Optional session ID for batch operations

    Returns:
        Dictionary containing the log record with tray info
    """
    scan_time = datetime.datetime.now().strftime(DATE_FORMAT)
    record = {
        'Timestamp': scan_time,
        'User': username,
        'SampleID': sample_id,
        'ProcessName': process_name,
        'TrayID': tray_id,
        'Position': position,
    }
    if session_id:
        record['SessionID'] = session_id
    return record


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

    # Determine fieldnames based on what's present in records
    # Standard fields first, optional fields (TrayID, Position, SessionID) at end
    has_tray = any(('TrayID' in r) for r in log_records)
    has_session = any(('SessionID' in r) for r in log_records)

    # Base fieldnames (always present)
    fieldnames = ['Timestamp', 'User', 'SampleID', 'ProcessName']

    # Add optional fields at the end
    if has_tray:
        fieldnames.extend(['TrayID', 'Position'])
    if has_session:
        fieldnames.append('SessionID')

    try:
        with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=fieldnames, extrasaction='ignore'
            )

            if not file_exists:
                writer.writeheader()

            writer.writerows(log_records)

        return (
            True,
            f"Successfully saved {len(log_records)} records to {log_file}."
        )
    except Exception as e:
        return False, f"Could not save log to file: {e}"


# --- User Management ---
def validate_username(name: str) -> tuple[bool, str]:
    """Validate a user name.

    Args:
        name: The user name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str or empty string)
    """
    name = name.strip()
    if not name:
        return False, "User name cannot be empty."
    if len(name) < 2:
        return False, "User name must be at least 2 characters."
    if len(name) > 50:
        return False, "User name must be less than 50 characters."
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


def _format_data_id(record: dict) -> str:
    """Helper to format either batch or sample ID for display.

    Args:
        record: Log record dictionary

    Returns:
        Formatted string like "Batch: 'ID'" or "Sample: 'ID'"
    """
    if record.get('BatchID'):
        return f"Batch: '{record['BatchID']}'"
    else:
        return f"Sample: '{record['SampleID']}'"


def format_log_message(record: dict) -> str:
    """Format a log record into a human-readable message.

    Args:
        record: Log record dictionary

    Returns:
        Formatted log message string
    """
    msg = f"[LOGGED] {record['Timestamp']} | User: '{record['User']}'"

    # Add tray info if present
    if 'TrayID' in record and 'Position' in record:
        msg += f" | Tray: '{record['TrayID']}' | Pos: '{record['Position']}'"

    # Add batch or sample, then process
    msg += f" | {_format_data_id(record)} | Process: '{record['ProcessName']}'"

    # Add session ID if present
    if 'SessionID' in record:
        msg += f" | Session: {record['SessionID']}"

    return msg


def format_undo_message(record: dict) -> str:
    """Format an undo message for a log record.

    Args:
        record: Log record dictionary that was undone

    Returns:
        Formatted undo message string
    """
    base_msg = (
        f"[UNDO] Removed last scan: {record['Timestamp']} | "
        f"Process: '{record['ProcessName']}' | "
    )
    return base_msg + _format_data_id(record)


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
            "Contact Rajiv.Daxini@nlr.gov to add this process to "
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
        - command_type: One of EXIT_CMD, SAVE_CMD, UNDO_CMD, RESET_USER_CMD, or None
    """
    qr_upper = qr_text.upper()

    if qr_upper == EXIT_CMD:
        return True, EXIT_CMD
    elif qr_upper == SAVE_CMD:
        return True, SAVE_CMD
    elif qr_upper == UNDO_CMD:
        return True, UNDO_CMD
    elif qr_upper == RESET_USER_CMD:
        return True, RESET_USER_CMD
    else:
        return False, None


def is_sample_type(scan_type: str) -> bool:
    """Check if scan type is a sample (including legacy).

    Args:
        scan_type: The scan type from parse_input()

    Returns:
        True if scan type represents a sample
    """
    return scan_type in ("SAMPLE", "SAMPLE_LEGACY")


def is_batch_type(scan_type: str) -> bool:
    """Check if scan type is a batch.

    Args:
        scan_type: The scan type from parse_input()

    Returns:
        True if scan type represents a batch
    """
    return scan_type == "BATCH"


def is_data_type(scan_type: str) -> bool:
    """Check if scan type is data (sample or batch) vs process.

    Args:
        scan_type: The scan type from parse_input()

    Returns:
        True if scan type is SAMPLE, SAMPLE_LEGACY, or BATCH
    """
    return is_sample_type(scan_type) or is_batch_type(scan_type)


# --- Tray Mode Logic ---
def validate_tray_ready_for_process(
    tray_position_index: int, total_positions: int
) -> tuple[bool, str]:
    """Check if tray is ready for process assignment.

    Args:
        tray_position_index: Current position index
        total_positions: Total number of positions in tray

    Returns:
        Tuple of (is_ready: bool, error_message: str or empty string)
    """
    if tray_position_index < total_positions:
        return (
            False,
            "[ERROR] Complete all tray positions or skip remaining "
            "before scanning process."
        )
    return True, ""


def should_accept_scan_in_tray_mode(
    data_type: str, tray_position_index: int, total_positions: int
) -> tuple[bool, str]:
    """Determine if a scan should be accepted in tray mode.

    Args:
        data_type: Type of scan ("SAMPLE", "SAMPLE_LEGACY", "PROCESS", etc.)
        tray_position_index: Current position index
        total_positions: Total number of positions in tray

    Returns:
        Tuple of (should_accept: bool, error_message: str or empty string)
    """
    if data_type in ("SAMPLE", "SAMPLE_LEGACY"):
        # Always accept samples in tray mode
        return True, ""
    elif data_type == "PROCESS":
        # Only accept process if all positions are filled/skipped
        return validate_tray_ready_for_process(
            tray_position_index, total_positions
        )
    else:
        return (
            False,
            "[ERROR] In tray mode, only SAMPLE or PROCESS QR codes "
            "are accepted."
        )


def create_tray_batch_records(
    username: str,
    tray_id: str,
    tray_samples: list,
    process_name: str
) -> list:
    """Create log records for all samples in a tray with the assigned process.

    Args:
        username: Name of the user
        tray_id: ID of the tray
        tray_samples: List of dicts with 'position' and 'sample_id' keys
        process_name: Name of the process to assign

    Returns:
        List of log record dictionaries
    """
    records = []
    for entry in tray_samples:
        record = create_log_record_with_tray(
            username,
            tray_id,
            entry["position"],
            entry["sample_id"],
            process_name
        )
        records.append(record)
    return records


def create_batch_operation_records(
    username: str,
    all_tray_data: dict,
    process_name: str,
    session_id: str
) -> list:
    """Create log records for all samples across multiple trays for batch operations.

    Args:
        username: Name of the user
        all_tray_data: Dict mapping {tray_id: [{"position": pos, "sample_id": id}, ...]}
        process_name: Name of the batch operation process
        session_id: Session ID linking all trays together

    Returns:
        List of log record dictionaries with session ID
    """
    records = []
    for tray_id, samples_list in all_tray_data.items():
        for entry in samples_list:
            record = create_log_record_with_tray(
                username,
                tray_id,
                entry["position"],
                entry["sample_id"],
                process_name,
                session_id
            )
            records.append(record)
    return records


# --- Checkout Logic ---
def generate_consecutive_sample_ids(start_id: str, count: int) -> list[str]:
    """Generate consecutive sample IDs starting from start_id.

    Parses IDs in the format <prefix>-<NNN> where NNN is a zero-padded numeric
    suffix. The original padding width is preserved in all generated IDs.

    Args:
        start_id: Starting sample ID (e.g. '2503-015')
        count: Number of IDs to generate (>= 1)

    Returns:
        List of count sample ID strings

    Raises:
        ValueError: If start_id has no '-' separator, suffix is non-numeric,
                    count < 1, or the range would overflow the suffix padding.
    """
    if count < 1:
        raise ValueError(f"Count must be at least 1, got {count}.")
    parts = start_id.rsplit("-", 1)
    if len(parts) != 2 or not parts[1]:
        raise ValueError(
            f"Sample ID '{start_id}' must contain a '-' separator with a "
            "numeric suffix (e.g. '2503-015')."
        )
    prefix, suffix = parts
    if not suffix.isdigit():
        raise ValueError(
            f"Suffix '{suffix}' in '{start_id}' is not numeric. "
            "Expected format: prefix-NNN (e.g. '2503-015')."
        )
    pad_len = len(suffix)
    start_num = int(suffix)
    max_num = (10 ** pad_len) - 1
    if start_num + count - 1 > max_num:
        raise ValueError(
            f"Range overflow: '{start_id}' + {count} samples would exceed "
            f"maximum suffix value {max_num} for {pad_len}-digit padding."
        )
    return [
        f"{prefix}-{str(start_num + i).zfill(pad_len)}" for i in range(count)
    ]


def create_checkout_record(username: str, sample_id: str) -> dict:
    """Create a checkout log record with the current timestamp.

    Args:
        username: Name of the user checking out the sample
        sample_id: ID of the sample being checked out

    Returns:
        Dictionary with Timestamp, User, SampleID
    """
    return {
        'Timestamp': datetime.datetime.now().strftime(DATE_FORMAT),
        'User': username,
        'SampleID': sample_id,
    }


def get_checkout_log_filename(year: int, month: int) -> str:
    """Get the checkout log filename for a given year and month.

    Args:
        year: Four-digit year (e.g., 2026)
        month: Month number (1-12)

    Returns:
        Filename string like 'checkout_log_2026-04.csv'
    """
    return f"checkout_log_{year:04d}-{month:02d}.csv"


def save_checkout_to_csv(
    records: list, outputs_folder: str
) -> tuple[bool, str]:
    """Append checkout records to monthly checkout log CSV files.

    Records are grouped by the month in their Timestamp and written to
    the appropriate monthly file (e.g., checkout_log_2026-04.csv).

    Args:
        records: List of checkout record dicts (Timestamp, User, SampleID)
        outputs_folder: Directory to write monthly log files into

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not records:
        return False, "No checkout records to save."

    os.makedirs(outputs_folder, exist_ok=True)
    fieldnames = ['Timestamp', 'User', 'SampleID']

    # Group records by (year, month) derived from each record's Timestamp
    now = datetime.datetime.now()
    monthly_groups: dict = {}
    for record in records:
        try:
            ts = datetime.datetime.strptime(record['Timestamp'], DATE_FORMAT)
            key = (ts.year, ts.month)
        except (ValueError, KeyError):
            key = (now.year, now.month)
        monthly_groups.setdefault(key, []).append(record)

    total_written = 0
    files_written = []
    try:
        for (year, month), month_records in monthly_groups.items():
            filename = get_checkout_log_filename(year, month)
            filepath = os.path.join(outputs_folder, filename)
            file_exists = os.path.exists(filepath)
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=fieldnames, extrasaction='ignore'
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerows(month_records)
            total_written += len(month_records)
            files_written.append(filename)
        return (
            True,
            f"Successfully saved {total_written} checkout record(s) to "
            f"{', '.join(files_written)}."
        )
    except Exception as e:
        return False, f"Could not save checkout log: {e}"


def format_checkout_message(record: dict) -> str:
    """Format a checkout record into a human-readable terminal message.

    Args:
        record: Checkout record dictionary

    Returns:
        Formatted message string
    """
    return (
        f"[CHECKOUT] {record['Timestamp']} | "
        f"User: '{record['User']}' | "
        f"Sample: '{record['SampleID']}'"
    )
