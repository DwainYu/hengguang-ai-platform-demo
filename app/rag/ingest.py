"""Document ingest: read public docs from data/documents, chunk, embed, store in Chroma."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from app.config import Settings, settings
from app.embeddings import EmbeddingProvider
from app.rag.chunker import chunk_document
from app.rag.extractor import SUPPORTED_SUFFIXES, extract_document
from app.rag.schemas import DocumentSummary, IngestReport
from app.rag.store import VectorStore

SKIPPED_FILENAMES = {"README.md"}


def iter_document_files(root: Path) -> Iterable[Path]:
    """Every ingestable file under ``root``, in a stable order."""
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_SUFFIXES
        and path.name not in SKIPPED_FILENAMES
    )


class DocumentIngester:
    """Document -> text extraction -> chunking -> embedding -> vector store."""

    def __init__(
        self,
        *,
        store: VectorStore,
        embeddings: EmbeddingProvider,
        config: Settings | None = None,
    ) -> None:
        cfg = config or settings
        self._store = store
        self._embeddings = embeddings
        self._chunk_size = cfg.rag_chunk_size
        self._chunk_overlap = cfg.rag_chunk_overlap

    async def ingest_directory(self, root: str | Path, *, rebuild: bool = False) -> IngestReport:
        """Ingest every supported document below ``root``."""
        base = Path(root)
        report = IngestReport()
        if not base.exists():
            report.status = "failed"
            report.errors.append(f"path does not exist: {base}")
            return report

        files = list(iter_document_files(base)) if base.is_dir() else [base]
        if not files:
            report.status = "empty"
            report.skipped.append(f"no supported documents found under {base}")
            return report

        if rebuild:
            self._store.clear()

        ingested_ids: set[str] = set()
        for path in files:
            try:
                chunks = await self.ingest_file(path, root=base, ingested_ids=ingested_ids)
            except Exception as exc:  # keep going: one bad file must not stop the run
                report.errors.append(f"{path.name}: {exc}")
                continue
            if chunks is None:
                continue
            report.documents += 1
            report.chunks += chunks

        if report.errors:
            report.status = "completed_with_errors"
        return report

    async def ingest_file(
        self, path: Path, *, root: Path, ingested_ids: set[str] | None = None
    ) -> int | None:
        """Ingest one file; returns the number of stored chunks (None if skipped)."""
        document = extract_document(path, root=root)
        document_id = document.metadata.document_id
        if ingested_ids is not None and document_id in ingested_ids:
            # Two files claiming one document_id would silently overwrite each other.
            raise ValueError(f"duplicate document_id: {document_id}")
        if not document.blocks:
            return None

        chunks = chunk_document(
            document.metadata,
            document.blocks,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        if not chunks:
            return None

        embeddings = await self._embeddings.embed_documents(
            [chunk.embedding_text for chunk in chunks]
        )
        # Re-ingesting a document replaces its previous chunks.
        self._store.delete_document(document_id)
        self._store.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.to_storage_metadata() for chunk in chunks],
        )
        if ingested_ids is not None:
            ingested_ids.add(document_id)
        return len(chunks)


def summarize_documents(store: VectorStore) -> list[DocumentSummary]:
    """Aggregate stored chunks into the document listing (SPEC section 8.5)."""
    grouped: dict[str, dict] = defaultdict(
        lambda: {"chunks": 0, "chars": 0, "sections": [], "meta": {}}
    )
    for metadata in store.all_metadata():
        document_id = str(metadata.get("document_id") or "unknown")
        entry = grouped[document_id]
        entry["meta"] = metadata
        entry["chunks"] += 1
        entry["chars"] += int(metadata.get("char_count") or 0)
        section = metadata.get("section")
        if section and section not in entry["sections"]:
            entry["sections"].append(str(section))

    summaries: list[DocumentSummary] = []
    for document_id, entry in grouped.items():
        meta = entry["meta"]
        summaries.append(
            DocumentSummary(
                document_id=document_id,
                title=str(meta.get("title") or document_id),
                source=str(meta.get("source") or "public"),
                url=str(meta.get("url") or ""),
                published_at=str(meta.get("published_at") or ""),
                chunks=entry["chunks"],
                chars=entry["chars"],
                sections=sorted(entry["sections"]),
            )
        )
    return sorted(summaries, key=lambda item: item.document_id)
