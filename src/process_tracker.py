import os
import sys
import argparse
import tracker_utils as tu

# --- Global Variables ---
OUTPUTS_FOLDER = None
LOG_FILE = None

# --- Data Storage ---
operator_name = None
current_process = None
tool_process = None
log_records = []

def parse_args():
    parser = argparse.ArgumentParser(description="Lab Process Tracker")
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for scan logs"
    )
    return parser.parse_args()

def log_scan_event(process_name: str, sample_id: str):
    """Creates a new log record with the current PC time."""
    global log_records, operator_name

    record = tu.create_log_record(operator_name, process_name, sample_id)
    log_records.append(record)
    print(f"\n{tu.format_log_message(record)}")

def undo_last_scan():
    """Removes the last logged scan from the records."""
    global log_records

    if not log_records:
        print("\n[INFO] No scans to undo.")
        return

    removed_record = log_records.pop()
    print(f"\n{tu.format_undo_message(removed_record)}")

def save_log():
    """Saves all collected log records to the CSV file."""
    global log_records, LOG_FILE

    if not LOG_FILE:
        print(
            "\n[ERROR] No log file defined. "
            "Please scan a PROCESS QR code first."
        )
        return

    success, message = tu.save_log_to_csv(
        log_records, LOG_FILE, OUTPUTS_FOLDER
    )

    if success:
        print(f"\n[SUCCESS] {message}")
        log_records.clear()
    else:
        print(f"\n[CRITICAL ERROR] {message}")

def is_running_as_exe():
    """Check if the script is running as a compiled executable."""
    return tu.is_running_as_exe()

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
    global current_process, operator_name, tool_process
    global OUTPUTS_FOLDER, LOG_FILE

    # --- Deprecation Warning ---
    print(
        "\n[DEPRECATION WARNING] The CLI is deprecated as of v0.2.0 "
        "and will not be maintained."
    )
    print(
        "It will be removed in v0.3.0. "
        "Please use the new GUI interface for future use.\n"
    )

    # Parse args and set up paths
    args = parse_args()
    OUTPUTS_FOLDER = (
        args.output_dir if args.output_dir
        else tu.get_default_output_dir()
    )

    # Ensure the outputs folder exists at startup
    os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

    print("--- Lab Process Tracker Initialized ---")
    print(f"Logs will be saved to: {OUTPUTS_FOLDER}")

    # Prompt for operator name at session start
    while not operator_name:
        name = input("\nEnter operator name: ").strip()
        is_valid, error_msg = tu.validate_operator_name(name)
        if not is_valid:
            print(f"[ERROR] {error_msg}")
        else:
            operator_name = name

    print(
        f"\nHello, {operator_name}. Have fun scanning... "
        "ps I hope your processes have a UWL file"
    )
    print("---------------------------------------")
    print(
        f"Enter '{tu.EXIT_CMD}' or '{tu.SAVE_CMD}' to quit or "
        "save the current session."
    )
    print(f"Enter '{tu.UNDO_CMD}' to remove the last scan.")
    print(f"Enter '{tu.RESET_OPERATOR_CMD}' to change the operator.")
    print("Scan a PROCESS QR code to set the tool and begin logging.")
    print("---------------------------------------")

    while True:
        try:
            # Check if we need to prompt for operator name
            while not operator_name:
                name = input("\nEnter operator name: ").strip()
                is_valid, error_msg = tu.validate_operator_name(name)
                if not is_valid:
                    print(f"[ERROR] {error_msg}")
                else:
                    operator_name = name
                    print(f"\nWelcome, {operator_name}!")

            # Build the prompt with tool and process information
            status_parts = []
            if tool_process:
                tool_name = tu.get_tool_display_name(tool_process)
                status_parts.append(f"TOOL: {tool_name}")
            else:
                status_parts.append("NO TOOL SET")

            if current_process:
                process_name = tu.get_process_display_name(current_process)
                status_parts.append(f"PROCESS: {process_name}")

            status_str = " | ".join(status_parts)
            prompt = (
                f"\n[{status_str}] >> Scan QR Code "
                f"(or {tu.EXIT_CMD}/{tu.SAVE_CMD}/"
                f"{tu.UNDO_CMD}/{tu.RESET_OPERATOR_CMD}): "
            )
            qr_input = input(prompt).strip()

            if not qr_input:
                continue

            # Check if input is a command
            is_cmd, cmd_type = tu.is_command(qr_input)

            if is_cmd:
                if cmd_type == tu.EXIT_CMD:
                    if log_records and input(
                        "Unsaved data exists. Save before exiting? (Y/N): "
                    ).upper() == 'Y':
                        save_log()
                    print(
                        f"\nExiting tracker. Goodbye, {operator_name}. "
                        "Seriously though, does your process have a UWL?"
                    )
                    pause_before_exit()
                    break
                elif cmd_type == tu.SAVE_CMD:
                    save_log()
                    continue
                elif cmd_type == tu.UNDO_CMD:
                    undo_last_scan()
                    continue
                elif cmd_type == tu.RESET_OPERATOR_CMD:
                    reset_operator()
                    continue

            # --- Core Logic: Parse and Act ---
            data_type, data_id = tu.parse_input(qr_input)
            if not data_type:
                print(
                    f"\n[ERROR] Invalid format: '{qr_input}'. "
                    "Use 'P%:Name' or 'S%:ID'"
                )
                continue

            if data_type == 'PROCESS':
                # Use centralized validation
                is_valid, normalized_process, error_msg = (
                    tu.validate_and_normalize_process(data_id)
                )

                if not is_valid:
                    print(f"\n[ERROR] {error_msg}")
                    continue

                # Check if we need to auto-save before switching processes
                if tu.should_auto_save_on_process_switch(
                    tool_process,
                    normalized_process,
                    len(log_records) > 0
                ):
                    # Auto-save current records before switching
                    record_count = len(log_records)
                    old_log_file = os.path.basename(LOG_FILE)
                    success, _ = tu.save_log_to_csv(
                        log_records, LOG_FILE, OUTPUTS_FOLDER
                    )
                    if success:
                        log_records.clear()
                        # Show notification to user
                        print(
                            f"\n{tu.format_auto_save_message(
                                record_count, old_log_file)}"
                        )

                # Only set current_process if validation passed
                current_process = normalized_process

                # Update tool_process and LOG_FILE when switching
                if not tool_process or normalized_process != tool_process:
                    tool_process = normalized_process
                    LOG_FILE = os.path.join(
                        OUTPUTS_FOLDER,
                        tu.get_log_filename(tool_process)
                    )
                    tool_display_name = tu.get_tool_display_name(
                        tool_process
                    )
                    print(f"\n>>> TOOL SET: '{tool_display_name}'")
                    print(f">>> Log file: {LOG_FILE}")

                process_display_name = tu.get_process_display_name(
                    current_process
                )
                print(
                    f"\n>>> PROCESS UPDATED: "
                    f"Now running: '{process_display_name}'"
                )

            elif data_type == 'SAMPLE':
                if not tool_process or not current_process:
                    print(
                        "\n[ALERT] Cannot log sample. "
                        "Please scan a PROCESS QR code first."
                    )
                else:
                    log_scan_event(current_process, data_id)
            elif data_type == 'SAMPLE_LEGACY':
                if not tool_process or not current_process:
                    print(
                        "\n[ALERT] Cannot log sample. "
                        "Please scan a PROCESS QR code first."
                    )
                else:
                    print(
                        f"\n{tu.format_legacy_sample_warning(data_id)}"
                    )
                    log_scan_event(current_process, data_id)
            else:
                print(f"\n[ERROR] Unknown data type: '{data_type}'")

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