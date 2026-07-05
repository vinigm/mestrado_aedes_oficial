"""

Contas do experimento de comparacao com a literatura (treina modelos e mede o
acerto).

Sao tres jeitos de medir, todos treinando no passado (ou num pedaco dos dados) e
prevendo o resto:
  - o quanto o modelo explica os casos, por semana a frente (R2), semana a semana;
  - o acerto em dizer se os casos vao "acelerar", do jeito honesto (treina no
    passado e preve o futuro);
  - o mesmo acerto, mas do jeito da literatura (embaralha e separa treino/teste),
    que costuma dar numeros mais bonitos do que a realidade.

QUAL modelo usar chega pronto na ficha (EspecificacaoModelo): uma pra prever
numero (regressao) e outra pra prever sim/nao (classificacao).

"""

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, r2_score
from sklearn.model_selection import train_test_split

from config.modelo import EspecificacaoModelo


def r2_por_horizonte(
    dados: pd.DataFrame,
    colunas_features: list[str],
    coluna_alvo: str,
    horizontes: tuple[int, ...],
    especificacao_modelo: EspecificacaoModelo,
    minimo_semanas_treino: int,
    passo: int,
    coluna_fonte: str = "fonte",
    coluna_data: str = "data",
) -> pd.Series:
    """

    Treina no passado, preve o futuro, e devolve o quanto o modelo explica os
    casos (R2) pra cada semana a frente.

    Returns:
        Uma serie com o R2 de cada horizonte.

    """
    grupos_por_fonte = dados.groupby(coluna_fonte, group_keys=False)
    r2_de_cada_horizonte = {}
    for horizonte in horizontes:
        dados_horizonte = dados.copy()
        dados_horizonte["y"] = grupos_por_fonte[coluna_alvo].shift(-horizonte)
        dados_validos = (
            dados_horizonte.dropna(subset=colunas_features + ["y"])
            .sort_values(coluna_data)
            .reset_index(drop=True)
        )
        valores_reais = []
        valores_previstos = []
        for indice_corte in range(minimo_semanas_treino, len(dados_validos), passo):
            treino = dados_validos.iloc[:indice_corte]
            teste = dados_validos.iloc[indice_corte:indice_corte + 1]
            modelo = especificacao_modelo.criar()
            modelo.fit(treino[colunas_features], treino["y"])
            valores_reais.append(teste["y"].to_numpy()[0])
            valores_previstos.append(modelo.predict(teste[colunas_features])[0])
        r2_de_cada_horizonte[horizonte] = r2_score(valores_reais, valores_previstos)
    return pd.Series(r2_de_cada_horizonte)


def acerto_aceleracao_walk_forward(
    dados: pd.DataFrame,
    colunas_features: list[str],
    coluna_binaria: str,
    especificacao_modelo: EspecificacaoModelo,
    minimo_semanas_treino: int,
    passo: int,
    coluna_data: str = "data",
) -> tuple[float, int]:
    """

    Mede o acerto (jeito honesto) em dizer se os casos vao acelerar.

    Treina no passado e preve a proxima semana, sempre. Pula os passos em que o
    treino so tem um tipo de resposta (sem os dois lados nao da pra treinar).

    Returns:
        O acerto equilibrado (balanced accuracy) e quantas semanas foram testadas.

    """
    dados_validos = (
        dados.dropna(subset=colunas_features + [coluna_binaria])
        .sort_values(coluna_data)
        .reset_index(drop=True)
    )
    valores_reais = []
    valores_previstos = []
    for indice_corte in range(minimo_semanas_treino, len(dados_validos), passo):
        treino = dados_validos.iloc[:indice_corte]
        teste = dados_validos.iloc[indice_corte:indice_corte + 1]
        if treino[coluna_binaria].nunique() < 2:
            continue
        modelo = especificacao_modelo.criar()
        modelo.fit(treino[colunas_features], treino[coluna_binaria])
        valores_previstos.append(int(modelo.predict(teste[colunas_features])[0]))
        valores_reais.append(int(teste[coluna_binaria].to_numpy()[0]))
    return balanced_accuracy_score(valores_reais, valores_previstos), len(valores_reais)


def acerto_aceleracao_split_aleatorio(
    dados: pd.DataFrame,
    colunas_features: list[str],
    coluna_binaria: str,
    especificacao_modelo: EspecificacaoModelo,
    sementes: tuple[int, ...],
    fracao_teste: float = 0.3,
) -> float:
    """

    Mede o acerto do jeito da literatura: embaralha e separa treino/teste.

    Esse jeito costuma dar numeros mais altos que a realidade, porque deixa o
    modelo treinar com semanas do meio do periodo que ele depois "adivinha".
    Roda com varias sementes de sorteio e tira a media.

    Returns:
        A media do acerto equilibrado (balanced accuracy) sobre as sementes.

    """
    dados_validos = dados.dropna(subset=colunas_features + [coluna_binaria]).copy()
    acertos = []
    for semente in sementes:
        features_treino, features_teste, alvo_treino, alvo_teste = train_test_split(
            dados_validos[colunas_features],
            dados_validos[coluna_binaria],
            test_size=fracao_teste,
            random_state=semente,
            stratify=dados_validos[coluna_binaria],
        )
        modelo = especificacao_modelo.criar()
        modelo.fit(features_treino, alvo_treino)
        acertos.append(balanced_accuracy_score(alvo_teste, modelo.predict(features_teste)))
    return float(np.mean(acertos))
