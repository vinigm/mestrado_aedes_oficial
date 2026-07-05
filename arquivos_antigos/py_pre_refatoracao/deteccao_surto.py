"""Modelo 6 — DETECCAO DE SURTO (classificacao), o alvo que a tese promete.

Reformula o eixo cidade de REGRESSAO de volume (Modelos 1-5; lift do vetor
NAO-significativo por Diebold-Mariano) para DETECCAO DE SURTO (evento/limiar),
com metricas de alarme e teste de McNemar para o lift do vetor NA TAREFA CERTA.
Implementa o passo #1 do plano de aproveitamento do Robson (aproveitamento_robson.md).

Dois experimentos:
  A) InfoDengue notificado (2010-2026, sem censura): "da pra detectar surto
     1-3 meses a frente em POA?" — viabilidade + baselines (sazonal, persistencia).
  B) tabela_final (SINAN confirmado, 2019-23 + 2025-26, COM vetor): so-clima
     vs clima+vetor na deteccao -> McNemar (apples-to-apples com a regressao).

Definicao de surto: casos_{t+h} >= limiar, limiar = percentil (P90/P95) calculado
SO no treino de cada passo (point-in-time, sem leakage). Multi-horizonte direto
h=4/8/12 sem (=1/2/3 meses) = a antecedencia do alarme. Walk-forward expansivel.
Baselines: sazonal (taxa de surto por semana epi.) e persistencia de estado.
n_jobs=1 -> reproducivel.

Saidas:
  - Bases de dados/tabela_modelagem/deteccao_surto_resultados.csv (metricas)
  - Bases de dados/tabela_modelagem/deteccao_surto_mcnemar.csv (McNemar Exp B)
"""
from pathlib import Path
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import (confusion_matrix, roc_auc_score, average_precision_score,
                             f1_score, balanced_accuracy_score)

# --------------------------------------------------------------------- config
def achar_raiz(marcador="Raspagem"):
    for p in [Path.cwd(), *Path.cwd().parents]:
        if (p / marcador).is_dir():
            return p
    raise FileNotFoundError("raiz nao encontrada")

RAIZ = achar_raiz()
TAB = RAIZ / "Bases de dados" / "tabela_modelagem"
INFO = RAIZ / "Bases de dados" / "infodengue_poa" / "infodengue_poa_dengue.csv"

HORIZONTES = [4, 8, 12]          # 1, 2, 3 meses (a antecedencia do alarme)
PARAMS = dict(n_estimators=250, learning_rate=0.05, num_leaves=15,
              min_child_samples=5, class_weight="balanced", verbose=-1, n_jobs=1)
MIN_TREINO = 104                 # ~2 anos
pd.set_option("display.width", 170)


def mcnemar(acertos_a, acertos_b):
    """McNemar entre dois classificadores nos MESMOS pontos.
    acertos_* : arrays booleanos (predicao correta?). Retorna (n01, n10, stat, p)."""
    a = np.asarray(acertos_a, bool); b = np.asarray(acertos_b, bool)
    n01 = int(np.sum(a & ~b))     # A certo, B errado
    n10 = int(np.sum(~a & b))     # A errado, B certo
    n = n01 + n10
    if n == 0:
        return n01, n10, 0.0, 1.0
    stat = (abs(n01 - n10) - 1) ** 2 / n      # chi2 c/ correcao de continuidade
    from scipy.stats import chi2, binomtest
    if n < 25:                                 # exato binomial p/ n pequeno
        p = binomtest(min(n01, n10), n, 0.5).pvalue
    else:
        p = float(chi2.sf(stat, 1))
    return n01, n10, stat, p


def metricas_bloco(y, pred, prob=None):
    y = np.asarray(y, int); pred = np.asarray(pred, int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    sens = tp / (tp + fn) if (tp + fn) else np.nan       # recall / sensibilidade
    spec = tn / (tn + fp) if (tn + fp) else np.nan
    prec = tp / (tp + fp) if (tp + fp) else np.nan
    out = dict(n=len(y), n_pos=int((y == 1).sum()), tp=tp, fp=fp, fn=fn, tn=tn,
               sensib=sens, espec=spec, precisao=prec,
               f1=f1_score(y, pred, zero_division=0),
               bal_acc=balanced_accuracy_score(y, pred))
    if prob is not None and len(np.unique(y)) == 2:
        out["auc"] = roc_auc_score(y, prob)
        out["ap"] = average_precision_score(y, prob)
    return out


def montar_features(df, fonte_col="fonte"):
    """lags/rolling/sazonalidade por bloco (mesma receita dos Modelos 1-5)."""
    g = df.groupby(fonte_col, group_keys=False)
    for col in ["casos", "aedes_aegypti_por_armadilha", "temp_media",
                "precip_total_mm", "orvalho_media", "umid_media", "pressao_media"]:
        if col in df.columns:
            for k in [1, 2, 3, 4]:
                df[f"{col}_lag{k}"] = g[col].shift(k)
    if "casos" in df.columns:
        df["casos_mm4"] = g["casos"].transform(lambda s: s.rolling(4).mean())
    if "aedes_aegypti_por_armadilha" in df.columns:
        df["vetor_mm4"] = g["aedes_aegypti_por_armadilha"].transform(lambda s: s.rolling(4).mean())
    df["sem_sin"] = np.sin(2 * np.pi * df["semana"] / 52)
    df["sem_cos"] = np.cos(2 * np.pi * df["semana"] / 52)
    return df


def walk_forward_surto(df, feats, fonte_col, h, pctl, passo=1):
    """Walk-forward expansivel; alvo = surto (casos_{t+h} >= P{pctl} do TREINO).
    Retorna real + predicoes de 3 modelos que compartilham os MESMOS folds/limiar:
      - LGBM(feats): clima(+vetor) + AR + sazonalidade
      - sazonal: taxa de surto por semana epidemiologica do alvo (so treino)
      - persistencia: surto_{t+h} = surto_t (estado atual persiste)."""
    g = df.groupby(fonte_col, group_keys=False)
    d = df.copy()
    d["casos_h"] = g["casos"].shift(-h)
    d["semana_alvo"] = g["semana"].shift(-h)
    d["alvo_sin"] = np.sin(2 * np.pi * d["semana_alvo"] / 52)
    d["alvo_cos"] = np.cos(2 * np.pi * d["semana_alvo"] / 52)
    cols = feats + ["alvo_sin", "alvo_cos"]
    dh = d.dropna(subset=cols + ["casos_h", "casos", "semana_alvo"]).sort_values("data").reset_index(drop=True)
    linhas = []
    for i in range(MIN_TREINO, len(dh), passo):
        tr, te = dh.iloc[:i], dh.iloc[i:i + 1]
        lim = np.percentile(tr["casos_h"], pctl)          # limiar so no treino
        ytr = (tr["casos_h"].values >= lim).astype(int)
        yte = int(te["casos_h"].values[0] >= lim)
        if len(np.unique(ytr)) < 2:                        # treino degenerado
            continue
        m = LGBMClassifier(**PARAMS).fit(tr[cols], ytr)
        prob = float(m.predict_proba(te[cols])[0, 1])
        # baseline sazonal: prob = fracao de surto no treino na mesma sem.epi.(+-1) do alvo
        sw = te["semana_alvo"].values[0]
        dist = np.minimum(np.abs(tr["semana_alvo"].values - sw), 52 - np.abs(tr["semana_alvo"].values - sw))
        mask = dist <= 1
        prob_saz = float(ytr[mask].mean()) if mask.sum() else float(ytr.mean())
        # baseline persistencia: surto agora (casos_t >= limiar do alvo) persiste
        pred_pers = int(te["casos"].values[0] >= lim)
        linhas.append({"h": h, "real": yte, "data": te["data"].values[0],
                       "prob": prob, "pred": int(prob >= 0.5),
                       "prob_saz": prob_saz, "pred_saz": int(prob_saz >= 0.5),
                       "pred_pers": pred_pers})
    return pd.DataFrame(linhas)


# ============================================================ EXPERIMENTO A
print("#" * 80)
print("# EXPERIMENTO A — InfoDengue notificado (2010-2026, sem censura)")
print("#   'da pra detectar surto 1-3 meses a frente em POA?'")
print("#" * 80)
info = pd.read_csv(INFO, parse_dates=["data_iniSE"]).rename(columns={"data_iniSE": "data"})
info = info.sort_values("data").reset_index(drop=True)
info["ano"] = info["SE"].astype(str).str[:4].astype(int)
info["semana"] = info["SE"].astype(str).str[4:].astype(int)
info["fonte"] = "infodengue"
info["temp_media"] = info["tempmed"]; info["umid_media"] = info["umidmed"]
info = montar_features(info)
FEATS_A = [c for c in info.columns if c.startswith(("casos_lag", "casos_mm",
           "temp_media_lag", "umid_media_lag"))] + ["sem_sin", "sem_cos"]

linhas_a = []
for pctl in (90, 95):
    for h in HORIZONTES:
        res = walk_forward_surto(info, FEATS_A, "fonte", h, pctl)
        for nome, pred_c, prob_c in [("clima+AR_LGBM", "pred", "prob"),
                                      ("sazonal", "pred_saz", "prob_saz"),
                                      ("persistencia", "pred_pers", None)]:
            m = metricas_bloco(res["real"], res[pred_c], res[prob_c] if prob_c else None)
            m.update(dict(exp="A_infodengue", pctl=pctl, h=h, modelo=nome))
            linhas_a.append(m)
resA = pd.DataFrame(linhas_a)
print(resA[["pctl", "h", "modelo", "n", "n_pos", "sensib", "espec", "f1", "bal_acc", "auc", "ap"]].round(3).to_string(index=False))

# ============================================================ EXPERIMENTO B
print("\n" + "#" * 80)
print("# EXPERIMENTO B — tabela_final: so-clima vs clima+VETOR na deteccao (McNemar)")
print("#" * 80)
df = pd.read_csv(TAB / "tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"]).rename(
    columns={"data_inicio_semana_epidemi": "data", "casos_confirmados": "casos"})
df = df.sort_values(["fonte", "data"]).reset_index(drop=True)
# corte de maturidade (Modelo 4c): zeros falsos recentes -> NaN
REF = df["data"].max(); corte = REF - pd.Timedelta(weeks=12)
df.loc[df["data"] > corte, "casos"] = np.nan
df = montar_features(df)

CLIMA = [c for c in df.columns if c.startswith(("temp_media_lag", "precip_total_mm_lag",
         "orvalho_media_lag", "umid_media_lag", "pressao_media_lag"))]
AR = [c for c in df.columns if c.startswith(("casos_lag", "casos_mm"))]
VETOR = [c for c in df.columns if c.startswith(("aedes_aegypti_por_armadilha_lag", "vetor_mm"))]
FEATS_CLIMA = AR + CLIMA + ["sem_sin", "sem_cos"]
FEATS_VETOR = AR + CLIMA + VETOR + ["sem_sin", "sem_cos"]

linhas_b, linhas_mc = [], []
for pctl in (90, 95):
    for h in HORIZONTES:
        r_clima = walk_forward_surto(df, FEATS_CLIMA, "fonte", h, pctl)
        r_vetor = walk_forward_surto(df, FEATS_VETOR, "fonte", h, pctl)
        j = r_clima.merge(r_vetor, on=["h", "data", "real"], suffixes=("_c", "_v"))
        # baseline sazonal (identico nos dois; vem do r_clima)
        ms = metricas_bloco(j["real"], j["pred_saz_c"], j["prob_saz_c"])
        ms.update(dict(exp="B_tabela_final", pctl=pctl, h=h, modelo="sazonal"))
        linhas_b.append(ms)
        for nome, sufixo in [("so-clima", "_c"), ("clima+vetor", "_v")]:
            m = metricas_bloco(j["real"], j[f"pred{sufixo}"], j[f"prob{sufixo}"])
            m.update(dict(exp="B_tabela_final", pctl=pctl, h=h, modelo=nome))
            linhas_b.append(m)
        # McNemar clima vs clima+vetor
        n01, n10, stat, p = mcnemar((j["pred_c"] == j["real"]).values,
                                    (j["pred_v"] == j["real"]).values)
        linhas_mc.append(dict(pctl=pctl, h=h, n=len(j), n_pos=int(j["real"].sum()),
                              clima_certo_vetor_errado=n01, vetor_certo_clima_errado=n10, p=round(p, 3)))
        print(f"  P{pctl} h={h:2d}: n={len(j):3d} pos={int(j['real'].sum()):2d} | "
              f"clima>vetor={n01} vetor>clima={n10} McNemar p={p:.3f}")
resB = pd.DataFrame(linhas_b)
print("\n=== Metricas por modelo (Experimento B) ===")
print(resB[["pctl", "h", "modelo", "n", "n_pos", "sensib", "espec", "f1", "bal_acc", "auc", "ap"]].round(3).to_string(index=False))

# --------------------------------------------------------------------- salvar
out = pd.concat([resA, resB], ignore_index=True)
out.to_csv(TAB / "deteccao_surto_resultados.csv", index=False)
pd.DataFrame(linhas_mc).to_csv(TAB / "deteccao_surto_mcnemar.csv", index=False)
print("\nsalvo:", TAB / "deteccao_surto_resultados.csv")
print("salvo:", TAB / "deteccao_surto_mcnemar.csv")
