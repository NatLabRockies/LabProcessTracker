import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
from tracker_utils import (
    DATE_FORMAT,
    DATA_SEPARATOR,
    EXIT_CMD,
    SAVE_CMD,
    UNDO_CMD,
    RESET_OPERATOR_CMD,
    get_default_output_dir,
    parse_input,
    create_log_record,
    save_log_to_csv,
    get_process_color,
    get_log_filename,
    validate_process,
    get_tool_name,
    get_process_name,
)

OUTPUTS_FOLDER = get_default_output_dir()


# --- GUI Class ---
class ProcessTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lab Process Tracker GUI")
        self.geometry("700x650")
        self.configure(bg="#f0f0f0")
        self.current_process = None
        self.tool_process = None  # The main tool/process for this session
        self.log_file = None
        self.operator_name = None
        self.log_records = []
        self.create_widgets()

    def create_widgets(self):
        # Main container with margins
        main_container = tk.Frame(self, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Operator Name Entry
        operator_frame = tk.Frame(main_container, bg="#f0f0f0")
        operator_frame.pack(pady=(10, 0))

        tk.Label(operator_frame, text="Operator Name:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(0, 5))
        self.operator_entry = tk.Entry(operator_frame, width=25)
        self.operator_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.operator_entry.focus_set()
        self.operator_entry.bind("<Return>", lambda e: self.set_operator())

        self.set_operator_btn = tk.Button(
            operator_frame, text="Set Operator", command=self.set_operator
        )
        self.set_operator_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_operator_btn = tk.Button(
            operator_frame, text="Reset Operator", command=self.reset_operator, state="disabled"
        )
        self.reset_operator_btn.pack(side=tk.LEFT)

        # Process Status Block
        self.process_frame = tk.Frame(main_container, height=150, bg="grey")
        self.process_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)
        self.process_label = tk.Label(
            self.process_frame,
            text="No process",
            font=("Arial", 18, "bold"),
            bg="grey",
            fg="white",
            wraplength=380,
        )
        self.process_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Sample Status Block
        self.sample_frame = tk.Frame(main_container, height=150, bg="#95a5a6")
        self.sample_frame.pack(pady=(5, 10), fill=tk.BOTH, expand=True)

        # Single label that will show either "No sample" or "SAMPLE\n{ID}"
        self.sample_label = tk.Label(
            self.sample_frame,
            text="No sample",
            font=("Arial", 18, "bold"),
            bg="#95a5a6",
            fg="white",
            wraplength=380,
            justify=tk.CENTER,
        )
        self.sample_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # QR Input
        tk.Label(main_container, text="Scan QR Code:", bg="#f0f0f0").pack()
        self.qr_entry = tk.Entry(main_container, width=50)
        self.qr_entry.pack(pady=5)
        self.qr_entry.bind("<Return>", lambda e: self.handle_scan())

        # Command Buttons
        btn_frame = tk.Frame(main_container, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        self.save_btn = tk.Button(
            btn_frame, text="SAVE", width=10, command=self.save_log
        )
        self.save_btn.grid(row=0, column=0, padx=5)
        self.undo_btn = tk.Button(
            btn_frame, text="UNDO", width=10, command=self.undo_last_scan
        )
        self.undo_btn.grid(row=0, column=1, padx=5)
        self.exit_btn = tk.Button(
            btn_frame, text="EXIT", width=10, command=self.exit_app
        )
        self.exit_btn.grid(row=0, column=2, padx=5)

        # Terminal Output
        tk.Label(main_container, text="Activity Log:", bg="#f0f0f0").pack()
        self.terminal = scrolledtext.ScrolledText(
            main_container,
            width=80,
            height=5,
            state="disabled",
            font=("Consolas", 9),
        )
        self.terminal.pack(pady=5, fill=tk.BOTH, expand=True)

        # Info
        self.log_file_label = tk.Label(
            main_container,
            text="Scan a PROCESS QR code to set the tool and begin logging.",
            bg="#f0f0f0",
            fg="gray",
            font=("Arial", 8),
        )
        self.log_file_label.pack(pady=(5, 0))

    def set_operator(self):
        name = self.operator_entry.get().strip()
        if not name:
            self.print_terminal("[ERROR] Operator name cannot be empty.")
            return
        self.operator_name = name
        greeting = (
            f"Hello, {self.operator_name}. Have fun scanning... "
            "ps I hope your processes have a UWL file"
        )
        self.print_terminal(greeting)
        self.operator_entry.config(state="disabled")
        self.set_operator_btn.config(state="disabled")
        self.reset_operator_btn.config(state="normal")
        self.qr_entry.focus_set()

    def reset_operator(self):
        """Reset the operator name, allowing a new operator to take over."""
        if not self.operator_name:
            self.print_terminal("[INFO] No operator is currently set.")
            return

        old_operator = self.operator_name
        self.operator_name = None
        self.operator_entry.delete(0, tk.END)
        self.operator_entry.config(state="normal")
        self.set_operator_btn.config(state="normal")
        self.reset_operator_btn.config(state="disabled")
        self.print_terminal(f"[RESET] Operator '{old_operator}' has been reset.")
        self.print_terminal("Please enter a new operator name to continue.")
        self.operator_entry.focus_set()

    def handle_scan(self):
        if not self.operator_name:
            self.print_terminal("[ERROR] Please enter operator name first.")
            return
        qr_text = self.qr_entry.get().strip()
        self.qr_entry.delete(0, tk.END)
        if not qr_text:
            return
        # Handle commands
        if qr_text.upper() == EXIT_CMD:
            self.exit_app()
            return
        if qr_text.upper() == SAVE_CMD:
            self.save_log()
            return
        if qr_text.upper() == UNDO_CMD:
            self.undo_last_scan()
            return
        if qr_text.upper() == RESET_OPERATOR_CMD:
            self.reset_operator()
            return
        # Parse input
        data_type, data_id = parse_input(qr_text)
        if not data_type:
            error_msg = (
                f"[ERROR] Invalid format: '{qr_text}'. "
                f"Use 'TYPE{DATA_SEPARATOR}ID' "
                "(e.g., PROCESS:Name or SAMPLE:ID)."
            )
            self.print_terminal(error_msg)
            return
        if data_type == "PROCESS":
            try:
                validate_process(data_id)
            except ValueError as e:
                self.print_terminal(f"[ERROR] {str(e)}")
                self.update_sample_block("Invalid process", status_type="ERROR")
                return

            self.current_process = data_id

            # If this is the first process scan, set it as the tool process and create log file
            if not self.tool_process:
                self.tool_process = data_id
                self.log_file = os.path.join(OUTPUTS_FOLDER, get_log_filename(self.tool_process))
                tool_name = get_tool_name(self.tool_process)
                self.title(f"Lab Process Tracker GUI - {tool_name}")
                self.log_file_label.config(text=f"Log will be saved to: {self.log_file}")
                self.print_terminal(f">>> TOOL SET: '{tool_name}'")
                self.print_terminal(f">>> Log file: {self.log_file}")

            self.update_process_block(data_id)
            self.update_sample_block(None, status_type="RESET")
            process_name = get_process_name(self.current_process)
            self.print_terminal(
                f">>> PROCESS UPDATED: Now running: '{process_name}'"
            )
        elif data_type == "SAMPLE":
            if not self.tool_process:
                alert_msg = (
                    "[ALERT] Cannot log sample. Please scan a "
                    "**PROCESS QR code** first to set the tool."
                )
                self.print_terminal(alert_msg)
                self.update_sample_block("No tool set", status_type="ALERT")
            elif self.current_process:
                self.log_scan_event(self.current_process, data_id)
                self.update_sample_block(data_id, status_type="SAMPLE")
            else:
                alert_msg = (
                    "[ALERT] Cannot log sample. Please scan a "
                    "**PROCESS QR code** first to define the current step."
                )
                self.print_terminal(alert_msg)
                self.update_sample_block("No process set", status_type="ALERT")
        else:
            error_msg = (
                f"[ERROR] Unknown data type scanned: '{data_type}'. "
                "Must be 'PROCESS' or 'SAMPLE'."
            )
            self.print_terminal(error_msg)
            self.update_sample_block(data_type, status_type="ERROR")

    def log_scan_event(self, process_name, sample_id):
        record = create_log_record(
            self.operator_name, process_name, sample_id
        )
        self.log_records.append(record)
        log_msg = (
            f"[LOGGED] {record['Timestamp']} | "
            f"Operator: '{self.operator_name}' | "
            f"Process: '{process_name}' | "
            f"Sample: '{sample_id}'"
        )
        self.print_terminal(log_msg)

    def undo_last_scan(self):
        if not self.log_records:
            self.print_terminal("[INFO] No scans to undo.")
            return
        removed_record = self.log_records.pop()
        undo_msg = (
            f"[UNDO] Removed last scan: {removed_record['Timestamp']} | "
            f"Process: '{removed_record['ProcessName']}' | "
            f"Sample: '{removed_record['SampleID']}'"
        )
        self.print_terminal(undo_msg)
        self.update_sample_block("Last scan undone", status_type="UNDO")

    def save_log(self):
        if not self.log_file:
            self.print_terminal("[ERROR] No log file defined. Please scan a PROCESS QR code first.")
            return

        success, message = save_log_to_csv(
            self.log_records, self.log_file, OUTPUTS_FOLDER
        )

        if success:
            self.print_terminal(f"[SUCCESS] {message}")
            self.log_records.clear()
        else:
            self.print_terminal(f"[CRITICAL ERROR] {message}")

    def exit_app(self):
        if self.log_records:
            if messagebox.askyesno(
                "Unsaved Data", "Unsaved data exists. Save before exiting?"
            ):
                self.save_log()
        self.destroy()

    def print_terminal(self, msg):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, msg + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def update_process_block(self, process_name):
        if process_name:
            color = get_process_color(process_name)
            # Display only the process name (after underscore)
            display_name = get_process_name(process_name)
            text = display_name
        else:
            color = "grey"
            text = "No process"
        self.process_frame.config(bg=color)
        self.process_label.config(bg=color, text=text)

    def update_sample_block(self, sample_info, status_type="SAMPLE"):
        # Sample box stays neutral gray, only text changes
        if status_type == "SAMPLE":
            # Display only the sample ID without "SAMPLE" prefix
            self.sample_label.config(
                text=sample_info, font=("Arial", 18, "bold")
            )
        elif status_type == "UNDO":
            self.sample_label.config(
                text="Last scan undone", font=("Arial", 18, "bold")
            )
        elif status_type == "ALERT":
            self.sample_label.config(
                text=sample_info, font=("Arial", 18, "bold")
            )
        elif status_type == "ERROR":
            self.sample_label.config(
                text=f"ERROR\n{sample_info}", font=("Arial", 14, "bold")
            )
        elif status_type == "RESET":
            self.sample_label.config(
                text="No sample", font=("Arial", 18, "bold")
            )
        else:
            self.sample_label.config(
                text="No sample", font=("Arial", 18, "bold")
            )


if __name__ == "__main__":
    app = ProcessTrackerGUI()
    app.mainloop()
