import datetime
import csv
import os
import sys
import argparse

# --- Output Directory Logic ---
def get_default_output_dir():
    # Determine project outputs path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_outputs = os.path.join(project_root, "outputs")
    # Check if running from a temp directory (PyInstaller .exe)
    temp_dirs = [os.environ.get('TEMP'), os.environ.get('TMP')]
    is_temp = any(project_root.lower().startswith(td.lower()) for td in temp_dirs if td)
    if os.path.isdir(project_outputs) and not is_temp:
        return project_outputs
    # Else, fallback to user's Documents
    user_docs = os.path.expanduser(r"~\Documents\process_tracking_outputs")
    return user_docs

def parse_args():
    parser = argparse.ArgumentParser(description="Lab Process Tracker")
    parser.add_argument("--output-dir", type=str, help="Custom output directory for scan logs")
    return parser.parse_args()

args = parse_args()
OUTPUTS_FOLDER = args.output_dir if args.output_dir else get_default_output_dir()
LOG_FILE = os.path.join(OUTPUTS_FOLDER, "scan_log.csv")

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
# The separator used in the simulated QR code input
DATA_SEPARATOR = ':'

EXIT_CMD = 'EXIT'
SAVE_CMD = 'SAVE'
UNDO_CMD = 'UNDO'

# --- Data Storage ---
# Stores the operator name for the session
operator_name = None
# Stores the currently active process name
current_process = None
# Stores all collected records before saving
log_records = []

def parse_input(qr_text: str) -> tuple[str, str] | tuple[None, None]:
    """Parses the QR code text to determine type and ID."""
    try:
        # Split the input (e.g., "PROCESS:Example Process" -> ["PROCESS", "Example Process"])
        parts = qr_text.strip().split(DATA_SEPARATOR, 1)
        if len(parts) == 2:
            data_type = parts[0].strip().upper()
            data_id = parts[1].strip()
            return data_type, data_id

        print(f"\n[ERROR] Invalid format: '{qr_text}'. Use 'TYPE{DATA_SEPARATOR}ID' (e.g., PROCESS:Name or SAMPLE:ID).")
        return None, None
    except Exception as e:
        print(f"\n[ERROR] Failed to parse input: {e}")
        return None, None

def log_scan_event(process_name: str, sample_id: str):
    """Creates a new log record with the current PC time."""
    global log_records, operator_name

    scan_time = datetime.datetime.now().strftime(DATE_FORMAT)

    record = {
        'Timestamp': scan_time,
        'Operator': operator_name,
        'ProcessName': process_name,
        'SampleID': sample_id,
    }

    log_records.append(record)
    print(f"\n[LOGGED] {scan_time} | Operator: '{operator_name}' | Process: '{process_name}' | Sample: '{sample_id}'")

def undo_last_scan():
    """Removes the last logged scan from the records."""
    global log_records

    if not log_records:
        print("\n[INFO] No scans to undo.")
        return

    removed_record = log_records.pop()
    print(f"\n[UNDO] Removed last scan: {removed_record['Timestamp']} | Process: '{removed_record['ProcessName']}' | Sample: '{removed_record['SampleID']}'")

def save_log():
    """Saves all collected log records to the CSV file."""
    if not log_records:
        print("\nNo records to save.")
        return

    # Ensure the outputs folder exists
    os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

    # Check if file exists to decide whether to write headers
    file_exists = os.path.exists(LOG_FILE)
    fieldnames = list(log_records[0].keys())

    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()  # Write header only if the file is new

            writer.writerows(log_records)

        print(f"\n[SUCCESS] Successfully saved {len(log_records)} records to {LOG_FILE}.")
        log_records.clear() # Clear in-memory log after successful save
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Could not save log to file: {e}")

def main():
    """Main loop for the scanning control process."""
    global current_process, operator_name

    # Ensure the outputs folder exists at startup
    os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

    print("--- Lab Process Tracker Initialized ---")
    print(f"Log will be saved to: {LOG_FILE}")

    # Prompt for operator name at session start
    while not operator_name:
        operator_name = input("\nEnter operator name: ").strip()
        if not operator_name:
            print("[ERROR] Operator name cannot be empty.")

    print(f"\nHello, {operator_name}. Have fun scanning... ps I hope your processes have a UWL file")
    print("---------------------------------------")
    print(f"Enter '{EXIT_CMD}' or '{SAVE_CMD}' to quit or save the current session.")
    print(f"Enter '{UNDO_CMD}' to remove the last scan.")
    print("---------------------------------------")

    while True:
        try:
            # Simulate the QR code scanner output being read via input()
            prompt = f"\n{'[ACTIVE PROCESS: ' + current_process + ']' if current_process else '[NO ACTIVE PROCESS]'} >> Scan QR Code (or {EXIT_CMD}/{SAVE_CMD}/{UNDO_CMD}): "
            qr_input = input(prompt).strip()

            if not qr_input:
                continue

            if qr_input.upper() == EXIT_CMD:
                if log_records and input("Unsaved data exists. Save before exiting? (Y/N): ").upper() == 'Y':
                    save_log()
                print(f"\nExiting tracker. Goodbye, {operator_name}. Seriously though, does your process have a UWL?")
                break

            if qr_input.upper() == SAVE_CMD:
                save_log()
                continue

            if qr_input.upper() == UNDO_CMD:
                undo_last_scan()
                continue

            # --- Core Logic: Parse and Act ---
            data_type, data_id = parse_input(qr_input)
            if not data_type:
                continue

            if data_type == 'PROCESS':
                # 1. Process Scan: Update the current state
                current_process = data_id
                print(f"\n>>> PROCESS UPDATED: Now running: '{current_process}'")

            elif data_type == 'SAMPLE':
                # 2. Sample Scan: Log the event using the current process
                if current_process:
                    log_scan_event(current_process, data_id)
                else:
                    print("\n[ALERT] Cannot log sample. Please scan a **PROCESS QR code** first to define the current step.")

            else:
                print(f"\n[ERROR] Unknown data type scanned: '{data_type}'. Must be 'PROCESS' or 'SAMPLE'.")

        except EOFError:
            print("\nReceived EOF. Saving and exiting.")
            save_log()
            break
        except KeyboardInterrupt:
            print("\n\nProcess interrupted. Saving and exiting.")
            save_log()
            break

if __name__ == "__main__":
    main()