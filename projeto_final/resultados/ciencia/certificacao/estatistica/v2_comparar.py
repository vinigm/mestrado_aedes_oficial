import sys, numpy as np, pandas as pd
arq = sys.argv[1] if len(sys.argv)>1 else "minhas_familias.csv"
ex = pd.read_csv("../../estatistica/familias.csv", float_precision="round_trip")
me = pd.read_csv(arq, float_precision="round_trip")
print(ex[["familia","A","B"]].drop_duplicates().to_string())
print("mesmo numero de linhas", len(ex), len(me))
ex["k"]=ex.groupby("familia").cumcount(); me["k"]=me.groupby("familia").cumcount()
# garantir mesma ordem logica: ordenar ambos por (familia, h, linhas na ordem de definicao)
m = ex.merge(me, on=["familia","h","k"], suffixes=("_e","_m"))
print("linhas casadas", len(m), "| h iguais e ordem:", (m.k>=0).all())
# conferir se A/B correspondem
print(m[["familia","h","A_e","A_m","B_e","B_m"]].drop_duplicates(["familia","A_e","A_m","B_e","B_m"]).to_string())
num = ["n","mae_A","mae_B","delta","ganho_pct","dm_hln","p_bruto","p_holm","limiar_piso"]
for c in num:
    print(f"{c:12s} max|dif| = {(m[c+'_e']-m[c+'_m']).abs().max():.3e}")
for c in ["ic_inf","ic_sup"]:
    print(f"{c:12s} max|dif| = {(m[c+'_e']-m[c+'_m']).abs().max():.3e}")
print("fallback diferente:", (m.variancia_fallback_e!=m.variancia_fallback_m).sum())
print("veredito diferente:", (m.veredito_e!=m.veredito_m).sum())
print(m[m.veredito_e!=m.veredito_m][["familia","h","A_e","veredito_e","veredito_m"]])
