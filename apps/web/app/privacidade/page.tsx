import Link from "next/link";
import { NexoLogo } from "@/components/brand-assets";

export default function PrivacidadePage() {
  return (
    <main className="legal-page">
      <header>
        <Link href="/login" aria-label="Voltar para o Nexo"><NexoLogo /></Link>
        <span>Versão 2026-07-21</span>
      </header>
      <article>
        <h1>Aviso de Privacidade</h1>
        <p>O Nexo trata dados de cadastro e informações financeiras fornecidas por você para organizar sua vida financeira, autenticar sua conta e oferecer o assistente Fin.</p>
        <h2>Dados e finalidade</h2>
        <p>Nome, e-mail, telefone e foto identificam sua conta. Contas, cartões, categorias e movimentações são usados somente para entregar os recursos financeiros solicitados.</p>
        <h2>Inteligência artificial</h2>
        <p>O uso da Groq é opcional. Quando autorizado, o Fin envia apenas a mensagem e o contexto financeiro mínimo necessário. A autorização pode ser revogada nas configurações.</p>
        <h2>Seus direitos</h2>
        <p>Você pode acessar, corrigir, exportar e excluir seus dados pela área de configurações. Solicitações adicionais devem ser encaminhadas ao canal de privacidade informado pelo operador do serviço.</p>
        <h2>Segurança e retenção</h2>
        <p>O Nexo usa controles de acesso, sessões revogáveis, registros de auditoria e criptografia fornecida pela infraestrutura de hospedagem. Os dados permanecem enquanto a conta estiver ativa ou pelo período legal aplicável.</p>
        <h2>Operador e contato</h2>
        <p>Antes da publicação, o responsável pelo Nexo deve inserir nesta seção sua razão social ou nome, CNPJ ou CPF aplicável e o canal oficial do encarregado de dados.</p>
      </article>
    </main>
  );
}
