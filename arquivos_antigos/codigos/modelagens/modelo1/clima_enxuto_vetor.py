"""clima_enxuto + vetor — o lift marginal real (M0 vs M1).

Pergunta: depois de PODAR o clima para suas poucas features que importam
(M0, o baseline parcimonioso "da literatura"), adicionar a densidade de
Aedes aegypti (M1) reduz o erro de forma consistente?

- M0 = nucleo + clima_enxuto(top-K por importancia)
- M1 = M0 + vetor_limpo (so densidade de aegypti: 6 feats)
- referencias (do lift_limpo_resultados.csv): so_clima(52), so_vetor(14)

Selecao de clima: gain do LightGBM, calculada SO nas linhas iniciais de
treino (primeiros 60% de cada horizonte), pooled sobre h in {1,4,8} -> sem
leakage do periodo de teste. Roda para K=6 e K=8.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# --------------------------------------------------------------------- config
# Coluna alvo da previsao (volume de casos confirmados de dengue).
COLUNA_ALVO = "casos_confirmados"

# Colunas de origem cujos lags 1-4 sao gerados como features autorregressivas.
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

# Media movel de 4 semanas de casos e de vetor (por bloco de fonte).
JANELA_MEDIA_MOVEL_SEMANAS = 4
SEMANAS_POR_ANO = 52

# Colunas que NAO devem virar features (identificadores, metadados e contagens
# de vetor brutas que sao substituidas pela densidade por armadilha).
COLUNAS_VETOR_BRUTO_DESCARTADAS = [
    "aedes_aegypti",
    "aedes_albopictus",
    "culex_sp",
    "numero_de_armadilhas",
]
COLUNAS_IGNORADAS = [
    "fonte",
    "SE",
    "data_inicio_semana_epidemi",
    "ano",
    "semana",
    "interpolado",
] + COLUNAS_VETOR_BRUTO_DESCARTADAS

# Uma feature e classificada como vetor/clima se seu nome contiver um destes
# padroes (substring). O nucleo e o que sobra (autorregressivo + sazonalidade).
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

# Hiperparametros do LightGBM (mesmos dos Modelos 1-5).
PARAMETROS_LGBM = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "verbose": -1,
    "n_jobs": -1,
}

# Horizontes usados SO na selecao de clima (gain pooled sobre estes h).
HORIZONTES_SELECAO_CLIMA = (1, 4, 8)
# Fracao inicial de cada horizonte usada para calcular o gain (epoca de treino,
# sem leakage do periodo de teste).
FRACAO_TREINO_SELECAO = 0.60
# Quantidade de features de clima exibidas no ranking impresso.
TOP_RANKING_EXIBIDO = 15

# Quantidades de features de clima enxuto (K) testadas em M0 e M1.
VALORES_K_CLIMA_ENXUTO = (6, 8)

# Walk-forward de avaliacao dos modelos.
HORIZONTES_AVALIACAO = range(1, 13)
MINIMO_TREINO = 104
PASSO_WALK_FORWARD = 2

# Conjuntos de referencia (do run anterior) e ordem de exibicao das colunas.
CONJUNTOS_REFERENCIA = ["so_clima", "so_vetor"]
CASAS_DECIMAIS_R2 = 3
CASAS_DECIMAIS_MAE = 1
CASAS_DECIMAIS_RANKING = 0
CASAS_DECIMAIS_LIFT = 1


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


def media_movel_janela_padrao(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap entre
    os blocos de dados de fontes distintas.

    Args:
        serie: Serie temporal de um unico bloco de fonte.

    Returns:
        Serie com a media movel de JANELA_MEDIA_MOVEL_SEMANAS semanas.
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def carregar_tabela_final(caminho_tabela_final: Path) -> pd.DataFrame:
    """Le a tabela_final e a ordena por fonte e data.

    Args:
        caminho_tabela_final: Caminho do CSV tabela_final.csv.

    Returns:
        DataFrame ordenado por ['fonte', 'data_inicio_semana_epidemi'] com o
        indice reiniciado.
    """
    tabela_final = pd.read_csv(
        caminho_tabela_final, parse_dates=["data_inicio_semana_epidemi"]
    )
    tabela_final = tabela_final.sort_values(
        ["fonte", "data_inicio_semana_epidemi"]
    ).reset_index(drop=True)
    return tabela_final


def construir_features_temporais(tabela_final: pd.DataFrame) -> pd.DataFrame:
    """Cria lags, medias moveis e sazonalidade da semana epidemiologica.

    Todas as features temporais sao calculadas POR BLOCO (groupby em 'fonte'),
    de modo que lags e medias moveis nunca atravessem o gap entre os blocos.

    Args:
        tabela_final: Tabela semanal ordenada por fonte e data.

    Returns:
        O MESMO DataFrame com as colunas de features adicionadas (modificado in
        place, como no script original).
    """
    grupos_por_fonte = tabela_final.groupby("fonte", group_keys=False)

    for coluna_origem in COLUNAS_PARA_LAG:
        for numero_de_semanas in LAGS_SEMANAS:
            nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
            tabela_final[nome_coluna_lag] = grupos_por_fonte[coluna_origem].shift(
                numero_de_semanas
            )

    tabela_final["casos_mm4"] = grupos_por_fonte["casos_confirmados"].transform(
        media_movel_janela_padrao
    )
    tabela_final["vetor_mm4"] = grupos_por_fonte[
        "aedes_aegypti_por_armadilha"
    ].transform(media_movel_janela_padrao)

    angulo_sazonal = 2 * np.pi * tabela_final["semana"] / SEMANAS_POR_ANO
    tabela_final["sem_sin"] = np.sin(angulo_sazonal)
    tabela_final["sem_cos"] = np.cos(angulo_sazonal)
    return tabela_final


def nome_contem_algum_padrao(nome_coluna: str, padroes: tuple[str, ...]) -> bool:
    """Indica se o nome da coluna contem algum dos padroes (substring).

    Args:
        nome_coluna: Nome da coluna a testar.
        padroes: Padroes de substring a procurar no nome.

    Returns:
        True se algum padrao aparece como substring do nome.
    """
    for padrao in padroes:
        if padrao in nome_coluna:
            return True
    return False


def classificar_features(
    tabela_final: pd.DataFrame,
) -> tuple[list[str], list[str], list[str]]:
    """Separa as features candidatas em vetor, clima e nucleo.

    Percorre as colunas na ordem do DataFrame (a ordem importa: define a ordem
    das features passadas aos modelos), descarta as colunas ignoradas e
    classifica o restante por padrao de nome. O nucleo e o que nao e vetor nem
    clima (autorregressivo + sazonalidade).

    Args:
        tabela_final: Tabela ja com todas as features construidas.

    Returns:
        Tupla (colunas_vetor, colunas_clima, colunas_nucleo), cada uma na ordem
        das colunas do DataFrame.
    """
    todas_as_features = []
    for nome_coluna in tabela_final.columns:
        if nome_coluna not in COLUNAS_IGNORADAS:
            todas_as_features.append(nome_coluna)

    colunas_vetor = []
    for nome_coluna in todas_as_features:
        if nome_contem_algum_padrao(nome_coluna, PADROES_VETOR):
            colunas_vetor.append(nome_coluna)

    colunas_clima = []
    for nome_coluna in todas_as_features:
        if nome_contem_algum_padrao(nome_coluna, PADROES_CLIMA):
            colunas_clima.append(nome_coluna)

    colunas_nucleo = []
    for nome_coluna in todas_as_features:
        if nome_coluna not in colunas_vetor and nome_coluna not in colunas_clima:
            colunas_nucleo.append(nome_coluna)

    return colunas_vetor, colunas_clima, colunas_nucleo


def construir_alvo_horizonte(tabela_final: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Cria o alvo h semanas a frente e a sazonalidade da semana-alvo.

    Args:
        tabela_final: Tabela ja com as features construidas.
        horizonte: Numero de semanas a frente a prever.

    Returns:
        Uma COPIA do DataFrame com as colunas 'y_h', 'alvo_sin' e 'alvo_cos'.
    """
    grupos_por_fonte = tabela_final.groupby("fonte", group_keys=False)
    dados_com_alvo = tabela_final.copy()
    dados_com_alvo["y_h"] = grupos_por_fonte[COLUNA_ALVO].shift(-horizonte)

    semana_alvo = grupos_por_fonte["semana"].shift(-horizonte)
    dados_com_alvo["alvo_sin"] = np.sin(2 * np.pi * semana_alvo / SEMANAS_POR_ANO)
    dados_com_alvo["alvo_cos"] = np.cos(2 * np.pi * semana_alvo / SEMANAS_POR_ANO)
    return dados_com_alvo


def calcular_ranking_clima(
    tabela_final: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_clima: list[str],
) -> pd.Series:
    """Ranqueia as features de clima por gain pooled, sem leakage de teste.

    Para cada horizonte de selecao, treina um LightGBM SO nos primeiros 60% das
    linhas validas (epoca de treino), coleta o gain de cada feature e acumula o
    gain das features de clima. O ranking final e o gain acumulado, em ordem
    decrescente.

    Args:
        tabela_final: Tabela ja com as features construidas.
        colunas_nucleo: Features de nucleo (autorregressivo + sazonalidade base).
        colunas_clima: Features de clima candidatas a ranquear.

    Returns:
        Serie de importancia acumulada indexada pelas features de clima, ordenada
        de forma decrescente.
    """
    importancia_acumulada = pd.Series(0.0, index=colunas_clima)

    for horizonte in HORIZONTES_SELECAO_CLIMA:
        dados_com_alvo = construir_alvo_horizonte(tabela_final, horizonte)
        features = colunas_nucleo + colunas_clima + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values("data_inicio_semana_epidemi")
            .reset_index(drop=True)
        )

        indice_corte = int(len(dados_validos) * FRACAO_TREINO_SELECAO)
        treino = dados_validos.iloc[:indice_corte]

        modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(treino[features], treino["y_h"])
        gain_do_horizonte = pd.Series(
            modelo.booster_.feature_importance(importance_type="gain"), index=features
        )
        importancia_acumulada = importancia_acumulada.add(
            gain_do_horizonte.reindex(colunas_clima).fillna(0), fill_value=0
        )

    ranking = importancia_acumulada.sort_values(ascending=False)
    return ranking


def executar_walk_forward(
    tabela_final: pd.DataFrame,
    features_do_modelo: list[str],
    horizontes: range = HORIZONTES_AVALIACAO,
    minimo_treino: int = MINIMO_TREINO,
    passo: int = PASSO_WALK_FORWARD,
) -> pd.DataFrame:
    """Walk-forward expansivel de regressao para cada horizonte.

    Para cada horizonte, monta o alvo, descarta linhas incompletas, e avanca em
    passos treinando em todo o historico ate a linha i e prevendo a linha i.

    Args:
        tabela_final: Tabela ja com as features construidas.
        features_do_modelo: Features de entrada do modelo (a sazonalidade do alvo
            e adicionada aqui).
        horizontes: Horizontes de previsao (em semanas).
        minimo_treino: Numero minimo de linhas de treino antes de prever.
        passo: Espacamento entre as linhas de teste.

    Returns:
        DataFrame com uma linha por passo e as colunas: h, real, pred.
    """
    linhas_resultado = []
    for horizonte in horizontes:
        dados_com_alvo = construir_alvo_horizonte(tabela_final, horizonte)
        features = features_do_modelo + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values("data_inicio_semana_epidemi")
            .reset_index(drop=True)
        )

        for indice_corte in range(minimo_treino, len(dados_validos), passo):
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


def calcular_metricas_por_horizonte(
    resultado_walk_forward: pd.DataFrame,
    nome_conjunto: str,
) -> list[dict]:
    """Calcula MAE e R2 por horizonte de um resultado de walk-forward.

    Args:
        resultado_walk_forward: DataFrame com colunas h, real e pred.
        nome_conjunto: Rotulo do conjunto de features (ex.: 'M0_clima6').

    Returns:
        Lista de dicionarios com conjunto, h, MAE e R2, um por horizonte.
    """
    metricas = []
    for horizonte, grupo in resultado_walk_forward.groupby("h"):
        metricas.append(
            {
                "conjunto": nome_conjunto,
                "h": horizonte,
                "MAE": mean_absolute_error(grupo["real"], grupo["pred"]),
                "R2": r2_score(grupo["real"], grupo["pred"]),
            }
        )
    return metricas


def avaliar_modelos_por_k(
    tabela_final: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_vetor: list[str],
    ranking_clima: pd.Series,
) -> pd.DataFrame:
    """Avalia M0 (so clima enxuto) e M1 (clima enxuto + vetor) para cada K.

    Para cada K, seleciona as top-K features de clima do ranking, imprime-as, e
    roda o walk-forward de M0 e de M1, coletando as metricas por horizonte.

    Args:
        tabela_final: Tabela ja com as features construidas.
        colunas_nucleo: Features de nucleo.
        colunas_vetor: Features de vetor (densidade de aegypti).
        ranking_clima: Ranking de importancia das features de clima.

    Returns:
        DataFrame com as metricas de M0 e M1 de todos os K, empilhadas.
    """
    linhas_metricas = []
    for quantidade_clima in VALORES_K_CLIMA_ENXUTO:
        clima_top = ranking_clima.head(quantidade_clima).index.tolist()
        print(f"\n=== clima_enxuto K={quantidade_clima} ===\n{clima_top}")

        features_m0 = colunas_nucleo + clima_top
        resultado_m0 = executar_walk_forward(tabela_final, features_m0)
        linhas_metricas += calcular_metricas_por_horizonte(
            resultado_m0, f"M0_clima{quantidade_clima}"
        )

        features_m1 = colunas_nucleo + clima_top + colunas_vetor
        resultado_m1 = executar_walk_forward(tabela_final, features_m1)
        linhas_metricas += calcular_metricas_por_horizonte(
            resultado_m1, f"M1_clima{quantidade_clima}_vetor"
        )
    return pd.DataFrame(linhas_metricas)


def carregar_referencias(caminho_lift_limpo: Path) -> pd.DataFrame:
    """Le as metricas de referencia (so_clima, so_vetor) do run anterior.

    Args:
        caminho_lift_limpo: Caminho do CSV lift_limpo_resultados.csv.

    Returns:
        DataFrame com uma linha por (conjunto, h) para os conjuntos de
        referencia, com colunas conjunto, h, MAE e R2.
    """
    referencias = pd.read_csv(caminho_lift_limpo)
    referencias = (
        referencias[referencias.conjunto.isin(CONJUNTOS_REFERENCIA)]
        .groupby(["conjunto", "h"])[["MAE", "R2"]]
        .first()
        .reset_index()
    )
    return referencias


def montar_tabelas_comparativas(
    comparacao: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Pivota as metricas por horizonte e calcula o lift marginal do vetor.

    Args:
        comparacao: Metricas empilhadas (conjunto, h, MAE, R2) de M0/M1 e das
            referencias.

    Returns:
        Tupla (tabela_r2, tabela_mae, ordem_colunas). tabela_r2 tem o R2 por
        horizonte; tabela_mae tem o MAE por horizonte mais as colunas de lift
        percentual de cada K; ordem_colunas e a ordem de exibicao dos conjuntos.
    """
    tabela_r2 = comparacao.pivot(index="h", columns="conjunto", values="R2").round(
        CASAS_DECIMAIS_R2
    )
    tabela_mae = comparacao.pivot(index="h", columns="conjunto", values="MAE").round(
        CASAS_DECIMAIS_MAE
    )

    for quantidade_clima in VALORES_K_CLIMA_ENXUTO:
        coluna_m0 = f"M0_clima{quantidade_clima}"
        coluna_m1 = f"M1_clima{quantidade_clima}_vetor"
        lift_percentual = (
            (tabela_mae[coluna_m0] - tabela_mae[coluna_m1]) / tabela_mae[coluna_m0] * 100
        ).round(CASAS_DECIMAIS_LIFT)
        tabela_mae[f"lift_K{quantidade_clima}_%"] = lift_percentual

    ordem_colunas = [
        "so_clima",
        "M0_clima6",
        "M1_clima6_vetor",
        "M0_clima8",
        "M1_clima8_vetor",
        "so_vetor",
    ]
    return tabela_r2, tabela_mae, ordem_colunas


def main() -> None:
    """Roda a selecao de clima, avalia M0 vs M1 e salva o resultado em CSV."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela_modelagem = raiz_do_projeto / "Bases de dados" / "tabela_modelagem"
    caminho_tabela_final = diretorio_tabela_modelagem / "tabela_final.csv"
    caminho_lift_limpo = diretorio_tabela_modelagem / "lift_limpo_resultados.csv"
    caminho_resultados = diretorio_tabela_modelagem / "clima_enxuto_vetor_resultados.csv"

    tabela_final = carregar_tabela_final(caminho_tabela_final)
    tabela_final = construir_features_temporais(tabela_final)
    colunas_vetor, colunas_clima, colunas_nucleo = classificar_features(tabela_final)

    # --- 1. Selecao do clima enxuto (gain, so dados iniciais, sem leakage) ---
    ranking_clima = calcular_ranking_clima(tabela_final, colunas_nucleo, colunas_clima)
    print("=== ranking de importancia do clima (gain, dados iniciais) ===")
    print(
        ranking_clima.head(TOP_RANKING_EXIBIDO).round(CASAS_DECIMAIS_RANKING).to_string()
    )

    # --- 2. M0 e M1 para K=6 e K=8 ---
    comparacao = avaliar_modelos_por_k(
        tabela_final, colunas_nucleo, colunas_vetor, ranking_clima
    )

    # --- 3. referencias do run anterior ---
    referencias = carregar_referencias(caminho_lift_limpo)
    comparacao = pd.concat([comparacao, referencias], ignore_index=True)

    tabela_r2, tabela_mae, ordem_colunas = montar_tabelas_comparativas(comparacao)
    print("\n=== R2 por horizonte ===")
    print(tabela_r2[ordem_colunas].to_string())
    print("\n=== MAE + lift marginal do vetor (M1 vs M0) ===")
    print(tabela_mae[ordem_colunas + ["lift_K6_%", "lift_K8_%"]].to_string())

    comparacao.to_csv(caminho_resultados, index=False)
    print("\nsalvo: clima_enxuto_vetor_resultados.csv")


if __name__ == "__main__":
    main()
