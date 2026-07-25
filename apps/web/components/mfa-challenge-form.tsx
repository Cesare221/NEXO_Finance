"use client";

import { LoaderCircle, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

type MfaChallengeFormProps = {
  redirectTo: string;
};

export function MfaChallengeForm({ redirectTo }: MfaChallengeFormProps) {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [isRecoveryMode, setIsRecoveryMode] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await fetch("/api/auth/mfa/challenge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code.trim() })
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: unknown };

      if (!response.ok) {
        setError(
          typeof body.detail === "string"
            ? body.detail
            : "Código de verificação incorreto ou expirado."
        );
        return;
      }

      router.replace(redirectTo);
      router.refresh();
    } catch {
      setError("Erro de conexão. Tente novamente em instantes.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="form auth-form" onSubmit={handleSubmit}>
      <p className="form-description">
        {isRecoveryMode
          ? "Informe um dos seus códigos de recuperação únicos guardados durante a ativação."
          : "Digite o código de 6 dígitos gerado pelo seu aplicativo autenticador (Google Authenticator, Authy, 1Password, etc.)."}
      </p>

      <div className="field">
        <label htmlFor="mfa-code">
          {isRecoveryMode ? "Código de Recuperação" : "Código de Verificação (TOTP)"}
        </label>
        <input
          className="input mfa-code-input"
          id="mfa-code"
          type="text"
          inputMode={isRecoveryMode ? "text" : "numeric"}
          autoComplete="one-time-code"
          maxLength={isRecoveryMode ? 32 : 6}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder={isRecoveryMode ? "ABCD-EFGH" : "000000"}
          required
          autoFocus
        />
      </div>

      <div className="field-footer">
        <button
          className="button link-button"
          type="button"
          onClick={() => {
            setIsRecoveryMode((prev) => !prev);
            setCode("");
            setError("");
          }}
        >
          {isRecoveryMode ? "Usar código de 6 dígitos do app" : "Usar código de recuperação"}
        </button>
      </div>

      <div className="auth-feedback" aria-live="polite">
        {error && <p className="error" role="alert">{error}</p>}
      </div>

      <button className="button auth-submit" type="submit" disabled={pending || !code.trim()}>
        {pending ? (
          <>
            <LoaderCircle className="spin" size={18} aria-hidden="true" />
            Validando...
          </>
        ) : (
          <>
            <ShieldCheck size={18} aria-hidden="true" />
            Verificar e Entrar
          </>
        )}
      </button>
    </form>
  );
}
