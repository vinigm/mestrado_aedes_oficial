"""

Aqui ficam as contas que dizem se o modelo acertou quando previu se ia ter
surto ou nao (uma resposta do tipo sim ou nao).

A funcao deste arquivo pega o que realmente aconteceu e o que o modelo
previu, ponto por ponto, e devolve um resumo em numeros: quantos acertos e
erros de cada tipo, e algumas notas gerais como F1 e AUC.

"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)


def calcular_metricas_classificacao(
    y_real: pd.Series | np.ndarray,
    y_previsto: pd.Series | np.ndarray,
    probabilidade: pd.Series | np.ndarray | None = None,
) -> dict[str, float]:
    """

    Calcula se as previsoes de surto acertaram, pra um grupo de pontos.

    Compara, ponto a ponto, se realmente teve surto com o que o modelo disse
    que ia acontecer, e junta os acertos e erros num resumo com varios
    numeros.

    Args:
        y_real: se realmente teve surto (0 ou 1) em cada ponto.
        y_previsto: o que o modelo previu pra cada ponto (0 ou 1).
        probabilidade: a chance que o modelo deu de ter surto. Quando isso e
            passado e aparecem os dois casos (com e sem surto) nos dados, o
            resultado tambem traz as notas AUC e average precision.

    Returns:
        Um dicionario com as contas, sempre com as mesmas chaves e na mesma
        ordem (pra virarem colunas certinhas quando varias dessas linhas forem
        empilhadas numa tabela): n, n_pos, tp, fp, fn, tn, sensib, espec,
        precisao, f1, bal_acc e, se for o caso, auc e ap.
        Sensibilidade, especificidade e precisao ficam vazias (NaN) quando a
        conta ia dividir por zero.

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
