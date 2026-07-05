"""Lift entomologico — versao LIMPA do bloco vetor.

Igual ao lift_entomologico.ipynb (mesmo walk-forward multi-horizonte, mesmos
params LightGBM, mesmo passo=2), mas o bloco "vetor" passa a ser SO a densidade
de Aedes aegypti (por armadilha) + lags + media movel.

Removidos de TODOS os conjuntos (drop explicito, nao reclassificados no nucleo):
  - aedes_albopictus, culex_sp   -> nao sao o vetor da dengue em foco
  - aedes_aegypti (total bruto)  -> depende do numero de armadilhas (esforco)
  - numero_de_armadilhas         -> esforco de coleta, nao causa de dengue

O objetivo do script e medir o "lift" (ganho de MAE) que o bloco vetor traz
sobre um modelo so-clima, por horizonte de previsao, e salvar as metricas.

Entrada:
  - Bases de dados/tabela_modelagem/tabela_final.csv

Saida:
  - Bases de dados/tabela_modelagem/lift_limpo_resultados.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# --------------------------------------------------------------------- config
# Coluna-alvo da previsao (numero de casos confirmados de dengue por semana).
COLUNA_ALVO = "casos_confirmados"

# Coluna que identifica o bloco de dados de cada linha (fonte da serie). Todas
# as features temporais sao calculadas por bloco para nao atravessar o gap
# entre blocos distintos.
COLUNA_FONTE = "fonte"

# Coluna de data usada para ordenar os dados no walk-forward.
COLUNA_DATA = "data_inicio_semana_epidemi"

# Coluna com o numero da semana epidemiologica (base da sazonalidade).
COLUNA_SEMANA = "semana"

# Colunas cujos lags 1-4 sao gerados como features.
COLUNAS_PARA_LAG = [
    "casos_confirmados",
    "aedes_aegypti_por_armadilha",
    "temp_media",
    "precip_total_mm",
    "orvalho_media",
    "umid_media",
    "pressao_media",
]
LAGS_SEMANAS = [1, 2, 3, 4]

# Constantes de dominio usadas nos calculos (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Colunas removidas de QUALQUER conjunto de features: nao sao o vetor da dengue
# em foco, ou sao esforco de coleta (viesam por numero de armadilhas).
COLUNAS_DESCARTADAS = [
    "aedes_aegypti",
    "aedes_albopictus",
    "culex_sp",
    "numero_de_armadilhas",
]

# Colunas nunca usadas como feature (identificadores, datas, metadados) somadas
# as colunas descartadas acima.
COLUNAS_IGNORADAS = [
    "fonte",
    "SE",
    "data_inicio_semana_epidemi",
    "ano",
    "semana",
    "interpolado",
] + COLUNAS_DESCARTADAS

# Substrings que classificam uma coluna como "vetor" (densidade de Aedes) ou
# como "clima". A classificacao usa correspondencia por SUBSTRING (nao prefixo):
# a coluna entra no grupo se qualquer padrao aparecer em qualquer posicao do nome.
# "culex" NAO entra em vetor (nao e o vetor da dengue em foco).
PADROES_VETOR = ("aedes", "armadilha", "vetor")
PADROES_CLIMA = (
    "temp",
    "precip",
    "orvalho",
    "umid",
    "pressao",
    "radiacao",
    "vento",
    "dias_de_chuva",
    "nino34",
    "oni",
)

# Hiperparametros do LightGBM (arvores pequenas por causa da serie curta).
PARAMETROS_LGBM = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "verbose": -1,
    "n_jobs": -1,
}

# Parametros do walk-forward multi-horizonte.
HORIZONTES = range(1, 13)
MINIMO_SEMANAS_TREINO = 104
PASSO = 2

# Arredondamentos aplicados nas tabelas de resumo impressas no console.
CASAS_DECIMAIS_MAE = 1
CASAS_DECIMAIS_R2 = 3
CASAS_DECIMAIS_LIFT = 1
FATOR_PERCENTUAL = 100

# Nome do arquivo CSV de saida.
NOME_ARQUIVO_RESULTADOS = "lift_limpo_resultados.csv"


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
    raise FileNotFoundError(
        f"raiz com '{marcador_de_diretorio}/' nao encontrada de {Path.cwd()}"
    )


def carregar_tabela_final(caminho_tabela_final: Path) -> pd.DataFrame:
    """Le a tabela_final e a ordena por fonte e data.

    Args:
        caminho_tabela_final: Caminho do CSV tabela_final.

    Returns:
        DataFrame semanal ordenado por (fonte, data), com indice reiniciado.
    """
    tabela_final = pd.read_csv(
        caminho_tabela_final,
        parse_dates=[COLUNA_DATA],
    )
    tabela_final = tabela_final.sort_values([COLUNA_FONTE, COLUNA_DATA])
    tabela_final = tabela_final.reset_index(drop=True)
    return tabela_final


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap
    entre os blocos de dados.

    Args:
        serie: Serie temporal de um unico bloco.

    Returns:
        Serie com a media movel de 4 semanas (primeiras 3 posicoes NaN).
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def construir_features_temporais(dados: pd.DataFrame) -> pd.DataFrame:
    """Adiciona lags, medias moveis e sazonalidade ao DataFrame.

    Todas as features temporais sao calculadas POR BLOCO (groupby na coluna de
    fonte), de modo que os lags e as medias moveis nunca atravessem o gap entre
    os blocos de dados. As colunas sao adicionadas na ordem: lags (por coluna de
    origem, do lag 1 ao 4), casos_mm4, vetor_mm4, sem_sin e sem_cos.

    Args:
        dados: Tabela semanal ordenada, ja com as colunas de origem e 'semana'.

    Returns:
        O mesmo DataFrame (modificado in place) com as features adicionadas.
    """
    grupos_por_fonte = dados.groupby(COLUNA_FONTE, group_keys=False)

    for coluna_origem in COLUNAS_PARA_LAG:
        for numero_de_semanas in LAGS_SEMANAS:
            nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
            dados[nome_coluna_lag] = grupos_por_fonte[coluna_origem].shift(
                numero_de_semanas
            )

    dados["casos_mm4"] = grupos_por_fonte["casos_confirmados"].transform(
        media_movel_4_semanas
    )
    dados["vetor_mm4"] = grupos_por_fonte["aedes_aegypti_por_armadilha"].transform(
        media_movel_4_semanas
    )

    angulo_sazonal = 2 * np.pi * dados[COLUNA_SEMANA] / SEMANAS_POR_ANO
    dados["sem_sin"] = np.sin(angulo_sazonal)
    dados["sem_cos"] = np.cos(angulo_sazonal)
    return dados


def coluna_casa_algum_padrao(nome_coluna: str, padroes: tuple[str, ...]) -> bool:
    """Indica se algum padrao aparece como SUBSTRING no nome da coluna.

    A correspondencia e por substring (o padrao pode aparecer em qualquer
    posicao do nome), replicando exatamente a regra de classificacao original.

    Args:
        nome_coluna: Nome da coluna a testar.
        padroes: Substrings de classificacao.

    Returns:
        True se ao menos um padrao for substring do nome da coluna.
    """
    for padrao in padroes:
        if padrao in nome_coluna:
            return True
    return False


def listar_features_candidatas(dados: pd.DataFrame) -> list[str]:
    """Lista as colunas elegiveis a feature, na ordem em que aparecem.

    Descarta as colunas ignoradas (identificadores, datas, metadados e as
    colunas removidas por decisao de dominio).

    Args:
        dados: DataFrame ja com todas as features construidas.

    Returns:
        Lista de nomes de colunas candidatas, na ordem das colunas do DataFrame.
    """
    colunas_candidatas = []
    for nome_coluna in dados.columns:
        if nome_coluna not in COLUNAS_IGNORADAS:
            colunas_candidatas.append(nome_coluna)
    return colunas_candidatas


def separar_grupos_de_features(
    colunas_candidatas: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Separa as features candidatas em nucleo, clima e vetor.

    Uma coluna vai para 'vetor' se casar com PADROES_VETOR, para 'clima' se casar
    com PADROES_CLIMA, e para 'nucleo' caso nao pertenca nem a vetor nem a clima.
    Cada grupo preserva a ordem original das colunas candidatas.

    Args:
        colunas_candidatas: Colunas elegiveis a feature, na ordem original.

    Returns:
        Tripla (nucleo, clima, vetor) com as listas de colunas de cada grupo.
    """
    colunas_vetor = []
    for nome_coluna in colunas_candidatas:
        if coluna_casa_algum_padrao(nome_coluna, PADROES_VETOR):
            colunas_vetor.append(nome_coluna)

    colunas_clima = []
    for nome_coluna in colunas_candidatas:
        if coluna_casa_algum_padrao(nome_coluna, PADROES_CLIMA):
            colunas_clima.append(nome_coluna)

    colunas_nucleo = []
    for nome_coluna in colunas_candidatas:
        if nome_coluna not in colunas_vetor and nome_coluna not in colunas_clima:
            colunas_nucleo.append(nome_coluna)

    return colunas_nucleo, colunas_clima, colunas_vetor


def montar_conjuntos_de_features(
    colunas_nucleo: list[str],
    colunas_clima: list[str],
    colunas_vetor: list[str],
) -> dict[str, list[str]]:
    """Monta os tres conjuntos de features comparados no experimento.

    A ordem das colunas em cada conjunto e relevante (a arvore e sensivel a ela)
    e por isso e preservada exatamente: nucleo, depois clima e/ou vetor.

    Args:
        colunas_nucleo: Colunas autorregressivas e de sazonalidade.
        colunas_clima: Colunas de clima.
        colunas_vetor: Colunas de densidade do vetor.

    Returns:
        Dicionario ordenado nome_conjunto -> lista de features.
    """
    return {
        "so_clima": colunas_nucleo + colunas_clima,
        "clima_vetor": colunas_nucleo + colunas_clima + colunas_vetor,
        "so_vetor": colunas_nucleo + colunas_vetor,
    }


def walk_forward_conjunto(
    dados: pd.DataFrame,
    features_conjunto: list[str],
    alvo: str = "casos_confirmados",
    horizontes: range = range(1, 13),
    minimo_treino: int = 104,
    passo: int = 2,
) -> pd.DataFrame:
    """Walk-forward multi-horizonte de regressao de casos para um conjunto.

    Para cada horizonte, o alvo desloca-se -h semanas por bloco e sao adicionadas
    as componentes de sazonalidade da semana-alvo (alvo_sin, alvo_cos). As linhas
    com qualquer feature (ou o alvo) ausente sao descartadas via dropna. A partir
    de 'minimo_treino', treina um LightGBM em todo o historico ate a semana i e
    preve a proxima semana, avancando de 'passo' em 'passo'.

    A ordem das features passadas ao modelo e sempre
    features_conjunto + [alvo_sin, alvo_cos] (a arvore e sensivel a ela).

    Args:
        dados: DataFrame semanal ja com as features construidas.
        features_conjunto: Colunas de entrada do conjunto (sem a sazonalidade
            do alvo, que e adicionada aqui).
        alvo: Coluna-alvo cujos valores futuros serao previstos.
        horizontes: Horizontes de previsao (em semanas).
        minimo_treino: Numero minimo de semanas de treino antes de prever.
        passo: Espacamento entre as semanas de teste.

    Returns:
        DataFrame com uma linha por passo de teste e colunas h, real e pred.
    """
    grupos_por_fonte = dados.groupby(COLUNA_FONTE, group_keys=False)
    linhas_resultado = []
    for horizonte in horizontes:
        dados_horizonte = dados.copy()
        dados_horizonte["y_h"] = grupos_por_fonte[alvo].shift(-horizonte)

        semana_alvo = grupos_por_fonte[COLUNA_SEMANA].shift(-horizonte)
        angulo_sazonal_alvo = 2 * np.pi * semana_alvo / SEMANAS_POR_ANO
        dados_horizonte["alvo_sin"] = np.sin(angulo_sazonal_alvo)
        dados_horizonte["alvo_cos"] = np.cos(angulo_sazonal_alvo)

        features_com_sazonalidade = features_conjunto + ["alvo_sin", "alvo_cos"]
        colunas_obrigatorias = features_com_sazonalidade + ["y_h"]
        dados_validos = dados_horizonte.dropna(subset=colunas_obrigatorias)
        dados_validos = dados_validos.sort_values(COLUNA_DATA)
        dados_validos = dados_validos.reset_index(drop=True)

        for indice_corte in range(minimo_treino, len(dados_validos), passo):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]

            modelo = LGBMRegressor(**PARAMETROS_LGBM)
            modelo.fit(treino[features_com_sazonalidade], treino["y_h"])

            valor_real = teste["y_h"].values[0]
            valor_previsto = modelo.predict(teste[features_com_sazonalidade])[0]
            linhas_resultado.append(
                {"h": horizonte, "real": valor_real, "pred": valor_previsto}
            )
    return pd.DataFrame(linhas_resultado)


def avaliar_conjuntos(
    dados: pd.DataFrame,
    conjuntos: dict[str, list[str]],
) -> pd.DataFrame:
    """Roda o walk-forward de cada conjunto e agrega MAE e R2 por horizonte.

    Args:
        dados: DataFrame semanal ja com as features construidas.
        conjuntos: Mapa nome_conjunto -> features do conjunto.

    Returns:
        DataFrame com uma linha por (conjunto, horizonte) e colunas conjunto, h,
        MAE e R2.
    """
    linhas_metricas = []
    for nome_conjunto, features_conjunto in conjuntos.items():
        print(
            "rodando:",
            nome_conjunto,
            f"({len(features_conjunto)} features)",
            flush=True,
        )
        resultado_walk_forward = walk_forward_conjunto(dados, features_conjunto)
        for horizonte, previsoes in resultado_walk_forward.groupby("h"):
            mae = mean_absolute_error(previsoes["real"], previsoes["pred"])
            r2 = r2_score(previsoes["real"], previsoes["pred"])
            linhas_metricas.append(
                {"conjunto": nome_conjunto, "h": horizonte, "MAE": mae, "R2": r2}
            )
    return pd.DataFrame(linhas_metricas)


def resumir_mae_com_lift(comparacao: pd.DataFrame) -> pd.DataFrame:
    """Pivota o MAE por horizonte e acrescenta as colunas de lift do vetor.

    O lift e a reducao percentual de MAE em relacao ao modelo so-clima, tanto
    para clima+vetor quanto para so_vetor.

    Args:
        comparacao: DataFrame de metricas (colunas conjunto, h, MAE, R2).

    Returns:
        DataFrame com MAE por horizonte (uma coluna por conjunto) e as colunas
        lift_vetor_% e lift_sovetor_%.
    """
    mae_por_horizonte = comparacao.pivot(
        index="h", columns="conjunto", values="MAE"
    ).round(CASAS_DECIMAIS_MAE)

    reducao_clima_vetor = (
        (mae_por_horizonte["so_clima"] - mae_por_horizonte["clima_vetor"])
        / mae_por_horizonte["so_clima"]
        * FATOR_PERCENTUAL
    )
    mae_por_horizonte["lift_vetor_%"] = reducao_clima_vetor.round(CASAS_DECIMAIS_LIFT)

    reducao_so_vetor = (
        (mae_por_horizonte["so_clima"] - mae_por_horizonte["so_vetor"])
        / mae_por_horizonte["so_clima"]
        * FATOR_PERCENTUAL
    )
    mae_por_horizonte["lift_sovetor_%"] = reducao_so_vetor.round(CASAS_DECIMAIS_LIFT)
    return mae_por_horizonte


def resumir_r2(comparacao: pd.DataFrame) -> pd.DataFrame:
    """Pivota o R2 por horizonte (uma coluna por conjunto).

    Args:
        comparacao: DataFrame de metricas (colunas conjunto, h, MAE, R2).

    Returns:
        DataFrame com R2 por horizonte, arredondado.
    """
    return comparacao.pivot(index="h", columns="conjunto", values="R2").round(
        CASAS_DECIMAIS_R2
    )


def main() -> None:
    """Roda o experimento de lift do vetor e salva as metricas em CSV."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela_modelagem = (
        raiz_do_projeto / "Bases de dados" / "tabela_modelagem"
    )
    caminho_tabela_final = diretorio_tabela_modelagem / "tabela_final.csv"
    caminho_resultados = diretorio_tabela_modelagem / NOME_ARQUIVO_RESULTADOS

    dados = carregar_tabela_final(caminho_tabela_final)
    dados = construir_features_temporais(dados)

    colunas_candidatas = listar_features_candidatas(dados)
    colunas_nucleo, colunas_clima, colunas_vetor = separar_grupos_de_features(
        colunas_candidatas
    )
    conjuntos = montar_conjuntos_de_features(
        colunas_nucleo, colunas_clima, colunas_vetor
    )

    print(
        f"nucleo: {len(colunas_nucleo)} | clima: {len(colunas_clima)} | "
        f"vetor: {len(colunas_vetor)}"
    )
    print("vetor (limpo):", colunas_vetor)
    print("nucleo:", colunas_nucleo)

    comparacao = avaliar_conjuntos(dados, conjuntos)

    mae_por_horizonte = resumir_mae_com_lift(comparacao)
    r2_por_horizonte = resumir_r2(comparacao)

    print("\n=== MAE por horizonte ===")
    print(mae_por_horizonte.to_string())
    print("\n=== R2 por horizonte ===")
    print(r2_por_horizonte.to_string())

    comparacao.to_csv(caminho_resultados, index=False)
    print("\nsalvo: lift_limpo_resultados.csv")


if __name__ == "__main__":
    main()
