"use client";

import {
  Archive,
  CalendarDays,
  CheckCircle2,
  CreditCard,
  LoaderCircle,
  Pencil,
  Plus,
  ReceiptText,
  X
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { CreditCardForm } from "@/components/credit-card-form";
import type {
  DashboardData,
  FinancialAccount,
  FinancialCategory,
  FinancialCreditCard
} from "@/lib/financial-types";

type CategoryOption = { id: number; label: string };

function flattenCategories(categories: FinancialCategory[], depth = 0): CategoryOption[] {
  return categories.flatMap((category) => [
    { id: category.id, label: `${"— ".repeat(depth)}${category.name}` },
    ...flattenCategories(category.children ?? [], depth + 1)
  ]);
}

function localDateValue() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(value));
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short", timeZone: "UTC" })
    .format(new Date(`${value}T00:00:00Z`));
}

function parseAmount(value: string) {
  const normalized = value.trim().replace(/\./g, "").replace(",", ".");
  const amount = Number(normalized);
  return Number.isFinite(amount) ? amount : 0;
}

async function readError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: string } | null;
  return data?.detail ?? "Não foi possível concluir a operação.";
}

export function CardManager() {
  const [cards, setCards] = useState<FinancialCreditCard[]>([]);
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [mode, setMode] = useState<"card" | "purchase" | null>(null);
  const [editingCard, setEditingCard] = useState<FinancialCreditCard | null>(null);
  const [selectedCardId, setSelectedCardId] = useState("");
  const [purchaseAmount, setPurchaseAmount] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [occurredOn, setOccurredOn] = useState(localDateValue);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [archivingId, setArchivingId] = useState<number | null>(null);
  const [payingStatementId, setPayingStatementId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const categoryOptions = useMemo(() => flattenCategories(categories), [categories]);
  const accountNames = useMemo(() => new Map(accounts.map((account) => [account.id, account.name])), [accounts]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [cardsResponse, accountsResponse, categoriesResponse, dashboardResponse] = await Promise.all([
        fetch("/api/financial/credit-cards"),
        fetch("/api/financial/accounts"),
        fetch("/api/financial/categories"),
        fetch("/api/financial/dashboard")
      ]);
      const failed = [cardsResponse, accountsResponse, categoriesResponse, dashboardResponse]
        .find((response) => !response.ok);
      if (failed) throw new Error(await readError(failed));
      const [cardData, accountData, categoryData, dashboardData] = await Promise.all([
        cardsResponse.json() as Promise<FinancialCreditCard[]>,
        accountsResponse.json() as Promise<FinancialAccount[]>,
        categoriesResponse.json() as Promise<FinancialCategory[]>,
        dashboardResponse.json() as Promise<DashboardData>
      ]);
      const activeCards = cardData.filter((card) => !card.is_archived);
      const activeAccounts = accountData.filter((account) => !account.is_archived);
      setCards(activeCards);
      setAccounts(activeAccounts);
      setCategories(categoryData);
      setDashboard(dashboardData);
      setSelectedCardId((current) => current || String(activeCards[0]?.id ?? ""));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Não foi possível carregar os cartões.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  function closeForm() {
    setMode(null);
    setEditingCard(null);
    setDescription("");
    setPurchaseAmount("");
    setCategoryId("");
  }

  function startEdit(card: FinancialCreditCard) {
    setEditingCard(card);
    setError("");
    setSuccess("");
    setMode("card");
  }

  function startCreateCard() {
    setEditingCard(null);
    setError("");
    setSuccess("");
    setMode("card");
  }

  async function createPurchase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    setError("");
    setSuccess("");
    if (!selectedCardId || parseAmount(purchaseAmount) <= 0 || description.trim().length < 2) {
      setError("Selecione o cartão, informe o valor e descreva a compra.");
      return;
    }
    setSaving(true);
    try {
      const response = await fetch(`/api/financial/credit-cards/${selectedCardId}/purchases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount: parseAmount(purchaseAmount).toFixed(2),
          description: description.trim(),
          category_id: categoryId ? Number(categoryId) : null,
          occurred_on: occurredOn
        })
      });
      if (!response.ok) throw new Error(await readError(response));
      closeForm();
      setSuccess("Compra registrada na fatura.");
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
      await loadData();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível registrar a compra.");
    } finally {
      setSaving(false);
    }
  }

  async function archiveCard(card: FinancialCreditCard) {
    if (archivingId !== null) return;
    if (!window.confirm(`Arquivar ${card.name}? Compras futuras serão bloqueadas, mas o histórico e as faturas serão preservados.`)) return;
    setArchivingId(card.id);
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/financial/credit-cards/${card.id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(await readError(response));
      setSuccess("Cartão arquivado com o histórico preservado.");
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
      await loadData();
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : "Não foi possível arquivar o cartão.");
    } finally {
      setArchivingId(null);
    }
  }

  async function payStatement(statementId: number, cardName: string) {
    if (payingStatementId !== null) return;
    if (!window.confirm(`Confirmar o pagamento da fatura de ${cardName}? O valor será descontado da conta vinculada.`)) return;
    setPayingStatementId(statementId);
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/financial/statements/${statementId}/pay`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paid_on: localDateValue() })
      });
      if (!response.ok) throw new Error(await readError(response));
      setSuccess("Fatura paga e saldo da conta atualizado.");
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
      await loadData();
    } catch (paymentError) {
      setError(paymentError instanceof Error ? paymentError.message : "Não foi possível pagar a fatura.");
    } finally {
      setPayingStatementId(null);
    }
  }

  return (
    <div className="resource-layout" aria-busy={saving || archivingId !== null || payingStatementId !== null}>
      <section className="resource-summary card-summary-actions" aria-label="Ações de cartões">
        <div><span>Cartões ativos</span><strong>{cards.length}</strong></div>
        <div><span>Faturas abertas</span><strong>{dashboard?.open_statements.length ?? 0}</strong></div>
        <div className="header-actions">
          <button className="button secondary" type="button" disabled={cards.length === 0} onClick={() => setMode("purchase")}>
            <ReceiptText size={18} aria-hidden="true" />Registrar compra
          </button>
          <button className="button" type="button" onClick={startCreateCard}>
            <Plus size={18} aria-hidden="true" />Novo cartão
          </button>
        </div>
      </section>

      {mode === "card" && (
        <CreditCardForm
          key={editingCard?.id ?? "new"}
          accounts={accounts}
          card={editingCard ?? undefined}
          onCancel={closeForm}
          onSaved={async () => {
            const wasEditing = Boolean(editingCard);
            closeForm();
            setSuccess(wasEditing ? "Cartão atualizado." : "Cartão adicionado ao Nexo.");
            window.dispatchEvent(new Event("nexo:financial-data-changed"));
            await loadData();
          }}
        />
      )}

      {mode === "purchase" && (
        <form className="card form resource-form" onSubmit={createPurchase}>
          <div className="resource-heading">
            <div><span className="section-kicker">Fatura</span><h2>Registrar compra</h2></div>
            <button className="icon-button" type="button" aria-label="Fechar formulário" onClick={closeForm}><X size={19} aria-hidden="true" /></button>
          </div>
          <div className="resource-form-grid">
            <div className="field"><label htmlFor="purchase-card">Cartão</label><select className="input" id="purchase-card" value={selectedCardId} onChange={(event) => setSelectedCardId(event.target.value)} required>{cards.map((card) => <option key={card.id} value={card.id}>{card.name}</option>)}</select></div>
            <div className="field"><label htmlFor="purchase-amount">Valor</label><input className="input" id="purchase-amount" inputMode="decimal" value={purchaseAmount} onChange={(event) => setPurchaseAmount(event.target.value)} placeholder="0,00" required /></div>
            <div className="field"><label htmlFor="purchase-description">Descrição da compra</label><input className="input" id="purchase-description" value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} required /></div>
            <div className="field"><label htmlFor="purchase-category">Categoria</label><select className="input" id="purchase-category" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">Sem categoria</option>{categoryOptions.map((category) => <option key={category.id} value={category.id}>{category.label}</option>)}</select></div>
            <div className="field"><label htmlFor="purchase-date">Data</label><input className="input" id="purchase-date" type="date" value={occurredOn} onChange={(event) => setOccurredOn(event.target.value)} required /></div>
          </div>
          <div className="resource-form-actions"><button className="button secondary" type="button" onClick={closeForm}>Cancelar</button><button className="button" type="submit" disabled={saving}>{saving ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <ReceiptText size={18} aria-hidden="true" />}{saving ? "Registrando" : "Registrar compra"}</button></div>
        </form>
      )}

      <div className="resource-feedback" aria-live="polite">{error && <p className="error">{error}</p>}{success && <p className="success-message"><CheckCircle2 size={17} aria-hidden="true" />{success}</p>}</div>

      {loading ? (
        <section className="card resource-state"><LoaderCircle className="spin" aria-hidden="true" /><p>Carregando cartões...</p></section>
      ) : cards.length === 0 ? (
        <section className="card resource-state"><CreditCard aria-hidden="true" /><h2>Nenhum cartão cadastrado</h2><p>Adicione um cartão para acompanhar limite e fatura sem duplicar as despesas.</p><button className="button" type="button" onClick={startCreateCard}>Adicionar cartão</button></section>
      ) : (
        <section className="card-grid" aria-label="Cartões ativos">
          {cards.map((card) => {
            const statement = dashboard?.open_statements.find((item) => item.credit_card_id === card.id);
            const usage = Math.min(100, Math.max(0, Number(card.used_limit) / Number(card.limit_amount) * 100));
            return (
              <article className="card payment-card" key={card.id}>
                <div className="payment-card-heading">
                  <span className="resource-icon"><CreditCard aria-hidden="true" /></span>
                  <div><strong>{card.name}</strong><span>{accountNames.get(card.payment_account_id) ?? "Conta de pagamento"}</span></div>
                  <div className="resource-actions payment-card-actions">
                    <button className="icon-button" type="button" aria-label={`Editar cartão ${card.name}`} onClick={() => startEdit(card)}><Pencil size={17} aria-hidden="true" /></button>
                    <button className="icon-button" type="button" aria-label={`Arquivar cartão ${card.name}`} disabled={archivingId === card.id} onClick={() => void archiveCard(card)}>{archivingId === card.id ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <Archive size={17} aria-hidden="true" />}</button>
                  </div>
                </div>
                <div className="payment-card-limit"><span>Limite disponível</span><strong>{formatCurrency(card.available_limit)}</strong><div className="limit-track" aria-label={`${usage.toFixed(0)}% do limite utilizado`}><span style={{ width: `${usage}%` }} /></div><small>{formatCurrency(card.used_limit)} usados de {formatCurrency(card.limit_amount)}</small></div>
                <div className="payment-card-statement">
                  <div><span>Fatura aberta</span><strong>{formatCurrency(statement ? Number(statement.total_amount) - Number(statement.paid_amount) : 0)}</strong></div>
                  <div><CalendarDays size={17} aria-hidden="true" /><span>{statement ? `Vence ${formatDate(statement.due_on)}` : `Vence dia ${card.due_day}`}</span></div>
                  {statement && <button className="button secondary statement-pay-button" type="button" disabled={payingStatementId === statement.id} onClick={() => void payStatement(statement.id, card.name)}>{payingStatementId === statement.id ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <CheckCircle2 size={17} aria-hidden="true" />}Pagar fatura</button>}
                </div>
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
}
