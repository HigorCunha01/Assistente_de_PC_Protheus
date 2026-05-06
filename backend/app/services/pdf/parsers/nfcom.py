"""Parser de NFCom (Nota Fiscal de Comunicação Eletrônica) — provedores de internet.

Calibrado com: bairronet_2381_pc_021786.pdf (BR PROVEDOR LTDA).
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, normalizar_cnpj, parse_decimal_br, remover_zeros_esquerda


def _extrair_total_nf(texto: str):
    padroes = [
        r"VALOR\s+TOTAL\s+NF\s*([\d.]+,\d{2}|[\d]+[.]\d{2})",
        r"TOTAL\s+A\s+PAGAR\s*(?:-\s*R\$|R\$|:)?\s*([\d.]+,\d{2}|[\d]+[.]\d{2})",
        r"TOTAL\s+A\s+PAGAR[\s\S]{0,30}?([\d.]+,\d{2}|[\d]+[.]\d{2})",
    ]
    for padrao in padroes:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            valor = parse_decimal_br(m.group(1))
            if valor:
                return valor
    return None


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    if (
        "FATURA DE SERVIÇOS DE COMUNICAÇÃO" not in upper
        and "FATURA DE SERVICOS DE COMUNICACAO" not in upper
        and "SERVIÇO DE COMUNICAÇÃO ELETRÔNICA" not in upper
        and "SERVICO DE COMUNICACAO ELETRONICA" not in upper
        and "COMUNICAÇÃO ELETRÔNICA" not in upper
        and "COMUNICACAO ELETRONICA" not in upper
        and "NFCOM" not in upper
    ):
        return ParseResult(template_usado="nfcom", confianca=0.0)

    cnpjs = extrair_cnpjs(texto)
    cnpj_emissor = None
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    if not cnpj_tomador:
        m_tomador_ruidoso = re.search(r"CPF/CNP[\s\S]{0,40}?((?:\D*\d){14})", texto, re.IGNORECASE)
        if m_tomador_ruidoso:
            cnpj_ruidoso = normalizar_cnpj(m_tomador_ruidoso.group(1))
            if cnpj_ruidoso.startswith(raizes):
                cnpj_tomador = cnpj_ruidoso

    # Nome emissor: linha antes do CNPJ do emissor
    nome_emissor = None
    linhas = texto.split("\n")
    for i, l in enumerate(linhas):
        if "CNPJ" in l and cnpj_emissor and (cnpj_emissor[:2] + ".") in l:
            for j in range(i - 1, max(-1, i - 4), -1):
                cand = linhas[j].strip()
                if cand and cand.isupper() and len(cand) > 3 and "RECEBEMOS" not in cand:
                    nome_emissor = cand
                    break
            break

    # Número: NOTA FISCAL FATURA Nº
    numero = None
    m = re.search(r"NOTA\s*FISCAL\s*FATURA\s*N[º°]?\s*(\d+)", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"NOTA\s*FISCAL\s*(?:FATURA\s*)?(?:No\.?|N[º°]?)\s*(\d+)", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"N[º°]?\s*NFCOM\s*(\d+)", texto, re.IGNORECASE)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # Itens: tabela "COD. ITENS UN QTD V. UNIT. TOTAL"
    itens: list[ItemExtraido] = []
    bloco = re.search(
        r"(?:COD\.\s*ITENS|ITENS\s+DA\s+FATURA)[\s\S]+?\n([\s\S]+?)(?=VALOR\s*(?:NFF|TOTAL\s*NF)|TOTAL\s*BC\s*ICMS|TOTAL\s+BASE\s+DE\s+C[ÁA]LCULO|INFORMA[ÇC][ÕO]ES\s+COMPLEMENTARES|$)",
        texto,
        re.IGNORECASE,
    )
    if bloco:
        linhas = [l.strip() for l in bloco.group(1).split("\n") if l.strip()]
        for idx, linha in enumerate(linhas):
            # Padrão com código, descrição, CFOP opcional, unidade, quantidade, unitário e total.
            m = re.match(
                r"^\s*\S+\s+(.+?)\s+(?:\d{4}\s+)?([A-Z]{1,4})\s+([\d.,]+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)",
                linha,
                re.IGNORECASE,
            )
            if m:
                desc = m.group(1).strip()
                qtd = parse_decimal_br(m.group(3)) or 1.0
                vu = parse_decimal_br(m.group(4))
                if desc and vu is not None:
                    itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vu))
                continue

            # Padrão multiline: descrição na linha anterior/seguinte e valores na linha do código.
            m = re.match(r"^\s*\d{7}\s+(?:UN|[A-Z]{1,4})\s+([\d.,]+)\s+([\d.,]+)\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)", linha, re.IGNORECASE)
            if m:
                partes_desc = []
                if idx > 0 and not re.match(r"^\d", linhas[idx - 1]):
                    partes_desc.append(linhas[idx - 1])
                if idx + 1 < len(linhas) and not re.match(r"^\d", linhas[idx + 1]) and "VALOR" not in linhas[idx + 1].upper():
                    partes_desc.append(linhas[idx + 1])
                desc = " ".join(partes_desc).strip() or "Serviço de comunicação"
                qtd = parse_decimal_br(m.group(1)) or 1.0
                vu = parse_decimal_br(m.group(2))
                if vu is not None:
                    itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vu))
                continue

            # Padrão OCR com separadores visuais: DESCRICAO CODIGO | UN | QTD VALOR ...
            m = re.match(r"^(.+?)\s+\d{6,7}\s*\|?\s*UN\s*\|?\s*([\d.,]+)\s*\|?\s+([\d.,]+)", linha, re.IGNORECASE)
            if m:
                desc = m.group(1).strip(" |")
                qtd = parse_decimal_br(m.group(2)) or 1.0
                vu = parse_decimal_br(m.group(3))
                if desc and vu is not None:
                    itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vu))
                continue

            # Padrão sem código: DESCRICAO UN QTD UNIT TOTAL ...
            m = re.match(r"^(?!\d)(.+?)\s+UN\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\b", linha, re.IGNORECASE)
            if m:
                desc = m.group(1).strip()
                qtd = parse_decimal_br(m.group(2)) or 1.0
                vu = parse_decimal_br(m.group(3))
                if desc and vu is not None:
                    itens.append(ItemExtraido(descricao=desc, quantidade=qtd, valor_unitario=vu))

    valor_total_nf = _extrair_total_nf(texto)
    if valor_total_nf and ("TELEFONICA BRASIL" in upper or "TELEFÔNICA BRASIL" in upper or "VIVO.COM" in upper):
        itens = [ItemExtraido(
            descricao="Serviços de telecomunicação",
            quantidade=1.0,
            valor_unitario=valor_total_nf,
            valor_unitario_calculado=True,
        )]

    if not itens and valor_total_nf:
        itens.append(ItemExtraido(
            descricao="Serviços de comunicação",
            quantidade=1.0,
            valor_unitario=valor_total_nf,
            valor_unitario_calculado=True,
        ))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador and numero: confianca += 0.6
    if itens: confianca += 0.4

    return ParseResult(
        template_usado="nfcom",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NF Comunicação",
        itens=itens,
    )
