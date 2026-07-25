import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    fingerprint_token,
    hash_password,
    verify_password,
)
from app.models.audit_event import AuditEvent
from app.models.mfa_challenge import MfaChallenge
from app.models.mfa_method import MfaMethod
from app.models.mfa_recovery_code import MfaRecoveryCode
from app.models.session import UserSession
from app.models.user import User
from app.services.mfa_crypto import decrypt_totp_secret, encrypt_totp_secret


class MfaError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def generate_recovery_codes() -> list[str]:
    codes = []
    for _ in range(10):
        part1 = secrets.token_hex(2).upper()
        part2 = secrets.token_hex(2).upper()
        codes.append(f"{part1}-{part2}")
    return codes


def get_mfa_status(db: Session, user_id: int) -> tuple[bool, datetime | None]:
    method = db.query(MfaMethod).filter(MfaMethod.user_id == user_id).first()
    if method and method.activated_at is not None and method.disabled_at is None:
        return True, method.activated_at
    return False, None


def start_totp_enrollment(db: Session, user: User, password: str) -> tuple[str, str]:
    if not verify_password(password, user.password_hash):
        raise MfaError("Senha incorreta", 401)

    secret = pyotp.random_base32()
    ciphertext, key_version = encrypt_totp_secret(secret)

    method = db.query(MfaMethod).filter(MfaMethod.user_id == user.id).first()
    if method:
        method.secret_ciphertext = ciphertext
        method.key_version = key_version
        method.activated_at = None
        method.disabled_at = None
    else:
        method = MfaMethod(
            user_id=user.id,
            secret_ciphertext=ciphertext,
            key_version=key_version,
            activated_at=None,
            disabled_at=None,
        )
        db.add(method)

    db.commit()
    otpauth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Nexo")
    return secret, otpauth_uri


def confirm_totp_enrollment(db: Session, user: User, code: str) -> list[str]:
    method = db.query(MfaMethod).filter(MfaMethod.user_id == user.id).first()
    if not method:
        raise MfaError("MFA não configurado", 400)

    secret = decrypt_totp_secret(method.secret_ciphertext, method.key_version)
    if not pyotp.TOTP(secret).verify(code, valid_window=1):
        raise MfaError("Código TOTP inválido", 400)

    now = datetime.now(timezone.utc)
    method.activated_at = now
    method.disabled_at = None

    db.query(MfaRecoveryCode).filter(MfaRecoveryCode.method_id == method.id).delete()

    plain_codes = generate_recovery_codes()
    for code_str in plain_codes:
        db.add(
            MfaRecoveryCode(
                method_id=method.id,
                code_hash=hash_password(code_str),
            )
        )

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="security.mfa_activated",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
    return plain_codes


def create_mfa_challenge(db: Session, user_id: int) -> str:
    raw_challenge = secrets.token_urlsafe(32)
    c_hash = fingerprint_token(raw_challenge)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.mfa_challenge_ttl_minutes)

    challenge = MfaChallenge(
        user_id=user_id,
        challenge_hash=c_hash,
        expires_at=expires_at,
        attempts=0,
    )
    db.add(challenge)
    db.commit()
    return raw_challenge


def complete_mfa_challenge(
    db: Session,
    challenge_token: str,
    code: str,
    device_name: str | None = None,
    ip_hash: str | None = None,
) -> tuple[str, str, User]:
    c_hash = fingerprint_token(challenge_token)
    challenge = (
        db.query(MfaChallenge)
        .filter(MfaChallenge.challenge_hash == c_hash)
        .with_for_update()
        .first()
    )
    if not challenge or challenge.consumed_at is not None:
        raise MfaError("Desafio de MFA inválido ou expirado", 400)

    now = datetime.now(timezone.utc)
    if _as_utc(challenge.expires_at) <= now:
        raise MfaError("Desafio de MFA expirado", 400)

    if challenge.attempts >= 5:
        raise MfaError("Máximo de tentativas excedido", 400)

    challenge.attempts += 1

    method = (
        db.query(MfaMethod)
        .filter(
            MfaMethod.user_id == challenge.user_id,
            MfaMethod.activated_at.is_not(None),
            MfaMethod.disabled_at.is_(None),
        )
        .first()
    )
    if not method:
        db.commit()
        raise MfaError("MFA não está ativo para esta conta", 400)

    secret = decrypt_totp_secret(method.secret_ciphertext, method.key_version)
    is_valid_totp = pyotp.TOTP(secret).verify(code, valid_window=1)

    if not is_valid_totp:
        recovery_codes = (
            db.query(MfaRecoveryCode)
            .filter(
                MfaRecoveryCode.method_id == method.id,
                MfaRecoveryCode.consumed_at.is_(None),
            )
            .all()
        )
        matching_code = None
        for rec in recovery_codes:
            if verify_password(code, rec.code_hash):
                matching_code = rec
                break

        if not matching_code:
            db.commit()
            raise MfaError("Código de verificação inválido", 400)

        matching_code.consumed_at = now

    challenge.consumed_at = now
    user = db.get(User, challenge.user_id)

    access_token = create_access_token(user.id, user.token_version)
    import uuid
    family_id = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, family_id, user.token_version)

    session = UserSession(
        user_id=user.id,
        refresh_token_hash=fingerprint_token(refresh_token),
        family_id=family_id,
        device_name=device_name,
        ip_hash=ip_hash,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session)
    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="security.mfa_challenge_completed",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
    return access_token, refresh_token, user


def regenerate_recovery_codes(db: Session, user: User, password: str) -> list[str]:
    if not verify_password(password, user.password_hash):
        raise MfaError("Senha incorreta", 401)

    method = (
        db.query(MfaMethod)
        .filter(
            MfaMethod.user_id == user.id,
            MfaMethod.activated_at.is_not(None),
            MfaMethod.disabled_at.is_(None),
        )
        .first()
    )
    if not method:
        raise MfaError("MFA não está ativo", 400)

    db.query(MfaRecoveryCode).filter(MfaRecoveryCode.method_id == method.id).delete()

    plain_codes = generate_recovery_codes()
    for code_str in plain_codes:
        db.add(
            MfaRecoveryCode(
                method_id=method.id,
                code_hash=hash_password(code_str),
            )
        )

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="security.mfa_recovery_codes_regenerated",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
    return plain_codes


def disable_totp(db: Session, user: User, password: str, code: str) -> None:
    if not verify_password(password, user.password_hash):
        raise MfaError("Senha incorreta", 401)

    method = (
        db.query(MfaMethod)
        .filter(
            MfaMethod.user_id == user.id,
            MfaMethod.activated_at.is_not(None),
            MfaMethod.disabled_at.is_(None),
        )
        .first()
    )
    if not method:
        raise MfaError("MFA não está ativo", 400)

    secret = decrypt_totp_secret(method.secret_ciphertext, method.key_version)
    is_valid = pyotp.TOTP(secret).verify(code, valid_window=1)

    if not is_valid:
        recovery_codes = (
            db.query(MfaRecoveryCode)
            .filter(
                MfaRecoveryCode.method_id == method.id,
                MfaRecoveryCode.consumed_at.is_(None),
            )
            .all()
        )
        matching = next(
            (rec for rec in recovery_codes if verify_password(code, rec.code_hash)),
            None,
        )
        if not matching:
            raise MfaError("Código de verificação inválido", 400)
        matching.consumed_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    method.disabled_at = now
    method.activated_at = None
    user.token_version += 1

    db.query(UserSession).filter(
        UserSession.user_id == user.id,
        UserSession.is_active.is_(True),
    ).update(
        {
            "is_active": False,
            "revoked_at": now,
            "revocation_reason": "mfa_disabled",
        },
        synchronize_session=False,
    )

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="security.mfa_disabled",
            entity_type="user",
            entity_id=user.id,
            payload={},
        )
    )
    db.commit()
