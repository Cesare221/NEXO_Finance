import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { NexoLogo } from "@/components/brand-assets";

export default function CadastroPage() {
  return (
    <main className="auth-page">
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
