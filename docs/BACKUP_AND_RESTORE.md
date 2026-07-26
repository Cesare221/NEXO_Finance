# Backup and Restore Runbook

This document defines the backup strategy, restore procedures, and validation for Nexo production data.

## Backup Strategy

### PostgreSQL (Railway Managed)

| Tier | Schedule | Retention | Storage |
|------|----------|-----------|---------|
| Continuous | WAL archiving (point-in-time recovery) | 7 days | Railway managed |
| Daily | Full dump at 03:00 UTC | 30 days | Railway managed |
| Weekly | Full dump (Sunday 03:00 UTC) | 12 weeks | Railway managed |
| Monthly | Full dump (1st of month 03:00 UTC) | 12 months | Railway managed |

### Redis (Railway Managed)

| Tier | Schedule | Retention |
|------|----------|-----------|
| AOF | Every 1 second (always) | 7 days |
| RDB | Daily at 04:00 UTC | 30 days |

### Application-Level Backups

| Data | Method | Schedule | Retention |
|------|--------|----------|-----------|
| Demo dataset | `DELETE /financial/demo-dataset` | On-demand | N/A (recreatable) |
| User exports | `GET /auth/data-export` | On-demand | N/A (user-initiated) |

## Restore Procedures

### 1. Point-in-Time Recovery (PITR)

**When to use**: Accidental data corruption, bad migration, partial data loss within last 7 days.

**Procedure**:
1. In Railway dashboard → PostgreSQL service → Backups
2. Select "Point-in-time recovery"
3. Choose target timestamp (up to 7 days back)
4. Click "Restore to new database"
5. Wait for restore to complete (typically 10-30 min)
6. Update application `DATABASE_URL` to restored instance
7. Run verifier: `python scripts/verify_restored_database.py --database-url $RESTORED_URL`
8. Run smoke tests against restored database
9. If validation passes, promote restored database as primary

### 2. Full Backup Restore

**When to use**: Catastrophic failure, PITR window exceeded, new environment setup.

**Procedure**:
1. In Railway dashboard → PostgreSQL service → Backups
2. Select desired daily/weekly/monthly backup
3. Click "Restore to new database"
4. Wait for restore to complete
5. Update `DATABASE_URL` in application
6. Run Alembic migrations if schema version differs:
   ```bash
   cd apps/api
   python -m alembic upgrade head
   ```
7. Run verifier: `python scripts/verify_restored_database.py --database-url $RESTORED_URL`
8. Run smoke tests
9. If validation passes, promote restored database as primary

### 3. Cross-Region Restore (Disaster Recovery)

**When to use**: Regional outage affecting primary Railway region.

**Procedure**:
1. Provision new Railway project in alternate region
2. Restore from latest daily backup to new project
3. Update DNS to point `api.nexo.example` to new Railway endpoint
4. Deploy API to new project (same SHA)
5. Run verifier and smoke tests
6. Update Vercel `API_URL` environment variable
7. Verify end-to-end functionality

## Verification Script

The `scripts/verify_restored_database.py` validates a restored database:

```bash
# Usage
python scripts/verify_restored_database.py \
  --database-url "postgresql://user:pass@restored-host/db" \
  --expected-head "c91d4e7a2f10"
```

**Checks performed**:
1. ✅ Single Alembic migration head
2. ✅ Expected migration revision matches
3. ✅ All 9 required tables exist
4. ✅ Row counts for each table
5. ✅ Zero foreign key orphans (8 relationships checked)
5. ✅ Read-only mode enforced (no writes possible)

**Output**: JSON with status and aggregate counts

## Backup Validation Schedule

| Frequency | Action | Owner |
|-----------|--------|-------|
| Daily | Automated PITR and full backup completion alert | Railway |
| Weekly | Restore latest daily backup to staging, run verifier + smoke tests | DevOps |
| Monthly | Restore weekly backup to isolated env, full smoke suite | DevOps |
| Quarterly | Full disaster recovery drill (cross-region restore) | DevOps |

## Restore Validation Checklist

After any restore, verify:

- [ ] Verifier script returns `{"status": "ok"}`
- [ ] Smoke tests pass (public + authenticated)
- [ ] Alembic revision matches expected head
- [ ] All required tables present with expected row counts
- [ ] Zero foreign key orphans
- [ ] Application starts and serves `/health` and `/ready`
- [ ] Login, MFA, dashboard work end-to-end
- [ ] No write operations possible (read-only enforced during verification)

## Data Retention Policy

| Data Type | Retention | Deletion Method |
|-----------|-----------|-----------------|
| Financial transactions | 7 years (legal) | Soft delete + audit trail |
| User accounts | Indefinite (until deletion request) | GDPR Art. 17 compliance |
| Audit events | 3 years | Automatic partition drop |
| MFA challenges/tokens | 30 days post-expiry | Cron job (`app.maintenance`) |
| Email verification tokens | 30 days post-expiry | Cron job |
| Password reset tokens | 20 minutes TTL | Automatic expiry |
| Session tokens | 7 days (refresh) / 15 min (access) | JWT expiry + rotation |
| Demo dataset | Until user deletes | `DELETE /financial/demo-dataset` |
| Sentry events | 90 days (configurable) | Sentry retention policy |
| Application logs | 30 days (Railway) | Railway log rotation |

## Emergency Contacts

| Role | Name | Contact | Escalation |
|------|------|---------|------------|
| Primary DBA | | | 0 min |
| Secondary DBA | | | 15 min |
| Infrastructure Lead | | | 30 min |
| CTO | | | 1 hour |

## Runbook: Restore to Staging (Weekly Drill)

```bash
# 1. Trigger restore in Railway UI (daily backup → new staging DB)
# 2. Get connection URL for restored DB
export RESTORED_DB_URL="postgresql://..."

# 3. Run verifier
cd apps/api
python ../scripts/verify_restored_database.py \
  --database-url "$RESTORED_DB_URL" \
  --expected-head "$(python -m alembic heads | grep -o '^[a-f0-9]*')"

# 4. If verifier passes, run smoke tests
python scripts/smoke_production.py \
  --api-url "https://api-staging.nexo.example" \
  --web-url "https://staging.nexo.example" \
  --email "$SMOKE_EMAIL" \
  --password "$SMOKE_PASSWORD" \
  --totp-secret "$SMOKE_TOTP_SECRET"

# 5. Document results
# - Verifier output (JSON)
# - Smoke test output (JSON lines)
# - Duration of restore
# - Any anomalies
# Store in: evidence/restore-drill-$(date +%Y%m%d)/
```

## Runbook: Production Restore (Incident)

```bash
# 1. ALERT: Page primary DBA
# 2. Assess: What data is lost? Since when?
# 3. Choose: PITR (if <7 days) or Full Restore (if older)
# 4. EXECUTE in Railway:
#    - PITR: Select timestamp → Restore to new DB
#    - Full: Select backup → Restore to new DB
# 5. VALIDATE:
#    python scripts/verify_restored_database.py --database-url $NEW_DB_URL
# 4. PROMOTE: Update production DATABASE_URL secret to new DB
# 5. DEPLOY: Trigger API deploy (same SHA) to pick up new DB
# 6. VERIFY: Smoke tests against production URLs
# 7. COMMUNICATE: Status page update
# 8. DOCUMENT: Incident timeline, root cause, action items
```

## Testing Restore Integrity

The verifier ensures:

```json
{
  "status": "ok",
  "checks": {
    "single_migration_head": true,
    "required_tables": {"missing": [], "counts": {...}},
    "foreign_key_orphans": {...},
    "alembic_revision": "c91d4e7a2f10"
  },
  "summary": {
    "total_tables_checked": 9,
    "tables_found": 9,
    "total_rows_sampled": 1234,
    "total_foreign_key_orphans": 0
  }
}
```

Any non-zero orphans, missing tables, or migration mismatch = **FAIL**.

## Compliance Notes

- **LGPD Art. 16**: Right to rectification - supported via user profile edit
- **LGPD Art. 17**: Right to erasure - `DELETE /auth/me` with password confirmation
- **LGPD Art. 18**: Right to restriction - soft delete preserves audit trail
- **LGPD Art. 20**: Right to portability - `GET /auth/data-export` returns JSON
- **Financial records**: 7-year retention per Brazilian Central Bank regulations
- **Audit trail**: Immutable, never deleted, queryable via admin endpoint

## Backup Encryption

- **At rest**: Railway managed (AES-256)
- **In transit**: TLS 1.2+ for all connections
- **WAL files**: Encrypted at rest
- **Dump files**: Encrypted at rest in Railway storage

## Recovery Time Objectives (RTO/RPO)

| Scenario | RPO | RTO |
|----------|-----|-----|
| Accidental deletion (PITR) | < 5 min | < 30 min |
| Corruption (full restore) | 24 hours | < 2 hours |
| Regional outage (cross-region) | 24 hours | < 4 hours |
| Catastrophic (new project) | 24 hours | < 8 hours |

## Appendix: Railway Backup Commands (CLI)

```bash
# List backups
railway backups --service postgresql --environment production

# Trigger manual backup
railway backup create --service postgresql --environment production

# Restore (creates new service)
railway backup restore <backup-id> --service postgresql --environment staging

# Monitor restore progress
railway logs --service postgresql-restored-<timestamp>
```