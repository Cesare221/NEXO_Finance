import logging
import json

import httpx
import pytest

from app.core.config import settings
from app.models.user import User
from app.services.mail_service import ConsoleMailService, ResendMailService, get_mail_service


@pytest.fixture()
def user():
    return User(
        id=7,
        name="Mail User",
        email="mail@example.com",
        password_hash="sensitive-password-hash",
    )


@pytest.fixture()
def httpx_mock():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(202, json={"id": "email_123"})

    class Mock:
        def client(self):
            return httpx.Client(transport=httpx.MockTransport(handler))

        def get_request(self):
            assert len(requests) == 1
            return requests[0]

    return Mock()


def test_resend_payload_contains_only_expected_fields(httpx_mock, user, monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key")
    monkeypatch.setattr(settings, "email_from", "Nexo <no-reply@nexo.example>")
    monkeypatch.setattr(settings, "public_web_url", "https://app.nexo.example")
    service = ResendMailService(client=httpx_mock.client(), timeout_seconds=2.5)

    service.send_verification(user, "raw-token")

    request = httpx_mock.get_request()
    payload = json.loads(request.content)
    assert request.url == "https://api.resend.com/emails"
    assert request.headers["authorization"] == "Bearer re_test_key"
    assert request.headers["content-type"] == "application/json"
    assert set(payload) == {"from", "to", "subject", "html", "text"}
    assert payload["from"] == settings.email_from
    assert payload["to"] == [user.email]
    assert "raw-token" in payload["html"]
    assert "raw-token" in payload["text"]
    assert "password_hash" not in str(payload)
    assert user.password_hash not in str(payload)


def test_resend_password_reset_uses_reset_copy(httpx_mock, user, monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test_key")
    monkeypatch.setattr(settings, "public_web_url", "https://app.nexo.example")
    service = ResendMailService(client=httpx_mock.client())

    service.send_password_reset(user, "raw-token")

    payload = json.loads(httpx_mock.get_request().content)
    assert "password" in payload["subject"].lower()
    assert "/reset-password?token=raw-token" in payload["html"]


def test_console_adapter_never_logs_raw_tokens(user, caplog):
    caplog.set_level(logging.INFO)

    ConsoleMailService().send_verification(user, "raw-token")

    assert "raw-token" not in caplog.text


def test_get_mail_service_selects_console_for_development(monkeypatch):
    monkeypatch.setattr(settings, "mail_provider", "console")

    assert isinstance(get_mail_service(), ConsoleMailService)


def test_resend_uses_the_configured_timeout_without_retrying(user, monkeypatch):
    attempts = 0
    observed_timeout = None

    def handler(request):
        nonlocal attempts, observed_timeout
        attempts += 1
        observed_timeout = request.extensions["timeout"]
        raise httpx.ConnectTimeout("timed out", request=request)

    monkeypatch.setattr(settings, "resend_api_key", "re_test_key")
    service = ResendMailService(
        client=httpx.Client(transport=httpx.MockTransport(handler)), timeout_seconds=2.5
    )

    with pytest.raises(httpx.ConnectTimeout):
        service.send_verification(user, "raw-token")

    assert attempts == 1
    assert observed_timeout["connect"] == 2.5
