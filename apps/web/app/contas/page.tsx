import { AppShell } from "@/components/app-shell";
import { AccountManager } from "@/components/account-manager";

export default function ContasPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="section-kicker">Saldos</span>
          <h1>Contas</h1>
          <p>Gerencie bancos, carteiras e investimentos.</p>
        </div>
      </header>
      <AccountManager />
    </AppShell>
  );
}
