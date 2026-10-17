"""Itens 3, 4 e 5 (so pandas/numpy; sem treino). Recalcula travas, MAE, contagens, pares e
integridade dos 192 parciais; compara as linhas de cada parcial com a matriz da minha receita."""
import itertools
import json
import pathlib
import numpy as np
import pandas as pd
import minha_receita as R

E2 = R.RAIZ / "resultados/ciencia/E2_ablacao"
out = {}
BR = ["completo", "sem_casos", "sem_clima", "sem_vetor", "so_casos", "so_clima", "so_vetor", "so_calendario"]
INI, FIM, FIM_CAL = pd.Timestamp("2024-01-07"), pd.Timestamp("2026-02-01"), pd.Timestamp("2023-12-31")

# ---------- item 5: parciais
arq = sorted(p.name for p in (E2 / "parciais").iterdir())
esperados = sorted(f"previsoes_{b}_folha{f}_h{h:02d}.csv" for b in BR for f in (5, 20) for h in range(1, 13))
out["parciais_presentes"] = len(arq)
out["parciais_iguais_ao_esperado"] = arq == esperados
out["arquivos_estranhos"] = sorted(set(arq) - set(esperados))
partes = []
t = R.carregar_tabela_cortada()
linhas_ok = True
detalhe_linhas = []
mats = {}
for b in BR:
    for f in (5, 20):
        for h in range(1, 13):
            p = pd.read_csv(E2 / "parciais" / f"previsoes_{b}_folha{f}_h{h:02d}.csv", parse_dates=["data_origem", "data_alvo"])
            partes.append(p)
            if (b, h) not in mats:
                mats[(b, h)] = R.matriz_do_braco(t, h, b)
            m = mats[(b, h)].iloc[104:]
            ok = (len(p) == len(m) and (p["data_origem"].values == m["data_origem"].values).all()
                  and (p["data_alvo"].values == m["data_alvo"].values).all()
                  and np.array_equal(p["real"].values, m["y_h"].values)
                  and (p["h"].unique().tolist() == [h] if "h" in p.columns else True))
            if not ok:
                linhas_ok = False
                detalhe_linhas.append((b, f, h))
out["parciais_linhas_e_real_iguais_a_minha_matriz"] = linhas_ok
out["parciais_linhas_divergentes"] = detalhe_linhas
print("colunas parcial:", list(partes[0].columns))
todas = pd.concat(partes, ignore_index=True)
prev = pd.read_csv(E2 / "previsoes.csv", parse_dates=["data_origem", "data_alvo"])
out["previsoes_total"] = len(prev)
out["previsoes_igual_concat_parciais"] = bool(prev.reset_index(drop=True).equals(todas[prev.columns].reset_index(drop=True)))
out["duplicatas_braco_folha_h_dataalvo"] = int(prev.duplicated(["braco", "folha", "h", "data_alvo"]).sum())
out["duplicatas_braco_folha_h_dataorigem"] = int(prev.duplicated(["braco", "folha", "h", "data_origem"]).sum())
out["nan_em_previsto_ou_real"] = int(prev[["real", "previsto"]].isna().sum().sum())
out["data_alvo_menos_origem_correto"] = bool(((prev["data_alvo"] - prev["data_origem"]) == pd.to_timedelta(prev["h"] * 7, unit="D")).all())
out["previsto_negativo"] = int((prev["previsto"] < 0).sum())
# real identico entre bracos na mesma (h, data_alvo)
g = prev.groupby(["h", "data_alvo"])["real"].nunique()
out["real_inconsistente_entre_bracos"] = int((g > 1).sum())
# real = casos da tabela em data_origem+h semanas
casos = t.set_index(R.COL_DATA)[R.COL_CASOS]
rr = casos.reindex(prev["data_alvo"]).values
out["real_igual_casos_da_tabela"] = bool(np.array_equal(rr, prev["real"].values))
contagem = prev.groupby(["braco", "folha"]).size().unstack()
out["linhas_por_braco_folha"] = contagem.to_dict()

# ---------- item 3: travas
ref = pd.read_csv(R.RAIZ / "resultados/referencia/previsoes.csv", parse_dates=["data_alvo"])
gab = pd.read_csv(R.RAIZ / "testes/referencia_antiga/previsoes_por_braco_original.csv", parse_dates=["data_alvo"])
out["referencia_bracos"] = sorted(ref["braco"].unique().tolist())
out["gabarito_bracos"] = sorted(gab["braco"].unique().tolist())
def comparar(a, b, rot):
    j = a.merge(b, on=["h", "data_alvo"], how="outer", suffixes=("_e2", "_g"), indicator=True)
    so_e2 = int((j["_merge"] == "left_only").sum()); so_g = int((j["_merge"] == "right_only").sum())
    amb = j[j["_merge"] == "both"]
    d = (amb["previsto_e2"] - amb["previsto_g"]).abs()
    r = (amb["real_e2"] - amb["real_g"]).abs()
    return dict(rotulo=rot, n_e2=len(a), n_gabarito=len(b), so_e2=so_e2, so_gabarito=so_g, pares=len(amb),
                dif_max_previsto=float(d.max()), n_dif_gt_1e9=int((d > 1e-9).sum()), dif_max_real=float(r.max()))
c5 = prev[(prev.braco == "completo") & (prev.folha == 5)]
c20 = prev[(prev.braco == "completo") & (prev.folha == 20)]
sv20 = prev[(prev.braco == "sem_vetor") & (prev.folha == 20)]
out["trava1_f5"] = comparar(c5, ref[ref.braco == "referencia"], "completo f5 x referencia")
out["trava1_f20"] = comparar(c20, ref[ref.braco == "HistGB_folha20_M1"], "completo f20 x HistGB_folha20_M1 (referencia)")
out["trava2"] = comparar(sv20, gab[gab.braco == "HistGB_folha20_M0"], "sem_vetor f20 x HistGB_folha20_M0")
# gabarito antigo: o proprio 'referencia' e 'HistGB_folha20_M1' do arquivo antigo
out["completo_f5_x_gabarito_antigo_referencia"] = comparar(c5, gab[gab.braco == "referencia"], "completo f5 x gabarito antigo")
out["completo_f20_x_gabarito_antigo_M1"] = comparar(c20, gab[gab.braco == "HistGB_folha20_M1"], "completo f20 x gabarito antigo M1")
out["gabarito_M0_n_por_h_janela"] = gab[(gab.braco == "HistGB_folha20_M0") & (gab.data_alvo >= INI) & (gab.data_alvo <= FIM)].groupby("h").size().unique().tolist()

# ---------- item 4: MAE e contagens
def mae_n(df):
    j = df[(df.data_alvo >= INI) & (df.data_alvo <= FIM)]
    return len(j), float((j["previsto"] - j["real"]).abs().mean())
linhas = []
for (b, f, h), d in prev.groupby(["braco", "folha", "h"]):
    n, mae = mae_n(d)
    linhas.append(dict(braco=b, folha=f, h=h, n_janela=n, mae=mae))
meu = pd.DataFrame(linhas)
mae = pd.read_csv(E2 / "mae_descritivo.csv")
j = mae.merge(meu, on=["braco", "folha", "h"], suffixes=("_arq", "_meu"), how="outer", indicator=True)
out["mae_linhas_arquivo"] = len(mae); out["mae_linhas_meu"] = len(meu)
out["mae_merge_ok"] = bool((j["_merge"] == "both").all())
out["mae_dif_max"] = float((j["mae_arq"] - j["mae_meu"]).abs().max())
out["mae_dif_n_janela"] = int((j["n_janela_arq"] != j["n_janela_meu"]).sum())
out["n_janela_por_braco"] = {b: sorted(set(meu[meu.braco == b].n_janela)) for b in BR}
# ancoras
def m_(b, f, h): return float(meu[(meu.braco == b) & (meu.folha == f) & (meu.h == h)].mae.iloc[0])
out["ancoras_janela_completo"] = {f"f{f}": [round(m_("completo", f, h), 3) for h in (1, 4, 8, 12)] for f in (5, 20)}
out["gabarito_M0_mae_janela"] = [round(float((lambda d: (d.previsto - d.real).abs().mean())(gab[(gab.braco == "HistGB_folha20_M0") & (gab.h == h) & (gab.data_alvo >= INI) & (gab.data_alvo <= FIM)])), 3) for h in (1, 4, 8, 12)]
# calibracao completo f5, quantil 0.85
cal = []
for h in (1, 4, 8, 12):
    d = prev[(prev.braco == "completo") & (prev.folha == 5) & (prev.h == h) & (prev.data_alvo <= FIM_CAL)]
    cal.append((len(d), round(float((d.previsto - d.real).abs().mean()), 3)))
out["calibracao_completo_f5"] = cal
# pares pre-declarados
def pares(b1, b2, f, h):
    a = prev[(prev.braco == b1) & (prev.folha == f) & (prev.h == h) & (prev.data_alvo >= INI) & (prev.data_alvo <= FIM)]
    c = prev[(prev.braco == b2) & (prev.folha == f) & (prev.h == h) & (prev.data_alvo >= INI) & (prev.data_alvo <= FIM)]
    return len(set(a.data_alvo) & set(c.data_alvo))
pp = {}
for f in (5, 20):
    for h in (1, 4, 8, 12):
        for x in ("casos", "clima", "vetor"):
            pp[f"completo x sem_{x} f{f} h{h}"] = pares("completo", f"sem_{x}", f, h)
            pp[f"so_{x} x so_calendario f{f} h{h}"] = pares(f"so_{x}", "so_calendario", f, h)
out["pares_em_comum"] = pp
out["pares_valores_distintos"] = {}
for k, v in pp.items():
    out["pares_valores_distintos"].setdefault(k.split(" f")[0], set()).add(v)
out["pares_valores_distintos"] = {k: sorted(v) for k, v in out["pares_valores_distintos"].items()}
json.dump(out, open("v03_resultado.json", "w"), indent=1, default=str)
for k, v in out.items():
    if k not in ("pares_em_comum", "linhas_por_braco_folha"):
        print(k, "=", v)
