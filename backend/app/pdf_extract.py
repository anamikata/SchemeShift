from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class ExtractedDocument:
    pages: list[ExtractedPage]
    page_count: int
    text_character_count: int
    likely_scanned: bool


def extract_pdf_pages(data: bytes, *, max_pages: int = 80) -> ExtractedDocument:
    """Extract page text without storing the uploaded PDF on disk.

    Scanned pages are not silently treated as empty documents. The caller can
    ask for pasted text or a future OCR pass when text extraction is inadequate.
    """
    if not data:
        raise ValueError("The uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(data), strict=False)
    except Exception as exc:  # pypdf raises several parser-specific exceptions
        raise ValueError(f"Could not read this PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise ValueError("This PDF is password-protected. Upload an unlocked copy.")
        except Exception as exc:
            raise ValueError("This PDF is password-protected. Upload an unlocked copy.") from exc

    pages: list[ExtractedPage] = []
    for index, page in enumerate(reader.pages[:max_pages], start=1):
        try:
            text = page.extract_text(extraction_mode="layout") or ""
        except TypeError:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(ExtractedPage(page_number=index, text=text.strip()))

    total_chars = sum(len(page.text) for page in pages)
    average_chars = total_chars / max(len(pages), 1)
    likely_scanned = total_chars < 250 or average_chars < 80

    return ExtractedDocument(
        pages=pages,
        page_count=len(reader.pages),
        text_character_count=total_chars,
        likely_scanned=likely_scanned,
    )
