"""

Aqui o programa separa as colunas da tabela em tres grupos - nucleo, clima e
vetor do mosquito - e escolhe, sem deixar o modelo ver o futuro, quais poucas
colunas de clima realmente ajudam a prever os casos.

Isso e usado pelos experimentos de regressao da cidade, quando a ideia e
montar um modelo mais enxuto so com as colunas de clima que mais importam. Qual
modelo faz essa escolha chega pronto na ficha (LightGBM por padrao).

"""

import pandas as pd

from config.modelo import EspecificacaoModelo
from dominio.features import construir_alvo_horizonte


def separar_grupos_de_features(
    dados: pd.DataFrame,
    colunas_ignorar: tuple[str, ...],
    padroes_vetor: tuple[str, ...],
    padroes_clima: tuple[str, ...],
) -> tuple[list[str], list[str], list[str]]:
    """

    Separa as colunas da tabela em tres grupos: nucleo, clima e vetor.

    Uma coluna vai pro grupo "vetor" se o nome dela tiver algum dos pedacos de
    texto usados pra marcar coisas do mosquito; vai pro grupo "clima" se tiver
    algum pedaco de texto de clima; e cai no grupo "nucleo" nos outros casos.
    As colunas da lista colunas_ignorar (identificadores, dados do El Nino,
    contagens brutas) ficam de fora dos tres grupos. A ordem de cada lista
    segue a ordem das colunas na tabela original.

    Returns:
        Tres listas com os nomes das colunas: nucleo, clima e vetor.

    """
    todas_as_features = [c for c in dados.columns if c not in colunas_ignorar]
    colunas_vetor = [c for c in todas_as_features if any(p in c for p in padroes_vetor)]
    colunas_clima = [c for c in todas_as_features if any(p in c for p in padroes_clima)]
    colunas_nucleo = [
        c for c in todas_as_features if c not in colunas_vetor and c not in colunas_clima
    ]
    return colunas_nucleo, colunas_clima, colunas_vetor


# Le "o quanto cada coluna ajudou" de um modelo ja treinado, seja ele qual for.
# O LightGBM expoe isso pelo "ganho" (via booster_); os modelos do scikit-learn
# (RandomForest, etc.) e o XGBoost expoem via feature_importances_.
def importancia_do_modelo(modelo, nomes_features: list[str]) -> pd.Series:
    if hasattr(modelo, "booster_"):
        valores = modelo.booster_.feature_importance(importance_type="gain")
    else:
        valores = modelo.feature_importances_
    return pd.Series(valores, index=nomes_features)


def selecionar_clima_por_ganho(
    dados: pd.DataFrame,
    colunas_nucleo: list[str],
    colunas_clima: list[str],
    coluna_alvo: str,
    horizontes_selecao: tuple[int, ...],
    especificacao_modelo_selecao: EspecificacaoModelo,
    fracao_treino: float,
) -> pd.Series:
    """

    Coloca as colunas de clima em ordem de importancia, sem deixar o modelo
    ver o futuro.

    Para cada horizonte (quantas semanas a frente), o codigo treina um modelo
    usando so a parte mais antiga dos dados - a fatia definida por
    'fracao_treino' - pra nao deixar o modelo aprender com coisa que ainda nao
    tinha acontecido. Ele usa as colunas de nucleo junto com as de clima, e
    depois soma o quanto cada coluna de clima ajudou o modelo a acertar. Esse
    total somado mostra quais poucas colunas de clima valem a pena entrar no
    modelo final, mais enxuto.

    Args:
        dados: A tabela, ja com as colunas calculadas prontas.
        colunas_nucleo: Nomes das colunas do grupo nucleo (historico dos
            casos e o padrao que se repete todo ano).
        colunas_clima: Nomes de todas as colunas de clima candidatas.
        coluna_alvo: Nome da coluna que o modelo tenta prever (ex.: 'casos').
        horizontes_selecao: Quantas semanas a frente sao usadas pra pontuar
            cada coluna de clima.
        especificacao_modelo_selecao: A ficha do modelo que faz essa escolha
            (por padrao, LightGBM). Pode ser diferente do modelo do experimento.
        fracao_treino: Qual fatia inicial dos dados e usada pra treinar o
            modelo nessa escolha (o resto fica de fora, de proposito).

    Returns:
        Uma lista com o total de importancia de cada coluna de clima, da que
        ajudou mais pra que ajudou menos.

    """
    importancia_acumulada = pd.Series(0.0, index=colunas_clima)
    for horizonte in horizontes_selecao:
        dados_horizonte = construir_alvo_horizonte(dados, coluna_alvo, horizonte)
        features = colunas_nucleo + colunas_clima + ["alvo_sin", "alvo_cos"]
        dados_validos = (
            dados_horizonte.dropna(subset=features + ["y_h"])
            .sort_values("data")
            .reset_index(drop=True)
        )
        n_treino = int(len(dados_validos) * fracao_treino)
        treino = dados_validos.iloc[:n_treino]

        modelo = especificacao_modelo_selecao.criar()
        modelo.fit(treino[features], treino["y_h"])
        ganho_por_feature = importancia_do_modelo(modelo, features)
        importancia_acumulada = importancia_acumulada.add(
            ganho_por_feature.reindex(colunas_clima).fillna(0), fill_value=0
        )
    return importancia_acumulada.sort_values(ascending=False)
