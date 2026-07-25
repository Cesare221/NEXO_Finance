"""
End-to-end identity lifecycle test.
Walks a user through registration, email verification, login, MFA enrollment,
MFA challenge completion, password recovery, session revocation, and account deletion.
"""
from datetime import datetime, timezone

import pyotp
import pytest
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.session import UserSession
from tests.conftest import TestingSessionLocal

STRONG_PASSWORD = "FinSeguro123!"


def _fetch_verification_token(mail_recorder) -> str:
    assert len(mail_recorder.sent_verifications) == 1
    return mail_recorder.sent_verifications[0][1]


def _fetch_reset_token(mail_recorder) -> str:
    assert len(mail_recorder.sent_resets) == 1
    return mail_recorder.sent_resets[0][1]


class MailRecorder:
    def __init__(self):
        self.sent_verifications: list[tuple[str, str]] = []
        self.sent_resets: list[tuple[str, str]] = []

    def send_verification(self, user, raw_token):
        self.sent_verifications.append((user.email, raw_token))

    def send_password_reset(self, user, raw_token):
        self.sent_resets.append((user.email, raw_token))


@pytest.fixture()
def mail_recorder(monkeypatch):
    recorder = MailRecorder()
    monkeypatch.setattr(
        "app.services.account_security_service.get_mail_service",
        lambda: recorder
    )
    return recorder


# ── Phase 1: Registration & email verification ──


def test_identity_e2e_registration_and_verification(client: TestClient, mail_recorder) -> None:
    email = "e2e-register@example.com"

    response = client.post("/auth/register", json={
        "name": "E2E User",
        "email": email,
        "password": STRONG_PASSWORD,
        "privacy_accepted": True,
        "ai_data_processing_consent": False,
    })
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "verification_required"
    assert body["email"] == email
    assert "access_token" not in body

    assert len(mail_recorder.sent_verifications) == 1
    token = _fetch_verification_token(mail_recorder)
    assert len(token) > 30

    verify_response = client.post("/auth/email-verification/confirm", json={"token": token})
    assert verify_response.status_code == 200

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        assert user.email_verified_at is not None


def test_identity_e2e_unverified_login(client: TestClient, mail_recorder) -> None:
    email = "unverified-login@example.com"
    client.post("/auth/register", json={
        "name": "Unverified", "email": email, "password": STRONG_PASSWORD
    })

    login = client.post("/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    assert login.status_code == 200
    assert login.json()["status"] == "email_verification_required"
    assert login.json().get("access_token") is None
    assert login.json().get("refresh_token") is None


# ── Phase 2: Login & session management ──


def test_identity_e2e_login_and_refresh(client: TestClient) -> None:
    email = "login-e2e@example.com"

    client.post("/auth/register", json={
        "name": "Login Test", "email": email, "password": STRONG_PASSWORD,
    })
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()

    login = client.post("/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["status"] == "authenticated"
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {access_token}"}
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email

    refreshed = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"] != access_token
    assert new_tokens["refresh_token"] != refresh_token

    client.post("/auth/logout", json={"refresh_token": new_tokens["refresh_token"]},
                headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    stale = client.post("/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert stale.status_code == 401

    old_session = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert old_session.status_code == 401


# ── Phase 3: MFA enrollment, login challenge, and recovery ──


def test_identity_e2e_mfa_full_lifecycle(client: TestClient) -> None:
    email = "mfa-e2e@example.com"
    password = STRONG_PASSWORD

    client.post("/auth/register", json={
        "name": "MFA E2E", "email": email, "password": password,
    })
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()

    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    auth_header = {"Authorization": f"Bearer {login.json()['access_token']}"}

    status = client.get("/auth/mfa/status", headers=auth_header)
    assert status.json() == {"enabled": False, "activated_at": None}

    enroll = client.post("/auth/mfa/enroll",
                         json={"password": password}, headers=auth_header)
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]
    assert "otpauth://totp/" in enroll.json()["otpauth_uri"]

    confirm = client.post("/auth/mfa/confirm",
                          json={"code": pyotp.TOTP(secret).now()}, headers=auth_header)
    assert confirm.status_code == 200
    recovery_codes = confirm.json()["recovery_codes"]
    assert len(recovery_codes) == 10

    status = client.get("/auth/mfa/status", headers=auth_header)
    assert status.json()["enabled"] is True
    assert status.json()["activated_at"] is not None

    # ── MFA login challenge ──

    challenge_login = client.post("/auth/login", json={"email": email, "password": password})
    assert challenge_login.status_code == 200
    challenge_body = challenge_login.json()
    assert challenge_body["status"] == "mfa_required"
    assert challenge_body.get("access_token") is None
    challenge_token = challenge_body["challenge_token"]

    challenge = client.post("/auth/mfa/challenge", json={
        "challenge_token": challenge_token,
        "code": pyotp.TOTP(secret).now(),
    })
    assert challenge.status_code == 200
    assert challenge.json()["access_token"]
    assert challenge.json()["refresh_token"]

    # ── Recovery code challenge ──

    recovery_login = client.post("/auth/login", json={"email": email, "password": password})
    recovery_challenge_token = recovery_login.json()["challenge_token"]

    recovery_challenge = client.post("/auth/mfa/challenge", json={
        "challenge_token": recovery_challenge_token,
        "code": recovery_codes[0],
    })
    assert recovery_challenge.status_code == 200

    # Recovery code is consumed — second use should fail
    second_login = client.post("/auth/login", json={"email": email, "password": password})
    second_recovery = client.post("/auth/mfa/challenge", json={
        "challenge_token": second_login.json()["challenge_token"],
        "code": recovery_codes[0],
    })
    assert second_recovery.status_code == 400

    # ── Regenerate recovery codes ──

    regen = client.post("/auth/mfa/recovery-codes",
                        json={"password": password}, headers=auth_header)
    assert regen.status_code == 200
    new_codes = regen.json()["recovery_codes"]
    assert len(new_codes) == 10
    assert set(new_codes) != set(recovery_codes)

    # ── Disable MFA ──

    disable = client.request("DELETE", "/auth/mfa", json={
        "password": password,
        "code": pyotp.TOTP(secret).now(),
    }, headers=auth_header)
    assert disable.status_code == 200

    # Disable revokes all sessions — re-login to verify
    disable_login = client.post("/auth/login", json={"email": email, "password": password})
    assert disable_login.status_code == 200
    assert disable_login.json()["status"] == "authenticated"


# ── Phase 4: Password recovery with session revocation ──


def test_identity_e2e_password_recovery_and_revocation(client: TestClient, mail_recorder) -> None:
    email = "reset-e2e@example.com"
    old_password = STRONG_PASSWORD
    new_password = "R3cuperadaSenhaE2E!"

    client.post("/auth/register", json={
        "name": "Reset E2E", "email": email, "password": old_password,
    })
    token = _fetch_verification_token(mail_recorder)
    client.post("/auth/email-verification/confirm", json={"token": token})
    mail_recorder.sent_verifications.clear()

    login = client.post("/auth/login", json={"email": email, "password": old_password})
    old_access = login.json()["access_token"]
    old_refresh = login.json()["refresh_token"]

    request_reset = client.post("/auth/password-reset/request", json={"email": email})
    assert request_reset.status_code == 202
    assert len(mail_recorder.sent_resets) == 1
    reset_token = _fetch_reset_token(mail_recorder)

    confirm_reset = client.post("/auth/password-reset/confirm", json={
        "token": reset_token,
        "new_password": new_password,
    })
    assert confirm_reset.status_code == 200

    # Old tokens should be rejected
    old_access_check = client.get("/auth/me", headers={
        "Authorization": f"Bearer {old_access}"
    })
    assert old_access_check.status_code == 401

    old_refresh_check = client.post("/auth/refresh", json={
        "refresh_token": old_refresh
    })
    assert old_refresh_check.status_code == 401

    old_password_login = client.post("/auth/login", json={
        "email": email, "password": old_password
    })
    assert old_password_login.status_code == 401

    new_login = client.post("/auth/login", json={
        "email": email, "password": new_password
    })
    assert new_login.status_code == 200
    assert new_login.json()["status"] == "authenticated"
    assert new_login.json()["access_token"]


def test_identity_e2e_missing_email_enumeration_resistant(client: TestClient) -> None:
    response = client.post("/auth/password-reset/request",
                           json={"email": "nobody@nowhere.example"})
    assert response.status_code == 202
    body = response.json()
    assert "message" in body or body == {}


def test_identity_e2e_account_deletion(client: TestClient) -> None:
    email = "delete-e2e@example.com"
    password = STRONG_PASSWORD

    client.post("/auth/register", json={
        "name": "Delete E2E", "email": email, "password": password,
    })
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()

    login = client.post("/auth/login", json={"email": email, "password": password})
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    wrong = client.request("DELETE", "/auth/me", json={"password": "wrongpass"}, headers=headers)
    assert wrong.status_code == 401

    delete = client.request("DELETE", "/auth/me", json={"password": password}, headers=headers)
    assert delete.status_code == 204

    after = client.get("/auth/me", headers=headers)
    assert after.status_code == 401


def test_identity_e2e_session_management(client: TestClient) -> None:
    email = "sessions-e2e@example.com"

    client.post("/auth/register", json={
        "name": "Session User", "email": email, "password": STRONG_PASSWORD,
    })
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()

    login = client.post("/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    sessions = client.get("/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1
    session_id = sessions.json()[0]["id"]

    revoke = client.request("DELETE", f"/auth/sessions/{session_id}", headers=headers)
    assert revoke.status_code in (200, 204)

    remaining = client.get("/auth/sessions", headers=headers)
    for s in remaining.json():
        assert s["id"] != session_id