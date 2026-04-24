"""
Shared utilities for QR code generation.
Used by generate_test_qr_codes.py and generate_custom_qr_codes.py
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr_with_label(data, label, filename, output_dir):
    """Generate a QR code image with a label underneath and save it to output_dir."""
    # Generate QR code with minimal border
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=30,  # Size of each QR code box in pixels
        border=1,     # Minimal border for compact QR codes
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
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        # Fallback to default font if arial not available
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
