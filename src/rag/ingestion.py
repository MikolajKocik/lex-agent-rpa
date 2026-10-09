from uuid import UUID
from src.infrastructure.database.db import get_postgres_connection
from src.infrastructure.blob.client import upload_document_to_blob

from src.rag.embeddings.legal_embedder import LegalEmbedder
from src.rag.parsers.isap_parser import extract_act_signature, parse_legal_act_into_chunks
from src.rag.parsers.pdf_extractor import extract_text_from_pdf_bytes


INSERT_ACT_QUERY = """
    INSERT INTO legal_acts (title, signature, publication_date, status, blob_url)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id;
"""

INSERT_CHUNK_QUERY = """
    INSERT INTO legal_chunks (act_id, article_number, paragraph, content, embedding)
    VALUES ($1, $2, $3, $4, $5::vector)
    RETURNING id;
"""


class LegalDocumentIngestionService:
    """Orchestrates end-to-end ingestion pipeline: raw document parsing, embedding, and storage."""

    def __init__(self, embedder: LegalEmbedder | None = None) -> None:
        self._embedder = embedder or LegalEmbedder()

    async def ingest_document(
        self,
        title: str,
        content: str | bytes,
        is_pdf: bool = False,
        archive_blob_name: str | None = None,
    ) -> tuple[UUID, int]:
        """
        Ingests a raw legal document into Azure Blob Storage and PostgreSQL pgvector.
        Returns the created legal act UUID and the count of indexed chunks.
        """
        blob_url: str | None = None

        if isinstance(content, bytes):
            if archive_blob_name:
                blob_url = await upload_document_to_blob(
                    blob_name=archive_blob_name,
                    data=content,
                    content_type="application/pdf" if is_pdf else "text/plain",
                )
            if is_pdf:
                raw_text = extract_text_from_pdf_bytes(content)
            else:
                raw_text = content.decode("utf-8")
        else:
            raw_text = content
            if archive_blob_name:
                blob_url = await upload_document_to_blob(
                    blob_name=archive_blob_name,
                    data=raw_text,
                    content_type="text/plain",
                )

        chunks = parse_legal_act_into_chunks(raw_text, fallback_title=title)
        signature = extract_act_signature(raw_text)

        embedded_chunks = await self._embedder.embed_chunks(chunks)

        async with get_postgres_connection(readonly=False) as conn:
            act_id_val = await conn.fetchval(
                INSERT_ACT_QUERY,
                title,
                signature,
                None,
                "obowiazujacy",
                blob_url,
            )
            act_id = UUID(str(act_id_val))

            for chunk in embedded_chunks:
                vector_str = (
                    self._embedder.vector_to_pgvector(chunk.embedding)
                    if chunk.embedding
                    else None
                )
                await conn.execute(
                    INSERT_CHUNK_QUERY,
                    act_id,
                    chunk.article_number,
                    chunk.paragraph,
                    chunk.content,
                    vector_str,
                )

        return act_id, len(embedded_chunks)
