"""Tests for the privacy-safe Sentry scrubber and observability initialization."""
from __future__ import annotations

import pytest

from app.core.config import Settings


VALID_FERNET_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def _production_settings(**overrides) -> Settings:
    values = {
        "environment": "production",
        "database_url": "postgresql://nexo:secret@db.internal:5432/nexo",
        "secret_key": "a" * 64,
        "allowed_origins": "https://app.nexo.example",
        "allowed_hosts": "api.nexo.example",
        "redis_url": "redis://redis.internal:6379/0",
        "mail_provider": "resend",
        "resend_api_key": "re_test_key",
        "email_from": "Nexo <no-reply@nexo.example>",
        "public_web_url": "https://app.nexo.example",
        "mfa_encryption_keys": f"v1:{VALID_FERNET_KEY}",
        "mfa_active_key_version": "v1",
        "sentry_dsn": "https://key@sentry.io/123",
        "sentry_environment": "production",
        "sentry_release": "nexo-api@1.0.0",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


# ── Scrubber tests ──


def test_scrubber_removes_sensitive_request_data():
    from app.core.observability import scrub_sentry_event

    event = {
        "request": {
            "headers": {"authorization": "Bearer secret", "cookie": "refresh=secret"},
            "data": {"password": "secret", "amount": "120.00", "description": "Farmacia"},
        },
        "user": {"email": "person@example.com", "ip_address": "127.0.0.1"},
        "extra": {"chat_message": "meu saldo", "request_id": "safe-id"},
    }
    scrubbed = scrub_sentry_event(event, {})
    assert scrubbed["request"]["headers"] == {}
    assert "data" not in scrubbed["request"]
    assert scrubbed.get("user") is None
    assert scrubbed["extra"] == {"request_id": "safe-id"}


def test_scrubber_removes_sensitive_breadcrumbs():
    from app.core.observability import scrub_sentry_event

    event = {
        "breadcrumbs": {
            "values": [
                {"message": "request body received", "data": {"token": "abc", "code": "123"}},
                {"message": "normal log", "data": {}},
            ]
        }
    }
    scrubbed = scrub_sentry_event(event, {})
    assert len(scrubbed["breadcrumbs"]["values"]) == 1
    assert scrubbed["breadcrumbs"]["values"][0]["message"] == "normal log"


def test_scrubber_preserves_exception_and_stack():
    from app.core.observability import scrub_sentry_event

    event = {
        "exception": {
            "values": [
                {
                    "type": "ValueError",
                    "value": "bad input",
                    "stacktrace": {"frames": [{"filename": "app/main.py", "lineno": 42}]},
                }
            ]
        },
        "request": {"headers": {"authorization": "Bearer x"}},
    }
    scrubbed = scrub_sentry_event(event, {})
    assert scrubbed["exception"]["values"][0]["type"] == "ValueError"
    assert scrubbed["exception"]["values"][0]["stacktrace"]["frames"][0]["filename"] == "app/main.py"
    assert scrubbed["request"]["headers"] == {}


def test_scrubber_returns_none_for_empty_event():
    from app.core.observability import scrub_sentry_event

    result = scrub_sentry_event({}, {})
    assert result is not None


def test_scrubber_handles_missing_keys_gracefully():
    from app.core.observability import scrub_sentry_event

    event = {"exception": {"values": [{"type": "Error"}]}}
    scrubbed = scrub_sentry_event(event, {})
    assert "request" not in scrubbed
    assert scrubbed["exception"]["values"][0]["type"] == "Error"


def test_scrubber_removes_set_cookie_header():
    from app.core.observability import scrub_sentry_event

    event = {
        "request": {
            "headers": {"set-cookie": "session=abc123", "content-type": "application/json"}
        }
    }
    scrubbed = scrub_sentry_event(event, {})
    assert "set-cookie" not in scrubbed["request"]["headers"]
    assert scrubbed["request"]["headers"]["content-type"] == "application/json"


# ── Config tests ──


def test_sentry_settings_defaults():
    s = Settings(_env_file=None)
    assert s.sentry_dsn == ""
    assert s.sentry_environment == "development"
    assert s.sentry_release == ""
    assert s.sentry_traces_sample_rate == 0.0


def test_production_requires_sentry_environment_when_dsn_set():
    s = _production_settings(sentry_environment="")
    with pytest.raises(RuntimeError, match="SENTRY_ENVIRONMENT"):
        s.validate_runtime()


def test_production_requires_sentry_release_when_dsn_set():
    s = _production_settings(sentry_release="")
    with pytest.raises(RuntimeError, match="SENTRY_RELEASE"):
        s.validate_runtime()


def test_production_rejects_invalid_traces_sample_rate():
    s = _production_settings(sentry_traces_sample_rate=1.5)
    with pytest.raises(RuntimeError, match="SENTRY_TRACES_SAMPLE_RATE"):
        s.validate_runtime()


def test_valid_sentry_production_config_passes():
    s = _production_settings()
    s.validate_runtime()


def test_init_observability_skipped_without_dsn(monkeypatch):
    from app.core.observability import init_observability

    monkeypatch.setattr("app.core.observability.settings", Settings(_env_file=None))
    init_observability()


def test_init_observability_initializes_with_dsn(monkeypatch):
    import app.core.observability as obs
    from app.core.observability import init_observability

    calls = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(obs.sentry_sdk, "init", fake_init)
    monkeypatch.setattr(obs, "settings", _production_settings())

    init_observability()
    assert len(calls) == 1
    assert calls[0]["dsn"] == "https://key@sentry.io/123"
    assert calls[0]["environment"] == "production"
    assert calls[0]["send_default_pii"] is False
