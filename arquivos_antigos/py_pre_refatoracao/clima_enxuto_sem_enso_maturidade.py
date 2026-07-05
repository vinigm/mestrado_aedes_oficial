"""Modelo 4c — clima_enxuto + vetor, sem ENSO, com CORTE DE MATURIDADE no alvo.

Corrige o bug do right-censoring: semanas de onset (SEM_PRI) cujos casos
confirmados ainda estao imaturos (dentro de MATURITY_WEEKS da data do extrato)
viram NaN em vez de zero falso. Re-roda o M0 (clima-enxuto s/ENSO) vs
M1 (+vetor) e compara com a versao contaminada (clima_enxuto_sem_enso_resultados.csv).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

MATURITY_WEEKS = 12   # ~janela de confirmacao/encerramento da dengue


def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError("raiz nao encontrada")


RAIZ = achar_raiz()
TAB = RAIZ / "Bases de dados" / "tabela_modelagem"
df = pd.read_csv(TAB / "tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"])
df = df.sort_values(["fonte", "data_inicio_semana_epidemi"]).reset_index(drop=True)

# --- CORTE DE MATURIDADE: zeros falsos recentes -> NaN ---
REF = df["data_inicio_semana_epidemi"].max()
corte = REF - pd.Timedelta(weeks=MATURITY_WEEKS)
imaturo = df["data_inicio_semana_epidemi"] > corte
n_cortadas = int((imaturo & df["casos_confirmados"].notna()).sum())
df.loc[imaturo, "casos_confirmados"] = np.nan
print(f"corte de maturidade: onset > {corte.date()} -> {n_cortadas} semanas viraram NaN (eram zero/baixo falso)")

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

DROP = ["aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas"]
ENSO = ["nino34_anom", "oni"]
ignorar = ["fonte", "SE", "data_inicio_semana_epidemi", "ano", "semana", "interpolado"] + DROP + ENSO
todas = [c for c in df.columns if c not in ignorar]
PADROES_VETOR = ("aedes", "armadilha", "vetor")
PADROES_CLIMA = ("temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva")
vetor = [c for c in todas if any(t in c for t in PADROES_VETOR)]
clima = [c for c in todas if any(t in c for t in PADROES_CLIMA)]
nucleo = [c for c in todas if c not in vetor and c not in clima]

PARAMS = dict(n_estimators=250, learning_rate=0.05, num_leaves=15,
              min_child_samples=5, verbose=-1, n_jobs=-1)


def alvo_h(df, h):
    g = df.groupby("fonte", group_keys=False)
    d = df.copy()
    d["y_h"] = g[ALVO].shift(-h)
    sa = g["semana"].shift(-h)
    d["alvo_sin"] = np.sin(2 * np.pi * sa / 52)
    d["alvo_cos"] = np.cos(2 * np.pi * sa / 52)
    return d


# selecao do clima (gain, dados iniciais, sem leakage)
imp = pd.Series(0.0, index=clima)
for h in (1, 4, 8):
    d = alvo_h(df, h)
    feats = nucleo + clima + ["alvo_sin", "alvo_cos"]
    dh = d.dropna(subset=feats + ["y_h"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
    tr = dh.iloc[:int(len(dh) * 0.60)]
    m = LGBMRegressor(**PARAMS).fit(tr[feats], tr["y_h"])
    gi = pd.Series(m.booster_.feature_importance(importance_type="gain"), index=feats)
    imp = imp.add(gi.reindex(clima).fillna(0), fill_value=0)
ranking = imp.sort_values(ascending=False)
print("clima top-8:", ranking.head(8).index.tolist())


def walk_forward(df, cols, horizontes=range(1, 13), min_treino=104, passo=2):
    linhas = []
    for h in horizontes:
        d = alvo_h(df, h)
        feats = cols + ["alvo_sin", "alvo_cos"]
        dh = d.dropna(subset=feats + ["y_h"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
        for i in range(min_treino, len(dh), passo):
            tr, te = dh.iloc[:i], dh.iloc[i:i + 1]
            m = LGBMRegressor(**PARAMS).fit(tr[feats], tr["y_h"])
            linhas.append({"h": h, "real": te["y_h"].values[0], "pred": m.predict(te[feats])[0]})
    return pd.DataFrame(linhas)


def metricas(res, nome):
    return [{"conjunto": nome, "h": h, "n": len(x),
             "MAE": mean_absolute_error(x["real"], x["pred"]),
             "R2": r2_score(x["real"], x["pred"])} for h, x in res.groupby("h")]


linhas = []
for K in (6, 8):
    clima_top = ranking.head(K).index.tolist()
    linhas += metricas(walk_forward(df, nucleo + clima_top), f"M0_clima{K}")
    linhas += metricas(walk_forward(df, nucleo + clima_top + vetor), f"M1_clima{K}_vetor")
comp = pd.DataFrame(linhas)

r2 = comp.pivot(index="h", columns="conjunto", values="R2").round(3)
mae = comp.pivot(index="h", columns="conjunto", values="MAE").round(1)
npts = comp.pivot(index="h", columns="conjunto", values="n")
for K in (6, 8):
    mae[f"lift_K{K}_%"] = ((mae[f"M0_clima{K}"] - mae[f"M1_clima{K}_vetor"]) / mae[f"M0_clima{K}"] * 100).round(1)

print(f"\npontos de teste por horizonte (h=1): {int(npts['M0_clima6'].iloc[0])} (era ~maior antes do corte)")
ordem = ["M0_clima6", "M1_clima6_vetor", "M0_clima8", "M1_clima8_vetor"]
print("\n=== R2 por horizonte (sem ENSO, COM corte de maturidade) ==="); print(r2[ordem].to_string())
print("\n=== MAE + lift marginal do vetor ==="); print(mae[ordem + ["lift_K6_%", "lift_K8_%"]].to_string())
comp.to_csv(TAB / "clima_enxuto_maturidade_resultados.csv", index=False)
print("\nsalvo: clima_enxuto_maturidade_resultados.csv")
