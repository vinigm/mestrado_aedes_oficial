"""

Configuracao do experimento que compara o nosso modelo com o metodo da
literatura, nos mesmos dados de Porto Alegre.

Como nao temos as previsoes publicadas dos autores, a gente refaz o METODO deles
(so clima, no estilo Oliveira et al. 2025) e compara com o nosso (clima +
mosquito), os dois contra a realidade. Sao duas comparacoes: prever o numero de
casos, e dizer se os casos vao "acelerar".

"""

import dataclasses

from lightgbm import LGBMClassifier, LGBMRegressor

from config.modelo import EspecificacaoModelo


@dataclasses.dataclass(frozen=True)
class ConfiguracaoComparacaoLiteratura:
    """

    Os ajustes do experimento de comparacao com a literatura.

    Attributes:
        nome: Nome que identifica este experimento.
        coluna_alvo: Nome da coluna de casos ('casos').
        modelo_regressao: A ficha do algoritmo que preve o numero de casos (parte 1).
        modelo_classificacao: A ficha do algoritmo que preve a aceleracao (parte 2).
        horizontes: Quantas semanas a frente prever, na comparacao de casos.
        minimo_semanas_treino: Historico minimo antes de comecar a prever.
        passo_regressao: De quantas em quantas semanas testar, na parte de casos.
        passo_classificacao: De quantas em quantas semanas testar, na parte de
            aceleracao (1 = testa todas).
        defasagem_aceleracao: Contra quantas semanas atras comparar pra dizer que
            os casos "aceleraram" (subiram).
        sementes_split: As sementes de sorteio usadas no jeito da literatura
            (embaralhar e separar treino/teste), pra tirar a media.
        fracao_teste: Que pedaco dos dados vira teste nesse sorteio.
        referencia_oliveira: O acerto que o trabalho do Oliveira reportou (pra
            marcar no grafico).
        arquivo_saida_casos: Arquivo .csv com o resultado da comparacao de casos.
        arquivo_saida_oliveira: Arquivo .csv com o resultado da aceleracao.

    """

    nome: str
    coluna_alvo: str
    modelo_regressao: EspecificacaoModelo
    modelo_classificacao: EspecificacaoModelo
    horizontes: tuple[int, ...]
    minimo_semanas_treino: int
    passo_regressao: int
    passo_classificacao: int
    defasagem_aceleracao: int
    sementes_split: tuple[int, ...]
    fracao_teste: float
    referencia_oliveira: float
    arquivo_saida_casos: str
    arquivo_saida_oliveira: str


COMPARACAO_LITERATURA = ConfiguracaoComparacaoLiteratura(
    nome="comparacao_literatura",
    coluna_alvo="casos",
    modelo_regressao=EspecificacaoModelo(
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
    ),
    modelo_classificacao=EspecificacaoModelo(
        nome="lightgbm",
        classe=LGBMClassifier,
        parametros={
            "n_estimators": 250,
            "learning_rate": 0.05,
            "num_leaves": 15,
            "min_child_samples": 5,
            "verbose": -1,
            "n_jobs": -1,
        },
    ),
    horizontes=tuple(range(1, 13)),
    minimo_semanas_treino=104,
    passo_regressao=2,
    passo_classificacao=1,
    defasagem_aceleracao=2,
    sementes_split=(0, 1, 2, 3, 4),
    fracao_teste=0.3,
    referencia_oliveira=0.6738,
    arquivo_saida_casos="comparacao_casos_resultados.csv",
    arquivo_saida_oliveira="comparacao_oliveira_resultados.csv",
)
