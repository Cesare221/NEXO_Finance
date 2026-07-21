# Nexo Dashboard, Fin Panel and Review Inbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o primeiro incremento dashboard-first do Nexo com dados reais, menu sanduiche global, painel responsivo do Fin e movimentacoes reconhecidas agrupadas para aprovacao.

**Architecture:** O FastAPI continua como fonte de verdade para dados financeiros e propostas. O Next.js usa rotas BFF autenticadas com cookies HttpOnly; `AppShell` passa a controlar barra superior, drawer e painel do Fin, enquanto um provider compartilhado sincroniza propostas pendentes entre chat, menu e dashboard.

**Tech Stack:** Next.js 15, React 19, TypeScript, Recharts, FastAPI, SQLAlchemy, Alembic, pytest.

## Global Constraints

- `/dashboard` permanece como rota inicial autenticada.
- `Nexo` identifica o produto; `Fin` identifica somente o agente.
- Menu sanduiche e o unico gatilho de navegacao global em todos os breakpoints.
- O painel do Fin fica na direita em telas com pelo menos 1180 px e vira overlay abaixo disso.
- Propostas reconhecidas nunca alteram dados antes da aprovacao.
- Cookies `fin_access_token` e `fin_refresh_token` permanecem inalterados para preservar sessoes.
- Dados financeiros autenticados nao entram no cache do service worker.

---

### Task 1: Branding Nexo

**Files:**
- Modify: `apps/web/app/layout.tsx`
- Modify: `apps/web/app/manifest.ts`
- Modify: `apps/web/components/app-shell.tsx`
- Modify: `apps/web/app/login/page.tsx`
- Modify: `apps/web/app/cadastro/page.tsx`
- Modify: `apps/web/app/offline/page.tsx`
- Modify: `apps/web/app/configuracoes/page.tsx`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: produto visivel como `Nexo`; agente permanece `Fin`.

- [ ] Atualizar o smoke test para exigir `Nexo` nos metadados, manifesto e shell, e manter `FinConversation` como nome do agente.
- [ ] Executar `npm test` e observar falha de branding.
- [ ] Trocar textos e metadados de produto sem renomear cookies, rotas ou contratos de API.
- [ ] Executar `npm test` e `npx tsc --noEmit` ate ambos passarem.

### Task 2: Dashboard real e tipado

**Files:**
- Modify: `apps/api/app/services/financial_service.py`
- Modify: `apps/api/app/api/financial.py`
- Modify: `apps/api/app/schemas/financial.py`
- Create: `apps/web/app/api/financial/dashboard/route.ts`
- Create: `apps/web/lib/financial-types.ts`
- Create: `apps/web/components/dashboard-view.tsx`
- Modify: `apps/web/app/dashboard/page.tsx`
- Test: `apps/api/tests/test_financial.py`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: `GET /financial/dashboard` com `total_balance`, `period_income`, `period_expenses`, `open_statement_total`, `cash_flow`, `recent_transactions`, `upcoming_due` e `accounts`.
- Produces: `GET /api/financial/dashboard?months=6` autenticado pelo BFF.

- [ ] Escrever teste pytest com receitas e despesas em meses diferentes e esperar serie mensal agregada e totais reais.
- [ ] Executar o teste alvo e confirmar falha por ausencia de `cash_flow` e `open_statement_total`.
- [ ] Implementar schemas de resposta e agregacao mensal no servico sem consultas fora do usuario autenticado.
- [ ] Criar BFF reutilizando `authenticatedBackendRequest` e renovacao de sessao.
- [ ] Criar `DashboardView` com estados loading, empty, error e success; remover valores financeiros fixos.
- [ ] Executar teste alvo, suite financeira, smoke test e TypeScript.

### Task 3: Propostas pendentes como inbox

**Files:**
- Modify: `apps/api/app/schemas/assistant.py`
- Modify: `apps/api/app/api/assistant.py`
- Modify: `apps/api/app/services/assistant_service.py`
- Create: `apps/web/app/api/assistant/proposals/route.ts`
- Create: `apps/web/components/pending-proposals-provider.tsx`
- Create: `apps/web/components/movement-review-inbox.tsx`
- Modify: `apps/web/components/fin-conversation.tsx`
- Test: `apps/api/tests/test_assistant.py`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: `GET /assistant/proposals?status=proposed` filtrado por usuario e com `created_at`.
- Produces: `usePendingProposals(): { proposals, loading, error, refresh, actOnProposal }`.
- Produces: evento `nexo:proposals-changed` apos criar, editar, aprovar ou rejeitar proposta.

- [ ] Escrever teste para filtro por status, isolamento por usuario e `created_at` na resposta.
- [ ] Executar teste alvo e confirmar falha do novo contrato.
- [ ] Implementar filtro opcional e expor `created_at` sem migracao de banco.
- [ ] Criar rota BFF GET e provider compartilhado.
- [ ] Implementar grupos por origem, conta e data, selecao explicita e aprovacoes idempotentes item a item.
- [ ] Bloquear selecao em lote quando `possible_duplicate` ou `confidence < 0.7` estiver no payload.
- [ ] Executar testes da API, smoke e TypeScript.

### Task 4: AppShell com hamburger e Fin global

**Files:**
- Create: `apps/web/components/navigation-drawer.tsx`
- Create: `apps/web/components/fin-chat-panel.tsx`
- Modify: `apps/web/components/app-shell.tsx`
- Modify: `apps/web/components/fin-conversation.tsx`
- Modify: `apps/web/app/fin/page.tsx`
- Modify: `apps/web/app/globals.css`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Consumes: `usePendingProposals()` da Task 3.
- Produces: `NavigationDrawer({ open, onClose })` com foco preso e restaurado.
- Produces: `FinChatPanel({ open, onClose })` fixo no desktop e modal abaixo de 1180 px.

- [ ] Atualizar smoke test para exigir `Menu principal`, `NavigationDrawer`, `FinChatPanel`, badge e ausencia de sidebar/bottom-nav legadas.
- [ ] Executar smoke test e confirmar falha.
- [ ] Extrair drawer com links, perfil, badge, Escape, scrim e foco inicial.
- [ ] Integrar topbar fixa e workspace em duas colunas, mantendo dashboard como conteudo principal.
- [ ] Adaptar conversa para variante compacta e notificar o provider quando propostas mudarem.
- [ ] Implementar CSS responsivo para 320, 768, 1180 e 1440 px sem overflow.
- [ ] Executar smoke test e TypeScript.

### Task 5: Dashboard review surface

**Files:**
- Modify: `apps/web/components/dashboard-view.tsx`
- Modify: `apps/web/components/movement-review-inbox.tsx`
- Modify: `apps/web/app/globals.css`
- Test: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Consumes: `MovementReviewInbox` e dados reais do dashboard.
- Produces: aviso compacto de pendencias e inbox expansivel dentro do dashboard.

- [ ] Adicionar marcadores de smoke para agrupamento, aprovar selecionadas, editar/rejeitar e estados vazios.
- [ ] Renderizar inbox antes das metricas quando houver pendencias e em estado compacto quando vazio.
- [ ] Garantir que aprovar atualize simultaneamente inbox, badge e dados do dashboard.
- [ ] Executar smoke, TypeScript e build de producao.

### Task 6: Verificacao integrada

**Files:**
- Modify: `docs/superpowers/plans/2026-07-17-nexo-dashboard-fin-inbox.md`

**Interfaces:**
- Verifica todos os contratos produzidos nas Tasks 1 a 5.

- [ ] Executar `python -m pytest -q` em `apps/api` e exigir zero falhas.
- [ ] Executar `npm test`, `npx tsc --noEmit`, `npm run build` e `npm audit --omit=dev` em `apps/web`.
- [ ] Reiniciar API e frontend se hot reload nao refletir o novo shell.
- [ ] Validar no navegador cadastro/login, dashboard real, drawer, painel do Fin, proposta pendente, rejeicao e aprovacao.
- [ ] Validar 1440x900, 1024x768 e 390x844 sem overflow, sobreposicao incoerente ou controles cortados.
- [ ] Executar `graphify update .`.
