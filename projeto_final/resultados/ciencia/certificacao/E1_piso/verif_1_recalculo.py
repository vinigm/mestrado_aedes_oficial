"""Verificacoes 1, 3 e 4a: recalcula, so com pandas/numpy, E1 (MAE, cobertura, decisao, trava 3) e os 40 MAE e pisos do piso de ruido,
a partir das previsoes SALVAS. Nao treina nada."""

import json

import numpy as np
import pandas as pd

from comum_cert import (
    CAMINHO_DA_REFERENCIA,
    COLUNA_ALVO_DATA,
    COLUNA_ORIGEM,
    FIM_DA_CALIBRACAO,
    FIM_DA_JANELA,
    INICIO_DA_JANELA,
    PASTA_DA_CERTIFICACAO,
    PASTA_DA_CIENCIA,
    PASTA_DO_GABARITO,
    ler_referencia,
    mae,
)

saida: dict[str, object] = {}
QUANTIS = [0.5, 0.7, 0.8, 0.85, 0.9]
HORIZONTES = [1, 4, 8, 12]

# ---------------- E1 ----------------
previsoes_e1 = pd.read_csv(
    PASTA_DA_CIENCIA / "E1_quantil" / "previsoes.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA]
)
saida["e1_linhas"] = int(len(previsoes_e1))
saida["e1_data_alvo_maxima"] = str(previsoes_e1[COLUNA_ALVO_DATA].max().date())
saida["e1_data_alvo_minima"] = str(previsoes_e1[COLUNA_ALVO_DATA].min().date())
saida["e1_tem_alvo_depois_da_calibracao"] = bool((previsoes_e1[COLUNA_ALVO_DATA] > FIM_DA_CALIBRACAO).any())
saida["e1_ausentes_ou_infinitos"] = int((~np.isfinite(previsoes_e1[["real", "previsto"]].to_numpy())).sum())
saida["e1_duplicatas_quantil_h_alvo"] = int(previsoes_e1.duplicated(["quantil", "h", COLUNA_ALVO_DATA]).sum())
saida["e1_origem_mais_h_igual_alvo"] = bool(
    (
        (previsoes_e1[COLUNA_ORIGEM] + pd.to_timedelta(7 * previsoes_e1["h"], unit="D"))
        == previsoes_e1[COLUNA_ALVO_DATA]
    ).all()
)

tabela_metricas: list[dict[str, object]] = []
mae_medio_por_quantil: dict[float, float] = {}
for quantil in QUANTIS:
    maes_do_quantil: list[float] = []
    for horizonte in HORIZONTES:
        mascara = (previsoes_e1["quantil"] == quantil) & (previsoes_e1["h"] == horizonte)
        recorte = previsoes_e1.loc[mascara]
        reais = recorte["real"].to_numpy(dtype=float)
        previstos = recorte["previsto"].to_numpy(dtype=float)
        mae_da_celula = mae(reais, previstos)
        cobertura = float(np.mean(reais > previstos))
        maes_do_quantil.append(mae_da_celula)
        tabela_metricas.append(
            {"quantil": quantil, "h": horizonte, "n": len(recorte), "mae": mae_da_celula, "cobertura": cobertura}
        )
    mae_medio_por_quantil[quantil] = float(np.mean(maes_do_quantil))
tabela_metricas_df = pd.DataFrame(tabela_metricas)

metricas_salvas = pd.read_csv(PASTA_DA_CIENCIA / "E1_quantil" / "metricas.csv")
juncao = tabela_metricas_df.merge(metricas_salvas, on=["quantil", "h"], suffixes=("_meu", "_salvo"))
saida["e1_metricas_linhas_comparadas"] = int(len(juncao))
saida["e1_dif_max_mae"] = float((juncao["mae_meu"] - juncao["mae_salvo"]).abs().max())
saida["e1_dif_max_cobertura"] = float((juncao["cobertura_meu"] - juncao["cobertura_salvo"]).abs().max())
saida["e1_n_igual"] = bool((juncao["n_meu"] == juncao["n_salvo"]).all())
saida["e1_n_por_h_q085"] = {
    int(h): int(n) for h, n in zip(tabela_metricas_df.query("quantil == 0.85")["h"], tabela_metricas_df.query("quantil == 0.85")["n"])
}

# decisao pela regra da secao 3 (reimplementada)
mae_referencia = mae_medio_por_quantil[0.85]
melhor = min(mae_medio_por_quantil, key=mae_medio_por_quantil.get)
mae_melhor = mae_medio_por_quantil[melhor]
ganho = (mae_referencia - mae_melhor) / mae_referencia
quantil_escolhido = melhor if (ganho >= 0.02 and melhor != 0.85) else 0.85
saida["e1_mae_medio_por_quantil_meu"] = {str(q): v for q, v in mae_medio_por_quantil.items()}
saida["e1_melhor_meu"] = melhor
saida["e1_ganho_meu"] = ganho
saida["e1_escolhido_meu"] = quantil_escolhido
# vantagem de cada candidato sobre 0,85, para ver se algum chega perto de 2%
saida["e1_ganho_de_cada_candidato_sobre_085"] = {
    str(q): (mae_referencia - v) / mae_referencia for q, v in mae_medio_por_quantil.items()
}
decisao = json.loads((PASTA_DA_CIENCIA / "E1_quantil" / "decisao.json").read_text())
saida["e1_decisao_json_bate"] = bool(
    decisao["melhor_quantil"] == melhor
    and decisao["quantil_escolhido"] == quantil_escolhido
    and abs(decisao["ganho_relativo"] - ganho) < 1e-12
    and all(abs(decisao["mae_medio_por_quantil"][f"{q:.2f}"] - mae_medio_por_quantil[q]) < 1e-9 for q in QUANTIS)
    and decisao["n_por_horizonte"] == {"1": 193, "4": 190, "8": 186, "12": 182}
)

# ---------------- Trava 3 ----------------
referencia = ler_referencia()
saida["referencia_bracos"] = sorted(referencia["braco"].unique().tolist())
ref_f5 = referencia.loc[
    (referencia["braco"] == "referencia")
    & referencia["h"].isin(HORIZONTES)
    & (referencia[COLUNA_ALVO_DATA] <= FIM_DA_CALIBRACAO)
]
q085 = previsoes_e1.loc[previsoes_e1["quantil"] == 0.85]
cruzado = q085.merge(ref_f5, on=["h", COLUNA_ALVO_DATA], how="outer", suffixes=("_e1", "_ref"), indicator=True)
saida["trava3_linhas_e1"] = int(len(q085))
saida["trava3_linhas_ref"] = int(len(ref_f5))
saida["trava3_comuns"] = int((cruzado["_merge"] == "both").sum())
saida["trava3_so_e1"] = int((cruzado["_merge"] == "left_only").sum())
saida["trava3_so_ref"] = int((cruzado["_merge"] == "right_only").sum())
comuns = cruzado.loc[cruzado["_merge"] == "both"]
saida["trava3_dif_max_previsto"] = float((comuns["previsto_e1"] - comuns["previsto_ref"]).abs().max())
saida["trava3_dif_max_real"] = float((comuns["real_e1"] - comuns["real_ref"]).abs().max())
saida["trava3_dif_max_data_origem"] = int((comuns[f"{COLUNA_ORIGEM}_e1"] != comuns[f"{COLUNA_ORIGEM}_ref"]).sum())

# triangulacao com o gabarito do codigo ANTIGO (previsoes_referencia.csv, sem data_origem)
antigo = pd.read_csv(PASTA_DO_GABARITO / "previsoes_referencia.csv", parse_dates=[COLUNA_ALVO_DATA])
antigo_cal = antigo.loc[(antigo["braco"] == "referencia") & antigo["h"].isin(HORIZONTES) & (antigo[COLUNA_ALVO_DATA] <= FIM_DA_CALIBRACAO)]
cruz_antigo = q085.merge(antigo_cal, on=["h", COLUNA_ALVO_DATA], how="outer", suffixes=("_e1", "_antigo"), indicator=True)
saida["gabarito_antigo_comuns"] = int((cruz_antigo["_merge"] == "both").sum())
saida["gabarito_antigo_so_e1"] = int((cruz_antigo["_merge"] == "left_only").sum())
saida["gabarito_antigo_so_gab"] = int((cruz_antigo["_merge"] == "right_only").sum())
ambos = cruz_antigo.loc[cruz_antigo["_merge"] == "both"]
saida["gabarito_antigo_dif_max_previsto"] = float((ambos["previsto_e1"] - ambos["previsto_antigo"]).abs().max())

# MAE de calibracao da PROPRIA referencia (independe da E1)
maes_ref_cal: dict[int, float] = {}
n_ref_cal: dict[int, int] = {}
for horizonte in HORIZONTES:
    recorte = ref_f5.loc[ref_f5["h"] == horizonte]
    maes_ref_cal[horizonte] = mae(recorte["real"].to_numpy(), recorte["previsto"].to_numpy())
    n_ref_cal[horizonte] = len(recorte)
saida["ancora_mae_cal_ref_f5"] = {str(h): v for h, v in maes_ref_cal.items()}
saida["ancora_n_cal_ref_f5"] = {str(h): v for h, v in n_ref_cal.items()}
saida["ancora_mae_cal_ref_f5_media"] = float(np.mean(list(maes_ref_cal.values())))

# ---------------- Ancoras da referencia na janela ----------------
def mae_na_janela(previsoes: pd.DataFrame, braco: str, horizonte: int) -> tuple[int, float]:
    recorte = previsoes.loc[
        (previsoes["braco"] == braco)
        & (previsoes["h"] == horizonte)
        & (previsoes[COLUNA_ALVO_DATA] >= INICIO_DA_JANELA)
        & (previsoes[COLUNA_ALVO_DATA] <= FIM_DA_JANELA)
    ]
    return len(recorte), mae(recorte["real"].to_numpy(), recorte["previsto"].to_numpy())


ancoras_janela = {}
for braco in ("referencia", "HistGB_folha20_M1"):
    for horizonte in HORIZONTES:
        n, valor = mae_na_janela(referencia, braco, horizonte)
        ancoras_janela[f"{braco}_h{horizonte}"] = (n, valor)
saida["ancoras_janela_referencia"] = {k: [v[0], v[1]] for k, v in ancoras_janela.items()}
saida["referencia_previsoes_por_folha_h1_h12"] = {
    braco: [
        int(((referencia["braco"] == braco) & (referencia["h"] == 1)).sum()),
        int(((referencia["braco"] == braco) & (referencia["h"] == 12)).sum()),
    ]
    for braco in ("referencia", "HistGB_folha20_M1")
}

# ---------------- Piso ----------------
previsoes_piso = pd.read_csv(
    PASTA_DA_CIENCIA / "piso_de_ruido" / "previsoes.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA]
)
saida["piso_linhas"] = int(len(previsoes_piso))
saida["piso_ausentes_ou_infinitos"] = int((~np.isfinite(previsoes_piso[["real", "previsto"]].to_numpy())).sum())
linhas_piso: list[dict[str, object]] = []
mapa_braco = {5: "referencia", 20: "HistGB_folha20_M1"}
for perturbacao in ("csv", "s1", "s2", "s3", "s4"):
    for folha in (5, 20):
        for horizonte in HORIZONTES:
            recorte = previsoes_piso.loc[
                (previsoes_piso["perturbacao"] == perturbacao)
                & (previsoes_piso["folha"] == folha)
                & (previsoes_piso["h"] == horizonte)
                & (previsoes_piso[COLUNA_ALVO_DATA] >= INICIO_DA_JANELA)
                & (previsoes_piso[COLUNA_ALVO_DATA] <= FIM_DA_JANELA)
            ]
            n_ref, mae_ref = ancoras_janela[f"{mapa_braco[folha]}_h{horizonte}"]
            mae_pert = mae(recorte["real"].to_numpy(), recorte["previsto"].to_numpy())
            linhas_piso.append(
                {
                    "perturbacao": perturbacao,
                    "folha": folha,
                    "h": horizonte,
                    "n": len(recorte),
                    "mae": mae_pert,
                    "mae_ref": mae_ref,
                    "delta_abs": abs(mae_pert - mae_ref),
                }
            )
meus_maes = pd.DataFrame(linhas_piso)
meus_maes.to_csv(PASTA_DA_CERTIFICACAO / "piso_mae_recalculado.csv", index=False)
saida["piso_n_todos_102"] = bool((meus_maes["n"] == 102).all())
saida["piso_celulas"] = int(len(meus_maes))
salvo = pd.read_csv(PASTA_DA_CIENCIA / "piso_de_ruido" / "mae_por_perturbacao.csv")
cruz = meus_maes.merge(salvo, on=["perturbacao", "folha", "h"], suffixes=("_meu", "_salvo"))
saida["piso_dif_max_mae"] = float((cruz["mae_meu"] - cruz["mae_salvo"]).abs().max())
saida["piso_dif_max_delta"] = float((cruz["delta_abs"] - cruz["delta"]).abs().max())
saida["piso_dif_max_mae_ref"] = float((cruz["mae_ref"] - cruz["mae_referencia"]).abs().max())

meu_piso = (
    meus_maes.groupby(["folha", "h"], as_index=False)["delta_abs"].max().rename(columns={"delta_abs": "piso"})
)
piso_salvo = pd.read_csv(PASTA_DA_CIENCIA / "piso_de_ruido" / "piso.csv")
cruz_piso = meu_piso.merge(piso_salvo, on=["folha", "h"])
saida["piso_dif_max_piso"] = float((cruz_piso["piso"] - cruz_piso["piso_de_ruido"]).abs().max())
saida["piso_dif_max_2x"] = float((2 * cruz_piso["piso"] - cruz_piso["duas_vezes_o_piso"]).abs().max())
idx_max = meus_maes.loc[meus_maes.groupby(["folha", "h"])["delta_abs"].idxmax()]
saida["piso_perturbacao_do_maximo_bate"] = bool(
    all(
        linha.perturbacao == piso_salvo.loc[(piso_salvo["folha"] == linha.folha) & (piso_salvo["h"] == linha.h), "perturbacao_do_maximo"].iloc[0]
        for linha in idx_max.itertuples()
    )
)
saida["piso_meu"] = {f"f{int(r.folha)}_h{int(r.h)}": r.piso for r in meu_piso.itertuples()}

# referencia != perturbada: checar que a janela da referencia e a mesma do piso (n=102) e sinal dos deltas
saida["piso_delta_assinado_extremos"] = {
    "min": float((meus_maes["mae"] - meus_maes["mae_ref"]).min()),
    "max": float((meus_maes["mae"] - meus_maes["mae_ref"]).max()),
}

(PASTA_DA_CERTIFICACAO / "verif_1_recalculo.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False, default=str))
print(json.dumps(saida, indent=2, ensure_ascii=False, default=str))
