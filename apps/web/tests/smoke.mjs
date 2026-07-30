import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const requiredFiles = [
  "app/page.tsx",
  "app/login/page.tsx",
  "app/cadastro/page.tsx",
  "app/onboarding/page.tsx",
  "app/dashboard/page.tsx",
  "app/contas/page.tsx",
  "app/cartoes/page.tsx",
  "app/transacoes/page.tsx",
  "app/categorias/page.tsx",
  "app/fin/page.tsx",
  "app/configuracoes/page.tsx",
  "app/verificar-email/page.tsx",
  "app/recuperar-senha/page.tsx",
  "app/redefinir-senha/page.tsx",
  "app/mfa/page.tsx",
  "app/manifest.ts",
  "app/offline/page.tsx",
  "components/app-shell.tsx",
  "components/auth-form.tsx",
  "components/email-verification-form.tsx",
  "components/password-recovery-form.tsx",
  "components/password-reset-form.tsx",
  "components/mfa-challenge-form.tsx",
  "components/mfa-settings.tsx",
  "components/session-profile.tsx",
  "components/theme-provider.tsx",
  "components/theme-toggle.tsx",
  "components/theme-settings.tsx",
  "components/profile-settings.tsx",
  "components/install-app-button.tsx",
  "components/pwa-registration.tsx",
  "components/proposal-card.tsx",
  "components/fin-conversation.tsx",
  "components/dashboard-view.tsx",
  "components/demo-dataset-control.tsx",
  "components/navigation-drawer.tsx",
  "components/fin-chat-panel.tsx",
  "components/pending-proposals-provider.tsx",
  "components/movement-review-inbox.tsx",
  "components/transaction-manager.tsx",
  "components/account-manager.tsx",
  "components/category-manager.tsx",
  "components/card-manager.tsx",
  "components/currency-input.tsx",
  "components/credit-card-form.tsx",
  "components/brand-assets.tsx",
  "components/ui/cash-flow-chart.tsx",
  "components/ui/financial-score-cards.tsx",
  "components/ui/financial-dashboard.tsx",
  "lib/api.ts",
  "lib/auth-cookies.ts",
  "lib/auth-server.ts",
  "lib/financial-types.ts",
  "lib/theme.ts",
  "app/api/auth/login/route.ts",
  "app/api/auth/register/route.ts",
  "app/api/auth/session/route.ts",
  "app/api/auth/logout/route.ts",
  "app/api/auth/profile/route.ts",
  "app/api/auth/mfa/challenge/route.ts",
  "app/api/auth/mfa/status/route.ts",
  "app/api/auth/mfa/enroll/route.ts",
  "app/api/auth/mfa/confirm/route.ts",
  "app/api/auth/mfa/recovery-codes/route.ts",
  "app/api/auth/mfa/route.ts",
  "app/api/auth/email-verification/request/route.ts",
  "app/api/auth/email-verification/confirm/route.ts",
  "app/api/auth/password-reset/request/route.ts",
  "app/api/auth/password-reset/confirm/route.ts",
  "app/api/assistant/message/route.ts",
  "app/api/assistant/proposals/route.ts",
  "app/api/financial/dashboard/route.ts",
  "app/api/financial/demo-dataset/route.ts",
  "app/api/financial/accounts/route.ts",
  "app/api/financial/accounts/[accountId]/route.ts",
  "app/api/financial/categories/route.ts",
  "app/api/financial/categories/[categoryId]/route.ts",
  "app/api/financial/credit-cards/route.ts",
  "app/api/financial/credit-cards/[cardId]/purchases/route.ts",
  "app/api/financial/credit-cards/[cardId]/route.ts",
  "app/api/financial/statements/[statementId]/pay/route.ts",
  "app/api/financial/transactions/route.ts",
  "app/api/financial/transactions/[transactionId]/route.ts",
  "app/api/assistant/proposals/[proposalId]/route.ts",
  "app/api/assistant/proposals/[proposalId]/[action]/route.ts",
  "middleware.ts",
  "instrumentation.ts",
  "instrumentation-client.ts",
  "sentry.server.config.ts",
  "sentry.edge.config.ts",
  "app/global-error.tsx",
  "lib/sentry-scrub.ts",
  "lib/runtime-config.ts",
  "public/sw.js",
  "public/favicon.ico",
  "public/icons/nexo-16.png",
  "public/icons/nexo-32.png",
  "public/icons/nexo-192.png",
  "public/icons/nexo-512.png",
  "public/icons/nexo-maskable-512.png",
  "public/icons/nexo-apple-180.png",
  "public/brand/nexo-logo.webp",
  "public/brand/nexo-logo-dark.webp",
  "public/brand/fin-mascot-v2.png",
  "public/brand/fin-mascot-v2.webp",
  "public/brand/fin-avatar-v2.webp"
];

const missing = requiredFiles.filter((file) => !existsSync(join(root, file)));
if (missing.length > 0) {
  throw new Error(`Missing required frontend files: ${missing.join(", ")}`);
}

const finPage =
  readFileSync(join(root, "app/fin/page.tsx"), "utf8") +
  readFileSync(join(root, "components/proposal-card.tsx"), "utf8");
for (const label of ["Confirmar", "Editar", "Cancelar"]) {
  if (!finPage.includes(label)) {
    throw new Error(`Fin page must expose ${label}`);
  }
}

const dashboard =
  readFileSync(join(root, "app/dashboard/page.tsx"), "utf8") +
  readFileSync(join(root, "components/dashboard-view.tsx"), "utf8") +
  readFileSync(join(root, "components/date-range-picker.tsx"), "utf8");
for (const label of ["Saldo total", "Receitas", "Despesas", "Faturas"]) {
  if (!dashboard.includes(label)) {
    throw new Error(`Dashboard must include ${label}`);
  }
}

for (const marker of ["metric-card", "CashFlowChart", "Nova transação"]) {
  if (!dashboard.includes(marker)) {
    throw new Error(`Dashboard must include ${marker}`);
  }
}

for (const marker of ["CashFlowChart", "FinancialScoreCards", "FinancialDashboard"]) {
  if (marker === "CashFlowChart" && !dashboard.includes(marker)) {
    throw new Error(`Dashboard integrations must include ${marker}`);
  }
}

for (const marker of ["/api/financial/dashboard", "DashboardSkeleton", "dashboard-empty", "recent_transactions"]) {
  if (!dashboard.includes(marker)) {
    throw new Error(`Real dashboard must include ${marker}`);
  }
}

const sessionRoute = readFileSync(join(root, "app/api/auth/session/route.ts"), "utf8");
for (const marker of ["fetchCurrentUser", "refreshSession", "validateRequestOrigin", "clearAuthCookies"]) {
  if (!sessionRoute.includes(marker)) {
    throw new Error(`Session route must use authenticated backend flow: missing ${marker}`);
  }
}
for (const forbidden of ["mockUser", "demo@nexo.app", "Usuário Demo"]) {
  if (sessionRoute.includes(forbidden)) {
    throw new Error(`Session route must not include demo user marker: ${forbidden}`);
  }
}

const dashboardRoute = readFileSync(join(root, "app/api/financial/dashboard/route.ts"), "utf8");
for (const marker of ["authenticatedBackendRequest", "/financial/dashboard", "ACCESS_COOKIE", "REFRESH_COOKIE"]) {
  if (!dashboardRoute.includes(marker)) {
    throw new Error(`Dashboard route must proxy the authenticated backend: missing ${marker}`);
  }
}
for (const forbidden of ["mockData", "45280.50", "Passagem Aérea"]) {
  if (dashboardRoute.includes(forbidden)) {
    throw new Error(`Dashboard route must not include static financial demo data: ${forbidden}`);
  }
}
for (const marker of ["DateRangePicker", 'type="date"', "Últimos 30 dias", "Aplicar período"]) {
  if (!dashboard.includes(marker)) {
    throw new Error(`Dashboard period selector must include ${marker}`);
  }
}

for (const fakeValue of ["R$ 5.420,80", "R$ 8.200,00", "R$ 2.779,20", "R$ 1.148,90"]) {
  if (dashboard.includes(fakeValue)) {
    throw new Error(`Dashboard must not ship demo value ${fakeValue}`);
  }
}

const chart = readFileSync(join(root, "components/ui/cash-flow-chart.tsx"), "utf8");
for (const marker of [
  "AreaChart",
  "ResponsiveContainer",
  "Tooltip",
  "accessibilityLayer",
  "sr-only",
  "var(--chart-income)",
  "var(--chart-expense)",
  'strokeDasharray="7 4"'
]) {
  if (!chart.includes(marker)) {
    throw new Error(`Accessible cash flow chart must include ${marker}`);
  }
}

const scoreCards = readFileSync(join(root, "components/ui/financial-score-cards.tsx"), "utf8");
for (const marker of ["score-gauge", "Saúde financeira", "Reserva de emergência"]) {
  if (!scoreCards.includes(marker)) {
    throw new Error(`Financial score cards must include ${marker}`);
  }
}

const financialDashboard = readFileSync(join(root, "components/ui/financial-dashboard.tsx"), "utf8");
for (const marker of ["Central financeira", "Ações rápidas", "Atividade recente"]) {
  if (!financialDashboard.includes(marker)) {
    throw new Error(`Financial dashboard must include ${marker}`);
  }
}

const conversation =
  readFileSync(join(root, "components/fin-conversation.tsx"), "utf8") +
  readFileSync(join(root, "components/proposal-card.tsx"), "utf8") +
  readFileSync(join(root, "app/fin/page.tsx"), "utf8");
for (const marker of [
  "/api/assistant/message",
  "client_message_id",
  "Confirmar",
  "Editar",
  "Cancelar",
  'aria-live="polite"'
]) {
  if (!conversation.includes(marker)) {
    throw new Error(`Fin conversation must include ${marker}`);
  }
}

const shell = readFileSync(join(root, "components/app-shell.tsx"), "utf8");
for (const marker of ["usePathname", "Menu principal", "NavigationDrawer", "FinChatPanel", "PendingProposalsProvider", "SessionProfile", "ThemeToggle"]) {
  if (!shell.includes(marker)) {
    throw new Error(`Nexo app shell must include ${marker}`);
  }
}

const brand =
  readFileSync(join(root, "components/brand-assets.tsx"), "utf8") +
  readFileSync(join(root, "components/app-shell.tsx"), "utf8") +
  readFileSync(join(root, "components/navigation-drawer.tsx"), "utf8") +
  readFileSync(join(root, "components/fin-conversation.tsx"), "utf8") +
  readFileSync(join(root, "app/manifest.ts"), "utf8");
for (const marker of [
  "NexoMark",
  "NexoLogo",
  "FinMascot",
  "/icons/nexo-512.png",
  "/icons/nexo-maskable-512.png",
  "/brand/nexo-logo.webp",
  "/brand/nexo-logo-dark.webp",
  "/brand/fin-mascot-v2.webp",
  "/brand/fin-avatar-v2.webp",
  'variant?: "full" | "avatar"',
  'variant="avatar"'
]) {
  if (!brand.includes(marker)) {
    throw new Error(`Institutional Nexo branding must include ${marker}`);
  }
}

for (const legacyMarker of ["mobile-bottom-nav", "more-sheet", 'className="sidebar"']) {
  if (shell.includes(legacyMarker)) {
    throw new Error(`Nexo app shell must not render legacy ${legacyMarker}`);
  }
}

const movementInbox =
  readFileSync(join(root, "components/movement-review-inbox.tsx"), "utf8") +
  readFileSync(join(root, "components/pending-proposals-provider.tsx"), "utf8") +
  dashboard;
for (const marker of ["Movimentações reconhecidas", "Aprovar selecionadas", "possible_duplicate", "confidence", "nexo:financial-data-changed", "MovementReviewInbox"]) {
  if (!movementInbox.includes(marker)) {
    throw new Error(`Movement review inbox must include ${marker}`);
  }
}

const transactions =
  readFileSync(join(root, "app/transacoes/page.tsx"), "utf8") +
  readFileSync(join(root, "components/transaction-manager.tsx"), "utf8") +
  readFileSync(join(root, "app/api/financial/transactions/route.ts"), "utf8");
for (const marker of [
  "Descrição do",
  'name="description"',
  "maxLength={500}",
  "/api/financial/transactions",
  "nexo:financial-data-changed",
  "FinancialTransaction"
]) {
  if (!transactions.includes(marker)) {
    throw new Error(`Functional transaction form must include ${marker}`);
  }
}

const accounts =
  readFileSync(join(root, "app/contas/page.tsx"), "utf8") +
  readFileSync(join(root, "components/account-manager.tsx"), "utf8") +
  readFileSync(join(root, "app/api/financial/accounts/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/financial/accounts/[accountId]/route.ts"), "utf8");
for (const marker of [
  "AccountManager",
  "/api/financial/accounts",
  "Nova conta",
  "Saldo inicial",
  "validateRequestOrigin",
  "nexo:financial-data-changed"
]) {
  if (!accounts.includes(marker)) {
    throw new Error(`Functional accounts manager must include ${marker}`);
  }
}
if (accounts.includes("R$ 5.420,80")) {
  throw new Error("Accounts page must not ship demo balances");
}

const categories =
  readFileSync(join(root, "app/categorias/page.tsx"), "utf8") +
  readFileSync(join(root, "components/category-manager.tsx"), "utf8") +
  readFileSync(join(root, "app/api/financial/categories/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/financial/categories/[categoryId]/route.ts"), "utf8");
for (const marker of [
  "CategoryManager",
  "/api/financial/categories",
  "Nova categoria",
  "Categoria principal",
  "Excluir categoria",
  "Excluir ${category.name}? Se a categoria tiver histórico, o Nexo irá arquivá-la para preservar seus lançamentos.",
  'result.action === "deleted"',
  'result.action === "archived"',
  "Categoria excluída.",
  "Categoria arquivada para preservar seu histórico.",
  "validateRequestOrigin",
  "nexo:financial-data-changed"
]) {
  if (!categories.includes(marker)) {
    throw new Error(`Functional categories manager must include ${marker}`);
  }
}

const categorySelectorSources =
  readFileSync(join(root, "components/transaction-manager.tsx"), "utf8") +
  readFileSync(join(root, "components/card-manager.tsx"), "utf8") +
  readFileSync(join(root, "../api/app/services/financial_service.py"), "utf8");
for (const marker of [
  'id="transaction-category"',
  'id="purchase-category"',
  "def get_category_tree",
  "Category.is_archived.is_(False)",
  "def create_transaction",
  "def create_card_purchase",
  "def create_installment_plan",
  "def create_recurring_rule",
  "_validate_category(db, user_id, category_id)",
  "Archived categories cannot receive new records"
]) {
  if (!categorySelectorSources.includes(marker)) {
    throw new Error(`Category selectors must remain active-only: missing ${marker}`);
  }
}

const demoDatasetRoute = readFileSync(
  join(root, "app/api/financial/demo-dataset/route.ts"),
  "utf8"
);
for (const marker of [
  "/financial/demo-dataset",
  "validateRequestOrigin",
  "export async function GET",
  "export async function POST",
  "export async function DELETE",
  "data, tokens, status"
]) {
  if (!demoDatasetRoute.includes(marker)) {
    throw new Error(`Demo dataset BFF must include ${marker}`);
  }
}

const demoDatasetExperience =
  readFileSync(join(root, "components/demo-dataset-control.tsx"), "utf8") +
  readFileSync(join(root, "app/onboarding/page.tsx"), "utf8") +
  readFileSync(join(root, "components/dashboard-view.tsx"), "utf8") +
  readFileSync(join(root, "app/configuracoes/page.tsx"), "utf8");
for (const marker of [
  "DemoDatasetControl",
  "Explorar com dados de exemplo",
  "Limpar dados de exemplo",
  "aria-busy",
  "3 contas, 1 cart",
  "recursos demonstrativos",
  "Recursos adotados",
  "nexo:financial-data-changed",
  "/api/financial/demo-dataset",
  "<dialog",
  "AbortController",
  "mutationControllerRef",
  "demo-dialog-feedback"
]) {
  if (!demoDatasetExperience.includes(marker)) {
    throw new Error(`Optional demo dataset experience must include ${marker}`);
  }
}

const financialTypes = readFileSync(join(root, "lib/financial-types.ts"), "utf8");
for (const marker of [
  "DemoDatasetState",
  "CategoryDeleteResult",
  'action: "deleted" | "archived"',
  "recurring_rules"
]) {
  if (!financialTypes.includes(marker)) {
    throw new Error(`Financial contracts must include ${marker}`);
  }
}

const cards =
  readFileSync(join(root, "app/cartoes/page.tsx"), "utf8") +
  readFileSync(join(root, "components/card-manager.tsx"), "utf8") +
  readFileSync(join(root, "app/api/financial/credit-cards/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/financial/credit-cards/[cardId]/purchases/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/financial/credit-cards/[cardId]/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/financial/statements/[statementId]/pay/route.ts"), "utf8");
for (const marker of [
  "CardManager",
  "/api/financial/credit-cards",
  "Novo cartão",
  "Registrar compra",
  "Editar cartão",
  "Arquivar cartão",
  "Pagar fatura",
  "Limite disponível",
  "validateRequestOrigin",
  "nexo:financial-data-changed"
]) {
  if (!cards.includes(marker)) {
    throw new Error(`Functional cards manager must include ${marker}`);
  }
}

const cardForm =
  readFileSync(join(root, "components/currency-input.tsx"), "utf8") +
  readFileSync(join(root, "components/credit-card-form.tsx"), "utf8") +
  readFileSync(join(root, "components/card-manager.tsx"), "utf8");
for (const marker of [
  "CurrencyInput",
  "CreditCardForm",
  "Identifica",
  "Ciclo e pagamento",
  "via do cart",
  "aria-describedby",
  "field-error",
  "toFixed(2)",
  "saving",
  'href="/contas"'
]) {
  if (!cardForm.includes(marker)) {
    throw new Error(`Refined credit card form must include ${marker}`);
  }
}
for (const fakeValue of ["R$ 3.851,10", "R$ 1.148,90", "20/07/2026"]) {
  if (cards.includes(fakeValue)) {
    throw new Error(`Cards page must not ship demo value ${fakeValue}`);
  }
}

const authCookies = readFileSync(join(root, "lib/auth-cookies.ts"), "utf8");
const authMiddleware = readFileSync(join(root, "middleware.ts"), "utf8");
for (const marker of [
  "__Host-nexo",
  "_access_token",
  "_refresh_token",
  "_mfa_challenge",
  "httpOnly: true",
  'sameSite: "strict"',
  "secure: process.env.NODE_ENV === \"production\""
]) {
  if (!authCookies.includes(marker)) {
    throw new Error(`Auth cookies must include ${marker}`);
  }
}
for (const marker of ["__Host-nexo", "_access_token", "_refresh_token"]) {
  if (!authMiddleware.includes(marker)) {
    throw new Error(`Auth middleware must use the current cookie contract: ${marker}`);
  }
}

const authRoutes = ["login", "register", "session", "logout"]
  .map((route) => readFileSync(join(root, `app/api/auth/${route}/route.ts`), "utf8"))
  .join("\n");
for (const marker of [
  "setAuthCookies",
  "clearAuthCookies",
  "refreshSession",
  "validateRequestOrigin"
]) {
  if (!authRoutes.includes(marker)) {
    throw new Error(`Auth facade must include ${marker}`);
  }
}

const authUi =
  readFileSync(join(root, "components/auth-form.tsx"), "utf8") +
  readFileSync(join(root, "components/session-profile.tsx"), "utf8") +
  readFileSync(join(root, "app/login/page.tsx"), "utf8") +
  readFileSync(join(root, "app/cadastro/page.tsx"), "utf8");
for (const marker of [
  "/api/auth/login",
  "/api/auth/register",
  "/api/auth/logout",
  'aria-live="polite"',
  '"new-password"',
  "Mostrar senha"
]) {
  if (!authUi.includes(marker)) {
    throw new Error(`Auth UX must include ${marker}`);
  }
}

const middleware = readFileSync(join(root, "middleware.ts"), "utf8");
for (const marker of ["protectedRoutes", "__Host-nexo", "_access_token", "_refresh_token", "/login"]) {
  if (!middleware.includes(marker)) {
    throw new Error(`Route protection must include ${marker}`);
  }
}

const nextConfig = readFileSync(join(root, "next.config.ts"), "utf8");
for (const marker of [
  "Content-Security-Policy",
  "X-Content-Type-Options",
  "Referrer-Policy",
  "Permissions-Policy"
]) {
  if (!nextConfig.includes(marker)) {
    throw new Error(`Security headers must include ${marker}`);
  }
}

const layout = readFileSync(join(root, "app/layout.tsx"), "utf8");
for (const marker of ["PWARegistration", "viewportFit", "/manifest.webmanifest"]) {
  if (!layout.includes(marker)) {
    throw new Error(`Root layout must include ${marker}`);
  }
}

const productBrand =
  layout +
  readFileSync(join(root, "app/manifest.ts"), "utf8") +
  readFileSync(join(root, "app/login/page.tsx"), "utf8") +
  readFileSync(join(root, "app/cadastro/page.tsx"), "utf8") +
  shell;
for (const marker of ['title: "Nexo"', 'applicationName: "Nexo"', 'short_name: "Nexo"', "Entrar no Nexo", "NexoMark"]) {
  if (!productBrand.includes(marker)) {
    throw new Error(`Nexo product branding must include ${marker}`);
  }
}

if (!conversation.includes("Conversa com o Fin")) {
  throw new Error("Fin must remain the assistant identity");
}

const styles = readFileSync(join(root, "app/globals.css"), "utf8");
if (styles.includes("min-width: 320px")) {
  throw new Error("Global styles must not force horizontal overflow on narrow mobile viewports");
}

for (const marker of [
  "--chrome-sidebar:",
  "--chrome-sidebar-active:",
  "--chrome-sidebar-active-ink:",
  "--chrome-topbar:",
  "--chrome-topbar-hover:",
  "--chrome-topbar-border:",
  "background: var(--chrome-sidebar);",
  "background: var(--chrome-topbar);"
]) {
  if (!styles.includes(marker)) {
    throw new Error(`Application chrome must use the Mintlify-inspired semantic palette: missing ${marker}`);
  }
}

const financialMutationFeedback = {
  "Account manager": readFileSync(join(root, "components/account-manager.tsx"), "utf8"),
  "Card manager": readFileSync(join(root, "components/card-manager.tsx"), "utf8"),
  "Category manager": readFileSync(join(root, "components/category-manager.tsx"), "utf8"),
  "Transaction manager": readFileSync(join(root, "components/transaction-manager.tsx"), "utf8")
};

for (const [manager, source] of Object.entries(financialMutationFeedback)) {
  for (const marker of ["aria-busy", 'aria-live="polite"', "disabled={saving", "nexo:financial-data-changed"]) {
    if (!source.includes(marker)) {
      throw new Error(`${manager} must expose normalized mutation feedback: missing ${marker}`);
    }
  }
}

const finRefresh = readFileSync(join(root, "components/fin-conversation.tsx"), "utf8");
for (const marker of [
  "aria-busy",
  'aria-live="polite"',
  "disabled={sending",
  "nexo:financial-data-changed",
  "addEventListener",
  "removeEventListener",
  "DashboardData",
  'fetch("/api/financial/dashboard"',
  'cache: "no-store"',
  "refreshPromiseRef",
  "await refreshPromise",
  "financialContext",
  "async function waitForLatestFinancialContext",
  "while (true)",
  "const requestId = contextRequestRef.current",
  "const refreshPromise = refreshPromiseRef.current",
  "requestId === contextRequestRef.current",
  "refreshPromise === refreshPromiseRef.current",
  "await waitForLatestFinancialContext();"
]) {
  if (!finRefresh.includes(marker)) {
    throw new Error(`Fin conversation must refresh financial context: missing ${marker}`);
  }
}
if (finRefresh.includes("Seus dados financeiros foram atualizados. Vou considerar os valores mais recentes nas próximas respostas.")) {
  throw new Error("Fin conversation must not use a static financial refresh message");
}
const finSubmitPreparation = finRefresh.slice(
  finRefresh.indexOf("async function handleSubmit"),
  finRefresh.indexOf('fetch("/api/assistant/message"')
);
if (!finSubmitPreparation.includes("await waitForLatestFinancialContext();")) {
  throw new Error("Fin submission must wait for the latest financial context generation");
}
if (finSubmitPreparation.includes("const refreshPromise = refreshPromiseRef.current")) {
  throw new Error("Fin submission must not regress to a single captured financial refresh promise");
}

const creditCardFeedback = readFileSync(join(root, "components/credit-card-form.tsx"), "utf8");
for (const marker of ["aria-busy={saving}", 'aria-live="polite"', "if (saving) return", "disabled={saving}", "fetch("]) {
  if (!creditCardFeedback.includes(marker)) {
    throw new Error(`Credit card form must expose normalized save feedback: missing ${marker}`);
  }
}

for (const marker of ["aria-busy", 'aria-live="polite"', "nexo:financial-data-changed", "addEventListener", "removeEventListener"]) {
  if (!dashboard.includes(marker)) {
    throw new Error(`Dashboard must preserve financial refresh feedback: missing ${marker}`);
  }
}

for (const marker of [
  "env(safe-area-inset-bottom)",
  "prefers-reduced-motion",
  "@media (max-width: 767px)"
]) {
  if (!styles.includes(marker)) {
    throw new Error(`Global styles must include ${marker}`);
  }
}

const serviceWorker = readFileSync(join(root, "public/sw.js"), "utf8");
for (const marker of [
  "install",
  "activate",
  "fetch",
  "/offline",
  "/brand/fin-mascot-v2.webp",
  "/brand/fin-avatar-v2.webp"
]) {
  if (!serviceWorker.includes(marker)) {
    throw new Error(`Service worker must include ${marker}`);
  }
}
if (serviceWorker.includes("/brand/fin-mascot.webp") || serviceWorker.includes("/brand/fin-avatar.webp")) {
  throw new Error("Service worker must cache the Fin v2 assets only");
}

const manifest = readFileSync(join(root, "app/manifest.ts"), "utf8");
for (const marker of [
  'name: "Nexo - Controle financeiro"',
  'start_url: "/dashboard"',
  'display: "standalone"',
  'theme_color: "#101a19"',
  'purpose: "maskable"'
]) {
  if (!manifest.includes(marker)) {
    throw new Error(`PWA manifest must include ${marker}`);
  }
}

const onboarding = readFileSync(join(root, "app/onboarding/page.tsx"), "utf8");
const themeSettings = readFileSync(join(root, "components/theme-settings.tsx"), "utf8");
for (const source of [onboarding, themeSettings]) {
  if (/>[^<{]*\\u[0-9a-f]{4}/i.test(source)) {
    throw new Error("JSX text must not render Unicode escape sequences literally");
  }
}

const settings = readFileSync(join(root, "app/configuracoes/page.tsx"), "utf8");
if (!settings.includes("InstallAppButton")) {
  throw new Error("Settings must expose the PWA installation action");
}
const privacyExperience =
  readFileSync(join(root, "components/privacy-settings.tsx"), "utf8") +
  readFileSync(join(root, "app/privacidade/page.tsx"), "utf8") +
  readFileSync(join(root, "app/api/auth/data-export/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/auth/account/route.ts"), "utf8");
for (const marker of ["ai_data_processing_consent", "/api/auth/data-export", "/api/auth/account", "Aviso de Privacidade", "EXCLUIR"]) {
  if (!privacyExperience.includes(marker)) {
    throw new Error(`Privacy controls must include ${marker}`);
  }
}
const securityExperience =
  readFileSync(join(root, "components/security-settings.tsx"), "utf8") +
  readFileSync(join(root, "app/api/auth/sessions/route.ts"), "utf8") +
  readFileSync(join(root, "app/api/auth/sessions/[sessionId]/route.ts"), "utf8");
for (const marker of ["Sessões ativas", "/api/auth/sessions", "validateRequestOrigin", "Encerrar sessão"]) {
  if (!securityExperience.includes(marker)) {
    throw new Error(`Session security controls must include ${marker}`);
  }
}

const verificationExperience =
  readFileSync(join(root, "components/email-verification-form.tsx"), "utf8") +
  readFileSync(join(root, "app/verificar-email/page.tsx"), "utf8");
for (const marker of [
  "/api/auth/email-verification/confirm",
  "/api/auth/email-verification/request",
  "token",
  "reenviar",
  'aria-live="polite"',
  "role=\"status\"",
  "role=\"alert\""
]) {
  if (!verificationExperience.includes(marker)) {
    throw new Error(`Email verification UX must include ${marker}`);
  }
}

const passwordResetExperience =
  readFileSync(join(root, "components/password-recovery-form.tsx"), "utf8") +
  readFileSync(join(root, "components/password-reset-form.tsx"), "utf8") +
  readFileSync(join(root, "app/recuperar-senha/page.tsx"), "utf8") +
  readFileSync(join(root, "app/redefinir-senha/page.tsx"), "utf8");
for (const marker of [
  "/api/auth/password-reset/request",
  "/api/auth/password-reset/confirm",
  "new-password",
  "aria-live=\"polite\"",
  "Mostrar senha"
]) {
  if (!passwordResetExperience.includes(marker)) {
    throw new Error(`Password reset UX must include ${marker}`);
  }
}
if (passwordResetExperience.includes("12 caracteres") !== true) {
  throw new Error("Password reset must enforce minimum length validation");
}

const mfaExperience =
  readFileSync(join(root, "components/mfa-challenge-form.tsx"), "utf8") +
  readFileSync(join(root, "components/mfa-settings.tsx"), "utf8") +
  readFileSync(join(root, "app/mfa/page.tsx"), "utf8") +
  settings;
for (const marker of [
  "/api/auth/mfa/challenge",
  "/api/auth/mfa/status",
  "/api/auth/mfa/enroll",
  "/api/auth/mfa/confirm",
  "/api/auth/mfa",
  "/api/auth/mfa/recovery-codes",
  "MfaSettings",
  "MfaChallengeForm",
  "QRCode",
  "otpauth_uri",
  "recovery_codes",
  "Códigos de Recuperação",
  "Baixar códigos",
  "Entendi",
  "Desativar MFA",
  "Ativar Proteção MFA",
  "aria-live=\"polite\"",
  "role=\"alert\"",
  "6 dígitos",
  "inputMode=\"numeric\""
]) {
  if (!mfaExperience.includes(marker)) {
    throw new Error(`MFA UX must include ${marker}`);
  }
}

const themeExperience =
  readFileSync(join(root, "lib/theme.ts"), "utf8") +
  readFileSync(join(root, "components/theme-provider.tsx"), "utf8") +
  readFileSync(join(root, "components/theme-toggle.tsx"), "utf8") +
  readFileSync(join(root, "components/theme-settings.tsx"), "utf8") +
  readFileSync(join(root, "components/session-profile.tsx"), "utf8") +
  layout +
  settings +
  styles;
for (const marker of [
  "ThemeSettings",
  "ThemeToggle",
  "ThemeProvider",
  "resolvedTheme",
  "theme_preference",
  "data-theme",
  "nexo-theme",
  "prefers-color-scheme",
  "Sistema",
  "Claro",
  "Escuro",
  'aria-pressed',
  'aria-live="polite"'
]) {
  if (!themeExperience.includes(marker)) {
    throw new Error(`Persistent theme experience must include ${marker}`);
  }
}

const profile =
  settings +
  readFileSync(join(root, "components/profile-settings.tsx"), "utf8") +
  readFileSync(join(root, "components/session-profile.tsx"), "utf8") +
  readFileSync(join(root, "app/api/auth/profile/route.ts"), "utf8");
for (const marker of [
  "ProfileSettings",
  "Telefone",
  "Foto de perfil",
  'accept="image/png,image/jpeg,image/webp"',
  "canvas.toDataURL",
  "/api/auth/profile",
  "validateRequestOrigin",
  "nexo:profile-updated",
  "avatar_data_url"
]) {
  if (!profile.includes(marker)) {
    throw new Error(`Editable profile must include ${marker}`);
  }
}

const sentryExperience =
  readFileSync(join(root, "instrumentation.ts"), "utf8") +
  readFileSync(join(root, "instrumentation-client.ts"), "utf8") +
  readFileSync(join(root, "sentry.server.config.ts"), "utf8") +
  readFileSync(join(root, "sentry.edge.config.ts"), "utf8") +
  readFileSync(join(root, "app/global-error.tsx"), "utf8") +
  readFileSync(join(root, "lib/sentry-scrub.ts"), "utf8") +
  readFileSync(join(root, "next.config.ts"), "utf8");
for (const marker of [
  "sendDefaultPii: false",
  "beforeSend",
  "scrubEvent",
  "NEXT_RUNTIME",
  "SENTRY_DSN",
  "NEXT_PUBLIC_SENTRY_DSN",
  "onRouterTransitionStart",
  "onRequestError",
  "removeDebugLogging",
  "GlobalError",
  "reset()",
  "withSentryConfig"
]) {
  if (!sentryExperience.includes(marker)) {
    throw new Error(`Sentry integration must include ${marker}`);
  }
}

const runtimeConfig = readFileSync(join(root, "lib/runtime-config.ts"), "utf8");
for (const marker of [
  "validateWebRuntime",
  "API_URL",
  "https:",
  "localhost",
  "new URL"
]) {
  if (!runtimeConfig.includes(marker)) {
    throw new Error(`Runtime config must include ${marker}`);
  }
}

console.log("frontend smoke checks passed");
