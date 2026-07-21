"use client";

import {
  Archive,
  Building2,
  CheckCircle2,
  LoaderCircle,
  Pencil,
  Plus,
  WalletCards,
  X
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import type { DashboardData, FinancialAccount } from "@/lib/financial-types";

const accountTypes = [
  { value: "checking", label: "Conta corrente" },
  { value: "savings", label: "Poupança" },
  { value: "wallet", label: "Carteira" },
  { value: "investment", label: "Investimentos" }
];

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number(value));
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

export function AccountManager() {
  const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
  const [balances, setBalances] = useState<Map<number, string>>(new Map());
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [type, setType] = useState("checking");
  const [initialBalance, setInitialBalance] = useState("0,00");
  const [color, setColor] = useState("#237a70");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [archivingId, setArchivingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadAccounts = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [accountsResponse, dashboardResponse] = await Promise.all([
        fetch("/api/financial/accounts"),
        fetch("/api/financial/dashboard")
      ]);
      if (!accountsResponse.ok) throw new Error(await readError(accountsResponse));
      if (!dashboardResponse.ok) throw new Error(await readError(dashboardResponse));
      const accountData = await accountsResponse.json() as FinancialAccount[];
      const dashboard = await dashboardResponse.json() as DashboardData;
      setAccounts(accountData.filter((account) => !account.is_archived));
      setBalances(new Map(dashboard.accounts.map((account) => [account.id, account.current_balance])));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Não foi possível carregar as contas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts]);

  const totalBalance = useMemo(
    () => accounts.reduce((total, account) => total + Number(balances.get(account.id) ?? account.initial_balance), 0),
    [accounts, balances]
  );

  function resetForm() {
    setEditingId(null);
    setName("");
    setType("checking");
    setInitialBalance("0,00");
    setColor("#237a70");
    setFormOpen(false);
  }

  function startEdit(account: FinancialAccount) {
    setEditingId(account.id);
    setName(account.name);
    setType(account.type);
    setInitialBalance(String(account.initial_balance).replace(".", ","));
    setColor(account.color ?? "#237a70");
    setError("");
    setSuccess("");
    setFormOpen(true);
  }

  async function submitAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (name.trim().length < 2) {
      setError("Informe um nome com pelo menos dois caracteres.");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(
        editingId ? `/api/financial/accounts/${editingId}` : "/api/financial/accounts",
        {
          method: editingId ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            type,
            initial_balance: parseAmount(initialBalance).toFixed(2),
            color,
            icon: type === "wallet" ? "wallet" : "building"
          })
        }
      );
      if (!response.ok) throw new Error(await readError(response));
      resetForm();
      setSuccess(editingId ? "Conta atualizada." : "Conta adicionada ao Nexo.");
      await loadAccounts();
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar a conta.");
    } finally {
      setSaving(false);
    }
  }

  async function archiveAccount(account: FinancialAccount) {
    if (!window.confirm(`Arquivar ${account.name}? O histórico será preservado.`)) return;
    setArchivingId(account.id);
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/financial/accounts/${account.id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(await readError(response));
      setSuccess("Conta arquivada. As movimentações continuam no histórico.");
      await loadAccounts();
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : "Não foi possível arquivar a conta.");
    } finally {
      setArchivingId(null);
    }
  }

  return (
    <div className="resource-layout">
      <section className="resource-summary" aria-label="Resumo das contas">
        <div>
          <span>Saldo consolidado</span>
          <strong>{formatCurrency(totalBalance)}</strong>
        </div>
        <div>
          <span>Contas ativas</span>
          <strong>{accounts.length}</strong>
        </div>
        <button className="button" type="button" onClick={() => setFormOpen(true)}>
          <Plus size={18} aria-hidden="true" />
          Nova conta
        </button>
      </section>

      {formOpen && (
        <form className="card form resource-form" onSubmit={submitAccount}>
          <div className="resource-heading">
            <div>
              <span className="section-kicker">{editingId ? "Edição" : "Cadastro"}</span>
              <h2>{editingId ? "Editar conta" : "Adicionar conta"}</h2>
            </div>
            <button className="icon-button" type="button" aria-label="Fechar formulário" onClick={resetForm}>
              <X size={19} aria-hidden="true" />
            </button>
          </div>
          <div className="resource-form-grid">
            <div className="field">
              <label htmlFor="account-name">Nome da conta</label>
              <input className="input" id="account-name" value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
            </div>
            <div className="field">
              <label htmlFor="account-type">Tipo</label>
              <select className="input" id="account-type" value={type} onChange={(event) => setType(event.target.value)}>
                {accountTypes.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="initial-balance">Saldo inicial</label>
              <input className="input" id="initial-balance" inputMode="decimal" value={initialBalance} onChange={(event) => setInitialBalance(event.target.value)} />
            </div>
            <div className="field color-field">
              <label htmlFor="account-color">Cor de identificação</label>
              <input id="account-color" type="color" value={color} onChange={(event) => setColor(event.target.value)} />
            </div>
          </div>
          <div className="resource-form-actions">
            <button className="button secondary" type="button" onClick={resetForm}>Cancelar</button>
            <button className="button" type="submit" disabled={saving}>
              {saving ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <CheckCircle2 size={18} aria-hidden="true" />}
              {saving ? "Salvando" : "Salvar conta"}
            </button>
          </div>
        </form>
      )}

      <div className="resource-feedback" aria-live="polite">
        {error && <p className="error">{error}</p>}
        {success && <p className="success-message"><CheckCircle2 size={17} aria-hidden="true" />{success}</p>}
      </div>

      {loading ? (
        <section className="card resource-state"><LoaderCircle className="spin" aria-hidden="true" /><p>Carregando contas...</p></section>
      ) : accounts.length === 0 ? (
        <section className="card resource-state">
          <WalletCards aria-hidden="true" />
          <h2>Sua primeira conta começa aqui</h2>
          <p>Adicione onde você movimenta dinheiro para o dashboard calcular seus saldos.</p>
          <button className="button" type="button" onClick={() => setFormOpen(true)}>Adicionar conta</button>
        </section>
      ) : (
        <section className="resource-list" aria-label="Contas ativas">
          {accounts.map((account) => (
            <article className="card resource-row" key={account.id}>
              <span className="resource-icon" style={{ backgroundColor: account.color ?? "#dcefe9" }}>
                {account.type === "wallet" ? <WalletCards aria-hidden="true" /> : <Building2 aria-hidden="true" />}
              </span>
              <div className="resource-copy">
                <strong>{account.name}</strong>
                <span>{accountTypes.find((option) => option.value === account.type)?.label ?? account.type}</span>
              </div>
              <div className="resource-value">
                <span>Saldo atual</span>
                <strong>{formatCurrency(balances.get(account.id) ?? account.initial_balance)}</strong>
              </div>
              <div className="resource-actions">
                <button className="icon-button" type="button" aria-label={`Editar ${account.name}`} onClick={() => startEdit(account)}>
                  <Pencil size={17} aria-hidden="true" />
                </button>
                <button className="icon-button" type="button" aria-label={`Arquivar ${account.name}`} disabled={archivingId === account.id} onClick={() => void archiveAccount(account)}>
                  {archivingId === account.id ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <Archive size={17} aria-hidden="true" />}
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
