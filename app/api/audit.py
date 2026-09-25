"""GET /api/audit — read the audit trail (admin + manager only, SPEC section 9).

Pagination (``page`` / ``page_size``) plus the filters the demo needs: ``tool``,
``action``, ``status`` and ``request_id``. ``GET /api/audit/{request_id}`` returns
the whole trail of one run, which is the fastest way to follow
HTTP → Agent → Permission → Tool → Audit in the demo.

Rows only ever contain compact summaries: the audit writer decides what is safe to
store, so this endpoint cannot expose prompts or document text.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.errors import NotFoundError
from app.auth.auth import CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission
from app.observability.audit import AuditLog, get_audit_log
from app.observability.middleware import request_id_of

router = APIRouter(prefix="/api/audit", tags=["audit"])

MAX_PAGE_SIZE = 100

AuditReaderDep = Annotated[CurrentUser, Depends(require(Permission.AUDIT_READ))]
AuditLogDep = Annotated[AuditLog, Depends(get_audit_log)]
RequestIdDep = Annotated[str, Depends(request_id_of)]


@router.get("")
async def list_audit(
    user: AuditReaderDep,
    audit: AuditLogDep,
    request_id: RequestIdDep,
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Rows per page")] = 20,
    tool: Annotated[str | None, Query(description="Filter by tool name")] = None,
    action: Annotated[str | None, Query(description="Filter by audited action")] = None,
    status: Annotated[
        str | None, Query(description="Filter by status (success/error/denied)")
    ] = None,
    target_request_id: Annotated[
        str | None, Query(alias="request_id", description="Filter by the request id of a run")
    ] = None,
) -> dict:
    """Paginated audit entries, newest first: ``{items, page, page_size, total}``."""

    result = audit.list(
        page=page,
        page_size=page_size,
        tool=tool,
        action=action,
        status=status,
        request_id=target_request_id,
    )
    result["request_id"] = request_id
    result["viewer"] = {"username": user.username, "role": user.role}
    return result


@router.get("/{queried_request_id}")
async def audit_by_request_id(
    queried_request_id: str,
    user: AuditReaderDep,
    audit: AuditLogDep,
    request_id: RequestIdDep,
) -> dict:
    """Every audit row that belongs to one ``request_id`` (the trace of a single run)."""

    page = audit.list(request_id=queried_request_id, page=1, page_size=MAX_PAGE_SIZE)
    if not page["items"]:
        raise NotFoundError(
            "没有找到该 request_id 的审计记录", details={"request_id": queried_request_id}
        )
    return {"request_id": request_id, "query_request_id": queried_request_id, **page}
