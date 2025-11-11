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

You can run the tracker in two ways:

### 1. Run the standalone executable

Navigate to the `exe/dist` folder and double-click the `process_tracker_v<version>.exe` file to start the tracker.

### 2. Run the Python script directly

#### Navigate to the repository directory:
```bash
cd path/to/process_tracking
```

#### Run the tracker:
```bash
python scripts/process_tracker.py
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

- All logs are saved in `outputs/scan_log.csv` (created automatically if missing).
- If a scan log .csv file already exists, new session outputs will be appended to the
  existing file.

## Folder Structure

```
├── outputs/
│   └── scan_log.csv
├── scripts/
│   └── process_tracker.py
├── exe/
│   └── dist/
│       └── process_tracker_v<version>.exe
├── README.md
└── ...
```

## Requirements

- Python 3.13.

### For Developers

If you want to install and run the repository directly (for development or customization), you can install it using pip:

```bash
pip install .
```

If you also want to install optional dependencies for building a standalone executable (using PyInstaller), use:

```bash
pip install .[build]
```

Developed and tested in Python 3.13 only.
No external dependencies required unless using optional features.

## TODO

- Add auto-save feature when switching processes
- Print session summary/stats at end of session
- Add user entry field for operator at start of session

---
