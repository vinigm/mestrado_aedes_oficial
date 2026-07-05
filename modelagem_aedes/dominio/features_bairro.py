"""

Prepara os dados do modelo por bairro: monta a tabela bairro x semana, descobre
os bairros vizinhos e cria as colunas que entram no modelo.

Tudo aqui e so preparo (nao treina modelo). A ideia central e prever quanto
mosquito vai ter em cada bairro, usando o passado do proprio bairro E o dos
bairros vizinhos (mosquito que sobe num lugar tende a subir na vizinhanca).

"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from config import settings

# Janela (em semanas) das medias moveis de densidade e de vizinhanca.
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Quantas semanas atras entram como colunas curtas (1, 2, 3 e 4 semanas).
LAGS_CURTOS = [1, 2, 3, 4]

# Colunas de "passado mais longe": 8 semanas atras e 52 (um ano atras).
LAG_MEDIO_SEMANAS = 8
LAG_SAZONAL_SEMANAS = 52


def media_movel_semanas(serie: pd.Series) -> pd.Series:
    """

    Media das ultimas semanas de um unico bairro (pra suavizar o sobe-e-desce).

    Usada por bairro, pra a janela nunca passar de um bairro pro outro.

    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def criticidade_point_in_time(serie: pd.Series) -> pd.Series:
    """

    Media de tudo que aconteceu ate a semana ANTERIOR (sem espiar o presente).

    Vai acumulando a media semana a semana, mas sempre atrasada em uma semana,
    pra a coluna de cada semana usar so o passado de verdade.

    """
    return serie.expanding().mean().shift(1)


def construir_painel_semanal(capturas: pd.DataFrame) -> pd.DataFrame:
    """

    Junta as capturas numa tabela por bairro, ano e semana, com a densidade de mosquito.

    Pra cada (bairro, ano, semana) soma o Aedes aegypti, conta as armadilhas e
    tira a media da posicao (latitude/longitude). A densidade e o mosquito
    dividido pelo numero de armadilhas. Tambem cria um numero de tempo 't', que
    conta as semanas em ordem (0, 1, 2, ...).

    Args:
        capturas: As capturas ja abertas e padronizadas.

    Returns:
        A tabela por bairro/semana com densidade e o numero de tempo 't'.

    """
    painel = (
        capturas.groupby(["bairro", "Ano", "Semana"])
        .agg(
            aegypti=("Aedes aegypti", "sum"),
            n=("ID", "count"),
            lat=("Latitude", "mean"),
            lon=("Longitude", "mean"),
        )
        .reset_index()
    )
    painel["dens"] = painel["aegypti"] / painel["n"]

    calendario = (
        painel[["Ano", "Semana"]]
        .drop_duplicates()
        .sort_values(["Ano", "Semana"])
        .reset_index(drop=True)
    )
    calendario["t"] = np.arange(len(calendario))
    painel = painel.merge(calendario, on=["Ano", "Semana"])
    return painel


def construir_grade_completa(painel: pd.DataFrame) -> pd.DataFrame:
    """

    Monta a grade com TODOS os bairros em TODAS as semanas e preenche o que falta com zero.

    Faz o cruzamento de cada bairro com cada semana; onde nao houve captura, a
    densidade vira 0 (nao teve mosquito medido). Traz tambem a semana do ano de
    cada tempo 't'.

    Args:
        painel: A tabela por bairro/semana.

    Returns:
        A grade completa, em ordem de bairro e tempo, com densidade e semana.

    """
    bairros = sorted(painel["bairro"].unique())
    calendario = (
        painel[["t", "Semana"]].drop_duplicates().sort_values("t").reset_index(drop=True)
    )
    instantes = painel[["t"]].drop_duplicates().sort_values("t")["t"].values

    grade = pd.MultiIndex.from_product(
        [bairros, instantes], names=["bairro", "t"]
    ).to_frame(index=False)

    dados_bairro = (
        grade.merge(painel[["bairro", "t", "dens"]], on=["bairro", "t"], how="left")
        .merge(calendario[["t", "Semana"]], on="t", how="left")
    )
    dados_bairro["dens"] = dados_bairro["dens"].fillna(0.0)
    dados_bairro = dados_bairro.sort_values(["bairro", "t"]).reset_index(drop=True)
    return dados_bairro


def mapear_vizinhos(
    painel: pd.DataFrame,
    bairros: list[str],
    numero_vizinhos: int,
) -> dict[str, list[str]]:
    """

    Descobre, pra cada bairro, quais sao os bairros mais proximos dele.

    Usa a posicao media (latitude/longitude) de cada bairro pra achar os
    vizinhos mais perto. O proprio bairro (distancia zero) e descartado.

    Args:
        painel: A tabela por bairro/semana (de onde vem a posicao dos bairros).
        bairros: A lista de bairros, em ordem.
        numero_vizinhos: Quantos vizinhos guardar pra cada bairro.

    Returns:
        Um dicionario ligando cada bairro a lista dos seus bairros mais proximos.

    """
    centroides = painel.groupby("bairro")[["lat", "lon"]].mean().loc[bairros]
    vizinhos_mais_proximos = NearestNeighbors(n_neighbors=numero_vizinhos + 1)
    vizinhos_mais_proximos.fit(centroides.values)
    _, indices_vizinhos = vizinhos_mais_proximos.kneighbors(centroides.values)

    vizinhos_de = {}
    for posicao_bairro in range(len(bairros)):
        indices_sem_o_proprio = indices_vizinhos[posicao_bairro][1:]
        vizinhos = []
        for indice_vizinho in indices_sem_o_proprio:
            vizinhos.append(bairros[indice_vizinho])
        vizinhos_de[bairros[posicao_bairro]] = vizinhos
    return vizinhos_de


def adicionar_densidade_vizinhanca(
    dados_bairro: pd.DataFrame,
    vizinhos_de: dict[str, list[str]],
    bairros: list[str],
) -> pd.DataFrame:
    """

    Adiciona, pra cada semana, a densidade media de mosquito dos bairros vizinhos.

    Monta uma tabela tempo x bairro de densidade, calcula pra cada bairro a media
    dos seus vizinhos e junta isso de volta (coluna 'viz').

    Args:
        dados_bairro: A grade completa (bairro, tempo, densidade).
        vizinhos_de: O mapa de vizinhos de cada bairro.
        bairros: A lista de bairros, em ordem.

    Returns:
        A mesma tabela com a coluna 'viz' (densidade media da vizinhanca).

    """
    matriz_densidade = dados_bairro.pivot(index="t", columns="bairro", values="dens")

    densidade_vizinhanca_por_bairro = {}
    for bairro in bairros:
        colunas_vizinhas = vizinhos_de[bairro]
        densidade_vizinhanca_por_bairro[bairro] = matriz_densidade[colunas_vizinhas].mean(axis=1)
    densidade_vizinhanca = pd.DataFrame(densidade_vizinhanca_por_bairro)

    vizinhanca_longa = densidade_vizinhanca.reset_index().melt(
        id_vars="t", var_name="bairro", value_name="viz"
    )
    return dados_bairro.merge(vizinhanca_longa, on=["t", "bairro"], how="left")


def adicionar_features_temporais(dados_bairro: pd.DataFrame) -> pd.DataFrame:
    """

    Cria as colunas que dependem do tempo, sempre por bairro.

    Inclui: densidade de 1 a 4 semanas atras (do proprio bairro e da vizinhanca),
    media das ultimas 4 semanas, a epoca do ano (seno e cosseno), a media
    acumulada sem espiar o presente (criticidade), o passado mais longe (8 e 52
    semanas atras) e a diferenca entre o bairro e seus vizinhos (grad1). Tudo por
    bairro, pra nunca passar de um bairro pro outro.

    Args:
        dados_bairro: A grade com densidade e a densidade da vizinhanca.

    Returns:
        A mesma tabela com as colunas novas.

    """
    grupos_por_bairro = dados_bairro.groupby("bairro", group_keys=False)

    for numero_de_semanas in LAGS_CURTOS:
        dados_bairro[f"dens_lag{numero_de_semanas}"] = grupos_por_bairro["dens"].shift(
            numero_de_semanas
        )
        dados_bairro[f"viz_lag{numero_de_semanas}"] = grupos_por_bairro["viz"].shift(
            numero_de_semanas
        )

    dados_bairro["dens_mm4"] = grupos_por_bairro["dens"].transform(media_movel_semanas)

    angulo_do_ano = 2 * np.pi * dados_bairro["Semana"] / settings.SEMANAS_POR_ANO
    dados_bairro["sin"] = np.sin(angulo_do_ano)
    dados_bairro["cos"] = np.cos(angulo_do_ano)

    dados_bairro["crit"] = grupos_por_bairro["dens"].transform(criticidade_point_in_time)
    dados_bairro["dens_lag8"] = grupos_por_bairro["dens"].shift(LAG_MEDIO_SEMANAS)
    dados_bairro["dens_lag52"] = grupos_por_bairro["dens"].shift(LAG_SAZONAL_SEMANAS)
    dados_bairro["viz_mm4"] = grupos_por_bairro["viz"].transform(media_movel_semanas)
    dados_bairro["grad1"] = dados_bairro["dens_lag1"] - dados_bairro["viz_lag1"]
    return dados_bairro
