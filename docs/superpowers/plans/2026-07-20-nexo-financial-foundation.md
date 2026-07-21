# Nexo Financial Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar dados demonstrativos opcionais, tema claro/escuro, exclusão segura de categorias e um fluxo completo de cartões e faturas, mantendo isolamento por usuário e consistência financeira.

**Architecture:** A API FastAPI continua como fonte de verdade. Novos serviços focados encapsulam dataset, ciclo de fatura e ciclo de vida de categorias; as rotas Next.js permanecem como BFF autenticado e validam origem antes de mutações. No frontend, componentes pequenos cuidam de tema, dataset e formulário de cartão, enquanto os managers existentes coordenam carregamento e atualização global.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest, Next.js 15, React 19, TypeScript, CSS e smoke tests Node.

## Global Constraints

- Dados demonstrativos são opcionais e nunca aparecem automaticamente em contas novas.
- A instalação do dataset é transacional, idempotente, auditada e isolada por `user_id`.
- A limpeza remove somente dados demonstrativos e preserva recursos adotados por dados reais.
- Tema disponível em `Sistema`, `Claro` e `Escuro`, com persistência no perfil e no dispositivo.
- O tema escuro usa a direção visual Petróleo Nexo e tokens semânticos.
- Categoria sem dependências é excluída; categoria com histórico é arquivada.
- Cartão ativo não pode repetir nome no mesmo usuário.
- Compras no cartão alteram limite e fatura, mas não o saldo bancário; apenas o pagamento da fatura altera a conta.
- Toda rota BFF mutável mantém `validateRequestOrigin`.
- Nenhuma resposta pública expõe manifesto interno do dataset ou IDs de outro usuário.
- Fora do escopo: Open Finance, importação bancária, contas compartilhadas, organizações e alteração de e-mail.

## Execution Order

1. Persistência compartilhada e contratos.
2. Ciclo de cartões e faturas.
3. Ciclo de vida de categorias.
4. Dataset demonstrativo no backend e no BFF.
5. Tema e preferência do usuário.
6. Experiência de dataset, cartões e categorias.
7. Consistência transversal e verificação final.

---

### Task 1: Persistência compartilhada para dataset e tema

**Files:**
- Create: `apps/api/alembic/versions/b81f4c6d2a10_add_demo_datasets_and_theme.py`
- Create: `apps/api/app/models/demo_dataset.py`
- Modify: `apps/api/app/models/__init__.py`
- Modify: `apps/api/app/models/user.py`
- Modify: `apps/api/app/models/financial_account.py`
- Modify: `apps/api/app/models/category.py`
- Modify: `apps/api/app/models/credit_card.py`
- Modify: `apps/api/app/models/billing_statement.py`
- Modify: `apps/api/app/models/transaction.py`
- Modify: `apps/api/app/models/recurring_rule.py`
- Test: `apps/api/tests/test_financial_foundation.py`

**Interfaces:**
- Produces: `DemoDataset`, `User.theme_preference` and nullable `demo_dataset_id` ownership on demonstrative resources.
- `DemoDataset.status` accepts `installing`, `active`, `cleaning`, `removed`, `failed`.

- [ ] **Step 1: Write the failing metadata test**

```python
def test_demo_dataset_and_theme_are_mapped():
    from app.core.database import Base

    assert "demo_datasets" in Base.metadata.tables
    assert "theme_preference" in Base.metadata.tables["users"].c
    for table in (
        "financial_accounts", "categories", "credit_cards",
        "billing_statements", "transactions", "recurring_rules",
    ):
        assert "demo_dataset_id" in Base.metadata.tables[table].c
```

- [ ] **Step 2: Run the test and verify the missing table failure**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial_foundation.py::test_demo_dataset_and_theme_are_mapped -q`

Expected: FAIL because `demo_datasets` and `theme_preference` do not exist.

- [ ] **Step 3: Add the model and ownership columns**

```python
# apps/api/app/models/demo_dataset.py
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class DemoDataset(Base):
    __tablename__ = "demo_datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="installing")
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

Add `theme_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="system", server_default="system")` to `User`. Add a nullable, indexed `demo_dataset_id` foreign key with `ondelete="SET NULL"` to each resource model listed above.

- [ ] **Step 4: Create the Alembic migration**

Use revision `b81f4c6d2a10` with `down_revision = "ac12f8739a6b"`. Create the table, columns, indexes and foreign keys explicitly. Add an active-dataset uniqueness index:

```python
op.create_index(
    "uq_demo_datasets_active_user_version",
    "demo_datasets",
    ["user_id", "version"],
    unique=True,
    postgresql_where=sa.text("status = 'active'"),
    sqlite_where=sa.text("status = 'active'"),
)
```

- [ ] **Step 5: Register the model and run tests**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial_foundation.py -q`

Expected: PASS.

- [ ] **Step 6: Verify a single migration head**

Run: `cd apps/api; python -m alembic heads`

Expected: exactly `b81f4c6d2a10 (head)`.

- [ ] **Step 7: Commit**

```powershell
git add apps/api/alembic/versions/b81f4c6d2a10_add_demo_datasets_and_theme.py apps/api/app/models apps/api/tests/test_financial_foundation.py
git commit -m "feat(api): add demo dataset ownership and theme preference"
```

---

### Task 2: Correct credit-card statement cycles and duplicate protection

**Files:**
- Modify: `apps/api/app/services/financial_service.py`
- Modify: `apps/api/tests/test_financial.py`

**Interfaces:**
- Produces: `_statement_cycle(occurred_on, closing_day, due_day) -> tuple[date, date, date]`.
- Existing `_get_or_create_statement` consumes the new cycle without changing existing statements.

- [ ] **Step 1: Add failing cycle and duplicate-card tests**

```python
@pytest.mark.parametrize(
    ("occurred_on", "expected_start", "expected_end", "expected_due"),
    [
        ("2026-07-09", "2026-06-11", "2026-07-10", "2026-07-17"),
        ("2026-07-10", "2026-06-11", "2026-07-10", "2026-07-17"),
        ("2026-07-11", "2026-07-11", "2026-08-10", "2026-08-17"),
        ("2026-12-31", "2026-12-11", "2027-01-10", "2027-01-17"),
    ],
)
def test_card_purchase_uses_closing_cycle(client, occurred_on, expected_start, expected_end, expected_due):
    # register, create account/card, post purchase, then inspect dashboard statement
    assert statement["period_start"] == expected_start
    assert statement["period_end"] == expected_end
    assert statement["due_on"] == expected_due

def test_duplicate_active_card_name_is_rejected(client):
    # create "Nexo Principal" twice for the same user
    assert duplicate.status_code == 409
```

Also cover closing day 31 in February, due day before closing day, two users with the same card name and renaming a card to another active card's name.

- [ ] **Step 2: Run focused tests and verify current calendar-month behavior fails**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial.py -k "closing_cycle or duplicate_active_card" -q`

Expected: FAIL on period boundaries and duplicate acceptance.

- [ ] **Step 3: Implement cycle helpers**

```python
def _valid_day(year: int, month: int, requested_day: int) -> date:
    return date(year, month, min(requested_day, monthrange(year, month)[1]))

def _month_shift(day: date, months: int) -> date:
    index = day.year * 12 + day.month - 1 + months
    return _valid_day(index // 12, index % 12 + 1, day.day)

def _statement_cycle(occurred_on: date, closing_day: int, due_day: int) -> tuple[date, date, date]:
    current_close = _valid_day(occurred_on.year, occurred_on.month, closing_day)
    next_month = _month_shift(current_close, 1)
    period_end = current_close if occurred_on <= current_close else _valid_day(
        next_month.year, next_month.month, closing_day
    )
    previous_month = _month_shift(period_end, -1)
    period_start = _valid_day(previous_month.year, previous_month.month, closing_day) + timedelta(days=1)
    same_month_due = _valid_day(period_end.year, period_end.month, due_day)
    if same_month_due > period_end:
        due_on = same_month_due
    else:
        following_month = _month_shift(period_end, 1)
        due_on = _valid_day(following_month.year, following_month.month, due_day)
    return period_start, period_end, due_on
```

Use this tuple in `_get_or_create_statement`. Query by `credit_card_id`, `period_start` and `period_end`; never mutate an existing statement after card settings change.

- [ ] **Step 4: Reject duplicate active names**

Before create/update, normalize with `name.strip().casefold()` and compare active cards owned by the same `user_id`. Raise `_conflict("Credit card", name)` when another active card matches.

- [ ] **Step 5: Run card and dashboard tests**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial.py -k "CreditCards or Dashboard" -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/api/app/services/financial_service.py apps/api/tests/test_financial.py
git commit -m "fix(api): calculate statements from card closing cycle"
```

---

### Task 3: Delete or archive categories according to dependencies

**Files:**
- Modify: `apps/api/app/schemas/financial.py`
- Modify: `apps/api/app/services/financial_service.py`
- Modify: `apps/api/app/api/financial.py`
- Modify: `apps/api/tests/test_financial.py`

**Interfaces:**
- Produces: `CategoryDeleteResponse { action: Literal["deleted", "archived"], category: CategoryResponse }`.
- Produces: `delete_or_archive_category(db, user_id, category_id) -> dict`.

- [ ] **Step 1: Replace archive-only tests with the lifecycle matrix**

Add tests for: permanent deletion without dependencies; archive with transaction, installment plan, recurring rule, child or pending proposal; cross-user isolation; and omission of archived categories from the active tree.

```python
def test_unused_category_is_deleted(client):
    response = client.delete(f"/financial/categories/{category['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["action"] == "deleted"
    assert all(item["id"] != category["id"] for item in client.get("/financial/categories", headers=headers).json())
```

- [ ] **Step 2: Run the category tests and confirm archive-only behavior fails**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial.py -k "Categor" -q`

Expected: FAIL because the endpoint currently always returns an archived category.

- [ ] **Step 3: Add the response schema**

```python
class CategoryDeleteResponse(BaseModel):
    action: Literal["deleted", "archived"]
    category: CategoryResponse
```

- [ ] **Step 4: Implement dependency inspection and mutation**

`delete_or_archive_category` must scope every query by `user_id`, inspect transactions, installment plans, recurring rules, children and proposed/confirmed action proposals, and include descendant IDs. If no dependency exists, snapshot the category, `db.delete(category)`, audit `category.deleted`, commit and return `deleted`. Otherwise archive the category plus descendants required to preserve the tree, audit `category.archived`, commit and return `archived`.

```python
return {"action": action, "category": snapshot}
```

`get_category_tree` must start from `Category.is_archived.is_(False)` and attach only active descendants. `_validate_category`, `create_transaction`, `create_card_purchase`, installment and recurring creation must reject archived categories.

- [ ] **Step 5: Change the route contract and run tests**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_financial.py -k "Categor or archived" -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/api/app/schemas/financial.py apps/api/app/services/financial_service.py apps/api/app/api/financial.py apps/api/tests/test_financial.py
git commit -m "feat(api): delete unused categories and archive historical ones"
```

---

### Task 4: Install and clean the optional demo dataset

**Files:**
- Create: `apps/api/app/services/demo_dataset_service.py`
- Modify: `apps/api/app/schemas/financial.py`
- Modify: `apps/api/app/api/financial.py`
- Create: `apps/api/tests/test_demo_dataset.py`

**Interfaces:**
- Produces: `get_demo_dataset_status`, `install_demo_dataset`, `clean_demo_dataset`.
- API: `GET|POST|DELETE /financial/demo-dataset`.
- Public response: `active`, `version`, `installed_at`, `summary`; never `manifest`.

- [ ] **Step 1: Write failing install, idempotency, rollback and isolation tests**

```python
def test_install_is_complete_and_idempotent(client):
    first = client.post("/financial/demo-dataset", headers=headers)
    second = client.post("/financial/demo-dataset", headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert first.json()["summary"] == {
        "accounts": 3, "cards": 1, "categories": 14,
        "transactions": 12, "recurring_rules": 1,
    }
```

Add tests for exact opening balances, relative dates, an open statement, user B isolation, forced exception rollback, selective cleanup and audit payloads without amounts/descriptions.

- [ ] **Step 2: Run tests and verify routes are missing**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_demo_dataset.py -q`

Expected: FAIL with 404 for `/financial/demo-dataset`.

- [ ] **Step 3: Add schemas and route handlers**

```python
class DemoDatasetSummary(BaseModel):
    accounts: int
    cards: int
    categories: int
    transactions: int
    recurring_rules: int

class DemoDatasetResponse(BaseModel):
    active: bool
    version: str
    installed_at: datetime | None
    summary: DemoDatasetSummary
```

The POST route returns 201 for a new install and stable 200 for an existing active version. DELETE is idempotent and returns an inactive summary when already clean.

- [ ] **Step 4: Implement a deterministic builder**

Use `DEMO_VERSION = "2026.07.v1"` and a single `installed_on: date`. Build three accounts (`Conta principal`, `Reserva`, `Carteira`), one card, 14 category/subcategory rows, 12 income/expense/card transactions and one monthly recurring rule. Compute dates with `_add_months` and the card cycle helper; attach `demo_dataset_id` to every generated resource.

Use one transaction boundary:

```python
try:
    dataset = DemoDataset(user_id=user_id, version=DEMO_VERSION, status="installing")
    db.add(dataset)
    db.flush()
    summary = _build_resources(db, user_id, dataset.id, installed_on)
    dataset.status = "active"
    dataset.installed_at = datetime.now(timezone.utc)
    dataset.manifest = summary.resource_ids
    _audit(db, user_id, "demo_dataset.installed", dataset.id, summary.counts)
    db.commit()
except Exception:
    db.rollback()
    raise
```

- [ ] **Step 5: Implement selective cleanup**

Delete demo transactions and rules first. Delete statements only when all their transactions are demonstrative. For account/category/card resources with non-demo dependencies, set `demo_dataset_id = None` and count them as preserved; otherwise delete them. Mark the dataset removed, clear the internal manifest, audit only removed/preserved counts and commit once.

- [ ] **Step 6: Run demo and financial suites**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_demo_dataset.py tests/test_financial.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add apps/api/app/services/demo_dataset_service.py apps/api/app/schemas/financial.py apps/api/app/api/financial.py apps/api/tests/test_demo_dataset.py
git commit -m "feat(api): add optional transactional demo dataset"
```

---

### Task 5: Expose dataset and category contracts through the Next.js BFF

**Files:**
- Create: `apps/web/app/api/financial/demo-dataset/route.ts`
- Modify: `apps/web/app/api/financial/categories/[categoryId]/route.ts`
- Modify: `apps/web/lib/financial-types.ts`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Produces: `DemoDatasetState`, `CategoryDeleteResult` and authenticated same-origin BFF routes.

- [ ] **Step 1: Add failing smoke markers**

Require the new route and markers `validateRequestOrigin`, `/financial/demo-dataset`, `DemoDatasetState`, `CategoryDeleteResult`, `deleted` and `archived`.

- [ ] **Step 2: Run smoke tests**

Run: `cd apps/web; npm test`

Expected: FAIL because the route and types do not exist.

- [ ] **Step 3: Add shared types**

```typescript
export type DemoDatasetState = {
  active: boolean;
  version: string;
  installed_at: string | null;
  summary: { accounts: number; cards: number; categories: number; transactions: number; recurring_rules: number };
};

export type CategoryDeleteResult = {
  action: "deleted" | "archived";
  category: FinancialCategory;
};
```

- [ ] **Step 4: Implement GET, POST and DELETE proxy handlers**

Follow the existing authenticated BFF pattern. GET skips origin validation; POST and DELETE reject invalid origins with 403, forward cookies with `authenticatedBackendRequest`, refresh tokens when returned and clear cookies on 401.

- [ ] **Step 5: Run smoke and TypeScript checks**

Run: `cd apps/web; npm test; npx tsc --noEmit`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/web/app/api/financial/demo-dataset/route.ts apps/web/app/api/financial/categories/[categoryId]/route.ts apps/web/lib/financial-types.ts apps/web/tests/smoke.mjs
git commit -m "feat(web): expose demo dataset and category lifecycle contracts"
```

---

### Task 6: Persist and apply the Nexo theme without flash

**Files:**
- Modify: `apps/api/app/schemas/auth.py`
- Modify: `apps/api/app/services/auth_service.py`
- Modify: `apps/api/app/api/auth.py`
- Modify: `apps/api/tests/test_auth.py`
- Create: `apps/web/lib/theme.ts`
- Create: `apps/web/components/theme-provider.tsx`
- Create: `apps/web/components/theme-settings.tsx`
- Modify: `apps/web/components/session-profile.tsx`
- Modify: `apps/web/app/layout.tsx`
- Modify: `apps/web/app/configuracoes/page.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- `ThemePreference = "system" | "light" | "dark"`.
- `SessionUser.theme_preference` is authoritative after login; localStorage key is `nexo-theme`.

- [ ] **Step 1: Add failing API and smoke tests**

API test: PATCH `/auth/me` with each valid preference, reject any other value, return the preference from login/session profile, and audit `theme_preference` as a changed field. Smoke test requires `data-theme`, `nexo-theme`, `prefers-color-scheme`, `ThemeSettings` and all three labels.

- [ ] **Step 2: Run focused tests and verify failures**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_auth.py -k theme -q`

Run: `cd ../web; npm test`

Expected: FAIL because the preference is absent.

- [ ] **Step 3: Extend auth schemas and profile update**

```python
ThemePreference = Literal["system", "light", "dark"]

class MeResponse(BaseModel):
    # existing fields
    theme_preference: ThemePreference

class ProfileUpdateRequest(BaseModel):
    # existing fields
    theme_preference: ThemePreference | None = None
```

Include `theme_preference` in `update_profile` and every `MeResponse` construction.

- [ ] **Step 4: Add the pre-hydration script and provider**

`apps/web/lib/theme.ts` exports `resolveTheme`, `applyTheme` and `THEME_STORAGE_KEY`. `layout.tsx` adds an inline script before children that reads localStorage, resolves system preference and sets `document.documentElement.dataset.theme` plus `colorScheme`. `ThemeProvider` listens to system changes only when preference is `system` and updates localStorage immediately.

- [ ] **Step 5: Add the segmented settings control**

`ThemeSettings` renders three radio-like buttons with `aria-pressed`, applies the choice immediately and PATCHes `/api/auth/profile`. On failure it restores the previous theme and presents an `aria-live` error.

- [ ] **Step 6: Convert literal theme colors to semantic tokens**

Define light values under `:root` and dark values under `[data-theme="dark"]` for `--canvas`, `--surface`, `--surface-soft`, `--text`, `--muted`, `--hairline`, `--primary`, `--focus`, `--success`, `--warning`, `--danger`. Replace literal page/surface/text/border colors in components touched by this milestone. Keep chart series distinguishable by label and pattern, not only hue.

- [ ] **Step 7: Run API, smoke, TypeScript and build**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests/test_auth.py -q`

Run: `cd ../web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add apps/api/app apps/api/tests/test_auth.py apps/web/lib/theme.ts apps/web/components/theme-provider.tsx apps/web/components/theme-settings.tsx apps/web/components/session-profile.tsx apps/web/app/layout.tsx apps/web/app/configuracoes/page.tsx apps/web/app/globals.css apps/web/tests/smoke.mjs
git commit -m "feat: add persistent light dark and system themes"
```

---

### Task 7: Add demo-dataset UX to onboarding, empty dashboard and settings

**Files:**
- Create: `apps/web/components/demo-dataset-control.tsx`
- Modify: `apps/web/app/onboarding/page.tsx`
- Modify: `apps/web/components/dashboard-view.tsx`
- Modify: `apps/web/app/configuracoes/page.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Consumes: `DemoDatasetState` and `/api/financial/demo-dataset`.
- Emits: `nexo:financial-data-changed` after successful install or cleanup.

- [ ] **Step 1: Add failing smoke assertions**

Require `Explorar com dados de exemplo`, `Limpar dados de exemplo`, `DemoDatasetControl`, `aria-busy`, confirmation copy and the global event.

- [ ] **Step 2: Run smoke test and verify failure**

Run: `cd apps/web; npm test`

Expected: FAIL for missing dataset UX.

- [ ] **Step 3: Implement the reusable control**

The component fetches status on mount, supports `install` and `cleanup` variants, opens an accessible confirmation dialog, disables controls during mutation, reports progress and errors through `aria-live`, then dispatches `nexo:financial-data-changed`.

Confirmation copy must enumerate: 3 contas, 1 cartão, categorias e movimentações relativas ao mês atual. Cleanup copy must state that only demonstrative resources are targeted and adopted resources are preserved.

- [ ] **Step 4: Integrate the three entry points**

Place install action in onboarding and `.dashboard-empty`. Place status, installed date and cleanup action in Configurações. Do not render install CTA when state is active.

- [ ] **Step 5: Run smoke, TypeScript and responsive build checks**

Run: `cd apps/web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/web/components/demo-dataset-control.tsx apps/web/app/onboarding/page.tsx apps/web/components/dashboard-view.tsx apps/web/app/configuracoes/page.tsx apps/web/app/globals.css apps/web/tests/smoke.mjs
git commit -m "feat(web): add optional demo dataset experience"
```

---

### Task 8: Refine the single-screen credit-card form

**Files:**
- Create: `apps/web/components/currency-input.tsx`
- Create: `apps/web/components/credit-card-form.tsx`
- Modify: `apps/web/components/card-manager.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- `CurrencyInput` receives decimal cents as a string and emits normalized `"1234.56"`.
- `CreditCardForm` receives accounts, optional card, `onSaved` and `onCancel`.

- [ ] **Step 1: Add failing smoke markers for the complete form**

Require `Identificação`, `Ciclo e pagamento`, `Prévia do cartão`, `aria-describedby`, field-level errors, normalized BRL value, saving state and `/contas` empty-account action.

- [ ] **Step 2: Run smoke tests and verify failure**

Run: `cd apps/web; npm test`

Expected: FAIL because the current inline form lacks the required structure.

- [ ] **Step 3: Implement `CurrencyInput`**

Keep digits only, interpret the last two digits as cents, display with `Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })`, and call `onValueChange((cents / 100).toFixed(2))`. Preserve label association and `aria-invalid`.

- [ ] **Step 4: Implement `CreditCardForm`**

Render one form with two fieldsets, live visual preview, inline errors and help IDs for closing/due dates. Validate name length, positive limit, days 1-31, distinct user intent for closing/due dates and required payment account. Guard duplicate submission with `saving` before the fetch begins.

When accounts are empty, replace submit with a clear empty state and `<Link href="/contas">Criar conta</Link>`.

- [ ] **Step 5: Replace the inline card form and add responsive styles**

Use a two-column content grid above 768px and one column below. Keep preview dimensions stable with `aspect-ratio`, and ensure labels/errors do not resize the preview.

- [ ] **Step 6: Run smoke, TypeScript and build**

Run: `cd apps/web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add apps/web/components/currency-input.tsx apps/web/components/credit-card-form.tsx apps/web/components/card-manager.tsx apps/web/app/globals.css apps/web/tests/smoke.mjs
git commit -m "feat(web): refine credit card creation and editing"
```

---

### Task 9: Present real category deletion outcomes

**Files:**
- Modify: `apps/web/components/category-manager.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Consumes: `CategoryDeleteResult`.
- User-facing outcomes: `Categoria excluída.` or `Categoria arquivada para preservar seu histórico.`

- [ ] **Step 1: Add failing smoke assertions**

Require `Excluir categoria`, impact confirmation text, `result.action === "deleted"`, `result.action === "archived"` and both success messages.

- [ ] **Step 2: Run smoke and verify failure**

Run: `cd apps/web; npm test`

Expected: FAIL because the current action is archive-only.

- [ ] **Step 3: Change the action flow**

Rename `archivingId` to `deletingId` and `archiveCategory` to `deleteCategory`. Confirm with: `Excluir <nome>? Se a categoria tiver histórico, o Nexo irá arquivá-la para preservar seus lançamentos.` Parse `CategoryDeleteResult`, select the exact success message from `action`, reload the active tree and dispatch the financial update event.

- [ ] **Step 4: Verify selectors remain active-only**

Exercise transaction, card-purchase, installment and recurring selectors after an archived result. They must receive no archived category from the API.

- [ ] **Step 5: Run smoke, TypeScript and build**

Run: `cd apps/web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/web/components/category-manager.tsx apps/web/app/globals.css apps/web/tests/smoke.mjs
git commit -m "feat(web): show category deletion and archive outcomes"
```

---

### Task 10: Normalize financial mutation feedback and Fin refresh

**Files:**
- Modify: `apps/web/components/account-manager.tsx`
- Modify: `apps/web/components/card-manager.tsx`
- Modify: `apps/web/components/category-manager.tsx`
- Modify: `apps/web/components/transaction-manager.tsx`
- Modify: `apps/web/components/fin-conversation.tsx`
- Modify: `apps/web/components/dashboard-view.tsx`
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/tests/smoke.mjs`

**Interfaces:**
- Shared browser event remains `nexo:financial-data-changed`.
- Every mutating form exposes idle, saving, success and actionable error states.

- [ ] **Step 1: Add smoke assertions for consistent states and refresh listeners**

Require `aria-busy`, `aria-live="polite"`, disabled duplicate-submit controls and `nexo:financial-data-changed` in every manager plus dashboard and Fin conversation.

- [ ] **Step 2: Run smoke and identify missing state contracts**

Run: `cd apps/web; npm test`

Expected: FAIL with the exact manager missing a marker.

- [ ] **Step 3: Normalize managers**

For each mutation: clear stale feedback before request, set `saving` before fetch, block repeated submits, parse backend `detail`, show success, close/reset only after success, dispatch the global event, then restore idle state in `finally`.

- [ ] **Step 4: Refresh dashboard and Fin context**

Dashboard already listens to the event; preserve it. Add the same listener to the Fin conversation/context loader so the next message and visible financial context use fresh server data after any mutation.

- [ ] **Step 5: Run full frontend checks**

Run: `cd apps/web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add apps/web/components apps/web/app/globals.css apps/web/tests/smoke.mjs
git commit -m "refactor(web): normalize financial mutation feedback"
```

---

### Task 11: Complete security, migration and visual acceptance

**Files:**
- Modify: `README.md`
- Modify: `docs/DEPLOYMENT.md`
- Modify: `apps/web/tests/smoke.mjs`
- Modify only when a failing acceptance test identifies a defect: files from Tasks 1-10.

**Interfaces:**
- Produces a release candidate with one Alembic head, passing suites and validated desktop/mobile themes.

- [ ] **Step 1: Run the complete API suite**

Run: `cd apps/api; $env:PYTHONPATH=(Get-Location).Path; python -m pytest tests -q`

Expected: PASS, including rollback, user isolation, card cycle, category lifecycle and audit tests.

- [ ] **Step 2: Validate migrations**

Run: `cd apps/api; python -m alembic heads; python -m alembic upgrade head; python -m alembic current`

Expected: one head and current revision `b81f4c6d2a10`.

- [ ] **Step 3: Run complete frontend verification**

Run: `cd apps/web; npm test; npx tsc --noEmit; npm run build`

Expected: PASS.

- [ ] **Step 4: Verify API security contracts manually**

For demo install/cleanup, category DELETE, card POST/PUT and profile PATCH, verify unauthenticated requests return 401, cross-user IDs return 404, invalid BFF origin returns 403 and audit payloads omit amounts, descriptions, email and internal manifests.

- [ ] **Step 5: Perform browser acceptance**

At 1440x900 and 390x844, capture Dashboard, Configurações, Cartões, Categorias and the demo confirmation in light/dark modes. Verify no overflow, no overlapping chat panel, visible keyboard focus, readable charts, stable card preview and correct Nexo light/dark logo variants.

- [ ] **Step 6: Test PWA and offline shell**

Verify `/manifest.webmanifest`, service-worker activation, maskable/Apple icons and cached offline page. Confirm theme color remains `#101a19` and installation does not auto-create financial data.

- [ ] **Step 7: Update operational documentation**

Document migration command, dataset endpoints, `theme_preference`, cleanup behavior, rollback steps and a warning that demo data is never installed automatically.

- [ ] **Step 8: Update the knowledge graph**

Run: `graphify update .`

Expected: SUCCESS.

- [ ] **Step 9: Commit final verification and docs**

```powershell
git add README.md docs/DEPLOYMENT.md apps/web/tests/smoke.mjs graphify-out
git commit -m "docs: finalize Nexo financial foundation rollout"
```

## Self-Review Results

- Spec coverage: dataset lifecycle, relative sample data, theme persistence, no-flash application, category delete/archive, card cycle, duplicate protection, consistent feedback, security, audit, PWA and final visual checks all map to Tasks 1-11.
- Placeholder scan: no `TBD`, `TODO`, deferred implementation or unnamed test step remains.
- Type consistency: `DemoDatasetState`, `CategoryDeleteResult`, `ThemePreference`, `_statement_cycle` and `nexo:financial-data-changed` retain the same names at every producer/consumer boundary.
- Scope control: Open Finance, automatic bank imports, shared accounts, organizations and email changes remain excluded.
