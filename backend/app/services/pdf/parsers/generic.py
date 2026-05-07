"""Parser genérico — fallback para documentos sem template específico.

Estratégia: extrai apenas os campos comuns (CNPJs, número provável) e
sinaliza baixa confiança. A revisão manual é esperada nesse caminho.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult, ItemExtraido
from app.services.pdf.utils import extrair_cnpjs, parse_decimal_br, remover_zeros_esquerda


REGEX_NUMERO = re.compile(r"(?:N[º°o]?\s*[:.]?\s*|N[uú]mero\s*[:.]?\s*|Fatura\s*[:#]?\s*|Nota\s*[:#]?\s*)([\d\.\-/]{3,})", re.IGNORECASE)
RAIZES_TOMADOR = ("73305997", "67844183")


def parse(texto: str, caminho: Path) -> ParseResult:
    upper = texto.upper()
    cnpjs = extrair_cnpjs(texto)

    cnpj_tomador = None
    cnpj_emissor = None
    for c in cnpjs:
        if c.startswith(RAIZES_TOMADOR):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    nome_emissor = None
    if "EVOLIUM TECHNOLOGIES" in upper or "REDTRUST" in upper:
        nome_emissor = "REDTRUST"

    # Tenta achar número do documento por padrões comuns
    numero = None
    for m in REGEX_NUMERO.finditer(texto):
        candidato = remover_zeros_esquerda(m.group(1))
        if candidato and len(candidato) >= 2:
            numero = candidato
            break

    itens: list[ItemExtraido] = []
    item = _extrair_item_generico(texto)
    if item:
        itens.append(item)

    confianca = 0.5 if (cnpj_tomador and (cnpj_emissor or nome_emissor) and numero) else 0.3
    if itens:
        confianca += 0.3
    if itens and cnpj_tomador and (cnpj_emissor or nome_emissor):
        confianca = max(confianca, 0.8)

    return ParseResult(
        template_usado="generic",
        confianca=min(1.0, confianca),
        cnpj_emissor=cnpj_emissor,
        nome_emissor=nome_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel="Fatura" if itens else None,
        itens=itens,
        observacoes=[] if itens else ["Parser genérico — itens não extraídos automaticamente. Adicione manualmente na revisão."],
    )


def _extrair_item_generico(texto: str) -> ItemExtraido | None:
    padroes_total = [
        r"TOTAL\s+A\s+PAGAR\s*R\$\s*([\d.]+,\d{2})",
        r"Total\s+a\s+pagar\s*R\$\s*([\d.]+,\d{2})",
        r"VALOR\s+TOTAL\s+NF\s*R\$\s*([\d.]+,\d{2})",
        r"Valor\s+L[ií]quido\s+da\s+Nota\s+Fiscal\s*R\$\s*([\d.]+,\d{2})",
        r"VALOR\s+TOTAL\s+COBRADO\s*=\s*R\$\s*([\d.]+,\d{2})",
        r"Total\s*\(BRL\)\s*R\$\s*([\d.]+,\d{2})",
        r"TIM\s*S\.A\.[\s\S]{0,120}?R\$\s*([\d.]+,\d{2})",
    ]
    for padrao in padroes_total:
        m = re.search(padrao, texto, re.IGNORECASE)
        if m:
            valor = parse_decimal_br(m.group(1))
            if valor:
                return ItemExtraido(
                    descricao="Serviço",
                    quantidade=1.0,
                    valor_unitario=valor,
                    valor_unitario_calculado=True,
                )

    padroes_linha = [
        r"^\s*\S+\s+(.+?)\s+1[,.]0\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})\s*$",
        r"Descri[çc][aã]o\s+do\s+Servi[çc]o\s+QTD\s+vlr\s+unit[aá]rio\s+vlr\s+Servi[çc]o\s*\n\s*\d+\s+(.+?)\s+([\d.]+,\d{2})\s+([\d.]+,\d{2})",
    ]
    for padrao in padroes_linha:
        m = re.search(padrao, texto, re.IGNORECASE | re.MULTILINE)
        if m:
            desc = m.group(1).strip()
            valor = parse_decimal_br(m.group(3) if len(m.groups()) >= 3 else m.group(2))
            if desc and valor:
                return ItemExtraido(descricao=desc, quantidade=1.0, valor_unitario=valor)

    return None
