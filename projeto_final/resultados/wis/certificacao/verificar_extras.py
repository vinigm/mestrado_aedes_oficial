"""Certificacao E7 - parte 2: retreino vs parciais, WIS ponta a ponta de 2 (folha,h), sensibilidades, mutacoes, Holm alternativo."""
import json, math, pathlib, glob
import numpy as np, pandas as pd
from scipy import stats
CERT = pathlib.Path(__file__).resolve().parent
PF = CERT.parents[2]
WIS = PF / "resultados" / "wis"
NIVEIS = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
rel = {}; LOG = []
def log(m): print(m); LOG.append(str(m))
def csv(p, **k): return pd.read_csv(p, float_precision="round_trip", **k)

# ---- retreino vs parciais
linhas = []
for f in sorted(glob.glob(str(CERT / "retreino" / "retreino_*.csv"))):
    r = csv(f, parse_dates=["data_origem", "data_alvo"])
    fo, q, h = int(r.folha[0]), float(r.quantil[0]), int(r.h[0])
    p = csv(WIS / "parciais" / f"previsoes_folha{fo}_q{round(q*100):03d}_h{h:02d}.csv", parse_dates=["data_origem", "data_alvo"])
    m = r.merge(p, on=["data_origem", "data_alvo"], how="outer", indicator=True, suffixes=("_r", "_p"))
    both = m[m._merge == "both"]
    linhas.append(dict(folha=fo, quantil=q, h=h, n_retreino=len(r), n_parcial=len(p), so_um_lado=int((m._merge != "both").sum()),
                       dif_max_previsto=float((both.previsto_bruto - both.previsto).abs().max()), dif_max_real=float((both.real_r - both.real_p).abs().max()),
                       n_acima_1e9=int(((both.previsto_bruto - both.previsto).abs() > 1e-9).sum())))
RT = pd.DataFrame(linhas); RT.to_csv(CERT / "retreino_vs_parciais.csv", index=False)
log(RT.to_string())
rel["retreino"] = {"celulas": len(RT), "dif_max": float(RT.dif_max_previsto.max()), "so_um_lado_total": int(RT.so_um_lado.sum()), "acima_1e9": int(RT.n_acima_1e9.sum()),
                   "n_linhas_total_retreinadas": int(RT.n_retreino.sum())}

# ---- WIS ponta a ponta a partir so do retreino (folha5 h4 e folha20 h12): sorted + Bracher vs resumo do executor
def wis(y, q):
    tot = 0.0
    for j, tau in enumerate(NIVEIS):
        d = y - q[:, j]; tot = tot + np.where(d >= 0, tau * d, (tau - 1) * d)
    return tot / 3.5
ex = csv(WIS / "wis_resumo.csv")
out = {}
for fo, h in ((5, 4), (20, 12)):
    cols = []
    for q in NIVEIS:
        r = csv(CERT / "retreino" / f"retreino_f{fo}_q{round(q*100):03d}_h{h:02d}.csv", parse_dates=["data_alvo"]).set_index("data_alvo")
        cols.append(r.previsto_bruto.rename(q)); y = r.real
    Q = pd.concat(cols, axis=1).sort_index(); y = y.sort_index()
    s = np.sort(Q.to_numpy(), axis=1)
    w = pd.Series(wis(y.to_numpy(), s), index=y.index)
    wj = w[(w.index >= "2024-01-07") & (w.index <= "2026-02-01")]
    e = ex[(ex.modelo == f"folha{fo}") & (ex.h == h) & ex.janela.str.startswith("padrao")].iloc[0]
    out[f"folha{fo}_h{h}"] = dict(n=len(wj), wis_retreino=float(wj.mean()), wis_executor=float(e.wis_medio), dif=float(abs(wj.mean() - e.wis_medio)))
    log(f"WIS retreino ponta a ponta folha{fo} h{h}: n={len(wj)} meu={wj.mean():.10f} executor={e.wis_medio:.10f}")
rel["wis_ponta_a_ponta"] = out

# ---- sensibilidades
P = pd.concat([csv(f) for f in sorted((WIS / "parciais").glob("previsoes_folha*_q*_h*.csv"))], ignore_index=True)
for c in ("data_origem", "data_alvo"): P[c] = pd.to_datetime(P[c])
P = P[~np.isclose(P.quantil, 0.85)].copy(); P["quantil"] = P.quantil.round(2)
w_ord = {}; w_raw = {}; neg = []
for (fo, h), g in P.groupby(["folha", "h"]):
    piv = g.pivot(index="data_alvo", columns="quantil", values="previsto").sort_index()
    y = g.drop_duplicates("data_alvo").set_index("data_alvo").real.sort_index()
    mk = (piv.index >= "2024-01-07") & (piv.index <= "2026-02-01")
    v = piv.to_numpy()[mk]; yy = y.to_numpy()[mk]
    w_raw[(fo, h)] = wis(yy, v).mean(); w_ord[(fo, h)] = wis(yy, np.sort(v, axis=1)).mean()
    neg.append((fo, h, float((v[:, 0] < 0).mean()), float(v.min())))
d = [(k, w_raw[k], w_ord[k], 100 * (w_raw[k] / w_ord[k] - 1)) for k in w_ord]
log("sensibilidade a ordenacao (WIS sem ordenar vs ordenado): variacao relativa min/max %.2f%% / %.2f%%" % (min(x[3] for x in d), max(x[3] for x in d)))
rel["ordenacao_pct_min_max"] = [min(x[3] for x in d), max(x[3] for x in d)]
log("quantil 0,05 negativo: fracao min/max %.3f / %.3f ; menor previsao %.2f" % (min(x[2] for x in neg), max(x[2] for x in neg), min(x[3] for x in neg)))
rel["q005_negativo_fracao_min_max"] = [min(x[2] for x in neg), max(x[2] for x in neg)]

# ---- mutacao: o teste F5 reage? (1) regua trocada por modelo ruim; (2) bootstrap com bloco diferente nao muda o veredito (que vem do DM)
F = csv(CERT / "meu_familia_F5.csv")
PO_ex = csv(WIS / "wis_por_origem.csv", parse_dates=["data_alvo"])
def dm(d, h):
    n = len(d); x = d - d.mean(); g = lambda k: float(np.sum(x[k:] * x[:n - k]) / n)
    V = (g(0) + 2 * sum(g(k) for k in range(1, h))) / n
    return d.mean() / math.sqrt(V) * math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
a = PO_ex[(PO_ex.modelo == "folha5") & (PO_ex.h == 1) & PO_ex.data_alvo.between("2024-01-07", "2026-02-01")].set_index("data_alvo").wis
b = PO_ex[(PO_ex.modelo == "regua_climatologica") & (PO_ex.h == 1)].set_index("data_alvo").wis
c = a.index.intersection(b.index).sort_values()
d0 = (b.loc[c] - a.loc[c]).to_numpy()
rel["mutacao_F5"] = {"original_dm_h1_folha5": dm(d0, 1), "sinal_trocado": dm(-d0, 1), "com_regua_igual_ao_modelo": "d=0 -> V=0 (DM indefinido, tratado como borda)",
                     "ordem_embaralhada_dm": dm(np.random.default_rng(0).permutation(d0), 1)}
log(f"mutacao F5: DM h1 folha5 original {rel['mutacao_F5']['original_dm_h1_folha5']:.4f}, sinal trocado {rel['mutacao_F5']['sinal_trocado']:.4f}, embaralhado {rel['mutacao_F5']['ordem_embaralhada_dm']:.4f}")
# Holm alternativo: statsmodels se existir, senao step-down manual diferente
try:
    from statsmodels.stats.multitest import multipletests
    aj = multipletests(F.p_bruto.to_numpy(), method="holm")[1]
    rel["holm_statsmodels_dif_max"] = float(np.abs(aj - F.p_holm.to_numpy()).max()); log(f"Holm statsmodels vs meu: dif max {rel['holm_statsmodels_dif_max']:.2e}")
except Exception as e:
    ps = F.p_bruto.to_numpy(); o = np.argsort(ps); m = len(ps); aj = np.empty(m); prev = 0
    # implementacao alternativa: p_adj_i = max_{j<=i} min(1, (m-j+1) p_(j)) com j de 1
    for j, i in enumerate(o, start=1):
        prev = max(prev, min(1, (m - j + 1) * ps[i])); aj[i] = prev
    rel["holm_alt_dif_max"] = float(np.abs(aj - F.p_holm.to_numpy()).max()); log(f"statsmodels ausente ({type(e).__name__}); Holm alternativo dif max {rel['holm_alt_dif_max']:.2e}")
# p-valor DM: conferir a cauda t com outra rotina (stats.ttest_1samp nao serve; usar cdf)
dif = max(abs(2 * (1 - stats.t.cdf(abs(r.dm_hln), 100)) - r.p_bruto) for r in F.itertuples() if False) if False else None
# p bilateral via cdf com n-1 gl
dmax = 0.0
for r in F.itertuples():
    p2 = 2 * (1 - stats.t.cdf(abs(r.dm_hln), r.n - 1)); dmax = max(dmax, abs(p2 - r.p_bruto))
rel["p_bruto_via_cdf_dif_max"] = dmax; log(f"p bruto via t.cdf: dif max {dmax:.2e}")
# coerencia interna dos numeros do relato do executor (janela padrao): amostra
chk = {("folha5", 1): 97.0, ("folha20", 1): 115.5, ("composto_N13", 1): 106.2, ("regua_climatologica", 1): 278.3, ("folha5", 4): 205.0, ("folha20", 4): 189.5, ("composto_N13", 4): 188.5, ("regua_climatologica", 4): 298.1,
       ("folha5", 8): 275.0, ("folha20", 8): 246.9, ("composto_N13", 8): 248.0, ("regua_climatologica", 8): 306.3, ("folha5", 12): 286.3, ("folha20", 12): 265.3, ("composto_N13", 12): 279.5, ("regua_climatologica", 12): 308.2}
R = csv(CERT / "meu_wis_resumo.csv"); R = R[R.janela.str.startswith("padrao")]
bad = [(k, v, round(float(R[(R.modelo == k[0]) & (R.h == k[1])].wis_medio.iloc[0]), 1)) for k, v in chk.items() if abs(round(float(R[(R.modelo == k[0]) & (R.h == k[1])].wis_medio.iloc[0]), 1) - v) > 0.05]
log(f"relato do executor: 16 WIS medios da janela padrao conferem com os meus (arred. 0,1): {'sim' if not bad else bad}")
rel["relato_16_wis_conferem"] = not bad
cob = {("folha5", 12): (0.20, 0.40, 0.54), ("regua_climatologica", 12): (0.21, 0.36, 0.41)}
for k, v in cob.items():
    r = R[(R.modelo == k[0]) & (R.h == k[1])].iloc[0]; log(f"cobertura {k}: meu {r.cobertura_50:.3f}/{r.cobertura_80:.3f}/{r.cobertura_90:.3f} vs relato {v}")
# cobertura: abaixo do nominal em quantos (modelo,h)?
Rall = csv(CERT / "meu_wis_resumo.csv"); Rall = Rall[Rall.janela.str.startswith("padrao")]
for mod in ("folha5", "folha20", "composto_N13", "regua_climatologica"):
    s = Rall[Rall.modelo == mod]
    rel[f"cobertura_{mod}_faixa"] = {k: [float(s[f"cobertura_{k}"].min()), float(s[f"cobertura_{k}"].max())] for k in (50, 80, 90)}
    log(f"cobertura {mod} h1-12: 50% [{s.cobertura_50.min():.2f},{s.cobertura_50.max():.2f}] 80% [{s.cobertura_80.min():.2f},{s.cobertura_80.max():.2f}] 90% [{s.cobertura_90.min():.2f},{s.cobertura_90.max():.2f}]")
(CERT / "resultado_verificacao_extras.json").write_text(json.dumps(rel, indent=1, default=str))
(CERT / "verificar_extras.log").write_text("\n".join(LOG))
