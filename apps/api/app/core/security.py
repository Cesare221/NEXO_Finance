import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jwt.exceptions import InvalidTokenError

from app.core.config import settings

ALGORITHM = "HS256"
password_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    if hashed.startswith("$argon2"):
        try:
            return password_hasher.verify(hashed, plain)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def password_needs_rehash(hashed: str) -> bool:
    return not hashed.startswith("$argon2") or password_hasher.check_needs_rehash(hashed)


def fingerprint_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _make_token(
    user_id: int,
    token_type: str,
    expire_delta: timedelta,
    family_id: str | None = None,
) -> str:
    claims = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expire_delta,
        "type": token_type,
    }
    if family_id is not None:
        claims["family_id"] = family_id
    return jwt.encode(
        claims,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_access_token(user_id: int) -> str:
    return _make_token(
        user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: int, family_id: str) -> str:
    return _make_token(
        user_id,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        family_id,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return {}
