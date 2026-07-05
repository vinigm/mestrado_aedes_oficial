"""

Aqui o programa calcula duas medidas pra saber se as previsoes de casos estao
boas: o erro medio (MAE, a diferenca media entre o que foi previsto e o que
realmente aconteceu) e o R2 (o quanto da variacao dos casos reais o modelo
consegue explicar). As contas saem separadas por horizonte (quantas semanas
a frente era a previsao).

"""

import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score


def calcular_metricas_regressao(
    resultados: pd.DataFrame,
    nome_conjunto: str,
) -> list[dict[str, float]]:
    """

    Calcula o erro medio (MAE) e o R2 pra cada horizonte, usando as previsoes
    do teste que treina no passado e preve o futuro, semana a semana.

    Args:
        resultados: tabela com as colunas h, real e pred (o resultado desse teste).
        nome_conjunto: nome do grupo de colunas usadas pra treinar o modelo (ex.: 'M0_clima6').

    Returns:
        Lista de dicionarios (um por horizonte) com conjunto, h, n, MAE e R2.

    """
    linhas_metricas = []
    for horizonte, grupo in resultados.groupby("h"):
        linhas_metricas.append(
            {
                "conjunto": nome_conjunto,
                "h": horizonte,
                "n": len(grupo),
                "MAE": mean_absolute_error(grupo["real"], grupo["pred"]),
                "R2": r2_score(grupo["real"], grupo["pred"]),
            }
        )
    return linhas_metricas
