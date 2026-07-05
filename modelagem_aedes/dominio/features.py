"""

Aqui o programa monta as colunas que ajudam a prever o futuro: valores de
semanas passadas, medias das ultimas semanas e um jeito de marcar a epoca
do ano.

Essas colunas sao usadas por todos os experimentos de cada cidade — antes
cada script tinha sua propria copia desse calculo; agora existe UM lugar
so, aqui.

"""

import numpy as np
import pandas as pd

from config import settings

# Colunas que ganham uma copia atrasada de 1, 2, 3 e 4 semanas (quando existirem na tabela).
COLUNAS_PARA_LAG = [
    "casos",
    "aedes_aegypti_por_armadilha",
    "temp_media",
    "precip_total_mm",
    "orvalho_media",
    "umid_media",
    "pressao_media",
]
LAGS_SEMANAS = [1, 2, 3, 4]
JANELA_MEDIA_MOVEL_SEMANAS = 4


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """

    Calcula a media das ultimas 4 semanas de uma serie que pertence a um
    unico bloco de dados (uma fonte).

    Isso e usado no calculo feito grupo por grupo, pra que a media nao
    misture dados dos dois blocos diferentes (o bloco antigo da Marilia,
    de 2019 a 2023, e o bloco novo da raspagem, de 2025 em diante).

    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()



def selecionar_colunas_por_prefixo(
    dados: pd.DataFrame,
    prefixos: tuple[str, ...],
) -> list[str]:
    """

    Devolve os nomes das colunas que comecam com um dos prefixos informados.

    A ordem segue a ordem das colunas na tabela, pra que a lista de colunas
    usada pelo modelo seja sempre a mesma (a ordem importa: treinar o
    modelo e usar ele pra prever precisam usar exatamente as mesmas
    colunas, na mesma ordem).

    """
    colunas_selecionadas = []
    for nome_coluna in dados.columns:
        if nome_coluna.startswith(prefixos):
            colunas_selecionadas.append(nome_coluna)
    return colunas_selecionadas



def construir_features_temporais(
    dados: pd.DataFrame,
    coluna_fonte: str = "fonte",
) -> pd.DataFrame:
    """

    Cria as colunas de semanas passadas, as medias moveis e a marcacao da
    epoca do ano — a mesma receita usada nos Modelos 1 a 5.

    Todas essas colunas sao calculadas POR BLOCO (separando pela coluna de
    fonte), pra que os valores de semanas passadas e as medias nunca
    misturem dados dos dois blocos diferentes.

    Args:
        dados: Tabela semanal com, no minimo, a coluna 'semana' e as
            colunas de origem listadas em COLUNAS_PARA_LAG que estiverem
            presentes.
        coluna_fonte: Coluna que diz de qual bloco de dados cada linha veio.

    Returns:
        Uma COPIA da tabela com as colunas novas adicionadas. A tabela
        original nao e alterada.

    """
    dados_com_features = dados.copy()
    grupos_por_fonte = dados_com_features.groupby(coluna_fonte, group_keys=False)

    for coluna_origem in COLUNAS_PARA_LAG:
        if coluna_origem in dados_com_features.columns:
            for numero_de_semanas in LAGS_SEMANAS:
                nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
                dados_com_features[nome_coluna_lag] = grupos_por_fonte[coluna_origem].shift(
                    numero_de_semanas
                )

    if "casos" in dados_com_features.columns:
        dados_com_features["casos_mm4"] = grupos_por_fonte["casos"].transform(
            media_movel_4_semanas
        )
    if "aedes_aegypti_por_armadilha" in dados_com_features.columns:
        dados_com_features["vetor_mm4"] = grupos_por_fonte[
            "aedes_aegypti_por_armadilha"
        ].transform(media_movel_4_semanas)

    angulo_sazonal = 2 * np.pi * dados_com_features["semana"] / settings.SEMANAS_POR_ANO
    dados_com_features["sem_sin"] = np.sin(angulo_sazonal)
    dados_com_features["sem_cos"] = np.cos(angulo_sazonal)
    return dados_com_features



def construir_alvo_horizonte(
    dados: pd.DataFrame,
    coluna_alvo: str,
    horizonte: int,
    coluna_fonte: str = "fonte",
) -> pd.DataFrame:
    """

    Desloca a coluna do que a gente quer prever pra frente no tempo, tantas
    semanas quanto for o horizonte escolhido, e marca a epoca do ano dessa
    semana futura.

    Cria a coluna 'y_h' (o valor a prever, la na frente, dentro de cada
    bloco de fonte) e o sin/cos da semana que sera prevista. Usada tanto na
    escolha das colunas do modelo quanto no teste que treina no passado e
    preve o futuro, semana a semana.

    Args:
        dados: Tabela semanal com as colunas 'semana' e a coluna do que
            queremos prever.
        coluna_alvo: Nome da coluna que sera deslocada pra frente no tempo.
        horizonte: Quantas semanas a frente a gente quer prever.
        coluna_fonte: Coluna que diz de qual bloco de dados cada linha veio.

    Returns:
        Uma COPIA da tabela com as colunas y_h, alvo_sin e alvo_cos.

    """
    grupos_por_fonte = dados.groupby(coluna_fonte, group_keys=False)
    resultado = dados.copy()
    resultado["y_h"] = grupos_por_fonte[coluna_alvo].shift(-horizonte)
    semana_alvo = grupos_por_fonte["semana"].shift(-horizonte)
    angulo_sazonal_alvo = 2 * np.pi * semana_alvo / settings.SEMANAS_POR_ANO
    resultado["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    resultado["alvo_cos"] = np.cos(angulo_sazonal_alvo)
    return resultado
