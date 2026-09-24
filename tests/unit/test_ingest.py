"""Unit tests for text extraction and ingest (markdown / txt / pdf)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.embeddings.mock import MockEmbeddingProvider
from app.rag.extractor import (
    UnsupportedDocumentError,
    build_metadata,
    extract_document,
    extract_pdf_blocks,
    parse_front_matter,
)
from app.rag.ingest import DocumentIngester, iter_document_files, summarize_documents
from app.rag.store import VectorStore

PROFILE = """\
---
document_id: demo-profile
title: 演示公司简介
source: public
url: https://example.com/profile
published_at: 2026-01-01
---

# 演示公司简介

## 主营业务

演示公司主营硫化工与氯化工产品链。

## 产业基地

演示基地位于湖南。
"""

NO_FRONT_MATTER = "# 标题\n\n正文内容。\n"


class _FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakeReader:
    def __init__(self, pages: list[str]) -> None:
        self.pages = [_FakePage(text) for text in pages]


def test_parse_front_matter_splits_metadata_from_body():
    front_matter, body = parse_front_matter(PROFILE)
    assert front_matter["document_id"] == "demo-profile"
    assert body.startswith("# 演示公司简介")


def test_parse_front_matter_tolerates_missing_or_broken_block():
    assert parse_front_matter(NO_FRONT_MATTER) == ({}, NO_FRONT_MATTER)
    front_matter, body = parse_front_matter("---\n: : not yaml : :\n---\nbody\n")
    assert front_matter == {}
    assert body.endswith("body\n")


def test_extract_document_reads_front_matter(tmp_path: Path):
    path = tmp_path / "profile.md"
    path.write_text(PROFILE, encoding="utf-8")
    document = extract_document(path, root=tmp_path)
    assert document.metadata.document_id == "demo-profile"
    assert document.metadata.published_at == "2026-01-01"
    assert document.metadata.path == "profile.md"
    assert [block.section for block in document.blocks] == [None, "主营业务", "产业基地"]


def test_extract_document_falls_back_to_file_name_and_heading(tmp_path: Path):
    path = tmp_path / "My Notes.md"
    path.write_text(NO_FRONT_MATTER, encoding="utf-8")
    document = extract_document(path, root=tmp_path)
    assert document.metadata.document_id == "my-notes"
    assert document.metadata.title == "标题"
    assert document.metadata.source == "public"


def test_build_metadata_uses_relative_path_outside_root(tmp_path: Path):
    metadata = build_metadata(path=tmp_path / "a.md", root=tmp_path.parent, front_matter={})
    assert metadata.path.endswith("a.md")


def test_extract_document_rejects_unknown_suffix(tmp_path: Path):
    path = tmp_path / "sheet.xlsx"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(UnsupportedDocumentError):
        extract_document(path, root=tmp_path)


def test_pdf_pages_become_blocks_with_page_numbers(tmp_path: Path, monkeypatch):
    import app.rag.extractor as extractor

    monkeypatch.setattr(
        extractor, "PdfReader", lambda _path: _FakeReader(["第一页内容", "", "第三页"])
    )
    blocks = extract_pdf_blocks(tmp_path / "report.pdf")
    assert [(block.page, block.text) for block in blocks] == [(1, "第一页内容"), (3, "第三页")]


def test_iter_document_files_skips_readme_and_unsupported(tmp_path: Path):
    (tmp_path / "README.md").write_text("# rules\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("# a\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("b\n", encoding="utf-8")
    (tmp_path / "image.png").write_text("x", encoding="utf-8")
    names = {path.name for path in iter_document_files(tmp_path)}
    assert names == {"a.md", "notes.txt"}


class TestIngestIntoVectorStore:
    """Real Chroma collection in a temp directory; mock embeddings, no network."""

    @pytest.fixture
    def corpus(self, tmp_path: Path) -> Path:
        root = tmp_path / "documents"
        (root / "public_reports").mkdir(parents=True)
        (root / "profile.md").write_text(PROFILE, encoding="utf-8")
        (root / "public_reports" / "report.md").write_text(
            "---\ntitle: 年报要点\n---\n\n# 年报要点\n\n## 主要财务数据\n\n营业收入 1 亿元。\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text("# rules\n", encoding="utf-8")
        return root

    @pytest.fixture
    def ingester(self, tmp_path: Path) -> DocumentIngester:
        store = VectorStore(path=tmp_path / "chroma", collection="unittest")
        return DocumentIngester(store=store, embeddings=MockEmbeddingProvider())

    async def test_ingest_directory_counts_documents_and_chunks(
        self, ingester: DocumentIngester, corpus: Path
    ):
        report = await ingester.ingest_directory(corpus)
        assert report.status == "completed"
        assert report.documents == 2
        assert report.chunks == 5
        assert report.errors == []
        assert ingester._store.count() == report.chunks  # noqa: SLF001

    async def test_reingest_replaces_chunks_instead_of_duplicating(
        self, ingester: DocumentIngester, corpus: Path
    ):
        first = await ingester.ingest_directory(corpus)
        second = await ingester.ingest_directory(corpus)
        assert first.chunks == second.chunks
        assert ingester._store.count() == first.chunks  # noqa: SLF001

    async def test_duplicate_document_id_is_reported_not_overwritten(
        self, ingester: DocumentIngester, corpus: Path
    ):
        (corpus / "clash.md").write_text(
            "---\ndocument_id: demo-profile\n---\n\n# 另一个文件\n\n冲突内容。\n",
            encoding="utf-8",
        )
        report = await ingester.ingest_directory(corpus)
        assert report.status == "completed_with_errors"
        assert any("duplicate document_id" in error for error in report.errors)
        assert report.documents == 2  # profile + report; clash.md skipped

    async def test_missing_path_reports_failure(self, ingester: DocumentIngester, tmp_path: Path):
        report = await ingester.ingest_directory(tmp_path / "nowhere")
        assert report.status == "failed"
        assert report.documents == 0

    async def test_empty_directory_is_not_an_error(
        self, ingester: DocumentIngester, tmp_path: Path
    ):
        empty = tmp_path / "empty"
        empty.mkdir()
        report = await ingester.ingest_directory(empty)
        assert report.status == "empty"
        assert report.documents == 0

    async def test_single_file_ingest_and_document_summary(
        self, ingester: DocumentIngester, corpus: Path
    ):
        await ingester.ingest_directory(corpus)
        summaries = summarize_documents(ingester._store)  # noqa: SLF001
        by_id = {summary.document_id: summary for summary in summaries}
        assert set(by_id) == {"demo-profile", "report"}
        profile = by_id["demo-profile"]
        assert profile.title == "演示公司简介"
        assert profile.url == "https://example.com/profile"
        assert profile.sections == ["主营业务", "产业基地"]
        assert profile.chunks == 3
