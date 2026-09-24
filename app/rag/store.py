"""Chroma persistent vector store: the only module allowed to touch chromadb."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings

UPSERT_BATCH = 256


@dataclass(frozen=True)
class VectorHit:
    """One similarity-search hit from the vector store."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float


class VectorStore:
    """Thin wrapper over a Chroma collection that stores document chunks.

    Embeddings are always supplied by an ``EmbeddingProvider``; the collection
    never uses a Chroma built-in embedding function, which keeps the demo
    runnable without network access or API keys.
    """

    def __init__(self, path: str | Path | None = None, collection: str | None = None) -> None:
        self._path = str(path or settings.chroma_path)
        self._collection_name = collection or settings.chroma_collection
        self._client: chromadb.ClientAPI | None = None
        self._collection: Collection | None = None

    @property
    def path(self) -> str:
        return self._path

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            Path(self._path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self._path)
        return self._client

    @property
    def collection(self) -> Collection:
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def count(self) -> int:
        return int(self.collection.count())

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or refresh chunks in bulk."""
        for start in range(0, len(ids), UPSERT_BATCH):
            stop = start + UPSERT_BATCH
            self.collection.upsert(
                ids=ids[start:stop],
                embeddings=embeddings[start:stop],
                documents=documents[start:stop],
                metadatas=metadatas[start:stop],
            )

    def delete_document(self, document_id: str) -> None:
        """Drop every chunk of a document (called before re-ingesting it)."""
        self.collection.delete(where={"document_id": document_id})

    def query(self, embedding: list[float], top_k: int) -> list[VectorHit]:
        """Cosine similarity search; score is similarity = 1 - cosine distance."""
        available = self.count()
        if available == 0 or top_k <= 0:
            return []
        res = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, available),
            include=["metadatas", "documents", "distances"],
        )
        ids = (res.get("ids") or [[]])[0]
        documents = (res.get("documents") or [[]])[0]
        metadatas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]

        hits: list[VectorHit] = []
        for index, chunk_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else 1.0
            hits.append(
                VectorHit(
                    chunk_id=chunk_id,
                    text=documents[index] if index < len(documents) else "",
                    metadata=dict(metadatas[index] or {}) if index < len(metadatas) else {},
                    score=round(1.0 - float(distance), 4),
                )
            )
        return hits

    def all_metadata(self) -> list[dict[str, Any]]:
        """Metadata of every stored chunk (used for the document listing)."""
        if self.count() == 0:
            return []
        res = self.collection.get(include=["metadatas"])
        return [dict(item or {}) for item in (res.get("metadatas") or [])]

    def clear(self) -> None:
        """Delete the whole collection so the next ingest starts from scratch."""
        try:
            self.client.delete_collection(self._collection_name)
        except Exception:  # pragma: no cover - collection simply does not exist yet
            pass
        self._collection = None


_stores: dict[tuple[str, str], VectorStore] = {}


def get_vector_store(path: str | None = None, collection: str | None = None) -> VectorStore:
    """Process-wide vector store for the configured Chroma path/collection."""
    key = (path or settings.chroma_path, collection or settings.chroma_collection)
    store = _stores.get(key)
    if store is None:
        store = VectorStore(*key)
        _stores[key] = store
    return store


def reset_vector_stores() -> None:
    """Forget cached stores (used by tests)."""
    _stores.clear()
