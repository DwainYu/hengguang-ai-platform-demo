"""Unit tests for retrieval metadata and citations (test_retrieval_metadata)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.embeddings.mock import MockEmbeddingProvider
from app.rag.ingest import DocumentIngester
from app.rag.retriever import Retriever, lexical_overlap, query_terms
from app.rag.store import VectorStore

DOCS = {
    "profile.md": """\
---
document_id: hg-profile
title: 恒光股份公开简介
source: public
url: https://example.com/profile
published_at: 2026-04-28
---

# 恒光股份公开简介

## 主营业务

恒光股份主要业务为硫化工、氯化工产品链的研发、生产和销售。

## 产业基地

公司在怀化、衡阳和老挝设有化工产业基地，怀化基地占地约 600 亩。
""",
    "products.md": """\
---
document_id: hg-products
title: 恒光股份产品介绍
source: public
---

# 恒光股份产品介绍

## 氯化工产品链

氯酸钠主要用于净水、造纸、医疗、冶金和化工行业。

## 硫化工产品链

氨基磺酸主要用于甜味剂、清洗剂、漂白剂和电镀添加剂的生产。
""",
}


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    root = tmp_path / "documents"
    root.mkdir()
    for name, text in DOCS.items():
        (root / name).write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def retriever(tmp_path: Path, corpus: Path):
    async def build():
        store = VectorStore(path=tmp_path / "chroma", collection="retrieval")
        embeddings = MockEmbeddingProvider()
        await DocumentIngester(store=store, embeddings=embeddings).ingest_directory(corpus)
        return Retriever(store=store, embeddings=embeddings)

    return build


class TestQueryTerms:
    def test_cjk_bigrams_and_words(self):
        terms = query_terms("氯酸钠 NaClO3 用途")
        assert "氯酸" in terms and "酸钠" in terms
        assert "naclo3" in terms

    def test_single_char_query(self):
        assert query_terms("锗") == {"锗"}

    def test_lexical_overlap_bounds(self):
        terms = query_terms("氯酸钠")
        assert lexical_overlap(terms, "氯酸钠用于净水") == 1.0
        assert lexical_overlap(terms, "无关内容") == 0.0
        assert lexical_overlap(set(), "任何内容") == 0.0


class TestRetrieve:
    async def test_results_carry_citation_metadata(self, retriever):
        service = await retriever()
        results = await service.retrieve("氯酸钠有什么用途", top_k=3)
        assert results
        top = results[0]
        assert top.document_id == "hg-products"
        assert top.title == "恒光股份产品介绍"
        assert top.section == "氯化工产品链"
        assert top.source == "public"
        assert "氯酸钠" in top.content
        assert 0 < top.score <= 1
        assert top.chunk_id.startswith("hg-products::")

    async def test_default_top_k_comes_from_settings(self, retriever):
        service = await retriever()
        assert service.top_k == Settings().rag_top_k
        assert len(await service.retrieve("恒光")) <= service.top_k

    async def test_results_are_ranked_by_score(self, retriever):
        service = await retriever()
        results = await service.retrieve("产业基地在哪里", top_k=5)
        scores = [result.score for result in results]
        assert scores == sorted(scores, reverse=True)
        assert results[0].section == "产业基地"

    async def test_irrelevant_query_returns_nothing(self, retriever):
        service = await retriever()
        assert await service.retrieve("帮我写一首诗", top_k=5) == []
        assert await service.retrieve("   ", top_k=5) == []

    async def test_citations_are_numbered_in_order(self, retriever):
        service = await retriever()
        results = await service.retrieve("氨基磺酸用途", top_k=3)
        citations = Retriever.build_citations(results)
        assert [citation.index for citation in citations] == list(range(1, len(results) + 1))
        citation = citations[0]
        assert citation.title == "恒光股份产品介绍"
        assert citation.section == "硫化工产品链"
        assert citation.marker == "[1]"
        assert citation.label == "恒光股份产品介绍 · 硫化工产品链"
        assert citation.url == ""
