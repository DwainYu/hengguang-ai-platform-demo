"""Unified structured errors (Day 4 §十五).

Every failure that leaves the platform uses one envelope::

    {
      "detail": "人类可读信息",
      "request_id": "req_...",
      "error": {"code": "PERMISSION_DENIED", "message": "...", "details": {...}}
    }

``detail`` is kept because FastAPI clients (and the Day-1/2 tests) read it, while
``error.code`` is what the Day-5 dashboard should branch on. Tracebacks, provider
payloads, connection strings and credentials are never echoed to the client — the
full exception goes to the structured log with its request id instead.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.observability.logging import current_request_id

logger = logging.getLogger("app.api.errors")

ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_UNAUTHENTICATED = "UNAUTHENTICATED"
ERROR_PERMISSION_DENIED = "PERMISSION_DENIED"
ERROR_CONFLICT = "CONFLICT"
ERROR_TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
ERROR_PROVIDER = "PROVIDER_ERROR"
ERROR_STORAGE = "STORAGE_ERROR"
ERROR_DATABASE = "DATABASE_ERROR"
ERROR_INTERNAL = "INTERNAL_ERROR"

_CODE_BY_STATUS: dict[int, str] = {
    400: ERROR_VALIDATION,
    401: ERROR_UNAUTHENTICATED,
    403: ERROR_PERMISSION_DENIED,
    404: ERROR_NOT_FOUND,
    409: ERROR_CONFLICT,
    422: ERROR_VALIDATION,
    429: ERROR_TOO_MANY_REQUESTS,
    502: ERROR_PROVIDER,
    503: ERROR_STORAGE,
}


class PlatformError(Exception):
    """Base class for controlled, structured API failures."""

    status_code: int = 500
    code: str = ERROR_INTERNAL

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.status_code = int(status_code or self.status_code)
        self.details = details or {}
        self.headers = headers or {}


class AuthenticationError(PlatformError):
    status_code = 401
    code = ERROR_UNAUTHENTICATED


class PermissionDeniedError(PlatformError):
    status_code = 403
    code = ERROR_PERMISSION_DENIED


class NotFoundError(PlatformError):
    status_code = 404
    code = ERROR_NOT_FOUND


class ConflictError(PlatformError):
    status_code = 409
    code = ERROR_CONFLICT


class ProviderError(PlatformError):
    status_code = 502
    code = ERROR_PROVIDER


class StorageError(PlatformError):
    status_code = 503
    code = ERROR_STORAGE


class DatabaseError(PlatformError):
    status_code = 503
    code = ERROR_DATABASE


def error_code_for_status(status_code: int) -> str:
    """Default machine code for a plain ``HTTPException`` status."""

    return _CODE_BY_STATUS.get(status_code, ERROR_INTERNAL)


def error_body(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str = "",
) -> dict[str, Any]:
    """The single error envelope used by all handlers below."""

    if not request_id:
        request_id = current_request_id()
    return {
        "detail": message,
        "request_id": request_id,
        "error": {"code": code, "message": message, "details": details or {}},
    }


def error_response(
    status_code: int,
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(code=code, message=message, details=details),
        headers=headers or None,
    )


def _remember(request: Request, code: str, status_code: int) -> None:
    """Expose the machine code to the metrics middleware through request state."""

    state = getattr(request, "state", None)
    if state is not None:
        state.error_code = code
        state.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Install handlers for PlatformError, HTTPException, validation and the rest."""

    @app.exception_handler(PlatformError)
    async def handle_platform_error(request: Request, exc: PlatformError) -> JSONResponse:
        _remember(request, exc.code, exc.status_code)
        if exc.status_code >= 500:
            logger.error(
                "platform error",
                extra={
                    "event": "error.platform",
                    "error_code": exc.code,
                    "endpoint": request.url.path,
                },
            )
        return error_response(
            exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            headers=exc.headers,
        )

    # Both FastAPI's and Starlette's HTTPException: unrouted paths raise the
    # Starlette one, and the handler map is keyed by exact class.
    @app.exception_handler(StarletteHTTPException)
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        code = error_code_for_status(exc.status_code)
        _remember(request, code, exc.status_code)
        message = exc.detail if isinstance(exc.detail, str) else "请求无法处理"
        return error_response(
            exc.status_code,
            code=code,
            message=message,
            headers=dict(exc.headers or {}),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        _remember(request, ERROR_VALIDATION, 422)
        return error_response(
            422,
            code=ERROR_VALIDATION,
            message="请求参数校验失败",
            details={"errors": _json_safe(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        _remember(request, ERROR_INTERNAL, 500)
        logger.exception(
            "unhandled error",
            extra={
                "event": "error.unhandled",
                "endpoint": request.url.path,
                "error_type": type(exc).__name__,
            },
        )
        return error_response(
            500,
            code=ERROR_INTERNAL,
            message="服务内部错误，请使用 request_id 查询审计日志",
        )


def _json_safe(value: Any) -> Any:
    """``RequestValidationError.errors()`` can carry exceptions/bytes; make it safe."""

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Exception):
        return type(value).__name__
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


__all__ = [
    "ERROR_CONFLICT",
    "ERROR_DATABASE",
    "ERROR_INTERNAL",
    "ERROR_NOT_FOUND",
    "ERROR_PERMISSION_DENIED",
    "ERROR_PROVIDER",
    "ERROR_STORAGE",
    "ERROR_TOO_MANY_REQUESTS",
    "ERROR_UNAUTHENTICATED",
    "ERROR_VALIDATION",
    "AuthenticationError",
    "ConflictError",
    "DatabaseError",
    "NotFoundError",
    "PermissionDeniedError",
    "PlatformError",
    "ProviderError",
    "StorageError",
    "error_body",
    "error_code_for_status",
    "error_response",
    "register_exception_handlers",
]
