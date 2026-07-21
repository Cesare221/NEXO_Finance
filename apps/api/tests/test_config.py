import pytest

from app.core.config import Settings


def production_settings(**overrides):
    values = {
        "environment": "production",
        "database_url": "postgresql://nexo:secret@db.internal:5432/nexo",
        "secret_key": "a" * 64,
        "allowed_origins": "https://app.nexo.example",
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
