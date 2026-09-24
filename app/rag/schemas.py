"""Pydantic schemas: chunk metadata, retrieval result, source citation."""

from __future__ import annotations

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------
# Document metadata (SPEC section 6.1)
# --------------------------------------------------------------------------


class DocumentMetadata(BaseModel):
    """Metadata every ingested document must carry."""

    document_id: str
    title: str
    source: str = "public"
    url: str = ""
    section: str | None = None
    page: int | None = None
    published_at: str = ""
    path: str = ""  # repo-relative source file


class Chunk(BaseModel):
    """A single embeddable piece of a document, with its citation metadata."""

    chunk_id: str
    document_id: str
    text: str
    title: str
    source: str = "public"
    url: str = ""
    published_at: str = ""
    section: str | None = None
    page: int | None = None
    position: int = 0  # ordinal inside the document
    char_count: int = 0

    @classmethod
    def build(
        cls,
        *,
        metadata: DocumentMetadata,
        text: str,
        position: int,
        section: str | None = None,
        page: int | None = None,
    ) -> Chunk:
        """Create a chunk, inheriting document metadata and filling in ids."""
        return cls(
            chunk_id=f"{metadata.document_id}::{position:04d}",
            document_id=metadata.document_id,
            text=text,
            title=metadata.title,
            source=metadata.source,
            url=metadata.url,
            published_at=metadata.published_at,
            section=section if section is not None else metadata.section,
            page=page if page is not None else metadata.page,
            position=position,
            char_count=len(text),
        )

    @property
    def embedding_text(self) -> str:
        """Text handed to the embedding model: chunk plus its title / section.

        Prepending where the chunk came from makes document-level terms (such as
        the company name in the title) part of every vector, which is what lets
        the offline mock embedding rank sensible chunks first.
        """
        header = " > ".join(part for part in (self.title, self.section) if part)
        return f"{header}\n{self.text}" if header else self.text

    def to_storage_metadata(self) -> dict[str, str | int]:
        """Flatten metadata for the vector store (Chroma needs scalar values)."""
        meta: dict[str, str | int] = {
            "document_id": self.document_id,
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at,
            "position": self.position,
            "char_count": self.char_count,
        }
        if self.section:
            meta["section"] = self.section
        if self.page is not None:
            meta["page"] = self.page
        return meta


# --------------------------------------------------------------------------
# Retrieval + citation (SPEC section 6.3)
# --------------------------------------------------------------------------


class RetrievedChunk(BaseModel):
    """A chunk recalled by similarity search, with score and metadata."""

    chunk_id: str
    document_id: str
    title: str
    content: str
    score: float
    section: str | None = None
    page: int | None = None
    source: str = "public"
    url: str = ""
    published_at: str = ""
    position: int = 0

    @classmethod
    def from_chunk(cls, chunk: Chunk, score: float) -> RetrievedChunk:
        return cls(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            content=chunk.text,
            score=round(score, 4),
            section=chunk.section,
            page=chunk.page,
            source=chunk.source,
            url=chunk.url,
            published_at=chunk.published_at,
            position=chunk.position,
        )


class Citation(BaseModel):
    """A numbered reference that can be pointed at from an answer."""

    index: int
    document_id: str
    title: str
    section: str | None = None
    page: int | None = None
    source: str = "public"
    url: str = ""
    published_at: str = ""
    score: float = 0.0

    @classmethod
    def from_result(cls, result: RetrievedChunk, index: int) -> Citation:
        return cls(
            index=index,
            document_id=result.document_id,
            title=result.title,
            section=result.section,
            page=result.page,
            source=result.source,
            url=result.url,
            published_at=result.published_at,
            score=result.score,
        )

    @property
    def label(self) -> str:
        """Human readable location inside the source, e.g. `主营业务 · 第 3 页`."""
        parts = [self.title]
        if self.section:
            parts.append(self.section)
        if self.page is not None:
            parts.append(f"第 {self.page} 页")
        return " · ".join(parts)

    @property
    def marker(self) -> str:
        return f"[{self.index}]"


class DocumentSummary(BaseModel):
    """Entry of `GET /api/knowledge/documents`."""

    document_id: str
    title: str
    source: str = "public"
    url: str = ""
    published_at: str = ""
    chunks: int = 0
    chars: int = Field(default=0, description="Total characters stored in chunks")
    sections: list[str] = []


class IngestReport(BaseModel):
    """Outcome of an ingest run."""

    documents: int = 0
    chunks: int = 0
    status: str = "completed"
    skipped: list[str] = []
    errors: list[str] = []
