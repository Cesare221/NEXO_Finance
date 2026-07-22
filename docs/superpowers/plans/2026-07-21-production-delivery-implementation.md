# Production Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Nexo reproducibly deployable to Vercel and Railway with safe configuration, controlled migrations, CI gates, production smoke tests, and recovery runbooks.

**Architecture:** Vercel serves `apps/web`; Railway runs the `apps/api` Docker image plus managed PostgreSQL and Redis. GitHub Actions validates each revision and performs manually approved staging/production promotions using environment-scoped secrets.

**Tech Stack:** Vercel, Railway, Docker, GitHub Actions, PostgreSQL 17, Redis 7, Alembic, FastAPI/Uvicorn, Next.js 15, Node.js 22, Python 3.13.

## Global Constraints

- Vercel hosts the web application; Railway hosts API, PostgreSQL, Redis, and maintenance cron.
- Staging and production have separate databases, Redis, domains, Sentry environments, Resend settings, Groq keys, and encryption keys.
- `alembic upgrade head` runs as a release step before the new API receives traffic.
- Database downgrades never run automatically.
- Production refuses startup with localhost, wildcard, HTTP, missing Redis, unsafe cookie/domain, missing mail, or incomplete MFA configuration.
- `/health` proves process liveness; `/ready` proves PostgreSQL and Redis readiness without exposing credentials.
- Deployments use Git SHA release identifiers and GitHub environment approval for production.
- No platform token or production secret is committed to Git.
- Public launch remains blocked until DNS, legal operator text, backup restore drill, Resend delivery, Sentry alert, and independent penetration test are complete.

---

### Task 1: Production Environment Contract And Startup Gate

**Files:**
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/app/api/health.py`
- Modify: `apps/api/.env.example`
- Create: `apps/api/tests/test_production_runtime.py`
- Modify: `apps/api/tests/test_health.py`
- Create: `apps/web/lib/runtime-config.ts`
- Modify: `apps/web/next.config.ts`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: `Settings.validate_runtime()` as the API startup gate.
- Produces: `validateWebRuntime()` called during Next.js production configuration.
- Produces readiness shape `{"status":"ready","checks":{"database":"ok","redis":"ok"}}` in production.

- [ ] **Step 1: Write failing API runtime tests**

Parameterize missing/unsafe `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `PUBLIC_WEB_URL`, Resend settings, MFA keyring, and provider-specific Groq key. Assert each failure names only the variable, never its value.

```python
@pytest.mark.parametrize("field", ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "PUBLIC_WEB_URL"])
def test_production_rejects_missing_required_setting(field, production_env):
    production_env[field] = ""
    with pytest.raises(RuntimeError, match=field):
        Settings(**production_env).validate_runtime()
```

- [ ] **Step 2: Write failing Redis readiness tests**

Inject a fake Redis adapter. Assert success reports `redis=ok`, failure returns 503 with `redis=unavailable`, and development without Redis reports only database.

- [ ] **Step 3: Run focused tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_production_runtime.py tests/test_health.py -q`

- [ ] **Step 4: Complete API validation and readiness**

Parse URLs with `urllib.parse.urlparse`, require `postgresql` or `postgresql+psycopg2`, `rediss` when the provider exposes TLS, explicit HTTPS origins/URLs, hostnames without schemes, 64-character secret minimum, active MFA key, Resend production provider, and Sentry release when Sentry is enabled. Redis readiness uses `PING` with a short socket timeout.

- [ ] **Step 5: Add web build-time validation**

```typescript
export function validateWebRuntime(env = process.env) {
  if (env.NODE_ENV !== "production") return;
  const apiUrl = env.API_URL;
  if (!apiUrl || !apiUrl.startsWith("https://")) {
    throw new Error("API_URL must be an explicit HTTPS URL in production");
  }
}
```

Call this from `next.config.ts`. Keep `API_URL` server-only and remove the `NEXT_PUBLIC_API_URL` fallback from `auth-server.ts` after all browser traffic uses BFF routes.

- [ ] **Step 6: Run runtime, web, and full regression tests**

Run API focused/full tests and web typecheck/smoke/build. Expected: PASS.

- [ ] **Step 7: Commit runtime gates**

```powershell
git add apps/api/app/core/config.py apps/api/app/main.py apps/api/app/api/health.py apps/api/.env.example apps/api/tests/test_production_runtime.py apps/api/tests/test_health.py apps/web/lib/runtime-config.ts apps/web/lib/auth-server.ts apps/web/next.config.ts apps/web/tests/smoke.mjs
git commit -m "feat: fail closed on unsafe production configuration"
```

### Task 2: Reproducible API Image And Local Production Rehearsal

**Files:**
- Modify: `apps/api/Dockerfile`
- Modify: `apps/api/.dockerignore`
- Modify: `apps/api/railway.json`
- Create: `apps/web/Dockerfile`
- Create: `apps/web/.dockerignore`
- Create: `docker-compose.production-like.yml`
- Create: `.env.production-like.example`
- Create: `scripts/production-like.ps1`

**Interfaces:**
- Produces immutable API and web image builds.
- Produces local commands `scripts/production-like.ps1 Up|Migrate|Smoke|Down`.

- [ ] **Step 1: Add a failing Docker build job locally**

Run: `docker build --pull -t nexo-api:test apps/api`

Expected before changes: identify any build/runtime issue and preserve the exact failure in the task notes; if it already passes, record PASS and continue with runtime hardening.

- [ ] **Step 2: Harden the API image**

Keep the non-root `nexo` user, install locked hashes only, add an OCI source/revision label from build args, use exec-form startup through a small Python entrypoint or `sh -c` only for `$PORT`, set a 30-second graceful timeout, and keep `/ready` healthcheck. Do not embed `.env`, tests, Git metadata, or provider credentials.

- [ ] **Step 3: Add a standalone production web image for rehearsal**

Use a multi-stage Node 22 Alpine build with `npm ci`, `npm run build`, Next standalone output, non-root runtime user, and port 3000. Set `output: "standalone"` only when `NEXT_STANDALONE=true` so Vercel behavior remains unchanged.

- [ ] **Step 4: Create the production-like compose stack**

Define PostgreSQL 17, Redis 7, one migration job, API, and web. Use health dependencies, named volumes, internal service DNS, no committed passwords, and only publish web 3011 and API 8000 locally. The API starts only after migration success and healthy dependencies.

- [ ] **Step 5: Add the PowerShell rehearsal wrapper**

`Up` validates the local env file and runs `docker compose up --build -d`; `Migrate` runs the one-off migration; `Smoke` invokes the production smoke script from Task 4; `Down` stops containers without deleting volumes unless `-RemoveData` is explicitly provided.

- [ ] **Step 6: Validate images and stack**

Run:

```powershell
docker build --pull -t nexo-api:test apps/api
docker build --pull --build-arg NEXT_STANDALONE=true -t nexo-web:test apps/web
docker compose -f docker-compose.production-like.yml config
```

Expected: both builds and Compose validation PASS.

- [ ] **Step 7: Commit reproducible containers**

```powershell
git add apps/api/Dockerfile apps/api/.dockerignore apps/api/railway.json apps/web/Dockerfile apps/web/.dockerignore docker-compose.production-like.yml .env.production-like.example scripts/production-like.ps1
git commit -m "build: add reproducible production rehearsal stack"
```

### Task 3: CI Release Gates And Supply-Chain Checks

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `.github/dependabot.yml`
- Create: `.github/workflows/container-security.yml`
- Create: `scripts/check-migration-head.py`
- Create: `scripts/check-secrets.ps1`

**Interfaces:**
- Produces required checks `api`, `web`, `docker`, `codeql`, `dependency-review`, and `container-security`.
- Produces one-head migration and tracked-secret gates.

- [ ] **Step 1: Add Redis and migration-head coverage to CI**

Run Redis 7 as a service, set `REDIS_URL=redis://localhost:6379/0`, run `alembic heads`, and fail unless exactly one revision is marked head. Run upgrade on PostgreSQL before tests.

- [ ] **Step 2: Add deterministic web gates**

Use Node 22 and `npm ci`; run `npx tsc --noEmit`, smoke tests, high-severity audit, and production build with a syntactically valid HTTPS `API_URL`.

- [ ] **Step 3: Add Docker and image scanning**

Build the API image and scan it with Trivy, failing on unfixed `CRITICAL` vulnerabilities and recording `HIGH` findings for review. Pin third-party GitHub actions to reviewed major versions and enable least-privilege permissions.

- [ ] **Step 4: Add secret and migration scripts**

The secret script scans tracked files for Groq, Resend, Sentry, Vercel, Railway, JWT, and private-key patterns and prints paths only. The migration script parses Alembic command output and returns nonzero for zero or multiple heads.

- [ ] **Step 5: Configure Dependabot**

Add weekly grouped updates for npm in `/apps/web`, pip/uv-visible dependencies in `/apps/api`, GitHub Actions at `/`, and Docker in `/apps/api`, with a limit of five open pull requests per ecosystem.

- [ ] **Step 6: Validate workflow syntax and run local equivalents**

Run API tests/audit, web typecheck/tests/audit/build, migration-head script, secret scan, and both Docker builds. Expected: PASS.

- [ ] **Step 7: Commit CI gates**

```powershell
git add .github/workflows .github/dependabot.yml scripts/check-migration-head.py scripts/check-secrets.ps1
git commit -m "ci: gate production releases and container security"
```

### Task 4: Non-Destructive Production Smoke Test

**Files:**
- Create: `apps/api/scripts/smoke_production.py`
- Create: `apps/api/tests/test_smoke_production.py`
- Modify: `apps/api/pyproject.toml`
- Modify: `docs/DEPLOYMENT.md`

**Interfaces:**
- Produces command `python scripts/smoke_production.py --web-url URL --api-url URL`.
- Consumes secrets `SMOKE_EMAIL`, `SMOKE_PASSWORD`, and optional `SMOKE_TOTP_SECRET` from the runtime environment.

- [ ] **Step 1: Write failing tests with HTTPX mock transport**

Test health/readiness success, CSP/HSTS headers on web, login without printing credentials, optional MFA challenge with generated TOTP, refresh rotation, `/auth/me`, dashboard read, and logout. Assert the script never calls a financial mutation endpoint.

- [ ] **Step 2: Run smoke tests and confirm failure**

Run: `cd apps/api; .\.venv\Scripts\python.exe -m pytest tests/test_smoke_production.py -q`

- [ ] **Step 3: Implement the bounded smoke client**

Use an HTTPX client with 10-second timeout and no redirect across hosts. Validate HTTPS unless `--allow-http-localhost` is explicitly passed. Redact credentials and cookies from output. Return JSON lines containing check name, status, duration, and request ID only.

- [ ] **Step 4: Implement optional authenticated path**

When smoke credentials exist, log in, satisfy MFA with `pyotp.TOTP(secret).now()`, read current user and dashboard, rotate refresh once, and log out. Without credentials, run public health/header checks and report authenticated checks as `skipped`, not passed.

- [ ] **Step 5: Validate failure behavior**

Any failed required check returns exit code 1. Readiness 503, missing HSTS in production, cross-host redirect, unexpected mutation, or authentication secret in captured output must fail tests.

- [ ] **Step 6: Run focused and local smoke tests**

Run the unit test, then the script against the production-like stack. Expected: all required checks PASS.

- [ ] **Step 7: Commit smoke tooling**

```powershell
git add apps/api/scripts/smoke_production.py apps/api/tests/test_smoke_production.py apps/api/pyproject.toml docs/DEPLOYMENT.md
git commit -m "test: add non-destructive production smoke checks"
```

### Task 5: Controlled Vercel And Railway Promotion

**Files:**
- Create: `.github/workflows/deploy.yml`
- Modify: `apps/api/railway.json`
- Modify: `apps/web/vercel.json`
- Create: `docs/PLATFORM_SETUP.md`
- Modify: `docs/DEPLOYMENT.md`

**Interfaces:**
- Produces manual workflow input `environment: staging | production`.
- Consumes environment-scoped GitHub secrets for Vercel and Railway only.

- [ ] **Step 1: Define GitHub environments and exact secret names in documentation**

Use `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_SERVICE_ID`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `SMOKE_EMAIL`, `SMOKE_PASSWORD`, and `SMOKE_TOTP_SECRET`. Production GitHub environment requires an operator reviewer.

- [ ] **Step 2: Add the manual deployment workflow**

The workflow checks out a selected Git SHA, reruns required validation, deploys Railway API, waits for `/ready`, deploys Vercel from `apps/web`, runs the smoke command, and records the deployed URLs and SHA in the job summary. Production uses the `production` GitHub environment approval gate.

The workflow has this concrete dispatch and environment contract:

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]
        required: true
      git_sha:
        type: string
        required: true

jobs:
  deploy:
    environment: ${{ inputs.environment }}
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.git_sha }}
      - run: npx @railway/cli up --service "${{ secrets.RAILWAY_SERVICE_ID }}" --environment "${{ secrets.RAILWAY_ENVIRONMENT_ID }}" --detach
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      - run: npx vercel pull --yes --environment="${{ inputs.environment == 'production' && 'production' || 'preview' }}" --token="${{ secrets.VERCEL_TOKEN }}"
        working-directory: apps/web
      - if: inputs.environment == 'production'
        run: npx vercel build --prod --token="${{ secrets.VERCEL_TOKEN }}"
        working-directory: apps/web
      - if: inputs.environment == 'staging'
        run: npx vercel build --token="${{ secrets.VERCEL_TOKEN }}"
        working-directory: apps/web
      - if: inputs.environment == 'production'
        run: npx vercel deploy --prebuilt --prod --token="${{ secrets.VERCEL_TOKEN }}"
        working-directory: apps/web
      - if: inputs.environment == 'staging'
        run: npx vercel deploy --prebuilt --token="${{ secrets.VERCEL_TOKEN }}"
        working-directory: apps/web
      - run: python scripts/smoke_production.py --web-url "${{ vars.WEB_URL }}" --api-url "${{ vars.API_URL }}"
        working-directory: apps/api
        env:
          SMOKE_EMAIL: ${{ secrets.SMOKE_EMAIL }}
          SMOKE_PASSWORD: ${{ secrets.SMOKE_PASSWORD }}
          SMOKE_TOTP_SECRET: ${{ secrets.SMOKE_TOTP_SECRET }}
```

Tests assert deployment steps consume only GitHub environment secrets and the environment-scoped `WEB_URL` and `API_URL` variables.

- [ ] **Step 3: Prevent accidental automatic production promotion**

Document Vercel/Railway Git integration settings so pull requests create previews or staging deploys only. Production deployment is owned by the approved workflow; do not enable two competing automatic production deploy paths.

- [ ] **Step 4: Keep platform configuration explicit**

Railway retains Dockerfile build, pre-deploy migration, `/ready` healthcheck, and restart limits. Vercel retains `npm ci` and `npm run build` with `apps/web` as project root. Neither file contains domains or secrets.

- [ ] **Step 5: Validate workflow and dry-run commands**

Use GitHub Actions syntax validation and CLI authentication checks against staging. Run a staging deployment, smoke it, and verify production remains untouched.

- [ ] **Step 6: Commit controlled promotion**

```powershell
git add .github/workflows/deploy.yml apps/api/railway.json apps/web/vercel.json docs/PLATFORM_SETUP.md docs/DEPLOYMENT.md
git commit -m "deploy: add approved vercel and railway promotion"
```

### Task 6: Backup, Restore, DNS, And Launch Runbooks

**Files:**
- Create: `docs/BACKUP_AND_RESTORE.md`
- Create: `docs/LAUNCH_CHECKLIST.md`
- Create: `docs/DNS_AND_EMAIL.md`
- Create: `scripts/verify-restored-database.py`
- Create: `apps/api/tests/test_verify_restored_database.py`
- Modify: `docs/SECURITY_AND_LGPD.md`

**Interfaces:**
- Produces a read-only restored-database verifier.
- Produces objective launch evidence and named external blockers.

- [ ] **Step 1: Write failing restored-database verifier tests**

Test single migration head, required tables, row-count queries, foreign-key orphan checks, and read-only behavior. The verifier outputs aggregate counts only and never exports user rows.

- [ ] **Step 2: Implement the verifier**

Connect through `RESTORE_DATABASE_URL`, require the hostname not equal production, set transaction read-only, check Alembic revision, tables, selected aggregate counts, and orphan counts, then roll back unconditionally.

- [ ] **Step 3: Write the backup and restore drill**

Define Railway backup schedule, weekly/monthly retention selected by the operator, restore into isolated staging, run the verifier and application smoke tests, record duration/result, and destroy restored sensitive data after evidence capture.

- [ ] **Step 4: Write DNS and e-mail setup**

Define `app` CNAME/records for Vercel, `api` custom domain for Railway, Resend SPF/DKIM records, DMARC starting at monitoring policy then enforcement after review, HTTPS validation, sender alignment, and no use of personal mailbox credentials.

- [ ] **Step 5: Write the objective launch checklist**

Require successful CI, staging deploy, identity lifecycle, Resend delivery, MFA recovery, Sentry sanitized event and alert, Redis multi-instance rate limit, backup restore, DNS/HTTPS, legal operator fields, subprocessors, incident owner, penetration test, and signed production approval.

- [ ] **Step 6: Run verifier tests and documentation scans**

Run the focused test and scan all production docs for unresolved planning markers, the literal domains `example.com` and `nexo.example`, localhost production values, and the literal operator fields `CONTROLADOR_NAO_PREENCHIDO`, `ENCARREGADO_NAO_PREENCHIDO`, and `CONTATO_LGPD_NAO_PREENCHIDO`. Public launch fails while any match remains.

- [ ] **Step 7: Commit operations runbooks**

```powershell
git add docs/BACKUP_AND_RESTORE.md docs/LAUNCH_CHECKLIST.md docs/DNS_AND_EMAIL.md docs/SECURITY_AND_LGPD.md scripts/verify-restored-database.py apps/api/tests/test_verify_restored_database.py
git commit -m "docs: add production recovery and launch gates"
```

### Task 7: Final Production Readiness Gate

**Files:**
- Modify: `README.md`
- Modify: `docs/DEPLOYMENT.md`
- Modify: `graphify-out/*`

**Interfaces:**
- Consumes: identity, observability, and delivery workstreams.
- Produces: a reproducible release candidate and final operator handoff.

- [ ] **Step 1: Run the complete local validation matrix**

Run migration-head checks, full API tests, pip audit, web typecheck/tests/audit/build, Docker builds, Compose validation, secret scan, Graphify update, and `git diff --check`.

- [ ] **Step 2: Run production-like rehearsal**

Start fresh PostgreSQL and Redis volumes, migrate, start API/web, run public and authenticated smoke tests, restart the API during an active session, verify refresh behavior, and stop without deleting evidence logs.

- [ ] **Step 3: Run staging release rehearsal**

Deploy the exact candidate SHA to staging, verify custom domains/HTTPS, Resend verification/reset, MFA/recovery, Sentry sanitation/alert, Groq consent/fallback, PWA installation, mobile layouts, and backup restore.

- [ ] **Step 4: Update architecture graph and operator entry point**

Run `graphify update .`. Update README with local, staging, production, runbook, and release commands plus links to identity, incident, retention, backup, and launch documents.

- [ ] **Step 5: Record unresolved external gates honestly**

Do not mark production ready until real domains, platform credentials, legal operator/DPO details, restore evidence, Sentry alert evidence, Resend domain verification, Groq ZDR decision, and penetration-test results are attached to the launch checklist.

- [ ] **Step 6: Commit the release-candidate documentation**

```powershell
git add README.md docs/DEPLOYMENT.md graphify-out
git commit -m "docs: finalize nexo production readiness"
```

## Reference Documentation

- Vercel monorepos: `https://vercel.com/docs/monorepos`
- Vercel CLI deployments: `https://vercel.com/docs/cli/deploy`
- Railway config as code: `https://docs.railway.com/reference/config-as-code`
- Railway pre-deploy command: `https://docs.railway.com/guides/pre-deploy-command`
- GitHub deployment environments: `https://docs.github.com/actions/deployment/targeting-different-environments/managing-environments-for-deployment`
