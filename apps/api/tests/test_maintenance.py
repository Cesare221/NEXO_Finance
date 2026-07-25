"""Tests for the security record maintenance CLI."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.account_action_token import AccountActionToken
from app.models.mfa_challenge import MfaChallenge
from app.models.user import User
from app.maintenance import purge_expired_security_records
from tests.conftest import TestingSessionLocal


def _create_user(db, email: str = "maint@example.com") -> User:
    user = User(name="Maint User", email=email, password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_expired_token(db, user_id: int) -> AccountActionToken:
    token = AccountActionToken(
        user_id=user_id,
        purpose="verify_email",
        token_hash="expired-hash",
        expires_at=datetime.now(timezone.utc) - timedelta(days=31),
    )
    db.add(token)
    db.commit()
    return token


def _create_active_token(db, user_id: int) -> AccountActionToken:
    token = AccountActionToken(
        user_id=user_id,
        purpose="verify_email",
        token_hash="active-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(token)
    db.commit()
    return token


def _create_expired_challenge(db, user_id: int) -> MfaChallenge:
    challenge = MfaChallenge(
        user_id=user_id,
        challenge_hash="expired-challenge",
        expires_at=datetime.now(timezone.utc) - timedelta(days=31),
    )
    db.add(challenge)
    db.commit()
    return challenge


def _create_active_challenge(db, user_id: int) -> MfaChallenge:
    challenge = MfaChallenge(
        user_id=user_id,
        challenge_hash="active-challenge",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(challenge)
    db.commit()
    return challenge


def test_purge_removes_expired_tokens():
    with TestingSessionLocal() as db:
        user = _create_user(db)
        _create_expired_token(db, user.id)
        _create_active_token(db, user.id)

    result = purge_expired_security_records(session_factory=TestingSessionLocal)

    assert result["account_action_tokens_deleted"] == 1
    assert result["status"] == "ok"

    with TestingSessionLocal() as db:
        remaining = db.query(AccountActionToken).all()
        assert len(remaining) == 1
        assert remaining[0].token_hash == "active-hash"


def test_purge_removes_expired_challenges():
    with TestingSessionLocal() as db:
        user = _create_user(db, "challenge@example.com")
        _create_expired_challenge(db, user.id)
        _create_active_challenge(db, user.id)

    result = purge_expired_security_records(session_factory=TestingSessionLocal)

    assert result["mfa_challenges_deleted"] == 1

    with TestingSessionLocal() as db:
        remaining = db.query(MfaChallenge).all()
        assert len(remaining) == 1
        assert remaining[0].challenge_hash == "active-challenge"


def test_purge_preserves_all_when_nothing_expired():
    with TestingSessionLocal() as db:
        user = _create_user(db, "fresh@example.com")
        token = AccountActionToken(
            user_id=user.id,
            purpose="verify_email",
            token_hash="fresh-active-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(token)
        challenge = MfaChallenge(
            user_id=user.id,
            challenge_hash="fresh-active-challenge",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(challenge)
        db.commit()

    result = purge_expired_security_records(session_factory=TestingSessionLocal)

    assert result["account_action_tokens_deleted"] == 0
    assert result["mfa_challenges_deleted"] == 0

    with TestingSessionLocal() as db:
        assert db.query(AccountActionToken).count() == 1
        assert db.query(MfaChallenge).count() == 1


def test_purge_returns_zero_counts_on_empty_db():
    result = purge_expired_security_records(session_factory=TestingSessionLocal)
    assert result["account_action_tokens_deleted"] == 0
    assert result["mfa_challenges_deleted"] == 0
    assert result["status"] == "ok"


def test_purge_handles_multiple_expired_records():
    with TestingSessionLocal() as db:
        user = _create_user(db, "multi@example.com")
        for i in range(5):
            token = AccountActionToken(
                user_id=user.id,
                purpose="verify_email",
                token_hash=f"expired-hash-{i}",
                expires_at=datetime.now(timezone.utc) - timedelta(days=31),
            )
            db.add(token)
        for i in range(3):
            challenge = MfaChallenge(
                user_id=user.id,
                challenge_hash=f"expired-challenge-{i}",
                expires_at=datetime.now(timezone.utc) - timedelta(days=31),
            )
            db.add(challenge)
        db.commit()

    result = purge_expired_security_records(session_factory=TestingSessionLocal)

    assert result["account_action_tokens_deleted"] == 5
    assert result["mfa_challenges_deleted"] == 3
