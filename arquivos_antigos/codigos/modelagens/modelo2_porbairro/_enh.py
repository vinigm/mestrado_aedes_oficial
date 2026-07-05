#!/usr/bin/env python3
"""Testa engenharia de features v2 (leak-safe) no modelo de vetor por bairro.

Compara quatro combinacoes de features na previsao da densidade de Aedes aegypti
por bairro de Marilia, via walk-forward expansivel com LightGBM:

  - base_own:  autorregressivo do proprio bairro (lags, media movel, sazonalidade);
  - base_+viz: base_own + lags da densidade dos bairros vizinhos;
  - enh_own:   base_own + features v2 (criticidade point-in-time, lags 8 e 52) e
               a sazonalidade do horizonte-alvo (alvo_sin/alvo_cos);
  - enh_+viz:  enh_own + lags de vizinhanca, media movel de vizinhanca e gradiente.

Todas as features de vizinhanca sao leak-safe (usam so passado). A saida e uma
tabela de R2 por horizonte de previsao (1 a 4 semanas), impressa no console;
o script NAO grava nenhum arquivo.

Observacao de reprodutibilidade: o LightGBM roda com n_jobs=-1 (paralelismo total),
o que pode tornar os resultados NAO exatamente reprodutiveis entre execucoes.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import r2_score
from sklearn.neighbors import NearestNeighbors

# --------------------------------------------------------------------- config
# Anos das capturas de Marilia lidos (saida_2019.csv ... saida_2023.csv).
ANOS_CAPTURA = range(2019, 2024)

# Numero de bairros vizinhos considerados na vizinhanca de cada bairro.
NUMERO_VIZINHOS = 4

# Sazonalidade anual: 52 semanas epidemiologicas por ano.
SEMANAS_POR_ANO = 52

# Janela (em semanas) das medias moveis de densidade e de vizinhanca.
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Defasagens (lags) autorregressivas curtas de densidade e vizinhanca.
LAGS_CURTOS = [1, 2, 3, 4]

# Defasagens longas adicionadas nas features v2: 8 semanas e 52 (ano anterior).
LAG_MEDIO_SEMANAS = 8
LAG_SAZONAL_SEMANAS = 52

# Walk-forward: primeira semana de teste, passo entre semanas de teste e
# tamanho minimo do treino para treinar um modelo no passo.
SEMANA_MINIMA_TESTE = 120
PASSO_WALK_FORWARD = 4
MINIMO_LINHAS_TREINO = 200

# Horizontes de previsao (semanas a frente): 1, 2, 3 e 4.
HORIZONTES_SEMANAS = range(1, 5)

# Colunas de features derivadas (nomes e ORDEM importam: a arvore e sensivel a
# ordem das colunas passadas no fit/predict).
COLUNAS_LAG_DENSIDADE = ["dens_lag1", "dens_lag2", "dens_lag3", "dens_lag4"]
COLUNAS_LAG_VIZINHANCA = ["viz_lag1", "viz_lag2", "viz_lag3", "viz_lag4"]

FEATURES_OWN_BASE = COLUNAS_LAG_DENSIDADE + ["dens_mm4", "sin", "cos"]
FEATURES_VIZ_BASE = FEATURES_OWN_BASE + COLUNAS_LAG_VIZINHANCA
FEATURES_OWN_ENH = FEATURES_OWN_BASE + ["crit", "dens_lag8", "dens_lag52"]
FEATURES_VIZ_ENH = (
    FEATURES_OWN_ENH + COLUNAS_LAG_VIZINHANCA + ["viz_mm4", "grad1"]
)

# Hiperparametros do LightGBM. n_jobs=-1 usa todos os nucleos (pode ser
# nao-deterministico); verbose=-1 silencia o log de treino.
PARAMETROS_LGBM = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": -1,
}


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = "Raspagem") -> Path:
    """Sobe a partir do diretorio atual ate achar a raiz do projeto.

    A raiz e identificada pela presenca de um subdiretorio marcador (por padrao
    'Raspagem'), o que torna o script executavel de qualquer subpasta.

    Args:
        marcador_de_diretorio: Nome do subdiretorio que identifica a raiz.

    Returns:
        Caminho da raiz do projeto.

    Raises:
        FileNotFoundError: Se nenhum diretorio ancestral contiver o marcador.
    """
    diretorio_atual = Path.cwd()
    for diretorio_candidato in [diretorio_atual, *diretorio_atual.parents]:
        if (diretorio_candidato / marcador_de_diretorio).is_dir():
            return diretorio_candidato
    raise FileNotFoundError


def media_movel_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de JANELA_MEDIA_MOVEL_SEMANAS semanas de um unico bairro.

    Usada em transform() por bairro para que a janela nunca atravesse a fronteira
    entre bairros distintos.
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def criticidade_point_in_time(serie: pd.Series) -> pd.Series:
    """Media expansiva ate a semana anterior (criticidade sem vazamento).

    A media acumulada e deslocada em uma semana (shift(1)) para que o valor de
    cada semana use apenas o passado estrito, evitando leakage do presente.
    """
    return serie.expanding().mean().shift(1)


def r2_do_grupo(grupo: pd.DataFrame) -> float:
    """R2 entre valores reais e previstos de um grupo de previsoes."""
    return r2_score(grupo.real, grupo.pred)


def carregar_capturas(diretorio_dados: Path) -> pd.DataFrame:
    """Le e concatena as capturas anuais de Marilia, normalizando os campos.

    Concatena os arquivos saida_{ano}.csv (separados por ';'), padroniza o nome
    do bairro (maiusculas, sem espacos nas pontas) e converte latitude, longitude
    e contagem de Aedes aegypti para numerico (virgula decimal -> ponto).

    Args:
        diretorio_dados: Diretorio que contem os arquivos saida_{ano}.csv.

    Returns:
        DataFrame com todas as capturas concatenadas e os campos normalizados.
    """
    capturas_por_ano = []
    for ano in ANOS_CAPTURA:
        caminho_ano = diretorio_dados / f"saida_{ano}.csv"
        capturas_por_ano.append(pd.read_csv(caminho_ano, sep=";"))
    capturas = pd.concat(capturas_por_ano, ignore_index=True)

    capturas["bairro"] = capturas["Local"].astype(str).str.upper().str.strip()

    for coluna_numerica in ["Latitude", "Longitude", "Aedes aegypti"]:
        texto_com_ponto = (
            capturas[coluna_numerica].astype(str).str.replace(",", ".", regex=False)
        )
        capturas[coluna_numerica] = pd.to_numeric(texto_com_ponto, errors="coerce")

    return capturas


def construir_painel_semanal(capturas: pd.DataFrame) -> pd.DataFrame:
    """Agrega as capturas em um painel bairro x ano x semana com densidade.

    Para cada (bairro, ano, semana) soma o Aedes aegypti, conta as armadilhas
    (ID), tira a media de latitude/longitude e calcula a densidade (aegypti/n).
    Adiciona um indice temporal continuo 't' sobre os pares (ano, semana)
    ordenados cronologicamente.

    Args:
        capturas: Capturas normalizadas por carregar_capturas.

    Returns:
        Painel semanal com colunas bairro, Ano, Semana, aegypti, n, lat, lon,
        dens e t.
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
    """Cria a grade completa bairro x t e preenche a densidade ausente com zero.

    Monta o produto cartesiano de todos os bairros por todos os instantes 't',
    traz a densidade do painel (ausencia = sem captura = densidade 0) e a semana
    epidemiologica de cada 't'.

    Args:
        painel: Painel semanal produzido por construir_painel_semanal.

    Returns:
        DataFrame ordenado por (bairro, t) com colunas bairro, t, dens e Semana.
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


def mapear_vizinhos(painel: pd.DataFrame, bairros: list[str]) -> dict[str, list[str]]:
    """Mapeia cada bairro aos seus NUMERO_VIZINHOS bairros mais proximos.

    Usa o centroide de cada bairro (media de latitude/longitude) e k-vizinhos
    mais proximos. O primeiro vizinho retornado e o proprio bairro (distancia 0)
    e por isso e descartado.

    Args:
        painel: Painel semanal (usado para os centroides de lat/lon).
        bairros: Lista ordenada de bairros.

    Returns:
        Dicionario bairro -> lista dos NUMERO_VIZINHOS bairros mais proximos.
    """
    centroides = painel.groupby("bairro")[["lat", "lon"]].mean().loc[bairros]
    vizinhos_mais_proximos = NearestNeighbors(n_neighbors=NUMERO_VIZINHOS + 1)
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
    dados_bairro: pd.DataFrame, vizinhos_de: dict[str, list[str]], bairros: list[str]
) -> pd.DataFrame:
    """Adiciona a densidade media dos bairros vizinhos em cada instante 't'.

    Constroi a matriz t x bairro de densidade, calcula por bairro a media da
    densidade dos seus vizinhos e junta o resultado (coluna 'viz') de volta ao
    painel longo.

    Args:
        dados_bairro: Grade completa com densidade por bairro e instante.
        vizinhos_de: Mapa de vizinhos produzido por mapear_vizinhos.
        bairros: Lista ordenada de bairros.

    Returns:
        DataFrame com a coluna 'viz' (densidade media da vizinhanca) adicionada.
    """
    matriz_densidade = dados_bairro.pivot(index="t", columns="bairro", values="dens")

    densidade_vizinhanca_por_bairro = {}
    for bairro in bairros:
        colunas_vizinhas = vizinhos_de[bairro]
        densidade_vizinhanca_por_bairro[bairro] = matriz_densidade[colunas_vizinhas].mean(
            axis=1
        )
    densidade_vizinhanca = pd.DataFrame(densidade_vizinhanca_por_bairro)

    vizinhanca_longa = densidade_vizinhanca.reset_index().melt(
        id_vars="t", var_name="bairro", value_name="viz"
    )
    return dados_bairro.merge(vizinhanca_longa, on=["t", "bairro"], how="left")


def adicionar_features_temporais(dados_bairro: pd.DataFrame) -> pd.DataFrame:
    """Adiciona lags, medias moveis, sazonalidade e features v2 (leak-safe).

    Todas as features temporais sao calculadas por bairro (groupby), de modo que
    lags e janelas nunca atravessem a fronteira entre bairros. Inclui:
      - lags 1-4 de densidade e de vizinhanca;
      - media movel de 4 semanas da densidade (dens_mm4);
      - sazonalidade da semana atual (sin, cos);
      - criticidade point-in-time (crit) e lags longos (8 e 52) de densidade;
      - media movel de 4 semanas da vizinhanca (viz_mm4);
      - gradiente bairro - vizinhos no lag 1 (grad1).

    Args:
        dados_bairro: Painel longo com densidade e vizinhanca.

    Returns:
        O mesmo DataFrame com as colunas de features adicionadas.
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

    angulo_sazonal = 2 * np.pi * dados_bairro["Semana"] / SEMANAS_POR_ANO
    dados_bairro["sin"] = np.sin(angulo_sazonal)
    dados_bairro["cos"] = np.cos(angulo_sazonal)

    # --- features v2 (leak-safe) ---
    dados_bairro["crit"] = grupos_por_bairro["dens"].transform(criticidade_point_in_time)
    dados_bairro["dens_lag8"] = grupos_por_bairro["dens"].shift(LAG_MEDIO_SEMANAS)
    dados_bairro["dens_lag52"] = grupos_por_bairro["dens"].shift(LAG_SAZONAL_SEMANAS)
    dados_bairro["viz_mm4"] = grupos_por_bairro["viz"].transform(media_movel_semanas)
    dados_bairro["grad1"] = dados_bairro["dens_lag1"] - dados_bairro["viz_lag1"]
    return dados_bairro


def avaliar_combinacao(
    dados_bairro: pd.DataFrame,
    features: list[str],
    usar_sazonalidade_do_alvo: bool = False,
) -> pd.Series:
    """Roda o walk-forward de uma combinacao de features e retorna R2 por horizonte.

    Para cada horizonte, define o alvo (densidade h semanas a frente), opcionalmente
    adiciona a sazonalidade do alvo, descarta linhas com features/alvo ausentes e,
    a cada PASSO_WALK_FORWARD semanas, treina em todo o passado (t < i) e preve a
    semana i. Ao final, agrega o R2 por horizonte.

    Args:
        dados_bairro: Painel com todas as features ja construidas.
        features: Colunas de entrada do modelo, na ordem em que serao usadas.
        usar_sazonalidade_do_alvo: Se True, acrescenta alvo_sin e alvo_cos.

    Returns:
        Serie de R2 indexada pelo horizonte de previsao.
    """
    grupos_por_bairro = dados_bairro.groupby("bairro", group_keys=False)
    instante_maximo = int(dados_bairro["t"].max())
    previsoes_por_horizonte = []

    for horizonte in HORIZONTES_SEMANAS:
        dados_horizonte = dados_bairro.copy()
        dados_horizonte["y"] = grupos_por_bairro["dens"].shift(-horizonte)

        features_do_passo = list(features)
        if usar_sazonalidade_do_alvo:
            semana_do_alvo = grupos_por_bairro["Semana"].shift(-horizonte)
            angulo_do_alvo = 2 * np.pi * semana_do_alvo / SEMANAS_POR_ANO
            dados_horizonte["alvo_sin"] = np.sin(angulo_do_alvo)
            dados_horizonte["alvo_cos"] = np.cos(angulo_do_alvo)
            features_do_passo = features_do_passo + ["alvo_sin", "alvo_cos"]

        dados_validos = dados_horizonte.dropna(subset=features_do_passo + ["y"])

        for semana_teste in range(
            SEMANA_MINIMA_TESTE, instante_maximo - horizonte + 1, PASSO_WALK_FORWARD
        ):
            treino = dados_validos[dados_validos["t"] < semana_teste]
            teste = dados_validos[dados_validos["t"] == semana_teste]
            if len(teste) == 0 or len(treino) < MINIMO_LINHAS_TREINO:
                continue

            modelo = LGBMRegressor(**PARAMETROS_LGBM)
            modelo.fit(treino[features_do_passo], treino["y"])
            previsoes_do_passo = pd.DataFrame(
                {
                    "h": horizonte,
                    "real": teste["y"].values,
                    "pred": modelo.predict(teste[features_do_passo]),
                }
            )
            previsoes_por_horizonte.append(previsoes_do_passo)

    previsoes = pd.concat(previsoes_por_horizonte, ignore_index=True)
    return previsoes.groupby("h").apply(r2_do_grupo, include_groups=False)


def montar_tabela_resultados(dados_bairro: pd.DataFrame) -> pd.DataFrame:
    """Roda as quatro combinacoes de features e monta a tabela de R2 comparativa.

    Args:
        dados_bairro: Painel com todas as features construidas.

    Returns:
        DataFrame de R2 por horizonte com as colunas base_own, base_+viz, enh_own,
        enh_+viz e as colunas derivadas ganho_enh e lift_viz_enh (todas com 3 casas).
    """
    resultados = pd.DataFrame(
        {
            "base_own": avaliar_combinacao(dados_bairro, FEATURES_OWN_BASE),
            "base_+viz": avaliar_combinacao(dados_bairro, FEATURES_VIZ_BASE),
            "enh_own": avaliar_combinacao(
                dados_bairro, FEATURES_OWN_ENH, usar_sazonalidade_do_alvo=True
            ),
            "enh_+viz": avaliar_combinacao(
                dados_bairro, FEATURES_VIZ_ENH, usar_sazonalidade_do_alvo=True
            ),
        }
    ).round(3)
    resultados["ganho_enh"] = (resultados["enh_+viz"] - resultados["base_+viz"]).round(3)
    resultados["lift_viz_enh"] = (resultados["enh_+viz"] - resultados["enh_own"]).round(3)
    return resultados


def imprimir_resultados(resultados: pd.DataFrame) -> None:
    """Imprime a tabela de R2 por horizonte e as medias por combinacao."""
    print("\n==== R² por horizonte ====")
    print(resultados.to_string())
    print(
        "\nmédia R²: base_own=%.3f base_+viz=%.3f enh_own=%.3f enh_+viz=%.3f"
        % (
            resultados.base_own.mean(),
            resultados["base_+viz"].mean(),
            resultados.enh_own.mean(),
            resultados["enh_+viz"].mean(),
        )
    )


def main() -> None:
    """Orquestra a preparacao dos dados e a avaliacao das quatro combinacoes."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_dados = raiz_do_projeto / "Bases de dados" / "dados_marilia"

    capturas = carregar_capturas(diretorio_dados)
    painel = construir_painel_semanal(capturas)

    bairros = sorted(painel["bairro"].unique())
    dados_bairro = construir_grade_completa(painel)

    vizinhos_de = mapear_vizinhos(painel, bairros)
    dados_bairro = adicionar_densidade_vizinhanca(dados_bairro, vizinhos_de, bairros)
    dados_bairro = adicionar_features_temporais(dados_bairro)

    print("rodando 4 combos...")
    resultados = montar_tabela_resultados(dados_bairro)
    imprimir_resultados(resultados)


if __name__ == "__main__":
    main()
