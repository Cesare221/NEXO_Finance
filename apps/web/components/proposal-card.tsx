"use client";

import { Check, LoaderCircle, Pencil, Save, ShieldCheck, X } from "lucide-react";
import { FormEvent, useState } from "react";

export type ActionProposal = {
  id: number;
  action_type: string;
  human_summary: string;
  status: string;
  expires_at: string;
  created_at: string;
  payload: {
    type?: string;
    account_id?: number;
    category_id?: number | null;
    amount?: string;
    description?: string;
    occurred_on?: string;
    origin?: string;
    [key: string]: unknown;
  };
};

type ProposalCardProps = {
  proposal: ActionProposal;
  pendingAction: "confirm" | "cancel" | "edit" | null;
  onConfirm: () => Promise<void>;
  onCancel: () => Promise<void>;
  onEdit: (payload: ActionProposal["payload"], summary: string) => Promise<void>;
};

const statusLabels: Record<string, string> = {
  proposed: "Aguardando confirmação",
  executed: "Concluída",
  cancelled: "Cancelada",
  expired: "Expirada",
  failed: "Falhou"
};

export function ProposalCard({
  proposal,
  pendingAction,
  onConfirm,
  onCancel,
  onEdit
}: ProposalCardProps) {
  const [editing, setEditing] = useState(false);
  const canAct = proposal.status === "proposed";

  async function handleEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const amount = String(formData.get("amount") ?? proposal.payload.amount ?? "");
    const description = String(formData.get("description") ?? proposal.payload.description ?? "").trim();
    const typeLabel = proposal.payload.type === "income" ? "receita" : "despesa";
    try {
      await onEdit(
        { ...proposal.payload, amount, description },
        `Criar ${typeLabel} de R$ ${amount.replace(".", ",")}.`
      );
      setEditing(false);
    } catch {
      // The conversation keeps the editor open and announces the request error.
    }
  }

  return (
    <section className="proposal-card" aria-labelledby={`proposal-title-${proposal.id}`}>
      <div className="proposal-heading">
        <span className="proposal-icon"><ShieldCheck size={20} aria-hidden="true" /></span>
        <div>
          <span className="eyebrow">Revisão obrigatória</span>
          <h3 id={`proposal-title-${proposal.id}`}>Proposta do Fin</h3>
        </div>
        <span className={`status proposal-status ${proposal.status}`}>
          {statusLabels[proposal.status] ?? proposal.status}
        </span>
      </div>

      <p className="proposal-summary">{proposal.human_summary}</p>
      <p className="proposal-safety">Nada é salvo antes de você confirmar.</p>

      {editing ? (
        <form className="proposal-edit-form" onSubmit={handleEdit}>
          <div className="field">
            <label htmlFor={`proposal-amount-${proposal.id}`}>Valor</label>
            <input
              className="input"
              id={`proposal-amount-${proposal.id}`}
              name="amount"
              inputMode="decimal"
              defaultValue={proposal.payload.amount}
              required
            />
          </div>
          <div className="field">
            <label htmlFor={`proposal-description-${proposal.id}`}>Descrição</label>
            <input
              className="input"
              id={`proposal-description-${proposal.id}`}
              name="description"
              defaultValue={proposal.payload.description}
              maxLength={500}
            />
          </div>
          <div className="proposal-actions">
            <button className="button" type="submit" disabled={pendingAction !== null}>
              {pendingAction === "edit"
                ? <LoaderCircle className="spin" size={18} aria-hidden="true" />
                : <Save size={18} aria-hidden="true" />}
              Salvar alterações
            </button>
            <button className="button secondary" type="button" onClick={() => setEditing(false)}>
              <X size={18} aria-hidden="true" /> Fechar
            </button>
          </div>
        </form>
      ) : canAct ? (
        <div className="proposal-actions" aria-label="Ações da proposta">
          <button className="button" type="button" onClick={() => void onConfirm()} disabled={pendingAction !== null}>
            {pendingAction === "confirm"
              ? <LoaderCircle className="spin" size={18} aria-hidden="true" />
              : <Check size={18} aria-hidden="true" />}
            Confirmar
          </button>
          <button className="button secondary" type="button" onClick={() => setEditing(true)} disabled={pendingAction !== null}>
            <Pencil size={18} aria-hidden="true" /> Editar
          </button>
          <button className="button danger" type="button" onClick={() => void onCancel()} disabled={pendingAction !== null}>
            {pendingAction === "cancel"
              ? <LoaderCircle className="spin" size={18} aria-hidden="true" />
              : <X size={18} aria-hidden="true" />}
            Cancelar
          </button>
        </div>
      ) : null}
    </section>
  );
}
