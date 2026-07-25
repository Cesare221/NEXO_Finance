import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.rate_limit import auth_rate_limiter
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    auth_rate_limiter.clear()
    if not settings.mfa_keyring:
        key = Fernet.generate_key().decode("ascii")
        monkeypatch.setattr(settings, "mfa_encryption_keys", f"v1:{key}")
        monkeypatch.setattr(settings, "mfa_active_key_version", "v1")
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    auth_rate_limiter.clear()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    return TestClient(app)
