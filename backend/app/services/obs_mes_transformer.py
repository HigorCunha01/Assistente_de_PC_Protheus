"""Transforma a OBS_PEDIDO sugerindo o próximo mês quando aplicável."""
import re
from typing import Optional


MESES_PT = {
    "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4,
    "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9,
    "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12,
}
MESES_PT_INV = {v: k for k, v in MESES_PT.items() if k != "MARCO"}

MESES_ABREV = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
}
MESES_ABREV_INV = {v: k for k, v in MESES_ABREV.items()}


def proximo_mes(numero: int) -> int:
    return 1 if numero == 12 else numero + 1


def _ajustar_caso(novo: str, antigo: str) -> str:
    if antigo.isupper():
        return novo.upper()
    if antigo.islower():
        return novo.lower()
    if antigo[0].isupper():
        return novo.title()
    return novo


def transformar_obs(obs):
    if not obs or not obs.strip():
        return obs

    novo = obs

    pattern_ext = re.compile(
        r"\b(" + "|".join(MESES_PT.keys()) + r")\b(\s*(?:/|de\s+))?(\d{2,4})?",
        re.IGNORECASE,
    )

    def _sub_ext(m):
        antigo_mes = m.group(1)
        sep = m.group(2)
        ano_str = m.group(3)
        n = MESES_PT[antigo_mes.upper()]
        nm = MESES_PT_INV[proximo_mes(n)]
        nm = _ajustar_caso(nm, antigo_mes)
        if sep and ano_str:
            ano_int = int(ano_str)
            if n == 12:
                if len(ano_str) == 2:
                    ano_int = (ano_int + 1) % 100
                    return f"{nm}{sep}{ano_int:02d}"
                return f"{nm}{sep}{ano_int + 1}"
            return f"{nm}{sep}{ano_str}"
        return nm

    novo = pattern_ext.sub(_sub_ext, novo)

    pattern_abr = re.compile(
        r"\b(" + "|".join(MESES_ABREV.keys()) + r")(\s*[/\-]\s*(\d{2,4}))?\b",
        re.IGNORECASE,
    )

    def _sub_abr(m):
        antigo_mes = m.group(1)
        n = MESES_ABREV[antigo_mes.upper()]
        nm = _ajustar_caso(MESES_ABREV_INV[proximo_mes(n)], antigo_mes)
        if m.group(2):
            ano_str = m.group(3)
            ano_int = int(ano_str)
            if n == 12:
                if len(ano_str) == 2:
                    ano_int = (ano_int + 1) % 100
                    return f"{nm}/{ano_int:02d}"
                return f"{nm}/{ano_int + 1}"
            return f"{nm}{m.group(2)}"
        return nm

    novo = pattern_abr.sub(_sub_abr, novo)

    pattern_num = re.compile(r"\b(0[1-9]|1[0-2])\s*/\s*(\d{2,4})\b")

    def _sub_num(m):
        mes = int(m.group(1))
        ano_str = m.group(2)
        ano_int = int(ano_str)
        nm = proximo_mes(mes)
        if mes == 12:
            if len(ano_str) == 2:
                ano_int = (ano_int + 1) % 100
                return f"{nm:02d}/{ano_int:02d}"
            return f"{nm:02d}/{ano_int + 1}"
        if len(ano_str) == 2:
            return f"{nm:02d}/{ano_str}"
        return f"{nm:02d}/{ano_int}"

    novo = pattern_num.sub(_sub_num, novo)
    return novo
