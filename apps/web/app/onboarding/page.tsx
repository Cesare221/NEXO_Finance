import { AppShell } from "@/components/app-shell";
import { DemoDatasetControl } from "@/components/demo-dataset-control";

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
      <section className="onboarding-demo" aria-labelledby="onboarding-demo-title">
        <div>
          <span className="section-kicker">Opcional</span>
          <h2 id="onboarding-demo-title">{"Conhe\u00e7a o Nexo antes de cadastrar tudo"}</h2>
          <p>{"Use um conjunto remov\u00edvel para explorar saldos, gr\u00e1ficos, cart\u00f5es e o Fin."}</p>
        </div>
        <DemoDatasetControl variant="install" />
      </section>
    </AppShell>
  );
}
