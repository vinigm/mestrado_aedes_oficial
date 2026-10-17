import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGB
from cert_comum import *
t = tabela(); nuc, cli, vet = grupos(t); M1 = nuc + CLIMA6 + vet
O = f"{RAIZ}/analises/2026-09-23_bateria_noturna/bloco_6_hiperparametros/saidas"
old = pd.read_csv(f"{O}/previsoes_por_configuracao.csv", parse_dates=["data_alvo"], float_precision="round_trip")
def fit_pred(h, lr, it, fol, mn, idx_list, v, cs):
    out = {}
    for i in idx_list:
        tr = treino_corrigido(v, i, h)
        m = HGB(loss="quantile", quantile=0.85, max_iter=it, learning_rate=lr, max_leaf_nodes=fol, min_samples_leaf=mn, random_state=42).fit(tr[cs], tr["y_h"])
        out[v["data"].iloc[i]] = float(m.predict(v.iloc[[i]][cs])[0])   # sem truncar em 0
    return out
pior = 0; N = 0
casos = [(8, 0.03, 400, 15, 5), (4, 0.10, 150, 31, 20), (4, 0.10, 150, 15, 20), (12, 0.03, 400, 7, 5)]
for h, lr, it, fol, mn in casos:
    nome = f"lr{lr if lr!=0.1 else 0.1}_it{it}_folhas{fol}_min{mn}"
    v, cs = validos(t, h, M1); n = len(v)
    idx = [104, 177, 260, n-60, n-1]
    p = fit_pred(h, lr, it, fol, mn, idx, v, cs)
    ref = old[(old.braco==nome)&(old.h==h)].set_index("data_alvo")
    for o, val in p.items():
        al = o + pd.Timedelta(weeks=h); r = ref.loc[al, "previsto"]
        d = abs(val-r); pior = max(pior, d); N += 1
        print(f"{nome:30s} h={h:2d} origem={o.date()} meu={val:.10f} antigo={r:.10f} dif={d:.2e}")
    if (fol, mn) == (31, 20): p31 = p
    if (fol, mn) == (15, 20): p15 = p
print("N:", N, "dif max:", pior)
print("empate folhas15 vs folhas31 (min20, lr0.1, h=4): dif max entre as previsoes:", max(abs(p15[k]-p31[k]) for k in p15))
