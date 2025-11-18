import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
from tracker_utils import (
    DATE_FORMAT,
    DATA_SEPARATOR,
    EXIT_CMD,
    SAVE_CMD,
    UNDO_CMD,
    get_default_output_dir,
    parse_input,
    create_log_record,
    save_log_to_csv,
)

OUTPUTS_FOLDER = get_default_output_dir()
LOG_FILE = os.path.join(OUTPUTS_FOLDER, "scan_log.csv")


# --- GUI Class ---
class ProcessTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lab Process Tracker GUI")
        self.geometry("700x650")
        self.configure(bg="#f0f0f0")
        self.current_process = None
        self.operator_name = None
        self.log_records = []
        self.create_widgets()

    def create_widgets(self):
        # Operator Name Entry
        tk.Label(self, text="Operator Name:", bg="#f0f0f0").pack(
            pady=(10, 0)
        )
        self.operator_entry = tk.Entry(self, width=30)
        self.operator_entry.pack()
        self.operator_entry.focus_set()
        self.operator_entry.bind("<Return>", lambda e: self.set_operator())

        self.set_operator_btn = tk.Button(
            self, text="Set Operator", command=self.set_operator
        )
        self.set_operator_btn.pack(pady=(0, 10))

        # Process Status Block
        self.process_frame = tk.Frame(self, width=400, height=150, bg="grey")
        self.process_frame.pack(pady=(10, 0))
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
        self.sample_frame = tk.Frame(
            self, width=400, height=150, bg="#95a5a6"
        )
        self.sample_frame.pack(pady=(5, 10))

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
        tk.Label(self, text="Scan QR Code:", bg="#f0f0f0").pack()
        self.qr_entry = tk.Entry(self, width=50)
        self.qr_entry.pack(pady=5)
        self.qr_entry.bind("<Return>", lambda e: self.handle_scan())

        # Command Buttons
        btn_frame = tk.Frame(self, bg="#f0f0f0")
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
        tk.Label(self, text="Activity Log:", bg="#f0f0f0").pack()
        self.terminal = scrolledtext.ScrolledText(
            self,
            width=80,
            height=5,
            state="disabled",
            font=("Consolas", 9),
        )
        self.terminal.pack(pady=5)

        # Info
        tk.Label(
            self,
            text=f"Log will be saved to: {LOG_FILE}",
            bg="#f0f0f0",
            fg="gray",
            font=("Arial", 8),
        ).pack(pady=(5, 0))

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
        self.qr_entry.focus_set()

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
            self.current_process = data_id
            self.update_process_block(data_id)
            self.update_sample_block(None, status_type="RESET")
            self.print_terminal(
                f">>> PROCESS UPDATED: Now running: '{self.current_process}'"
            )
        elif data_type == "SAMPLE":
            if self.current_process:
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
        success, message = save_log_to_csv(
            self.log_records, LOG_FILE, OUTPUTS_FOLDER
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
            color = "#e74c3c"
            text = f"PROCESS: {process_name}"
        else:
            color = "grey"
            text = "No process"
        self.process_frame.config(bg=color)
        self.process_label.config(bg=color, text=text)

    def update_sample_block(self, sample_info, status_type="SAMPLE"):
        # Sample box stays neutral gray, only text changes
        if status_type == "SAMPLE":
            self.sample_label.config(
                text=f"SAMPLE\n{sample_info}", font=("Arial", 14, "bold")
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
