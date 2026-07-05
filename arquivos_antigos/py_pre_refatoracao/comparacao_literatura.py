#!/usr/bin/env python3
"""Comparação controlada com a literatura, nos MESMOS dados de POA / mesmas semanas / mesma métrica.
Como não temos as previsões publicadas dos autores, reproduzimos o MÉTODO deles (só-clima, estilo
Oliveira et al. 2025) e comparamos contra o nosso (clima + vetor de armadilha), ambos vs a realidade.
XGBoost (usado pelo Oliveira) não está instalado -> usamos LightGBM (mesmo tipo de gradient boosting)."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, balanced_accuracy_score
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor, LGBMClassifier

AQUI = Path(__file__).resolve().parent

def achar_raiz(m="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents, *AQUI.parents]:
        if (p / m).is_dir():
            return p
    raise FileNotFoundError
RAIZ = achar_raiz()
T = RAIZ / "Bases de dados" / "tabela_modelagem" / "tabela_final.csv"

df = pd.read_csv(T, parse_dates=["data_inicio_semana_epidemi"])
df = df.sort_values(["fonte", "data_inicio_semana_epidemi"]).reset_index(drop=True)
g = df.groupby("fonte", group_keys=False)

clima_base = ["temp_media", "precip_total_mm", "orvalho_media", "umid_media", "pressao_media"]
for col in clima_base:
    for k in [1, 2, 3, 4]:
        df[f"{col}_lag{k}"] = g[col].shift(k)
    df[f"{col}_mm4"] = g[col].transform(lambda s: s.rolling(4).mean())
df["vet"] = df["aedes_aegypti_por_armadilha"]
for k in [1, 2, 3, 4]:
    df[f"vet_lag{k}"] = g["vet"].shift(k)
df["vet_mm4"] = g["vet"].transform(lambda s: s.rolling(4).mean())
df["sin"] = np.sin(2 * np.pi * df["semana"] / 52)
df["cos"] = np.cos(2 * np.pi * df["semana"] / 52)

feat_clima = (clima_base + [f"{c}_lag{k}" for c in clima_base for k in [1, 2, 3, 4]]
              + [f"{c}_mm4" for c in clima_base] + ["sin", "cos"])
feat_vet = feat_clima + ["vet"] + [f"vet_lag{k}" for k in [1, 2, 3, 4]] + ["vet_mm4"]

REG = dict(n_estimators=250, learning_rate=0.05, num_leaves=15, min_child_samples=5, verbose=-1, n_jobs=-1)
CLF = dict(n_estimators=250, learning_rate=0.05, num_leaves=15, min_child_samples=5, verbose=-1, n_jobs=-1)

# ---------- PARTE 1: regressão de casos, só-clima × clima+vetor ----------
def wf_reg(feats, horizs=range(1, 13), min_t=104, passo=2):
    gg = df.groupby("fonte", group_keys=False)
    rows = []
    for h in horizs:
        d = df.copy(); d["y"] = gg["casos_confirmados"].shift(-h)
        dd = d.dropna(subset=feats + ["y"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
        for i in range(min_t, len(dd), passo):
            tr, te = dd.iloc[:i], dd.iloc[i:i + 1]
            m = LGBMRegressor(**REG).fit(tr[feats], tr["y"])
            rows.append({"h": h, "real": te["y"].values[0], "pred": m.predict(te[feats])[0]})
    r = pd.DataFrame(rows)
    return r.groupby("h").apply(lambda x: r2_score(x.real, x.pred), include_groups=False)

print("PARTE 1: regressão de casos (walk-forward)...")
r_clima = wf_reg(feat_clima)
r_vet = wf_reg(feat_vet)
p1 = pd.DataFrame({"R2_so_clima": r_clima, "R2_clima_vetor": r_vet})
p1["ganho"] = (p1["R2_clima_vetor"] - p1["R2_so_clima"])
print(p1.round(3).to_string())

# ---------- PARTE 2: réplica do Oliveira (aceleração de casos, Balanced Accuracy) ----------
# alvo: casos sobem vs 2 semanas atrás (analogo semanal ao "dia vs 15 dias" do Oliveira)
df["accel"] = (g["casos_confirmados"].diff(2) > 0).astype(int)

def wf_clf(feats, min_t=104, passo=1):
    dd = df.dropna(subset=feats + ["accel"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
    reals, preds = [], []
    for i in range(min_t, len(dd), passo):
        tr, te = dd.iloc[:i], dd.iloc[i:i + 1]
        if tr["accel"].nunique() < 2:
            continue
        m = LGBMClassifier(**CLF).fit(tr[feats], tr["accel"])
        preds.append(int(m.predict(te[feats])[0])); reals.append(int(te["accel"].values[0]))
    return balanced_accuracy_score(reals, preds), len(reals)

def rand_split(feats, seed=42):
    dd = df.dropna(subset=feats + ["accel"]).copy()
    Xtr, Xte, ytr, yte = train_test_split(dd[feats], dd["accel"], test_size=0.3,
                                          random_state=seed, stratify=dd["accel"])
    m = LGBMClassifier(**CLF).fit(Xtr, ytr)
    return balanced_accuracy_score(yte, m.predict(Xte))

print("\nPARTE 2: aceleração de casos (réplica Oliveira)...")
ba_wf_clima, n = wf_clf(feat_clima)
ba_wf_vet, _ = wf_clf(feat_vet)
ba_rs_clima = np.mean([rand_split(feat_clima, s) for s in [0, 1, 2, 3, 4]])
ba_rs_vet = np.mean([rand_split(feat_vet, s) for s in [0, 1, 2, 3, 4]])
print(f"  split aleatório (protocolo Oliveira): só-clima={ba_rs_clima:.3f} | clima+vetor={ba_rs_vet:.3f}  (Oliveira reportou 0,67)")
print(f"  walk-forward (honesto, n={n}):         só-clima={ba_wf_clima:.3f} | clima+vetor={ba_wf_vet:.3f}")

# ---------- gráficos ----------
TEAL, GRAY, ACC, INK = "#0e7c7b", "#9b9488", "#c25a22", "#0f2540"
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})

# Parte 1
fig, ax = plt.subplots(figsize=(8.6, 4.6))
ax.plot(p1.index, p1["R2_so_clima"], "s--", color=GRAY, lw=2.2, ms=6, label="só-clima (estilo literatura)")
ax.plot(p1.index, p1["R2_clima_vetor"], "o-", color=TEAL, lw=2.6, ms=7, label="clima + vetor (nosso)")
ax.axhline(0, color="#c9c2b4", lw=1)
ax.set_xlabel("horizonte (semanas à frente)"); ax.set_ylabel("R² — previsão de casos")
ax.set_title("Mesma POA, mesmas semanas: quem prevê melhor os casos?\nsó-clima × clima+vetor · walk-forward",
             fontsize=13, fontweight="bold", color=INK, loc="left")
ax.set_xticks(list(p1.index)); ax.legend(frameon=False); ax.grid(alpha=.25)
fig.tight_layout(); fig.savefig(AQUI / "comparacao_casos.png", bbox_inches="tight", facecolor="white")

# Parte 2
fig, ax = plt.subplots(figsize=(7.6, 4.6))
grupos = ["split aleatório\n(protocolo Oliveira)", "walk-forward\n(honesto)"]
x = np.arange(2); w = 0.36
ax.bar(x - w/2, [ba_rs_clima, ba_wf_clima], w, color=GRAY, label="só-clima (estilo literatura)")
ax.bar(x + w/2, [ba_rs_vet, ba_wf_vet], w, color=TEAL, label="clima + vetor (nosso)")
ax.axhline(0.6738, color=ACC, lw=2, ls=":", label="Oliveira 2025 (0,67)")
ax.axhline(0.5, color="#c9c2b4", lw=1, ls="--")
ax.set_xticks(x); ax.set_xticklabels(grupos); ax.set_ylim(0.45, 0.8)
ax.set_ylabel("Balanced Accuracy — aceleração de casos")
ax.set_title("Réplica da tarefa do Oliveira (POA)\naceleração de casos · LightGBM",
             fontsize=13, fontweight="bold", color=INK, loc="left")
ax.legend(frameon=False, fontsize=10.5); ax.grid(axis="y", alpha=.25)
for xi, v in zip([x[0]-w/2, x[0]+w/2, x[1]-w/2, x[1]+w/2], [ba_rs_clima, ba_rs_vet, ba_wf_clima, ba_wf_vet]):
    ax.text(xi, v+0.006, f"{v:.2f}", ha="center", fontsize=10, fontweight="bold", color=INK)
fig.tight_layout(); fig.savefig(AQUI / "comparacao_oliveira.png", bbox_inches="tight", facecolor="white")
print("\nsalvos: comparacao_casos.png, comparacao_oliveira.png\nDONE")
