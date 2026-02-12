"""
GUI components for the Process Tracker GUI application.
Contains reusable dialog and widget classes.
"""
import tkinter as tk

# Color constants for dialog components
BG_COLOR_DIALOG = "#eaf6ff"
BG_COLOR_GRID_CELL = "#ffffff"
BG_COLOR_GRID_COMPLETE = "#d5f4e6"  # Light green


class TrayPositionDialog(tk.Toplevel):
    """Popup dialog for prompting user to scan samples for tray
    positions with visual grid."""

    def __init__(
        self, parent, tray_id, positions, on_skip_callback,
        on_skip_all_callback
    ):
        super().__init__(parent)
        self.title(f"Tray Mode - {tray_id}")
        self.configure(bg=BG_COLOR_DIALOG)
        self.resizable(False, False)

        self.parent = parent
        self.tray_id = tray_id
        self.positions = positions
        self.on_skip_callback = on_skip_callback
        self.on_skip_all_callback = on_skip_all_callback

        # Calculate grid dimensions from positions
        self.rows, self.cols = self._calculate_grid_dimensions(positions)

        # Cell size based on grid size (smaller cells for larger grids)
        if self.rows <= 2:
            self.cell_size = 80
        elif self.rows <= 5:
            self.cell_size = 60
        else:
            self.cell_size = 50

        # Calculate dialog size based on grid
        grid_width = self.cols * self.cell_size + 40
        grid_height = self.rows * self.cell_size + 40
        dialog_width = max(600, grid_width + 40)
        dialog_height = grid_height + 200  # Extra space for message and buttons
        self.geometry(f"{dialog_width}x{dialog_height}")

        # Make dialog stay on top but NOT modal (so QR entry stays accessible)
        self.transient(parent)
        self.attributes('-topmost', True)

        # Center the dialog on parent
        self.update_idletasks()
        x = (parent.winfo_x() + (parent.winfo_width() // 2)
             - (self.winfo_width() // 2))
        y = (parent.winfo_y() + (parent.winfo_height() // 2)
             - (self.winfo_height() // 2))
        self.geometry(f"+{x}+{y}")

        # Message label
        self.message_label = tk.Label(
            self,
            text="Initializing...",
            bg=BG_COLOR_DIALOG,
            fg="#1a5276",
            font=("Arial", 14, "bold"),
            wraplength=dialog_width - 40
        )
        self.message_label.pack(pady=(10, 10))

        # Grid frame
        self.grid_frame = tk.Frame(
            self, bg=BG_COLOR_GRID_CELL, relief=tk.RIDGE, borderwidth=2
        )
        self.grid_frame.pack(pady=10, padx=20)

        # Create grid cells
        self.grid_cells = {}
        self._create_grid()

        # Buttons frame
        btn_frame = tk.Frame(self, bg=BG_COLOR_DIALOG)
        btn_frame.pack(pady=(10, 20))

        # Skip current button
        self.skip_btn = tk.Button(
            btn_frame,
            text="Skip Current",
            command=self.skip_current,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            padx=15,
            pady=8,
            width=15
        )
        self.skip_btn.grid(row=0, column=0, padx=5)

        # Skip all button
        self.skip_all_btn = tk.Button(
            btn_frame,
            text="Skip All Remaining",
            command=self.skip_all_remaining,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.RAISED,
            padx=15,
            pady=8,
            width=15
        )
        self.skip_all_btn.grid(row=0, column=1, padx=5)

        # Handle window close (X button) - treat as skip all
        self.protocol("WM_DELETE_WINDOW", self.skip_all_remaining)

    def _calculate_grid_dimensions(self, positions):
        """Calculate grid dimensions from position strings (e.g., A1, B2, H8)."""
        if not positions:
            return 1, 1

        max_row = 0
        max_col = 0
        for pos in positions:
            # Parse position like "A1", "B2", "H8"
            row_letter = pos[0]
            col_num = int(pos[1:])
            row_index = ord(row_letter.upper()) - ord('A')
            max_row = max(max_row, row_index)
            max_col = max(max_col, col_num)

        return max_row + 1, max_col

    def _create_grid(self):
        """Create the visual grid of tray positions. Letters are x-axis, numbers are
        y-axis. Scan order: left->right, bottom->top."""
        row_numbers = sorted({int(pos[1:]) for pos in self.positions})
        col_letters = sorted({pos[0] for pos in self.positions})

        letter_to_x = {letter: idx for idx, letter in enumerate(col_letters)}
        number_to_y = {num: idx for idx, num in enumerate(row_numbers)}
        num_rows = len(row_numbers)

        for pos in self.positions:
            col_letter = pos[0]
            row_number = int(pos[1:])
            x_index = letter_to_x[col_letter]
            # y_index: 0 is bottom (lowest number), so flip so 0 is bottom
            y_index = num_rows - 1 - number_to_y[row_number]

            cell = tk.Frame(
                self.grid_frame,
                width=self.cell_size,
                height=self.cell_size,
                bg=BG_COLOR_GRID_CELL,
                relief=tk.RAISED,
                borderwidth=1
            )
            cell.grid(row=y_index, column=x_index, padx=2, pady=2)
            cell.grid_propagate(False)

            pos_label = tk.Label(
                cell,
                text=pos,
                bg=BG_COLOR_GRID_CELL,
                fg="#2c3e50",
                font=("Arial", 10, "bold")
            )
            pos_label.pack(pady=(5, 0))

            sample_label = tk.Label(
                cell,
                text="",
                bg=BG_COLOR_GRID_CELL,
                fg="#27ae60",
                font=("Arial", 8),
                wraplength=self.cell_size - 10
            )
            sample_label.pack(pady=(2, 0), expand=True)

            self.grid_cells[pos] = {
                'frame': cell,
                'sample_label': sample_label
            }

    def update_position(self, position):
        """Update the position being prompted for."""
        prompt_text = (
            f"Scan sample for position: {position}\n"
        )
        self.message_label.config(text=prompt_text)

    def update_grid(self, position, sample_id):
        """Update a grid cell with the scanned sample ID."""
        if position in self.grid_cells:
            cell_data = self.grid_cells[position]
            cell_data['sample_label'].config(text=sample_id)
            cell_data['frame'].config(bg=BG_COLOR_GRID_COMPLETE)  # Light green

    def skip_current(self):
        """Call the skip current callback."""
        self.on_skip_callback()
        # Refocus QR entry in parent window
        self.parent.qr_entry.focus_set()

    def skip_all_remaining(self):
        """Call the skip all callback and close dialog."""
        # Refocus QR entry before closing
        self.parent.qr_entry.focus_set()
        self.on_skip_all_callback()
        self.destroy()

    def close(self):
        """Close the dialog."""
        self.destroy()
