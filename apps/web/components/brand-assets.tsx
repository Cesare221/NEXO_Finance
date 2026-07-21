import Image from "next/image";

type BrandAssetProps = {
  className?: string;
  priority?: boolean;
};

export function NexoMark({ className = "", priority = false }: BrandAssetProps) {
  return (
    <Image
      className={`nexo-mark ${className}`.trim()}
      src="/icons/nexo-512.png"
      alt=""
      width={512}
      height={512}
      priority={priority}
    />
  );
}

export function NexoLogo({ className = "", priority = false }: BrandAssetProps) {
  return (
    <span className={`nexo-logo ${className}`.trim()} role="img" aria-label="Nexo">
      <Image
        className="nexo-logo-image nexo-logo-light"
        src="/brand/nexo-logo.webp"
        alt=""
        width={960}
        height={240}
        priority={priority}
      />
      <Image
        className="nexo-logo-image nexo-logo-dark"
        src="/brand/nexo-logo-dark.webp"
        alt=""
        width={960}
        height={240}
        priority={priority}
      />
    </span>
  );
}

type FinMascotProps = BrandAssetProps & {
  variant?: "full" | "avatar";
};

export function FinMascot({ className = "", priority = false, variant = "full" }: FinMascotProps) {
  const isAvatar = variant === "avatar";

  return (
    <Image
      className={`fin-mascot ${className}`.trim()}
      src={isAvatar ? "/brand/fin-avatar.webp" : "/brand/fin-mascot.webp"}
      alt="Fin, agente financeiro do Nexo"
      width={isAvatar ? 512 : 640}
      height={isAvatar ? 512 : 960}
      priority={priority}
    />
  );
}
