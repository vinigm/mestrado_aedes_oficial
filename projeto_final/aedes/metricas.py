"""Metricas de avaliacao e reguas simples: MAE, R2, regua sazonal e persistencia.

Funcoes puras: recebem Series ou DataFrames e devolvem resultado ou levantam
erro. Nenhuma le nem grava arquivo, e nenhuma depende de estado global.

Replica, sem nenhuma correcao, o calculo do codigo antigo:
    - MAE e R2: `analises/2026-09-25_regua_regras_simples/calcular_regua.py:747-785`
      (`calcular_metricas_previsao`), que chama `sklearn.metrics.mean_absolute_error`
      e `r2_score` e devolve NaN quando ha 0 pontos (MAE e R2) ou 1 ponto (R2);
    - regua de persistencia: `calcular_regua.py:490-511` (`calcular_regra_persistencia`):
      casos na semana `data_alvo - h semanas` (a semana de origem);
    - regua sazonal: `calcular_regua.py:514-534` (`calcular_regra_sazonal`): casos na
      semana `data_alvo - 52 semanas`;
    - pareamento: `calcular_regua.py:582-673` (`montar_previsoes_das_regras_simples`) e
      `calcular_regua.py:1435-1439`: a grade de (h, data_alvo) das reguas e a do
      braco `referencia`, e as linhas em que a regua nao existe (NaN) saem antes
      de medir. Assim a regua e medida nas MESMAS semanas do modelo;
    - janela: `calcular_regua.py:715-745` (`selecionar_periodo`, "avaliacao").
      O antigo so tinha o limite inferior (`data_alvo >= 2024-01-01`) porque as
      previsoes ja terminavam na ultima semana madura; aqui a janela tem os dois
      limites, da `ConfiguracaoAvaliacao`, e o resultado e o mesmo (n = 102).

A serie de casos que as reguas consultam e a JA CORTADA pelo corte de maturidade
(`aedes.dados.aplicar_corte_de_maturidade`), indexada pela data da semana.
"""

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, ConfiguracaoAvaliacao

SEMANAS_DO_PASSO_SAZONAL = 52

NOME_DO_BRACO_REGUA_SAZONAL = "regua_sazonal"
NOME_DO_BRACO_PERSISTENCIA = "persistencia"

COLUNA_DO_HORIZONTE = "h"
COLUNA_DO_BRACO = "braco"
COLUNA_DO_REAL = "real"
COLUNA_DO_PREVISTO = "previsto"
COLUNA_DO_N = "n"
COLUNA_DO_MAE = "mae"
COLUNA_DO_R2 = "r2"

COLUNAS_DO_RESUMO = (COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, COLUNA_DO_N, COLUNA_DO_MAE, COLUNA_DO_R2)
COLUNAS_DAS_PREVISOES_DAS_REGUAS = (
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_ALVO,
    COLUNA_DO_REAL,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_BRACO,
)


def _converter_para_vetor_de_floats(valores: pd.Series | np.ndarray, nome_do_argumento: str) -> np.ndarray:
    """Converte para vetor 1-D de float, sem ausente nem infinito.

    Args:
        valores: Casos reais ou previstos.
        nome_do_argumento: Nome mostrado na mensagem de erro.

    Returns:
        Vetor NumPy de float64.

    Raises:
        ValueError: Se nao for 1-D ou tiver NaN ou infinito.
    """
    vetor = np.asarray(valores, dtype=float)
    if vetor.ndim != 1:
        raise ValueError(f"{nome_do_argumento} deve ser 1-D, recebido {vetor.ndim}-D.")
    if not np.isfinite(vetor).all():
        raise ValueError(
            f"{nome_do_argumento} tem valor ausente ou infinito; "
            "descarte os pares incompletos antes de medir (a regua sem previsao sai da conta)."
        )
    return vetor


def _validar_pares(
    valores_reais: pd.Series | np.ndarray,
    valores_previstos: pd.Series | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Converte e confere o par (real, previsto): mesmo tamanho, sem ausente.

    Raises:
        ValueError: Se os tamanhos diferirem, ou houver NaN ou infinito.
    """
    reais = _converter_para_vetor_de_floats(valores_reais, "valores_reais")
    previstos = _converter_para_vetor_de_floats(valores_previstos, "valores_previstos")
    if len(reais) != len(previstos):
        raise ValueError(
            f"valores_reais ({len(reais)}) e valores_previstos ({len(previstos)}) "
            "devem ter o mesmo tamanho."
        )
    return reais, previstos


def erro_absoluto_medio(
    valores_reais: pd.Series | np.ndarray,
    valores_previstos: pd.Series | np.ndarray,
) -> float:
    """Erro absoluto medio (MAE): media de |real - previsto|, em casos por semana.

    Mesma conta de `sklearn.metrics.mean_absolute_error` (que o codigo antigo
    usava), com a convencao do antigo para entrada vazia.

    Args:
        valores_reais: Casos confirmados observados.
        valores_previstos: Previsoes de um modelo ou de uma regua, pareadas por
            posicao com os reais.

    Returns:
        O MAE; NaN se nao houver nenhum par (como em `calcular_metricas_previsao`).

    Raises:
        ValueError: Se os tamanhos diferirem ou houver ausente ou infinito.
    """
    reais, previstos = _validar_pares(valores_reais, valores_previstos)
    if len(reais) == 0:
        return float("nan")
    erros_absolutos = np.abs(reais - previstos)
    return float(np.mean(erros_absolutos))


def r_quadrado(
    valores_reais: pd.Series | np.ndarray,
    valores_previstos: pd.Series | np.ndarray,
) -> float:
    """Coeficiente de determinacao R2 = 1 - SQ_residual / SQ_total.

    Mesma conta de `sklearn.metrics.r2_score` (que o codigo antigo usava), com
    as convencoes do antigo e do sklearn, preservadas por equivalencia:
        - menos de 2 pares: NaN (o antigo nem chamava o sklearn);
        - serie real CONSTANTE (SQ_total = 0), onde o R2 nao e definido: o
          sklearn (`force_finite=True`) devolve 1,0 se o erro e zero e 0,0 caso
          contrario. Essa convencao e mantida; quem interpretar R2 com serie
          constante deve saber que o numero e convencao, nao medida.

    Args:
        valores_reais: Casos confirmados observados.
        valores_previstos: Previsoes pareadas por posicao com os reais.

    Returns:
        O R2 (pode ser negativo: pior que prever a media dos reais).

    Raises:
        ValueError: Se os tamanhos diferirem ou houver ausente ou infinito.
    """
    reais, previstos = _validar_pares(valores_reais, valores_previstos)
    if len(reais) < 2:
        return float("nan")

    media_dos_reais = np.mean(reais)
    soma_dos_quadrados_residuais = float(np.sum((reais - previstos) ** 2))
    soma_dos_quadrados_totais = float(np.sum((reais - media_dos_reais) ** 2))

    if soma_dos_quadrados_totais == 0.0:
        if soma_dos_quadrados_residuais == 0.0:
            return 1.0
        return 0.0
    return float(1.0 - soma_dos_quadrados_residuais / soma_dos_quadrados_totais)


def _validar_serie_de_casos(casos_por_data: pd.Series) -> None:
    """Confere que a serie de casos e indexada por data, sem data repetida.

    Raises:
        TypeError: Se o indice nao for de datas.
        ValueError: Se houver data repetida no indice.
    """
    if not isinstance(casos_por_data.index, pd.DatetimeIndex):
        raise TypeError("casos_por_data deve ter indice de datas (pd.DatetimeIndex).")
    if casos_por_data.index.has_duplicates:
        raise ValueError("casos_por_data tem data repetida no indice.")


def _buscar_casos_nas_datas(casos_por_data: pd.Series, datas_consultadas: pd.Series) -> pd.Series:
    """Casos da serie em cada data consultada; NaN se a data nao existe ou esta sem caso.

    Equivale ao `dict.get(data, nan)` do codigo antigo (nao ha interpolacao nem
    preenchimento). O resultado tem o MESMO indice de `datas_consultadas`.
    """
    _validar_serie_de_casos(casos_por_data)
    indice_das_datas = pd.DatetimeIndex(datas_consultadas)
    casos_nas_datas = casos_por_data.reindex(indice_das_datas).to_numpy(dtype=float)
    return pd.Series(casos_nas_datas, index=datas_consultadas.index, dtype=float)


def previsao_regua_sazonal(
    casos_por_data: pd.Series,
    datas_alvo: pd.Series,
    semanas_do_passo_sazonal: int = SEMANAS_DO_PASSO_SAZONAL,
) -> pd.Series:
    """Regua sazonal: preve os casos da semana-alvo com os da MESMA semana do ano anterior.

    Para cada `data_alvo`, devolve os casos em `data_alvo - 52 semanas`. Como o
    horizonte vai ate 12 semanas, essa semana tinha pelo menos 40 semanas na
    origem: ja era conhecida e madura, a regua nao usa informacao do futuro.
    Passo fixo de 52 semanas (ignora anos de 53 semanas), simplificacao do antigo.

    Args:
        casos_por_data: Casos por semana, ja cortados pela maturidade, com
            indice de datas (domingos) sem repeticao.
        datas_alvo: Semanas-alvo (Timestamps); o resultado mantem o indice.
        semanas_do_passo_sazonal: Quantas semanas voltar (52).

    Returns:
        Series float com o mesmo indice de `datas_alvo`; NaN onde a semana do
        ano anterior nao existe na serie ou nao tem caso (antes do inicio dos
        casos, ou apagada pelo corte).

    Raises:
        TypeError: Se o indice de `casos_por_data` nao for de datas.
        ValueError: Se o indice de `casos_por_data` tiver data repetida.
    """
    atraso = pd.Timedelta(weeks=semanas_do_passo_sazonal)
    datas_um_ano_antes = datas_alvo - atraso
    return _buscar_casos_nas_datas(casos_por_data, datas_um_ano_antes)


def previsao_persistencia(
    casos_por_data: pd.Series,
    datas_alvo: pd.Series,
    horizonte: int,
) -> pd.Series:
    """Persistencia: preve os casos da semana-alvo com os da semana de ORIGEM.

    Para cada `data_alvo`, devolve os casos em `data_alvo - horizonte semanas`,
    isto e, o ultimo numero que o modelo tambem conhece na origem `t`
    (a defasagem `h` dos casos). E o piso de comparacao mais simples.

    Args:
        casos_por_data: Casos por semana, ja cortados pela maturidade, com
            indice de datas (domingos) sem repeticao.
        datas_alvo: Semanas-alvo (Timestamps); o resultado mantem o indice.
        horizonte: Semanas a frente (inteiro >= 1).

    Returns:
        Series float com o mesmo indice de `datas_alvo`; NaN onde a semana de
        origem nao existe na serie ou nao tem caso.

    Raises:
        ValueError: Se `horizonte` nao for inteiro >= 1, ou o indice de
            `casos_por_data` tiver data repetida.
        TypeError: Se o indice de `casos_por_data` nao for de datas.
    """
    horizonte_e_valido = isinstance(horizonte, int) and not isinstance(horizonte, bool)
    if not horizonte_e_valido or horizonte < 1:
        raise ValueError(f"horizonte deve ser inteiro >= 1, recebido {horizonte!r}.")
    atraso = pd.Timedelta(weeks=horizonte)
    datas_de_origem = datas_alvo - atraso
    return _buscar_casos_nas_datas(casos_por_data, datas_de_origem)


def recortar_janela_de_avaliacao(
    previsoes: pd.DataFrame,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
) -> pd.DataFrame:
    """Mantem so as semanas-alvo da janela de avaliacao (limites incluidos).

    A janela e por `data_alvo`, nunca por data de origem: o que se julga e a
    semana prevista (07/01/2024 a 01/02/2026 na configuracao oficial).

    Args:
        previsoes: DataFrame com a coluna `data_alvo`.
        configuracao_avaliacao: Traz a primeira e a ultima `data_alvo` avaliadas.

    Returns:
        Copia do recorte, mesmas colunas, ordem das linhas preservada.

    Raises:
        KeyError: Se faltar a coluna `data_alvo`.
    """
    if COLUNA_DATA_ALVO not in previsoes.columns:
        raise KeyError(f"Coluna {COLUNA_DATA_ALVO!r} ausente nas previsoes.")
    datas_alvo = previsoes[COLUNA_DATA_ALVO]
    depois_do_inicio = datas_alvo >= configuracao_avaliacao.primeira_data_alvo_avaliada
    antes_do_fim = datas_alvo <= configuracao_avaliacao.ultima_data_alvo_avaliada
    return previsoes.loc[depois_do_inicio & antes_do_fim].copy()


def montar_previsoes_das_reguas(
    previsoes_do_braco_de_referencia: pd.DataFrame,
    casos_por_data: pd.Series,
) -> pd.DataFrame:
    """Aplica a regua sazonal e a persistencia na MESMA grade (h, data_alvo) do modelo.

    A grade vem do braco `referencia` do walk-forward (como no codigo antigo,
    `calcular_regua.py:1435-1439`), e o `real` de cada linha e a serie de casos
    na `data_alvo`. Linhas em que a regua nao existe (NaN) saem: a regua e
    medida so onde faz previsao, e o `n` do resumo mostra quantas sobraram.

    Args:
        previsoes_do_braco_de_referencia: Previsoes de UM braco, com `h` e
            `data_alvo` (e, tipicamente, ja recortadas na janela de avaliacao).
        casos_por_data: Casos por semana, ja cortados pela maturidade, com
            indice de datas sem repeticao.

    Returns:
        DataFrame com `h`, `data_alvo`, `real`, `previsto`, `braco`: primeiro as
        linhas da regua sazonal, depois as da persistencia, cada uma na ordem
        de `h` e `data_alvo` da entrada.

    Raises:
        KeyError: Se faltar `h` ou `data_alvo`.
    """
    colunas_ausentes = []
    for nome_da_coluna in (COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO):
        if nome_da_coluna not in previsoes_do_braco_de_referencia.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes nas previsoes de referencia: {colunas_ausentes}")

    grade = previsoes_do_braco_de_referencia[[COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]]
    grade = grade.drop_duplicates().reset_index(drop=True)
    datas_alvo = grade[COLUNA_DATA_ALVO]
    horizontes = grade[COLUNA_DO_HORIZONTE]
    casos_na_data_alvo = _buscar_casos_nas_datas(casos_por_data, datas_alvo)

    previsao_sazonal = previsao_regua_sazonal(casos_por_data, datas_alvo)

    # A persistencia depende de h: cada horizonte recua um numero diferente de semanas.
    previsao_da_persistencia = pd.Series(np.nan, index=grade.index, dtype=float)
    for horizonte in pd.unique(horizontes):
        linhas_do_horizonte = horizontes == horizonte
        datas_do_horizonte = datas_alvo[linhas_do_horizonte]
        previsao_do_horizonte = previsao_persistencia(casos_por_data, datas_do_horizonte, int(horizonte))
        previsao_da_persistencia.loc[linhas_do_horizonte] = previsao_do_horizonte

    tabelas_das_reguas: list[pd.DataFrame] = []
    reguas = [
        (NOME_DO_BRACO_REGUA_SAZONAL, previsao_sazonal),
        (NOME_DO_BRACO_PERSISTENCIA, previsao_da_persistencia),
    ]
    for nome_da_regua, previsoes_da_regua in reguas:
        tabela_da_regua = pd.DataFrame(
            {
                COLUNA_DO_HORIZONTE: horizontes,
                COLUNA_DATA_ALVO: datas_alvo,
                COLUNA_DO_REAL: casos_na_data_alvo,
                COLUNA_DO_PREVISTO: previsoes_da_regua,
                COLUNA_DO_BRACO: nome_da_regua,
            }
        )
        regua_existe = tabela_da_regua[COLUNA_DO_PREVISTO].notna()
        tabelas_das_reguas.append(tabela_da_regua.loc[regua_existe])

    previsoes_das_reguas = pd.concat(tabelas_das_reguas, ignore_index=True)
    return previsoes_das_reguas[list(COLUNAS_DAS_PREVISOES_DAS_REGUAS)]


def resumir_metricas_por_horizonte_e_braco(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE, R2 e n por braco e horizonte, sobre as linhas que receber.

    Nao recorta janela nem descarta linha: quem chama decide o que entra
    (ver `resumir_na_janela_de_avaliacao`). A ordem dos bracos e a da primeira
    aparicao na entrada; dentro de cada braco, `h` crescente.

    Args:
        previsoes: DataFrame com `braco`, `h`, `real` e `previsto`, sem ausente.

    Returns:
        DataFrame com `braco`, `h`, `n`, `mae`, `r2`, uma linha por (braco, h).

    Raises:
        KeyError: Se faltar alguma das colunas.
        ValueError: Se houver ausente em `real` ou `previsto`.
    """
    colunas_ausentes = []
    for nome_da_coluna in (COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE, COLUNA_DO_REAL, COLUNA_DO_PREVISTO):
        if nome_da_coluna not in previsoes.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes nas previsoes: {colunas_ausentes}")

    linhas_do_resumo: list[dict[str, object]] = []
    for nome_do_braco in pd.unique(previsoes[COLUNA_DO_BRACO]):
        do_braco = previsoes.loc[previsoes[COLUNA_DO_BRACO] == nome_do_braco]
        for horizonte in sorted(pd.unique(do_braco[COLUNA_DO_HORIZONTE])):
            do_horizonte = do_braco.loc[do_braco[COLUNA_DO_HORIZONTE] == horizonte]
            valores_reais = do_horizonte[COLUNA_DO_REAL]
            valores_previstos = do_horizonte[COLUNA_DO_PREVISTO]
            linhas_do_resumo.append(
                {
                    COLUNA_DO_BRACO: nome_do_braco,
                    COLUNA_DO_HORIZONTE: int(horizonte),
                    COLUNA_DO_N: len(do_horizonte),
                    COLUNA_DO_MAE: erro_absoluto_medio(valores_reais, valores_previstos),
                    COLUNA_DO_R2: r_quadrado(valores_reais, valores_previstos),
                }
            )
    return pd.DataFrame(linhas_do_resumo, columns=list(COLUNAS_DO_RESUMO))


def resumir_na_janela_de_avaliacao(
    previsoes: pd.DataFrame,
    configuracao_avaliacao: ConfiguracaoAvaliacao,
) -> pd.DataFrame:
    """Recorta a janela de avaliacao (por `data_alvo`) e resume MAE, R2 e n por braco e h.

    Args:
        previsoes: DataFrame com `braco`, `h`, `data_alvo`, `real`, `previsto`.
        configuracao_avaliacao: Define a janela (07/01/2024 a 01/02/2026).

    Returns:
        DataFrame com `braco`, `h`, `n`, `mae`, `r2`.

    Raises:
        KeyError: Se faltar alguma coluna.
        ValueError: Se houver ausente em `real` ou `previsto` dentro da janela.
    """
    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes, configuracao_avaliacao)
    return resumir_metricas_por_horizonte_e_braco(previsoes_na_janela)
