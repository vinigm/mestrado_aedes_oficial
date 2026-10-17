import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd
from reimpl import dm_hln, holm
# --- piso ignorado
d=pd.read_csv("minhas_familias.csv",float_precision="round_trip")
print("=== VEREDITOS COM x SEM piso (descritivo)")
print("com piso :", d.veredito.value_counts().to_dict())
print("sem piso :", d.veredito_sem_piso.value_counts().to_dict())
mud=d[d.veredito!=d.veredito_sem_piso]
print("vereditos que mudam se o piso for ignorado:", len(mud))
if len(mud): print(mud[["familia","h","A","B","delta","limiar_piso","p_holm","veredito","veredito_sem_piso"]].round(4).to_string())
print("\n=== p_Holm<0.05 (qualquer direcao)"); print(d[d.p_holm<0.05][["familia","h","A","B","delta","limiar_piso","p_holm","veredito"]].round(4).to_string())
print("\n=== quase-passagens: p_holm entre 0.05 e 0.10 ou |delta| perto do limiar (0.5x-2x) com p_holm<0.05")
print(d[(d.p_holm>=0.05)&(d.p_holm<0.10)][["familia","h","A","B","delta","p_bruto","p_holm"]].round(4).to_string())
# --- holm contra statsmodels, se existir
try:
    from statsmodels.stats.multitest import multipletests
    mx=0
    for f in d.familia.unique():
        p=d[d.familia==f].p_bruto.to_numpy(); mx=max(mx,np.abs(multipletests(p,method="holm")[1]-holm(p)).max())
    print("\nHolm minha vs statsmodels max dif:", mx)
except Exception as e:
    print("\nstatsmodels indisponivel:", e)
    p=np.array([0.01,0.04,0.03,0.005]); print("Holm exemplo manual [0.01,0.04,0.03,0.005] ->", holm(p), "esperado [0.03,0.06,0.06,0.02]")
# --- simulacao DM-HLN
rng=np.random.default_rng(20261012)
def sim(h,n=102,R=20000,kind="iid",shift=0.0):
    rej=0; fb=0; nan=0
    for _ in range(R):
        if kind=="iid":
            x=rng.standard_normal(n)
        else:  # MA(h-1) com pesos iguais: estrutura de erro de previsao h passos a frente
            e=rng.standard_normal(n+h-1); x=np.convolve(e,np.ones(h)/np.sqrt(h),mode="valid")
        r=dm_hln(x+shift,h)
        fb+=r["fallback"]; rej+= (r["p"]<0.05) and not np.isnan(r["dm_hln"])
    return rej/R, fb/R
print("\n=== DM-HLN sob H0 (n=102, 20000 simulacoes, nivel nominal 5%)")
for kind in ("iid","ma"):
    for h in (1,4,8,12):
        taxa,fb=sim(h,kind=kind)
        print(f"d {kind:3s} h={h:2d}: rejeicao={taxa*100:5.2f}%  (erro-padrao MC ~0.15 pp)  fallback_Bartlett={fb*100:.2f}%")
print("\nPoder: iid normal com media 0.4 sd, n=102:")
for h in (4,12): print(f" h={h}: ", sim(h,R=5000,shift=0.4)[0])
