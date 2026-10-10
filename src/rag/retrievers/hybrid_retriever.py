import asyncio
from collections import defaultdict

from src.infrastructure.database.db import get_postgres_connection
from src.rag.embeddings.legal_embedder import LegalEmbedder
from src.rag.models import SearchResultChunk

DENSE_SEARCH_QUERY = """
    SELECT 
        c.id, 
        c.article_number, 
        c.paragraph, 
        c.content, 
        a.title AS act_title,
        1 - (c.embedding <=> $1::vector) AS score
    FROM legal_chunks c
    LEFT JOIN legal_acts a ON c.act_id = a.id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> $1::vector
    LIMIT $2;
"""

SPARSE_SEARCH_QUERY = """
    SELECT 
        c.id, 
        c.article_number, 
        c.paragraph, 
        c.content, 
        a.title AS act_title,
        similarity(c.content, $1) AS score
    FROM legal_chunks c
    LEFT JOIN legal_acts a ON c.act_id = a.id
    WHERE similarity(c.content, $1) > 0.1
    ORDER BY score DESC
    LIMIT $2;
"""


class HybridLegalRetriever:
    """Hybrid legal information retriever combining dense vector search and sparse lexical search using RRF."""

    def __init__(self, embedder: LegalEmbedder | None = None, rrf_k: int = 60) -> None:
        self._embedder = embedder or LegalEmbedder()
        self._rrf_k = rrf_k

    async def search_dense(self, query: str, limit: int = 10) -> list[SearchResultChunk]:
        """Executes semantic vector similarity search via pgvector."""
        query_vector = await self._embedder.embed_query(query)
        vector_str = self._embedder.vector_to_pgvector(query_vector)

        async with get_postgres_connection(readonly=True) as conn:
            rows = await conn.fetch(DENSE_SEARCH_QUERY, vector_str, limit)

        return [
            SearchResultChunk(
                chunk_id=str(r["id"]),
                act_title=r["act_title"],
                article_number=r["article_number"],
                paragraph=r["paragraph"],
                content=r["content"],
                score=float(r["score"] or 0.0),
            )
            for r in rows
        ]

    async def search_sparse(self, query: str, limit: int = 10) -> list[SearchResultChunk]:
        """Executes lexical text similarity search via trigram GIN index."""
        async with get_postgres_connection(readonly=True) as conn:
            rows = await conn.fetch(SPARSE_SEARCH_QUERY, query, limit)

        return [
            SearchResultChunk(
                chunk_id=str(r["id"]),
                act_title=r["act_title"],
                article_number=r["article_number"],
                paragraph=r["paragraph"],
                content=r["content"],
                score=float(r["score"] or 0.0),
            )
            for r in rows
        ]

    async def search_hybrid(self, query: str, top_k: int = 5) -> list[SearchResultChunk]:
        """Executes both dense and sparse searches and fuses their rankings using Reciprocal Rank Fusion."""
        dense_results, sparse_results = await asyncio.gather(
            self.search_dense(query, limit=top_k * 2),
            self.search_sparse(query, limit=top_k * 2)
        )

        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, SearchResultChunk] = {}

        for rank, chunk in enumerate(dense_results, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (self._rrf_k + rank)
            chunk_map[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(sparse_results, start=1):
            rrf_scores[chunk.chunk_id] += 1.0 / (self._rrf_k + rank)
            chunk_map[chunk.chunk_id] = chunk

        sorted_chunk_ids = sorted(
            rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True
        )

        fused_results: list[SearchResultChunk] = []
        for cid in sorted_chunk_ids[:top_k]:
            original_chunk = chunk_map[cid]
            fused_results.append(
                SearchResultChunk(
                    chunk_id=original_chunk.chunk_id,
                    act_title=original_chunk.act_title,
                    article_number=original_chunk.article_number,
                    paragraph=original_chunk.paragraph,
                    content=original_chunk.content,
                    score=rrf_scores[cid],
                )
            )

        return fused_results


def format_rag_context(chunks: list[SearchResultChunk]) -> str:
    """Formats retrieved legal chunks into structured Markdown context for prompt injection."""
    if not chunks:
        return ""

    formatted_docs: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        header = f"[Dokument {idx}]"
        if chunk.act_title:
            header += f" Akt: {chunk.act_title} |"
        header += f" Jednostka: {chunk.article_number}"
        formatted_docs.append(f"{header}\nTreść:\n{chunk.content}")

    return "\n\n".join(formatted_docs)
