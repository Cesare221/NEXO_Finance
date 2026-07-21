# Fin Public Authentication and Security Design

## Context

Fin will be a public multi-user personal finance product. The FastAPI backend already owns users, password verification, JWT access tokens, rotating refresh sessions, authorization by `user_id`, and audited assistant proposals. The Next.js login and registration screens are currently visual-only and browser code has no secure session boundary.

## Decision

Deliver a same-origin authentication boundary in Next.js now, using the existing FastAPI identity service behind it. The browser never receives refresh tokens and never stores access tokens in `localStorage` or `sessionStorage`. Next.js route handlers exchange credentials with FastAPI and store tokens in `HttpOnly`, `SameSite=Lax`, path-scoped cookies; production cookies are `Secure`.

This boundary is intentionally provider-neutral. A later Clerk integration can replace the FastAPI credential exchange behind the Next.js route handlers while preserving the forms, protected routes, application session endpoint, shell profile, and backend `user_id` ownership model. External provider subject IDs will map to internal Fin users when that migration is activated.

## Authentication Flow

1. Login and registration submit JSON to same-origin `/api/auth/*` route handlers.
2. The route handler validates the request origin, calls FastAPI, and writes access and refresh cookies.
3. Browser navigation to application routes is optimistically protected by Next.js middleware.
4. `/api/auth/session` validates the access token through FastAPI `/auth/me`; on expiration it rotates the refresh token once and retries.
5. Logout revokes the refresh session in FastAPI and expires both cookies.
6. FastAPI remains the secure authorization boundary for every financial object and proposal.

## Backend Hardening

- Production startup rejects the development JWT secret and development database credentials.
- CORS accepts only configured origins; credentials, methods, and headers use explicit allowlists.
- New passwords require at least 12 characters and at most 128 characters.
- Password hashes use Argon2id for new accounts while bcrypt verification remains available for existing hashes and upgrades them after a successful login.
- Refresh tokens are represented in the database by SHA-256 fingerprints rather than reusable plaintext values.
- Access tokens expire after 15 minutes; refresh sessions expire after 7 days and rotate on every use.
- Authentication endpoints use a bounded rate limiter with separate limits for login, registration, and refresh. Deployment documentation requires a shared Redis-backed limiter before horizontal scaling.
- Login errors remain generic and all authentication failures use stable public messages.

## User Experience

- Login and registration provide visible labels, inline validation, loading states, password visibility controls, accessible error announcements, and recovery-oriented copy.
- Successful login returns the user to the originally requested protected route when safe, otherwise `/dashboard`.
- The application shell loads the authenticated profile, shows a skeleton while loading, and exposes a clear logout action.
- Expired sessions redirect to `/login` with a short explanation instead of leaving broken financial screens.
- Touch targets remain at least 44px and all interactions work with keyboard and screen readers.

## Security Headers and PWA

- Next.js sends CSP, frame, referrer, MIME-sniffing, and permissions headers.
- The service worker continues caching only the offline shell and versioned static assets. Authentication responses and financial API data are never cached.
- Sensitive mutations continue using the existing ActionProposal confirmation and AuditEvent flow.

## Testing

- API tests cover password policy, explicit CORS, refresh rotation, token fingerprint storage, throttling, and cross-user isolation.
- Frontend tests cover required route handlers, protected-route middleware, cookie flags, form behavior markers, session profile, and logout.
- Production build, full API suite, service-worker syntax, and browser checks at desktop and narrow mobile widths are release gates.

## Deferred Managed Identity

Clerk remains the recommended managed provider for public launch because it supplies email verification, password recovery, MFA, passkeys, breached-password checks, and session risk controls. Activating it requires project-specific Clerk keys and dashboard configuration. The current phase does not invent or embed those credentials; it prepares the application boundary so the provider can be introduced without rewriting product screens.
