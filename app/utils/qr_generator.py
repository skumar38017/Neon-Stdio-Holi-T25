# app/utils/qr_generator.py
import qrcode
from io import BytesIO
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_qr_code(user_details: str) -> bytes:
    try:
        logger.info(f"Generating QR code for: {user_details}")
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(user_details)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        logger.info("QR code generated successfully.")
        print("QR code generated successfully.")
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise
