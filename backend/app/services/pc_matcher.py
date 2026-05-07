"""Sugere PC antigo pra cópia, baseado em filial+fornecedor e data de emissão.

Regra:
1. Filtra PCs que têm o mesmo fornecedor + mesma filial (obrigatório).
2. Escolhe o PC com DT EMISSAO PC mais recente.
3. Se não houver PC do mesmo fornecedor+filial, tenta validar o PC informado no
   nome do arquivo.
"""
from datetime import date, datetime
import re

from app.schemas.ficha import FichaPedido
from app.services.referencias import pedidos_compra_por_fornecedor_filial, pedidos_compra_por_numero
from app.services.obs_mes_transformer import transformar_obs


# Tolerância de preço pra reportar como "match com variação"
TOLERANCIA_EXATA = 0.01


def sugerir_pedido_compra(ficha: FichaPedido) -> None:
    """Anota a ficha (in place) com sugestao_pc_num + obs sugerida."""
    if not ficha.fornecedor_cnpj or not ficha.filial_codigo:
        return

    candidatos = pedidos_compra_por_fornecedor_filial(ficha.fornecedor_cnpj, ficha.filial_codigo)
    pc_nome_arquivo = _pc_informado_no_nome(ficha)
    if not candidatos:
        if pc_nome_arquivo:
            linhas_pc_nome = pedidos_compra_por_numero(pc_nome_arquivo)
            if _pc_do_nome_compativel(ficha, linhas_pc_nome):
                _aplicar_pc_sugerido(ficha, pc_nome_arquivo, linhas_pc_nome, match_exato=True)
        return

    # Agrupa linhas por PC NUM
    pcs: dict[str, list[dict]] = {}
    for linha in candidatos:
        if not linha["pc_num"]:
            continue
        pcs.setdefault(linha["pc_num"], []).append(linha)

    if not pcs:
        return

    melhor_pc = _pc_mais_recente(pcs)

    if not melhor_pc:
        return

    pc_num, linhas = melhor_pc
    _aplicar_pc_sugerido(ficha, pc_num, linhas, match_exato=True)


def _aplicar_pc_sugerido(ficha: FichaPedido, pc_num: str, linhas: list[dict], match_exato: bool) -> None:
    obs_original = next((l["obs_pedido"] for l in linhas if l["obs_pedido"]), None)
    obs_modificada = transformar_obs(obs_original) if obs_original else None

    ficha.sugestao_pc_num = pc_num
    ficha.sugestao_pc_obs_original = obs_original
    ficha.sugestao_pc_obs_modificada = obs_modificada

    # Anota observação se foi match com variação de preço
    if not match_exato:
        ficha.observacoes.append(
            f"PC sugerido por proximidade — preços do PC antigo diferem do documento. Conferir antes de copiar."
        )


def _pc_mais_recente(pcs: dict[str, list[dict]]) -> tuple[str, list[dict]] | None:
    melhor: tuple[str, list[dict]] | None = None
    melhor_data = datetime.min

    for pc_num, linhas_pc in pcs.items():
        data_pc = max((_parse_dt_emissao(l["dt_emissao"]) for l in linhas_pc), default=datetime.min)
        if melhor is None or data_pc > melhor_data:
            melhor = (pc_num, linhas_pc)
            melhor_data = data_pc

    return melhor


def _parse_dt_emissao(valor) -> datetime:
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())

    texto = str(valor or "").strip()
    if not texto:
        return datetime.min

    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    return datetime.min


def _pc_informado_no_nome(ficha: FichaPedido) -> str | None:
    for nome in ficha.arquivos_origem:
        m = re.search(r"_pc_?\s*(\d{5,6})", nome, re.IGNORECASE)
        if not m:
            m = re.search(r"pc_?(\d{5,6})", nome, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _pc_do_nome_compativel(ficha: FichaPedido, linhas: list[dict]) -> bool:
    if not linhas or not ficha.filial_codigo or not ficha.itens:
        return False
    if not any(l["filial"] == ficha.filial_codigo for l in linhas):
        return False
    distancia, _ = _calcular_distancia(ficha.itens, linhas)
    total_doc = sum(float(i.quantidade) * float(i.valor_unitario) for i in ficha.itens)
    limite = max(1.0, total_doc * 0.05)
    return distancia <= limite


def _calcular_distancia(itens_ficha, linhas_pc):
    """Retorna (soma_distancias, todos_exatos).

    Pra cada item da ficha, encontra o item de PC mais próximo em preço e soma
    a distância. Se nenhum item da ficha encontrar nada com distância < infinito,
    retorna infinito (PC não compatível).
    """
    soma = 0.0
    todos_exatos = True
    encontrou_algum = False
    for item in itens_ficha:
        melhor_dist = float("inf")
        for linha in linhas_pc:
            preco_pc = linha["item_prc_unt"]
            if preco_pc <= 0:
                continue
            d = abs(item.valor_unitario - preco_pc)
            if d < melhor_dist:
                melhor_dist = d
        if melhor_dist == float("inf"):
            # Item não encontrou par — penaliza com o próprio valor (distância máxima razoável)
            melhor_dist = item.valor_unitario
        soma += melhor_dist
        if melhor_dist > TOLERANCIA_EXATA:
            todos_exatos = False
        encontrou_algum = True

    if not encontrou_algum:
        return float("inf"), False
    return soma, todos_exatos
