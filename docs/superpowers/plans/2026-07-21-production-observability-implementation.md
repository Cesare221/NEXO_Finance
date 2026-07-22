# Production Observability And Privacy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add privacy-safe Sentry monitoring, structured production logs, retention cleanup, and actionable operational signals to Nexo.

**Architecture:** Initialize observability through isolated adapters that are disabled without configuration. Sanitize events before transport, emit structured request metadata without financial or identity payloads, and run bounded cleanup through a Railway cron command.

**Tech Stack:** Sentry Python SDK 2.x with FastAPI integration, `@sentry/nextjs` 10.x, Python logging, Next.js instrumentation hooks, PostgreSQL, Railway cron.

## Global Constraints

- Sentry is the production error-monitoring provider for both API and web.
- Use `sentry-sdk[fastapi]>=2.66,<3` and `@sentry/nextjs@^10.67.0`.
- `send_default_pii` is always false and session replay remains disabled for public v1.
- Remove cookies, authorization headers, e-mail, phone, raw IP, passwords, tokens, codes, chat content, transaction descriptions, financial values, and request bodies before transport.
- Sentry failure must never block application requests.
- Production logs are JSON and identify requests only through validated `request_id`, route template, release, and environment.
- Expired account tokens and MFA challenges are purged without deleting required financial audit records.
- Staging and production use separate Sentry environments and alert channels.

---

### Task 1: API Sentry Configuration And Event Scrubbing

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/uv.lock`
- Modify: `apps/api/requirements.lock`
- Modify: `apps/api/requirements-dev.lock`
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/.env.example`
- Create: `apps/api/app/core/observability.py`
- Create: `apps/api/tests/test_observability.py`
- Modify: `apps/api/tests/test_config.py`

**Interfaces:**
- Produces: `init_observability() -> None` and `scrub_sentry_event(event, hint) -> dict | None`.
- Produces settings `sentry_dsn`, `sentry_environment`, `sentry_release`, and `sentry_traces_sample_rate`.

- [ ] **Step 1: Write failing scrubber tests**

```python
def test_scrubber_removes_sensitive_request_data():
    event = {
        "request": {
            "headers": {"authorization": "Bearer secret", "cookie": "refresh=secret"},
            "data": {"password": "secret", "amount": "120.00", "description": "Farmacia"},
        },
        "user": {"email": "person@example.com", "ip_address": "127.0.0.1"},
        "extra": {"chat_message": "meu saldo", "request_id": "safe-id"},
    }
    scrubbed = scrub_sentry_event(event, {})
    assert scrubbed["request"]["headers"] == {}
    assert "data" not in scrubbed["request"]
    assert scrubbed.get("user") is None
    assert scrubbed["extra"] == {"request_id": "safe-id"}
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_observability.py tests/test_config.py -q`

- [ ] **Step 3: Add and lock the Sentry dependency**

Add `sentry-sdk[fastapi]>=2.66,<3`, then run `uv lock`, both `uv export` commands, and `uv sync --locked --extra dev` using the same commands as the identity plan.

- [ ] **Step 4: Implement deterministic event scrubbing**

Recursively remove keys matching this case-insensitive denylist:

```python
SENSITIVE_KEYS = {
    "authorization", "cookie", "set-cookie", "password", "token", "access_token",
    "refresh_token", "challenge_token", "totp", "mfa_code", "recovery_code",
    "email", "phone", "ip_address", "amount", "balance", "description",
    "chat_message", "request_body",
}
```

Delete `request.data`, `request.cookies`, user context, breadcrumbs containing request bodies, and denied extras. Preserve exception type, stack trace, route, status, release, environment, and `request_id`.

- [ ] **Step 5: Initialize Sentry only when configured**

```python
def init_observability() -> None:
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
```

Validate sample rate between `0.0` and `1.0`; production requires explicit environment and release when DSN is set.

- [ ] **Step 6: Run tests and audit**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_observability.py tests/test_config.py -q; .\.venv\Scripts\python.exe -m pip_audit -r requirements.lock`

Expected: PASS and no known vulnerability.

- [ ] **Step 7: Commit API monitoring foundation**

```powershell
git add apps/api/pyproject.toml apps/api/uv.lock apps/api/requirements.lock apps/api/requirements-dev.lock apps/api/app/core/config.py apps/api/app/core/observability.py apps/api/.env.example apps/api/tests/test_observability.py apps/api/tests/test_config.py
git commit -m "feat: add privacy-safe api monitoring"
```

### Task 2: Structured Request Logging And Error Correlation

**Files:**
- Create: `apps/api/app/core/logging_config.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/api/health.py`
- Create: `apps/api/tests/test_logging.py`
- Modify: `apps/api/tests/test_health.py`

**Interfaces:**
- Produces: `configure_logging()`, `JsonFormatter`, and middleware-bound request context.
- Produces logs with `timestamp`, `level`, `service`, `environment`, `release`, `request_id`, `method`, `route`, `status`, and `duration_ms`.

- [ ] **Step 1: Write failing formatter and middleware tests**

```python
def test_json_formatter_excludes_sensitive_values():
    record = logging.LogRecord("nexo", logging.INFO, __file__, 1, "request.complete", (), None)
    record.request_id = "9bfa6d7d-3987-45b8-9468-2ed7cd97266a"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == record.request_id
    assert "authorization" not in payload
    assert "body" not in payload
```

Test one successful and one failing request and assert the response and captured error share `X-Request-ID`.

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_logging.py tests/test_health.py -q`

- [ ] **Step 3: Implement JSON logging**

Use UTC ISO-8601 timestamps and a `contextvars.ContextVar` for `request_id`. Log route templates, not raw URLs or query strings. Development keeps human-readable formatting; production uses one JSON object per line.

- [ ] **Step 4: Correlate middleware and Sentry**

Initialize observability once during lifespan startup, set Sentry tag `request_id`, capture unexpected exceptions, log `request.complete` after response creation, and clear request context in `finally`. Do not manually capture expected 4xx errors.

- [ ] **Step 5: Make readiness operationally explicit**

Return only dependency names and states from `/ready`; include PostgreSQL and Redis in production. A failed check returns 503 and logs dependency name, not credentials or connection URLs.

- [ ] **Step 6: Run focused and full API tests**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_logging.py tests/test_health.py -q; .\.venv\Scripts\python.exe -m pytest -q`

- [ ] **Step 7: Commit logging and correlation**

```powershell
git add apps/api/app/core/logging_config.py apps/api/app/main.py apps/api/app/api/health.py apps/api/tests/test_logging.py apps/api/tests/test_health.py
git commit -m "feat: correlate production logs and errors"
```

### Task 3: Next.js Sentry Integration With Client Scrubbing

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`
- Modify: `apps/web/next.config.ts`
- Create: `apps/web/instrumentation.ts`
- Create: `apps/web/instrumentation-client.ts`
- Create: `apps/web/sentry.server.config.ts`
- Create: `apps/web/sentry.edge.config.ts`
- Create: `apps/web/app/global-error.tsx`
- Create: `apps/web/lib/sentry-scrub.ts`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: server, edge, and browser Sentry initialization.
- Produces: `scrubEvent(event: Event) -> Event | null` shared by all web runtimes.

- [ ] **Step 1: Add failing smoke assertions**

Assert `sendDefaultPii: false`, replay integration absence, `beforeSend: scrubEvent`, environment/release fields, server-only auth token behavior, source-map upload config, and an accessible global error fallback.

- [ ] **Step 2: Run smoke test and confirm failure**

Run: `cd apps/web; npm test`

- [ ] **Step 3: Install and audit Sentry**

Run: `cd apps/web; npm install @sentry/nextjs@^10.67.0; npm audit --audit-level=high`

- [ ] **Step 4: Implement shared event scrubbing**

Delete request bodies, cookies, authorization headers, user identity, denied extras, and breadcrumbs containing form or fetch payloads. Preserve stack frames, component names, route, release, environment, and `request_id` response tag.

- [ ] **Step 5: Configure server, edge, and browser runtimes**

Use `SENTRY_DSN` server-side and `NEXT_PUBLIC_SENTRY_DSN` client-side. Set `tracesSampleRate` from validated environment values, `sendDefaultPii: false`, no replay integration, and `enabled: Boolean(dsn)`. `instrumentation.ts` dynamically imports server or edge config based on `NEXT_RUNTIME`.

- [ ] **Step 6: Wrap Next configuration safely**

Use `withSentryConfig(nextConfig, { org, project, authToken, silent: true }, { hideSourceMaps: true, disableLogger: true })`. `SENTRY_AUTH_TOKEN` is build-only and never prefixed `NEXT_PUBLIC_`.

- [ ] **Step 7: Implement global error UX**

Capture the exception in an effect, show a concise Portuguese message, expose a retry button calling `reset()`, and never render the exception message or stack to the user.

- [ ] **Step 8: Run frontend validation**

Run: `cd apps/web; npx tsc --noEmit; npm test; npm audit --audit-level=high; npm run build`

Expected: PASS with no high vulnerability.

- [ ] **Step 9: Commit web monitoring**

```powershell
git add apps/web/package.json apps/web/package-lock.json apps/web/next.config.ts apps/web/instrumentation.ts apps/web/instrumentation-client.ts apps/web/sentry.server.config.ts apps/web/sentry.edge.config.ts apps/web/app/global-error.tsx apps/web/lib/sentry-scrub.ts apps/web/tests/smoke.mjs
git commit -m "feat: add privacy-safe web monitoring"
```

### Task 4: Retention Cleanup And Incident Documentation

**Files:**
- Create: `apps/api/app/maintenance.py`
- Create: `apps/api/tests/test_maintenance.py`
- Create: `apps/api/railway.cron.json`
- Modify: `docs/SECURITY_AND_LGPD.md`
- Create: `docs/INCIDENT_RESPONSE.md`
- Create: `docs/DATA_RETENTION.md`

**Interfaces:**
- Produces command `python -m app.maintenance purge-expired-security-records`.
- Produces Railway daily cron definition and operational runbooks.

- [ ] **Step 1: Write failing cleanup tests**

Create expired, active, and consumed account tokens/challenges. Assert the command removes records older than 30 days, preserves active/unexpired records, never touches audit events, and reports only aggregate counts.

- [ ] **Step 2: Run cleanup tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_maintenance.py -q`

- [ ] **Step 3: Implement an idempotent maintenance CLI**

Use explicit subcommands, one transaction, UTC cutoffs, bounded deletes, and JSON aggregate output:

```json
{"account_action_tokens_deleted": 12, "mfa_challenges_deleted": 4, "status": "ok"}
```

- [ ] **Step 4: Define the Railway cron service**

Use this config as the custom config path for a separate Railway cron service:

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "startCommand": "python -m app.maintenance purge-expired-security-records",
    "cronSchedule": "17 3 * * *",
    "restartPolicyType": "NEVER"
  }
}
```

The cron uses the API image and production database secret but does not expose a public port.

- [ ] **Step 5: Write exact retention and incident runbooks**

Specify 30-day expired security-token retention, configured Sentry retention, Railway log retention, audit retention approved by the operator, backup retention, breach triage roles, evidence preservation, secret rotation, user notification decision path, and LGPD authority/contact escalation.

- [ ] **Step 6: Run maintenance and full regression tests**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_maintenance.py -q; .\.venv\Scripts\python.exe -m pytest -q`

- [ ] **Step 7: Commit cleanup and runbooks**

```powershell
git add apps/api/app/maintenance.py apps/api/tests/test_maintenance.py apps/api/railway.cron.json docs/SECURITY_AND_LGPD.md docs/INCIDENT_RESPONSE.md docs/DATA_RETENTION.md
git commit -m "feat: add security retention and incident operations"
```

### Task 5: Observability Release Gate

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/DEPLOYMENT.md`

**Interfaces:**
- Consumes: API and web observability contracts.
- Produces: CI checks and an operator acceptance checklist.

- [ ] **Step 1: Add CI checks for scrubbing and production builds**

Run focused scrubber tests as named tests, run the complete API suite, and build Next.js once with DSNs unset to prove observability is optional. Do not place real DSNs or auth tokens in workflow YAML.

- [ ] **Step 2: Document Sentry project configuration**

Document separate `nexo-api` and `nexo-web` projects, `staging` and `production` environments, release naming from Git SHA, alert rules for new regression, error-rate spike, readiness failure, and authentication-abuse spike, plus source-map token scoping.

- [ ] **Step 3: Execute the complete observability matrix**

Run API tests/audit and web typecheck/tests/audit/build. Inject a synthetic sanitized exception in staging only, verify arrival, verify no denied fields, and remove the synthetic endpoint or feature flag before production.

- [ ] **Step 4: Commit the release gate**

```powershell
git add .github/workflows/ci.yml docs/DEPLOYMENT.md
git commit -m "ci: enforce production observability gates"
```

## Reference Documentation

- Sentry FastAPI integration: `https://docs.sentry.io/platforms/python/integrations/fastapi/`
- Sentry Next.js manual setup: `https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/`
- Sentry data scrubbing: `https://docs.sentry.io/security-legal-pii/scrubbing/`
- Railway cron jobs: `https://docs.railway.com/reference/cron-jobs`
