"""Parser de NFS-e da Prefeitura de São Paulo (formato antigo).

Calibrado com:
- Thiago Covre_462_pc_397270.pdf
- totvs_1041187_pc_397271.pdf
- veti_6584_pc_397275.pdf
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    if "PREFEITURA DO MUNICÍPIO DE SÃO PAULO" not in upper and "PREFEITURA DO MUNICIPIO DE SAO PAULO" not in upper:
        return ParseResult(template_usado="nfse_sao_paulo", confianca=0.0)

    # Número da Nota: aparece em linha logo após o cabeçalho
    numero = None
    m = re.search(r"N[uú]mero\s*da\s*Nota\s*\n\s*PREFEITURA[\s\S]+?\n\s*(\d+)", texto, re.IGNORECASE)
    if not m:
        m = re.search(r"PREFEITURA\s*DO\s*MUN[\s\S]+?\n\s*(\d{4,10})", texto, re.IGNORECASE)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # Prestador
    cnpj_emissor = None
    nome_emissor = None
    bloco_prest = re.search(r"PRESTADOR\s*DE\s*SERVI[ÇC]OS([\s\S]+?)TOMADOR\s*DE\s*SERVI[ÇC]OS", texto, re.IGNORECASE)
    if bloco_prest:
        cnpjs_prest = extrair_cnpjs(bloco_prest.group(1))
        if cnpjs_prest:
            cnpj_emissor = cnpjs_prest[0]
        m_nome = re.search(r"Nome/Raz[aã]o\s*Social[:\s]+([^\n]+)", bloco_prest.group(1), re.IGNORECASE)
        if m_nome:
            nome_emissor = m_nome.group(1).strip()

    # Tomador
    cnpj_tomador = None
    bloco_tom = re.search(r"TOMADOR\s*DE\s*SERVI[ÇC]OS([\s\S]+?)(?=INTERMEDI|DISCRIMINA|$)", texto, re.IGNORECASE)
    if bloco_tom:
        cnpjs_tom = extrair_cnpjs(bloco_tom.group(1))
        for c in cnpjs_tom:
            if c.startswith(("73305997", "67844183")):
                cnpj_tomador = c
                break

    # Item: descrição em "DISCRIMINAÇÃO DE SERVIÇOS", valor em "VALOR TOTAL DO SERVIÇO = R$"
    descricao = None
    bloco_disc = re.search(r"DISCRIMINA[ÇC][AÃ]O\s*DE\s*SERVI[ÇC]OS([\s\S]+?)VALOR\s*TOTAL", texto, re.IGNORECASE)
    if bloco_disc:
        descricao = bloco_disc.group(1).strip().split("\n")[0].strip()
        if len(descricao) > 200:
            descricao = descricao[:200]

    valor = None
    m_val = re.search(r"VALOR\s*TOTAL\s*DO\s*SERVI[ÇC]O\s*=?\s*R\$\s*([\d.,]+)", texto, re.IGNORECASE)
    if m_val:
        valor = parse_decimal_br(m_val.group(1))

    itens: list[ItemExtraido] = []
    if descricao and valor:
        itens.append(ItemExtraido(descricao=descricao, quantidade=1.0, valor_unitario=valor))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador: confianca += 0.4
    if numero: confianca += 0.2
    if itens: confianca += 0.3
    if nome_emissor: confianca += 0.1

    return ParseResult(
        template_usado="nfse_sao_paulo",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NFS-e",
        itens=itens,
    )
