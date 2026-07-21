import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Nexo - Controle financeiro",
    short_name: "Nexo",
    description: "Controle contas, transações e cartões e converse com o agente Fin.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#071817",
    theme_color: "#101a19",
    lang: "pt-BR",
    categories: ["finance", "productivity"],
    icons: [
      {
        src: "/icons/nexo-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/icons/nexo-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/icons/nexo-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable"
      }
    ]
  };
}
