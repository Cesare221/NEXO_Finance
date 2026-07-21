import { AppShell } from "@/components/app-shell";
import { TransactionManager } from "@/components/transaction-manager";

export default function TransacoesPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="section-kicker">Controle financeiro</span>
          <h1>Transações</h1>
          <p>Registre o que entrou ou saiu e mantenha cada valor fácil de reconhecer.</p>
        </div>
      </header>
      <TransactionManager />
    </AppShell>
  );
}
