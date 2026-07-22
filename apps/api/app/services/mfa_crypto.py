from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class MfaCryptoError(Exception):
    """Raised when a TOTP secret cannot be encrypted or decrypted."""


def _fernet_for_version(version: str) -> Fernet:
    key = settings.mfa_keyring.get(version)
    if not key:
        raise MfaCryptoError("MFA encryption key version is unavailable")
    try:
        return Fernet(key.encode("ascii"))
    except (TypeError, UnicodeEncodeError, ValueError):
        raise MfaCryptoError("MFA encryption key is invalid") from None


def encrypt_totp_secret(secret: str) -> tuple[str, str]:
    version = settings.mfa_active_key_version
    fernet = _fernet_for_version(version)
    try:
        ciphertext = fernet.encrypt(secret.encode("utf-8")).decode("ascii")
    except (TypeError, UnicodeEncodeError, ValueError):
        raise MfaCryptoError("TOTP secret could not be encrypted") from None
    return ciphertext, version


def decrypt_totp_secret(ciphertext: str, version: str) -> str:
    fernet = _fernet_for_version(version)
    try:
        return fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, TypeError, UnicodeDecodeError, UnicodeEncodeError, ValueError):
        raise MfaCryptoError("TOTP secret could not be decrypted") from None
