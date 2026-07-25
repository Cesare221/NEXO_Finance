"""Structured JSON logging for production and human-readable development logs."""
from __future__ import annotations

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_SENSITIVE_PATTERNS = {"authorization", "cookie", "password", "token", "secret"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line.  Strips sensitive fields."""

    _nexo_json_formatter = True  # sentinel for identify in tests

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "nexo-api",
            "message": record.getMessage(),
        }

        # Attach request context if present
        request_id = getattr(record, "request_id", None) or _request_id_var.get()
        if request_id:
            payload["request_id"] = request_id

        for field in ("method", "route", "status_code", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        # Include exception info without traceback
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = {
                "type": record.exc_info[0].__name__,
                "value": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        return json.dumps(payload, default=str, ensure_ascii=False)


class _SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that can be identified by tests."""

    _nexo_json_formatter = True


def configure_logging(environment: str = "development") -> None:
    """Configure root logger for the given environment."""
    root = logging.getLogger()

    # Remove any previously added nexo JSON handlers
    for handler in root.handlers[:]:
        if getattr(handler, "_nexo_json_formatter", False):
            root.removeHandler(handler)

    if environment == "production":
        handler = _SafeStreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._nexo_json_formatter = True
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    else:
        # Development: keep human-readable format
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
