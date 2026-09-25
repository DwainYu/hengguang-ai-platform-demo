"""Unit tests for Day-4 demo authentication (fixed bearer tokens, no JWT)."""

from __future__ import annotations

import pytest

from app.auth.auth import (
    DEMO_ADMIN,
    DEMO_MANAGER,
    DEMO_OPERATOR,
    DEMO_ROLES,
    DEMO_USERS,
    CurrentUser,
    authenticate,
    demo_current_users,
    demo_user,
    parse_authorization,
)
from app.db.seed import load_seed


class TestTokenParsing:
    def test_bearer_prefix_is_case_insensitive(self):
        assert parse_authorization("Bearer demo-admin-token") == "demo-admin-token"
        assert parse_authorization("bearer demo-admin-token") == "demo-admin-token"

    def test_surrounding_whitespace_is_ignored(self):
        assert parse_authorization("  Bearer   demo-manager-token  ") == "demo-manager-token"

    def test_bare_token_is_accepted(self):
        assert parse_authorization("demo-operator-token") == "demo-operator-token"

    @pytest.mark.parametrize("value", [None, "", "   ", "Bearer ", "Bearer"])
    def test_empty_values_have_no_token(self, value):
        assert parse_authorization(value) is None


class TestAuthenticate:
    def test_each_demo_token_maps_to_its_role(self):
        assert authenticate("Bearer demo-admin-token").role == "admin"
        assert authenticate("Bearer demo-manager-token").role == "manager"
        assert authenticate("Bearer demo-operator-token").role == "operator"

    def test_known_identity_fields(self):
        user = authenticate("Bearer demo-manager-token")
        assert isinstance(user, CurrentUser)
        assert user.id == "demo-manager"
        assert user.username == "manager_demo"
        assert user.user_id == 2

    @pytest.mark.parametrize(
        "header", [None, "", "Bearer nope", "Token demo-admin-token", "Bearer demo-admin"]
    )
    def test_unknown_or_missing_token_authenticates_nobody(self, header):
        assert authenticate(header) is None

    def test_missing_header_never_inherits_admin(self):
        """The critical demo safety property: no token must not mean admin."""

        assert authenticate(None) is not DEMO_ADMIN
        assert authenticate(None) is None

    def test_token_lookup_helpers(self):
        assert demo_user("demo-admin-token").username == "admin_demo"
        assert demo_user("nope") is None
        assert demo_user(None) is None
        assert {user.token for user in DEMO_USERS} == {
            "demo-admin-token",
            "demo-manager-token",
            "demo-operator-token",
        }


class TestDemoUserConsistency:
    def test_three_roles_only(self):
        assert DEMO_ROLES == ("admin", "manager", "operator")
        assert len(DEMO_USERS) == 3

    def test_current_user_helpers_match_the_token_map(self):
        assert demo_current_users() == (DEMO_ADMIN, DEMO_MANAGER, DEMO_OPERATOR)

    @pytest.mark.parametrize("demo", DEMO_USERS, ids=[user.role for user in DEMO_USERS])
    def test_auth_map_matches_the_seeded_users_table(self, demo):
        """``app.auth`` and ``data/synthetic/seed.json`` must not drift apart.

        The audit log stores ``users.id``, so the row ids used by auth have to be
        the ones the seeder inserts (in file order: admin, manager, operator).
        """

        rows = load_seed()["users"]
        index = [row["username"] for row in rows].index(demo.username)
        row = rows[index]
        assert demo.row_id == index + 1
        assert row["role"] == demo.role
        assert row["token"] == demo.token

    def test_tokens_are_demo_credentials_not_secrets(self):
        assert all(token.startswith("demo-") for token in [user.token for user in DEMO_USERS])
