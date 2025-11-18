import os
import sys
import argparse
from tracker_utils import (
    DATE_FORMAT, DATA_SEPARATOR, EXIT_CMD, SAVE_CMD, UNDO_CMD,
    get_default_output_dir, parse_input, create_log_record, save_log_to_csv
)

# --- Global Variables ---
OUTPUTS_FOLDER = None
LOG_FILE = None

# --- Data Storage ---
operator_name = None
current_process = None
log_records = []

def parse_args():
    parser = argparse.ArgumentParser(description="Lab Process Tracker")
    parser.add_argument("--output-dir", type=str, help="Custom output directory for scan logs")
    return parser.parse_args()

def log_scan_event(process_name: str, sample_id: str):
    """Creates a new log record with the current PC time."""
    global log_records, operator_name

    record = create_log_record(operator_name, process_name, sample_id)
    log_records.append(record)
    print(f"\n[LOGGED] {record['Timestamp']} | Operator: '{operator_name}' | Process: '{process_name}' | Sample: '{sample_id}'")

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
    global log_records

    success, message = save_log_to_csv(log_records, LOG_FILE, OUTPUTS_FOLDER)

    if success:
        print(f"\n[SUCCESS] {message}")
        log_records.clear()
    else:
        print(f"\n[CRITICAL ERROR] {message}")

def is_running_as_exe():
    """Check if the script is running as a compiled executable."""
    return getattr(sys, 'frozen', False)

def pause_before_exit(message="Press Enter to exit..."):
    """Pause execution to allow user to read messages before window closes."""
    if is_running_as_exe():
        try:
            input(f"\n{message}")
        except:
            pass

def main():
    """Main loop for the scanning control process."""
    global current_process, operator_name, OUTPUTS_FOLDER, LOG_FILE

    # Parse args and set up paths
    args = parse_args()
    OUTPUTS_FOLDER = args.output_dir if args.output_dir else get_default_output_dir()
    LOG_FILE = os.path.join(OUTPUTS_FOLDER, "scan_log.csv")

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
                pause_before_exit()
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
            pause_before_exit()
            break
        except KeyboardInterrupt:
            print("\n\nProcess interrupted. Saving and exiting.")
            save_log()
            pause_before_exit()
            break

if __name__ == "__main__":
    main()