"""Modelo 4c — clima_enxuto + vetor, sem ENSO, com CORTE DE MATURIDADE no alvo.

Corrige o bug do right-censoring: semanas de onset (SEM_PRI) cujos casos
confirmados ainda estao imaturos (dentro de MATURITY_WEEKS da data do extrato)
viram NaN em vez de zero falso. Re-roda o M0 (clima-enxuto s/ENSO) vs
M1 (+vetor) e compara com a versao contaminada (clima_enxuto_sem_enso_resultados.csv).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# --------------------------------------------------------------------- config
# Janela de confirmacao/encerramento da dengue: as ultimas semanas ainda estao
# sendo confirmadas e por isso o alvo delas e cortado (vira NaN) para nao entrar
# como zero/baixo falso no treino (right-censoring do SINAN).
SEMANAS_CORTE_MATURIDADE = 12

# Nome do subdiretorio que identifica a raiz do projeto (torna o script
# executavel de qualquer subpasta).
MARCADOR_RAIZ = "Raspagem"

# Coluna alvo (volume de casos confirmados) e colunas de identificacao usadas
# nos calculos temporais.
COLUNA_ALVO = "casos_confirmados"
COLUNA_FONTE = "fonte"
COLUNA_DATA = "data_inicio_semana_epidemi"
COLUNA_SEMANA = "semana"

# Nome do arquivo de resultados gravado ao final.
NOME_ARQUIVO_SAIDA = "clima_enxuto_maturidade_resultados.csv"

# Colunas cujos lags 1-4 sao gerados (na ordem exata em que entram no DataFrame).
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

# Constantes de dominio dos calculos (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4

# Colunas de contagem bruta de vetor descartadas da modelagem e colunas de ENSO
# (este modelo e "sem ENSO"); ambas entram na lista de colunas ignoradas.
COLUNAS_DESCARTADAS = ["aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas"]
COLUNAS_ENSO = ["nino34_anom", "oni"]
COLUNAS_IGNORADAS_BASE = [
    "fonte",
    "SE",
    "data_inicio_semana_epidemi",
    "ano",
    "semana",
    "interpolado",
]

# Padroes de nome que classificam uma coluna como de vetor ou de clima
# (casamento por SUBSTRING, mantendo a semantica exata do script original).
PADROES_VETOR = ("aedes", "armadilha", "vetor")
PADROES_CLIMA = ("temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva")

# Hiperparametros do LightGBM (mantidos identicos ao original, inclusive
# n_jobs=-1, que usa todos os nucleos).
PARAMETROS_LGBM = dict(
    n_estimators=250,
    learning_rate=0.05,
    num_leaves=15,
    min_child_samples=5,
    verbose=-1,
    n_jobs=-1,
)

# Horizontes (em semanas) usados na SELECAO de clima por ganho e a fracao
# inicial de cada serie usada como treino nessa selecao.
HORIZONTES_SELECAO_CLIMA = (1, 4, 8)
FRACAO_TREINO_SELECAO = 0.60

# Configuracao do walk-forward de avaliacao.
HORIZONTES_WALK_FORWARD = range(1, 13)
MINIMO_SEMANAS_TREINO = 104
PASSO_WALK_FORWARD = 2

# Quantidades de features de clima testadas (top-K do ranking de ganho).
VALORES_K = (6, 8)

# Arredondamentos das tabelas exibidas no console.
CASAS_DECIMAIS_R2 = 3
CASAS_DECIMAIS_MAE = 1

# Ordem das colunas (conjuntos de modelos) exibida nas tabelas de metricas.
ORDEM_CONJUNTOS = ["M0_clima6", "M1_clima6_vetor", "M0_clima8", "M1_clima8_vetor"]


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
    raise FileNotFoundError("raiz nao encontrada")


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap entre
    os blocos de dados de fontes diferentes.

    Args:
        serie: Serie temporal de um unico bloco/fonte.

    Returns:
        Serie com a media movel de 4 semanas (NaN nas 3 primeiras posicoes).
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def carregar_tabela_modelagem(caminho_tabela_final: Path) -> pd.DataFrame:
    """Le a tabela_final e a ordena por fonte e data.

    Args:
        caminho_tabela_final: Caminho do CSV tabela_final.csv.

    Returns:
        DataFrame semanal ordenado por (fonte, data) com indice reiniciado.
    """
    dados_modelagem = pd.read_csv(caminho_tabela_final, parse_dates=[COLUNA_DATA])
    dados_modelagem = dados_modelagem.sort_values([COLUNA_FONTE, COLUNA_DATA]).reset_index(drop=True)
    return dados_modelagem


def aplicar_corte_de_maturidade(dados_modelagem: pd.DataFrame) -> pd.DataFrame:
    """Zera-para-NaN o alvo das semanas ainda imaturas (right-censoring).

    As ultimas SEMANAS_CORTE_MATURIDADE semanas (a partir da data mais recente)
    ainda estao em confirmacao; seus casos confirmados sao substituidos por NaN
    para nao entrarem como zeros/baixos falsos. Imprime quantas semanas foram
    afetadas (mesma mensagem do script original).

    Args:
        dados_modelagem: Tabela semanal ordenada por (fonte, data).

    Returns:
        O mesmo DataFrame, com o alvo das semanas imaturas ajustado para NaN.
    """
    data_referencia = dados_modelagem[COLUNA_DATA].max()
    limite_maturidade = data_referencia - pd.Timedelta(weeks=SEMANAS_CORTE_MATURIDADE)
    semanas_imaturas = dados_modelagem[COLUNA_DATA] > limite_maturidade
    tinha_valor_de_alvo = dados_modelagem[COLUNA_ALVO].notna()
    quantidade_cortada = int((semanas_imaturas & tinha_valor_de_alvo).sum())
    dados_modelagem.loc[semanas_imaturas, COLUNA_ALVO] = np.nan
    print(
        f"corte de maturidade: onset > {limite_maturidade.date()} -> "
        f"{quantidade_cortada} semanas viraram NaN (eram zero/baixo falso)"
    )
    return dados_modelagem


def construir_features_temporais(dados_modelagem: pd.DataFrame) -> pd.DataFrame:
    """Cria lags 1-4, medias moveis de 4 semanas e sazonalidade.

    Todas as features temporais sao calculadas POR BLOCO (groupby na fonte), de
    modo que lags e medias moveis nunca atravessem o gap entre blocos.

    Args:
        dados_modelagem: Tabela semanal ordenada por (fonte, data).

    Returns:
        O mesmo DataFrame com as colunas de features adicionadas ao final.
    """
    grupos_por_fonte = dados_modelagem.groupby(COLUNA_FONTE, group_keys=False)

    for coluna_origem in COLUNAS_PARA_LAG:
        for numero_de_semanas in LAGS_SEMANAS:
            nome_coluna_lag = f"{coluna_origem}_lag{numero_de_semanas}"
            dados_modelagem[nome_coluna_lag] = grupos_por_fonte[coluna_origem].shift(numero_de_semanas)

    dados_modelagem["casos_mm4"] = grupos_por_fonte["casos_confirmados"].transform(media_movel_4_semanas)
    dados_modelagem["vetor_mm4"] = grupos_por_fonte["aedes_aegypti_por_armadilha"].transform(
        media_movel_4_semanas
    )

    angulo_sazonal = 2 * np.pi * dados_modelagem[COLUNA_SEMANA] / SEMANAS_POR_ANO
    dados_modelagem["sem_sin"] = np.sin(angulo_sazonal)
    dados_modelagem["sem_cos"] = np.cos(angulo_sazonal)
    return dados_modelagem


def nome_contem_algum_padrao(nome_coluna: str, padroes: tuple[str, ...]) -> bool:
    """Indica se o nome da coluna contem (por substring) algum dos padroes.

    Args:
        nome_coluna: Nome da coluna a testar.
        padroes: Padroes de substring a procurar.

    Returns:
        True se algum padrao aparecer como substring do nome da coluna.
    """
    for padrao in padroes:
        if padrao in nome_coluna:
            return True
    return False


def classificar_colunas(dados_modelagem: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Separa as colunas candidatas em vetor, clima e nucleo.

    Ignora identificadores, colunas de contagem bruta de vetor e colunas de
    ENSO. Entre as restantes (na ordem em que aparecem no DataFrame), classifica
    como vetor ou clima quem casa os respectivos padroes de substring; o que
    sobra e o nucleo (autorregressivo/sazonal).

    Args:
        dados_modelagem: Tabela ja com as features temporais construidas.

    Returns:
        Tripla (colunas_vetor, colunas_clima, colunas_nucleo), cada uma na ordem
        das colunas do DataFrame.
    """
    colunas_ignoradas = COLUNAS_IGNORADAS_BASE + COLUNAS_DESCARTADAS + COLUNAS_ENSO

    colunas_candidatas = []
    for nome_coluna in dados_modelagem.columns:
        if nome_coluna not in colunas_ignoradas:
            colunas_candidatas.append(nome_coluna)

    colunas_vetor = []
    for nome_coluna in colunas_candidatas:
        if nome_contem_algum_padrao(nome_coluna, PADROES_VETOR):
            colunas_vetor.append(nome_coluna)

    colunas_clima = []
    for nome_coluna in colunas_candidatas:
        if nome_contem_algum_padrao(nome_coluna, PADROES_CLIMA):
            colunas_clima.append(nome_coluna)

    colunas_nucleo = []
    for nome_coluna in colunas_candidatas:
        if nome_coluna not in colunas_vetor and nome_coluna not in colunas_clima:
            colunas_nucleo.append(nome_coluna)

    return colunas_vetor, colunas_clima, colunas_nucleo


def adicionar_alvo_horizonte(dados_modelagem: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Adiciona o alvo deslocado h semanas a frente e a sazonalidade do alvo.

    Args:
        dados_modelagem: Tabela ja com as features temporais construidas.
        horizonte: Numero de semanas a frente a prever.

    Returns:
        Uma COPIA do DataFrame com as colunas y_h, alvo_sin e alvo_cos.
    """
    grupos_por_fonte = dados_modelagem.groupby(COLUNA_FONTE, group_keys=False)
    dados_com_alvo = dados_modelagem.copy()
    dados_com_alvo["y_h"] = grupos_por_fonte[COLUNA_ALVO].shift(-horizonte)
    semana_do_alvo = grupos_por_fonte[COLUNA_SEMANA].shift(-horizonte)
    dados_com_alvo["alvo_sin"] = np.sin(2 * np.pi * semana_do_alvo / SEMANAS_POR_ANO)
    dados_com_alvo["alvo_cos"] = np.cos(2 * np.pi * semana_do_alvo / SEMANAS_POR_ANO)
    return dados_com_alvo


def calcular_ranking_clima(
    dados_modelagem: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_clima: list[str],
) -> pd.Series:
    """Ordena as features de clima pelo ganho acumulado do LightGBM (sem leakage).

    Para cada horizonte de selecao, treina um LightGBM na fracao inicial da
    serie (dados iniciais) usando nucleo + clima + sazonalidade do alvo, soma o
    ganho por feature de clima e ordena de forma decrescente.

    Args:
        dados_modelagem: Tabela ja com as features temporais construidas.
        colunas_nucleo: Colunas nucleo (autorregressivas/sazonais).
        colunas_clima: Colunas de clima candidatas.

    Returns:
        Serie com o ganho acumulado por feature de clima, ordenada de forma
        decrescente.
    """
    ganho_acumulado = pd.Series(0.0, index=colunas_clima)
    for horizonte in HORIZONTES_SELECAO_CLIMA:
        dados_com_alvo = adicionar_alvo_horizonte(dados_modelagem, horizonte)
        features = colunas_nucleo + colunas_clima + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values(COLUNA_DATA)
            .reset_index(drop=True)
        )
        indice_fim_treino = int(len(dados_validos) * FRACAO_TREINO_SELECAO)
        treino = dados_validos.iloc[:indice_fim_treino]
        modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(treino[features], treino["y_h"])
        ganho_por_feature = pd.Series(
            modelo.booster_.feature_importance(importance_type="gain"), index=features
        )
        ganho_do_clima = ganho_por_feature.reindex(colunas_clima).fillna(0)
        ganho_acumulado = ganho_acumulado.add(ganho_do_clima, fill_value=0)

    ranking_clima = ganho_acumulado.sort_values(ascending=False)
    return ranking_clima


def executar_walk_forward(
    dados_modelagem: pd.DataFrame,
    colunas_features: list[str],
    horizontes: range = HORIZONTES_WALK_FORWARD,
    minimo_treino: int = MINIMO_SEMANAS_TREINO,
    passo: int = PASSO_WALK_FORWARD,
) -> pd.DataFrame:
    """Walk-forward expansivel de regressao para varios horizontes.

    Em cada horizonte, monta o alvo deslocado, remove linhas incompletas e, a
    partir de minimo_treino, treina em todo o historico ate a semana i e preve a
    semana i (passo em passo).

    Args:
        dados_modelagem: Tabela ja com as features temporais construidas.
        colunas_features: Colunas de entrada (sem a sazonalidade do alvo, que e
            adicionada aqui).
        horizontes: Horizontes (em semanas) a avaliar.
        minimo_treino: Tamanho minimo do treino antes de comecar a prever.
        passo: Espacamento entre as semanas de teste.

    Returns:
        DataFrame com uma linha por semana de teste e as colunas h, real e pred.
    """
    linhas_resultado = []
    for horizonte in horizontes:
        dados_com_alvo = adicionar_alvo_horizonte(dados_modelagem, horizonte)
        features = colunas_features + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_com_alvo.dropna(subset=features + ["y_h"])
            .sort_values(COLUNA_DATA)
            .reset_index(drop=True)
        )
        for indice_corte in range(minimo_treino, len(dados_validos), passo):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]
            modelo = LGBMRegressor(**PARAMETROS_LGBM).fit(treino[features], treino["y_h"])
            linhas_resultado.append(
                {
                    "h": horizonte,
                    "real": teste["y_h"].values[0],
                    "pred": modelo.predict(teste[features])[0],
                }
            )
    return pd.DataFrame(linhas_resultado)


def calcular_metricas(resultado_walk_forward: pd.DataFrame, nome_conjunto: str) -> list[dict]:
    """Calcula MAE e R2 por horizonte para um conjunto de previsoes.

    Args:
        resultado_walk_forward: Saida de executar_walk_forward (colunas h, real,
            pred).
        nome_conjunto: Rotulo do conjunto de modelos (ex.: 'M0_clima6').

    Returns:
        Lista de dicionarios, um por horizonte, com conjunto, h, n, MAE e R2.
    """
    linhas_metricas = []
    for horizonte, previsoes_do_horizonte in resultado_walk_forward.groupby("h"):
        linhas_metricas.append(
            {
                "conjunto": nome_conjunto,
                "h": horizonte,
                "n": len(previsoes_do_horizonte),
                "MAE": mean_absolute_error(
                    previsoes_do_horizonte["real"], previsoes_do_horizonte["pred"]
                ),
                "R2": r2_score(
                    previsoes_do_horizonte["real"], previsoes_do_horizonte["pred"]
                ),
            }
        )
    return linhas_metricas


def avaliar_modelos(
    dados_modelagem: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_vetor: list[str],
    ranking_clima: pd.Series,
) -> pd.DataFrame:
    """Roda o walk-forward do M0 (so-clima) e do M1 (+vetor) para cada K.

    Para cada K em VALORES_K, seleciona as K features de clima de maior ganho e
    avalia dois conjuntos: nucleo + clima (M0) e nucleo + clima + vetor (M1).

    Args:
        dados_modelagem: Tabela ja com as features temporais construidas.
        colunas_nucleo: Colunas nucleo (autorregressivas/sazonais).
        colunas_vetor: Colunas de vetor.
        ranking_clima: Ranking de clima por ganho (decrescente).

    Returns:
        DataFrame empilhado de metricas por conjunto e horizonte.
    """
    linhas_metricas = []
    for quantidade_clima in VALORES_K:
        clima_top = ranking_clima.head(quantidade_clima).index.tolist()
        resultado_so_clima = executar_walk_forward(dados_modelagem, colunas_nucleo + clima_top)
        linhas_metricas += calcular_metricas(resultado_so_clima, f"M0_clima{quantidade_clima}")
        resultado_com_vetor = executar_walk_forward(
            dados_modelagem, colunas_nucleo + clima_top + colunas_vetor
        )
        linhas_metricas += calcular_metricas(
            resultado_com_vetor, f"M1_clima{quantidade_clima}_vetor"
        )
    return pd.DataFrame(linhas_metricas)


def montar_tabelas_de_exibicao(
    comparacao: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Constroi os pivots de R2, MAE (com lift do vetor) e contagem de pontos.

    Args:
        comparacao: DataFrame empilhado de metricas (colunas conjunto, h, n,
            MAE, R2).

    Returns:
        Tripla (tabela_r2, tabela_mae, tabela_pontos). A tabela de MAE inclui as
        colunas de lift marginal do vetor por K.
    """
    tabela_r2 = comparacao.pivot(index="h", columns="conjunto", values="R2").round(CASAS_DECIMAIS_R2)
    tabela_mae = comparacao.pivot(index="h", columns="conjunto", values="MAE").round(CASAS_DECIMAIS_MAE)
    tabela_pontos = comparacao.pivot(index="h", columns="conjunto", values="n")

    for quantidade_clima in VALORES_K:
        mae_so_clima = tabela_mae[f"M0_clima{quantidade_clima}"]
        mae_com_vetor = tabela_mae[f"M1_clima{quantidade_clima}_vetor"]
        lift_percentual = ((mae_so_clima - mae_com_vetor) / mae_so_clima * 100).round(1)
        tabela_mae[f"lift_K{quantidade_clima}_%"] = lift_percentual

    return tabela_r2, tabela_mae, tabela_pontos


def imprimir_resultados(
    tabela_r2: pd.DataFrame,
    tabela_mae: pd.DataFrame,
    tabela_pontos: pd.DataFrame,
) -> None:
    """Imprime as tabelas de R2 e MAE no mesmo formato do script original.

    Args:
        tabela_r2: Pivot de R2 por horizonte.
        tabela_mae: Pivot de MAE por horizonte, com colunas de lift.
        tabela_pontos: Pivot da contagem de pontos de teste por horizonte.
    """
    quantidade_pontos_h1 = int(tabela_pontos["M0_clima6"].iloc[0])
    print(
        f"\npontos de teste por horizonte (h=1): {quantidade_pontos_h1} "
        f"(era ~maior antes do corte)"
    )
    print("\n=== R2 por horizonte (sem ENSO, COM corte de maturidade) ===")
    print(tabela_r2[ORDEM_CONJUNTOS].to_string())
    print("\n=== MAE + lift marginal do vetor ===")
    print(tabela_mae[ORDEM_CONJUNTOS + ["lift_K6_%", "lift_K8_%"]].to_string())


def main() -> None:
    """Orquestra o pipeline do Modelo 4c e grava a tabela de resultados."""
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela_modelagem = raiz_do_projeto / "Bases de dados" / "tabela_modelagem"
    caminho_tabela_final = diretorio_tabela_modelagem / "tabela_final.csv"

    dados_modelagem = carregar_tabela_modelagem(caminho_tabela_final)
    dados_modelagem = aplicar_corte_de_maturidade(dados_modelagem)
    dados_modelagem = construir_features_temporais(dados_modelagem)

    colunas_vetor, colunas_clima, colunas_nucleo = classificar_colunas(dados_modelagem)

    ranking_clima = calcular_ranking_clima(dados_modelagem, colunas_nucleo, colunas_clima)
    print("clima top-8:", ranking_clima.head(8).index.tolist())

    comparacao = avaliar_modelos(dados_modelagem, colunas_nucleo, colunas_vetor, ranking_clima)

    tabela_r2, tabela_mae, tabela_pontos = montar_tabelas_de_exibicao(comparacao)
    imprimir_resultados(tabela_r2, tabela_mae, tabela_pontos)

    caminho_saida = diretorio_tabela_modelagem / NOME_ARQUIVO_SAIDA
    comparacao.to_csv(caminho_saida, index=False)
    print(f"\nsalvo: {NOME_ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
