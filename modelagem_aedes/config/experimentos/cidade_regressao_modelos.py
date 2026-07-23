"""

Varios algoritmos rodando o MESMO experimento de regressao (o cidade_regressao,
4c), pra comparar qual preve melhor os casos — alem do LightGBM e do RandomForest
que ja temos.

A regra da comparacao justa: muda SO o algoritmo. Todo o resto fica igual (as
mesmas colunas, os mesmos horizontes, o mesmo corte, e a escolha das colunas de
clima continua sendo feita pelo LightGBM). Assim todos competem nas mesmas
condicoes, e a coluna 'algoritmo' na saida diz qual foi cada um.

Um detalhe: modelos de arvore (ExtraTrees, os boosting) nao ligam pra escala dos
numeros. Ja os lineares (Ridge, ElasticNet), o SVR e o KNN precisam que os numeros
estejam na mesma escala, senao vao mal. Por isso esses sao embrulhados num
"pipeline" que primeiro padroniza os numeros e depois treina.

Os ajustes de cada modelo sao padroes sensatos (nao uma otimizacao pesada de cada
um) — o passo aqui e comparar modelos em pe de igualdade; afinar a fundo quem se
destacar e um passo seguinte.

"""

import dataclasses

from sklearn.ensemble import (
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from config.modelo import EspecificacaoModelo


# Devolve uma "fabrica" que embrulha o modelo num pipeline que padroniza os numeros antes de treinar.
def _com_escala(classe_modelo):
    """

    Alguns modelos (lineares, SVR, KNN) so funcionam bem se os numeros estiverem
    na mesma escala. Esta funcao entrega uma fabrica que, a cada chamada, monta um
    pipeline novo: primeiro padroniza os numeros (StandardScaler) e depois treina
    o modelo. Cada chamada cria pecas novas, entao nada e reaproveitado sem querer.

    """
    def fabrica(**parametros):
        return Pipeline([("escala", StandardScaler()), ("modelo", classe_modelo(**parametros))])

    return fabrica


# --- As fichas dos modelos alternativos (nome + classe + ajustes padrao) ---

# Arvores/boosting (nao precisam de escala): entram direto.
EXTRA_TREES = EspecificacaoModelo(
    nome="extra_trees",
    classe=ExtraTreesRegressor,
    parametros={"n_estimators": 300, "min_samples_leaf": 5, "n_jobs": -1, "random_state": 42},
)

HIST_GRADIENT_BOOSTING = EspecificacaoModelo(
    nome="hist_gradient_boosting",
    classe=HistGradientBoostingRegressor,
    parametros={"max_iter": 250, "learning_rate": 0.05, "max_leaf_nodes": 15, "min_samples_leaf": 5, "random_state": 42},
)

GRADIENT_BOOSTING = EspecificacaoModelo(
    nome="gradient_boosting",
    classe=GradientBoostingRegressor,
    parametros={"n_estimators": 250, "learning_rate": 0.05, "max_depth": 3, "min_samples_leaf": 5, "random_state": 42},
)

# Lineares, kernel e vizinhos (precisam de escala): embrulhados no pipeline.
RIDGE = EspecificacaoModelo(
    nome="ridge",
    classe=_com_escala(Ridge),
    parametros={"alpha": 10.0},
)

ELASTIC_NET = EspecificacaoModelo(
    nome="elastic_net",
    classe=_com_escala(ElasticNet),
    parametros={"alpha": 1.0, "l1_ratio": 0.5, "max_iter": 5000, "random_state": 42},
)

SVR_RBF = EspecificacaoModelo(
    nome="svr",
    classe=_com_escala(SVR),
    parametros={"kernel": "rbf", "C": 100.0, "epsilon": 1.0, "gamma": "scale"},
)

KNN = EspecificacaoModelo(
    nome="knn",
    classe=_com_escala(KNeighborsRegressor),
    parametros={"n_neighbors": 7, "weights": "distance"},
)


# Monta um config = o cidade_regressao trocando SO o modelo (o resto fica igual).
def _config_com_modelo(especificacao: EspecificacaoModelo):
    return dataclasses.replace(
        CIDADE_REGRESSAO,
        nome=f"cidade_regressao_{especificacao.nome}",
        modelo=especificacao,
        arquivo_saida=f"clima_enxuto_maturidade_{especificacao.nome}_resultados.csv",
        # MESMO cenario do cidade_regressao -> todos os modelos caem no mesmo
        # experimento do MLflow, pra comparar lado a lado.
        cenario="cidade_regressao",
    )


# Todos os experimentos alternativos, prontos pra registrar no main.py (nome -> config).
TODOS_MODELOS = {
    config.nome: config
    for config in map(
        _config_com_modelo,
        [EXTRA_TREES, HIST_GRADIENT_BOOSTING, GRADIENT_BOOSTING, RIDGE, ELASTIC_NET, SVR_RBF, KNN],
    )
}
