"""Utilitários compartilhados pelos parsers de PDF."""
import re
from typing import Optional


# CNPJ formatado: 12.345.678/0001-90
REGEX_CNPJ_FMT = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")
# CNPJ formatado com hífen unicode (alguns docs usam): 12.345.678/0001‐90
REGEX_CNPJ_FMT_UNI = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}[-‐]\d{2}\b")
# CNPJ "limpo": 14 dígitos isolados (não dentro de número maior)
REGEX_CNPJ_BRUTO = re.compile(r"(?<!\d)\d{14}(?!\d)")


def normalizar_cnpj(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


def extrair_cnpjs(texto: str) -> list[str]:
    """Extrai CNPJs do texto, dando preferência aos formatados.

    Estratégia: primeiro pega formatos com pontos/barra/hífen (mais confiáveis);
    depois adiciona CNPJs brutos que ainda não estejam capturados.
    """
    out: list[str] = []
    seen: set[str] = set()

    for regex in (REGEX_CNPJ_FMT, REGEX_CNPJ_FMT_UNI):
        for m in regex.finditer(texto):
            cnpj = normalizar_cnpj(m.group(0))
            if cnpj not in seen and len(cnpj) == 14:
                out.append(cnpj)
                seen.add(cnpj)

    for m in REGEX_CNPJ_BRUTO.finditer(texto):
        cnpj = m.group(0)
        if cnpj not in seen and len(cnpj) == 14:
            out.append(cnpj)
            seen.add(cnpj)

    return out


def parse_decimal_br(s) -> Optional[float]:
    """Converte string em formato BR ou EN para float.
    Trata: '1.234,56', '1234,56', '1234.56', 'R$ 86,00', etc.
    """
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = re.sub(r"R\$\s*", "", s)
    s = s.replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def remover_zeros_esquerda(numero: str) -> str:
    if not numero:
        return ""
    n = re.sub(r"[^\d]", "", str(numero))
    n = n.lstrip("0")
    return n or "0"


def normalizar_nome_arquivo(nome_fornecedor: str, numero_doc: str) -> str:
    nome = (nome_fornecedor or "").strip()
    numero = remover_zeros_esquerda(numero_doc)
    return f"{nome}_{numero}_pc_"
