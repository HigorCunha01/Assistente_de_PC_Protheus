"""Parser de NFS-e Pinhais (Prefeitura de Pinhais/PR).

Calibrado com: solo network_177288.pdf.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    if "PREFEITURA MUNICIPAL DE PINHAIS" not in upper:
        return ParseResult(template_usado="nfse_pinhais", confianca=0.0)

    linhas = texto.split("\n")

    # Nome emissor: primeira linha não-vazia, recortando antes de "Número"
    nome_emissor = None
    for l in linhas:
        s = l.strip()
        if s:
            nome_emissor = re.split(r"N[uú]mero", s, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            break

    # CNPJs
    cnpjs = extrair_cnpjs(texto)
    cnpj_emissor = None
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    # Número: na linha que tem o CNPJ formatado do emissor, o último grupo de dígitos = número da NFS-e
    numero = None
    if cnpj_emissor:
        for l in linhas:
            if cnpj_emissor[:2] + "." in l or re.search(r"CNPJ", l, re.IGNORECASE):
                # captura todos números >= 3 dígitos NÃO contidos em formato de CNPJ
                # remove a parte do CNPJ formatado pra evitar pegar pedaços dele
                limpo = re.sub(r"\d{2}\.\d{3}\.\d{3}/\d{4}[‐\-]\d{2}", " ", l)
                nums = re.findall(r"\b\d{3,10}\b", limpo)
                if nums:
                    numero = remover_zeros_esquerda(nums[-1])
                    break

    # Itens: "Descrição do Serviço:..." + valor líquido
    descricao = None
    qtd = 1.0
    m_desc = re.search(r"Descri[çc][aã]o do Servi[çc]o[:\s]*([^\n]+)", texto, re.IGNORECASE)
    if m_desc:
        descricao = m_desc.group(1).strip()
        m_qtd = re.search(r"qtde[:\s]*([\d.,]+)", descricao, re.IGNORECASE)
        if m_qtd:
            qtd = parse_decimal_br(m_qtd.group(1)) or 1.0

    valor = None
    for chave in ["Valor\\s+L[ií]quido", "Valor\\s+Servi[çc]o", "Valor\\s+Total"]:
        m = re.search(chave + r"[\s\S]{0,80}?([\d.]+,\d{2}|[\d]+[.]\d{2})", texto, re.IGNORECASE)
        if m:
            v = parse_decimal_br(m.group(1))
            if v and v > 0:
                valor = v
                break

    itens: list[ItemExtraido] = []
    if descricao and valor and qtd > 0:
        vu = valor / qtd if qtd != 1 else valor
        itens.append(ItemExtraido(
            descricao=descricao,
            quantidade=qtd,
            valor_unitario=vu,
            valor_unitario_calculado=qtd != 1,
        ))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador: confianca += 0.4
    if numero: confianca += 0.2
    if itens: confianca += 0.3
    if nome_emissor: confianca += 0.1

    return ParseResult(
        template_usado="nfse_pinhais",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NFS-e",
        itens=itens,
    )
