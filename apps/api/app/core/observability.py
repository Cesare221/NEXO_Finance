"""Privacy-safe Sentry integration and event scrubbing."""
from __future__ import annotations

from typing import Any

import sentry_sdk

from app.core.config import settings

SENSITIVE_KEYS = {
    "authorization", "cookie", "set-cookie", "password", "token", "access_token",
    "refresh_token", "challenge_token", "totp", "mfa_code", "recovery_code",
    "email", "phone", "ip_address", "amount", "balance", "description",
    "chat_message", "request_body",
}

REQUEST_KEYS_TO_REMOVE = {"data", "cookies"}
USER_KEYS_TO_REMOVE = {"email", "ip_address", "username"}


def _scrub_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove sensitive keys from a dict."""
    cleaned: dict[str, Any] = {}
    for key, value in d.items():
        if key.lower() in SENSITIVE_KEYS:
            continue
        if isinstance(value, dict):
            cleaned[key] = _scrub_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [_scrub_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            cleaned[key] = value
    return cleaned


def scrub_sentry_event(event: dict[str, Any], hint: Any) -> dict[str, Any] | None:
    """Remove sensitive data before sending to Sentry.

    Preserves: exception type, stack trace, route, status, release,
    environment, and ``request_id``.  Returns ``None`` only if the
    event is intentionally empty after scrubbing (which should not
    normally happen).
    """
    # Scrub request headers
    if "request" in event:
        request = event["request"]
        if "headers" in request:
            request["headers"] = {
                k: v for k, v in request["headers"].items()
                if k.lower() not in SENSITIVE_KEYS
            }
        # Remove request body entirely — it may contain passwords, amounts, etc.
        request.pop("data", None)
        request.pop("cookies", None)

    # Remove user identity
    if "user" in event:
        user = event["user"]
        scrubbed_user = {k: v for k, v in user.items() if k.lower() not in USER_KEYS_TO_REMOVE}
        if scrubbed_user:
            event["user"] = scrubbed_user
        else:
            event.pop("user", None)

    # Scrub extra context
    if "extra" in event:
        event["extra"] = _scrub_dict(event["extra"])

    # Scrub breadcrumbs — remove any containing request body data
    if "breadcrumbs" in event and "values" in event["breadcrumbs"]:
        clean_breadcrumbs = []
        for crumb in event["breadcrumbs"]["values"]:
            if isinstance(crumb, dict):
                data = crumb.get("data", {})
                if isinstance(data, dict) and any(k.lower() in SENSITIVE_KEYS for k in data):
                    continue
                crumb["data"] = _scrub_dict(data) if isinstance(data, dict) else data
            clean_breadcrumbs.append(crumb)
        event["breadcrumbs"]["values"] = clean_breadcrumbs

    return event


def init_observability() -> None:
    """Initialize Sentry if configured.  No-op when DSN is empty."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.sentry_release or None,
        send_default_pii=False,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        before_send=scrub_sentry_event,
    )
