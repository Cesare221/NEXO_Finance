"use client";

import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronRight,
  CircleDollarSign,
  CreditCard,
  Plus,
  ReceiptText,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  WalletCards
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CashFlowChart } from "@/components/ui/cash-flow-chart";
import { MovementReviewInbox } from "@/components/movement-review-inbox";
import { DemoDatasetControl } from "@/components/demo-dataset-control";
import {
  DateRangePicker,
  defaultDashboardPeriod,
  type DateRange
} from "@/components/date-range-picker";
import type { DashboardData, DashboardTransaction } from "@/lib/financial-types";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const monthFormatter = new Intl.DateTimeFormat("pt-BR", { month: "short", timeZone: "UTC" });
const dateFormatter = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", timeZone: "UTC" });
const periodFormatter = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric", timeZone: "UTC" });

function money(value: string | number) {
  return currency.format(Number(value));
}

function monthLabel(value: string) {
  const [year, month] = value.split("-").map(Number);
  const label = monthFormatter.format(new Date(Date.UTC(year, month - 1, 1))).replace(".", "");
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function transactionIcon(transaction: DashboardTransaction) {
  if (transaction.type === "income") return CircleDollarSign;
  if (transaction.type === "card_purchase") return CreditCard;
  return ReceiptText;
}

function initialPeriod(): DateRange {
  const fallback = defaultDashboardPeriod();
  if (typeof window === "undefined") return fallback;
  const params = new URLSearchParams(window.location.search);
  const start = params.get("inicio");
  const end = params.get("fim");
  return /^\d{4}-\d{2}-\d{2}$/.test(start ?? "") && /^\d{4}-\d{2}-\d{2}$/.test(end ?? "")
    ? { start: start!, end: end! }
    : fallback;
}

function periodQuery(period: DateRange) {
  const start = new Date(`${period.start}T00:00:00Z`);
  const end = new Date(`${period.end}T00:00:00Z`);
  const months = Math.min(24, Math.max(1,
    (end.getUTCFullYear() - start.getUTCFullYear()) * 12
      + end.getUTCMonth() - start.getUTCMonth() + 1
  ));
  const query = new URLSearchParams({
    months: String(months),
    start_date: period.start,
    end_date: period.end
  });
  return query.toString();
}

function periodSummary(period: DateRange) {
  const start = periodFormatter.format(new Date(`${period.start}T00:00:00Z`)).replace(".", "");
  const end = periodFormatter.format(new Date(`${period.end}T00:00:00Z`)).replace(".", "");
  return start === end ? start : `${start} a ${end}`;
}

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [period, setPeriod] = useState<DateRange>(initialPeriod);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`/api/financial/dashboard?${periodQuery(period)}`, { cache: "no-store" });
      const body = (await response.json().catch(() => ({}))) as DashboardData & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Não foi possível carregar o dashboard.");
      setData(body);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível carregar o dashboard.");
    } finally {
      setLoading(false);
    }
  }, [period]);

  const changePeriod = useCallback((nextPeriod: DateRange) => {
    setPeriod(nextPeriod);
    const url = new URL(window.location.href);
    url.searchParams.set("inicio", nextPeriod.start);
    url.searchParams.set("fim", nextPeriod.end);
    window.history.replaceState({}, "", url);
  }, []);

  useEffect(() => {
    void loadDashboard();
    const refresh = () => void loadDashboard();
    window.addEventListener("nexo:financial-data-changed", refresh);
    return () => window.removeEventListener("nexo:financial-data-changed", refresh);
  }, [loadDashboard]);

  const chartData = useMemo(
    () => data?.cash_flow.map((point) => ({
      month: monthLabel(point.month),
      income: Number(point.income),
      expense: Number(point.expense)
    })) ?? [],
    [data]
  );

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <section className="card dashboard-state" role="alert" aria-live="polite">
        <RefreshCw size={24} aria-hidden="true" />
        <h1>Não foi possível atualizar sua visão financeira</h1>
        <p>{error}</p>
        <button className="button" type="button" onClick={() => void loadDashboard()}>
          <RefreshCw size={18} aria-hidden="true" /> Tentar novamente
        </button>
      </section>
    );
  }

  const income = Number(data.period_income);
  const expenses = Number(data.period_expenses);
  const result = income - expenses;
  const expenseRatio = income > 0 ? Math.round((expenses / income) * 100) : 0;
  const metrics = [
    { label: "Saldo total", value: money(data.total_balance), detail: `${data.accounts.length} conta${data.accounts.length === 1 ? "" : "s"}`, tone: "teal", icon: WalletCards },
    { label: "Receitas", value: money(data.period_income), detail: "no período selecionado", tone: "mint", icon: TrendingUp },
    { label: "Despesas", value: money(data.period_expenses), detail: income > 0 ? `${expenseRatio}% da receita` : "sem receitas no período", tone: "peach", icon: TrendingDown },
    { label: "Faturas", value: money(data.open_statement_total), detail: `${data.open_statements.length} em aberto`, tone: "lavender", icon: CreditCard }
  ];

  return (
    <>
      <p className="sr-only" aria-live="polite">Dashboard atualizado com os dados financeiros mais recentes.</p>
      <header className="page-header dashboard-header">
        <div>
          <span className="eyebrow">Visão geral</span>
          <h1>Seu dinheiro, sem ruído.</h1>
          <p>{data.accounts.length ? "Dados atualizados com suas movimentações." : "Comece criando sua primeira conta."}</p>
        </div>
        <div className="header-actions">
          <DateRangePicker value={period} onChange={changePeriod} disabled={loading} />
          <Link className="button" href="/transacoes"><Plus size={18} aria-hidden="true" />Nova transação</Link>
        </div>
      </header>

      <MovementReviewInbox />

      {!data.accounts.length ? (
        <section className="card dashboard-state dashboard-empty">
          <WalletCards size={28} aria-hidden="true" />
          <h2>Seu dashboard está pronto para receber dados</h2>
          <p>Cadastre uma conta para acompanhar saldos, receitas, despesas e vencimentos reais.</p>
          <div className="dashboard-empty-actions">
            <Link className="button" href="/onboarding"><Plus size={18} aria-hidden="true" />Configurar primeira conta</Link>
            <DemoDatasetControl variant="install" />
          </div>
        </section>
      ) : null}

      <section className="metric-grid" aria-label="Resumo financeiro">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article className={`card metric-card tone-${metric.tone}`} key={metric.label}>
              <div className="metric-topline"><span className="metric-icon"><Icon size={20} aria-hidden="true" /></span><span className="metric-label">{metric.label}</span></div>
              <div className="metric-value">{metric.value}</div>
              <div className="metric-detail">{metric.detail}</div>
            </article>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <article className="card cashflow-card">
          <div className="section-heading"><div><span className="eyebrow">{periodSummary(period)}</span><h2>Fluxo de caixa</h2></div></div>
          <CashFlowChart data={chartData} />
        </article>
        <article className="card insight-card">
          <div className="insight-icon"><Sparkles size={22} aria-hidden="true" /></div>
          <span className="eyebrow">Leitura do Fin</span>
          <h2>{income === 0 && expenses === 0 ? "Ainda não há movimentações neste período." : result >= 0 ? `Seu resultado está positivo em ${money(result)}.` : `Suas despesas superaram as receitas em ${money(Math.abs(result))}.`}</h2>
          <p>{income > 0 ? `As despesas representam ${expenseRatio}% das receitas do período.` : "Adicione receitas e despesas para receber uma leitura contextual."}</p>
          <button type="button" className="text-action" onClick={() => window.dispatchEvent(new Event("nexo:open-fin"))}>Conversar com o Fin <ChevronRight size={17} aria-hidden="true" /></button>
        </article>
      </section>

      <section className="dashboard-grid lower-grid">
        <article className="card list-card">
          <div className="section-heading"><div><span className="eyebrow">Atividade real</span><h2>Movimentações recentes</h2></div><Link className="text-action quiet" href="/transacoes">Ver todas <ChevronRight size={16} aria-hidden="true" /></Link></div>
          <div className="transaction-list">
            {data.recent_transactions.length ? data.recent_transactions.slice(0, 5).map((transaction) => {
              const Icon = transactionIcon(transaction);
              const positive = transaction.type === "income";
              return (
                <div className="transaction-row" key={transaction.id}>
                  <span className={`transaction-icon ${positive ? "income" : "expense"}`}><Icon size={20} aria-hidden="true" /></span>
                  <span className="transaction-copy"><strong>{transaction.description || "Movimentação"}</strong><span>{dateFormatter.format(new Date(`${transaction.occurred_on}T00:00:00Z`))}</span></span>
                  <span className={`transaction-amount ${positive ? "positive" : ""}`}>{positive ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}{money(transaction.amount)}</span>
                </div>
              );
            }) : <p className="hub-empty">Nenhuma movimentação registrada.</p>}
          </div>
        </article>

        <article className="card due-card">
          <div className="section-heading"><div><span className="eyebrow">Compromissos</span><h2>Próximos vencimentos</h2></div></div>
          {data.upcoming_due.length ? data.upcoming_due.slice(0, 3).map((statement) => {
            const due = new Date(`${statement.due_on}T00:00:00Z`);
            return (
              <div className="due-item" key={statement.id}>
                <div className="date-tile"><strong>{String(due.getUTCDate()).padStart(2, "0")}</strong><span>{monthLabel(statement.due_on.slice(0, 7)).toUpperCase()}</span></div>
                <div className="due-copy"><strong>Fatura #{statement.id}</strong><span>Cartão #{statement.credit_card_id}</span></div>
                <strong className="due-amount">{money(Number(statement.total_amount) - Number(statement.paid_amount))}</strong>
              </div>
            );
          }) : <p className="hub-empty">Nenhum vencimento pendente.</p>}
          <div className="due-summary"><span>Saldo após faturas</span><strong>{money(Number(data.total_balance) - Number(data.open_statement_total))}</strong></div>
        </article>
      </section>
    </>
  );
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton" aria-busy="true" aria-label="Carregando dashboard">
      <p className="sr-only" aria-live="polite">Carregando dashboard.</p>
      <div className="skeleton skeleton-title" />
      <div className="metric-grid">{Array.from({ length: 4 }, (_, index) => <div className="card skeleton skeleton-metric" key={index} />)}</div>
      <div className="dashboard-grid"><div className="card skeleton skeleton-chart" /><div className="card skeleton skeleton-chart" /></div>
    </div>
  );
}
