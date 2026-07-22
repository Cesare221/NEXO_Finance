# Nexo Production Readiness Plan Index

**Approved design:** `docs/superpowers/specs/2026-07-21-production-hosting-security-design.md`

Execute these plans in order:

1. `2026-07-21-production-identity-implementation.md`
   - Adds e-mail verification, password recovery, TOTP MFA, recovery codes, BFF routes, and user experiences.
   - Exit gate: complete identity lifecycle passes API, web, migration, build, and dependency validation.
2. `2026-07-21-production-observability-implementation.md`
   - Adds Sentry, JSON logs, request correlation, data scrubbing, retention cleanup, and incident runbooks.
   - Exit gate: sanitized staging exception and alert are proven without sensitive data.
3. `2026-07-21-production-delivery-implementation.md`
   - Adds production runtime gates, Docker rehearsal, CI, controlled Vercel/Railway promotion, smoke tests, backup verification, DNS guidance, and launch evidence.
   - Exit gate: production-like and staging rehearsals pass and every external launch requirement has an accountable owner.

## Shared Execution Rules

- Use test-driven development for every behavior change.
- Commit only files belonging to the current task; preserve unrelated working-tree changes.
- Run focused tests after each implementation step and the full affected suite before each task commit.
- Never add real provider credentials, domains owned by the operator, user records, or production logs to Git.
- Stop promotion when a dependency audit, migration, readiness check, smoke test, restore drill, privacy review, or penetration test fails.
- A successful local build is not evidence of a successful public deployment.

## External Inputs Required During Delivery

- Vercel organization/project identifiers and scoped deployment token.
- Railway project/environment/service identifiers and scoped deployment token.
- Verified production and staging domains.
- Resend API keys, verified sending domains, and aligned sender addresses.
- Sentry organization/project identifiers, DSNs, source-map token, environments, and alert recipients.
- Separate production/staging MFA encryption keys, JWT secrets, databases, Redis instances, and Groq keys.
- Real controller/operator identity, DPO or privacy contact, retention approval, incident owner, and subprocessor approval.
- Independent penetration-test report and completed backup-restore evidence.

## Specification Coverage

| Design requirement | Implementation plan |
| --- | --- |
| Vercel web and Railway API/PostgreSQL/Redis | Delivery Tasks 1, 2, and 5 |
| E-mail verification and password recovery through Resend | Identity Tasks 1, 3, 4, 6, and 7 |
| TOTP, recovery codes, and bounded MFA login challenge | Identity Tasks 2, 3, 5, 6, and 7 |
| Token-version session invalidation | Identity Tasks 4 and 5 |
| Sentry API/web setup and sensitive-data scrubbing | Observability Tasks 1 and 3 |
| Structured logs and request correlation | Observability Task 2 |
| Security-record retention and incident procedures | Observability Task 4 |
| Runtime validation, readiness, Docker, and CI | Delivery Tasks 1, 2, and 3 |
| Controlled migration and promotion | Delivery Task 5 |
| Non-destructive smoke tests | Delivery Task 4 |
| Backup restore, DNS, e-mail alignment, and launch evidence | Delivery Task 6 |
| Full local and staging release rehearsal | Delivery Task 7 |
