"""
Generate custom QR codes for the process tracker application.

Edit the lists in main() and run the script to generate labeled QR code images.
For testing edge cases, see generate_test_qr_codes.py
"""
from pathlib import Path
from qr_utils import generate_qr_with_label


def main():
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "custom_qr_codes"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating CUSTOM QR codes in: {output_dir}\n")

    # Sample format: S%:YYMM-NN where YY=year, MM=month, NN=sample number
    samples = [
        ("S%:2601-01", "Sample: 2601-01", "sample_2601-01.png"),
        # ("S%:2601-02", "Sample: 2601-02", "sample_2601-02.png"),
    ]

    # Format: B%:BATCH_ID
    batches = [
        ("B%:1234", "Batch: 1234", "batch_1234.png"),
        # ("B%:5678", "Batch: 5678", "batch_5678.png"),
    ]

    # Format: P%:process_abbreviation (must match tools_processes.json)
    processes = [
        ("P%:ftlb234_spinbox", "Spincoating", "process_spincoating.png"),
        # ("P%:c215ss_jv", "JV Measurement", "process_jv.png"),
    ]

    # Format: T%:TRAY_ID
    trays = [
        # ("T%:066726-S-XXX", "Tray: 066726-S-XXX (2x2)", "tray_2x2.png"),
    ]

    commands = [
        # ("SAVE", "Command: SAVE", "command_SAVE.png"),
        # ("UNDO", "Command: UNDO", "command_UNDO.png"),
        # ("EXIT", "Command: EXIT", "command_EXIT.png"),
        # ("RESET", "Command: RESET", "command_RESET.png"),
    ]

    sections = [
        ("Samples", samples),
        ("Batches", batches),
        ("Processes", processes),
        ("Trays", trays),
        ("Commands", commands),
    ]

    total_count = 0
    for label, items in sections:
        if not items:
            continue
        print(f"=== Generating {label} ===")
        for data, qr_label, filename in items:
            generate_qr_with_label(data, qr_label, filename, output_dir)
            total_count += 1
        print()

    print(f"✓ Generated {total_count} custom QR codes successfully!\n")
    print(f"Location: {output_dir}")


if __name__ == "__main__":
    main()
