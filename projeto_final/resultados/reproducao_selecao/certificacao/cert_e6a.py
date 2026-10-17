"""Certificacao independente da E6a: selecao de clima. Codigo proprio, sem importar aedes/."""
import numpy as np, pandas as pd, lightgbm as lgb, json, sys
RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final"
t = pd.read_csv(f"{RAIZ}/dados/tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"])
t = t.rename(columns={"data_inicio_semana_epidemi": "data", "casos_confirmados": "casos"})
# corte de maturidade (surto.py antigo)
ult = t.dropna(subset=["casos"])["data"].max()
lim = ult - pd.Timedelta(weeks=12)
t.loc[t["data"] > lim, "casos"] = np.nan
print("ultima semana com caso crua:", ult, "limite:", lim, "casos nao nulos apos corte:", t["casos"].notna().sum())
for c in ["casos","aedes_aegypti_por_armadilha","temp_media","precip_total_mm","orvalho_media","umid_media","pressao_media"]:
    for l in (1,2,3,4):
        t[f"{c}_lag{l}"] = t[c].shift(l)
t["casos_mm4"] = t["casos"].rolling(4).mean()
t["vetor_mm4"] = t["aedes_aegypti_por_armadilha"].rolling(4).mean()
ang = 2*np.pi*t["semana"]/52
t["sem_sin"] = np.sin(ang); t["sem_cos"] = np.cos(ang)
IGN = ("fonte","SE","data","ano","semana","interpolado","denominador_aproximado","aedes_aegypti","aedes_albopictus","culex_sp","numero_de_armadilhas","nino34_anom","oni")
todas = [c for c in t.columns if c not in IGN]
vetor = [c for c in todas if any(p in c for p in ("aedes","armadilha","vetor"))]
clima = [c for c in todas if any(p in c for p in ("temp","precip","orvalho","umid","pressao","radiacao","vento","dias_de_chuva"))]
nucleo = [c for c in todas if c not in vetor and c not in clima]
print(len(nucleo), nucleo); print(len(clima), len(vetor))
def rodar(nj, sem):
    imp = pd.Series(0.0, index=clima); porh = {}
    for h in (1,4,8):
        d = t.copy(); d["y_h"] = t["casos"].shift(-h)
        sa = t["semana"].shift(-h); a = 2*np.pi*sa/52
        d["alvo_sin"] = np.sin(a); d["alvo_cos"] = np.cos(a)
        feats = nucleo + clima + ["alvo_sin","alvo_cos"]
        v = d.dropna(subset=feats+["y_h"]).sort_values("data").reset_index(drop=True)
        n = int(len(v)*0.6); tr = v.iloc[:n]
        kw = dict(n_estimators=250, learning_rate=0.05, num_leaves=15, min_child_samples=5, verbose=-1, n_jobs=nj)
        if sem is not None: kw["random_state"] = sem
        m = lgb.LGBMRegressor(**kw).fit(tr[feats], tr["y_h"])
        g = pd.Series(m.booster_.feature_importance(importance_type="gain"), index=feats)
        porh[h] = g.reindex(clima).fillna(0)
        imp = imp.add(porh[h], fill_value=0)
        print("h",h,"validas",len(v),"treino",n)
    return imp.sort_values(ascending=False), porh
res = {}
for nome, nj, sem in [("a_nj-1_semsemente",-1,None),("b_nj1_semsemente",1,None),("c_nj1_s42",1,42),("d_nj1_s42_repetida",1,42),("e_nj1_s7",1,7)]:
    r, porh = rodar(nj, sem)
    res[nome] = r
    print(nome, list(r.index[:8]), [f"{x:.0f}" for x in r.iloc[:8]])
    r.to_csv(f"cert_e6a_ganho_{nome}.csv", header=["ganho_total"])
ex = pd.read_csv(f"{RAIZ}/resultados/reproducao_selecao/E6a_clima/ganho_identico_ao_antigo.csv")
for nome, r in res.items():
    m = ex.set_index("candidata")["ganho_total"].reindex(r.index)
    print(nome, "dif max vs executor identico_ao_antigo:", float((m-r).abs().max()))
