# Lab Process Tracker

A simple command-line tool for tracking lab processes and sample scans using
QR code input. The scan log is saved to a .csv file in the `outputs` folder.

## Features

- Track process and sample scans
- Undo the last scan (`UNDO`)
- Save logs to CSV (`SAVE`)
- Exit safely with optional save (`EXIT`)
- Organized output files in the `outputs` directory

## Start the tracker

after downloading the repository from GitHub, you can run the tracker in two ways:

### 1. Run the standalone executable

Navigate to the `exe/dist` folder and double-click the `process_tracker_v<version>.exe`
file to start the tracker.

No additional installations are required.

### 2. Run the Python script directly
To run the Python script directly out of a terminal, after downloading the repository
and installing Python:

#### Navigate to the repository directory:
```bash
cd path/to/process_tracking
```

#### Run the tracker:
```bash
python src/process_tracker.py
```

## How to use
**Scan QR codes:**
   - Scan a process QR code to set the current process.
   - Scan a sample QR code to log a sample under the current process.

Note: QR codes must contain either the `PROCESS:` tag or `SAMPLE:` tag in order to be
succesfully identified as a process or sample scan event, respectively.

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
- **Custom output location:** You can specify a custom output directory by providing a
  command-line argument when starting the tracker:

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
│   └── process_tracker.py         # Core tracker application
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
├── pyproject.toml                 # Project metadata and dependencies
├── README.md
└── ...
```

## Requirements

- Python 3.10 or higher.

Developed on Python 3.13, tested on 3.10<=Python<=3.13.
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
- Update README.md for tox testing on multiple python versions
---
