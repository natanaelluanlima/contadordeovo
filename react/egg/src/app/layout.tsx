import type { Metadata } from "next";
import { Montserrat } from "next/font/google";

import "./globals.css";

const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Contador de Ovos",
  description: "Contador de ovos em esteira de produção.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={montserrat.className}>{children}</body>
    </html>
  );
}
