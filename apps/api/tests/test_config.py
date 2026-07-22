import pytest

from app.core.config import Settings


def production_settings(**overrides):
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
        "mfa_encryption_keys": "v1:test-key",
        "mfa_active_key_version": "v1",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_requires_a_strong_secret():
    settings = production_settings(secret_key="short")

    with pytest.raises(RuntimeError, match="at least 64 characters"):
        settings.validate_runtime()


@pytest.mark.parametrize(
    "allowed_origins",
    ["*", "http://app.nexo.example", "https://app.nexo.example,*"],
)
def test_production_rejects_insecure_origins(allowed_origins):
    settings = production_settings(allowed_origins=allowed_origins)

    with pytest.raises(RuntimeError, match="HTTPS origins"):
        settings.validate_runtime()


def test_production_requires_distributed_rate_limiting():
    settings = production_settings(redis_url=None)

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        settings.validate_runtime()


def test_production_rejects_wildcard_hosts():
    settings = production_settings(allowed_hosts="*")

    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        settings.validate_runtime()


def test_production_requires_groq_key_when_provider_is_enabled():
    settings = production_settings(fin_ai_provider="groq", groq_api_key=None)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        settings.validate_runtime()


def test_production_requires_resend_and_mfa_keys(monkeypatch):
    config = production_settings(
        mail_provider="resend",
        resend_api_key=None,
        email_from="Nexo <no-reply@nexo.example>",
        public_web_url="https://app.nexo.example",
        mfa_encryption_keys="",
        mfa_active_key_version="v1",
    )
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        config.validate_runtime()


def test_production_rejects_non_https_public_web_url():
    config = production_settings(public_web_url="http://app.nexo.example")
    with pytest.raises(RuntimeError, match="PUBLIC_WEB_URL"):
        config.validate_runtime()


def test_valid_production_settings_pass_runtime_validation():
    settings = production_settings()

    settings.validate_runtime()
