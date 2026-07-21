import { AppShell } from "@/components/app-shell";
import { AccountManager } from "@/components/account-manager";

export default function ContasPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="section-kicker">Seu dinheiro</span>
          <h1>Contas</h1>
          <p>Centralize bancos, carteiras e investimentos com saldos calculados pelas movimentações.</p>
        </div>
      </header>
      <AccountManager />
    </AppShell>
  );
}
