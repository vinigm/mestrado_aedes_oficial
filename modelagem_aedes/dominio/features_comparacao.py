"""

Colunas usadas so no experimento de comparacao com a literatura.

Aqui as colunas sao montadas de um jeito diferente dos outros experimentos, de
proposito, pra imitar o metodo dos trabalhos publicados (que usam so clima).
Repare que NAO entra o historico dos proprios casos como coluna: o modelo
"so clima" enxerga apenas clima e a epoca do ano. Depois, o modelo "clima +
mosquito" e o mesmo, so que somando os dados do mosquito.

"""

import numpy as np
import pandas as pd

from config import settings
from dominio.features import media_movel_4_semanas

# As cinco medidas de clima usadas nesta comparacao.
CLIMA_BASE = ["temp_media", "precip_total_mm", "orvalho_media", "umid_media", "pressao_media"]

# Quantas semanas atras entram como colunas (1, 2, 3 e 4 semanas).
LAGS_SEMANAS = [1, 2, 3, 4]


def construir_features_comparacao(
    dados: pd.DataFrame,
    coluna_fonte: str = "fonte",
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """

    Monta as colunas do experimento de comparacao e devolve as duas listas de colunas.

    Pra cada medida de clima, cria as versoes de 1 a 4 semanas atras e a media
    das ultimas 4 semanas. Faz o mesmo com a densidade de mosquito. Tudo por
    bloco de dados (por fonte), pra nao misturar os dois periodos. Adiciona a
    epoca do ano (seno e cosseno da semana).

    Args:
        dados: Tabela semana a semana da cidade.
        coluna_fonte: Coluna que separa os blocos de dados.

    Returns:
        A tabela com as colunas novas, a lista de colunas "so clima" e a lista
        "clima + mosquito".

    """
    tabela = dados.copy()
    grupos_por_fonte = tabela.groupby(coluna_fonte, group_keys=False)

    for coluna_clima in CLIMA_BASE:
        for numero_de_semanas in LAGS_SEMANAS:
            tabela[f"{coluna_clima}_lag{numero_de_semanas}"] = grupos_por_fonte[coluna_clima].shift(
                numero_de_semanas
            )
        tabela[f"{coluna_clima}_mm4"] = grupos_por_fonte[coluna_clima].transform(media_movel_4_semanas)

    tabela["vet"] = tabela["aedes_aegypti_por_armadilha"]
    for numero_de_semanas in LAGS_SEMANAS:
        tabela[f"vet_lag{numero_de_semanas}"] = grupos_por_fonte["vet"].shift(numero_de_semanas)
    tabela["vet_mm4"] = grupos_por_fonte["vet"].transform(media_movel_4_semanas)

    angulo_do_ano = 2 * np.pi * tabela["semana"] / settings.SEMANAS_POR_ANO
    tabela["sin"] = np.sin(angulo_do_ano)
    tabela["cos"] = np.cos(angulo_do_ano)

    colunas_lag_clima = [
        f"{coluna}_lag{k}" for coluna in CLIMA_BASE for k in LAGS_SEMANAS
    ]
    colunas_mm4_clima = [f"{coluna}_mm4" for coluna in CLIMA_BASE]
    features_so_clima = CLIMA_BASE + colunas_lag_clima + colunas_mm4_clima + ["sin", "cos"]

    colunas_lag_vetor = [f"vet_lag{k}" for k in LAGS_SEMANAS]
    features_clima_vetor = features_so_clima + ["vet"] + colunas_lag_vetor + ["vet_mm4"]

    return tabela, features_so_clima, features_clima_vetor
