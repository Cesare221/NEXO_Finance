"use client";

import { CheckCircle2, LoaderCircle, Mail } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";

export function PasswordRecoveryForm() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch("/api/auth/password-reset/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: unknown; message?: string };

      if (!response.ok) {
        setErrorMessage(
          typeof body.detail === "string" ? body.detail : "Não foi possível processar a solicitação."
        );
      } else {
        setSuccessMessage(
          body.message ?? "Se o e-mail estiver cadastrado, as instruções de redefinição foram enviadas."
        );
      }
    } catch {
      setErrorMessage("Erro de conexão. Tente novamente em instantes.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="recovery-container">
      <div className="auth-feedback" aria-live="polite">
        {successMessage && (
          <div className="status-banner success" role="status">
            <CheckCircle2 size={20} aria-hidden="true" />
            <p>{successMessage}</p>
          </div>
        )}
        {errorMessage && <p className="error" role="alert">{errorMessage}</p>}
      </div>

      {!successMessage && (
        <form className="form auth-form" onSubmit={handleSubmit}>
          <p className="form-description">
            Informe o e-mail cadastrado em sua conta para receber as instruções e o link seguro de redefinição de senha.
          </p>

          <div className="field">
            <label htmlFor="recovery-email">Seu e-mail</label>
            <input
              className="input"
              id="recovery-email"
              type="email"
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <button className="button auth-submit" type="submit" disabled={pending || !email.trim()}>
            {pending ? (
              <>
                <LoaderCircle className="spin" size={18} aria-hidden="true" />
                Enviando...
              </>
            ) : (
              <>
                <Mail size={18} aria-hidden="true" />
                Enviar link de redefinição
              </>
            )}
          </button>
        </form>
      )}

      <div className="auth-footer-actions">
        <Link className="button secondary" href="/login">
          Voltar para o Login
        </Link>
      </div>
    </div>
  );
}
