"""Parser genérico — fallback para documentos sem template específico.

Estratégia: extrai apenas os campos comuns (CNPJs, número provável) e
sinaliza baixa confiança. A revisão manual é esperada nesse caminho.
"""
import re
from pathlib import Path

from app.services.pdf.parsers.base import ParseResult
from app.services.pdf.utils import extrair_cnpjs, remover_zeros_esquerda


REGEX_NUMERO = re.compile(r"(?:N[º°o]?\s*[:.]?\s*|N[uú]mero\s*[:.]?\s*|Fatura\s*[:#]?\s*|Nota\s*[:#]?\s*)([\d\.\-/]{3,})", re.IGNORECASE)
RAIZES_TOMADOR = ("73305997", "67844183")


def parse(texto: str, caminho: Path) -> ParseResult:
    cnpjs = extrair_cnpjs(texto)

    cnpj_tomador = None
    cnpj_emissor = None
    for c in cnpjs:
        if c.startswith(RAIZES_TOMADOR):
            cnpj_tomador = cnpj_tomador or c
        else:
            cnpj_emissor = cnpj_emissor or c

    # Tenta achar número do documento por padrões comuns
    numero = None
    for m in REGEX_NUMERO.finditer(texto):
        candidato = remover_zeros_esquerda(m.group(1))
        if candidato and len(candidato) >= 2:
            numero = candidato
            break

    confianca = 0.5 if (cnpj_tomador and cnpj_emissor and numero) else 0.3

    return ParseResult(
        template_usado="generic",
        confianca=confianca,
        cnpj_emissor=cnpj_emissor,
        cnpj_tomador=cnpj_tomador,
        numero_documento=numero,
        tipo_documento_legivel=None,
        itens=[],
        observacoes=["Parser genérico — itens não extraídos automaticamente. Adicione manualmente na revisão."],
    )
