import { AppShell } from "@/components/app-shell";
import { CategoryManager } from "@/components/category-manager";

export default function CategoriasPage() {
  return (
    <AppShell>
      <header className="page-header">
        <div>
          <span className="section-kicker">Organização</span>
          <h1>Categorias</h1>
          <p>Crie uma estrutura simples para reconhecer padrões nas suas receitas e despesas.</p>
        </div>
      </header>
      <CategoryManager />
    </AppShell>
  );
}
