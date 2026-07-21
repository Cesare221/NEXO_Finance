from app.models.audit_event import AuditEvent
from app.models.session import UserSession
from app.models.user import User
from tests.conftest import TestingSessionLocal


STRONG_PASSWORD = "FinSeguro123!"
VALID_AVATAR = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


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
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


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
    response = client.post(
        "/auth/login",
        json={"email": "badpw@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_authenticated(client):
    reg = client.post(
        "/auth/register",
        json={
            "name": "Me User",
            "email": "me@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token = reg.json()["access_token"]
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
    reg = client.post(
        "/auth/register",
        json={
            "name": "Original Name",
            "email": "profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token = reg.json()["access_token"]

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
    reg = client.post(
        "/auth/register",
        json={
            "name": "Profile User",
            "email": "clear-profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token = reg.json()["access_token"]
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
    reg = client.post(
        "/auth/register",
        json={
            "name": "Profile User",
            "email": "invalid-profile@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token = reg.json()["access_token"]
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
    reg = client.post(
        "/auth/register",
        json={
            "name": "Refresh",
            "email": "refresh@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    refresh = reg.json()["refresh_token"]
    response = client.post(
        "/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh


def test_logout(client):
    reg = client.post(
        "/auth/register",
        json={
            "name": "Logout",
            "email": "logout@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    access = reg.json()["access_token"]
    refresh = reg.json()["refresh_token"]
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
    reg_a = client.post(
        "/auth/register",
        json={
            "name": "User A",
            "email": "a@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token_a = reg_a.json()["access_token"]
    me_a = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert me_a.json()["email"] == "a@example.com"
    reg_b = client.post(
        "/auth/register",
        json={
            "name": "User B",
            "email": "b@example.com",
            "password": STRONG_PASSWORD,
        },
    )
    token_b = reg_b.json()["access_token"]
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
    refresh_token = response.json()["refresh_token"]

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
