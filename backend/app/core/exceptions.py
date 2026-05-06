"""Exceções customizadas do domínio."""


class AppError(Exception):
    """Erro genérico da aplicação."""


class ReferenciaNaoEncontrada(AppError):
    """Planilha de referência ainda não foi importada."""


class PdfExtractionError(AppError):
    """Erro ao extrair conteúdo de um PDF."""


class TemplateNaoReconhecido(AppError):
    """Não foi possível identificar o tipo do documento."""
