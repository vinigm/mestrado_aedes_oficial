"""Reimplementacao INDEPENDENTE (do zero) da estatistica da E3 e das familias F1-F4.

Nao importa nada de aedes/*. Usa so numpy, pandas, scipy. Fonte da especificacao:
METODO_ESTATISTICO.md + PRE_DECLARACAO.md (emendas 1-3).
"""
from __future__ import annotations

import glob
import math
import os

import numpy as np
import pandas as pd
from scipy import stats

RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final"
PARCIAIS = RAIZ + "/resultados/ciencia/E2_ablacao/parciais/"
PISO = RAIZ + "/resultados/ciencia/piso_de_ruido/piso.csv"
TABELA = RAIZ + "/dados/tabela_final.csv"

JANELA_INI = pd.Timestamp("2024-01-07")
JANELA_FIM = pd.Timestamp("2026-02-01")
HS_TESTE = [1, 4, 8, 12]


def carregar_parciais() -> pd.DataFrame:
    arquivos = sorted(glob.glob(PARCIAIS + "*.csv"))
    assert len(arquivos) == 192, len(arquivos)
    tabelas = [
        pd.read_csv(a, float_precision="round_trip", parse_dates=["data_origem", "data_alvo"])
        for a in arquivos
    ]
    return pd.concat(tabelas, ignore_index=True)


def serie(prev: pd.DataFrame, braco: str, folha: int, h: int) -> pd.DataFrame:
    """Previsoes de um braco/folha/h indexadas por data_alvo, ordenadas."""
    m = (prev["braco"] == braco) & (prev["folha"] == folha) & (prev["h"] == h)
    s = prev.loc[m].set_index("data_alvo").sort_index()
    assert s.index.is_unique
    return s[["data_origem", "real", "previsto"]]


# ----------------------------------------------------------------------- regua
def regua_sazonal() -> pd.Series:
    """Casos por data da tabela CORTADA (maturidade 12 semanas)."""
    t = pd.read_csv(TABELA, parse_dates=["data_inicio_semana_epidemi"])
    casos = t.set_index("data_inicio_semana_epidemi")["casos_confirmados"].astype(float)
    ultima = casos.dropna().index.max()
    limite = ultima - pd.Timedelta(weeks=12)
    casos = casos.copy()
    casos[casos.index > limite] = np.nan
    return casos


# ------------------------------------------------------------------------- E3
def composto(prev: pd.DataFrame, N: int, h: int, janela_de_pares_futura: int = 0) -> pd.DataFrame:
    """Composto N, horizonte h. Devolve linhas (data_alvo) com previsao.

    janela_de_pares_futura > 0 e APENAS para o teste de mutacao (vaza futuro): aceita pares com
    data_alvo <= t + k semanas.
    """
    s5 = serie(prev, "completo", 5, h)
    s20 = serie(prev, "completo", 20, h)
    comuns = s5.index.intersection(s20.index).sort_values()
    e5 = (s5.loc[comuns, "real"] - s5.loc[comuns, "previsto"]).abs().to_numpy()
    e20 = (s20.loc[comuns, "real"] - s20.loc[comuns, "previsto"]).abs().to_numpy()
    datas = comuns.to_numpy()
    linhas = []
    for da in s5.index:  # semanas-alvo em que o folha 5 tem previsao
        if da not in s20.index:
            continue
        t = da - pd.Timedelta(weeks=h)
        corte = t + pd.Timedelta(weeks=janela_de_pares_futura)
        # pares com data_alvo' <= t, do mais antigo ao mais recente
        ate = np.searchsorted(datas, np.datetime64(corte), side="right")
        if ate < N:
            continue
        ult5 = e5[ate - N : ate]
        ult20 = e20[ate - N : ate]
        mae5 = ult5.mean()
        mae20 = ult20.mean()
        usa20 = mae20 < mae5  # empate -> folha 5
        s = s20 if usa20 else s5
        linhas.append(
            dict(
                N=N,
                h=h,
                data_origem=t,
                data_alvo=da,
                real=s.loc[da, "real"],
                previsto=s.loc[da, "previsto"],
                folha_escolhida=20 if usa20 else 5,
                max_data_alvo_usada=pd.Timestamp(datas[ate - 1]),
            )
        )
    return pd.DataFrame(linhas)


# ------------------------------------------------------------------ estatistica
def dm_hln(d: np.ndarray, h: int) -> dict:
    n = len(d)
    dbar = d.mean()
    dc = d - dbar

    def gam(k):
        return float((dc[k:] * dc[: n - k]).sum() / n)

    V = (gam(0) + 2 * sum(gam(k) for k in range(1, h))) / n
    fallback = False
    if V <= 0:
        V = (gam(0) + 2 * sum((1 - k / h) * gam(k) for k in range(1, h))) / n
        fallback = True
    if V <= 0:
        return dict(dm=np.nan, dm_hln=np.nan, p=1.0, fallback=True)
    dm = dbar / math.sqrt(V)
    fator = math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    d_h = dm * fator
    p = 2 * stats.t.sf(abs(d_h), n - 1)
    return dict(dm=dm, dm_hln=d_h, p=float(p), fallback=fallback)


def bootstrap_ic(eA: np.ndarray, eB: np.ndarray, seed=42, B=2000, bloco=8, variante="matriz"):
    n = len(eA)
    nb = -(-n // bloco)
    rng = np.random.default_rng(seed)
    if variante == "matriz":
        ini = rng.integers(0, n - bloco + 1, size=(B, nb))
    elif variante == "por_rep":
        ini = np.stack([rng.integers(0, n - bloco + 1, size=nb) for _ in range(B)])
    elif variante == "por_bloco_escalar":
        ini = np.array([[rng.integers(0, n - bloco + 1) for _ in range(nb)] for _ in range(B)])
    else:
        raise ValueError(variante)
    off = np.arange(bloco)
    ganhos = np.empty(B)
    aA = np.abs(eA)
    aB = np.abs(eB)
    for b in range(B):
        idx = (ini[b][:, None] + off[None, :]).ravel()[:n]
        ma = aA[idx].mean()
        mb = aB[idx].mean()
        ganhos[b] = (mb - ma) / mb * 100
    return float(np.percentile(ganhos, 2.5)), float(np.percentile(ganhos, 97.5))


def holm(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    ordem = np.argsort(p, kind="stable")
    aj = np.empty(m)
    corrente = 0.0
    for rank, i in enumerate(ordem):
        v = min(1.0, (m - rank) * p[i])
        corrente = max(corrente, v)
        aj[i] = corrente
    return aj


def comparar(sA: pd.DataFrame, sB: pd.DataFrame, h: int, seed=42, variante="matriz") -> dict:
    comuns = sA.index.intersection(sB.index).sort_values()
    eA = (sA.loc[comuns, "real"] - sA.loc[comuns, "previsto"]).to_numpy()
    eB = (sB.loc[comuns, "real"] - sB.loc[comuns, "previsto"]).to_numpy()
    n = len(comuns)
    maeA = np.abs(eA).mean()
    maeB = np.abs(eB).mean()
    delta = maeB - maeA
    ganho = delta / maeB * 100
    d = np.abs(eB) - np.abs(eA)
    r = dm_hln(d, h)
    lo, hi = bootstrap_ic(eA, eB, seed=seed, variante=variante)
    return dict(
        n=n, mae_A=maeA, mae_B=maeB, delta=delta, ganho_pct=ganho, ic_inf=lo, ic_sup=hi,
        dm_hln=r["dm_hln"], p_bruto=r["p"], variancia_fallback=r["fallback"],
    )


def veredito(p_holm: float, delta: float, limiar: float) -> str:
    if p_holm < 0.05 and abs(delta) > limiar:
        return "A melhor" if delta > 0 else "A pior"
    return "sem evidencia"


def janela(s: pd.DataFrame) -> pd.DataFrame:
    return s[(s.index >= JANELA_INI) & (s.index <= JANELA_FIM)]


def definir_familias():
    """Lista (familia, h, A, B) onde A/B sao (braco, folha) ou 'composto'/'regua'."""
    fam = []
    for X in ["casos", "clima", "vetor"]:
        for h in HS_TESTE:
            fam.append(("F1", h, ("completo", 5), (f"sem_{X}", 5)))
    for X in ["casos", "clima", "vetor"]:
        for h in HS_TESTE:
            fam.append(("F2", h, (f"so_{X}", 5), ("so_calendario", 5)))
    for X in ["casos", "clima", "vetor"]:
        for h in HS_TESTE:
            fam.append(("F3", h, ("completo", 20), (f"sem_{X}", 20)))
    for h in HS_TESTE:
        fam.append(("F4", h, ("completo", 5), "regua"))
    for h in HS_TESTE:
        fam.append(("F4", h, ("completo", 20), "regua"))
    for h in HS_TESTE:
        fam.append(("F4", h, "composto", "regua"))
    for h in HS_TESTE:
        fam.append(("F4", h, "composto", ("completo", 5)))
    return fam
