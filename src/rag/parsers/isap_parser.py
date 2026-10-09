import re

from src.rag.models import LegalChunkModel

ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)(Art\.\s*\d+[a-z]*(?:\s*(?:ust|§)\.?\s*\d+)?\.?|§\s*\d+[a-z]*\.?)",
    re.IGNORECASE,
)
SIGNATURE_PATTERN = re.compile(
    r"(Dz\.?\s*U\.?\s*(?:z\s*\d{4}\s*r\.?)?\s*(?:poz\.?|nr)\s*\d+)",
    re.IGNORECASE,
)


def extract_act_signature(text: str) -> str | None:
    """Extracts formal publication journal signature (e.g. Dz. U. 2018 poz. 1000)."""
    match = SIGNATURE_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None


def parse_legal_act_into_chunks(raw_text: str, fallback_title: str = "Dokument prawny") -> list[LegalChunkModel]:
    """
    Parses a Polish statutory legal text into structured editorial chunks based on articles.
    Falls back to paragraph-based chunking if explicit articles are absent.
    """
    if not raw_text or not raw_text.strip():
        return []

    splits = ARTICLE_PATTERN.split(raw_text)
    chunks: list[LegalChunkModel] = []

    if len(splits) > 1:
        preamble = splits[0].strip()
        if preamble:
            chunks.append(
                LegalChunkModel(
                    article_number="Wstęp / Preambuła",
                    content=preamble,
                )
            )

        for i in range(1, len(splits), 2):
            article_tag = splits[i].strip()
            article_body = splits[i + 1].strip() if i + 1 < len(splits) else ""

            combined_content = f"{article_tag}\n{article_body}".strip()
            chunks.append(
                LegalChunkModel(
                    article_number=article_tag,
                    content=combined_content,
                )
            )
    else:
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        for idx, para in enumerate(paragraphs, start=1):
            chunks.append(
                LegalChunkModel(
                    article_number=f"Sekcja {idx}",
                    content=para,
                )
            )

    return chunks
