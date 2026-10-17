import pandas as pd, numpy as np
def ler(a):
    d=pd.read_csv(a,float_precision="round_trip")
    d["A"]=d.A.str.replace("composto_N13","composto13"); d["B"]=d.B.str.replace("composto_N13","composto13")
    return d.set_index(["familia","h","A","B"]).sort_index()
ex=ler("../../estatistica/familias.csv")
def cmp(a):
    m=ler(a); return max((ex.ic_inf-m.ic_inf).abs().max(),(ex.ic_sup-m.ic_sup).abs().max())
print("variante matriz size=(B,nb) sem 42 (a do executor): max dif IC =", cmp("minhas_familias.csv"))
print("variante por_rep (size=nb por reamostra) sem 42: max dif IC =", cmp("fam_porrep.csv"), "(ambiguidade de ordem dos sorteios)")
print("variante escalar (1 sorteio por bloco) sem 42: max dif IC =", cmp("fam_escalar.csv"))
dfs={s:ler(f"fam_seed{s}.csv") for s in (1,7,123)}; dfs[42]=ler("minhas_familias.csv")
for s,d in dfs.items():
    print(f"semente {s}: p_bruto/p_holm/delta identicos ao executor: {np.allclose(d.p_holm,ex.p_holm,atol=1e-12) and np.allclose(d.p_bruto,ex.p_bruto,atol=1e-12) and np.allclose(d.delta,ex.delta,atol=1e-9)} | vereditos identicos: {(d.veredito==ex.veredito).all()}")
al=pd.concat([d[["ic_inf","ic_sup"]].assign(s=s) for s,d in dfs.items()]).reset_index()
g=al.groupby(["familia","h","A","B"]).agg(i0=("ic_inf","min"),i1=("ic_inf","max"),s0=("ic_sup","min"),s1=("ic_sup","max"))
ai=(g.i1-g.i0); asu=(g.s1-g.s0)
print("Variacao de Monte Carlo (sementes 42,1,7,123), amplitude entre sementes em pontos de ganho_pct: limite inferior mediana=%.2f max=%.2f | limite superior mediana=%.2f max=%.2f"%(ai.median(),ai.max(),asu.median(),asu.max()))
print("amplitude maxima por teste (top 5):"); print(pd.concat([ai.rename("inf"),asu.rename("sup")],axis=1).sort_values("inf",ascending=False).head(5).round(2).to_string())
tab=pd.DataFrame({s:((d.ic_inf>0)|(d.ic_sup<0)) for s,d in dfs.items()})
mud=tab[tab.nunique(axis=1)>1]
print("testes cujo 'IC exclui zero' muda entre sementes:", len(mud))
print(pd.concat([mud.astype(int), ex.loc[mud.index,["ic_inf","ic_sup"]].round(2)],axis=1).to_string())
g.assign(amp_inf=ai,amp_sup=asu).round(3).to_csv("variacao_monte_carlo_ic.csv")
