[![Version](https://img.shields.io/badge/version-v0.2.1-blue.svg)](https://github.com/rdaxini/process_tracking)

<div align="left">
  <img src="logo/logo_text.jpg" alt="Sample Tracker Logo" width="400">
</div>

# Lab Process Tracker

A tracking application for lab operations with a graphical user interface.
Track processes and sample scans using QR code input, with logs saved to CSV files.

## Features

- **Graphical User Interface (GUI)**
- **Per-Tool Logging:** Each tool/process has its own dedicated CSV log file
- Track tool, process, and sample scans with timestamps
- RESET (username), UNDO, SAVE, and EXIT commands
- Centralized process/tool configuration via JSON file

## Start the tracker

After downloading the repository from GitHub, you can run the tracker in multiple ways:

### 1. Run the standalone executable

Navigate to the `exe/dist` folder and double-click the executable:
- **`process_tracker_gui_v<version>.exe`**

### 2. Run the GUI from source

```bash
python src/process_tracker_gui.py
```

The GUI provides:
- Visual status blocks for current process and sample
- Color-coded feedback for different processes
- Terminal-style activity log
- Button controls for SAVE, UNDO, EXIT, and Reset user

No additional installations are required.

## How to use

1. **Enter your NREL username** when prompted
  - Type your NREL username and click "Set" or press Enter
  - Use "Reset" button to change users

2. **Scan a PROCESS QR code** to set the tool/process:
   - This must be done first before scanning any samples
   - The first process scanned determines the log file name
     (e.g., `scan_log_c215ss_jv.csv`)
   - Valid processes are defined in `tools_processes.json`

3. **Scan SAMPLE QR codes** to log samples under the current process

4. **Switch between processes:** When you scan a different process QR code, the application
   automatically saves your current records and switches to the new process. You'll see
   a notification showing how many records were saved.

5. **Use commands:**
   - `UNDO` — Remove the last scan from the session (not saved to log)
   - `SAVE` — Save all current session scans to the tool-specific CSV file
  - `RESET` — Change the user by clicking "Reset" button
   - `EXIT` — Exit the tracker (prompts to save if there are unsaved scans)

**QR Code Format:**
- Process QR codes must contain: `P%:abbreviated_name` (e.g., `P%:c215ss_jv`)
- Sample QR codes must contain: `S%:SampleID` (e.g., `S%:2511-09`)
- The prefixes (`P%:` and `S%:`) must be uppercase and include the colon
- Process names are case-insensitive (automatically normalized to lowercase)
- Sample IDs preserve their original case
- Legacy sample QR codes in format `####-##` (e.g., `2511-09`) are supported
  - A warning will be displayed when legacy format is detected
  - No `S%:` prefix required for legacy samples

**Examples:**
- `P%:c215ss_jv` — Sets process to C215 Solar Simulator JV measurement
- `S%:2511-09` — Logs sample 2511-09 under the current process
- `2511-09` — Legacy format, automatically recognized as a sample (logs with warning)

**Process Validation & Quarantine Logging:**

When you scan a process QR code (`P%:process_name`):

- If the process **is listed in `tools_processes.json`**:
  - The process is set and scans are logged to a dedicated CSV file (e.g., `scan_log_c215ss_jv.csv`).
  - The process block is color-coded and the activity log confirms the process/tool.

- If the process **is NOT listed in `tools_processes.json`**:
  - You will see a **WARNING** in the activity log and process block.
  - All scans for this process are logged in a **quarantine CSV file** named `scan_log_UNAPPROVED_<process_name>.csv` in `outputs/unapproved/`.
  - You can continue logging samples for this process, but records are kept separate from approved processes.
  - **Contact Rajiv.Daxini@nrel.gov** to request adding new processes to the database.

The quarantine logic allows rapid deployment on new systems without blocking workflow, while ensuring unapproved processes are tracked and not mixed with approved logs.

## Output

- Logs are saved to tool-specific CSV files (e.g., `scan_log_c215ss_jv.csv`,
  `scan_log_bd8_xrd.csv`)
- **Multi-process sessions:** When you switch between different processes, the
  application automatically saves records to the appropriate file for each process
- Default output locations:
  - **Running from source:** `outputs/` folder in the project directory
  - **Running as executable:** `~/Documents/process_tracking_outputs/`
- If a log file already exists, new session outputs will be appended

## Folder Structure

```
process_tracking/
├── src/                           # Main application code
│   ├── tracker_utils.py           # Shared core utilities and business logic
│   └── process_tracker_gui.py     # GUI application (Tkinter)
├── tools_processes.json           # Central database of all tools/processes
├── scripts/                       # Utility and build scripts
│   ├── create_exe.py              # Build script for creating executable
│   └── run_tests.py               # Test runner script
├── tests/                         # Test suite
│   ├── __init__.py
│   └── test_tracker_utils.py      # Core functionality tests
├── outputs/                       # Default output location (auto-created)
│   ├── scan_log_c215ss_jv.csv     # Example: c215ss_jv tool log
│   ├── scan_log_bd8_xrd.csv       # Example: bd8_xrd tool log
│   └── ...                        # One CSV per tool/process
├── exe/                           # Compiled executable
│   └── dist/
│       └── process_tracker_gui_v<version>.exe
├── .github/                       # CI/CD workflows
│   └── workflows/
│       └── pytest.yml             # Automated testing workflow
├── pyproject.toml                 # Project metadata and dependencies
├── README.md
└── ...
```

## Requirements

- Python 3.10 or higher

All dependencies are managed via `pyproject.toml`.
No external dependencies required unless using optional features or development tools.

## For Developers

If you want to install and run the repository directly (for development or
customization), you can install it using pip:

```bash
pip install .
```

If you also want to install optional dependencies for building standalone executables
(using PyInstaller) or running tests (using pytest), use:

```bash
# Install build dependencies (PyInstaller)
pip install .[build]

# Install test dependencies (pytest, pytest-cov)
pip install .[test]

# Install all development dependencies (build + test)
pip install .[dev]
```

#### Building Executable

To build the standalone executable:

```bash
python scripts/create_exe.py
```

The executable will be created in `exe/dist/` directory:
- `process_tracker_gui_v<version>.exe` - GUI version (no console window)

**Note:** You need PyInstaller installed: `pip install .[build]`

#### Running Tests

To run the test suite:

```bash
# Using the test runner script
python scripts/run_tests.py

# Or directly with pytest
pytest tests/ -v

# With coverage report (requires pytest-cov)
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

**Note:** You need to install the test dependencies first: `pip install .[test]`

The test suite focuses on the testable core logic in `tracker_utils.py`. The CLI main
loop and GUI are validated through manual testing and usage.

## Test Coverage

Test coverage reports are generated in `htmlcov/` after running tests.
See the terminal output for summary and open `htmlcov/index.html` for details.
