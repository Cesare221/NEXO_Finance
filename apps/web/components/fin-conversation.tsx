"use client";

import { LoaderCircle, Send, UserRound, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { FinMascot } from "@/components/brand-assets";
import { defaultDashboardPeriod } from "@/components/date-range-picker";
import { notifyProposalsChanged } from "@/components/pending-proposals-provider";
import { ActionProposal, ProposalCard } from "@/components/proposal-card";
import type { DashboardData, FinancialAccount, FinancialCategory } from "@/lib/financial-types";

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

type ExpenseWizardStep = "amount" | "account" | "category" | "description" | "date" | "review";

type ExpenseDraft = {
  amount: string;
  accountId: string;
  categoryId: string;
  description: string;
  occurredOn: string;
};

const expenseWizardOrder: ExpenseWizardStep[] = ["amount", "account", "category", "description", "date", "review"];

const suggestions = [
  "Quanto gastei este mês?",
  "Qual é o meu saldo?",
  "Adicionar despesa",
  "Gastei R$ 35 no mercado"
];

const currencyFormatter = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const compactCurrencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1
});

function formatCurrency(value: string) {
  const amount = Number(value);
  return Math.abs(amount) >= 10_000
    ? compactCurrencyFormatter.format(amount)
    : currencyFormatter.format(amount);
}

function dashboardContextQuery() {
  const period = defaultDashboardPeriod();
  return new URLSearchParams({
    start_date: period.start,
    end_date: period.end
  }).toString();
}

function normalizeText(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR");
}

function isExpenseQuestionnaireIntent(value: string) {
  const normalized = normalizeText(value);
  return /(adicionar|lancar|registrar|cadastrar|nova|novo)/.test(normalized)
    && /(despesa|compra|gasto)/.test(normalized);
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function extractAmountFromMessage(value: string) {
  const match = value.match(/(?:r\$\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+\.\d{1,2}|\d+(?:,\d{1,2})?)/i);
  return match?.[1] ?? "";
}

function normalizeAmount(value: string) {
  const cleaned = value.trim().replace(/\s/g, "");
  if (!cleaned) return "";
  if (cleaned.includes(".") && cleaned.includes(",")) return cleaned.replace(/\./g, "").replace(",", ".");
  if (cleaned.includes(",")) return cleaned.replace(",", ".");
  return cleaned;
}

function flattenCategories(categories: FinancialCategory[]): FinancialCategory[] {
  return categories.flatMap((category) => [category, ...flattenCategories(category.children ?? [])]);
}

export function FinConversation({ compact = false, onClose }: { compact?: boolean; onClose?: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Olá! Posso consultar dados ou preparar um lançamento."
    }
  ]);
  const [message, setMessage] = useState("");
  const [proposal, setProposal] = useState<ActionProposal | null>(null);
  const [expenseWizard, setExpenseWizard] = useState<{ step: ExpenseWizardStep; draft: ExpenseDraft } | null>(null);
  const [wizardAccounts, setWizardAccounts] = useState<FinancialAccount[]>([]);
  const [wizardCategories, setWizardCategories] = useState<FinancialCategory[]>([]);
  const [wizardLoading, setWizardLoading] = useState(false);
  const [wizardError, setWizardError] = useState("");
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
        const response = await fetch("/api/financial/dashboard" + `?${dashboardContextQuery()}`, { cache: "no-store" });
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

  async function startExpenseWizard(seedMessage = "") {
    if (!conversationId.current) conversationId.current = crypto.randomUUID();
    setWizardLoading(true);
    setWizardError("");
    setError("");
    try {
      const [accountsResponse, categoriesResponse] = await Promise.all([
        fetch("/api/financial/accounts", { cache: "no-store" }),
        fetch("/api/financial/categories", { cache: "no-store" })
      ]);
      const accountsBody = await accountsResponse.json().catch(() => []) as FinancialAccount[] | { detail?: string };
      const categoriesBody = await categoriesResponse.json().catch(() => []) as FinancialCategory[] | { detail?: string };
      if (!accountsResponse.ok) throw new Error("detail" in accountsBody && accountsBody.detail ? accountsBody.detail : "Não foi possível carregar as contas.");
      if (!categoriesResponse.ok) throw new Error("detail" in categoriesBody && categoriesBody.detail ? categoriesBody.detail : "Não foi possível carregar as categorias.");

      const accounts = (accountsBody as FinancialAccount[]).filter((account) => !account.is_archived);
      if (!accounts.length) {
        addAssistantMessage("Antes de registrar uma despesa, cadastre pelo menos uma conta.");
        setExpenseWizard(null);
        return;
      }

      setWizardAccounts(accounts);
      setWizardCategories(flattenCategories(categoriesBody as FinancialCategory[]).filter((category) => !category.is_archived));
      setExpenseWizard({
        step: extractAmountFromMessage(seedMessage) ? "account" : "amount",
        draft: {
          amount: extractAmountFromMessage(seedMessage),
          accountId: String(accounts[0].id),
          categoryId: "",
          description: "",
          occurredOn: todayIsoDate()
        }
      });
      addAssistantMessage("Vamos por etapas. Preencha um campo por vez.");
    } catch (requestError) {
      setWizardError(requestError instanceof Error ? requestError.message : "Não foi possível iniciar o questionário.");
    } finally {
      setWizardLoading(false);
    }
  }

  function updateExpenseDraft(patch: Partial<ExpenseDraft>) {
    setExpenseWizard((current) => current ? { ...current, draft: { ...current.draft, ...patch } } : current);
  }

  function setExpenseStep(step: ExpenseWizardStep) {
    setExpenseWizard((current) => current ? { ...current, step } : current);
  }

  function nextExpenseStep() {
    if (!expenseWizard) return;
    const next = expenseWizardOrder[Math.min(expenseWizardOrder.indexOf(expenseWizard.step) + 1, expenseWizardOrder.length - 1)];
    setExpenseStep(next);
  }

  function previousExpenseStep() {
    if (!expenseWizard) return;
    const previous = expenseWizardOrder[Math.max(expenseWizardOrder.indexOf(expenseWizard.step) - 1, 0)];
    setExpenseStep(previous);
  }

  async function createExpenseProposalFromWizard() {
    if (!expenseWizard || wizardLoading) return;
    const amount = normalizeAmount(expenseWizard.draft.amount);
    const account = wizardAccounts.find((item) => String(item.id) === expenseWizard.draft.accountId);
    const category = wizardCategories.find((item) => String(item.id) === expenseWizard.draft.categoryId);
    const description = expenseWizard.draft.description.trim();
    if (!amount || Number(amount) <= 0 || !account || description.length < 2) {
      setWizardError("Confira valor, conta e descrição.");
      return;
    }

    setWizardLoading(true);
    setWizardError("");
    try {
      const summary = `Criar despesa de ${currencyFormatter.format(Number(amount))}${category ? ` em ${category.name}` : ""} na conta ${account.name}.`;
      const response = await fetch("/api/assistant/proposals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId.current,
          action_type: "create_transaction",
          payload: {
            type: "expense",
            account_id: account.id,
            category_id: category?.id ?? null,
            amount,
            description,
            occurred_on: expenseWizard.draft.occurredOn,
            origin: "fin"
          },
          human_summary: summary,
          previous_state_snapshot: { source: "fin_questionnaire" },
          idempotency_key: `fin-questionnaire-${crypto.randomUUID()}`
        })
      });
      const body = (await response.json().catch(() => ({}))) as ActionProposal & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "Não foi possível criar a proposta.");
      setProposal(body);
      setExpenseWizard(null);
      notifyProposalsChanged();
      addAssistantMessage("Proposta pronta para revisão.");
    } catch (requestError) {
      setWizardError(requestError instanceof Error ? requestError.message : "Não foi possível criar a proposta.");
    } finally {
      setWizardLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = message.trim();
    if (!content || sending || messageSubmissionRef.current) return;

    if (isExpenseQuestionnaireIntent(content)) {
      const clientMessageId = crypto.randomUUID();
      if (!conversationId.current) conversationId.current = crypto.randomUUID();
      setMessages((current) => [
        ...current,
        { id: clientMessageId, role: "user", text: content }
      ]);
      setMessage("");
      void startExpenseWizard(content);
      return;
    }

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
      addAssistantMessage("Proposta atualizada.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível editar a proposta.");
      throw requestError;
    } finally {
      setPendingAction(null);
    }
  }

  function useSuggestion(value: string) {
    if (isExpenseQuestionnaireIntent(value)) {
      void startExpenseWizard(value);
      return;
    }
    setMessage(value);
    inputRef.current?.focus();
  }

  function renderExpenseWizard() {
    if (!expenseWizard) return null;
    const { step, draft } = expenseWizard;
    const amount = Number(normalizeAmount(draft.amount));
    const account = wizardAccounts.find((item) => String(item.id) === draft.accountId);
    const category = wizardCategories.find((item) => String(item.id) === draft.categoryId);
    const canGoNext =
      (step === "amount" && Number.isFinite(amount) && amount > 0)
      || (step === "account" && Boolean(account))
      || step === "category"
      || (step === "description" && draft.description.trim().length >= 2)
      || (step === "date" && Boolean(draft.occurredOn));
    const stepLabels: Record<ExpenseWizardStep, string> = {
      amount: "Valor",
      account: "Conta",
      category: "Categoria",
      description: "Descrição",
      date: "Data",
      review: "Revisão"
    };
    const currentStepIndex = expenseWizardOrder.indexOf(step);

    return (
      <section className="fin-wizard-card" aria-label="Questionário para adicionar despesa">
        <div className="fin-wizard-heading">
          <div>
            <span className="eyebrow">Adicionar despesa</span>
            <h3>{stepLabels[step]}</h3>
          </div>
          <button className="icon-button" type="button" aria-label="Fechar questionário" onClick={() => setExpenseWizard(null)}>
            <X size={17} aria-hidden="true" />
          </button>
        </div>
        <ol className="fin-wizard-steps" aria-label="Progresso do questionário">
          {expenseWizardOrder.map((item, index) => (
            <li
              className={index <= currentStepIndex ? "active" : ""}
              key={item}
              aria-current={item === step ? "step" : undefined}
            >
              <span>{index + 1}</span>
              <strong>{stepLabels[item]}</strong>
            </li>
          ))}
        </ol>

        {step === "amount" ? (
          <label className="field">
            Valor da despesa
            <input
              className="input"
              inputMode="decimal"
              value={draft.amount}
              onChange={(event) => updateExpenseDraft({ amount: event.target.value })}
              placeholder="190,00"
              autoFocus
            />
          </label>
        ) : null}

        {step === "account" ? (
          <div className="fin-wizard-options" role="group" aria-label="Selecionar conta">
            {wizardAccounts.map((item) => (
              <button
                className={String(item.id) === draft.accountId ? "selected" : ""}
                key={item.id}
                type="button"
                onClick={() => updateExpenseDraft({ accountId: String(item.id) })}
              >
                {item.name}
              </button>
            ))}
          </div>
        ) : null}

        {step === "category" ? (
          <div className="fin-wizard-options" role="group" aria-label="Selecionar categoria">
            <button
              className={!draft.categoryId ? "selected" : ""}
              type="button"
              onClick={() => updateExpenseDraft({ categoryId: "" })}
            >
              Sem categoria
            </button>
            {wizardCategories.map((item) => (
              <button
                className={String(item.id) === draft.categoryId ? "selected" : ""}
                key={item.id}
                type="button"
                onClick={() => updateExpenseDraft({ categoryId: String(item.id) })}
              >
                {item.name}
              </button>
            ))}
          </div>
        ) : null}

        {step === "description" ? (
          <label className="field">
            Descrição curta
            <input
              className="input"
              value={draft.description}
              onChange={(event) => updateExpenseDraft({ description: event.target.value })}
              placeholder="Ex.: Compra no mercado"
              maxLength={120}
              autoFocus
            />
          </label>
        ) : null}

        {step === "date" ? (
          <label className="field">
            Data da despesa
            <input
              className="input"
              type="date"
              value={draft.occurredOn}
              onChange={(event) => updateExpenseDraft({ occurredOn: event.target.value })}
            />
          </label>
        ) : null}

        {step === "review" ? (
          <div className="fin-wizard-review">
            <span><strong>Valor</strong>{Number.isFinite(amount) ? currencyFormatter.format(amount) : "-"}</span>
            <span><strong>Conta</strong>{account?.name ?? "-"}</span>
            <span><strong>Categoria</strong>{category?.name ?? "Sem categoria"}</span>
            <span><strong>Descrição</strong>{draft.description}</span>
            <span><strong>Data</strong>{draft.occurredOn}</span>
          </div>
        ) : null}

        {wizardError ? <p className="error fin-wizard-error" role="alert">{wizardError}</p> : null}

        <div className="fin-wizard-actions">
          {step !== "amount" ? (
            <button className="button secondary" type="button" onClick={previousExpenseStep} disabled={wizardLoading}>
              Voltar
            </button>
          ) : null}
          {step !== "review" ? (
            <button className="button" type="button" onClick={nextExpenseStep} disabled={!canGoNext || wizardLoading}>
              Próximo
            </button>
          ) : (
            <button className="button" type="button" onClick={() => void createExpenseProposalFromWizard()} disabled={wizardLoading}>
              {wizardLoading ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : null}
              Criar proposta
            </button>
          )}
        </div>
      </section>
    );
  }

  return (
    <section className={compact ? "fin-chat compact" : "fin-chat"} aria-busy={sending || pendingAction !== null || contextLoading} aria-labelledby="fin-chat-title">
      <div className="fin-chat-header">
        <span className="fin-avatar" aria-hidden="true"><FinMascot variant="avatar" /></span>
        <div><h2 id="fin-chat-title">Conversa com o Fin</h2><span>Revisão antes de salvar.</span></div>
        {onClose ? <button className="icon-button fin-chat-close" type="button" aria-label="Fechar conversa com o Fin" onClick={onClose}><X size={18} aria-hidden="true" /></button> : null}
      </div>

      <section className="fin-financial-context" aria-busy={contextLoading} aria-live="polite" aria-label="Resumo financeiro atual">
        <div className="fin-financial-context-heading">
          <span>Resumo</span>
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
        {!financialContext && contextLoading && <p className="fin-context-state">Carregando dados.</p>}
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
        {renderExpenseWizard()}
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
