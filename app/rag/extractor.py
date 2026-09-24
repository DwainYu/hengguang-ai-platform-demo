"""Text extraction: read a Markdown / TXT / PDF file into metadata + text blocks.

Only public materials are ingested (SPEC section 6.1). Markdown documents carry
their citation metadata in a YAML front matter block:

```text
---
document_id: hengguang-annual-report-2025
title: 湖南恒光科技股份有限公司2025年年度报告摘要
source: public
url: https://static.cninfo.com.cn/...
published_at: 2026-04-28
---
```

Missing values fall back to the file name / first heading, so a plain note
still ingests with a usable document_id.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from pypdf import PdfReader

from app.rag.chunker import TextBlock, split_markdown_blocks
from app.rag.schemas import DocumentMetadata

MARKDOWN_SUFFIXES = {".md", ".markdown"}
TEXT_SUFFIXES = {".txt"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = MARKDOWN_SUFFIXES | TEXT_SUFFIXES | PDF_SUFFIXES

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
_NON_ID_RE = re.compile(r"[^a-z0-9]+")


class UnsupportedDocumentError(ValueError):
    """Raised for files we do not know how to extract."""


@dataclass(frozen=True)
class ExtractedDocument:
    """Metadata plus the text blocks of one source file."""

    metadata: DocumentMetadata
    blocks: list[TextBlock]

    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks)


def slugify_identifier(value: str) -> str:
    """File name / title -> stable, ASCII-safe document_id fragment."""
    return _NON_ID_RE.sub("-", value.lower()).strip("-") or "document"


def parse_front_matter(raw: str) -> tuple[dict[str, object], str]:
    """Split YAML front matter from the body of a markdown/text document."""
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, raw
    if not isinstance(data, dict):
        return {}, raw
    return data, raw[match.end() :]


def build_metadata(*, path: Path, root: Path, front_matter: dict[str, object]) -> DocumentMetadata:
    """Resolve citation metadata for a file, filling sensible defaults."""
    relative = _relative_path(path, root)
    document_id = str(front_matter.get("document_id") or "").strip() or slugify_identifier(
        path.stem
    )
    title = str(front_matter.get("title") or "").strip()
    if not title:
        title = _first_heading(path) or path.stem
    page = front_matter.get("page")
    section = front_matter.get("section")
    return DocumentMetadata(
        document_id=document_id,
        title=title,
        source=str(front_matter.get("source") or "public").strip(),
        url=str(front_matter.get("url") or "").strip(),
        published_at=str(front_matter.get("published_at") or "").strip(),
        section=str(section).strip() if section else None,
        page=int(page) if page is not None and str(page).strip() else None,
        path=relative,
    )


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _first_heading(path: Path) -> str:
    if path.suffix.lower() in PDF_SUFFIXES:
        return ""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    _, body = parse_front_matter(raw)
    match = _HEADING_RE.search(body)
    return match.group(1).strip() if match else ""


def extract_pdf_blocks(path: Path) -> list[TextBlock]:
    """One block per PDF page so citations can point at a page number."""
    reader = PdfReader(str(path))
    blocks: list[TextBlock] = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            blocks.append(TextBlock(text=text, page=number))
    return blocks


def extract_document(path: Path, *, root: Path) -> ExtractedDocument:
    """Extract one supported file into metadata + text blocks."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedDocumentError(f"unsupported document type: {path.name}")

    if suffix in PDF_SUFFIXES:
        front_matter: dict[str, object] = {}
        blocks = extract_pdf_blocks(path)
    else:
        raw = path.read_text(encoding="utf-8", errors="replace")
        front_matter, body = parse_front_matter(raw)
        body = _COMMENT_RE.sub("", body)
        if suffix in MARKDOWN_SUFFIXES:
            blocks = split_markdown_blocks(body)
        else:
            blocks = [TextBlock(text=body.strip())]

    metadata = build_metadata(path=path, root=root, front_matter=front_matter)
    return ExtractedDocument(metadata=metadata, blocks=blocks)
