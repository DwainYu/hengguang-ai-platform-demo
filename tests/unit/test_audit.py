"""Unit tests for the audit trail: record shape, privacy rules, pagination."""

from __future__ import annotations

import json
from collections import deque

import pytest
from sqlalchemy import text

from app.auth.auth import DEMO_ADMIN, DEMO_MANAGER, DEMO_OPERATOR
from app.config import get_settings, update_settings
from app.db.database import Database
from app.observability.audit import (
    Actor,
    AuditAction,
    AuditEvent,
    AuditLog,
    AuditStatus,
    sanitize_summary,
)


@pytest.fixture
def audit(seeded_database: Database) -> AuditLog:
    recorder = AuditLog(lambda: seeded_database)
    recorder.clear()
    return recorder


def actor(request_id: str = "req_test_1", user=DEMO_ADMIN) -> Actor:
    return Actor.from_user(user, request_id)


class TestRecording:
    def test_api_operation_is_written_to_the_database(self, audit, seeded_database):
        audit.record_api(
            actor(),
            action=AuditAction.AGENT_RUN,
            status=AuditStatus.SUCCESS,
            endpoint="POST /api/agent/run",
            model_name="mock-model",
            mode="agent",
            input_summary={"steps": 2, "tool_calls": 1},
            latency_ms=15,
        )
        rows = seeded_database.query("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 1")
        assert rows[0]["user_id"] == DEMO_ADMIN.user_id
        assert rows[0]["request_id"] == "req_test_1"
        assert rows[0]["action"] == "agent.run"
        assert rows[0]["endpoint"] == "POST /api/agent/run"
        assert rows[0]["model_name"] == "mock-model"
        assert rows[0]["mode"] == "agent"
        assert rows[0]["status"] == "success"
        assert rows[0]["latency_ms"] == 15
        assert rows[0]["created_at"]

    def test_tool_call_is_a_compact_row(self, audit, seeded_database):
        audit.record_tool_call(
            actor("req_test_2"),
            tool_name="erp_purchase_analysis",
            status=AuditStatus.SUCCESS,
            model_name="mock-model",
            input_summary={"operation": "purchase_price_trend", "days": 30, "limit": 10},
            latency_ms=7,
        )
        row = seeded_database.query(
            "SELECT * FROM audit_logs WHERE tool_name IS NOT NULL ORDER BY id DESC LIMIT 1"
        )[0]
        assert row["action"] == AuditAction.TOOL_CALL
        assert row["tool_name"] == "erp_purchase_analysis"
        summary = json.loads(row["input_summary"])
        assert summary == {"operation": "purchase_price_trend", "days": 30, "limit": 10}
        assert len(row["input_summary"]) < 200

    def test_anonymous_events_stay_in_memory_only(self, audit, seeded_database):
        """SPEC keeps ``audit_logs.user_id`` NOT NULL, so 401 attempts are not rows."""

        before = seeded_database.table_row_count("audit_logs")
        event = audit.record(
            AuditEvent.build(None, action=AuditAction.MODELS_LIST, status=AuditStatus.SUCCESS)
        )
        assert event.user_id is None
        assert event in audit.records
        assert seeded_database.table_row_count("audit_logs") == before

    def test_unauthenticated_status_is_recordable(self, audit):
        event = audit.record_api(
            None,
            action=AuditAction.AUDIT_READ,
            status=AuditStatus.UNAUTHENTICATED,
            endpoint="GET /api/audit",
        )
        assert event.status == "unauthenticated"


class TestPrivacy:
    def test_secrets_are_never_persisted(self, audit, seeded_database):
        audit.record_api(
            actor("req_privacy"),
            action=AuditAction.CHAT_COMPLETE,
            status=AuditStatus.SUCCESS,
            input_summary={
                "authorization": "Bearer demo-admin-token",
                "api_key": "sk-secret-value",
                "token": "demo-manager-token",
                "prompt": "完整的用户提示词内容",
                "messages": [{"role": "user", "content": "机密全文"}],
                "content": "整段文档正文",
                "chars": 12,
                "mode": "auto",
            },
        )
        row = seeded_database.query(
            "SELECT input_summary FROM audit_logs WHERE request_id = 'req_privacy'"
        )[0]
        stored = row["input_summary"]
        for forbidden in (
            "demo-admin-token",
            "sk-secret-value",
            "demo-manager-token",
            "机密全文",
            "完整的用户提示词",
        ):
            assert forbidden not in stored
        assert json.loads(stored) == {"chars": 12, "mode": "auto"}

    def test_long_values_are_truncated(self):
        summary = sanitize_summary({"document_id": "x" * 500})
        assert len(summary["document_id"]) <= 160

    def test_nested_structures_are_reduced_to_sizes(self):
        summary = sanitize_summary({"results": [1, 2, 3], "params": {"a": 1}})
        assert summary == {"results": 3, "params": 1}

    def test_key_count_is_bounded(self):
        summary = sanitize_summary({f"key_{index}": index for index in range(50)})
        assert len(summary) <= 12


class TestReading:
    def test_pagination_shape(self, audit, seeded_database):
        for index in range(12):
            audit.record_api(
                actor(f"req_page_{index}", DEMO_MANAGER),
                action=AuditAction.KNOWLEDGE_SEARCH,
                status=AuditStatus.SUCCESS,
            )
        page = audit.list(page=2, page_size=5)
        assert set(page) >= {"items", "page", "page_size", "total"}
        assert page["page"] == 2 and page["page_size"] == 5
        assert len(page["items"]) == 5
        assert page["total"] >= 12

    def test_newest_first(self, audit):
        audit.record_api(
            actor("req_old"), action=AuditAction.MODELS_LIST, status=AuditStatus.SUCCESS
        )
        audit.record_api(
            actor("req_new"), action=AuditAction.MODELS_LIST, status=AuditStatus.SUCCESS
        )
        items = audit.list(page_size=2)["items"]
        assert items[0]["request_id"] == "req_new"

    def test_filter_by_tool_and_status(self, audit):
        audit.record_tool_call(
            actor("req_f1"), tool_name="safety_incident_analysis", status=AuditStatus.SUCCESS
        )
        audit.record_tool_call(
            actor("req_f2"), tool_name="erp_purchase_analysis", status=AuditStatus.DENIED
        )
        # The session database is shared with the integration suites, so filter on
        # the dimensions under test and assert membership rather than equality.
        by_tool = audit.list(tool="safety_incident_analysis", page_size=100)
        assert {item["tool"] for item in by_tool["items"]} == {"safety_incident_analysis"}
        assert "req_f1" in {item["request_id"] for item in by_tool["items"]}
        denied = audit.list(tool="erp_purchase_analysis", status="denied", page_size=100)
        assert {item["status"] for item in denied["items"]} == {"denied"}
        assert "req_f2" in {item["request_id"] for item in denied["items"]}
        assert audit.list(tool="not_a_tool")["total"] == 0

    def test_filter_by_request_id(self, audit):
        audit.record_api(
            actor("req_trace"), action=AuditAction.AGENT_RUN, status=AuditStatus.SUCCESS
        )
        audit.record_tool_call(
            actor("req_trace"), tool_name="knowledge_search", status=AuditStatus.SUCCESS
        )
        page = audit.list(request_id="req_trace")
        assert page["total"] == 2
        assert {item["tool"] for item in page["items"]} == {None, "knowledge_search"}

    def test_page_parameters_are_clamped(self, audit):
        audit.record_api(
            actor("req_clamp"), action=AuditAction.MODELS_LIST, status=AuditStatus.SUCCESS
        )
        page = audit.list(page=0, page_size=5000)
        assert page["page"] == 1
        assert page["page_size"] == 100

    def test_items_expose_display_fields(self, audit):
        audit.record_api(
            actor("req_shape", DEMO_OPERATOR),
            action=AuditAction.AGENT_RUN,
            status=AuditStatus.SUCCESS,
        )
        item = audit.list(request_id="req_shape")["items"][0]
        assert item["username"] == "operator_demo"
        assert item["role"] == "operator"
        assert item["operation"] == "agent.run"
        assert item["request_id"] == "req_shape"

    def test_count_returns_database_rows(self, audit):
        audit.record_api(
            actor("req_count"), action=AuditAction.AUDIT_READ, status=AuditStatus.SUCCESS
        )
        assert audit.count() >= 1


class TestMemoryBound:
    """Regression for Fix #5: the in-memory trail is a bounded deque.

    ``clear()`` used to rebind ``_records`` to a plain list, which silently
    removed the cap for the rest of the process' lifetime. These tests pin the
    bound, so only a real deque that keeps its ``maxlen`` can pass.
    """

    def test_clear_keeps_the_deque_and_its_maxlen(self, seeded_database):
        original = get_settings().audit_memory_max_records
        update_settings(audit_memory_max_records=3)
        try:
            recorder = AuditLog(lambda: seeded_database)
            for index in range(2):
                recorder.record_api(
                    actor(f"req_pre_{index}"),
                    action=AuditAction.CHAT_COMPLETE,
                    status=AuditStatus.SUCCESS,
                )
            assert len(recorder.records) == 2

            recorder.clear()

            assert recorder.records == ()
            # the cap survives the reset: still the same bounded deque
            assert isinstance(recorder._records, deque)  # noqa: SLF001
            assert recorder._records.maxlen == 3  # noqa: SLF001

            for index in range(5):
                recorder.record_api(
                    actor(f"req_post_{index}"),
                    action=AuditAction.CHAT_COMPLETE,
                    status=AuditStatus.SUCCESS,
                )
            assert [event.request_id for event in recorder.records] == [
                "req_post_2",
                "req_post_3",
                "req_post_4",
            ]
        finally:
            update_settings(audit_memory_max_records=original)

    def test_clear_does_not_touch_persisted_rows(self, audit):
        audit.record_api(
            actor("req_persisted"),
            action=AuditAction.CHAT_COMPLETE,
            status=AuditStatus.SUCCESS,
        )
        assert audit.list(request_id="req_persisted")["total"] == 1
        audit.clear()
        assert audit.records == ()
        assert audit.list(request_id="req_persisted")["total"] == 1


class TestResilience:
    def test_write_failure_never_raises(self, tmp_path):
        broken = Database(url=f"sqlite:///{tmp_path / 'broken.db'}")
        broken.initialize()
        with broken.session() as session:
            session.execute(text("DROP TABLE audit_logs"))
        audit = AuditLog(lambda: broken)
        event = audit.record_api(actor(), action=AuditAction.AGENT_RUN, status=AuditStatus.SUCCESS)
        assert event.status == "success"
        assert audit.last_error is not None

    def test_uninitialised_database_skips_the_write(self):
        audit = AuditLog(lambda: Database(url="sqlite:///:memory:"))
        audit.record_api(actor(), action=AuditAction.AGENT_RUN, status=AuditStatus.SUCCESS)
        assert audit.records  # still visible in memory, nothing crashed

    def test_actor_accepts_a_user_directly(self, audit):
        event = audit.record_api(
            DEMO_MANAGER, action=AuditAction.CHAT_COMPLETE, status=AuditStatus.SUCCESS
        )
        assert event.username == "manager_demo"
        assert event.user_id == DEMO_MANAGER.user_id


def test_429_maps_to_too_many_requests():
    """429 status should map to TOO_MANY_REQUESTS, not VALIDATION_ERROR."""
    from app.api.errors import ERROR_TOO_MANY_REQUESTS, error_code_for_status

    assert error_code_for_status(429) == ERROR_TOO_MANY_REQUESTS
    assert error_code_for_status(429) != "VALIDATION_ERROR"
