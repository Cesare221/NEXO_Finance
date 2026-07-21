import { AppShell } from "@/components/app-shell";
import { CardManager } from "@/components/card-manager";

export default function CartoesPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="section-kicker">Crédito sob controle</span>
          <h1>Cartões</h1>
          <p>Acompanhe limite, faturas e compras ligadas à conta que fará o pagamento.</p>
        </div>
      </header>
      <CardManager />
    </AppShell>
  );
}
