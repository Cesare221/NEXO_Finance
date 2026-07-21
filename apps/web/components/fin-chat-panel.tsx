"use client";

import { FinConversation } from "@/components/fin-conversation";

export function FinChatPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

  return (
    <>
      <button className="fin-panel-scrim" type="button" aria-label="Fechar conversa com o Fin" onClick={onClose} />
      <aside className="fin-panel" aria-label="Painel do Fin">
        <FinConversation compact onClose={onClose} />
      </aside>
    </>
  );
}
