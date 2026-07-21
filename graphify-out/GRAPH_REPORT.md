# Graph Report - NEXO_finance  (2026-07-21)

## Corpus Check
- 145 files · ~216,992 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1104 nodes · 2090 edges · 87 communities (72 shown, 15 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 104 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1a9a41eb`
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
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]

## God Nodes (most connected - your core abstractions)
1. `_auth_header()` - 65 edges
2. `_register_and_get_token()` - 64 edges
3. `_create_account()` - 46 edges
4. `setAuthCookies()` - 44 edges
5. `publicAuthError()` - 43 edges
6. `clearAuthCookies()` - 41 edges
7. `validateRequestOrigin()` - 40 edges
8. `authenticatedBackendRequest()` - 37 edges
9. `TestCategories` - 24 edges
10. `TestCreditCards` - 24 edges

## Surprising Connections (you probably didn't know these)
- `BillingStatement` --uses--> `Base`  [INFERRED]
  apps/api/app/models/billing_statement.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `Category` --uses--> `Base`  [INFERRED]
  apps/api/app/models/category.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `CreditCard` --uses--> `Base`  [INFERRED]
  apps/api/app/models/credit_card.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `DemoDataset` --uses--> `Base`  [INFERRED]
  apps/api/app/models/demo_dataset.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py
- `Transaction` --uses--> `Base`  [INFERRED]
  apps/api/app/models/transaction.py → C:/Users/Usuario/Desktop/PROJETOS/Fin/apps/api/app/core/database.py

## Communities (87 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (16): ActionProposal, AuditEvent, User, _auth_header(), _create_account(), _create_category(), _create_credit_card(), _register_and_get_token() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.10
Nodes (28): _check_rate_limit(), _client_host(), login(), logout(), me(), refresh(), register(), update_me() (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.16
Nodes (20): archive_account(), archive_category(), archive_credit_card(), _card_response(), _card_used_limit(), _category_snapshot(), _conflict(), create_credit_card() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (48): BaseModel, ActionExecutionResponse, ActionProposalCreate, ActionProposalResponse, ActionProposalUpdate, AssistantMessageRequest, AssistantMessageResponse, AuditEventResponse (+40 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (26): archive_account(), archive_credit_card(), confirm_installment(), confirm_recurring_rule(), create_account(), create_card_purchase(), create_category(), create_credit_card() (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (23): _register_theme_user(), test_authorization_isolation(), test_cors_rejects_unconfigured_origin(), test_login_invalid_password(), test_login_is_rate_limited(), test_login_success(), test_logout(), test_me_authenticated() (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.40
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 7 - "Community 7"
Cohesion: 0.60
Nodes (3): client(), override_get_db(), setup_db()

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (3): BaseSettings, cors_origins(), Settings

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
Cohesion: 0.56
Nodes (12): _auth_header(), _create_account(), _register_and_get_token(), test_cancel_proposal_does_not_execute(), test_confirm_proposal_executes_once_and_records_audit(), test_expired_proposal_does_not_execute(), test_list_proposals_filters_status_exposes_created_at_and_isolates_user(), test_message_creates_proposal_without_mutating_balance() (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.39
Nodes (7): cancel_proposal(), confirm_proposal(), create_proposal(), list_audit_events(), list_proposals(), send_message(), update_proposal()

### Community 28 - "Community 28"
Cohesion: 0.33
Nodes (4): ADR 0001: Phase 1 Modular Monolith, Consequences, Context, Decision

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (17): initials(), SessionContext, SessionContextValue, SessionProfile(), SessionProvider(), SessionUser, useSession(), ThemeContext (+9 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 35 - "Community 35"
Cohesion: 0.11
Nodes (21): dependencies, lucide-react, next, react, react-dom, recharts, @types/node, @types/react (+13 more)

### Community 36 - "Community 36"
Cohesion: 0.08
Nodes (25): authCookies, authRoutes, chart, creditCardFeedback, dashboard, demoDatasetRoute, financialDashboard, financialMutationFeedback (+17 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (10): chartData, metrics, activities, currency, FinancialDashboard(), quickActions, services, FinancialScore (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.18
Nodes (11): build, builder, dockerfilePath, deploy, healthcheckPath, healthcheckTimeout, preDeployCommand, restartPolicyMaxRetries (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (57): DELETE(), mutateAccount(), PUT(), errorResponse(), GET(), POST(), requestBackend(), POST() (+49 more)

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
Cohesion: 0.24
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
Cohesion: 0.80
Nodes (3): production_settings(), test_production_rejects_insecure_origins(), test_production_requires_a_strong_secret()

### Community 64 - "Community 64"
Cohesion: 0.08
Nodes (22): API e segurança, Auditoria atual, Backend, Cadastro e ciclo do cartão, Conteúdo, Dataset demonstrativo, Decisões aprovadas, Direção visual (+14 more)

### Community 65 - "Community 65"
Cohesion: 0.05
Nodes (37): code:python (def test_demo_dataset_and_theme_are_mapped():), code:python (return {"action": action, "category": snapshot}), code:powershell (git add apps/api/app/schemas/financial.py apps/api/app/servi), code:python (def test_install_is_complete_and_idempotent(client):), code:python (class DemoDatasetSummary(BaseModel):), code:python (try:), code:powershell (git add apps/api/app/services/demo_dataset_service.py apps/a), code:typescript (export type DemoDatasetState = {) (+29 more)

### Community 66 - "Community 66"
Cohesion: 0.14
Nodes (9): CategoryManager(), CategoryRow, CategoryDeleteResult, DashboardAccount, DashboardCashFlowPoint, DashboardStatement, DashboardTransaction, FinancialCategory (+1 more)

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (9): links, mobileLinks, moreLinks, pageTitles, primaryLinks, FinChatPanel(), links, NavigationDrawer() (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (8): Base, get_db(), DeclarativeBase, FinancialAccount, Installment, InstallmentPlan, RecurringRule, create_account()

### Community 70 - "Community 70"
Cohesion: 0.23
Nodes (13): CreditCard, DemoDataset, _active_dataset(), _audit(), _build_resources(), clean_demo_dataset(), get_demo_dataset_status(), _has_row() (+5 more)

### Community 71 - "Community 71"
Cohesion: 0.23
Nodes (15): Transaction, _add_months(), confirm_installment(), confirm_recurring_rule(), create_card_purchase(), create_installment_plan(), create_recurring_rule(), create_transaction() (+7 more)

### Community 72 - "Community 72"
Cohesion: 0.15
Nodes (9): currency, DashboardView(), dateFormatter, money(), monthFormatter, CashFlowChart(), CashFlowPoint, compactCurrency (+1 more)

### Community 73 - "Community 73"
Cohesion: 0.60
Nodes (3): _run_migration(), _task_one_migration(), test_alembic_migration_round_trips_sqlite_schema_and_dataset_ownership()

### Community 81 - "Community 81"
Cohesion: 0.25
Nodes (6): BeforeInstallPromptEvent, InstallAppButton(), initials(), loadImage(), prepareAvatar(), ProfileSettings()

### Community 82 - "Community 82"
Cohesion: 0.22
Nodes (6): AccountManager(), accountTypes, formatCurrency(), AppShell(), DashboardData, FinancialAccount

### Community 83 - "Community 83"
Cohesion: 0.23
Nodes (14): Category, create_category(), _assert_public_state(), _register(), test_builder_exception_rolls_back_every_resource_and_audit(), test_cleanup_deletes_only_demo_resources_and_is_repeatable(), test_cleanup_preserves_and_detaches_adopted_demo_graph(), test_cleanup_preserves_demo_parent_with_real_child_category() (+6 more)

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (7): BillingStatement, _due_date(), _get_or_create_statement(), _month_shift(), _statement_cycle(), _statement_period(), _valid_day()

### Community 85 - "Community 85"
Cohesion: 0.33
Nodes (4): metadata, viewport, PWARegistration(), ThemeProvider()

## Knowledge Gaps
- **269 isolated node(s):** `builder`, `dockerfilePath`, `preDeployCommand`, `startCommand`, `healthcheckPath` (+264 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditEvent` connect `Community 0` to `Community 1`, `Community 2`, `Community 69`, `Community 70`, `Community 22`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `Base` connect `Community 69` to `Community 0`, `Community 1`, `Community 70`, `Community 71`, `Community 83`, `Community 84`, `Community 22`, `Community 86`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `update_profile()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `builder`, `dockerfilePath`, `preDeployCommand` to the rest of the system?**
  _271 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08043775649794802 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.09595959595959595 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.0936408106219427 - nodes in this community are weakly interconnected._