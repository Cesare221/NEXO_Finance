from sqlalchemy.exc import SQLAlchemyError

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
