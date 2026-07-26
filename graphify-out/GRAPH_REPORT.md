# Graph Report - NEXO_finance  (2026-07-21)

## Corpus Check
- 173 files · ~235,819 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1376 nodes · 2521 edges · 98 communities (83 shown, 15 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 157 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d6a410d0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 98|Community 98]]

## God Nodes (most connected - your core abstractions)
1. `_auth_header()` - 65 edges
2. `_register_and_get_token()` - 64 edges
3. `publicAuthError()` - 51 edges
4. `setAuthCookies()` - 50 edges
5. `clearAuthCookies()` - 49 edges
6. `_create_account()` - 46 edges
7. `validateRequestOrigin()` - 44 edges
8. `authenticatedBackendRequest()` - 42 edges
9. `TestCategories` - 24 edges
10. `TestCreditCards` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Category` --uses--> `Base`  [INFERRED]
  apps/api/app/models/category.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `CreditCard` --uses--> `Base`  [INFERRED]
  apps/api/app/models/credit_card.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `InstallmentPlan` --uses--> `Base`  [INFERRED]
  apps/api/app/models/installment_plan.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `MfaChallenge` --uses--> `Base`  [INFERRED]
  apps/api/app/models/mfa_challenge.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `MfaMethod` --uses--> `Base`  [INFERRED]
  apps/api/app/models/mfa_method.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py

## Communities (98 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (17): ActionProposal, AuditEvent, Transaction, User, _auth_header(), _create_account(), _create_category(), _create_credit_card() (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (39): _check_rate_limit(), _client_host(), delete_me(), _device_name(), export_me(), login(), logout(), me() (+31 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (24): archive_account(), archive_category(), _category_snapshot(), confirm_installment(), _conflict(), create_card_purchase(), create_category(), create_transaction() (+16 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (51): BaseModel, ActionExecutionResponse, ActionProposalCreate, ActionProposalResponse, ActionProposalUpdate, AssistantMessageRequest, AssistantMessageResponse, AuditEventResponse (+43 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (26): archive_account(), archive_credit_card(), confirm_installment(), confirm_recurring_rule(), create_account(), create_card_purchase(), create_category(), create_credit_card() (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (23): _register_theme_user(), test_authorization_isolation(), test_cors_rejects_unconfigured_origin(), test_login_invalid_password(), test_login_is_rate_limited(), test_login_success(), test_logout(), test_me_authenticated() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.40
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 7 - "Community 7"
Cohesion: 0.60
Nodes (3): client(), override_get_db(), setup_db()

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (15): AuthRateLimiter, _key(), RateLimitExceeded, RateLimitUnavailable, Exception, decrypt_totp_secret(), encrypt_totp_secret(), _fernet_for_version() (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.06
Nodes (34): code:python (def test_production_requires_resend_and_mfa_keys(monkeypatch), code:python (def test_totp_secret_round_trip(settings_with_keyring):), code:python (def generate_secret() -> str:), code:powershell (git add apps/api/app/services/account_token_service.py apps/), code:python (def test_password_reset_is_enumeration_resistant(client, mai), code:python (class EmailRequest(BaseModel):), code:powershell (git add apps/api/app/api apps/api/app/core/security.py apps/), code:python (def test_login_with_active_mfa_returns_challenge_without_tok) (+26 more)

### Community 14 - "Community 14"
Cohesion: 0.60
Nodes (3): test_health_check(), test_readiness_check_confirms_database_connection(), test_readiness_check_reports_database_outage()

### Community 22 - "Community 22"
Cohesion: 0.24
Nodes (18): ActionExecution, _audit(), _aware(), cancel_proposal(), confirm_proposal(), create_proposal(), _execute_create_transaction(), _existing_execution() (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (13): 1. Completar Incremento 3: Transferencias, 2. Implementar Incremento 4: Cartoes e Faturas, 3. Implementar Incremento 5: Parcelas e Recorrencias, 4. Implementar Incremento 6: Dashboard, 5. Implementar Incremento 7: Fin Minimo com ActionProposal, 6. Criar Frontend Web Usavel, 7. Segurança e Qualidade, 8. Operacao Local e Deploy (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (11): Arquitetura Atual, Execution Rule, Fin Phase 1 Implementation Plan, Global Constraints, Inventario Atual, Status de Execucao, Task 1: Parcelas e Recorrencias, Task 2: Dashboard Backend (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.06
Nodes (37): Banco E Migrations, code:powershell (cd apps/api), code:powershell (cd apps/web), code:powershell (cd apps/api), code:powershell (cd apps/api), code:powershell (cd apps/api), code:text (http://localhost:3000), code:powershell (cd apps/api) (+29 more)

### Community 26 - "Community 26"
Cohesion: 0.46
Nodes (15): _auth_header(), _create_account(), _register_and_get_token(), test_cancel_proposal_does_not_execute(), test_confirm_proposal_executes_once_and_records_audit(), test_expired_proposal_does_not_execute(), test_external_ai_is_not_called_without_user_consent(), test_groq_provider_can_only_prepare_a_pending_proposal() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.44
Nodes (8): cancel_proposal(), confirm_proposal(), create_proposal(), _limit(), list_audit_events(), list_proposals(), send_message(), update_proposal()

### Community 28 - "Community 28"
Cohesion: 0.33
Nodes (4): ADR 0001: Phase 1 Modular Monolith, Consequences, Context, Decision

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (13): PrivacySettings(), initials(), SessionContext, SessionContextValue, SessionProfile(), SessionProvider(), SessionUser, useSession() (+5 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (24): dependencies, lucide-react, next, qrcode, react, react-dom, recharts, @types/node (+16 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (26): authCookies, authMiddleware, authRoutes, chart, creditCardFeedback, dashboard, demoDatasetRoute, financialDashboard (+18 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (16): BaseSettings, cors_origins(), Settings, Protocol, RuntimeError, ConsoleMailService, _email_payload(), get_mail_service() (+8 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (11): build, builder, dockerfilePath, deploy, healthcheckPath, healthcheckTimeout, preDeployCommand, restartPolicyMaxRetries (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (61): DELETE(), DELETE(), mutateAccount(), PUT(), errorResponse(), GET(), POST(), requestBackend() (+53 more)

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): contentSecurityPolicy, nextConfig, securityHeaders

### Community 44 - "Community 44"
Cohesion: 0.07
Nodes (35): Border Radius Scale, Brand & Accent, Breakpoints, Buttons, Cards & Containers, Collapsing Strategy, Colors, Components (+27 more)

### Community 45 - "Community 45"
Cohesion: 0.50
Nodes (3): APP_SHELL, copy, url

### Community 48 - "Community 48"
Cohesion: 0.21
Nodes (6): AuthForm(), AuthFormProps, BrandAssetProps, FinMascotProps, NexoLogo(), NexoMark()

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (9): Authentication Flow, Backend Hardening, Context, Decision, Deferred Managed Identity, Fin Public Authentication and Security Design, Security Headers and PWA, Testing (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.14
Nodes (16): FinMascot(), AssistantResponse, ChatMessage, currencyFormatter, FinConversation(), formatCurrency(), suggestions, notifyProposalsChanged() (+8 more)

### Community 51 - "Community 51"
Cohesion: 0.22
Nodes (7): Fin Public Authentication and Security Implementation Plan, Global Constraints, Task 1: Harden FastAPI Authentication, Task 2: Add the Next.js Authentication Facade, Task 3: Build Accessible Login and Registration UX, Task 4: Add Session Profile and Logout, Task 5: Add Security Headers and Complete Verification

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (19): Acessibilidade e responsividade, Arquitetura de componentes, Barra superior, Caixa de conversa do Fin, Central de movimentacoes reconhecidas, Conversa e revisao, Criterios de aceite, Dados e API (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.18
Nodes (3): CategoryOption, TransactionManager(), TransactionType

### Community 55 - "Community 55"
Cohesion: 0.14
Nodes (13): API No Railway, Arquitetura Recomendada, Backups, Checklist De Produção, code:text (ENVIRONMENT=production), code:text (GET https://api.seudominio.com/health -> 200 {"status":"ok"}), code:powershell (cd apps/api), Financial Rollout (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (8): Global Constraints, Nexo Dashboard, Fin Panel and Review Inbox Implementation Plan, Task 1: Branding Nexo, Task 2: Dashboard real e tipado, Task 3: Propostas pendentes como inbox, Task 4: AppShell com hamburger e Fin global, Task 5: Dashboard review surface, Task 6: Verificacao integrada

### Community 57 - "Community 57"
Cohesion: 0.25
Nodes (6): AppShellContent(), currency, dateFormatter, MovementReviewInbox(), ProposalGroup, usePendingProposals()

### Community 58 - "Community 58"
Cohesion: 0.20
Nodes (9): brlFormatter, CreditCardForm(), CreditCardFormProps, FieldErrors, brlFormatter, CurrencyInput(), CurrencyInputProps, formatDecimal() (+1 more)

### Community 59 - "Community 59"
Cohesion: 0.29
Nodes (4): DemoDatasetControl(), DemoDatasetControlProps, installedDate, DemoDatasetState

### Community 61 - "Community 61"
Cohesion: 0.53
Nodes (4): buildCommand, framework, installCommand, $schema

### Community 62 - "Community 62"
Cohesion: 0.31
Nodes (11): production_settings(), test_production_rejects_any_invalid_mfa_encryption_key(), test_production_rejects_https_public_web_url_without_hostname(), test_production_rejects_insecure_origins(), test_production_rejects_non_https_public_web_url(), test_production_rejects_wildcard_hosts(), test_production_requires_a_strong_secret(), test_production_requires_distributed_rate_limiting() (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.08
Nodes (22): API e segurança, Auditoria atual, Backend, Cadastro e ciclo do cartão, Conteúdo, Dataset demonstrativo, Decisões aprovadas, Direção visual (+14 more)

### Community 65 - "Community 65"
Cohesion: 0.05
Nodes (37): code:python (def test_demo_dataset_and_theme_are_mapped():), code:python (return {"action": action, "category": snapshot}), code:powershell (git add apps/api/app/schemas/financial.py apps/api/app/servi), code:python (def test_install_is_complete_and_idempotent(client):), code:python (class DemoDatasetSummary(BaseModel):), code:python (try:), code:powershell (git add apps/api/app/services/demo_dataset_service.py apps/a), code:typescript (export type DemoDatasetState = {) (+29 more)

### Community 66 - "Community 66"
Cohesion: 0.20
Nodes (4): CategoryManager(), CategoryRow, CategoryDeleteResult, FinancialCategory

### Community 67 - "Community 67"
Cohesion: 0.25
Nodes (7): Bloqueadores Antes Da Producao Publica, Controles Implementados, Direitos Do Titular, Fronteira De Confianca Do Fin, Resposta A Incidentes, Retencao Recomendada, Seguranca E LGPD Do Nexo

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (9): links, mobileLinks, moreLinks, pageTitles, primaryLinks, FinChatPanel(), links, NavigationDrawer() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.15
Nodes (8): Base, get_db(), DeclarativeBase, BillingStatement, DemoDataset, FinancialAccount, MfaChallenge, create_account()

### Community 70 - "Community 70"
Cohesion: 0.36
Nodes (11): _active_dataset(), _audit(), _build_resources(), clean_demo_dataset(), get_demo_dataset_status(), _has_row(), install_demo_dataset(), _lock_namespace() (+3 more)

### Community 71 - "Community 71"
Cohesion: 0.08
Nodes (24): Acceptance Criteria, API And BFF Contracts, API And Data, Authentication Design, Chosen Architecture, Context, Data Model, Deployment And Release Flow (+16 more)

### Community 72 - "Community 72"
Cohesion: 0.06
Nodes (31): currency, DashboardView(), dateFormatter, initialPeriod(), money(), monthFormatter, periodFormatter, periodSummary() (+23 more)

### Community 73 - "Community 73"
Cohesion: 0.60
Nodes (3): _run_migration(), _task_one_migration(), test_alembic_migration_round_trips_sqlite_schema_and_dataset_ownership()

### Community 81 - "Community 81"
Cohesion: 0.18
Nodes (9): BeforeInstallPromptEvent, InstallAppButton(), initials(), loadImage(), prepareAvatar(), ProfileSettings(), dateTime, SecuritySettings() (+1 more)

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (10): AccountManager(), accountTypes, formatCurrency(), DashboardAccount, DashboardCashFlowPoint, DashboardData, DashboardStatement, DashboardTransaction (+2 more)

### Community 83 - "Community 83"
Cohesion: 0.12
Nodes (23): Category, AssistantProviderError, GroqAssistantProvider, _json_safe(), _normalize(), ProviderResult, RecentTransactionsArguments, _resolve_named() (+15 more)

### Community 85 - "Community 85"
Cohesion: 0.18
Nodes (11): metadata, viewport, PWARegistration(), ThemeContext, ThemeContextValue, ThemeProvider(), applyTheme(), isThemePreference() (+3 more)

### Community 86 - "Community 86"
Cohesion: 0.17
Nodes (9): RecurringRule, Transfer, create_recurring_rule(), create_transfer(), get_account(), get_account_balance(), get_dashboard(), list_accounts() (+1 more)

### Community 90 - "Community 90"
Cohesion: 0.09
Nodes (21): code:python (@pytest.mark.parametrize("field", ["DATABASE_URL", "REDIS_UR), code:powershell (git add docs/BACKUP_AND_RESTORE.md docs/LAUNCH_CHECKLIST.md ), code:powershell (git add README.md docs/DEPLOYMENT.md graphify-out), code:typescript (export function validateWebRuntime(env = process.env) {), code:powershell (git add apps/api/app/core/config.py apps/api/app/main.py app), code:powershell (docker build --pull -t nexo-api:test apps/api), code:powershell (git add apps/api/Dockerfile apps/api/.dockerignore apps/api/), code:powershell (git add .github/workflows .github/dependabot.yml scripts/che) (+13 more)

### Community 91 - "Community 91"
Cohesion: 0.10
Nodes (19): code:python (def test_scrubber_removes_sensitive_request_data():), code:powershell (git add apps/api/app/maintenance.py apps/api/tests/test_main), code:powershell (git add .github/workflows/ci.yml docs/DEPLOYMENT.md), code:python (SENSITIVE_KEYS = {), code:python (def init_observability() -> None:), code:powershell (git add apps/api/pyproject.toml apps/api/uv.lock apps/api/re), code:python (def test_json_formatter_excludes_sensitive_values():), code:powershell (git add apps/api/app/core/logging_config.py apps/api/app/mai) (+11 more)

### Community 92 - "Community 92"
Cohesion: 0.27
Nodes (9): CreditCard, archive_credit_card(), _card_response(), _card_used_limit(), create_credit_card(), _has_active_card_name_conflict(), list_credit_cards(), _lock_card_name_namespace() (+1 more)

### Community 93 - "Community 93"
Cohesion: 0.40
Nodes (4): External Inputs Required During Delivery, Nexo Production Readiness Plan Index, Shared Execution Rules, Specification Coverage

### Community 94 - "Community 94"
Cohesion: 0.17
Nodes (3): MfaMethod, MfaRecoveryCode, test_recovery_code_round_trips_argon2_hash()

### Community 96 - "Community 96"
Cohesion: 0.22
Nodes (5): Installment, InstallmentPlan, _add_months(), confirm_recurring_rule(), create_installment_plan()

## Knowledge Gaps
- **357 isolated node(s):** `builder`, `dockerfilePath`, `preDeployCommand`, `startCommand`, `healthcheckPath` (+352 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthError` connect `Community 1` to `Community 0`, `Community 96`, `Community 69`, `Community 9`, `Community 83`, `Community 22`, `Community 86`, `Community 92`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `Category` connect `Community 83` to `Community 1`, `Community 2`, `Community 69`, `Community 70`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `Transaction` connect `Community 0` to `Community 96`, `Community 1`, `Community 2`, `Community 69`, `Community 70`, `Community 83`, `Community 86`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `builder`, `dockerfilePath`, `preDeployCommand` to the rest of the system?**
  _360 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07915360501567398 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0889894419306184 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.08771929824561403 - nodes in this community are weakly interconnected._