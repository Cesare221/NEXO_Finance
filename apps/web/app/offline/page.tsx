import Link from "next/link";
import { WifiOff } from "lucide-react";

export default function OfflinePage() {
  return (
    <main className="auth-page">
      <section className="card auth-panel offline-panel">
        <div className="offline-icon"><WifiOff size={26} aria-hidden="true" /></div>
        <h1>Você está sem conexão</h1>
        <p>O Nexo continua instalado. Reconecte-se para atualizar saldos e movimentações.</p>
        <Link className="button" href="/dashboard" style={{ marginTop: 20 }}>
          Tentar novamente
        </Link>
      </section>
    </main>
  );
}
