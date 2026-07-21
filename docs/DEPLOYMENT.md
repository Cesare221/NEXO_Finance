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
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
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

## Checklist De Produção

- [ ] Domínios e HTTPS ativos.
- [ ] Segredos diferentes entre homologação e produção.
- [ ] Migration concluída antes do startup.
- [ ] `/ready` aprovado pela plataforma.
- [ ] Backups e restauração testados.
- [ ] Monitoramento de erros e alertas configurados.
- [ ] Política de privacidade e exclusão de conta publicadas.
- [ ] Smoke test completo aprovado.
