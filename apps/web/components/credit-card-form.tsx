"use client";

import Link from "next/link";
import { CheckCircle2, CreditCard, LoaderCircle, WalletCards, X } from "lucide-react";
import { FormEvent, useId, useMemo, useState } from "react";
import { CurrencyInput } from "@/components/currency-input";
import type { FinancialAccount, FinancialCreditCard } from "@/lib/financial-types";

type CreditCardFormProps = {
  accounts: FinancialAccount[];
  card?: FinancialCreditCard;
  onSaved: (card: FinancialCreditCard) => void | Promise<void>;
  onCancel: () => void;
};

type FieldErrors = Partial<Record<"name" | "limit" | "closingDay" | "dueDay" | "account", string>>;

const brlFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL"
});

async function readError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: string } | null;
  return data?.detail ?? "Não foi possível salvar o cartão.";
}

export function CreditCardForm({ accounts, card, onSaved, onCancel }: CreditCardFormProps) {
  const formId = useId().replace(/:/g, "");
  const [name, setName] = useState(card?.name ?? "");
  const [limitAmount, setLimitAmount] = useState(card?.limit_amount ?? "0.00");
  const [closingDay, setClosingDay] = useState(String(card?.closing_day ?? 10));
  const [dueDay, setDueDay] = useState(String(card?.due_day ?? 20));
  const [paymentAccountId, setPaymentAccountId] = useState(String(card?.payment_account_id ?? accounts[0]?.id ?? ""));
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const accountName = useMemo(
    () => accounts.find((account) => String(account.id) === paymentAccountId)?.name ?? "Conta não selecionada",
    [accounts, paymentAccountId]
  );

  const ids = {
    name: `${formId}-card-name`,
    limit: `${formId}-card-limit`,
    closing: `${formId}-closing-day`,
    due: `${formId}-due-day`,
    account: `${formId}-payment-account`
  };

  function validate() {
    const nextErrors: FieldErrors = {};
    const closing = Number(closingDay);
    const due = Number(dueDay);

    if (name.trim().length < 2) nextErrors.name = "Informe um nome com pelo menos 2 caracteres.";
    if (Number(limitAmount) <= 0) nextErrors.limit = "Informe um limite maior que zero.";
    if (!Number.isInteger(closing) || closing < 1 || closing > 31) nextErrors.closingDay = "Use um dia entre 1 e 31.";
    if (!Number.isInteger(due) || due < 1 || due > 31) nextErrors.dueDay = "Use um dia entre 1 e 31.";
    if (!nextErrors.closingDay && !nextErrors.dueDay && closing === due) {
      nextErrors.dueDay = "O vencimento deve ser diferente do fechamento.";
    }
    if (!paymentAccountId) nextErrors.account = "Selecione a conta usada para pagar a fatura.";

    setFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function saveCard(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    setError("");
    if (!validate()) return;

    setSaving(true);
    try {
      const response = await fetch(
        card ? `/api/financial/credit-cards/${card.id}` : "/api/financial/credit-cards",
        {
          method: card ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            limit_amount: Number(limitAmount).toFixed(2),
            closing_day: Number(closingDay),
            due_day: Number(dueDay),
            payment_account_id: Number(paymentAccountId)
          })
        }
      );
      if (!response.ok) throw new Error(await readError(response));
      await onSaved(await response.json() as FinancialCreditCard);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar o cartão.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card form resource-form credit-card-form" onSubmit={saveCard} noValidate>
      <div className="resource-heading">
        <div>
          <span className="section-kicker">{card ? "Edição" : "Cadastro"}</span>
          <h2>{card ? "Editar cartão" : "Novo cartão"}</h2>
        </div>
        <button className="icon-button" type="button" aria-label="Fechar formulário" onClick={onCancel}>
          <X size={19} aria-hidden="true" />
        </button>
      </div>

      <div className="credit-card-form-layout">
        <div className="credit-card-fields">
          <fieldset className="credit-card-fieldset">
            <legend>Identificação</legend>
            <div className="field">
              <label htmlFor={ids.name}>Nome do cartão</label>
              <input
                className="input"
                id={ids.name}
                value={name}
                onChange={(event) => setName(event.target.value)}
                aria-invalid={Boolean(fieldErrors.name)}
                aria-describedby={fieldErrors.name ? `${ids.name}-error` : undefined}
                maxLength={80}
                required
              />
              {fieldErrors.name && <span className="field-error" id={`${ids.name}-error`}>{fieldErrors.name}</span>}
            </div>
            <CurrencyInput
              id={ids.limit}
              label="Limite total"
              value={limitAmount}
              onValueChange={setLimitAmount}
              error={fieldErrors.limit}
              disabled={saving}
              required
            />
          </fieldset>

          <fieldset className="credit-card-fieldset">
            <legend>Ciclo e pagamento</legend>
            <div className="credit-card-cycle-grid">
              <div className="field">
                <label htmlFor={ids.closing}>Dia de fechamento</label>
                <input
                  className="input"
                  id={ids.closing}
                  type="number"
                  min="1"
                  max="31"
                  value={closingDay}
                  onChange={(event) => setClosingDay(event.target.value)}
                  aria-invalid={Boolean(fieldErrors.closingDay)}
                  aria-describedby={`${ids.closing}-help${fieldErrors.closingDay ? ` ${ids.closing}-error` : ""}`}
                  required
                />
                <span className="field-help" id={`${ids.closing}-help`}>Compras após esse dia entram no próximo ciclo.</span>
                {fieldErrors.closingDay && <span className="field-error" id={`${ids.closing}-error`}>{fieldErrors.closingDay}</span>}
              </div>
              <div className="field">
                <label htmlFor={ids.due}>Dia de vencimento</label>
                <input
                  className="input"
                  id={ids.due}
                  type="number"
                  min="1"
                  max="31"
                  value={dueDay}
                  onChange={(event) => setDueDay(event.target.value)}
                  aria-invalid={Boolean(fieldErrors.dueDay)}
                  aria-describedby={`${ids.due}-help${fieldErrors.dueDay ? ` ${ids.due}-error` : ""}`}
                  required
                />
                <span className="field-help" id={`${ids.due}-help`}>Dia previsto para pagamento da fatura.</span>
                {fieldErrors.dueDay && <span className="field-error" id={`${ids.due}-error`}>{fieldErrors.dueDay}</span>}
              </div>
            </div>
            <div className="field">
              <label htmlFor={ids.account}>Conta de pagamento</label>
              <select
                className="input"
                id={ids.account}
                value={paymentAccountId}
                onChange={(event) => setPaymentAccountId(event.target.value)}
                aria-invalid={Boolean(fieldErrors.account)}
                aria-describedby={fieldErrors.account ? `${ids.account}-error` : undefined}
                required
              >
                <option value="">Selecione</option>
                {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
              </select>
              {fieldErrors.account && <span className="field-error" id={`${ids.account}-error`}>{fieldErrors.account}</span>}
            </div>
          </fieldset>
        </div>

        <aside className="credit-card-preview-wrap" aria-label="Prévia do cartão">
          <span className="section-kicker">Prévia do cartão</span>
          <div className="credit-card-preview">
            <div className="credit-card-preview-top">
              <WalletCards size={24} aria-hidden="true" />
              <span>NEXO</span>
            </div>
            <strong>{name.trim() || "Meu cartão"}</strong>
            <div className="credit-card-preview-limit">
              <span>Limite</span>
              <b>{brlFormatter.format(Number(limitAmount) || 0)}</b>
            </div>
            <div className="credit-card-preview-meta">
              <span>Fecha dia {closingDay || "--"}</span>
              <span>Vence dia {dueDay || "--"}</span>
            </div>
          </div>
          <p><CreditCard size={16} aria-hidden="true" />{accountName}</p>
        </aside>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {accounts.length === 0 ? (
        <div className="credit-card-account-empty">
          <p>Cadastre uma conta antes de criar o cartão. Ela será usada no pagamento das faturas.</p>
          <Link className="button" href="/contas">Criar conta</Link>
        </div>
      ) : (
        <div className="resource-form-actions">
          <button className="button secondary" type="button" onClick={onCancel}>Cancelar</button>
          <button className="button" type="submit" disabled={saving}>
            {saving ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <CheckCircle2 size={18} aria-hidden="true" />}
            {saving ? "Salvando" : "Salvar cartão"}
          </button>
        </div>
      )}
    </form>
  );
}
