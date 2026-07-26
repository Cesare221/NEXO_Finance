from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import get_db
from app.main import app


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_confirms_database_connection(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_readiness_check_reports_database_outage(client):
    original_override = app.dependency_overrides[get_db]

    class UnavailableDatabase:
        def execute(self, _query):
            raise SQLAlchemyError("database unavailable")

    def override_unavailable_database():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = override_unavailable_database
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides[get_db] = original_override

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json() == {
        "detail": {
            "status": "not_ready",
            "checks": {"database": "unavailable"},
        }
    }


class FakeRedis:
    def __init__(self, *, fail=False):
        self._fail = fail

    def ping(self):
        if self._fail:
            raise ConnectionError("redis unavailable")

    def close(self):
        pass


def test_readiness_includes_redis_in_production(client):
    with patch.object(settings, "environment", "production"), \
         patch.object(settings, "redis_url", "redis://localhost:6379/0"), \
         patch("redis.from_url") as mock_from_url:
        mock_from_url.return_value = FakeRedis()
        response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "ok"


def test_readiness_returns_503_on_redis_failure(client):
    with patch.object(settings, "environment", "production"), \
         patch.object(settings, "redis_url", "redis://localhost:6379/0"), \
         patch("redis.from_url") as mock_from_url:
        mock_from_url.return_value = FakeRedis(fail=True)
        response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert "redis" in str(data)


def test_readiness_skips_redis_in_development(client):
    with patch.object(settings, "environment", "development"), \
         patch.object(settings, "redis_url", None):
        response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"] == {"database": "ok"}
