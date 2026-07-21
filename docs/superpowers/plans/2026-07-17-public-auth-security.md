# Fin Public Authentication and Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an accessible end-to-end login, registration, session, protected-route, and logout experience for the public Fin application while hardening the existing FastAPI identity boundary.

**Architecture:** Next.js acts as a same-origin authentication facade and stores FastAPI tokens only in protected cookies. FastAPI remains responsible for credential validation, session rotation, authorization, and user ownership. The facade is the replacement boundary for a later Clerk-backed identity adapter.

**Tech Stack:** Next.js 15 App Router, React 19, FastAPI, SQLAlchemy, JWT, Argon2id/bcrypt, pytest, Node smoke tests.

## Global Constraints

- Never store access or refresh tokens in browser storage.
- Never cache authentication responses or financial API payloads in the service worker.
- Preserve the existing `user_id` authorization filters and ActionProposal confirmation boundary.
- Keep local development functional on `http://localhost:3000` and require secure cookies in production.
- Keep errors generic enough to avoid account enumeration while providing a recovery path.
- The workspace has no project-local Git repository; verification checkpoints replace commit steps.

---

### Task 1: Harden FastAPI Authentication

**Files:**
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/app/core/security.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/schemas/auth.py`
- Modify: `apps/api/app/services/auth_service.py`
- Modify: `apps/api/app/models/session.py`
- Create: `apps/api/app/core/rate_limit.py`
- Create: `apps/api/alembic/versions/f31a8c7d9b02_fingerprint_refresh_tokens.py`
- Test: `apps/api/tests/test_auth.py`

**Interfaces:**
- Produces `fingerprint_token(token: str) -> str` for session persistence and lookup.
- Produces `AuthRateLimiter.check(bucket: str, identity: str, limit: int, window_seconds: int) -> None`.
- Preserves `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, and `/auth/me` response contracts.

- [ ] Add failing tests for 12-character passwords, explicit origins, token fingerprinting, rotation, and rate limits.
- [ ] Run `python -m pytest tests/test_auth.py -q` and confirm failures are caused by the missing hardening.
- [ ] Implement environment validation, Argon2id with bcrypt migration, refresh fingerprints, and bounded throttling.
- [ ] Generate and inspect the Alembic migration.
- [ ] Run `python -m pytest tests/test_auth.py -q` and confirm PASS.

### Task 2: Add the Next.js Authentication Facade

**Files:**
- Create: `apps/web/lib/auth-cookies.ts`
- Create: `apps/web/lib/auth-server.ts`
- Create: `apps/web/app/api/auth/login/route.ts`
- Create: `apps/web/app/api/auth/register/route.ts`
- Create: `apps/web/app/api/auth/session/route.ts`
- Create: `apps/web/app/api/auth/logout/route.ts`
- Create: `apps/web/middleware.ts`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- `setAuthCookies(response, tokens)` writes access and refresh cookies with environment-safe names and flags.
- `clearAuthCookies(response)` expires both cookies.
- `assertSameOrigin(request)` rejects cross-site mutation attempts.
- `/api/auth/session` returns `{ user: { id, name, email } }` or `401`.

- [ ] Add failing smoke assertions for route handlers, cookie flags, origin checks, and protected route matchers.
- [ ] Run `npm test` and confirm the required files and markers fail.
- [ ] Implement the facade and middleware with no browser-readable tokens.
- [ ] Run `npm test` and confirm PASS.

### Task 3: Build Accessible Login and Registration UX

**Files:**
- Create: `apps/web/components/auth-form.tsx`
- Modify: `apps/web/app/login/page.tsx`
- Modify: `apps/web/app/cadastro/page.tsx`
- Modify: `apps/web/app/globals.css`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- `AuthForm({ mode: "login" | "register" })` submits to the same-origin auth facade.
- Form success redirects to a validated same-origin return path or `/dashboard`.
- Form errors render in `role="alert"`; pending submission disables the primary action.

- [ ] Add failing assertions for loading, accessible errors, password visibility, and autocomplete markers.
- [ ] Run `npm test` and confirm RED.
- [ ] Implement the shared form and responsive auth composition.
- [ ] Run `npm test` and confirm PASS.

### Task 4: Add Session Profile and Logout

**Files:**
- Create: `apps/web/components/session-profile.tsx`
- Modify: `apps/web/components/app-shell.tsx`
- Modify: `apps/web/app/globals.css`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- `SessionProfile({ compact?: boolean })` loads `/api/auth/session`, renders the user, and logs out through `/api/auth/logout`.
- Unauthorized session responses redirect to `/login?reason=session-expired`.

- [ ] Add failing assertions for session loading, logout, and expired-session recovery.
- [ ] Run `npm test` and confirm RED.
- [ ] Implement the profile component in desktop and mobile shells.
- [ ] Run `npm test` and confirm PASS.

### Task 5: Add Security Headers and Complete Verification

**Files:**
- Modify: `apps/web/next.config.ts`
- Modify: `apps/web/README.md` or root `README.md`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Next.js returns CSP, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, and frame protection for application routes.

- [ ] Add failing assertions for required headers and service-worker cache exclusions.
- [ ] Run `npm test` and confirm RED.
- [ ] Implement headers and document environment variables and the managed-provider activation path.
- [ ] Run `npm test`, `npm run build`, `node --check public/sw.js`, and `python -m pytest tests/ -q`.
- [ ] Run `graphify update .` and verify desktop/mobile login, logout, protected redirects, CSS loading, and browser console errors.
