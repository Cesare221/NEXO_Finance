# ADR 0001: Phase 1 Modular Monolith

**Status:** Accepted

## Context

O Fin esta nascendo como assistente financeiro pessoal. A Fase 1 precisa entregar controle financeiro funcional sem criar complexidade operacional prematura.

## Decision

Usar um modular monolith:

- `apps/api`: FastAPI, SQLAlchemy, Alembic, Pydantic e PostgreSQL.
- `apps/web`: Next.js, TypeScript, Tailwind e shadcn/ui quando o frontend for criado.
- Separar responsabilidades por dominio: identity, accounts, categories, transactions, cards, billing, installments, recurring, assistant e audit.
- Manter IA como orquestradora; regras financeiras ficam em servicos determinísticos do backend.
- Toda escrita assistida deve passar por ActionProposal, confirmacao explicita, idempotencia e AuditEvent.

## Consequences

- Menor custo de deploy e desenvolvimento local.
- Menos risco de inconsistencia entre servicos.
- O arquivo `financial_service.py` deve ser quebrado gradualmente conforme os dominios crescerem.
- Open Finance, WhatsApp, importacoes e investimentos ficam fora do nucleo inicial.
