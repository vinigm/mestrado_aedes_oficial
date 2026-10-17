import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from reimpl import *
variante = sys.argv[1] if len(sys.argv)>1 else "matriz"
seed = int(sys.argv[2]) if len(sys.argv)>2 else 42
saida = sys.argv[3] if len(sys.argv)>3 else "minhas_familias.csv"
prev = carregar_parciais()
casos = regua_sazonal()
piso = pd.read_csv(PISO).set_index(["folha","h"])["piso_de_ruido"]
comp = pd.read_csv("meu_e3_previsoes.csv", parse_dates=["data_origem","data_alvo"], float_precision="round_trip")
comp13 = comp[comp.N==13]

def obter(spec, h):
    if spec == "composto":
        s = comp13[comp13.h==h].set_index("data_alvo").sort_index()[["data_origem","real","previsto"]]
    elif spec == "regua":
        g = serie(prev,"completo",5,h)
        g = janela(g)
        yhat = casos.reindex(g.index - pd.Timedelta(weeks=52)).to_numpy()
        real = casos.reindex(g.index).to_numpy()
        assert np.array_equal(real, g["real"].to_numpy()), "real da regua != real E2"
        s = pd.DataFrame({"real":real,"previsto":yhat}, index=g.index)
        s = s[s.previsto.notna()]
    else:
        s = serie(prev, spec[0], spec[1], h)
    return janela(s)

def piso_de(A,B,h):
    pisos=[]
    for sp in (A,B):
        if sp=="regua": continue
        if sp=="composto": pisos += [piso[(5,h)], piso[(20,h)]]
        else: pisos.append(piso[(sp[1],h)])
    # regra: comparacoes de folha 5 -> piso f5; f20 -> f20; composto -> maior dos dois. Folhas A e B sempre iguais nas familias F1-F3.
    return 2*max(pisos)

def rotulo(sp):
    if sp=="composto": return "composto13"
    if sp=="regua": return "regua_sazonal"
    return f"{sp[0]}@f{sp[1]}"

linhas=[]
for fam,h,A,B in definir_familias():
    r = comparar(obter(A,h), obter(B,h), h, seed=seed, variante=variante)
    r.update(familia=fam,h=h,A=rotulo(A),B=rotulo(B),limiar_piso=piso_de(A,B,h))
    linhas.append(r)
df = pd.DataFrame(linhas)
df["p_holm"]=np.nan
for fam in df.familia.unique():
    m=df.familia==fam
    df.loc[m,"p_holm"]=holm(df.loc[m,"p_bruto"].to_numpy())
df["veredito"]=[veredito(p,d,l) for p,d,l in zip(df.p_holm,df.delta,df.limiar_piso)]
df["veredito_sem_piso"]=[veredito(p,d,0.0) for p,d in zip(df.p_holm,df.delta)]
df=df[["familia","h","A","B","n","mae_A","mae_B","delta","ganho_pct","ic_inf","ic_sup","dm_hln","p_bruto","p_holm","limiar_piso","variancia_fallback","veredito","veredito_sem_piso"]]
df.to_csv(saida,index=False)
print(df.groupby("familia").size().to_dict())
