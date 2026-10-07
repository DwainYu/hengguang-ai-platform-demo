"""FastAPI auth dependencies: bearer token → :class:`CurrentUser` → permission gate.

Authentication/authorisation logic lives here (plus :mod:`app.auth.auth` and
:mod:`app.auth.permissions`) — routes never parse headers themselves, they declare
``Depends(require(Permission.X))`` and receive a typed :class:`CurrentUser`.

Every route under ``/api`` is protected; ``GET /health`` (liveness) and
``GET /metrics`` (operational counters, no business data) are the only public
endpoints. Missing/invalid token → 401 ``UNAUTHENTICATED``; known token without
the permission → 403 ``PERMISSION_DENIED``; both as the shared error envelope.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Final

from fastapi import Depends, Request

from app.api.errors import AuthenticationError, PermissionDeniedError
from app.auth.auth import DEMO_USERS, CurrentUser, authenticate
from app.auth.permissions import Permission, has_permission
from app.observability.audit import Actor, AuditAction, AuditLog, AuditStatus, get_audit_log
from app.observability.middleware import endpoint_label, request_id_of

AUTHORIZATION_HEADER: Final = "Authorization"
WWW_AUTHENTICATE: Final = 'Bearer realm="hengguang-demo"'

DEMO_TOKEN_HINT: Final = "、".join(f"{user.role}" for user in DEMO_USERS)

#: Permission -> the audited action a *denied* attempt of that permission is filed
#: under. Denials deliberately reuse the same ``action`` as the successful call, so
#: ``action=knowledge.ingest`` returns both the completions and the refusals (the
#: permission that was missing stays in ``input_summary.required_permission``).
_DENIED_ACTION: Final[dict[Permission, str]] = {
    Permission.CHAT_RUN: AuditAction.CHAT_COMPLETE,
    Permission.MODELS_LIST: AuditAction.MODELS_LIST,
    Permission.KNOWLEDGE_QUERY: AuditAction.KNOWLEDGE_SEARCH,
    Permission.KNOWLEDGE_INGEST: AuditAction.KNOWLEDGE_INGEST,
    Permission.AGENT_RUN: AuditAction.AGENT_RUN,
    Permission.AUDIT_READ: AuditAction.AUDIT_READ,
    Permission.USERS_MANAGE: AuditAction.USERS_MANAGE,
}


def get_current_user(request: Request) -> CurrentUser:
    """Resolve the demo bearer token into a :class:`CurrentUser` or raise 401."""

    header = request.headers.get(AUTHORIZATION_HEADER)  # Starlette headers are case-insensitive
    user = authenticate(header)
    if user is None:
        raise AuthenticationError(
            "缺少或无效的 Bearer token" if header is None else "无效的 Bearer token",
            details={"scheme": "Bearer", "demo_tokens": DEMO_TOKEN_HINT},
            headers={"WWW-Authenticate": WWW_AUTHENTICATE},
        )
    return user


def require(permission: Permission | str) -> Callable[..., CurrentUser]:
    """Dependency factory: the caller must hold ``permission`` (401 → 403).

    A route-level denial is written to the audit trail as well: recording denied
    attempts is the point of having an audit log, and here the identity is known, so
    the SPEC ``audit_logs.user_id NOT NULL`` contract still holds.
    """

    wanted = Permission(permission)
    # `tool:*` permissions are enforced in the ToolExecutor, but `require()` stays
    # safe if one is ever declared on a route: derive a namespaced action from it.
    action = _DENIED_ACTION.get(wanted, f"tool.{wanted.value.split(':', 1)[-1]}")

    async def dependency(
        request: Request,
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if not has_permission(user.role, wanted):
            audit: AuditLog = get_audit_log()
            audit.record_api(
                Actor.from_user(user, request_id_of(request)),
                action=action,
                status=AuditStatus.DENIED,
                endpoint=endpoint_label(request.scope),
                input_summary={"required_permission": wanted.value, "role": user.role},
            )
            raise PermissionDeniedError(
                f"角色 '{user.role}' 没有权限 '{wanted.value}'",
                details={"required_permission": wanted.value, "role": user.role},
            )
        return user

    dependency.__name__ = f"require_{wanted.value.replace(':', '_')}"
    return dependency


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]

__all__ = [
    "AUTHORIZATION_HEADER",
    "CurrentUserDep",
    "DEMO_TOKEN_HINT",
    "get_current_user",
    "require",
]
