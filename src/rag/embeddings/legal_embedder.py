from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from src.rag.models import LegalChunkModel


class LegalEmbedder:
    """Generates dense vector representations for legal text queries and document chunks."""

    def __init__(self, model_name: str | None = None) -> None:
        if model_name:
            self._client = NVIDIAEmbeddings(model=model_name)
        else:
            self._client = NVIDIAEmbeddings()

    async def embed_query(self, query: str) -> list[float]:
        """Generates an embedding vector for a search query string."""
        return await self._client.aembed_query(query)

    async def embed_chunks(self, chunks: list[LegalChunkModel]) -> list[LegalChunkModel]:
        """Generates embedding vectors for a list of legal chunks in batches."""
        if not chunks:
            return []

        texts = [c.content for c in chunks]
        vectors = await self._client.aembed_documents(texts)

        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

        return chunks

    @staticmethod
    def vector_to_pgvector(vector: list[float]) -> str:
        """Converts a floating-point vector into a PostgreSQL pgvector literal string."""
        return "[" + ",".join(map(str, vector)) + "]"
