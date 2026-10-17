"""Testes de `aedes/familias.py`: definicao das 52 comparacoes, piso de ruido (Emenda 1), veredito e Holm por familia.

Previsoes fabricadas em memoria; nenhum arquivo do projeto e lido ou escrito.
"""

import zlib

import numpy as np
import pandas as pd
import pytest

from aedes.familias import (
    COLUNAS_DA_TABELA_DE_FAMILIAS,
    HORIZONTES_TESTADOS,
    NOME_DA_REGUA_SAZONAL,
    NOME_DO_COMPOSTO,
    VEREDITO_A_MELHOR,
    VEREDITO_A_PIOR,
    VEREDITO_SEM_EVIDENCIA,
    DefinicaoDoTeste,
    calcular_limiar_do_piso,
    decidir_veredito,
    executar_familias,
    montar_definicoes_das_familias,
    nome_do_candidato,
)

PRIMEIRO_DOMINGO = pd.Timestamp("2024-01-07")
UMA_SEMANA = pd.Timedelta(weeks=1)


def montar_piso() -> pd.DataFrame:
    """Piso de ruido de mentira: folha 5 = 1,0 / 2,0 / 3,0 / 4,0 e folha 20 = 10 / 20 / 30 / 40 em h = 1, 4, 8, 12."""
    linhas = []
    for indice, horizonte in enumerate(HORIZONTES_TESTADOS):
        linhas.append({"folha": 5, "h": horizonte, "piso_de_ruido": 1.0 + indice})
        linhas.append({"folha": 20, "h": horizonte, "piso_de_ruido": 10.0 * (1.0 + indice)})
    return pd.DataFrame(linhas)


def test_as_definicoes_tem_52_testes_12_12_12_16() -> None:
    definicoes = montar_definicoes_das_familias()
    assert len(definicoes) == 52
    contagem = pd.Series([definicao.familia for definicao in definicoes]).value_counts().to_dict()
    assert contagem == {"F1": 12, "F2": 12, "F3": 12, "F4": 16}
    assert len(set(definicoes)) == 52


def test_f1_f2_f3_f4_comparam_exatamente_o_que_a_preregistro_diz() -> None:
    definicoes = montar_definicoes_das_familias()
    por_familia: dict[str, set[tuple[str, str]]] = {"F1": set(), "F2": set(), "F3": set(), "F4": set()}
    for definicao in definicoes:
        por_familia[definicao.familia].add((definicao.nome_a, definicao.nome_b))

    assert por_familia["F1"] == {
        ("completo@f5", "sem_casos@f5"),
        ("completo@f5", "sem_clima@f5"),
        ("completo@f5", "sem_vetor@f5"),
    }
    assert por_familia["F3"] == {
        ("completo@f20", "sem_casos@f20"),
        ("completo@f20", "sem_clima@f20"),
        ("completo@f20", "sem_vetor@f20"),
    }
    assert por_familia["F2"] == {
        ("so_casos@f5", "so_calendario@f5"),
        ("so_clima@f5", "so_calendario@f5"),
        ("so_vetor@f5", "so_calendario@f5"),
    }
    assert por_familia["F4"] == {
        ("completo@f5", "regua_sazonal"),
        ("completo@f20", "regua_sazonal"),
        ("composto_N13", "regua_sazonal"),
        ("composto_N13", "completo@f5"),
    }
    for definicao in definicoes:
        assert definicao.horizonte in (1, 4, 8, 12)


def test_folhas_do_piso_por_familia() -> None:
    """F1, F2 e f5 x regua: piso da folha 5; F3 e f20 x regua: folha 20; composto: as duas."""
    for definicao in montar_definicoes_das_familias():
        if definicao.familia in ("F1", "F2"):
            assert definicao.folhas_do_piso == (5,)
        elif definicao.familia == "F3":
            assert definicao.folhas_do_piso == (20,)
        elif definicao.nome_a == "completo@f5":
            assert definicao.folhas_do_piso == (5,)
        elif definicao.nome_a == "completo@f20":
            assert definicao.folhas_do_piso == (20,)
        else:
            assert definicao.nome_a == NOME_DO_COMPOSTO
            assert definicao.folhas_do_piso == (5, 20)


def test_limiar_do_piso_e_2x_o_piso_da_folha_ou_2x_o_maior_quando_envolve_o_composto() -> None:
    piso = montar_piso()
    assert calcular_limiar_do_piso(piso, (5,), 4) == pytest.approx(2.0 * 2.0)
    assert calcular_limiar_do_piso(piso, (20,), 4) == pytest.approx(2.0 * 20.0)
    assert calcular_limiar_do_piso(piso, (5, 20), 8) == pytest.approx(2.0 * 30.0)
    assert calcular_limiar_do_piso(piso, (), 8) == 0.0
    with pytest.raises(ValueError):
        calcular_limiar_do_piso(piso, (5,), 3)
    with pytest.raises(KeyError):
        calcular_limiar_do_piso(piso.drop(columns=["piso_de_ruido"]), (5,), 1)


def test_veredito_exige_holm_menor_que_5_por_cento_e_delta_maior_que_o_limiar_estritos() -> None:
    assert decidir_veredito(0.049, 5.0, 4.0) == VEREDITO_A_MELHOR
    assert decidir_veredito(0.049, -5.0, 4.0) == VEREDITO_A_PIOR
    assert decidir_veredito(0.05, 5.0, 4.0) == VEREDITO_SEM_EVIDENCIA  # p exatamente 0,05 nao passa
    assert decidir_veredito(0.049, 4.0, 4.0) == VEREDITO_SEM_EVIDENCIA  # |delta| exatamente no limiar nao passa
    assert decidir_veredito(0.049, -4.0, 4.0) == VEREDITO_SEM_EVIDENCIA
    assert decidir_veredito(0.049, 4.0001, 4.0) == VEREDITO_A_MELHOR
    assert decidir_veredito(0.2, 100.0, 4.0) == VEREDITO_SEM_EVIDENCIA
    assert decidir_veredito(0.0001, 0.0, 0.0) == VEREDITO_SEM_EVIDENCIA


def montar_previsoes_sinteticas(escala_do_erro_por_nome: dict[str, float]) -> dict[tuple[str, int], pd.DataFrame]:
    """Um DataFrame por (nome, h): mesmo `real`, erro = escala x ruido comum (+ vies), 100 semanas."""
    gerador = np.random.default_rng(31)
    quantidade = 100
    datas = [PRIMEIRO_DOMINGO + i * UMA_SEMANA for i in range(quantidade)]
    reais = gerador.uniform(50.0, 400.0, size=quantidade)
    previsoes: dict[tuple[str, int], pd.DataFrame] = {}
    for nome, escala in escala_do_erro_por_nome.items():
        for horizonte in HORIZONTES_TESTADOS:
            semente_do_candidato = zlib.crc32(f"{nome}|{horizonte}".encode("utf-8"))
            ruido = np.random.default_rng(semente_do_candidato).normal(0.0, 1.0, size=quantidade)
            previsoes[(nome, horizonte)] = pd.DataFrame(
                {"data_alvo": datas, "real": reais, "previsto": reais + escala * ruido}
            )
    return previsoes


def test_executar_familias_com_dados_sinteticos_aplica_holm_por_familia_e_veredito_pela_regra() -> None:
    escalas = {
        "completo@f5": 5.0,
        "sem_casos@f5": 60.0,  # muito pior
        "sem_clima@f5": 5.0,  # igual
        "sem_vetor@f5": 5.0,
        "so_casos@f5": 20.0,
        "so_clima@f5": 80.0,
        "so_vetor@f5": 80.0,
        "so_calendario@f5": 80.0,
        "completo@f20": 5.0,
        "sem_casos@f20": 60.0,
        "sem_clima@f20": 5.0,
        "sem_vetor@f20": 5.0,
        NOME_DO_COMPOSTO: 5.0,
        NOME_DA_REGUA_SAZONAL: 80.0,
    }
    previsoes = montar_previsoes_sinteticas(escalas)
    # `sem_clima` = copia exata do completo (empate total) para exercitar o DM indefinido
    for horizonte in HORIZONTES_TESTADOS:
        previsoes[("sem_clima@f5", horizonte)] = previsoes[("completo@f5", horizonte)].copy()
        previsoes[("sem_clima@f20", horizonte)] = previsoes[("completo@f20", horizonte)].copy()

    definicoes = montar_definicoes_das_familias()
    tabela = executar_familias(definicoes, previsoes, montar_piso())

    assert list(tabela.columns) == list(COLUNAS_DA_TABELA_DE_FAMILIAS)
    assert len(tabela) == 52
    assert (tabela["n"] == 100).all()
    assert (tabela["p_holm"] >= tabela["p_bruto"] - 1e-15).all()

    sem_casos_f1 = tabela.loc[(tabela["familia"] == "F1") & (tabela["B"] == "sem_casos@f5")]
    assert (sem_casos_f1["veredito"] == VEREDITO_A_MELHOR).all()
    assert (sem_casos_f1["delta"] > 0.0).all()

    sem_clima_f1 = tabela.loc[(tabela["familia"] == "F1") & (tabela["B"] == "sem_clima@f5")]
    assert (sem_clima_f1["veredito"] == VEREDITO_SEM_EVIDENCIA).all()
    assert (sem_clima_f1["p_bruto"] == 1.0).all()
    assert sem_clima_f1["variancia_fallback"].all()

    f1 = tabela.loc[tabela["familia"] == "F1"]
    # Holm conferido por reaplicacao independente (laco simples) sobre os 12 p brutos da F1
    ordem = np.argsort(f1["p_bruto"].to_numpy(), kind="stable")
    quantidade = len(f1)
    maximo = 0.0
    esperado = np.zeros(quantidade)
    for posicao, indice in enumerate(ordem):
        candidato = min(1.0, (quantidade - posicao) * f1["p_bruto"].to_numpy()[indice])
        maximo = max(maximo, candidato)
        esperado[indice] = maximo
    np.testing.assert_allclose(f1["p_holm"].to_numpy(), esperado, atol=1e-12)

    # a F4 tem 16 testes: o multiplicador maximo do Holm e 16 (o menor p bruto), nao 12
    f4 = tabela.loc[tabela["familia"] == "F4"]
    menor_p_bruto_f4 = f4["p_bruto"].min()
    menor_p_holm_f4 = f4["p_holm"].min()
    assert menor_p_holm_f4 == pytest.approx(min(1.0, 16.0 * menor_p_bruto_f4), abs=1e-12)


def test_limiar_do_piso_trava_o_veredito_quando_o_delta_e_pequeno() -> None:
    """Delta significativo, mas menor que 2x o piso: sem evidencia."""
    escalas = {nome: 5.0 for nome in (
        "completo@f5", "sem_casos@f5", "sem_clima@f5", "sem_vetor@f5", "so_casos@f5", "so_clima@f5", "so_vetor@f5",
        "so_calendario@f5", "completo@f20", "sem_casos@f20", "sem_clima@f20", "sem_vetor@f20", NOME_DO_COMPOSTO,
        NOME_DA_REGUA_SAZONAL,
    )}
    escalas["sem_casos@f5"] = 9.0
    previsoes = montar_previsoes_sinteticas(escalas)
    definicoes = [
        DefinicaoDoTeste("F1", 1, "completo@f5", "sem_casos@f5", (5,)),
    ]
    piso_baixo = pd.DataFrame([{"folha": 5, "h": 1, "piso_de_ruido": 0.01}, {"folha": 20, "h": 1, "piso_de_ruido": 0.01}])
    piso_alto = pd.DataFrame([{"folha": 5, "h": 1, "piso_de_ruido": 1000.0}, {"folha": 20, "h": 1, "piso_de_ruido": 1000.0}])
    com_piso_baixo = executar_familias(definicoes, previsoes, piso_baixo)
    com_piso_alto = executar_familias(definicoes, previsoes, piso_alto)
    assert com_piso_baixo["veredito"].iloc[0] == VEREDITO_A_MELHOR
    assert com_piso_alto["veredito"].iloc[0] == VEREDITO_SEM_EVIDENCIA
    assert com_piso_alto["limiar_piso"].iloc[0] == 2000.0
    assert nome_do_candidato("completo", 5) == "completo@f5"
