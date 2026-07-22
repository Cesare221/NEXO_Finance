# Task 3 Report: One-Time Tokens, Encryption, And Resend Adapter

## Files

- `apps/api/app/services/account_token_service.py`
- `apps/api/app/services/mfa_crypto.py`
- `apps/api/app/services/mail_service.py`
- `apps/api/tests/test_account_token_service.py`
- `apps/api/tests/test_mfa_crypto.py`
- `apps/api/tests/test_mail_service.py`

## Implementation

- Account-action tokens are generated with `secrets.token_urlsafe(32)` and only their SHA-256 fingerprints are stored.
- Issuing a token consumes outstanding tokens for the same user and purpose in the same synchronous SQLAlchemy transaction.
- Consumption uses `SELECT FOR UPDATE`, validates purpose, expiry, and prior consumption, then marks the token consumed before committing.
- TOTP secrets use Fernet and retain the active key version used for encryption; decryption resolves only that stored version.
- The console adapter logs delivery metadata without raw tokens. The Resend adapter uses synchronous HTTPX, a bounded timeout, one POST attempt, and only the expected payload fields.

## Tests

- Focused service tests: PASS.
- Complete API suite: `159 passed, 1 warning`.
- Dependency audit: completed against `apps/api/requirements.lock` with no vulnerability output.

## Commands

- `cd apps/api; .\\.venv\\Scripts\\python.exe -m pytest tests/test_account_token_service.py tests/test_mfa_crypto.py tests/test_mail_service.py -q`
- `cd apps/api; .\\.venv\\Scripts\\python.exe -m pytest -q`
- `cd apps/api; .\\.venv\\Scripts\\python.exe -m pip_audit -r requirements.lock`
- `graphify update .`

## Residual Risks

- Unit tests use SQLite, where `SELECT FOR UPDATE` is not enforced; a PostgreSQL concurrency integration test remains advisable before release.
- Resend coverage uses HTTPX MockTransport. Production still requires verified Resend credentials, sender domain, and network-level delivery monitoring.
