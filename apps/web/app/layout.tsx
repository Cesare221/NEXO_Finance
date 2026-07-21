import type { Metadata, Viewport } from "next";
import { PWARegistration } from "@/components/pwa-registration";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexo",
  description: "Organize sua vida financeira com o agente Fin",
  applicationName: "Nexo",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Nexo"
  },
  icons: {
    icon: [
      { url: "/icons/nexo-32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/nexo-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/nexo-512.png", sizes: "512x512", type: "image/png" }
    ],
    apple: [{ url: "/icons/nexo-apple-180.png", sizes: "180x180", type: "image/png" }],
    shortcut: [{ url: "/icons/nexo-32.png", sizes: "32x32", type: "image/png" }]
  }
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#101a19"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <PWARegistration />
        {children}
      </body>
    </html>
  );
}
