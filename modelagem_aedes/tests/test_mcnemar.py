"""

Aqui a gente confere se a conta do teste de McNemar (avaliacao.mcnemar) esta
certa. Esse teste compara dois modelos avaliados nos mesmos casos e mostra se
um acerta e erra de um jeito bem diferente do outro.

O arquivo confere as contagens de quando um modelo acerta e o outro erra, se
o programa escolhe certo entre as duas contas possiveis (uma pra quando ha
poucas discordancias entre os modelos, outra pra quando ha muitas) e compara
os resultados com os do scipy, um pacote de contas prontas usado aqui so pra
conferir. Roda rapido. Pra rodar: "python tests/test_mcnemar.py" (ou pytest).

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from scipy.stats import binomtest, chi2

from avaliacao import mcnemar



# Transforma uma lista de acertos e erros (True/False) numa lista pronta pra fazer conta.
def como_acertos(lista_de_bools):
    return np.asarray(lista_de_bools, bool)



def test_sem_discordancia_p_valor_um():
    resultado = mcnemar.teste_mcnemar(
        como_acertos([True, False, True]), como_acertos([True, False, True])
    )
    assert resultado.n_a_certo_b_errado == 0
    assert resultado.n_a_errado_b_certo == 0
    assert resultado.estatistica == 0.0
    assert resultado.valor_p == 1.0



def test_poucas_discordancias_usa_binomial_exato():
    acertos_a = como_acertos([True, True, True, False, False])
    acertos_b = como_acertos([False, True, True, True, False])
    resultado = mcnemar.teste_mcnemar(acertos_a, acertos_b)
    n_discordancias = resultado.n_a_certo_b_errado + resultado.n_a_errado_b_certo
    assert n_discordancias < mcnemar.MINIMO_DISCORDANCIAS_QUI_QUADRADO
    menor_discordancia = min(resultado.n_a_certo_b_errado, resultado.n_a_errado_b_certo)
    p_esperado = binomtest(menor_discordancia, n_discordancias, 0.5).pvalue
    assert np.isclose(resultado.valor_p, p_esperado, rtol=1e-12)



def test_muitas_discordancias_usa_qui_quadrado():
    acertos_a = como_acertos([True] * 40)
    acertos_b = como_acertos([False] * 30 + [True] * 10)
    resultado = mcnemar.teste_mcnemar(acertos_a, acertos_b)
    n_discordancias = resultado.n_a_certo_b_errado + resultado.n_a_errado_b_certo
    assert n_discordancias >= mcnemar.MINIMO_DISCORDANCIAS_QUI_QUADRADO
    diferenca_absoluta = abs(resultado.n_a_certo_b_errado - resultado.n_a_errado_b_certo)
    estatistica_esperada = (diferenca_absoluta - 1) ** 2 / n_discordancias
    assert np.isclose(resultado.estatistica, estatistica_esperada, rtol=1e-12)
    p_esperado = float(chi2.sf(estatistica_esperada, 1))
    assert np.isclose(resultado.valor_p, p_esperado, rtol=1e-12)


if __name__ == "__main__":
    testes = [
        valor
        for nome, valor in sorted(globals().items())
        if nome.startswith("test_") and callable(valor)
    ]
    for teste in testes:
        teste()
        print("OK:", teste.__name__)
    print(f"\n{len(testes)} teste(s) passaram")
