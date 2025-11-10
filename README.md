# Lab Process Tracker

A simple command-line tool for tracking lab processes and sample scans using
QR code input. The scan log is saved to a a .csv file in the `outputs` folder.

## Features

- Track process and sample scans
- Undo the last scan (`UNDO`)
- Save logs to CSV (`SAVE`)
- Exit safely with optional save (`EXIT`)
- Organized output files in the `outputs` directory

## Usage

### Run the tracker

#### Navigate to the repository directory:
```bash
cd path/to/process_tracking
```

#### Run the tracker:
```bash
python scripts/process_tracker.py
```

3. **Scan QR codes:**
   - Enter `PROCESS:ProcessName` to set the current process.
   - Enter `SAMPLE:SampleID` to log a sample under the current process.

Note: QR codes must contain either the `PROCESS:` tag or `SAMPLE:` tag in order to be
succesfully identified as a process or sample scan event, respectively.

3. **Commands:**
   - `UNDO` — Remove the last scan from the session (not saved to log).
   - `SAVE` — Save all current session scans to `outputs/scan_log.csv`.
   - `EXIT` — Exit the tracker (prompts to save if there are unsaved scans).

## Output

- All logs are saved in `outputs/scan_log.csv` (created automatically if missing).

## Folder Structure

```
process_tracking/
├── outputs/
│   └── scan_log.csv
├── scripts/
│   └── process_tracker.py
└── README.md
```

## Requirements

- Python 3.13.

### Optional

- For building a standalone executable with PyInstaller, install with:
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
