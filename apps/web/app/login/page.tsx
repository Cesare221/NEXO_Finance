import Link from "next/link";
import { AuthForm } from "@/components/auth-form";
import { NexoLogo } from "@/components/brand-assets";

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
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Entrar no Nexo</h1>
        <p className="auth-intro">Acesse seu espaço financeiro com segurança.</p>
        <AuthForm mode="login" redirectTo={redirectTo} />
        <p>
          Ainda não tem conta? <Link href="/cadastro">Criar cadastro</Link>
        </p>
      </section>
    </main>
  );
}
