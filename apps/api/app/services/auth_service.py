from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from sqlalchemy import inspect
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


def _export_value(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _export_row(row, excluded: set[str] | None = None) -> dict:
    blocked = excluded or set()
    return {
        attribute.key: _export_value(getattr(row, attribute.key))
        for attribute in inspect(row).mapper.column_attrs
        if attribute.key not in blocked
    }


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def register_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    privacy_accepted: bool = False,
    ai_data_processing_consent: bool = False,
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise AuthError("Email already registered", 409)
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        privacy_policy_version="2026-07-21" if privacy_accepted else None,
        privacy_accepted_at=datetime.now(timezone.utc) if privacy_accepted else None,
        ai_data_processing_consent=ai_data_processing_consent,
        ai_consent_updated_at=(
            datetime.now(timezone.utc) if ai_data_processing_consent else None
        ),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(
    db: Session,
    email: str,
    password: str,
    device_name: str | None = None,
    ip_hash: str | None = None,
) -> tuple[str, str, User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password", 401)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    access_token = create_access_token(user.id, user.token_version)
    family_id = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, family_id, user.token_version)
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=fingerprint_token(refresh_token),
        family_id=family_id,
        device_name=device_name,
        ip_hash=ip_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session)
    db.commit()
    return access_token, refresh_token, user


def refresh_tokens(
    db: Session,
    old_refresh_token: str,
    device_name: str | None = None,
    ip_hash: str | None = None,
) -> tuple[str, str]:
    payload = decode_token(old_refresh_token)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    family_id = payload.get("family_id")
    token_ver = payload.get("ver")
    if not user_id or token_type != "refresh" or not family_id or token_ver is None:
        raise AuthError("Invalid refresh token", 401)
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.token_version != int(token_ver):
        raise AuthError("Invalid refresh token", 401)
    token_hash = fingerprint_token(old_refresh_token)
    session = (
        db.query(UserSession)
        .filter(UserSession.refresh_token_hash == token_hash)
        .with_for_update()
        .first()
    )
    if not session:
        raise AuthError("Session not found", 401)
    if session.user_id != int(user_id) or session.family_id != family_id:
        raise AuthError("Invalid refresh token", 401)
    now = datetime.now(timezone.utc)
    if not session.is_active:
        db.query(UserSession).filter(
            UserSession.user_id == int(user_id),
            UserSession.family_id == family_id,
            UserSession.is_active.is_(True),
        ).update(
            {
                "is_active": False,
                "revoked_at": now,
                "revocation_reason": "refresh_token_reuse",
            },
            synchronize_session=False,
        )
        db.commit()
        raise AuthError("Refresh token reuse detected", 401)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        session.is_active = False
        session.revoked_at = now
        session.revocation_reason = "expired"
        db.commit()
        raise AuthError("Session expired", 401)
    session.is_active = False
    session.rotated_at = now
    session.last_used_at = now
    new_access = create_access_token(int(user_id), user.token_version)
    new_refresh = create_refresh_token(int(user_id), family_id, user.token_version)
    new_session = UserSession(
        user_id=int(user_id),
        refresh_token_hash=fingerprint_token(new_refresh),
        family_id=family_id,
        parent_refresh_token_hash=token_hash,
        device_name=device_name or session.device_name,
        ip_hash=ip_hash or session.ip_hash,
        expires_at=now
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_session)
    db.commit()
    return new_access, new_refresh


def logout_user(db: Session, user_id: int, refresh_token: str | None = None):
    now = datetime.now(timezone.utc)
    query = db.query(UserSession).filter(
        UserSession.user_id == user_id, UserSession.is_active == True
    )
    if refresh_token:
        query = query.filter(
            UserSession.refresh_token_hash == fingerprint_token(refresh_token)
        )
    query.update(
        {
            "is_active": False,
            "revoked_at": now,
            "revocation_reason": "logout",
        },
        synchronize_session=False,
    )
    db.commit()


def update_profile(db: Session, user: User, changes: dict) -> User:
    changed_fields: list[str] = []
    for field in (
        "name",
        "phone",
        "avatar_data_url",
        "theme_preference",
        "ai_data_processing_consent",
    ):
        if field not in changes:
            continue
        value = changes[field]
        if field == "name" and value is None:
            continue
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)
            if field == "ai_data_processing_consent":
                user.ai_consent_updated_at = datetime.now(timezone.utc)
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


def export_user_data(db: Session, user: User) -> dict:
    from app.models.action_execution import ActionExecution
    from app.models.action_proposal import ActionProposal
    from app.models.audit_event import AuditEvent
    from app.models.billing_statement import BillingStatement
    from app.models.category import Category
    from app.models.credit_card import CreditCard
    from app.models.demo_dataset import DemoDataset
    from app.models.financial_account import FinancialAccount
    from app.models.installment import Installment
    from app.models.installment_plan import InstallmentPlan
    from app.models.recurring_rule import RecurringRule
    from app.models.transaction import Transaction
    from app.models.transfer import Transfer

    collections = {
        "accounts": FinancialAccount,
        "categories": Category,
        "transactions": Transaction,
        "credit_cards": CreditCard,
        "billing_statements": BillingStatement,
        "installment_plans": InstallmentPlan,
        "installments": Installment,
        "recurring_rules": RecurringRule,
        "transfers": Transfer,
        "assistant_proposals": ActionProposal,
        "assistant_executions": ActionExecution,
        "audit_events": AuditEvent,
        "demo_datasets": DemoDataset,
    }
    exported = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "privacy_policy_version": user.privacy_policy_version,
        "profile": _export_row(user, {"password_hash"}),
    }
    for name, model in collections.items():
        rows = db.query(model).filter(model.user_id == user.id).all()
        exported[name] = [_export_row(row) for row in rows]
    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="privacy.data_exported",
            entity_type="user",
            entity_id=user.id,
            payload={"collections": sorted(collections)},
        )
    )
    db.commit()
    return exported


def delete_user_account(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise AuthError("Invalid password", 401)
    db.query(UserSession).filter(UserSession.user_id == user.id).update(
        {
            "is_active": False,
            "revoked_at": datetime.now(timezone.utc),
            "revocation_reason": "account_deleted",
        },
        synchronize_session=False,
    )
    db.delete(user)
    db.commit()


def list_active_sessions(db: Session, user_id: int) -> list[UserSession]:
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_used_at.desc(), UserSession.id.desc())
        .all()
    )


def revoke_user_session(db: Session, user_id: int, session_id: int) -> bool:
    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == user_id)
        .first()
    )
    if not session:
        return False
    session.is_active = False
    session.revoked_at = datetime.now(timezone.utc)
    session.revocation_reason = "user_revoked"
    db.commit()
    return True
