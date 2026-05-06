"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type ReferenciasStatus } from "@/lib/api";

const PLANILHAS = [
  { tipo: "filiais" as const, nome: "Filiais", descricao: "Mapeamento Código da Filial → CNPJ" },
  { tipo: "fornecedores" as const, nome: "Fornecedores", descricao: "Cadastro de fornecedores Protheus" },
  { tipo: "pedidos_compra" as const, nome: "Pedidos de Compra", descricao: "Histórico de PCs para sugestão de cópia" },
];

export default function ReferenciasPage() {
  const [status, setStatus] = useState<ReferenciasStatus | null>(null);
  const [carregando, setCarregando] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<{ texto: string; tipo: "ok" | "erro" } | null>(null);

  const recarregar = () => {
    api.referencias.status().then(setStatus).catch(() => setStatus(null));
  };

  useEffect(() => recarregar(), []);

  const handleUpload = async (tipo: "filiais" | "fornecedores" | "pedidos_compra", file: File) => {
    setCarregando(tipo);
    setMensagem(null);
    try {
      const r = await api.referencias.upload(tipo, file);
      setMensagem({ texto: `${r.tipo}: ${r.linhas} linhas carregadas.`, tipo: "ok" });
      recarregar();
    } catch (e) {
      setMensagem({ texto: `Erro: ${String(e)}`, tipo: "erro" });
    } finally {
      setCarregando(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Planilhas de referência</h1>
        <p className="text-muted-foreground">
          As 3 planilhas são lidas pelo backend a cada processamento. Atualize quando quiser.
        </p>
      </div>

      {mensagem && (
        <div
          className={
            mensagem.tipo === "ok"
              ? "rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900"
              : "rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900"
          }
        >
          {mensagem.texto}
        </div>
      )}

      <div className="grid gap-4">
        {PLANILHAS.map((p) => {
          const presente = status?.[p.tipo]?.presente ?? false;
          const tamanho = status?.[p.tipo]?.tamanho_bytes ?? 0;
          return (
            <Card key={p.tipo}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{p.nome}</CardTitle>
                    <CardDescription>{p.descricao}</CardDescription>
                  </div>
                  {presente ? (
                    <Badge variant="success">
                      Carregada ({(tamanho / 1024).toFixed(1)} KB)
                    </Badge>
                  ) : (
                    <Badge variant="warning">Não carregada</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Input
                    type="file"
                    accept=".xlsx"
                    disabled={carregando === p.tipo}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleUpload(p.tipo, f);
                      e.target.value = "";
                    }}
                  />
                  {carregando === p.tipo && <span className="text-sm text-muted-foreground">Enviando...</span>}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
