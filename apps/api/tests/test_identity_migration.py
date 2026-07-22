import pytest
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.database import Base
from app.models import User
from tests.conftest import TestingSessionLocal


@pytest.fixture()
def db() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_identity_tables_are_registered() -> None:
    assert "account_action_tokens" in Base.metadata.tables
    assert "mfa_methods" in Base.metadata.tables
    assert "mfa_recovery_codes" in Base.metadata.tables
    assert "mfa_challenges" in Base.metadata.tables


def test_user_defaults_token_version(db: Session) -> None:
    user = User(name="A", email="a@example.com", password_hash="hash")
    db.add(user)
    db.commit()

    assert user.email_verified_at is None
    assert user.token_version == 0


def test_identity_metadata_has_required_lifecycle_contracts() -> None:
    action_tokens = Base.metadata.tables["account_action_tokens"]
    methods = Base.metadata.tables["mfa_methods"]
    recovery_codes = Base.metadata.tables["mfa_recovery_codes"]
    challenges = Base.metadata.tables["mfa_challenges"]

    assert action_tokens.c.token_hash.type.length == 64
    assert action_tokens.c.token_hash.unique is True
    assert action_tokens.c.request_ip_hash.type.length == 64
    assert action_tokens.c.expires_at.type.timezone is True
    assert methods.c.user_id.unique is True
    assert methods.c.activated_at.nullable is True
    assert methods.c.disabled_at.nullable is True
    assert recovery_codes.c.consumed_at.nullable is True
    assert challenges.c.challenge_hash.type.length == 64
    assert challenges.c.challenge_hash.unique is True
    assert challenges.c.attempts.default.arg == 0

    for table, column, target in (
        (action_tokens, "user_id", "users.id"),
        (methods, "user_id", "users.id"),
        (recovery_codes, "method_id", "mfa_methods.id"),
        (challenges, "user_id", "users.id"),
    ):
        foreign_key = next(iter(table.c[column].foreign_keys))
        assert foreign_key.target_fullname == target
        assert foreign_key.ondelete == "CASCADE"
