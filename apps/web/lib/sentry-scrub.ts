import type { ErrorEvent, EventHint } from "@sentry/nextjs";

const SENSITIVE_KEYS = new Set([
  "authorization",
  "cookie",
  "set-cookie",
  "password",
  "token",
  "access_token",
  "refresh_token",
  "challenge_token",
  "totp",
  "mfa_code",
  "recovery_code",
  "email",
  "phone",
  "ip_address",
  "amount",
  "balance",
  "description",
  "chat_message",
  "request_body",
]);

function scrubDict(obj: Record<string, unknown>): Record<string, unknown> {
  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_KEYS.has(key.toLowerCase())) continue;
    if (value && typeof value === "object" && !Array.isArray(value)) {
      cleaned[key] = scrubDict(value as Record<string, unknown>);
    } else if (Array.isArray(value)) {
      cleaned[key] = value.map((item) =>
        item && typeof item === "object"
          ? scrubDict(item as Record<string, unknown>)
          : item
      );
    } else {
      cleaned[key] = value;
    }
  }
  return cleaned;
}

export function scrubEvent(event: ErrorEvent, _hint: EventHint): ErrorEvent | null {
  const scrubbed = { ...event };

  // Scrub request
  if (scrubbed.request) {
    scrubbed.request = { ...scrubbed.request };
    if (scrubbed.request.headers) {
      scrubbed.request.headers = Object.fromEntries(
        Object.entries(scrubbed.request.headers).filter(
          ([k]) => !SENSITIVE_KEYS.has(k.toLowerCase())
        )
      );
    }
    delete scrubbed.request.data;
    delete (scrubbed.request as Record<string, unknown>).cookies;
  }

  // Remove user identity
  delete scrubbed.user;

  // Scrub extra
  if (scrubbed.extra) {
    scrubbed.extra = scrubDict(scrubbed.extra as Record<string, unknown>);
  }

  // Scrub breadcrumbs
  if (scrubbed.breadcrumbs) {
    const bc = scrubbed.breadcrumbs as unknown as Record<string, unknown>;
    if (Array.isArray(bc.values)) {
      bc.values = bc.values.filter((crumb: unknown) => {
        if (!crumb || typeof crumb !== "object") return true;
        const data = (crumb as Record<string, unknown>).data;
        if (!data || typeof data !== "object") return true;
        return !Object.keys(data as Record<string, unknown>).some((k) =>
          SENSITIVE_KEYS.has(k.toLowerCase())
        );
      });
    }
  }

  return scrubbed;
}
