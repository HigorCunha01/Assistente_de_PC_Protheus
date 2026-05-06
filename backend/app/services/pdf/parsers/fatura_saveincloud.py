"""Parser de fatura SaveInCloud (IP Company).

Calibrado com: save in cloud_261967.pdf.

Particularidade: PDF não traz CNPJ do emissor. Identificamos por nome
e fazemos lookup posterior na planilha de Fornecedores.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


REGEX_FATURA = re.compile(r"Fatura\s*#?\s*(\d+)", re.IGNORECASE)
# Itens: descrição [tab/spaces] R$VALOR
REGEX_ITEM = re.compile(r"^([A-Za-zÀ-ÿ][^\n]*?)\s+R\$\s*([\d.,]+)\s*$", re.MULTILINE)
PALAVRAS_RESERVADAS = {"sub-total", "subtotal", "crédito", "credito", "total", "balanço", "balanco", "dt", "data"}


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    if "SAVEINCLOUD" not in upper.replace(" ", "") and "SAVE IN CLOUD" not in upper:
        return ParseResult(template_usado="fatura_saveincloud", confianca=0.0)

    nome_emissor = "SaveInCloud"

    # Tomador
    cnpjs = extrair_cnpjs(texto)
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = c
            break

    # Sem CNPJ do emissor no PDF — deixa em branco; lookup será por nome
    cnpj_emissor = None

    numero = None
    m = REGEX_FATURA.search(texto)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # Itens
    itens: list[ItemExtraido] = []
    inicio = texto.find("Descrição")
    fim = texto.find("Sub-total", inicio if inicio > 0 else 0)
    secao = texto[inicio:fim] if (inicio > 0 and fim > inicio) else texto

    for m in REGEX_ITEM.finditer(secao):
        desc = m.group(1).strip()
        if desc.lower() in PALAVRAS_RESERVADAS:
            continue
        vlr = parse_decimal_br(m.group(2))
        if desc and vlr is not None:
            itens.append(ItemExtraido(descricao=desc, quantidade=1.0, valor_unitario=vlr))

    confianca = 0.0
    if cnpj_tomador and numero:
        confianca += 0.5
    if itens:
        confianca += 0.4
    confianca += 0.1  # nome_emissor sempre identificado

    obs = ["CNPJ do emissor não consta no PDF — lookup do fornecedor por nome."]

    return ParseResult(
        template_usado="fatura_saveincloud",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="Fatura",
        itens=itens,
        observacoes=obs,
    )
