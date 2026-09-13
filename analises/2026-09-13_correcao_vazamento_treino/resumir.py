"""
Reconstroi grid_resumo.csv e grid_ranking_completo.csv a partir de um CSV de
previsoes brutas (colunas: h, data_alvo, real, pred, algoritmo, perda, conjunto
[+ colunas extras opcionais, ignoradas: n_treino, n_treino_original,
pos_ranking_30_08]).

Uso:
    python3 resumir.py <caminho_previsoes.csv> <dir_saida>

Gera em <dir_saida>: resumo_reconstruido.csv, ranking_reconstruido.csv.

Formulas usadas (confirmadas por igualdade exata contra
2026-08-30_grid_completo/saidas/grid_resumo.csv e grid_ranking_completo.csv,
ver bloco de verificacao no fim do arquivo):

- periodo:      "avaliacao" se data_alvo > 2023-12-31, senao "calibracao".
- n:            contagem de linhas do grupo (algoritmo, perda, conjunto, h, periodo).
- MAE:          media(|pred - real|) no grupo.
- R2:           1 - soma((real-pred)^2) / soma((real-media_real)^2) no grupo.
- vies_pico:    media(pred - real) restrito a real > LIMITE_PICO (=100) no grupo.
- captura_pico: media(pred) / media(real) restrito a real > LIMITE_PICO (=100)
                no grupo (coluna NOVA, pedida na tarefa; nao existe no
                grid_resumo.csv original).
- MAE_cal (ranking): media das 4 MAE de periodo=calibracao dos horizontes
                h em {1,4,8,12}, por (algoritmo, perda, conjunto).
- MAE_aval, R2_aval, vies_pico (ranking): mesma media, mas sobre periodo=avaliacao.
- dif_%:        (MAE_cal / MAE_cal_do_1o_colocado - 1) * 100.
- pos:          ranking crescente de MAE_cal (1 = menor MAE_cal).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

LIMITE_PICO = 100
HORIZONTES_RANKING = [1, 4, 8, 12]
DATA_CORTE_AVALIACAO = pd.Timestamp("2023-12-31")
CHAVES_CONFIG = ["algoritmo", "perda", "conjunto"]


def classificar_periodo(data_alvo: pd.Series) -> pd.Series:
    """Rotula cada linha como 'avaliacao' (apos o corte) ou 'calibracao'."""
    return np.where(data_alvo > DATA_CORTE_AVALIACAO, "avaliacao", "calibracao")


def calcular_r2(real: pd.Series, pred: pd.Series) -> float:
    """R2 = 1 - soma(erro^2) / soma((real - media_real)^2)."""
    soma_quadrados_residuos = np.sum((real - pred) ** 2)
    soma_quadrados_totais = np.sum((real - real.mean()) ** 2)
    return 1 - soma_quadrados_residuos / soma_quadrados_totais


def calcular_metricas_grupo(grupo: pd.DataFrame) -> pd.Series:
    """Aplica as formulas de MAE/R2/vies_pico/captura_pico a um grupo."""
    real = grupo["real"]
    pred = grupo["pred"]

    mascara_pico = real > LIMITE_PICO
    real_pico = real[mascara_pico]
    pred_pico = pred[mascara_pico]

    return pd.Series(
        {
            "n": len(grupo),
            "MAE": np.mean(np.abs(pred - real)),
            "R2": calcular_r2(real, pred),
            "vies_pico": np.mean(pred_pico - real_pico),
            "captura_pico": pred_pico.mean() / real_pico.mean(),
        }
    )


def construir_resumo(previsoes: pd.DataFrame) -> pd.DataFrame:
    previsoes = previsoes.copy()
    previsoes["periodo"] = classificar_periodo(previsoes["data_alvo"])

    resumo = (
        previsoes.groupby(CHAVES_CONFIG + ["h", "periodo"], sort=False)
        .apply(calcular_metricas_grupo, include_groups=False)
        .reset_index()
    )
    resumo["n"] = resumo["n"].astype(int)
    colunas_finais = CHAVES_CONFIG + ["h", "periodo", "n", "MAE", "R2", "vies_pico", "captura_pico"]
    return resumo[colunas_finais]


def construir_ranking(resumo: pd.DataFrame) -> pd.DataFrame:
    calibracao = resumo[
        (resumo["periodo"] == "calibracao") & (resumo["h"].isin(HORIZONTES_RANKING))
    ]
    avaliacao = resumo[
        (resumo["periodo"] == "avaliacao") & (resumo["h"].isin(HORIZONTES_RANKING))
    ]

    medias_cal = calibracao.groupby(CHAVES_CONFIG)["MAE"].mean().rename("MAE_cal")
    medias_aval = avaliacao.groupby(CHAVES_CONFIG).agg(
        MAE_aval=("MAE", "mean"),
        R2_aval=("R2", "mean"),
        vies_pico=("vies_pico", "mean"),
        captura_pico=("captura_pico", "mean"),
    )

    ranking = pd.concat([medias_cal, medias_aval], axis=1).reset_index()
    ranking = ranking.sort_values("MAE_cal", ascending=True).reset_index(drop=True)
    ranking.insert(0, "pos", ranking.index + 1)

    mae_cal_primeiro = ranking.loc[0, "MAE_cal"]
    ranking["dif_%"] = (ranking["MAE_cal"] / mae_cal_primeiro - 1) * 100

    colunas_finais = [
        "pos", "algoritmo", "perda", "conjunto",
        "MAE_cal", "dif_%", "MAE_aval", "R2_aval", "vies_pico", "captura_pico",
    ]
    return ranking[colunas_finais]


def gerar_tabelas(caminho_previsoes: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    previsoes = pd.read_csv(caminho_previsoes, parse_dates=["data_alvo"])
    resumo = construir_resumo(previsoes)
    ranking = construir_ranking(resumo)
    return resumo, ranking


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python3 resumir.py <previsoes.csv> <dir_saida>")

    caminho_entrada = sys.argv[1]
    dir_saida = Path(sys.argv[2])
    dir_saida.mkdir(parents=True, exist_ok=True)

    df_resumo, df_ranking = gerar_tabelas(caminho_entrada)

    caminho_resumo = dir_saida / "resumo_reconstruido.csv"
    caminho_ranking = dir_saida / "ranking_reconstruido.csv"
    df_resumo.to_csv(caminho_resumo, index=False)
    df_ranking.to_csv(caminho_ranking, index=False)

    print(f"resumo:  {caminho_resumo} ({len(df_resumo)} linhas)")
    print(f"ranking: {caminho_ranking} ({len(df_ranking)} linhas)")
