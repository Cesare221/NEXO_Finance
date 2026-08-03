import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { FinMascot, NexoLogo } from "@/components/brand-assets";

export default function CadastroPage() {
  return (
    <main className="auth-page">
      <section className="auth-story" aria-label="Resumo do Nexo Finance">
        <span className="auth-kicker">NEXO Finance</span>
        <h1>Organize sua vida financeira desde o primeiro acesso.</h1>
        <p>Cadastre receitas, despesas e cartões com apoio do Fin.</p>
        <div className="auth-fin-showcase" aria-label="Fin, assistente financeiro do Nexo">
          <FinMascot priority />
          <div>
            <span>Fin online</span>
            <strong>Lançamentos guiados por etapas.</strong>
          </div>
        </div>
        <div className="auth-proof-grid" aria-label="Recursos inclusos">
          <div>
            <strong>Seguro</strong>
            <span>Dados por conta</span>
          </div>
          <div>
            <strong>Fin</strong>
            <span>Assistente com revisão</span>
          </div>
          <div>
            <strong>Dashboard</strong>
            <span>Visão prática</span>
          </div>
        </div>
      </section>
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Criar cadastro</h1>
        <p className="auth-intro">Crie sua conta pessoal.</p>
        <AuthForm mode="register" redirectTo="/onboarding" />
        <p>
          Já tem conta? <Link href="/login">Entrar</Link>
        </p>
      </section>
    </main>
  );
}
