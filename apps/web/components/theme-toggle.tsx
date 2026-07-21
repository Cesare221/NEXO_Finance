"use client";

import { Moon, Sun } from "lucide-react";
import { useState } from "react";
import { useSession } from "@/components/session-profile";
import { useTheme } from "@/components/theme-provider";

interface ThemeToggleProps {
  className?: string;
}

async function readError(response: Response) {
  const body = (await response.json().catch(() => null)) as { detail?: string } | null;
  return body?.detail ?? "Não foi possível salvar o tema.";
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { user, updateUser } = useSession();
  const { preference, resolvedTheme, setPreference } = useTheme();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const isDark = resolvedTheme === "dark";
  const label = isDark ? "Ativar tema claro" : "Ativar tema escuro";
  const classes = ["theme-toggle", isDark ? "is-dark" : "is-light", className]
    .filter(Boolean)
    .join(" ");

  async function toggleTheme() {
    if (saving) return;
    const nextPreference = isDark ? "light" : "dark";
    const previousPreference = preference;
    setSaving(true);
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
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar o tema.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <span className="theme-toggle-wrap">
      <button
        className={classes}
        type="button"
        aria-label={label}
        aria-pressed={isDark}
        title={label}
        disabled={saving}
        onClick={() => void toggleTheme()}
      >
        <span className="theme-toggle-track" aria-hidden="true">
          <Moon className="theme-toggle-icon theme-toggle-moon" size={15} strokeWidth={1.5} />
          <Sun className="theme-toggle-icon theme-toggle-sun" size={15} strokeWidth={1.5} />
          <span className="theme-toggle-thumb">
            {isDark ? <Moon size={15} strokeWidth={1.5} /> : <Sun size={15} strokeWidth={1.5} />}
          </span>
        </span>
      </button>
      <span className="sr-only" aria-live="polite">{error}</span>
    </span>
  );
}
