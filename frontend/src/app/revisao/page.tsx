"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type Ficha } from "@/lib/api";

export default function RevisaoPage() {
  const router = useRouter();
  const [fichas, setFichas] = useState<Ficha[]>([]);
  const [gerando, setGerando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("fichas");
    if (!raw) {
      router.replace("/processar");
      return;
    }
    setFichas(JSON.parse(raw));
  }, [router]);

  const updateFicha = (idx: number, patch: Partial<Ficha>) => {
    setFichas((atual) => atual.map((f, i) => (i === idx ? { ...f, ...patch } : f)));
  };

  const updateItem = (
    idxFicha: number,
    idxItem: number,
    patch: Partial<Ficha["itens"][number]>
  ) => {
    setFichas((atual) =>
      atual.map((f, i) =>
        i === idxFicha
          ? { ...f, itens: f.itens.map((it, j) => (j === idxItem ? { ...it, ...patch } : it)) }
          : f
      )
    );
  };

  const removerItem = (idxFicha: number, idxItem: number) => {
    setFichas((atual) =>
      atual.map((f, i) => (i === idxFicha ? { ...f, itens: f.itens.filter((_, j) => j !== idxItem) } : f))
    );
  };

  const adicionarItem = (idxFicha: number) => {
    setFichas((atual) =>
      atual.map((f, i) =>
        i === idxFicha
          ? { ...f, itens: [...f.itens, { descricao: "", quantidade: 1, valor_unitario: 0 }] }
          : f
      )
    );
  };

  const gerar = async () => {
    setGerando(true);
    setErro(null);
    try {
      const blob = await api.processamentos.gerarExcel(fichas);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pedidos_compra.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErro(String(e));
    } finally {
      setGerando(false);
    }
  };

  if (fichas.length === 0) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Revisar dados extraídos</h1>
          <p className="text-muted-foreground">
            Ajuste o que estiver errado e clique em &ldquo;Gerar Excel&rdquo; quando terminar.
          </p>
        </div>
        <Button onClick={gerar} disabled={gerando}>
          {gerando ? "Gerando..." : "Gerar Excel"}
        </Button>
      </div>

      {erro && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">{erro}</div>
      )}

      <div className="space-y-4">
        {fichas.map((f, i) => (
          <FichaCard
            key={i}
            ficha={f}
            onUpdate={(patch) => updateFicha(i, patch)}
            onUpdateItem={(idx, patch) => updateItem(i, idx, patch)}
            onRemoveItem={(idx) => removerItem(i, idx)}
            onAddItem={() => adicionarItem(i)}
          />
        ))}
      </div>

      <div className="flex gap-2">
        <Button onClick={gerar} disabled={gerando}>
          {gerando ? "Gerando..." : "Gerar Excel"}
        </Button>
        <Button variant="outline" onClick={() => router.push("/processar")}>
          Voltar
        </Button>
      </div>
    </div>
  );
}

function FichaCard({
  ficha,
  onUpdate,
  onUpdateItem,
  onRemoveItem,
  onAddItem,
}: {
  ficha: Ficha;
  onUpdate: (patch: Partial<Ficha>) => void;
  onUpdateItem: (idx: number, patch: Partial<Ficha["itens"][number]>) => void;
  onRemoveItem: (idx: number) => void;
  onAddItem: () => void;
}) {
  const status = ficha.status_extracao;
  const variantStatus =
    status === "ok" ? "success" : status === "parcial" ? "warning" : status === "manual" ? "outline" : "destructive";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg">{ficha.arquivos_origem.join(", ")}</CardTitle>
            <p className="text-xs text-muted-foreground">
              Template: {ficha.template_usado || "—"}
            </p>
          </div>
          <Badge variant={variantStatus}>{status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Filial">
            <Input value={ficha.filial_codigo || ""} onChange={(e) => onUpdate({ filial_codigo: e.target.value })} />
          </Field>
          <Field label="CNPJ Filial">
            <Input value={ficha.filial_cnpj || ""} onChange={(e) => onUpdate({ filial_cnpj: e.target.value })} />
          </Field>
          <Field label="Fornecedor (cód)">
            <Input
              value={ficha.fornecedor_codigo || ""}
              onChange={(e) => onUpdate({ fornecedor_codigo: e.target.value })}
            />
          </Field>
          <Field label="Fornecedor (nome)">
            <Input
              value={ficha.fornecedor_nome || ""}
              onChange={(e) => onUpdate({ fornecedor_nome: e.target.value })}
            />
          </Field>
          <Field label="CNPJ Fornecedor">
            <Input
              value={ficha.fornecedor_cnpj || ""}
              onChange={(e) => onUpdate({ fornecedor_cnpj: e.target.value })}
            />
          </Field>
          <Field label="Tipo">
            <select
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={ficha.tipo_pedido || ""}
              onChange={(e) =>
                onUpdate({ tipo_pedido: (e.target.value || null) as Ficha["tipo_pedido"] })
              }
            >
              <option value="">—</option>
              <option value="Produto">Produto</option>
              <option value="Servico">Serviço</option>
            </select>
          </Field>
          <Field label="Tipo de documento">
            <Input
              value={ficha.documentos_tipo || ""}
              onChange={(e) => onUpdate({ documentos_tipo: e.target.value })}
            />
          </Field>
          <Field label="Números dos docs (vírgula)">
            <Input
              value={ficha.numeros_documentos.join(", ")}
              onChange={(e) =>
                onUpdate({
                  numeros_documentos: e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
            />
          </Field>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-semibold">Itens</h3>
            <Button size="sm" variant="outline" onClick={onAddItem}>
              + Adicionar item
            </Button>
          </div>
          <div className="space-y-2">
            {ficha.itens.map((it, idx) => (
              <div key={idx} className="grid grid-cols-1 gap-2 rounded border p-2 md:grid-cols-[1fr_100px_120px_auto]">
                <Input
                  placeholder="Descrição"
                  value={it.descricao}
                  onChange={(e) => onUpdateItem(idx, { descricao: e.target.value })}
                />
                <Input
                  type="number"
                  step="0.01"
                  placeholder="Qtd"
                  value={it.quantidade}
                  onChange={(e) => onUpdateItem(idx, { quantidade: parseFloat(e.target.value) || 0 })}
                />
                <Input
                  type="number"
                  step="0.01"
                  placeholder="Vlr unit"
                  value={it.valor_unitario}
                  onChange={(e) => onUpdateItem(idx, { valor_unitario: parseFloat(e.target.value) || 0 })}
                />
                <Button size="sm" variant="ghost" onClick={() => onRemoveItem(idx)}>
                  Remover
                </Button>
              </div>
            ))}
            {ficha.itens.length === 0 && (
              <p className="text-sm text-muted-foreground">Nenhum item — adicione manualmente.</p>
            )}
          </div>
        </div>

        {ficha.observacoes.length > 0 && (
          <div className="rounded border bg-muted/50 p-3 text-sm">
            <p className="mb-1 font-medium">Observações:</p>
            <ul className="list-disc pl-5">
              {ficha.observacoes.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      {children}
    </label>
  );
}
