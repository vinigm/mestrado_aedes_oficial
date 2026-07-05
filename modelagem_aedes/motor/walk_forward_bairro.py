"""

Treina o modelo por bairro ao longo do tempo: usa so o passado pra prever a
densidade de mosquito de cada bairro nas semanas seguintes.

A cada passo no tempo, o modelo treina com tudo que aconteceu ate ali (em todos
os bairros de uma vez) e preve a semana seguinte pra todos os bairros. No fim,
mede o quanto ele explica (R2) pra cada quantidade de semanas a frente.

"""

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from config import settings
from config.modelo import EspecificacaoModelo


def r2_do_grupo(grupo: pd.DataFrame) -> float:
    """R2 entre o valor real e o previsto de um grupo de previsoes."""
    return r2_score(grupo["real"], grupo["pred"])


def executar_walk_forward_bairro(
    dados_bairro: pd.DataFrame,
    colunas_features: list[str],
    coluna_alvo: str,
    horizontes,
    semana_minima_teste: int,
    passo: int,
    minimo_linhas_treino: int,
    especificacao_modelo: EspecificacaoModelo,
    usar_sazonalidade_do_alvo: bool = False,
    coluna_fonte: str = "bairro",
    coluna_tempo: str = "t",
    coluna_semana: str = "Semana",
) -> pd.Series:
    """

    Roda o treina-passado-preve-futuro por bairro e devolve o R2 de cada horizonte.

    Pra cada quantidade de semanas a frente, define o alvo (a densidade daqui a
    tantas semanas). Se pedido, adiciona a epoca do ano da semana-alvo como
    coluna. Depois, a cada 'passo' semanas, treina com todo o passado (todos os
    bairros com tempo antes da semana de teste) e preve aquela semana pra todos
    os bairros. So treina quando ja ha historico suficiente.

    Args:
        dados_bairro: A tabela por bairro/semana, ja com as colunas prontas.
        colunas_features: Colunas de entrada do modelo.
        coluna_alvo: Nome da coluna a prever (por exemplo, 'dens').
        horizontes: Pra quantas semanas a frente prever.
        semana_minima_teste: A partir de qual semana (tempo 't') comecar a testar.
        passo: De quantas em quantas semanas testar.
        minimo_linhas_treino: Quantas linhas de treino sao precisas, no minimo.
        especificacao_modelo: A ficha que diz qual modelo usar e com quais ajustes.
        usar_sazonalidade_do_alvo: Se True, soma a epoca do ano da semana-alvo.
        coluna_fonte: Coluna que separa os bairros.
        coluna_tempo: Coluna do numero de tempo (semanas em ordem).
        coluna_semana: Coluna da semana do ano (pra epoca do ano do alvo).

    Returns:
        Uma serie com o R2 de cada horizonte.

    """
    grupos_por_bairro = dados_bairro.groupby(coluna_fonte, group_keys=False)
    instante_maximo = int(dados_bairro[coluna_tempo].max())
    previsoes_por_horizonte = []

    for horizonte in horizontes:
        dados_horizonte = dados_bairro.copy()
        dados_horizonte["y"] = grupos_por_bairro[coluna_alvo].shift(-horizonte)

        features_do_passo = list(colunas_features)
        if usar_sazonalidade_do_alvo:
            semana_do_alvo = grupos_por_bairro[coluna_semana].shift(-horizonte)
            angulo_do_alvo = 2 * np.pi * semana_do_alvo / settings.SEMANAS_POR_ANO
            dados_horizonte["alvo_sin"] = np.sin(angulo_do_alvo)
            dados_horizonte["alvo_cos"] = np.cos(angulo_do_alvo)
            features_do_passo = features_do_passo + ["alvo_sin", "alvo_cos"]

        dados_validos = dados_horizonte.dropna(subset=features_do_passo + ["y"])

        for semana_teste in range(semana_minima_teste, instante_maximo - horizonte + 1, passo):
            treino = dados_validos[dados_validos[coluna_tempo] < semana_teste]
            teste = dados_validos[dados_validos[coluna_tempo] == semana_teste]
            if len(teste) == 0 or len(treino) < minimo_linhas_treino:
                continue

            modelo = especificacao_modelo.criar()
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
