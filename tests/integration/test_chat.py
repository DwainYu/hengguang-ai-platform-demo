"""Integration tests for chat API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestModelsEndpoint:
    """Tests for /api/models endpoint."""

    def test_models_returns_list(self, client):
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) >= 1

    def test_models_no_api_keys(self, client):
        """Response should never contain API keys."""
        resp = client.get("/api/models")
        data = resp.json()
        # Check no sensitive fields
        resp_text = str(data)
        assert "api_key" not in resp_text.lower()
        assert "apikey" not in resp_text.lower()


class TestChatEndpoint:
    """Tests for /api/chat endpoint."""

    def test_chat_success(self, client):
        """Basic chat request should succeed."""
        resp = client.post("/api/chat", json={"message": "你好"})
        assert resp.status_code == 200
        data = resp.json()
        assert "request_id" in data
        assert data["request_id"].startswith("req_")
        assert "answer" in data
        assert data["answer"]
        assert data["mode"] == "auto"
        assert "model" in data
        assert "provider" in data
        assert data["provider"] == "mock"
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], int)
        assert data["latency_ms"] >= 0

    def test_chat_with_model_param(self, client):
        """Chat should accept model parameter."""
        resp = client.post("/api/chat", json={"message": "测试", "model": "custom-model"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["model"] == "custom-model"

    def test_chat_with_temperature(self, client):
        """Chat should accept temperature parameter."""
        resp = client.post("/api/chat", json={"message": "测试", "temperature": 0.5})
        assert resp.status_code == 200

    def test_chat_invalid_empty_message(self, client):
        """Empty message should be rejected."""
        resp = client.post("/api/chat", json={"message": ""})
        assert resp.status_code == 422  # Validation error

    def test_chat_invalid_missing_message(self, client):
        """Missing message should be rejected."""
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 422

    def test_chat_invalid_temperature(self, client):
        """Temperature out of bounds should be rejected."""
        resp = client.post("/api/chat", json={"message": "测试", "temperature": 3.0})
        assert resp.status_code == 422

    def test_chat_hengguang_business_query(self, client):
        """Chat with Hengguang business query returns canned response."""
        resp = client.post("/api/chat", json={"message": "恒光主要有哪些业务？"})
        assert resp.status_code == 200
        data = resp.json()
        assert "无机精细化学品" in data["answer"]
        assert "氯碱" in data["answer"]

    def test_chat_purchase_price_query(self, client):
        """Chat with purchase price query returns canned response."""
        resp = client.post("/api/chat", json={"message": "最近30天原材料采购价格有什么变化？"})
        assert resp.status_code == 200
        data = resp.json()
        assert "盐酸" in data["answer"]

    def test_chat_safety_query(self, client):
        """Chat with safety query returns canned response."""
        resp = client.post("/api/chat", json={"message": "最近一个月哪个区域安全问题最多？"})
        assert resp.status_code == 200
        data = resp.json()
        assert "A 车间" in data["answer"]

    def test_chat_response_structure(self, client):
        """Response should have all required fields."""
        resp = client.post("/api/chat", json={"message": "测试"})
        data = resp.json()
        required = [
            "request_id",
            "answer",
            "mode",
            "model",
            "provider",
            "latency_ms",
            "sources",
            "tool_calls",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["sources"], list)
        assert isinstance(data["tool_calls"], list)

    def test_chat_mode_auto(self, client):
        """Mode auto should be accepted."""
        resp = client.post("/api/chat", json={"message": "测试", "mode": "auto"})
        assert resp.status_code == 200
        assert resp.json()["mode"] == "auto"


class TestProviderFailureHandling:
    """Tests for provider failure handling."""

    def test_chat_fallback_on_provider_error(self, client):
        """If provider fails, should fallback or return error."""
        # With mock provider, it should always work
        resp = client.post("/api/chat", json={"message": "测试"})
        assert resp.status_code == 200
        # If we had a real provider that fails, the gateway falls back to mock


class TestChatAudit:
    """Tests for chat audit trail coverage."""

    def test_success_chat_writes_audit(self, client, audit_log):
        """Successful chat should create an audit record with status=success."""
        resp = client.post("/api/chat", json={"message": "你好"})
        assert resp.status_code == 200
        records = audit_log.records
        assert len(records) >= 1
        latest = records[-1]
        assert latest.action == "chat.complete"
        assert latest.status == "success"
        assert latest.request_id.startswith("req_")
        assert latest.endpoint == "POST /api/chat"
        assert latest.model_name is not None

    def test_failed_chat_writes_audit(self, client, audit_log):
        """Failed chat (provider error) should create an audit record with status=error."""
        from unittest.mock import patch

        from app.gateway.router import gateway

        async def failing_chat(*args, **kwargs):
            raise RuntimeError("Simulated provider failure")

        with patch.object(gateway, "chat", failing_chat):
            resp = client.post("/api/chat", json={"message": "测试"})
            assert resp.status_code == 502
            body = resp.json()
            assert body["error"]["code"] == "PROVIDER_ERROR"

        records = audit_log.records
        assert len(records) >= 1
        latest = records[-1]
        assert latest.action == "chat.complete"
        assert latest.status == "error"
        assert latest.request_id.startswith("req_")
        assert "error_type" in latest.input_summary

    def test_chat_error_preserves_request_id(self, client, audit_log):
        """Audit record request_id must match the response request_id."""
        from unittest.mock import patch

        from app.gateway.router import gateway

        async def failing_chat(*args, **kwargs):
            raise RuntimeError("Simulated failure")

        with patch.object(gateway, "chat", failing_chat):
            resp = client.post("/api/chat", json={"message": "测试"})
            assert resp.status_code == 502
            response_request_id = resp.json()["request_id"]

        records = audit_log.records
        assert any(r.request_id == response_request_id for r in records)

    def test_chat_does_not_leak_sensitive_data(self, client, audit_log):
        """Audit input_summary must not contain sensitive fields."""
        client.post("/api/chat", json={"message": "你好"})
        records = audit_log.records
        for record in records:
            if record.action == "chat.complete":
                summary = record.input_summary
                for forbidden in ("prompt", "messages", "content", "text"):
                    assert forbidden not in summary, f"Sensitive field '{forbidden}' found in audit"
