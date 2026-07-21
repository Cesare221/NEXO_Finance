import { AppShell } from "@/components/app-shell";

export default function OnboardingPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <h1>Onboarding</h1>
          <p>Configure a primeira conta, categoria e cartão para começar.</p>
        </div>
      </header>
      <section className="grid cols-2">
        <article className="card">
          <h2>Primeira conta</h2>
          <p>Cadastre sua conta corrente ou carteira com saldo inicial.</p>
        </article>
        <article className="card">
          <h2>Categorias base</h2>
          <p>Organize alimentação, moradia, transporte e renda.</p>
        </article>
      </section>
    </AppShell>
  );
}
