"""Certificacao adversarial E4, verificacoes 1 e 2. Codigo proprio: sklearn direto, numpy/pandas.
Usa so o construtor de MATRIZ certificado (aedes.bracos / aedes.variaveis); NAO usa walk_forward*, comparacoes, metricas."""
import pathlib, hashlib, json, sys
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from aedes.configuracao import CONFIGURACAO_DADOS, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_AVALIACAO, FOLHA_5
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.bracos import montar_matriz_do_braco
from aedes.variaveis import montar_matriz_do_horizonte

PF = pathlib.Path(".").resolve()
SAIDA = PF / "resultados/ciencia/certificacao/E4_integridade"
out = {}
tab = aplicar_corte_de_maturidade(montar_tabela_a_partir_dos_bytes((PF/"dados/tabela_final.csv").read_bytes(), CONFIGURACAO_DADOS), CONFIGURACAO_DADOS)

PARAMS = dict(loss="quantile", quantile=0.85, max_iter=250, learning_rate=0.05, max_leaf_nodes=15,
              min_samples_leaf=5, random_state=42)
out["params_config_folha5"] = {k: str(v) for k, v in FOLHA_5.parametros_do_sklearn().items()}
dif_params = {k: (v, FOLHA_5.parametros_do_sklearn()[k]) for k, v in PARAMS.items() if FOLHA_5.parametros_do_sklearn()[k] != v}
out["params_explicitos_vs_config_divergentes"] = {k: str(v) for k, v in dif_params.items()}

E4 = pd.read_csv(PF/"resultados/ciencia/E4_corte/previsoes.csv", parse_dates=["data_origem","data_alvo"])
E2 = pd.read_csv(PF/"resultados/ciencia/E2_ablacao/previsoes.csv", parse_dates=["data_origem","data_alvo"])
REF = pd.read_csv(PF/"resultados/referencia/previsoes.csv", parse_dates=["data_origem","data_alvo"])
ini, fim = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada, CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
out["janela"] = [str(ini.date()), str(fim.date())]

# ---------- Verificacao 1: retreino com corte ingenuo (s < t), codigo proprio
def prever_origem(mat, h, t, regra):
    cols = [c for c in mat.columns if c not in ("data_origem","data_alvo","y_h")]
    if regra == "pergunta":
        tr = mat[mat["data_origem"] < t]
    else:
        tr = mat[mat["data_origem"] + pd.Timedelta(weeks=h) <= t]
    m = HistGradientBoostingRegressor(**PARAMS).fit(tr[cols], tr["y_h"])
    linha = mat[mat["data_origem"] == t]
    assert len(linha) == 1
    return float(m.predict(linha[cols])[0]), tr, cols

v1 = []
for braco in ("completo", "sem_vetor"):
    for h in (4, 12):
        mat = montar_matriz_do_braco(tab, h, braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DATAS if False else CONFIGURACAO_DADOS)
        salvo = E4[(E4.braco == braco) & (E4.h == h)].set_index("data_origem")
        na_janela = salvo[(salvo.data_alvo >= ini) & (salvo.data_alvo <= fim)]
        # 3 origens: primeira, meio e ultima da janela
        idx = [0, len(na_janela)//2, len(na_janela)-1]
        for i in idx:
            t = na_janela.index[i]
            p, tr, cols = prever_origem(mat, h, t, "pergunta")
            pr, tr_r, _ = prever_origem(mat, h, t, "resposta")
            vaza = int((tr["data_origem"] + pd.Timedelta(weeks=h) > t).sum())
            vaza_resp = int((tr_r["data_origem"] + pd.Timedelta(weeks=h) > t).sum())
            # treino pergunta == EXATAMENTE {s < t}
            igual = set(tr["data_origem"]) == set(mat.loc[mat.data_origem < t, "data_origem"])
            v1.append(dict(braco=braco, h=h, t=str(t.date()), n_treino_pergunta=len(tr), n_treino_resposta=len(tr_r),
                           linhas_com_resposta_apos_t_no_treino_pergunta=vaza, idem_resposta=vaza_resp,
                           treino_igual_a_s_menor_t=igual, max_data_origem_treino=str(tr.data_origem.max().date()),
                           previsto_meu=p, previsto_salvo_e4=float(salvo.loc[t, "previsto"]),
                           dif_abs_pergunta=abs(p - float(salvo.loc[t, "previsto"])),
                           previsto_meu_resposta=pr))
v1 = pd.DataFrame(v1)
# o corte resposta tambem confere com a E2 (so p/ completo e sem_vetor, folha 5)
e2 = E2[(E2.folha == 5)].set_index(["braco","h","data_origem"])["previsto"]
v1["dif_abs_resposta_vs_E2"] = [abs(r.previsto_meu_resposta - float(e2.loc[(r.braco, r.h, pd.Timestamp(r.t))])) for r in v1.itertuples()]
v1.to_csv(SAIDA/"v1_retreino_tres_origens.csv", index=False)
out["v1_max_dif_pergunta"] = float(v1.dif_abs_pergunta.max())
out["v1_max_dif_resposta_vs_E2"] = float(v1.dif_abs_resposta_vs_E2.max())
out["v1_treino_igual_a_s_menor_t_todas"] = bool(v1.treino_igual_a_s_menor_t.all())
out["v1_vazamento_pergunta_por_h"] = {f"{r.braco}_h{r.h}": int(r.linhas_com_resposta_apos_t_no_treino_pergunta) for r in v1.itertuples()}
out["v1_vazamento_resposta_max"] = int(v1.idem_resposta.max())

# ---------- Verificacao 2: recomputar comparacao.csv
def mae(a, b): return float(np.mean(np.abs(a - b)))
def r2(a, b):
    sst = float(np.sum((a - a.mean())**2)); sse = float(np.sum((a - b)**2))
    return 1 - sse/sst
res_e2 = E2[(E2.folha == 5) & E2.braco.isin(["completo","sem_vetor"])]
linhas = []
checks = {"mesmas_semanas_todas": True, "real_igual": True, "origens_iguais_em_toda_a_serie": True}
for braco in ("completo","sem_vetor"):
    for h in range(1, 13):
        a = res_e2[(res_e2.braco==braco)&(res_e2.h==h)]
        b = E4[(E4.braco==braco)&(E4.h==h)]
        # series completas (nao so a janela): mesmas origens?
        if set(a.data_origem) != set(b.data_origem) or len(a) != len(b): checks["origens_iguais_em_toda_a_serie"] = False
        aj = a[(a.data_alvo>=ini)&(a.data_alvo<=fim)].sort_values("data_alvo")
        bj = b[(b.data_alvo>=ini)&(b.data_alvo<=fim)].sort_values("data_alvo")
        if list(aj.data_alvo) != list(bj.data_alvo): checks["mesmas_semanas_todas"] = False
        if not np.array_equal(aj.real.values, bj.real.values): checks["real_igual"] = False
        ma, mb = mae(aj.real.values, aj.previsto.values), mae(bj.real.values, bj.previsto.values)
        linhas.append(dict(braco=braco,h=h,n=len(aj),mae_resposta=ma,mae_pergunta=mb,variacao_pct=100*(mb-ma)/ma,
                           r2_resposta=r2(aj.real.values,aj.previsto.values), r2_pergunta=r2(bj.real.values,bj.previsto.values),
                           delta_r2_pontos=r2(bj.real.values,bj.previsto.values)-r2(aj.real.values,aj.previsto.values)))
mine = pd.DataFrame(linhas)
mine.to_csv(SAIDA/"v2_comparacao_recomputada.csv", index=False)
sal = pd.read_csv(PF/"resultados/ciencia/E4_corte/comparacao.csv")
m = sal.merge(mine, on=["braco","h"], suffixes=("_s","_m"))
out["v2_linhas_salvo_mine"] = [len(sal), len(mine), len(m)]
out["v2_max_dif"] = {c: float((m[a]-m[b]).abs().max()) for c,(a,b) in {
    "mae_resposta":("mae_corte_resposta","mae_resposta"),"mae_pergunta":("mae_corte_pergunta","mae_pergunta"),
    "variacao_pct":("variacao_pct_s","variacao_pct_m"),"r2_resposta":("r2_corte_resposta","r2_resposta"),
    "r2_pergunta":("r2_corte_pergunta","r2_pergunta"),"n":("n_s","n_m")}.items()}
out["v2_n_por_braco"] = {b: sorted(set(mine[mine.braco==b].n)) for b in ("completo","sem_vetor")}
out["v2_checks"] = checks
out["v2_h1_variacao_exatamente_zero"] = bool((mine[mine.h==1].variacao_pct == 0.0).all())
out["v2_completo_resposta_igual_referencia"] = float(
    (res_e2[(res_e2.braco=="completo")].set_index(["h","data_alvo"]).previsto
     - REF[REF.braco=="referencia"].set_index(["h","data_alvo"]).previsto).abs().max())
out["v2_variacao_completo"] = [round(x,1) for x in mine[mine.braco=="completo"].variacao_pct]
out["v2_variacao_sem_vetor"] = [round(x,1) for x in mine[mine.braco=="sem_vetor"].variacao_pct]
out["v2_mae_resposta_completo_h1_4_8_12"] = [round(x,3) for x in mine[(mine.braco=="completo")&mine.h.isin([1,4,8,12])].mae_resposta]
out["v2_mae_resposta_sem_vetor_h1_4_8_12"] = [round(x,3) for x in mine[(mine.braco=="sem_vetor")&mine.h.isin([1,4,8,12])].mae_resposta]
out["v2_delta_r2_pontos_h12_completo_sem_vetor"] = [round(float(mine[(mine.braco==b)&(mine.h==12)].delta_r2_pontos.iloc[0]),4) for b in ("completo","sem_vetor")]
# parciais == previsoes.csv
parc = pd.concat([pd.read_csv(p, parse_dates=["data_origem","data_alvo"]) for p in sorted((PF/"resultados/ciencia/E4_corte/parciais").glob("*.csv"))])
out["parciais"] = [len(list((PF/"resultados/ciencia/E4_corte/parciais").glob("*"))), len(parc), len(E4)]
out["previsoes_e4_corte_col_unica"] = sorted(E4.corte.unique().tolist())
out["previsoes_e4_duplicadas"] = int(E4.duplicated(["braco","h","data_origem"]).sum())
(SAIDA/"v1_v2_resumo.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str))
print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
print(v1.drop(columns=["previsto_meu_resposta"]).to_string())
