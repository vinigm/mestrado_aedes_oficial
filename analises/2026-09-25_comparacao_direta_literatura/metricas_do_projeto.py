"""Métricas do projeto nas mesmas unidades que a literatura reporta.

A comparação com artigos publicados não pode usar o MAE em casos por semana:
Singapura tem centenas de casos por semana, Porto Alegre tem semanas com zero.
Este script calcula, sobre previsões já gravadas, as métricas relativas que os
artigos usam: erro percentual (MAPE), erro percentual simétrico (sMAPE), erro
relativo ao total (WAPE) e R², em casos e em log.

Não treina nada. Só lê previsões existentes.
"""

import dataclasses
import pathlib

import numpy as np
import pandas as pd

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DE_ANALISES = PASTA_DESTE_ARQUIVO.parent
ARQUIVO_BLOCO_7 = (
    PASTA_DE_ANALISES / "2026-09-23_bateria_noturna" / "bloco_7_vetor_com_folha_20" / "saidas"
    / "previsoes_por_braco.csv"
)
ARQUIVO_FUNDACAO = PASTA_DE_ANALISES / "2026-09-25_modelos_de_fundacao" / "saidas" / "previsoes_por_braco.csv"
ARQUIVO_TABELA = (
    PASTA_DE_ANALISES.parent / "modelagem_aedes" / "dados" / "entradas" / "tabela_modelagem" / "tabela_final.csv"
)
ARQUIVO_DE_SAIDA = PASTA_DESTE_ARQUIVO / "metricas_do_projeto.csv"

INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
HORIZONTES = (1, 4, 8, 12)
SEMANAS_DO_PASSO_SAZONAL = 52

# O MAPE divide pelo real: semana com zero caso dá divisão por zero, e semana
# com 2 casos transforma um erro de 20 em 1.000%. Por isso ele é reportado em
# três recortes, e o de semanas epidêmicas é o comparável a séries como a de
# Singapura, que têm centenas de casos toda semana.
LIMIAR_SEMANA_COM_CASO = 1
LIMIAR_SEMANA_EPIDEMICA = 100


@dataclasses.dataclass(frozen=True)
class MetricasRelativas:
    """Métricas de erro que independem da escala da série."""

    mape_semanas_com_caso: float
    mape_semanas_epidemicas: float
    smape: float
    wape: float
    r2_casos: float
    r2_log: float
    n: int


def calcular_r2(reais: np.ndarray, previstos: np.ndarray) -> float:
    """R² clássico: 1 − soma dos erros ao quadrado / variância do real."""
    residuo = np.sum((reais - previstos) ** 2)
    variancia = np.sum((reais - np.mean(reais)) ** 2)
    return float(1.0 - residuo / variancia)


def calcular_mape(reais: np.ndarray, previstos: np.ndarray, limiar_minimo: float) -> float:
    """Erro percentual médio, só nas semanas com real ≥ limiar."""
    mascara = reais >= limiar_minimo
    erro_percentual = np.abs(reais[mascara] - previstos[mascara]) / reais[mascara]
    return float(100.0 * np.mean(erro_percentual))


def calcular_smape(reais: np.ndarray, previstos: np.ndarray) -> float:
    """Erro percentual simétrico, de 0 a 200%. Semanas com real e previsto zero entram como 0."""
    soma_absoluta = np.abs(reais) + np.abs(previstos)
    erro_simetrico = np.zeros_like(reais, dtype=float)
    mascara_com_valor = soma_absoluta > 0
    erro_simetrico[mascara_com_valor] = (
        2.0 * np.abs(reais[mascara_com_valor] - previstos[mascara_com_valor]) / soma_absoluta[mascara_com_valor]
    )
    return float(100.0 * np.mean(erro_simetrico))


def calcular_wape(reais: np.ndarray, previstos: np.ndarray) -> float:
    """Soma dos erros absolutos dividida pela soma dos casos reais, em %."""
    return float(100.0 * np.sum(np.abs(reais - previstos)) / np.sum(reais))


def calcular_metricas(reais: np.ndarray, previstos: np.ndarray) -> MetricasRelativas:
    """Todas as métricas relativas de um conjunto de previsões pareadas.

    O HistGB quantílico às vezes prevê valor levemente negativo. Só o R² em
    log corta em zero, porque log1p de valor menor que −1 não existe; as
    demais métricas usam a previsão como ela é.
    """
    previstos_sem_negativo = np.maximum(previstos, 0.0)
    return MetricasRelativas(
        mape_semanas_com_caso=calcular_mape(reais, previstos, LIMIAR_SEMANA_COM_CASO),
        mape_semanas_epidemicas=calcular_mape(reais, previstos, LIMIAR_SEMANA_EPIDEMICA),
        smape=calcular_smape(reais, previstos),
        wape=calcular_wape(reais, previstos),
        r2_casos=calcular_r2(reais, previstos),
        r2_log=calcular_r2(np.log1p(reais), np.log1p(previstos_sem_negativo)),
        n=int(len(reais)),
    )


def carregar_previsoes_pareadas() -> pd.DataFrame:
    """Uma linha por (h, data_alvo), com o real e cada previsão numa coluna."""
    bloco_7 = pd.read_csv(ARQUIVO_BLOCO_7, parse_dates=["data_alvo"])
    fundacao = pd.read_csv(ARQUIVO_FUNDACAO, parse_dates=["data_alvo"])
    tabela = pd.read_csv(ARQUIVO_TABELA, parse_dates=["data_inicio_semana_epidemi"])
    casos_por_semana = tabela.set_index("data_inicio_semana_epidemi")["casos_confirmados"]

    adotado = bloco_7[bloco_7["braco"] == "referencia"][["h", "data_alvo", "real", "previsto"]]
    adotado = adotado.rename(columns={"previsto": "cenario_adotado"})
    folha_20 = bloco_7[bloco_7["braco"] == "HistGB_folha20_M1"][["h", "data_alvo", "previsto"]]
    folha_20 = folha_20.rename(columns={"previsto": "B0_folha_20"})

    chronos = fundacao[fundacao["braco"] == "c2_casos"][["h", "data_alvo", "q085", "q050"]]
    chronos = chronos.rename(columns={"q085": "chronos2_q085", "q050": "chronos2_mediana"})

    pareadas = adotado.merge(folha_20, on=["h", "data_alvo"]).merge(chronos, on=["h", "data_alvo"])
    semana_um_ano_antes = pareadas["data_alvo"] - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    pareadas["regua_sazonal"] = casos_por_semana.reindex(semana_um_ano_antes).to_numpy()
    return pareadas


def montar_tabela_de_metricas(pareadas: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por modelo e horizonte, na avaliação 2024+."""
    avaliacao = pareadas[pareadas["data_alvo"] >= INICIO_DA_AVALIACAO]
    modelos = ["cenario_adotado", "B0_folha_20", "chronos2_q085", "chronos2_mediana", "regua_sazonal"]

    linhas: list[dict[str, object]] = []
    for horizonte in HORIZONTES:
        do_horizonte = avaliacao[avaliacao["h"] == horizonte]
        reais = do_horizonte["real"].to_numpy(dtype=float)
        for modelo in modelos:
            previstos = do_horizonte[modelo].to_numpy(dtype=float)
            metricas = calcular_metricas(reais, previstos)
            linha = {"modelo": modelo, "h": horizonte}
            linha.update(dataclasses.asdict(metricas))
            linhas.append(linha)

    return pd.DataFrame(linhas)


def main() -> None:
    """Calcula e grava as métricas relativas do projeto."""
    pareadas = carregar_previsoes_pareadas()
    tabela = montar_tabela_de_metricas(pareadas)
    tabela.to_csv(ARQUIVO_DE_SAIDA, index=False)
    print(tabela.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
