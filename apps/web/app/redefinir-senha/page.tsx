import { Suspense } from "react";
import Link from "next/link";
import { NexoLogo } from "@/components/brand-assets";
import { PasswordResetForm } from "@/components/password-reset-form";

export default function PasswordResetPage() {
  return (
    <main className="auth-page">
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Redefinir Senha</h1>
        <Suspense fallback={<div className="status-banner info">Carregando formulário...</div>}>
          <PasswordResetForm />
        </Suspense>
      </section>
    </main>
  );
}
