import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Protheus PC",
  description: "Extrator de pedidos de compra a partir de NF/NFS-e/Faturas",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-background text-foreground antialiased">
        <header className="border-b bg-card">
          <div className="container flex h-14 items-center justify-between">
            <Link href="/" className="font-semibold">
              Protheus PC
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/referencias" className="hover:underline">
                Referências
              </Link>
              <Link href="/processar" className="hover:underline">
                Processar PDFs
              </Link>
            </nav>
          </div>
        </header>
        <main className="container py-8">{children}</main>
      </body>
    </html>
  );
}
