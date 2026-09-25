"""document_lookup tool: one knowledge-base document's business metadata.

Backed by the minimal ``KnowledgeService.get_document`` lookup; internal
storage structures are not exposed — only business fields.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agent.tools.base import Tool, ToolResult
from app.auth.permissions import Permission
from app.services.knowledge_service import KnowledgeService


class DocumentLookupArgs(BaseModel):
    """Arguments for document_lookup."""

    document_id: str = Field(..., min_length=1, max_length=200)


class DocumentLookupTool(Tool):
    """Look up one ingested document by document_id."""

    name = "document_lookup"
    permission = Permission.TOOL_KNOWLEDGE
    description = (
        "Look up one knowledge-base document's metadata (title, source, url, "
        "published_at, sections, chunk count) by its document_id."
    )
    args_model = DocumentLookupArgs

    def __init__(self, knowledge_service: KnowledgeService) -> None:
        self._service = knowledge_service

    async def execute(self, arguments: dict) -> ToolResult:
        document_id = arguments["document_id"]
        summary = self._service.get_document(document_id)
        if summary is None:
            return ToolResult(
                tool_name=self.name,
                success=False,
                content="",
                metadata={"document_id": document_id},
                error=f"Document not found: {document_id}",
            )
        lines = [summary.title, f"document_id: {summary.document_id}"]
        source_line = f"source: {summary.source}"
        if summary.url:
            source_line += f"（{summary.url}）"
        lines.append(source_line)
        if summary.published_at:
            lines.append(f"published_at: {summary.published_at}")
        if summary.sections:
            lines.append(f"章节：{'、'.join(summary.sections)}")
        lines.append(f"规模：{summary.chunks} 个片段，共 {summary.chars} 字")
        return ToolResult(
            tool_name=self.name,
            success=True,
            content="\n".join(lines),
            metadata={
                "document_id": summary.document_id,
                "title": summary.title,
                "source": summary.source,
                "chunk_count": summary.chunks,
                "sections": summary.sections,
            },
        )
