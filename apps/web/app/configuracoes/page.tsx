import { AppShell } from "@/components/app-shell";
import { InstallAppButton } from "@/components/install-app-button";
import { ProfileSettings } from "@/components/profile-settings";

export default function ConfiguracoesPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <h1>Configurações</h1>
          <p>Preferências de conta, segurança e variáveis operacionais.</p>
        </div>
      </header>
      <div className="settings-stack">
        <ProfileSettings />
        <section className="card settings-info-panel">
          <div>
            <h2>Segurança</h2>
            <p>As operações do Fin exigem confirmação autenticada e são registradas para auditoria.</p>
          </div>
        </section>
        <section className="card install-panel">
          <div>
            <h2>Nexo no seu dispositivo</h2>
            <p>Instale o aplicativo para abrir em tela cheia e ter acesso ao modo offline.</p>
          </div>
          <InstallAppButton />
        </section>
      </div>
    </AppShell>
  );
}
