"use client";

import { CheckCircle2, Eye, EyeOff, LoaderCircle, LockKeyhole } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";

export function PasswordResetForm() {
  const searchParams = useSearchParams();
  const tokenParam = searchParams.get("token") ?? "";

  const [token, setToken] = useState(tokenParam);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    if (newPassword.length < 12) {
      setErrorMessage("A nova senha deve ter pelo menos 12 caracteres.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage("As senhas informadas não conferem.");
      return;
    }

    setPending(true);

    try {
      const response = await fetch("/api/auth/password-reset/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: token.trim(),
          new_password: newPassword
        })
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: unknown; message?: string };

      if (!response.ok) {
        setErrorMessage(
          typeof body.detail === "string" ? body.detail : "Não foi possível redefinir a senha. Verifique o token."
        );
      } else {
        setSuccessMessage(body.message ?? "Senha redefinida com sucesso. Faça login com sua nova senha.");
      }
    } catch {
      setErrorMessage("Erro de conexão. Tente novamente em instantes.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="reset-container">
      <div className="auth-feedback" aria-live="polite">
        {successMessage && (
          <div className="status-banner success" role="status">
            <CheckCircle2 size={20} aria-hidden="true" />
            <p>{successMessage}</p>
          </div>
        )}
        {errorMessage && <p className="error" role="alert">{errorMessage}</p>}
      </div>

      {!successMessage ? (
        <form className="form auth-form" onSubmit={handleSubmit}>
          {!tokenParam && (
            <div className="field">
              <label htmlFor="reset-token">Código ou Token de Redefinição</label>
              <input
                className="input"
                id="reset-token"
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="new-password">Nova Senha</label>
            <div className="password-field">
              <input
                className="input"
                id="new-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                aria-describedby="reset-password-help"
              />
              <button
                className="password-toggle"
                type="button"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                aria-pressed={showPassword}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff size={19} aria-hidden="true" /> : <Eye size={19} aria-hidden="true" />}
              </button>
            </div>
            <span className="field-help" id="reset-password-help">
              Use pelo menos 12 caracteres com letras, números e símbolos.
            </span>
          </div>

          <div className="field">
            <label htmlFor="confirm-password">Confirmar Nova Senha</label>
            <input
              className="input"
              id="confirm-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <button className="button auth-submit" type="submit" disabled={pending}>
            {pending ? (
              <>
                <LoaderCircle className="spin" size={18} aria-hidden="true" />
                Redefinindo...
              </>
            ) : (
              <>
                <LockKeyhole size={18} aria-hidden="true" />
                Redefinir Senha
              </>
            )}
          </button>
        </form>
      ) : (
        <div className="auth-footer-actions">
          <Link className="button primary" href="/login">
            Ir para o Login
          </Link>
        </div>
      )}
    </div>
  );
}
