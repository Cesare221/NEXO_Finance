import { Suspense } from "react";
import Link from "next/link";
import { NexoLogo } from "@/components/brand-assets";
import { MfaChallengeForm } from "@/components/mfa-challenge-form";

export default async function MfaPage({
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
        <h1>Autenticação de Duas Etapas</h1>
        <p className="auth-intro">Proteção adicional ativada para sua conta.</p>
        <Suspense fallback={<div className="status-banner info">Carregando formulário...</div>}>
          <MfaChallengeForm redirectTo={redirectTo} />
        </Suspense>
      </section>
    </main>
  );
}
