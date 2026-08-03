import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { NexoLogo } from "@/components/brand-assets";

export default function CadastroPage() {
  return (
    <main className="auth-page">
      <section className="auth-story" aria-label="Resumo do Nexo Finance">
        <span className="auth-kicker">NEXO Finance</span>
        <h1>Comece com uma base financeira organizada desde o primeiro acesso.</h1>
        <p>
          Crie sua conta para cadastrar receitas, despesas, cartões e usar o Fin como copiloto financeiro.
        </p>
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
        <p className="auth-intro">Seus dados ficam separados em uma conta pessoal protegida.</p>
        <AuthForm mode="register" redirectTo="/onboarding" />
        <p>
          Já tem conta? <Link href="/login">Entrar</Link>
        </p>
      </section>
    </main>
  );
}
