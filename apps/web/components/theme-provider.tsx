"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";
import {
  applyTheme,
  isThemePreference,
  THEME_STORAGE_KEY,
  ThemePreference
} from "@/lib/theme";

type ThemeContextValue = {
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>("system");

  const setPreference = useCallback((nextPreference: ThemePreference) => {
    setPreferenceState(nextPreference);
    applyTheme(nextPreference);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    const initialPreference = isThemePreference(stored) ? stored : "system";
    setPreferenceState(initialPreference);
    applyTheme(initialPreference);
  }, []);

  useEffect(() => {
    if (preference !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const syncSystemTheme = () => applyTheme("system");
    media.addEventListener("change", syncSystemTheme);
    return () => media.removeEventListener("change", syncSystemTheme);
  }, [preference]);

  const value = useMemo(
    () => ({ preference, setPreference }),
    [preference, setPreference]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used inside ThemeProvider");
  return context;
}
