"""Receita INDEPENDENTE do certificador da E2 (nao importa nada de aedes/ nem de experimentos/).

Monta a matriz de cada braco do zero a partir de dados/tabela_final.csv, aplica o corte de
maturidade (12 semanas contadas da ultima semana com caso) e roda o walk-forward com o corte
pela data da RESPOSTA. Escrita pelo certificador a partir da DESCRICAO da tarefa e da
pre-declaracao; so as operacoes numericas de pandas/numpy (shift, rolling(4).mean, sin, cos)
sao as mesmas, porque o modelo e sensivel ao ultimo bit.
"""
import hashlib
import pathlib

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

RAIZ = pathlib.Path(__file__).resolve().parents[4]  # .../projeto_final
CAMINHO_TABELA = RAIZ / "dados" / "tabela_final.csv"
SHA256_ESPERADO = "6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f"

COL_DATA = "data_inicio_semana_epidemi"
COL_CASOS = "casos_confirmados"

BLOCO_C = ["casos", "casos_lag1", "casos_lag2", "casos_lag3", "casos_lag4", "casos_mm4"]
BLOCO_M = ["temp_media_lag4", "umid_media", "temp_media_lag3", "temp_max",
           "pressao_media_lag3", "pressao_media_lag4"]
BLOCO_V = ["aedes_aegypti_por_armadilha", "aedes_aegypti_por_armadilha_lag1",
           "aedes_aegypti_por_armadilha_lag2", "aedes_aegypti_por_armadilha_lag3",
           "aedes_aegypti_por_armadilha_lag4", "vetor_mm4"]
BLOCO_K = ["sem_sin", "sem_cos", "alvo_sin", "alvo_cos"]

# Ordem fixa do modelo (22 variaveis), dada na descricao da tarefa.
ORDEM = ["casos", "casos_lag1", "casos_lag2", "casos_lag3", "casos_lag4", "casos_mm4",
         "sem_sin", "sem_cos",
         "temp_media_lag4", "umid_media", "temp_media_lag3", "temp_max",
         "pressao_media_lag3", "pressao_media_lag4",
         "aedes_aegypti_por_armadilha", "aedes_aegypti_por_armadilha_lag1",
         "aedes_aegypti_por_armadilha_lag2", "aedes_aegypti_por_armadilha_lag3",
         "aedes_aegypti_por_armadilha_lag4", "vetor_mm4",
         "alvo_sin", "alvo_cos"]
assert sorted(ORDEM) == sorted(BLOCO_C + BLOCO_M + BLOCO_V + BLOCO_K)

BLOCOS_DOS_BRACOS = {
    "completo": BLOCO_C + BLOCO_M + BLOCO_V + BLOCO_K,
    "sem_casos": BLOCO_M + BLOCO_V + BLOCO_K,
    "sem_clima": BLOCO_C + BLOCO_V + BLOCO_K,
    "sem_vetor": BLOCO_C + BLOCO_M + BLOCO_K,
    "so_casos": BLOCO_C + BLOCO_K,
    "so_clima": BLOCO_M + BLOCO_K,
    "so_vetor": BLOCO_V + BLOCO_K,
    "so_calendario": list(BLOCO_K),
}


def colunas_do_braco(braco):
    conjunto = set(BLOCOS_DOS_BRACOS[braco])
    return [c for c in ORDEM if c in conjunto]


def carregar_tabela_cortada():
    bruto = CAMINHO_TABELA.read_bytes()
    assert hashlib.sha256(bruto).hexdigest() == SHA256_ESPERADO, "hash da tabela diverge"
    t = pd.read_csv(CAMINHO_TABELA, parse_dates=[COL_DATA])
    t[COL_CASOS] = t[COL_CASOS].astype("float64")
    ultima = t.loc[t[COL_CASOS].notna(), COL_DATA].max()
    limite = ultima - pd.Timedelta(weeks=12)
    t.loc[t[COL_DATA] > limite, COL_CASOS] = np.nan
    return t


def todas_as_variaveis(t, h):
    """Todas as 22 + y_h, SEM dropna, indexadas como a tabela."""
    c = t[COL_CASOS]
    v = t["aedes_aegypti_por_armadilha"]
    sem = t["semana"]
    d = {}
    d["casos"] = c
    for k in (1, 2, 3, 4):
        d[f"casos_lag{k}"] = c.shift(k)
    d["casos_mm4"] = c.rolling(4).mean()
    d["sem_sin"] = np.sin(2 * np.pi * sem / 52)
    d["sem_cos"] = np.cos(2 * np.pi * sem / 52)
    d["temp_media_lag4"] = t["temp_media"].shift(4)
    d["umid_media"] = t["umid_media"]
    d["temp_media_lag3"] = t["temp_media"].shift(3)
    d["temp_max"] = t["temp_max"]
    d["pressao_media_lag3"] = t["pressao_media"].shift(3)
    d["pressao_media_lag4"] = t["pressao_media"].shift(4)
    d["aedes_aegypti_por_armadilha"] = v
    for k in (1, 2, 3, 4):
        d[f"aedes_aegypti_por_armadilha_lag{k}"] = v.shift(k)
    d["vetor_mm4"] = v.rolling(4).mean()
    sem_alvo = sem.shift(-h)
    d["alvo_sin"] = np.sin(2 * np.pi * sem_alvo / 52)
    d["alvo_cos"] = np.cos(2 * np.pi * sem_alvo / 52)
    d["y_h"] = c.shift(-h)
    out = pd.DataFrame(d, index=t.index)
    out.insert(0, "data_alvo", t[COL_DATA] + pd.Timedelta(weeks=h))
    out.insert(0, "data_origem", t[COL_DATA])
    return out


def matriz_do_braco(t, h, braco):
    cols = colunas_do_braco(braco)
    tudo = todas_as_variaveis(t, h)
    m = tudo[["data_origem", "data_alvo"] + cols + ["y_h"]]
    m = m.dropna(subset=cols + ["y_h"])
    return m.reset_index(drop=True)


def parametros(folha, quantil=0.85):
    return dict(loss="quantile", quantile=quantil, max_iter=250, learning_rate=0.05,
                max_leaf_nodes=15, min_samples_leaf=folha, random_state=42)


def prever_uma_origem(m, h, pos, folha, corte="resposta", colunas=None):
    cols = colunas or [c for c in m.columns if c not in ("data_origem", "data_alvo", "y_h")]
    t = m.loc[pos, "data_origem"]
    if corte == "resposta":
        treino = m[m["data_alvo"] <= t]
    else:  # ingenuo: pela data da pergunta
        treino = m[m["data_origem"] < t]
    mod = HistGradientBoostingRegressor(**parametros(folha))
    mod.fit(treino[cols], treino["y_h"])
    return float(mod.predict(m.loc[[pos], cols])[0]), len(treino)


def walk_forward(m, h, folha, treino_minimo=104, corte="resposta", colunas=None):
    cols = colunas or [c for c in m.columns if c not in ("data_origem", "data_alvo", "y_h")]
    linhas = []
    for pos in range(treino_minimo, len(m)):
        p, _ = prever_uma_origem(m, h, pos, folha, corte, cols)
        linhas.append((h, m.loc[pos, "data_origem"], m.loc[pos, "data_alvo"], float(m.loc[pos, "y_h"]), p))
    return pd.DataFrame(linhas, columns=["h", "data_origem", "data_alvo", "real", "previsto"])
