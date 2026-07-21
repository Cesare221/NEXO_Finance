# Nexo Production Hosting And Security Design

**Date:** 2026-07-21  
**Status:** Approved design  
**Target:** Public v1 deployment

## Context

Nexo currently runs as a Next.js web application backed by a FastAPI API, PostgreSQL, and optional Redis. The application already has authenticated sessions, refresh-token rotation, financial data isolation, LGPD controls, a Groq-backed Fin assistant with explicit consent, health checks, migrations, CI, and local production builds.

This design completes the application-level work required for a public deployment using Vercel and Railway. Platform accounts, DNS ownership, legal operator details, production secrets, and third-party commercial agreements remain external release prerequisites.

## Goals

- Deploy the Next.js application on Vercel and the FastAPI API on Railway.
- Use managed PostgreSQL and Redis in the Railway production environment.
- Verify user e-mail addresses and provide secure password recovery through Resend.
- Add TOTP multi-factor authentication with one-time recovery codes.
- Add privacy-safe frontend and backend error monitoring through Sentry.
- Make releases reproducible, observable, reversible, and testable.
- Preserve the existing authentication and financial ownership model.
- Satisfy the technical controls needed to support the Nexo LGPD program.

## Non-Goals

- Replacing the existing authentication system with Clerk, Auth0, or Supabase Auth.
- SMS-based MFA.
- Automatic execution of financial transactions without user approval.
- Storing production secrets in the repository.
- Claiming legal certification, regulatory approval, or absolute security.
- Provisioning paid platform accounts or purchasing a domain on behalf of the operator.

## Chosen Architecture

### Web

- `apps/web` deploys to Vercel.
- The browser communicates only with same-origin Next.js BFF routes.
- `API_URL` remains a server-only Vercel variable.
- Production cookies use the `__Host-nexo` prefix and are `Secure`, `HttpOnly`, and `SameSite=Strict`.
- Preview deployments use a separate staging API and staging database.

### API And Data

- `apps/api` deploys as a Docker service on Railway.
- Railway provides managed PostgreSQL and Redis services.
- A Railway pre-deploy command runs `alembic upgrade head` before new application instances receive traffic.
- `/health` checks the process and `/ready` checks required dependencies.
- The API accepts traffic only from configured hosts and origins.
- Redis is mandatory in production and rate limiting fails closed when it is unavailable.

### External Services

- Resend sends account verification and password recovery messages.
- Sentry receives scrubbed application errors and traces from the web and API.
- Groq remains optional per user and is called only after explicit external-AI consent.

## Authentication Design

### E-mail Verification

1. Registration creates the user with `email_verified_at = null`.
2. The API generates at least 32 cryptographically random bytes.
3. Only a SHA-256 fingerprint of the token is stored with user, purpose, expiry, creation, and consumption timestamps.
4. Resend receives the raw token only as part of a single-use HTTPS link.
5. Verification consumes the token atomically and revokes other outstanding verification tokens for that user.
6. Resending is rate limited by account and network identity.
7. Expired or consumed tokens produce the same user-facing result.
8. Public production access to financial routes requires a verified e-mail. Login may establish a restricted session so the user can verify, resend, export, or delete the account.

### Password Recovery

1. Recovery requests always return the same public response regardless of account existence.
2. Existing accounts receive a single-use token using the same hashing and expiry model as verification.
3. Completing recovery requires the token and a password that satisfies the current password policy.
4. Successful reset increments the user's token version, revokes every refresh-token family, consumes all outstanding reset tokens, and records an audit event.
5. Passwords are never sent by e-mail or logged.

### TOTP MFA

1. Enrolment requires a valid password and a recently authenticated session.
2. The API creates a TOTP secret and returns an `otpauth://` URI once.
3. The secret is encrypted at rest with a dedicated versioned encryption key, separate from `SECRET_KEY`.
4. MFA remains pending until the user submits a valid TOTP code.
5. Activation generates ten recovery codes. Only Argon2 hashes are stored, and the plain codes are shown once.
6. Login with active MFA issues a short-lived challenge instead of application tokens.
7. Completing the challenge with TOTP or one recovery code creates the normal access and refresh tokens.
8. Recovery codes are single use. Regeneration invalidates all previous recovery codes.
9. Disabling MFA requires password confirmation and a valid TOTP or recovery code.
10. Challenge attempts are rate limited, expire quickly, and cannot be reused.

## API And BFF Contracts

The API adds endpoints for:

- requesting and completing e-mail verification;
- requesting and completing password recovery;
- starting, confirming, inspecting, regenerating recovery codes for, and disabling TOTP;
- completing an MFA login challenge.

The web application exposes matching same-origin BFF routes. Raw provider credentials, encryption keys, database URLs, and API hostnames are never exposed to client JavaScript.

All mutation endpoints use typed request schemas, bounded body sizes, neutral authentication errors where enumeration is possible, CSRF-resistant same-origin cookies, rate limits, and audit events.

## Data Model

New persistence uses separate, purpose-specific tables:

- `account_action_tokens`: token fingerprint, user, purpose, expiry, consumed timestamp, and request metadata hash;
- `mfa_methods`: user, encrypted TOTP secret, encryption-key version, activation timestamp, and disabled timestamp;
- `mfa_recovery_codes`: method, Argon2 hash, creation timestamp, and consumed timestamp;
- `mfa_challenges`: opaque challenge fingerprint, user, expiry, attempt count, and consumed timestamp.

The user record adds `email_verified_at` and `token_version`. Migrations are additive and have a single Alembic head. Existing local users are marked verified during migration to avoid locking out established development accounts; new production registrations require verification.

## Resend Integration

- A focused mail service owns provider calls and template rendering.
- `RESEND_API_KEY`, `EMAIL_FROM`, `PUBLIC_WEB_URL`, and timeout settings are server-only.
- Templates include account verification, password reset, password-changed notification, and MFA-changed notification.
- Messages contain no balances, transaction descriptions, chat content, or authentication secrets other than the intended one-time link.
- Provider failures are retried only when safe and never create duplicate valid tokens.
- Development and tests use an in-memory or recording adapter without network calls.

## Sentry And Logging

- Sentry SDKs are enabled only when a DSN is configured.
- Environment and release identifiers distinguish staging from production.
- `beforeSend` hooks remove cookies, authorization headers, passwords, tokens, e-mail addresses, phone numbers, chat messages, transaction descriptions, financial values, and request bodies from events.
- Session replay is disabled for the public v1 unless a separate privacy review enables masked replay.
- Logs are structured JSON in production and include timestamp, severity, service, environment, release, route template, status, duration, and validated `request_id`.
- Logs do not contain raw IP addresses, access tokens, refresh tokens, MFA codes, e-mail links, provider keys, or financial payloads.
- Sentry errors link to request IDs without duplicating sensitive payloads.

## Deployment And Release Flow

1. Pull requests run API tests, web tests, type checking, production build, migration checks, dependency audits, CodeQL, and Docker image build.
2. Staging deploys first with isolated services and credentials.
3. Railway runs the migration release command and checks `/ready`.
4. Vercel deploys the web application against the staging or production API selected by environment.
5. A smoke script validates health, readiness, registration, verification adapter behavior, login, refresh, MFA challenge, password recovery, and a protected route.
6. Production promotion requires a successful staging smoke run and an explicit platform approval.
7. Rollback redeploys the last healthy application images. Database downgrades are never automatic; incompatible changes require additive corrective migrations.

## Production Configuration

Startup validation fails when production is missing required database, Redis, host, origin, cookie, encryption, Resend, or Sentry settings. Secrets must be distinct between staging and production.

The deployment documentation will define all required variables without real values and will include:

- Vercel project and domain configuration;
- Railway API, PostgreSQL, and Redis configuration;
- Resend domain verification and sender configuration;
- Sentry projects, environments, release identifiers, and alert setup;
- Groq Zero Data Retention requirement when the provider is enabled;
- backup, restore, incident, and secret-rotation procedures.

## Security And LGPD Controls

- Collect only data required for authentication, finance features, security, and user-requested AI processing.
- Keep AI consent separate and revocable.
- Document retention periods for inactive accounts, audit events, expired account tokens, logs, backups, and Sentry events.
- Purge expired verification, reset, and MFA challenge records through a scheduled maintenance command.
- Preserve user export and account deletion behavior, including disclosure of operational retention exceptions.
- Record security-sensitive actions without recording their secrets.
- Maintain a subprocessor inventory for Vercel, Railway, Resend, Sentry, and Groq.
- Require a production privacy notice containing the controller, operator, DPO/contact channel, purposes, legal bases, retention, subprocessors, and data-subject request process.

## Error Handling

- Provider timeouts produce retryable user messages without exposing internals.
- Authentication failures remain deliberately generic.
- E-mail delivery failure does not mark an address verified or a reset complete.
- Redis failure in production denies rate-limited operations and reports dependency failure through readiness.
- Sentry failure never blocks the user request.
- Migration failure prevents the new API release from receiving traffic.

## Testing Strategy

- Unit tests cover token generation, fingerprinting, expiry, consumption, TOTP windows, recovery-code use, encryption, scrubbing, and configuration validation.
- API integration tests cover verification, recovery, MFA enrolment, MFA login, session revocation, authorization boundaries, rate limits, and neutral error responses.
- Provider tests mock Resend and Sentry; no test sends real e-mail or telemetry.
- Migration tests upgrade an empty database and the current schema to the single head.
- Web smoke tests cover forms, BFF cookie handling, accessibility labels, loading, success, expiry, and error states.
- CI audits Python and npm dependencies and builds the production Docker image and Next.js bundle.
- A staging runbook verifies DNS, HTTPS, cookies, CORS, e-mail delivery, MFA, password recovery, backups, restore, Sentry alerts, and mobile PWA behavior.

## Rollout

1. Implement and test the application changes locally.
2. Deploy isolated staging infrastructure.
3. Verify Resend DNS and send test messages only to operator-controlled addresses.
4. Exercise the staging security and recovery runbooks.
5. Run a database restore drill.
6. Complete legal text and subprocessor review.
7. Perform an independent penetration test and fix release-blocking findings.
8. Promote the same reviewed release to production.
9. Monitor authentication failures, e-mail delivery, API errors, readiness, and abuse alerts during the initial rollout.

## Acceptance Criteria

- A new user must verify their e-mail before accessing financial features in production.
- Password recovery is single use, time bounded, enumeration resistant, and revokes existing sessions.
- TOTP and one-time recovery codes work through a bounded challenge flow.
- No authentication secret or financial payload reaches logs or Sentry events.
- Production startup rejects incomplete or unsafe configuration.
- CI passes tests, builds, migrations, audits, static analysis, and Docker validation.
- Staging smoke tests and the restore drill pass before production promotion.
- Vercel, Railway, Resend, and Sentry configuration is documented and reproducible.
- The privacy notice and incident contacts contain real operator information before public registration is enabled.

## External Release Prerequisites

The application can prepare and validate contracts for these items but cannot create or approve them without operator access:

- verified production domain and DNS records;
- Vercel, Railway, Resend, and Sentry accounts and project credentials;
- production and staging secrets stored in platform secret managers;
- Groq Zero Data Retention and data-processing terms when Groq is enabled;
- named controller, operator, DPO/contact channel, and approved legal notices;
- backup retention settings and a completed restore drill;
- external penetration-test evidence and an incident-response owner.
