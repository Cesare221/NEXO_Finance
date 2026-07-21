"use client";

import { AlertTriangle, Check, ChevronRight, Inbox, LoaderCircle, MessageSquareText, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { ActionProposal } from "@/components/proposal-card";
import { usePendingProposals } from "@/components/pending-proposals-provider";

type ProposalGroup = {
  key: string;
  label: string;
  proposals: ActionProposal[];
  total: number;
};

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const dateFormatter = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "long", year: "numeric" });

function canBulkApprove(proposal: ActionProposal) {
  const confidence = typeof proposal.payload.confidence === "number" ? proposal.payload.confidence : 1;
  return proposal.payload.possible_duplicate !== true && confidence >= 0.7;
}

function groupProposals(proposals: ActionProposal[]) {
  const groups = new Map<string, ProposalGroup>();
  for (const proposal of proposals) {
    const origin = String(proposal.payload.origin ?? "fin");
    const account = String(proposal.payload.account_id ?? "sem-conta");
    const date = proposal.created_at.slice(0, 10);
    const key = `${date}:${origin}:${account}`;
    const existing = groups.get(key) ?? {
      key,
      label: `${origin === "fin" || origin === "recognized" ? "Reconhecidas pelo Fin" : origin} · ${dateFormatter.format(new Date(`${date}T00:00:00`))}`,
      proposals: [],
      total: 0
    };
    existing.proposals.push(proposal);
    const amount = Number(proposal.payload.amount ?? 0);
    existing.total += proposal.payload.type === "income" ? amount : -amount;
    groups.set(key, existing);
  }
  return [...groups.values()];
}

export function MovementReviewInbox() {
  const { proposals, loading, error, actOnProposal } = usePendingProposals();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [busy, setBusy] = useState<number | "bulk" | null>(null);
  const [actionError, setActionError] = useState("");
  const groups = useMemo(() => groupProposals(proposals), [proposals]);

  function toggleSelected(proposalId: number) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(proposalId)) next.delete(proposalId);
      else next.add(proposalId);
      return next;
    });
  }

  async function review(proposalId: number, action: "confirm" | "cancel") {
    setBusy(proposalId);
    setActionError("");
    try {
      await actOnProposal(proposalId, action);
      setSelected((current) => {
        const next = new Set(current);
        next.delete(proposalId);
        return next;
      });
    } catch (requestError) {
      setActionError(requestError instanceof Error ? requestError.message : "Não foi possível revisar a movimentação.");
    } finally {
      setBusy(null);
    }
  }

  async function approveSelected() {
    const approvedIds = proposals.filter((proposal) => selected.has(proposal.id) && canBulkApprove(proposal)).map((proposal) => proposal.id);
    if (!approvedIds.length) return;
    setBusy("bulk");
    setActionError("");
    const failures: number[] = [];
    for (const proposalId of approvedIds) {
      try {
        await actOnProposal(proposalId, "confirm");
        setSelected((current) => {
          const next = new Set(current);
          next.delete(proposalId);
          return next;
        });
      } catch {
        failures.push(proposalId);
      }
    }
    if (failures.length) setActionError(`${failures.length} movimentação(ões) continuaram pendentes. Tente novamente.`);
    setBusy(null);
  }

  return (
    <section className="card movement-inbox" aria-labelledby="movement-inbox-title">
      <div className="section-heading movement-inbox-heading">
        <div>
          <span className="eyebrow">Aguardando sua decisão</span>
          <h2 id="movement-inbox-title">Movimentações reconhecidas</h2>
        </div>
        {proposals.length ? <span className="pending-count">{proposals.length} pendente{proposals.length === 1 ? "" : "s"}</span> : null}
      </div>

      {loading ? <p className="inbox-state"><LoaderCircle className="spin" size={18} /> Carregando reconhecimentos...</p> : null}
      {error ? <p className="error" role="alert">{error}</p> : null}
      {!loading && !error && !groups.length ? (
        <div className="inbox-empty"><Inbox size={22} aria-hidden="true" /><div><strong>Nenhuma movimentação para revisar</strong><span>Quando o Fin reconhecer algo, o aviso aparecerá aqui.</span></div></div>
      ) : null}

      {groups.map((group) => (
        <div className="movement-group" key={group.key}>
          <div className="movement-group-heading"><div><strong>{group.label}</strong><span>{group.proposals.length} item(ns)</span></div><strong className={group.total >= 0 ? "positive" : ""}>{currency.format(group.total)}</strong></div>
          <div className="movement-review-list">
            {group.proposals.map((proposal) => {
              const bulkAllowed = canBulkApprove(proposal);
              const confidence = typeof proposal.payload.confidence === "number" ? Math.round(proposal.payload.confidence * 100) : null;
              return (
                <article className="movement-review-row" key={proposal.id}>
                  <label className="movement-select">
                    <input type="checkbox" checked={selected.has(proposal.id)} disabled={!bulkAllowed || busy !== null} onChange={() => toggleSelected(proposal.id)} />
                    <span className="sr-only">Selecionar {proposal.human_summary}</span>
                  </label>
                  <div className="movement-review-copy">
                    <strong>{String(proposal.payload.description ?? proposal.human_summary)}</strong>
                    <span>{proposal.payload.type === "income" ? "Receita" : "Despesa"} · {currency.format(Number(proposal.payload.amount ?? 0))}</span>
                    {!bulkAllowed ? <span className="review-warning"><AlertTriangle size={14} /> Revisão individual obrigatória{confidence !== null ? ` · confiança ${confidence}%` : ""}</span> : null}
                  </div>
                  <div className="movement-review-actions">
                    <button className="icon-button approve" type="button" title="Aprovar" aria-label={`Aprovar ${proposal.human_summary}`} disabled={busy !== null} onClick={() => void review(proposal.id, "confirm")}>{busy === proposal.id ? <LoaderCircle className="spin" size={17} /> : <Check size={17} />}</button>
                    <button className="icon-button" type="button" title="Rejeitar" aria-label={`Rejeitar ${proposal.human_summary}`} disabled={busy !== null} onClick={() => void review(proposal.id, "cancel")}><X size={17} /></button>
                    <button className="icon-button" type="button" title="Abrir no Fin" aria-label={`Abrir ${proposal.human_summary} no Fin`} onClick={() => window.dispatchEvent(new Event("nexo:open-fin"))}><MessageSquareText size={17} /></button>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      ))}

      {selected.size ? (
        <div className="movement-bulk-bar">
          <span>{selected.size} selecionada{selected.size === 1 ? "" : "s"}</span>
          <button className="button" type="button" disabled={busy !== null} onClick={() => void approveSelected()}>{busy === "bulk" ? <LoaderCircle className="spin" size={18} /> : <Check size={18} />}Aprovar selecionadas</button>
        </div>
      ) : null}
      {actionError ? <p className="error" role="alert">{actionError}</p> : null}
      {proposals.length ? <button className="text-action quiet inbox-fin-link" type="button" onClick={() => window.dispatchEvent(new Event("nexo:open-fin"))}>Revisar com o Fin <ChevronRight size={16} /></button> : null}
    </section>
  );
}
