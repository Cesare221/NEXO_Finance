"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  ArrowDownRight,
  ArrowRightLeft,
  ArrowUpRight,
  Bot,
  ChevronRight,
  CreditCard,
  FolderTree,
  History,
  Landmark,
  Search,
  WalletCards
} from "lucide-react";

const quickActions = [
  { href: "/transacoes", title: "Lançar", description: "Receita ou despesa", icon: ArrowRightLeft },
  { href: "/contas", title: "Contas", description: "Saldos e carteiras", icon: Landmark },
  { href: "/cartoes", title: "Cartões", description: "Faturas e limites", icon: CreditCard },
  { href: "/fin", title: "Perguntar", description: "Conversar com o Fin", icon: Bot }
];

const activities = [
  { title: "Salário", detail: "Hoje · Conta principal", amount: 8200, type: "income" },
  { title: "Mercado", detail: "Ontem · Alimentação", amount: -420.3, type: "expense" },
  { title: "Streaming", detail: "14 jul · Assinaturas", amount: -55.9, type: "expense" }
];

const services = [
  { href: "/categorias", title: "Organizar categorias", description: "Revise onde seu dinheiro está indo", icon: FolderTree },
  { href: "/contas", title: "Planejar sua reserva", description: "Separe saldo para emergências", icon: WalletCards }
];

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function FinancialDashboard() {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
  const filteredActivities = useMemo(
    () => activities.filter((activity) => activity.title.toLocaleLowerCase("pt-BR").includes(normalizedQuery)),
    [normalizedQuery]
  );

  return (
    <section className="card financial-hub" aria-labelledby="financial-hub-title">
      <div className="section-heading financial-hub-heading">
        <div>
          <span className="eyebrow">Atalhos e contexto</span>
          <h2 id="financial-hub-title">Central financeira</h2>
        </div>
      </div>

      <label className="financial-search">
        <Search size={19} aria-hidden="true" />
        <span className="sr-only">Buscar na atividade recente</span>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar movimentações recentes"
        />
      </label>

      <h3 className="hub-subtitle">Ações rápidas</h3>
      <div className="quick-actions">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <Link href={action.href} key={action.href}>
              <span className="quick-action-icon"><Icon size={21} aria-hidden="true" /></span>
              <strong>{action.title}</strong>
              <span>{action.description}</span>
            </Link>
          );
        })}
      </div>

      <div className="hub-columns">
        <div>
          <h3 className="hub-subtitle"><History size={18} aria-hidden="true" />Atividade recente</h3>
          <div className="hub-activity-list" aria-live="polite">
            {filteredActivities.length > 0 ? filteredActivities.map((activity) => (
              <div className="hub-activity" key={activity.title}>
                <span className={`transaction-icon ${activity.type}`}>
                  {activity.amount > 0
                    ? <ArrowUpRight size={18} aria-hidden="true" />
                    : <ArrowDownRight size={18} aria-hidden="true" />}
                </span>
                <span><strong>{activity.title}</strong><small>{activity.detail}</small></span>
                <strong className={activity.amount > 0 ? "positive" : ""}>
                  {activity.amount > 0 ? "+" : ""}{currency.format(activity.amount)}
                </strong>
              </div>
            )) : <p className="hub-empty">Nenhuma movimentação encontrada.</p>}
          </div>
        </div>
        <div>
          <h3 className="hub-subtitle">Próximos passos</h3>
          <div className="service-list">
            {services.map((service) => {
              const Icon = service.icon;
              return (
                <Link href={service.href} key={service.href}>
                  <span className="service-icon"><Icon size={20} aria-hidden="true" /></span>
                  <span><strong>{service.title}</strong><small>{service.description}</small></span>
                  <ChevronRight size={18} aria-hidden="true" />
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
