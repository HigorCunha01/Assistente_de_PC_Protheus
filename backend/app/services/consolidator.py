"""Consolida fichas (1 PDF cada) em pedidos únicos quando compatíveis.

Regra: mesmo fornecedor + mesma filial + mesmo tipo (Produto OU Servico).
Documentos com tipos diferentes geram fichas separadas.
"""
from app.schemas.ficha import FichaPedido, ItemFicha


def _chave(ficha: FichaPedido) -> tuple:
    return (
        ficha.fornecedor_codigo or ficha.fornecedor_cnpj or ficha.fornecedor_nome or "?",
        ficha.filial_codigo or ficha.filial_cnpj or "?",
        ficha.tipo_pedido or "?",
    )


def consolidar_fichas(fichas: list[FichaPedido]) -> list[FichaPedido]:
    """Recebe N fichas e retorna lista consolidada."""
    grupos: dict[tuple, list[FichaPedido]] = {}
    for f in fichas:
        # Fichas em status manual ou erro NÃO são consolidadas — usuário precisa revisar
        if f.status_extracao in ("manual", "erro"):
            grupos[(f.arquivos_origem[0] if f.arquivos_origem else id(f),)] = [f]
            continue
        # Faturas de comunicação/telecom costumam representar contas, links ou
        # contratos diferentes mesmo quando fornecedor e filial são iguais.
        # Mantê-las separadas evita sugerir um PC errado após somar documentos.
        if f.documentos_tipo == "NF Comunicação":
            grupos[(f.arquivos_origem[0] if f.arquivos_origem else id(f),)] = [f]
            continue
        grupos.setdefault(_chave(f), []).append(f)

    consolidadas: list[FichaPedido] = []
    for chave, lista in grupos.items():
        if len(lista) == 1:
            consolidadas.append(lista[0])
            continue
        consolidadas.append(_unir_fichas(lista))
    return consolidadas


def _unir_fichas(fichas: list[FichaPedido]) -> FichaPedido:
    """Une múltiplas fichas compatíveis numa só, somando itens e listando documentos."""
    base = fichas[0].model_copy(deep=True)
    arquivos: list[str] = list(base.arquivos_origem)
    nomes_padrao: list[str] = list(base.nomes_arquivos_padrao)
    numeros: list[str] = list(base.numeros_documentos)
    itens: list[ItemFicha] = list(base.itens)
    obs: list[str] = list(base.observacoes)

    for f in fichas[1:]:
        for a in f.arquivos_origem:
            if a not in arquivos:
                arquivos.append(a)
        for n in f.nomes_arquivos_padrao:
            if n not in nomes_padrao:
                nomes_padrao.append(n)
        for d in f.numeros_documentos:
            if d not in numeros:
                numeros.append(d)
        itens.extend(f.itens)
        for o in f.observacoes:
            if o not in obs:
                obs.append(o)

    obs.append(f"Pedido consolidado de {len(fichas)} documentos.")

    base.arquivos_origem = arquivos
    base.nomes_arquivos_padrao = nomes_padrao
    base.numeros_documentos = numeros
    base.itens = itens
    base.observacoes = obs
    return base
