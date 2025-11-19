import os
import sys
import argparse
from tracker_utils import (
    DATE_FORMAT, DATA_SEPARATOR, EXIT_CMD, SAVE_CMD, UNDO_CMD, RESET_OPERATOR_CMD,
    get_default_output_dir, parse_input, create_log_record, save_log_to_csv,
    get_log_filename, validate_process, get_tool_name, get_process_name
)

# --- Global Variables ---
OUTPUTS_FOLDER = None
LOG_FILE = None

# --- Data Storage ---
operator_name = None
current_process = None
tool_process = None  # The main tool/process for this session
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
    global log_records, LOG_FILE

    if not LOG_FILE:
        print("\n[ERROR] No log file defined. Please scan a PROCESS QR code first.")
        return

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

def reset_operator():
    """Reset the operator name, allowing a new operator to take over."""
    global operator_name

    if not operator_name:
        print("\n[INFO] No operator is currently set.")
        return

    old_operator = operator_name
    operator_name = None
    print(f"\n[RESET] Operator '{old_operator}' has been reset.")
    print("Please enter a new operator name to continue.")

def main():
    """Main loop for the scanning control process."""
    global current_process, operator_name, tool_process, OUTPUTS_FOLDER, LOG_FILE

    # Parse args and set up paths
    args = parse_args()
    OUTPUTS_FOLDER = args.output_dir if args.output_dir else get_default_output_dir()

    # Ensure the outputs folder exists at startup
    os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

    print("--- Lab Process Tracker Initialized ---")
    print(f"Logs will be saved to: {OUTPUTS_FOLDER}")

    # Prompt for operator name at session start
    while not operator_name:
        operator_name = input("\nEnter operator name: ").strip()
        if not operator_name:
            print("[ERROR] Operator name cannot be empty.")

    print(f"\nHello, {operator_name}. Have fun scanning... ps I hope your processes have a UWL file")
    print("---------------------------------------")
    print(f"Enter '{EXIT_CMD}' or '{SAVE_CMD}' to quit or save the current session.")
    print(f"Enter '{UNDO_CMD}' to remove the last scan.")
    print(f"Enter '{RESET_OPERATOR_CMD}' to change the operator.")
    print("Scan a PROCESS QR code to set the tool and begin logging.")
    print("---------------------------------------")

    while True:
        try:
            # Check if we need to prompt for operator name
            while not operator_name:
                operator_name = input("\nEnter operator name: ").strip()
                if not operator_name:
                    print("[ERROR] Operator name cannot be empty.")
                else:
                    print(f"\nWelcome, {operator_name}!")

            # Build the prompt with tool and process information
            status_parts = []
            if tool_process:
                tool_name = get_tool_name(tool_process)
                status_parts.append(f"TOOL: {tool_name}")
            else:
                status_parts.append("NO TOOL SET")

            if current_process:
                process_name = get_process_name(current_process)
                status_parts.append(f"PROCESS: {process_name}")

            status_str = " | ".join(status_parts)
            prompt = f"\n[{status_str}] >> Scan QR Code (or {EXIT_CMD}/{SAVE_CMD}/{UNDO_CMD}/{RESET_OPERATOR_CMD}): "
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

            if qr_input.upper() == RESET_OPERATOR_CMD:
                reset_operator()
                continue

            # --- Core Logic: Parse and Act ---
            data_type, data_id = parse_input(qr_input)
            if not data_type:
                continue

            if data_type == 'PROCESS':
                # 1. Process Scan: Update the current state
                try:
                    validate_process(data_id)
                except ValueError as e:
                    print(f"\n[ERROR] {e}")
                    continue

                current_process = data_id

                # If this is the first process scan, set it as the tool process and create log file
                if not tool_process:
                    tool_process = data_id
                    LOG_FILE = os.path.join(OUTPUTS_FOLDER, get_log_filename(tool_process))
                    print(f"\n>>> TOOL SET: '{tool_process}'")
                    print(f">>> Log file: {LOG_FILE}")

                print(f"\n>>> PROCESS UPDATED: Now running: '{current_process}'")

            elif data_type == 'SAMPLE':
                # 2. Sample Scan: Log the event using the current process
                if not tool_process:
                    print("\n[ALERT] Cannot log sample. Please scan a **PROCESS QR code** first to set the tool.")
                elif current_process:
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