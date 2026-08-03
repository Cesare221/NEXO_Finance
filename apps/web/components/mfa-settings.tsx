"use client";

import { CheckCircle2, Download, Eye, EyeOff, LoaderCircle, QrCode, Shield, ShieldAlert, ShieldCheck } from "lucide-react";
import QRCode from "qrcode";
import { FormEvent, useEffect, useState } from "react";

type MfaStatus = {
  enabled: boolean;
  activated_at: string | null;
};

export function MfaSettings() {
  const [mfaStatus, setMfaStatus] = useState<MfaStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState<"idle" | "enroll_password" | "confirming" | "show_recovery" | "disable_confirm">("idle");

  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [totpSecret, setTotpSecret] = useState("");
  const [qrCodeUrl, setQrCodeUrl] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [acknowledged, setAcknowledged] = useState(false);

  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      const response = await fetch("/api/auth/mfa/status");
      if (response.ok) {
        const data = await response.json();
        setMfaStatus(data);
      }
    } catch {
      setError("Não foi possível carregar o status do MFA.");
    } finally {
      setLoading(false);
    }
  }

  async function handleStartEnroll(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await fetch("/api/auth/mfa/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });
      const body = await response.json();

      if (!response.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Senha incorreta.");
        return;
      }

      setTotpSecret(body.secret);
      const url = await QRCode.toDataURL(body.otpauth_uri, {
        errorCorrectionLevel: "M",
        margin: 1,
        width: 224
      });
      setQrCodeUrl(url);
      setStep("confirming");
      setPassword("");
    } catch {
      setError("Erro ao iniciar configuração do MFA.");
    } finally {
      setPending(false);
    }
  }

  async function handleConfirmEnroll(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await fetch("/api/auth/mfa/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: totpCode.trim() })
      });
      const body = await response.json();

      if (!response.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Código TOTP inválido.");
        return;
      }

      setRecoveryCodes(body.recovery_codes ?? []);
      setStep("show_recovery");
      setTotpCode("");
      await fetchStatus();
    } catch {
      setError("Erro ao confirmar código TOTP.");
    } finally {
      setPending(false);
    }
  }

  async function handleRegenerateCodes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await fetch("/api/auth/mfa/recovery-codes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });
      const body = await response.json();

      if (!response.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Senha incorreta.");
        return;
      }

      setRecoveryCodes(body.recovery_codes ?? []);
      setStep("show_recovery");
      setPassword("");
    } catch {
      setError("Erro ao regenerar códigos de recuperação.");
    } finally {
      setPending(false);
    }
  }

  async function handleDisableMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");

    try {
      const response = await fetch("/api/auth/mfa", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, code: totpCode.trim() })
      });
      const body = await response.json();

      if (!response.ok) {
        setError(typeof body.detail === "string" ? body.detail : "Senha ou código incorreto.");
        return;
      }

      setNotice("Autenticação em duas etapas desativada.");
      setStep("idle");
      setPassword("");
      setTotpCode("");
      await fetchStatus();
    } catch {
      setError("Erro ao desativar o MFA.");
    } finally {
      setPending(false);
    }
  }

  function downloadRecoveryCodes() {
    const text = `Nexo - Códigos de Recuperação MFA\nGuardado em: ${new Date().toLocaleString("pt-BR")}\n\n` +
      recoveryCodes.join("\n") +
      `\n\nATENÇÃO: Cada código pode ser utilizado apenas uma vez. Mantenha em local seguro.`;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "nexo-codigos-recuperacao.txt";
    link.click();
    URL.revokeObjectURL(url);
  }

  if (loading) {
    return (
      <section className="card settings-card">
        <div className="status-banner info">Carregando configurações de segurança.</div>
      </section>
    );
  }

  const isEnabled = mfaStatus?.enabled ?? false;

  return (
    <section className="card settings-card mfa-settings-panel">
      <div className="settings-card-header">
        <div className="mfa-icon-badge">
          {isEnabled ? <ShieldCheck size={24} className="text-primary" /> : <ShieldAlert size={24} />}
        </div>
        <div>
          <h2>Autenticação em duas etapas (MFA)</h2>
          <p>
            {isEnabled
              ? "Sua conta está protegida por verificação em duas etapas via aplicativo autenticador."
              : "Adicione uma camada extra de proteção à sua conta exigindo um código do celular ao entrar."}
          </p>
        </div>
      </div>

      <div className="auth-feedback" aria-live="polite">
        {notice && <p className="success" role="status">{notice}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </div>

      {step === "idle" && (
        <div className="mfa-actions-row">
          {!isEnabled ? (
            <button className="button primary" type="button" onClick={() => setStep("enroll_password")}>
              <Shield size={18} aria-hidden="true" />
              Ativar Proteção MFA
            </button>
          ) : (
            <div className="mfa-enabled-controls">
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  setStep("enroll_password");
                  setError("");
                }}
              >
                Gerar novos códigos de recuperação
              </button>
              <button
                className="button danger"
                type="button"
                onClick={() => {
                  setStep("disable_confirm");
                  setError("");
                }}
              >
                Desativar MFA
              </button>
            </div>
          )}
        </div>
      )}

      {step === "enroll_password" && (
        <form className="form auth-form step-up-form" onSubmit={isEnabled ? handleRegenerateCodes : handleStartEnroll}>
          <p className="form-description">
            Informe sua senha atual para continuar a {isEnabled ? "geração de novos códigos" : "configuração do MFA"}.
          </p>
          <div className="field">
            <label htmlFor="mfa-password">Sua Senha Atual</label>
            <div className="password-field">
              <input
                className="input"
                id="mfa-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoFocus
              />
              <button
                className="password-toggle"
                type="button"
                aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
              </button>
            </div>
          </div>
          <div className="button-group">
            <button className="button primary" type="submit" disabled={pending || !password}>
              {pending ? <LoaderCircle className="spin" size={18} /> : "Continuar"}
            </button>
            <button className="button secondary" type="button" onClick={() => setStep("idle")}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {step === "confirming" && (
        <div className="mfa-setup-flow">
          <div className="mfa-qr-container">
            {qrCodeUrl ? (
              <img className="mfa-qr-code" src={qrCodeUrl} alt="QR Code para escaneamento no aplicativo autenticador" />
            ) : (
              <div className="qr-placeholder"><QrCode size={48} /></div>
            )}
            <div className="mfa-manual-key">
              <span className="field-help">Chave secreta manual:</span>
              <code className="secret-code">{totpSecret}</code>
            </div>
          </div>

          <form className="form auth-form" onSubmit={handleConfirmEnroll}>
            <div className="field">
              <label htmlFor="totp-code">Digite o código de 6 dígitos para confirmar</label>
              <input
                className="input mfa-code-input"
                id="totp-code"
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder="000000"
                required
                autoFocus
              />
            </div>
            <div className="button-group">
              <button className="button primary" type="submit" disabled={pending || totpCode.length < 6}>
                {pending ? <LoaderCircle className="spin" size={18} /> : "Ativar MFA"}
              </button>
              <button className="button secondary" type="button" onClick={() => setStep("idle")}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {step === "show_recovery" && (
        <div className="mfa-recovery-codes-panel">
          <p className="form-description">
            Guarde estes 10 códigos de recuperação em local seguro. Se perder seu celular, eles serão a única forma de acessar sua conta.
          </p>

          <ul className="recovery-codes-grid">
            {recoveryCodes.map((code, idx) => (
              <li key={idx} className="recovery-code-item">
                <code>{code}</code>
              </li>
            ))}
          </ul>

          <div className="recovery-actions">
            <button className="button secondary" type="button" onClick={downloadRecoveryCodes}>
              <Download size={18} aria-hidden="true" />
              Baixar códigos (.txt)
            </button>
          </div>

          <label className="checkbox-row acknowledge-row">
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
            />
            <span>Entendi e já guardei meus códigos de recuperação com segurança.</span>
          </label>

          <button
            className="button primary"
            type="button"
            disabled={!acknowledged}
            onClick={() => {
              setStep("idle");
              setRecoveryCodes([]);
              setNotice("Autenticação em duas etapas configurada e ativa!");
            }}
          >
            Concluir
          </button>
        </div>
      )}

      {step === "disable_confirm" && (
        <form className="form auth-form" onSubmit={handleDisableMfa}>
          <p className="form-description">
            Para desativar o MFA, informe sua senha e o código de 6 dígitos do app (ou um código de recuperação).
          </p>
          <div className="field">
            <label htmlFor="disable-password">Sua Senha</label>
            <input
              className="input"
              id="disable-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="disable-code">Código TOTP ou de Recuperação</label>
            <input
              className="input"
              id="disable-code"
              type="text"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              required
            />
          </div>
          <div className="button-group">
            <button className="button danger" type="submit" disabled={pending || !password || !totpCode}>
              {pending ? <LoaderCircle className="spin" size={18} /> : "Confirmar Desativação"}
            </button>
            <button className="button secondary" type="button" onClick={() => setStep("idle")}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
