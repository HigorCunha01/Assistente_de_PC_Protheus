"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

export default function ProcessarPage() {
  const router = useRouter();
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const onSelect = (files: FileList | null) => {
    if (!files) return;
    const novos = Array.from(files).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    setArquivos((atual) => [...atual, ...novos]);
  };

  const remover = (idx: number) => {
    setArquivos((a) => a.filter((_, i) => i !== idx));
  };

  const processar = async () => {
    if (arquivos.length === 0) return;
    setCarregando(true);
    setErro(null);
    try {
      const { fichas } = await api.processamentos.extrair(arquivos);
      sessionStorage.setItem("fichas", JSON.stringify(fichas));
      router.push("/revisao");
    } catch (e) {
      setErro(String(e));
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Processar PDFs</h1>
        <p className="text-muted-foreground">
          Selecione 1 ou mais PDFs (NF-e, NFS-e, faturas, notas de débito).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Selecionar arquivos</CardTitle>
          <CardDescription>Apenas PDFs. Você poderá revisar antes de gerar o Excel.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            type="file"
            accept=".pdf"
            multiple
            onChange={(e) => {
              onSelect(e.target.files);
              e.target.value = "";
            }}
          />

          {arquivos.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">{arquivos.length} arquivo(s) selecionado(s):</p>
              <ul className="space-y-1 text-sm">
                {arquivos.map((f, i) => (
                  <li key={i} className="flex items-center justify-between rounded border p-2">
                    <span className="truncate">{f.name}</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{(f.size / 1024).toFixed(1)} KB</Badge>
                      <Button size="sm" variant="ghost" onClick={() => remover(i)}>
                        Remover
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {erro && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">{erro}</div>
          )}

          <div className="flex gap-2">
            <Button onClick={processar} disabled={arquivos.length === 0 || carregando}>
              {carregando ? "Processando..." : `Extrair dados de ${arquivos.length || 0} PDF(s)`}
            </Button>
            <Button variant="outline" onClick={() => setArquivos([])}>
              Limpar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
