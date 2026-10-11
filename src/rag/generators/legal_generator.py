import io
from collections.abc import Iterable

from pypdf import PdfReader


def _get_pdf_stream(reader: PdfReader) -> Iterable[str]:
    """
    Lazily extracts non-empty text content from PDF pages one by one.

    Args:
        reader: An initialized PdfReader instance.

    Yields:
        str: Raw stripped page content of each non-empty page.
    """
    if not reader:
        return

    for content in reader.pages:
        page = content.extract_text()
        if page is not None:
            if page.strip():
                page = page.strip()
                yield page


def _clear_pages(pages: Iterable[str]) -> Iterable[str]:
    """
    Normalizes legal text pages and filters out short or artifact pages.

    Performs legal text sanitization:
    - Drops pages shorter than 50 characters (e.g. blank sheets, empty covers).
    - Unwraps hyphenated words split across line breaks ("-\\n").
    - Removes form feed characters ("\\x0c").
    - Normalizes multi-space indentation and newline formatting.

    Args:
        pages: An iterable stream of raw text pages.

    Yields:
        str: Cleaned and normalized page text.
    """
    for page in pages:
        if len(page) < 50:
            continue
        page = page.replace("-\n", "").replace("\x0c", "").replace("   ", "  ")
        page = page.splitlines()
        yield "\n".join(page)


def stream_clean_pdf_pages(stream: io.BytesIO) -> Iterable[str]:
    """
    Orchestrates the lazy streaming and cleaning pipeline for PDF documents.

    Chains generator functions to process pages incrementally without
    loading the full document into memory.

    Args:
        stream: In-memory binary stream of the PDF file.

    Returns:
        Iterable[str]: Lazy generator yielding cleaned legal text page-by-page.
    """
    reader = PdfReader(stream)
    return _clear_pages(_get_pdf_stream(reader))
