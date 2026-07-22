# Production Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-grade e-mail verification, password recovery, and TOTP MFA to the existing Nexo authentication system.

**Architecture:** Preserve the current FastAPI JWT and rotated-session model. Add purpose-specific token and MFA tables, focused account-security and mail services, matching Next.js BFF routes, and explicit UI states; raw one-time tokens and MFA challenges never enter persistent browser storage.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, PyJWT, Argon2, `cryptography`, `pyotp`, HTTPX, Resend HTTP API, Next.js 15, React 19, TypeScript, `qrcode`.

## Global Constraints

- Production topology is Vercel web plus Railway API, PostgreSQL, and Redis.
- Resend is the only outbound e-mail provider for public v1.
- MFA is RFC 6238 TOTP with ten single-use recovery codes; SMS is not supported.
- Store only SHA-256 fingerprints of e-mail/reset/challenge tokens and Argon2 hashes of recovery codes.
- Encrypt TOTP secrets with a dedicated versioned Fernet key that is not `SECRET_KEY`.
- Password recovery revokes every active refresh-token family and invalidates current access tokens through `token_version`.
- Financial routes require verified e-mail in production; account security, export, deletion, and logout remain available to restricted users.
- Never log passwords, raw tokens, TOTP secrets, MFA codes, recovery codes, e-mail links, or financial payloads.
- Existing non-production users are migrated as verified; new registrations start unverified.

---

### Task 1: Security Dependencies And Runtime Configuration

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/.env.example`
- Modify: `apps/api/tests/test_config.py`
- Modify: `apps/api/uv.lock`
- Modify: `apps/api/requirements.lock`
- Modify: `apps/api/requirements-dev.lock`
- Modify: `apps/web/package.json`
- Modify: `apps/web/package-lock.json`

**Interfaces:**
- Produces: `Settings.mail_provider`, `resend_api_key`, `email_from`, `public_web_url`, `mfa_encryption_keys`, `mfa_active_key_version`, and token TTL settings.
- Produces: Python imports `Fernet` and `pyotp`; web import `QRCode.toDataURL(uri)`.

- [ ] **Step 1: Add failing production configuration tests**

```python
def test_production_requires_resend_and_mfa_keys(monkeypatch):
    config = production_settings(
        mail_provider="resend",
        resend_api_key=None,
        email_from="Nexo <no-reply@nexo.example>",
        public_web_url="https://app.nexo.example",
        mfa_encryption_keys="",
        mfa_active_key_version="v1",
    )
    with pytest.raises(RuntimeError, match="RESEND_API_KEY"):
        config.validate_runtime()


def test_production_rejects_non_https_public_web_url():
    config = production_settings(public_web_url="http://app.nexo.example")
    with pytest.raises(RuntimeError, match="PUBLIC_WEB_URL"):
        config.validate_runtime()
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_config.py -q`

Expected: FAIL because the new settings do not exist.

- [ ] **Step 3: Add exact configuration fields and validation**

```python
mail_provider: str = "console"
resend_api_key: str | None = None
email_from: str = "Nexo <no-reply@example.com>"
public_web_url: str = "http://localhost:3000"
email_verification_ttl_minutes: int = 30
password_reset_ttl_minutes: int = 20
mfa_challenge_ttl_minutes: int = 5
mfa_encryption_keys: str = ""
mfa_active_key_version: str = "v1"

@property
def mfa_keyring(self) -> dict[str, str]:
    return dict(item.split(":", 1) for item in self.mfa_encryption_keys.split(",") if ":" in item)
```

Production validation must require `mail_provider == "resend"`, a non-empty Resend key, HTTPS `public_web_url`, an explicit sender, and an active MFA key present in `mfa_keyring`. Test/development may use `mail_provider="console"` and a test key injected by fixtures.

- [ ] **Step 4: Add and lock dependencies**

Add `cryptography>=46.0`, `pyotp>=2.9` to API dependencies and `qrcode>=1.5.4`, `@types/qrcode>=1.5.5` to web dependencies. Run:

```powershell
cd apps/api
uv lock
uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.lock
uv export --locked --extra dev --no-emit-project --format requirements-txt --output-file requirements-dev.lock
uv sync --locked --extra dev
cd ../web
npm install
```

- [ ] **Step 5: Run configuration tests and dependency audits**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_config.py -q; .\.venv\Scripts\python.exe -m pip_audit -r requirements.lock`

Run: `cd apps/web; npm audit --audit-level=high`

Expected: tests PASS and both audits report no actionable high-severity vulnerability.

- [ ] **Step 6: Commit the dependency and configuration foundation**

```powershell
git add apps/api/pyproject.toml apps/api/uv.lock apps/api/requirements.lock apps/api/requirements-dev.lock apps/api/app/core/config.py apps/api/.env.example apps/api/tests/test_config.py apps/web/package.json apps/web/package-lock.json
git commit -m "feat: add production identity configuration"
```

### Task 2: Identity Persistence And Migration

**Files:**
- Create: `apps/api/app/models/account_action_token.py`
- Create: `apps/api/app/models/mfa_method.py`
- Create: `apps/api/app/models/mfa_recovery_code.py`
- Create: `apps/api/app/models/mfa_challenge.py`
- Modify: `apps/api/app/models/user.py`
- Modify: `apps/api/app/models/__init__.py`
- Create: `apps/api/alembic/versions/e3b7a12c9d40_add_account_verification_and_mfa.py`
- Create: `apps/api/tests/test_identity_migration.py`

**Interfaces:**
- Produces: `AccountActionToken`, `MfaMethod`, `MfaRecoveryCode`, `MfaChallenge` SQLAlchemy models.
- Produces: `User.email_verified_at: datetime | None` and `User.token_version: int`.

- [ ] **Step 1: Write model and migration tests**

```python
def test_identity_tables_are_registered():
    assert "account_action_tokens" in Base.metadata.tables
    assert "mfa_methods" in Base.metadata.tables
    assert "mfa_recovery_codes" in Base.metadata.tables
    assert "mfa_challenges" in Base.metadata.tables


def test_user_defaults_token_version(db):
    user = User(name="A", email="a@example.com", password_hash="hash")
    db.add(user)
    db.commit()
    assert user.token_version == 0
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_identity_migration.py -q`

Expected: FAIL on missing models/columns.

- [ ] **Step 3: Implement focused SQLAlchemy models**

Use these required columns:

```python
class AccountActionToken(Base):
    __tablename__ = "account_action_tokens"
    id: Mapped[int]
    user_id: Mapped[int]
    purpose: Mapped[str]  # verify_email | reset_password
    token_hash: Mapped[str]  # String(64), unique, indexed
    request_ip_hash: Mapped[str | None]
    expires_at: Mapped[datetime]
    consumed_at: Mapped[datetime | None]
    created_at: Mapped[datetime]

class MfaMethod(Base):
    __tablename__ = "mfa_methods"
    id: Mapped[int]
    user_id: Mapped[int]  # unique
    secret_ciphertext: Mapped[str]
    key_version: Mapped[str]
    activated_at: Mapped[datetime | None]
    disabled_at: Mapped[datetime | None]

class MfaRecoveryCode(Base):
    __tablename__ = "mfa_recovery_codes"
    id: Mapped[int]
    method_id: Mapped[int]
    code_hash: Mapped[str]
    consumed_at: Mapped[datetime | None]

class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"
    id: Mapped[int]
    user_id: Mapped[int]
    challenge_hash: Mapped[str]  # String(64), unique, indexed
    expires_at: Mapped[datetime]
    attempts: Mapped[int]
    consumed_at: Mapped[datetime | None]
```

All user/method foreign keys use `ondelete="CASCADE"`. Add bounded string lengths, timezone-aware timestamps, indexes on user/purpose/expiry, and relationships only where navigation is used.

- [ ] **Step 4: Write the additive Alembic migration**

Migration `down_revision` is `c91d4e7a2f10`. Add `email_verified_at` and non-null `token_version` with server default `0`, create all four tables, and execute:

```python
op.execute("UPDATE users SET email_verified_at = NOW()")
```

This preserves existing local accounts. New rows receive no server default for `email_verified_at`.

- [ ] **Step 5: Validate the migration and models**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m alembic heads; .\.venv\Scripts\python.exe -m alembic upgrade head; .\.venv\Scripts\python.exe -m pytest tests/test_identity_migration.py -q`

Expected: one head `e3b7a12c9d40` and tests PASS.

- [ ] **Step 6: Commit persistence**

```powershell
git add apps/api/app/models apps/api/alembic/versions/e3b7a12c9d40_add_account_verification_and_mfa.py apps/api/tests/test_identity_migration.py
git commit -m "feat: persist account verification and mfa"
```

### Task 3: One-Time Tokens, Encryption, And Resend Adapter

**Files:**
- Create: `apps/api/app/services/account_token_service.py`
- Create: `apps/api/app/services/mfa_crypto.py`
- Create: `apps/api/app/services/mail_service.py`
- Create: `apps/api/tests/test_account_token_service.py`
- Create: `apps/api/tests/test_mfa_crypto.py`
- Create: `apps/api/tests/test_mail_service.py`

**Interfaces:**
- Produces: `issue_account_token(db, user_id, purpose, ttl, ip_hash) -> str`.
- Produces: `consume_account_token(db, raw_token, purpose) -> User`.
- Produces: `encrypt_totp_secret(secret) -> tuple[str, str]` and `decrypt_totp_secret(ciphertext, version) -> str`.
- Produces: `MailService.send_verification(user, raw_token)` and `send_password_reset(user, raw_token)`.

- [ ] **Step 1: Write failing unit tests for token lifecycle**

```python
def test_issuing_second_token_invalidates_first(db, user):
    first = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), "ip")
    second = issue_account_token(db, user.id, "verify_email", timedelta(minutes=30), "ip")
    with pytest.raises(AccountTokenError):
        consume_account_token(db, first, "verify_email")
    assert consume_account_token(db, second, "verify_email").id == user.id


def test_token_is_single_use(db, user):
    raw = issue_account_token(db, user.id, "reset_password", timedelta(minutes=20), None)
    consume_account_token(db, raw, "reset_password")
    with pytest.raises(AccountTokenError):
        consume_account_token(db, raw, "reset_password")
```

- [ ] **Step 2: Write failing crypto and mail tests**

```python
def test_totp_secret_round_trip(settings_with_keyring):
    ciphertext, version = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
    assert version == "v1"
    assert decrypt_totp_secret(ciphertext, version) == "JBSWY3DPEHPK3PXP"


def test_resend_payload_contains_only_expected_fields(httpx_mock, user):
    send_verification_email(user, "raw-token")
    payload = httpx_mock.get_request().json()
    assert payload["from"] == settings.email_from
    assert "raw-token" in payload["html"]
    assert "password_hash" not in str(payload)
```

- [ ] **Step 3: Run focused tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_account_token_service.py tests/test_mfa_crypto.py tests/test_mail_service.py -q`

- [ ] **Step 4: Implement cryptographic token lifecycle**

```python
def generate_secret() -> str:
    return secrets.token_urlsafe(32)

def token_fingerprint(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
```

`issue_account_token` atomically consumes active tokens with the same user/purpose, stores only the fingerprint, commits, and returns the raw token. `consume_account_token` locks the row with `FOR UPDATE`, checks purpose/expiry/consumption, marks it consumed, and returns the user.

- [ ] **Step 5: Implement versioned Fernet encryption**

Resolve the active key from `settings.mfa_keyring`, use `Fernet.encrypt`, and require the stored key version for decryption. Raise `MfaCryptoError` for missing versions or invalid ciphertext without including ciphertext in the message.

- [ ] **Step 6: Implement the Resend HTTP adapter**

POST to `https://api.resend.com/emails` with `Authorization: Bearer`, `Content-Type: application/json`, a configured HTTPX timeout, and exact `from`, `to`, `subject`, and HTML/text bodies. The console adapter records no raw token in production logs. Tests inject a recording adapter through `get_mail_service()`.

- [ ] **Step 7: Run focused tests**

Expected: all token, crypto, and mail tests PASS.

- [ ] **Step 8: Commit services**

```powershell
git add apps/api/app/services/account_token_service.py apps/api/app/services/mfa_crypto.py apps/api/app/services/mail_service.py apps/api/tests/test_account_token_service.py apps/api/tests/test_mfa_crypto.py apps/api/tests/test_mail_service.py
git commit -m "feat: add secure account token and mail services"
```

### Task 4: E-mail Verification And Password Recovery API

**Files:**
- Create: `apps/api/app/schemas/account_security.py`
- Create: `apps/api/app/services/account_security_service.py`
- Create: `apps/api/app/api/account_security.py`
- Modify: `apps/api/app/api/auth.py`
- Modify: `apps/api/app/services/auth_service.py`
- Modify: `apps/api/app/core/security.py`
- Modify: `apps/api/app/api/deps.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_account_security.py`
- Modify: `apps/api/tests/test_auth.py`

**Interfaces:**
- Produces endpoints `POST /auth/email-verification/request`, `POST /auth/email-verification/confirm`, `POST /auth/password-reset/request`, `POST /auth/password-reset/confirm`.
- Produces dependency `get_verified_user(current_user) -> User`.
- Produces JWT claim `ver` matching `User.token_version`.
- Produces registration response `RegistrationResponse(status="verification_required", email=user.email)` without access or refresh tokens.

- [ ] **Step 1: Write failing API integration tests**

Cover registration as unverified, neutral reset response for existing/missing accounts, single-use verification/reset links, expiry, wrong purpose, session revocation after reset, and denial of `/financial/dashboard` to unverified users in production mode.

```python
def test_password_reset_is_enumeration_resistant(client, mail_recorder):
    existing = client.post("/auth/password-reset/request", json={"email": "known@example.com"})
    missing = client.post("/auth/password-reset/request", json={"email": "missing@example.com"})
    assert existing.status_code == missing.status_code == 202
    assert existing.json() == missing.json()
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_account_security.py tests/test_auth.py -q`

- [ ] **Step 3: Add exact schemas and service methods**

Schemas:

```python
class EmailRequest(BaseModel):
    email: EmailStr

class TokenConfirmation(BaseModel):
    token: str = Field(min_length=32, max_length=256)

class PasswordResetConfirmation(TokenConfirmation):
    new_password: str = Field(min_length=12, max_length=128)

class RegistrationResponse(BaseModel):
    status: Literal["verification_required"] = "verification_required"
    email: EmailStr
```

Service methods: `request_email_verification`, `confirm_email_verification`, `request_password_reset`, and `confirm_password_reset`. Reset increments `token_version`, revokes all sessions with reason `password_reset`, consumes outstanding reset tokens, and writes `security.password_reset` audit metadata without secrets.

- [ ] **Step 4: Version access and refresh tokens**

Change token creators to require `token_version` and add claim `ver`. `get_current_user` loads the user and rejects a claim whose integer value differs from `user.token_version`. Refresh loads and compares the same user before rotating.

- [ ] **Step 5: Restrict financial dependencies in production**

Add `get_verified_user` and replace `Depends(get_current_user)` with it for financial and assistant routes. In non-production tests/development, existing migrated accounts remain verified. Export, deletion, sessions, verification, logout, and profile endpoints use `get_current_user`.

- [ ] **Step 6: Register routes and rate limits**

Use separate Redis buckets for verification request/confirm and reset request/confirm. Requests are bounded per minute and per day using hashed e-mail plus trusted client identity. Public responses do not disclose account existence.

- [ ] **Step 7: Run API identity tests**

Expected: account-security and existing auth tests PASS.

- [ ] **Step 8: Commit verification and recovery**

```powershell
git add apps/api/app/api apps/api/app/core/security.py apps/api/app/services apps/api/app/schemas/account_security.py apps/api/tests/test_account_security.py apps/api/tests/test_auth.py
git commit -m "feat: add email verification and password recovery"
```

### Task 5: TOTP MFA Service And Login Challenge

**Files:**
- Create: `apps/api/app/services/mfa_service.py`
- Modify: `apps/api/app/services/auth_service.py`
- Modify: `apps/api/app/api/account_security.py`
- Modify: `apps/api/app/schemas/account_security.py`
- Modify: `apps/api/app/schemas/auth.py`
- Modify: `apps/api/app/api/auth.py`
- Create: `apps/api/tests/test_mfa.py`
- Modify: `apps/api/tests/test_auth.py`

**Interfaces:**
- Produces: `start_totp_enrollment`, `confirm_totp_enrollment`, `complete_mfa_challenge`, `regenerate_recovery_codes`, and `disable_totp`.
- Produces login response status `authenticated | mfa_required | email_verification_required`.
- Produces endpoints under `/auth/mfa` for status, enrollment, confirmation, challenge completion, recovery-code regeneration, and disablement.

- [ ] **Step 1: Write failing TOTP and recovery-code tests**

Cover pending enrollment, valid and invalid windows, activation only after confirmation, ten one-time recovery codes, challenge expiry, maximum attempts, challenge replay, recovery-code consumption, regeneration, disable with password plus code, and session creation only after challenge completion.

```python
def test_login_with_active_mfa_returns_challenge_without_tokens(client, active_mfa_user):
    response = client.post("/auth/login", json={"email": active_mfa_user.email, "password": "ValidPassword123"})
    assert response.status_code == 200
    assert response.json()["status"] == "mfa_required"
    assert "access_token" not in response.json()
    assert response.json()["challenge_token"]
```

The response schema is explicit and rejects impossible status/payload combinations in service tests:

```python
class LoginResponse(BaseModel):
    status: Literal["authenticated", "mfa_required", "email_verification_required"]
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    challenge_token: str | None = None
    email: EmailStr | None = None

@dataclass(frozen=True)
class LoginOutcome:
    status: Literal["authenticated", "mfa_required", "email_verification_required"]
    user: User
    access_token: str | None = None
    refresh_token: str | None = None
    challenge_token: str | None = None
```

- [ ] **Step 2: Run MFA tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_mfa.py -q`

- [ ] **Step 3: Implement TOTP enrollment**

Generate with `pyotp.random_base32()`, encrypt immediately, and return:

```python
EnrollmentResult(
    secret=secret,
    otpauth_uri=pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Nexo"),
)
```

Do not activate until `pyotp.TOTP(secret).verify(code, valid_window=1)` succeeds.

- [ ] **Step 4: Implement recovery codes**

Generate ten uppercase groups from cryptographic randomness, hash each with existing Argon2 `hash_password`, store hashes, and return the plain list once. Verification checks unused rows with `verify_password`, locks the match, and sets `consumed_at` atomically.

- [ ] **Step 5: Implement bounded challenges and login outcome**

After password verification and e-mail verification, active MFA creates a five-minute opaque challenge, stores only its fingerprint, and returns no JWT. Completion locks the challenge, increments attempts before verification, caps attempts at five, consumes the challenge on success, and only then calls the existing session-creation function.

- [ ] **Step 6: Implement step-up operations**

Enrollment, code regeneration, and disablement require current password. Disablement also requires a valid TOTP or unused recovery code, revokes other sessions, increments `token_version`, and records an audit event.

- [ ] **Step 7: Run MFA plus complete API tests**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_mfa.py tests/test_auth.py -q; .\.venv\Scripts\python.exe -m pytest -q`

Expected: focused and full API suites PASS.

- [ ] **Step 8: Commit MFA API**

```powershell
git add apps/api/app/services/mfa_service.py apps/api/app/services/auth_service.py apps/api/app/api apps/api/app/schemas apps/api/tests/test_mfa.py apps/api/tests/test_auth.py
git commit -m "feat: require totp challenges for protected accounts"
```

### Task 6: Next.js BFF Cookies And Account-Security Routes

**Files:**
- Modify: `apps/web/lib/auth-cookies.ts`
- Modify: `apps/web/lib/auth-server.ts`
- Modify: `apps/web/app/api/auth/login/route.ts`
- Modify: `apps/web/app/api/auth/register/route.ts`
- Create: `apps/web/app/api/auth/mfa/challenge/route.ts`
- Create: `apps/web/app/api/auth/mfa/status/route.ts`
- Create: `apps/web/app/api/auth/mfa/enroll/route.ts`
- Create: `apps/web/app/api/auth/mfa/confirm/route.ts`
- Create: `apps/web/app/api/auth/mfa/recovery-codes/route.ts`
- Create: `apps/web/app/api/auth/mfa/route.ts`
- Create: `apps/web/app/api/auth/email-verification/request/route.ts`
- Create: `apps/web/app/api/auth/email-verification/confirm/route.ts`
- Create: `apps/web/app/api/auth/password-reset/request/route.ts`
- Create: `apps/web/app/api/auth/password-reset/confirm/route.ts`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces HttpOnly `MFA_CHALLENGE_COOKIE` with five-minute TTL.
- Produces same-origin BFF contracts consumed by the UI in Task 7.

- [ ] **Step 1: Add failing smoke assertions for all BFF routes and cookie flags**

Assert every mutation calls `validateRequestOrigin`, all provider calls remain server-side, challenge raw value is read only from an HttpOnly cookie, and normal auth cookies are set only for `authenticated` outcomes.

- [ ] **Step 2: Run smoke tests and confirm failure**

Run: `cd apps/web; npm test`

- [ ] **Step 3: Add the temporary challenge cookie**

```typescript
export const MFA_CHALLENGE_COOKIE = `${COOKIE_PREFIX}_mfa_challenge`;

export function setMfaChallengeCookie(response: NextResponse, token: string) {
  response.cookies.set(MFA_CHALLENGE_COOKIE, token, {
    ...baseCookieOptions,
    maxAge: 5 * 60
  });
}
```

Add matching clear behavior. Never return the raw challenge token to React.

- [ ] **Step 4: Adapt registration and login outcomes**

Registration returns `{ status: "verification_required", email }`. Login returns authenticated user with cookies, `{ status: "mfa_required" }` with only the temporary cookie, or `{ status: "email_verification_required", email }` without application cookies.

- [ ] **Step 5: Implement focused BFF proxy routes**

Use `authenticatedBackendRequest` for MFA management and direct `backendRequest` wrappers for public token confirmation/request routes. Preserve API status and `Retry-After`; normalize error messages through `publicAuthError`.

- [ ] **Step 6: Run TypeScript and smoke tests**

Run: `cd apps/web; npx tsc --noEmit; npm test`

Expected: PASS.

- [ ] **Step 7: Commit BFF flows**

```powershell
git add apps/web/lib apps/web/app/api/auth apps/web/tests/smoke.mjs
git commit -m "feat: proxy account security flows through the bff"
```

### Task 7: Verification, Recovery, MFA, And Settings UX

**Files:**
- Modify: `apps/web/components/auth-form.tsx`
- Modify: `apps/web/app/login/page.tsx`
- Create: `apps/web/app/verificar-email/page.tsx`
- Create: `apps/web/app/recuperar-senha/page.tsx`
- Create: `apps/web/app/redefinir-senha/page.tsx`
- Create: `apps/web/app/mfa/page.tsx`
- Create: `apps/web/components/email-verification-form.tsx`
- Create: `apps/web/components/password-recovery-form.tsx`
- Create: `apps/web/components/password-reset-form.tsx`
- Create: `apps/web/components/mfa-challenge-form.tsx`
- Create: `apps/web/components/mfa-settings.tsx`
- Modify: `apps/web/app/configuracoes/page.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Consumes: BFF response status unions from Task 6.
- Produces: accessible public account-security pages and authenticated MFA settings.

- [ ] **Step 1: Add failing UI smoke assertions**

Assert labels, autocomplete values, live regions, disabled/pending states, password requirements, verification resend, forgot-password link, TOTP QR alternative text, manual setup key, recovery-code acknowledgment, and no raw token in local storage.

- [ ] **Step 2: Run smoke tests and confirm failure**

Run: `cd apps/web; npm test`

- [ ] **Step 3: Adapt login and registration navigation**

Registration routes to `` `/verificar-email?email=${encodeURIComponent(email)}` ``. Login routes MFA to `` `/mfa?next=${encodeURIComponent(redirectTo)}` ``, unverified users to verification, and authenticated users to the validated relative `next` path. Add a `Recuperar senha` link below the password field.

- [ ] **Step 4: Implement verification and reset pages**

Pages accept query token only long enough to POST it to their BFF route. Use generic success copy, `aria-live="polite"`, clear pending states, and links back to login. The reset form uses `autocomplete="new-password"` and requires the password twice client-side.

- [ ] **Step 5: Implement the MFA challenge page**

Use one input that accepts six-digit TOTP or formatted recovery code, `inputMode="numeric"` only for TOTP mode, and a segmented mode control. The BFF obtains the challenge from HttpOnly cookie.

- [ ] **Step 6: Implement MFA settings with QR and one-time recovery display**

Generate the QR locally using `QRCode.toDataURL(otpauthUri, { errorCorrectionLevel: "M", margin: 1, width: 224 })`. Also show the manual secret. Recovery codes appear once in a selectable list with a download button and an explicit acknowledgment before dismissal.

- [ ] **Step 7: Validate responsive layout and accessibility**

Check 375 px, 768 px, and desktop. Ensure QR, codes, fields, buttons, errors, and chat panel do not overlap or resize their containers.

- [ ] **Step 8: Run frontend validation**

Run: `cd apps/web; npx tsc --noEmit; npm test; npm run build`

Expected: all commands PASS.

- [ ] **Step 9: Commit identity UX**

```powershell
git add apps/web/app apps/web/components apps/web/tests/smoke.mjs
git commit -m "feat: add verification recovery and mfa experiences"
```

### Task 8: Identity End-To-End Gate

**Files:**
- Create: `apps/api/tests/test_identity_end_to_end.py`
- Modify: `docs/SECURITY_AND_LGPD.md`
- Modify: `docs/DEPLOYMENT.md`

**Interfaces:**
- Consumes: all identity API, BFF, UI, and configuration contracts.
- Produces: release evidence for the identity workstream.

- [ ] **Step 1: Add an end-to-end API test**

The test performs registration, recorded verification delivery, confirmation, login, MFA enrollment/activation, logout, password login challenge, TOTP completion, password-reset delivery, reset, old-session rejection, and new-password login.

- [ ] **Step 2: Run the complete validation matrix**

```powershell
cd apps/api
.\.venv\Scripts\python.exe -m alembic heads
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip_audit -r requirements.lock
cd ../web
npx tsc --noEmit
npm test
npm audit --audit-level=high
npm run build
```

Expected: one migration head, all tests/builds PASS, and no high vulnerability.

- [ ] **Step 3: Update security and deployment documentation**

Document exact token TTLs, MFA recovery procedure, required environment variables, session revocation behavior, operator support boundaries, and the fact that support cannot recover a lost TOTP secret without a valid recovery path.

- [ ] **Step 4: Commit the identity gate**

```powershell
git add apps/api/tests/test_identity_end_to_end.py docs/SECURITY_AND_LGPD.md docs/DEPLOYMENT.md
git commit -m "test: verify production identity lifecycle"
```

## Reference Documentation

- Resend Python and HTTP API: `https://resend.com/docs/send-with-python`
- Resend domain verification: `https://resend.com/docs/dashboard/domains/introduction`
- PyOTP TOTP provisioning: `https://pyauth.github.io/pyotp/`
- Cryptography Fernet: `https://cryptography.io/en/latest/fernet/`
