# Implementação Final — Nexo v1

> Status em 2026-07-30: o código local foi revisado e corrigido, mas o sistema
> **ainda não está pronto para produção real**. O que falta agora é concluir
> infraestrutura externa, staging real, validação operacional, segurança e LGPD.
> Não realizar deploy em produção sem aprovação explícita.

---

## Sumário

0. [Estado Atual Validado](#0-estado-atual-validado)
1. [Domínio E DNS](#1-domínio-e-dns)
2. [Contas De Plataforma](#2-contas-de-plataforma)
3. [Configuração Das Plataformas](#3-configuração-das-plataformas)
4. [Deploy E Validação Em Staging](#4-deploy-e-validação-em-staging)
5. [Validação Operacional](#5-validação-operacional)
6. [Adequação Legal LGPD](#6-adequação-legal-lgpd)
7. [Segurança E Pentest](#7-segurança-e-pentest)
8. [Deploy Em Produção](#8-deploy-em-produção)
9. [Checklist Consolidado](#9-checklist-consolidado)
10. [Estimativa De Esforço](#10-estimativa-de-esforço)

---

## 0. Estado Atual Validado

### Correções De Código Já Aplicadas

- Rotas BFF críticas deixaram de usar mocks:
  - `apps/web/app/api/auth/session/route.ts` voltou a usar cookies, backend, refresh token, validação de origem e limpeza de sessão em 401.
  - `apps/web/app/api/financial/dashboard/route.ts` voltou a usar proxy autenticado real para `/financial/dashboard`.
- Sentry/Next.js corrigido:
  - `onRouterTransitionStart` no client instrumentation.
  - `onRequestError` no server instrumentation.
  - substituição de `disableLogger` por `webpack.treeshake.removeDebugLogging`.
- CI corrigido:
  - caminho correto para `scripts/check-migration-head.py`.
  - execução correta do scanner PowerShell de segredos.
- Lockfiles da API sincronizados com `sentry-sdk`.
- Validação de `API_URL` ajustada para permitir `localhost` apenas em builds locais e exigir HTTPS para URLs reais.
- Compose production-like ajustado para `ENVIRONMENT=staging`, pois `production` deve rejeitar configurações locais como `http://localhost`.

### Validações Locais Executadas

- Frontend:
  - `npm test`: PASS.
  - `npx tsc --noEmit`: PASS.
  - `npm run build`: SUCCESS.
  - `npm audit --audit-level=high`: PASS.
  - `node --check public/sw.js`: PASS.
  - frontend buildado iniciou e respondeu HTTP 200.
- Backend:
  - `uv run pytest -q`: PASS.
  - `uv run pytest tests/test_observability.py -v -q`: 13 passed, 1 warning de deprecação.
  - observabilidade importou e inicializou com sucesso.
  - `uv run pip-audit --progress-spinner off`: sem vulnerabilidades conhecidas.
  - API iniciou localmente e `/health` respondeu HTTP 200.
- Scripts/CI:
  - `python scripts/check-migration-head.py`: PASS.
  - `python ../../scripts/check-migration-head.py` a partir de `apps/api`: PASS.
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-secrets.ps1`: PASS.
  - `git diff --check`: PASS; apenas avisos LF/CRLF do Git no Windows.
- Docker production-like:
  - Docker client/server `29.5.3 / 29.5.3`.
  - imagens `nexo_finance-api`, `nexo_finance-migrate` e `nexo_finance-web` geradas.
  - `docker compose -f docker-compose.production-like.yml config --quiet`: PASS.
  - stack subiu com Postgres, Redis, migrate, API e web.
  - API, Postgres e Redis ficaram `healthy`; web ficou `Up`.
  - `http://localhost:8000/health`: HTTP 200.
  - `http://localhost:8000/ready`: HTTP 200 com `database=ok`.
  - `http://localhost:3011`: HTTP 200.
  - logs recentes de `api`, `web` e `migrate` sem `error`, `exception`, `traceback`, `failed`, `fatal` ou `warn`.

### O Que Ainda Falta

- Configurar ambientes reais `staging` e `production` em GitHub, Vercel, Railway, Resend, Sentry e Groq.
- Provisionar PostgreSQL e Redis reais no Railway e executar migrations em staging.
- Configurar domínios HTTPS reais, DNS, CORS, cookies `Secure`, SPF, DKIM e DMARC.
- Executar smoke autenticado contra staging com `SMOKE_EMAIL`, `SMOKE_PASSWORD` e `SMOKE_TOTP_SECRET`.
- Validar em navegador real/responsivo com console limpo.
- Validar e-mails reais via Resend.
- Configurar Sentry com scrubbing, releases e alertas.
- Solicitar/confirmar Groq Zero Data Retention.
- Fazer restore drill.
- Completar dados LGPD reais: controlador, CNPJ, DPO, canal de contato e políticas publicadas.
- Realizar pentest independente autenticado e não autenticado.

Relatório detalhado da revisão: `docs/REVIEW_FIX_REPORT_2026-07-30.md`.

---

## 1. Domínio E DNS

### Comprar Domínio

Registrar um domínio real (ex: `nexo.com.br` ou `nexofinanceiro.com.br`).

### Registrar DNS

Após criar os projetos na Vercel e Railway, criar os seguintes registros:

| Tipo | Nome | Valor |
|------|------|-------|
| CNAME | `app` | `<vercel-project>.vercel.app` |
| CNAME | `api` | `<railway-project>.railway.app` |
| CNAME | `app-staging` | `<vercel-preview>.vercel.app` |
| CNAME | `api-staging` | `<railway-staging>.railway.app` |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@seudominio.com` |
| TXT | `@` | `v=spf1 include:_spf.resend.com ~all` |
| CNAME | `default._domainkey` | Valor fornecido pelo Resend |

> **Nota:** Os domínios de staging podem ser os domínios temporários da Vercel/Railway
> durante a validação inicial.

**Referência:** `docs/DNS_AND_EMAIL.md`

---

## 2. Contas De Plataforma

### 2.1 Vercel

Criar conta em [vercel.com](https://vercel.com) (plana Hobby é suficiente para começar).

### 2.2 Railway

Criar conta em [railway.com](https://railway.com). O plano Developer (US$5/mês)
cobre PostgreSQL, Redis e dois serviços.

### 2.3 Resend

Criar conta em [resend.com](https://resend.com) para envio de e-mails
transacionais (verificação, recovery, MFA).

### 2.4 Sentry

Criar dois projetos no Sentry:
- `nexo-api` (Python/FastAPI)
- `nexo-web` (Next.js)

Cada projeto com ambientes `staging` e `production`.

### 2.5 Groq

Criar conta em [groq.com](https://groq.com) e gerar chave de API.
**Solicitar ativação de Zero Data Retention (ZDR)** para não armazenamento
de prompts/respostas.

### 2.6 GitHub

Garantir que o repositório tem acesso a GitHub Actions (público ou plano grátis).

---

## 3. Configuração Das Plataformas

### 3.1 GitHub Environments

Criar em Settings → Environments:

| Environment | Proteção |
|-------------|----------|
| `staging` | Nenhuma |
| `production` | Required reviewers: 1 operador |

**Secrets (por ambiente):**

| Secret | De Onde Obter |
|--------|---------------|
| `RAILWAY_TOKEN` | Railway → Account → Tokens |
| `RAILWAY_PROJECT_ID` | URL do projeto Railway |
| `RAILWAY_ENVIRONMENT_ID` | URL do ambiente Railway |
| `RAILWAY_SERVICE_ID` | URL do serviço API |
| `VERCEL_TOKEN` | Vercel → Settings → Tokens |
| `VERCEL_ORG_ID` | `vercel inspect` ou team settings |
| `VERCEL_PROJECT_ID` | `vercel inspect` ou project settings |
| `SMOKE_EMAIL` | E-mail do usuário de teste |
| `SMOKE_PASSWORD` | Senha do usuário de teste |
| `SMOKE_TOTP_SECRET` | Secret TOTP do MFA do teste |

**Variables (por ambiente):**

| Variable | Staging | Production |
|----------|---------|------------|
| `API_URL` | `https://api-staging.seudominio.com` | `https://api.seudominio.com` |
| `WEB_URL` | `https://app-staging.seudominio.com` | `https://app.seudominio.com` |

### 3.2 Railway

**Serviços a criar:**

1. **PostgreSQL** — gerenciado, daily backups, 30/12/12 retention
2. **Redis** — gerenciado, multi-instance (primary + replica)
3. **API** — Dockerfile a partir de `apps/api/`, Root Directory = `apps/api`
4. **Cron** — mesmo Dockerfile, sem porta pública, schedule `17 3 * * *`

**Configuração do serviço API (railway.json já no repo):**

```json
{
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

**Variáveis de ambiente (Railway):**

```
ENVIRONMENT=staging|production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<64+ caracteres aleatórios>
ALLOWED_ORIGINS=https://app-staging.seudominio.com,https://app.seudominio.com
ALLOWED_HOSTS=api-staging.seudominio.com,api.seudominio.com
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
GROQ_API_KEY=<chave-groq>
GROQ_BASE_URL=https://api.groq.com/openai/v1
TRUSTED_PROXY_IPS=<IPs dos LBs da Railway>
MAIL_PROVIDER=resend
RESEND_API_KEY=<chave-resend>
EMAIL_FROM=Nexo <no-reply@seudominio.com>
PUBLIC_WEB_URL=https://app.seudominio.com
EMAIL_VERIFICATION_TTL_MINUTES=30
PASSWORD_RESET_TTL_MINUTES=20
MFA_CHALLENGE_TTL_MINUTES=5
MFA_ENCRYPTION_KEYS=v1:<chave-fernet-64-caracteres>
MFA_ACTIVE_KEY_VERSION=v1
SENTRY_DSN=<dsn-nexo-api>
SENTRY_ENVIRONMENT=staging|production
SENTRY_RELEASE=<git-sha>
SENTRY_TRACES_SAMPLE_RATE=0.1
```

> **Staging e produção** devem ter valores diferentes para SECRET_KEY,
> SENTRY_DSN, MFA_ENCRYPTION_KEYS, chaves de API, e domínios.

### 3.3 Vercel

**Configuração do projeto:**

- Root Directory: `apps/web`
- Framework: Next.js
- Install Command: `npm ci`
- Build Command: `npm run build`
- Output Directory: `.next`

**Variáveis de ambiente:**

| Variable | Staging | Production |
|----------|---------|------------|
| `API_URL` | `https://api-staging.seudominio.com` | `https://api.seudominio.com` |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN staging nexo-web | DSN production nexo-web |
| `SENTRY_DSN` | DSN staging nexo-web | DSN production nexo-web |
| `SENTRY_ENVIRONMENT` | `staging` | `production` |
| `SENTRY_RELEASE` | `$(git rev-parse --short HEAD)` | `$(git rev-parse --short HEAD)` |
| `SENTRY_AUTH_TOKEN` | Token build-only scoped | Token build-only scoped |

**Git Integration:**

- Production Branch: `production-locked` (ou branch que nunca auto-mergeia)
- Preview Deployments: enabled
- Production Deployments: only via CLI/API (nosso workflow)

### 3.4 Sentry

**Dois projetos:**

| Projeto | Plataforma | Ambientes |
|---------|------------|-----------|
| `nexo-api` | Python/FastAPI | `staging`, `production` |
| `nexo-web` | Next.js | `staging`, `production` |

**Configuração comum:**

- `send_default_pii = false`
- Scrubbing: cookies, authorization, email, phone, ip_address, amount, balance, token, code, chat_message, request_body
- Release naming: Git short SHA

**Regras de alerta (ambos os projetos):**

| Regra | Condição | Ação |
|-------|----------|------|
| New Regression | Primeira ocorrência de erro no release | Notificar responsável |
| Error Rate Spike | 5x baseline por 5 minutos | Notificar responsável |
| Readiness Failure | `/ready` falha 3+ minutos seguidos | Notificar responsável |
| Auth Abuse Spike | 401/403 > 50/minuto | Notificar segurança |

### 3.5 Resend

**Configuração:**

1. Adicionar domínio em Resend (ex: `seudominio.com`)
2. Resend fornece valores DKIM/SPF — adicionar ao DNS
3. Aguardar verificação do domínio
4. Criar identidade de remetente: `Nexo <no-reply@seudominio.com>`
5. Criar chave de API dedicada para produção
6. Configurar webhook de eventos de entrega

### 3.6 Groq

1. Gerar chave de API de produção
2. Gerar chave de API de staging separada
3. **Solicitar ativação de Zero Data Retention (ZDR)**
4. Revisar termos de serviço para compatibilidade com dados financeiros

---

## 4. Deploy E Validação Em Staging

### 4.1 Primeiro Deploy Manual

```bash
# Da raiz do repositório
gh workflow run deploy.yml -f environment=staging -f git_sha=$(git rev-parse HEAD)
```

### 4.2 Validar Deploy

- [ ] Healthcheck `/ready` retorna 200 com `database=ok, redis=ok`
- [ ] Healthcheck `/health` retorna 200
- [ ] Aplicação web carrega no domínio de staging
- [ ] Smoke tests de produção passam (executados automaticamente pelo workflow)

### 4.3 Validar Migrações

- [ ] `alembic upgrade head` executou com sucesso (pré-deploy)
- [ ] Cabeçalho único: `e3b7a12c9d40`

---

## 5. Validação Operacional

### 5.1 Ciclo De Identidade

Testar manualmente em staging:

- [ ] Registro → e-mail de verificação chega (Resend)
- [ ] Link de verificação → conta verificada → login funciona
- [ ] Login → access + refresh tokens
- [ ] Refresh automático funciona
- [ ] Logout revoga refresh token
- [ ] Recuperação de senha (request + confirm)
- [ ] MFA: enrollment (QR + manual) → challenge → códigos de recuperação
- [ ] MFA login com TOTP
- [ ] MFA login com recovery code
- [ ] MFA disable com senha + TOTP/recovery
- [ ] Exclusão de conta

### 5.2 Ciclo Financeiro

- [ ] Criar conta, categoria, transação, cartão
- [ ] Listar com filtros e paginação
- [ ] Dashboard carrega com dados corretos
- [ ] Dataset demonstrativo: instalar e limpar
- [ ] Fin: propor → aprovar → executar
- [ ] Fin: propor → cancelar

### 5.3 Sentry

- [ ] Evento de teste aparece no ambiente `staging` do Sentry
- [ ] Alertas disparam (triggerar erro sintético)

### 5.4 PWA E Mobile

- [ ] Manifest válido, ícones 192/512
- [ ] Service worker registra e cacheia
- [ ] Instalação no Android (Chrome)
- [ ] Instalação no iOS (Safari)
- [ ] Offline page exibe quando desconectado
- [ ] Responsivo em 375px, 768px, 1440px
- [ ] Sem layout shift no carregamento

### 5.5 Restore Drill

- [ ] Executar backup manual no Railway
- [ ] Restaurar em um banco isolado (staging)
- [ ] Rodar `python scripts/verify_restored_database.py` — aprovado
- [ ] Smoke tests passam contra o banco restaurado
- [ ] Registrar duração, resultado, evidência

---

## 6. Adequação Legal LGPD

### 6.1 Aviso De Privacidade

Em `docs/SECURITY_AND_LGPD.md` e no rodapé da aplicação, preencher:

- [ ] **Operador:** Nome/CNPJ da entidade responsável
- [ ] **Encarregado (DPO):** Nome completo
- [ ] **E-mail do DPO:** Endereço para contato
- [ ] **Canal LGPD:** Caminho para exercer direitos (e-mail + formulário)
- [ ] **Prazo de resposta:** 15 dias úteis (Art. 18 LGPD)

Dados cadastrais para a política:

| Campo | Valor |
|-------|-------|
| Controlador | `[NOME_EMPRESA]` — `[CNPJ]` |
| Encarregado | `[NOME_DPO]` — `[EMAIL]` |
| Contato LGPD | `[EMAIL/CANAL]` |

### 6.2 Subprocessadores

Documentar e divulgar na política:

| Subprocessador | Finalidade | Dados |
|----------------|------------|-------|
| Railway | Hospedagem da API, banco, Redis | Todos os dados |
| Vercel | Hospedagem do frontend | Dados de navegação |
| Resend | Envio de e-mails transacionais | E-mail |
| Sentry | Monitoramento de erros | Metadados (scrubbed) |
| Groq | Assistente Fin | Prompts financeiros |

### 6.3 Políticas Publicadas

- [ ] Termos de Serviço publicados em `/termos`
- [ ] Política de Privacidade publicada em `/privacidade`
- [ ] Banner de consentimento LGPD (se necessário)
- [ ] Identificação do operador no rodapé
- [ ] Contato do DPO no rodapé

### 6.4 Data Retention

- [ ] `docs/DATA_RETENTION.md` revisado juridicamente
- [ ] Prazos de retenção fiscal definidos
- [ ] Processo de exclusão de conta documentado

---

## 7. Segurança E Pentest

- [ ] **WAF:** Configurar proteção contra injeção, XSS, rate limiting em nível de edge
- [ ] **Proteção contra bots:** Configurar challenge em login/registro
- [ ] **Credential stuffing:** Rate limiting + alertas no Sentry (>50 401/min)
- [ ] **Pentest independente:** Autenticado e não autenticado, incluindo:
  - IDOR (modificação de IDs de recursos)
  - CSRF (tokens já implementados)
  - SSRF (validação de URLs na API)
  - Prompt injection no Fin
  - Vazamento de dados em respostas de erro

---

## 8. Deploy Em Produção

**Pré-requisitos:** Todos os itens das fases 1-7 concluídos.

### 8.1 Ações Antes Do Deploy

- [ ] Ambiente `production` no GitHub com ao menos 1 required reviewer
- [ ] Secrets de produção criados (valores diferentes do staging)
- [ ] Railway: domínio customizado `api.seudominio.com` com TLS
- [ ] Vercel: domínio customizado `app.seudominio.com` com TLS
- [ ] Resend: domínio verificado, SPF/DKIM/DMARC propagado
- [ ] Sentry: ambiente `production` configurado em ambos os projetos
- [ ] Groq: chave de produção com ZDR ativo
- [ ] Backup schedule ativo no Railway PostgreSQL

### 8.2 Executar Deploy

```bash
gh workflow run deploy.yml \
  -f environment=production \
  -f git_sha=$(git rev-parse HEAD)
```

O workflow aguarda aprovação de um operador no GitHub.

### 8.3 Pós-Deploy

- [ ] Smoke tests de produção passam
- [ ] Sentry recebendo eventos no ambiente `production`
- [ ] Regras de alerta ativas
- [ ] Healthcheck `/ready` responde 200
- [ ] Login funcional com usuário real

---

## 9. Checklist Consolidado

| # | Item | Tipo | Esforço |
|---|------|------|---------|
| 1 | Comprar domínio | Administrativo | 30 min |
| 2 | Criar conta Vercel | Setup | 15 min |
| 3 | Criar conta Railway | Setup | 15 min |
| 4 | Criar conta Resend | Setup | 15 min |
| 5 | Criar conta Groq + solicitar ZDR | Setup | 30 min |
| 6 | Criar projetos Sentry (API + Web) | Setup | 20 min |
| 7 | Configurar GitHub Environments + Secrets | Setup | 30 min |
| 8 | Configurar Railway (PostgreSQL, Redis, API, Cron) | Setup | 45 min |
| 9 | Configurar Vercel (projeto, variáveis, domínios) | Setup | 30 min |
| 10 | Configurar Resend (domínio, DKIM, identidade) | Setup | 30 min |
| 11 | Configurar Sentry (alertas, scrubbing) | Setup | 20 min |
| 12 | Configurar DNS (todos os registros) | Setup | 20 min |
| 13 | **Deploy staging + migrations + smoke tests** | **Validação** | **45 min** |
| 14 | Validar ciclo de identidade completo | Validação | 30 min |
| 15 | Validar ciclo financeiro completo | Validação | 20 min |
| 16 | Validar PWA + mobile | Validação | 20 min |
| 17 | Validar entrega de e-mail (Resend) | Validação | 15 min |
| 18 | Validar Sentry + alertas | Validação | 20 min |
| 19 | **Restore drill** | **Validação** | **60 min** |
| 20 | Preencher operador/DPO/LGPD | Legal | 30 min |
| 21 | Publicar Termos + Política de Privacidade | Legal | 60 min |
| 22 | Documentar subprocessadores | Legal | 20 min |
| 23 | Configurar WAF + rate limiting edge | Segurança | 30 min |
| 24 | **Pentest independente** | **Segurança** | **1-3 dias** |
| 25 | Deploy produção + pós-verificação | Deploy | 30 min |
| 26 | Registrar evidências no launch checklist | Documentação | 30 min |

### Legenda

| Ícone | Significado |
|-------|-------------|
| Administrativo | Compra, cadastro, contratação |
| Setup | Configuração técnica nas plataformas |
| **Validação** | Teste manual ou automatizado |
| Legal | Documentação jurídica |
| Segurança | Revisão ou teste de segurança |
| Deploy | Execução do pipeline |

---

## 10. Estimativa De Esforço

| Fase | Itens | Esforço Estimado |
|------|-------|------------------|
| Domínio + Contas (1-6) | 6 | ~2 horas |
| Configuração das plataformas (7-12) | 6 | ~3 horas |
| Deploy + Validação em staging (13-18) | 6 | ~2-3 horas |
| Restore drill (19) | 1 | ~1 hora |
| Legal (20-22) | 3 | ~2 horas |
| Segurança (23-24) | 2 | ~1-3 dias |
| Deploy produção (25-26) | 2 | ~1 hora |

**Total código local após esta revisão:** 0 horas pendentes conhecidas.
**Total setup + validação externa:** ~9-11 horas (sem pentest)
**Total com pentest:** ~1-3 dias

---

## Documentos De Referência

| Documento | Conteúdo |
|-----------|----------|
| `docs/PLATFORM_SETUP.md` | Configuração detalhada de Railway, Vercel, Sentry, secrets |
| `docs/DEPLOYMENT.md` | Pipeline de deploy, rollback, validação |
| `docs/DNS_AND_EMAIL.md` | Registros DNS, SPF/DKIM/DMARC, Resend |
| `docs/ROADMAP_IMPLEMENTACAO_PRODUCAO.md` | Roadmap passo a passo da situacao atual ate o go-live |
| `docs/BACKUP_AND_RESTORE.md` | Estratégia de backup, restore drill, verificação |
| `docs/LAUNCH_CHECKLIST.md` | Checklist completo de 80+ itens |
| `docs/SECURITY_AND_LGPD.md` | Controles de segurança, LGPD, direitos do titular |
| `docs/DATA_RETENTION.md` | Prazos de retenção por tipo de dado |
| `docs/INCIDENT_RESPONSE.md` | Processo de resposta a incidentes |
| `README.md` | Desenvolvimento local, deploy, runbooks |
| `.github/workflows/deploy.yml` | Workflow automatizado de deploy |
| `.github/workflows/ci.yml` | Validações contínuas (testes, segurança) |
