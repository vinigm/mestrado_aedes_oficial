"""

A CONFIGURACAO DE REFERENCIA do projeto para previsao do numero de casos.

Escolhida em 30/08/2026 por um grid de 120 execucoes sobre 30 configuracoes
(3 algoritmos x 5 funcoes de perda x com/sem vetor), com protocolo declarado
por escrito ANTES de rodar. O registro completo, com as regras e os numeros,
esta em analises/2026-08-30_grid_completo/.

O que este experimento tem de diferente do cidade_regressao:

  - ALGORITMO: HistGradientBoosting no lugar do LightGBM. Foi o melhor dos nove
    testados (R2 medio 0,779 contra 0,749 do LightGBM).

  - FUNCAO DE PERDA: quantilica em 0,85, no lugar do erro quadratico. E a
    mudanca que mais pesou - trocar a perda custa 20,2% de MAE, contra 16,5%
    de trocar o melhor algoritmo pelo pior. As seis configuracoes de perda
    padrao do grid ficaram entre a 10a e a 23a posicao de 30.

  - PASSO 1 no lugar de 2: avalia toda semana, e nao a cada duas. Dobra a base
    de avaliacao (de ~150 para ~300 pontos por horizonte) ao custo de dobrar o
    tempo de execucao.

  - So k=6 no lugar de (6, 8): o grid rodou com as seis melhores colunas de
    clima, e nao ha motivo para reprocessar k=8 aqui.

ATENCAO AO QUE O MODELO ENTREGA. Com perda quantilica em 0,85 ele NAO estima o
numero esperado de casos: estima um PATAMAR que so sera ultrapassado em 15% das
vezes. E enviesado para cima de proposito, o que e adequado para alarme
epidemiologico - onde subestimar custa mais caro que superestimar - mas muda o
que o numero significa. Qualquer texto que cite uma previsao deste experimento
precisa dizer isso.

O conjunto de referencia e o M1 (com as colunas de vetor). Como
pipeline.rodar_regressao_selecao_clima roda M0 e M1 lado a lado para medir o
ganho do vetor, a saida traz os dois; a linha de referencia e a M1.

"""

import dataclasses

from sklearn.ensemble import HistGradientBoostingRegressor

from config.experimentos.cidade_regressao import CIDADE_REGRESSAO, LGBM_REGRESSAO
from config.modelo import EspecificacaoModelo

# O quantil escolhido pelo grid. As tres primeiras colocadas foram o mesmo
# algoritmo variando so este numero, separadas por poucos porcento de MAE - ou
# seja, estatisticamente indistinguiveis.
#
# HISTORICO, porque este numero ja mudou uma vez e a razao importa:
#
#   - No grid original de 30/08/2026 o 0,80 venceu, e a decisao foi mantida de
#     proposito mesmo com o 0,85 melhor no periodo de AVALIACAO. Trocar por ali
#     invalidaria o julgamento, ja que a avaliacao e juiz e nao campo de treino.
#
#   - Em 13/09/2026 o vazamento temporal foi corrigido e as 30 configuracoes
#     foram reprocessadas, com pre-declaracao escrita antes (a Fase 2 do
#     analises/2026-09-13_correcao_vazamento_treino/). O ranking mudou: pelo
#     MESMO criterio pre-declarado - menor MAE medio no periodo de CALIBRACAO -
#     o 0,85 com vetor passou a primeiro, com 42,02 contra 42,71 do 0,80, que
#     caiu para terceiro.
#
# Ou seja, a troca NAO foi escolher pelo periodo de avaliacao. Foi o mesmo
# criterio de sempre, aplicado a numeros que deixaram de estar contaminados.
#
# Conferido em 23/09/2026 recalculando do CSV bruto: os oito numeros publicados
# no painel (MAE 98,0/219,7/272,6/278,7 e R2 0,898/0,628/0,450/0,437) reproduzem
# exatamente a linha quantil_0.85, e nao a do 0,80.
QUANTIL_DE_REFERENCIA = 0.85

HIST_GRADIENT_BOOSTING_QUANTIL = EspecificacaoModelo(
    nome="hist_gradient_boosting_quantil",
    classe=HistGradientBoostingRegressor,
    parametros={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 5,
        "random_state": 42,
        "loss": "quantile",
        "quantile": QUANTIL_DE_REFERENCIA,
    },
)

# A selecao das colunas de clima CONTINUA usando o LightGBM de regressao, e nao
# o modelo de referencia. Nao e descuido: foi com ele que o ranking de clima do
# grid foi produzido, e trocar aqui mudaria as seis colunas escolhidas, tornando
# o resultado nao comparavel com o que foi medido em 30/08/2026.
CIDADE_REFERENCIA = dataclasses.replace(
    CIDADE_REGRESSAO,
    nome="cidade_referencia",
    modelo=HIST_GRADIENT_BOOSTING_QUANTIL,
    modelo_selecao_clima=LGBM_REGRESSAO,
    valores_k=(6,),
    passo=1,
    arquivo_saida="cidade_referencia_resultados.csv",
)
