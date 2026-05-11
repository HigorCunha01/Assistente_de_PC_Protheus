"""Parser de NFS-e no formato DANFSe v1.0 (padrão nacional novo).

Calibrado com:
- spirit it_12_pc_021798.pdf (Atibaia)
- telegestao_1463_pc_021799.pdf (Porto Alegre)
- aprovador_1501_397277.pdf (Belo Horizonte)
- brazpine_232_pc_021785.pdf (São Leopoldo)
- ronditech.pdf (Atibaia)
- team ti_9570_397268.pdf (Cuiabá)

Layout comum: tem "DANFSe v1.0", bloco "EMITENTE DA NFS-e", bloco "TOMADOR DO SERVIÇO",
"Número da NFS-e" + valor numérico, "Descrição do Serviço".
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper().replace(" ", "")
    if "DANFSE" not in upper and "DANFSEV1" not in upper:
        return ParseResult(template_usado="nfse_danfse_nacional", confianca=0.0)

    # Texto pode vir colado (sem espaços) ou normal — normaliza adicionando espaços antes de palavras-chave
    # Mas isso é destrutivo. Vamos trabalhar com o texto original e usar regex flexíveis.

    # Número da NFS-e: vem após "Número da NFS-e" (com ou sem espaços)
    numero = None
    # Tenta achar bloco "Número da NFS-e ... NUM"
    pat = re.compile(r"N[uú]mero\s*da\s*NFS[‐\-]?e[\s\S]{0,80}?(\d{1,12})", re.IGNORECASE)
    m = pat.search(texto)
    if m:
        numero = remover_zeros_esquerda(m.group(1))
    # Fallback: versão "colada"
    if not numero:
        pat2 = re.compile(r"N[uú]merodaNFS[‐\-]?e[\s\S]{0,80}?(\d{1,12})", re.IGNORECASE)
        m = pat2.search(texto)
        if m:
            numero = remover_zeros_esquerda(m.group(1))

    # Bloco emitente: pega CNPJ que vem após "EMITENTE" e antes de "TOMADOR"
    cnpj_emissor = None
    nome_emissor = None
    bloco_emi = re.search(r"EMITENTE\s*DA\s*NFS[‐\-]?e([\s\S]+?)TOMADOR", texto, re.IGNORECASE)
    if not bloco_emi:
        bloco_emi = re.search(r"EMITENTEDANFS[‐\-]?e([\s\S]+?)TOMADOR", texto, re.IGNORECASE)
    if bloco_emi:
        cnpjs_emi = extrair_cnpjs(bloco_emi.group(1))
        if cnpjs_emi:
            cnpj_emissor = cnpjs_emi[0]
        # Nome empresarial: aparece após "Nome / Nome Empresarial" ou "Nome/NomeEmpresarial"
        m_nome = re.search(
            r"Nome\s*/?\s*Nome\s*Empresarial[\s\S]{0,30}?E[\-\s]?mail[\s\S]{0,5}?\n?([^\n]+)",
            bloco_emi.group(1), re.IGNORECASE
        )
        if m_nome:
            nome_emissor = m_nome.group(1).strip()
        else:
            # tenta versão sem espaços: pega primeira linha após CNPJ que pareça nome
            for linha in bloco_emi.group(1).split("\n"):
                s = linha.strip()
                if s and s.isupper() and "EMPRESARIAL" not in s and "CNPJ" not in s and "@" not in s and len(s) > 10:
                    nome_emissor = s
                    break

    # Bloco tomador
    cnpj_tomador = None
    bloco_tom = re.search(r"TOMADOR[\s\S]+?(?=INTERMEDI|SERVI[ÇC]O\s*PRESTADO|$)", texto, re.IGNORECASE)
    if bloco_tom:
        cnpjs_tom = extrair_cnpjs(bloco_tom.group(0))
        for c in cnpjs_tom:
            if c.startswith(("73305997", "67844183")):
                cnpj_tomador = c
                break

    # Itens: 2 padrões observados
    # (A) Múltiplos itens em "Descricao do Servico" com formato:
    #     "1 - Servico: NOME - QTD: 1. - Valor Unit: 2320.59"
    # (B) Único item na descrição, valor total no final
    itens: list[ItemExtraido] = []
    bloco_desc = re.search(
        r"Descri[çc][aã]o\s*do\s*Servi[çc]o([\s\S]+?)(?=TRIBUTA[ÇC][AÃ]O|VALOR\s*TOTAL|$)",
        texto, re.IGNORECASE
    )
    if not bloco_desc:
        bloco_desc = re.search(
            r"DescriçãodoServiço([\s\S]+?)(?=TRIBUTA[ÇC][AÃ]O|VALORTOTAL|$)",
            texto, re.IGNORECASE
        )

    if bloco_desc:
        desc_text = bloco_desc.group(1).strip()
        # Padrão A
        pat_item = re.compile(
            r"\d+\s*-\s*Servico:\s*([^-]+?)\s*-\s*QTD:\s*([\d.,]+)\.?\s*-\s*Valor\s*Unit:\s*([\d.,]+)",
            re.IGNORECASE,
        )
        for m in pat_item.finditer(desc_text):
            d = m.group(1).strip()
            q = parse_decimal_br(m.group(2)) or 1.0
            v = parse_decimal_br(m.group(3))
            if d and v is not None:
                itens.append(ItemExtraido(descricao=d, quantidade=q, valor_unitario=v))

        # Padrão B: 1 item único - usa primeira linha como descrição + valor total
        if not itens:
            primeira_linha = desc_text.split("\n")[0].strip()
            # Limita o tamanho da descrição
            if len(primeira_linha) > 200:
                primeira_linha = primeira_linha[:200]
            # Procura "Valor Total" / "Valor do Serviço" no texto inteiro
            valor = None
            for chave in [
                r"Valor\s*Total\s*\(R\$\)",
                r"Valor\s*do\s*Servi[çc]o",
                r"ValorTotal",
                r"VALOR\s*TOTAL\s*DO\s*SERVI[ÇC]O",
            ]:
                m = re.search(chave + r"[\s\S]{0,80}?([\d.]+,\d{2}|[\d]+[.]\d{2})", texto, re.IGNORECASE)
                if m:
                    v = parse_decimal_br(m.group(1))
                    if v and v > 0:
                        valor = v
                        break
            if primeira_linha and valor:
                itens.append(ItemExtraido(descricao=primeira_linha, quantidade=1.0, valor_unitario=valor))

    confianca = 0.0
    if cnpj_emissor and cnpj_tomador: confianca += 0.4
    if numero: confianca += 0.2
    if itens: confianca += 0.3
    if nome_emissor: confianca += 0.1

    return ParseResult(
        template_usado="nfse_danfse_nacional",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="NFS-e",
        itens=itens,
    )
