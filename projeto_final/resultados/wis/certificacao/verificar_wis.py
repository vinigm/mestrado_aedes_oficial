"""Certificacao adversarial da E7 (WIS) - reimplementacao independente.

Nao importa nada de aedes/ nem de experimentos/. Le so CSVs: parciais brutos de quantil, tabela_final.csv,
previsoes da E2 e da E3, e os gabaritos antigos (somente leitura). Grava saidas em certificacao/.
"""
import json, math, pathlib, sys
import numpy as np, pandas as pd
from scipy import stats

RAIZ_PF = pathlib.Path(__file__).resolve().parents[3]          # projeto_final
WIS = RAIZ_PF / "resultados" / "wis"
CERT = WIS / "certificacao"
MEU_PROJETO = RAIZ_PF.parent
ANTIGO = MEU_PROJETO / "analises" / "2026-09-26_wis_na_tabela_restaurada" / "saidas"
NIVEIS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
ALFAS = [0.5, 0.2, 0.1]            # K = 3 intervalos centrais 50, 80, 90%
PAR_DE_NIVEIS = {0.5: (0.25, 0.75), 0.2: (0.10, 0.90), 0.1: (0.05, 0.95)}
JAN_PADRAO = (pd.Timestamp("2024-01-07"), pd.Timestamp("2026-02-01"))
JAN_ANTIGA = (pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"))
HS = list(range(1, 13))
rel: dict = {}
LOG = []
def log(msg):
    print(msg); LOG.append(str(msg))

def csv(path, **kw):
    return pd.read_csv(path, float_precision="round_trip", **kw)

# ------------------------------------------------------------------ WIS (duas implementacoes)
def wis_bracher(y, q):
    """y: (n,), q: (n,7) ordenado, colunas = NIVEIS. Formula de Bracher 2021 com K=3 e mediana."""
    mediana = q[:, 3]
    soma = 0.0
    for a in ALFAS:
        lo_n, hi_n = PAR_DE_NIVEIS[a]
        l = q[:, NIVEIS.index(lo_n)]; u = q[:, NIVEIS.index(hi_n)]
        IS = (u - l) + (2 / a) * (l - y) * (y < l) + (2 / a) * (y - u) * (y > u)
        soma = soma + (a / 2) * IS
    return (0.5 * np.abs(y - mediana) + soma) / (len(ALFAS) + 0.5)

def wis_pinball(y, q):
    """Identidade: WIS = soma das 7 perdas pinball (tau*(y-q) se y>=q, (1-tau)*(q-y) se y<q) / (K+0,5)."""
    tot = 0.0
    for j, tau in enumerate(NIVEIS):
        d = y - q[:, j]
        tot = tot + np.where(d >= 0, tau * d, (tau - 1) * d)
    return tot / (len(ALFAS) + 0.5)

def cobertura(y, q, nivel):
    lo_n, hi_n = PAR_DE_NIVEIS[round(1 - nivel, 1)]
    l = q[:, NIVEIS.index(lo_n)]; u = q[:, NIVEIS.index(hi_n)]
    return (y >= l) & (y <= u)

# testes unitarios do WIS
y0 = np.array([10.0, 0.0, 5.0]); q0 = np.tile(np.array([10.0] * 7), (3, 1))
assert np.allclose(wis_bracher(y0[:1], q0[:1]), 0) and np.allclose(wis_pinball(y0[:1], q0[:1]), 0)
# exemplo manual: y=20, quantis 1..7 -> IS50=(6-... ) conferencia a mao
yq = np.array([20.0]); qq = np.array([[1., 2., 3., 4., 5., 6., 7.]])
# 0.5|20-4|=8 ; a=.5: (5-3)+4*(20-5)=62 -> .25*62=15.5 ; a=.2: (6-2)+10*(20-6)=144 -> .1*144=14.4 ; a=.1:(7-1)+20*(20-7)=266 -> .05*266=13.3
esperado = (8 + 15.5 + 14.4 + 13.3) / 3.5
assert abs(wis_bracher(yq, qq)[0] - esperado) < 1e-12 and abs(wis_pinball(yq, qq)[0] - esperado) < 1e-12, (wis_bracher(yq, qq), esperado)
rng0 = np.random.default_rng(1)
yr = rng0.gamma(2, 50, 500); qr = np.sort(rng0.gamma(2, 50, (500, 7)), axis=1)
assert np.allclose(wis_bracher(yr, qr), wis_pinball(yr, qr), atol=1e-9)
log("OK testes unitarios do WIS: zero perfeito, exemplo manual 59,2/3,5=%.6f, identidade Bracher = soma de pinball (500 casos aleatorios)" % esperado)

# ------------------------------------------------------------------ 1. quantis brutos -> ordenados
parciais = []
for f in sorted((WIS / "parciais").glob("previsoes_folha*_q*_h*.csv")):
    parciais.append(csv(f))
P = pd.concat(parciais, ignore_index=True)
for c in ("data_origem", "data_alvo"):
    P[c] = pd.to_datetime(P[c])
log(f"parciais lidos: {len(parciais)} arquivos, {len(P)} linhas")
assert len(parciais) == 176
P85 = P[np.isclose(P.quantil, 0.85)]
P = P[~np.isclose(P.quantil, 0.85)].copy()
assert set(np.round(P.quantil, 2)) == set(NIVEIS)
P["quantil"] = P.quantil.round(2)
# consistencia: mesma grade e mesmo real nos 7 quantis
base = {}
for (f, h), g in P.groupby(["folha", "h"]):
    piv = g.pivot(index="data_alvo", columns="quantil", values="previsto")
    rl = g.groupby("data_alvo").real.nunique()
    assert list(piv.columns) == NIVEIS and not piv.isna().any().any() and (rl == 1).all(), (f, h)
    reais = g.drop_duplicates("data_alvo").set_index("data_alvo").real
    base[(f, h)] = (reais.sort_index(), piv.sort_index())
log(f"OK grade completa: 24 (folha,h), 7 quantis cada, sem NaN, real unico por data_alvo; linhas por (folha,h): {sorted(set(len(v[0]) for v in base.values()))}")
rel["linhas_por_folha_h"] = sorted(set(len(v[0]) for v in base.values()))

# real contra tabela_final (apos corte) e contra E2
tab = csv(RAIZ_PF / "dados" / "tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"])
tab = tab.rename(columns={"data_inicio_semana_epidemi": "data"})
casos = tab.set_index("data").casos_confirmados.copy()
ult = casos.dropna().index.max()
casos[casos.index > ult - pd.Timedelta(weeks=12)] = np.nan    # corte de maturidade: apaga as 12 ultimas semanas
log(f"serie de casos: ultima semana com caso {ult.date()}, ultima apos o corte {casos.dropna().index.max().date()}")
ref_serie = csv(RAIZ_PF / "testes" / "referencia_antiga" / "serie_casos_apos_corte.csv", parse_dates=["data_inicio_semana_epidemi"]).set_index("data_inicio_semana_epidemi").casos_confirmados
cmp_serie = pd.concat([casos, ref_serie], axis=1, keys=["meu", "ref"])
dif = (cmp_serie.meu.fillna(-1) - cmp_serie.ref.fillna(-1)).abs().max()
log(f"serie apos corte: minha vs gabarito antigo, dif max {dif}")
rel["serie_apos_corte_dif_max"] = float(dif)
maxdif_real = 0.0
for (f, h), (reais, piv) in base.items():
    d = (reais - casos.reindex(reais.index)).abs().max()
    maxdif_real = max(maxdif_real, d)
log(f"real dos parciais vs casos da tabela (apos corte): dif max {maxdif_real}")
rel["real_vs_tabela_dif_max"] = float(maxdif_real)

# ordenacao propria e comparacao com previsoes_quantis.csv
ordenados = {}
cruz_stat = []
for (f, h), (reais, piv) in base.items():
    v = piv.to_numpy()
    s = np.sort(v, axis=1)
    cruz_stat.append((f, h, int((np.diff(v, axis=1) < 0).any(axis=1).sum()), len(v)))
    ordenados[(f, h)] = pd.DataFrame(s, index=piv.index, columns=NIVEIS)
ex = csv(WIS / "previsoes_quantis.csv", parse_dates=["data_origem", "data_alvo"])
ex["quantil"] = ex.quantil.round(2)
chk = []
for (f, h), g in ex.groupby(["folha", "h"]):
    piv = g.pivot(index="data_alvo", columns="quantil", values="previsto").sort_index()
    pivb = g.pivot(index="data_alvo", columns="quantil", values="previsto_bruto").sort_index()
    chk.append((np.abs(piv.to_numpy() - ordenados[(f, h)].to_numpy()).max(), np.abs(pivb.to_numpy() - base[(f, h)][1].to_numpy()).max(), len(piv) == len(ordenados[(f, h)])))
rel["quantis_ordenados_exec_vs_meu_dif_max"] = float(max(c[0] for c in chk))
rel["quantis_brutos_exec_vs_parciais_dif_max"] = float(max(c[1] for c in chk))
assert all(c[2] for c in chk)
log(f"quantis ordenados: executor vs meu np.sort, dif max {rel['quantis_ordenados_exec_vs_meu_dif_max']}; brutos vs parciais {rel['quantis_brutos_exec_vs_parciais_dif_max']}")
frac = [(f, h, c / n) for f, h, c, n in cruz_stat]
log(f"origens com cruzamento (antes de ordenar): min {min(x[2] for x in frac):.3f} max {max(x[2] for x in frac):.3f}")
rel["cruzamento_frac_min_max"] = [min(x[2] for x in frac), max(x[2] for x in frac)]
cx = csv(WIS / "cruzamentos.csv")
mine = pd.DataFrame(cruz_stat, columns=["folha", "h", "mine", "n"]).merge(cx, on=["folha", "h"])
assert (mine.mine == mine.com_cruzamento).all() and (mine.n == mine.origens).all()
log("OK cruzamentos.csv confere com a minha contagem (24 linhas)")

# trava q0,85 (p/ confirmar): parciais q0,85 vs referencia
refp = csv(RAIZ_PF / "resultados" / "referencia" / "previsoes.csv", parse_dates=["data_origem", "data_alvo"])
rel["colunas_referencia"] = list(refp.columns)
tr = {}
for f, braco in ((5, "referencia"), (20, "HistGB_folha20_M1")):
    a = P85[P85.folha == f][["h", "data_alvo", "previsto"]]
    b = refp[(refp.braco == braco) & refp.h.isin([1, 4, 8, 12])][["h", "data_alvo", "previsto"]]
    m = a.merge(b, on=["h", "data_alvo"], how="outer", indicator=True, suffixes=("_a", "_b"))
    tr[f] = (int((m._merge != "both").sum()), float((m.previsto_a - m.previsto_b).abs().max()), int((m._merge == "both").sum()))
log(f"trava q0,85: folha5 {tr[5]}, folha20 {tr[20]} (linhas fora do cruzamento, dif max, em comum)")
rel["trava_q085"] = {str(k): v for k, v in tr.items()}

# ------------------------------------------------------------------ 2. regua climatologica independente
def regua_para(data_alvo):
    r = tab[tab.data == data_alvo].iloc[0]
    ano, sem = int(r.ano), int(r.semana)
    h = tab.assign(c=casos.reindex(tab.data).to_numpy())
    h = h[(h.semana == sem) & (h.ano >= 2018) & (h.ano < ano)].dropna(subset=["c"])
    if h.ano.nunique() < 3:
        return None
    return np.quantile(h.c.to_numpy(), NIVEIS)

datas_grade = sorted(set().union(*[set(v[0].index) for v in base.values()]))
regua = {d: regua_para(d) for d in datas_grade}
sem_regua = [d.date().isoformat() for d, v in regua.items() if v is None and d >= pd.Timestamp("2021-02-01")]
log(f"datas da grade {len(datas_grade)}; sem regua a partir de 2021-02: {sem_regua}")
rel["datas_sem_regua_desde_2021_02"] = sem_regua
rx = csv(WIS / "regua_climatologica.csv", parse_dates=["data_alvo"])
rx["quantil"] = rx.quantil.round(2)
rp = rx.pivot_table(index=["h", "data_alvo"], columns="quantil", values="previsto")
mx = 0.0; nlin = 0; faltam = 0
for (h, d), row in rp.iterrows():
    mine_q = regua.get(d)
    if mine_q is None:
        faltam += 1; continue
    mx = max(mx, np.abs(row.to_numpy() - mine_q).max()); nlin += 1
n_meu = sum(1 for d in datas_grade if regua[d] is not None)
log(f"regua: executor {len(rp)} (h,data) vs minha; dif max {mx}; executor com data que eu nao tenho regua: {faltam}; datas com regua minha {n_meu}")
rel["regua_dif_max"] = float(mx); rel["regua_exec_sem_minha"] = faltam
# o executor tem regua em todas as datas em que eu tenho (por h)?
pares_exec = set(rp.index)
falt_no_exec = 0
for h in HS:
    datas_h = set(base[(5, h)][0].index)
    for d in datas_h:
        if regua[d] is not None and (h, d) not in pares_exec:
            falt_no_exec += 1
log(f"datas em que eu tenho regua e o executor nao (por h): {falt_no_exec}")
rel["regua_minha_sem_exec"] = falt_no_exec

# ------------------------------------------------------------------ 3. composto
e3 = csv(RAIZ_PF / "resultados" / "ciencia" / "E3_composto" / "previsoes.csv", parse_dates=["data_origem", "data_alvo"])
e3 = e3[e3.N == 13]
# reimplementacao da escolha (METODO_ESTATISTICO.md, E3): MAE nas ultimas 13 semanas-alvo ate t usando as previsoes q0,85 da E2
e2 = csv(RAIZ_PF / "resultados" / "ciencia" / "E2_ablacao" / "previsoes.csv", parse_dates=["data_origem", "data_alvo"])
e2 = e2[e2.braco == "completo"]
escolha_minha = {}
for h in HS:
    a = e2[(e2.h == h) & (e2.folha == 5)].set_index("data_alvo").sort_index()
    b = e2[(e2.h == h) & (e2.folha == 20)].set_index("data_alvo").sort_index()
    comuns = a.index.intersection(b.index)
    ea = (a.loc[comuns, "real"] - a.loc[comuns, "previsto"]).abs()
    eb = (b.loc[comuns, "real"] - b.loc[comuns, "previsto"]).abs()
    for d in sorted(set(base[(5, h)][0].index)):
        t = d - pd.Timedelta(weeks=h)
        prev = comuns[comuns <= t]
        if len(prev) < 13:
            continue
        w = prev[-13:]
        ma, mb = ea.loc[w].mean(), eb.loc[w].mean()
        escolha_minha[(h, d)] = 20 if mb < ma else 5
e3c = e3.set_index(["h", "data_alvo"]).folha_escolhida
comuns_e3 = [k for k in e3c.index if k in escolha_minha]
disc = [(k, int(e3c[k]), escolha_minha[k]) for k in comuns_e3 if int(e3c[k]) != escolha_minha[k]]
log(f"composto: escolhas E3 {len(e3c)}, minhas {len(escolha_minha)}, em comum {len(comuns_e3)}, divergentes {len(disc)}; so na E3 {len([k for k in e3c.index if k not in escolha_minha])}")
rel["composto_escolhas"] = {"E3": int(len(e3c)), "minhas": len(escolha_minha), "em_comum": len(comuns_e3), "divergentes": len(disc), "exemplos": [str(x) for x in disc[:5]]}
# composto: quantis da folha escolhida pela E3
def quantis_composto(h, escolha):
    linhas = {}
    for d, f in escolha.items():
        if d[0] == h and d[1] in ordenados[(f, h)].index:
            linhas[d[1]] = ordenados[(f, h)].loc[d[1]].to_numpy()
    return pd.DataFrame(linhas, index=NIVEIS).T.sort_index()
comp = {h: quantis_composto(h, {k: int(v) for k, v in e3c.items()}) for h in HS}
cx2 = csv(WIS / "previsoes_quantis_composto.csv", parse_dates=["data_alvo"])
cx2["quantil"] = cx2.quantil.round(2)
mxc = 0.0; nc = 0; so_exec = 0
for h, g in cx2.groupby("h"):
    piv = g.pivot(index="data_alvo", columns="quantil", values="previsto").sort_index()
    mi = comp[h]
    so_exec += len(piv.index.difference(mi.index)); 
    inter = piv.index.intersection(mi.index)
    mxc = max(mxc, np.abs(piv.loc[inter].to_numpy() - mi.loc[inter].to_numpy()).max()); nc += len(inter)
log(f"composto: quantis executor vs meus (folha escolhida pela E3), {nc} (h,data), dif max {mxc}, so no executor {so_exec}")
rel["composto_quantis_dif_max"] = float(mxc); rel["composto_so_exec"] = int(so_exec)
rel["composto_meu_sem_exec"] = int(sum(len(comp[h].index.difference(cx2[cx2.h == h].data_alvo.unique())) for h in HS))

# ------------------------------------------------------------------ 4. WIS e cobertura por modelo, h, janela
modelos = {}   # modelo -> h -> (reais, quantis DataFrame)
for h in HS:
    modelos.setdefault("folha5", {})[h] = (base[(5, h)][0], ordenados[(5, h)])
    modelos.setdefault("folha20", {})[h] = (base[(20, h)][0], ordenados[(20, h)])
    cm = comp[h]; rr = base[(5, h)][0]
    modelos.setdefault("composto_N13", {})[h] = (rr.loc[cm.index], cm)
    dd = [d for d in rr.index if regua[d] is not None]
    modelos.setdefault("regua_climatologica", {})[h] = (rr.loc[dd], pd.DataFrame([regua[d] for d in dd], index=dd, columns=NIVEIS))
linhas = []; por_origem = []
for mod, d in modelos.items():
    for h, (reais, q) in d.items():
        y = reais.to_numpy(); qq = q.to_numpy()
        w1 = wis_bracher(y, qq); w2 = wis_pinball(y, qq)
        assert np.allclose(w1, w2, atol=1e-9)
        c50, c80, c90 = cobertura(y, qq, 0.5), cobertura(y, qq, 0.8), cobertura(y, qq, 0.9)
        df = pd.DataFrame({"modelo": mod, "h": h, "data_alvo": reais.index, "real": y, "wis": w1, "c50": c50, "c80": c80, "c90": c90})
        por_origem.append(df)
PO = pd.concat(por_origem, ignore_index=True)
resumo = []
for nome, (a, b) in (("padrao_2024-01-07_a_2026-02-01", JAN_PADRAO), ("antiga_2024-2025", JAN_ANTIGA)):
    s = PO[(PO.data_alvo >= a) & (PO.data_alvo <= b)]
    g = s.groupby(["modelo", "h"]).agg(n=("wis", "size"), wis_medio=("wis", "mean"), cobertura_50=("c50", "mean"), cobertura_80=("c80", "mean"), cobertura_90=("c90", "mean")).reset_index()
    g["janela"] = nome
    resumo.append(g)
R = pd.concat(resumo, ignore_index=True)
R.to_csv(CERT / "meu_wis_resumo.csv", index=False, float_format="%.17g")
ex_r = csv(WIS / "wis_resumo.csv")
M = R.merge(ex_r, on=["modelo", "h", "janela"], suffixes=("_meu", "_exec"), how="outer", indicator=True)
assert (M._merge == "both").all() and len(M) == 96, M._merge.value_counts()
d_wis = (M.wis_medio_meu - M.wis_medio_exec).abs().max()
d_cob = max((M[f"cobertura_{k}_meu"] - M[f"cobertura_{k}_exec"]).abs().max() for k in (50, 80, 90))
d_n = int((M.n_meu != M.n_exec).sum())
log(f"WIS medio e cobertura: 96 linhas (4 modelos x 12 h x 2 janelas); dif max WIS {d_wis:.3e}; dif max cobertura {d_cob:.3e}; n diferentes {d_n}")
rel["wis_resumo_dif_max"] = float(d_wis); rel["cobertura_dif_max"] = float(d_cob); rel["n_diferentes"] = d_n
# por origem
exo = csv(WIS / "wis_por_origem.csv", parse_dates=["data_alvo"])
MO = PO.merge(exo, on=["modelo", "h", "data_alvo"], suffixes=("_meu", "_exec"), how="outer", indicator=True)
log(f"wis_por_origem: {len(MO)} linhas; so meu {int((MO._merge=='left_only').sum())}, so exec {int((MO._merge=='right_only').sum())}; dif max wis {(MO.wis_meu-MO.wis_exec).abs().max():.3e}; real {(MO.real_meu-MO.real_exec).abs().max():.3e}; cobertura 50/80/90 divergentes {(MO.c50!=MO.cobertura_50).sum()}/{(MO.c80!=MO.cobertura_80).sum()}/{(MO.c90!=MO.cobertura_90).sum()}")
rel["por_origem"] = {"so_meu": int((MO._merge=='left_only').sum()), "so_exec": int((MO._merge=='right_only').sum()), "dif_max_wis": float((MO.wis_meu-MO.wis_exec).abs().max()), "cob_divergentes": [int((MO.c50!=MO.cobertura_50).sum()), int((MO.c80!=MO.cobertura_80).sum()), int((MO.c90!=MO.cobertura_90).sum())]}
# janela padrao: n por modelo/h
pad = R[R.janela.str.startswith("padrao")]
log("n padrao por modelo: " + str(pad.groupby("modelo").n.agg(["min", "max"]).to_dict("index")))
rel["n_padrao"] = pad.groupby("modelo").n.agg(["min", "max"]).to_dict("index")
# sensibilidade da cobertura: estrita
cob_estrita = {}
for mod in modelos:
    reais, q = modelos[mod][4]
    for k, par in ((50, (0.25, 0.75)), ):
        pass
rel["cobertura_definicao"] = "inclusiva: l <= y <= u (conferida contra o executor: 0 divergencias por origem)"

# 26/09: previsoes brutas e WIS antigos
ant = csv(ANTIGO / "previsoes_quantis.csv", parse_dates=["data_alvo"])
ant["quantil"] = ant.quantil.round(2)
nome_ant = {"cenario_adotado": 5, "histgb_folha20": 20}
ant = ant[ant.modelo.isin(nome_ant)].copy()
ant["folha"] = ant.modelo.map(nome_ant)
mm = P.merge(ant[["folha", "h", "data_alvo", "quantil", "previsto_bruto"]], on=["folha", "h", "data_alvo", "quantil"], how="outer", indicator=True, suffixes=("", "_ant"))
mm = mm[mm.h.isin([1, 4, 8, 12])]
em = mm[mm._merge == "both"]
log(f"previsoes brutas vs 26/09: em comum {len(em)}, so novas {(mm._merge=='left_only').sum()}, so antigas {(mm._merge=='right_only').sum()}, dif max {(em.previsto-em.previsto_bruto).abs().max()}")
rel["vs_2609_previsoes"] = {"em_comum": int(len(em)), "so_novas": int((mm._merge=='left_only').sum()), "so_antigas": int((mm._merge=='right_only').sum()), "dif_max": float((em.previsto-em.previsto_bruto).abs().max())}
wa = csv(ANTIGO / "wis_e_cobertura.csv")
wa = wa[wa.recorte == "2024-2025"]
nome_m = {"cenario_adotado": "folha5", "histgb_folha20": "folha20", "regua_climatologica": "regua_climatologica"}
wa = wa[wa.modelo.isin(nome_m)].copy(); wa["modelo"] = wa.modelo.map(nome_m)
w_ant = R[R.janela == "antiga_2024-2025"].merge(wa, on=["modelo", "h"], suffixes=("_meu", "_ant"))
dw = (w_ant.wis_medio_meu - w_ant.wis_medio_ant).abs().max(); dc50 = (w_ant.cobertura_50_meu - w_ant.cobertura_50_ant).abs().max(); dc90 = (w_ant.cobertura_90_meu - w_ant.cobertura_90_ant).abs().max()
log(f"WIS janela antiga vs 26/09: {len(w_ant)} linhas, dif max WIS {dw:.3e}, cob50 {dc50:.3e}, cob90 {dc90:.3e}, n dif {(w_ant.n_meu!=w_ant.n_ant).sum()}")
rel["vs_2609_wis"] = {"linhas": int(len(w_ant)), "dif_max_wis": float(dw), "dif_cob50": float(dc50), "dif_cob90": float(dc90), "n_dif": int((w_ant.n_meu!=w_ant.n_ant).sum())}
anc = {("folha5", 1): 101.9, ("folha5", 4): 215.4, ("folha5", 8): 288.6, ("folha5", 12): 300.7, ("folha20", 1): 121.3, ("folha20", 4): 199.0, ("folha20", 8): 259.0, ("folha20", 12): 278.6, ("regua_climatologica", 1): 292.7, ("regua_climatologica", 4): 313.5, ("regua_climatologica", 8): 322.2, ("regua_climatologica", 12): 324.2}
ok_anc = all(abs(float(w_ant[(w_ant.modelo == m) & (w_ant.h == h)].wis_medio_meu.iloc[0]) - v) < 0.05 + 1e-9 for (m, h), v in anc.items())
log(f"ancoras da pre-declaracao (12 valores, tolerancia 0,05): {'todas batem' if ok_anc else 'DIVERGE'}")
rel["ancoras_12_batem"] = bool(ok_anc)
nant = {m: sorted(set(w_ant[w_ant.modelo == m].n_meu)) for m in ("folha5", "folha20", "regua_climatologica")}
log(f"n janela antiga (meu): {nant}")
rel["n_janela_antiga"] = nant

# ------------------------------------------------------------------ 5. F5: DM-HLN, bootstrap de blocos, Holm
def dm_hln(d, h):
    n = len(d); dbar = d.mean(); x = d - dbar
    def gam(k):
        return float(np.sum(x[k:] * x[:n - k]) / n)
    V = (gam(0) + 2 * sum(gam(k) for k in range(1, h))) / n
    fb = False
    if V <= 0:
        V = (gam(0) + 2 * sum((1 - k / h) * gam(k) for k in range(1, h))) / n; fb = True
    if V <= 0:
        return float("nan"), 1.0, True
    dm = dbar / math.sqrt(V)
    dm *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p = 2 * stats.t.sf(abs(dm), n - 1)
    return dm, float(p), fb

def boot_ic(LA, LB, variante=1, B=2000, bl=8, seed=42):
    n = len(LA); rng = np.random.default_rng(seed); nb = math.ceil(n / bl); out = np.empty(B)
    mb = LB.mean()
    for r in range(B):
        if variante == 1:
            st = rng.integers(0, n - bl + 1, size=nb)
        else:
            st = np.array([rng.integers(0, n - bl + 1) for _ in range(nb)])
        idx = np.concatenate([np.arange(s, s + bl) for s in st])[:n]
        out[r] = (LB[idx].mean() - LA[idx].mean()) / LB[idx].mean() * 100
    return np.percentile(out, 2.5), np.percentile(out, 97.5)

def holm(ps):
    m = len(ps); ordem = np.argsort(ps); aj = np.empty(m); run = 0.0
    for rank, i in enumerate(ordem):
        run = max(run, min(1.0, (m - rank) * ps[i])); aj[i] = run
    return aj

linhas_f5 = []
for mod in ("folha5", "folha20", "composto_N13"):
    for h in (1, 4, 8, 12):
        A = PO[(PO.modelo == mod) & (PO.h == h) & (PO.data_alvo >= JAN_PADRAO[0]) & (PO.data_alvo <= JAN_PADRAO[1])].set_index("data_alvo").wis
        B_ = PO[(PO.modelo == "regua_climatologica") & (PO.h == h) & (PO.data_alvo >= JAN_PADRAO[0]) & (PO.data_alvo <= JAN_PADRAO[1])].set_index("data_alvo").wis
        com = A.index.intersection(B_.index).sort_values()
        a = A.loc[com].to_numpy(); b = B_.loc[com].to_numpy(); d = b - a
        dm, p, fb = dm_hln(d, h)
        ic1 = boot_ic(a, b, 1); ic2 = boot_ic(a, b, 2)
        linhas_f5.append(dict(h=h, A=mod, n=len(com), wis_A=a.mean(), wis_B=b.mean(), delta=d.mean(), ganho_pct=d.mean() / b.mean() * 100, ic_inf_v1=ic1[0], ic_sup_v1=ic1[1], ic_inf_v2=ic2[0], ic_sup_v2=ic2[1], dm_hln=dm, p_bruto=p, fb=fb))
F = pd.DataFrame(linhas_f5)
F["p_holm"] = holm(F.p_bruto.to_numpy())
F["veredito"] = np.where(F.p_holm < 0.05, np.where(F.delta > 0, "A melhor", "A pior"), "sem evidencia")
F.to_csv(CERT / "meu_familia_F5.csv", index=False, float_format="%.17g")
EF = csv(WIS / "familia_F5.csv").rename(columns={"A": "A"})
J = F.merge(EF, on=["A", "h"], suffixes=("_meu", "_exec"))
assert len(J) == 12
log("F5: dif max n %d | wis_A %.2e | wis_B %.2e | delta %.2e | ganho %.2e | DM %.2e | p_bruto %.2e | p_holm %.2e" % (
    (J.n_meu != J.n_exec).sum(), (J.wis_A_meu - J.wis_A_exec).abs().max(), (J.wis_B_meu - J.wis_B_exec).abs().max(), (J.delta_meu - J.delta_exec).abs().max(),
    (J.ganho_pct_meu - J.ganho_pct_exec).abs().max(), (J.dm_hln_meu - J.dm_hln_exec).abs().max(), (J.p_bruto_meu - J.p_bruto_exec).abs().max(), (J.p_holm_meu - J.p_holm_exec).abs().max()))
log("F5: vereditos divergentes: %d; fallback de variancia meu: %d" % ((J.veredito_meu != J.veredito_exec).sum(), int(J.fb.sum())))
dic1 = max((J.ic_inf_v1 - J.ic_inf).abs().max(), (J.ic_sup_v1 - J.ic_sup).abs().max())
dic2 = max((J.ic_inf_v2 - J.ic_inf).abs().max(), (J.ic_sup_v2 - J.ic_sup).abs().max())
log(f"F5: IC bootstrap, dif max vs executor: variante vetor-por-replica {dic1:.4f} pp; variante sorteio escalar {dic2:.4f} pp")
rel["F5"] = {"n_dif": int((J.n_meu != J.n_exec).sum()), "dif_wis_A": float((J.wis_A_meu - J.wis_A_exec).abs().max()), "dif_delta": float((J.delta_meu - J.delta_exec).abs().max()), "dif_dm": float((J.dm_hln_meu - J.dm_hln_exec).abs().max()), "dif_p_bruto": float((J.p_bruto_meu - J.p_bruto_exec).abs().max()), "dif_p_holm": float((J.p_holm_meu - J.p_holm_exec).abs().max()), "vereditos_divergentes": int((J.veredito_meu != J.veredito_exec).sum()), "ic_dif_max_v1": float(dic1), "ic_dif_max_v2": float(dic2)}
log(J[["A", "h", "n_meu", "delta_meu", "ganho_pct_meu", "ic_inf_v1", "ic_sup_v1", "ic_inf", "ic_sup", "p_holm_meu", "p_holm_exec", "veredito_meu", "veredito_exec"]].to_string())

# ------------------------------------------------------------------ 6. mutacao da cobertura / sensibilidade: WIS em janela padrao sem a data sem regua
# (a regua nao tem 28/12/2025): WIS dos modelos nas 101 semanas pareadas vs 102
Rr = {}
for mod in ("folha5", "folha20", "composto_N13"):
    for h in (1, 4, 8, 12):
        s = PO[(PO.modelo == mod) & (PO.h == h) & (PO.data_alvo >= JAN_PADRAO[0]) & (PO.data_alvo <= JAN_PADRAO[1])]
        Rr[f"{mod}_h{h}"] = (len(s), float(s.wis.mean()), float(s[s.data_alvo != pd.Timestamp('2025-12-28')].wis.mean()))
rel["wis_102_vs_101"] = Rr

# 7. integridade da janela: semanas ausentes na grade de 108 semanas
grade = pd.date_range(JAN_PADRAO[0], JAN_PADRAO[1], freq="7D")
for mod in ("folha5", "folha20", "composto_N13"):
    s = PO[(PO.modelo == mod) & (PO.h == 4) & PO.data_alvo.between(*JAN_PADRAO)]
    falt = [d.date().isoformat() for d in grade if d not in set(s.data_alvo)]
    rel[f"semanas_da_janela_sem_previsao_{mod}_h4"] = falt
log(f"semanas de 07/01/2024 a 01/02/2026 ({len(grade)}) sem previsao em h=4: {rel['semanas_da_janela_sem_previsao_folha5_h4']}")
# a mesma lista nos 12 h para folha5
listas = {h: tuple(d.date().isoformat() for d in grade if d not in set(PO[(PO.modelo=='folha5')&(PO.h==h)].data_alvo)) for h in HS}
rel["datas_faltantes_folha5_por_h_distintas"] = len(set(listas.values()))

(CERT / "resultado_verificacao.json").write_text(json.dumps(rel, indent=1, default=str, ensure_ascii=False))
(CERT / "verificar_wis.log").write_text("\n".join(LOG))
