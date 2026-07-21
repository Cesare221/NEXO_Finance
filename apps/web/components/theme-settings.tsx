"use client";

import { Laptop, LoaderCircle, Moon, Sun } from "lucide-react";
import { useState } from "react";
import { useSession } from "@/components/session-profile";
import { useTheme } from "@/components/theme-provider";
import type { ThemePreference } from "@/lib/theme";

const options: Array<{
  value: ThemePreference;
  label: string;
  description: string;
  icon: typeof Laptop;
}> = [
  {
    value: "system",
    label: "Sistema",
    description: "Acompanha este dispositivo",
    icon: Laptop
  },
  { value: "light", label: "Claro", description: "Maior luminosidade", icon: Sun },
  { value: "dark", label: "Escuro", description: "Petr\u00f3leo Nexo", icon: Moon }
];

async function readError(response: Response) {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail ?? "N\u00e3o foi poss\u00edvel salvar o tema.";
}

export function ThemeSettings() {
  const { user, updateUser } = useSession();
  const { preference, setPreference } = useTheme();
  const [saving, setSaving] = useState<ThemePreference | null>(null);
  const [error, setError] = useState("");

  async function chooseTheme(nextPreference: ThemePreference) {
    if (saving || nextPreference === preference) return;
    const previousPreference = preference;
    setSaving(nextPreference);
    setError("");
    setPreference(nextPreference);
    try {
      const response = await fetch("/api/auth/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme_preference: nextPreference })
      });
      if (!response.ok) throw new Error(await readError(response));
      const updatedUser = (await response.json()) as typeof user;
      updateUser(updatedUser);
    } catch (saveError) {
      setPreference(previousPreference);
      setError(
        saveError instanceof Error
          ? saveError.message
          : "N\u00e3o foi poss\u00edvel salvar o tema."
      );
    } finally {
      setSaving(null);
    }
  }

  return (
    <section className="card theme-settings" aria-labelledby="theme-settings-title">
      <div className="settings-section-heading">
        <div>
          <span className="section-kicker">{"Apar\u00eancia"}</span>
          <h2 id="theme-settings-title">Tema do Nexo</h2>
          <p>{"Escolha como o aplicativo aparece neste e nos pr\u00f3ximos acessos."}</p>
        </div>
      </div>

      <div className="theme-segmented-control" role="group" aria-label="Tema do aplicativo">
        {options.map((option) => {
          const Icon = option.icon;
          const active = preference === option.value;
          const loading = saving === option.value;
          return (
            <button
              key={option.value}
              className={active ? "theme-option active" : "theme-option"}
              type="button"
              aria-pressed={active}
              disabled={saving !== null}
              onClick={() => void chooseTheme(option.value)}
            >
              {loading ? (
                <LoaderCircle className="spin" size={20} aria-hidden="true" />
              ) : (
                <Icon size={20} aria-hidden="true" />
              )}
              <span>
                <strong>{option.label}</strong>
                <small>{option.description}</small>
              </span>
            </button>
          );
        })}
      </div>
      <div className="resource-feedback theme-feedback" aria-live="polite">
        {error ? <p className="error">{error}</p> : null}
      </div>
    </section>
  );
}
