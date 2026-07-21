"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { RefObject, useEffect, useRef } from "react";
import {
  ArrowRightLeft,
  Bot,
  CreditCard,
  FolderTree,
  Inbox,
  LayoutDashboard,
  Settings,
  Wallet,
  X
} from "lucide-react";
import { SessionProfile } from "@/components/session-profile";
import { NexoLogo } from "@/components/brand-assets";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/contas", label: "Contas", icon: Wallet },
  { href: "/cartoes", label: "Cartões", icon: CreditCard },
  { href: "/transacoes", label: "Transações", icon: ArrowRightLeft },
  { href: "/categorias", label: "Categorias", icon: FolderTree },
  { href: "/fin", label: "Conversas com o Fin", icon: Bot },
  { href: "/configuracoes", label: "Configurações", icon: Settings }
];

type NavigationDrawerProps = {
  open: boolean;
  onClose: () => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
  pendingCount: number;
};

export function NavigationDrawer({ open, onClose, triggerRef, pendingCount }: NavigationDrawerProps) {
  const pathname = usePathname();
  const drawerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const firstFocusable = drawerRef.current?.querySelector<HTMLElement>("button, a[href]");
    firstFocusable?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !drawerRef.current) return;
      const focusable = [...drawerRef.current.querySelectorAll<HTMLElement>("button:not([disabled]), a[href]")];
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
      triggerRef.current?.focus();
    };
  }, [onClose, open, triggerRef]);

  if (!open) return null;

  return (
    <>
      <button className="drawer-scrim" type="button" aria-label="Fechar menu" onClick={onClose} />
      <aside ref={drawerRef} className="navigation-drawer" role="dialog" aria-modal="true" aria-labelledby="navigation-title">
        <div className="drawer-header">
          <Link className="drawer-brand" href="/dashboard" onClick={onClose}>
            <NexoLogo />
            <span className="sr-only" id="navigation-title">Nexo</span>
          </Link>
          <button className="icon-button" type="button" aria-label="Fechar menu" onClick={onClose}><X size={20} aria-hidden="true" /></button>
        </div>

        <nav className="drawer-nav" aria-label="Navegação principal">
          {links.map((link) => {
            const Icon = link.icon;
            const active = pathname === link.href;
            return (
              <Link className={active ? "drawer-link active" : "drawer-link"} href={link.href} key={link.href} aria-current={active ? "page" : undefined} onClick={onClose}>
                <Icon size={19} aria-hidden="true" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <Link className="drawer-review-link" href="/dashboard#movement-inbox-title" onClick={onClose}>
          <Inbox size={19} aria-hidden="true" />
          <span>Revisar movimentações</span>
          {pendingCount ? <span className="nav-badge" aria-label={`${pendingCount} movimentações pendentes`}>{pendingCount}</span> : null}
        </Link>

        <SessionProfile />
      </aside>
    </>
  );
}
