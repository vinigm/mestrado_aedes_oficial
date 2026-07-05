"""Modelo 6 — DETECCAO DE SURTO (classificacao), o alvo que a tese promete.

Reformula o eixo cidade de REGRESSAO de volume (Modelos 1-5; lift do vetor
NAO-significativo por Diebold-Mariano) para DETECCAO DE SURTO (evento/limiar),
com metricas de alarme e teste de McNemar para o lift do vetor NA TAREFA CERTA.
Implementa o passo #1 do plano de aproveitamento do Robson (aproveitamento_robson.md).

Dois experimentos:
  A) InfoDengue notificado (2010-2026, sem censura): "da pra detectar surto
     1-3 meses a frente em POA?" — viabilidade + baselines (sazonal, persistencia).
  B) tabela_final (SINAN confirmado, 2019-23 + 2025-26, COM vetor): so-clima
     vs clima+vetor na deteccao -> McNemar (apples-to-apples com a regressao).

Definicao de surto: casos_{t+h} >= limiar, limiar = percentil (P90/P95) calculado
SO no treino de cada passo (point-in-time, sem leakage). Multi-horizonte direto
h=4/8/12 sem (=1/2/3 meses) = a antecedencia do alarme. Walk-forward expansivel.
Baselines: sazonal (taxa de surto por semana epi.) e persistencia de estado.
n_jobs=1 -> reproducivel.

Saidas:
  - Bases de dados/tabela_modelagem/deteccao_surto_resultados.csv (metricas)
  - Bases de dados/tabela_modelagem/deteccao_surto_mcnemar.csv (McNemar Exp B)
"""
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from scipy.stats import binomtest, chi2
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)

# --------------------------------------------------------------------- config
# Horizontes de previsao, em semanas epidemiologicas. 4/8/12 sem = 1/2/3 meses
# de antecedencia do alarme (mesma leitura operacional dos Modelos 1-5).
HORIZONTES_SEMANAS = [4, 8, 12]

# Percentis de casos usados para definir "surto". O limiar em si e recalculado
# so no treino de cada passo do walk-forward (point-in-time, sem leakage).
PERCENTIS_SURTO = (90, 95)

# Hiperparametros do LightGBM. Arvores pequenas (num_leaves=15, min_child=5)
# por causa da serie curta; class_weight balanceia surto (raro) x nao-surto;
# n_jobs=1 garante reprodutibilidade exata entre execucoes.
PARAMETROS_LGBM = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "num_leaves": 15,
    "min_child_samples": 5,
    "class_weight": "balanced",
    "verbose": -1,
    "n_jobs": 1,
}

# Tamanho minimo do treino antes de comecar a prever (~2 anos de historico).
MINIMO_SEMANAS_TREINO = 104

# Colunas cujos lags 1-4 sao gerados (quando presentes no DataFrame de entrada).
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

# Constantes de dominio usadas nos calculos (evita numeros magicos soltos).
SEMANAS_POR_ANO = 52
JANELA_MEDIA_MOVEL_SEMANAS = 4
SEMANAS_CORTE_MATURIDADE = 12          # right-censoring do SINAN (Modelo 4c)
DISTANCIA_MAXIMA_SEMANA_SAZONAL = 1    # baseline sazonal: mesma sem.epi. +-1
LIMIAR_DECISAO_PROBABILIDADE = 0.5     # prob >= 0.5 -> preve surto
MINIMO_DISCORDANCIAS_QUI_QUADRADO = 25  # abaixo disso, McNemar exato (binomial)

# Colunas (e ordem) exibidas nas tabelas de metricas impressas no console.
COLUNAS_EXIBICAO = [
    "pctl", "h", "modelo", "n", "n_pos",
    "sensib", "espec", "f1", "bal_acc", "auc", "ap",
]


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
    raise FileNotFoundError("raiz nao encontrada")


RAIZ_DO_PROJETO = encontrar_raiz_do_projeto()
DIRETORIO_TABELA_MODELAGEM = RAIZ_DO_PROJETO / "Bases de dados" / "tabela_modelagem"
CAMINHO_INFODENGUE = (
    RAIZ_DO_PROJETO / "Bases de dados" / "infodengue_poa" / "infodengue_poa_dengue.csv"
)
CAMINHO_RESULTADOS = DIRETORIO_TABELA_MODELAGEM / "deteccao_surto_resultados.csv"
CAMINHO_MCNEMAR = DIRETORIO_TABELA_MODELAGEM / "deteccao_surto_mcnemar.csv"


@dataclasses.dataclass(frozen=True)
class ResultadoMcNemar:
    """Resultado do teste de McNemar entre dois classificadores pareados.

    Attributes:
        n_a_certo_b_errado: Casos em que o modelo A acertou e o B errou.
        n_a_errado_b_certo: Casos em que o modelo A errou e o B acertou.
        estatistica: Estatistica qui-quadrado com correcao de continuidade.
        valor_p: p-valor do teste (exato binomial quando ha poucas discordancias).
    """

    n_a_certo_b_errado: int
    n_a_errado_b_certo: int
    estatistica: float
    valor_p: float


def media_movel_4_semanas(serie: pd.Series) -> pd.Series:
    """Media movel de 4 semanas de uma serie de um unico bloco (fonte).

    Usada em transform() por grupo, para que a janela nao atravesse o gap
    entre os blocos de dados (Marilia 2019-23 x raspagem 2025-26).
    """
    return serie.rolling(JANELA_MEDIA_MOVEL_SEMANAS).mean()


def teste_mcnemar(
    acertos_modelo_a: np.ndarray,
    acertos_modelo_b: np.ndarray,
) -> ResultadoMcNemar:
    """Testa se dois classificadores diferem nos MESMOS pontos de teste.

    Compara os padroes de acerto/erro pareados. Usa o teste exato binomial
    quando ha poucas discordancias e a aproximacao qui-quadrado (com correcao
    de continuidade) caso contrario.

    Args:
        acertos_modelo_a: Booleanos indicando se o modelo A acertou cada ponto.
        acertos_modelo_b: Booleanos indicando se o modelo B acertou cada ponto.

    Returns:
        ResultadoMcNemar com as contagens de discordancia, a estatistica e o
        p-valor. Quando nao ha discordancia alguma, retorna estatistica 0.0 e
        p-valor 1.0.
    """
    acertos_a = np.asarray(acertos_modelo_a, bool)
    acertos_b = np.asarray(acertos_modelo_b, bool)
    n_a_certo_b_errado = int(np.sum(acertos_a & ~acertos_b))
    n_a_errado_b_certo = int(np.sum(~acertos_a & acertos_b))
    n_discordancias = n_a_certo_b_errado + n_a_errado_b_certo

    if n_discordancias == 0:
        return ResultadoMcNemar(n_a_certo_b_errado, n_a_errado_b_certo, 0.0, 1.0)

    # Estatistica qui-quadrado de McNemar com correcao de continuidade (-1).
    diferenca_absoluta = abs(n_a_certo_b_errado - n_a_errado_b_certo)
    estatistica = (diferenca_absoluta - 1) ** 2 / n_discordancias

    if n_discordancias < MINIMO_DISCORDANCIAS_QUI_QUADRADO:
        menor_discordancia = min(n_a_certo_b_errado, n_a_errado_b_certo)
        valor_p = binomtest(menor_discordancia, n_discordancias, 0.5).pvalue
    else:
        valor_p = float(chi2.sf(estatistica, 1))

    return ResultadoMcNemar(n_a_certo_b_errado, n_a_errado_b_certo, estatistica, valor_p)


def calcular_metricas_classificacao(
    y_real: pd.Series | np.ndarray,
    y_previsto: pd.Series | np.ndarray,
    probabilidade: pd.Series | np.ndarray | None = None,
) -> dict[str, float]:
    """Calcula as metricas de deteccao de surto de um bloco de previsoes.

    Args:
        y_real: Rotulo verdadeiro de surto (0/1) de cada ponto.
        y_previsto: Rotulo previsto de surto (0/1) de cada ponto.
        probabilidade: Probabilidade prevista de surto. Quando informada e ha
            as duas classes presentes, adiciona AUC e average precision.

    Returns:
        Dicionario de metricas. As chaves (e a ordem) sao mantidas fixas para
        que virem colunas estaveis ao empilhar em um DataFrame: n, n_pos, tp,
        fp, fn, tn, sensib, espec, precisao, f1, bal_acc e, opcionalmente, auc e ap.
        Sensibilidade/especificidade/precisao viram NaN quando o denominador e 0.
    """
    y_real_int = np.asarray(y_real, int)
    y_previsto_int = np.asarray(y_previsto, int)

    matriz_confusao = confusion_matrix(y_real_int, y_previsto_int, labels=[0, 1])
    verdadeiros_negativos, falsos_positivos, falsos_negativos, verdadeiros_positivos = (
        matriz_confusao.ravel()
    )

    positivos_reais = verdadeiros_positivos + falsos_negativos
    if positivos_reais > 0:
        sensibilidade = verdadeiros_positivos / positivos_reais
    else:
        sensibilidade = np.nan

    negativos_reais = verdadeiros_negativos + falsos_positivos
    if negativos_reais > 0:
        especificidade = verdadeiros_negativos / negativos_reais
    else:
        especificidade = np.nan

    positivos_previstos = verdadeiros_positivos + falsos_positivos
    if positivos_previstos > 0:
        precisao = verdadeiros_positivos / positivos_previstos
    else:
        precisao = np.nan

    metricas: dict[str, float] = {
        "n": len(y_real_int),
        "n_pos": int((y_real_int == 1).sum()),
        "tp": verdadeiros_positivos,
        "fp": falsos_positivos,
        "fn": falsos_negativos,
        "tn": verdadeiros_negativos,
        "sensib": sensibilidade,
        "espec": especificidade,
        "precisao": precisao,
        "f1": f1_score(y_real_int, y_previsto_int, zero_division=0),
        "bal_acc": balanced_accuracy_score(y_real_int, y_previsto_int),
    }

    if probabilidade is not None and len(np.unique(y_real_int)) == 2:
        metricas["auc"] = roc_auc_score(y_real_int, probabilidade)
        metricas["ap"] = average_precision_score(y_real_int, probabilidade)

    return metricas


def selecionar_colunas_por_prefixo(
    dados: pd.DataFrame,
    prefixos: tuple[str, ...],
) -> list[str]:
    """Retorna as colunas cujo nome comeca com um dos prefixos informados.

    A ordem segue a ordem das colunas no DataFrame, para que a lista de
    features passada ao modelo seja sempre a mesma (a ordem importa: fit e
    predict precisam usar exatamente as mesmas colunas na mesma ordem).
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
    """Cria lags, medias moveis e sazonalidade — a mesma receita dos Modelos 1-5.

    Todas as features temporais sao calculadas POR BLOCO (groupby na coluna de
    fonte), de modo que os lags e as medias moveis nunca atravessem o gap entre
    os dois blocos de dados.

    Args:
        dados: Tabela semanal com, no minimo, as colunas 'semana' e as colunas
            de origem listadas em COLUNAS_PARA_LAG que estiverem presentes.
        coluna_fonte: Coluna que identifica o bloco de dados de cada linha.

    Returns:
        Uma COPIA do DataFrame com as colunas de features adicionadas. O
        DataFrame original nao e modificado.
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

    angulo_sazonal = 2 * np.pi * dados_com_features["semana"] / SEMANAS_POR_ANO
    dados_com_features["sem_sin"] = np.sin(angulo_sazonal)
    dados_com_features["sem_cos"] = np.cos(angulo_sazonal)
    return dados_com_features


def executar_walk_forward_surto(
    dados: pd.DataFrame,
    features: list[str],
    coluna_fonte: str,
    horizonte: int,
    percentil: int,
    passo: int = 1,
) -> pd.DataFrame:
    """Walk-forward expansivel de deteccao de surto para um horizonte e percentil.

    Em cada passo, treina em todo o historico ate a semana i e preve a semana i.
    O alvo de cada passo e "surto" = casos_{t+h} >= percentil calculado SO no
    treino daquele passo (point-in-time, sem leakage). Tres previsores compartilham
    exatamente os mesmos folds e o mesmo limiar:
      - LGBM(features): clima(+vetor) + autorregressivo + sazonalidade;
      - sazonal: taxa de surto no treino na mesma semana epidemiologica (+-1) do alvo;
      - persistencia: surto_{t+h} = surto_t (o estado de surto atual persiste).

    Args:
        dados: Tabela semanal ja com as features construidas.
        features: Colunas de entrada do LightGBM (sem a sazonalidade do alvo,
            que e adicionada aqui).
        coluna_fonte: Coluna que identifica o bloco de dados.
        horizonte: Numero de semanas a frente a prever.
        percentil: Percentil de casos que define o limiar de surto.
        passo: Espacamento entre as semanas de teste (1 = todas as semanas).

    Returns:
        DataFrame com uma linha por semana de teste e as colunas: h, real, data,
        prob, pred, prob_saz, pred_saz, pred_pers.
    """
    dados_trabalho = dados.copy()
    grupos_por_fonte = dados_trabalho.groupby(coluna_fonte, group_keys=False)
    dados_trabalho["casos_h"] = grupos_por_fonte["casos"].shift(-horizonte)
    dados_trabalho["semana_alvo"] = grupos_por_fonte["semana"].shift(-horizonte)

    angulo_sazonal_alvo = 2 * np.pi * dados_trabalho["semana_alvo"] / SEMANAS_POR_ANO
    dados_trabalho["alvo_sin"] = np.sin(angulo_sazonal_alvo)
    dados_trabalho["alvo_cos"] = np.cos(angulo_sazonal_alvo)

    features_com_sazonalidade = features + ["alvo_sin", "alvo_cos"]
    colunas_obrigatorias = features_com_sazonalidade + ["casos_h", "casos", "semana_alvo"]
    dados_validos = (
        dados_trabalho.dropna(subset=colunas_obrigatorias)
        .sort_values("data")
        .reset_index(drop=True)
    )

    linhas_resultado = []
    for indice_corte in range(MINIMO_SEMANAS_TREINO, len(dados_validos), passo):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]

        limiar_surto = np.percentile(treino["casos_h"], percentil)
        surto_treino = (treino["casos_h"].to_numpy() >= limiar_surto).astype(int)
        surto_teste = int(teste["casos_h"].to_numpy()[0] >= limiar_surto)
        if len(np.unique(surto_treino)) < 2:
            # Treino degenerado (uma classe so): pula este passo.
            continue

        modelo = LGBMClassifier(**PARAMETROS_LGBM)
        modelo.fit(treino[features_com_sazonalidade], surto_treino)
        probabilidade_surto = float(
            modelo.predict_proba(teste[features_com_sazonalidade])[0, 1]
        )

        # Baseline sazonal: fracao de surtos no treino na mesma semana epi. (+-1)
        # da semana-alvo, com distancia circular no calendario de 52 semanas.
        semana_do_alvo = teste["semana_alvo"].to_numpy()[0]
        diferenca_semanas = np.abs(treino["semana_alvo"].to_numpy() - semana_do_alvo)
        distancia_circular = np.minimum(diferenca_semanas, SEMANAS_POR_ANO - diferenca_semanas)
        mascara_mesma_semana = distancia_circular <= DISTANCIA_MAXIMA_SEMANA_SAZONAL
        if mascara_mesma_semana.sum() > 0:
            probabilidade_sazonal = float(surto_treino[mascara_mesma_semana].mean())
        else:
            probabilidade_sazonal = float(surto_treino.mean())

        # Baseline persistencia: o estado de surto de agora (casos_t >= limiar) persiste.
        surto_persistencia = int(teste["casos"].to_numpy()[0] >= limiar_surto)

        linhas_resultado.append(
            {
                "h": horizonte,
                "real": surto_teste,
                "data": teste["data"].to_numpy()[0],
                "prob": probabilidade_surto,
                "pred": int(probabilidade_surto >= LIMIAR_DECISAO_PROBABILIDADE),
                "prob_saz": probabilidade_sazonal,
                "pred_saz": int(probabilidade_sazonal >= LIMIAR_DECISAO_PROBABILIDADE),
                "pred_pers": surto_persistencia,
            }
        )
    return pd.DataFrame(linhas_resultado)


def preparar_infodengue() -> pd.DataFrame:
    """Le e prepara a serie InfoDengue de POA para o Experimento A.

    Renomeia a data, deriva ano/semana epidemiologica a partir da coluna SE,
    marca a fonte, mapeia temperatura/umidade medias para os nomes usados pelas
    features e adiciona as features temporais.

    Returns:
        DataFrame semanal do InfoDengue pronto para o walk-forward.
    """
    infodengue = pd.read_csv(CAMINHO_INFODENGUE, parse_dates=["data_iniSE"]).rename(
        columns={"data_iniSE": "data"}
    )
    infodengue = infodengue.sort_values("data").reset_index(drop=True)
    infodengue["ano"] = infodengue["SE"].astype(str).str[:4].astype(int)
    infodengue["semana"] = infodengue["SE"].astype(str).str[4:].astype(int)
    infodengue["fonte"] = "infodengue"
    infodengue["temp_media"] = infodengue["tempmed"]
    infodengue["umid_media"] = infodengue["umidmed"]
    return construir_features_temporais(infodengue)


def rodar_experimento_a(infodengue: pd.DataFrame) -> pd.DataFrame:
    """Experimento A: viabilidade da deteccao de surto no InfoDengue.

    Para cada percentil e horizonte, roda o walk-forward e compara o LightGBM
    (clima + autorregressivo) com os baselines sazonal e de persistencia.

    Args:
        infodengue: Serie InfoDengue ja preparada.

    Returns:
        DataFrame de metricas por percentil, horizonte e modelo.
    """
    print("#" * 80)
    print("# EXPERIMENTO A — InfoDengue notificado (2010-2026, sem censura)")
    print("#   'da pra detectar surto 1-3 meses a frente em POA?'")
    print("#" * 80)

    features_infodengue = selecionar_colunas_por_prefixo(
        infodengue,
        ("casos_lag", "casos_mm", "temp_media_lag", "umid_media_lag"),
    ) + ["sem_sin", "sem_cos"]

    modelos_experimento_a = [
        ("clima+AR_LGBM", "pred", "prob"),
        ("sazonal", "pred_saz", "prob_saz"),
        ("persistencia", "pred_pers", None),
    ]

    linhas_metricas = []
    for percentil in PERCENTIS_SURTO:
        for horizonte in HORIZONTES_SEMANAS:
            resultado_walk_forward = executar_walk_forward_surto(
                infodengue, features_infodengue, "fonte", horizonte, percentil
            )
            for nome_modelo, coluna_pred, coluna_prob in modelos_experimento_a:
                probabilidade = (
                    resultado_walk_forward[coluna_prob] if coluna_prob else None
                )
                metricas = calcular_metricas_classificacao(
                    resultado_walk_forward["real"],
                    resultado_walk_forward[coluna_pred],
                    probabilidade,
                )
                metricas.update(
                    {
                        "exp": "A_infodengue",
                        "pctl": percentil,
                        "h": horizonte,
                        "modelo": nome_modelo,
                    }
                )
                linhas_metricas.append(metricas)

    resultados_experimento_a = pd.DataFrame(linhas_metricas)
    print(
        resultados_experimento_a[COLUNAS_EXIBICAO].round(3).to_string(index=False)
    )
    return resultados_experimento_a


def preparar_tabela_final() -> pd.DataFrame:
    """Le e prepara a tabela_final (SINAN confirmado + vetor) para o Experimento B.

    Renomeia data e alvo, ordena por fonte e data e aplica o corte de maturidade
    do Modelo 4c: os casos das ultimas semanas (ainda em confirmacao) viram NaN
    para nao entrarem como zeros falsos. Por fim, adiciona as features temporais.

    Returns:
        DataFrame semanal da tabela_final pronto para o walk-forward.
    """
    tabela_final = pd.read_csv(
        DIRETORIO_TABELA_MODELAGEM / "tabela_final.csv",
        parse_dates=["data_inicio_semana_epidemi"],
    ).rename(
        columns={
            "data_inicio_semana_epidemi": "data",
            "casos_confirmados": "casos",
        }
    )
    tabela_final = tabela_final.sort_values(["fonte", "data"]).reset_index(drop=True)

    # Corte de maturidade (Modelo 4c): as ultimas SEMANAS_CORTE_MATURIDADE semanas
    # ainda estao sendo confirmadas -> casos incompletos viram NaN (nao zero falso).
    data_referencia = tabela_final["data"].max()
    limite_maturidade = data_referencia - pd.Timedelta(weeks=SEMANAS_CORTE_MATURIDADE)
    tabela_final.loc[tabela_final["data"] > limite_maturidade, "casos"] = np.nan

    return construir_features_temporais(tabela_final)


def rodar_experimento_b(tabela_final: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Experimento B: lift do vetor na deteccao de surto, com teste de McNemar.

    Para cada percentil e horizonte, roda o walk-forward duas vezes — so-clima e
    clima+vetor — sobre os MESMOS folds, e compara os acertos pareados com McNemar.
    O baseline sazonal (identico nos dois) e reportado a partir do modelo so-clima.

    Args:
        tabela_final: Tabela_final ja preparada.

    Returns:
        Par (metricas_por_modelo, resultados_mcnemar), ambos DataFrames.
    """
    print("\n" + "#" * 80)
    print("# EXPERIMENTO B — tabela_final: so-clima vs clima+VETOR na deteccao (McNemar)")
    print("#" * 80)

    colunas_clima = selecionar_colunas_por_prefixo(
        tabela_final,
        (
            "temp_media_lag",
            "precip_total_mm_lag",
            "orvalho_media_lag",
            "umid_media_lag",
            "pressao_media_lag",
        ),
    )
    colunas_autorregressivas = selecionar_colunas_por_prefixo(
        tabela_final, ("casos_lag", "casos_mm")
    )
    colunas_vetor = selecionar_colunas_por_prefixo(
        tabela_final, ("aedes_aegypti_por_armadilha_lag", "vetor_mm")
    )
    features_so_clima = (
        colunas_autorregressivas + colunas_clima + ["sem_sin", "sem_cos"]
    )
    features_clima_vetor = (
        colunas_autorregressivas + colunas_clima + colunas_vetor + ["sem_sin", "sem_cos"]
    )

    linhas_metricas = []
    linhas_mcnemar = []
    for percentil in PERCENTIS_SURTO:
        for horizonte in HORIZONTES_SEMANAS:
            resultado_clima = executar_walk_forward_surto(
                tabela_final, features_so_clima, "fonte", horizonte, percentil
            )
            resultado_vetor = executar_walk_forward_surto(
                tabela_final, features_clima_vetor, "fonte", horizonte, percentil
            )
            comparacao = resultado_clima.merge(
                resultado_vetor, on=["h", "data", "real"], suffixes=("_c", "_v")
            )

            # Baseline sazonal e identico nos dois modelos; vem do lado so-clima.
            metricas_sazonal = calcular_metricas_classificacao(
                comparacao["real"], comparacao["pred_saz_c"], comparacao["prob_saz_c"]
            )
            metricas_sazonal.update(
                {
                    "exp": "B_tabela_final",
                    "pctl": percentil,
                    "h": horizonte,
                    "modelo": "sazonal",
                }
            )
            linhas_metricas.append(metricas_sazonal)

            for nome_modelo, sufixo in [("so-clima", "_c"), ("clima+vetor", "_v")]:
                metricas = calcular_metricas_classificacao(
                    comparacao["real"],
                    comparacao[f"pred{sufixo}"],
                    comparacao[f"prob{sufixo}"],
                )
                metricas.update(
                    {
                        "exp": "B_tabela_final",
                        "pctl": percentil,
                        "h": horizonte,
                        "modelo": nome_modelo,
                    }
                )
                linhas_metricas.append(metricas)

            # McNemar: so-clima (A) vs clima+vetor (B) nos mesmos pontos de teste.
            resultado_mcnemar = teste_mcnemar(
                (comparacao["pred_c"] == comparacao["real"]).to_numpy(),
                (comparacao["pred_v"] == comparacao["real"]).to_numpy(),
            )
            linhas_mcnemar.append(
                {
                    "pctl": percentil,
                    "h": horizonte,
                    "n": len(comparacao),
                    "n_pos": int(comparacao["real"].sum()),
                    "clima_certo_vetor_errado": resultado_mcnemar.n_a_certo_b_errado,
                    "vetor_certo_clima_errado": resultado_mcnemar.n_a_errado_b_certo,
                    "p": round(resultado_mcnemar.valor_p, 3),
                }
            )
            mensagem_mcnemar = (
                f"  P{percentil} h={horizonte:2d}: n={len(comparacao):3d} "
                f"pos={int(comparacao['real'].sum()):2d} | "
                f"clima>vetor={resultado_mcnemar.n_a_certo_b_errado} "
                f"vetor>clima={resultado_mcnemar.n_a_errado_b_certo} "
                f"McNemar p={resultado_mcnemar.valor_p:.3f}"
            )
            print(mensagem_mcnemar)

    resultados_experimento_b = pd.DataFrame(linhas_metricas)
    print("\n=== Metricas por modelo (Experimento B) ===")
    print(
        resultados_experimento_b[COLUNAS_EXIBICAO].round(3).to_string(index=False)
    )
    resultados_mcnemar = pd.DataFrame(linhas_mcnemar)
    return resultados_experimento_b, resultados_mcnemar


def main() -> None:
    """Roda os dois experimentos e salva as duas tabelas de resultado em CSV."""
    pd.set_option("display.width", 170)

    infodengue = preparar_infodengue()
    resultados_experimento_a = rodar_experimento_a(infodengue)

    tabela_final = preparar_tabela_final()
    resultados_experimento_b, resultados_mcnemar = rodar_experimento_b(tabela_final)

    resultados_completos = pd.concat(
        [resultados_experimento_a, resultados_experimento_b], ignore_index=True
    )
    resultados_completos.to_csv(CAMINHO_RESULTADOS, index=False)
    resultados_mcnemar.to_csv(CAMINHO_MCNEMAR, index=False)
    print("\nsalvo:", CAMINHO_RESULTADOS)
    print("salvo:", CAMINHO_MCNEMAR)


if __name__ == "__main__":
    main()
