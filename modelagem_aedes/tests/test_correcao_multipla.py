"""

Testes da correcao de Holm.

A conferencia central e um teste DIFERENCIAL contra uma segunda implementacao,
escrita do zero a partir da definicao do metodo (nao e o mesmo codigo com outro
nome): a versao de referencia usa lacos explicitos e listas Python, sem
argsort nem acumulacao vetorizada. Se as duas concordarem em centenas de
entradas aleatorias, o risco de um erro de vetorizacao passar batido cai muito.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from avaliacao.correcao_multipla import corrigir_holm


def corrigir_holm_referencia(valores_p: list[float]) -> list[float]:
    """

    Segunda implementacao de Holm, escrita direto da definicao, so com lacos.

    Serve unicamente como referencia dos testes diferenciais. Nao usa numpy nem
    nenhuma operacao vetorizada, de proposito: o objetivo e nao repetir o
    mesmo raciocinio de implementacao da versao de producao.

    """
    indices_validos = []
    for posicao, valor in enumerate(valores_p):
        if not np.isnan(valor):
            indices_validos.append(posicao)

    numero_de_testes = len(indices_validos)
    corrigidos = [float("nan")] * len(valores_p)
    if numero_de_testes == 0:
        return corrigidos

    fila = []
    for posicao in indices_validos:
        fila.append((valores_p[posicao], posicao))
    fila.sort()

    maior_ajustado_ate_agora = 0.0
    for lugar_na_fila, (valor_bruto, posicao_original) in enumerate(fila):
        testes_restantes = numero_de_testes - lugar_na_fila
        ajustado = valor_bruto * testes_restantes

        if ajustado < maior_ajustado_ate_agora:
            ajustado = maior_ajustado_ate_agora
        maior_ajustado_ate_agora = ajustado

        if ajustado > 1.0:
            ajustado = 1.0

        corrigidos[posicao_original] = ajustado

    return corrigidos


def test_ancora_conhecida_do_projeto():
    """O McNemar de 16/08/2026: p bruto 0,031 em 6 comparacoes deu Holm 0,185."""
    valores_p = np.array([0.031, 0.20, 0.35, 0.50, 0.70, 0.90])
    corrigidos = corrigir_holm(valores_p)
    assert corrigidos[0] == pytest.approx(0.186, abs=0.001)


def test_diferencial_contra_implementacao_de_referencia():
    """As duas implementacoes concordam em 500 sorteios independentes."""
    gerador = np.random.default_rng(20260829)

    for _ in range(500):
        quantidade = int(gerador.integers(1, 15))
        valores_p = gerador.random(quantidade)

        obtido = corrigir_holm(valores_p)
        esperado = corrigir_holm_referencia(list(valores_p))

        np.testing.assert_allclose(obtido, esperado, rtol=1e-12, atol=1e-15)


def test_diferencial_com_nulos_e_empates():
    """Empates exatos e NaN tambem batem entre as duas implementacoes."""
    casos = [
        [0.02, 0.02, 0.02],
        [0.5, np.nan, 0.1, np.nan],
        [np.nan],
        [0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.001],
    ]
    for valores_p in casos:
        obtido = corrigir_holm(np.array(valores_p, dtype=float))
        esperado = corrigir_holm_referencia(valores_p)
        np.testing.assert_allclose(obtido, esperado, rtol=1e-12, atol=1e-15, equal_nan=True)


def test_lista_vazia_devolve_lista_vazia():
    assert corrigir_holm(np.array([])).size == 0


def test_nunca_passa_de_um():
    valores_p = np.array([0.9, 0.95, 0.99])
    assert (corrigir_holm(valores_p) <= 1.0).all()


def test_nunca_diminui_na_ordem_dos_p_brutos():
    """Um teste com p bruto maior nao pode terminar com p corrigido menor."""
    valores_p = np.array([0.01, 0.02, 0.03, 0.04])
    corrigidos = corrigir_holm(valores_p)
    assert (np.diff(corrigidos) >= -1e-15).all()


def test_um_unico_teste_nao_e_penalizado():
    """Com uma comparacao so, Holm devolve o proprio p bruto."""
    assert corrigir_holm(np.array([0.031]))[0] == pytest.approx(0.031)


def test_rejeita_p_fora_do_intervalo():
    with pytest.raises(ValueError):
        corrigir_holm(np.array([0.5, 1.5]))
    with pytest.raises(ValueError):
        corrigir_holm(np.array([-0.1, 0.5]))
