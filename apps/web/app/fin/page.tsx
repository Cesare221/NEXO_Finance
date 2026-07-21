import { MessageSquareText } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { FinMascot } from "@/components/brand-assets";

export default function FinPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="eyebrow">Agente financeiro</span>
          <h1>Conversas com o Fin</h1>
          <p>Consulte seus dados e revise movimentações reconhecidas no painel ao lado.</p>
        </div>
      </header>
      <section className="card fin-page-prompt">
        <FinMascot className="fin-page-mascot" priority />
        <div><h2>O Fin está disponível neste painel</h2><p>A conversa acompanha você em todas as áreas do Nexo.</p></div>
        <MessageSquareText className="fin-page-message-icon" size={22} aria-hidden="true" />
        <span className="status ok">Painel aberto</span>
      </section>
    </AppShell>
  );
}
