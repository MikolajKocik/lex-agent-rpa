import io
from pathlib import Path

from src.rag.generators.legal_generator import stream_clean_pdf_pages


def extract_text_from_pdf_stream(stream: io.BytesIO) -> str:
    """Extracts raw text content from a binary stream of a PDF document."""
    pages = stream_clean_pdf_pages(stream)
    return "\n\n".join(pages)

def extract_text_from_pdf_file(file_path: str | Path) -> str:
    """Extracts text content from a local PDF file on disk."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at: {path}")

    with open(path, "rb") as f:
        return extract_text_from_pdf_stream(io.BytesIO(f.read()))


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts text content directly from raw bytes of a PDF file."""
    return extract_text_from_pdf_stream(io.BytesIO(pdf_bytes))
