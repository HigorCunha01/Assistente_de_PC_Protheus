"""Endpoint de health check."""
from fastapi import APIRouter
from pathlib import Path
from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    """Retorna status do serviço e disponibilidade das planilhas de referência."""
    refs_dir: Path = settings.referencias_dir
    return {
        "status": "ok",
        "version": "0.1.0",
        "referencias": {
            "filiais": (refs_dir / settings.arquivo_filiais).exists(),
            "fornecedores": (refs_dir / settings.arquivo_fornecedores).exists(),
            "pedidos_compra": (refs_dir / settings.arquivo_pedidos_compra).exists(),
        },
    }
