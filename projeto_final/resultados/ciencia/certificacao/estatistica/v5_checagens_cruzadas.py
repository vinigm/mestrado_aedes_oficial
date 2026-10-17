import sys; sys.path.insert(0,".")
import numpy as np, pandas as pd, math
from scipy import stats
from reimpl import *
prev=carregar_parciais()
# (a) h=1: DM-HLN == teste t de 1 amostra sobre d (identidade algebrica)
mx=0
for A,B in [(("completo",5),("sem_casos",5)),(("so_casos",5),("so_calendario",5)),(("completo",20),("sem_vetor",20))]:
    a=janela(serie(prev,*A,1)); b=janela(serie(prev,*B,1)); c=a.index.intersection(b.index)
    d=(b.loc[c,"real"]-b.loc[c,"previsto"]).abs().to_numpy()-(a.loc[c,"real"]-a.loc[c,"previsto"]).abs().to_numpy()
    t=stats.ttest_1samp(d,0.0)
    mine=dm_hln(d,1)
    mx=max(mx,abs(t.pvalue-mine["p"]),abs(t.statistic-mine["dm_hln"]))
print("h=1: |p_t_amostra_unica - p_DM_HLN| max =",mx)
# (b) autocovariancias por caminho alternativo (np.correlate) para h=4,12 em series reais
def dm_alt(d,h):
    n=len(d); x=d-d.mean()
    full=np.correlate(x,x,mode="full")[n-1:]/n   # gamma_k, k=0..n-1
    V=(full[0]+2*full[1:h].sum())/n
    return d.mean()/math.sqrt(V)*math.sqrt((n+1-2*h+h*(h-1)/n)/n), 2*stats.t.sf(abs(d.mean()/math.sqrt(V)*math.sqrt((n+1-2*h+h*(h-1)/n)/n)),n-1)
mx=0
for h in (4,8,12):
    for A,B in [(("completo",5),("sem_clima",5)),(("so_vetor",5),("so_calendario",5)),(("completo",20),("sem_casos",20))]:
        a=janela(serie(prev,*A,h)); b=janela(serie(prev,*B,h)); c=a.index.intersection(b.index)
        d=(b.loc[c,"real"]-b.loc[c,"previsto"]).abs().to_numpy()-(a.loc[c,"real"]-a.loc[c,"previsto"]).abs().to_numpy()
        r=dm_hln(d,h); s,p=dm_alt(d,h)
        mx=max(mx,abs(r["dm_hln"]-s),abs(r["p"]-p))
print("h=4,8,12 reais: |dif| max entre meu DM (loop) e DM por np.correlate =",mx)
# (c) buracos de calendario na serie pareada (a dependencia serial trata semanas nao adjacentes como adjacentes)
for h in (1,12):
    a=janela(serie(prev,"completo",5,h)); dd=np.diff(a.index.values).astype("timedelta64[D]").astype(int)
    print(f"h={h}: n={len(a)} ; saltos de calendario >7 dias:", int((dd>7).sum()), "tamanhos(dias):", sorted(set(dd[dd>7].tolist())))
# (d) conferencia: previsto do composto bate com a folha escolhida nos parciais, e nenhuma linha usa pares futuros (ja em v1)
comp=pd.read_csv("meu_e3_previsoes.csv",parse_dates=["data_origem","data_alvo"],float_precision="round_trip")
bad=0
for (h,f),g in comp[comp.N==13].groupby(["h","folha_escolhida"]):
    s=serie(prev,"completo",int(f),int(h)).loc[g.data_alvo]
    bad+=int((s["previsto"].to_numpy()!=g["previsto"].to_numpy()).sum())
print("N=13: linhas em que previsto != previsao da folha escolhida:",bad)
