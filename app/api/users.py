"""GET /api/users — demo user directory (admin only, SPEC section 9 "用户管理").

There is no real user management in Day 4: this route exposes the three demo
accounts so the RBAC matrix is visible in the API, and it deliberately omits the
tokens (they are public demo credentials documented in README, but they must not
spread through every response body).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.auth import DEMO_USERS, CurrentUser
from app.auth.dependencies import require
from app.auth.permissions import Permission, permissions_for_role, roles_for_permission
from app.observability.middleware import request_id_of

router = APIRouter(prefix="/api", tags=["users"])

AdminDep = Annotated[CurrentUser, Depends(require(Permission.USERS_MANAGE))]
RequestIdDep = Annotated[str, Depends(request_id_of)]


@router.get("/users")
async def list_users(user: AdminDep, request_id: RequestIdDep) -> dict:
    """The three demo accounts with their role permissions (no tokens)."""

    return {
        "request_id": request_id,
        "users": [
            {
                "id": demo.id,
                "username": demo.username,
                "role": demo.role,
                "permissions": sorted(str(item) for item in _permissions_for(demo.role)),
            }
            for demo in DEMO_USERS
        ],
        "permission_roles": {
            permission.value: roles_for_permission(permission)
            for permission in (
                Permission.KNOWLEDGE_INGEST,
                Permission.AUDIT_READ,
                Permission.TOOL_ERP,
                Permission.TOOL_SAFETY,
            )
        },
    }


def _permissions_for(role: str):
    return permissions_for_role(role)
