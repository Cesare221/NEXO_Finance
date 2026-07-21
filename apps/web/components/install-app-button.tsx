"use client";

import { Download } from "lucide-react";
import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function InstallAppButton() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [message, setMessage] = useState("");
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const standalone = window.matchMedia("(display-mode: standalone)").matches;
    setInstalled(standalone);

    const capturePrompt = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as BeforeInstallPromptEvent);
    };

    const markInstalled = () => {
      setInstalled(true);
      setInstallPrompt(null);
      setMessage("Fin instalado neste dispositivo.");
    };

    window.addEventListener("beforeinstallprompt", capturePrompt);
    window.addEventListener("appinstalled", markInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", capturePrompt);
      window.removeEventListener("appinstalled", markInstalled);
    };
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) {
      setMessage("Abra o menu do navegador e escolha “Adicionar à tela inicial” ou “Instalar app”.");
      return;
    }

    await installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    setInstallPrompt(null);
    setMessage(choice.outcome === "accepted" ? "Instalação iniciada." : "Instalação cancelada.");
  };

  return (
    <div>
      <button className="button secondary" type="button" onClick={handleInstall} disabled={installed}>
        <Download size={18} aria-hidden="true" />
        {installed ? "App instalado" : installPrompt ? "Instalar aplicativo" : "Como instalar"}
      </button>
      <div aria-live="polite" className="metric-label" style={{ marginTop: 8 }}>
        {message}
      </div>
    </div>
  );
}
