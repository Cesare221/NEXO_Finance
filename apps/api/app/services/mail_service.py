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
        title = "Confirme seu e-mail"
        preview = "Finalize a criacao da sua conta Nexo."
        message = "Use o botao abaixo para confirmar seu e-mail e liberar o acesso a sua conta."
        caution = "Se voce nao criou uma conta no Nexo, ignore este e-mail."
    else:
        subject = "Redefina sua senha Nexo"
        path = "/reset-password"
        action = "Redefina sua senha"
        title = "Redefinicao de senha"
        preview = "Recebemos uma solicitacao para redefinir sua senha."
        message = "Use o botao abaixo para criar uma nova senha para sua conta."
        caution = "Se voce nao solicitou a redefinicao, ignore este e-mail."

    url = f"{base_url}{path}?token={quote(raw_token, safe='')}"
    safe_url = escape(url, quote=True)
    safe_name = escape(user.name)
    safe_title = escape(title)
    safe_preview = escape(preview)
    safe_message = escape(message)
    safe_caution = escape(caution)
    safe_action = escape(action)
    html = f"""\
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{safe_title}</title>
  </head>
  <body style="margin:0;background:#f5f7fb;color:#172033;font-family:Arial,Helvetica,sans-serif;">
    <span style="display:none;overflow:hidden;max-height:0;color:transparent;opacity:0;">
      {safe_preview}
    </span>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fb;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border:1px solid #e1e7f0;border-radius:12px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px 16px 32px;">
                <div style="font-size:20px;font-weight:700;color:#111827;">Nexo</div>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 28px 32px;">
                <h1 style="margin:0 0 14px 0;font-size:24px;line-height:1.25;color:#111827;">{safe_title}</h1>
                <p style="margin:0 0 18px 0;font-size:16px;line-height:1.55;color:#374151;">Ola, {safe_name}.</p>
                <p style="margin:0 0 24px 0;font-size:16px;line-height:1.55;color:#374151;">{safe_message}</p>
                <p style="margin:0 0 28px 0;">
                  <a href="{safe_url}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;padding:13px 18px;border-radius:8px;">
                    {safe_action}
                  </a>
                </p>
                <p style="margin:0 0 10px 0;font-size:13px;line-height:1.5;color:#6b7280;">Se o botao nao funcionar, copie e cole este link no navegador:</p>
                <p style="margin:0 0 22px 0;font-size:13px;line-height:1.5;word-break:break-all;color:#2563eb;">
                  <a href="{safe_url}" style="color:#2563eb;">{safe_url}</a>
                </p>
                <p style="margin:0;font-size:13px;line-height:1.5;color:#6b7280;">{safe_caution}</p>
              </td>
            </tr>
          </table>
          <p style="margin:18px 0 0 0;font-size:12px;line-height:1.5;color:#8a94a6;">
            Nexo envia apenas mensagens transacionais sobre sua conta.
          </p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
    return {
        "from": settings.email_from,
        "to": [user.email],
        "subject": subject,
        "html": html,
        "text": f"{title}\n\nOla, {user.name}.\n\n{message}\n\n{action}: {url}\n\n{caution}",
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
