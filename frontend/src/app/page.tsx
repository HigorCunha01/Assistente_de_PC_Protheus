"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, type HealthResponse } from "@/lib/api";

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api.health()
      .then(setHealth)
      .catch((e) => setErro(String(e)));
  }, []);

  const refsOk =
    health?.referencias?.filiais &&
    health?.referencias?.fornecedores &&
    health?.referencias?.pedidos_compra;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Protheus PC</h1>
        <p className="text-muted-foreground">
          Extrator de pedidos de compra a partir de NF, NFS-e, faturas e notas de débito.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Status do sistema</CardTitle>
          <CardDescription>
            {erro
              ? `Não foi possível conectar ao backend: ${erro}`
              : health
                ? `Backend versão ${health.version} — ${health.status}`
                : "Carregando..."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {health && (
            <div className="space-y-2">
              <RefRow label="Filiais" ok={health.referencias.filiais} />
              <RefRow label="Fornecedores" ok={health.referencias.fornecedores} />
              <RefRow label="Pedidos de Compra" ok={health.referencias.pedidos_compra} />
            </div>
          )}
          <div className="flex gap-2 pt-2">
            <Link href="/referencias">
              <Button variant={refsOk ? "outline" : "default"}>
                {refsOk ? "Atualizar referências" : "Carregar referências"}
              </Button>
            </Link>
            <Link href="/processar">
              <Button disabled={!refsOk}>Processar PDFs</Button>
            </Link>
          </div>
          {!refsOk && health && (
            <p className="text-sm text-amber-600">
              Faça upload das 3 planilhas de referência antes de processar PDFs.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Como funciona</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>1. Referências:</strong> faça upload das planilhas Filiais, Fornecedores e
            Pedidos de Compra. Elas ficam armazenadas no servidor e podem ser atualizadas a
            qualquer momento.
          </p>
          <p>
            <strong>2. Processar PDFs:</strong> arraste 1 ou mais PDFs (NF-e, NFS-e, faturas).
            O sistema extrai os dados e abre uma tela de revisão.
          </p>
          <p>
            <strong>3. Revisar:</strong> ajuste os dados extraídos, confirme a sugestão de PC
            (quando houver) e clique em &ldquo;Gerar Excel&rdquo; pra baixar o resultado.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function RefRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-md border p-3">
      <span>{label}</span>
      {ok ? (
        <Badge variant="success">Carregada</Badge>
      ) : (
        <Badge variant="warning">Falta carregar</Badge>
      )}
    </div>
  );
}
