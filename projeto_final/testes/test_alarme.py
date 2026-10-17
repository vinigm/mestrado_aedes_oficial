"""Testes de `aedes/alarme.py` (E5): contagens a mao, limites estritos, razao notificacao/residencia e conversao do limiar.

Nenhum arquivo do projeto e lido ou escrito (as fichas sao fabricadas em memoria).
"""

import numpy as np
import pandas as pd
import pytest

from aedes.alarme import (
    ANOS_DA_AVALIACAO,
    calcular_metricas_do_alarme,
    calcular_razao_notificacao_residencia,
    contar_confirmados_de_porto_alegre,
    converter_limiar,
)


def test_alarme_contagens_a_mao_com_valor_exatamente_no_limiar_nao_conta() -> None:
    """L = 421, estrito (`>`), como no codigo antigo.

    real     = [100, 421, 422, 500, 10]  -> surto (> 421): [F, F, T, T, F]
    previsto = [430, 421, 100, 600,  5]  -> alarme (> 421): [T, F, F, T, F]
    VP = 1 (semana 3); FN = 1 (semana 2); FP = 1 (semana 0); VN = 2 (semanas 1 e 4).
    sensibilidade = 1/2; precisao = 1/2; falsos por ano = 1/1,96.
    """
    metricas = calcular_metricas_do_alarme(
        np.array([100.0, 421.0, 422.0, 500.0, 10.0]),
        np.array([430.0, 421.0, 100.0, 600.0, 5.0]),
        limiar=421.0,
    )
    assert metricas.n == 5
    assert metricas.semanas_de_surto == 2
    assert metricas.verdadeiros_positivos == 1
    assert metricas.falsos_negativos == 1
    assert metricas.falsos_positivos == 1
    assert metricas.verdadeiros_negativos == 2
    assert metricas.sensibilidade == pytest.approx(0.5, abs=1e-12)
    assert metricas.precisao == pytest.approx(0.5, abs=1e-12)
    assert metricas.falsos_por_ano == pytest.approx(1.0 / 1.96, abs=1e-12)


def test_alarme_limiar_nao_inteiro_separa_421_de_422() -> None:
    """L = 421,5: 421 nao passa e 422 passa."""
    metricas = calcular_metricas_do_alarme(np.array([421.0, 422.0]), np.array([422.0, 421.0]), limiar=421.5)
    assert metricas.semanas_de_surto == 1
    assert metricas.verdadeiros_positivos == 0
    assert metricas.falsos_negativos == 1
    assert metricas.falsos_positivos == 1


def test_alarme_sem_surto_ou_sem_alarme_da_nan_como_no_codigo_antigo() -> None:
    sem_surto = calcular_metricas_do_alarme(np.array([1.0, 2.0]), np.array([500.0, 3.0]), limiar=421.0)
    assert np.isnan(sem_surto.sensibilidade)
    assert sem_surto.precisao == 0.0
    sem_alarme = calcular_metricas_do_alarme(np.array([500.0, 2.0]), np.array([1.0, 3.0]), limiar=421.0)
    assert sem_alarme.sensibilidade == 0.0
    assert np.isnan(sem_alarme.precisao)


def test_alarme_falsos_por_ano_usa_1_96_por_padrao_e_aceita_outro_denominador() -> None:
    reais = np.array([0.0] * 7)
    previstos = np.array([500.0] * 7)
    padrao = calcular_metricas_do_alarme(reais, previstos, limiar=421.0)
    assert padrao.falsos_positivos == 7
    assert padrao.falsos_por_ano == pytest.approx(7.0 / 1.96, abs=1e-12)
    assert ANOS_DA_AVALIACAO == 1.96
    com_tres_anos = calcular_metricas_do_alarme(reais, previstos, limiar=421.0, anos_da_avaliacao=3.0)
    assert com_tres_anos.falsos_por_ano == pytest.approx(7.0 / 3.0, abs=1e-12)


def test_alarme_valida_entradas() -> None:
    with pytest.raises(ValueError):
        calcular_metricas_do_alarme(np.array([1.0, 2.0]), np.array([1.0]), limiar=421.0)
    with pytest.raises(ValueError):
        calcular_metricas_do_alarme(np.array([1.0, np.nan]), np.array([1.0, 2.0]), limiar=421.0)
    with pytest.raises(ValueError):
        calcular_metricas_do_alarme(np.array([1.0]), np.array([np.inf]), limiar=421.0)
    with pytest.raises(ValueError):
        calcular_metricas_do_alarme(np.array([1.0]), np.array([1.0]), limiar=421.0, anos_da_avaliacao=0.0)


def montar_fichas() -> pd.DataFrame:
    """Fichas fabricadas, tudo como texto. Contagem esperada a mao no teste.

    ficha | notif.  | resid.  | classi | sintomas   | entra?
      0   | 431490  | 431490  | 10     | 2018-01-05 | notif + resid
      1   | 431490  | 430000  | 11     | 2023-12-31 | so notif
      2   | 430000  | 431490  | 12     | 2020-06-01 | so resid
      3   | 431490  | 431490  | 5      | 2020-06-01 | nada (descartada)
      4   | 431490  | 431490  | 10     | 2017-12-31 | nada (antes de 2018)
      5   | 431490  | 431490  | 10     | 2024-01-01 | nada (depois de 2023)
      6   | 431490  | 431490  | 10     | (vazio)    | nada (sem data)
      7   | 431490  | 431490  | 10     | 2019-13-45 | nada (data invalida)
      8   | 4314900 | 431490  | 11     | 2021-03-03 | so resid (codigo de notificacao diferente)
      9   |  431490 | 431490  | 12     | 2022-07-07 | notif + resid (espaco no codigo e removido)
    """
    return pd.DataFrame(
        {
            "ID_MUNICIP": ["431490", "431490", "430000", "431490", "431490", "431490", "431490", "431490", "4314900", " 431490"],
            "ID_MN_RESI": ["431490", "430000", "431490", "431490", "431490", "431490", "431490", "431490", "431490", "431490"],
            "CLASSI_FIN": ["10", "11", "12", "5", "10", "10", "10", "10", "11", "12"],
            "DT_SIN_PRI": [
                "2018-01-05", "2023-12-31", "2020-06-01", "2020-06-01", "2017-12-31",
                "2024-01-01", "", "2019-13-45", "2021-03-03", "2022-07-07",
            ],
        }
    )


def test_contagem_de_confirmados_a_mao() -> None:
    contagem = contar_confirmados_de_porto_alegre(montar_fichas(), 2018, 2023)
    assert contagem.por_notificacao == 3  # fichas 0, 1 e 9
    assert contagem.por_residencia == 4  # fichas 0, 2, 8 e 9


def test_contagem_com_tabela_vazia_e_coluna_ausente() -> None:
    vazia = montar_fichas().iloc[0:0]
    contagem = contar_confirmados_de_porto_alegre(vazia, 2018, 2023)
    assert contagem.por_notificacao == 0
    assert contagem.por_residencia == 0
    with pytest.raises(KeyError):
        contar_confirmados_de_porto_alegre(montar_fichas().drop(columns=["CLASSI_FIN"]), 2018, 2023)


def test_razao_e_conversao_do_limiar_a_mao() -> None:
    """r = 9/10 = 0,9; L = 421 x 0,9 = 378,9."""
    razao = calcular_razao_notificacao_residencia(9, 10)
    assert razao == pytest.approx(0.9, abs=1e-12)
    assert converter_limiar(421.0, razao) == pytest.approx(378.9, abs=1e-9)
    with pytest.raises(ValueError):
        calcular_razao_notificacao_residencia(5, 0)
    with pytest.raises(ValueError):
        calcular_razao_notificacao_residencia(-1, 5)
    with pytest.raises(ValueError):
        converter_limiar(421.0, 0.0)
