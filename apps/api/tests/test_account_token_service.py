from datetime import datetime, timedelta, timezone

import pytest

from app.models.account_action_token import AccountActionToken
from app.models.user import User
from app.services.account_token_service import (
    AccountTokenError,
    consume_account_token,
    issue_account_token,
    token_fingerprint,
)
from tests.conftest import TestingSessionLocal


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user(db):
    account = User(
        name="Token User",
        email="token@example.com",
        password_hash="not-a-real-password-hash",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_issuing_second_token_invalidates_first(db, user):
    first = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), "ip")
    second = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), "ip")

    with pytest.raises(AccountTokenError):
        consume_account_token(db, first, "verify_email")

    assert consume_account_token(db, second, "verify_email").id == user.id


def test_token_is_single_use(db, user):
    raw = issue_account_token(db, user.id, "reset_password", timedelta(minutes=20), None)

    consume_account_token(db, raw, "reset_password")

    with pytest.raises(AccountTokenError):
        consume_account_token(db, raw, "reset_password")


def test_issued_token_persists_only_its_sha256_fingerprint(db, user):
    raw = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), "ip-hash")

    token = db.query(AccountActionToken).one()

    assert token.token_hash == token_fingerprint(raw)
    assert token.token_hash != raw
    assert len(token.token_hash) == 64
    assert token.request_ip_hash == "ip-hash"


def test_expired_token_is_rejected(db, user):
    raw = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), None)
    token = db.query(AccountActionToken).one()
    token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    with pytest.raises(AccountTokenError, match="expired"):
        consume_account_token(db, raw, "verify_email")


def test_token_cannot_be_consumed_for_a_different_purpose(db, user):
    raw = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), None)

    with pytest.raises(AccountTokenError, match="purpose"):
        consume_account_token(db, raw, "reset_password")

    assert consume_account_token(db, raw, "verify_email").id == user.id


def test_issuing_a_token_does_not_invalidate_another_purpose(db, user):
    verification = issue_account_token(
        db, user.id, "verify_email", timedelta(minutes=30), None
    )
    reset = issue_account_token(
        db, user.id, "reset_password", timedelta(minutes=20), None
    )

    assert consume_account_token(db, verification, "verify_email").id == user.id
    assert consume_account_token(db, reset, "reset_password").id == user.id
