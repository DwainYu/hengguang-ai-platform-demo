"""Markdown-aware chunker: 800-1200 chars, 100-200 overlap, keeps section metadata.

Strategy (SPEC section 6.2):

1. Split a document into heading-scoped blocks, so a chunk never mixes two
   sections and always carries the section name used for citations.
2. A block longer than ``chunk_size`` is split on sentence boundaries, with
   ``chunk_overlap`` characters repeated between windows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.rag.schemas import Chunk, DocumentMetadata

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_SENTENCE_END_RE = re.compile(r"(?<=[。！？；!?;\n])")


@dataclass(frozen=True)
class TextBlock:
    """A piece of text plus the place it came from."""

    text: str
    section: str | None = None
    page: int | None = None


def _section_path(stack: list[tuple[int, str]]) -> str | None:
    """Heading path used in citations; the level-1 heading is the title itself."""
    named = [name for level, name in stack if level > 1]
    if not named:
        return None
    return " > ".join(named)


def split_markdown_blocks(markdown: str) -> list[TextBlock]:
    """Split markdown into heading-scoped blocks (every heading starts a block)."""
    blocks: list[TextBlock] = []
    stack: list[tuple[int, str]] = []
    section: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            blocks.append(TextBlock(text=text, section=section))
        buffer.clear()

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            stack = [(lv, name) for lv, name in stack if lv < level]
            stack.append((level, match.group(2).strip()))
            section = _section_path(stack)
        buffer.append(line)
    flush()
    return blocks


def split_sentences(text: str) -> list[str]:
    """Split on 。！？；/newline so chunks end on readable boundaries."""
    parts = [part for part in _SENTENCE_END_RE.split(text) if part and part.strip()]
    if not parts:
        return [text] if text.strip() else []
    return sentences_with_continuations(parts)


def sentences_with_continuations(parts: list[str]) -> list[str]:
    """Attach fragments that do not end on a terminator to the previous sentence."""
    sentences: list[str] = []
    for part in parts:
        if sentences and not sentences[-1].rstrip().endswith(
            ("。", "！", "？", "；", "!", "?", ";", "\n")
        ):
            sentences[-1] += part
        else:
            sentences.append(part)
    return sentences


def _hard_split(sentence: str, chunk_size: int) -> list[str]:
    """Last resort for a single sentence longer than the chunk size."""
    stripped = sentence.strip()
    return [stripped[start : start + chunk_size] for start in range(0, len(stripped), chunk_size)]


def split_text_with_overlap(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split one long text into windows of at most ``chunk_size`` characters."""
    chunk_size = max(1, chunk_size)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size - 1))
    sentences = split_sentences(text.strip())
    if not sentences:
        return []
    if len("".join(sentences).strip()) <= chunk_size:
        return [text.strip()]

    windows: list[str] = []
    current: list[str] = []
    current_len = 0

    def close_window() -> None:
        nonlocal current, current_len
        windows.append("".join(current).strip())
        tail: list[str] = []
        tail_len = 0
        for sentence in reversed(current):
            if tail_len + len(sentence) > chunk_overlap:
                break
            tail.insert(0, sentence)
            tail_len += len(sentence)
        current, current_len = tail, tail_len

    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                close_window()
            windows.extend(_hard_split(sentence, chunk_size))
            current, current_len = [], 0
            continue
        if current and current_len + len(sentence) > chunk_size:
            close_window()
        current.append(sentence)
        current_len += len(sentence)

    if current:
        windows.append("".join(current).strip())
    return [window for window in windows if window]


def chunk_blocks(
    blocks: list[TextBlock],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextBlock]:
    """Keep one section per chunk; only oversized sections are split."""
    results: list[TextBlock] = []
    for block in blocks:
        text = block.text.strip()
        if not text:
            continue
        if len(text) <= chunk_size:
            results.append(TextBlock(text=text, section=block.section, page=block.page))
            continue
        for piece in split_text_with_overlap(text, chunk_size, chunk_overlap):
            results.append(TextBlock(text=piece, section=block.section, page=block.page))
    return results


def chunk_document(
    metadata: DocumentMetadata,
    blocks: list[TextBlock],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Turn extracted blocks into chunks ready for embedding."""
    return [
        Chunk.build(
            metadata=metadata,
            text=block.text,
            position=index,
            section=block.section,
            page=block.page,
        )
        for index, block in enumerate(
            chunk_blocks(blocks, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        )
    ]
