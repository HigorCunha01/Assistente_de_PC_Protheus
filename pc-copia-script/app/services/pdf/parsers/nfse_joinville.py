"""Parser de NFS-e da Prefeitura de Joinville/SC.

Calibrado com: totvs_1340464_pc_397272.pdf.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


def parse(texto: str, caminho: Path) -> ParseResult:
    if "PREFEITURA DE JOINVILLE" not in texto.upper():
        return ParseResult(template_usado="nfse_joinville", confianca=0.0)

    numero = None
    m = re.search(r"N[uú]mero\s*/\s*S[eé]rie\s*\n\s*(\d+)\s*/\s*\w+", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"N[uú]mero\s*/\s*S[eé]rie\s*\n\s*(\d{6,})", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"N[uú]mero\s*/\s*S[eé]rie[\s\S]{0,80}?(\d{6,})", texto, re.IGNORECASE)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    cnpj_emissor = None
    nome_emissor = None
    bloco_prest = re.search(r"PRESTADOR\s*DE\s*SERVI[ÇC]OS([\s\S]+?)TOMADOR\s*DE\s*SERVI[ÇC]OS", texto, re.IGNORECASE)
    if bloco_prest:
        cnpjs_prest = extrair_cnpjs(bloco_prest.group(1))
        if cnpjs_prest:
            cnpj_emissor = cnpjs_prest[0]
        m_nome = re.search(r"Nome\s*empresarial[:\s]+([^\n]+)", bloco_prest.group(1), re.IGNORECASE)
        if not m_nome:
            m_nome = re.search(r"Nome\s*fantasia[:\s]+([^\n]+)", bloco_prest.group(1), re.IGNORECASE)
        if not m_nome:
            m_nome = re.search(r"Raz[aã]o\s*Social[:\s]+([^\n]+)", bloco_prest.group(1), re.IGNORECASE)
        if m_nome:
            nome_emissor = m_nome.group(1).strip()

    cnpj_tomador = None
    bloco_tom = re.search(r"TOMADOR\s*DE\s*SERVI[ÇC]OS([\s\S]+?)(?=DISCRIMINA|$)", texto, re.IGNORECASE)
    if bloco_tom:
        cnpjs_tom = extrair_cnpjs(bloco_tom.group(1))
        for c in cnpjs_tom:
            if c.startswith(("73305997", "67844183")):
                cnpj_tomador = c
                break

    descricao = None
    bloco_disc = re.search(r"DISCRIMINA[ÇC][AÃ]O\s*DOS?\s*SERVI[ÇC]OS([\s\S]+?)(?=VALOR|$)", texto, re.IGNORECASE)
    if bloco_disc:
        # pega primeira linha "útil"
        for l in bloco_disc.group(1).split("\n"):
            s = l.strip()
            if s and len(s) > 5:
                descricao = s
                break
        if descricao and len(descricao) > 200:
            descricao = descricao[:200]

    valor = None
    for chave in [r"VALOR\s*TOTAL\s*DO\s*SERVI[ÇC]O", r"Valor\s*Total\s*\(R\$\)", r"Valor\s*L[ií]quido"]:
        m = re.search(chave + r"[\s\S]{0,80}?([\d.]+,\d{2}|[\d]+[.]\d{2})", texto, re.IGNORECASE)
        if m:
            v = parse_decimal_br(m.group(1))
            if v and v > 0:
                valor = v
                break

    itens: list[ItemExtraido] = []
    if descricao and valor:
        itens.append(ItemExtraido(descricao=descricao, quantidade=1.0, valor_unitario=valor))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador: confianca += 0.4
    if numero: confianca += 0.2
    if itens: confianca += 0.3
    if nome_emissor: confianca += 0.1

    return ParseResult(
        template_usado="nfse_joinville",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NFS-e",
        itens=itens,
    )
