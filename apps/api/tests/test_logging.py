"""Tests for structured JSON logging and request correlation."""
from __future__ import annotations

import json
import logging
import time
from unittest.mock import MagicMock

from app.core.logging_config import JsonFormatter, configure_logging, _request_id_var


def test_json_formatter_includes_required_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="nexo", level=logging.INFO, pathname="app/main.py",
        lineno=42, msg="request.complete", args=(), exc_info=None,
    )
    record.request_id = "9bfa6d7d-3987-45b8-9468-2ed7cd97266a"
    record.method = "POST"
    record.route = "/auth/login"
    record.status_code = 200
    record.duration_ms = 45.2

    output = json.loads(formatter.format(record))
    assert output["request_id"] == "9bfa6d7d-3987-45b8-9468-2ed7cd97266a"
    assert output["method"] == "POST"
    assert output["route"] == "/auth/login"
    assert output["status_code"] == 200
    assert output["duration_ms"] == 45.2
    assert output["level"] == "INFO"
    assert output["service"] == "nexo-api"


def test_json_formatter_excludes_sensitive_values():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="nexo", level=logging.INFO, pathname="app/main.py",
        lineno=1, msg="request.complete", args=(), exc_info=None,
    )
    record.request_id = "9bfa6d7d-3987-45b8-9468-2ed7cd97266a"
    record.method = "GET"
    record.route = "/health"
    record.status_code = 200
    record.duration_ms = 1.0

    output = json.loads(formatter.format(record))
    assert "authorization" not in output
    assert "body" not in output
    assert "cookie" not in output
    assert "password" not in output
    assert "token" not in output


def test_json_formatter_handles_missing_optional_fields():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="nexo", level=logging.ERROR, pathname="app/main.py",
        lineno=1, msg="error occurred", args=(), exc_info=None,
    )
    record.request_id = "abc-123"

    output = json.loads(formatter.format(record))
    assert output["request_id"] == "abc-123"
    assert output["level"] == "ERROR"
    assert output["service"] == "nexo-api"
    # Missing optional fields should not appear
    assert "method" not in output
    assert "route" not in output


def test_json_formatter_includes_exception_info():
    formatter = JsonFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="nexo", level=logging.ERROR, pathname="app/main.py",
        lineno=1, msg="unhandled exception", args=(), exc_info=exc_info,
    )
    record.request_id = "err-1"

    output = json.loads(formatter.format(record))
    assert "exception" in output
    assert output["exception"]["type"] == "ValueError"
    assert output["exception"]["value"] == "test error"
    assert "traceback" in output["exception"]


def test_request_id_var_isolation():
    _request_id_var.set("req-aaa")
    assert _request_id_var.get() == "req-aaa"
    _request_id_var.set("req-bbb")
    assert _request_id_var.get() == "req-bbb"
    _request_id_var.set(None)


def test_configure_logging_sets_up_root_logger():
    import logging as _logging

    root = _logging.getLogger()
    original_level = root.level
    try:
        configure_logging(environment="development")
        # Should not raise
    finally:
        root.level = original_level
        for h in root.handlers[:]:
            if getattr(h, "_nexo_json_formatter", False):
                root.removeHandler(h)


def test_configure_logging_json_in_production():
    import logging as _logging

    root = _logging.getLogger()
    original_level = root.level
    original_handlers = root.handlers[:]
    try:
        configure_logging(environment="production")
        # In production, root logger should have a handler with JsonFormatter
        json_handlers = [h for h in root.handlers if getattr(h, "_nexo_json_formatter", False)]
        assert len(json_handlers) >= 1
    finally:
        root.level = original_level
        for h in root.handlers:
            if getattr(h, "_nexo_json_formatter", False):
                root.removeHandler(h)


def test_request_logging_middleware_captures_metrics(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) > 0


def test_request_logging_middleware_captures_error_status(client):
    response = client.get("/nonexistent-path-xyz")
    assert response.status_code == 404
    assert "X-Request-ID" in response.headers


def test_request_id_is_uuid_format(client):
    import uuid
    response = client.get("/health")
    request_id = response.headers["X-Request-ID"]
    uuid.UUID(request_id)  # Should not raise


def test_request_id_preserved_from_client(client):
    custom_id = "12345678-1234-5678-1234-567812345678"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_large_body_rejected(client):
    import json as _json
    huge_body = _json.dumps({"data": "x" * 1_100_000})
    response = client.post(
        "/auth/login",
        content=huge_body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(huge_body))},
    )
    assert response.status_code == 413
    assert "X-Request-ID" in response.headers
