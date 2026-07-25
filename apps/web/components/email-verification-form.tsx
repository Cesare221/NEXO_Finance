"use client";

import { CheckCircle2, LoaderCircle, Mail } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

export function EmailVerificationForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const emailParam = searchParams.get("email");

  const [email, setEmail] = useState(emailParam ?? "");
  const [pendingConfirm, setPendingConfirm] = useState(Boolean(token));
  const [pendingRequest, setPendingRequest] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!token) return;

    let mounted = true;
    async function confirmToken() {
      try {
        const response = await fetch("/api/auth/email-verification/confirm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token })
        });
        const body = (await response.json().catch(() => ({}))) as { detail?: unknown; message?: string };

        if (!mounted) return;

        if (!response.ok) {
          setErrorMessage(
            typeof body.detail === "string"
              ? body.detail
              : "Link de verificação inválido ou expirado. Solicite um novo e-mail."
          );
        } else {
          setSuccessMessage(body.message ?? "E-mail verificado com sucesso. Você já pode entrar.");
        }
      } catch {
        if (mounted) {
          setErrorMessage("Não foi possível conectar ao servidor. Tente novamente.");
        }
      } finally {
        if (mounted) setPendingConfirm(false);
      }
    }

    confirmToken();
    return () => {
      mounted = false;
    };
  }, [token]);

  async function handleResend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPendingRequest(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch("/api/auth/email-verification/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: unknown; message?: string };

      if (!response.ok) {
        setErrorMessage(
          typeof body.detail === "string" ? body.detail : "Não foi possível enviar a solicitação."
        );
      } else {
        setSuccessMessage(
          body.message ?? "Se o e-mail estiver cadastrado, as instruções foram enviadas."
        );
      }
    } catch {
      setErrorMessage("Erro de conexão. Tente novamente em instantes.");
    } finally {
      setPendingRequest(false);
    }
  }

  return (
    <div className="verification-container">
      {pendingConfirm && (
        <div className="status-banner info" aria-live="polite">
          <LoaderCircle className="spin" size={20} aria-hidden="true" />
          <span>Verificando seu e-mail...</span>
        </div>
      )}

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
        <form className="form auth-form" onSubmit={handleResend}>
          <p className="form-description">
            Confira sua caixa de entrada e clique no link de confirmação enviado pelo Nexo. Se não recebeu, informe seu e-mail para reenviar.
          </p>

          <div className="field">
            <label htmlFor="resend-email">Seu e-mail</label>
            <input
              className="input"
              id="resend-email"
              type="email"
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <button className="button auth-submit" type="submit" disabled={pendingRequest || !email.trim()}>
            {pendingRequest ? (
              <>
                <LoaderCircle className="spin" size={18} aria-hidden="true" />
                Enviando...
              </>
            ) : (
              <>
                <Mail size={18} aria-hidden="true" />
                Reenviar e-mail de verificação
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
