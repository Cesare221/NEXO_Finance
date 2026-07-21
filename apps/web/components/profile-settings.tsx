"use client";

import { Camera, CheckCircle2, LoaderCircle, Trash2, UserRound } from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useSession } from "@/components/session-profile";

const MAX_SOURCE_SIZE = 8 * 1024 * 1024;
const AVATAR_SIZE = 256;

async function readError(response: Response) {
  const data = await response.json().catch(() => null) as { detail?: string } | null;
  return data?.detail ?? "Não foi possível salvar seu perfil.";
}

function loadImage(source: string) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Não foi possível ler esta imagem."));
    image.src = source;
  });
}

async function prepareAvatar(file: File) {
  if (!file.type.match(/^image\/(png|jpeg|webp)$/)) {
    throw new Error("Escolha uma imagem PNG, JPG ou WebP.");
  }
  if (file.size > MAX_SOURCE_SIZE) {
    throw new Error("A imagem original deve ter no máximo 8 MB.");
  }

  const source = URL.createObjectURL(file);
  try {
    const image = await loadImage(source);
    const cropSize = Math.min(image.naturalWidth, image.naturalHeight);
    const sourceX = (image.naturalWidth - cropSize) / 2;
    const sourceY = (image.naturalHeight - cropSize) / 2;
    const canvas = document.createElement("canvas");
    canvas.width = AVATAR_SIZE;
    canvas.height = AVATAR_SIZE;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Seu navegador não conseguiu processar a imagem.");
    context.drawImage(
      image,
      sourceX,
      sourceY,
      cropSize,
      cropSize,
      0,
      0,
      AVATAR_SIZE,
      AVATAR_SIZE
    );
    return canvas.toDataURL("image/webp", 0.82);
  } finally {
    URL.revokeObjectURL(source);
  }
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "NX";
}

export function ProfileSettings() {
  const { user, updateUser } = useSession();
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone ?? "");
  const [avatar, setAvatar] = useState<string | null>(user.avatar_data_url);
  const [processingPhoto, setProcessingPhoto] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setName(user.name);
    setPhone(user.phone ?? "");
    setAvatar(user.avatar_data_url);
  }, [user]);

  async function selectPhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setProcessingPhoto(true);
    setError("");
    setSuccess("");
    try {
      setAvatar(await prepareAvatar(file));
    } catch (photoError) {
      setError(photoError instanceof Error ? photoError.message : "Não foi possível preparar a imagem.");
    } finally {
      setProcessingPhoto(false);
    }
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedName = name.trim();
    if (normalizedName.length < 2) {
      setError("Informe seu nome com pelo menos dois caracteres.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const response = await fetch("/api/auth/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: normalizedName,
          phone: phone.trim() || null,
          avatar_data_url: avatar
        })
      });
      if (!response.ok) throw new Error(await readError(response));
      const updatedUser = await response.json() as typeof user;
      updateUser(updatedUser);
      window.dispatchEvent(new CustomEvent("nexo:profile-updated", { detail: updatedUser }));
      setSuccess("Perfil atualizado.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Não foi possível salvar seu perfil.");
    } finally {
      setSaving(false);
    }
  }

  const hasChanges =
    name.trim() !== user.name ||
    phone.trim() !== (user.phone ?? "") ||
    avatar !== user.avatar_data_url;

  return (
    <section className="card profile-settings" aria-labelledby="profile-settings-title">
      <div className="settings-section-heading">
        <div>
          <span className="section-kicker">Sua conta</span>
          <h2 id="profile-settings-title">Perfil pessoal</h2>
          <p>Mantenha seus dados de contato e a foto usados no Nexo.</p>
        </div>
      </div>

      <form className="profile-settings-form" onSubmit={saveProfile}>
        <div className="profile-photo-editor">
          <div className="profile-photo-preview" aria-label="Prévia da foto de perfil">
            {avatar ? (
              <img src={avatar} alt="Sua foto de perfil" />
            ) : (
              <span>{initials(name)}</span>
            )}
          </div>
          <div className="profile-photo-actions">
            <strong>Foto de perfil</strong>
            <span>PNG, JPG ou WebP. A imagem será ajustada para um formato leve.</span>
            <div>
              <label className="button secondary profile-photo-button">
                {processingPhoto ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <Camera size={18} aria-hidden="true" />}
                {processingPhoto ? "Preparando" : avatar ? "Trocar foto" : "Adicionar foto"}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => void selectPhoto(event)}
                  disabled={processingPhoto || saving}
                />
              </label>
              {avatar && (
                <button className="icon-button" type="button" aria-label="Remover foto de perfil" title="Remover foto" onClick={() => setAvatar(null)} disabled={saving}>
                  <Trash2 size={18} aria-hidden="true" />
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="profile-fields">
          <div className="field">
            <label htmlFor="profile-name">Nome</label>
            <input id="profile-name" className="input" value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" maxLength={255} required />
          </div>
          <div className="field">
            <label htmlFor="profile-phone">Telefone</label>
            <input id="profile-phone" className="input" type="tel" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" inputMode="tel" maxLength={32} placeholder="(11) 99999-9999" />
          </div>
          <div className="field profile-email-field">
            <label htmlFor="profile-email">E-mail de acesso</label>
            <input id="profile-email" className="input" type="email" value={user.email} autoComplete="email" readOnly aria-describedby="profile-email-help" />
            <span id="profile-email-help" className="field-help">O e-mail não pode ser alterado por esta tela.</span>
          </div>
        </div>

        <div className="profile-settings-footer">
          <div className="resource-feedback" aria-live="polite">
            {error && <p className="error">{error}</p>}
            {success && <p className="success-message"><CheckCircle2 size={17} aria-hidden="true" />{success}</p>}
          </div>
          <button className="button" type="submit" disabled={saving || processingPhoto || !hasChanges}>
            {saving ? <LoaderCircle className="spin" size={18} aria-hidden="true" /> : <UserRound size={18} aria-hidden="true" />}
            {saving ? "Salvando" : "Salvar perfil"}
          </button>
        </div>
      </form>
    </section>
  );
}
