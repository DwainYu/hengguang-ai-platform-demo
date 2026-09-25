"""Structured application logging with per-request correlation (Day 4).

Deliberately minimal: one JSON line per logged event on stdout, a ``request_id``
bound by :mod:`app.observability.middleware` for the lifetime of a request, and no
external stack (no ELK / OpenTelemetry — SPEC Day 4 explicitly does not require it).
"""

from __future__ import annotations

import contextvars
import datetime as dt
import json
import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.config import get_settings

REQUEST_ID_HEADER = "X-Request-ID"

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "hengguang_request_id", default=""
)

#: Structured fields copied into the JSON line when present on a record.
FIELD_KEYS = (
    "event",
    "endpoint",
    "operation",
    "method",
    "status",
    "status_code",
    "latency_ms",
    "tool",
    "model",
    "mode",
    "steps",
    "user",
    "role",
    "error_code",
    "provider",
    "rows",
    "documents",
    "chunks",
    "db_path",
    "as_of",
    "count",
    "source",
    "path",
)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


def current_request_id() -> str:
    """request_id bound for the current request (empty string when none)."""

    return _request_id.get()


@contextmanager
def request_id_scope(value: str) -> Iterator[str]:
    token = _request_id.set(value)
    try:
        yield value
    finally:
        _request_id.reset(token)


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message + safe fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if current_request_id():
            payload["request_id"] = current_request_id()
        for key in FIELD_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        for key, value in record.__dict__.items():
            if key not in _RESERVED and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable fallback used when ``LOG_JSON=false``."""

    def format(self, record: logging.LogRecord) -> str:
        base = (
            f"{local_timestamp(record)} [{record.levelname.lower()}] "
            f"{record.name}: {record.getMessage()}"
        )
        fields = {
            key: getattr(record, key)
            for key in FIELD_KEYS
            if getattr(record, key, None) is not None
        }
        if current_request_id():
            fields.setdefault("request_id", current_request_id())
        if fields:
            base += " | " + " ".join(f"{key}={value}" for key, value in fields.items())
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def local_timestamp(record: logging.LogRecord) -> str:
    """Local wall-clock timestamp for the text formatter."""
    return dt.datetime.fromtimestamp(record.created).isoformat(timespec="milliseconds")


def configure_logging(level: str | None = None, *, json_logs: bool | None = None) -> None:
    """Install the structured handler on the root logger (idempotent)."""

    settings = get_settings()
    resolved_level = (level or settings.log_level or "INFO").upper()
    use_json = settings.log_json if json_logs is None else json_logs

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if use_json else TextFormatter())
    handler.set_name("hengguang-structured")

    root = logging.getLogger()
    for existing in list(root.handlers):
        if getattr(existing, "name", "") == handler.get_name():
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(resolved_level)

    # uvicorn writes its own access lines; the request middleware already emits a
    # structured record per request, so keep the duplicate stream quiet.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name if name.startswith("app") else f"app.{name}")


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    **fields: Any,
) -> None:
    """Emit one structured log record (extra fields go into the JSON line)."""

    logger.log(level, message, extra=dict(fields))


__all__ = [
    "FIELD_KEYS",
    "REQUEST_ID_HEADER",
    "JsonFormatter",
    "configure_logging",
    "current_request_id",
    "get_logger",
    "log_event",
    "request_id_scope",
]
