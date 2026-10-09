import io
from pypdf import PdfWriter

from src.rag.parsers.isap_parser import extract_act_signature, parse_legal_act_into_chunks
from src.rag.parsers.pdf_extractor import extract_text_from_pdf_bytes
from src.rag.models import SearchResultChunk
from src.rag.retrievers.hybrid_retriever import format_rag_context


def test_isap_parser_extracts_signature_and_articles() -> None:
    raw_legal_text = (
        "USTAWA z dnia 10 maja 2018 r. o ochronie danych osobowych\n"
        "Dz. U. z 2018 r. poz. 1000\n\n"
        "Rozdział 1. Przepisy ogólne\n\n"
        "Art. 1. Ustawa określa organy właściwe w sprawach ochrony danych osobowych.\n\n"
        "Art. 2. Ilekroć w ustawie jest mowa o RODO, rozumie się przez to rozporządzenie 2016/679.\n\n"
        "Art. 3 ust. 1. Przepisów ustawy nie stosuje się do działalności wyłączonej."
    )

    signature = extract_act_signature(raw_legal_text)
    assert signature is not None
    assert "2018" in signature
    assert "1000" in signature

    chunks = parse_legal_act_into_chunks(raw_legal_text, fallback_title="Ustawa RODO")
    assert len(chunks) == 4

    assert chunks[0].article_number == "Wstęp / Preambuła"
    assert "Art. 1." in chunks[1].article_number
    assert "Art. 2." in chunks[2].article_number
    assert "Art. 3 ust. 1." in chunks[3].article_number


def test_pdf_extractor_parses_binary_pdf() -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()

    extracted = extract_text_from_pdf_bytes(pdf_bytes)
    assert isinstance(extracted, str)


def test_format_rag_context_renders_clean_markdown() -> None:
    chunks = [
        SearchResultChunk(
            chunk_id="chunk-1",
            act_title="Kodeks Cywilny",
            article_number="Art. 353(1)",
            paragraph=None,
            content="Strony zawierające umowę mogą ułożyć stosunek prawny według swego uznania.",
            score=0.95,
        ),
        SearchResultChunk(
            chunk_id="chunk-2",
            act_title="Kodeks Cywilny",
            article_number="Art. 471",
            paragraph=None,
            content="Dłużnik obowiązany jest do naprawienia szkody wynikłej z niewykonania zobowiązania.",
            score=0.89,
        ),
    ]

    formatted = format_rag_context(chunks)
    assert "[Dokument 1] Akt: Kodeks Cywilny | Jednostka: Art. 353(1)" in formatted
    assert "Strony zawierające umowę mogą ułożyć stosunek prawny" in formatted
    assert "[Dokument 2]" in formatted
