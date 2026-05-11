"""Parser de fatura Blink Telecom (BTT TELECOMUNICACOES).

Calibrado com: blink telecom_14189335.pdf.

A tabela de itens vem em duas linhas:
  Linha 1: descrição (ex: "Blink Fibra Link Semi Dedicado 300M - SCM")
  Linha 2: número R$ valor R$ total %ICMS
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


REGEX_FATURA_NUM = re.compile(r"Fatura[:\s]+(\d+)", re.IGNORECASE)


def parse(texto: str, caminho: Path) -> ParseResult:
    if "BTT TELECOMUNICACOES" not in texto.upper() and "BLINK" not in texto.upper():
        return ParseResult(template_usado="fatura_blink", confianca=0.0)

    cnpjs = extrair_cnpjs(texto)
    cnpj_emissor = None
    cnpj_tomador = None
    raizes = ("73305997", "67844183")
    for c in cnpjs:
        if c.startswith(raizes):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    nome_emissor = "BTT TELECOMUNICACOES S/A"

    numero = None
    m = REGEX_FATURA_NUM.search(texto)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # Itens: pareia descrição (linha N) com valores (linha N+1)
    itens: list[ItemExtraido] = []
    bloco = re.search(
        r"NR\s+DESCRI[ÇC][AÃ]O.+?\n(.+?)(?=\nEstedocumento|\Z)",
        texto, re.IGNORECASE | re.DOTALL,
    )
    if bloco:
        linhas = [l.rstrip() for l in bloco.group(1).split("\n") if l.strip()]
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            # Linha de valores: começa com número, tem "R$" e percentual
            m_val = re.match(r"^\s*(\d+)\s+R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)\s+(\d+)\s*%", linha)
            if m_val:
                # Se é linha de valor mas vinda no meio do bloco, sem desc na anterior, pula
                desc = linhas[i - 1].strip() if i > 0 else ""
                # Não confundir com cabeçalho
                if desc and not re.search(r"DESCRI[ÇC][AÃ]O", desc, re.IGNORECASE):
                    vlr = parse_decimal_br(m_val.group(2))
                    if vlr is not None:
                        itens.append(ItemExtraido(descricao=desc, quantidade=1.0, valor_unitario=vlr))
                i += 1
                continue
            i += 1

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador and numero:
        confianca += 0.6
    if itens:
        confianca += 0.4

    return ParseResult(
        template_usado="fatura_blink",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="Fatura",
        itens=itens,
        observacoes=["Documento sem valor fiscal — confirmar tratamento no Protheus."],
    )
