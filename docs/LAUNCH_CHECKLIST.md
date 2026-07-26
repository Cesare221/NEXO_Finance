# Launch Checklist

## Objective Launch Criteria for Nexo Production Release

All items must be ✅ with evidence attached. No exceptions.

---

## Phase 1: Infrastructure & Platform

### DNS & Domains
- [ ] `app.nexo.example` CNAME → Vercel (HTTPS, HSTS)
- [ ] `api.nexo.example` CNAME → Railway (HTTPS, HSTS)
- [ ] Root domain `nexo.example` → Vercel (if apex)
- [ ] Staging `app-staging.nexo.example` configured
- [ ] Staging `api-staging.nexo.example` configured
- [ ] DNS propagation verified globally (dnschecker.org)

### TLS & Certificates
- [ ] Vercel automatic TLS active for production domain
- [ ] Railway custom domain TLS active
- [ ] HSTS headers present on all responses
- [ ] Certificate transparency logs monitored

### Platform Configuration
- [ ] Vercel project: Root = `apps/web`, Framework = Next.js
- [ ] Vercel: Preview deployments for PRs, Production for main
- [ ] Vercel: Git integration enabled, no auto-production
- [ ] Railway: Dockerfile build, pre-deploy `alembic upgrade head`
- [ ] Railway: `/ready` healthcheck configured
- [ ] Railway: Restart policy ON_FAILURE, max 3 retries
- [ ] Railway: Maintenance cron service deployed (no public port)

---

## Phase 2: Secrets & Environment Variables

### GitHub Environments
- [ ] `staging` environment exists (no protection rules)
- [ ] `production` environment exists (required reviewer: operator)

### GitHub Secrets (per environment)
| Secret | Staging | Production |
|--------|---------|------------|
| `RAILWAY_TOKEN` | ✅ | ✅ |
| `RAILWAY_PROJECT_ID` | ✅ | ✅ |
| `RAILWAY_ENVIRONMENT_ID` | ✅ | ✅ |
| `RAILWAY_SERVICE_ID` | ✅ | ✅ |
| `VERCEL_TOKEN` | ✅ | ✅ |
| `VERCEL_ORG_ID` | ✅ | ✅ |
| `VERCEL_PROJECT_ID` | ✅ | ✅ |
| `SMOKE_EMAIL` | ✅ | ✅ |
| `SMOKE_PASSWORD` | ✅ | ✅ |
| `SMOKE_TOTP_SECRET` | ✅ | ✅ |

### GitHub Variables (per environment)
| Variable | Staging | Production |
|----------|---------|------------|
| `API_URL` | `https://api-staging.nexo.example` | `https://api.nexo.example` |
| `WEB_URL` | `https://staging.nexo.example` | `https://app.nexo.example` |

---

## Phase 3: External Services

### Resend (Email)
- [ ] Domain `nexo.example` verified (SPF/DKIM/DMARC)
- [ ] Sender identity `Nexo <no-reply@nexo.example>` verified
- [ ] Dedicated API key for production
- [ ] Webhook endpoint configured for delivery events
- [ ] Suppression list monitored

### Sentry
- [ ] Project `nexo-api` (Python) with `staging`/`production` environments
- [ ] Project `nexo-web` (Next.js) with `staging`/`production` environments
- [ ] Release naming: Git short SHA (`git rev-parse --short HEAD`)
- [ ] `send_default_pii = false` enforced
- [ ] Scrubbing: cookies, auth headers, email, phone, IP, amounts, tokens, chat content
- [ ] Alert rules configured:
  - [ ] New regression (first occurrence in release)
  - [ ] Error rate spike (5× baseline, 5 min)
  - [ ] Readiness failure (3 consecutive)
  - [ ] Auth abuse spike (>50 401/403/min)
- [ ] Source map upload: `SENTRY_AUTH_TOKEN` scoped to `nexo-web`
- [ ] `SENTRY_AUTH_TOKEN` build-only, never `NEXT_PUBLIC_`

### Railway (Database & Redis)
- [ ] PostgreSQL 17, daily backups, 30/12/12 retention
- [ ] Redis 7, multi-instance (primary + replica)
- [ ] Backup schedule: 03:17 UTC daily
- [ ] Separate staging/production databases
- [ ] Separate Redis instances per environment

### Groq (AI)
- [ ] Production API key with ZDR enabled
- [ ] Separate staging API key
- [ ] Model: `openai/gpt-oss-20b` (or approved)
- [ ] Terms of service reviewed for financial data

---

## Phase 4: Application Configuration

### API (Railway)
| Variable | Value | Verified |
|----------|-------|----------|
| `ENVIRONMENT` | `production` | ☐ |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | ☐ |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | ☐ |
| `SECRET_KEY` | 64+ char random | ☐ |
| `ALLOWED_ORIGINS` | `https://app.nexo.example` | ☐ |
| `ALLOWED_HOSTS` | `api.nexo.example` | ☐ |
| `PUBLIC_WEB_URL` | `https://app.nexo.example` | ☐ |
| `MAIL_PROVIDER` | `resend` | ☐ |
| `RESEND_API_KEY` | `re_...` | ☐ |
| `EMAIL_FROM` | `Nexo <no-reply@nexo.example>` | ☐ |
| `EMAIL_VERIFICATION_TTL_MINUTES` | `30` | ☐ |
| `PASSWORD_RESET_TTL_MINUTES` | `20` | ☐ |
| `MFA_CHALLENGE_TTL_MINUTES` | `5` | ☐ |
| `MFA_ENCRYPTION_KEYS` | `v1:<fernet64>` | ☐ |
| `MFA_ACTIVE_KEY_VERSION` | `v1` | ☐ |
| `SENTRY_DSN` | `https://...@sentry.io/...` | ☐ |
| `SENTRY_ENVIRONMENT` | `production` | ☐ |
| `SENTRY_RELEASE` | `${GITHUB_SHA::8}` | ☐ |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | ☐ |
| `GROQ_API_KEY` | `gsk_...` | ☐ |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | ☐ |
| `FIN_AI_PROVIDER` | `groq` | ☐ |
| `FIN_AI_MODEL` | `openai/gpt-oss-20b` | ☐ |
| `TRUSTED_PROXY_IPS` | Railway LB CIDRs | ☐ |

### Web (Vercel)
| Variable | Value | Verified |
|----------|-------|----------|
| `API_URL` | `https://api.nexo.example` | ☐ |
| `NEXT_PUBLIC_SENTRY_DSN` | `https://...@sentry.io/...` | ☐ |
| `SENTRY_DSN` | `https://...@sentry.io/...` | ☐ |
| `SENTRY_ENVIRONMENT` | `production` | ☐ |
| `SENTRY_RELEASE` | `${GITHUB_SHA::8}` | ☐ |
| `SENTRY_AUTH_TOKEN` | Build only | ☐ |

---

## Phase 5: Functional Validation

### CI Pipeline (All Green)
- [ ] `api-tests` job passes (PostgreSQL + Redis)
- [ ] `web-build` job passes (typecheck, tests, audit, build)
- [ ] `docker` job passes (API + Web images build)
- [ ] `container-security` job passes (Trivy, no CRITICAL)
- [ ] `secret-scan` job passes (no leaks)
- [ ] `check-migration-head` passes (single head)

### Identity Lifecycle
- [ ] Registration → unverified → email sent
- [ ] Email verification link → verified → login works
- [ ] Login → access + refresh tokens issued
- [ ] Refresh rotation works, old revoked
- [ ] Logout revokes refresh token
- [ ] Password reset request (enumeration resistant)
- [ ] Reset link → new password → old sessions revoked
- [ ] MFA enrollment: QR + manual key → TOTP confirm → recovery codes
- [ ] MFA login: challenge → TOTP → tokens
- [ ] MFA login: recovery code → tokens (code consumed)
- [ ] MFA disable: password + TOTP/recovery → disabled
- [ ] MFA recovery code regeneration
- [ ] Account deletion: password confirm → deleted

### Financial Features
- [ ] Create account/category/transaction/card
- [ ] List with filters, pagination
- [ ] Dashboard loads (balance, charts)
- [ ] Demo dataset install/cleanup (explicit consent)
- [ ] Propose → approve → execute flow (Fin AI)
- [ ] Propose → cancel flow

### PWA & Mobile
- [ ] Manifest valid, icons 192/512
- [ ] Service worker registers, caches
- [ ] Install prompt works (Android/iOS)
- [ ] Offline page shows when disconnected
- [ ] Responsive: 375px, 768px, 1440px
- [ ] No layout shift on load

### Security
- [ ] CSP header present (no `unsafe-inline` scripts)
- [ ] HSTS header present (max-age=31536000)
- [ ] Cookies: Secure, HttpOnly, SameSite=Lax
- [ ] No sensitive data in logs (Sentry scrubber verified)
- [ ] Rate limiting: auth endpoints bucketed
- [ ] CORS: explicit origins, no wildcard
- [ ] X-Frame-Options: DENY
- [ ] Referrer-Policy: strict-origin-when-cross-origin

---

## Phase 6: Operational Readiness

### Monitoring & Alerts
- [ ] Sentry alerts firing in test (trigger synthetic error)
- [ ] Railway healthcheck `/ready` alerting
- [ ] Uptime monitor (external) on `/health`
- [ ] Log aggregation working (Railway + Vercel)
- [ ] Dashboard with key metrics (error rate, latency, auth success)

### Incident Response
- [ ] Runbook: `docs/INCIDENT_RESPONSE.md` accessible
- [ ] On-call rotation defined (primary/secondary)
- [ ] Escalation path documented
- [ ] Communication channels: Slack, email, status page
- [ ] Post-incident review template ready

### Backup & Recovery
- [ ] Railway daily backups enabled (30/12/12)
- [ ] Weekly restore drill completed (evidence captured)
- [ ] Verifier script tested against restored DB
- [ ] Smoke tests pass against restored DB
- [ ] Cross-region DR documented

### Data Retention & Privacy
- [ ] `DATA_RETENTION.md` documented
- [ ] `SECURITY_AND_LGPD.md` updated with operator details
- [ ] LGPD operator, DPO, contact filled
- [ ] Subprocessor list: Railway, Vercel, Resend, Sentry, Groq
- [ ] Data export endpoint tested
- [ ] Account deletion tested

### Legal & Compliance
- [ ] Terms of Service published
- [ ] Privacy Policy published (LGPD compliant)
- [ ] Cookie consent banner (if applicable)
- [ ] Operator identification in footer
- [ ] DPO contact in footer
- [ ] LGPD authority contact in footer

---

## Phase 7: Staging Rehearsal (Must Pass Before Production)

Deploy exact candidate SHA to staging:

- [ ] `gh workflow run deploy.yml -f environment=staging -f git_sha=<SHA>`
- [ ] Deployment succeeds (API + Web)
- [ ] Custom domains resolve with HTTPS
- [ ] Smoke tests pass (public + authenticated)
- [ ] Identity lifecycle works end-to-end
- [ ] Resend emails delivered (check inbox + spam)
- [ ] MFA enrollment/challenge/recovery works
- [ ] Sentry test event appears in `staging` environment
- [ ] Sentry alert rules fire (trigger test)
- [ ] Financial dashboard loads with real data
- [ ] PWA installs on Android/iOS
- [ ] Mobile layouts verified
- [ ] Backup restore drill completed this week

---

## Phase 8: Production Deployment

- [ ] All Phase 1-7 items ✅
- [ ] Operator approval recorded (GitHub review)
- [ ] `gh workflow run deploy.yml -f environment=production -f git_sha=<SHA>`
- [ ] Deployment succeeds
- [ ] Post-deploy smoke tests pass
- [ ] Sentry `production` environment receiving events
- [ ] Alert rules active in production
- [ ] Status page updated: "Operational"
- [ ] Launch announcement sent (if applicable)

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Release Engineer | | | |
| Security Reviewer | | | |
| DPO / Privacy Officer | | | |
| Operator / Legal Entity | | | |

---

## Evidence Attachments (Required)

| # | Evidence | Location |
|---|----------|----------|
| 1 | Vercel production domain config screenshot | |
| 2 | Railway production domain config screenshot | |
| 3 | Resend domain verification screenshot | |
| 4 | Sentry projects + alert rules screenshots | |
| 5 | GitHub Environments + Secrets configuration | |
| 6 | CI pipeline full green run (link) | |
| 7 | Staging deploy run (link) | |
| 8 | Staging smoke test output (JSON) | |
| 9 | Backup restore drill evidence (this week) | |
| 10 | Production deploy run (link) | |
| 11 | Production smoke test output (JSON) | |
| 12 | Sentry production event screenshot | |
| 13 | Operator/DPO/LGPD fields filled | |
| 13 | Signed launch approval | |