"""Recalculo independente das metricas de alarme (E5) e do composto N=13 (E3), sem importar codigo do pacote."""
import json, sys
import numpy as np
import pandas as pd

RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final/resultados/ciencia/"
razao = json.load(open(RAIZ + "E5_alarme/razao.json"))
# L recalculado pela minha verificacao da razao (lido do meu json), nao do executor
mine = json.load(open("razao_por_arquivo_e_ano.json"))
ANOS = {"2018","2019","2020","2021","2022","2023"}
num = sum(v[0] for a in range(2018, 2025) for k, v in mine[str(a)]["por_ano_sintoma"].items() if k in ANOS)
den = sum(v[1] for a in range(2018, 2025) for k, v in mine[str(a)]["por_ano_sintoma"].items() if k in ANOS)
L_MEU = 421 * num / den
print("L meu", L_MEU, "L executor", razao["L"])

d = pd.read_csv(RAIZ + "E2_ablacao/previsoes.csv", float_precision="round_trip")
d["data_alvo"] = pd.to_datetime(d["data_alvo"]); d["data_origem"] = pd.to_datetime(d["data_origem"])
IN, FIM = pd.Timestamp("2024-01-07"), pd.Timestamp("2026-02-01")

# --- composto N=13 refeito do zero (a partir das previsoes de E2, folhas 5 e 20 do completo)
def composto(N=13):
    out = []
    for h in range(1, 13):
        a = d[(d.braco == "completo") & (d.folha == 5) & (d.h == h)].set_index("data_alvo").sort_index()
        b = d[(d.braco == "completo") & (d.folha == 20) & (d.h == h)].set_index("data_alvo").sort_index()
        comum = a.index.intersection(b.index)
        a = a.loc[comum]; b = b.loc[comum]
        ea = (a.real - a.previsto).abs(); eb = (b.real - b.previsto).abs()
        origem = pd.Series(comum - pd.Timedelta(weeks=h), index=comum)
        for dt in comum:
            t = dt - pd.Timedelta(weeks=h)
            hist = comum[comum <= t]
            if len(hist) < N: continue
            ult = hist[-N:]
            ma, mb = ea.loc[ult].mean(), eb.loc[ult].mean()
            fol = 5 if ma <= mb else 20
            out.append((h, t, dt, a.loc[dt, "real"], (a if fol == 5 else b).loc[dt, "previsto"], fol))
    return pd.DataFrame(out, columns=["h", "data_origem", "data_alvo", "real", "previsto", "folha_escolhida"])
comp = composto()
e3 = pd.read_csv(RAIZ + "E3_composto/previsoes.csv", float_precision="round_trip")
e3 = e3[e3.N == 13].copy(); e3["data_alvo"] = pd.to_datetime(e3["data_alvo"])
mm = comp.merge(e3, on=["h", "data_alvo"], suffixes=("", "_e"), how="outer", indicator=True)
print("composto: linhas meu", len(comp), "e3", len(e3), "merge", mm["_merge"].value_counts().to_dict())
both = mm[mm["_merge"] == "both"]
print("max |dif previsto|", (both.previsto - both.previsto_e).abs().max(), "folha dif", int((both.folha_escolhida != both.folha_escolhida_e).sum()))
comp["braco"] = "composto"; comp["folha"] = 0

# --- metricas de alarme
def metricas(g, L, estrito=True):
    ra = g.real > L if estrito else g.real >= L
    pa = g.previsto > L if estrito else g.previsto >= L
    vp = int((ra & pa).sum()); fn = int((ra & ~pa).sum()); fp = int((~ra & pa).sum()); vn = int((~ra & ~pa).sum())
    return dict(n=len(g), surtos=int(ra.sum()), VP=vp, FN=fn, FP=fp, VN=vn,
                sens=vp / (vp + fn) if vp + fn else np.nan, prec=vp / (vp + fp) if vp + fp else np.nan)

alvo = {}
for h in (1, 4, 8):
    g = d[(d.braco == "completo") & (d.folha == 5) & (d.h == h) & (d.data_alvo >= IN) & (d.data_alvo <= FIM)]
    alvo[h] = set(g.data_alvo)
    print("h", h, "semanas alvo completo f5:", len(g), "f20:", len(d[(d.braco=="completo")&(d.folha==20)&(d.h==h)&(d.data_alvo>=IN)&(d.data_alvo<=FIM)]))
todos = pd.concat([d[["braco","folha","h","data_alvo","real","previsto"]], comp[["braco","folha","h","data_alvo","real","previsto"]]])
linhas = []
for (br, fo), gg in todos.groupby(["braco", "folha"]):
    for h in (1, 4, 8):
        g = gg[(gg.h == h) & (gg.data_alvo.isin(alvo[h]))]
        for rot, L in (("conv", L_MEU), ("421", 421.0)):
            for est in (True, False):
                m = metricas(g, L, est)
                linhas.append(dict(braco=br, folha=fo, h=h, versao=rot, estrito=est, **m))
R = pd.DataFrame(linhas)
R["falsos_ano_196"] = R.FP / 1.96
R["falsos_ano_calc"] = R.FP / (102 / (365.25 / 7))
R.to_csv("alarme_recalculado.csv", index=False)

# --- comparacao com o executor
def comparar(arq, rot):
    ex = pd.read_csv(RAIZ + "E5_alarme/" + arq, float_precision="round_trip")
    print("\n==", arq, "linhas executor", len(ex))
    mym = R[(R.versao == rot) & (R.estrito)].copy()
    mym["folha"] = mym["folha"].astype(int)
    ex["folha"] = ex["folha"].replace("composto", "0").astype(int)
    ex["braco"] = ex["braco"].replace("composto_N13", "composto")
    print("bracos executor:", sorted(ex.braco.unique()), "folhas", sorted(ex.folha.unique()))
    m = ex.merge(mym, on=["braco", "folha", "h"], how="outer", suffixes=("_e", "_m"), indicator=True)
    print(m["_merge"].value_counts().to_dict())
    b = m[m["_merge"] == "both"]
    for c in ["VP", "FN", "FP", "VN", "n_e"]:
        pass
    bad = b[(b.VP_e != b.VP_m) | (b.FN_e != b.FN_m) | (b.FP_e != b.FP_m) | (b.VN_e != b.VN_m) | (b.n_e != b.n_m)]
    print("linhas com contagens diferentes:", len(bad))
    if len(bad): print(bad[["braco","folha","h","VP_e","VP_m","FN_e","FN_m","FP_e","FP_m"]])
    print("max dif sens", (b.sensibilidade - b.sens).abs().max(), "prec", (b.precisao - b.prec).abs().max(),
          "falsos/ano vs 1,96", (b.falsos_por_ano - b.falsos_ano_196).abs().max(),
          "vs calculado", (b.falsos_por_ano - b.falsos_ano_calc).abs().max())
    print("surtos dif", int((b.semanas_de_surto != b.surtos).sum()))
    print("limiar executor", ex.limiar.unique())
comparar("alarme.csv", "conv")
comparar("alarme_421_sem_conversao.csv", "421")

# diferenca > vs >=
est = R[(R.versao == "conv")].pivot_table(index=["braco","folha","h"], columns="estrito", values=["VP","FP","FN"])
dif = est[(est[("VP", True)] != est[("VP", False)]) | (est[("FP", True)] != est[("FP", False)]) | (est[("FN", True)] != est[("FN", False)])]
print("\nlinhas em que > e >= diferem (L convertido):", len(dif)); print(dif.to_string() if len(dif) else "")
for h in (1,4,8):
    print(R[(R.versao=="conv")&(R.estrito)&(R.h==h)&(R.braco.isin(["completo","composto"]))][["braco","folha","h","n","surtos","VP","FN","FP","sens","prec","falsos_ano_196","falsos_ano_calc"]].round(4).to_string(index=False))
