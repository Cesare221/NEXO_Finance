import { MessageSquareText } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { FinMascot } from "@/components/brand-assets";

export default function FinPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="eyebrow">Agente financeiro</span>
          <h1>Fin</h1>
          <p>Consulte dados e revise lançamentos.</p>
        </div>
      </header>
      <section className="card fin-page-prompt">
        <FinMascot className="fin-page-mascot" priority />
        <div><h2>Conversa ativa</h2><p>Use o painel lateral para continuar.</p></div>
        <MessageSquareText className="fin-page-message-icon" size={22} aria-hidden="true" />
        <span className="status ok">Painel aberto</span>
      </section>
    </AppShell>
  );
}
