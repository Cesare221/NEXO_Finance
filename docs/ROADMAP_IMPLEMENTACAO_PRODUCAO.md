# Roadmap De Implementacao E Publicacao - Nexo Finance

Data: 2026-07-30
Projeto: `C:\Users\Usuario\Desktop\PROJETOS\NEXO_finance`
Status atual: codigo local corrigido e validado; producao real ainda depende de infraestrutura externa e validacoes operacionais.

## Visao Geral

Este roadmap organiza o caminho do estado atual ate producao em fases sequenciais. Cada fase tem objetivo, responsavel principal, pre-requisitos, tarefas, entregaveis, validacoes e criterio de conclusao.

Responsaveis:

- **Voce:** contas, cartoes, dominio, credenciais, decisoes legais, aprovacao de deploy e servicos pagos.
- **Eu/Codex:** comandos, configuracoes no repositorio, validacoes locais, ajuda com CLI, ajustes de pipeline, revisao de logs e correcao de erros encontrados.
- **Servicos externos:** Vercel, Railway, Resend, Sentry, Groq, DNS e eventuais ferramentas de seguranca.

## Fase 0 - Estado Atual Ja Concluido

Objetivo: confirmar que o projeto local esta tecnicamente consistente antes de envolver infraestrutura externa.

Ja foi feito:

- Rotas criticas do BFF voltaram a usar backend real em vez de mocks.
- Sessao usa cookies, refresh token, validacao de origem e limpeza de cookies em 401.
- Dashboard financeiro usa proxy autenticado real.
- Sentry/Next.js foi corrigido para o SDK atual.
- CI foi corrigido para migration head e secret scan.
- Lockfiles da API foram sincronizados com `sentry-sdk`.
- `docker-compose.production-like.yml` foi ajustado para rehearsal local com `ENVIRONMENT=staging`.
- `docs/IMPLEMENTATION_FINAL.md` e `docs/REVIEW_FIX_REPORT_2026-07-30.md` foram atualizados.

Validacoes executadas:

- `npm test`: PASS.
- `npx tsc --noEmit`: PASS.
- `npm run build`: SUCCESS.
- `uv run pytest -q`: PASS, 277 testes.
- `uv run pip-audit --progress-spinner off`: sem vulnerabilidades conhecidas.
- Docker production-like subiu com Postgres, Redis, migration, API e web.
- API `/health`: HTTP 200.
- API `/ready`: HTTP 200 com `database=ok`.
- Web: HTTP 200 em `http://localhost:3011`.

Criterio de conclusao: concluido.

## Fase 1 - Decisoes De Produto, Marca E Legal

Objetivo: definir informacoes que nao podem ser inventadas no codigo.

Responsavel principal: voce.

Tarefas:

- Definir nome publico final do produto.
- Definir dominio principal, por exemplo `seudominio.com.br`.
- Definir entidade responsavel: nome empresarial, CNPJ, endereco/canal oficial e e-mail de suporte.
- Definir responsavel LGPD/DPO ou canal LGPD.
- Decidir se o app comeca fechado, beta privado ou aberto ao publico.
- Definir se havera usuarios reais no primeiro deploy ou apenas ambiente de teste.

Entregaveis:

- Dominio escolhido.
- Dados legais reais para termos e politica de privacidade.
- E-mail oficial de suporte e LGPD.
- Decisao de lancamento: staging, beta ou producao publica.

Validacao:

- Revisar `docs/SECURITY_AND_LGPD.md`.
- Revisar textos de `/privacidade` e `/termos`, se estiverem publicados no app.
- Nenhum placeholder legal deve restar em documento que va para producao.

Criterio de conclusao:

- Dados legais e dominio definidos.

## Fase 2 - Contas E Servicos Externos

Objetivo: criar as contas que vao hospedar e operar o app.

Responsavel principal: voce.

Servicos necessarios:

- GitHub: repositorio e GitHub Actions.
- Vercel: frontend Next.js.
- Railway: API, PostgreSQL, Redis e cron.
- Resend: e-mails transacionais.
- Sentry: observabilidade API e web.
- Groq: assistente Fin.
- Provedor DNS: dominio e registros.

Tarefas:

- Criar conta na Vercel.
- Criar conta na Railway.
- Criar conta no Resend.
- Criar conta no Sentry.
- Criar conta na Groq.
- Comprar ou configurar dominio.
- Habilitar billing onde for exigido.

Entregaveis:

- Acesso administrativo a cada plataforma.
- Tokens de deploy quando necessario.
- Projetos/organizacoes criados.

Validacao:

- Login funcionando em cada plataforma.
- Billing ativo onde o plano gratuito nao cobre Postgres/Redis/dominios/custom domains.

Criterio de conclusao:

- Todas as plataformas acessiveis e prontas para receber configuracao.

## Fase 3 - Ambientes GitHub E Segredos

Objetivo: separar staging e producao com controle de acesso e secrets diferentes.

Responsavel principal: voce com apoio meu via CLI se os tokens forem fornecidos localmente.

Tarefas:

- Criar GitHub Environments `staging` e `production`.
- Configurar `production` com aprovador obrigatorio.
- Criar secrets de deploy: `RAILWAY_TOKEN`, `RAILWAY_PROJECT_ID`, `RAILWAY_ENVIRONMENT_ID`, `RAILWAY_SERVICE_ID`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.
- Criar secrets de smoke: `SMOKE_EMAIL`, `SMOKE_PASSWORD`, `SMOKE_TOTP_SECRET`, se MFA for obrigatorio no smoke.
- Criar variables: `API_URL` e `WEB_URL`.

Entregaveis:

- Ambientes GitHub configurados.
- Secrets separados por ambiente.
- Producao protegida contra deploy acidental.

Validacao:

- Rodar CI sem expor secrets.
- Confirmar que secrets nao aparecem em logs.
- Confirmar que `scripts/check-secrets.ps1` passa.

Criterio de conclusao:

- GitHub Actions consegue acessar tokens de staging sem erro.
- Deploy de production exige aprovacao manual.

## Fase 4 - Infraestrutura Railway

Objetivo: provisionar backend, banco, cache e tarefas agendadas.

Responsavel principal: voce com apoio meu na configuracao.

Servicos Railway:

- PostgreSQL.
- Redis.
- API FastAPI.
- Cron para rotinas agendadas, se usado pelo projeto.

Tarefas:

- Criar projeto Railway.
- Criar ambientes `staging` e `production`.
- Provisionar PostgreSQL e Redis em cada ambiente.
- Criar servico API apontando para `apps/api`.
- Confirmar Dockerfile da API.
- Configurar healthcheck `/ready`.
- Configurar comando de start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Configurar migrations antes do deploy: `alembic upgrade head`.
- Configurar cron, se aplicavel.

Variaveis principais da API:

- `ENVIRONMENT`
- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `ALLOWED_HOSTS`
- `REDIS_URL`
- `PUBLIC_WEB_URL`
- `MAIL_PROVIDER`
- `RESEND_API_KEY`
- `EMAIL_FROM`
- `FIN_AI_PROVIDER`
- `GROQ_API_KEY`
- `GROQ_BASE_URL`
- `MFA_ENCRYPTION_KEYS`
- `MFA_ACTIVE_KEY_VERSION`
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`
- `SENTRY_RELEASE`
- `SENTRY_TRACES_SAMPLE_RATE`

Entregaveis:

- API deployada em staging.
- Banco e Redis conectados.
- Migrations aplicadas.
- `/health` e `/ready` acessiveis.

Validacao:

```powershell
Invoke-WebRequest -UseBasicParsing https://api-staging.seudominio.com/health
Invoke-WebRequest -UseBasicParsing https://api-staging.seudominio.com/ready
```

Criterio de conclusao:

- `/health` retorna 200.
- `/ready` retorna 200.
- Logs da API sem erro critico.
- Banco tem migrations no head esperado.

## Fase 5 - Infraestrutura Vercel

Objetivo: publicar o frontend Next.js com variaveis corretas e apontando para a API real.

Responsavel principal: voce com apoio meu na configuracao.

Tarefas:

- Criar projeto Vercel.
- Root Directory: `apps/web`.
- Framework: Next.js.
- Install Command: `npm ci`.
- Build Command: `npm run build`.
- Output: `.next`.
- Configurar variaveis de staging:
  - `API_URL=https://api-staging.seudominio.com`
  - `NEXT_PUBLIC_SENTRY_DSN`
  - `SENTRY_DSN`
  - `SENTRY_ENVIRONMENT=staging`
  - `SENTRY_RELEASE`
  - `SENTRY_AUTH_TOKEN`, se sourcemaps forem enviados.
- Configurar variaveis de producao separadas.
- Desativar deploy automatico de producao sem controle, se necessario.

Entregaveis:

- Web deployada em staging.
- Web apontando para API de staging.
- Build Vercel sem erro.

Validacao:

- Abrir app de staging.
- Login/cadastro deve chamar API correta.
- Console do navegador sem erro critico.
- Cookies devem respeitar HTTPS/Secure em staging.

Criterio de conclusao:

- Frontend carrega.
- Rotas principais funcionam.
- BFF responde corretamente.
- Nenhum mock critico aparece nos fluxos autenticados.

## Fase 6 - Dominio, DNS E HTTPS

Objetivo: configurar URLs reais e e-mail autenticado.

Responsavel principal: voce.

Tarefas:

- Criar registros DNS para frontend: `app.seudominio.com` e `app-staging.seudominio.com`.
- Criar registros DNS para API: `api.seudominio.com` e `api-staging.seudominio.com`.
- Configurar custom domains na Vercel.
- Configurar custom domains na Railway.
- Aguardar certificados TLS.
- Configurar SPF, DKIM e DMARC para Resend.

Entregaveis:

- Dominios HTTPS funcionando.
- DNS propagado.
- E-mail com autenticacao basica configurada.

Validacao:

- `https://app-staging...` carrega.
- `https://api-staging.../ready` retorna 200.
- Certificados TLS validos.
- SPF/DKIM/DMARC aceitos pelo Resend.

Criterio de conclusao:

- Nenhuma URL de staging/producao usa HTTP.
- `ALLOWED_ORIGINS`, `ALLOWED_HOSTS`, `API_URL` e `PUBLIC_WEB_URL` usam dominios reais corretos.

## Fase 7 - E-mails Transacionais Com Resend

Objetivo: garantir que cadastro, verificacao e recuperacao funcionem de ponta a ponta.

Responsavel principal: voce com apoio meu para testes.

Tarefas:

- Verificar dominio no Resend.
- Criar API key de staging.
- Criar API key de producao.
- Configurar `EMAIL_FROM`.
- Configurar webhooks de entrega, se necessario.
- Testar verificacao de e-mail, recuperacao de senha e notificacoes de seguranca.

Entregaveis:

- E-mails chegando em caixa real.
- Remetente correto.
- Links apontando para `PUBLIC_WEB_URL` correto.

Validacao:

- Criar usuario em staging.
- Confirmar recebimento do e-mail.
- Clicar no link e validar estado da conta.
- Testar reset de senha.

Criterio de conclusao:

- Fluxos de e-mail funcionam em staging sem console provider.

## Fase 8 - Observabilidade Com Sentry

Objetivo: enxergar erros antes e depois do lancamento.

Responsavel principal: voce com apoio meu.

Tarefas:

- Criar projeto `nexo-api`.
- Criar projeto `nexo-web`.
- Configurar DSNs por ambiente.
- Configurar scrubbing para authorization, cookies, tokens, e-mail, valores financeiros e mensagens do assistente.
- Configurar releases com Git SHA.
- Criar alertas para nova regressao, pico de erro, falha de readiness e abuso de autenticacao.

Entregaveis:

- Eventos chegando no Sentry em staging.
- Dados sensiveis mascarados.
- Alertas ativos.

Validacao:

- Gerar evento de teste em staging.
- Confirmar release/environment.
- Conferir se nao vazou cookie, token ou request body sensivel.

Criterio de conclusao:

- Sentry captura erro de API e web com scrubbing adequado.

## Fase 9 - IA Fin Com Groq

Objetivo: habilitar o assistente financeiro com chave real e protecao de dados.

Responsavel principal: voce.

Tarefas:

- Criar chave Groq para staging.
- Criar chave Groq para producao.
- Solicitar ou confirmar Zero Data Retention.
- Configurar `FIN_AI_PROVIDER`, `FIN_AI_MODEL`, `GROQ_API_KEY`, `GROQ_BASE_URL` e limites por minuto/dia.
- Revisar termos de uso da Groq para dados financeiros.

Entregaveis:

- Fin funcionando em staging.
- ZDR confirmado ou risco formalmente aceito.
- Rate limits ativos.

Validacao:

- Enviar pergunta simples ao Fin.
- Gerar proposta.
- Aprovar proposta.
- Cancelar proposta.
- Confirmar que erro da IA e exibido de forma clara ao usuario.

Criterio de conclusao:

- Fluxo Fin funciona em staging sem expor segredo e com limites ativos.

## Fase 10 - Smoke E Validacao Funcional Em Staging

Objetivo: provar que os principais fluxos funcionam com infraestrutura real.

Responsavel principal: eu posso executar e corrigir, voce fornece ambiente e credenciais.

Fluxos a testar:

- Cadastro.
- Verificacao de e-mail.
- Login.
- Refresh automatico.
- Logout.
- Recuperacao de senha.
- MFA: enrollment, challenge, recovery code e disable.
- Conta: editar perfil, exportar dados e excluir conta.
- Financeiro: contas, categorias, transacoes, cartoes, faturas, dashboard e dataset demo.
- Fin: mensagem, proposta, aprovar e cancelar.

Entregaveis:

- Relatorio de smoke staging.
- Lista de bugs encontrados.
- Correcoes aplicadas, se houver.

Validacao tecnica:

- CI passa.
- Build Vercel passa.
- Railway deploy passa.
- Logs sem erro critico.
- Console navegador sem erro critico.

Criterio de conclusao:

- Fluxos principais passam em staging com credenciais reais.

## Fase 11 - Responsividade, Acessibilidade E UX

Objetivo: garantir uso aceitavel em desktop e mobile antes de lancar.

Responsavel principal: eu posso executar validacoes e propor correcoes.

Tarefas:

- Testar viewports 375px, 768px e 1440px.
- Validar formularios, estados de loading, erros, empty states e sucesso.
- Validar foco de teclado.
- Validar contraste basico.
- Validar labels de inputs.
- Validar que texto nao quebra layout.
- Validar PWA: manifest, service worker, offline page e instalacao.

Entregaveis:

- Lista de ajustes de UX.
- Correcoes aplicadas no frontend, se necessarias.
- Evidencias de screenshots.

Validacao:

- Playwright ou navegador real.
- Console limpo.
- Sem layout quebrado nas paginas principais.

Criterio de conclusao:

- App usavel em mobile e desktop nos fluxos principais.

## Fase 12 - Backup, Restore E Operacao

Objetivo: garantir recuperacao de dados antes de aceitar usuario real.

Responsavel principal: voce com apoio meu.

Tarefas:

- Ativar backup do PostgreSQL no Railway.
- Documentar frequencia e retencao.
- Fazer backup manual.
- Restaurar em banco isolado.
- Rodar verificador de banco restaurado, se aplicavel.
- Executar smoke contra banco restaurado.
- Documentar tempo de restore.

Entregaveis:

- Evidencia de backup.
- Evidencia de restore.
- Tempo de recuperacao medido.

Validacao:

- Banco restaurado abre conexao.
- Migrations consistentes.
- Smoke minimo passa.

Criterio de conclusao:

- Existe prova de que dados podem ser recuperados.

## Fase 13 - Seguranca E Pentest

Objetivo: reduzir risco antes de expor dados financeiros reais.

Responsavel principal: voce contrata/coordena; eu corrijo achados tecnicos.

Tarefas:

- Configurar WAF/rate limiting de borda.
- Revisar CORS.
- Revisar cookies `HttpOnly`, `Secure` e `SameSite`.
- Revisar permissoes e isolamento por usuario.
- Testar IDOR, CSRF, brute force, credential stuffing, reset de senha, MFA, prompt injection no Fin e vazamento de dados em erros.
- Rodar pentest autenticado e nao autenticado.

Entregaveis:

- Relatorio de seguranca.
- Lista de vulnerabilidades.
- Correcoes aplicadas.
- Reteste aprovado.

Validacao:

- Nenhum achado critico ou alto aberto.
- Achados medios aceitos formalmente ou corrigidos.

Criterio de conclusao:

- Sistema aprovado para beta/producao sob risco conhecido.

## Fase 14 - Preparacao De Producao

Objetivo: preparar o ambiente final sem promover ainda.

Responsavel principal: voce com apoio meu.

Tarefas:

- Criar secrets de producao diferentes de staging.
- Configurar API production no Railway.
- Configurar web production na Vercel.
- Configurar dominios `api.seudominio.com` e `app.seudominio.com`.
- Configurar Resend, Sentry e Groq production.
- Confirmar backups production.
- Confirmar alertas production.
- Revisar checklist de LGPD.
- Confirmar que deploy production exige aprovacao.

Entregaveis:

- Ambiente production pronto.
- Deploy ainda nao executado ou bloqueado por aprovacao.
- Checklist de go-live preenchido.

Validacao:

- Variaveis conferidas.
- Segredos nao expostos.
- Dominios HTTPS prontos.
- Aprovador configurado.

Criterio de conclusao:

- Producao pronta para receber deploy aprovado.

## Fase 15 - Go-Live Controlado

Objetivo: publicar com controle, validar e manter rollback possivel.

Responsavel principal: voce aprova; eu posso acompanhar logs e corrigir incidentes.

Tarefas:

- Confirmar janela de deploy.
- Congelar mudancas nao essenciais.
- Rodar CI na branch final.
- Executar deploy production.
- Aguardar aprovacao manual no GitHub.
- Validar web production, API production, `/health`, `/ready`, login, dashboard, e-mail, Sentry, logs Railway e logs Vercel.
- Criar usuario real ou beta.
- Monitorar por 1 a 2 horas.

Entregaveis:

- Producao publicada.
- Evidencias de validacao.
- Plano de rollback conhecido.

Criterio de conclusao:

- Smoke production passa.
- Logs sem erro critico.
- Sentry sem regressao critica.
- Usuario consegue executar fluxo principal.

## Fase 16 - Pos-Lancamento

Objetivo: manter estabilidade depois do primeiro deploy.

Responsavel principal: voce com apoio tecnico meu.

Tarefas:

- Monitorar Sentry diariamente na primeira semana.
- Monitorar uso de Railway/Vercel.
- Monitorar custos.
- Monitorar entregabilidade de e-mail.
- Revisar feedback dos primeiros usuarios.
- Priorizar bugs.
- Criar rotina de backup/restore periodica.
- Definir ciclo de releases.

Entregaveis:

- Lista de melhorias pos-lancamento.
- Bugs priorizados.
- Runbook atualizado.

Criterio de conclusao:

- Operacao estabilizada e processo de manutencao definido.

## Ordem Recomendada

1. Fechar dados legais e dominio.
2. Criar contas externas.
3. Configurar GitHub Environments e secrets.
4. Subir Railway staging.
5. Subir Vercel staging.
6. Configurar DNS/HTTPS staging.
7. Configurar Resend, Sentry e Groq em staging.
8. Rodar smoke e validacao funcional.
9. Corrigir qualquer bug encontrado em staging.
10. Fazer UX/browser/PWA.
11. Fazer backup/restore drill.
12. Fazer seguranca/pentest.
13. Preparar production.
14. Fazer go-live controlado.
15. Monitorar pos-lancamento.

## Checklist Executivo

- [x] Codigo local corrigido.
- [x] Testes locais passaram.
- [x] Build frontend passou.
- [x] API local passou.
- [x] Docker production-like passou.
- [ ] Dominio definido.
- [ ] Contas Vercel/Railway/Resend/Sentry/Groq criadas.
- [ ] GitHub Environments configurados.
- [ ] Railway staging configurado.
- [ ] Vercel staging configurado.
- [ ] DNS/HTTPS staging configurado.
- [ ] Resend staging validado.
- [ ] Sentry staging validado.
- [ ] Groq staging validado com ZDR confirmado ou risco aceito.
- [ ] Smoke autenticado staging passou.
- [ ] UX/browser/PWA validado.
- [ ] Backup/restore drill executado.
- [ ] LGPD preenchida com dados reais.
- [ ] Pentest executado e achados criticos/altos corrigidos.
- [ ] Production configurado.
- [ ] Deploy production aprovado explicitamente.
- [ ] Smoke production passou.
- [ ] Monitoramento pos-lancamento ativo.

## Proxima Acao Pratica

A proxima acao que depende de voce e criar ou confirmar as contas externas e o dominio. Assim que existirem tokens/IDs de Vercel, Railway, Resend, Sentry e Groq, eu consigo ajudar a configurar os ambientes, validar logs e corrigir erros de deploy.
