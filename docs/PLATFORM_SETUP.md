# Platform Setup Guide

This document describes the exact GitHub secrets, environment variables, and platform configuration required for the Nexo deployment pipeline.

## Required GitHub Environments

Create two GitHub environments in repository settings (Settings → Environments):

| Environment | Protection Rules | Purpose |
|-------------|------------------|---------|
| `staging` | None (auto-approval) | Internal testing, PR validation |
| `production` | **Required reviewers**: at least one operator/owner | Production releases only |

Both environments must have the same secret names (values differ per environment).

## Required GitHub Secrets

### Railway (API)

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `RAILWAY_TOKEN` | Railway CLI token with project deploy scope | Railway → Account → Tokens → Create Token |
| `RAILWAY_PROJECT_ID` | Railway project UUID | Railway project URL: `https://railway.com/project/<PROJECT_ID>` |
| `RAILWAY_ENVIRONMENT_ID` | Environment UUID (staging or production) | Railway environment URL |
| `RAILWAY_SERVICE_ID` | API service UUID within the project | Railway service URL |

### Vercel (Web)

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `VERCEL_TOKEN` | Vercel CLI token (personal or team) | Vercel → Settings → Tokens → Create |
| `VERCEL_ORG_ID` | Vercel organization/team ID | `vercel inspect <deployment>` or API |
| `VERCEL_PROJECT_ID` | Vercel project ID | `vercel inspect <deployment>` or API |

### Smoke Test Credentials

| Secret Name | Description | Notes |
|-------------|-------------|-------|
| `SMOKE_EMAIL` | Pre-registered test user email (MFA enabled) | Create dedicated user in each environment |
| `SMOKE_PASSWORD` | Test user password (12+ chars) | Store securely, rotate periodically |
| `SMOKE_TOTP_SECRET` | TOTP secret for MFA challenge | From user's MFA enrollment QR code |

## GitHub Environment Variables

These are set per environment (Settings → Environments → Variables):

| Variable Name | Staging Value | Production Value |
|---------------|---------------|------------------|
| `API_URL` | `https://api-staging.nexo.example` | `https://api.nexo.example` |
| `WEB_URL` | `https://staging.nexo.example` | `https://app.nexo.example` |

## Railway Configuration

### Project Setup

1. Create Railway project: `nexo-api`
2. Add PostgreSQL service (managed)
3. Add Redis service (managed)
4. Add API service from GitHub repo, Root Directory: `apps/api`

### Environment Variables (per environment)

```
ENVIRONMENT=staging|production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<64+ char random>
ALLOWED_ORIGINS=https://staging.nexo.example,https://app.nexo.example
ALLOWED_HOSTS=api-staging.nexo.example,api.nexo.example
REDIS_URL=${{Redis.REDIS_URL}}
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
FIN_AI_PROVIDER=groq
FIN_AI_MODEL=openai/gpt-oss-20b
FIN_AI_TIMEOUT_SECONDS=12
FIN_AI_MAX_TOOL_ROUNDS=3
FIN_AI_MESSAGES_PER_MINUTE=12
FIN_AI_MESSAGES_PER_DAY=200
GROQ_API_KEY=<groq-key>
GROQ_BASE_URL=https://api.groq.com/openai/v1
TRUSTED_PROXY_IPS=<load-balancer-ips>
MAIL_PROVIDER=resend
RESEND_API_KEY=<resend-key>
EMAIL_FROM=Nexo <no-reply@nexo.example>
PUBLIC_WEB_URL=https://staging.nexo.example|https://app.nexo.example
EMAIL_VERIFICATION_TTL_MINUTES=30
PASSWORD_RESET_TTL_MINUTES=20
MFA_CHALLENGE_TTL_MINUTES=5
MFA_ENCRYPTION_KEYS=v1:<fernet-key-64-chars>
MFA_ACTIVE_KEY_VERSION=v1
SENTRY_DSN=<nexo-api-dsn>
SENTRY_ENVIRONMENT=staging|production
SENTRY_RELEASE=<git-sha>
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Railway Service Settings

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "DOCKERFILE", "dockerfilePath": "Dockerfile" },
  "deploy": {
    "preDeployCommand": "alembic upgrade head",
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/ready",
    "healthcheckTimeout": 120,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Cron Service (Maintenance)

Create a **separate** Railway cron service using the same API image:

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

This service:
- Uses the API image + production database secret
- Does NOT expose a public port
- Runs daily at 03:17 UTC

## Vercel Configuration

### Project Setup

1. Import same GitHub repo
2. Root Directory: `apps/web`
3. Framework: Next.js (auto-detected)
4. Install Command: `npm ci`
5. Build Command: `npm run build`
6. Output Directory: `.next` (default)

### Environment Variables (per environment)

| Variable | Preview/Staging | Production |
|----------|-----------------|------------|
| `API_URL` | `https://api-staging.nexo.example` | `https://api.nexo.example` |
| `NEXT_PUBLIC_SENTRY_DSN` | `<nexo-web-staging-dsn>` | `<nexo-web-production-dsn>` |
| `SENTRY_DSN` | `<nexo-web-staging-dsn>` | `<nexo-web-production-dsn>` |
| `SENTRY_ENVIRONMENT` | `staging` | `production` |
| `SENTRY_RELEASE` | `<git-sha>` | `<git-sha>` |
| `SENTRY_AUTH_TOKEN` | `<build-only-token>` | `<build-only-token>` |

### Vercel Project Settings

- **Git Integration**: PRs → Preview deployments; `main` branch → Production (if configured) or Preview
- **Domains**: Add custom domains per environment
- **Protection**: Enable Vercel Authentication for staging if needed

### Git Integration Settings (Prevent Auto-Production)

In Vercel project settings:
- **Production Branch**: Set to a branch that never auto-merges (e.g., `production-locked`)
- **Preview Deployments**: Enabled for all branches
- **Production Deployments**: Only via CLI/API (our workflow)

In Railway:
- **Auto-deploy**: Enabled for staging environment only
- **Production environment**: Manual deploy only

## Sentry Configuration

### Projects

Create two Sentry projects:
- `nexo-api` (Python/FastAPI)
- `nexo-web` (Next.js)

### Environments

Each project needs:
- `staging`
- `production`

### Release Naming

Use Git short SHA: `git rev-parse --short HEAD`

### Alert Rules (both projects)

| Rule | Condition | Action |
|------|-----------|--------|
| New Regression | First occurrence of error type in release | Alert on-call |
| Error Rate Spike | 5x baseline for 5 minutes | Alert on-call |
| Readiness Failure | `/ready` fails for 3+ minutes | Alert on-call |
| Auth Abuse Spike | 401/403 > 50/min | Alert security |

### Scrubbing (both projects)

```
send_default_pii = false
scrub: cookies, authorization, email, phone, ip_address, amount, balance, token, code, chat_message, request_body
```

### Source Maps (nexo-web)

- Build generates source maps automatically
- `SENTRY_AUTH_TOKEN` scoped to `nexo-web` project only
- Upload via `@sentry/nextjs` during build

## Deployment Flow

### Staging (Manual or PR-triggered)

```bash
gh workflow run deploy.yml \
  -f environment=staging \
  -f git_sha=$(git rev-parse HEAD)
```

### Production (Requires Approval)

```bash
gh workflow run deploy.yml \
  -f environment=production \
  -f git_sha=$(git rev-parse HEAD)
```

The production run will:
1. Wait for operator approval in GitHub UI
2. Run full CI validation
3. Deploy API → wait for `/ready`
4. Deploy Web
5. Run smoke tests with credentials
6. Record summary with URLs and SHA

## Verification Checklist

Before first production deploy:

- [ ] Staging environment fully configured (Railway + Vercel + secrets)
- [ ] Staging deploy succeeds and smoke tests pass
- [ ] Production secrets created (different from staging)
- [ ] GitHub `production` environment has required reviewer
- [ ] Sentry projects have both environments with alert rules
- [ ] Custom domains configured and HTTPS verified
- [ ] Resend domain verified, SPF/DKIM/DMARC aligned
- [ ] Backup schedule active in Railway PostgreSQL
- [ ] Cron service deployed and tested
- [ ] At least one staging deploy + smoke test completed successfully