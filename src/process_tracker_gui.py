import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
import tracker_utils as tu
from gui_components import TrayPositionDialog, BulkCheckoutDialog, BG_COLOR_CHECKOUT

OUTPUTS_FOLDER = tu.get_default_output_dir()

# Font size constants
FONT_SIZE_LARGE = 26
FONT_SIZE_MEDIUM = 22


# --- GUI Class ---
class ProcessTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lab Process Tracker GUI")
        self.geometry("700x650")
        self.configure(bg="#f0f0f0")
        self.current_process = None
        self.tool_process = None
        self.log_file = None
        self.username = None
        self.log_records = []

        # Tray mode state - updated for multi-tray support
        self.tray_mode = False
        self.current_tray_id = None  # Currently active tray
        self.tray_positions = []  # Positions for current tray
        # Dict of {tray_id: [{"position": pos, "sample_id": id}, ...]}
        self.tray_samples = {}
        self.tray_position_index = 0  # Index for current tray
        self.tray_dialog = None
        # Multi-tray session state
        self.all_trays_in_session = []  # List of completed tray IDs
        self.session_id = None  # Session ID for batch operations

        # Checkout mode state
        self.checkout_mode = False
        self.checkout_records = []

        self.create_widgets()

        # Handle window close event (X button)
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def create_widgets(self):
        # Main container with margins
        main_container = tk.Frame(self, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # NLR Username Entry
        username_frame = tk.Frame(main_container, bg="#f0f0f0")
        username_frame.pack(pady=(10, 0))

        tk.Label(
            username_frame, text="NLR Username:", bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=(0, 5))
        self.user_entry = tk.Entry(username_frame, width=25)
        self.user_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.user_entry.focus_set()
        self.user_entry.bind("<Return>", lambda e: self.set_user())

        self.set_user_btn = tk.Button(
            username_frame, text="Set", command=self.set_user
        )
        self.set_user_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_user_btn = tk.Button(
            username_frame,
            text="Reset",
            command=self.reset_user,
            state="disabled"
        )
        self.reset_user_btn.pack(side=tk.LEFT)

        # Process Status Block
        self.process_frame = tk.Frame(main_container, height=150, bg="grey")
        self.process_frame.pack(pady=(10, 0), fill=tk.BOTH, expand=True)
        self.process_label = tk.Label(
            self.process_frame,
            text="No process",
            font=("Arial", FONT_SIZE_LARGE, "bold"),
            bg="grey",
            fg="white",
            wraplength=380,
        )
        self.process_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Sample Status Block
        self.sample_frame = tk.Frame(main_container, height=150, bg="#95a5a6")
        self.sample_frame.pack(pady=(5, 10), fill=tk.BOTH, expand=True)

        # Label "No sample" or "SAMPLE\n{ID}"
        self.sample_label = tk.Label(
            self.sample_frame,
            text="No sample",
            font=("Arial", FONT_SIZE_LARGE, "bold"),
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
        self.checkout_btn = tk.Button(
            btn_frame, text="CHECKOUT", width=12,
            command=self.toggle_checkout_mode
        )
        self.checkout_btn.grid(row=0, column=3, padx=5)
        self._checkout_btn_default_bg = self.checkout_btn.cget("bg")
        self._checkout_btn_default_fg = self.checkout_btn.cget("fg")

        # Terminal Output
        tk.Label(main_container, text="Activity Log:", bg="#f0f0f0").pack()
        self.terminal = scrolledtext.ScrolledText(
            main_container,
            width=80,
            height=5,
            state="disabled",
            font=("Consolas", 9),
            takefocus=0
        )
        self.terminal.pack(pady=5, fill=tk.BOTH, expand=True)
        # Prevent focus and selection in the activity log
        self.terminal.bind(
            "<1>", lambda e: (self.qr_entry.focus_set(), "break")
        )
        self.terminal.bind("<FocusIn>", lambda e: self.qr_entry.focus_set())

        # Info
        self.log_file_label = tk.Label(
            main_container,
            text="Scan a PROCESS QR code to set the tool and begin logging.",
            bg="#f0f0f0",
            fg="gray",
            font=("Arial", 8),
        )
        self.log_file_label.pack(pady=(5, 0))

    def set_user(self):
        name = self.user_entry.get().strip()
        is_valid, error_msg = tu.validate_username(name)
        if not is_valid:
            self.print_terminal(f"[ERROR] {error_msg}")
            return
        self.username = name
        greeting = (
            f"Hello, {self.username}. Have fun scanning... "
            "ps I hope your processes have a UWL file"
        )
        self.print_terminal(greeting)
        self.user_entry.config(state="disabled")
        self.set_user_btn.config(state="disabled")
        self.reset_user_btn.config(state="normal")
        self.qr_entry.focus_set()

    def reset_user(self):
        """Reset the NLR username, allowing a new user to take over."""
        if not self.username:
            self.print_terminal("[INFO] No NLR username is currently set.")
            return

        old_user = self.username
        self.username = None
        self.user_entry.delete(0, tk.END)
        self.user_entry.config(state="normal")
        self.set_user_btn.config(state="normal")
        self.reset_user_btn.config(state="disabled")
        self.print_terminal(f"[RESET] NLR username '{old_user}' has been reset.")
        self.print_terminal("Please enter a new NLR username to continue.")
        self.user_entry.focus_set()

    # --- Checkout Mode ---
    def toggle_checkout_mode(self):
        """Toggle checkout mode on or off."""
        if self.checkout_mode:
            self.exit_checkout_mode()
        else:
            self.enter_checkout_mode()

    def enter_checkout_mode(self):
        """Enter checkout mode: log samples against user without a process."""
        if self.tray_mode:
            self.print_terminal(
                "[ERROR] Cannot enter checkout mode during tray mode. "
                "Complete or exit tray scanning first."
            )
            return
        self.checkout_mode = True
        self.process_frame.config(bg=BG_COLOR_CHECKOUT)
        self.process_label.config(bg=BG_COLOR_CHECKOUT, text="CHECKOUT MODE")
        self.checkout_btn.config(
            text="EXIT CHECKOUT", bg=BG_COLOR_CHECKOUT, fg="white"
        )
        self.print_terminal(
            "[CHECKOUT] Checkout mode active. Scan a sample QR code to begin."
        )
        self.qr_entry.focus_set()

    def exit_checkout_mode(self):
        """Exit checkout mode, auto-saving any pending checkout records."""
        if self.checkout_records:
            self.save_checkout_log()
        self.checkout_mode = False
        self.checkout_btn.config(
            text="CHECKOUT",
            bg=self._checkout_btn_default_bg,
            fg=self._checkout_btn_default_fg,
        )
        if self.current_process:
            valid = tu.is_process_valid(self.current_process)
            self.update_process_block(self.current_process, valid=valid)
        else:
            self.update_process_block(None)
        self.print_terminal("[CHECKOUT] Checkout mode exited.")
        self.qr_entry.focus_set()

    def handle_checkout_scan(self, sample_id: str):
        """Open BulkCheckoutDialog after scanning a sample in checkout mode."""
        BulkCheckoutDialog(
            self,
            sample_id,
            tu.generate_consecutive_sample_ids,
            self._confirm_checkout,
            lambda: self.print_terminal("[CHECKOUT] Cancelled."),
        )

    def _confirm_checkout(self, first_sample_id: str, count: int):
        """Create checkout records for first_sample_id plus count-1 consecutives."""
        assert self.username is not None
        try:
            sample_ids = tu.generate_consecutive_sample_ids(
                first_sample_id, count
            )
        except ValueError as exc:
            self.print_terminal(f"[CHECKOUT ERROR] {exc}")
            return
        for sid in sample_ids:
            self.checkout_records.append(
                tu.create_checkout_record(self.username, sid)
            )
        if count == 1:
            self.print_terminal(
                tu.format_checkout_message(self.checkout_records[-1])
            )
        else:
            self.print_terminal(
                f"[CHECKOUT] {count} samples queued: "
                f"{sample_ids[0]} \u2192 {sample_ids[-1]}. "
                f"{len(self.checkout_records)} total unsaved."
            )
        self.qr_entry.focus_set()

    def save_checkout_log(self):
        """Save pending checkout records to the checkout log CSV."""
        if not self.checkout_records:
            self.print_terminal("[INFO] No checkout records to save.")
            return
        checkout_log_path = os.path.join(
            OUTPUTS_FOLDER, tu.CHECKOUT_LOG_FILENAME
        )
        success, message = tu.save_checkout_to_csv(
            self.checkout_records, checkout_log_path, OUTPUTS_FOLDER
        )
        if success:
            self.print_terminal(f"[SUCCESS] {message}")
            self.checkout_records.clear()
        else:
            self.print_terminal(f"[CRITICAL ERROR] {message}")

    def show_tray_dialog(self, tray_id, positions, position):
        """Show or update the tray position dialog."""
        if (self.tray_dialog is None or
                not self.tray_dialog.winfo_exists()):
            self.tray_dialog = TrayPositionDialog(
                self,
                tray_id,
                positions,
                self.skip_current_position,
                self.skip_all_remaining_positions
            )
            self.tray_dialog.update_position(position)
        else:
            self.tray_dialog.update_position(position)
            self.tray_dialog.lift()

        # Always refocus QR entry after showing/updating dialog
        self.qr_entry.focus_set()

    def close_tray_dialog(self):
        """Close the tray position dialog if it exists."""
        if self.tray_dialog and self.tray_dialog.winfo_exists():
            self.tray_dialog.close()
            self.tray_dialog = None

    def skip_current_position(self):
        """Skip the current position and move to next."""
        if (self.tray_mode and
                self.tray_position_index < len(self.tray_positions)):
            skipped_pos = self.tray_positions[self.tray_position_index]
            self.print_terminal(f"[TRAY] Skipped position {skipped_pos}.")
            self.tray_position_index += 1
            if self.tray_position_index < len(self.tray_positions):
                next_pos = self.tray_positions[self.tray_position_index]
                self.show_tray_dialog(
                    self.current_tray_id, self.tray_positions, next_pos
                )
            else:
                # Mark tray as complete
                self.all_trays_in_session.append(self.current_tray_id)
                self.close_tray_dialog()

                # Calculate counts for display
                sample_count = len(self.tray_samples[self.current_tray_id])
                tray_count = len(self.all_trays_in_session)
                total_samples = sum(
                    len(self.tray_samples[tray_id])
                    for tray_id in self.all_trays_in_session
                )

                self.print_terminal(
                    f"[TRAY] Tray {self.current_tray_id} complete with "
                    f"{sample_count} sample(s). "
                    f"Total: {tray_count} tray(s), "
                    f"{total_samples} sample(s) in session."
                )
                self.print_terminal(
                    "[TRAY] Scan another TRAY to add to session, "
                    "or scan PROCESS QR code."
                )

    def skip_all_remaining_positions(self):
        """Skip all remaining tray positions and allow process scanning."""
        if (self.tray_mode and
                self.tray_position_index < len(self.tray_positions)):
            skipped = len(self.tray_positions) - self.tray_position_index
            self.print_terminal(f"[TRAY] Skipped {skipped} remaining position(s).")
            self.tray_position_index = len(self.tray_positions)

            # Mark tray as complete
            self.all_trays_in_session.append(self.current_tray_id)
            self.close_tray_dialog()

            # Calculate counts for display
            sample_count = len(self.tray_samples[self.current_tray_id])
            tray_count = len(self.all_trays_in_session)
            total_samples = sum(
                len(self.tray_samples[tray_id])
                for tray_id in self.all_trays_in_session
            )

            self.print_terminal(
                f"[TRAY] Tray {self.current_tray_id} complete with "
                f"{sample_count} sample(s). "
                f"Total: {tray_count} tray(s), "
                f"{total_samples} sample(s) in session."
            )
            self.print_terminal(
                "[TRAY] Scan another TRAY to add to session, "
                "or scan PROCESS QR code."
            )

    def handle_scan(self):
        if not self.username:
            self.print_terminal("[ERROR] Please enter user name first.")
            return
        # Type assertion: username is not None after check
        assert self.username is not None
        qr_text = self.qr_entry.get().strip()
        self.qr_entry.delete(0, tk.END)
        if not qr_text:
            return

        # Check if input is a command
        is_cmd, cmd_type = tu.is_command(qr_text)

        if is_cmd:
            if cmd_type == tu.EXIT_CMD:
                self.exit_app()
                return
            elif cmd_type == tu.SAVE_CMD:
                self.save_log()
                return
            elif cmd_type == tu.UNDO_CMD:
                self.undo_last_scan()
                return
            elif cmd_type == tu.RESET_USER_CMD:
                self.reset_user()
                return

        # Parse input
        data_type, data_id = tu.parse_input(qr_text)
        if not data_type:
            self.print_terminal(
                f"[ERROR] Invalid format: '{qr_text}'. "
                "Use 'P%:Name', 'S%:ID', 'B%:ID', or 'T%:TrayID'."
            )
            return

        # Type assertion: if data_type is not None, data_id is also not None
        assert data_id is not None

        # --- Checkout Mode ---
        if self.checkout_mode:
            if tu.is_sample_type(data_type):
                self.handle_checkout_scan(data_id)
            else:
                self.print_terminal(
                    "[CHECKOUT] Only sample QR codes (S%:ID) are accepted "
                    "in checkout mode."
                )
            return

        # --- Tray Mode Entry ---
        if data_type == "TRAY":
            tray_id = data_id
            layout = tu.TRAY_LAYOUTS.get(tray_id)
            if not layout:
                self.print_terminal(f"[ERROR] Unknown tray ID: {tray_id}")
                return

            # Check if starting new tray while current tray incomplete
            if self.tray_mode and self.tray_position_index < len(self.tray_positions):
                self.print_terminal(
                    "[ERROR] Complete or skip all positions in current tray "
                    "before scanning a new tray."
                )
                return

            # Initialize session on first tray
            if not self.tray_mode or len(self.all_trays_in_session) == 0:
                self.session_id = tu.generate_session_id()
                self.print_terminal(
                    f"[SESSION] Started new multi-tray session: "
                    f"{self.session_id}"
                )

            # Set up new tray
            self.tray_mode = True
            self.current_tray_id = tray_id
            self.tray_positions = layout
            self.tray_samples[tray_id] = []  # Initialize list for this tray
            self.tray_position_index = 0

            # Show dialog with grid
            self.show_tray_dialog(tray_id, layout, self.tray_positions[0])

            tray_num = len(self.all_trays_in_session) + 1
            self.print_terminal(
                f"[TRAY MODE] Tray {tray_num}: {tray_id} loaded "
                f"({len(layout)} positions)."
            )
            self.update_sample_block(None, status_type="RESET")
            return

        # --- Tray Mode: Sequential Sample Scanning ---
        if self.tray_mode:
            # Validate if this scan type is acceptable in tray mode
            should_accept, error_msg = tu.should_accept_scan_in_tray_mode(
                data_type, self.tray_position_index, len(self.tray_positions)
            )
            if not should_accept:
                self.print_terminal(error_msg)
                return

            if data_type == "SAMPLE" or data_type == "SAMPLE_LEGACY":
                # Check if we're trying to scan more samples than positions
                if self.tray_position_index >= len(self.tray_positions):
                    self.print_terminal(
                        "[ERROR] All tray positions filled. "
                        "Scan PROCESS to assign, or scan new TRAY ID."
                    )
                    return

                pos = self.tray_positions[self.tray_position_index]
                sample_id = data_id
                if data_type == "SAMPLE_LEGACY":
                    self.print_terminal(
                        tu.format_legacy_sample_warning(sample_id)
                    )

                # Add to current tray's sample list
                self.tray_samples[self.current_tray_id].append(
                    {"position": pos, "sample_id": sample_id}
                )

                # Update grid display
                if self.tray_dialog and self.tray_dialog.winfo_exists():
                    self.tray_dialog.update_grid(pos, sample_id)

                self.print_terminal(
                    f"[TRAY] Sample '{sample_id}' → position {pos}."
                )
                self.tray_position_index += 1

                if self.tray_position_index < len(self.tray_positions):
                    next_pos = self.tray_positions[self.tray_position_index]
                    if self.tray_dialog and self.tray_dialog.winfo_exists():
                        self.tray_dialog.update_position(next_pos)
                    self.update_sample_block(sample_id, status_type="SAMPLE")
                else:
                    # Current tray complete
                    self.all_trays_in_session.append(self.current_tray_id)
                    self.close_tray_dialog()

                    sample_count = len(self.tray_samples[self.current_tray_id])
                    tray_count = len(self.all_trays_in_session)
                    total_samples = sum(
                        len(samples) for samples in self.tray_samples.values()
                    )

                    self.print_terminal(
                        f"[TRAY] Tray {self.current_tray_id} complete "
                        f"({sample_count} samples). "
                        f"{tray_count} tray(s) in session "
                        f"({total_samples} total samples)."
                    )
                    self.print_terminal(
                        "[TRAY] Scan PROCESS for this tray, "
                        "BATCH OPERATION to apply to all trays, "
                        "or scan next TRAY ID."
                    )
                    self.update_sample_block(None, status_type="RESET")
                return

            elif data_type == "PROCESS":
                # Check if this is a batch operation process
                is_valid, normalized_process, error_msg = (
                    tu.validate_and_normalize_process(data_id)
                )
                if not is_valid:
                    self.print_terminal(error_msg)

                is_batch_op = tu.is_batch_operation_process(normalized_process)

                if is_batch_op:
                    # Batch operation - apply to ALL trays in session
                    if not self.all_trays_in_session:
                        self.print_terminal(
                            "[ERROR] No completed trays in session for batch operation."
                        )
                        return
                    # Type assertion: session_id is set when tray mode is active
                    assert self.session_id is not None
                    # Set process info
                    self.current_process = normalized_process
                    self.tool_process = normalized_process
                    self.outputs_folder = tu.get_output_dir(
                        normalized_process, OUTPUTS_FOLDER
                    )
                    valid = tu.is_process_valid(normalized_process)
                    self.log_file = os.path.join(
                        self.outputs_folder,
                        tu.get_log_filename(self.tool_process, valid=valid)
                    )
                    tool_display_name = tu.get_tool_display_name(
                        self.tool_process
                    )
                    process_display_name = tu.get_process_display_name(
                        self.current_process
                    )

                    # Create batch operation records for all trays
                    batch_records = tu.create_batch_operation_records(
                        self.username,
                        self.tray_samples,
                        self.current_process,
                        self.session_id
                    )
                    self.log_records.extend(batch_records)

                    # Log each record
                    for record in batch_records:
                        self.print_terminal(tu.format_log_message(record))

                    tray_count = len(self.all_trays_in_session)
                    sample_count = len(batch_records)
                    self.print_terminal(
                        f"[BATCH OPERATION] '{process_display_name}' applied to "
                        f"{tray_count} tray(s) ({sample_count} samples) - "
                        f"Session: {self.session_id}"
                    )

                    # End multi-tray session
                    self.tray_mode = False
                    self.current_tray_id = None
                    self.tray_positions = []
                    self.tray_samples = {}
                    self.tray_position_index = 0
                    self.all_trays_in_session = []
                    self.session_id = None

                    self.title(f"Lab Process Tracker GUI - {tool_display_name}")
                    self.log_file_label.config(
                        text=f"Log will be saved to: {self.log_file}",
                        fg="orange" if not valid else "gray"
                    )
                    self.update_sample_block(None, status_type="RESET")
                    self.update_process_block(self.current_process, valid=valid)

                else:
                    # Regular process - apply to current tray only
                    # Mark current tray as complete if it has samples
                    if (
                        self.current_tray_id and
                        self.current_tray_id not in self.all_trays_in_session and
                        self.tray_samples.get(self.current_tray_id)
                    ):
                        self.all_trays_in_session.append(self.current_tray_id)
                        self.close_tray_dialog()

                    if not self.all_trays_in_session:
                        self.print_terminal(
                            "[ERROR] No samples in current tray to assign process."
                        )
                        return

                    self.current_process = normalized_process
                    self.tool_process = normalized_process
                    self.outputs_folder = tu.get_output_dir(
                        normalized_process, OUTPUTS_FOLDER
                    )
                    valid = tu.is_process_valid(normalized_process)
                    self.log_file = os.path.join(
                        self.outputs_folder,
                        tu.get_log_filename(self.tool_process, valid=valid)
                    )
                    tool_display_name = tu.get_tool_display_name(self.tool_process)

                    # Type assertion: current_tray_id is set in tray mode
                    assert self.current_tray_id is not None

                    # Log samples from current tray only
                    current_tray_samples = self.tray_samples[self.current_tray_id]
                    batch_records = tu.create_tray_batch_records(
                        self.username,
                        self.current_tray_id,
                        current_tray_samples,
                        self.current_process
                    )
                    self.log_records.extend(batch_records)
                    for record in batch_records:
                        self.print_terminal(tu.format_log_message(record))

                    self.print_terminal(
                        f"[TRAY] Process '{tool_display_name}' assigned to "
                        f"{len(current_tray_samples)} sample(s) in tray "
                        f"{self.current_tray_id}."
                    )
                    self.print_terminal(
                        "[TRAY] Ready to scan next TRAY or BATCH OPERATION process."
                    )

                    self.title(f"Lab Process Tracker GUI - {tool_display_name}")
                    self.log_file_label.config(
                        text=f"Log will be saved to: {self.log_file}",
                        fg="orange" if not valid else "gray"
                    )
                    self.update_process_block(self.current_process, valid=valid)
                    # Stay in tray mode for next tray
                return

        # --- Normal Mode (no tray) ---
        if data_type == "PROCESS":
            is_valid, normalized_process, error_msg = (
                tu.validate_and_normalize_process(data_id)
            )

            # Auto-save if switching processes
            # Type check: ensure tool_process is not None
            if self.tool_process is not None and tu.should_auto_save_on_process_switch(
                self.tool_process,
                normalized_process,
                len(self.log_records) > 0
            ):
                # Type assertion: log_file set when tool_process is set
                assert self.log_file is not None

                record_count = len(self.log_records)
                old_log_file = os.path.basename(self.log_file)
                success, _ = tu.save_log_to_csv(
                    self.log_records,
                    self.log_file,
                    self.outputs_folder
                )
                if success:
                    self.log_records.clear()
                    self.print_terminal(
                        tu.format_auto_save_message(
                            record_count, old_log_file
                        )
                    )

            # Always allow setting the process, but warn if invalid
            if not is_valid:
                self.print_terminal(error_msg)

            self.current_process = normalized_process

            # Set quarantine folder and file if invalid
            self.outputs_folder = tu.get_output_dir(
                normalized_process, OUTPUTS_FOLDER
            )
            valid = tu.is_process_valid(normalized_process)
            self.tool_process = normalized_process
            self.log_file = os.path.join(
                self.outputs_folder,
                tu.get_log_filename(self.tool_process, valid=valid)
            )
            tool_display_name = tu.get_tool_display_name(self.tool_process)
            self.title(f"Lab Process Tracker GUI - {tool_display_name}")
            self.log_file_label.config(
                text=f"Log will be saved to: {self.log_file}"
            )
            if not valid:
                self.log_file_label.config(fg="orange")
            else:
                self.log_file_label.config(fg="gray")
            self.print_terminal(f">>> TOOL SET: '{tool_display_name}'")
            self.print_terminal(f">>> Log file: {self.log_file}")

            self.update_process_block(self.current_process, valid=valid)
            self.update_sample_block(None, status_type="RESET")
            process_display_name = tu.get_process_display_name(
                self.current_process
            )
            self.print_terminal(
                f">>> PROCESS UPDATED: Now running: '{process_display_name}'"
            )
        elif tu.is_sample_type(data_type):
            if not self.tool_process or not self.current_process:
                self.print_terminal(
                    "[ALERT] Cannot log sample. "
                    "Please scan a PROCESS QR code first."
                )
                self.update_sample_block(
                    "No tool/process set", status_type="ALERT"
                )
            else:
                if data_type == "SAMPLE_LEGACY":
                    self.print_terminal(
                        tu.format_legacy_sample_warning(data_id)
                    )
                self.log_scan_event(self.current_process, sample_id=data_id)
                self.update_sample_block(data_id, status_type="SAMPLE")
        elif tu.is_batch_type(data_type):
            if not self.tool_process or not self.current_process:
                self.print_terminal(
                    "[ALERT] Cannot log batch. "
                    "Please scan a PROCESS QR code first."
                )
                self.update_sample_block(
                    "No tool/process set", status_type="ALERT"
                )
            else:
                self.log_scan_event(self.current_process, batch_id=data_id)
                self.update_sample_block(data_id, status_type="BATCH")
        else:
            self.print_terminal(
                f"[ERROR] Unknown data type: '{data_type}'"
            )
            self.update_sample_block(data_type, status_type="ERROR")

    def log_scan_event(self, process_name, sample_id="", batch_id=""):
        # Type assertion: username checked at start of handle_scan
        assert self.username is not None
        record = tu.create_log_record(
            self.username, process_name, sample_id, batch_id
        )
        self.log_records.append(record)
        self.print_terminal(tu.format_log_message(record))

    def undo_last_scan(self):
        if self.checkout_mode:
            if self.checkout_records:
                removed = self.checkout_records.pop()
                self.print_terminal(
                    f"[UNDO] Removed checkout: '{removed['SampleID']}'"
                )
            else:
                self.print_terminal("[INFO] No checkout records to undo.")
            return
        if self.tray_mode and self.current_tray_id:
            # Undo in tray mode: remove last tray sample
            current_tray_samples = self.tray_samples.get(self.current_tray_id, [])
            if current_tray_samples and self.tray_position_index > 0:
                removed_sample = current_tray_samples.pop()
                self.tray_position_index = self.tray_positions.index(
                    removed_sample['position']
                )
                prev_pos = self.tray_positions[self.tray_position_index]

                # If tray was marked complete, un-complete it
                if self.current_tray_id in self.all_trays_in_session:
                    self.all_trays_in_session.remove(self.current_tray_id)

                # Update grid to clear the cell
                if self.tray_dialog and self.tray_dialog.winfo_exists():
                    cell_data = self.tray_dialog.grid_cells.get(
                        removed_sample['position']
                    )
                    if cell_data:
                        cell_data['sample_label'].config(text="")
                        cell_data['frame'].config(bg="#ffffff")
                    self.tray_dialog.update_position(prev_pos)
                else:
                    self.show_tray_dialog(
                        self.current_tray_id, self.tray_positions, prev_pos
                    )
                    for entry in current_tray_samples:
                        self.tray_dialog.update_grid(
                            entry['position'], entry['sample_id']
                        )

                self.print_terminal(
                    f"[UNDO] Removed sample '{removed_sample['sample_id']}' "
                    f"from position {removed_sample['position']}."
                )
                self.update_sample_block("Last scan undone", status_type="UNDO")
            else:
                self.print_terminal("[INFO] No tray samples to undo.")
        else:
            # Normal mode undo (existing functionality)
            if not self.log_records:
                self.print_terminal("[INFO] No scans to undo.")
                return
            removed_record = self.log_records.pop()
            self.print_terminal(tu.format_undo_message(removed_record))
            self.update_sample_block("Last scan undone", status_type="UNDO")

    def save_log(self):
        if self.checkout_mode:
            self.save_checkout_log()
            return
        if not self.log_file:
            self.print_terminal(
                "[ERROR] No log file defined. "
                "Please scan a PROCESS QR code first."
            )
            return

        success, message = tu.save_log_to_csv(
            self.log_records, self.log_file, OUTPUTS_FOLDER
        )

        if success:
            self.print_terminal(f"[SUCCESS] {message}")
            self.log_records.clear()
        else:
            self.print_terminal(f"[CRITICAL ERROR] {message}")

    def exit_app(self):
        """Exit the application with prompt to save unsaved data."""
        # Close tray dialog if open
        self.close_tray_dialog()

        # Prompt to save pending checkout records before exiting
        if self.checkout_records:
            count = len(self.checkout_records)
            if messagebox.askyesno(
                "Unsaved Checkout Data",
                f"You have {count} unsaved checkout record(s). "
                "Save before exiting?"
            ):
                self.save_checkout_log()

        if self.log_records:
            count = len(self.log_records)
            if messagebox.askyesno(
                "Unsaved Data",
                f"You have {count} unsaved record(s). "
                "Save before exiting?"
            ):
                self.save_log()
                if not self.log_records:
                    self.destroy()
                else:
                    if messagebox.askyesno(
                        "Save Failed",
                        "Failed to save. Exit anyway?"
                    ):
                        self.destroy()
            else:
                # Second prompt: Confirm exit without saving
                if messagebox.askyesno(
                    "Confirm Exit",
                    "Exit without saving? "
                    "All unsaved data will be lost."
                ):
                    self.destroy()
        else:
            self.destroy()

    def print_terminal(self, msg):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, msg + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def update_process_block(self, process_name, valid=True):
        if process_name:
            color = tu.get_process_color(process_name)
            display_name = tu.get_process_display_name(process_name)
            text = display_name
            if not tu.is_process_valid(process_name):
                text += "\n[UNAPPROVED — quarantined]"
        else:
            color = "grey"
            text = "No process"
        self.process_frame.config(bg=color)
        self.process_label.config(bg=color, text=text)

    def update_sample_block(self, sample_info, status_type="SAMPLE"):
        # Sample box stays neutral gray, only text changes
        if status_type == "SAMPLE":
            # Display "Sample" prefix above the sample ID
            self.sample_label.config(
                text=f"Sample\n{sample_info}",
                font=("Arial", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "BATCH":
            # Display "Batch" prefix for batch IDs
            self.sample_label.config(
                text=f"Batch\n{sample_info}",
                font=("Arial", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "UNDO":
            self.sample_label.config(
                text="Last scan undone",
                font=("Arial", FONT_SIZE_LARGE, "bold")
            )
        elif status_type == "ALERT":
            self.sample_label.config(
                text=sample_info,
                font=("Arial", FONT_SIZE_LARGE, "bold")
            )
        elif status_type == "ERROR":
            self.sample_label.config(
                text=f"ERROR\n{sample_info}",
                font=("Arial", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "RESET":
            self.sample_label.config(
                text="No sample",
                font=("Arial", FONT_SIZE_LARGE, "bold")
            )
        else:
            self.sample_label.config(
                text="No sample",
                font=("Arial", FONT_SIZE_LARGE, "bold")
            )


if __name__ == "__main__":
    app = ProcessTrackerGUI()
    app.mainloop()
