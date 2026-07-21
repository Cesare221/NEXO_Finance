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
  "app/manifest.ts",
  "app/offline/page.tsx",
  "components/app-shell.tsx",
  "components/auth-form.tsx",
  "components/session-profile.tsx",
  "components/theme-provider.tsx",
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
  "public/brand/fin-mascot.webp",
  "public/brand/fin-avatar.webp"
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
  readFileSync(join(root, "components/dashboard-view.tsx"), "utf8");
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
for (const marker of ["usePathname", "Menu principal", "NavigationDrawer", "FinChatPanel", "PendingProposalsProvider", "SessionProfile"]) {
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
  "/brand/fin-mascot.webp",
  "/brand/fin-avatar.webp",
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
  "validateRequestOrigin",
  "nexo:financial-data-changed"
]) {
  if (!categories.includes(marker)) {
    throw new Error(`Functional categories manager must include ${marker}`);
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
  "<dialog"
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
for (const fakeValue of ["R$ 3.851,10", "R$ 1.148,90", "20/07/2026"]) {
  if (cards.includes(fakeValue)) {
    throw new Error(`Cards page must not ship demo value ${fakeValue}`);
  }
}

const authCookies = readFileSync(join(root, "lib/auth-cookies.ts"), "utf8");
for (const marker of [
  "fin_access_token",
  "fin_refresh_token",
  "httpOnly: true",
  'sameSite: "lax"',
  "secure: process.env.NODE_ENV === \"production\""
]) {
  if (!authCookies.includes(marker)) {
    throw new Error(`Auth cookies must include ${marker}`);
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
for (const marker of ["protectedRoutes", "fin_access_token", "fin_refresh_token", "/login"]) {
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
  "env(safe-area-inset-bottom)",
  "prefers-reduced-motion",
  "@media (max-width: 767px)"
]) {
  if (!styles.includes(marker)) {
    throw new Error(`Global styles must include ${marker}`);
  }
}

const serviceWorker = readFileSync(join(root, "public/sw.js"), "utf8");
for (const marker of ["install", "activate", "fetch", "/offline"]) {
  if (!serviceWorker.includes(marker)) {
    throw new Error(`Service worker must include ${marker}`);
  }
}

const settings = readFileSync(join(root, "app/configuracoes/page.tsx"), "utf8");
if (!settings.includes("InstallAppButton")) {
  throw new Error("Settings must expose the PWA installation action");
}

const themeExperience =
  readFileSync(join(root, "lib/theme.ts"), "utf8") +
  readFileSync(join(root, "components/theme-provider.tsx"), "utf8") +
  readFileSync(join(root, "components/theme-settings.tsx"), "utf8") +
  readFileSync(join(root, "components/session-profile.tsx"), "utf8") +
  layout +
  settings +
  styles;
for (const marker of [
  "ThemeSettings",
  "ThemeProvider",
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

console.log("frontend smoke checks passed");
