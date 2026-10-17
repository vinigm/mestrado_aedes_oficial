"""Testes de `aedes/composto.py` (E3): escolha da folha pelo erro recente, sem olhar o futuro.

Casos a mao, empate, buracos de calendario, historico curto, um teste que FALHA se a regra usar
`data_alvo > t`, e comparacao com uma implementacao ingenua (laco com filtro explicito por data).
Nenhum arquivo do projeto e lido ou escrito.
"""

import numpy as np
import pandas as pd
import pytest

from aedes.composto import (
    COLUNAS_DO_COMPOSTO,
    escolher_folha_pelo_erro_recente,
    montar_composto,
)

PRIMEIRO_DOMINGO = pd.Timestamp("2022-01-02")
UMA_SEMANA = pd.Timedelta(weeks=1)


def datas_semanais(quantidade: int) -> list[pd.Timestamp]:
    return [PRIMEIRO_DOMINGO + i * UMA_SEMANA for i in range(quantidade)]


def montar_folha(datas: list[pd.Timestamp], reais: list[float], previstos: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"data_alvo": datas, "real": reais, "previsto": previstos})


def composto_ingenuo(
    folha_5: pd.DataFrame,
    folha_20: pd.DataFrame,
    horizonte: int,
    semanas_recentes: int,
) -> pd.DataFrame:
    """Implementacao de conferencia: laco com filtro explicito `data_alvo <= t`, sem searchsorted."""
    pares = folha_5.merge(folha_20, on="data_alvo", suffixes=("_5", "_20")).sort_values("data_alvo")
    linhas = []
    for _, linha in pares.iterrows():
        origem = linha["data_alvo"] - pd.Timedelta(weeks=horizonte)
        conhecidos = pares.loc[pares["data_alvo"] <= origem]
        if len(conhecidos) < semanas_recentes:
            continue
        ultimos = conhecidos.tail(semanas_recentes)
        mae_5 = float(np.mean(np.abs(ultimos["real_5"] - ultimos["previsto_5"])))
        mae_20 = float(np.mean(np.abs(ultimos["real_5"] - ultimos["previsto_20"])))
        if mae_20 < mae_5:
            folha = 20
            previsto = linha["previsto_20"]
        else:
            folha = 5
            previsto = linha["previsto_5"]
        linhas.append((origem, linha["data_alvo"], linha["real_5"], previsto, folha))
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_COMPOSTO))


def test_escolha_pelo_menor_mae_e_empate_exato_vai_para_a_folha_5() -> None:
    assert escolher_folha_pelo_erro_recente(np.array([3.0, 3.0]), np.array([2.0, 3.0])) == 20  # MAE 3 x 2,5
    assert escolher_folha_pelo_erro_recente(np.array([2.0, 2.0]), np.array([3.0, 3.0])) == 5
    assert escolher_folha_pelo_erro_recente(np.array([2.0, 4.0]), np.array([3.0, 3.0])) == 5  # empate exato: 3 x 3
    with pytest.raises(ValueError):
        escolher_folha_pelo_erro_recente(np.array([]), np.array([]))
    with pytest.raises(ValueError):
        escolher_folha_pelo_erro_recente(np.array([1.0]), np.array([1.0, 2.0]))


def test_composto_h1_n2_calculado_a_mao() -> None:
    """h = 1, N = 2, 6 semanas (w0..w5), real = 100 sempre.

    Erros da folha 5:  [10, 10, 1, 1, 10, 10]   Erros da folha 20: [1, 1, 10, 10, 1, 1].
    Origem da semana i e w(i-1); pares conhecidos = w0..w(i-1); janela = os 2 ultimos.
      i=0, i=1: menos de 2 pares conhecidos -> sem previsao (i=1: so w0 conhecido).
      i=2: pares w0,w1:  MAE5 = 10; MAE20 = 1  -> folha 20 -> previsto20 de w2.
      i=3: pares w1,w2:  MAE5 = 5,5; MAE20 = 5,5 -> empate -> folha 5.
      i=4: pares w2,w3:  MAE5 = 1; MAE20 = 10 -> folha 5.
      i=5: pares w3,w4:  MAE5 = 5,5; MAE20 = 5,5 -> empate -> folha 5.
    """
    datas = datas_semanais(6)
    reais = [100.0] * 6
    erros_5 = [10.0, 10.0, 1.0, 1.0, 10.0, 10.0]
    erros_20 = [1.0, 1.0, 10.0, 10.0, 1.0, 1.0]
    previsto_5 = [100.0 + erro for erro in erros_5]
    previsto_20 = [100.0 - erro for erro in erros_20]
    composto = montar_composto(montar_folha(datas, reais, previsto_5), montar_folha(datas, reais, previsto_20), 1, 2)

    assert list(composto.columns) == list(COLUNAS_DO_COMPOSTO)
    assert list(composto["data_alvo"]) == datas[2:]
    assert list(composto["folha_escolhida"]) == [20, 5, 5, 5]
    assert list(composto["previsto"]) == [previsto_20[2], previsto_5[3], previsto_5[4], previsto_5[5]]
    assert list(composto["data_origem"]) == [datas[1], datas[2], datas[3], datas[4]]
    assert list(composto["real"]) == [100.0] * 4


def test_composto_h3_usa_so_pares_com_data_alvo_ate_a_origem() -> None:
    """h = 3, N = 2: a origem da semana i e w(i-3); pares conhecidos: w0..w(i-3).

    A semana w5 (origem w2): pares w0,w1,w2 -> janela w1,w2.
    Erros folha 5: [0, 9, 9, 0, 0, 0, 0]; folha 20: [0, 1, 1, 9, 9, 9, 9], real = 50.
    w5: janela w1,w2: MAE5 = 9 x MAE20 = 1 -> folha 20. (Se usasse w3,w4, que ainda nao eram conhecidos em w2,
    escolheria a folha 5.) w6 (origem w3): janela w2,w3: MAE5 = 4,5; MAE20 = 5 -> folha 5.
    """
    datas = datas_semanais(7)
    reais = [50.0] * 7
    erros_5 = [0.0, 9.0, 9.0, 0.0, 0.0, 0.0, 0.0]
    erros_20 = [0.0, 1.0, 1.0, 9.0, 9.0, 9.0, 9.0]
    folha_5 = montar_folha(datas, reais, [50.0 + erro for erro in erros_5])
    folha_20 = montar_folha(datas, reais, [50.0 - erro for erro in erros_20])
    composto = montar_composto(folha_5, folha_20, 3, 2)
    assert list(composto["data_alvo"]) == datas[4:]
    # w4 (origem w1): pares w0,w1: MAE5 = 4,5; MAE20 = 0,5 -> folha 20
    assert list(composto["folha_escolhida"]) == [20, 20, 5]


def test_composto_ignora_buracos_de_calendario_usando_so_pares_disponiveis() -> None:
    """A semana w2 so existe na folha 5 (buraco na folha 20): ela nao e par e nao entra na janela."""
    datas = datas_semanais(8)
    reais = [100.0] * 8
    folha_5 = montar_folha(datas, reais, [100.0 + 5.0] * 8)
    folha_20 = montar_folha(datas, reais, [100.0 + 4.0] * 8).drop(index=2)
    composto = montar_composto(folha_5, folha_20, 1, 3)
    # pares: w0,w1,w3,w4,w5,w6,w7; w2 nao e par. A 1a semana com >= 3 pares conhecidos em w(i-1) e w5
    # (conhecidos em w4: w0,w1,w3,w4); w4 so tem w0,w1,w3 (3 pares) e entra tambem.
    assert datas[2] not in list(composto["data_alvo"])
    assert datas[4] in list(composto["data_alvo"])
    assert datas[3] not in list(composto["data_alvo"])  # origem w2: so w0,w1 conhecidos -> 2 pares < 3
    assert set(composto["folha_escolhida"]) == {20}  # a folha 20 erra 4 contra 5 em todas as semanas


def test_composto_nao_produz_previsao_com_menos_de_n_pares_conhecidos() -> None:
    datas = datas_semanais(15)
    reais = [10.0] * 15
    folha_5 = montar_folha(datas, reais, [11.0] * 15)
    folha_20 = montar_folha(datas, reais, [12.0] * 15)
    composto = montar_composto(folha_5, folha_20, 2, 13)
    # origem da semana i = w(i-2); pares conhecidos = i-1 (w0..w(i-2)); precisa de 13 -> i >= 14
    assert list(composto["data_alvo"]) == [datas[14]]


def test_composto_nao_olha_o_futuro_mudar_a_semana_alvo_e_as_posteriores_nao_muda_a_escolha() -> None:
    """Se a regra usasse data_alvo > t (a propria semana-alvo ou depois), este teste FALHA.

    Para cada semana-alvo i, troca o `real` e as previsoes da propria semana i e de todas as posteriores
    por valores aleatorios (e adversariais: a folha 20 passa a acertar exatamente o novo real, a 5 erra muito).
    A folha escolhida em i nao pode mudar, porque a janela so contem semanas com data_alvo <= t < data_alvo_i.
    """
    gerador = np.random.default_rng(2026)
    quantidade = 40
    datas = datas_semanais(quantidade)
    reais = gerador.uniform(20.0, 200.0, size=quantidade)
    folha_5 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 15.0, quantidade)))
    folha_20 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 15.0, quantidade)))
    horizonte = 2
    semanas_recentes = 4
    original = montar_composto(folha_5, folha_20, horizonte, semanas_recentes)
    escolhas_originais = dict(zip(original["data_alvo"], original["folha_escolhida"]))

    for posicao in range(horizonte + semanas_recentes, quantidade):
        data_alvo_testada = datas[posicao]
        folha_5_alterada = folha_5.copy()
        folha_20_alterada = folha_20.copy()
        reais_novos = gerador.uniform(500.0, 900.0, size=quantidade - posicao)
        # `real` novo igual nas duas folhas; a folha 20 acerta exatamente, a 5 erra por 300
        folha_5_alterada.loc[posicao:, "real"] = reais_novos
        folha_20_alterada.loc[posicao:, "real"] = reais_novos
        folha_5_alterada.loc[posicao:, "previsto"] = reais_novos + 300.0
        folha_20_alterada.loc[posicao:, "previsto"] = reais_novos
        alterado = montar_composto(folha_5_alterada, folha_20_alterada, horizonte, semanas_recentes)
        escolhas_alteradas = dict(zip(alterado["data_alvo"], alterado["folha_escolhida"]))
        assert escolhas_alteradas[data_alvo_testada] == escolhas_originais[data_alvo_testada]


def test_composto_confere_com_implementacao_ingenua_em_dados_aleatorios_com_buracos() -> None:
    gerador = np.random.default_rng(99)
    quantidade = 70
    datas = datas_semanais(quantidade)
    reais = gerador.uniform(0.0, 300.0, size=quantidade)
    folha_5 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 30.0, quantidade)))
    folha_20 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 30.0, quantidade)))
    folha_5 = folha_5.drop(index=[7, 19, 33])
    folha_20 = folha_20.drop(index=[12, 33, 50])
    for horizonte in (1, 4, 8, 12):
        for semanas_recentes in (8, 13, 26):
            esperado = composto_ingenuo(folha_5, folha_20, horizonte, semanas_recentes)
            obtido = montar_composto(folha_5, folha_20, horizonte, semanas_recentes)
            pd.testing.assert_frame_equal(
                obtido.reset_index(drop=True),
                esperado.reset_index(drop=True),
                check_dtype=False,
                check_exact=False,
                rtol=1e-12,
                atol=1e-12,
            )


def test_composto_ordem_das_linhas_de_entrada_nao_importa() -> None:
    gerador = np.random.default_rng(4)
    datas = datas_semanais(30)
    reais = gerador.uniform(0.0, 300.0, size=30)
    folha_5 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 30.0, 30)))
    folha_20 = montar_folha(datas, list(reais), list(reais + gerador.normal(0.0, 30.0, 30)))
    normal = montar_composto(folha_5, folha_20, 2, 5)
    embaralhado = montar_composto(folha_5.sample(frac=1.0, random_state=1), folha_20.sample(frac=1.0, random_state=2), 2, 5)
    pd.testing.assert_frame_equal(normal.reset_index(drop=True), embaralhado.reset_index(drop=True))


def test_composto_valida_entradas() -> None:
    datas = datas_semanais(5)
    folha = montar_folha(datas, [1.0] * 5, [1.0] * 5)
    with pytest.raises(ValueError):
        montar_composto(folha, folha, 0, 2)
    with pytest.raises(ValueError):
        montar_composto(folha, folha, 1, 0)
    with pytest.raises(KeyError):
        montar_composto(folha.drop(columns=["previsto"]), folha, 1, 2)
    repetida = pd.concat([folha, folha.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError):
        montar_composto(repetida, folha, 1, 2)
    real_diferente = folha.copy()
    real_diferente.loc[0, "real"] = 99.0
    with pytest.raises(ValueError):
        montar_composto(folha, real_diferente, 1, 2)
