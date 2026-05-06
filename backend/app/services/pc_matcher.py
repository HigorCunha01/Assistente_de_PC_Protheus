"""Sugere PC antigo pra cópia, baseado em filial+fornecedor e proximidade de preço.

Regra:
1. Filtra PCs que têm o mesmo fornecedor + mesma filial (obrigatório).
2. Para cada item da ficha, calcula a "distância" de preço pro item mais próximo
   em cada PC candidato.
3. Escolhe o PC com menor distância total. Empate é desempatado pela data mais
   recente (DT EMISSAO PC).
4. Se não houver PC do mesmo fornecedor+filial, não sugere nada.
"""
from app.schemas.ficha import FichaPedido
from app.services.referencias import pedidos_compra_por_fornecedor_filial
from app.services.obs_mes_transformer import transformar_obs


# Tolerância de preço pra reportar como "match com variação"
TOLERANCIA_EXATA = 0.01


def sugerir_pedido_compra(ficha: FichaPedido) -> None:
    """Anota a ficha (in place) com sugestao_pc_num + obs sugerida."""
    if not ficha.fornecedor_cnpj or not ficha.filial_codigo or not ficha.itens:
        return

    candidatos = pedidos_compra_por_fornecedor_filial(ficha.fornecedor_cnpj, ficha.filial_codigo)
    if not candidatos:
        return

    # Agrupa linhas por PC NUM
    pcs: dict[str, list[dict]] = {}
    for linha in candidatos:
        if not linha["pc_num"]:
            continue
        pcs.setdefault(linha["pc_num"], []).append(linha)

    if not pcs:
        return

    # Pra cada PC, calcula distância total e flag de match exato
    melhor_pc = None
    melhor_distancia = float("inf")
    melhor_data = ""
    melhor_exato = False

    for pc_num, linhas_pc in pcs.items():
        distancia, exato = _calcular_distancia(ficha.itens, linhas_pc)
        # data mais recente entre as linhas do PC
        data_pc = max((l["dt_emissao"] for l in linhas_pc), default="")

        # Critério: menor distância. Em empate de distância, exato vence; depois data mais recente.
        melhor = False
        if distancia < melhor_distancia:
            melhor = True
        elif distancia == melhor_distancia:
            if exato and not melhor_exato:
                melhor = True
            elif exato == melhor_exato and data_pc > melhor_data:
                melhor = True

        if melhor:
            melhor_pc = (pc_num, linhas_pc)
            melhor_distancia = distancia
            melhor_data = data_pc
            melhor_exato = exato

    if not melhor_pc:
        return

    pc_num, linhas = melhor_pc
    obs_original = next((l["obs_pedido"] for l in linhas if l["obs_pedido"]), None)
    obs_modificada = transformar_obs(obs_original) if obs_original else None

    ficha.sugestao_pc_num = pc_num
    ficha.sugestao_pc_obs_original = obs_original
    ficha.sugestao_pc_obs_modificada = obs_modificada

    # Anota observação se foi match com variação de preço
    if not melhor_exato:
        ficha.observacoes.append(
            f"PC sugerido por proximidade — preços do PC antigo diferem do documento. Conferir antes de copiar."
        )


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
