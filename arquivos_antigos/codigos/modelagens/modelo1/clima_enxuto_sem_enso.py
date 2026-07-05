"""clima_enxuto + vetor SEM ENSO — testa o confundimento do nino34.

Igual ao clima_enxuto_vetor.py, mas nino34_anom e oni saem do conjunto de
CANDIDATOS de clima antes da selecao por importancia. Se o lift marginal do
vetor (M1 vs M0) virar positivo aqui, o ENSO estava mascarando o sinal do
vetor; se continuar nulo/negativo, o resultado negativo se sustenta.

Fluxo:
  1. Le a tabela_final semanal (SINAN confirmado + clima + vetor).
  2. Constroi lags, medias moveis e sazonalidade por bloco (fonte).
  3. Separa as features em nucleo (autorregressivo + sazonal), clima e vetor,
     deixando o ENSO de fora do pool de candidatos de clima.
  4. Ranqueia as variaveis de clima por importancia (gain) do LightGBM nos
     horizontes iniciais 1/4/8.
  5. Roda um walk-forward comparando so-clima (M0) contra clima+vetor (M1)
     para os top-K climas (K = 6 e 8), reportando R2, MAE e o lift do vetor.

Saidas:
  - Bases de dados/tabela_modelagem/clima_enxuto_sem_enso_resultados.csv
"""
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# --------------------------------------------------------------------- config
# Subdiretorio que identifica a raiz do projeto (executavel de qualquer pasta).
MARCADOR_RAIZ = "Raspagem"

# Arquivo de entrada e de saida, ambos sob Bases de dados/tabela_modelagem.
NOME_ARQUIVO_ENTRADA = "tabela_final.csv"
NOME_ARQUIVO_SAIDA = "clima_enxuto_sem_enso_resultados.csv"

# Colunas-chave da tabela de entrada.
COLUNA_DATA = "data_inicio_semana_epidemi"
COLUNA_FONTE = "fonte"
COLUNA_SEMANA = "semana"
COLUNA_ALVO = "casos_confirmados"

# Colunas cujos lags 1-4 sao gerados.
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

# Constantes de sazonalidade e media movel (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Colunas descartadas do pool de candidatos (contagens brutas nao usadas).
COLUNAS_DESCARTADAS = [
    "aedes_aegypti",
    "aedes_albopictus",
    "culex_sp",
    "numero_de_armadilhas",
]

# Colunas de ENSO deliberadamente FORA do pool de candidatos de clima — o ponto
# central deste experimento (testar o confundimento do nino34).
COLUNAS_ENSO = ["nino34_anom", "oni"]

# Metadados/identificadores que nunca entram como feature.
COLUNAS_IGNORADAS_BASE = [
    "fonte",
    "SE",
    "data_inicio_semana_epidemi",
    "ano",
    "semana",
    "interpolado",
]

# Prefixos/trechos que classificam cada feature em vetor ou clima.
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

# Selecao por importancia: horizontes iniciais e fracao inicial usada como treino.
HORIZONTES_IMPORTANCIA = (1, 4, 8)
FRACAO_TREINO_IMPORTANCIA = 0.60

# Walk-forward: horizontes, treino minimo e espacamento entre semanas de teste.
HORIZONTES_WALK_FORWARD = range(1, 13)
MINIMO_SEMANAS_TREINO = 104
PASSO_WALK_FORWARD = 2

# Quantidades de climas selecionados (top-K do ranking) comparadas.
VALORES_K = (6, 8)

# Numero de climas exibidos no ranking impresso.
TOP_CLIMAS_EXIBIDOS = 12

# Casas decimais usadas em cada relatorio.
CASAS_RANKING = 0
CASAS_R2 = 3
CASAS_MAE = 1
CASAS_LIFT = 1

# Ordem fixa das colunas M0/M1 nas tabelas de R2 e MAE impressas.
ORDEM_CONJUNTOS = ["M0_clima6", "M1_clima6_vetor", "M0_clima8", "M1_clima8_vetor"]


@dataclasses.dataclass(frozen=True)
class GruposDeFeatures:
    """Particao das colunas candidatas em tres grupos disjuntos.

    Attributes:
        nucleo: Features autorregressivas e sazonais (casos, lags de casos,
            media movel de casos, sem_sin/sem_cos), sempre presentes.
        clima: Features climaticas (temperatura, precipitacao, umidade, etc.).
        vetor: Features do vetor (aedes/armadilha e sua media movel).
    """

    nucleo: list[str]
    clima: list[str]
    vetor: list[str]


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = MARCADOR_RAIZ) -> Path:
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


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap entre
    os blocos de dados.

    Args:
        serie: Serie temporal de um unico bloco.

    Returns:
        Serie com a media movel de JANELA_MEDIA_MOVEL_SEMANAS semanas.
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def carregar_tabela_modelagem(diretorio_tabela: Path) -> pd.DataFrame:
    """Le a tabela_final semanal e a ordena por fonte e data.

    Args:
        diretorio_tabela: Diretorio que contem o arquivo de entrada.

    Returns:
        DataFrame ordenado por (fonte, data) com o indice reiniciado.
    """
    tabela = pd.read_csv(
        diretorio_tabela / NOME_ARQUIVO_ENTRADA,
        parse_dates=[COLUNA_DATA],
    )
    tabela_ordenada = tabela.sort_values([COLUNA_FONTE, COLUNA_DATA]).reset_index(
        drop=True
    )
    return tabela_ordenada


def construir_features_temporais(dados: pd.DataFrame) -> pd.DataFrame:
    """Adiciona lags, medias moveis e sazonalidade — por bloco (fonte).

    Todas as features temporais sao calculadas POR BLOCO (groupby na fonte), de
    modo que os lags e as medias moveis nunca atravessem o gap entre os blocos.

    Args:
        dados: Tabela semanal ja ordenada por (fonte, data).

    Returns:
        O mesmo DataFrame com as colunas de features adicionadas.
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


def classificar_features(dados: pd.DataFrame) -> GruposDeFeatures:
    """Separa as colunas candidatas em nucleo, clima e vetor.

    Remove metadados, contagens brutas descartadas e o ENSO do pool de
    candidatos e, entre o que sobra, classifica cada coluna por padroes de nome.
    A ordem de cada grupo segue a ordem das colunas no DataFrame — importa,
    porque a arvore e sensivel a ordem das features.

    Args:
        dados: DataFrame ja com as features temporais construidas.

    Returns:
        GruposDeFeatures com as listas nucleo, clima e vetor.
    """
    colunas_ignoradas = COLUNAS_IGNORADAS_BASE + COLUNAS_DESCARTADAS + COLUNAS_ENSO
    colunas_candidatas = [
        nome_coluna
        for nome_coluna in dados.columns
        if nome_coluna not in colunas_ignoradas
    ]

    colunas_vetor = []
    colunas_clima = []
    colunas_nucleo = []
    for nome_coluna in colunas_candidatas:
        eh_vetor = any(padrao in nome_coluna for padrao in PADROES_VETOR)
        eh_clima = any(padrao in nome_coluna for padrao in PADROES_CLIMA)
        if eh_vetor:
            colunas_vetor.append(nome_coluna)
        elif eh_clima:
            colunas_clima.append(nome_coluna)
        else:
            colunas_nucleo.append(nome_coluna)

    return GruposDeFeatures(
        nucleo=colunas_nucleo,
        clima=colunas_clima,
        vetor=colunas_vetor,
    )


def adicionar_alvo_horizonte(dados: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Cria o alvo h semanas a frente e a sazonalidade da semana-alvo.

    O alvo (y_h) e o numero de casos deslocado h semanas para tras dentro de
    cada bloco; alvo_sin/alvo_cos codificam a semana epidemiologica do alvo.

    Args:
        dados: DataFrame com as features ja construidas.
        horizonte: Numero de semanas a frente a prever.

    Returns:
        Uma COPIA do DataFrame com as colunas y_h, alvo_sin e alvo_cos.
    """
    grupos_por_fonte = dados.groupby(COLUNA_FONTE, group_keys=False)
    dados_com_alvo = dados.copy()
    dados_com_alvo["y_h"] = grupos_por_fonte[COLUNA_ALVO].shift(-horizonte)

    semana_do_alvo = grupos_por_fonte[COLUNA_SEMANA].shift(-horizonte)
    angulo_sazonal_alvo = 2 * np.pi * semana_do_alvo / SEMANAS_POR_ANO
    dados_com_alvo["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    dados_com_alvo["alvo_cos"] = np.cos(angulo_sazonal_alvo)
    return dados_com_alvo


def calcular_ranking_clima(
    dados: pd.DataFrame,
    grupos: GruposDeFeatures,
) -> pd.Series:
    """Ranqueia as variaveis de clima por importancia (gain) do LightGBM.

    Para cada horizonte inicial (1/4/8), treina um LightGBM nos primeiros 60%
    dos dados validos e acumula o ganho de cada variavel de clima. O ranking
    final e a soma dos ganhos, em ordem decrescente.

    Args:
        dados: DataFrame com as features construidas.
        grupos: Particao das features em nucleo, clima e vetor.

    Returns:
        Serie de importancia acumulada por variavel de clima, ordenada de forma
        decrescente.
    """
    importancia_acumulada = pd.Series(0.0, index=grupos.clima)
    for horizonte in HORIZONTES_IMPORTANCIA:
        dados_com_alvo = adicionar_alvo_horizonte(dados, horizonte)
        features = grupos.nucleo + grupos.clima + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values(COLUNA_DATA)
            .reset_index(drop=True)
        )
        quantidade_treino = int(len(dados_validos) * FRACAO_TREINO_IMPORTANCIA)
        treino = dados_validos.iloc[:quantidade_treino]

        modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(treino[features], treino["y_h"])
        ganho_por_feature = pd.Series(
            modelo.booster_.feature_importance(importance_type="gain"),
            index=features,
        )
        ganho_clima = ganho_por_feature.reindex(grupos.clima).fillna(0)
        importancia_acumulada = importancia_acumulada.add(ganho_clima, fill_value=0)

    ranking = importancia_acumulada.sort_values(ascending=False)
    return ranking


def executar_walk_forward(
    dados: pd.DataFrame,
    colunas_features: list[str],
) -> pd.DataFrame:
    """Walk-forward expansivel de regressao de casos para varios horizontes.

    Em cada horizonte, treina em todo o historico ate a semana i e preve a
    semana i, avancando de PASSO_WALK_FORWARD em PASSO_WALK_FORWARD a partir de
    MINIMO_SEMANAS_TREINO.

    Args:
        dados: DataFrame com as features construidas.
        colunas_features: Colunas de entrada do modelo (a sazonalidade do alvo
            e adicionada aqui).

    Returns:
        DataFrame com uma linha por semana de teste e as colunas h, real e pred.
    """
    linhas_resultado = []
    for horizonte in HORIZONTES_WALK_FORWARD:
        dados_com_alvo = adicionar_alvo_horizonte(dados, horizonte)
        features = colunas_features + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values(COLUNA_DATA)
            .reset_index(drop=True)
        )
        for indice_corte in range(
            MINIMO_SEMANAS_TREINO, len(dados_validos), PASSO_WALK_FORWARD
        ):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]
            modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(
                treino[features], treino["y_h"]
            )
            linhas_resultado.append(
                {
                    "h": horizonte,
                    "real": teste["y_h"].values[0],
                    "pred": modelo.predict(teste[features])[0],
                }
            )
    return pd.DataFrame(linhas_resultado)


def calcular_metricas(resultado: pd.DataFrame, nome_conjunto: str) -> list[dict]:
    """Calcula MAE e R2 por horizonte de um resultado de walk-forward.

    Args:
        resultado: DataFrame com as colunas h, real e pred.
        nome_conjunto: Nome do conjunto de features (ex.: 'M0_clima6').

    Returns:
        Lista de dicionarios, um por horizonte, com conjunto, h, MAE e R2.
    """
    linhas_metricas = []
    for horizonte, previsoes_do_horizonte in resultado.groupby("h"):
        linhas_metricas.append(
            {
                "conjunto": nome_conjunto,
                "h": horizonte,
                "MAE": mean_absolute_error(
                    previsoes_do_horizonte["real"], previsoes_do_horizonte["pred"]
                ),
                "R2": r2_score(
                    previsoes_do_horizonte["real"], previsoes_do_horizonte["pred"]
                ),
            }
        )
    return linhas_metricas


def comparar_modelos(
    dados: pd.DataFrame,
    grupos: GruposDeFeatures,
    ranking: pd.Series,
) -> pd.DataFrame:
    """Compara so-clima (M0) contra clima+vetor (M1) para cada K de top-climas.

    Para cada K em VALORES_K, seleciona os K climas mais bem ranqueados e roda o
    walk-forward em dois conjuntos: nucleo+climas (M0) e nucleo+climas+vetor (M1).

    Args:
        dados: DataFrame com as features construidas.
        grupos: Particao das features em nucleo, clima e vetor.
        ranking: Ranking de importancia das variaveis de clima.

    Returns:
        DataFrame empilhado com as metricas de todos os conjuntos.
    """
    linhas_metricas = []
    for quantidade_climas in VALORES_K:
        climas_top = ranking.head(quantidade_climas).index.tolist()
        print(
            f"\n=== clima_enxuto SEM ENSO K={quantidade_climas} ===\n{climas_top}"
        )

        features_so_clima = grupos.nucleo + climas_top
        resultado_so_clima = executar_walk_forward(dados, features_so_clima)
        linhas_metricas += calcular_metricas(
            resultado_so_clima, f"M0_clima{quantidade_climas}"
        )

        features_clima_vetor = grupos.nucleo + climas_top + grupos.vetor
        resultado_clima_vetor = executar_walk_forward(dados, features_clima_vetor)
        linhas_metricas += calcular_metricas(
            resultado_clima_vetor, f"M1_clima{quantidade_climas}_vetor"
        )
    return pd.DataFrame(linhas_metricas)


def montar_tabela_r2(comparacao: pd.DataFrame) -> pd.DataFrame:
    """Pivota o R2 por horizonte x conjunto, arredondado.

    Args:
        comparacao: DataFrame empilhado de metricas.

    Returns:
        Tabela de R2 (indice = h, colunas = conjunto).
    """
    return comparacao.pivot(index="h", columns="conjunto", values="R2").round(CASAS_R2)


def montar_tabela_mae_com_lift(comparacao: pd.DataFrame) -> pd.DataFrame:
    """Pivota o MAE por horizonte x conjunto e adiciona o lift do vetor por K.

    O lift marginal do vetor e a reducao percentual do MAE de M1 (clima+vetor)
    em relacao a M0 (so-clima), por horizonte.

    Args:
        comparacao: DataFrame empilhado de metricas.

    Returns:
        Tabela de MAE (indice = h) com as colunas de lift lift_K6_% e lift_K8_%.
    """
    mae = comparacao.pivot(index="h", columns="conjunto", values="MAE").round(CASAS_MAE)
    for quantidade_climas in VALORES_K:
        coluna_m0 = f"M0_clima{quantidade_climas}"
        coluna_m1 = f"M1_clima{quantidade_climas}_vetor"
        reducao_percentual = (mae[coluna_m0] - mae[coluna_m1]) / mae[coluna_m0] * 100
        mae[f"lift_K{quantidade_climas}_%"] = reducao_percentual.round(CASAS_LIFT)
    return mae


def main() -> None:
    """Roda a selecao de clima e a comparacao M0 vs M1 e salva o resultado."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela = raiz_do_projeto / "Bases de dados" / "tabela_modelagem"

    dados = carregar_tabela_modelagem(diretorio_tabela)
    dados = construir_features_temporais(dados)
    grupos = classificar_features(dados)

    ranking = calcular_ranking_clima(dados, grupos)
    print("=== ranking clima SEM ENSO (gain, dados iniciais) ===")
    print(ranking.head(TOP_CLIMAS_EXIBIDOS).round(CASAS_RANKING).to_string())

    comparacao = comparar_modelos(dados, grupos, ranking)

    tabela_r2 = montar_tabela_r2(comparacao)
    tabela_mae = montar_tabela_mae_com_lift(comparacao)

    print("\n=== R2 por horizonte (SEM ENSO) ===")
    print(tabela_r2[ORDEM_CONJUNTOS].to_string())
    print("\n=== MAE + lift marginal do vetor (SEM ENSO) ===")
    colunas_mae_exibidas = ORDEM_CONJUNTOS + ["lift_K6_%", "lift_K8_%"]
    print(tabela_mae[colunas_mae_exibidas].to_string())

    comparacao.to_csv(diretorio_tabela / NOME_ARQUIVO_SAIDA, index=False)
    print(f"\nsalvo: {NOME_ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
