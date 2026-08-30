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

    Calcula a media das ultimas 4 semanas de uma serie semanal continua.

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



def construir_features_temporais(dados: pd.DataFrame) -> pd.DataFrame:
    """

    Cria as colunas de semanas passadas, as medias moveis e a marcacao da
    epoca do ano — a mesma receita usada nos Modelos 1 a 5.

    Antigamente essas colunas eram calculadas POR BLOCO (separando pela
    coluna 'fonte'), porque a tabela vinha de duas fontes com um buraco de
    tempo real entre elas (a Marilia, 2019-2023, e a raspagem, 2025+): sem
    separar por bloco, a primeira semana da raspagem teria puxado "1 semana
    atras" da ULTIMA semana da Marilia, quase 2 anos antes. Desde a migracao
    pra base certificada da Secretaria (16/08/2026) a serie e uma unica grade
    semanal continua (a raspagem so cobre o pedacinho de 2026 que a
    Secretaria ainda nao mandou, encostado sem buraco na semana anterior da
    Secretaria - ver dominio/montagem_tabela.py); por isso o calculo agora e
    direto, sem separar por bloco. As semanas sem dado (vetor NaN ou casos
    NaN) continuam propagando NaN nos lags e nas medias moveis de forma
    natural (o shift/rolling do pandas ja faz isso sozinho); ninguem
    preenche esse vazio aqui.

    Args:
        dados: Tabela semanal com, no minimo, a coluna 'semana' e as
            colunas de origem listadas em COLUNAS_PARA_LAG que estiverem
            presentes, EM ORDEM CRONOLOGICA (uma linha por semana).

    Returns:
        Uma COPIA da tabela com as colunas novas adicionadas. A tabela
        original nao e alterada.

    """
    dados_com_features = dados.copy()

    for coluna_origem in COLUNAS_PARA_LAG:
        if coluna_origem in dados_com_features.columns:
            for numero_de_semanas in LAGS_SEMANAS:
                nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
                dados_com_features[nome_coluna_lag] = dados_com_features[coluna_origem].shift(
                    numero_de_semanas
                )

    if "casos" in dados_com_features.columns:
        dados_com_features["casos_mm4"] = media_movel_4_semanas(dados_com_features["casos"])
    if "aedes_aegypti_por_armadilha" in dados_com_features.columns:
        dados_com_features["vetor_mm4"] = media_movel_4_semanas(
            dados_com_features["aedes_aegypti_por_armadilha"]
        )

    angulo_sazonal = 2 * np.pi * dados_com_features["semana"] / settings.SEMANAS_POR_ANO
    dados_com_features["sem_sin"] = np.sin(angulo_sazonal)
    dados_com_features["sem_cos"] = np.cos(angulo_sazonal)
    return dados_com_features



def construir_alvo_horizonte(
    dados: pd.DataFrame,
    coluna_alvo: str,
    horizonte: int,
) -> pd.DataFrame:
    """

    Desloca a coluna do que a gente quer prever pra frente no tempo, tantas
    semanas quanto for o horizonte escolhido, e marca a epoca do ano dessa
    semana futura.

    Cria a coluna 'y_h' (o valor a prever, la na frente) e o sin/cos da
    semana que sera prevista. Usada tanto na escolha das colunas do modelo
    quanto no teste que treina no passado e preve o futuro, semana a semana.

    Antes esse deslocamento era feito POR BLOCO de fonte (ver
    construir_features_temporais, que passou pelo mesmo ajuste e explica o
    motivo): a tabela agora e uma serie semanal unica e continua, entao o
    deslocamento e direto, sem separar por bloco. Nas ultimas linhas da
    tabela (tantas quanto o horizonte) nao existe semana futura pra olhar,
    entao y_h fica vazio (NaN) - isso continua exatamente igual.

    Args:
        dados: Tabela semanal com as colunas 'semana' e a coluna do que
            queremos prever, EM ORDEM CRONOLOGICA (uma linha por semana).
        coluna_alvo: Nome da coluna que sera deslocada pra frente no tempo.
        horizonte: Quantas semanas a frente a gente quer prever.

    Returns:
        Uma COPIA da tabela com as colunas y_h, alvo_sin e alvo_cos.

    """
    resultado = dados.copy()
    resultado["y_h"] = dados[coluna_alvo].shift(-horizonte)
    semana_alvo = dados["semana"].shift(-horizonte)
    angulo_sazonal_alvo = 2 * np.pi * semana_alvo / settings.SEMANAS_POR_ANO
    resultado["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    resultado["alvo_cos"] = np.cos(angulo_sazonal_alvo)
    return resultado
