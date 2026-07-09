import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Contador de Ovos",
  description: "Contador de ovos em esteira de produção.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
