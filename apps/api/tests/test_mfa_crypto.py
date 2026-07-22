import pytest
from cryptography.fernet import Fernet

from app.core.config import settings
from app.services.mfa_crypto import MfaCryptoError, decrypt_totp_secret, encrypt_totp_secret


@pytest.fixture()
def settings_with_keyring(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr(settings, "mfa_encryption_keys", f"v1:{key}")
    monkeypatch.setattr(settings, "mfa_active_key_version", "v1")
    return settings


def test_totp_secret_round_trip(settings_with_keyring):
    ciphertext, version = encrypt_totp_secret("JBSWY3DPEHPK3PXP")

    assert version == "v1"
    assert decrypt_totp_secret(ciphertext, version) == "JBSWY3DPEHPK3PXP"


def test_decryption_uses_the_exact_stored_key_version(monkeypatch):
    old_key = Fernet.generate_key().decode("ascii")
    active_key = Fernet.generate_key().decode("ascii")
    monkeypatch.setattr(settings, "mfa_encryption_keys", f"v1:{old_key},v2:{active_key}")
    monkeypatch.setattr(settings, "mfa_active_key_version", "v1")
    ciphertext, version = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
    monkeypatch.setattr(settings, "mfa_active_key_version", "v2")

    assert decrypt_totp_secret(ciphertext, version) == "JBSWY3DPEHPK3PXP"


def test_missing_key_version_does_not_expose_ciphertext(settings_with_keyring):
    ciphertext, _ = encrypt_totp_secret("JBSWY3DPEHPK3PXP")

    with pytest.raises(MfaCryptoError) as error:
        decrypt_totp_secret(ciphertext, "retired")

    assert ciphertext not in str(error.value)


def test_missing_active_key_version_does_not_expose_secret(monkeypatch):
    secret = "JBSWY3DPEHPK3PXP"
    monkeypatch.setattr(settings, "mfa_encryption_keys", "")
    monkeypatch.setattr(settings, "mfa_active_key_version", "retired")

    with pytest.raises(MfaCryptoError) as error:
        encrypt_totp_secret(secret)

    assert secret not in str(error.value)


def test_invalid_ciphertext_does_not_expose_its_value(settings_with_keyring):
    ciphertext = "sensitive-invalid-ciphertext"

    with pytest.raises(MfaCryptoError) as error:
        decrypt_totp_secret(ciphertext, "v1")

    assert ciphertext not in str(error.value)
