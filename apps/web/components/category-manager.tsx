"use client";

import { Archive, CheckCircle2, FolderTree, LoaderCircle, Pencil, Plus, Tag, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import type { FinancialCategory } from "@/lib/financial-types";

type CategoryRow = FinancialCategory & { depth: number };

function flattenCategories(categories: FinancialCategory[], depth = 0): CategoryRow[] {
  return categories.flatMap((category) => [
    { ...category, depth },
    ...flattenCategories(category.children ?? [], depth + 1)
  ]);
}

async function readError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: string } | null;
  return data?.detail ?? "Não foi possível concluir a operação.";
}

export function CategoryManager() {
  const [categories, setCategories] = useState<FinancialCategory[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [parentId, setParentId] = useState("");
  const [color, setColor] = useState("#e2b849");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [archivingId, setArchivingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const rows = useMemo(() => flattenCategories(categories).filter((category) => !category.is_archived), [categories]);

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/financial/categories");
      if (!response.ok) throw new Error(await readError(response));
      setCategories(await response.json() as FinancialCategory[]);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Não foi possível carregar as categorias.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCategories();
  }, [loadCategories]);

  function resetForm() {
    setEditingId(null);
    setName("");
    setParentId("");
    setColor("#e2b849");
    setFormOpen(false);
  }

  function startEdit(category: CategoryRow) {
    setEditingId(category.id);
    setName(category.name);
    setParentId(category.parent_id ? String(category.parent_id) : "");
    setColor(category.color ?? "#e2b849");
    setError("");
    setSuccess("");
    setFormOpen(true);
  }

  async function submitCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (name.trim().length < 2) {
      setError("Informe um nome com pelo menos dois caracteres.");
      return;
    }
    setSaving(true);
    try {
      const response = await fetch(
        editingId ? `/api/financial/categories/${editingId}` : "/api/financial/categories",
        {
          method: editingId ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            parent_id: parentId ? Number(parentId) : null,
            color,
            icon: "tag"
          })
        }
      );
      if (!response.ok) throw new Error(await readError(response));
      resetForm();
      setSuccess(editingId ? "Categoria atualizada." : "Categoria adicionada ao Nexo.");
      await loadCategories();
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar a categoria.");
    } finally {
      setSaving(false);
    }
  }

  async function archiveCategory(category: CategoryRow) {
    if (!window.confirm(`Arquivar ${category.name}? O histórico classificado será preservado.`)) return;
    setArchivingId(category.id);
    setError("");
    setSuccess("");
    try {
      const response = await fetch(`/api/financial/categories/${category.id}`, { method: "DELETE" });
      if (!response.ok) throw new Error(await readError(response));
      setSuccess("Categoria arquivada.");
      await loadCategories();
      window.dispatchEvent(new Event("nexo:financial-data-changed"));
    } catch (archiveError) {
      setError(archiveError instanceof Error ? archiveError.message : "Não foi possível arquivar a categoria.");
    } finally {
      setArchivingId(null);
    }
  }

  return (
    <div className="resource-layout">
      <section className="resource-summary" aria-label="Resumo das categorias">
        <div>
          <span>Categorias ativas</span>
          <strong>{rows.length}</strong>
        </div>
        <div>
          <span>Subcategorias</span>
          <strong>{rows.filter((category) => category.parent_id !== null).length}</strong>
        </div>
        <button className="button" type="button" onClick={() => setFormOpen(true)}>
          <Plus size={18} aria-hidden="true" />
          Nova categoria
        </button>
      </section>

      {formOpen && (
        <form className="card form resource-form" onSubmit={submitCategory}>
          <div className="resource-heading">
            <div>
              <span className="section-kicker">{editingId ? "Edição" : "Organização"}</span>
              <h2>{editingId ? "Editar categoria" : "Adicionar categoria"}</h2>
            </div>
            <button className="icon-button" type="button" aria-label="Fechar formulário" onClick={resetForm}>
              <X size={19} aria-hidden="true" />
            </button>
          </div>
          <div className="resource-form-grid">
            <div className="field">
              <label htmlFor="category-name">Nome</label>
              <input className="input" id="category-name" value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
            </div>
            <div className="field">
              <label htmlFor="category-parent">Categoria principal</label>
              <select className="input" id="category-parent" value={parentId} onChange={(event) => setParentId(event.target.value)}>
                <option value="">Nenhuma</option>
                {rows.filter((category) => category.id !== editingId).map((category) => (
                  <option key={category.id} value={category.id}>{`${"— ".repeat(category.depth)}${category.name}`}</option>
                ))}
              </select>
            </div>
            <div className="field color-field">
              <label htmlFor="category-color">Cor de identificação</label>
              <input id="category-color" type="color" value={color} onChange={(event) => setColor(event.target.value)} />
            </div>
          </div>
          <div className="resource-form-actions">
            <button className="button secondary" type="button" onClick={resetForm}>Cancelar</button>
            <button className="button" type="submit" disabled={saving}>
              {saving ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <CheckCircle2 size={18} aria-hidden="true" />}
              {saving ? "Salvando" : "Salvar categoria"}
            </button>
          </div>
        </form>
      )}

      <div className="resource-feedback" aria-live="polite">
        {error && <p className="error">{error}</p>}
        {success && <p className="success-message"><CheckCircle2 size={17} aria-hidden="true" />{success}</p>}
      </div>

      {loading ? (
        <section className="card resource-state"><LoaderCircle className="spin" aria-hidden="true" /><p>Carregando categorias...</p></section>
      ) : rows.length === 0 ? (
        <section className="card resource-state">
          <FolderTree aria-hidden="true" />
          <h2>Organize suas movimentações</h2>
          <p>Crie categorias e subcategorias para entender melhor para onde o dinheiro vai.</p>
          <button className="button" type="button" onClick={() => setFormOpen(true)}>Adicionar categoria</button>
        </section>
      ) : (
        <section className="resource-list" aria-label="Categorias ativas">
          {rows.map((category) => (
            <article className="card resource-row" key={category.id}>
              <span className="resource-icon" style={{ backgroundColor: category.color ?? "#f7e4a9", marginLeft: `${Math.min(category.depth, 3) * 20}px` }}>
                <Tag aria-hidden="true" />
              </span>
              <div className="resource-copy">
                <strong>{category.name}</strong>
                <span>{category.parent_id ? "Subcategoria" : "Categoria principal"}</span>
              </div>
              <span className="status ok">Ativa</span>
              <div className="resource-actions">
                <button className="icon-button" type="button" aria-label={`Editar ${category.name}`} onClick={() => startEdit(category)}>
                  <Pencil size={17} aria-hidden="true" />
                </button>
                <button className="icon-button" type="button" aria-label={`Arquivar ${category.name}`} disabled={archivingId === category.id} onClick={() => void archiveCategory(category)}>
                  {archivingId === category.id ? <LoaderCircle className="spin" size={17} aria-hidden="true" /> : <Archive size={17} aria-hidden="true" />}
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
