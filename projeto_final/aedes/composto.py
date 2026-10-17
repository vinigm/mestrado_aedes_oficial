"""E3: composto que escolhe, a cada origem, a folha com menor erro recente (pre-declaracao, secao 5).

Funcao pura: recebe as previsoes de UM horizonte das duas folhas e devolve a serie do composto.
Nenhuma le ou grava arquivo.

Regra: na origem `t = data_alvo - h semanas`, o composto usa a previsao da folha que teve o MENOR MAE
nas ultimas `N` semanas-alvo com `data_alvo <= t` em que as DUAS folhas tem previsao naquele horizonte
(pares disponiveis; buracos de calendario ignorados). Empate exato de MAE: folha 5.

Nunca olha o futuro: so entram pares cuja semana-alvo ja tinha terminado na origem `t`.
"""

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO, COLUNA_DATA_DE_ORIGEM
from aedes.metricas import COLUNA_DO_PREVISTO, COLUNA_DO_REAL

NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA = "folha_escolhida"
FOLHA_PADRAO_NO_EMPATE = 5
FOLHA_ALTERNATIVA = 20
COLUNAS_DO_COMPOSTO = (
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    COLUNA_DO_REAL,
    COLUNA_DO_PREVISTO,
    NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA,
)
TOLERANCIA_DO_REAL_ENTRE_FOLHAS = 1e-9


def escolher_folha_pelo_erro_recente(erros_absolutos_folha_5: np.ndarray, erros_absolutos_folha_20: np.ndarray) -> int:
    """Folha de menor MAE nas semanas recentes; empate exato escolhe a folha 5.

    Args:
        erros_absolutos_folha_5: `|real - previsto|` da folha 5 nas semanas recentes.
        erros_absolutos_folha_20: Idem da folha 20, mesmas semanas.

    Returns:
        5 ou 20.

    Raises:
        ValueError: Se os vetores forem vazios ou de tamanhos diferentes.
    """
    if len(erros_absolutos_folha_5) == 0 or len(erros_absolutos_folha_5) != len(erros_absolutos_folha_20):
        raise ValueError("Os erros recentes devem ser nao vazios e do mesmo tamanho.")
    mae_folha_5 = float(np.mean(erros_absolutos_folha_5))
    mae_folha_20 = float(np.mean(erros_absolutos_folha_20))
    if mae_folha_20 < mae_folha_5:
        return FOLHA_ALTERNATIVA
    return FOLHA_PADRAO_NO_EMPATE


def montar_composto(
    previsoes_folha_5: pd.DataFrame,
    previsoes_folha_20: pd.DataFrame,
    horizonte: int,
    semanas_recentes: int,
) -> pd.DataFrame:
    """Serie do composto de um horizonte: para cada semana-alvo, a previsao da folha escolhida pelo erro passado.

    Para cada semana-alvo `s` (par disponivel nas duas folhas) calcula a origem `t = s - h semanas`,
    pega os ULTIMOS `semanas_recentes` pares com `data_alvo <= t` e compara o MAE das duas folhas neles.
    Se houver menos de `semanas_recentes` pares com `data_alvo <= t`, a semana-alvo NAO recebe previsao
    do composto (a regra nunca usa menos semanas que N).

    Args:
        previsoes_folha_5: `data_alvo`, `real`, `previsto` do `completo` folha 5, um horizonte.
        previsoes_folha_20: Idem da folha 20, mesmo horizonte.
        horizonte: Horizonte h em semanas (>= 1).
        semanas_recentes: N, tamanho da janela de erro recente (>= 1).

    Returns:
        DataFrame com `COLUNAS_DO_COMPOSTO`, ordenado por `data_alvo`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se h ou N forem < 1, houver `data_alvo` repetida, ou o `real` diferir entre as folhas.
    """
    if horizonte < 1 or semanas_recentes < 1:
        raise ValueError("horizonte e semanas_recentes devem ser >= 1.")

    colunas = [COLUNA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    for nome_da_folha, tabela in (("5", previsoes_folha_5), ("20", previsoes_folha_20)):
        ausentes = sorted(set(colunas) - set(tabela.columns))
        if ausentes:
            raise KeyError(f"Colunas ausentes na folha {nome_da_folha}: {ausentes}")
        if tabela[COLUNA_DATA_ALVO].duplicated().any():
            raise ValueError(f"data_alvo repetida na folha {nome_da_folha}.")

    da_folha_5 = previsoes_folha_5[colunas].rename(
        columns={COLUNA_DO_REAL: "real_5", COLUNA_DO_PREVISTO: "previsto_5"}
    )
    da_folha_20 = previsoes_folha_20[colunas].rename(
        columns={COLUNA_DO_REAL: "real_20", COLUNA_DO_PREVISTO: "previsto_20"}
    )
    pares = da_folha_5.merge(da_folha_20, on=COLUNA_DATA_ALVO, how="inner")
    pares = pares.sort_values(COLUNA_DATA_ALVO).reset_index(drop=True)
    diferenca_do_real = (pares["real_5"] - pares["real_20"]).abs()
    if bool((diferenca_do_real > TOLERANCIA_DO_REAL_ENTRE_FOLHAS).any()):
        raise ValueError("O `real` difere entre as folhas.")

    datas_alvo = pd.DatetimeIndex(pares[COLUNA_DATA_ALVO])
    valores_reais = pares["real_5"].to_numpy(dtype=float)
    previsto_5 = pares["previsto_5"].to_numpy(dtype=float)
    previsto_20 = pares["previsto_20"].to_numpy(dtype=float)
    erros_absolutos_5 = np.abs(valores_reais - previsto_5)
    erros_absolutos_20 = np.abs(valores_reais - previsto_20)

    atraso_da_origem = pd.Timedelta(weeks=horizonte)
    linhas: list[dict[str, object]] = []
    for posicao in range(len(pares)):
        data_alvo_da_linha = datas_alvo[posicao]
        data_de_origem = data_alvo_da_linha - atraso_da_origem
        # Pares com data_alvo <= origem: a resposta ja era conhecida em `t` (nunca depois).
        quantidade_de_pares_conhecidos = int(datas_alvo.searchsorted(data_de_origem, side="right"))
        if quantidade_de_pares_conhecidos < semanas_recentes:
            continue
        inicio_da_janela = quantidade_de_pares_conhecidos - semanas_recentes
        recentes_5 = erros_absolutos_5[inicio_da_janela:quantidade_de_pares_conhecidos]
        recentes_20 = erros_absolutos_20[inicio_da_janela:quantidade_de_pares_conhecidos]
        folha_escolhida = escolher_folha_pelo_erro_recente(recentes_5, recentes_20)
        if folha_escolhida == FOLHA_ALTERNATIVA:
            previsao_do_composto = previsto_20[posicao]
        else:
            previsao_do_composto = previsto_5[posicao]
        linhas.append(
            {
                COLUNA_DATA_DE_ORIGEM: data_de_origem,
                COLUNA_DATA_ALVO: data_alvo_da_linha,
                COLUNA_DO_REAL: valores_reais[posicao],
                COLUNA_DO_PREVISTO: float(previsao_do_composto),
                NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA: folha_escolhida,
            }
        )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_COMPOSTO))
