import pytest
from datetime import datetime, timezone

from app.models.audit_event import AuditEvent
from app.models.session import UserSession
from app.models.user import User
from tests.conftest import TestingSessionLocal


STRONG_PASSWORD = "FinSeguro123!"
VALID_AVATAR = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _verify_user(email: str) -> None:
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).one()
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()


def _register_theme_user(client, email: str = "theme@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"name": "Theme User", "email": email, "password": STRONG_PASSWORD},
    )
    assert response.status_code == 201
    _verify_user(email)
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": STRONG_PASSWORD},
    )
    assert login_resp.status_code == 200
    return {"Authorization": f"Bearer {login_resp.json()['access_token']}"}


def test_theme_preference_defaults_to_system_and_is_returned(client):
    headers = _register_theme_user(client)

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["theme_preference"] == "system"


@pytest.mark.parametrize("preference", ["system", "light", "dark"])
def test_theme_preference_accepts_supported_values(client, preference):
    headers = _register_theme_user(client, f"theme-{preference}@example.com")

    response = client.patch(
        "/auth/me",
        json={"theme_preference": preference},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["theme_preference"] == preference
    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == f"theme-{preference}@example.com").one()
        assert user.theme_preference == preference


def test_theme_preference_rejects_unknown_value(client):
    headers = _register_theme_user(client, "theme-invalid@example.com")

    response = client.patch(
        "/auth/me",
        json={"theme_preference": "midnight"},
        headers=headers,
    )

    assert response.status_code == 422


def test_theme_preference_update_is_audited_without_profile_values(client):
    headers = _register_theme_user(client, "theme-audit@example.com")

    response = client.patch(
        "/auth/me",
        json={"theme_preference": "dark"},
        headers=headers,
    )

    assert response.status_code == 200
    with TestingSessionLocal() as db:
        audit = db.query(AuditEvent).filter_by(event_type="profile.updated").one()
        assert audit.payload == {"changed_fields": ["theme_preference"]}


def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "verification_required"
    assert data["email"] == "test@example.com"
    assert "access_token" not in data


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={
            "name": "User A",
            "email": "dup@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    response = client.post(
        "/auth/register",
        json={
            "name": "User B",
            "email": "dup@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "name": "Test",
            "email": "login@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("login@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": STRONG_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "name": "Test",
            "email": "badpw@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("badpw@example.com")
    response = client.post(
        "/auth/login",
        json={"email": "badpw@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_authenticated(client):
    client.post(
        "/auth/register",
        json={
            "name": "Me User",
            "email": "me@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("me@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "me@example.com", "password": STRONG_PASSWORD},
    )
    token = login_resp.json()["access_token"]
    response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["name"] == "Me User"


def test_me_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_update_own_profile(client):
    client.post(
        "/auth/register",
        json={
            "name": "Original Name",
            "email": "profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("profile@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "profile@example.com", "password": STRONG_PASSWORD},
    )
    token = login_resp.json()["access_token"]

    response = client.patch(
        "/auth/me",
        json={
            "name": "Updated Name",
            "phone": "+55 (11) 99999-9999",
            "avatar_data_url": VALID_AVATAR,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    assert response.json()["phone"] == "+55 (11) 99999-9999"
    assert response.json()["avatar_data_url"] == VALID_AVATAR

    db = TestingSessionLocal()
    try:
        audit = db.query(AuditEvent).filter(AuditEvent.event_type == "profile.updated").one()
        assert set(audit.payload["changed_fields"]) == {"name", "phone", "avatar_data_url"}
        assert "data:image" not in str(audit.payload)
    finally:
        db.close()


def test_update_profile_can_remove_phone_and_avatar(client):
    client.post(
        "/auth/register",
        json={
            "name": "Profile User",
            "email": "clear-profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("clear-profile@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "clear-profile@example.com", "password": STRONG_PASSWORD},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        "/auth/me",
        json={"phone": "+55 11 99999-9999", "avatar_data_url": VALID_AVATAR},
        headers=headers,
    )

    response = client.patch(
        "/auth/me",
        json={"phone": None, "avatar_data_url": None},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["phone"] is None
    assert response.json()["avatar_data_url"] is None


def test_update_profile_rejects_invalid_phone_and_avatar(client):
    client.post(
        "/auth/register",
        json={
            "name": "Profile User",
            "email": "invalid-profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("invalid-profile@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "invalid-profile@example.com", "password": STRONG_PASSWORD},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    invalid_phone = client.patch(
        "/auth/me",
        json={"phone": "telefone inválido"},
        headers=headers,
    )
    invalid_avatar = client.patch(
        "/auth/me",
        json={"avatar_data_url": "data:text/html;base64,PHNjcmlwdD4="},
        headers=headers,
    )

    assert invalid_phone.status_code == 422
    assert invalid_avatar.status_code == 422


def test_update_profile_requires_authentication(client):
    response = client.patch("/auth/me", json={"name": "No Session"})
    assert response.status_code == 401


def test_refresh_token(client):
    client.post(
        "/auth/register",
        json={
            "name": "Refresh",
            "email": "refresh@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("refresh@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "refresh@example.com", "password": STRONG_PASSWORD},
    )
    refresh = login_resp.json()["refresh_token"]
    response = client.post(
        "/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh


def test_logout(client):
    client.post(
        "/auth/register",
        json={
            "name": "Logout",
            "email": "logout@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("logout@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "logout@example.com", "password": STRONG_PASSWORD},
    )
    access = login_resp.json()["access_token"]
    refresh = login_resp.json()["refresh_token"]
    response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert response.status_code == 204
    re_refresh = client.post(
        "/auth/refresh", json={"refresh_token": refresh}
    )
    assert re_refresh.status_code == 401


def test_authorization_isolation(client):
    client.post(
        "/auth/register",
        json={
            "name": "User A",
            "email": "a@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("a@example.com")
    token_a = client.post("/auth/login", json={"email": "a@example.com", "password": STRONG_PASSWORD}).json()["access_token"]
    me_a = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert me_a.json()["email"] == "a@example.com"
    client.post(
        "/auth/register",
        json={
            "name": "User B",
            "email": "b@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("b@example.com")
    token_b = client.post("/auth/login", json={"email": "b@example.com", "password": STRONG_PASSWORD}).json()["access_token"]
    me_b = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert me_b.json()["email"] == "b@example.com"
    assert me_a.json()["id"] != me_b.json()["id"]


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Short Password",
            "email": "short-password@example.com",
            "password": "123456",
        },
    )
    assert response.status_code == 422


def test_new_passwords_use_argon2id(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Argon User",
            "email": "argon@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    assert response.status_code == 201

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "argon@example.com").one()
        assert user.password_hash.startswith("$argon2id$")
    finally:
        db.close()


def test_refresh_token_is_stored_as_fingerprint(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Fingerprint User",
            "email": "fingerprint@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    assert response.status_code == 201
    _verify_user("fingerprint@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "fingerprint@example.com", "password": STRONG_PASSWORD},
    )
    refresh_token = login_resp.json()["refresh_token"]

    db = TestingSessionLocal()
    try:
        session = db.query(UserSession).one()
        assert session.refresh_token_hash != refresh_token
        assert len(session.refresh_token_hash) == 64
    finally:
        db.close()


def test_cors_rejects_unconfigured_origin(client):
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_login_is_rate_limited(client):
    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"email": "limited@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"email": "limited@example.com", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Muitas tentativas. Aguarde um minuto e tente novamente."


def test_refresh_token_reuse_revokes_the_entire_session_family(client):
    client.post(
        "/auth/register",
        json={
            "name": "Reuse User",
            "email": "reuse@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("reuse@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "reuse@example.com", "password": STRONG_PASSWORD},
    )
    first_refresh = login_resp.json()["refresh_token"]
    rotated = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    second_refresh = rotated.json()["refresh_token"]

    replay = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    family_after_replay = client.post("/auth/refresh", json={"refresh_token": second_refresh})

    assert replay.status_code == 401
    assert "reuse" in replay.json()["detail"].lower()
    assert family_after_replay.status_code == 401
    with TestingSessionLocal() as db:
        sessions = db.query(UserSession).all()
        assert sessions
        assert all(not session.is_active for session in sessions)
        assert any(session.revocation_reason == "refresh_token_reuse" for session in sessions)


def test_user_can_export_data_without_authentication_secrets(client):
    client.post(
        "/auth/register",
        json={
            "name": "Export User",
            "email": "export@example.com",
            "password": STRONG_PASSWORD,
            "privacy_accepted": True,
            "ai_data_processing_consent": True,
        },
    )
    _verify_user("export@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "export@example.com", "password": STRONG_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = client.get("/auth/me/export", headers=headers)

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    serialized = response.text
    assert "password_hash" not in serialized
    assert "refresh_token_hash" not in serialized
    assert response.json()["profile"]["email"] == "export@example.com"


def test_account_deletion_requires_password_and_removes_access(client):
    client.post(
        "/auth/register",
        json={
            "name": "Delete User",
            "email": "delete@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    _verify_user("delete@example.com")
    login_resp = client.post(
        "/auth/login",
        json={"email": "delete@example.com", "password": STRONG_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    denied = client.request("DELETE", "/auth/me", json={"password": "wrong"}, headers=headers)
    deleted = client.request("DELETE", "/auth/me", json={"password": STRONG_PASSWORD}, headers=headers)
    after_delete = client.get("/auth/me", headers=headers)

    assert denied.status_code == 401
    assert deleted.status_code == 204
    assert after_delete.status_code == 401


def test_user_can_list_and_revoke_only_their_own_sessions(client):
    client.post(
        "/auth/register",
        json={"name": "Session A", "email": "session-a@example.com", "password": STRONG_PASSWORD},
        headers={"User-Agent": "Mozilla/5.0 Windows Chrome/130.0"},
    )
    _verify_user("session-a@example.com")
    login_a = client.post(
        "/auth/login",
        json={"email": "session-a@example.com", "password": STRONG_PASSWORD},
        headers={"User-Agent": "Mozilla/5.0 Windows Chrome/130.0"},
    )
    client.post(
        "/auth/register",
        json={"name": "Session B", "email": "session-b@example.com", "password": STRONG_PASSWORD},
    )
    _verify_user("session-b@example.com")
    login_b = client.post(
        "/auth/login",
        json={"email": "session-b@example.com", "password": STRONG_PASSWORD},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
    session_a = client.get("/auth/sessions", headers=headers_a).json()[0]

    forbidden = client.request("DELETE", f"/auth/sessions/{session_a['id']}", headers=headers_b)
    revoked = client.request("DELETE", f"/auth/sessions/{session_a['id']}", headers=headers_a)
    remaining = client.get("/auth/sessions", headers=headers_a)

    assert session_a["device_name"] == "Chrome em Windows"
    assert forbidden.status_code == 404
    assert revoked.status_code == 204
    assert remaining.json() == []
