# Nexo

Aplicativo de finanças pessoais com dashboard, PWA e o assistente Fin. O Nexo permite gerenciar contas, categorias e movimentações, além de revisar propostas financeiras reconhecidas pelo assistente antes de aplicá-las.

## Stack

- Web: Next.js 15, React 19 e TypeScript
- API: FastAPI, SQLAlchemy e Alembic
- Banco: PostgreSQL
- Testes: pytest e smoke checks do frontend
- Produção recomendada: Vercel, Railway e PostgreSQL gerenciado

## Desenvolvimento Local

API:

```powershell
cd apps/api
Copy-Item .env.example .env
python -m alembic upgrade head
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Web:

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Abra `http://localhost:3000`. A API publica liveness em `/health` e readiness com validação do banco em `/ready`.

## Testes

```powershell
cd apps/api
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests -q

cd ../web
npm test
npm run build
```

## Banco E Migrations

Alembic é a única fonte de criação e atualização do esquema. A aplicação não cria tabelas automaticamente durante o startup.

```powershell
cd apps/api
python -m alembic upgrade head
python -m alembic current
```

## Dependências Da API

`uv.lock`, `requirements.lock` e `requirements-dev.lock` fixam as versões usadas no contêiner e no CI. Depois de alterar `pyproject.toml`, atualize os arquivos com:

```powershell
cd apps/api
uv lock
uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.lock
uv export --locked --extra dev --no-emit-project --format requirements-txt --output-file requirements-dev.lock
```

## Hospedagem

As instruções completas, variáveis, smoke tests, backups e rollback estão em [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Nunca publique arquivos `.env`, logs locais, tokens ou credenciais do banco.
