#!/usr/bin/env python3
"""Testa engenharia de features v2 (leak-safe) no modelo por bairro.
Compara: base(own), base(+viz), enhanced(own), enhanced(+viz)."""
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import r2_score
from lightgbm import LGBMRegressor

def achar_raiz(m="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / m).is_dir(): return p
    raise FileNotFoundError
RAIZ = achar_raiz(); DIR = RAIZ / "Bases de dados" / "dados_marilia"

cap = pd.concat([pd.read_csv(DIR / f"saida_{y}.csv", sep=";") for y in range(2019, 2024)], ignore_index=True)
cap["bairro"] = cap["Local"].astype(str).str.upper().str.strip()
for c in ["Latitude", "Longitude", "Aedes aegypti"]:
    cap[c] = pd.to_numeric(cap[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")
painel = (cap.groupby(["bairro", "Ano", "Semana"])
          .agg(aegypti=("Aedes aegypti", "sum"), n=("ID", "count"),
               lat=("Latitude", "mean"), lon=("Longitude", "mean")).reset_index())
painel["dens"] = painel["aegypti"] / painel["n"]
sem = painel[["Ano", "Semana"]].drop_duplicates().sort_values(["Ano", "Semana"]).reset_index(drop=True)
sem["t"] = np.arange(len(sem)); painel = painel.merge(sem, on=["Ano", "Semana"])
bairros = sorted(painel["bairro"].unique())
grid = pd.MultiIndex.from_product([bairros, sem["t"].values], names=["bairro", "t"]).to_frame(index=False)
df = (grid.merge(painel[["bairro", "t", "dens"]], on=["bairro", "t"], how="left")
          .merge(sem[["t", "Semana"]], on="t", how="left"))
df["dens"] = df["dens"].fillna(0.0); df = df.sort_values(["bairro", "t"]).reset_index(drop=True)

# vizinhança: simples (mean) e ponderada por distância
cent = painel.groupby("bairro")[["lat", "lon"]].mean().loc[bairros]
K = 4
dist, idx = NearestNeighbors(n_neighbors=K + 1).fit(cent.values).kneighbors(cent.values)
viz_de = {bairros[i]: [bairros[j] for j in idx[i][1:]] for i in range(len(bairros))}
piv = df.pivot(index="t", columns="bairro", values="dens")
viz = pd.DataFrame({b: piv[viz_de[b]].mean(axis=1) for b in bairros})
df = df.merge(viz.reset_index().melt(id_vars="t", var_name="bairro", value_name="viz"), on=["t", "bairro"], how="left")

g = df.groupby("bairro", group_keys=False)
for k in [1, 2, 3, 4]:
    df[f"dens_lag{k}"] = g["dens"].shift(k)
    df[f"viz_lag{k}"] = g["viz"].shift(k)
df["dens_mm4"] = g["dens"].transform(lambda s: s.rolling(4).mean())
df["sin"] = np.sin(2 * np.pi * df["Semana"] / 52); df["cos"] = np.cos(2 * np.pi * df["Semana"] / 52)
# --- v2 features (leak-safe) ---
df["crit"] = g["dens"].transform(lambda s: s.expanding().mean().shift(1))     # criticidade point-in-time
df["dens_lag8"] = g["dens"].shift(8)
df["dens_lag52"] = g["dens"].shift(52)                                        # sazonal (ano anterior)
df["viz_mm4"] = g["viz"].transform(lambda s: s.rolling(4).mean())
df["grad1"] = df["dens_lag1"] - df["viz_lag1"]                                # gradiente bairro - vizinhos

own_base = [f"dens_lag{k}" for k in [1, 2, 3, 4]] + ["dens_mm4", "sin", "cos"]
viz_base = own_base + [f"viz_lag{k}" for k in [1, 2, 3, 4]]
own_enh = own_base + ["crit", "dens_lag8", "dens_lag52"]                      # + alvo_sin/cos na hora
viz_enh = own_enh + [f"viz_lag{k}" for k in [1, 2, 3, 4]] + ["viz_mm4", "grad1"]

PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20, verbose=-1, n_jobs=-1)

def avaliar(feats, alvo_saz=False, horizontes=range(1, 5), min_t=120, passo=4):
    gg = df.groupby("bairro", group_keys=False); Tmax = int(df["t"].max()); out = []
    for h in horizontes:
        d = df.copy(); d["y"] = gg["dens"].shift(-h)
        fs = list(feats)
        if alvo_saz:
            asem = gg["Semana"].shift(-h)
            d["alvo_sin"] = np.sin(2 * np.pi * asem / 52); d["alvo_cos"] = np.cos(2 * np.pi * asem / 52)
            fs = fs + ["alvo_sin", "alvo_cos"]
        dd = d.dropna(subset=fs + ["y"])
        for i in range(min_t, Tmax - h + 1, passo):
            tr, te = dd[dd["t"] < i], dd[dd["t"] == i]
            if len(te) == 0 or len(tr) < 200: continue
            m = LGBMRegressor(**PARAMS).fit(tr[fs], tr["y"])
            out.append(pd.DataFrame({"h": h, "real": te["y"].values, "pred": m.predict(te[fs])}))
    r = pd.concat(out, ignore_index=True)
    return r.groupby("h").apply(lambda x: r2_score(x.real, x.pred), include_groups=False)

print("rodando 4 combos...")
res = pd.DataFrame({
    "base_own":  avaliar(own_base),
    "base_+viz": avaliar(viz_base),
    "enh_own":   avaliar(own_enh, alvo_saz=True),
    "enh_+viz":  avaliar(viz_enh, alvo_saz=True),
}).round(3)
res["ganho_enh"] = (res["enh_+viz"] - res["base_+viz"]).round(3)
res["lift_viz_enh"] = (res["enh_+viz"] - res["enh_own"]).round(3)
print("\n==== R² por horizonte ====")
print(res.to_string())
print("\nmédia R²: base_own=%.3f base_+viz=%.3f enh_own=%.3f enh_+viz=%.3f"
      % (res.base_own.mean(), res["base_+viz"].mean(), res.enh_own.mean(), res["enh_+viz"].mean()))
