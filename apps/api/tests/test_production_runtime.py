"""Tests for production runtime validation gate."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from app.core.config import Settings


def _production_env(**overrides) -> dict:
    """Build a minimal valid production environment."""
    base = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql://user:pass@db.example.com:5432/nexo",
        "REDIS_URL": "redis://redis.example.com:6379/0",
        "SECRET_KEY": "a" * 64,
        "ALLOWED_ORIGINS": "https://app.nexo.example",
        "ALLOWED_HOSTS": "api.nexo.example",
        "PUBLIC_WEB_URL": "https://app.nexo.example",
        "MAIL_PROVIDER": "resend",
        "RESEND_API_KEY": "re_test_key",
        "EMAIL_FROM": "Nexo <no-reply@nexo.example>",
        "MFA_ENCRYPTION_KEYS": "v1:8pQ1hGvYzFaK9bCdEfGhIjKlMnOpQrStUvWxYz01234=",
        "MFA_ACTIVE_KEY_VERSION": "v1",
    }
    base.update(overrides)
    return base


def _make_settings(**overrides) -> Settings:
    env = _production_env(**overrides)
    # Convert non-string values to strings for os.environ
    str_env = {k: str(v) for k, v in env.items()}
    with patch.dict(os.environ, str_env, clear=True):
        return Settings()


class TestProductionRejectsMissingRequiredSetting:
    @pytest.mark.parametrize("field", [
        "REDIS_URL",
        "SECRET_KEY",
        "PUBLIC_WEB_URL",
    ])
    def test_missing_required_field_raises(self, field):
        settings = _make_settings(**{field: ""})
        with pytest.raises(RuntimeError, match=field):
            settings.validate_runtime()


class TestProductionRejectsUnsafeValues:
    def test_localhost_database_url(self):
        settings = _make_settings(DATABASE_URL="postgresql://user:pass@localhost:5432/nexo")
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            settings.validate_runtime()

    def test_http_allowed_origins(self):
        settings = _make_settings(ALLOWED_ORIGINS="http://app.nexo.example")
        with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
            settings.validate_runtime()

    def test_wildcard_allowed_origins(self):
        settings = _make_settings(ALLOWED_ORIGINS="*")
        with pytest.raises(RuntimeError, match="ALLOWED_ORIGINS"):
            settings.validate_runtime()

    def test_wildcard_allowed_hosts(self):
        settings = _make_settings(ALLOWED_HOSTS="*")
        with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
            settings.validate_runtime()

    def test_http_public_web_url(self):
        settings = _make_settings(PUBLIC_WEB_URL="http://app.nexo.example")
        with pytest.raises(RuntimeError, match="PUBLIC_WEB_URL"):
            settings.validate_runtime()

    def test_short_secret_key(self):
        settings = _make_settings(SECRET_KEY="too-short")
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            settings.validate_runtime()

    def test_default_secret_key(self):
        settings = _make_settings(
            SECRET_KEY="change-me-to-a-random-secret-at-least-32-chars-but-not-long-enough"
        )
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            settings.validate_runtime()

    def test_console_mail_provider(self):
        settings = _make_settings(MAIL_PROVIDER="console")
        with pytest.raises(RuntimeError, match="MAIL_PROVIDER"):
            settings.validate_runtime()

    def test_missing_resend_api_key(self):
        settings = _make_settings(RESEND_API_KEY="")
        with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
            settings.validate_runtime()

    def test_missing_mfa_keyring(self):
        settings = _make_settings(MFA_ENCRYPTION_KEYS="", MFA_ACTIVE_KEY_VERSION="v1")
        with pytest.raises(RuntimeError, match="MFA_ACTIVE_KEY_VERSION"):
            settings.validate_runtime()

    def test_invalid_mfa_key(self):
        settings = _make_settings(
            MFA_ENCRYPTION_KEYS="v1:not-a-valid-fernet-key",
            MFA_ACTIVE_KEY_VERSION="v1",
        )
        with pytest.raises(RuntimeError, match="MFA_ENCRYPTION_KEYS"):
            settings.validate_runtime()

    def test_groq_without_api_key(self):
        settings = _make_settings(FIN_AI_PROVIDER="groq", GROQ_API_KEY="")
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            settings.validate_runtime()

    def test_invalid_ai_provider(self):
        settings = _make_settings(FIN_AI_PROVIDER="openai")
        with pytest.raises(RuntimeError, match="FIN_AI_PROVIDER"):
            settings.validate_runtime()

    def test_sentry_without_environment(self):
        settings = _make_settings(
            SENTRY_DSN="https://key@sentry.io/1",
            SENTRY_ENVIRONMENT="",
            SENTRY_RELEASE="abc123",
        )
        with pytest.raises(RuntimeError, match="SENTRY_ENVIRONMENT"):
            settings.validate_runtime()

    def test_sentry_without_release(self):
        settings = _make_settings(
            SENTRY_DSN="https://key@sentry.io/1",
            SENTRY_ENVIRONMENT="production",
            SENTRY_RELEASE="",
        )
        with pytest.raises(RuntimeError, match="SENTRY_RELEASE"):
            settings.validate_runtime()

    def test_sentry_traces_rate_out_of_range(self):
        settings = _make_settings(
            SENTRY_DSN="https://key@sentry.io/1",
            SENTRY_ENVIRONMENT="production",
            SENTRY_RELEASE="abc123",
            SENTRY_TRACES_SAMPLE_RATE="1.5",
        )
        with pytest.raises(RuntimeError, match="SENTRY_TRACES_SAMPLE_RATE"):
            settings.validate_runtime()


class TestProductionAcceptsValidConfig:
    def test_valid_config_passes(self):
        settings = _make_settings()
        settings.validate_runtime()

    def test_valid_config_with_sentry(self):
        settings = _make_settings(
            SENTRY_DSN="https://key@sentry.io/1",
            SENTRY_ENVIRONMENT="production",
            SENTRY_RELEASE="abc123",
            SENTRY_TRACES_SAMPLE_RATE="0.1",
        )
        settings.validate_runtime()

    def test_valid_config_with_groq(self):
        settings = _make_settings(
            FIN_AI_PROVIDER="groq",
            GROQ_API_KEY="gsk_test_key_1234567890",
        )
        settings.validate_runtime()


class TestDevelopmentSkipsValidation:
    def test_development_skips_all_checks(self):
        settings = Settings()
        settings.validate_runtime()
