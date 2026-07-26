# Task 3 Report: One-Time Tokens, Encryption, And Resend Adapter

## RED Evidence

Command:

```powershell
cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_account_token_service.py tests/test_mfa_crypto.py tests/test_mail_service.py -q
```

Result: RED. Collection stopped with 3 expected `ModuleNotFoundError` errors for `app.services.account_token_service`, `app.services.mfa_crypto`, and `app.services.mail_service`.

## GREEN Evidence

Focused command:

```powershell
cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_account_token_service.py tests/test_mfa_crypto.py tests/test_mail_service.py -q
```

Result: `16 passed, 1 warning in 0.40s`.

Full API command:

```powershell
cd apps/api; .\.venv\Scripts\python.exe -m pytest -q
```

Result: `159 passed, 1 warning in 24.45s`.

Dependency audit command:

```powershell
cd apps/api; .\.venv\Scripts\pip-audit.exe
```

Result: no vulnerabilities found.

## Delivered Files

- `apps/api/app/services/account_token_service.py`
- `apps/api/app/services/mfa_crypto.py`
- `apps/api/app/services/mail_service.py`
- `apps/api/tests/test_account_token_service.py`
- `apps/api/tests/test_mfa_crypto.py`
- `apps/api/tests/test_mail_service.py`

## Self-Review

- Account action tokens use a 32-byte URL-safe secret, persist only its SHA-256 fingerprint, lock the user during issuance and the token during consumption, invalidate active same-purpose tokens, and enforce purpose, expiry, and single use.
- TOTP secrets are encrypted with the active Fernet key version and decrypted only with the stored version. Crypto errors do not include ciphertext.
- Resend requests use a single synchronous HTTPX POST with an explicit timeout, exact message fields, and no retry. Console logging excludes raw tokens.
- `git diff --check` completed without whitespace errors. Commit `d6a410d` contains the six Task 3 service/test files and the initial task report; this expanded evidence remains uncommitted, and existing `graphify-out` changes remain outside the task commit.

## Concerns

- The sole test warning is the existing Starlette deprecation warning about `httpx` use in `fastapi.testclient`; it is unrelated to Task 3.
- Resend delivery is verified with `httpx.MockTransport`; no live e-mail was sent.
