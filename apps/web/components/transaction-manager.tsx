"use client";

import {
  ArrowDownLeft,
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  LoaderCircle,
  ReceiptText,
  Tag,
  Trash2,
  WalletCards
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import type {
  FinancialAccount,
  FinancialCategory,
  FinancialTransaction
} from "@/lib/financial-types";

type TransactionType = "expense" | "income";
type CategoryOption = { id: number; label: string };

function localDateValue() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function flattenCategories(categories: FinancialCategory[], depth = 0): CategoryOption[] {
  return categories.flatMap((category) => [
    { id: category.id, label: `${"— ".repeat(depth)}${category.name}` },
    ...flattenCategories(category.children ?? [], depth + 1)
  ]);
}

function parseAmount(value: string) {
  const clean = value.replace(/\s/g, "").replace(/^R\$/i, "");
  const normalized = clean.includes(",")
    ? clean.replace(/\./g, "").replace(",", ".")
    : clean;
  const amount = Number(normalized);
  return Number.isFinite(amount) ? amount : 0;
}

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number(value));
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC"
  }).format(new Date(`${value}T00:00:00Z`));
}

async function readError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: string } | null;
  return data?.detail ?? "Não foi possível concluir a operação.";
}

export function TransactionManager() {
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [categories, setCategories] = useState<FinancialCategory[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [type, setType] = useState<TransactionType>("expense");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [occurredOn, setOccurredOn] = useState(localDateValue);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const categoryOptions = useMemo(() => flattenCategories(categories), [categories]);
  const accountNames = useMemo(
    () => new Map(accounts.map((account) => [account.id, account.name])),
    [accounts]
  );
  const categoryNames = useMemo(
    () => new Map(categoryOptions.map((category) => [category.id, category.label.replace(/^(— )+/, "")])),
    [categoryOptions]
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setLoading(true);
      setError("");
      try {
        const [accountsResponse, categoriesResponse, transactionsResponse] = await Promise.all([
          fetch("/api/financial/accounts", { signal: controller.signal }),
          fetch("/api/financial/categories", { signal: controller.signal }),
          fetch("/api/financial/transactions", { signal: controller.signal })
        ]);
        const failedResponse = [accountsResponse, categoriesResponse, transactionsResponse]
          .find((response) => !response.ok);
        if (failedResponse) throw new Error(await readError(failedResponse));

        const [accountData, categoryData, transactionData] = await Promise.all([
          accountsResponse.json() as Promise<FinancialAccount[]>,
          categoriesResponse.json() as Promise<FinancialCategory[]>,
          transactionsResponse.json() as Promise<FinancialTransaction[]>
        ]);
        const activeAccounts = accountData.filter((account) => !account.is_archived);
        setAccounts(activeAccounts);
        setCategories(categoryData);
        setTransactions(transactionData);
        setAccountId((current) => current || String(activeAccounts[0]?.id ?? ""));
      } catch (loadError) {
        if ((loadError as Error).name !== "AbortError") {
          setError(loadError instanceof Error ? loadError.message : "Não foi possível carregar as transações.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadData();
    return () => controller.abort();
  }, []);

  async function submitTransaction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    setError("");
    setSuccess("");

    const numericAmount = parseAmount(amount);
    const cleanDescription = description.trim();
    if (!accountId) {
      setError("Selecione a conta usada na movimentação.");
      return;
    }
    if (numericAmount <= 0) {
      setError("Informe um valor maior que zero.");
      return;
    }
    if (cleanDescription.length < 2) {
      setError("Descreva o que foi gasto ou recebido.");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("/api/financial/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type,
          account_id: Number(accountId),
          category_id: categoryId ? Number(categoryId) : null,
          amount: numericAmount.toFixed(2),
          description: cleanDescription,
          occurred_on: occurredOn,
          origin: "manual"
        })
      });
      if (!response.ok) throw new Error(await readError(response));

      const created = await response.json() as FinancialTransaction;
      setTransactions((current) => [created, ...current]);
      setAmount("");
      setDescription("");
      setCategoryId("");
      setSuccess(type === "expense" ? "Despesa adicionada ao histórico." : "Receita adicionada ao histórico.");
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar a movimentação.");
    } finally {
      setSaving(false);
    }
  }

  async function deleteTransaction(transaction: FinancialTransaction) {
    if (deletingId !== null) return;
    const label = transaction.description || "esta movimentação";
    if (!window.confirm(`Excluir ${label}? Essa ação atualizará seus saldos.`)) return;

    setError("");
    setSuccess("");
    setDeletingId(transaction.id);
    try {
      const response = await fetch(`/api/financial/transactions/${transaction.id}`, {
        method: "DELETE"
      });
      if (!response.ok) throw new Error(await readError(response));
      setTransactions((current) => current.filter((item) => item.id !== transaction.id));
      setSuccess("Movimentação removida do histórico.");
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Não foi possível remover a movimentação.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="transactions-layout" aria-busy={saving || deletingId !== null}>
      <form className="card form transaction-form" onSubmit={submitTransaction}>
        <div className="transaction-section-heading">
          <div>
            <span className="section-kicker">Registro manual</span>
            <h2>Nova movimentação</h2>
          </div>
          <ReceiptText aria-hidden="true" />
        </div>

        <fieldset className="transaction-type-fieldset">
          <legend>Tipo</legend>
          <div className="transaction-type-control">
            <button className={type === "expense" ? "active" : ""} type="button" aria-pressed={type === "expense"} onClick={() => setType("expense")}>
              <ArrowUpRight aria-hidden="true" />
              Despesa
            </button>
            <button className={type === "income" ? "active" : ""} type="button" aria-pressed={type === "income"} onClick={() => setType("income")}>
              <ArrowDownLeft aria-hidden="true" />
              Receita
            </button>
          </div>
        </fieldset>

        <div className="field transaction-description-field">
          <label htmlFor="transaction-description">Descrição do {type === "expense" ? "gasto" : "recebimento"}</label>
          <div className="input-with-icon">
            <ReceiptText aria-hidden="true" />
            <input
              className="input"
              id="transaction-description"
              name="description"
              maxLength={500}
              minLength={2}
              placeholder={type === "expense" ? "Ex.: almoço no restaurante" : "Ex.: pagamento do cliente"}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              required
            />
          </div>
          <span className="field-help">Essa descrição aparecerá no histórico e nos resumos do Nexo.</span>
        </div>

        <div className="transaction-form-grid">
          <div className="field">
            <label htmlFor="transaction-amount">Valor</label>
            <div className="currency-input">
              <span>R$</span>
              <input className="input" id="transaction-amount" name="amount" inputMode="decimal" autoComplete="off" placeholder="0,00" value={amount} onChange={(event) => setAmount(event.target.value)} required />
            </div>
          </div>
          <div className="field">
            <label htmlFor="transaction-date">Data</label>
            <div className="input-with-icon">
              <CalendarDays aria-hidden="true" />
              <input className="input" id="transaction-date" name="occurred_on" type="date" value={occurredOn} onChange={(event) => setOccurredOn(event.target.value)} required />
            </div>
          </div>
          <div className="field">
            <label htmlFor="transaction-account">Conta</label>
            <div className="input-with-icon">
              <WalletCards aria-hidden="true" />
              <select className="input" id="transaction-account" name="account_id" value={accountId} onChange={(event) => setAccountId(event.target.value)} disabled={loading || accounts.length === 0} required>
                <option value="">Selecione uma conta</option>
                {accounts.map((account) => <option value={account.id} key={account.id}>{account.name}</option>)}
              </select>
            </div>
          </div>
          <div className="field">
            <label htmlFor="transaction-category">Categoria</label>
            <div className="input-with-icon">
              <Tag aria-hidden="true" />
              <select className="input" id="transaction-category" name="category_id" value={categoryId} onChange={(event) => setCategoryId(event.target.value)} disabled={loading}>
                <option value="">Sem categoria</option>
                {categoryOptions.map((category) => <option value={category.id} key={category.id}>{category.label}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="transaction-feedback" aria-live="polite">
          {accounts.length === 0 && !loading && <p className="transaction-notice" role="status">Crie uma conta antes de registrar sua primeira movimentação.</p>}
          {error && <p className="error" role="alert">{error}</p>}
          {success && <p className="transaction-success" role="status"><CheckCircle2 aria-hidden="true" />{success}</p>}
        </div>

        <button className="button transaction-submit" type="submit" disabled={saving || loading || accounts.length === 0}>
          {saving ? <LoaderCircle className="spin" aria-hidden="true" /> : <ReceiptText aria-hidden="true" />}
          {saving ? "Salvando..." : "Adicionar movimentação"}
        </button>
      </form>

      <section className="card transaction-history" aria-labelledby="transaction-history-title">
        <div className="transaction-section-heading">
          <div>
            <span className="section-kicker">Atividade</span>
            <h2 id="transaction-history-title">Histórico</h2>
          </div>
          <span className="transaction-count">{transactions.length}</span>
        </div>

        {loading ? (
          <div className="transaction-state" role="status"><LoaderCircle className="spin" aria-hidden="true" />Carregando movimentações.</div>
        ) : transactions.length === 0 ? (
          <div className="transaction-empty"><ReceiptText aria-hidden="true" /><strong>Nenhuma movimentação registrada</strong><span>Seu histórico começa com o primeiro lançamento.</span></div>
        ) : (
          <div className="transaction-list">
            {transactions.map((transaction) => {
              const income = transaction.type === "income" || transaction.type === "transfer_in";
              return (
                <article className="transaction-row" key={transaction.id}>
                  <span className={`transaction-direction ${income ? "income" : "expense"}`}>{income ? <ArrowDownLeft aria-hidden="true" /> : <ArrowUpRight aria-hidden="true" />}</span>
                  <div className="transaction-copy">
                    <strong>{transaction.description || "Sem descrição"}</strong>
                    <span>{categoryNames.get(transaction.category_id ?? -1) ?? (income ? "Receita" : "Despesa")}{" · "}{accountNames.get(transaction.account_id) ?? "Conta"}</span>
                  </div>
                  <div className={`transaction-value ${income ? "income" : "expense"}`}>
                    <strong>{income ? "+" : "-"}{formatCurrency(transaction.amount)}</strong>
                    <span>{formatDate(transaction.occurred_on)}</span>
                  </div>
                  <button
                    className="transaction-delete"
                    type="button"
                    aria-label={`Excluir ${transaction.description || "movimentação"}`}
                    title="Excluir movimentação"
                    disabled={deletingId === transaction.id}
                    onClick={() => void deleteTransaction(transaction)}
                  >
                    {deletingId === transaction.id ? <LoaderCircle className="spin" aria-hidden="true" /> : <Trash2 aria-hidden="true" />}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
