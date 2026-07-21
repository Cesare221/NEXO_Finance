"use client";

import { LoaderCircle, Send, UserRound, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { FinMascot } from "@/components/brand-assets";
import { notifyProposalsChanged } from "@/components/pending-proposals-provider";
import { ActionProposal, ProposalCard } from "@/components/proposal-card";
import type { DashboardData } from "@/lib/financial-types";

type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  text: string;
};

type AssistantResponse = {
  kind: "answer" | "proposal" | "clarification";
  message: string;
  proposal: ActionProposal | null;
};

const suggestions = [
  "Quanto gastei este mês?",
  "Qual é o meu saldo?",
  "Gastei R$ 35 no mercado"
];

const currencyFormatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function formatCurrency(value: string) {
  return currencyFormatter.format(Number(value));
}

export function FinConversation({ compact = false, onClose }: { compact?: boolean; onClose?: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Olá! Posso consultar seus números ou preparar um lançamento para você revisar."
    }
  ]);
  const [message, setMessage] = useState("");
  const [proposal, setProposal] = useState<ActionProposal | null>(null);
  const [sending, setSending] = useState(false);
  const [pendingAction, setPendingAction] = useState<"confirm" | "cancel" | "edit" | null>(null);
  const [error, setError] = useState("");
  const [financialContext, setFinancialContext] = useState<DashboardData | null>(null);
  const [contextLoading, setContextLoading] = useState(true);
  const [contextError, setContextError] = useState("");
  const conversationId = useRef<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const refreshPromiseRef = useRef<Promise<void> | null>(null);
  const contextRequestRef = useRef(0);
  const messageSubmissionRef = useRef(false);

  function addAssistantMessage(text: string) {
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "assistant", text }
    ]);
  }

  const refreshFinancialContext = useCallback(() => {
    const requestId = contextRequestRef.current + 1;
    contextRequestRef.current = requestId;
    setContextLoading(true);
    setContextError("");

    const refreshPromise = (async () => {
      try {
        const response = await fetch("/api/financial/dashboard", { cache: "no-store" });
        const body = (await response.json().catch(() => ({}))) as DashboardData & { detail?: string };
        if (!response.ok) throw new Error(body.detail ?? "Não foi possível atualizar o contexto financeiro.");
        if (requestId === contextRequestRef.current) setFinancialContext(body);
      } catch (requestError) {
        if (requestId === contextRequestRef.current) {
          setContextError(requestError instanceof Error ? requestError.message : "Não foi possível atualizar o contexto financeiro.");
        }
      }
    })();

    refreshPromiseRef.current = refreshPromise;
    void refreshPromise.finally(() => {
      if (refreshPromiseRef.current === refreshPromise) {
        refreshPromiseRef.current = null;
        setContextLoading(false);
      }
    });

    return refreshPromise;
  }, []);

  useEffect(() => {
    void refreshFinancialContext();
    const refresh = () => void refreshFinancialContext();
    window.addEventListener("nexo:financial-data-changed", refresh);
    return () => window.removeEventListener("nexo:financial-data-changed", refresh);
  }, [refreshFinancialContext]);

  async function waitForLatestFinancialContext() {
    while (true) {
      const requestId = contextRequestRef.current;
      const refreshPromise = refreshPromiseRef.current;
      if (refreshPromise) await refreshPromise;

      if (
        requestId === contextRequestRef.current &&
        refreshPromise === refreshPromiseRef.current
      ) {
        return;
      }
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = message.trim();
    if (!content || sending || messageSubmissionRef.current) return;

    messageSubmissionRef.current = true;
    try {
      await waitForLatestFinancialContext();

      const clientMessageId = crypto.randomUUID();
      if (!conversationId.current) conversationId.current = crypto.randomUUID();
      setMessages((current) => [
        ...current,
        { id: clientMessageId, role: "user", text: content }
      ]);
      setMessage("");
      setSending(true);
      setError("");

      const response = await fetch("/api/assistant/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId.current,
          client_message_id: clientMessageId
        })
      });
      const body = (await response.json().catch(() => ({}))) as AssistantResponse & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Não foi possível enviar a mensagem.");
      addAssistantMessage(body.message);
      if (body.proposal) {
        setProposal(body.proposal);
        notifyProposalsChanged();
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível enviar a mensagem.");
    } finally {
      setSending(false);
      messageSubmissionRef.current = false;
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  async function proposalAction(action: "confirm" | "cancel") {
    if (!proposal || pendingAction) return;
    setPendingAction(action);
    setError("");
    try {
      const response = await fetch(`/api/assistant/proposals/${proposal.id}/${action}`, { method: "POST" });
      const body = (await response.json().catch(() => ({}))) as
        | ActionProposal
        | { proposal?: ActionProposal; detail?: string };
      if (!response.ok) {
        throw new Error("detail" in body && body.detail ? body.detail : "Não foi possível atualizar a proposta.");
      }
      const updated = "proposal" in body && body.proposal ? body.proposal : body as ActionProposal;
      setProposal(updated);
      notifyProposalsChanged();
      if (action === "confirm") window.dispatchEvent(new Event("nexo:financial-data-changed"));
      addAssistantMessage(
        action === "confirm"
          ? "Tudo certo. O lançamento foi confirmado e registrado uma única vez."
          : "Proposta cancelada. Nenhuma movimentação foi criada."
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível atualizar a proposta.");
    } finally {
      setPendingAction(null);
    }
  }

  async function editProposal(payload: ActionProposal["payload"], summary: string) {
    if (!proposal || pendingAction) return;
    setPendingAction("edit");
    setError("");
    try {
      const response = await fetch(`/api/assistant/proposals/${proposal.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload, human_summary: summary })
      });
      const body = (await response.json().catch(() => ({}))) as ActionProposal & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Não foi possível editar a proposta.");
      setProposal(body);
      notifyProposalsChanged();
      addAssistantMessage("Atualizei a proposta. Revise novamente antes de confirmar.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível editar a proposta.");
      throw requestError;
    } finally {
      setPendingAction(null);
    }
  }

  function useSuggestion(value: string) {
    setMessage(value);
    inputRef.current?.focus();
  }

  return (
    <section className={compact ? "fin-chat compact" : "fin-chat"} aria-busy={sending || pendingAction !== null || contextLoading} aria-labelledby="fin-chat-title">
      <div className="fin-chat-header">
        <span className="fin-avatar" aria-hidden="true"><FinMascot variant="avatar" /></span>
        <div><h2 id="fin-chat-title">Conversa com o Fin</h2><span>Online · suas ações sempre passam por revisão</span></div>
        {onClose ? <button className="icon-button fin-chat-close" type="button" aria-label="Fechar conversa com o Fin" onClick={onClose}><X size={18} aria-hidden="true" /></button> : null}
      </div>

      <section className="fin-financial-context" aria-busy={contextLoading} aria-live="polite" aria-label="Resumo financeiro atual">
        <div className="fin-financial-context-heading">
          <span>Contexto financeiro</span>
          {contextLoading && <span role="status">Atualizando</span>}
        </div>
        {financialContext && (
          <dl className="fin-financial-summary">
            <div><dt>Saldo</dt><dd>{formatCurrency(financialContext.total_balance)}</dd></div>
            <div><dt>Receitas</dt><dd>{formatCurrency(financialContext.period_income)}</dd></div>
            <div><dt>Despesas</dt><dd>{formatCurrency(financialContext.period_expenses)}</dd></div>
            <div><dt>Faturas</dt><dd>{formatCurrency(financialContext.open_statement_total)}</dd></div>
          </dl>
        )}
        {!financialContext && contextLoading && <p className="fin-context-state">Carregando dados financeiros...</p>}
        {contextError && <p className="fin-context-state error" role="status">{contextError}</p>}
      </section>

      <div className="fin-messages" aria-live="polite" aria-relevant="additions">
        {messages.map((item) => (
          <div className={`chat-row ${item.role}`} key={item.id}>
            <span className="chat-avatar" aria-hidden="true">
              {item.role === "assistant" ? <FinMascot variant="avatar" /> : <UserRound size={18} />}
            </span>
            <p>{item.text}</p>
          </div>
        ))}
        {sending && (
          <div className="chat-row assistant">
            <span className="chat-avatar" aria-hidden="true"><FinMascot variant="avatar" /></span>
            <p className="typing"><span /><span /><span /><span className="sr-only">Fin está analisando</span></p>
          </div>
        )}
        {proposal && (
          <ProposalCard
            proposal={proposal}
            pendingAction={pendingAction}
            onConfirm={() => proposalAction("confirm")}
            onCancel={() => proposalAction("cancel")}
            onEdit={editProposal}
          />
        )}
      </div>

      <div className="chat-suggestions" aria-label="Sugestões de mensagem">
        {suggestions.map((suggestion) => (
          <button type="button" key={suggestion} onClick={() => useSuggestion(suggestion)}>{suggestion}</button>
        ))}
      </div>

      {error && <p className="error fin-error" role="alert">{error}</p>}
      <form className="fin-composer" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="fin-message">Mensagem para o Fin</label>
        <textarea
          ref={inputRef}
          id="fin-message"
          rows={2}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Pergunte ou descreva uma movimentação"
          maxLength={1000}
          required
        />
        <button type="submit" aria-label="Enviar mensagem" title="Enviar mensagem" disabled={sending || !message.trim()}>
          {sending
            ? <LoaderCircle className="spin" size={20} aria-hidden="true" />
            : <Send size={20} aria-hidden="true" />}
        </button>
      </form>
    </section>
  );
}
