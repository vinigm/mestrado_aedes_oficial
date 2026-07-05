"""

Teste de Diebold-Mariano: serve pra dizer se um modelo erra MENOS que outro de
um jeito que da pra confiar (nao foi so sorte).

Aqui a gente compara dois modelos de previsao de casos: o M0 (so clima) e o M1
(clima + mosquito). O teste olha, semana a semana, a diferenca entre os erros
dos dois e responde: essa vantagem do M1 e forte o bastante pra ser levada a
serio? Ele ja vem ajustado pra previsoes de varias semanas a frente (que fazem
os erros de semanas seguidas "andarem juntos") e pra amostras pequenas.

"""

import dataclasses

import numpy as np
from scipy import stats

# Se a variancia estimada nao for positiva, o teste nao tem como ser calculado.
VARIANCIA_MINIMA = 0.0

# Piso pequeno pra correcao de amostra pequena, pra nunca tirar raiz de numero negativo.
PISO_CORRECAO_AMOSTRA_PEQUENA = 1e-9


@dataclasses.dataclass(frozen=True)
class ResultadoDieboldMariano:
    """

    O que o teste de Diebold-Mariano devolve.

    Attributes:
        diferenca_media: Media da diferenca de erro entre os dois modelos
            (positivo = o M1, com mosquito, erra menos).
        estatistica: O numero do teste (quanto maior, mais forte a vantagem).
        valor_p: A chance de essa vantagem ter sido so sorte (quanto menor, mais
            confiavel que o M1 erra menos de verdade).
        n: Quantas semanas de teste entraram na conta.

    """

    diferenca_media: float
    estatistica: float
    valor_p: float
    n: int


def teste_diebold_mariano(
    erros_m0: np.ndarray,
    erros_m1: np.ndarray,
    horizonte: int,
    tipo_erro: str = "quadratico",
) -> ResultadoDieboldMariano:
    """

    Compara os erros de dois modelos e diz se a vantagem de um sobre o outro e confiavel.

    Olha, semana a semana, a diferenca entre o erro do M0 e o do M1 (o erro pode
    ser medido ao quadrado ou pelo valor absoluto). Como previsoes de varias
    semanas a frente fazem os erros de semanas seguidas andarem juntos, a conta
    da "forca" da vantagem leva isso em conta, e ainda ajusta pra amostras
    pequenas. No fim, da um valor-p de um lado so (a ideia testada e "o M1 erra
    menos").

    Args:
        erros_m0: Erros do modelo M0 (real - previsto), semana a semana.
        erros_m1: Erros do modelo M1, nas mesmas semanas.
        horizonte: Quantas semanas a frente a previsao olhava.
        tipo_erro: "quadratico" (erro ao quadrado) ou "absoluto" (valor absoluto).

    Returns:
        Um ResultadoDieboldMariano com a diferenca media, a estatistica, o
        valor-p e o numero de semanas.

    """
    if tipo_erro == "quadratico":
        diferenca = erros_m0 ** 2 - erros_m1 ** 2
    else:
        diferenca = np.abs(erros_m0) - np.abs(erros_m1)

    n = len(diferenca)
    diferenca_media = diferenca.mean()
    desvios = diferenca - diferenca_media

    def autocovariancia(defasagem):
        return np.sum(desvios[defasagem:] * desvios[: n - defasagem]) / n

    variancia = autocovariancia(0) + 2 * sum(
        autocovariancia(defasagem) for defasagem in range(1, horizonte)
    )
    if variancia <= VARIANCIA_MINIMA:
        return ResultadoDieboldMariano(diferenca_media, float("nan"), float("nan"), n)

    estatistica = diferenca_media / np.sqrt(variancia / n)
    correcao_amostra_pequena = (n + 1 - 2 * horizonte + horizonte * (horizonte - 1) / n) / n
    estatistica = estatistica * np.sqrt(max(correcao_amostra_pequena, PISO_CORRECAO_AMOSTRA_PEQUENA))
    valor_p = float(stats.t.cdf(-estatistica, df=n - 1))
    return ResultadoDieboldMariano(diferenca_media, estatistica, valor_p, n)
