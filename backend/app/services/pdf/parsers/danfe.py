"""Parser de DANFE (NF-e modelo 55 — produtos).

Calibrado com:
- NF Canaã Material (R. CANUTO DE BRITO)
- NF 1192/1193 (Efigenia CPU - via Bling)

A DANFE é padronizada por legislação. As variações estão em:
- Cabeçalhos da tabela de itens (com/sem espaços)
- Formato dos valores (`960,0000` vs `960,00`)
- Códigos podem grudar com descrição (Bling)
"""
import re
from pathlib import Path
import pdfplumber

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import (
    extrair_cnpjs, normalizar_cnpj, parse_decimal_br, remover_zeros_esquerda,
)


REGEX_NUMERO_NF = re.compile(r"N[º°o]\s*([\d\.]+)", re.IGNORECASE)
REGEX_RECEBEMOS_DE = re.compile(r"RECEBEMOS\s+DE\s+(.+?)\s+OS\s+PRODUTOS", re.IGNORECASE | re.DOTALL)
REGEX_DESTINATARIO_CNPJ = re.compile(
    r"DESTINAT[AÁ]RIO/REMETENTE.*?(\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s]?\d{4}[-\s]?\d{2})",
    re.IGNORECASE | re.DOTALL,
)

# Linha de item: começa com código alfanumérico, NCM (8 dígitos), CST/CSOSN, CFOP, UN, qtd, vlr unit, vlr total
# Padrão observado nos exemplos:
#   01 CABO SOHO PLUS CAT5 e 85441100 0400 5101 UN 1,0000 960,0000 960,00
#   3454 BATERIA DELL IMPORTADA 85071090 0400 5.102 UN 1,00 360,00 360,00 ...
REGEX_LINHA_ITEM = re.compile(
    r"^(?P<cod>\S+?)\s+"
    r"(?P<desc>.+?)\s+"
    r"(?P<ncm>\d{8})\s+"
    r"\d+\s+"                          # CST/CSOSN
    r"\d+[\.\d]*\s+"                   # CFOP (pode ter ponto)
    r"(?P<un>[A-Za-z]{1,4})\s+"
    r"(?P<qtd>[\d.,]+)\s+"
    r"(?P<vunit>[\d.,]+)\s+"
    r"(?P<vtot>[\d.,]+)",
    re.MULTILINE,
)


def parse(texto: str, caminho: Path) -> ParseResult:
    if "DANFE" not in texto.upper():
        return ParseResult(template_usado="danfe", confianca=0.0)

    cnpjs = extrair_cnpjs(texto)

    # Emissor: primeiro CNPJ que NÃO comece com raízes do tomador
    cnpj_emissor = None
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    # Nome emissor (do "RECEBEMOS DE")
    nome_emissor = None
    m = REGEX_RECEBEMOS_DE.search(texto)
    if m:
        nome_emissor = " ".join(m.group(1).split())

    # Número da NF
    numero = None
    for m in REGEX_NUMERO_NF.finditer(texto):
        candidato = remover_zeros_esquerda(m.group(1))
        if candidato and len(candidato) >= 2 and candidato.isdigit():
            numero = candidato
            break

    # Itens — tenta primeiro extract_tables (mais robusto), depois regex linha
    itens = _extrair_itens_via_tabela(caminho)
    if not itens:
        itens = _extrair_itens_via_regex(texto)

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador and numero:
        confianca += 0.5
    if itens:
        confianca += 0.4
    if nome_emissor:
        confianca += 0.1

    obs = []
    if not itens:
        obs.append("Não foi possível extrair itens da DANFE — adicionar manualmente.")

    return ParseResult(
        template_usado="danfe",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="Nota Fiscal",
        itens=itens,
        observacoes=obs,
    )


def _extrair_itens_via_tabela(caminho: Path) -> list[ItemExtraido]:
    """Tenta extrair tabela de itens via pdfplumber.extract_tables()."""
    itens: list[ItemExtraido] = []
    try:
        with pdfplumber.open(str(caminho)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    cabec = [str(c or "").upper() for c in table[0]] if table else []
                    if not _eh_tabela_de_itens(cabec):
                        continue
                    idx = _mapear_colunas(cabec)
                    if not idx:
                        continue
                    for row in table[1:]:
                        if not row:
                            continue
                        item = _parse_row_item(row, idx)
                        if item:
                            itens.append(item)
                    if itens:
                        return itens
    except Exception:
        pass
    return itens


def _eh_tabela_de_itens(cabec: list[str]) -> bool:
    txt = " ".join(cabec)
    return ("DESCRI" in txt and "QTD" in txt) or ("DESCRI" in txt and "QUANT" in txt)


def _mapear_colunas(cabec: list[str]) -> dict | None:
    idx = {}
    for i, c in enumerate(cabec):
        cu = c.upper()
        if "DESCRI" in cu and "desc" not in idx:
            idx["desc"] = i
        elif ("QTD" in cu or "QUANT" in cu) and "qtd" not in idx:
            idx["qtd"] = i
        elif ("VLR. UNIT" in cu or "VLR.UNIT" in cu or "PRE" in cu and "UN" in cu) and "vunit" not in idx:
            idx["vunit"] = i
    if "desc" in idx and "qtd" in idx and "vunit" in idx:
        return idx
    return None


def _parse_row_item(row: list, idx: dict) -> ItemExtraido | None:
    desc = (row[idx["desc"]] or "").strip() if idx["desc"] < len(row) else ""
    qtd = parse_decimal_br(row[idx["qtd"]]) if idx["qtd"] < len(row) else None
    vunit = parse_decimal_br(row[idx["vunit"]]) if idx["vunit"] < len(row) else None
    if not desc or qtd is None or vunit is None:
        return None
    return ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vunit)


def _corrigir_descricao_com_codigo_grudado(codigo: str, descricao: str) -> str:
    """Move trecho textual grudado no código para a descrição.

    Alguns DANFEs emitidos pelo Bling saem sem espaço entre código/CFOP e a
    primeira palavra da descrição, por exemplo: ``CFOP5102Memoria notebook``.
    """
    m = re.match(r"^(?:CFOP)?\d{4,}([A-Za-zÀ-ÿ].*)$", codigo or "")
    if not m:
        return descricao
    return f"{m.group(1).strip()} {descricao}".strip()


def _extrair_itens_via_regex(texto: str) -> list[ItemExtraido]:
    """Fallback: extrai itens via regex linha-a-linha."""
    itens: list[ItemExtraido] = []
    # Restringe à seção dos produtos pra reduzir falso-positivo
    inicio = 0
    for marcador in ["DADOS DO PRODUTO", "Itens da nota fiscal", "DADOS DOS PRODUTOS"]:
        idx = texto.upper().find(marcador.upper())
        if idx > 0:
            inicio = idx
            break
    fim = texto.upper().find("CÁLCULO DO ISSQN", inicio) or len(texto)
    if fim <= 0:
        fim = len(texto)
    secao = texto[inicio:fim]

    for m in REGEX_LINHA_ITEM.finditer(secao):
        try:
            desc = _corrigir_descricao_com_codigo_grudado(
                m.group("cod").strip(),
                m.group("desc").strip(),
            )
            qtd = parse_decimal_br(m.group("qtd"))
            vunit = parse_decimal_br(m.group("vunit"))
            if desc and qtd is not None and vunit is not None:
                itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vunit))
        except Exception:
            continue
    return itens
