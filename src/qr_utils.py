"""
Shared utilities for QR code generation.
Used by generate_test_qr_codes.py and generate_custom_qr_codes.py
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr_with_label(data, label, filename, output_dir):
    """Generate a QR code image with a label underneath and save it to output_dir."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=30,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    qr_width, qr_height = qr_img.size
    label_height = 60
    final_img = Image.new('RGB', (qr_width, qr_height + label_height), 'white')
    final_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(final_img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_x = (qr_width - (bbox[2] - bbox[0])) // 2
    text_y = qr_height + 10
    draw.text((text_x, text_y), label, fill="black", font=font)

    filepath = os.path.join(output_dir, filename)
    final_img.save(filepath)
    print(f"Created: {filename}")
