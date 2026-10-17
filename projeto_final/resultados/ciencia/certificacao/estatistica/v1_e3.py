import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from reimpl import *
prev = carregar_parciais()
ex = pd.read_csv(RAIZ+"/resultados/ciencia/E3_composto/previsoes.csv", float_precision="round_trip", parse_dates=["data_origem","data_alvo"])
rs = pd.read_csv(RAIZ+"/resultados/ciencia/E3_composto/resumo.csv", float_precision="round_trip")
print("exec rows", len(ex), ex.groupby("N").size().to_dict())
meus=[]
for N in (8,13,26):
    for h in range(1,13):
        meus.append(composto(prev,N,h))
meus=pd.concat(meus,ignore_index=True)
print("meus rows", len(meus))
# leak check
vaz = (meus.max_data_alvo_usada > meus.data_origem).sum()
print("linhas com semana-alvo usada > origem (meu codigo):", vaz)
m = meus.merge(ex, on=["N","h","data_alvo"], how="outer", suffixes=("_m","_e"), indicator=True)
print(m["_merge"].value_counts().to_dict())
b = m[m["_merge"]=="both"]
print("max |dprevisto|", (b.previsto_m-b.previsto_e).abs().max(), " max |dreal|", (b.real_m-b.real_e).abs().max())
print("folha diferente:", (b.folha_escolhida_m!=b.folha_escolhida_e).sum(), " origem dif:", (b.data_origem_m!=b.data_origem_e).sum())
print(m[m["_merge"]!="both"].groupby(["N","h","_merge"]).size().head(20))
# resumo na janela
w = meus[(meus.data_alvo>=JANELA_INI)&(meus.data_alvo<=JANELA_FIM)]
res = w.assign(ae=(w.real-w.previsto).abs(), f20=(w.folha_escolhida==20)).groupby(["N","h"]).agg(n=("ae","size"),mae=("ae","mean"),fracao_folha20=("f20","mean")).reset_index()
c = res.merge(rs,on=["N","h"],suffixes=("_m","_e"))
print("resumo: n difere:", (c.n_m!=c.n_e).sum(), " max|dmae|", (c.mae_m-c.mae_e).abs().max(), " max|dfrac|", (c.fracao_folha20_m-c.fracao_folha20_e).abs().max(), "linhas", len(c))
print(res[res.N==13].query("h in [1,4,8,12]").round(3).to_string())
# mutacao: versao que vaza futuro (pares ate t+h) -> quantas escolhas mudam
for k in (1,4):
    mm=[composto(prev,13,h,janela_de_pares_futura=k) for h in (1,4,8,12)]
    mm=pd.concat(mm); j=mm.merge(ex[ex.N==13],on=["h","data_alvo"],suffixes=("_m","_e"))
    print(f"mutacao vaza +{k} sem: escolhas diferentes {(j.folha_escolhida_m!=j.folha_escolhida_e).sum()} de {len(j)}")
meus.drop(columns=["max_data_alvo_usada"]).to_csv("meu_e3_previsoes.csv", index=False)
# distribuicao de origem
print("N=13 janela: primeira/ultima data_alvo", w[w.N==13].data_alvo.min(), w[w.N==13].data_alvo.max())
