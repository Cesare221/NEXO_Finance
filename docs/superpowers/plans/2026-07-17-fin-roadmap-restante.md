# Fin Roadmap Restante

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o Fin rodar como um assistente financeiro pessoal utilizavel de ponta a ponta.

**Architecture:** Continuar a API FastAPI + SQLAlchemy + Alembic ja criada, completar o dominio financeiro no backend e depois adicionar uma web app Next.js. Operacoes feitas pelo agente Fin devem passar por ActionProposal, confirmacao explicita, idempotencia e auditoria.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL, pytest; frontend recomendado: Next.js, TypeScript, Tailwind e shadcn/ui.

## Estado Atual

- [x] Fundacao da API: auth, usuario, sessoes, health check, migrations.
- [x] Contas financeiras e categorias hierarquicas.
- [x] Transacoes basicas: receitas, despesas, historico, filtros, saldo calculado e exclusao logica.
- [ ] Ainda nao existe frontend web.
- [ ] Ainda nao existe ActionProposal/Fin minimo.
- [ ] Ainda faltam transferencias, cartoes, faturas, parcelas, recorrencias e dashboard consolidado.

## Plano Prioritario

### 1. Completar Incremento 3: Transferencias

- [x] Criar modelo `Transfer` com `user_id`, conta origem, conta destino, valor e transacoes vinculadas.
- [x] Criar endpoint `POST /financial/transfers`.
- [x] Criar endpoint `GET /financial/transfers`.
- [x] Ao transferir, criar dois lancamentos vinculados: saida da origem e entrada no destino.
- [x] Garantir que transferencia nao conte como receita nem despesa em relatorios.
- [x] Garantir que usuario B nao consegue usar contas do usuario A.
- [x] Testar saldo: patrimonio total permanece igual.

### 2. Implementar Incremento 4: Cartoes e Faturas

- [ ] Criar modelos `CreditCard` e `BillingStatement`.
- [ ] Criar endpoints CRUD para cartoes.
- [ ] Associar cartao a uma conta de pagamento.
- [ ] Registrar compra no cartao sem reduzir saldo bancario.
- [ ] Reduzir limite disponivel do cartao ao registrar compra.
- [ ] Associar compra a fatura correta por fechamento/vencimento.
- [ ] Criar pagamento de fatura que reduz saldo da conta.
- [ ] Garantir que pagamento de fatura nao cria nova despesa duplicada.
- [ ] Testar isolamento por `user_id`.

### 3. Implementar Incremento 5: Parcelas e Recorrencias

- [ ] Criar modelos `InstallmentPlan`, `Installment` e `RecurringRule`.
- [ ] Criar parcelamento simples para despesas e compras no cartao.
- [ ] Criar parcelas vinculadas ao plano original.
- [ ] Criar recorrencias previstas como pendentes.
- [ ] Confirmar previsao para gerar lancamento efetivo.
- [ ] Permitir ajuste manual de valor real.
- [ ] Tratar pagamento parcial, atraso e encargos manuais de forma simples.
- [ ] Testar que previsao nao altera saldo ate ser confirmada.

### 4. Implementar Incremento 6: Dashboard

- [ ] Criar endpoint `GET /financial/dashboard`.
- [ ] Retornar saldo atual por conta e total.
- [ ] Retornar receitas e despesas do periodo.
- [ ] Retornar faturas abertas e proximos vencimentos.
- [ ] Retornar movimentacoes recentes.
- [ ] Preparar campos para saldo previsto e valor seguro para gastar.
- [ ] Testar dashboard com contas, despesas, receitas, cartao e recorrencias.

### 5. Implementar Incremento 7: Fin Minimo com ActionProposal

- [ ] Criar modelos `ActionProposal`, `ActionExecution` e `AuditEvent`.
- [ ] Implementar estados: `draft`, `proposed`, `confirmed`, `executed`, `cancelled`, `expired`, `failed`.
- [ ] Criar endpoints para listar, criar, editar, confirmar e cancelar propostas.
- [ ] Garantir que proposta em `proposed` nao altera dados financeiros.
- [ ] Executar somente apos confirmacao explicita do usuario autenticado.
- [ ] Implementar idempotencia por `idempotency_key`.
- [ ] Registrar auditoria em toda execucao, cancelamento e falha.
- [ ] Criar parser deterministico inicial para frases simples, como "gastei 35 no mercado".
- [ ] Criar ferramentas somente leitura para perguntas sobre saldo, gastos e vencimentos.

### 6. Criar Frontend Web Usavel

- [x] Criar `apps/web` com Next.js + TypeScript.
- [x] Tela de login e cadastro.
- [x] Layout principal com navegacao: Dashboard, Contas, Categorias, Transacoes, Cartoes, Fin.
- [ ] CRUD de contas e categorias conectado a API.
- [ ] Formulario rapido de receita/despesa/transferencia conectado a API.
- [x] Historico com filtros visual.
- [x] Dashboard visual.
- [x] Tela de cartoes e faturas visual.
- [x] Chat do Fin com cards de Confirmar, Editar e Cancelar para propostas.

### 7. Segurança e Qualidade

- [ ] Remover secrets fixos do codigo e documentar `.env.example`.
- [ ] Garantir que nenhum endpoint aceite `user_id` do cliente.
- [ ] Padronizar erros sem expor stack trace.
- [ ] Adicionar CORS restrito por ambiente.
- [ ] Adicionar testes de integracao para isolamento multiusuario.
- [ ] Adicionar testes de idempotencia.
- [ ] Adicionar testes de auditoria.
- [ ] Validar Decimal/Numeric em todos os fluxos de dinheiro.

### 8. Operacao Local e Deploy

- [ ] Criar README com comandos para rodar API, web, migrations e testes.
- [ ] Criar `docker-compose.yml` para PostgreSQL local.
- [ ] Criar seed de desenvolvimento.
- [ ] Criar script de reset do banco local.
- [ ] Garantir `alembic upgrade head` no fluxo de setup.
- [ ] Preparar variaveis de ambiente para producao.

## Ordem Recomendada de Execucao

1. Transferencias.
2. Cartoes e faturas.
3. Parcelas e recorrencias.
4. Dashboard backend.
5. ActionProposal + auditoria.
6. Frontend web.
7. Chat Fin conectado a propostas.
8. Hardening de seguranca, docs e deploy.

## Criterio de App Rodando Bem

- [ ] Usuario cria conta e categoria.
- [ ] Usuario registra receita, despesa e transferencia.
- [ ] Usuario cadastra cartao, compra no cartao e paga fatura sem duplicar despesa.
- [ ] Usuario cria recorrencia e confirma lancamento real.
- [ ] Dashboard mostra saldo, gastos, receitas, faturas e vencimentos.
- [ ] Fin interpreta pedido de escrita, cria proposta e so executa apos confirmacao.
- [ ] Todas as operacoes financeiras registram auditoria.
- [ ] Usuario A nunca acessa dados do usuario B.
- [ ] Testes automatizados passam.
