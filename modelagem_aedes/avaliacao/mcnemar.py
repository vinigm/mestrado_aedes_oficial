"""

O teste de McNemar compara dois modelos que foram avaliados nos mesmos casos,
pra ver se um erra e acerta de um jeito bem diferente do outro, ou se essas
diferencas sao so coincidencia.

"""

import dataclasses

import numpy as np
from scipy.stats import binomtest, chi2

# Se o numero de vezes que os modelos discordam for menor que isso, o codigo usa a conta mais
# exata (teste binomial) em vez da aproximacao mais rapida (qui-quadrado).
MINIMO_DISCORDANCIAS_QUI_QUADRADO = 25


@dataclasses.dataclass(frozen=True)
class ResultadoMcNemar:
    """

    Resultado da comparacao entre dois modelos, testados exatamente nos mesmos casos.

    Attributes:
        n_a_certo_b_errado: Quantos casos o modelo A acertou e o modelo B errou.
        n_a_errado_b_certo: Quantos casos o modelo A errou e o modelo B acertou.
        estatistica: Numero que mostra o tamanho da diferenca entre os dois
            modelos (a conta qui-quadrado, ja com o ajuste chamado correcao de
            continuidade).
        valor_p: Chance de essa diferenca ser so coincidencia (p-valor). Quando
            ha poucas discordancias, calculado de um jeito mais exato (teste
            binomial).

    """

    n_a_certo_b_errado: int
    n_a_errado_b_certo: int
    estatistica: float
    valor_p: float


def teste_mcnemar(
    acertos_modelo_a: np.ndarray,
    acertos_modelo_b: np.ndarray,
) -> ResultadoMcNemar:
    """

    Ve se dois modelos acertam e erram de um jeito bem diferente, nos mesmos casos de teste.

    Compara, caso a caso, quando um modelo acerta e o outro erra. Quando ha
    poucos casos assim (poucas discordancias), usa um jeito de calcular mais
    exato (teste binomial); quando ha muitos, usa uma aproximacao mais rapida
    (qui-quadrado, com um pequeno ajuste chamado correcao de continuidade).

    Args:
        acertos_modelo_a: Lista dizendo, ponto por ponto, se o modelo A acertou (verdadeiro) ou errou (falso).
        acertos_modelo_b: Lista dizendo, ponto por ponto, se o modelo B acertou (verdadeiro) ou errou (falso).

    Returns:
        O resultado da comparacao: quantos pontos cada modelo acertou sozinho,
        a conta final e a chance de essa diferenca ser so coincidencia
        (p-valor). Se os dois modelos nunca discordarem, devolve conta 0.0 e
        p-valor 1.0.

    """
    acertos_a = np.asarray(acertos_modelo_a, bool)
    acertos_b = np.asarray(acertos_modelo_b, bool)
    n_a_certo_b_errado = int(np.sum(acertos_a & ~acertos_b))
    n_a_errado_b_certo = int(np.sum(~acertos_a & acertos_b))
    n_discordancias = n_a_certo_b_errado + n_a_errado_b_certo

    if n_discordancias == 0:
        return ResultadoMcNemar(n_a_certo_b_errado, n_a_errado_b_certo, 0.0, 1.0)

    # Conta qui-quadrado do teste de McNemar, com o ajuste chamado correcao de continuidade (o -1).
    diferenca_absoluta = abs(n_a_certo_b_errado - n_a_errado_b_certo)
    estatistica = (diferenca_absoluta - 1) ** 2 / n_discordancias

    if n_discordancias < MINIMO_DISCORDANCIAS_QUI_QUADRADO:
        menor_discordancia = min(n_a_certo_b_errado, n_a_errado_b_certo)
        valor_p = binomtest(menor_discordancia, n_discordancias, 0.5).pvalue
    else:
        valor_p = float(chi2.sf(estatistica, 1))

    return ResultadoMcNemar(n_a_certo_b_errado, n_a_errado_b_certo, estatistica, valor_p)
