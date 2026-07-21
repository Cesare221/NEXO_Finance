# Graph Report - Fin  (2026-07-20)

## Corpus Check
- 133 files · ~176,617 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 903 nodes · 1509 edges · 67 communities (64 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9315ed9d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 28|Community 28]]
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
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 70|Community 70]]

## God Nodes (most connected - your core abstractions)
1. `_register_and_get_token()` - 47 edges
2. `_auth_header()` - 47 edges
3. `setAuthCookies()` - 42 edges
4. `publicAuthError()` - 41 edges
5. `clearAuthCookies()` - 39 edges
6. `validateRequestOrigin()` - 37 edges
7. `authenticatedBackendRequest()` - 36 edges
8. `_create_account()` - 31 edges
9. `Base` - 16 edges
10. `TestCategories` - 16 edges

## Surprising Connections (you probably didn't know these)
- `ActionExecution` --uses--> `Base`  [INFERRED]
  apps/api/app/models/action_execution.py → apps/api/app/core/database.py
- `ActionProposal` --uses--> `Base`  [INFERRED]
  apps/api/app/models/action_proposal.py → apps/api/app/core/database.py
- `BillingStatement` --uses--> `Base`  [INFERRED]
  apps/api/app/models/billing_statement.py → apps/api/app/core/database.py
- `Category` --uses--> `Base`  [INFERRED]
  apps/api/app/models/category.py → apps/api/app/core/database.py
- `CreditCard` --uses--> `Base`  [INFERRED]
  apps/api/app/models/credit_card.py → apps/api/app/core/database.py

## Communities (67 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (11): _auth_header(), _create_account(), _create_category(), _register_and_get_token(), TestAccounts, TestCategories, TestCreditCards, TestDashboard (+3 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (33): _check_rate_limit(), _client_host(), login(), logout(), me(), refresh(), register(), update_me() (+25 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (44): BillingStatement, Category, CreditCard, FinancialAccount, Installment, InstallmentPlan, RecurringRule, Transaction (+36 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (40): BaseModel, ActionExecutionResponse, ActionProposalCreate, ActionProposalResponse, ActionProposalUpdate, AssistantMessageRequest, AssistantMessageResponse, AuditEventResponse (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.40
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (17): ActionExecution, ActionProposal, _audit(), _aware(), cancel_proposal(), confirm_proposal(), create_proposal(), _execute_create_transaction() (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (13): 1. Completar Incremento 3: Transferencias, 2. Implementar Incremento 4: Cartoes e Faturas, 3. Implementar Incremento 5: Parcelas e Recorrencias, 4. Implementar Incremento 6: Dashboard, 5. Implementar Incremento 7: Fin Minimo com ActionProposal, 6. Criar Frontend Web Usavel, 7. Segurança e Qualidade, 8. Operacao Local e Deploy (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (11): Arquitetura Atual, Execution Rule, Fin Phase 1 Implementation Plan, Global Constraints, Inventario Atual, Status de Execucao, Task 1: Parcelas e Recorrencias, Task 2: Dashboard Backend (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.11
Nodes (22): Banco E Migrations, code:powershell (cd apps/api), code:powershell (cd apps/web), code:powershell (cd apps/api), code:powershell (cd apps/api), code:powershell (cd apps/api), code:text (http://localhost:3000), code:powershell (cd apps/api) (+14 more)

### Community 26 - "Community 26"
Cohesion: 0.50
Nodes (12): _auth_header(), _create_account(), _register_and_get_token(), test_cancel_proposal_does_not_execute(), test_confirm_proposal_executes_once_and_records_audit(), test_expired_proposal_does_not_execute(), test_list_proposals_filters_status_exposes_created_at_and_isolates_user(), test_message_creates_proposal_without_mutating_balance() (+4 more)

### Community 28 - "Community 28"
Cohesion: 0.40
Nodes (4): ADR 0001: Phase 1 Modular Monolith, Consequences, Context, Decision

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (6): BeforeInstallPromptEvent, InstallAppButton(), initials(), loadImage(), prepareAvatar(), ProfileSettings()

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (21): dependencies, lucide-react, next, react, react-dom, recharts, @types/node, @types/react (+13 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (16): authCookies, authRoutes, chart, dashboard, financialDashboard, layout, middleware, missing (+8 more)

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (3): metadata, viewport, PWARegistration()

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (11): build, builder, dockerfilePath, deploy, healthcheckPath, healthcheckTimeout, preDeployCommand, restartPolicyMaxRetries (+3 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (52): DELETE(), mutateAccount(), PUT(), errorResponse(), GET(), POST(), requestBackend(), POST() (+44 more)

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): contentSecurityPolicy, nextConfig, securityHeaders

### Community 44 - "Community 44"
Cohesion: 0.06
Nodes (35): Border Radius Scale, Brand & Accent, Breakpoints, Buttons, Cards & Containers, Collapsing Strategy, Colors, Components (+27 more)

### Community 45 - "Community 45"
Cohesion: 0.50
Nodes (3): APP_SHELL, copy, url

### Community 48 - "Community 48"
Cohesion: 0.08
Nodes (20): currency, DashboardView(), dateFormatter, money(), monthFormatter, chartData, metrics, DashboardTransaction (+12 more)

### Community 49 - "Community 49"
Cohesion: 0.20
Nodes (9): Authentication Flow, Backend Hardening, Context, Decision, Deferred Managed Identity, Fin Public Authentication and Security Design, Security Headers and PWA, Testing (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (14): FinMascot(), AssistantResponse, ChatMessage, FinConversation(), suggestions, notifyProposalsChanged(), PendingProposalsContext, PendingProposalsContextValue (+6 more)

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (7): Fin Public Authentication and Security Implementation Plan, Global Constraints, Task 1: Harden FastAPI Authentication, Task 2: Add the Next.js Authentication Facade, Task 3: Build Accessible Login and Registration UX, Task 4: Add Session Profile and Logout, Task 5: Add Security Headers and Complete Verification

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (19): Acessibilidade e responsividade, Arquitetura de componentes, Barra superior, Caixa de conversa do Fin, Central de movimentacoes reconhecidas, Conversa e revisao, Criterios de aceite, Dados e API (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.06
Nodes (16): AccountManager(), accountTypes, formatCurrency(), CategoryOption, CategoryRow, CategoryOption, TransactionManager(), TransactionType (+8 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (10): API No Railway, Arquitetura Recomendada, Backups, Checklist De Produção, code:text (ENVIRONMENT=production), code:text (GET https://api.seudominio.com/health -> 200 {"status":"ok"}), Implantação Do Nexo, Rollback (+2 more)

### Community 56 - "Community 56"
Cohesion: 0.22
Nodes (8): Global Constraints, Nexo Dashboard, Fin Panel and Review Inbox Implementation Plan, Task 1: Branding Nexo, Task 2: Dashboard real e tipado, Task 3: Propostas pendentes como inbox, Task 4: AppShell com hamburger e Fin global, Task 5: Dashboard review surface, Task 6: Verificacao integrada

### Community 57 - "Community 57"
Cohesion: 0.25
Nodes (6): AppShellContent(), currency, dateFormatter, MovementReviewInbox(), ProposalGroup, usePendingProposals()

### Community 58 - "Community 58"
Cohesion: 0.21
Nodes (10): links, NavigationDrawer(), NavigationDrawerProps, initials(), SessionContext, SessionContextValue, SessionProfile(), SessionProvider() (+2 more)

### Community 59 - "Community 59"
Cohesion: 0.24
Nodes (6): AuthForm(), AuthFormProps, BrandAssetProps, FinMascotProps, NexoLogo(), NexoMark()

### Community 61 - "Community 61"
Cohesion: 0.40
Nodes (4): buildCommand, framework, installCommand, $schema

### Community 62 - "Community 62"
Cohesion: 0.83
Nodes (3): production_settings(), test_production_rejects_insecure_origins(), test_production_requires_a_strong_secret()

### Community 64 - "Community 64"
Cohesion: 0.09
Nodes (22): API e segurança, Auditoria atual, Backend, Cadastro e ciclo do cartão, Conteúdo, Dataset demonstrativo, Decisões aprovadas, Direção visual (+14 more)

### Community 65 - "Community 65"
Cohesion: 0.05
Nodes (37): code:python (def test_demo_dataset_and_theme_are_mapped():), code:python (return {"action": action, "category": snapshot}), code:powershell (git add apps/api/app/schemas/financial.py apps/api/app/servi), code:python (def test_install_is_complete_and_idempotent(client):), code:python (class DemoDatasetSummary(BaseModel):), code:python (try:), code:powershell (git add apps/api/app/services/demo_dataset_service.py apps/a), code:typescript (export type DemoDatasetState = {) (+29 more)

### Community 70 - "Community 70"
Cohesion: 0.14
Nodes (9): AppShell(), links, mobileLinks, moreLinks, pageTitles, primaryLinks, CardManager(), CategoryManager() (+1 more)

## Knowledge Gaps
- **254 isolated node(s):** `$schema`, `builder`, `dockerfilePath`, `preDeployCommand`, `startCommand` (+249 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Base` connect `Community 1` to `Community 2`, `Community 22`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `TokenResponse` connect `Community 1` to `Community 3`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **What connects `$schema`, `builder`, `dockerfilePath` to the rest of the system?**
  _256 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10695499707773232 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07358156028368794 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.06641604010025062 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.07585568917668825 - nodes in this community are weakly interconnected._