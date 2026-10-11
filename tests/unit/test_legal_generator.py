import io
from unittest.mock import MagicMock

from pypdf import PdfReader, PdfWriter

from src.rag.generators.legal_generator import (
    _clear_pages,
    _get_pdf_stream,
    stream_clean_pdf_pages,
)
from src.rag.parsers.pdf_extractor import extract_text_from_pdf_stream


def test_get_pdf_stream_extracts_only_non_empty_pages() -> None:
    """Verifies that _get_pdf_stream yields non-empty stripped text and skips None or blank pages."""
    mock_reader = MagicMock(spec=PdfReader)

    page1 = MagicMock()
    page1.extract_text.return_value = "   Art. 1. Kodeks cywilny reguluje stosunki.   "

    page2_none = MagicMock()
    page2_none.extract_text.return_value = None

    page3_blank = MagicMock()
    page3_blank.extract_text.return_value = "   \n\t  "

    page4 = MagicMock()
    page4.extract_text.return_value = "Art. 2. Przepisy ustawy stosuje się do osób fizycznych."

    mock_reader.pages = [page1, page2_none, page3_blank, page4]

    results = list(_get_pdf_stream(mock_reader))

    assert len(results) == 2
    assert results[0] == "Art. 1. Kodeks cywilny reguluje stosunki."
    assert results[1] == "Art. 2. Przepisy ustawy stosuje się do osób fizycznych."


def test_get_pdf_stream_handles_empty_or_none_reader() -> None:
    """Verifies that _get_pdf_stream gracefully handles empty or None reader."""
    assert list(_get_pdf_stream(None)) == []

    empty_reader = MagicMock(spec=PdfReader)
    empty_reader.pages = []
    assert list(_get_pdf_stream(empty_reader)) == []


def test_clear_pages_filters_pages_shorter_than_50_chars() -> None:
    """Verifies that _clear_pages skips pages with less than 50 characters."""
    pages = [
        "Krótka okładka",  # < 50 chars -> skip
        "Ta strona zawiera treść aktu prawnego i ma na pewno powyżej pięćdziesięciu znaków tekstu.",
        "Stopka końcowa",  # < 50 chars -> skip
    ]

    cleaned = list(_clear_pages(pages))

    assert len(cleaned) == 1
    assert "Ta strona zawiera treść aktu prawnego" in cleaned[0]


def test_clear_pages_normalizes_hyphenation_and_control_chars() -> None:
    """Verifies unwrapping of hyphenated words, removal of form feeds and space normalization."""
    raw_page = (
        "Art. 415. Kto z winy swej wyrządził drugiemu szkodę, zobowią-\n"
        "zany jest do jej naprawienia.\x0c Zgodnie z zasadami   współżycia."
    )

    cleaned = list(_clear_pages([raw_page]))

    assert len(cleaned) == 1
    result = cleaned[0]

    # Hyphen across newline should be glued
    assert "zobowiązany" in result
    assert "zobowią-\nzany" not in result

    # Form feed should be removed
    assert "\x0c" not in result

    # Triple spaces normalized
    assert "   " not in result


def test_stream_clean_pdf_pages_end_to_end_with_real_pdf_stream() -> None:
    """Verifies that stream_clean_pdf_pages pipeline correctly processes a real in-memory PDF stream."""
    writer = PdfWriter()
    # Add a blank page (should produce empty/none text and be filtered out)
    writer.add_blank_page(width=72, height=72)

    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)

    # Empty/blank pages should result in 0 yielded items
    result = list(stream_clean_pdf_pages(buffer))
    assert result == []


def test_extract_text_from_pdf_stream_integration() -> None:
    """Verifies that extract_text_from_pdf_stream integrates with the generator pipeline."""
    mock_stream = io.BytesIO(b"%PDF-mock")

    mock_pages = [
        "Pierwsza strona dokumentu prawnego posiadająca odpowiednią długość znaków.",
        "Druga strona dokumentu z artykułami kodeksu postępowania cywilnego.",
    ]

    mock_reader = MagicMock(spec=PdfReader)
    p1 = MagicMock()
    p1.extract_text.return_value = mock_pages[0]
    p2 = MagicMock()
    p2.extract_text.return_value = mock_pages[1]
    mock_reader.pages = [p1, p2]

    from unittest.mock import patch

    with patch("src.rag.generators.legal_generator.PdfReader", return_value=mock_reader):
        full_text = extract_text_from_pdf_stream(mock_stream)

    assert "Pierwsza strona dokumentu" in full_text
    assert "Druga strona dokumentu" in full_text
    assert "\n\n" in full_text
