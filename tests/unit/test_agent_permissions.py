"""Unit tests: tool permissions and audit inside the agent layer (Day 4 §八).

These cover the requirement that RBAC is enforced **at the tool boundary**, not only
on the route: the executor must refuse a call before the tool touches any data,
return a structured ``PERMISSION_DENIED`` ``ToolResult``, keep the agent loop alive,
and still write one compact audit row.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import create_model

from app.agent.executor import ToolExecutor
from app.agent.registry import ToolRegistry
from app.agent.tools import build_default_registry
from app.agent.tools.base import Tool, ToolResult
from app.auth.auth import DEMO_ADMIN, DEMO_MANAGER, DEMO_OPERATOR
from app.auth.permissions import Permission
from app.db.database import Database
from app.gateway.base import ToolCall
from app.observability.audit import Actor, AuditLog
from app.observability.metrics import Metrics

ERP_CALL = ToolCall(
    id="call_1",
    name="erp_purchase_analysis",
    arguments={"operation": "supplier_summary", "days": 30},
)
SAFETY_CALL = ToolCall(
    id="call_2", name="safety_incident_analysis", arguments={"operation": "incident_by_area"}
)


class RecordingTool(Tool):
    """Test double that records whether business code was actually reached."""

    name = "recording_tool"
    description = "Records that it ran."
    args_model = create_model("RecordingArgs", operation=(str, "x"), days=(int, 3))
    permission = Permission.TOOL_ERP

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def execute(self, arguments: dict) -> ToolResult:
        self.calls.append(arguments)
        return ToolResult(
            tool_name=self.name, success=True, content="ran", metadata={"result_count": 1}
        )


@pytest.fixture
def registry(seeded_database: Database) -> ToolRegistry:
    return build_default_registry(
        SimpleNamespace(name="stub-knowledge-service"), database=seeded_database
    )


def memory_audit() -> AuditLog:
    """Audit log whose database was never initialised: records stay in memory."""

    return AuditLog(lambda: Database(url="sqlite:///:memory:"))


def actor_for(user) -> Actor:
    return Actor.from_user(user, "req_executor_test")


@pytest.mark.asyncio
class TestPermissionBoundary:
    async def test_operator_cannot_execute_the_erp_tool(self, registry):
        executor = ToolExecutor(registry, audit=memory_audit())
        result = await executor.execute(ERP_CALL, actor=actor_for(DEMO_OPERATOR))
        assert result.success is False
        assert result.error_code == "PERMISSION_DENIED"
        assert result.error_detail == {"code": "PERMISSION_DENIED", "message": result.error}
        assert "operator" in result.error
        assert result.metadata["permission_required"] == "tool:erp"

    async def test_denial_happens_before_any_data_access(self):
        tool = RecordingTool()
        registry = ToolRegistry()
        registry.register(tool)
        executor = ToolExecutor(registry)
        call = ToolCall(id="c", name="recording_tool", arguments={"operation": "x", "days": 3})
        await executor.execute(call, actor=actor_for(DEMO_OPERATOR))
        assert tool.calls == []

    async def test_manager_and_admin_may_execute_the_erp_tool(self, registry):
        executor = ToolExecutor(registry)
        for user in (DEMO_MANAGER, DEMO_ADMIN):
            result = await executor.execute(ERP_CALL, actor=actor_for(user))
            assert result.success, result.error
            assert result.metadata["payload"]["data"]

    async def test_every_role_may_use_the_safety_tool(self, registry):
        executor = ToolExecutor(registry)
        for user in (DEMO_OPERATOR, DEMO_MANAGER, DEMO_ADMIN):
            result = await executor.execute(SAFETY_CALL, actor=actor_for(user))
            assert result.success, result.error

    async def test_knowledge_tools_are_allowed_for_operator(self, registry):
        executor = ToolExecutor(registry)
        assert executor.is_allowed("knowledge_search", actor_for(DEMO_OPERATOR))
        assert executor.permission_for("document_lookup") == "tool:knowledge"

    async def test_without_an_actor_the_executor_does_not_invent_one(self, registry):
        """Unit-test / scripted mode: no identity, no RBAC layer (Day-3 behaviour)."""

        executor = ToolExecutor(registry)
        result = await executor.execute(ERP_CALL)
        assert result.success is True

    async def test_unauthenticated_actor_is_treated_as_the_most_restrictive_role(self, registry):
        executor = ToolExecutor(registry)
        result = await executor.execute(ERP_CALL, actor=Actor.anonymous("req_x"))
        assert result.success is False
        assert result.error_code == "PERMISSION_DENIED"

    async def test_unknown_tool_stays_unknown_for_every_role(self, registry):
        executor = ToolExecutor(registry)
        result = await executor.execute(
            ToolCall(id="c", name="nope", arguments={}), actor=actor_for(DEMO_ADMIN)
        )
        assert result.error_code == "UNKNOWN_TOOL"
        assert executor.is_allowed("nope", actor_for(DEMO_ADMIN)) is False


@pytest.mark.asyncio
class TestObservabilityOfToolCalls:
    async def test_denied_call_is_audited_and_counted(self, registry):
        audit = memory_audit()
        counters = Metrics()
        executor = ToolExecutor(registry, audit=audit, metrics=counters)
        await executor.execute(ERP_CALL, actor=actor_for(DEMO_OPERATOR))
        events = [event for event in audit.records if event.tool_name == "erp_purchase_analysis"]
        assert events and events[-1].status == "denied"
        assert events[-1].request_id == "req_executor_test"
        assert events[-1].user_id == DEMO_OPERATOR.user_id
        assert counters.snapshot()["tool_call_count"] == 1
        assert counters.snapshot()["permission_denied_count"] == 1

    async def test_successful_call_is_audited_with_params_only(self, registry):
        audit = memory_audit()
        executor = ToolExecutor(registry, audit=audit)
        await executor.execute(ERP_CALL, actor=actor_for(DEMO_MANAGER))
        event = [item for item in audit.records if item.tool_name == "erp_purchase_analysis"][-1]
        assert event.status == "success"
        assert event.input_summary["operation"] == "supplier_summary"
        assert set(event.input_summary) <= {
            "operation",
            "days",
            "limit",
            "material",
            "area",
            "status",
            "mode",
            "error_code",
        }

    async def test_no_actor_means_no_audit_row(self, registry):
        audit = memory_audit()
        executor = ToolExecutor(registry, audit=audit)
        await executor.execute(ERP_CALL, actor=None)
        assert audit.records == ()

    async def test_invalid_arguments_are_reported_structurally(self, registry):
        executor = ToolExecutor(registry)
        result = await executor.execute(
            ToolCall(
                id="c",
                name="erp_purchase_analysis",
                arguments={"operation": "supplier_summary", "days": 999},
            ),
            actor=actor_for(DEMO_ADMIN),
        )
        assert result.success is False
        assert result.error_code == "INVALID_ARGUMENTS"
