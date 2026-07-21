"use client";

import { Eye, EyeOff, LoaderCircle, LockKeyhole } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

type AuthFormProps = {
  mode: "login" | "register";
  redirectTo: string;
};

export function AuthForm({ mode, redirectTo }: AuthFormProps) {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    const formData = new FormData(event.currentTarget);
    const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
    const payload = {
      ...(isRegister ? { name: String(formData.get("name") ?? "").trim() } : {}),
      email: String(formData.get("email") ?? "").trim(),
      password: String(formData.get("password") ?? "")
    };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: unknown };

      if (!response.ok) {
        setError(
          typeof body.detail === "string"
            ? body.detail
            : "Não foi possível continuar. Confira os dados e tente novamente."
        );
        return;
      }

      router.replace(redirectTo);
      router.refresh();
    } catch {
      setError("Não foi possível conectar ao Fin. Verifique sua internet e tente novamente.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="form auth-form" onSubmit={handleSubmit} noValidate={false}>
      {isRegister && (
        <div className="field">
          <label htmlFor="name">Nome</label>
          <input
            className="input"
            id="name"
            name="name"
            autoComplete="name"
            required
            maxLength={255}
          />
        </div>
      )}

      <div className="field">
        <label htmlFor="email">E-mail</label>
        <input
          className="input"
          id="email"
          name="email"
          type="email"
          inputMode="email"
          autoComplete="email"
          required
          autoFocus
        />
      </div>

      <div className="field">
        <label htmlFor="password">Senha</label>
        <div className="password-field">
          <input
            className="input"
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete={isRegister ? "new-password" : "current-password"}
            minLength={isRegister ? 12 : undefined}
            maxLength={128}
            aria-describedby={isRegister ? "password-help" : undefined}
            required
          />
          <button
            className="password-toggle"
            type="button"
            aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
            aria-pressed={showPassword}
            onClick={() => setShowPassword((visible) => !visible)}
          >
            {showPassword ? <EyeOff size={19} aria-hidden="true" /> : <Eye size={19} aria-hidden="true" />}
          </button>
        </div>
        {isRegister && (
          <span className="field-help" id="password-help">
            Use pelo menos 12 caracteres.
          </span>
        )}
      </div>

      <div className="auth-feedback" aria-live="polite">
        {error && <p className="error" role="alert">{error}</p>}
      </div>

      <button className="button auth-submit" type="submit" disabled={pending}>
        {pending ? (
          <>
            <LoaderCircle className="spin" size={18} aria-hidden="true" />
            Aguarde...
          </>
        ) : (
          <>
            <LockKeyhole size={18} aria-hidden="true" />
            {isRegister ? "Criar conta" : "Entrar"}
          </>
        )}
      </button>
    </form>
  );
}
