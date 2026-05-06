"""Parser de fatura de locação (não-fiscal, formato livre).

Calibrado com: i7 ti_955_pc_021797.pdf.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    # Heurística: fatura/recibo de locação tem "FATURA" ou "RECIBO" + "LOCAÇÃO".
    if not ((("FATURA" in upper) or ("RECIBO" in upper)) and ("LOCA" in upper or "LOCAÇÃO" in upper)):
        return ParseResult(template_usado="fatura_locacao", confianca=0.0)

    cnpjs = extrair_cnpjs(texto)
    cnpj_emissor = None
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    nome_emissor = None
    # Pega 2-3 primeiras linhas, busca empresa em maiúscula
    for linha in texto.split("\n")[:8]:
        s = linha.strip()
        if s and any(c.isupper() for c in s) and "@" not in s and len(s) > 3:
            # Limpa: pega só parte sem números/contatos
            limpo = re.sub(r"\(\d+\).*$", "", s).strip()
            if limpo and not limpo.startswith(("Nº", "RUA", "AV", "FATURA")) and len(limpo) > 3:
                nome_emissor = limpo
                break

    # Número: "Nº\nFinanceiro:" ou "FATURA DE\nLOCAÇÃO\nNUMERO"
    numero = None
    m = re.search(r"LOCA[ÇC][AÃ]O\s*\n\s*(\d{4,8})", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"Financeiro:[\s\S]{0,200}?(\d{4,8})\s*\n", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"RECIBO\s+DE\s+LOCA[ÇC][AÃ]O\s*n[º°o]?\s*(\d+)", texto, re.IGNORECASE)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # Itens: tabela "DADOS DO PRODUTO" → CÓDIGO DESCRIÇÃO QUANT. VALOR_UNIT VALOR_TOTAL
    itens: list[ItemExtraido] = []
    bloco = re.search(r"DADOS\s*DO\s*PRODUTO([\s\S]+?)(?=Obra|Boletim|Vencimento|VALOR\s*POR\s*EXTENSO|DADOS\s*ADICIONAIS|$)", texto, re.IGNORECASE)
    if bloco:
        for linha in bloco.group(1).split("\n"):
            s = linha.strip()
            if not s or "DESCRI" in s.upper() or "QUANT" in s.upper():
                continue
            # Padrão: "DESCRICAO 1 839,00 839,00" ou "COD DESC 1 839,00 839,00"
            m = re.match(r"^(.+?)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s*$", s)
            if m:
                desc = m.group(1).strip()
                qtd = parse_decimal_br(m.group(2)) or 1.0
                vu = parse_decimal_br(m.group(3))
                if desc and vu is not None and vu > 0:
                    itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vu))

    # Fallback: total da fatura como item único
    if not itens:
        m = re.search(r"VALOR\s*TOTAL\s*DA\s*FATURA[\s\S]{0,80}?R\$\s*([\d.,]+)", texto, re.IGNORECASE)
        if not m:
            m = re.search(r"Total\s+L[ií]quido\s*\n\s*[\d.,]+\s+[\d.,]+\s+([\d.,]+)", texto, re.IGNORECASE)
        if not m:
            m = re.search(r"Vencimento:[^\n]+?R\$\s*([\d.,]+)", texto, re.IGNORECASE)
        if m:
            v = parse_decimal_br(m.group(1))
            if v:
                # tenta achar descrição em "Natureza da Operação" ou "Objeto da Locação"
                m_nat = re.search(r"Natureza\s*da\s*Opera[çc][aã]o\s*\n([^\n]+)", texto, re.IGNORECASE)
                if not m_nat:
                    m_nat = re.search(r"Objeto\s+da\s+Loca[çc][aã]o:\s*Descri[çc][aã]o\s+Valor\s+Total\s*\n([^\n]+)", texto, re.IGNORECASE)
                desc = m_nat.group(1).strip() if m_nat else "Locação"
                desc = re.sub(r"\s+[\d.]*\d,\d{2}\s*$", "", desc).strip()
                itens.append(ItemExtraido(descricao=desc, quantidade=1.0, valor_unitario=v))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador: confianca += 0.4
    if numero: confianca += 0.2
    if itens: confianca += 0.3
    if nome_emissor: confianca += 0.1

    return ParseResult(
        template_usado="fatura_locacao",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="Fatura",
        itens=itens,
    )
