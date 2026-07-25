import pyotp
import pytest

from app.models.user import User
from tests.conftest import TestingSessionLocal


PASSWORD = "ValidPassword123!"


def _create_verified_user(client, email="mfa@example.com", name="MFA User"):
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": PASSWORD},
    )
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = user.email_verified_at or user.created_at
        db.commit()
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    return login_resp.json()["access_token"]


def test_mfa_status_defaults_to_disabled(client):
    token = _create_verified_user(client, "disabled@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/auth/mfa/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False, "activated_at": None}


def test_mfa_enrollment_requires_password_and_returns_secret_and_uri(client):
    token = _create_verified_user(client, "enroll@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    bad_pw = client.post("/auth/mfa/enroll", json={"password": "wrong"}, headers=headers)
    assert bad_pw.status_code == 401

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers)
    assert enroll.status_code == 200
    data = enroll.json()
    assert "secret" in data
    assert "otpauth_uri" in data
    assert "otpauth://totp/" in data["otpauth_uri"]
    assert "enroll" in data["otpauth_uri"]

    status = client.get("/auth/mfa/status", headers=headers)
    assert status.json()["enabled"] is False


def test_mfa_confirm_activates_mfa_and_returns_10_recovery_codes(client):
    token = _create_verified_user(client, "confirm@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    secret = enroll["secret"]

    bad_confirm = client.post("/auth/mfa/confirm", json={"code": "000000"}, headers=headers)
    assert bad_confirm.status_code == 400

    totp_code = pyotp.TOTP(secret).now()
    confirm = client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers)
    assert confirm.status_code == 200
    rec_codes = confirm.json()["recovery_codes"]
    assert len(rec_codes) == 10

    status = client.get("/auth/mfa/status", headers=headers)
    assert status.json()["enabled"] is True
    assert status.json()["activated_at"] is not None


def test_login_with_active_mfa_returns_challenge_without_tokens(client):
    token = _create_verified_user(client, "challenge@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    totp_code = pyotp.TOTP(enroll["secret"]).now()
    client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers)

    login_resp = client.post(
        "/auth/login",
        json={"email": "challenge@example.com", "password": PASSWORD},
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["status"] == "mfa_required"
    assert "challenge_token" in body
    assert body.get("access_token") is None
    assert body.get("refresh_token") is None


def test_complete_mfa_challenge_with_totp(client):
    token = _create_verified_user(client, "totp_solve@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    secret = enroll["secret"]
    totp_code = pyotp.TOTP(secret).now()
    client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers)

    login_resp = client.post(
        "/auth/login",
        json={"email": "totp_solve@example.com", "password": PASSWORD},
    ).json()
    challenge_token = login_resp["challenge_token"]

    totp_solve_code = pyotp.TOTP(secret).now()
    solve = client.post(
        "/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "code": totp_solve_code},
    )
    assert solve.status_code == 200
    tokens = solve.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


def test_complete_mfa_challenge_with_recovery_code_is_single_use(client):
    token = _create_verified_user(client, "rec_solve@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    totp_code = pyotp.TOTP(enroll["secret"]).now()
    confirm = client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers).json()
    rec_code = confirm["recovery_codes"][0]

    login_1 = client.post(
        "/auth/login",
        json={"email": "rec_solve@example.com", "password": PASSWORD},
    ).json()
    c_token_1 = login_1["challenge_token"]

    solve_1 = client.post(
        "/auth/mfa/challenge",
        json={"challenge_token": c_token_1, "code": rec_code},
    )
    assert solve_1.status_code == 200
    assert "access_token" in solve_1.json()

    # Second login, try using the same recovery code again
    login_2 = client.post(
        "/auth/login",
        json={"email": "rec_solve@example.com", "password": PASSWORD},
    ).json()
    c_token_2 = login_2["challenge_token"]

    solve_2 = client.post(
        "/auth/mfa/challenge",
        json={"challenge_token": c_token_2, "code": rec_code},
    )
    assert solve_2.status_code == 400


def test_mfa_challenge_attempts_are_bounded_to_5(client):
    token = _create_verified_user(client, "bounded@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    totp_code = pyotp.TOTP(enroll["secret"]).now()
    client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers)

    login_resp = client.post(
        "/auth/login",
        json={"email": "bounded@example.com", "password": PASSWORD},
    ).json()
    challenge_token = login_resp["challenge_token"]

    for _ in range(5):
        resp = client.post(
            "/auth/mfa/challenge",
            json={"challenge_token": challenge_token, "code": "000000"},
        )
        assert resp.status_code == 400

    sixth = client.post(
        "/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "code": "000000"},
    )
    assert sixth.status_code == 400


def test_regenerate_recovery_codes(client):
    token = _create_verified_user(client, "regen@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    totp_code = pyotp.TOTP(enroll["secret"]).now()
    confirm = client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers).json()
    old_codes = confirm["recovery_codes"]

    regen = client.post("/auth/mfa/recovery-codes", json={"password": PASSWORD}, headers=headers)
    assert regen.status_code == 200
    new_codes = regen.json()["recovery_codes"]
    assert len(new_codes) == 10
    assert set(old_codes) != set(new_codes)


def test_disable_mfa_requires_password_and_code(client):
    token = _create_verified_user(client, "disable@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    enroll = client.post("/auth/mfa/enroll", json={"password": PASSWORD}, headers=headers).json()
    secret = enroll["secret"]
    totp_code = pyotp.TOTP(secret).now()
    client.post("/auth/mfa/confirm", json={"code": totp_code}, headers=headers)

    code_now = pyotp.TOTP(secret).now()
    disable = client.request(
        "DELETE",
        "/auth/mfa",
        json={"password": PASSWORD, "code": code_now},
        headers=headers,
    )
    assert disable.status_code == 200

    new_login = client.post("/auth/login", json={"email": "disable@example.com", "password": PASSWORD}).json()
    new_token = new_login["access_token"]
    status = client.get("/auth/mfa/status", headers={"Authorization": f"Bearer {new_token}"})
    assert status.json()["enabled"] is False
