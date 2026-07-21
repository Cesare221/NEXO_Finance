"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ActionProposal } from "@/components/proposal-card";

type ProposalAction = "confirm" | "cancel";

type PendingProposalsContextValue = {
  proposals: ActionProposal[];
  loading: boolean;
  error: string;
  refresh: () => Promise<void>;
  actOnProposal: (proposalId: number, action: ProposalAction) => Promise<void>;
};

const PendingProposalsContext = createContext<PendingProposalsContextValue | null>(null);

export function notifyProposalsChanged() {
  window.dispatchEvent(new Event("nexo:proposals-changed"));
}

export function PendingProposalsProvider({ children }: { children: ReactNode }) {
  const [proposals, setProposals] = useState<ActionProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setError("");
    try {
      const response = await fetch("/api/assistant/proposals?status=proposed", { cache: "no-store" });
      const body = (await response.json().catch(() => ([]))) as ActionProposal[] | { detail?: string };
      if (!response.ok || !Array.isArray(body)) {
        throw new Error(!Array.isArray(body) && body.detail ? body.detail : "Não foi possível carregar as movimentações reconhecidas.");
      }
      setProposals(body);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível carregar as movimentações reconhecidas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const listener = () => void refresh();
    window.addEventListener("nexo:proposals-changed", listener);
    return () => window.removeEventListener("nexo:proposals-changed", listener);
  }, [refresh]);

  const actOnProposal = useCallback(async (proposalId: number, action: ProposalAction) => {
    const response = await fetch(`/api/assistant/proposals/${proposalId}/${action}`, { method: "POST" });
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    if (!response.ok) throw new Error(body.detail ?? "Não foi possível revisar a movimentação.");
    setProposals((current) => current.filter((proposal) => proposal.id !== proposalId));
    if (action === "confirm") window.dispatchEvent(new Event("nexo:financial-data-changed"));
  }, []);

  const value = useMemo(
    () => ({ proposals, loading, error, refresh, actOnProposal }),
    [proposals, loading, error, refresh, actOnProposal]
  );

  return <PendingProposalsContext.Provider value={value}>{children}</PendingProposalsContext.Provider>;
}

export function usePendingProposals() {
  const context = useContext(PendingProposalsContext);
  if (!context) throw new Error("usePendingProposals must be used inside PendingProposalsProvider");
  return context;
}
