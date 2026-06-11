"""
Generate QR code images for testing the process tracker application.
Creates a minimal set of valid and invalid QR codes to test all edge cases.

This script generates test QR codes with labels for easy identification.
For generating custom QR codes, see generate_custom_qr_codes.py
"""
from pathlib import Path
from qr_utils import generate_qr_with_label


# (section_label, [(data, qr_label, filename), ...])
# Sample format: S%:YYMM-NN. Batch: B%:NNNN. Process: P%:abbr. Tray: T%:ID.
_SECTIONS = [
    ("Valid Samples (2)", [
        ("S%:2601-01", "Sample: 2601-01", "sample_2601-01.png"),
        ("S%:2601-02", "Sample: 2601-02", "sample_2601-02.png"),
    ]),
    ("Legacy Sample (1)", [
        ("2512-99", "Legacy sample: 2512-99", "legacy_sample_2512-99.png"),
    ]),
    ("Valid Batch (1)", [
        ("B%:1234", "Batch: 1234", "batch_1234.png"),
    ]),
    ("Valid Processes (3)", [
        ("P%:ftlb234_spinbox", "Process: Spincoating", "process_spinbox.png"),
        ("P%:c212_sonicator", "Process: Sonication", "process_sonicator.png"),
        ("P%:c215ss_jv", "Process: JV Measurement", "process_jv.png"),
    ]),
    ("Valid Trays (2)", [
        ("T%:066726-S-001", "Tray: 066726-S-001 (2x2)", "tray_066726_2x2.png"),
        ("T%:072266-S-001", "Tray: 072266-S-001 (5x5)", "tray_072266_5x5.png"),
    ]),
    ("Invalid QR Codes (edge cases)", [
        ("X%:2601-01", "BAD: Invalid Prefix", "bad_invalid_prefix.png"),
        ("2601-01", "BAD: No Prefix", "bad_no_prefix.png"),
        ("S%2601-01", "BAD: Missing Colon", "bad_missing_colon.png"),
        ("S%:", "BAD: Empty ID", "bad_empty_id.png"),
        ("P%:fake_process", "BAD: Unapproved Process", "bad_unapproved_process.png"),
        ("S%: 2601-01", "BAD: Space After Prefix", "bad_space_in_id.png"),
        ("RANDOM TEXT", "BAD: Invalid Format", "bad_random_text.png"),
    ]),
]


def main():
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "test_qr_codes"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating TEST QR codes in: {output_dir}\n")
    print("This is a minimal test set. "
          "For custom QR codes, use generate_custom_qr_codes.py\n")

    for label, items in _SECTIONS:
        print(f"=== {label} ===")
        for data, qr_label, filename in items:
            generate_qr_with_label(data, qr_label, filename, output_dir)
        print()

    print("\u2713 All TEST QR codes generated successfully!\n")
    print(f"Location: {output_dir}")
    print(f"Total files: {len(list(output_dir.glob('*.png')))} PNG images\n")
    print("To generate custom QR codes, "
          "edit and run generate_custom_qr_codes.py")


if __name__ == "__main__":
    main()
