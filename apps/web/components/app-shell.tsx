"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, MessageSquareText } from "lucide-react";
import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { NexoMark } from "@/components/brand-assets";
import { FinChatPanel } from "@/components/fin-chat-panel";
import { NavigationDrawer } from "@/components/navigation-drawer";
import { PendingProposalsProvider, usePendingProposals } from "@/components/pending-proposals-provider";
import { SessionProfile, SessionProvider } from "@/components/session-profile";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/contas": "Contas",
  "/cartoes": "Cartões",
  "/transacoes": "Transações",
  "/categorias": "Categorias",
  "/fin": "Conversas",
  "/configuracoes": "Configurações",
  "/onboarding": "Primeiros passos"
};

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <PendingProposalsProvider>
        <AppShellContent>{children}</AppShellContent>
      </PendingProposalsProvider>
    </SessionProvider>
  );
}

function AppShellContent({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { proposals } = usePendingProposals();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const pageTitle = pageTitles[pathname] ?? "Nexo";

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const closeChat = useCallback(() => setChatOpen(false), []);

  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 1180px)");
    setChatOpen(desktop.matches || pathname === "/fin");
  }, [pathname]);

  useEffect(() => {
    const openChat = () => setChatOpen(true);
    window.addEventListener("nexo:open-fin", openChat);
    return () => window.removeEventListener("nexo:open-fin", openChat);
  }, []);

  return (
    <div className={chatOpen ? "app-shell chat-visible" : "app-shell"}>
      <a className="skip-link" href="#main-content">Ir para o conteúdo</a>

      <header className="app-topbar">
        <button ref={menuButtonRef} className="topbar-icon" type="button" aria-label="Menu principal" aria-expanded={drawerOpen} onClick={() => setDrawerOpen(true)}>
          <Menu size={21} aria-hidden="true" />
        </button>
        <Link className="topbar-brand" href="/dashboard" aria-label="Nexo, ir para o dashboard">
          <NexoMark priority />
          <strong>Nexo</strong>
        </Link>
        <span className="topbar-separator" aria-hidden="true" />
        <span className="topbar-page-title">{pageTitle}</span>
        <div className="topbar-actions">
          <button className={chatOpen ? "topbar-icon active" : "topbar-icon"} type="button" aria-label={chatOpen ? "Fechar conversa com o Fin" : "Abrir conversa com o Fin"} aria-pressed={chatOpen} onClick={() => setChatOpen((open) => !open)}>
            <MessageSquareText size={20} aria-hidden="true" />
            {proposals.length ? <span className="topbar-badge">{proposals.length}</span> : null}
          </button>
          <SessionProfile compact />
        </div>
      </header>

      <NavigationDrawer open={drawerOpen} onClose={closeDrawer} triggerRef={menuButtonRef} pendingCount={proposals.length} />

      <div className="app-workspace">
        <main className="main" id="main-content" tabIndex={-1}>
          <div className="main-inner">{children}</div>
        </main>
        <FinChatPanel open={chatOpen} onClose={closeChat} />
      </div>
    </div>
  );
}
