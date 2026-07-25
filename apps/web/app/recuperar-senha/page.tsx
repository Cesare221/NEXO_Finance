import Link from "next/link";
import { NexoLogo } from "@/components/brand-assets";
import { PasswordRecoveryForm } from "@/components/password-recovery-form";

export default function PasswordRecoveryPage() {
  return (
    <main className="auth-page">
      <section className="card auth-panel">
        <Link className="auth-brand" href="/" aria-label="Nexo">
          <NexoLogo priority />
        </Link>
        <h1>Recuperar Senha</h1>
        <PasswordRecoveryForm />
      </section>
    </main>
  );
}
