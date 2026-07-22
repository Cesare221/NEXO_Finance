# Implantação Do Nexo

## Arquitetura Recomendada

- `apps/web`: projeto Next.js na Vercel.
- `apps/api`: serviço Docker no Railway.
- PostgreSQL: serviço gerenciado no mesmo projeto Railway da API.

Crie primeiro um ambiente de homologação. Produção deve usar banco, segredos e domínios próprios.

## API No Railway

1. Crie um serviço PostgreSQL.
2. Crie um serviço a partir do repositório e defina `apps/api` como Root Directory.
3. O arquivo `railway.json` usa o `Dockerfile`, executa `alembic upgrade head` antes do deploy e verifica `/ready` antes de liberar tráfego.
4. Configure as variáveis:

```text
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<valor-aleatorio-com-64-ou-mais-caracteres>
ALLOWED_ORIGINS=https://app.seudominio.com
ALLOWED_HOSTS=api.seudominio.com
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
GROQ_API_KEY=<segredo-configurado-somente-na-api>
GROQ_BASE_URL=https://api.groq.com/openai/v1
TRUSTED_PROXY_IPS=<ips-dos-proxies-que-podem-enviar-x-forwarded-for>
```

Não use `*`, HTTP ou endereços locais em `ALLOWED_ORIGINS` na produção.

## Web Na Vercel

1. Importe o mesmo repositório e defina `apps/web` como Root Directory.
2. Configure `API_URL=https://api.seudominio.com` nos ambientes Preview e Production.
3. Mantenha `API_URL` somente no servidor. O navegador acessa a API pelo BFF `/api` do Next.js.
4. Faça o primeiro deploy usando o domínio temporário e depois configure o domínio definitivo.

## Validação Antes Da Liberação

O workflow `.github/workflows/ci.yml` valida migrations em PostgreSQL, executa a suíte da API, o smoke test web e o build do Next.js a cada pull request.

```text
GET https://api.seudominio.com/health -> 200 {"status":"ok"}
GET https://api.seudominio.com/ready  -> 200 com database=ok
```

Execute também:

1. Cadastro, login, refresh e logout.
2. Criação de conta e categoria.
3. Criação e exclusão de uma transação.
4. Aprovação e cancelamento de uma proposta do Fin.
5. Instalação PWA em Android e iOS.
6. Verificação em 375 px, 768 px e desktop.

## Rollout Financeiro

Execute as migrations antes de iniciar uma nova versão da API. O rollout financeiro deve terminar no único head `c91d4e7a2f10`:

```powershell
cd apps/api
python -m alembic heads
python -m alembic upgrade head
python -m alembic current
```

Os endpoints autenticados do dataset demonstrativo são `GET`, `POST` e `DELETE /financial/demo-dataset`; clientes do navegador devem usar o BFF equivalente em `/api/financial/demo-dataset`. A instalação exige confirmação explícita do usuário. Nunca instale dados de exemplo automaticamente durante cadastro, login, onboarding, ativação do service worker ou instalação do PWA.

`DELETE /financial/demo-dataset` remove somente recursos marcados como demonstrativos. Recursos adotados por movimentações financeiras reais são preservados, e a resposta informa as contagens removidas e preservadas.

O perfil do usuário armazena `theme_preference` como `system`, `light` ou `dark`. Atualize-o por `PATCH /auth/me` ou pelo BFF `PATCH /api/auth/profile`; aplique-o no carregamento inicial para evitar flash de tema.

## Backups

- Ative backups diários do PostgreSQL antes de aceitar usuários reais.
- Mantenha retenção semanal e mensal conforme a política do produto.
- Faça uma restauração em homologação pelo menos uma vez por trimestre.
- Registre horário, duração e resultado de cada teste de recuperação.

## Rollback

1. Interrompa novas gravações se houver risco de inconsistência.
2. Reimplante a última versão saudável da API e do web.
3. Restaure o banco apenas quando houver perda ou corrupção confirmada.
4. Não execute downgrade de migration automaticamente. Cada downgrade deve ser revisado conforme os dados envolvidos.
5. Valide `/ready`, login e uma leitura do dashboard antes de reabrir o tráfego.
6. Quando uma migration já estiver aplicada, prefira uma migration corretiva aditiva. Execute `alembic downgrade` somente com plano revisado, backup restaurável e janela de manutenção; ele não é rollback automático de deploy.

## Checklist De Produção

- [ ] Domínios e HTTPS ativos.
- [ ] Segredos diferentes entre homologação e produção.
- [ ] Migration concluída antes do startup.
- [ ] `/ready` aprovado pela plataforma.
- [ ] Backups e restauração testados.
- [ ] Monitoramento de erros e alertas configurados.
- [ ] Política de privacidade e exclusão de conta publicadas.
- [ ] Smoke test completo aprovado.
- [ ] Identificacao do operador, encarregado e canal LGPD preenchidos no aviso.
- [ ] Redis gerenciado configurado e testado em mais de uma instancia.
- [ ] Zero Data Retention habilitado na Groq e termos de tratamento revisados.
- [ ] Verificacao de e-mail, recuperacao de senha e MFA/passkeys ativos.
- [ ] WAF, alertas de abuso e plano de resposta a incidentes testados.
