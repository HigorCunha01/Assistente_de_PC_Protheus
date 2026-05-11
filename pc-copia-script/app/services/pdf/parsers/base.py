"""Estruturas comuns aos parsers de PDF."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ItemExtraido:
    descricao: str
    quantidade: float
    valor_unitario: float
    valor_unitario_calculado: bool = False


@dataclass
class ParseResult:
    """Resultado bruto de um parser, antes do enriquecimento com planilhas."""
    template_usado: str
    confianca: float  # 0.0 a 1.0

    cnpj_emissor: Optional[str] = None
    nome_emissor: Optional[str] = None

    cnpj_tomador: Optional[str] = None

    numero_documento: Optional[str] = None  # já sem zeros à esquerda
    tipo_documento_legivel: Optional[str] = None  # "Nota Fiscal", "NFS-e", etc.

    itens: list[ItemExtraido] = field(default_factory=list)

    observacoes: list[str] = field(default_factory=list)
