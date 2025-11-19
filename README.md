# Lab Process Tracker

A process tracking application for lab operations with both command-line and GUI interfaces.
Track processes and sample scans using QR code input, with logs saved to CSV files.

## Features

- Dual Interface: Command-line (CLI) and graphical user interface (GUI)
- Per-Tool Logging: Each tool/process has its own dedicated CSV log file
- Track process and sample scans with timestamps
- Undo the last scan (`UNDO`)
- Save logs to CSV (`SAVE`)
- Exit safely with optional save (`EXIT`)
- Organized output files with configurable locations
- Modern GUI with color-coded status indicators

## Start the tracker

After downloading the repository from GitHub, you can run the tracker in multiple ways:

### 1. Run the GUI (Graphical Interface)

```bash
python src/process_tracker_gui.py
```

The GUI provides:
- Visual status blocks for current process and sample
- Color-coded feedback for different processes
- Terminal-style activity log
- Button controls for SAVE, UNDO, and EXIT

### 2. Run the CLI (Command-Line Interface)

```bash
python src/process_tracker.py
```

### 3. Run the standalone executable

Navigate to the `exe/dist` folder and double-click the `process_tracker_v<version>.exe`
file to start the tracker.

No additional installations are required.

## How to use

1. **Enter operator name** when prompted

2. **Scan a PROCESS QR code** to set the tool/process:
   - This must be done first before scanning any samples
   - The first process scanned determines the log file name (e.g., `scan_log_C215SS_JV.csv`)
   - Valid processes: C215SS_JV, BD8_XRD, HSEM_SEM, OEQE_EQE, SUPSS_JV, PXT10_JV, OpProf_PROFIL, PAE_EVAP

3. **Scan SAMPLE QR codes** to log samples under the current process

4. **Use commands:**
   - `UNDO` — Remove the last scan from the session (not saved to log)
   - `SAVE` — Save all current session scans to the tool-specific CSV file
   - `EXIT` — Exit the tracker (prompts to save if there are unsaved scans)

**QR Code Format:**
- Process QR codes must contain: `PROCESS:ProcessName` (e.g., `PROCESS:C215SS_JV`)
- Sample QR codes must contain: `SAMPLE:SampleID` (e.g., `SAMPLE:2511-09`)

**Process Validation:**
If you scan a process that is not in the approved list, you will receive an error
message with:
- The list of available processes
- Contact information to request adding new processes (Rajiv.Daxini@nrel.gov)

## Output

- Logs are saved to tool-specific CSV files (e.g., `scan_log_C215SS_JV.csv`, `scan_log_BD8_XRD.csv`)
- Default output locations:
  - **Running from source:** `outputs/` folder in the project directory
  - **Running as executable:** `~/Documents/process_tracking_outputs/`
- If a log file already exists, new session outputs will be appended
- **Custom output location (CLI only):**

  ```bash
  python src/process_tracker.py --output-dir /path/to/your/folder
  ```
  or, for the executable:
  ```
  process_tracker_v<version>.exe --output-dir C:\path\to\your\folder
  ```

## Folder Structure

```
process_tracking/
├── src/                           # Main application code
│   ├── tracker_utils.py           # Shared core utilities and business logic
│   ├── process_tracker.py         # CLI application
│   └── process_tracker_gui.py     # GUI application (Tkinter)
├── scripts/                       # Utility and build scripts
│   ├── create_exe.py              # Build script for creating executables
│   └── run_tests.py               # Test runner script
├── tests/                         # Test suite
│   ├── __init__.py
│   └── test_tracker_utils.py      # Pytest-based tests
├── outputs/                       # Default output location (auto-created)
│   ├── scan_log_C215SS_JV.csv     # Example: C215SS_JV tool log
│   ├── scan_log_BD8_XRD.csv       # Example: BD8_XRD tool log
│   └── ...                        # One CSV per tool/process
├── exe/                           # Compiled executables
│   └── dist/
│       └── process_tracker_v<version>.exe
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

### For Developers

If you want to install and run the repository directly (for development or
customization), you can install it using pip:

```bash
pip install .
```

If you also want to install optional dependencies for building a standalone executable
(using PyInstaller) or running tests (using pytest), use:

```bash
# Install build dependencies (PyInstaller)
pip install .[build]

# Install test dependencies (pytest, pytest-cov)
pip install .[test]

# Install all development dependencies (build + test)
pip install .[dev]
```

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

## TODO

- Add auto-save feature when switching processes
- Print session summary/stats at end of session
- Add platen and position tracking

