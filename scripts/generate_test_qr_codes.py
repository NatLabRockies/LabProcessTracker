"""
Generate QR code images for testing the process tracker application.
Creates a minimal set of valid and invalid QR codes to test all edge cases.

This script generates test QR codes with labels for easy identification.
For generating custom QR codes, see generate_custom_qr_codes.py
"""
import qrcode
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_qr_with_label(data, label, filename, output_dir):
    """Generate a QR code image with a label underneath and save it.

    Args:
        data: The data to encode in the QR code
        label: Text label to display below the QR code
        filename: Output filename
        output_dir: Directory to save the file
    """
    # Generate QR code with minimal border
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=1,  # Minimal border for compact QR codes
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.convert('RGB')  # Convert to RGB for compatibility

    # Create a new image with space for label below
    qr_width, qr_height = qr_img.size
    label_height = 60  # Space for text label
    total_height = qr_height + label_height

    # Create white background image
    final_img = Image.new('RGB', (qr_width, total_height), 'white')

    # Paste QR code at the top
    final_img.paste(qr_img, (0, 0))

    # Add label text below QR code
    draw = ImageDraw.Draw(final_img)
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), label, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (qr_width - text_width) // 2
    text_y = qr_height + 10

    # Draw text
    draw.text((text_x, text_y), label, fill="black", font=font)

    # Save the final image
    filepath = os.path.join(output_dir, filename)
    final_img.save(filepath)
    print(f"Created: {filename}")


def main():
    # Create output directory
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "test_qr_codes"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating TEST QR codes in: {output_dir}\n")
    print("This is a minimal test set. For custom QR codes, use generate_custom_qr_codes.py\n")

    # === VALID SAMPLES (2) ===
    print("=== Valid Samples (2) ===")
    # Format: S%:YYMM-NN where YY=year, MM=month, NN=sample number
    generate_qr_with_label("S%:2601-01", "Sample: 2601-01", "sample_2601-01.png", output_dir)
    generate_qr_with_label("S%:2601-02", "Sample: 2601-02", "sample_2601-02.png", output_dir)
    print()

    # === LEGACY SAMPLE (1) ===
    print("=== Legacy Sample (1) ===")
    # Format: YYMM-NN (no S%: prefix)
    generate_qr_with_label("2512-99", "Legacy: 2512-99", "legacy_sample_2512-99.png", output_dir)
    print()

    # === VALID BATCH (1) ===
    print("=== Valid Batch (1) ===")
    # Format: B%:four-digit-number
    generate_qr_with_label("B%:1234", "Batch: 1234", "batch_1234.png", output_dir)
    print()

    # === VALID PROCESSES (3) ===
    print("=== Valid Processes (3) ===")
    generate_qr_with_label("P%:ftlb234_spinbox", "Process: Spincoating", "process_spinbox.png", output_dir)
    generate_qr_with_label("P%:c212_sonicator", "Process: Sonication", "process_sonicator.png", output_dir)
    generate_qr_with_label("P%:c215ss_jv", "Process: JV Measurement", "process_jv.png", output_dir)
    print()

    # === VALID TRAYS (2) ===
    print("=== Valid Trays (2) ===")
    # Format: T%:TRAY_ID
    generate_qr_with_label("T%:066726-S-XXX", "Tray: 066726-S-XXX (2x2)", "tray_066726_2x2.png", output_dir)
    generate_qr_with_label("T%:072266-XXX-A", "Tray: 072266-XXX-A (5x5)", "tray_072266_5x5.png", output_dir)
    print()

    # === INVALID/BAD QR CODES (one of each type) ===
    print("=== Invalid QR Codes (edge cases) ===")

    # Bad: Invalid prefix
    generate_qr_with_label("X%:2601-01", "BAD: Invalid Prefix", "bad_invalid_prefix.png", output_dir)

    # Bad: No prefix
    generate_qr_with_label("2601-01", "BAD: No Prefix", "bad_no_prefix.png", output_dir)

    # Bad: Missing colon
    generate_qr_with_label("S%2601-01", "BAD: Missing Colon", "bad_missing_colon.png", output_dir)

    # Bad: Empty ID
    generate_qr_with_label("S%:", "BAD: Empty ID", "bad_empty_id.png", output_dir)

    # Bad: Unapproved process
    generate_qr_with_label("P%:fake_process", "BAD: Unapproved Process", "bad_unapproved_process.png", output_dir)

    # Bad: Whitespace in ID
    generate_qr_with_label("S%: 2601-01", "BAD: Space After Prefix", "bad_space_in_id.png", output_dir)

    # Bad: Random text
    generate_qr_with_label("RANDOM TEXT", "BAD: Invalid Format", "bad_random_text.png", output_dir)

    print()
    print(f"✓ All TEST QR codes generated successfully!\n")
    print(f"Location: {output_dir}")
    print(f"Total files: {len(list(output_dir.glob('*.png')))} PNG images\n")
    print("To generate custom QR codes, edit and run generate_custom_qr_codes.py")


if __name__ == "__main__":
    main()
