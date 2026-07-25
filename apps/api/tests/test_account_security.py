import pytest
from app.models.user import User
from tests.conftest import TestingSessionLocal


class MailRecorder:
    def __init__(self):
        self.sent_verifications = []
        self.sent_resets = []

    def send_verification(self, user, raw_token):
        self.sent_verifications.append((user.email, raw_token))

    def send_password_reset(self, user, raw_token):
        self.sent_resets.append((user.email, raw_token))


@pytest.fixture()
def mail_recorder(monkeypatch):
    recorder = MailRecorder()
    monkeypatch.setattr("app.services.account_security_service.get_mail_service", lambda: recorder)
    return recorder


def test_register_returns_verification_required_and_sends_email(client, mail_recorder):
    response = client.post(
        "/auth/register",
        json={
            "name": "New User",
            "email": "unverified@example.com",
            "password": "ValidPassword123!",
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        "status": "verification_required",
        "email": "unverified@example.com",
    }
    assert len(mail_recorder.sent_verifications) == 1
    assert mail_recorder.sent_verifications[0][0] == "unverified@example.com"
    token = mail_recorder.sent_verifications[0][1]
    assert len(token) > 30


def test_unverified_user_cannot_access_financial_routes(client, mail_recorder):
    client.post(
        "/auth/register",
        json={
            "name": "Unverified",
            "email": "unverified2@example.com",
            "password": "ValidPassword123!",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "unverified2@example.com", "password": "ValidPassword123!"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    protected = client.get(
        "/financial/dashboard",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert protected.status_code == 403
    assert "verification" in protected.json()["detail"].lower()


def test_confirm_email_verification_success_grants_access(client, mail_recorder):
    client.post(
        "/auth/register",
        json={
            "name": "Verify Me",
            "email": "verifyme@example.com",
            "password": "ValidPassword123!",
        },
    )
    token = mail_recorder.sent_verifications[0][1]

    confirm_resp = client.post(
        "/auth/email-verification/confirm",
        json={"token": token},
    )
    assert confirm_resp.status_code == 200

    login_resp = client.post(
        "/auth/login",
        json={"email": "verifyme@example.com", "password": "ValidPassword123!"},
    )
    access_token = login_resp.json()["access_token"]

    protected = client.get(
        "/financial/dashboard",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert protected.status_code == 200


def test_email_verification_is_single_use(client, mail_recorder):
    client.post(
        "/auth/register",
        json={
            "name": "Single Use",
            "email": "singleuse@example.com",
            "password": "ValidPassword123!",
        },
    )
    token = mail_recorder.sent_verifications[0][1]

    first = client.post("/auth/email-verification/confirm", json={"token": token})
    assert first.status_code == 200

    second = client.post("/auth/email-verification/confirm", json={"token": token})
    assert second.status_code == 400


def test_email_verification_request_is_enumeration_resistant(client, mail_recorder):
    client.post(
        "/auth/register",
        json={"name": "Known", "email": "known@example.com", "password": "ValidPassword123!"},
    )
    mail_recorder.sent_verifications.clear()

    existing = client.post("/auth/email-verification/request", json={"email": "known@example.com"})
    missing = client.post("/auth/email-verification/request", json={"email": "missing@example.com"})

    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json() == missing.json()
    assert len(mail_recorder.sent_verifications) == 1
    assert mail_recorder.sent_verifications[0][0] == "known@example.com"


def test_password_reset_is_enumeration_resistant(client, mail_recorder):
    client.post(
        "/auth/register",
        json={"name": "Known", "email": "known@example.com", "password": "ValidPassword123!"},
    )

    existing = client.post("/auth/password-reset/request", json={"email": "known@example.com"})
    missing = client.post("/auth/password-reset/request", json={"email": "missing@example.com"})

    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json() == missing.json()
    assert len(mail_recorder.sent_resets) == 1
    assert mail_recorder.sent_resets[0][0] == "known@example.com"


def test_password_reset_flow_and_session_revocation(client, mail_recorder):
    client.post(
        "/auth/register",
        json={"name": "Reset User", "email": "reset@example.com", "password": "OldPassword123!"},
    )
    verify_token = mail_recorder.sent_verifications[0][1]
    client.post("/auth/email-verification/confirm", json={"token": verify_token})

    login_1 = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "OldPassword123!"},
    )
    old_access_token = login_1.json()["access_token"]
    old_refresh_token = login_1.json()["refresh_token"]

    client.post("/auth/password-reset/request", json={"email": "reset@example.com"})
    reset_token = mail_recorder.sent_resets[0][1]

    confirm_resp = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "NewSecurePassword123!"},
    )
    assert confirm_resp.status_code == 200

    old_access_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {old_access_token}"},
    )
    assert old_access_resp.status_code == 401

    old_refresh_resp = client.post("/auth/refresh", json={"refresh_token": old_refresh_token})
    assert old_refresh_resp.status_code == 401

    old_login_resp = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "OldPassword123!"},
    )
    assert old_login_resp.status_code == 401

    new_login_resp = client.post(
        "/auth/login",
        json={"email": "reset@example.com", "password": "NewSecurePassword123!"},
    )
    assert new_login_resp.status_code == 200
    assert new_login_resp.json()["access_token"]


def test_password_reset_token_single_use(client, mail_recorder):
    client.post(
        "/auth/register",
        json={"name": "Reset Once", "email": "resetonce@example.com", "password": "OldPassword123!"},
    )
    client.post("/auth/password-reset/request", json={"email": "resetonce@example.com"})
    reset_token = mail_recorder.sent_resets[0][1]

    first = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "NewPassword123!"},
    )
    assert first.status_code == 200

    second = client.post(
        "/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "AnotherPassword123!"},
    )
    assert second.status_code == 400


def test_verification_token_cannot_be_used_for_password_reset(client, mail_recorder):
    client.post(
        "/auth/register",
        json={"name": "Wrong Purpose", "email": "wrongpurpose@example.com", "password": "OldPassword123!"},
    )
    verify_token = mail_recorder.sent_verifications[0][1]

    wrong_reset = client.post(
        "/auth/password-reset/confirm",
        json={"token": verify_token, "new_password": "NewPassword123!"},
    )
    assert wrong_reset.status_code == 400
