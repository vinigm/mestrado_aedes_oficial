"""E6b: reproducao da grade de 30 configuracoes (3 algoritmos x 5 perdas x M0/M1).

Funcoes puras: nao leem nem gravam arquivo. Replica, sem nenhuma correcao, o
procedimento do codigo antigo:
    - hiperparametros e perdas: `analises/2026-08-30_grid_completo/rodar_grid.py:48-153`
      (`ALGORITMOS`, `montar_parametros`);
    - laco corrigido (treino pela data da RESPOSTA, passo 1, minimo de 104
      linhas) e a TRUNCAGEM DA PREVISAO EM ZERO (`max(previsao, 0.0)`):
      `analises/2026-09-13_correcao_vazamento_treino/rodar_corrigido.py:104-146`;
    - resumo e ranking: `analises/2026-09-13_correcao_vazamento_treino/resumir.py`.

AS 30 CONFIGURACOES

    algoritmo (3)  x  perda (5: quadratica + quantis 0,70 / 0,80 / 0,85 / 0,90)  x  conjunto (2)

    HistGB            250 iteracoes, taxa 0,05, 15 folhas, folha minima 5
    GradientBoosting  250 arvores,   taxa 0,05, profundidade 3, folha minima 5
    LightGBM          300 arvores,   taxa 0,05, 31 folhas, folha minima 20
    todos com `random_state=42` (o LightGBM com `n_jobs=-1`, como o antigo).

    M0 = nucleo + clima + calendario (16 variaveis) = braco `sem_vetor` do pacote.
    M1 = M0 + vetor (22 variaveis) = braco `completo` do pacote.

O criterio de escolha e o do antigo: menor MAE medio, nos horizontes 1, 4, 8 e
12, das semanas-alvo ate 31/12/2023 (calibracao).
"""

import dataclasses

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    FOLHA_5,
    ConfiguracaoAvaliacao,
)
from aedes.corte_temporal import selecionar_treino_ja_respondido
from aedes.metricas import erro_absoluto_medio, r_quadrado
from aedes.walk_forward import (
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    COLUNAS_DAS_PREVISOES,
    validar_matriz_para_walk_forward,
)

ALGORITMO_HISTGB = "hist_gradient_boosting"
ALGORITMO_GBR = "gradient_boosting"
ALGORITMO_LIGHTGBM = "lightgbm"
ALGORITMOS_DA_GRADE = (ALGORITMO_HISTGB, ALGORITMO_GBR, ALGORITMO_LIGHTGBM)

ROTULO_DA_PERDA_PADRAO = "padrao"
QUANTIS_DA_GRADE = (0.70, 0.80, 0.85, 0.90)

CONJUNTO_M0 = "M0_sem_vetor"
CONJUNTO_M1 = "M1_com_vetor"
CONJUNTOS_DA_GRADE = (CONJUNTO_M0, CONJUNTO_M1)
BRACO_DO_PACOTE_POR_CONJUNTO = {CONJUNTO_M0: "sem_vetor", CONJUNTO_M1: "completo"}

HORIZONTES_DA_GRADE = (1, 4, 8, 12)
SEMENTE_DA_GRADE = 42

# Limite de "semana de pico" nas metricas descritivas do antigo (`resumir.py:36`).
LIMITE_DE_PICO_EM_CASOS = 100

COLUNA_DO_ALGORITMO = "algoritmo"
COLUNA_DA_PERDA = "perda"
COLUNA_DO_CONJUNTO = "conjunto"
COLUNA_DO_PERIODO = "periodo"
PERIODO_DA_CALIBRACAO = "calibracao"
PERIODO_DA_AVALIACAO = "avaliacao"
CHAVES_DA_CONFIGURACAO = [COLUNA_DO_ALGORITMO, COLUNA_DA_PERDA, COLUNA_DO_CONJUNTO]

COLUNAS_DAS_PREVISOES_DA_GRADE = (*CHAVES_DA_CONFIGURACAO, *COLUNAS_DAS_PREVISOES)
COLUNAS_DO_RESUMO_DA_GRADE = (
    *CHAVES_DA_CONFIGURACAO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PERIODO,
    "n",
    "mae",
    "r2",
    "vies_pico",
    "captura_pico",
)
COLUNAS_DO_RANKING_DA_GRADE = (
    "pos",
    *CHAVES_DA_CONFIGURACAO,
    "mae_cal",
    "dif_pct",
    "mae_aval",
    "r2_aval",
    "vies_pico",
    "captura_pico",
)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDaGrade:
    """Uma das 30 configuracoes: algoritmo, perda e conjunto de variaveis.

    Attributes:
        algoritmo: Um dos tres de `ALGORITMOS_DA_GRADE`.
        quantil: Quantil da perda quantilica (0,70 a 0,90), ou `None` para a
            perda quadratica padrao.
        conjunto: `M0_sem_vetor` ou `M1_com_vetor`.
    """

    algoritmo: str
    quantil: float | None
    conjunto: str

    def __post_init__(self) -> None:
        """Rejeita algoritmo, quantil ou conjunto fora da grade.

        Raises:
            ValueError: Se algum campo nao pertencer a grade.
        """
        if self.algoritmo not in ALGORITMOS_DA_GRADE:
            raise ValueError(f"algoritmo {self.algoritmo!r} fora de {ALGORITMOS_DA_GRADE}.")
        if self.quantil is not None and not 0.0 < self.quantil < 1.0:
            raise ValueError(f"quantil deve estar em (0, 1) ou ser None, recebido {self.quantil!r}.")
        if self.conjunto not in CONJUNTOS_DA_GRADE:
            raise ValueError(f"conjunto {self.conjunto!r} fora de {CONJUNTOS_DA_GRADE}.")

    def rotulo_da_perda(self) -> str:
        """`padrao` ou `quantil_0.85` (o rotulo do codigo antigo)."""
        if self.quantil is None:
            return ROTULO_DA_PERDA_PADRAO
        return f"quantil_{self.quantil:.2f}"

    def rotulo(self) -> str:
        """Identificador unico: `hist_gradient_boosting|quantil_0.85|M1_com_vetor`."""
        return f"{self.algoritmo}|{self.rotulo_da_perda()}|{self.conjunto}"


def rotulo_da_perda_para_quantil(rotulo_da_perda: str) -> float | None:
    """Inverte `rotulo_da_perda`: `padrao` vira `None`; `quantil_0.85` vira 0,85.

    Raises:
        ValueError: Se o rotulo nao for `padrao` nem `quantil_<numero>`.
    """
    if rotulo_da_perda == ROTULO_DA_PERDA_PADRAO:
        return None
    prefixo = "quantil_"
    if not rotulo_da_perda.startswith(prefixo):
        raise ValueError(f"Rotulo de perda invalido: {rotulo_da_perda!r}.")
    return float(rotulo_da_perda[len(prefixo) :])


def montar_as_30_configuracoes() -> list[ConfiguracaoDaGrade]:
    """As 30 configuracoes na ordem do antigo: algoritmo, depois perda, depois conjunto (M0, M1)."""
    perdas: list[float | None] = [None]
    perdas.extend(QUANTIS_DA_GRADE)
    configuracoes: list[ConfiguracaoDaGrade] = []
    for algoritmo in ALGORITMOS_DA_GRADE:
        for quantil in perdas:
            for conjunto in CONJUNTOS_DA_GRADE:
                configuracoes.append(ConfiguracaoDaGrade(algoritmo, quantil, conjunto))
    return configuracoes


def _parametros_do_histgb(quantil: float | None) -> dict[str, object]:
    """HistGB da grade: os parametros EXPLICITOS da `FOLHA_5` (a mesma do pacote), trocando so a perda.

    Para a perda quadratica o antigo nao passava `quantile`; aqui a chave sai.
    O restante e o padrao do scikit-learn escrito por extenso (ver `ConfiguracaoModelo`).
    """
    parametros = FOLHA_5.parametros_do_sklearn()
    if quantil is None:
        parametros["loss"] = "squared_error"
        del parametros["quantile"]
    else:
        parametros["loss"] = "quantile"
        parametros["quantile"] = quantil
    return parametros


def _parametros_do_gbr(quantil: float | None) -> dict[str, object]:
    """GradientBoosting da grade (`rodar_grid.py:56-63`); `alpha` so existe com perda quantilica."""
    parametros: dict[str, object] = {
        "n_estimators": 250,
        "learning_rate": 0.05,
        "max_depth": 3,
        "min_samples_leaf": 5,
        "random_state": SEMENTE_DA_GRADE,
    }
    if quantil is None:
        parametros["loss"] = "squared_error"
    else:
        parametros["loss"] = "quantile"
        parametros["alpha"] = quantil
    return parametros


def _parametros_do_lightgbm(quantil: float | None) -> dict[str, object]:
    """LightGBM da grade (`rodar_grid.py:64-71`); `alpha` so existe com perda quantilica."""
    parametros: dict[str, object] = {
        "n_estimators": 300,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 20,
        "verbose": -1,
        "n_jobs": -1,
        "random_state": SEMENTE_DA_GRADE,
    }
    if quantil is None:
        parametros["objective"] = "regression"
    else:
        parametros["objective"] = "quantile"
        parametros["alpha"] = quantil
    return parametros


def montar_parametros_da_grade(algoritmo: str, quantil: float | None) -> dict[str, object]:
    """Hiperparametros do algoritmo com a perda pedida (quadratica se `quantil` for `None`).

    Args:
        algoritmo: Um dos tres de `ALGORITMOS_DA_GRADE`.
        quantil: Quantil da perda quantilica, ou `None`.

    Returns:
        Dicionario NOVO com os argumentos do construtor.

    Raises:
        ValueError: Se o algoritmo nao for da grade.
    """
    if algoritmo == ALGORITMO_HISTGB:
        return _parametros_do_histgb(quantil)
    if algoritmo == ALGORITMO_GBR:
        return _parametros_do_gbr(quantil)
    if algoritmo == ALGORITMO_LIGHTGBM:
        return _parametros_do_lightgbm(quantil)
    raise ValueError(f"algoritmo {algoritmo!r} fora de {ALGORITMOS_DA_GRADE}.")


def criar_modelo_da_grade(
    configuracao: ConfiguracaoDaGrade,
) -> HistGradientBoostingRegressor | GradientBoostingRegressor | LGBMRegressor:
    """Cria o modelo NOVO (sem treino) de uma configuracao da grade."""
    parametros = montar_parametros_da_grade(configuracao.algoritmo, configuracao.quantil)
    if configuracao.algoritmo == ALGORITMO_HISTGB:
        return HistGradientBoostingRegressor(**parametros)
    if configuracao.algoritmo == ALGORITMO_GBR:
        return GradientBoostingRegressor(**parametros)
    return LGBMRegressor(**parametros)


def truncar_previsao_em_zero(previsao: float) -> float:
    """`max(previsao, 0.0)`: a grade antiga nao aceita previsao negativa de casos.

    Regra do antigo (`rodar_corrigido.py:141`). Com `previsao` ausente (NaN),
    `max` devolve o NaN (a comparacao e falsa), como no antigo.
    """
    return max(previsao, 0.0)


def executar_walk_forward_da_grade(
    matriz_do_horizonte: pd.DataFrame,
    horizonte: int,
    configuracao: ConfiguracaoDaGrade,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
    truncar_em_zero: bool,
) -> pd.DataFrame:
    """Walk-forward de UM horizonte para uma configuracao da grade.

    O laco e o de `aedes.walk_forward.executar_walk_forward` (treino pela data
    da resposta, modelo novo a cada origem, minimo de 104 linhas, passo 1), com
    duas diferencas: o modelo vem de `criar_modelo_da_grade` e a previsao pode
    ser truncada em zero (a grade antiga truncava). Com HistGB, quantil 0,85 e
    `truncar_em_zero=False` o resultado e IGUAL, bit a bit, ao do pacote.

    Args:
        matriz_do_horizonte: Matriz do conjunto (M0 ou M1) de um horizonte,
            sem ausentes, em ordem cronologica.
        horizonte: Semanas a frente (inteiro >= 1).
        configuracao: Algoritmo, perda e conjunto.
        configuracao_avaliacao: Usa treino minimo e passo.
        truncar_em_zero: Se a previsao negativa vira zero.

    Returns:
        DataFrame com `h`, `data_origem`, `data_alvo`, `real`, `previsto`.

    Raises:
        KeyError, ValueError: Os de `validar_matriz_para_walk_forward`, ou
            origem sem nenhuma linha de treino.
    """
    nomes_das_variaveis = validar_matriz_para_walk_forward(matriz_do_horizonte, horizonte)

    treino_minimo = configuracao_avaliacao.treino_minimo_em_semanas
    passo = configuracao_avaliacao.passo_do_retreino_em_semanas
    quantidade_de_linhas = len(matriz_do_horizonte)
    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)

    previsoes_por_origem: list[dict[str, object]] = []

    for posicao_da_origem in range(treino_minimo, quantidade_de_linhas, passo):
        linha_de_teste = matriz_do_horizonte.iloc[posicao_da_origem : posicao_da_origem + 1]
        data_de_origem = pd.Timestamp(linha_de_teste[COLUNA_DATA_DE_ORIGEM].iloc[0])

        treino = selecionar_treino_ja_respondido(matriz_do_horizonte, data_de_origem, horizonte)
        if len(treino) == 0:
            raise ValueError(
                f"Nenhuma linha de treino ja respondida em {data_de_origem.date()} "
                f"(horizonte {horizonte}, posicao {posicao_da_origem})."
            )

        variaveis_do_treino = treino[nomes_das_variaveis]
        alvo_do_treino = treino[COLUNA_DO_ALVO]
        variaveis_do_teste = linha_de_teste[nomes_das_variaveis]

        modelo = criar_modelo_da_grade(configuracao)
        modelo.fit(variaveis_do_treino, alvo_do_treino)
        previsao_da_semana = float(modelo.predict(variaveis_do_teste)[0])
        if truncar_em_zero:
            previsao_da_semana = truncar_previsao_em_zero(previsao_da_semana)

        valor_real = float(linha_de_teste[COLUNA_DO_ALVO].iloc[0])

        previsoes_por_origem.append(
            {
                COLUNA_DO_HORIZONTE: horizonte,
                COLUNA_DATA_DE_ORIGEM: data_de_origem,
                COLUNA_DATA_ALVO: data_de_origem + atraso_do_horizonte,
                COLUNA_DO_REAL: valor_real,
                COLUNA_DO_PREVISTO: previsao_da_semana,
            }
        )

    return pd.DataFrame(previsoes_por_origem, columns=list(COLUNAS_DAS_PREVISOES))


def classificar_periodo(datas_alvo: pd.Series, fim_da_calibracao: pd.Timestamp) -> pd.Series:
    """`avaliacao` se a semana-alvo e POSTERIOR ao fim da calibracao; senao `calibracao`.

    O antigo usava `data_alvo > 2023-12-31` (`resumir.py:41-43`): o dia 31/12/2023
    e calibracao.
    """
    e_avaliacao = datas_alvo > fim_da_calibracao
    rotulos = np.where(e_avaliacao, PERIODO_DA_AVALIACAO, PERIODO_DA_CALIBRACAO)
    return pd.Series(rotulos, index=datas_alvo.index)


def _calcular_metricas_do_grupo(reais: pd.Series, previstos: pd.Series) -> dict[str, float]:
    """MAE, R2, vies e captura nas semanas de pico (real > 100), como `resumir.py:calcular_metricas_grupo`."""
    e_semana_de_pico = reais > LIMITE_DE_PICO_EM_CASOS
    reais_no_pico = reais[e_semana_de_pico]
    previstos_no_pico = previstos[e_semana_de_pico]

    # Sem nenhuma semana de pico no grupo, vies e captura ficam NaN (o antigo
    # tambem devolvia NaN; aqui nao ha aviso de media de vetor vazio).
    vies_no_pico = float("nan")
    captura_no_pico = float("nan")
    if len(reais_no_pico) > 0:
        vies_no_pico = float(np.mean(previstos_no_pico - reais_no_pico))
        captura_no_pico = float(previstos_no_pico.mean() / reais_no_pico.mean())
    return {
        "mae": erro_absoluto_medio(reais, previstos),
        "r2": r_quadrado(reais, previstos),
        "vies_pico": vies_no_pico,
        "captura_pico": captura_no_pico,
    }


def resumir_previsoes_da_grade(
    previsoes: pd.DataFrame,
    fim_da_calibracao: pd.Timestamp,
) -> pd.DataFrame:
    """MAE, R2 e n por configuracao, horizonte e periodo (calibracao ou avaliacao).

    Args:
        previsoes: Colunas `algoritmo`, `perda`, `conjunto`, `h`, `data_alvo`,
            `real`, `previsto`, sem ausente.
        fim_da_calibracao: 31/12/2023.

    Returns:
        DataFrame com `COLUNAS_DO_RESUMO_DA_GRADE`, na ordem da primeira
        aparicao de cada (configuracao, h, periodo) na entrada.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas_necessarias = [*CHAVES_DA_CONFIGURACAO, COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    colunas_ausentes = sorted(set(colunas_necessarias) - set(previsoes.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes nas previsoes da grade: {colunas_ausentes}")

    previsoes_com_periodo = previsoes.copy()
    previsoes_com_periodo[COLUNA_DO_PERIODO] = classificar_periodo(previsoes[COLUNA_DATA_ALVO], fim_da_calibracao)

    chaves_do_grupo = [*CHAVES_DA_CONFIGURACAO, COLUNA_DO_HORIZONTE, COLUNA_DO_PERIODO]
    linhas: list[dict[str, object]] = []
    for chave, grupo in previsoes_com_periodo.groupby(chaves_do_grupo, sort=False):
        metricas = _calcular_metricas_do_grupo(grupo[COLUNA_DO_REAL], grupo[COLUNA_DO_PREVISTO])
        linha: dict[str, object] = dict(zip(chaves_do_grupo, chave))
        linha["n"] = len(grupo)
        linha.update(metricas)
        linhas.append(linha)
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_RESUMO_DA_GRADE))


def construir_ranking_da_grade(
    resumo: pd.DataFrame,
    horizontes_do_ranking: tuple[int, ...] = HORIZONTES_DA_GRADE,
) -> pd.DataFrame:
    """Ranking pelo criterio do antigo: menor MAE medio de calibracao nos horizontes do ranking.

    `mae_cal` e a media, por configuracao, dos MAE de calibracao dos horizontes
    do ranking. `mae_aval`, `r2_aval`, `vies_pico` e `captura_pico` sao as medias
    das mesmas colunas na avaliacao (descritivas, nao entram na escolha). A
    ordenacao e ESTAVEL sobre a tabela agrupada: configuracoes com `mae_cal`
    identico ficam em ordem alfabetica de (algoritmo, perda, conjunto) (o antigo
    usava a ordenacao padrao do pandas, sem garantia para empates; a tabela de
    30 nao tem empate exato).

    Args:
        resumo: Saida de `resumir_previsoes_da_grade`.
        horizontes_do_ranking: Horizontes que entram na media (1, 4, 8, 12).

    Returns:
        DataFrame com `COLUNAS_DO_RANKING_DA_GRADE`; `pos` de 1 em diante;
        `dif_pct` = `(mae_cal / mae_cal_do_1o - 1) * 100`.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas_necessarias = [*CHAVES_DA_CONFIGURACAO, COLUNA_DO_HORIZONTE, COLUNA_DO_PERIODO, "mae", "r2", "vies_pico", "captura_pico"]
    colunas_ausentes = sorted(set(colunas_necessarias) - set(resumo.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes no resumo da grade: {colunas_ausentes}")

    esta_nos_horizontes = resumo[COLUNA_DO_HORIZONTE].isin(horizontes_do_ranking)
    e_calibracao = resumo[COLUNA_DO_PERIODO] == PERIODO_DA_CALIBRACAO
    e_avaliacao = resumo[COLUNA_DO_PERIODO] == PERIODO_DA_AVALIACAO
    calibracao = resumo.loc[esta_nos_horizontes & e_calibracao]
    avaliacao = resumo.loc[esta_nos_horizontes & e_avaliacao]

    medias_da_calibracao = calibracao.groupby(CHAVES_DA_CONFIGURACAO)["mae"].mean().rename("mae_cal")
    medias_da_avaliacao = avaliacao.groupby(CHAVES_DA_CONFIGURACAO).agg(
        mae_aval=("mae", "mean"),
        r2_aval=("r2", "mean"),
        vies_pico=("vies_pico", "mean"),
        captura_pico=("captura_pico", "mean"),
    )

    ranking = pd.concat([medias_da_calibracao, medias_da_avaliacao], axis=1).reset_index()
    ranking = ranking.sort_values("mae_cal", ascending=True, kind="stable").reset_index(drop=True)
    ranking.insert(0, "pos", ranking.index + 1)

    mae_cal_do_primeiro = ranking.loc[0, "mae_cal"]
    ranking["dif_pct"] = (ranking["mae_cal"] / mae_cal_do_primeiro - 1) * 100
    return ranking[list(COLUNAS_DO_RANKING_DA_GRADE)]
