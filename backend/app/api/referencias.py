"""Endpoints para upload/leitura das planilhas de referência."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pathlib import Path
import shutil

from app.config import settings
from app.services.referencias import (
    listar_filiais, listar_fornecedores, listar_pedidos_compra, validar_planilha
)

router = APIRouter()

ARQUIVOS_VALIDOS = {
    "filiais": settings.arquivo_filiais,
    "fornecedores": settings.arquivo_fornecedores,
    "pedidos_compra": settings.arquivo_pedidos_compra,
}


@router.post("/upload/{tipo}")
async def upload_planilha(tipo: str, arquivo: UploadFile = File(...)):
    """Faz upload de uma das 3 planilhas de referência (filiais | fornecedores | pedidos_compra)."""
    if tipo not in ARQUIVOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo inválido. Use: {list(ARQUIVOS_VALIDOS.keys())}",
        )

    if not arquivo.filename or not arquivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .xlsx são aceitos.",
        )

    nome_destino = ARQUIVOS_VALIDOS[tipo]
    destino: Path = settings.referencias_dir / nome_destino

    # Salva temporariamente, valida, e só então move pro destino
    tmp = settings.tmp_dir / f"_upload_{nome_destino}"
    with tmp.open("wb") as f:
        shutil.copyfileobj(arquivo.file, f)

    try:
        info = validar_planilha(tmp, tipo)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Planilha inválida: {e}")

    shutil.move(str(tmp), str(destino))
    return {"status": "ok", "tipo": tipo, "arquivo": nome_destino, **info}


@router.get("/status")
def status_referencias():
    """Indica quais planilhas estão disponíveis no momento."""
    refs = settings.referencias_dir
    return {
        tipo: {
            "presente": (refs / nome).exists(),
            "tamanho_bytes": (refs / nome).stat().st_size if (refs / nome).exists() else 0,
        }
        for tipo, nome in ARQUIVOS_VALIDOS.items()
    }


@router.get("/filiais")
def get_filiais():
    return listar_filiais()


@router.get("/fornecedores")
def get_fornecedores(busca: str | None = None, limite: int = 50):
    return listar_fornecedores(busca=busca, limite=limite)


@router.get("/pedidos-compra")
def get_pedidos_compra(limite: int = 50):
    return listar_pedidos_compra(limite=limite)
