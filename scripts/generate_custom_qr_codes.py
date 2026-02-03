"""
Generate custom QR codes for the process tracker application.

This script provides an easy template for generating your own QR codes.
Simply edit the lists below and run the script to generate labeled QR code images.

For testing edge cases, see generate_test_qr_codes.py
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.qr_utils import generate_qr_with_label

def main():
    # Create output directory
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "custom_qr_codes"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating CUSTOM QR codes in: {output_dir}\n")

    # ========================================================================
    # EDIT BELOW THIS LINE TO GENERATE YOUR CUSTOM QR CODES
    # ========================================================================

    # --- SAMPLES ---
    # Format: ("QR_DATA", "LABEL_TEXT", "filename.png")
    # Sample format: S%:YYMM-NN where YY=year, MM=month, NN=sample number
    samples = [
        ("S%:2601-01", "Sample: 2601-01", "sample_2601-01.png"),
        # Add more samples here:
        # ("S%:2601-02", "Sample: 2601-02", "sample_2601-02.png"),
    ]

    # --- BATCHES ---
    # Format: B%:BATCH_ID
    batches = [
        ("B%:1234", "Batch: 1234", "batch_1234.png"),
        # Add more batches here:
        # ("B%:5678", "Batch: 5678", "batch_5678.png"),
    ]

    # --- PROCESSES ---
    # Format: P%:process_abbreviation (must match tools_processes.json)
    processes = [
        ("P%:ftlb234_spinbox", "Spincoating", "process_spincoating.png"),
        # Add more processes here:
        # ("P%:c215ss_jv", "JV Measurement", "process_jv.png"),
    ]

    # --- TRAYS (if using tray tracking feature) ---
    # Format: T%:TRAY_ID
    trays = [
        # ("T%:066726-S-XXX", "Tray: 066726-S-XXX (2x2)", "tray_2x2.png"),
        # Add more trays here:
    ]

    # --- COMMANDS ---
    # Generate command QR codes if needed
    commands = [
        # ("SAVE", "Command: SAVE", "command_SAVE.png"),
        # ("UNDO", "Command: UNDO", "command_UNDO.png"),
        # ("EXIT", "Command: EXIT", "command_EXIT.png"),
        # ("RESET", "Command: RESET", "command_RESET.png"),
    ]

    # ========================================================================
    # DO NOT EDIT BELOW THIS LINE (unless you know what you're doing)
    # ========================================================================

    total_count = 0

    if samples:
        print("=== Generating Samples ===")
        for data, label, filename in samples:
            generate_qr_with_label(data, label, filename, output_dir)
            total_count += 1
        print()

    if batches:
        print("=== Generating Batches ===")
        for data, label, filename in batches:
            generate_qr_with_label(data, label, filename, output_dir)
            total_count += 1
        print()

    if processes:
        print("=== Generating Processes ===")
        for data, label, filename in processes:
            generate_qr_with_label(data, label, filename, output_dir)
            total_count += 1
        print()

    if trays:
        print("=== Generating Trays ===")
        for data, label, filename in trays:
            generate_qr_with_label(data, label, filename, output_dir)
            total_count += 1
        print()

    if commands:
        print("=== Generating Commands ===")
        for data, label, filename in commands:
            generate_qr_with_label(data, label, filename, output_dir)
            total_count += 1
        print()

    print(f"✓ Generated {total_count} custom QR codes successfully!\n")
    print(f"Location: {output_dir}")


if __name__ == "__main__":
    main()
