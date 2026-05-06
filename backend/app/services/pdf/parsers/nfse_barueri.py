"""Parser de NFS-e Barueri (Prefeitura de Barueri/SP).

Calibrado com: snd_347331.PDF (SND DISTRIBUIÇÃO).
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


REGEX_NOTA = re.compile(r"Nota[:\s]+(\d+)", re.IGNORECASE)
REGEX_TOMADOR_BLOCO = re.compile(
    r"TOMADOR DE SERVI[ÇC]OS(.+?)C[oó]digo Tributa",
    re.IGNORECASE | re.DOTALL,
)
REGEX_PRESTADOR_BLOCO = re.compile(
    r"PRESTADOR DE SERVI[ÇC]OS(.+?)TOMADOR",
    re.IGNORECASE | re.DOTALL,
)
REGEX_DESCRICAO_BLOCO = re.compile(
    r"DESCRI[ÇC][AÃ]O DOS SERVI[ÇC]OS(.+?)(?:RETEN[ÇC]|VALORES)",
    re.IGNORECASE | re.DOTALL,
)
REGEX_VLR_TOTAL = re.compile(r"Valor\s+Total\s+da\s+Nota.*?\(R\s*\$\s*\)\s*\n?([\d.,\s]+)", re.IGNORECASE | re.DOTALL)


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    if "PREFEITURA MUNICIPAL DE BARUERI" not in upper:
        return ParseResult(template_usado="nfse_barueri", confianca=0.0)

    # Nota
    numero = None
    m = REGEX_NOTA.search(texto)
    if m:
        numero = remover_zeros_esquerda(m.group(1))

    # CNPJs em blocos específicos pra evitar trocar emissor/tomador
    cnpj_emissor = None
    nome_emissor = None
    bloco_prest = REGEX_PRESTADOR_BLOCO.search(texto)
    if bloco_prest:
        cnpjs = extrair_cnpjs(bloco_prest.group(1))
        if cnpjs:
            cnpj_emissor = cnpjs[0]
        # Nome: primeira linha não-vazia depois de "Razão Social"
        m_nome = re.search(r"Raz[aã]o Social\s*\n?\s*CPF/CNPJ\s*\n?\s*([^\n]+)", bloco_prest.group(1))
        if m_nome:
            nome_emissor = m_nome.group(1).strip()

    cnpj_tomador = None
    bloco_tom = REGEX_TOMADOR_BLOCO.search(texto)
    if bloco_tom:
        cnpjs = extrair_cnpjs(bloco_tom.group(1))
        if cnpjs:
            cnpj_tomador = cnpjs[0]

    # Itens — Barueri costuma ter um único bloco descritivo, não tabular
    itens: list[ItemExtraido] = []
    bloco_desc = REGEX_DESCRICAO_BLOCO.search(texto)
    if bloco_desc:
        desc_raw = bloco_desc.group(1).strip()
        # heurística: pega qtd a partir de "Quant. X,XX" e descrição da linha
        m_qtd = re.search(r"Quant[.,]?\s*([\d.,]+)", desc_raw, re.IGNORECASE)
        qtd = parse_decimal_br(m_qtd.group(1)) if m_qtd else 1.0

        # Valor total da nota como unitário (1 item)
        vlr_unit = None
        m_vt = REGEX_VLR_TOTAL.search(texto)
        if m_vt:
            valores = re.findall(r"[\d.,]+", m_vt.group(1))
            if valores:
                vlr_unit = parse_decimal_br(valores[-1])  # último número antes do enter

        if not vlr_unit:
            # tenta achar "Valor dos Serviços"
            m_vs = re.search(r"Valor dos Servi[çc]os\s*\(\s*R\s*\$\s*\)([\d.,\s]+)", texto, re.IGNORECASE)
            if m_vs:
                valores = re.findall(r"[\d.,]+", m_vs.group(1))
                if valores:
                    vlr_unit = parse_decimal_br(valores[0])

        # Descrição limpa: pega tudo após "Quant. X,XX -" até quebra de linha
        descricao = desc_raw
        m_desc = re.search(r"Quant[.,]?\s*[\d.,]+\s*-\s*(.+)", desc_raw, re.IGNORECASE)
        if m_desc:
            descricao = m_desc.group(1).strip().split("\n")[0].strip()

        if vlr_unit is not None and qtd is not None and qtd > 0:
            # Se vlr_unit for o total (típico em NFS-e de 1 serviço), divide pra obter unitário
            unit_calc = False
            if qtd != 1:
                vlr_unit = vlr_unit / qtd
                unit_calc = True
            itens.append(ItemExtraido(
                descricao=descricao,
                quantidade=qtd,
                valor_unitario=vlr_unit,
                valor_unitario_calculado=unit_calc,
            ))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador and numero:
        confianca += 0.6
    if itens:
        confianca += 0.3
    if nome_emissor:
        confianca += 0.1

    return ParseResult(
        template_usado="nfse_barueri",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NFS-e",
        itens=itens,
    )
