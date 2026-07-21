"use client";

import { LogOut, RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

type SessionUser = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  avatar_data_url: string | null;
};

type SessionContextValue = {
  user: SessionUser;
  logout: () => Promise<void>;
  updateUser: (user: SessionUser) => void;
  loggingOut: boolean;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);
  const [networkError, setNetworkError] = useState(false);

  const loadSession = useCallback(async () => {
    setLoading(true);
    setNetworkError(false);
    try {
      const response = await fetch("/api/auth/session", { cache: "no-store" });
      if (response.status === 401) {
        router.replace(`/login?next=${encodeURIComponent(window.location.pathname)}`);
        return;
      }
      if (!response.ok) throw new Error("session_unavailable");
      const body = (await response.json()) as { user: SessionUser };
      setUser(body.user);
    } catch {
      setNetworkError(true);
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const logout = useCallback(async () => {
    setLoggingOut(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.replace("/login");
      router.refresh();
      setLoggingOut(false);
    }
  }, [router]);

  const updateUser = useCallback((nextUser: SessionUser) => {
    setUser(nextUser);
  }, []);

  const value = useMemo(
    () => (user ? { user, logout, updateUser, loggingOut } : null),
    [loggingOut, logout, updateUser, user]
  );

  if (loading || (!user && !networkError)) {
    return (
      <main className="session-state" aria-busy="true" aria-live="polite">
        <span className="session-loader" aria-hidden="true" />
        <p>Protegendo sua sessão...</p>
      </main>
    );
  }

  if (networkError || !value) {
    return (
      <main className="session-state" aria-live="polite">
        <p>Não foi possível validar sua sessão agora.</p>
        <button className="button secondary" type="button" onClick={() => void loadSession()}>
          <RotateCcw size={18} aria-hidden="true" />
          Tentar novamente
        </button>
      </main>
    );
  }

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) throw new Error("SessionProfile must be used inside SessionProvider");
  return context;
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "FN";
}

export function SessionProfile({ compact = false }: { compact?: boolean }) {
  const { user, logout, loggingOut } = useSession();
  const userInitials = initials(user.name);

  if (compact) {
    return (
      <span className="avatar" aria-label={`Conta de ${user.name}`} title={user.name}>
        {user.avatar_data_url ? (
          <img className="profile-avatar-image" src={user.avatar_data_url} alt="" />
        ) : userInitials}
      </span>
    );
  }

  return (
    <div className="session-profile">
      <span className="avatar" aria-hidden="true">
        {user.avatar_data_url ? (
          <img className="profile-avatar-image" src={user.avatar_data_url} alt="" />
        ) : userInitials}
      </span>
      <span className="profile-copy">
        <strong>{user.name}</strong>
        <span>{user.email}</span>
      </span>
      <button
        className="profile-logout"
        type="button"
        onClick={() => void logout()}
        disabled={loggingOut}
        aria-label="Sair da conta"
        title="Sair da conta"
      >
        <LogOut size={18} aria-hidden="true" />
      </button>
    </div>
  );
}
