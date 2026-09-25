"""Leituras descritivas da seção 4 da pré-declaração, sem teste estatístico.

O combinador grava as famílias J1, J2 e J3 e os pesos médios do ensemble, mas
não gravava as demais leituras que a pré-declaração pede. Este script as
calcula a partir de `saidas/previsoes_por_braco.csv`, sem treinar nada.

Roda com o Python do projeto ou com o ambiente isolado: só usa pandas e numpy.
"""

import pathlib

import numpy as np
import pandas as pd

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
ARQUIVO_DE_PREVISOES = PASTA_DESTE_ARQUIVO / "saidas" / "previsoes_por_braco.csv"
ARQUIVO_DE_SAIDA = PASTA_DESTE_ARQUIVO / "saidas" / "leituras_descritivas.csv"

INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
INICIO_DA_CALIBRACAO_EPIDEMICA = pd.Timestamp("2022-01-01")
QUANTIL_DO_PROJETO = 0.85
LIMIAR_DE_SEMANA_EPIDEMICA = 100


def calcular_perda_quantilica(reais: pd.Series, previstos: pd.Series) -> float:
    """Perda quantílica 0,85: pune mais a previsão que fica abaixo do real."""
    diferenca = reais - previstos
    perda_acima = QUANTIL_DO_PROJETO * diferenca
    perda_abaixo = (QUANTIL_DO_PROJETO - 1.0) * diferenca
    return float(np.mean(np.maximum(perda_acima, perda_abaixo)))


def resumir_um_recorte(recorte: pd.DataFrame) -> dict[str, float]:
    """MAE, perda quantílica, cobertura do q0,85 e n de um recorte de semanas."""
    erro_absoluto = (recorte["real"] - recorte["previsto"]).abs()
    real_abaixo_da_previsao = recorte["real"] <= recorte["previsto"]
    return {
        "mae": float(erro_absoluto.mean()),
        "perda_quantilica_085": calcular_perda_quantilica(recorte["real"], recorte["previsto"]),
        "cobertura_q085": float(real_abaixo_da_previsao.mean()),
        "n": int(len(recorte)),
    }


def montar_leituras(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por braço, horizonte e recorte de semanas."""
    mascara_avaliacao = previsoes["data_alvo"] >= INICIO_DA_AVALIACAO
    mascara_calibracao_epidemica = (
        (previsoes["data_alvo"] >= INICIO_DA_CALIBRACAO_EPIDEMICA)
        & (previsoes["data_alvo"] < INICIO_DA_AVALIACAO)
    )

    linhas: list[dict[str, object]] = []
    for (braco, horizonte), grupo in previsoes.groupby(["braco", "h"]):
        recortes: dict[str, pd.DataFrame] = {
            "avaliacao": grupo[mascara_avaliacao.loc[grupo.index]],
            "calibracao_epidemica_2022_2023": grupo[mascara_calibracao_epidemica.loc[grupo.index]],
        }

        avaliacao = recortes["avaliacao"]
        recortes["avaliacao_real_maior_ou_igual_100"] = avaliacao[avaliacao["real"] >= LIMIAR_DE_SEMANA_EPIDEMICA]
        recortes["avaliacao_real_menor_que_100"] = avaliacao[avaliacao["real"] < LIMIAR_DE_SEMANA_EPIDEMICA]

        anos_do_alvo = grupo["data_alvo"].dt.year
        for ano in sorted(anos_do_alvo.unique()):
            recortes[f"ano_{ano}"] = grupo[anos_do_alvo == ano]

        for nome_do_recorte, recorte in recortes.items():
            if recorte.empty:
                continue
            resumo = resumir_um_recorte(recorte)
            linha = {"braco": braco, "h": horizonte, "recorte": nome_do_recorte}
            linha.update(resumo)
            linhas.append(linha)

    return pd.DataFrame(linhas)


def main() -> None:
    """Lê as previsões, calcula as leituras e grava o CSV."""
    previsoes = pd.read_csv(ARQUIVO_DE_PREVISOES, parse_dates=["data_alvo"])
    leituras = montar_leituras(previsoes)
    leituras.to_csv(ARQUIVO_DE_SAIDA, index=False)
    print(f"Gravado: {ARQUIVO_DE_SAIDA.name} ({len(leituras)} linhas)")


if __name__ == "__main__":
    main()
