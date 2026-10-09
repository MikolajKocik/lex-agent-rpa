from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LegalActModel(BaseModel):
    """Data model representing a legal act registered in the system."""

    id: UUID | None = None
    title: str = Field(..., max_length=512)
    signature: str | None = Field(default=None, max_length=100)
    publication_date: date | None = None
    status: str = Field(default="obowiazujacy", max_length=50)
    blob_url: str | None = Field(default=None, max_length=1024)
    created_at: datetime | None = None


class LegalChunkModel(BaseModel):
    """Data model representing an editorial chunk of a legal act (article, paragraph)."""

    id: UUID | None = None
    act_id: UUID | None = None
    article_number: str = Field(..., max_length=50)
    paragraph: str | None = Field(default=None, max_length=50)
    content: str
    embedding: list[float] | None = None
    created_at: datetime | None = None


class SearchResultChunk(BaseModel):
    """Result item returned by dense, sparse, or hybrid retrievers."""

    chunk_id: str
    act_title: str | None = None
    article_number: str
    paragraph: str | None = None
    content: str
    score: float
