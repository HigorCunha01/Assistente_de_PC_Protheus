"""Configurações do backend lidas de variáveis de ambiente."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # CORS
    backend_cors_origins: str = "http://localhost:3000"

    # Paths
    referencias_dir: Path = Path("/app/data/referencias")
    tmp_dir: Path = Path("/app/data/tmp")

    # Nomes esperados das planilhas de referência
    arquivo_filiais: str = "Filiais.xlsx"
    arquivo_fornecedores: str = "Fornecedores.xlsx"
    arquivo_pedidos_compra: str = "Pedidos_de_Compra.xlsx"

    # Limites
    max_upload_mb: int = 20
    max_files_por_processamento: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
