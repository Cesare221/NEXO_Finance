import logging
from html import escape
from typing import Protocol
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.models.user import User


logger = logging.getLogger(__name__)

RESEND_EMAILS_URL = "https://api.resend.com/emails"
DEFAULT_TIMEOUT_SECONDS = 10.0


class MailService(Protocol):
    def send_verification(self, user: User, raw_token: str) -> None: ...

    def send_password_reset(self, user: User, raw_token: str) -> None: ...


def _email_payload(user: User, raw_token: str, kind: str) -> dict[str, object]:
    base_url = settings.public_web_url.rstrip("/")
    if kind == "verification":
        subject = "Confirme seu e-mail Nexo"
        path = "/verificar-email"
        action = "Confirme seu e-mail"
        message = "Use o link abaixo para confirmar seu e-mail."
    else:
        subject = "Nexo password reset"
        path = "/reset-password"
        action = "Redefina sua senha"
        message = "Use o link abaixo para redefinir sua senha."

    url = f"{base_url}{path}?token={quote(raw_token, safe='')}"
    safe_url = escape(url, quote=True)
    safe_name = escape(user.name)
    return {
        "from": settings.email_from,
        "to": [user.email],
        "subject": subject,
        "html": (
            f"<p>Olá, {safe_name}.</p><p>{message}</p>"
            f'<p><a href="{safe_url}">{action}</a></p>'
        ),
        "text": f"{message}\n\n{action}: {url}",
    }


class ConsoleMailService:
    def send_verification(self, user: User, raw_token: str) -> None:
        self._record_delivery(user, "verification")

    def send_password_reset(self, user: User, raw_token: str) -> None:
        self._record_delivery(user, "password_reset")

    @staticmethod
    def _record_delivery(user: User, kind: str) -> None:
        logger.info("Console e-mail delivery type=%s recipient=%s", kind, user.email)


class ResendMailService:
    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Resend timeout must be positive")
        self._timeout_seconds = timeout_seconds
        self._client = client

    def send_verification(self, user: User, raw_token: str) -> None:
        self._send(_email_payload(user, raw_token, "verification"))

    def send_password_reset(self, user: User, raw_token: str) -> None:
        self._send(_email_payload(user, raw_token, "password_reset"))

    def _send(self, payload: dict[str, object]) -> None:
        if not settings.resend_api_key:
            raise RuntimeError("RESEND_API_KEY is required for Resend delivery")
        headers = {
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        }
        if self._client is not None:
            response = self._client.post(
                RESEND_EMAILS_URL,
                headers=headers,
                json=payload,
                timeout=self._timeout_seconds,
            )
        else:
            with httpx.Client(timeout=httpx.Timeout(self._timeout_seconds)) as client:
                response = client.post(RESEND_EMAILS_URL, headers=headers, json=payload)
        response.raise_for_status()


def get_mail_service() -> MailService:
    if settings.mail_provider == "console":
        return ConsoleMailService()
    if settings.mail_provider == "resend":
        return ResendMailService()
    raise RuntimeError("Unsupported mail provider")
