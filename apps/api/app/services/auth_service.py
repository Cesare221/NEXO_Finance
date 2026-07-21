from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    fingerprint_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.core.config import settings
from app.models.session import UserSession
from app.models.audit_event import AuditEvent
from app.models.user import User


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def register_user(
    db: Session, name: str, email: str, password: str
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise AuthError("Email already registered", 409)
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(
    db: Session, email: str, password: str
) -> tuple[str, str, User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password", 401)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=fingerprint_token(refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session)
    db.commit()
    return access_token, refresh_token, user


def refresh_tokens(
    db: Session, old_refresh_token: str
) -> tuple[str, str]:
    payload = decode_token(old_refresh_token)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    if not user_id or token_type != "refresh":
        raise AuthError("Invalid refresh token", 401)
    session = (
        db.query(UserSession)
        .filter(
            UserSession.refresh_token_hash == fingerprint_token(old_refresh_token),
            UserSession.is_active == True,
        )
        .first()
    )
    if not session:
        raise AuthError("Session not found or inactive", 401)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        session.is_active = False
        db.commit()
        raise AuthError("Session expired", 401)
    session.is_active = False
    new_access = create_access_token(int(user_id))
    new_refresh = create_refresh_token(int(user_id))
    new_session = UserSession(
        user_id=int(user_id),
        refresh_token_hash=fingerprint_token(new_refresh),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_session)
    db.commit()
    return new_access, new_refresh


def logout_user(db: Session, user_id: int, refresh_token: str | None = None):
    query = db.query(UserSession).filter(
        UserSession.user_id == user_id, UserSession.is_active == True
    )
    if refresh_token:
        query = query.filter(
            UserSession.refresh_token_hash == fingerprint_token(refresh_token)
        )
    query.update({"is_active": False})
    db.commit()


def update_profile(db: Session, user: User, changes: dict) -> User:
    changed_fields: list[str] = []
    for field in ("name", "phone", "avatar_data_url"):
        if field not in changes:
            continue
        value = changes[field]
        if field == "name" and value is None:
            continue
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)
    if changed_fields:
        db.add(
            AuditEvent(
                user_id=user.id,
                event_type="profile.updated",
                entity_type="user",
                entity_id=user.id,
                payload={"changed_fields": sorted(changed_fields)},
            )
        )
        db.commit()
        db.refresh(user)
    return user
