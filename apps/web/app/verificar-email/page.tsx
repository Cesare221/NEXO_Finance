import { Suspense } from "react";
import Link from "next/link";
import { NexoLogo } from "@/components/brand-assets";
import { EmailVerificationForm } from "@/components/email-verification-form";

export default function EmailVerificationPage() {
  return (
    <main className="auth-page">
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Verificação de E-mail</h1>
        <Suspense fallback={<div className="status-banner info">Carregando formulário...</div>}>
          <EmailVerificationForm />
        </Suspense>
      </section>
    </main>
  );
}
