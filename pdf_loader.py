
"""PDF text extraction with OCR fallback for scanned/image-based pages."""

from pathlib import Path

import pymupdf
import pytesseract

from ocr_processor import ocr_image


# A page with fewer characters than this is treated as likely scanned.
MIN_TEXT_CHARS = 40
OCR_DPI = 300


def _ocr_page(page):
    """Render a PDF page and extract text using Tesseract OCR."""

    pixmap = page.get_pixmap(dpi=OCR_DPI, alpha=False)
    image_bytes = pixmap.tobytes("png")

    return ocr_image(image_bytes, language="eng")


def load_pdf(pdf_path):
    """Extract text from PDF pages using native extraction and OCR fallback."""

    pdf_path = str(pdf_path)
    document_name = Path(pdf_path).name
    document_id = Path(pdf_path).stem
    pages = []

    try:
        with pymupdf.open(pdf_path) as document:

            if document.is_encrypted and not document.authenticate(""):
                raise ValueError(
                    f"PDF is password-protected and could not be opened: "
                    f"{document_name}"
                )

            for page_number, page in enumerate(document, start=1):

                native_text = (page.get_text("text") or "").strip()
                text = native_text
                text_source = "pdf_text"

                # Run OCR when the page contains little or no extractable text.
                if len(native_text) < MIN_TEXT_CHARS:

                    try:
                        ocr_text = _ocr_page(page)

                    except pytesseract.pytesseract.TesseractNotFoundError as exc:
                        raise RuntimeError(
                            "Tesseract OCR was not found. Install Tesseract "
                            "and add it to the system PATH."
                        ) from exc

                    if ocr_text:
                        text = "\n\n".join(
                            part for part in (native_text, ocr_text) if part
                        )

                        text_source = (
                            "pdf_text+ocr" if native_text else "ocr"
                        )

                if not text.strip():
                    print(
                        f"Warning: No text extracted from page "
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

    if not pages:
        raise ValueError(
            f"No text could be extracted from '{document_name}'. "
            "The PDF may be blank, damaged, or require a different OCR language."
        )

    print(
        f"Successfully loaded PDF: {pdf_path} "
        f"({len(pages)} pages with text)"
    )

    return pages
