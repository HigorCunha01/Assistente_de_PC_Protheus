"""Entrypoint da API FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import health, referencias, processamentos

app = FastAPI(
    title="Protheus PC API",
    version="0.1.0",
    description="API para extração de dados de NF/NFS-e/fatura e geração de Excel para criação de pedidos de compra no Protheus.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Garante que diretórios de dados existem
settings.referencias_dir.mkdir(parents=True, exist_ok=True)
settings.tmp_dir.mkdir(parents=True, exist_ok=True)

# Routers
app.include_router(health.router, tags=["health"])
app.include_router(referencias.router, prefix="/referencias", tags=["referencias"])
app.include_router(processamentos.router, prefix="/processamentos", tags=["processamentos"])


@app.get("/", include_in_schema=False)
def root():
    return {"app": "protheus-pc", "version": "0.1.0", "docs": "/docs"}
