"""Small reusable OCR helper used by the PDF loader."""

import io

import pytesseract
from PIL import Image


def ocr_image(image_bytes, language="eng"):
    """Extract text from image bytes using the locally installed Tesseract engine."""
    if not image_bytes:
        return ""

    with Image.open(io.BytesIO(image_bytes)) as image:
        return pytesseract.image_to_string(image, lang=language).strip()
