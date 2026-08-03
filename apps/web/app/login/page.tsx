import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { FinMascot, NexoLogo } from "@/components/brand-assets";

export default async function LoginPage({
  searchParams
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  const params = await searchParams;
  const redirectTo =
    params.next?.startsWith("/") && !params.next.startsWith("//")
      ? params.next
      : "/dashboard";

  return (
    <main className="auth-page">
      <section className="auth-story" aria-label="Resumo do Nexo Finance">
        <span className="auth-kicker">NEXO Finance</span>
        <h1>Finanças com IA e revisão humana.</h1>
        <p>Acompanhe saldos, fluxo de caixa e lançamentos em um só lugar.</p>
        <div className="auth-fin-showcase" aria-label="Fin, assistente financeiro do Nexo">
          <FinMascot priority />
          <div>
            <span>Fin online</span>
            <strong>Revisão antes de salvar.</strong>
          </div>
        </div>
        <div className="auth-proof-grid" aria-label="Indicadores do produto">
          <div>
            <strong>2FA</strong>
            <span>Login protegido</span>
          </div>
          <div>
            <strong>30 dias</strong>
            <span>Visão padrão</span>
          </div>
          <div>
            <strong>IA</strong>
            <span>Revisão antes de salvar</span>
          </div>
        </div>
      </section>
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Entrar no Nexo</h1>
        <p className="auth-intro">Acesse sua conta.</p>
        <AuthForm mode="login" redirectTo={redirectTo} />
        <p>
          Ainda não tem conta? <Link href="/cadastro">Criar cadastro</Link>
        </p>
      </section>
    </main>
  );
}
