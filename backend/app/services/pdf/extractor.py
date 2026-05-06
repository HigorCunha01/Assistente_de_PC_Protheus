"""Pipeline principal de extração de PDF."""
from dataclasses import asdict, is_dataclass
from pathlib import Path
import pdfplumber
import pypdfium2 as pdfium
import pytesseract

from app.services.pdf.detector import detectar_tipo, detectar_tipo_pedido
from app.services.pdf.parsers import (
    danfe, nfse_barueri, nfse_pinhais, nfse_danfse_nacional, nfse_sao_paulo, nfse_joinville,
    fatura_blink, fatura_saveincloud, fatura_locacao, nfcom, generic
)
from app.services.pdf.utils import normalizar_nome_arquivo
from app.services.referencias import filial_por_cnpj, fornecedor_por_cnpj


# Ordem importa: parsers mais específicos primeiro, genérico por último
PARSERS_POR_TIPO = {
    "danfe_nfe": [danfe.parse],
    "nfse": [
        nfse_danfse_nacional.parse,  # padrão nacional novo
        nfse_sao_paulo.parse,
        nfse_joinville.parse,
        nfse_barueri.parse,
        nfse_pinhais.parse,
        fatura_locacao.parse,  # fallback p/ docs que mencionam NFS-e mas são fatura
        generic.parse,
    ],
    "fatura": [fatura_blink.parse, fatura_saveincloud.parse, fatura_locacao.parse, nfcom.parse, generic.parse],
    "nota_debito": [generic.parse],
    "desconhecido": [nfcom.parse, fatura_locacao.parse, nfse_danfse_nacional.parse, generic.parse],
}


def _ler_texto_nativo(caminho: Path) -> str:
    with pdfplumber.open(str(caminho)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def _ler_texto_ocr(caminho: Path) -> str:
    """Renderiza páginas sem texto e aplica OCR.

    O OCR é um fallback para PDFs escaneados; PDFs textuais continuam usando
    pdfplumber por ser mais rápido e preservar melhor a estrutura.
    """
    partes: list[str] = []
    pdf = pdfium.PdfDocument(str(caminho))
    try:
        for page in pdf:
            bitmap = page.render(scale=2.5)
            image = bitmap.to_pil()
            texto = pytesseract.image_to_string(image, lang="por+eng", config="--psm 6")
            if texto.strip():
                partes.append(texto)
    finally:
        pdf.close()
    return "\n".join(partes)


def _ler_texto(caminho: Path) -> tuple[str, bool]:
    texto = _ler_texto_nativo(caminho)
    if texto.strip():
        return texto, False

    try:
        texto_ocr = _ler_texto_ocr(caminho)
    except Exception:
        return "", False

    return texto_ocr, bool(texto_ocr.strip())


def extrair_documento(caminho: Path, nome_original: str) -> dict:
    texto, usou_ocr = _ler_texto(caminho)
    if not texto.strip():
        return _ficha_erro(nome_original, "PDF sem texto extraível (escaneado?)")

    tipo_doc = detectar_tipo(texto)
    parsers = PARSERS_POR_TIPO.get(tipo_doc, [generic.parse])

    resultado = None
    for parser in parsers:
        try:
            r = parser(texto, caminho)
            if r and r.confianca >= 0.5:
                resultado = r
                break
        except Exception:
            continue

    if not resultado:
        return _ficha_erro(nome_original, f"Nenhum parser conseguiu extrair (tipo detectado: {tipo_doc})")

    filial_codigo = None
    if resultado.cnpj_tomador:
        filial_codigo = filial_por_cnpj(resultado.cnpj_tomador)

    fornecedor_codigo = None
    fornecedor_nome_cadastro = None
    if resultado.cnpj_emissor:
        f = fornecedor_por_cnpj(resultado.cnpj_emissor)
        if f:
            fornecedor_codigo = f["codigo"]
            fornecedor_nome_cadastro = f["nome"]

    nome_fornecedor_final = fornecedor_nome_cadastro or resultado.nome_emissor or "DESCONHECIDO"

    obs = list(resultado.observacoes)
    if usou_ocr:
        obs.append("Texto extraído por OCR — conferir campos na revisão.")
    if resultado.cnpj_emissor and not fornecedor_codigo:
        obs.append("Fornecedor não cadastrado no Protheus — verificar inclusão.")
    if resultado.cnpj_tomador and not filial_codigo:
        obs.append("CNPJ do tomador não encontrado na tabela de Filiais.")

    itens_dict = []
    for item in resultado.itens:
        if is_dataclass(item):
            itens_dict.append(asdict(item))
        elif hasattr(item, "model_dump"):
            itens_dict.append(item.model_dump())
        else:
            itens_dict.append(item)

    return {
        "arquivos_origem": [nome_original],
        "nomes_arquivos_padrao": [normalizar_nome_arquivo(nome_fornecedor_final, resultado.numero_documento or "")],
        "filial_codigo": filial_codigo,
        "filial_cnpj": resultado.cnpj_tomador,
        "fornecedor_codigo": fornecedor_codigo,
        "fornecedor_nome": nome_fornecedor_final,
        "fornecedor_cnpj": resultado.cnpj_emissor,
        "tipo_pedido": detectar_tipo_pedido(tipo_doc, texto),
        "documentos_tipo": resultado.tipo_documento_legivel,
        "numeros_documentos": [resultado.numero_documento] if resultado.numero_documento else [],
        "itens": itens_dict,
        "status_extracao": "ok" if resultado.confianca >= 0.8 else "parcial",
        "template_usado": resultado.template_usado,
        "observacoes": obs,
    }


def _ficha_erro(nome_original: str, msg: str) -> dict:
    return {
        "arquivos_origem": [nome_original],
        "nomes_arquivos_padrao": [],
        "filial_codigo": None,
        "filial_cnpj": None,
        "fornecedor_codigo": None,
        "fornecedor_nome": None,
        "fornecedor_cnpj": None,
        "tipo_pedido": None,
        "documentos_tipo": None,
        "numeros_documentos": [],
        "itens": [],
        "status_extracao": "manual",
        "template_usado": None,
        "observacoes": [msg, "Preencher manualmente na tela de revisão."],
    }
