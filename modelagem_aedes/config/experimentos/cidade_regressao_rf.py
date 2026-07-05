"""

Exemplo de como comparar outro algoritmo: o MESMO experimento de regressao 4c,
mas usando RandomForest no lugar do LightGBM.

E so uma copia do cidade_regressao trocando duas coisas: o modelo (agora
RandomForest) e o arquivo de saida. Todo o resto (corte de maturidade, colunas,
horizontes) fica igual, pra a comparacao entre os dois algoritmos ser justa. A
ESCOLHA das colunas de clima continua sendo feita pelo LightGBM, de proposito,
pra os dois algoritmos competirem sobre exatamente as mesmas colunas.

O resultado sai num arquivo proprio, e a coluna 'algoritmo' diz "random_forest",
entao da pra empilhar com o resultado do LightGBM e comparar lado a lado.

"""

import dataclasses

from sklearn.ensemble import RandomForestRegressor

from config.experimentos.cidade_regressao import CIDADE_REGRESSAO, LGBM_REGRESSAO
from config.modelo import EspecificacaoModelo

RANDOM_FOREST = EspecificacaoModelo(
    nome="random_forest",
    classe=RandomForestRegressor,
    parametros={
        "n_estimators": 300,
        "min_samples_leaf": 5,
        "n_jobs": -1,
        "random_state": 42,
    },
)

CIDADE_REGRESSAO_RF = dataclasses.replace(
    CIDADE_REGRESSAO,
    nome="cidade_regressao_rf",
    modelo=RANDOM_FOREST,
    modelo_selecao_clima=LGBM_REGRESSAO,
    arquivo_saida="clima_enxuto_maturidade_rf_resultados.csv",
    # MESMO cenario do cidade_regressao (4c) -> os dois modelos caem no mesmo
    # experimento do MLflow, pra comparar LightGBM x RandomForest lado a lado.
    cenario="cidade_regressao",
)
