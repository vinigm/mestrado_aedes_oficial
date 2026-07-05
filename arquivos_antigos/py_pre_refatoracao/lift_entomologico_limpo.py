"""Lift entomológico — versão LIMPA do bloco vetor.

Igual ao lift_entomologico.ipynb (mesmo walk-forward multi-horizonte, mesmos
params LightGBM, mesmo passo=2), mas o bloco "vetor" passa a ser SÓ a densidade
de Aedes aegypti (por armadilha) + lags + média móvel.

Removidos de TODOS os conjuntos (drop explícito, não reclassificados no núcleo):
  - aedes_albopictus, culex_sp   -> não são o vetor da dengue em foco
  - aedes_aegypti (total bruto)  -> depende do nº de armadilhas (esforço)
  - numero_de_armadilhas         -> esforço de coleta, não causa de dengue
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score


def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError(f"raiz com '{marcador}/' nao encontrada de {Path.cwd()}")


RAIZ = achar_raiz()
df = pd.read_csv(RAIZ / "Bases de dados" / "tabela_modelagem" / "tabela_final.csv",
                 parse_dates=["data_inicio_semana_epidemi"])
df = df.sort_values(["fonte", "data_inicio_semana_epidemi"]).reset_index(drop=True)
ALVO = "casos_confirmados"
g = df.groupby("fonte", group_keys=False)

for col in ["casos_confirmados", "aedes_aegypti_por_armadilha",
            "temp_media", "precip_total_mm", "orvalho_media", "umid_media", "pressao_media"]:
    for k in [1, 2, 3, 4]:
        df[f"{col}_lag{k}"] = g[col].shift(k)
df["casos_mm4"] = g["casos_confirmados"].transform(lambda s: s.rolling(4).mean())
df["vetor_mm4"] = g["aedes_aegypti_por_armadilha"].transform(lambda s: s.rolling(4).mean())
df["sem_sin"] = np.sin(2 * np.pi * df["semana"] / 52)
df["sem_cos"] = np.cos(2 * np.pi * df["semana"] / 52)

# --- LIMPEZA: tira essas colunas de qualquer conjunto de features ---
DROP = ["aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas"]
ignorar = ["fonte", "SE", "data_inicio_semana_epidemi", "ano", "semana", "interpolado"] + DROP
todas = [c for c in df.columns if c not in ignorar]

PADROES_VETOR = ("aedes", "armadilha", "vetor")  # sem "culex"
PADROES_CLIMA = ("temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva", "nino34", "oni")
vetor = [c for c in todas if any(t in c for t in PADROES_VETOR)]
clima = [c for c in todas if any(t in c for t in PADROES_CLIMA)]
nucleo = [c for c in todas if c not in vetor and c not in clima]

CONJUNTOS = {
    "so_clima": nucleo + clima,
    "clima_vetor": nucleo + clima + vetor,
    "so_vetor": nucleo + vetor,
}
print(f"nucleo: {len(nucleo)} | clima: {len(clima)} | vetor: {len(vetor)}")
print("vetor (limpo):", vetor)
print("nucleo:", nucleo)

PARAMS = dict(n_estimators=250, learning_rate=0.05, num_leaves=15,
              min_child_samples=5, verbose=-1, n_jobs=-1)


def walk_forward_conjunto(df, cols, alvo="casos_confirmados",
                          horizontes=range(1, 13), min_treino=104, passo=2):
    g = df.groupby("fonte", group_keys=False)
    linhas = []
    for h in horizontes:
        d = df.copy()
        d["y_h"] = g[alvo].shift(-h)
        sa = g["semana"].shift(-h)
        d["alvo_sin"] = np.sin(2 * np.pi * sa / 52)
        d["alvo_cos"] = np.cos(2 * np.pi * sa / 52)
        feats = cols + ["alvo_sin", "alvo_cos"]
        dh = d.dropna(subset=feats + ["y_h"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
        for i in range(min_treino, len(dh), passo):
            tr, te = dh.iloc[:i], dh.iloc[i:i + 1]
            m = LGBMRegressor(**PARAMS).fit(tr[feats], tr["y_h"])
            linhas.append({"h": h, "real": te["y_h"].values[0], "pred": m.predict(te[feats])[0]})
    return pd.DataFrame(linhas)


linhas = []
for nome, cols in CONJUNTOS.items():
    print("rodando:", nome, f"({len(cols)} features)", flush=True)
    res = walk_forward_conjunto(df, cols)
    for h, x in res.groupby("h"):
        linhas.append({"conjunto": nome, "h": h,
                       "MAE": mean_absolute_error(x["real"], x["pred"]),
                       "R2": r2_score(x["real"], x["pred"])})
comp = pd.DataFrame(linhas)

mae = comp.pivot(index="h", columns="conjunto", values="MAE").round(1)
r2 = comp.pivot(index="h", columns="conjunto", values="R2").round(3)
mae["lift_vetor_%"] = ((mae["so_clima"] - mae["clima_vetor"]) / mae["so_clima"] * 100).round(1)
mae["lift_sovetor_%"] = ((mae["so_clima"] - mae["so_vetor"]) / mae["so_clima"] * 100).round(1)
print("\n=== MAE por horizonte ==="); print(mae.to_string())
print("\n=== R2 por horizonte ==="); print(r2.to_string())
comp.to_csv(RAIZ / "Bases de dados" / "tabela_modelagem" / "lift_limpo_resultados.csv", index=False)
print("\nsalvo: lift_limpo_resultados.csv")
