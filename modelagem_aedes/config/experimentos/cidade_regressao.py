"""

Configuracao do experimento de regressao (regressao = tentar adivinhar um
numero, e nao so dizer se vai ter surto ou nao): quantos casos de dengue a
cidade vai ter.

Este e o Modelo 4c (clima resumido, sem os dados do El Nino/La Nina, mais os
dados do mosquito, com um corte pra nao usar semanas recentes demais nos
casos): primeiro fica so com as poucas colunas de clima que mais ajudam (M0),
depois ve o quanto melhora quando soma os dados do mosquito (M1 = M0 + dados
do mosquito), pra cada quantidade de semanas a frente que tenta prever, e pra
duas quantidades de colunas de clima (K=6 e K=8).

O modelo em si (LightGBM, aqui) vem de uma ficha reutilizavel (EspecificacaoModelo),
entao da pra trocar por outro algoritmo sem mexer no resto.

"""

import dataclasses

from lightgbm import LGBMRegressor

from config.modelo import EspecificacaoModelo

# Ficha do LightGBM de regressao (a mesma usada por varios experimentos de
# regressao). Trocar isto por outra ficha = rodar outro algoritmo.
LGBM_REGRESSAO = EspecificacaoModelo(
    nome="lightgbm",
    classe=LGBMRegressor,
    parametros={
        "n_estimators": 250,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_child_samples": 5,
        "verbose": -1,
        "n_jobs": -1,
    },
)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoRegressao:
    """

    Os ajustes do experimento de regressao de casos na cidade.

    Attributes:

        nome: Nome que identifica este experimento.

        coluna_alvo: Nome da coluna que o modelo tenta prever (depois que os
            dados sao organizados, essa coluna se chama 'casos').

        modelo: A ficha do algoritmo usado pra prever os casos (LightGBM,
            RandomForest, etc.) e os ajustes dele.

        modelo_selecao_clima: A ficha do algoritmo que ESCOLHE as poucas colunas
            de clima que mais ajudam (pode ser o mesmo do modelo, ou fixo, pra a
            comparacao entre modelos ser justa).

        semanas_corte_maturidade: Quantas semanas mais recentes ficam com o
            numero de casos apagado, porque esse numero ainda esta incompleto.

        horizontes: Quantas semanas a frente o modelo tenta prever, em cada rodada.

        horizontes_selecao_clima: Quais dessas semanas a frente sao usadas pra
            decidir quais colunas de clima valem a pena manter.

        valores_k: Quantas colunas de clima entram no modelo (testa duas
            opcoes, ficando so com as que mais ajudam).

        fracao_treino_selecao: Que pedaco inicial dos dados e usado pra
            escolher quais colunas de clima manter.

        minimo_semanas_treino: Quantas semanas de historico o modelo precisa
            ter, no minimo, antes de comecar a prever (o modelo treina no
            passado e preve o futuro, semana a semana).

        passo: De quantas em quantas semanas o modelo repete esse treino no
            passado e previsao no futuro.

        colunas_ignorar: Colunas que nao entram no modelo (identificadores,
            dados do El Nino/La Nina, e numeros brutos que ja viram outras colunas).

        padroes_vetor: Pedacos de nome que indicam que a coluna e sobre o
            mosquito (o vetor da dengue).

        padroes_clima: Pedacos de nome que indicam que a coluna e sobre o clima.

        arquivo_saida: Nome do arquivo .csv onde a tabela de resultados e salva.

        colunas_saida: Quais colunas (e em que ordem) ficam na tabela final.

        arquivo_referencias: Se preenchido, um resultado ja salvo de onde puxar
            algumas linhas extras pra juntar no fim (deixa None pra nao juntar nada).

        conjuntos_referencia: Quais linhas puxar desse resultado de referencia.

        cenario: Nome do CENARIO pro versionamento (MLflow). Experimentos que sao
            o mesmo cenario com modelos diferentes (ex.: 4c com LightGBM e 4c com
            RandomForest) usam o MESMO cenario, pra os runs caírem juntos e dar pra
            comparar os modelos lado a lado. Se ficar None, usa-se o proprio 'nome'.

    """

    nome: str
    coluna_alvo: str
    modelo: EspecificacaoModelo
    modelo_selecao_clima: EspecificacaoModelo
    semanas_corte_maturidade: int
    horizontes: tuple[int, ...]
    horizontes_selecao_clima: tuple[int, ...]
    valores_k: tuple[int, ...]
    fracao_treino_selecao: float
    minimo_semanas_treino: int
    passo: int
    colunas_ignorar: tuple[str, ...]
    padroes_vetor: tuple[str, ...]
    padroes_clima: tuple[str, ...]
    arquivo_saida: str
    colunas_saida: tuple[str, ...]
    arquivo_referencias: str | None = None
    conjuntos_referencia: tuple[str, ...] = ()
    cenario: str | None = None


CIDADE_REGRESSAO = ConfiguracaoRegressao(
    nome="cidade_regressao",
    coluna_alvo="casos",
    modelo=LGBM_REGRESSAO,
    modelo_selecao_clima=LGBM_REGRESSAO,
    semanas_corte_maturidade=12,
    horizontes=tuple(range(1, 13)),
    horizontes_selecao_clima=(1, 4, 8),
    valores_k=(6, 8),
    fracao_treino_selecao=0.60,
    minimo_semanas_treino=104,
    passo=2,
    # As colunas 'data' e 'casos' ja saem com esse nome depois que os dados sao
    # organizados; a coluna alvo ('casos') NAO entra na lista abaixo, porque o
    # modelo usa o historico dela mesma pra prever o futuro. Ficam de fora so
    # os identificadores, os dados do El Nino/La Nina e os numeros brutos.
    colunas_ignorar=(
        "fonte", "SE", "data", "ano", "semana", "interpolado", "denominador_aproximado",
        "aedes_aegypti", "aedes_albopictus", "culex_sp", "numero_de_armadilhas",
        "nino34_anom", "oni",
    ),
    padroes_vetor=("aedes", "armadilha", "vetor"),
    padroes_clima=(
        "temp", "precip", "orvalho", "umid", "pressao", "radiacao", "vento", "dias_de_chuva",
    ),
    arquivo_saida="clima_enxuto_maturidade_resultados.csv",
    colunas_saida=("algoritmo", "conjunto", "h", "n", "MAE", "R2"),
)
