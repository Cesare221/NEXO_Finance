# Relatorio de Revisao e Correcoes - Nexo Finance

Data: 2026-07-30
Projeto: `C:\Users\Usuario\Desktop\PROJETOS\NEXO_finance`

## Resumo executivo

O projeto foi revisado com foco em rotas criticas, configuracao de producao, CI, observabilidade, dependencias, scanner de segredos, frontend e backend. Foram corrigidas regressões que substituiam fluxos reais por mocks, problemas de CI, configuracao Sentry desatualizada e lockfiles de API inconsistentes com o `pyproject.toml`.

O sistema compila, os testes automatizados locais passaram, o frontend buildado inicia, a API responde `/health` e o stack Docker production-like subiu com Postgres, Redis, migracao, API e web. A recomendacao final e: **ainda nao esta pronto para producao real**, porque dependencias externas e validacoes operacionais de staging/producao ainda precisam ser configuradas e comprovadas.

## Problemas identificados

- `apps/web/app/api/auth/session/route.ts` retornava `mockUser`, ignorando cookies, backend, refresh token e expiracao de sessao.
- `apps/web/app/api/financial/dashboard/route.ts` retornava `mockData`, expondo dados financeiros estaticos sem autenticacao.
- A rota de sessao chamava `validateRequestOrigin`, mas a versao correta anterior nao bloqueava explicitamente retorno falso.
- `apps/web/next.config.ts` tinha regressao de CSP/Sentry e usava `disableLogger`, opcao depreciada pelo `@sentry/nextjs`.
- `apps/web/instrumentation-client.ts` nao exportava `onRouterTransitionStart`.
- `apps/web/instrumentation.ts` nao exportava `onRequestError`.
- `.github/workflows/ci.yml` chamava `python ../scripts/check-migration-head.py` a partir de `apps/api`, caminho incorreto.
- `.github/workflows/ci.yml` executava `python scripts/check-secrets.ps1`, usando Python para um script PowerShell.
- `scripts/check-migration-head.py` dependia de `cwd` relativo e fragil.
- `scripts/check-secrets.ps1` gerava falsos positivos para exemplos sintéticos como `Bearer secret`.
- `apps/api/uv.lock`, `requirements.lock` e `requirements-dev.lock` estavam sem `sentry-sdk`, apesar de `pyproject.toml` declarar e o codigo importar observabilidade.
- O build local de producao podia falhar quando `API_URL=http://localhost:8000` estivesse em `.env.local`.
- O compose production-like usava `ENVIRONMENT=production`, incompativel com o rehearsal local porque a propria API bloqueia `http://localhost`, e-mail console e configuracoes nao-prod em ambiente `production`.
- Migrations contra PostgreSQL real nao foram executadas porque nao ha banco/credenciais de staging/producao configurados nesta sessao.

## Correcoes implementadas

- Restaurado o fluxo real de sessao no BFF:
  - leitura de cookies HttpOnly;
  - validacao de origem;
  - chamada a `/auth/me`;
  - refresh token quando o access token expira;
  - limpeza de cookies em 401.
- Restaurado o proxy autenticado real do dashboard:
  - preserva `start_date`, `end_date` e `months`;
  - usa `authenticatedBackendRequest`;
  - propaga refresh tokens renovados;
  - limpa cookies em 401.
- Atualizada configuracao Sentry:
  - `onRouterTransitionStart`;
  - `onRequestError`;
  - substituicao de `disableLogger` por `webpack.treeshake.removeDebugLogging`.
- Ajustada validacao de `API_URL`:
  - exige HTTPS para URLs reais;
  - permite `http://localhost` e `http://127.0.0.1` para build local.
- Corrigidos comandos do CI.
- Tornado o script de migration head independente do diretorio de execucao.
- Ajustado secret scan para detectar apenas Bearer tokens com tamanho compativel com credenciais reais.
- Sincronizados `uv.lock`, `requirements.lock` e `requirements-dev.lock` com `sentry-sdk`.
- Adicionados smoke checks para impedir retorno de mocks nas rotas criticas.
- Ajustado o ambiente Docker production-like para `staging`, mantendo a validacao de producao real restrita a infraestrutura e URLs reais.
- Atualizado `graphify-out` com `graphify update .`.

## Arquivos modificados

- `.github/workflows/ci.yml`
- `.env.production-like.example`
- `apps/api/requirements-dev.lock`
- `apps/api/requirements.lock`
- `apps/api/uv.lock`
- `apps/web/app/api/auth/session/route.ts`
- `apps/web/app/api/financial/dashboard/route.ts`
- `apps/web/instrumentation-client.ts`
- `apps/web/instrumentation.ts`
- `apps/web/lib/runtime-config.ts`
- `apps/web/next.config.ts`
- `apps/web/tests/smoke.mjs`
- `docker-compose.production-like.yml`
- `docs/IMPLEMENTATION_FINAL.md`
- `docs/ROADMAP_IMPLEMENTACAO_PRODUCAO.md`
- `scripts/check-migration-head.py`
- `scripts/check-secrets.ps1`
- `graphify-out/*` atualizado por `graphify update .`

## Arquivos preservados ou observacoes de versionamento

- `apps/web/.env.local` esta nao rastreado e foi preservado. Ele deve continuar fora do Git.
- `docs/IMPLEMENTATION_FINAL.md` foi mantido no local versionado e atualizado para refletir o estado real pos-revisao.

## Funcionalidades ajustadas

- Sessao autenticada real no frontend BFF.
- Dashboard financeiro autenticado real no frontend BFF.
- Observabilidade web com hooks exigidos pelo SDK atual.
- Validacao de runtime compativel com build local e producao.
- CI de migration head e secret scan.
- Cobertura de smoke contra regressao para mocks.

## Testes e validacoes executadas

- `npm test` em `apps/web`: PASS.
- `npx tsc --noEmit` em `apps/web`: PASS.
- `npm run build` em `apps/web`: SUCCESS.
- `npm audit --audit-level=high` em `apps/web`: PASS.
- `node --check public/sw.js` em `apps/web`: PASS.
- `uv run pytest -q` em `apps/api`: PASS.
- `uv run pytest tests/test_observability.py -v -q` em `apps/api`: 13 passed, 1 warning de deprecacao Starlette/TestClient.
- `uv run python -c "from app.core.observability import init_observability; init_observability(); print('OK')"` em `apps/api`: PASS.
- `python ../../scripts/check-migration-head.py` a partir de `apps/api`: PASS.
- `python scripts/check-migration-head.py` a partir da raiz: PASS.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-secrets.ps1`: PASS.
- `uv run pip-audit --progress-spinner off` em `apps/api`: PASS, sem vulnerabilidades conhecidas.
- Startup frontend buildado com `npm run start -- -p 3125`: HTTP 200.
- Startup API com `uv run uvicorn app.main:app --host 127.0.0.1 --port 8123`: `/health` HTTP 200 `{"status":"ok"}`.
- `git diff --check`: PASS, apenas warnings de conversao LF/CRLF do Git no Windows.
- `docker version --format "{{.Client.Version}} / {{.Server.Version}}"`: PASS, Docker client/server `29.5.3 / 29.5.3`.
- `docker compose -f docker-compose.production-like.yml build`: SUCCESS; imagens `nexo_finance-api`, `nexo_finance-migrate` e `nexo_finance-web` foram geradas. Observacao: o PowerShell registrou exit code 1 na execucao com pipe por causa de output de progresso em stderr, mas `docker image inspect` confirmou as imagens e o build log terminou com `Built`.
- `docker compose -f docker-compose.production-like.yml config --quiet`: PASS.
- `docker image inspect nexo_finance-api:latest nexo_finance-web:latest nexo_finance-migrate:latest`: PASS.
- `docker compose -f docker-compose.production-like.yml up -d`: PASS.
- `docker compose -f docker-compose.production-like.yml ps`: API, Postgres e Redis `healthy`; web `Up`.
- `Invoke-WebRequest http://localhost:8000/health`: HTTP 200 `{"status":"ok"}`.
- `Invoke-WebRequest http://localhost:8000/ready`: HTTP 200 `{"status":"ready","checks":{"database":"ok"}}`.
- `Invoke-WebRequest http://localhost:3011`: HTTP 200.
- Logs recentes de `api`, `web` e `migrate`: nenhum `error`, `exception`, `traceback`, `failed`, `fatal` ou `warn` encontrado.
- Pos-ajuste do `docs/IMPLEMENTATION_FINAL.md`: `npm test` em `apps/web` PASS; `npx tsc --noEmit` PASS; `npm run build` SUCCESS; `uv run pytest -q` em `apps/api` PASS com 277 passed e 1 warning de deprecacao; Docker `/health`, `/ready` e web HTTP 200; `git diff --check` PASS.
- `graphify update .`: SUCCESS.

## Comandos utilizados para validacao

```powershell
cd C:\Users\Usuario\Desktop\PROJETOS\NEXO_finance\apps\web
npm test
npx tsc --noEmit
npm run build
npm audit --audit-level=high
node --check public\sw.js
npm run start -- -p 3125

cd C:\Users\Usuario\Desktop\PROJETOS\NEXO_finance\apps\api
uv run pytest -q
uv run pytest tests/test_observability.py -v -q
uv run python -c "from app.core.observability import init_observability; init_observability(); print('OK')"
python ..\..\scripts\check-migration-head.py
uv run uvicorn app.main:app --host 127.0.0.1 --port 8123
uv run pip-audit --progress-spinner off

cd C:\Users\Usuario\Desktop\PROJETOS\NEXO_finance
python scripts\check-migration-head.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-secrets.ps1
git diff --check
graphify update .

docker version --format "{{.Client.Version}} / {{.Server.Version}}"
docker compose -f docker-compose.production-like.yml build
docker image inspect nexo_finance-api:latest nexo_finance-web:latest nexo_finance-migrate:latest --format "{{.RepoTags}} {{.Id}}"
docker compose -f docker-compose.production-like.yml config --quiet
docker compose -f docker-compose.production-like.yml up -d
docker compose -f docker-compose.production-like.yml ps
Invoke-WebRequest -UseBasicParsing http://localhost:8000/health
Invoke-WebRequest -UseBasicParsing http://localhost:8000/ready
Invoke-WebRequest -UseBasicParsing http://localhost:3011
docker compose -f docker-compose.production-like.yml logs --tail 120 api web migrate
```

## Problemas que nao puderam ser corrigidos ou validados

- `alembic upgrade head` contra banco real de staging/producao nao foi executado por falta de `DATABASE_URL` real e servico PostgreSQL provisionado.
- `/ready` foi validado no Docker local com PostgreSQL. Ainda falta validar `/ready` em staging/producao reais.
- Smoke tests de producao autenticados nao foram executados porque dependem de ambiente deployado e credenciais `SMOKE_*`.
- Validacao de console visual/browser responsivo com Playwright nao foi executada porque a solicitacao foi concluida com validacoes locais de build/startup; ainda deve ser feita em staging.
- CSP ainda permite `unsafe-inline` em scripts. A regressao foi revertida para o estado anterior com nonce, mas uma CSP estrita sem `unsafe-inline` exige estrategia dinamica de nonce/hash em Next.js e validacao em navegador.

## Riscos e limitacoes restantes

- Producao depende de Vercel, Railway, Resend, Sentry e Groq configurados corretamente.
- Sem staging validado, ainda ha risco de erro em variaveis, DNS, CORS, cookies `Secure`, healthchecks e SMTP.
- A cobertura de frontend e baseada em smoke/static checks; ainda falta teste de navegador cobrindo fluxos completos e console.
- Sem pentest independente, riscos de IDOR, CSRF, abuso de autenticacao e prompt injection ainda precisam de evidencia externa.
- `.env.local` local nao rastreado deve ser revisado manualmente antes de qualquer deploy, sem commit.

## Variaveis de ambiente necessarias

### API

- `ENVIRONMENT`
- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `ALLOWED_HOSTS`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `DATABASE_POOL_SIZE`
- `DATABASE_MAX_OVERFLOW`
- `DATABASE_POOL_TIMEOUT`
- `DATABASE_POOL_RECYCLE`
- `REDIS_URL`
- `TRUSTED_PROXY_IPS`
- `FIN_AI_PROVIDER`
- `FIN_AI_MODEL`
- `FIN_AI_TIMEOUT_SECONDS`
- `FIN_AI_MAX_TOOL_ROUNDS`
- `FIN_AI_MESSAGES_PER_MINUTE`
- `FIN_AI_MESSAGES_PER_DAY`
- `GROQ_API_KEY`
- `GROQ_BASE_URL`
- `MAIL_PROVIDER`
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `PUBLIC_WEB_URL`
- `EMAIL_VERIFICATION_TTL_MINUTES`
- `PASSWORD_RESET_TTL_MINUTES`
- `MFA_CHALLENGE_TTL_MINUTES`
- `MFA_ENCRYPTION_KEYS`
- `MFA_ACTIVE_KEY_VERSION`
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`
- `SENTRY_RELEASE`
- `SENTRY_TRACES_SAMPLE_RATE`

### Web

- `API_URL`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SENTRY_DSN`
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`
- `SENTRY_RELEASE`
- `SENTRY_AUTH_TOKEN`
- `SENTRY_ORG`
- `SENTRY_PROJECT`
- `SENTRY_TRACES_SAMPLE_RATE`
- `NEXT_STANDALONE`

### CI/Smoke

- `RAILWAY_TOKEN`
- `RAILWAY_PROJECT_ID`
- `RAILWAY_ENVIRONMENT_ID`
- `RAILWAY_SERVICE_ID`
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `API_URL`
- `WEB_URL`
- `SMOKE_EMAIL`
- `SMOKE_PASSWORD`
- `SMOKE_TOTP_SECRET`

## Servicos externos a configurar

- Vercel para `apps/web`.
- Railway para API, PostgreSQL, Redis e cron.
- Resend para e-mails transacionais.
- Sentry para `nexo-api` e `nexo-web`.
- Groq com Zero Data Retention para assistente Fin em producao.
- DNS com HTTPS, SPF, DKIM e DMARC.
- GitHub Environments e secrets.
- Monitoramento externo de uptime.
- WAF/rate limiting de borda.

## Checklist para producao

- [x] Ativar Docker Desktop e validar Docker build API/Web local.
- [ ] Repetir Docker build em runner CI limpo.
- [ ] Criar ambientes `staging` e `production` no GitHub.
- [ ] Configurar Vercel com root `apps/web`.
- [ ] Configurar Railway com PostgreSQL, Redis, API e cron.
- [ ] Definir `API_URL` e `NEXT_PUBLIC_API_URL` HTTPS.
- [ ] Configurar todos os secrets por ambiente.
- [ ] Executar `alembic upgrade head` em staging.
- [ ] Validar `/health` e `/ready` em staging.
- [ ] Executar smoke production contra staging.
- [ ] Validar cadastro, verificacao de e-mail, login, refresh, logout, reset de senha, MFA e exclusao de conta.
- [ ] Validar contas, categorias, transacoes, cartoes, faturas, dashboard, dataset demo e Fin.
- [ ] Configurar Resend com dominio verificado.
- [ ] Configurar Sentry, scrubbing, releases e alertas.
- [ ] Solicitar/confirmar Groq ZDR.
- [ ] Configurar DNS, TLS, SPF, DKIM e DMARC.
- [ ] Executar restore drill e registrar evidencia.
- [ ] Revisar LGPD com dados reais de controlador, DPO e canal de contato.
- [ ] Publicar termos e politica de privacidade.
- [ ] Configurar WAF e protecao contra abuso.
- [ ] Fazer validacao responsiva/browser com console limpo.
- [ ] Realizar pentest independente autenticado e nao autenticado.
- [ ] Promover para producao somente apos aprovacao explicita.

## Recomendacao final

**Ainda nao esta pronto para producao real.**

O codigo local esta em melhor estado e passou nas validacoes executaveis nesta maquina, mas producao depende de infraestrutura, credenciais, banco, Redis, DNS, e-mail, monitoramento, smoke em staging, restore drill e pentest.
