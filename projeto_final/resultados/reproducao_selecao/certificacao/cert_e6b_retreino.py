import sys, numpy as np, pandas as pd, lightgbm as lgb
from sklearn.ensemble import HistGradientBoostingRegressor as HGB, GradientBoostingRegressor as GBR
from cert_comum import *
t = tabela(); nuc, cli, vet = grupos(t)
M0 = nuc + CLIMA6; M1 = nuc + CLIMA6 + vet
print("M0", len(M0)+2, "M1", len(M1)+2, "vetor:", vet)
def modelo(alg, perda):
    q = None if perda=="padrao" else float(perda.split("_")[1])
    if alg=="hist_gradient_boosting":
        kw = dict(max_iter=250, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=5, random_state=42)
        kw.update(loss="squared_error") if q is None else kw.update(loss="quantile", quantile=q)
        return HGB(**kw)
    if alg=="gradient_boosting":
        kw = dict(n_estimators=250, learning_rate=0.05, max_depth=3, min_samples_leaf=5, random_state=42)
        kw.update(loss="squared_error") if q is None else kw.update(loss="quantile", alpha=q)
        return GBR(**kw)
    kw = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20, verbose=-1, n_jobs=1, random_state=42)
    kw.update(objective="regression") if q is None else kw.update(objective="quantile", alpha=q)
    return lgb.LGBMRegressor(**kw)
new = pd.read_csv(f"{PROJ}/resultados/reproducao_selecao/E6b_grade30/previsoes.csv", parse_dates=["data_origem","data_alvo"], float_precision="round_trip")
casos = [("hist_gradient_boosting","quantil_0.85","M1_com_vetor",4),
         ("gradient_boosting","quantil_0.80","M1_com_vetor",12),
         ("lightgbm","quantil_0.90","M1_com_vetor",1),
         ("lightgbm","padrao","M0_sem_vetor",8),
         ("hist_gradient_boosting","padrao","M0_sem_vetor",4)]
tot = 0; piorr = 0
for alg, perda, conj, h in casos:
    cols = M1 if conj.startswith("M1") else M0
    v, cs = validos(t, h, cols)
    n = len(v)
    idx = [104, 150, 250, n-1] if h!=8 else [104, 140, 230, n-1]
    # origem dentro da enchente de 2024 (buracos)
    enchente = v.index[(v["data"]>="2024-05-19")&(v["data"]<="2024-06-02")].tolist()[:1]
    idx = sorted(set(idx+enchente))
    sub = new[(new.algoritmo==alg)&(new.perda==perda)&(new.conjunto==conj)&(new.h==h)].set_index("data_origem")
    for i in idx:
        tr = treino_corrigido(v, i, h)
        m = modelo(alg, perda).fit(tr[cs], tr["y_h"])
        p = max(float(m.predict(v.iloc[[i]][cs])[0]), 0.0)
        o = v["data"].iloc[i]
        ref = sub.loc[o, "previsto"]; real_ref = sub.loc[o, "real"]
        d = abs(p-ref); tot += 1; piorr = max(piorr, d)
        print(f"{alg:24s} {perda:13s} {conj} h={h:2d} origem={o.date()} n_treino={len(tr)} meu={p:.10f} executor={ref:.10f} dif={d:.2e} real_ok={abs(v['y_h'].iloc[i]-real_ref)==0}")
print("N previsoes comparadas:", tot, "dif max:", piorr)
