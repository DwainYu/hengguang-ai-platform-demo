"""Unit tests for chunking (SPEC section 6.2, test name `test_chunking`)."""

from __future__ import annotations

from app.rag.chunker import (
    chunk_document,
    split_markdown_blocks,
    split_text_with_overlap,
)
from app.rag.schemas import DocumentMetadata

METADATA = DocumentMetadata(document_id="doc-1", title="文档标题", url="https://example.com")

MARKDOWN = """\
# 文档标题

引言段落。

## 主营业务

恒光股份主要业务为硫化工、氯化工产品链。

## 产业基地

怀化、衡阳、老挝三大基地。
"""


def test_headings_define_blocks_and_section_labels():
    chunks = chunk_document(METADATA, split_markdown_blocks(MARKDOWN), chunk_size=1000)
    assert [chunk.section for chunk in chunks] == [None, "主营业务", "产业基地"]
    assert "硫化工" in chunks[1].text
    # The heading line stays inside the chunk so the text remains self-describing.
    assert chunks[1].text.startswith("## 主营业务")


def test_nested_heading_path():
    blocks = split_markdown_blocks("# T\n## 产品\n### 氯化工产品链\n氯酸钠\n")
    assert blocks[-1].section == "产品 > 氯化工产品链"


def test_chunks_carry_citation_metadata_and_ids():
    chunks = chunk_document(METADATA, split_markdown_blocks(MARKDOWN), chunk_size=1000)
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))
    assert [chunk.chunk_id for chunk in chunks] == [f"doc-1::{i:04d}" for i in range(len(chunks))]
    assert chunks[1].title == "文档标题"
    assert chunks[1].url == "https://example.com"
    assert chunks[1].char_count == len(chunks[1].text)
    storage = chunks[1].to_storage_metadata()
    assert storage["document_id"] == "doc-1"
    assert storage["section"] == "主营业务"
    assert "page" not in storage  # unknown pages are omitted, not faked


def test_oversized_section_is_split_on_sentences_with_overlap():
    body = "。".join(f"第{i}句说明恒光股份的生产情况" for i in range(60)) + "。"
    chunks = chunk_document(
        METADATA,
        split_markdown_blocks(f"# T\n\n## 长章节\n\n{body}\n"),
        chunk_size=300,
        chunk_overlap=60,
    )
    # First chunk is the level-1 preamble; the rest are windows of the long section.
    windows = [chunk for chunk in chunks if chunk.section == "长章节"]
    assert len(windows) > 1
    assert all(len(chunk.text) <= 300 for chunk in chunks)
    # Consecutive windows repeat content instead of silently dropping it.
    assert windows[0].text[-20:] in windows[1].text


def test_runaway_sentence_without_terminators_is_hard_split():
    pieces = split_text_with_overlap("无" * 500, chunk_size=120, chunk_overlap=20)
    assert pieces
    assert all(len(piece) <= 120 for piece in pieces)
    assert sum(len(piece) for piece in pieces) == 500


def test_short_text_stays_one_chunk():
    assert split_text_with_overlap("短句子。", 1000, 150) == ["短句子。"]


def test_embedding_text_includes_title_and_section():
    chunks = chunk_document(METADATA, split_markdown_blocks(MARKDOWN), chunk_size=1000)
    assert chunks[1].embedding_text.startswith("文档标题 > 主营业务\n## 主营业务")
    # Without a section the document title alone is the header.
    assert chunks[0].embedding_text.startswith("文档标题\n")
