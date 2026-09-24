"""Unit tests for the RAG prompt contract and pipeline (SPEC sections 6.3 / 6.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.embeddings.mock import MockEmbeddingProvider
from app.gateway.mock import MockProvider
from app.rag.ingest import DocumentIngester
from app.rag.pipeline import RagPipeline
from app.rag.prompt import (
    CONTEXT_HEADER,
    NO_CONTEXT_BODY,
    RAG_SYSTEM_PROMPT,
    build_messages,
    format_context,
)
from app.rag.retriever import Retriever
from app.rag.schemas import Citation, RetrievedChunk
from app.rag.store import VectorStore

RESULT = RetrievedChunk(
    chunk_id="hg-profile::0001",
    document_id="hg-profile",
    title="恒光股份公开简介",
    content="## 主营业务\n\n恒光股份主要业务为硫化工、氯化工产品链。",
    score=0.42,
    section="主营业务",
    page=3,
    url="https://example.com/profile",
)


def _citations(*results: RetrievedChunk) -> list[Citation]:
    return Retriever.build_citations(list(results))


class TestPromptContract:
    def test_answer_policy_covers_spec_rules(self):
        for requirement in ("没有足够信息", "不得虚构", "[编号]", "区分事实", "优先依据"):
            assert requirement in RAG_SYSTEM_PROMPT

    def test_context_block_is_numbered_with_citation_labels(self):
        block = format_context([RESULT], _citations(RESULT))
        assert block.startswith(CONTEXT_HEADER)
        assert "[1] 恒光股份公开简介 · 主营业务 · 第 3 页" in block
        assert "硫化工" in block

    def test_empty_context_marks_no_evidence(self):
        block = format_context([], [])
        assert NO_CONTEXT_BODY in block

    def test_messages_keep_question_separate_from_context(self):
        messages = build_messages("恒光主要有哪些业务？", [RESULT], _citations(RESULT))
        assert [message["role"] for message in messages] == ["system", "system", "user"]
        assert messages[0]["content"] == RAG_SYSTEM_PROMPT
        assert messages[1]["content"].startswith(CONTEXT_HEADER)
        assert messages[2]["content"] == "恒光主要有哪些业务？"

    async def test_mock_provider_uses_the_retrieved_context(self):
        messages = build_messages("恒光主要有哪些业务？", [RESULT], _citations(RESULT))
        response = await MockProvider().chat(messages, model="mock-model")
        assert "硫化工" in response.content
        assert "[1] 恒光股份公开简介 · 主营业务 · 第 3 页" in response.content

    async def test_mock_provider_without_context_says_it_does_not_know(self):
        messages = build_messages("明天的股价会涨吗", [], [])
        response = await MockProvider().chat(messages, model="mock-model")
        assert "没有足够信息" in response.content


class TestRagPipeline:
    @pytest.fixture
    async def pipeline(self, tmp_path: Path) -> RagPipeline:
        root = tmp_path / "documents"
        root.mkdir()
        (root / "profile.md").write_text(
            "---\n"
            "document_id: hg-profile\n"
            "title: 恒光股份公开简介\n"
            "url: https://example.com/profile\n"
            "---\n"
            "\n"
            "# 恒光股份公开简介\n"
            "\n"
            "## 主营业务\n"
            "\n"
            "恒光股份主要业务为硫化工、氯化工产品链的研发、生产和销售。\n",
            encoding="utf-8",
        )
        embeddings = MockEmbeddingProvider()
        store = VectorStore(path=tmp_path / "chroma", collection="pipeline")
        await DocumentIngester(store=store, embeddings=embeddings).ingest_directory(root)
        config = Settings(documents_dir=str(root))
        return RagPipeline(
            Retriever(store=store, embeddings=embeddings, config=config),
            config=config,
        )

    async def test_answer_is_grounded_and_cited(self, pipeline: RagPipeline):
        answer = await pipeline.answer("恒光主要有哪些业务？", top_k=2)
        assert answer.grounded is True
        assert answer.provider == "mock"
        assert answer.results and answer.citations
        assert "[1]" in answer.answer
        assert "硫化工" in answer.answer
        assert answer.citations[0].title == "恒光股份公开简介"
        assert answer.citations[0].section == "主营业务"

    async def test_answer_without_evidence_declares_insufficient_info(self, pipeline: RagPipeline):
        answer = await pipeline.answer("明天的股价会涨吗")
        assert answer.grounded is False
        assert answer.results == []
        assert answer.citations == []
        assert "没有足够信息" in answer.answer

    async def test_retrieve_is_reusable_without_llm(self, pipeline: RagPipeline):
        results = await pipeline.retrieve("硫化工", top_k=3)
        assert results
        assert all(result.content for result in results)
