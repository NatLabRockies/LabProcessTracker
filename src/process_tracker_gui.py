import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import os
import tracker_utils as tu
from gui_components import TrayPositionDialog

OUTPUTS_FOLDER = tu.get_default_output_dir()

# Font size constants
FONT_SIZE_LARGE = 26
FONT_SIZE_MEDIUM = 22


# --- GUI Class ---
class ProcessTrackerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lab Process Tracker")
        self.geometry("900x800")
        self.minsize(800, 700)

        # Modern dark theme colors
        self.colors = {
            'bg_dark': '#2c3e50',
            'bg_medium': '#34495e',
            'bg_light': '#ecf0f1',
            'accent': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'danger': '#e74c3c',
            'text_light': '#ecf0f1',
            'text_dark': '#2c3e50',
            'border': '#bdc3c7'
        }

        self.configure(bg=self.colors['bg_dark'])

        # Apply modern ttk theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.current_process = None
        self.tool_process = None
        self.log_file = None
        self.operator_name = None
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

        self.create_widgets()

        # Handle window close event (X button)
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def configure_styles(self):
        """Configure ttk styles for modern appearance."""
        # Button style
        self.style.configure(
            'Modern.TButton',
            background=self.colors['accent'],
            foreground=self.colors['text_light'],
            borderwidth=0,
            focuscolor='none',
            font=('Segoe UI', 10, 'bold')
        )
        self.style.map('Modern.TButton',
                       background=[('active', '#2980b9')],
                       relief=[('pressed', 'flat')]
                       )

        # Entry style
        self.style.configure(
            'Modern.TEntry',
            fieldbackground=self.colors['bg_light'],
            borderwidth=2,
            relief='flat'
        )

    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # NLR Username Entry
        header_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = tk.Label(
            header_frame,
            text="🔬 Lab Process Tracker",
            font=('Segoe UI', 20, 'bold'),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_light']
        )
        title_label.pack()

        # Operator section with modern card design
        operator_card = tk.Frame(
            main_container,
            bg=self.colors['bg_medium'],
            relief=tk.FLAT,
            bd=0
        )
        operator_card.pack(fill=tk.X, pady=(0, 15))

        operator_inner = tk.Frame(operator_card, bg=self.colors['bg_medium'])
        operator_inner.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            operator_inner,
            text="NLR Username",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.operator_entry = tk.Entry(
            operator_inner,
            width=20,
            font=('Segoe UI', 11),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dark'],
            relief=tk.FLAT,
            bd=2
        )
        self.operator_entry.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        self.operator_entry.focus_set()
        self.operator_entry.bind("<Return>", lambda e: self.set_operator())

        self.set_operator_btn = tk.Button(
            operator_inner,
            text="✓ Set",
            command=self.set_operator,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['success'],
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        self.set_operator_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_operator_btn = tk.Button(
            operator_inner,
            text="↻ Reset",
            command=self.reset_operator,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['warning'],
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            state="disabled"
        )
        self.reset_operator_btn.pack(side=tk.LEFT)

        # Status display area
        status_container = tk.Frame(main_container, bg=self.colors['bg_dark'])
        status_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configure row weights to prevent process/sample from expanding too much
        status_container.grid_rowconfigure(0, weight=1)
        status_container.grid_rowconfigure(1, weight=1)
        status_container.grid_columnconfigure(0, weight=1)

        # Process Status Block
        self.process_frame = tk.Frame(
            status_container,
            bg='grey',
            relief=tk.FLAT,
            bd=0
        )
        self.process_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 10))

        self.process_label = tk.Label(
            self.process_frame,
            text="No process set",
            font=('Segoe UI', FONT_SIZE_LARGE, 'bold'),
            bg='grey',
            fg='white',
            wraplength=800,
            justify=tk.CENTER
        )
        self.process_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Sample Status Block
        self.sample_frame = tk.Frame(
            status_container,
            bg='#95a5a6',
            relief=tk.FLAT,
            bd=0
        )
        self.sample_frame.grid(row=1, column=0, sticky='nsew')

        self.sample_label = tk.Label(
            self.sample_frame,
            text="No sample",
            font=('Segoe UI', FONT_SIZE_LARGE, 'bold'),
            bg='#95a5a6',
            fg='white',
            wraplength=800,
            justify=tk.CENTER
        )
        self.sample_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # QR Input section (always visible, fixed size)
        input_card = tk.Frame(
            main_container,
            bg=self.colors['bg_medium']
        )
        input_card.pack(fill=tk.X, pady=(0, 10))

        input_inner = tk.Frame(input_card, bg=self.colors['bg_medium'])
        input_inner.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            input_inner,
            text="Scan QR Code:",
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light']
        ).pack(anchor=tk.W, pady=(0, 5))

        self.qr_entry = tk.Entry(
            input_inner,
            font=('Segoe UI', 12),
            bg=self.colors['bg_light'],
            fg=self.colors['text_dark'],
            relief=tk.FLAT,
            bd=2
        )
        self.qr_entry.pack(fill=tk.X, ipady=8)
        self.qr_entry.bind("<Return>", lambda e: self.handle_scan())

        # Command Buttons (always visible, fixed size)
        btn_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
        btn_frame.pack(pady=(0, 10))

        button_config = {
            'font': ('Segoe UI', 10, 'bold'),
            'relief': tk.FLAT,
            'padx': 25,
            'pady': 10,
            'cursor': 'hand2',
            'fg': 'white'
        }

        self.save_btn = tk.Button(
            btn_frame,
            text="💾 SAVE",
            command=self.save_log,
            bg=self.colors['success'],
            **button_config
        )
        self.save_btn.grid(row=0, column=0, padx=5)

        self.undo_btn = tk.Button(
            btn_frame,
            text="↶ UNDO",
            command=self.undo_last_scan,
            bg=self.colors['warning'],
            **button_config
        )
        self.undo_btn.grid(row=0, column=1, padx=5)

        self.exit_btn = tk.Button(
            btn_frame,
            text="✖ EXIT",
            command=self.exit_app,
            bg=self.colors['danger'],
            **button_config
        )
        self.exit_btn.grid(row=0, column=2, padx=5)

        # Terminal (always visible, fixed size)
        terminal_card = tk.Frame(
            main_container,
            bg=self.colors['bg_medium']
        )
        terminal_card.pack(fill=tk.X, pady=(0, 10))

        terminal_inner = tk.Frame(terminal_card, bg=self.colors['bg_medium'])
        terminal_inner.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            terminal_inner,
            text="Activity Log",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light']
        ).pack(anchor=tk.W, pady=(0, 5))

        self.terminal = scrolledtext.ScrolledText(
            terminal_inner,
            height=4,
            state='disabled',
            font=('Consolas', 10),
            bg='#1e272e',
            fg='#00ff00',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            takefocus=0

        )
        self.terminal.pack(pady=5, fill=tk.BOTH, expand=True)
        # Prevent focus and selection in the activity log
        self.terminal.bind(
            "<1>", lambda e: (self.qr_entry.focus_set(), "break")
        )
        self.terminal.bind("<FocusIn>", lambda e: self.qr_entry.focus_set())

        # Footer info
        self.log_file_label = tk.Label(
            main_container,
            text="Scan a PROCESS QR code to set the tool and begin logging.",
            font=('Segoe UI', 8),
            bg=self.colors['bg_dark'],
            fg=self.colors['border']
        )
        self.log_file_label.pack()

    def set_operator(self):
        name = self.operator_entry.get().strip()
        is_valid, error_msg = tu.validate_operator_name(name)
        if not is_valid:
            self.print_terminal(f"[ERROR] {error_msg}")
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
        """Reset the NLR username, allowing a new user to take over."""
        if not self.operator_name:
            self.print_terminal("[INFO] No NLR username is currently set.")
            return

        old_operator = self.operator_name
        self.operator_name = None
        self.operator_entry.delete(0, tk.END)
        self.operator_entry.config(state="normal")
        self.set_operator_btn.config(state="normal")
        self.reset_operator_btn.config(state="disabled")
        self.print_terminal(f"[RESET] NLR username '{old_operator}' has been reset.")
        self.print_terminal("Please enter a new NLR username to continue.")
        self.operator_entry.focus_set()

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
        if not self.operator_name:
            self.print_terminal("[ERROR] Please enter operator name first.")
            return
        # Type assertion: operator_name is not None after check
        assert self.operator_name is not None
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
            elif cmd_type == tu.RESET_OPERATOR_CMD:
                self.reset_operator()
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
                        self.operator_name,
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
                        self.operator_name,
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
        # Type assertion: operator_name checked at start of handle_scan
        assert self.operator_name is not None
        record = tu.create_log_record(
            self.operator_name, process_name, sample_id, batch_id
        )
        self.log_records.append(record)
        self.print_terminal(tu.format_log_message(record))

    def undo_last_scan(self):
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
                font=("Segoe UI", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "BATCH":
            # Display "Batch" prefix for batch IDs
            self.sample_label.config(
                text=f"Batch\n{sample_info}",
                font=("Segoe UI", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "UNDO":
            self.sample_label.config(
                text="Last scan undone",
                font=("Segoe UI", 18, "bold")
            )
        elif status_type == "ALERT":
            self.sample_label.config(
                text=sample_info,
                font=("Segoe UI", FONT_SIZE_LARGE, "bold")
            )
        elif status_type == "ERROR":
            self.sample_label.config(
                text=f"ERROR\n{sample_info}",
                font=("Segoe UI", FONT_SIZE_MEDIUM, "bold")
            )
        elif status_type == "RESET":
            self.sample_label.config(
                text="No sample",
                font=("Segoe UI", FONT_SIZE_LARGE, "bold")
            )
        else:
            self.sample_label.config(
                text="No sample",
                font=("Segoe UI", FONT_SIZE_LARGE, "bold")
            )


if __name__ == "__main__":
    app = ProcessTrackerGUI()
    app.mainloop()
