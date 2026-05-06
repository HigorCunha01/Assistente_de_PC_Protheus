"""Detector de tipo de documento baseado no texto extraído do PDF."""
from typing import Literal

TipoDoc = Literal[
    "danfe_nfe",        # NF-e modelo 55 (produto)
    "nfse",             # NFS-e (serviço, formato municipal)
    "fatura",           # Fatura comum
    "nota_debito",      # Nota de débito
    "desconhecido",
]


def detectar_tipo(texto: str) -> TipoDoc:
    """Identifica o tipo do documento por palavras-chave no texto."""
    t = texto.upper()

    # DANFE de NF-e (produto)
    if "DANFE" in t and ("NF-E" in t or "NOTA FISCAL ELETR" in t or "NOTAFISCAL" in t):
        if "NFS-E" not in t and "NOTA FISCAL DE SERVI" not in t:
            return "danfe_nfe"

    # NFS-e (serviço)
    if "NFS-E" in t or "NOTA FISCAL DE SERVI" in t or "NOTA FISCAL DE SERVIÇO" in t:
        return "nfse"

    # Nota de débito
    if "NOTA DE DEBITO" in t or "NOTA DE DÉBITO" in t:
        return "nota_debito"

    # Fatura
    if "FATURA" in t or "NFCOM" in t or "COMUNICAÇÃO ELETRÔNICA" in t or "COMUNICACAO ELETRONICA" in t:
        return "fatura"

    # Recibos de locação não-fiscais usados no mesmo fluxo de serviços.
    if "RECIBO DE LOCACAO" in t or "RECIBO DE LOCAÇÃO" in t:
        return "desconhecido"

    return "desconhecido"


def detectar_tipo_pedido(tipo_doc: TipoDoc, texto: str) -> Literal["Produto", "Servico"]:
    """Mapeia o tipo do documento pra Produto ou Servico."""
    if tipo_doc == "danfe_nfe":
        return "Produto"
    if tipo_doc in ("nfse", "nota_debito"):
        return "Servico"
    # Fatura: heurística por palavras-chave
    t = texto.upper()
    if any(p in t for p in ["TELECOM", "INTERNET", "FIBRA", "HOSPEDAGEM", "CLOUD", "LICENC", "ASSINATURA", "MENSAL", "SUPORTE"]):
        return "Servico"
    return "Servico"  # default conservador (faturas raramente são produto)
