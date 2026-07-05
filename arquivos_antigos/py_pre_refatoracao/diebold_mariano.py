"""Teste de Diebold-Mariano: o lift do vetor (M1) sobre o clima (M0) e significativo?

Compara, ponto a ponto e por horizonte, os erros de:
  M0 = nucleo + clima_enxuto (sem ENSO)        -- baseline "literatura"
  M1 = M0 + vetor (densidade de aegypti, 6)    -- + armadilha

DM proprio para previsao de h passos: variancia HAC (Newey-West, lag h-1) +
correcao de amostra pequena Harvey-Leybourne-Newbold (HLN), comparada a t(n-1).
H1 (unilateral): M1 erra MENOS que M0 (d_bar > 0, d = loss_M0 - loss_M1).

Roda nas DUAS versoes do alvo:
  - SEM corte de maturidade (= setup do Modelo 4b)
  - COM corte de maturidade 12 sem (= setup do Modelo 4c)
para checar se a significancia depende do corte.

PAREAMENTO: M0 e M1 sao avaliados nos MESMOS pontos de teste (dropna pela uniao
das features), senao o teste pareado nao e valido.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy import stats


def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError("raiz nao encontrada")


RAIZ = achar_raiz()
TAB = RAIZ / "Bases de dados" / "tabela_modelagem"
PARAMS = dict(n_estimators=250, learning_rate=0.05, num_leaves=15,
              min_child_samples=5, verbose=-1, n_jobs=-1)
K = 6


def montar(maturidade):
    df = pd.read_csv(TAB / "tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"])
    df = df.sort_values(["fonte", "data_inicio_semana_epidemi"]).reset_index(drop=True)
    if maturidade:
        REF = df["data_inicio_semana_epidemi"].max()
        corte = REF - pd.Timedelta(weeks=12)
        df.loc[df["data_inicio_semana_epidemi"] > corte, "casos_confirmados"] = np.nan
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
    ign = ["fonte", "SE", "data_inicio_semana_epidemi", "ano", "semana", "interpolado"] + DROP + ENSO
    todas = [c for c in df.columns if c not in ign]
    PV = ("aedes", "armadilha", "vetor")
    PC = ("temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva")
    vetor = [c for c in todas if any(t in c for t in PV)]
    clima = [c for c in todas if any(t in c for t in PC)]
    nucleo = [c for c in todas if c not in vetor and c not in clima]
    return df, nucleo, clima, vetor


def alvo_h(df, h):
    g = df.groupby("fonte", group_keys=False)
    d = df.copy()
    d["y_h"] = g["casos_confirmados"].shift(-h)
    sa = g["semana"].shift(-h)
    d["alvo_sin"] = np.sin(2 * np.pi * sa / 52)
    d["alvo_cos"] = np.cos(2 * np.pi * sa / 52)
    return d


def seleciona_clima(df, nucleo, clima):
    imp = pd.Series(0.0, index=clima)
    for h in (1, 4, 8):
        d = alvo_h(df, h)
        feats = nucleo + clima + ["alvo_sin", "alvo_cos"]
        dh = d.dropna(subset=feats + ["y_h"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
        tr = dh.iloc[:int(len(dh) * 0.60)]
        m = LGBMRegressor(**PARAMS).fit(tr[feats], tr["y_h"])
        gi = pd.Series(m.booster_.feature_importance(importance_type="gain"), index=feats)
        imp = imp.add(gi.reindex(clima).fillna(0), fill_value=0)
    return imp.sort_values(ascending=False).head(K).index.tolist()


def erros_pareados(df, cols_m0, cols_m1, h, min_treino=104, passo=1):
    """Treina M0 e M1 nos MESMOS pontos (dropna pela uniao=M1) e retorna erros pareados."""
    d = alvo_h(df, h)
    feats_m1 = cols_m1 + ["alvo_sin", "alvo_cos"]      # superset (inclui M0 + vetor)
    feats_m0 = cols_m0 + ["alvo_sin", "alvo_cos"]
    dh = d.dropna(subset=feats_m1 + ["y_h"]).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)
    e0, e1 = [], []
    for i in range(min_treino, len(dh), passo):
        tr, te = dh.iloc[:i], dh.iloc[i:i + 1]
        p0 = LGBMRegressor(**PARAMS).fit(tr[feats_m0], tr["y_h"]).predict(te[feats_m0])[0]
        p1 = LGBMRegressor(**PARAMS).fit(tr[feats_m1], tr["y_h"]).predict(te[feats_m1])[0]
        y = te["y_h"].values[0]
        e0.append(y - p0)
        e1.append(y - p1)
    return np.array(e0), np.array(e1)


def dm(e0, e1, h, loss="sq"):
    d = (e0**2 - e1**2) if loss == "sq" else (np.abs(e0) - np.abs(e1))
    n = len(d)
    dbar = d.mean()
    dm0 = d - dbar
    def autocov(k):
        return np.sum(dm0[k:] * dm0[:n - k]) / n
    var = autocov(0) + 2 * sum(autocov(k) for k in range(1, h))
    if var <= 0:
        return dbar, np.nan, np.nan, n
    stat = dbar / np.sqrt(var / n)
    hln = (n + 1 - 2 * h + h * (h - 1) / n) / n          # correcao amostra pequena
    stat *= np.sqrt(max(hln, 1e-9))
    p_um = stats.t.cdf(-stat, df=n - 1)                  # H1: M1 melhor (d>0)
    return dbar, stat, p_um, n


for maturidade in (False, True):
    tag = "COM corte de maturidade (Modelo 4c)" if maturidade else "SEM corte (Modelo 4b)"
    df, nucleo, clima, vetor = montar(maturidade)
    clima_top = seleciona_clima(df, nucleo, clima)
    M0, M1 = nucleo + clima_top, nucleo + clima_top + vetor
    print(f"\n================ {tag} ================")
    print("clima_enxuto:", clima_top)
    print(f"{'h':>3} {'n':>4} {'dMAE':>7} {'DM(sq)':>8} {'p_sq':>8} {'DM(abs)':>8} {'p_abs':>8}  sig?")
    for h in range(1, 13):
        e0, e1 = erros_pareados(df, M0, M1, h)
        dmae = np.abs(e0).mean() - np.abs(e1).mean()        # >0 => vetor melhor
        _, s_sq, p_sq, n = dm(e0, e1, h, "sq")
        _, s_ab, p_ab, _ = dm(e0, e1, h, "abs")
        sig = "***" if min(p_sq, p_ab) < 0.01 else "**" if min(p_sq, p_ab) < 0.05 else "*" if min(p_sq, p_ab) < 0.10 else ""
        print(f"{h:>3} {n:>4} {dmae:>+7.2f} {s_sq:>8.2f} {p_sq:>8.3f} {s_ab:>8.2f} {p_ab:>8.3f}  {sig}")
print("\np = prob. de a vantagem do vetor ser acaso (unilateral, H1: vetor erra menos). *** p<0.01  ** p<0.05  * p<0.10")
