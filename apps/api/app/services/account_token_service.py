import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.account_action_token import AccountActionToken
from app.models.user import User


class AccountTokenError(Exception):
    """Raised when an account action token cannot be used."""


def generate_secret() -> str:
    return secrets.token_urlsafe(32)


def token_fingerprint(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def issue_account_token(
    db: Session,
    user_id: int,
    purpose: str,
    ttl: timedelta,
    ip_hash: str | None,
) -> str:
    if ttl <= timedelta():
        raise ValueError("Account token TTL must be positive")

    now = datetime.now(timezone.utc)
    raw_token = generate_secret()
    user = db.query(User).filter(User.id == user_id).with_for_update().one_or_none()
    if user is None:
        raise AccountTokenError("Account token user no longer exists")
    db.query(AccountActionToken).filter(
        AccountActionToken.user_id == user_id,
        AccountActionToken.purpose == purpose,
        AccountActionToken.consumed_at.is_(None),
    ).update({"consumed_at": now}, synchronize_session=False)
    db.add(
        AccountActionToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=token_fingerprint(raw_token),
            request_ip_hash=ip_hash,
            expires_at=now + ttl,
        )
    )
    db.commit()
    return raw_token


def consume_account_token(db: Session, raw_token: str, purpose: str) -> User:
    token = (
        db.query(AccountActionToken)
        .filter(AccountActionToken.token_hash == token_fingerprint(raw_token))
        .with_for_update()
        .one_or_none()
    )
    if token is None:
        raise AccountTokenError("Account token is invalid")
    if token.purpose != purpose:
        raise AccountTokenError("Account token purpose does not match")
    if token.consumed_at is not None:
        raise AccountTokenError("Account token has already been consumed")
    if _as_utc(token.expires_at) <= datetime.now(timezone.utc):
        raise AccountTokenError("Account token has expired")

    user = db.get(User, token.user_id)
    if user is None:
        raise AccountTokenError("Account token user no longer exists")

    token.consumed_at = datetime.now(timezone.utc)
    db.commit()
    return user
