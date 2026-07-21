import Link from "next/link";
import { ArrowUpRight, Landmark, ShieldCheck, WalletCards } from "lucide-react";

type FinancialScore = {
  title: string;
  description: string;
  score: number;
  href: string;
  icon: typeof ShieldCheck;
};

const scores: FinancialScore[] = [
  {
    title: "Saúde financeira",
    description: "Equilíbrio entre entradas, saídas e saldo disponível neste mês.",
    score: 78,
    href: "/fin",
    icon: ShieldCheck
  },
  {
    title: "Reserva de emergência",
    description: "Progresso estimado para formar uma proteção de seis meses.",
    score: 46,
    href: "/contas",
    icon: Landmark
  },
  {
    title: "Organização",
    description: "Cobertura de categorias e consistência dos seus lançamentos.",
    score: 86,
    href: "/categorias",
    icon: WalletCards
  }
];

function strength(score: number) {
  if (score >= 80) return { label: "Forte", className: "strong" };
  if (score >= 50) return { label: "Bom", className: "moderate" };
  return { label: "Atenção", className: "weak" };
}

export function FinancialScoreCards() {
  return (
    <section className="score-section" aria-labelledby="score-section-title">
      <div className="section-heading score-heading">
        <div>
          <span className="eyebrow">Diagnóstico do Fin</span>
          <h2 id="score-section-title">Seus indicadores financeiros</h2>
        </div>
        <span className="score-note">Estimativas com os dados atuais</span>
      </div>
      <div className="score-grid">
        {scores.map((item) => {
          const Icon = item.icon;
          const state = strength(item.score);
          return (
            <article className="card score-card" key={item.title}>
              <div className="score-card-header">
                <span className="score-icon"><Icon size={20} aria-hidden="true" /></span>
                <span className={`score-status ${state.className}`}>{state.label}</span>
              </div>
              <div
                className="score-gauge"
                role="img"
                aria-label={`${item.title}: ${item.score} de 100, nível ${state.label}`}
              >
                <svg viewBox="0 0 180 100" aria-hidden="true">
                  <path className="score-track" pathLength="100" d="M 15 90 A 75 75 0 0 1 165 90" />
                  <path
                    className={`score-progress ${state.className}`}
                    pathLength="100"
                    strokeDasharray={`${item.score} 100`}
                    d="M 15 90 A 75 75 0 0 1 165 90"
                  />
                </svg>
                <strong>{item.score}</strong>
                <span>de 100</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <Link className="text-action" href={item.href}>
                Ver como melhorar <ArrowUpRight size={16} aria-hidden="true" />
              </Link>
            </article>
          );
        })}
      </div>
    </section>
  );
}
