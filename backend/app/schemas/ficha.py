"""Schemas Pydantic para fichas de pedido de compra."""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ItemFicha(BaseModel):
    descricao: str
    quantidade: float
    valor_unitario: float
    valor_unitario_calculado: bool = False


class FichaPedido(BaseModel):
    """Representa um documento extraído (1 PDF) ou um pedido consolidado (N PDFs)."""
    # Identificação
    arquivos_origem: list[str] = Field(default_factory=list)  # nomes dos PDFs originais
    nomes_arquivos_padrao: list[str] = Field(default_factory=list)  # FORNECEDOR_NUM_pc_

    # Filial
    filial_codigo: Optional[str] = None
    filial_cnpj: Optional[str] = None

    # Fornecedor
    fornecedor_codigo: Optional[str] = None
    fornecedor_nome: Optional[str] = None
    fornecedor_cnpj: Optional[str] = None

    # Documento
    tipo_pedido: Optional[Literal["Produto", "Servico"]] = None
    documentos_tipo: Optional[str] = None  # "Nota Fiscal", "NFS-e", "Fatura", "Nota de Débito"
    numeros_documentos: list[str] = Field(default_factory=list)

    # Itens
    itens: list[ItemFicha] = Field(default_factory=list)

    # Sugestão de PC (preenchido pelo matcher)
    sugestao_pc_num: Optional[str] = None
    sugestao_pc_obs_original: Optional[str] = None
    sugestao_pc_obs_modificada: Optional[str] = None

    # Meta
    status_extracao: Literal["ok", "parcial", "erro", "manual"] = "ok"
    template_usado: Optional[str] = None
    observacoes: list[str] = Field(default_factory=list)


class RevisaoRequest(BaseModel):
    fichas: list[FichaPedido]
