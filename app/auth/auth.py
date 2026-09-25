"""Demo identity: fixed bearer tokens, no JWT / OAuth / SSO (SPEC section 9).

The three tokens below are *demo credentials*, not secrets: they are written into
README/DEMO_SCRIPT on purpose. The only real rule in this file is that an unknown
or missing token is never allowed to inherit an admin role — unauthenticated
traffic stays unauthenticated and the API answers 401.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

ROLE_ADMIN: Final = "admin"
ROLE_MANAGER: Final = "manager"
ROLE_OPERATOR: Final = "operator"

DEMO_ROLES: Final[tuple[str, ...]] = (ROLE_ADMIN, ROLE_MANAGER, ROLE_OPERATOR)


@dataclass(frozen=True)
class CurrentUser:
    """Authenticated caller identity for the current request."""

    id: str
    username: str
    role: str
    user_id: int
    token: str = ""

    def __str__(self) -> str:  # pragma: no cover - logging helper
        return f"{self.username}({self.role})"


@dataclass(frozen=True)
class DemoUser:
    """One demo account: the fixed token plus its ``users`` table row id."""

    row_id: int
    id: str
    username: str
    role: str
    token: str

    def to_current_user(self) -> CurrentUser:
        return CurrentUser(
            id=self.id,
            username=self.username,
            role=self.role,
            user_id=self.row_id,
            token=self.token,
        )


DEMO_USERS: Final[tuple[DemoUser, ...]] = (
    DemoUser(1, "demo-admin", "admin_demo", ROLE_ADMIN, "demo-admin-token"),
    DemoUser(2, "demo-manager", "manager_demo", ROLE_MANAGER, "demo-manager-token"),
    DemoUser(3, "demo-operator", "operator_demo", ROLE_OPERATOR, "demo-operator-token"),
)

_USER_BY_TOKEN: Final[dict[str, DemoUser]] = {user.token: user for user in DEMO_USERS}

DEMO_ADMIN: Final[CurrentUser] = DEMO_USERS[0].to_current_user()
DEMO_MANAGER: Final[CurrentUser] = DEMO_USERS[1].to_current_user()
DEMO_OPERATOR: Final[CurrentUser] = DEMO_USERS[2].to_current_user()

BEARER_PREFIX: Final = "Bearer "


def parse_authorization(header_value: str | None) -> str | None:
    """Return the bearer token from an ``Authorization`` header value."""

    if not header_value:
        return None
    value = header_value.strip()
    if value.lower() == BEARER_PREFIX.strip().lower():
        return None
    if value.lower().startswith(BEARER_PREFIX.lower()):
        token = value[len(BEARER_PREFIX) :].strip()
        return token or None
    return value or None


def demo_user(token: str | None) -> DemoUser | None:
    """Look up a demo account by token (exact match, no fallback)."""

    if not token:
        return None
    return _USER_BY_TOKEN.get(token)


def authenticate(header_value: str | None) -> CurrentUser | None:
    """Resolve an ``Authorization`` header value into a :class:`CurrentUser`."""

    user = demo_user(parse_authorization(header_value))
    return user.to_current_user() if user else None


def demo_current_users() -> tuple[CurrentUser, ...]:
    return tuple(user.to_current_user() for user in DEMO_USERS)


__all__ = [
    "BEARER_PREFIX",
    "DEMO_ADMIN",
    "DEMO_MANAGER",
    "DEMO_OPERATOR",
    "DEMO_ROLES",
    "DEMO_USERS",
    "CurrentUser",
    "DemoUser",
    "ROLE_ADMIN",
    "ROLE_MANAGER",
    "ROLE_OPERATOR",
    "authenticate",
    "demo_current_users",
    "demo_user",
    "parse_authorization",
]
