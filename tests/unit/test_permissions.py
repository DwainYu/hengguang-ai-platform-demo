"""Unit tests for the Day-4 RBAC permission model."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agent.tools import build_default_registry
from app.agent.tools.business import BusinessQueryTool
from app.auth.auth import DEMO_USERS
from app.auth.permissions import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    Permission,
    allowed_tool_names,
    has_permission,
    normalize_role,
    permission_for_tool,
    permissions_for_role,
    roles_for_permission,
)


class TestRoleMatrix:
    def test_admin_holds_every_permission(self):
        assert permissions_for_role("admin") == ALL_PERMISSIONS

    @pytest.mark.parametrize(
        "permission",
        [
            Permission.CHAT_RUN,
            Permission.MODELS_LIST,
            Permission.KNOWLEDGE_QUERY,
            Permission.AGENT_RUN,
            Permission.AUDIT_READ,
            Permission.TOOL_KNOWLEDGE,
            Permission.TOOL_ERP,
            Permission.TOOL_SAFETY,
        ],
    )
    def test_manager_allowed_operations(self, permission):
        assert has_permission("manager", permission) is True

    @pytest.mark.parametrize("permission", [Permission.KNOWLEDGE_INGEST, Permission.USERS_MANAGE])
    def test_manager_denied_operations(self, permission):
        assert has_permission("manager", permission) is False

    @pytest.mark.parametrize(
        "permission",
        [
            Permission.CHAT_RUN,
            Permission.KNOWLEDGE_QUERY,
            Permission.AGENT_RUN,
            Permission.TOOL_SAFETY,
        ],
    )
    def test_operator_allowed_operations(self, permission):
        assert has_permission("operator", permission) is True

    @pytest.mark.parametrize(
        "permission",
        [
            Permission.KNOWLEDGE_INGEST,
            Permission.AUDIT_READ,
            Permission.MODELS_LIST,
            Permission.USERS_MANAGE,
            Permission.TOOL_ERP,
        ],
    )
    def test_operator_denied_operations(self, permission):
        assert has_permission("operator", permission) is False

    def test_matrix_is_closed_under_known_roles(self):
        assert set(ROLE_PERMISSIONS) == {user.role for user in DEMO_USERS}
        for role, granted in ROLE_PERMISSIONS.items():
            assert granted <= ALL_PERMISSIONS, role

    def test_manager_is_strictly_below_admin_and_above_operator(self):
        assert (
            permissions_for_role("operator")
            < permissions_for_role("manager")
            <= permissions_for_role("admin")
        )


class TestPermissionHelpers:
    def test_unknown_role_falls_back_to_the_most_restrictive_demo_role(self):
        assert normalize_role(None) == "operator"
        assert normalize_role("root") == "operator"
        assert has_permission("root", Permission.AUDIT_READ) is False

    def test_unknown_permission_is_denied(self):
        assert has_permission("admin", "does:not:exist") is False

    def test_permission_accepts_plain_strings(self):
        assert has_permission("admin", "audit:read") is True

    def test_roles_for_permission(self):
        assert roles_for_permission(Permission.KNOWLEDGE_INGEST) == ("admin",)
        assert set(roles_for_permission(Permission.AUDIT_READ)) == {"admin", "manager"}
        assert set(roles_for_permission(Permission.TOOL_SAFETY)) == {"admin", "manager", "operator"}


class TestToolPermissions:
    @pytest.mark.parametrize(
        ("tool", "permission"),
        [
            ("knowledge_search", Permission.TOOL_KNOWLEDGE),
            ("document_lookup", Permission.TOOL_KNOWLEDGE),
            ("erp_purchase_analysis", Permission.TOOL_ERP),
            ("safety_incident_analysis", Permission.TOOL_SAFETY),
        ],
    )
    def test_tool_permission_mapping(self, tool, permission):
        assert permission_for_tool(tool) is permission

    def test_unmapped_tool_has_no_tool_permission(self):
        assert permission_for_tool("delete_everything") is None

    def test_tool_and_role_permissions_are_different_families(self):
        """A route permission must not grant a tool permission and vice versa."""

        assert Permission.TOOL_ERP not in {Permission.KNOWLEDGE_INGEST, Permission.AUDIT_READ}
        assert has_permission("operator", Permission.AGENT_RUN) is True
        assert has_permission("operator", Permission.TOOL_ERP) is False

    def test_allowed_tool_names_per_role(self):
        names = [
            "knowledge_search",
            "document_lookup",
            "erp_purchase_analysis",
            "safety_incident_analysis",
        ]
        assert allowed_tool_names("operator", names) == [
            "knowledge_search",
            "document_lookup",
            "safety_incident_analysis",
        ]
        assert allowed_tool_names("manager", names) == names
        assert allowed_tool_names("admin", names) == names


class TestDefaultRegistry:
    """SPEC Day 4 §五: the registry holds exactly four tools and refuses surprises."""

    @pytest.fixture
    def registry(self):
        """The tools only store the service at construction time, so a stub is enough."""

        return build_default_registry(SimpleNamespace(name="stub-knowledge-service"))

    def test_four_tools_registered(self, registry):
        assert registry.names() == [
            "knowledge_search",
            "document_lookup",
            "erp_purchase_analysis",
            "safety_incident_analysis",
        ]

    def test_duplicate_registration_fails(self, registry):
        from app.agent.tools.erp import ErpPurchaseAnalysisTool

        with pytest.raises(ValueError, match="already registered"):
            registry.register(ErpPurchaseAnalysisTool())

    def test_unknown_tool_lookup_fails(self, registry):
        with pytest.raises(KeyError, match="Unknown tool"):
            registry.get("erp_write_order")

    def test_schemas_are_generated_for_every_tool(self, registry):
        schemas = registry.openai_schemas()
        assert len(schemas) == 4
        by_name = {schema["function"]["name"]: schema["function"] for schema in schemas}
        assert set(by_name) == set(registry.names())
        for function in by_name.values():
            assert function["description"]
            assert function["parameters"]["type"] == "object"
        # business tools expose their operations as a closed enum, never free text
        assert set(
            by_name["erp_purchase_analysis"]["parameters"]["properties"]["operation"]["enum"]
        ) == set(registry.get("erp_purchase_analysis").operations)
        assert set(
            by_name["safety_incident_analysis"]["parameters"]["properties"]["operation"]["enum"]
        ) == set(registry.get("safety_incident_analysis").operations)

    def test_business_tools_declare_their_permissions(self, registry):
        for name, expected in (
            ("erp_purchase_analysis", Permission.TOOL_ERP),
            ("safety_incident_analysis", Permission.TOOL_SAFETY),
            ("knowledge_search", Permission.TOOL_KNOWLEDGE),
        ):
            assert registry.get(name).permission == expected

    def test_business_operations_are_the_fixed_whitelist(self, registry):
        erp: BusinessQueryTool = registry.get("erp_purchase_analysis")
        safety: BusinessQueryTool = registry.get("safety_incident_analysis")
        assert set(erp.operations) == {
            "purchase_price_trend",
            "top_materials_by_spend",
            "supplier_summary",
            "recent_purchase_orders",
            "inventory_summary",
            "material_consumption",
            "purchase_amount_stats",
        }
        assert set(safety.operations) == {
            "incident_by_area",
            "incident_by_severity",
            "incident_by_category",
            "recent_high_risk",
            "incident_trend",
        }
