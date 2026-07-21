"use client";

import {
  CheckCircle2,
  Database,
  LoaderCircle,
  Sparkles,
  Trash2
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { DemoDatasetState } from "@/lib/financial-types";

type DemoDatasetControlProps = {
  variant: "install" | "cleanup";
};

const installedDate = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "medium",
  timeStyle: "short"
});

async function readResponse(response: Response) {
  const body = (await response.json().catch(() => null)) as
    | (DemoDatasetState & { detail?: string })
    | null;
  if (!response.ok) {
    throw new Error(body?.detail ?? "N\u00e3o foi poss\u00edvel atualizar os dados de exemplo.");
  }
  if (!body) throw new Error("O servidor n\u00e3o retornou o estado dos dados de exemplo.");
  return body;
}

export function DemoDatasetControl({ variant }: DemoDatasetControlProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const statusControllerRef = useRef<AbortController | null>(null);
  const mutationControllerRef = useRef<AbortController | null>(null);
  const [state, setState] = useState<DemoDatasetState | null>(null);
  const [loading, setLoading] = useState(true);
  const [mutating, setMutating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadState = useCallback(async () => {
    statusControllerRef.current?.abort();
    const controller = new AbortController();
    statusControllerRef.current = controller;
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/financial/demo-dataset", {
        cache: "no-store",
        signal: controller.signal
      });
      const nextState = await readResponse(response);
      if (controller.signal.aborted) return;
      setState(nextState);
    } catch (requestError) {
      if (controller.signal.aborted) return;
      setError(
        requestError instanceof Error
          ? requestError.message
          : "N\u00e3o foi poss\u00edvel consultar os dados de exemplo."
      );
    } finally {
      if (statusControllerRef.current === controller) {
        statusControllerRef.current = null;
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void loadState();
    return () => {
      const statusController = statusControllerRef.current;
      statusControllerRef.current = null;
      statusController?.abort();
      const mutationController = mutationControllerRef.current;
      mutationControllerRef.current = null;
      mutationController?.abort();
    };
  }, [loadState]);

  async function confirmMutation() {
    mutationControllerRef.current?.abort();
    const controller = new AbortController();
    mutationControllerRef.current = controller;
    setMutating(true);
    setError("");
    setSuccess("");
    try {
      const response = await fetch("/api/financial/demo-dataset", {
        method: variant === "install" ? "POST" : "DELETE",
        signal: controller.signal
      });
      const nextState = await readResponse(response);
      if (controller.signal.aborted) return;
      setState(nextState);
      setSuccess(
        variant === "install"
          ? "Dados de exemplo adicionados ao seu dashboard."
          : "Dados demonstrativos removidos com seguran\u00e7a."
      );
      dialogRef.current?.close();
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (requestError) {
      if (controller.signal.aborted) return;
      setError(
        requestError instanceof Error
          ? requestError.message
          : "N\u00e3o foi poss\u00edvel atualizar os dados de exemplo."
      );
    } finally {
      if (mutationControllerRef.current === controller) {
        mutationControllerRef.current = null;
        setMutating(false);
      }
    }
  }

  function openConfirmation() {
    setError("");
    setSuccess("");
    dialogRef.current?.showModal();
  }

  const feedback = (
    <div className="resource-feedback demo-dataset-feedback" aria-live="polite">
      {error ? <p className="error">{error}</p> : null}
      {success ? (
        <p className="success-message">
          <CheckCircle2 size={17} aria-hidden="true" />
          {success}
        </p>
      ) : null}
      {error && !state ? (
        <button className="text-action quiet" type="button" onClick={() => void loadState()}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );

  const dialog = (
    <dialog
      ref={dialogRef}
      className="demo-dataset-dialog"
      aria-labelledby={`demo-${variant}-title`}
      aria-describedby={`demo-${variant}-description`}
      aria-busy={mutating}
      onCancel={(event) => {
        if (mutating) event.preventDefault();
      }}
    >
      <div className="demo-dialog-icon" aria-hidden="true">
        {variant === "install" ? <Sparkles size={22} /> : <Trash2 size={22} />}
      </div>
      <h2 id={`demo-${variant}-title`}>
        {variant === "install" ? "Adicionar dados de exemplo?" : "Limpar dados de exemplo?"}
      </h2>
      <p id={`demo-${variant}-description`}>
        {variant === "install"
          ? "O Nexo vai criar 3 contas, 1 cart\u00e3o, categorias e movimenta\u00e7\u00f5es relativas ao m\u00eas atual. Voc\u00ea poder\u00e1 remover tudo depois."
          : "A limpeza mira somente recursos demonstrativos. Recursos adotados por movimenta\u00e7\u00f5es reais ser\u00e3o preservados."}
      </p>
      <div className="resource-feedback demo-dialog-feedback" aria-live="assertive">
        {error ? <p className="error">{error}</p> : null}
      </div>
      <div className="demo-dialog-actions">
        <button
          className="button secondary"
          type="button"
          disabled={mutating}
          onClick={() => dialogRef.current?.close()}
        >
          Cancelar
        </button>
        <button
          className={variant === "cleanup" ? "button danger" : "button"}
          type="button"
          disabled={mutating}
          onClick={() => void confirmMutation()}
        >
          {mutating ? (
            <LoaderCircle className="spin" size={18} aria-hidden="true" />
          ) : variant === "install" ? (
            <Sparkles size={18} aria-hidden="true" />
          ) : (
            <Trash2 size={18} aria-hidden="true" />
          )}
          {mutating
            ? variant === "install"
              ? "Adicionando"
              : "Limpando"
            : variant === "install"
              ? "Adicionar exemplos"
              : "Limpar exemplos"}
        </button>
      </div>
    </dialog>
  );

  if (variant === "install") {
    if (!loading && state?.active) {
      return success ? <div className="demo-install-control">{feedback}</div> : null;
    }
    return (
      <div className="demo-install-control" aria-busy={loading || mutating}>
        <button
          className="button secondary"
          type="button"
          disabled={loading || mutating || !state}
          onClick={openConfirmation}
        >
          {loading ? (
            <LoaderCircle className="spin" size={18} aria-hidden="true" />
          ) : (
            <Sparkles size={18} aria-hidden="true" />
          )}
          {loading ? "Verificando exemplos" : "Explorar com dados de exemplo"}
        </button>
        {feedback}
        {dialog}
      </div>
    );
  }

  return (
    <section
      className="card demo-dataset-settings"
      aria-labelledby="demo-dataset-settings-title"
      aria-busy={loading || mutating}
    >
      <div className="demo-settings-copy">
        <span className="demo-settings-icon" aria-hidden="true">
          <Database size={21} />
        </span>
        <div>
          <span className="section-kicker">Ambiente de explora\u00e7\u00e3o</span>
          <h2 id="demo-dataset-settings-title">Dados de exemplo</h2>
          <p>
            {loading
              ? "Consultando o estado dos dados demonstrativos."
              : state?.active
                ? `Ativos desde ${state.installed_at ? installedDate.format(new Date(state.installed_at)) : "esta sess\u00e3o"}.`
                : "Nenhum conjunto demonstrativo est\u00e1 ativo nesta conta."}
          </p>
        </div>
      </div>
      {state?.active ? (
        <button
          className="button secondary demo-cleanup-button"
          type="button"
          disabled={loading || mutating}
          onClick={openConfirmation}
        >
          <Trash2 size={18} aria-hidden="true" />
          Limpar dados de exemplo
        </button>
      ) : null}
      {feedback}
      {dialog}
    </section>
  );
}
