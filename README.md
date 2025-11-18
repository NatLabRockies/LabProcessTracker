# Lab Process Tracker

A process tracking application for lab operations with both command-line and GUI interfaces.
Track processes and sample scans using QR code input, with logs saved to CSV files.

## Features

- **Dual Interface:** Command-line (CLI) and graphical user interface (GUI)
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
- Color-coded feedback (red=process, green=sample, yellow=undo, orange=alert)
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

**Scan QR codes:**
   - Scan a process QR code to set the current process.
   - Scan a sample QR code to log a sample under the current process.

Note: QR codes must contain either the `PROCESS:` tag or `SAMPLE:` tag in order to be
successfully identified as a process or sample scan event, respectively.

**Commands:**
   - `UNDO` — Remove the last scan from the session (not saved to log).
   - `SAVE` — Save all current session scans to `outputs/scan_log.csv`.
   - `EXIT` — Exit the tracker (prompts to save if there are unsaved scans).

## Output

- By default, logs are saved in `outputs/scan_log.csv`:
  - **If running from source (with project folder):** logs are saved to the `outputs`
    folder in the project directory (created automatically if missing).
  - **If running as a standalone executable (.exe) without the project folder:** logs
    are saved to a folder named `process_tracking_outputs` in your user's Documents
    directory (e.g., `~/Documents/process_tracking_outputs/scan_log.csv`).
- If a scan log .csv file already exists, new session outputs will be appended to the
  existing file.
- **Custom output location (CLI only):** You can specify a custom output directoryby
  providing a command-line argument when starting the tracker:

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
│   └── test_process_tracker.py    # Pytest-based tests
├── outputs/                       # Default output location (auto-created)
│   └── scan_log.csv               # Scan log CSV file
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
- Tkinter (included with most Python installations)

Developed on Python 3.13, tested on 3.10 ≤ Python ≤ 3.13.
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
pytest tests/ -v --cov=src --cov-report=term-missing
```

**Note:** You need to install the test dependencies first: `pip install .[test]`

## TODO

- Add auto-save feature when switching processes
- Print session summary/stats at end of session
- Add platen and position tracking
- Update QR code tags (SAMPLE:/PROCESS:), add tool QR
- Create GUI and GUI executable build
