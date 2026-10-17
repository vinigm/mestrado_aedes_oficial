"""Testes de `aedes/estatistica.py`: Diebold-Mariano HLN, Holm, bootstrap de blocos moveis e a comparacao pareada.

Casos calculados A MAO (cada conta esta no comentario do teste), mais simulacao sob H0 e propriedades.
Nenhum arquivo do projeto e lido ou escrito.
"""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from aedes.estatistica import (
    calcular_autocovariancias,
    comparar_pareado,
    corrigir_por_holm,
    diebold_mariano_hln,
    ganho_percentual,
    intervalo_de_confianca_do_ganho,
    parear_por_data_alvo,
    sortear_indices_de_blocos_moveis,
)

UM_DOMINGO = pd.Timestamp("2024-01-07")
UMA_SEMANA = pd.Timedelta(weeks=1)


def montar_previsoes(datas: list[pd.Timestamp], reais: list[float], previstos: list[float]) -> pd.DataFrame:
    """DataFrame com `data_alvo`, `real`, `previsto`."""
    return pd.DataFrame({"data_alvo": datas, "real": reais, "previsto": previstos})


def semanas(quantidade: int, inicio: pd.Timestamp = UM_DOMINGO) -> list[pd.Timestamp]:
    """Domingos consecutivos."""
    return [inicio + i * UMA_SEMANA for i in range(quantidade)]


# --------------------------------------------------------------------------------------
# Diebold-Mariano com HLN
# --------------------------------------------------------------------------------------


def test_dm_hln_h1_calculado_a_mao() -> None:
    """d = 1..6, h = 1.

    dbar = 3,5; desvios = -2,5 -1,5 -0,5 0,5 1,5 2,5; gamma_0 = 17,5/6; V = gamma_0/6 = 17,5/36;
    DM = 3,5 / sqrt(17,5/36); fator HLN = sqrt((6+1-2+0)/6) = sqrt(5/6)
    => DM_HLN = 3,5 * 6 / sqrt(17,5) * sqrt(5/6) = sqrt(21).
    """
    resultado = diebold_mariano_hln(np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]), horizonte=1)
    assert resultado.n == 6
    assert resultado.media_das_diferencas == pytest.approx(3.5, abs=1e-12)
    assert resultado.variancia == pytest.approx(17.5 / 36.0, abs=1e-12)
    assert resultado.dm == pytest.approx(3.5 / np.sqrt(17.5 / 36.0), abs=1e-12)
    assert resultado.dm_hln == pytest.approx(np.sqrt(21.0), abs=1e-12)
    assert resultado.variancia_fallback is False
    assert resultado.definido is True
    # t de Student com 5 graus de liberdade: 4,032 (p bilateral 0,01) < sqrt(21) = 4,583 < 4,773 (p bilateral 0,005)
    assert 0.0025 < resultado.p_bilateral < 0.01
    assert resultado.p_bilateral == pytest.approx(2.0 * stats.t.sf(np.sqrt(21.0), df=5), abs=1e-12)


def test_dm_hln_h2_usa_a_autocovariancia_de_lag_1_calculado_a_mao() -> None:
    """d = [1, 3, 2, 4], h = 2.

    dbar = 2,5; desvios = -1,5 0,5 -0,5 1,5; gamma_0 = 5/4 = 1,25;
    gamma_1 = (0,5*-1,5 + -0,5*0,5 + 1,5*-0,5)/4 = -1,75/4 = -0,4375;
    V = (1,25 + 2*-0,4375)/4 = 0,09375; DM = 2,5/sqrt(0,09375);
    fator HLN = sqrt((4+1-4+2/4)/4) = sqrt(0,375) = 2*sqrt(0,09375) => DM_HLN = 5 (exato).
    """
    resultado = diebold_mariano_hln(np.array([1.0, 3.0, 2.0, 4.0]), horizonte=2)
    autocovariancias = calcular_autocovariancias(np.array([1.0, 3.0, 2.0, 4.0]), 2)
    assert autocovariancias[0] == pytest.approx(1.25, abs=1e-12)
    assert autocovariancias[1] == pytest.approx(-0.4375, abs=1e-12)
    assert resultado.variancia == pytest.approx(0.09375, abs=1e-12)
    assert resultado.dm == pytest.approx(2.5 / np.sqrt(0.09375), abs=1e-12)
    assert resultado.dm_hln == pytest.approx(5.0, abs=1e-12)
    assert resultado.p_bilateral == pytest.approx(2.0 * stats.t.sf(5.0, df=3), abs=1e-12)
    assert resultado.variancia_fallback is False


def test_dm_hln_com_variancia_nao_positiva_usa_pesos_de_bartlett_calculado_a_mao() -> None:
    """d = [2, 0, 2, 0, 2, 0], h = 2.

    dbar = 1; desvios alternam +1 -1; gamma_0 = 1; gamma_1 = -5/6;
    V sem pesos = (1 + 2*(-5/6))/6 = -1/9 < 0  => fallback;
    V com Bartlett (peso 1 - 1/2) = (1 + 2*0,5*(-5/6))/6 = 1/36; DM = 1/sqrt(1/36) = 6;
    fator HLN = sqrt((6+1-4+2/6)/6) = sqrt(5/9) => DM_HLN = 6*sqrt(5/9) = sqrt(20).
    """
    resultado = diebold_mariano_hln(np.array([2.0, 0.0, 2.0, 0.0, 2.0, 0.0]), horizonte=2)
    assert resultado.variancia_fallback is True
    assert resultado.definido is True
    assert resultado.variancia == pytest.approx(1.0 / 36.0, abs=1e-12)
    assert resultado.dm == pytest.approx(6.0, abs=1e-12)
    assert resultado.dm_hln == pytest.approx(np.sqrt(20.0), abs=1e-12)


def test_dm_hln_indefinido_quando_a_variancia_continua_nao_positiva() -> None:
    """d constante: gamma_k = 0 para todo k; DM indefinido (NaN), p = 1, marcado como fallback."""
    resultado = diebold_mariano_hln(np.array([1.0, 1.0, 1.0, 1.0]), horizonte=1)
    assert resultado.definido is False
    assert resultado.variancia_fallback is True
    assert np.isnan(resultado.dm)
    assert np.isnan(resultado.dm_hln)
    assert resultado.p_bilateral == 1.0


def test_dm_hln_sinal_positivo_quando_a_perda_de_b_e_maior() -> None:
    """d = |e_B| - |e_A| positivo => estatistica positiva (A melhor); invertendo o sinal, inverte a estatistica."""
    diferencas = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    a_melhor = diebold_mariano_hln(diferencas, horizonte=1)
    a_pior = diebold_mariano_hln(-diferencas, horizonte=1)
    assert a_melhor.dm_hln > 0.0
    assert a_pior.dm_hln == pytest.approx(-a_melhor.dm_hln, abs=1e-12)
    assert a_pior.p_bilateral == pytest.approx(a_melhor.p_bilateral, abs=1e-12)


def test_dm_hln_h1_sob_h0_com_d_normal_iid_tem_p_uniforme() -> None:
    """Com d iid normal e h = 1, DM_HLN e exatamente t(n-1): o p tem de ser uniforme (KS) e o tamanho ~5%."""
    gerador = np.random.default_rng(20261012)
    quantidade_de_simulacoes = 3000
    p_valores = np.zeros(quantidade_de_simulacoes)
    for simulacao in range(quantidade_de_simulacoes):
        diferencas = gerador.normal(loc=0.0, scale=1.0, size=100)
        p_valores[simulacao] = diebold_mariano_hln(diferencas, horizonte=1).p_bilateral
    teste_ks = stats.kstest(p_valores, "uniform")
    assert teste_ks.pvalue > 0.01
    taxa_de_rejeicao = float(np.mean(p_valores < 0.05))
    assert 0.035 < taxa_de_rejeicao < 0.065
    assert abs(float(p_valores.mean()) - 0.5) < 0.03


def test_dm_hln_h4_sob_h0_mantem_o_tamanho_proximo_de_5_por_cento() -> None:
    """Com d iid e h = 4 (lags 1 a 3 estimam zeros), a taxa de rejeicao a 5% fica perto do nominal."""
    gerador = np.random.default_rng(777)
    quantidade_de_simulacoes = 3000
    rejeicoes = 0
    for _ in range(quantidade_de_simulacoes):
        diferencas = gerador.normal(loc=0.0, scale=1.0, size=102)
        if diebold_mariano_hln(diferencas, horizonte=4).p_bilateral < 0.05:
            rejeicoes += 1
    taxa_de_rejeicao = rejeicoes / quantidade_de_simulacoes
    assert 0.03 < taxa_de_rejeicao < 0.08


def test_dm_hln_valida_entradas() -> None:
    with pytest.raises(ValueError):
        diebold_mariano_hln(np.array([1.0, 2.0, 3.0]), horizonte=0)
    with pytest.raises(ValueError):
        diebold_mariano_hln(np.array([1.0, np.nan, 3.0]), horizonte=1)
    with pytest.raises(ValueError):
        diebold_mariano_hln(np.array([1.0, np.inf, 3.0]), horizonte=1)
    with pytest.raises(ValueError):
        diebold_mariano_hln(np.array([1.0]), horizonte=1)
    with pytest.raises(ValueError):
        diebold_mariano_hln(np.array([1.0, 2.0, 3.0]), horizonte=4)


# --------------------------------------------------------------------------------------
# Holm
# --------------------------------------------------------------------------------------


def test_holm_exemplo_de_livro_com_monotonia() -> None:
    """p = [0,01; 0,04; 0,03; 0,005], m = 4.

    Ordenados: 0,005*4 = 0,02; 0,01*3 = 0,03; 0,03*2 = 0,06; 0,04*1 = 0,04 -> monotonia: 0,06.
    Na ordem original: [0,03; 0,06; 0,06; 0,02].
    """
    ajustados = corrigir_por_holm(np.array([0.01, 0.04, 0.03, 0.005]))
    np.testing.assert_allclose(ajustados, [0.03, 0.06, 0.06, 0.02], rtol=0.0, atol=1e-12)


def test_holm_trunca_em_1_e_mantem_a_ordem_original() -> None:
    ajustados = corrigir_por_holm(np.array([0.7, 0.6]))
    np.testing.assert_allclose(ajustados, [1.0, 1.0], atol=1e-12)


def test_holm_um_unico_teste_nao_muda() -> None:
    np.testing.assert_allclose(corrigir_por_holm(np.array([0.03])), [0.03], atol=1e-12)


def test_holm_vazio_e_valores_invalidos() -> None:
    assert len(corrigir_por_holm(np.array([]))) == 0
    with pytest.raises(ValueError):
        corrigir_por_holm(np.array([0.5, 1.5]))
    with pytest.raises(ValueError):
        corrigir_por_holm(np.array([0.5, np.nan]))


def test_holm_nunca_e_menor_que_o_p_bruto_e_e_monotono_nos_p_ordenados() -> None:
    gerador = np.random.default_rng(5)
    p_brutos = gerador.uniform(0.0, 0.2, size=16)
    ajustados = corrigir_por_holm(p_brutos)
    assert (ajustados >= p_brutos - 1e-15).all()
    ordem = np.argsort(p_brutos)
    assert (np.diff(ajustados[ordem]) >= -1e-15).all()


# --------------------------------------------------------------------------------------
# Bootstrap de blocos moveis
# --------------------------------------------------------------------------------------


def test_indices_do_bootstrap_sao_blocos_consecutivos_de_8_e_truncados_em_n() -> None:
    quantidade_de_pares = 30
    indices = sortear_indices_de_blocos_moveis(quantidade_de_pares, 8, 50, np.random.default_rng(42))
    assert indices.shape == (50, quantidade_de_pares)
    assert indices.min() >= 0
    assert indices.max() <= quantidade_de_pares - 1
    for linha in indices:
        # n = 30 -> 4 blocos (8+8+8+6 truncado)
        for inicio_do_bloco in (0, 8, 16, 24):
            fim_do_bloco = min(inicio_do_bloco + 8, quantidade_de_pares)
            bloco = linha[inicio_do_bloco:fim_do_bloco]
            assert (np.diff(bloco) == 1).all()
            # o bloco INTEIRO (8) cabe na serie: o inicio vai de 0 a n-8
            assert bloco[0] <= quantidade_de_pares - 8


def test_inicios_dos_blocos_cobrem_de_0_a_n_menos_8_incluindo_os_extremos() -> None:
    indices = sortear_indices_de_blocos_moveis(20, 8, 2000, np.random.default_rng(3))
    inicios = indices[:, 0::8][:, :2].ravel()
    assert inicios.min() == 0
    assert inicios.max() == 12


def test_bootstrap_e_reprodutivel_pela_semente() -> None:
    erros_b = np.array([4.0, 5.0, 3.0, 6.0, 4.0, 7.0, 5.0, 4.0, 6.0, 3.0, 5.0, 8.0, 4.0, 5.0, 6.0, 4.0, 3.0, 5.0, 7.0, 4.0])
    erros_a = np.array([3.0, 4.0, 3.5, 4.0, 3.0, 5.0, 4.5, 3.0, 4.0, 2.5, 4.0, 5.0, 3.0, 4.0, 4.5, 3.0, 2.5, 4.0, 5.5, 3.0])
    primeira = intervalo_de_confianca_do_ganho(erros_a, erros_b)
    segunda = intervalo_de_confianca_do_ganho(erros_a, erros_b)
    assert primeira == segunda
    outra_semente = intervalo_de_confianca_do_ganho(erros_a, erros_b, semente=43)
    assert outra_semente != primeira


def test_bootstrap_valor_fixado_para_semente_42() -> None:
    """Regressao: o IC desta serie com semente 42, blocos de 8 e 2.000 reamostragens nao pode mudar."""
    erros_b = np.array([4.0, 5.0, 3.0, 6.0, 4.0, 7.0, 5.0, 4.0, 6.0, 3.0, 5.0, 8.0, 4.0, 5.0, 6.0, 4.0, 3.0, 5.0, 7.0, 4.0])
    erros_a = np.array([3.0, 4.0, 3.5, 4.0, 3.0, 5.0, 4.5, 3.0, 4.0, 2.5, 4.0, 5.0, 3.0, 4.0, 4.5, 3.0, 2.5, 4.0, 5.5, 3.0])
    ic_inferior, ic_superior = intervalo_de_confianca_do_ganho(erros_a, erros_b)
    assert ic_inferior == pytest.approx(IC_FIXADO_INFERIOR, abs=1e-9)
    assert ic_superior == pytest.approx(IC_FIXADO_SUPERIOR, abs=1e-9)


# Valores obtidos com `np.random.default_rng(42)`, `integers(0, n-8+1, size=(2000, 3))` e percentis 2,5 e 97,5
# (conferidos por reimplementacao com laco simples no proprio arquivo, em `test_bootstrap_confere_com_laco_simples`).
IC_FIXADO_INFERIOR = 22.163456321215406
IC_FIXADO_SUPERIOR = 26.699029126213603


def test_bootstrap_confere_com_laco_simples() -> None:
    """Reimplementacao ingenua (laco por reamostra, concatenacao e truncamento) gera o mesmo IC."""
    erros_b = np.array([4.0, 5.0, 3.0, 6.0, 4.0, 7.0, 5.0, 4.0, 6.0, 3.0, 5.0, 8.0, 4.0, 5.0, 6.0, 4.0, 3.0, 5.0, 7.0, 4.0])
    erros_a = np.array([3.0, 4.0, 3.5, 4.0, 3.0, 5.0, 4.5, 3.0, 4.0, 2.5, 4.0, 5.0, 3.0, 4.0, 4.5, 3.0, 2.5, 4.0, 5.5, 3.0])
    quantidade_de_pares = len(erros_a)
    gerador = np.random.default_rng(42)
    quantidade_de_blocos = 3
    inicios = gerador.integers(0, quantidade_de_pares - 8 + 1, size=(2000, quantidade_de_blocos))
    ganhos: list[float] = []
    for reamostra in range(2000):
        posicoes: list[int] = []
        for inicio in inicios[reamostra]:
            for deslocamento in range(8):
                posicoes.append(int(inicio) + deslocamento)
        posicoes = posicoes[:quantidade_de_pares]
        mae_a = float(np.mean(erros_a[posicoes]))
        mae_b = float(np.mean(erros_b[posicoes]))
        ganhos.append(100.0 * (mae_b - mae_a) / mae_b)
    esperado = (float(np.percentile(ganhos, 2.5)), float(np.percentile(ganhos, 97.5)))
    obtido = intervalo_de_confianca_do_ganho(erros_a, erros_b)
    assert obtido[0] == pytest.approx(esperado[0], abs=1e-12)
    assert obtido[1] == pytest.approx(esperado[1], abs=1e-12)


def test_bootstrap_com_ganho_constante_tem_ic_degenerado() -> None:
    """Se |e_A| = 0,5 |e_B| em toda semana, o ganho e 50% em qualquer reamostra: IC = (50, 50)."""
    erros_b = np.array([4.0, 5.0, 3.0, 6.0, 4.0, 7.0, 5.0, 4.0, 6.0, 3.0, 5.0, 8.0])
    ic_inferior, ic_superior = intervalo_de_confianca_do_ganho(0.5 * erros_b, erros_b)
    assert ic_inferior == pytest.approx(50.0, abs=1e-9)
    assert ic_superior == pytest.approx(50.0, abs=1e-9)


def test_bootstrap_valida_entradas() -> None:
    with pytest.raises(ValueError):
        intervalo_de_confianca_do_ganho(np.ones(5), np.ones(5))
    with pytest.raises(ValueError):
        intervalo_de_confianca_do_ganho(np.ones(10), np.ones(11))


# --------------------------------------------------------------------------------------
# Ganho e comparacao pareada
# --------------------------------------------------------------------------------------


def test_ganho_percentual_a_mao() -> None:
    """MAE_B = 10, MAE_A = 8 -> (10-8)/10*100 = 20; A pior: MAE_A = 12 -> -20."""
    assert ganho_percentual(10.0, 8.0) == pytest.approx(20.0, abs=1e-12)
    assert ganho_percentual(10.0, 12.0) == pytest.approx(-20.0, abs=1e-12)
    with pytest.raises(ValueError):
        ganho_percentual(0.0, 1.0)


def test_pareamento_usa_so_as_semanas_em_comum_ordenadas_e_ignora_a_ordem_das_linhas() -> None:
    datas_a = semanas(12)
    datas_b = semanas(12, UM_DOMINGO + 2 * UMA_SEMANA)
    previsoes_a = montar_previsoes(datas_a, [float(i) for i in range(12)], [float(i) + 1 for i in range(12)])
    reais_b = [float(i) for i in range(2, 14)]
    previsoes_b = montar_previsoes(datas_b, reais_b, [valor + 2.0 for valor in reais_b])
    embaralhado = previsoes_a.sample(frac=1.0, random_state=1)
    pareado = parear_por_data_alvo(embaralhado, previsoes_b)
    assert len(pareado) == 10
    assert pareado["data_alvo"].is_monotonic_increasing
    assert pareado["data_alvo"].iloc[0] == UM_DOMINGO + 2 * UMA_SEMANA
    assert pareado["data_alvo"].iloc[-1] == UM_DOMINGO + 11 * UMA_SEMANA


def test_pareamento_rejeita_real_diferente_e_data_repetida_e_sem_semana_em_comum() -> None:
    datas = semanas(10)
    base = montar_previsoes(datas, [1.0] * 10, [2.0] * 10)
    real_diferente = montar_previsoes(datas, [1.0] * 9 + [9.0], [2.0] * 10)
    with pytest.raises(ValueError):
        parear_por_data_alvo(base, real_diferente)
    repetida = pd.concat([base, base.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        parear_por_data_alvo(repetida, base)
    sem_comum = montar_previsoes(semanas(10, UM_DOMINGO + 30 * UMA_SEMANA), [1.0] * 10, [2.0] * 10)
    with pytest.raises(ValueError):
        parear_por_data_alvo(base, sem_comum)
    with pytest.raises(KeyError):
        parear_por_data_alvo(base.drop(columns=["previsto"]), base)


def test_comparar_pareado_a_mao_e_com_buraco_de_calendario() -> None:
    """Real = 10 em 12 semanas; A erra 1 em toda semana e B erra 2; falta uma semana em B (buraco).

    n = 11; MAE_A = 1; MAE_B = 2; delta = +1 (A melhor); ganho = 50%; d_t = 1 constante => DM indefinido, p = 1.
    """
    datas = semanas(12)
    previsoes_a = montar_previsoes(datas, [10.0] * 12, [11.0] * 12)
    previsoes_b = montar_previsoes(datas, [10.0] * 12, [8.0] * 12).drop(index=5)
    comparacao = comparar_pareado(previsoes_a, previsoes_b, horizonte=1)
    assert comparacao.n == 11
    assert comparacao.mae_a == pytest.approx(1.0, abs=1e-12)
    assert comparacao.mae_b == pytest.approx(2.0, abs=1e-12)
    assert comparacao.delta == pytest.approx(1.0, abs=1e-12)
    assert comparacao.ganho_pct == pytest.approx(50.0, abs=1e-12)
    assert comparacao.ic_inf == pytest.approx(50.0, abs=1e-9)
    assert comparacao.ic_sup == pytest.approx(50.0, abs=1e-9)
    assert np.isnan(comparacao.dm_hln)
    assert comparacao.p_bruto == 1.0
    assert comparacao.variancia_fallback is True


def test_comparar_pareado_delta_positivo_quando_a_erra_menos_e_negativo_quando_erra_mais() -> None:
    gerador = np.random.default_rng(11)
    datas = semanas(60)
    reais = gerador.uniform(50.0, 100.0, size=60)
    ruido = gerador.normal(0.0, 1.0, size=60)
    previsoes_bom = montar_previsoes(datas, list(reais), list(reais + 2.0 * ruido))
    previsoes_ruim = montar_previsoes(datas, list(reais), list(reais + 10.0 * ruido))
    a_melhor = comparar_pareado(previsoes_bom, previsoes_ruim, horizonte=2)
    a_pior = comparar_pareado(previsoes_ruim, previsoes_bom, horizonte=2)
    assert a_melhor.delta > 0.0
    assert a_melhor.ganho_pct > 0.0
    assert a_melhor.dm_hln > 0.0
    assert a_pior.delta < 0.0
    assert a_pior.dm_hln < 0.0
    assert a_melhor.p_bruto < 0.01
    assert a_melhor.delta == pytest.approx(-a_pior.delta, abs=1e-12)
    assert a_melhor.ic_inf < a_melhor.ganho_pct < a_melhor.ic_sup
