"""
Generate custom QR codes for the process tracker application.

This script provides an easy template for generating your own QR codes.
Simply edit the lists below and run the script to generate labeled QR code images.

For testing edge cases, see generate_test_qr_codes.py
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
        box_size=10,
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
        ("S%:2601-02", "Sample: 2601-02", "sample_2601-02.png"),
        # Add more samples here:
        # ("S%:2601-03", "Sample: 2601-03", "sample_2601-03.png"),
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
    # Common processes:
    #   - ftlb234_spinbox (Spincoating)
    #   - c212_sonicator (Sonication)
    #   - ftlb234_uvo (UV-Ozone Cleaning)
    #   - c215ss_jv (JV Measurement)
    #   - w129_evap (Evaporation)
    #   - ftlb248_weighbox (Weighing & Solvation)
    processes = [
        ("P%:ftlb234_spinbox", "Spincoating", "process_spincoating.png"),
        ("P%:c212_sonicator", "Sonication", "process_sonication.png"),
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
        ("SAVE", "Command: SAVE", "command_SAVE.png"),
        ("UNDO", "Command: UNDO", "command_UNDO.png"),
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
