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

A API expõe endpoints de saúde em:
- /health
- /ready

### 2. Frontend

```powershell
cd apps/web
Copy-Item .env.example .env.local
npm ci
npm run dev
```

A aplicação fica disponível em http://localhost:3000.

## Banco de dados e migrations

As migrations são gerenciadas com Alembic e devem ser a única fonte de alteração do esquema.

```powershell
cd apps/api
python -m alembic upgrade head
python -m alembic current
```

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

## Rollout Financeiro

O rollout financeiro deve terminar no único head Alembic `b81f4c6d2a10`:

```powershell
cd apps/api
python -m alembic heads
python -m alembic upgrade head
python -m alembic current
```

Dados de exemplo são estritamente opcionais e nunca são instalados durante cadastro, login, onboarding ou instalação do PWA. O ciclo autenticado do dataset é:

- `GET /financial/demo-dataset` retorna o estado do dataset.
- `POST /financial/demo-dataset` instala o dataset após confirmação explícita do usuário.
- `DELETE /financial/demo-dataset` remove somente recursos demonstrativos e preserva recursos adotados por movimentações reais.

O BFF do Next.js expõe o mesmo ciclo em `/api/financial/demo-dataset`. `theme_preference` pertence ao perfil do usuário e aceita `system`, `light` ou `dark` por `PATCH /auth/me` (ou pelo BFF em `/api/auth/profile`); ela é aplicada antes da renderização para evitar flash de tema.
