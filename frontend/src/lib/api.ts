/**
 * Cliente HTTP simples pro backend FastAPI.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  referencias: {
    status: () => request<ReferenciasStatus>("/referencias/status"),
    upload: async (tipo: "filiais" | "fornecedores" | "pedidos_compra", file: File) => {
      const fd = new FormData();
      fd.append("arquivo", file);
      return request<{ status: string; tipo: string; arquivo: string; linhas: number }>(
        `/referencias/upload/${tipo}`,
        { method: "POST", body: fd }
      );
    },
    listarFiliais: () => request<Array<{ codigo: string; cnpj: string }>>("/referencias/filiais"),
  },
  processamentos: {
    extrair: async (files: File[]) => {
      const fd = new FormData();
      files.forEach((f) => fd.append("arquivos", f));
      return request<{ fichas: Ficha[] }>("/processamentos/extrair", {
        method: "POST",
        body: fd,
      });
    },
    gerarExcel: async (fichas: Ficha[]): Promise<Blob> => {
      const res = await fetch(`${API_URL}/processamentos/gerar-excel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fichas }),
      });
      if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
      return res.blob();
    },
  },
};

// ----- Tipos -----

export type HealthResponse = {
  status: string;
  version: string;
  referencias: {
    filiais: boolean;
    fornecedores: boolean;
    pedidos_compra: boolean;
  };
};

export type ReferenciasStatus = {
  filiais: { presente: boolean; tamanho_bytes: number };
  fornecedores: { presente: boolean; tamanho_bytes: number };
  pedidos_compra: { presente: boolean; tamanho_bytes: number };
};

export type ItemFicha = {
  descricao: string;
  quantidade: number;
  valor_unitario: number;
  valor_unitario_calculado?: boolean;
};

export type Ficha = {
  arquivos_origem: string[];
  nomes_arquivos_padrao: string[];
  filial_codigo: string | null;
  filial_cnpj: string | null;
  fornecedor_codigo: string | null;
  fornecedor_nome: string | null;
  fornecedor_cnpj: string | null;
  tipo_pedido: "Produto" | "Servico" | null;
  documentos_tipo: string | null;
  numeros_documentos: string[];
  itens: ItemFicha[];
  sugestao_pc_num?: string | null;
  sugestao_pc_obs_original?: string | null;
  sugestao_pc_obs_modificada?: string | null;
  status_extracao: "ok" | "parcial" | "erro" | "manual";
  template_usado: string | null;
  observacoes: string[];
};
