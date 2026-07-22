"use client";

import { Bot, Download, LoaderCircle, ShieldCheck, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useSession } from "@/components/session-profile";

async function errorMessage(response: Response) {
  const body = await response.json().catch(() => ({})) as { detail?: string };
  return body.detail ?? "Não foi possível concluir a solicitação.";
}

export function PrivacySettings() {
  const router = useRouter();
  const { user, updateUser } = useSession();
  const [consent, setConsent] = useState(user.ai_data_processing_consent);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");

  async function saveConsent() {
    setSaving(true);
    setError("");
    setFeedback("");
    try {
      const response = await fetch("/api/auth/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ai_data_processing_consent: consent })
      });
      if (!response.ok) throw new Error(await errorMessage(response));
      const updated = await response.json() as typeof user;
      updateUser(updated);
      setFeedback(consent ? "Uso da IA externa autorizado." : "Consentimento revogado. O Fin usará o modo local.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível salvar.");
    } finally {
      setSaving(false);
    }
  }

  async function exportData() {
    setExporting(true);
    setError("");
    try {
      const response = await fetch("/api/auth/data-export", { cache: "no-store" });
      if (!response.ok) throw new Error(await errorMessage(response));
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `nexo-meus-dados-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      setFeedback("Arquivo de dados preparado.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível exportar os dados.");
    } finally {
      setExporting(false);
    }
  }

  async function deleteAccount(event: FormEvent) {
    event.preventDefault();
    if (confirmation !== "EXCLUIR") {
      setError("Digite EXCLUIR para confirmar.");
      return;
    }
    setDeleting(true);
    setError("");
    try {
      const response = await fetch("/api/auth/account", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });
      if (!response.ok) throw new Error(await errorMessage(response));
      router.replace("/login");
      router.refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível excluir a conta.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <section className="card privacy-settings" aria-labelledby="privacy-settings-title">
      <div className="settings-section-heading">
        <div>
          <span className="section-kicker">Privacidade e LGPD</span>
          <h2 id="privacy-settings-title">Controle dos seus dados</h2>
          <p>Escolha como seus dados são processados, exporte uma cópia ou exclua sua conta.</p>
        </div>
        <ShieldCheck size={24} aria-hidden="true" />
      </div>

      <div className="privacy-control-row">
        <Bot size={22} aria-hidden="true" />
        <div>
          <strong>Processamento pelo Fin com Groq</strong>
          <span>Somente o contexto necessário é enviado. Operações continuam exigindo aprovação.</span>
        </div>
        <label className="switch-control">
          <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
          <span aria-hidden="true" />
          <span className="sr-only">Autorizar processamento por IA externa</span>
        </label>
        <button className="button secondary" type="button" disabled={saving || consent === user.ai_data_processing_consent} onClick={() => void saveConsent()}>
          {saving ? <LoaderCircle className="spin" size={17} /> : null} Salvar
        </button>
      </div>

      <div className="privacy-actions">
        <div>
          <strong>Portabilidade</strong>
          <span>Baixe seus dados financeiros e registros de auditoria em JSON.</span>
        </div>
        <button className="button secondary" type="button" disabled={exporting} onClick={() => void exportData()}>
          {exporting ? <LoaderCircle className="spin" size={17} /> : <Download size={17} />} Exportar dados
        </button>
      </div>

      <form className="privacy-delete" onSubmit={deleteAccount}>
        <div>
          <strong>Excluir conta permanentemente</strong>
          <span>Esta ação remove seu perfil e os dados financeiros associados.</span>
        </div>
        <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Senha atual" autoComplete="current-password" required />
        <input className="input" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder="Digite EXCLUIR" required />
        <button className="button danger" type="submit" disabled={deleting || confirmation !== "EXCLUIR"}>
          {deleting ? <LoaderCircle className="spin" size={17} /> : <Trash2 size={17} />} Excluir conta
        </button>
      </form>
      <div className="resource-feedback" aria-live="polite">
        {error ? <p className="error" role="alert">{error}</p> : null}
        {feedback ? <p className="success-message">{feedback}</p> : null}
      </div>
    </section>
  );
}
