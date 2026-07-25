from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.account_action_token import AccountActionToken
from app.models.audit_event import AuditEvent
from app.models.session import UserSession
from app.models.user import User
from app.services.account_token_service import AccountTokenError, consume_account_token, issue_account_token
from app.services.mail_service import get_mail_service


class AccountSecurityError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def request_email_verification_for_user(db: Session, user: User, ip_hash: str | None = None) -> None:
    if user.email_verified_at is not None:
        return
    ttl = timedelta(minutes=settings.email_verification_ttl_minutes)
    raw_token = issue_account_token(db, user.id, "verify_email", ttl, ip_hash)
    get_mail_service().send_verification(user, raw_token)


def request_email_verification(db: Session, email: str, ip_hash: str | None = None) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user and user.email_verified_at is None:
        request_email_verification_for_user(db, user, ip_hash)


def confirm_email_verification(db: Session, raw_token: str) -> None:
    try:
        user = consume_account_token(db, raw_token, "verify_email")
    except AccountTokenError as exc:
        raise AccountSecurityError(str(exc), 400) from exc

    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(timezone.utc)
        db.add(
            AuditEvent(
                user_id=user.id,
                event_type="security.email_verified",
                entity_type="user",
                entity_id=user.id,
                payload={},
            )
        )
        db.commit()


def request_password_reset(db: Session, email: str, ip_hash: str | None = None) -> None:
    user = db.query(User).filter(User.email == email).first()
    if user:
        ttl = timedelta(minutes=settings.password_reset_ttl_minutes)
        raw_token = issue_account_token(db, user.id, "reset_password", ttl, ip_hash)
        get_mail_service().send_password_reset(user, raw_token)


def confirm_password_reset(db: Session, raw_token: str, new_password: str) -> None:
    try:
        user = consume_account_token(db, raw_token, "reset_password")
    except AccountTokenError as exc:
        raise AccountSecurityError(str(exc), 400) from exc

    now = datetime.now(timezone.utc)
    user.password_hash = hash_password(new_password)
    user.token_version += 1

    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active.is_(True),
    ).update(
        {
            "is_active": False,
            "revoked_at": now,
            "revocation_reason": "password_reset",
        },
        synchronize_session=False,
    )

    db.query(AccountActionToken).filter(
        AccountActionToken.user_id == user.id,
        AccountActionToken.purpose == "reset_password",
        AccountActionToken.consumed_at.is_(None),
    ).update(
        {"consumed_at": now},
        synchronize_session=False,
    )

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="security.password_reset",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
