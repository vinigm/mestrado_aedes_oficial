"""Testes de `aedes.comparacoes`: travas, cobertura, regra do quantil, corte pela pergunta e piso de ruido.

Tabelas sinteticas com valores conferidos a mao. Sem nenhum teste estatistico: so MAE, R2, cobertura,
diferencas e regras de decisao.
"""

import numpy as np
import pandas as pd
import pytest

from aedes.comparacoes import (
    calcular_cobertura,
    calcular_deltas_e_piso_de_ruido,
    calcular_mae_na_janela,
    comparar_cortes,
    comparar_previsoes_com_gabarito,
    decidir_quantil,
)
from aedes.configuracao import CONFIGURACAO_AVALIACAO

PRIMEIRA_DATA_DA_JANELA = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
ULTIMA_DATA_DA_JANELA = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
UMA_SEMANA = pd.Timedelta(weeks=1)
CHAVE = ["h", "data_alvo"]


def montar_previsoes(
    reais: list[float],
    previstos: list[float],
    horizonte: int = 4,
    primeira_data: pd.Timestamp = pd.Timestamp("2024-01-07"),
) -> pd.DataFrame:
    """Previsoes de um horizonte em semanas consecutivas a partir de `primeira_data`."""
    datas = [primeira_data + posicao * UMA_SEMANA for posicao in range(len(reais))]
    return pd.DataFrame({"h": horizonte, "data_alvo": datas, "real": reais, "previsto": previstos})


# ---------------------------------------------------------------------------
# comparar_previsoes_com_gabarito (as travas)
# ---------------------------------------------------------------------------


def test_previsoes_identicas_passam_na_trava() -> None:
    """Mesmo conjunto de chaves, diferenca zero: passou."""
    novas = montar_previsoes([1.0, 2.0, 3.0], [1.5, 2.5, 3.5])
    resultado = comparar_previsoes_com_gabarito(novas, novas.copy(), CHAVE, 1e-9)
    assert resultado.passou
    assert resultado.linhas_em_comum == 3
    assert resultado.diferenca_maxima_do_previsto == 0.0
    assert resultado.linhas_so_nas_novas == 0
    assert resultado.linhas_so_no_gabarito == 0


def test_diferenca_abaixo_da_tolerancia_passa_e_acima_falha() -> None:
    """1e-12 passa; 2e-9 falha (limite estrito de 1e-9)."""
    gabarito = montar_previsoes([1.0, 2.0, 3.0], [1.5, 2.5, 3.5])
    quase_igual = gabarito.copy()
    quase_igual.loc[1, "previsto"] += 1e-12
    assert comparar_previsoes_com_gabarito(quase_igual, gabarito, CHAVE, 1e-9).passou

    diferente = gabarito.copy()
    diferente.loc[1, "previsto"] += 2e-9
    resultado = comparar_previsoes_com_gabarito(diferente, gabarito, CHAVE, 1e-9)
    assert not resultado.passou
    assert resultado.diferenca_maxima_do_previsto == pytest.approx(2e-9, rel=1e-3)


def test_diferenca_exatamente_igual_a_tolerancia_falha() -> None:
    """O limite e estrito: diferenca == tolerancia nao passa."""
    gabarito = montar_previsoes([1.0], [0.0])
    novas = montar_previsoes([1.0], [0.5])
    assert not comparar_previsoes_com_gabarito(novas, gabarito, CHAVE, 0.5).passou
    assert comparar_previsoes_com_gabarito(novas, gabarito, CHAVE, 0.5000001).passou


def test_linha_a_mais_ou_a_menos_falha_mesmo_com_diferenca_zero() -> None:
    """Conjunto de chaves diferente reprova, e conta de que lado esta a sobra."""
    gabarito = montar_previsoes([1.0, 2.0, 3.0], [1.5, 2.5, 3.5])
    com_a_mais = montar_previsoes([1.0, 2.0, 3.0, 4.0], [1.5, 2.5, 3.5, 4.5])
    resultado = comparar_previsoes_com_gabarito(com_a_mais, gabarito, CHAVE, 1e-9)
    assert not resultado.passou
    assert resultado.linhas_so_nas_novas == 1
    assert resultado.linhas_so_no_gabarito == 0

    com_a_menos = gabarito.iloc[:2]
    resultado = comparar_previsoes_com_gabarito(com_a_menos, gabarito, CHAVE, 1e-9)
    assert not resultado.passou
    assert resultado.linhas_so_no_gabarito == 1


def test_a_trava_casa_por_chave_e_nao_por_posicao() -> None:
    """Linhas em outra ordem (e com colunas extras nas novas) ainda passam."""
    gabarito = montar_previsoes([1.0, 2.0, 3.0], [1.5, 2.5, 3.5])
    embaralhada = gabarito.iloc[[2, 0, 1]].reset_index(drop=True)
    embaralhada["data_origem"] = pd.NaT
    assert comparar_previsoes_com_gabarito(embaralhada, gabarito, CHAVE, 1e-9).passou


def test_real_diferente_reprova_mesmo_com_previsto_igual() -> None:
    """A coluna `real` tambem e conferida."""
    gabarito = montar_previsoes([1.0, 2.0], [1.5, 2.5])
    novas = montar_previsoes([1.0, 9.0], [1.5, 2.5])
    resultado = comparar_previsoes_com_gabarito(novas, gabarito, CHAVE, 1e-9)
    assert not resultado.passou
    assert resultado.diferenca_maxima_do_real == 7.0


def test_sem_nenhuma_chave_em_comum_nao_passa() -> None:
    """Nada em comum: diferenca NaN, `passou` falso (nunca 'passou por vazio')."""
    novas = montar_previsoes([1.0], [1.0], primeira_data=pd.Timestamp("2024-01-07"))
    gabarito = montar_previsoes([1.0], [1.0], primeira_data=pd.Timestamp("2025-01-05"))
    resultado = comparar_previsoes_com_gabarito(novas, gabarito, CHAVE, 1e-9)
    assert not resultado.passou
    assert resultado.linhas_em_comum == 0
    assert np.isnan(resultado.diferenca_maxima_do_previsto)


def test_dois_vazios_nao_passam() -> None:
    """Comparar duas tabelas vazias nao e evidencia de igualdade."""
    vazia = montar_previsoes([], [])
    assert not comparar_previsoes_com_gabarito(vazia, vazia.copy(), CHAVE, 1e-9).passou


def test_a_trava_rejeita_chave_repetida_coluna_ausente_e_tolerancia_invalida() -> None:
    """Erros de entrada."""
    gabarito = montar_previsoes([1.0, 2.0], [1.5, 2.5])
    repetida = pd.concat([gabarito, gabarito.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Chave repetida"):
        comparar_previsoes_com_gabarito(repetida, gabarito, CHAVE, 1e-9)
    with pytest.raises(KeyError):
        comparar_previsoes_com_gabarito(gabarito.drop(columns=["previsto"]), gabarito, CHAVE, 1e-9)
    with pytest.raises(ValueError, match="tolerancia"):
        comparar_previsoes_com_gabarito(gabarito, gabarito, CHAVE, 0.0)


# ---------------------------------------------------------------------------
# calcular_cobertura
# ---------------------------------------------------------------------------


def test_cobertura_e_a_fracao_com_real_acima_do_previsto() -> None:
    """real = 1, 5, 3, 8; previsto = 2, 4, 3, 7: acima em 2 de 4 (o empate 3 = 3 nao conta)."""
    assert calcular_cobertura([1.0, 5.0, 3.0, 8.0], [2.0, 4.0, 3.0, 7.0]) == 0.5


def test_cobertura_extremos_e_vazio() -> None:
    """0 quando o previsto sempre cobre; 1 quando o real sempre passa; NaN sem pares."""
    assert calcular_cobertura([1.0, 2.0], [5.0, 5.0]) == 0.0
    assert calcular_cobertura([9.0, 9.0], [5.0, 5.0]) == 1.0
    assert np.isnan(calcular_cobertura([], []))


def test_cobertura_rejeita_tamanho_diferente_e_valor_invalido() -> None:
    """Tamanhos diferentes, NaN e infinito levantam ValueError."""
    with pytest.raises(ValueError):
        calcular_cobertura([1.0, 2.0], [1.0])
    with pytest.raises(ValueError):
        calcular_cobertura([1.0, np.nan], [1.0, 2.0])
    with pytest.raises(ValueError):
        calcular_cobertura([1.0, 2.0], [1.0, np.inf])


# ---------------------------------------------------------------------------
# decidir_quantil (regra de 2% da pre-declaracao)
# ---------------------------------------------------------------------------

MAE_BASE = {0.50: 120.0, 0.70: 110.0, 0.80: 101.0, 0.85: 100.0, 0.90: 105.0}


def test_quantil_de_referencia_continua_quando_ele_ja_e_o_melhor() -> None:
    """0,85 com o menor MAE: ganho zero, escolhido 0,85."""
    decisao = decidir_quantil(MAE_BASE, 0.85, 0.02)
    assert decisao.melhor_quantil == 0.85
    assert decisao.ganho_relativo == 0.0
    assert decisao.quantil_escolhido == 0.85


def test_vantagem_de_menos_de_2_por_cento_mantem_a_referencia() -> None:
    """0,80 com MAE 98,1 contra 100: ganho de 1,9% < 2%: o 0,85 continua."""
    mae = {**MAE_BASE, 0.80: 98.1}
    decisao = decidir_quantil(mae, 0.85, 0.02)
    assert decisao.melhor_quantil == 0.80
    assert decisao.ganho_relativo == pytest.approx(0.019)
    assert decisao.quantil_escolhido == 0.85


def test_vantagem_de_exatamente_2_por_cento_troca() -> None:
    """Regra 'so troca se a vantagem for de 2% ou mais': 98,0 contra 100 troca."""
    mae = {**MAE_BASE, 0.80: 98.0}
    decisao = decidir_quantil(mae, 0.85, 0.02)
    assert decisao.ganho_relativo == 0.02
    assert decisao.quantil_escolhido == 0.80


def test_vantagem_acima_de_2_por_cento_troca_para_o_melhor() -> None:
    """0,70 com 90 contra 100 (10%): escolhe 0,70, mesmo havendo outros melhores que a referencia."""
    mae = {**MAE_BASE, 0.70: 90.0}
    decisao = decidir_quantil(mae, 0.85, 0.02)
    assert decisao.melhor_quantil == 0.70
    assert decisao.mae_do_melhor == 90.0
    assert decisao.mae_da_referencia == 100.0
    assert decisao.ganho_relativo == pytest.approx(0.10)
    assert decisao.quantil_escolhido == 0.70


def test_empate_de_mae_prefere_a_referencia() -> None:
    """MAE igual ao da referencia nao e 'melhor'; a referencia vence."""
    mae = {**MAE_BASE, 0.80: 100.0}
    decisao = decidir_quantil(mae, 0.85, 0.02)
    assert decisao.melhor_quantil == 0.85
    assert decisao.quantil_escolhido == 0.85


def test_decidir_quantil_rejeita_entradas_invalidas() -> None:
    """Referencia ausente, MAE nao positivo ou nao finito, limite fora de [0, 1)."""
    sem_a_referencia = {quantil: mae for quantil, mae in MAE_BASE.items() if quantil != 0.85}
    with pytest.raises(ValueError, match="referencia"):
        decidir_quantil(sem_a_referencia, 0.85, 0.02)
    with pytest.raises(ValueError, match="MAE medio invalido"):
        decidir_quantil({**MAE_BASE, 0.70: 0.0}, 0.85, 0.02)
    with pytest.raises(ValueError, match="MAE medio invalido"):
        decidir_quantil({**MAE_BASE, 0.70: float("nan")}, 0.85, 0.02)
    with pytest.raises(ValueError, match="ganho_minimo"):
        decidir_quantil(MAE_BASE, 0.85, 1.0)
    with pytest.raises(ValueError, match="ganho_minimo"):
        decidir_quantil(MAE_BASE, 0.85, -0.01)


# ---------------------------------------------------------------------------
# calcular_mae_na_janela
# ---------------------------------------------------------------------------


def test_o_mae_na_janela_inclui_os_dois_limites_e_ignora_o_resto() -> None:
    """Linhas em 06/01/2024 (fora), 07/01/2024 e 01/02/2026 (dentro), 08/02/2026 (fora)."""
    datas = [
        pd.Timestamp("2024-01-06"),
        PRIMEIRA_DATA_DA_JANELA,
        ULTIMA_DATA_DA_JANELA,
        pd.Timestamp("2026-02-08"),
    ]
    previsoes = pd.DataFrame(
        {"data_alvo": datas, "real": [0.0, 10.0, 20.0, 0.0], "previsto": [999.0, 12.0, 17.0, 999.0]}
    )
    quantidade, mae = calcular_mae_na_janela(previsoes, CONFIGURACAO_AVALIACAO)
    assert quantidade == 2
    assert mae == pytest.approx((2.0 + 3.0) / 2.0)


def test_o_mae_de_janela_vazia_e_nan() -> None:
    """Sem nenhuma semana na janela: n = 0 e MAE NaN."""
    previsoes = pd.DataFrame({"data_alvo": [pd.Timestamp("2020-05-03")], "real": [1.0], "previsto": [2.0]})
    quantidade, mae = calcular_mae_na_janela(previsoes, CONFIGURACAO_AVALIACAO)
    assert quantidade == 0
    assert np.isnan(mae)


# ---------------------------------------------------------------------------
# comparar_cortes (E4)
# ---------------------------------------------------------------------------


def montar_previsoes_de_dois_bracos(deslocamento_do_completo: float, deslocamento_do_sem_vetor: float) -> pd.DataFrame:
    """Previsoes de `completo` e `sem_vetor` em h = 1 e h = 4, 4 semanas na janela cada.

    O real e 10, 20, 30, 40; o previsto e o real mais o deslocamento do braco (erro constante).
    """
    pedacos = []
    for nome_do_braco, deslocamento in (
        ("completo", deslocamento_do_completo),
        ("sem_vetor", deslocamento_do_sem_vetor),
    ):
        for horizonte in (1, 4):
            reais = [10.0, 20.0, 30.0, 40.0]
            previstos = [real + deslocamento for real in reais]
            do_braco = montar_previsoes(reais, previstos, horizonte=horizonte)
            do_braco.insert(0, "braco", nome_do_braco)
            pedacos.append(do_braco)
    return pd.concat(pedacos, ignore_index=True)


def test_comparar_cortes_calcula_mae_variacao_percentual_e_r2() -> None:
    """Erro constante de 10 pela resposta e de 5 pela pergunta: MAE 10 -> 5, variacao -50%."""
    pela_resposta = montar_previsoes_de_dois_bracos(10.0, 10.0)
    pela_pergunta = montar_previsoes_de_dois_bracos(5.0, 10.0)
    comparacao = comparar_cortes(pela_resposta, pela_pergunta, CONFIGURACAO_AVALIACAO)

    assert list(comparacao.columns) == [
        "braco", "h", "n", "mae_corte_resposta", "mae_corte_pergunta", "variacao_pct",
        "r2_corte_resposta", "r2_corte_pergunta",
    ]
    assert len(comparacao) == 4
    completo_h4 = comparacao.loc[(comparacao["braco"] == "completo") & (comparacao["h"] == 4)].iloc[0]
    assert completo_h4["n"] == 4
    assert completo_h4["mae_corte_resposta"] == 10.0
    assert completo_h4["mae_corte_pergunta"] == 5.0
    assert completo_h4["variacao_pct"] == -50.0

    soma_dos_quadrados_totais = 500.0  # reais 10..40, media 25: 225 + 25 + 25 + 225
    assert completo_h4["r2_corte_resposta"] == pytest.approx(1.0 - 4 * 100.0 / soma_dos_quadrados_totais)
    assert completo_h4["r2_corte_pergunta"] == pytest.approx(1.0 - 4 * 25.0 / soma_dos_quadrados_totais)

    sem_vetor_h4 = comparacao.loc[(comparacao["braco"] == "sem_vetor") & (comparacao["h"] == 4)].iloc[0]
    assert sem_vetor_h4["variacao_pct"] == 0.0


def test_comparar_cortes_pior_pela_pergunta_da_variacao_positiva() -> None:
    """Se o corte ingenuo piora, a variacao e positiva (sem assumir a direcao do vazamento)."""
    pela_resposta = montar_previsoes_de_dois_bracos(5.0, 5.0)
    pela_pergunta = montar_previsoes_de_dois_bracos(10.0, 5.0)
    comparacao = comparar_cortes(pela_resposta, pela_pergunta, CONFIGURACAO_AVALIACAO)
    completo = comparacao.loc[comparacao["braco"] == "completo"]
    assert (completo["variacao_pct"] == 100.0).all()


def test_comparar_cortes_ignora_semanas_fora_da_janela_nos_dois_lados() -> None:
    """Uma semana de 2020 (fora da janela) com erro enorme nao entra na conta."""
    pela_resposta = montar_previsoes_de_dois_bracos(10.0, 10.0)
    pela_pergunta = montar_previsoes_de_dois_bracos(5.0, 10.0)
    fora_da_janela = pd.DataFrame(
        {"braco": ["completo"], "h": [1], "data_alvo": [pd.Timestamp("2020-05-03")], "real": [0.0], "previsto": [1e6]}
    )
    pela_resposta_com_extra = pd.concat([pela_resposta, fora_da_janela], ignore_index=True)
    comparacao = comparar_cortes(pela_resposta_com_extra, pela_pergunta, CONFIGURACAO_AVALIACAO)
    completo_h1 = comparacao.loc[(comparacao["braco"] == "completo") & (comparacao["h"] == 1)].iloc[0]
    assert completo_h1["n"] == 4
    assert completo_h1["mae_corte_resposta"] == 10.0


def test_comparar_cortes_exige_as_mesmas_semanas_nos_dois_lados() -> None:
    """Uma semana so em um dos lados (dentro da janela) levanta ValueError."""
    pela_resposta = montar_previsoes_de_dois_bracos(10.0, 10.0)
    pela_pergunta = montar_previsoes_de_dois_bracos(5.0, 10.0).iloc[:-1]
    with pytest.raises(ValueError, match="so em um dos cortes"):
        comparar_cortes(pela_resposta, pela_pergunta, CONFIGURACAO_AVALIACAO)


def test_comparar_cortes_exige_o_mesmo_real_e_mae_nao_nulo() -> None:
    """`real` diferente entre os lados, ou MAE zero na base (divisao), levantam ValueError."""
    pela_resposta = montar_previsoes_de_dois_bracos(10.0, 10.0)
    pela_pergunta = montar_previsoes_de_dois_bracos(5.0, 10.0)
    pela_pergunta.loc[0, "real"] = 999.0
    with pytest.raises(ValueError, match="real"):
        comparar_cortes(pela_resposta, pela_pergunta, CONFIGURACAO_AVALIACAO)

    resposta_perfeita = montar_previsoes_de_dois_bracos(0.0, 10.0)
    pergunta_qualquer = montar_previsoes_de_dois_bracos(5.0, 10.0)
    with pytest.raises(ValueError, match="MAE zero"):
        comparar_cortes(resposta_perfeita, pergunta_qualquer, CONFIGURACAO_AVALIACAO)


def test_comparar_cortes_rejeita_coluna_ausente() -> None:
    """KeyError quando falta `braco`."""
    pela_resposta = montar_previsoes_de_dois_bracos(10.0, 10.0)
    with pytest.raises(KeyError):
        comparar_cortes(pela_resposta.drop(columns=["braco"]), pela_resposta, CONFIGURACAO_AVALIACAO)


# ---------------------------------------------------------------------------
# calcular_deltas_e_piso_de_ruido (pre-declaracao 8b)
# ---------------------------------------------------------------------------


def montar_mae_por_perturbacao() -> pd.DataFrame:
    """MAE de 5 perturbacoes em (folha 20, h 1) e (folha 5, h 4), com n = 102."""
    linhas = [
        ("csv", 20, 1, 102, 132.0),
        ("s1", 20, 1, 102, 135.5),
        ("s2", 20, 1, 102, 133.0),
        ("s3", 20, 1, 102, 131.0),
        ("s4", 20, 1, 102, 133.6),
        ("csv", 5, 4, 102, 220.0),
        ("s1", 5, 4, 102, 220.1),
        ("s2", 5, 4, 102, 219.7),
        ("s3", 5, 4, 102, 220.0),
        ("s4", 5, 4, 102, 220.2),
    ]
    return pd.DataFrame(linhas, columns=["perturbacao", "folha", "h", "n", "mae"])


def montar_mae_de_referencia() -> pd.DataFrame:
    """MAE da referencia certificada nas duas celulas."""
    return pd.DataFrame(
        {"folha": [20, 5], "h": [1, 4], "n": [102, 102], "mae": [133.5, 220.0]}
    )


def test_piso_e_o_maior_delta_absoluto_por_folha_e_horizonte() -> None:
    """Folha 20 h 1: deltas 1,5; 2,0; 0,5; 2,5; 0,1 -> piso 2,5 (da s3, abaixo da referencia: o sinal e descartado)."""
    deltas, piso = calcular_deltas_e_piso_de_ruido(montar_mae_por_perturbacao(), montar_mae_de_referencia())

    deltas_da_folha_20 = deltas.loc[deltas["folha"] == 20].set_index("perturbacao")["delta"]
    assert deltas_da_folha_20["csv"] == pytest.approx(1.5)
    assert deltas_da_folha_20["s1"] == pytest.approx(2.0)
    assert deltas_da_folha_20["s2"] == pytest.approx(0.5)
    assert deltas_da_folha_20["s3"] == pytest.approx(2.5)
    assert deltas_da_folha_20["s4"] == pytest.approx(0.1)

    piso_da_folha_20 = piso.loc[(piso["folha"] == 20) & (piso["h"] == 1)].iloc[0]
    assert piso_da_folha_20["piso_de_ruido"] == pytest.approx(2.5)
    assert piso_da_folha_20["perturbacao_do_maximo"] == "s3"
    assert piso_da_folha_20["duas_vezes_o_piso"] == pytest.approx(5.0)

    piso_da_folha_5 = piso.loc[(piso["folha"] == 5) & (piso["h"] == 4)].iloc[0]
    assert piso_da_folha_5["piso_de_ruido"] == pytest.approx(0.3)
    assert piso_da_folha_5["perturbacao_do_maximo"] == "s2"
    assert list(piso.columns) == ["folha", "h", "piso_de_ruido", "perturbacao_do_maximo", "duas_vezes_o_piso"]


def test_o_piso_traz_a_referencia_e_o_n_em_cada_linha_de_delta() -> None:
    """A tabela de deltas leva `mae_referencia` da celula certa."""
    deltas, _ = calcular_deltas_e_piso_de_ruido(montar_mae_por_perturbacao(), montar_mae_de_referencia())
    assert list(deltas.columns) == ["perturbacao", "folha", "h", "n", "mae", "mae_referencia", "delta"]
    assert (deltas.loc[deltas["folha"] == 20, "mae_referencia"] == 133.5).all()
    assert (deltas.loc[deltas["folha"] == 5, "mae_referencia"] == 220.0).all()
    assert len(deltas) == 10


def test_o_piso_rejeita_celula_sem_referencia_e_coluna_ausente() -> None:
    """Perturbacao em (folha, h) sem MAE de referencia: ValueError; coluna faltando: KeyError."""
    referencia_incompleta = montar_mae_de_referencia().iloc[:1]
    with pytest.raises(ValueError, match="sem MAE de referencia"):
        calcular_deltas_e_piso_de_ruido(montar_mae_por_perturbacao(), referencia_incompleta)
    with pytest.raises(KeyError):
        calcular_deltas_e_piso_de_ruido(montar_mae_por_perturbacao().drop(columns=["mae"]), montar_mae_de_referencia())
    with pytest.raises(KeyError):
        calcular_deltas_e_piso_de_ruido(montar_mae_por_perturbacao(), montar_mae_de_referencia().drop(columns=["mae"]))
