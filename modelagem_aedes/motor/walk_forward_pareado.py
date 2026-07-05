"""

Este arquivo treina DOIS modelos nas MESMAS semanas de teste e devolve os erros
dos dois lado a lado, semana a semana.

Um dos modelos e o M0 (menos colunas, so clima) e o outro e o M1 (as mesmas
colunas mais os dados do mosquito). Testar os dois exatamente nas mesmas semanas
e o que deixa o teste de Diebold-Mariano valido: so da pra comparar os erros se
os dois foram medidos nos mesmos pontos.

Como no motor de regressao normal, o modelo treina no passado e preve o futuro,
semana a semana, e QUAL modelo usar chega pronto na ficha (LightGBM, RandomForest...).

"""

import numpy as np
import pandas as pd

from config import settings
from config.modelo import EspecificacaoModelo
from dominio.features import construir_alvo_horizonte


def executar_walk_forward_pareado(
    dados: pd.DataFrame,
    colunas_m0: list[str],
    colunas_m1: list[str],
    coluna_alvo: str,
    horizonte: int,
    especificacao_modelo: EspecificacaoModelo,
    minimo_semanas_treino: int = settings.MINIMO_SEMANAS_TREINO,
    passo: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """

    Treina o M0 e o M1 nas mesmas semanas e devolve os erros pareados dos dois.

    A tabela e filtrada tirando as linhas que nao tem todas as colunas do M1 (o
    conjunto maior, que ja inclui as do M0), entao os dois modelos rodam sobre
    exatamente as mesmas semanas. Em cada passo no tempo, os dois treinam com
    todo o passado e preveem a semana seguinte.

    Args:
        dados: Tabela semana a semana, ja com as colunas calculadas prontas.
        colunas_m0: Colunas de entrada do modelo menor (M0, so clima).
        colunas_m1: Colunas de entrada do modelo maior (M1 = M0 + mosquito).
        coluna_alvo: Nome da coluna que se quer prever.
        horizonte: Quantas semanas a frente prever.
        especificacao_modelo: A ficha que diz qual modelo usar e com quais
            ajustes (o mesmo modelo e usado no M0 e no M1).
        minimo_semanas_treino: Historico minimo antes de comecar a prever.
        passo: De quantas em quantas semanas o teste e feito.

    Returns:
        Dois vetores de erro (real - previsto), um do M0 e um do M1, alinhados
        semana a semana.

    """
    dados_horizonte = construir_alvo_horizonte(dados, coluna_alvo, horizonte)
    features_m0 = colunas_m0 + ["alvo_sin", "alvo_cos"]
    features_m1 = colunas_m1 + ["alvo_sin", "alvo_cos"]
    dados_validos = (
        dados_horizonte.dropna(subset=features_m1 + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    erros_m0 = []
    erros_m1 = []
    for indice_corte in range(minimo_semanas_treino, len(dados_validos), passo):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]

        modelo_m0 = especificacao_modelo.criar()
        modelo_m0.fit(treino[features_m0], treino["y_h"])
        previsao_m0 = modelo_m0.predict(teste[features_m0])[0]

        modelo_m1 = especificacao_modelo.criar()
        modelo_m1.fit(treino[features_m1], treino["y_h"])
        previsao_m1 = modelo_m1.predict(teste[features_m1])[0]

        valor_real = teste["y_h"].to_numpy()[0]
        erros_m0.append(valor_real - previsao_m0)
        erros_m1.append(valor_real - previsao_m1)

    return np.array(erros_m0), np.array(erros_m1)
