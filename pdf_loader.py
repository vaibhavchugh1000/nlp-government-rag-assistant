"""PDF text extraction with OCR fallback for scanned/image-based pages."""

from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
import io


# A page with fewer characters than this is treated as likely scanned.
# Set to 0 to OCR only pages with no extractable text.
MIN_TEXT_CHARS = 40
OCR_DPI = 300


def _ocr_page(page):
    """Render a PDF page and OCR the rendered image."""
    pixmap = page.get_pixmap(dpi=OCR_DPI, alpha=False)
    image_bytes = pixmap.tobytes("png")
    with Image.open(io.BytesIO(image_bytes)) as image:
        return pytesseract.image_to_string(image).strip()


def load_pdf(pdf_path):
    """Return one record per page, using native PDF text or OCR as needed.

    Text-based pages use PyMuPDF's native extraction. Pages with no or very
    little extractable text are rendered and passed to Tesseract OCR. The
    returned record shape remains compatible with the existing RAG pipeline.
    """
    pdf_path = str(pdf_path)
    document_name = Path(pdf_path).name
    document_id = Path(pdf_path).stem
    pages = []

    try:
        with pymupdf.open(pdf_path) as document:
            if document.is_encrypted and not document.authenticate(""):
                raise ValueError(
                    f"PDF is password-protected and could not be opened: {document_name}"
                )

            for page_number, page in enumerate(document, start=1):
                native_text = (page.get_text("text") or "").strip()
                text = native_text
                text_source = "pdf_text"

                if len(native_text) < MIN_TEXT_CHARS:
                    try:
                        ocr_text = _ocr_page(page)
                    except pytesseract.pytesseract.TesseractNotFoundError as exc:
                        raise RuntimeError(
                            "Tesseract OCR was not found. Install the Tesseract OCR "
                            "application and add it to PATH, then restart the terminal."
                        ) from exc

                    if ocr_text:
                        # Keep native text too, since a page may contain both
                        # a small amount of selectable text and scanned content.
                        text = "\n\n".join(
                            part for part in (native_text, ocr_text) if part
                        )
                        text_source = "pdf_text+ocr" if native_text else "ocr"
                    elif native_text:
                        text_source = "pdf_text"

                if not text.strip():
                    print(
                        f"Warning: no text could be extracted from page "
                        f"{page_number} of {document_name}"
                    )
                    continue

                pages.append({
                    "text": text,
                    "page_number": page_number,
                    "document_id": document_id,
                    "document_name": document_name,
                    "document_path": pdf_path,
                    "document_type": "pdf",
                    "text_source": text_source,
                })
    except pytesseract.pytesseract.TesseractNotFoundError:
        raise
    except Exception:
        # Preserve the original exception and traceback for Flask logging.
        raise

    if not pages:
        raise ValueError(
            f"No text could be extracted from '{document_name}'. "
            "The PDF may be blank, damaged, or require a different OCR language."
        )

    print(f"Successfully loaded PDF: {pdf_path} ({len(pages)} pages with text)")
    return pages
