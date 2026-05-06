"""Endpoints de processamento de PDFs e geração de Excel."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import uuid

from app.config import settings
from app.services.pdf.extractor import extrair_documento
from app.services.consolidator import consolidar_fichas
from app.services.pc_matcher import sugerir_pedido_compra
from app.services.excel_generator import gerar_excel
from app.schemas.ficha import FichaPedido, RevisaoRequest

router = APIRouter()


@router.post("/extrair")
async def extrair_pdfs(arquivos: list[UploadFile] = File(...)):
    """
    Recebe N PDFs, extrai dados de cada um, retorna lista de fichas pra revisão.
    Não consolida ainda — isso acontece após a revisão.
    """
    if len(arquivos) > settings.max_files_por_processamento:
        raise HTTPException(400, f"Máximo de {settings.max_files_por_processamento} arquivos por vez")

    fichas: list[dict] = []
    for arq in arquivos:
        if not arq.filename or not arq.filename.lower().endswith(".pdf"):
            continue
        # Salva temporariamente
        tmp_path = settings.tmp_dir / f"{uuid.uuid4()}_{arq.filename}"
        with tmp_path.open("wb") as f:
            shutil.copyfileobj(arq.file, f)
        try:
            ficha = extrair_documento(tmp_path, nome_original=arq.filename)
            fichas.append(ficha)
        except Exception as e:
            fichas.append({
                "arquivo": arq.filename,
                "erro": str(e),
                "status_extracao": "erro",
            })
        finally:
            tmp_path.unlink(missing_ok=True)

    return {"fichas": fichas}


@router.post("/gerar-excel")
def gerar_excel_endpoint(req: RevisaoRequest):
    """
    Recebe as fichas (já revisadas pelo usuário), aplica consolidação,
    cruza com pedidos antigos pra sugerir PC, e gera o Excel.
    """
    fichas_revisadas = req.fichas
    if not fichas_revisadas:
        raise HTTPException(400, "Nenhuma ficha enviada")

    # Consolida documentos compatíveis
    fichas_consolidadas = consolidar_fichas(fichas_revisadas)

    # Sugere PC pra cada ficha consolidada
    for ficha in fichas_consolidadas:
        sugerir_pedido_compra(ficha)

    # Gera Excel
    nome_arquivo = f"pedidos_compra_{uuid.uuid4().hex[:8]}.xlsx"
    caminho = settings.tmp_dir / nome_arquivo
    gerar_excel(fichas_consolidadas, caminho)

    return FileResponse(
        path=str(caminho),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="pedidos_compra.xlsx",
    )
