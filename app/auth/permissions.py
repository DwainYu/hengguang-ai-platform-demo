"""Role/permission matrix (SPEC section 9) — role permissions only.

Two distinct permission families live in this module on purpose:

* **API permissions** (``chat:run``, ``knowledge:ingest``, ``audit:read`` ...) are
  enforced by FastAPI dependencies on the routes.
* **Tool permissions** (``tool:erp``, ``tool:safety``, ``tool:knowledge``) are
  enforced by the agent ``ToolExecutor`` before a tool runs, so a denial also
  works when the model calls the tool from inside an agent loop.

Keeping them separate means "can call this endpoint" and "may use this tool" stay
independently assignable; a tool never inherits rights from a route and vice versa.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from app.auth.auth import DEMO_ROLES, ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR


class Permission(StrEnum):
    """Stable permission identifiers."""

    CHAT_RUN = "chat:run"
    MODELS_LIST = "models:list"
    KNOWLEDGE_QUERY = "knowledge:query"
    KNOWLEDGE_INGEST = "knowledge:ingest"
    AGENT_RUN = "agent:run"
    AUDIT_READ = "audit:read"
    USERS_MANAGE = "users:manage"
    TOOL_KNOWLEDGE = "tool:knowledge"
    TOOL_ERP = "tool:erp"
    TOOL_SAFETY = "tool:safety"


ALL_PERMISSIONS: Final[frozenset[Permission]] = frozenset(Permission)

#: Matrix copied from SPEC section 9 / Day-4 role list.
ROLE_PERMISSIONS: Final[dict[str, frozenset[Permission]]] = {
    ROLE_ADMIN: ALL_PERMISSIONS,
    ROLE_MANAGER: frozenset(
        {
            Permission.CHAT_RUN,
            Permission.MODELS_LIST,
            Permission.KNOWLEDGE_QUERY,
            Permission.AGENT_RUN,
            Permission.AUDIT_READ,
            Permission.TOOL_KNOWLEDGE,
            Permission.TOOL_ERP,
            Permission.TOOL_SAFETY,
        }
    ),
    ROLE_OPERATOR: frozenset(
        {
            Permission.CHAT_RUN,
            Permission.KNOWLEDGE_QUERY,
            Permission.AGENT_RUN,
            Permission.TOOL_KNOWLEDGE,
            Permission.TOOL_SAFETY,
        }
    ),
}

#: Tools an agent may even see for a role (derived from the tool permissions).
_TOOL_PERMISSIONS: Final[tuple[tuple[str, Permission], ...]] = (
    ("knowledge_search", Permission.TOOL_KNOWLEDGE),
    ("document_lookup", Permission.TOOL_KNOWLEDGE),
    ("erp_purchase_analysis", Permission.TOOL_ERP),
    ("safety_incident_analysis", Permission.TOOL_SAFETY),
)


def normalize_role(role: str | None) -> str:
    """Return a known role name, defaulting to the most restrictive demo role."""

    return role if role in DEMO_ROLES else ROLE_OPERATOR


def has_permission(role: str | None, permission: Permission | str) -> bool:
    """True when ``role`` holds ``permission``."""

    try:
        wanted = Permission(permission)
    except ValueError:
        return False
    return wanted in ROLE_PERMISSIONS.get(normalize_role(role), frozenset())


def permissions_for_role(role: str | None) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(normalize_role(role), frozenset())


def roles_for_permission(permission: Permission | str) -> tuple[str, ...]:
    wanted = Permission(permission)
    return tuple(role for role in DEMO_ROLES if wanted in ROLE_PERMISSIONS.get(role, frozenset()))


def permission_for_tool(tool_name: str) -> Permission | None:
    """Tool permission required to execute ``tool_name`` (``None`` when unmapped)."""

    for name, permission in _TOOL_PERMISSIONS:
        if name == tool_name:
            return permission
    return None


def allowed_tool_names(role: str | None, tool_names: list[str] | tuple[str, ...]) -> list[str]:
    """Subset of ``tool_names`` the role may use (unknown tools stay visible)."""

    allowed: list[str] = []
    for name in tool_names:
        permission = permission_for_tool(name)
        if permission is None or has_permission(role, permission):
            allowed.append(name)
    return allowed


__all__ = [
    "ALL_PERMISSIONS",
    "Permission",
    "ROLE_PERMISSIONS",
    "allowed_tool_names",
    "has_permission",
    "normalize_role",
    "permission_for_tool",
    "permissions_for_role",
    "roles_for_permission",
]
