import glob, numpy as np, pandas as pd
from scipy import stats
RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
R = f"{RAIZ}/projeto_final/resultados/reproducao_selecao/E6c_grade18"
O = f"{RAIZ}/analises/2026-09-23_bateria_noturna/bloco_6_hiperparametros/saidas"
old = pd.read_csv(f"{O}/previsoes_por_configuracao.csv", parse_dates=["data_alvo"], float_precision="round_trip")
f1 = pd.read_csv(f"{R}/previsoes_fase1.csv", parse_dates=["data_origem","data_alvo"], float_precision="round_trip")
f2 = pd.concat([pd.read_csv(p, parse_dates=["data_origem","data_alvo"], float_precision="round_trip") for p in sorted(glob.glob(f"{R}/parciais_fase2/*.csv"))])
print("old", len(old), old.braco.nunique(), "f1", len(f1), f1.configuracao.nunique(), "f2", len(f2), f2.configuracao.nunique())
# fase 1 x antigo
o1 = old.rename(columns={"braco":"configuracao"})
m = f1.merge(o1, on=["configuracao","h","data_alvo"], how="outer", indicator=True, suffixes=("_n","_o"))
print("merge fase1:", m[m.data_alvo<=pd.Timestamp("2023-12-31")]["_merge"].value_counts().to_dict(), "(right_only fora da calibracao:", int(((m._merge=='right_only')&(m.data_alvo>pd.Timestamp('2023-12-31'))).sum()),")")
b = m[m._merge=="both"]
print("fase1 dif max previsto:", (b.previsto_n-b.previsto_o).abs().max(), " real:", (b.real_n-b.real_o).abs().max())
# fase 2 x antigo (todas as origens)
m2 = f2.merge(o1, on=["configuracao","h","data_alvo"], how="outer", indicator=True, suffixes=("_n","_o"))
m2 = m2[m2.configuracao.isin(f2.configuracao.unique())]
print("merge fase2:", m2._merge.value_counts().to_dict(), " dif max:", (m2.previsto_n-m2.previsto_o).abs().max())
# ranking do zero, a partir do CSV antigo (calibracao: data_alvo < 2024-01-01; media dos 4 MAE por h)
def mae_cal(df, col):
    d = df[df.data_alvo < pd.Timestamp("2024-01-01")].copy()
    d["ae"] = (d[col]-d["real"]).abs()
    return d.groupby(["configuracao","h"])["ae"].mean().groupby("configuracao").mean()
ro = mae_cal(o1, "previsto"); rn = mae_cal(f1, "previsto")
ex = pd.read_csv(f"{R}/ranking.csv").set_index("configuracao")["mae_calibracao"]
print("ranking: dif max old-vs-meu(f1):", (ro.reindex(rn.index)-rn).abs().max(), " vs executor:", (rn-ex.reindex(rn.index)).abs().max())
rk = rn.sort_values(kind="mergesort")
print(rk.head(5).round(3).to_dict()); print("posicao da referencia:", list(rk.index).index("lr0.05_it250_folhas15_min5")+1)
mn20 = rk[rk.index.str.endswith("min20")]; print("min20: posicoes", [list(rk.index).index(i)+1 for i in mn20.index][:1], "..", mn20.min().round(2), mn20.max().round(2), len(mn20))
print("ordem dos 18 por MAE (meu) == executor (exceto empates):", [ (a==b) for a,b in zip(rk.index, ex.index)].count(False), "diferencas de posicao")
ties = rk[rk.duplicated(keep=False)]; print("empates exatos:", ties.round(6).to_dict())
# fase 2 do zero
def holm(ps):
    o = np.argsort(ps); k = len(ps); adj = np.empty(k); mx = 0.0
    for r, i in enumerate(o):
        mx = max(mx, min(1.0, ps[i]*(k-r))); adj[i] = mx
    return adj
def wilcoxon_manual(a, b):
    d = a-b; d = d[d != 0]; n = len(d)
    r = stats.rankdata(np.abs(d)); w = min(r[d>0].sum(), r[d<0].sum())
    mu = n*(n+1)/4
    _, cnt = np.unique(np.abs(d), return_counts=True)
    var = n*(n+1)*(2*n+1)/24 - (cnt**3-cnt).sum()/48
    z = (w-mu)/np.sqrt(var)
    return 2*stats.norm.cdf(z)  # w=min -> z<=0
win, ref = "lr0.03_it400_folhas15_min5", "lr0.05_it250_folhas15_min5"
ev = o1[o1.data_alvo >= pd.Timestamp("2024-01-01")]
rows = []
for h in (1,4,8,12):
    pr = ev[(ev.configuracao==ref)&(ev.h==h)].set_index("data_alvo"); pw = ev[(ev.configuracao==win)&(ev.h==h)].set_index("data_alvo")
    idx = pr.index.intersection(pw.index)
    er = (pr.loc[idx,"real"]-pr.loc[idx,"previsto"]).abs().to_numpy(); ew = (pw.loc[idx,"real"]-pw.loc[idx,"previsto"]).abs().to_numpy()
    p_sc = stats.wilcoxon(er, ew).pvalue; p_m = wilcoxon_manual(er, ew)
    rows.append(dict(h=h, n=len(idx), mae_ref=er.mean(), mae_win=ew.mean(), red_pct=(1-ew.mean()/er.mean())*100, p_scipy=p_sc, p_manual=p_m))
t = pd.DataFrame(rows); t["p_holm"] = holm(t.p_scipy.to_numpy()); t["p_holm_manual"] = holm(t.p_manual.to_numpy())
print(t.to_string())
# vs executor (fase2.csv) e vs antigo (comparacoes.csv)
e2 = pd.read_csv(f"{R}/fase2.csv"); oc = pd.read_csv(f"{O}/comparacoes.csv")
print("dif vs executor p_bruto:", (t.p_scipy.to_numpy()-e2.p_bruto.to_numpy()).__abs__().max(), " p_holm:", (t.p_holm.to_numpy()-e2.p_holm.to_numpy()).__abs__().max(), " reducao:", (t.red_pct.to_numpy()-e2.reducao_percentual.to_numpy()).__abs__().max())
print("dif vs antigo p_bruto:", (t.p_scipy.to_numpy()-oc.p_bruto.to_numpy()).__abs__().max(), " mae_win:", (t.mae_win.to_numpy()-oc.mae_variante.to_numpy()).__abs__().max())
# a regra de troca
print("troca? (reduz h8 e h12 com Holm<0,05):", bool(((t.red_pct>0)&(t.p_holm<0.05))[t.h.isin([8,12])].all()))
t.to_csv("cert_e6c_fase2_recalculada.csv", index=False); rk.to_csv("cert_e6c_ranking_recalculado.csv", header=["mae_cal"])
