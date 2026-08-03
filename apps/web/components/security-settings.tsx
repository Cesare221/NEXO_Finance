"use client";

import { LoaderCircle, LogOut, MonitorSmartphone, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

type UserSession = {
  id: number;
  device_name: string | null;
  created_at: string;
  last_used_at: string;
  expires_at: string;
};

const dateTime = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

export function SecuritySettings() {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [revoking, setRevoking] = useState<number | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/auth/sessions", { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível carregar as sessões.");
      setSessions(await response.json() as UserSession[]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível carregar as sessões.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function revoke(sessionId: number) {
    setRevoking(sessionId);
    setError("");
    try {
      const response = await fetch(`/api/auth/sessions/${sessionId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Não foi possível encerrar esta sessão.");
      setSessions((current) => current.filter((session) => session.id !== sessionId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível encerrar esta sessão.");
    } finally {
      setRevoking(null);
    }
  }

  return (
    <section className="card security-settings" aria-labelledby="security-settings-title">
      <div className="settings-section-heading security-settings-heading">
        <div>
          <span className="section-kicker">Segurança</span>
          <h2 id="security-settings-title">Sessões ativas</h2>
          <p>Revise os dispositivos conectados e encerre acessos que não reconhecer.</p>
        </div>
        <button className="icon-button" type="button" aria-label="Atualizar sessões" title="Atualizar" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={loading ? "spin" : ""} size={18} />
        </button>
      </div>
      {loading ? <p className="security-loading"><LoaderCircle className="spin" size={18} /> Carregando sessões.</p> : null}
      {!loading && !sessions.length ? <p className="security-loading">Nenhuma sessão ativa encontrada.</p> : null}
      <div className="session-list">
        {sessions.map((session) => (
          <div className="session-row" key={session.id}>
            <MonitorSmartphone size={21} aria-hidden="true" />
            <div>
              <strong>{session.device_name ?? "Dispositivo não identificado"}</strong>
              <span>Último uso em {dateTime.format(new Date(session.last_used_at))}</span>
            </div>
            <button className="icon-button" type="button" aria-label={`Encerrar sessão em ${session.device_name ?? "dispositivo"}`} title="Encerrar sessão" onClick={() => void revoke(session.id)} disabled={revoking === session.id}>
              {revoking === session.id ? <LoaderCircle className="spin" size={18} /> : <LogOut size={18} />}
            </button>
          </div>
        ))}
      </div>
      {error ? <p className="error" role="alert">{error}</p> : null}
    </section>
  );
}
