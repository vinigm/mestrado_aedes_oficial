"""

Aqui o programa ajeita os casos de dengue mais recentes, que ainda nao
terminaram de ser confirmados pelo sistema do governo (SINAN).

"""

import numpy as np
import pandas as pd


def aplicar_corte_maturidade(
    dados: pd.DataFrame,
    semanas_corte: int,
) -> pd.DataFrame:
    """

    Deixa em branco (NaN) os casos das ultimas semanas, que ainda nao acabaram de ser confirmados.

    Os casos das semanas mais recentes ainda estao em processo de confirmacao
    (isso costuma demorar algumas semanas), entao aparecem em numero bem menor
    do que o real, quase zerados. Se o modelo tratar esses numeros baixos como
    se fossem definitivos, ele vai aprender errado. Por isso, aqui a gente
    troca esses casos recentes por "sem informacao" (NaN).
    (Ajuste feito no Modelo 4c.)

    Args:
        dados: Tabela com uma linha por semana, com as colunas 'data' e 'casos'.
        semanas_corte: Quantas semanas mais recentes (contando a partir da
            data mais nova) devem ficar com os casos marcados como sem informacao.

    Returns:
        Uma COPIA da tabela, com os casos das semanas mais recentes marcados como sem informacao.

    """
    dados_corrigidos = dados.copy()
    data_referencia = dados_corrigidos["data"].max()
    limite_maturidade = data_referencia - pd.Timedelta(weeks=semanas_corte)
    dados_corrigidos.loc[dados_corrigidos["data"] > limite_maturidade, "casos"] = np.nan
    return dados_corrigidos
