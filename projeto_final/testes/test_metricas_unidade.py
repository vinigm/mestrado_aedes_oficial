"""Testes de unidade de `aedes.metricas` em dados sinteticos pequenos.

Cobrem as regras e os casos-limite, nao os numeros do artigo (esses sao do
teste diferencial `test_referencia_diferencial.py`):
    - MAE e R2 contra o `sklearn` (que o codigo antigo usava) e contra contas a mao;
    - entrada vazia, de 1 ponto, serie real constante (R2 por convencao do sklearn);
    - ausente, infinito e tamanhos diferentes: erro claro, nunca numero silencioso;
    - regua sazonal em semana sem o ano anterior (inicio da serie, caso apagado);
    - persistencia na semana de origem inexistente;
    - janela de avaliacao com limites incluidos;
    - a regua so entra na conta onde existe (pareada com a grade do modelo);
    - resumo por braco e horizonte com `n`.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, r2_score

from aedes.configuracao import CONFIGURACAO_AVALIACAO
from aedes.metricas import (
    COLUNAS_DO_RESUMO,
    NOME_DO_BRACO_PERSISTENCIA,
    NOME_DO_BRACO_REGUA_SAZONAL,
    erro_absoluto_medio,
    montar_previsoes_das_reguas,
    previsao_persistencia,
    previsao_regua_sazonal,
    r_quadrado,
    recortar_janela_de_avaliacao,
    resumir_metricas_por_horizonte_e_braco,
    resumir_na_janela_de_avaliacao,
)

PRIMEIRO_DOMINGO = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)
SEMANAS_DA_SERIE = 120


def montar_serie_sintetica(semanas_sem_caso: tuple[int, ...] = ()) -> pd.Series:
    """Serie semanal de 120 semanas: casos = 10 * posicao + 1, com NaN nas posicoes pedidas."""
    posicoes = np.arange(SEMANAS_DA_SERIE)
    datas = pd.DatetimeIndex(PRIMEIRO_DOMINGO + posicoes * UMA_SEMANA)
    casos = (10.0 * posicoes + 1.0).astype(float)
    for posicao in semanas_sem_caso:
        casos[posicao] = np.nan
    return pd.Series(casos, index=datas)


def data_da_posicao(posicao: int) -> pd.Timestamp:
    """Domingo da semana de posicao `posicao` da serie sintetica."""
    return PRIMEIRO_DOMINGO + posicao * UMA_SEMANA


# --------------------------------------------------------------------------- MAE e R2


def test_mae_conta_a_mao() -> None:
    reais = np.array([10.0, 20.0, 30.0])
    previstos = np.array([12.0, 15.0, 30.0])
    assert erro_absoluto_medio(reais, previstos) == pytest.approx((2.0 + 5.0 + 0.0) / 3.0)


def test_r2_conta_a_mao() -> None:
    reais = np.array([10.0, 20.0, 30.0])
    previstos = np.array([12.0, 15.0, 30.0])
    soma_residual = 4.0 + 25.0 + 0.0
    soma_total = 100.0 + 0.0 + 100.0
    assert r_quadrado(reais, previstos) == pytest.approx(1.0 - soma_residual / soma_total)


def test_mae_e_r2_identicos_ao_sklearn_em_dados_aleatorios() -> None:
    gerador = np.random.default_rng(7)
    reais = gerador.gamma(2.0, 50.0, size=200)
    previstos = reais + gerador.normal(0.0, 30.0, size=200)
    assert erro_absoluto_medio(reais, previstos) == pytest.approx(mean_absolute_error(reais, previstos), abs=1e-12)
    assert r_quadrado(reais, previstos) == pytest.approx(r2_score(reais, previstos), abs=1e-12)


def test_r2_de_previsao_perfeita_e_1_e_de_prever_a_media_e_0() -> None:
    reais = np.array([3.0, 8.0, 1.0, 12.0])
    assert r_quadrado(reais, reais) == 1.0
    media_constante = np.full(4, reais.mean())
    assert r_quadrado(reais, media_constante) == pytest.approx(0.0, abs=1e-12)


def test_r2_pode_ser_negativo_quando_pior_que_a_media() -> None:
    reais = np.array([1.0, 2.0, 3.0])
    previstos = np.array([30.0, 20.0, 10.0])
    assert r_quadrado(reais, previstos) < 0.0
    assert r_quadrado(reais, previstos) == pytest.approx(r2_score(reais, previstos))


def test_aceita_series_do_pandas() -> None:
    reais = pd.Series([10.0, 20.0], index=[5, 9])
    previstos = pd.Series([14.0, 20.0], index=[1, 2])
    assert erro_absoluto_medio(reais, previstos) == pytest.approx(2.0)


def test_serie_real_constante_segue_a_convencao_do_sklearn() -> None:
    """SQ_total = 0: R2 nao e definido; o sklearn (e o antigo) devolve 1,0 se o erro e zero, senao 0,0."""
    reais_constantes = np.array([5.0, 5.0, 5.0, 5.0])
    previsao_exata = np.array([5.0, 5.0, 5.0, 5.0])
    previsao_errada = np.array([4.0, 6.0, 5.0, 5.0])

    assert r_quadrado(reais_constantes, previsao_exata) == 1.0
    assert r_quadrado(reais_constantes, previsao_errada) == 0.0
    assert r_quadrado(reais_constantes, previsao_exata) == r2_score(reais_constantes, previsao_exata)
    assert r_quadrado(reais_constantes, previsao_errada) == r2_score(reais_constantes, previsao_errada)
    # O MAE nao tem esse problema.
    assert erro_absoluto_medio(reais_constantes, previsao_errada) == pytest.approx(0.5)


def test_entrada_vazia_devolve_nan() -> None:
    vazio = np.array([], dtype=float)
    assert np.isnan(erro_absoluto_medio(vazio, vazio))
    assert np.isnan(r_quadrado(vazio, vazio))


def test_um_unico_ponto_tem_mae_mas_r2_nan() -> None:
    reais = np.array([10.0])
    previstos = np.array([13.0])
    assert erro_absoluto_medio(reais, previstos) == pytest.approx(3.0)
    assert np.isnan(r_quadrado(reais, previstos))


@pytest.mark.parametrize("funcao", [erro_absoluto_medio, r_quadrado])
def test_ausente_e_infinito_levantam_erro_claro(funcao) -> None:
    com_ausente = np.array([1.0, np.nan, 3.0])
    com_infinito = np.array([1.0, np.inf, 3.0])
    normal = np.array([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="ausente ou infinito"):
        funcao(com_ausente, normal)
    with pytest.raises(ValueError, match="ausente ou infinito"):
        funcao(normal, com_ausente)
    with pytest.raises(ValueError, match="ausente ou infinito"):
        funcao(normal, com_infinito)


@pytest.mark.parametrize("funcao", [erro_absoluto_medio, r_quadrado])
def test_tamanhos_diferentes_levantam_erro(funcao) -> None:
    with pytest.raises(ValueError, match="mesmo tamanho"):
        funcao(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))


def test_entrada_que_nao_e_unidimensional_levanta_erro() -> None:
    with pytest.raises(ValueError, match="1-D"):
        erro_absoluto_medio(np.ones((2, 2)), np.ones((2, 2)))


# --------------------------------------------------------------------------- regua sazonal


def test_regua_sazonal_usa_a_mesma_semana_do_ano_anterior() -> None:
    serie = montar_serie_sintetica()
    datas_alvo = pd.Series([data_da_posicao(52), data_da_posicao(60), data_da_posicao(119)])

    previsto = previsao_regua_sazonal(serie, datas_alvo)

    # posicao 52 -> 0 (1 caso), 60 -> 8 (81), 119 -> 67 (671)
    assert previsto.tolist() == [1.0, 81.0, 671.0]


def test_regua_sazonal_nao_interpola_52_vs_53_semanas() -> None:
    serie = montar_serie_sintetica()
    datas_alvo = pd.Series([data_da_posicao(100)])
    assert previsao_regua_sazonal(serie, datas_alvo).iloc[0] == 10.0 * 48 + 1.0
    assert previsao_regua_sazonal(serie, datas_alvo, semanas_do_passo_sazonal=53).iloc[0] == 10.0 * 47 + 1.0


def test_regua_sazonal_em_semana_sem_o_ano_anterior_e_nan() -> None:
    serie = montar_serie_sintetica()
    # posicao 51: o ano anterior seria a posicao -1, antes do inicio da serie.
    datas_alvo = pd.Series([data_da_posicao(51), data_da_posicao(52)])

    previsto = previsao_regua_sazonal(serie, datas_alvo)

    assert np.isnan(previsto.iloc[0])
    assert previsto.iloc[1] == 1.0


def test_regua_sazonal_com_caso_apagado_no_ano_anterior_e_nan() -> None:
    serie = montar_serie_sintetica(semanas_sem_caso=(8,))
    datas_alvo = pd.Series([data_da_posicao(60), data_da_posicao(61)])

    previsto = previsao_regua_sazonal(serie, datas_alvo)

    assert np.isnan(previsto.iloc[0])
    assert previsto.iloc[1] == 10.0 * 9 + 1.0


def test_regua_mantem_o_indice_das_datas_alvo() -> None:
    serie = montar_serie_sintetica()
    datas_alvo = pd.Series([data_da_posicao(60), data_da_posicao(61)], index=[40, 7])

    previsto = previsao_regua_sazonal(serie, datas_alvo)

    assert previsto.index.tolist() == [40, 7]


# --------------------------------------------------------------------------- persistencia


def test_persistencia_usa_a_semana_de_origem() -> None:
    serie = montar_serie_sintetica()
    datas_alvo = pd.Series([data_da_posicao(10), data_da_posicao(50)])

    previsto_h1 = previsao_persistencia(serie, datas_alvo, horizonte=1)
    previsto_h4 = previsao_persistencia(serie, datas_alvo, horizonte=4)

    assert previsto_h1.tolist() == [10.0 * 9 + 1.0, 10.0 * 49 + 1.0]
    assert previsto_h4.tolist() == [10.0 * 6 + 1.0, 10.0 * 46 + 1.0]


def test_persistencia_em_origem_antes_da_serie_ou_sem_caso_e_nan() -> None:
    serie = montar_serie_sintetica(semanas_sem_caso=(30,))
    datas_alvo = pd.Series([data_da_posicao(2), data_da_posicao(34), data_da_posicao(35)])

    previsto = previsao_persistencia(serie, datas_alvo, horizonte=4)

    assert np.isnan(previsto.iloc[0])  # origem na posicao -2
    assert np.isnan(previsto.iloc[1])  # origem na posicao 30, sem caso
    assert previsto.iloc[2] == 10.0 * 31 + 1.0


@pytest.mark.parametrize("horizonte_invalido", [0, -1, 1.5, True])
def test_persistencia_recusa_horizonte_invalido(horizonte_invalido) -> None:
    serie = montar_serie_sintetica()
    with pytest.raises(ValueError, match="horizonte"):
        previsao_persistencia(serie, pd.Series([data_da_posicao(10)]), horizonte_invalido)


def test_serie_com_indice_que_nao_e_de_datas_levanta_erro() -> None:
    serie_com_indice_inteiro = pd.Series([1.0, 2.0, 3.0])
    with pytest.raises(TypeError, match="DatetimeIndex"):
        previsao_regua_sazonal(serie_com_indice_inteiro, pd.Series([data_da_posicao(60)]))


def test_serie_com_data_repetida_levanta_erro() -> None:
    serie = montar_serie_sintetica()
    serie_repetida = pd.concat([serie, serie.iloc[[10]]])
    with pytest.raises(ValueError, match="repetida"):
        previsao_persistencia(serie_repetida, pd.Series([data_da_posicao(60)]), 1)


# --------------------------------------------------------------------------- janela


def montar_previsoes_do_modelo(posicoes_alvo: list[int], horizonte: int = 1, braco: str = "referencia") -> pd.DataFrame:
    """Previsoes sinteticas: real = casos da serie, previsto = real + 10."""
    serie = montar_serie_sintetica()
    datas_alvo = [data_da_posicao(posicao) for posicao in posicoes_alvo]
    reais = [float(serie.loc[data]) for data in datas_alvo]
    return pd.DataFrame(
        {
            "h": horizonte,
            "data_alvo": datas_alvo,
            "real": reais,
            "previsto": [real + 10.0 for real in reais],
            "braco": braco,
        }
    )


def test_janela_inclui_os_dois_limites_e_exclui_o_resto() -> None:
    primeira = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    ultima = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
    datas = [primeira - UMA_SEMANA, primeira, primeira + UMA_SEMANA, ultima, ultima + UMA_SEMANA]
    previsoes = pd.DataFrame({"h": 1, "data_alvo": datas, "real": 1.0, "previsto": 2.0, "braco": "x"})

    recorte = recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)

    assert recorte["data_alvo"].tolist() == [primeira, primeira + UMA_SEMANA, ultima]


def test_janela_nao_modifica_a_entrada_e_exige_data_alvo() -> None:
    previsoes = pd.DataFrame({"h": [1], "real": [1.0], "previsto": [2.0], "braco": ["x"]})
    with pytest.raises(KeyError, match="data_alvo"):
        recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)

    com_data = pd.DataFrame(
        {"h": [1], "data_alvo": [CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada], "real": [1.0], "previsto": [2.0], "braco": ["x"]}
    )
    copia_antes = com_data.copy()
    recorte = recortar_janela_de_avaliacao(com_data, CONFIGURACAO_AVALIACAO)
    recorte.loc[:, "previsto"] = 999.0
    pd.testing.assert_frame_equal(com_data, copia_antes)


# --------------------------------------------------------------------------- reguas pareadas


def test_reguas_so_entram_onde_existem_e_na_grade_do_modelo() -> None:
    serie = montar_serie_sintetica()
    # Posicoes 40 e 51 nao tem o ano anterior (sazonal NaN); 60 e 70 tem.
    grade = montar_previsoes_do_modelo([40, 51, 60, 70], horizonte=2)

    reguas = montar_previsoes_das_reguas(grade, serie)

    sazonal = reguas.loc[reguas["braco"] == NOME_DO_BRACO_REGUA_SAZONAL]
    persistencia = reguas.loc[reguas["braco"] == NOME_DO_BRACO_PERSISTENCIA]
    assert sazonal["data_alvo"].tolist() == [data_da_posicao(60), data_da_posicao(70)]
    assert persistencia["data_alvo"].tolist() == [data_da_posicao(40), data_da_posicao(51), data_da_posicao(60), data_da_posicao(70)]
    assert sazonal["previsto"].tolist() == [10.0 * 8 + 1.0, 10.0 * 18 + 1.0]
    assert persistencia["previsto"].tolist() == [10.0 * 38 + 1.0, 10.0 * 49 + 1.0, 10.0 * 58 + 1.0, 10.0 * 68 + 1.0]
    assert reguas["real"].notna().all()
    assert list(reguas.columns) == ["h", "data_alvo", "real", "previsto", "braco"]


def test_reguas_ordem_sazonal_depois_persistencia_e_real_da_serie() -> None:
    serie = montar_serie_sintetica()
    grade = montar_previsoes_do_modelo([60, 70], horizonte=1)

    reguas = montar_previsoes_das_reguas(grade, serie)

    assert reguas["braco"].tolist() == [NOME_DO_BRACO_REGUA_SAZONAL] * 2 + [NOME_DO_BRACO_PERSISTENCIA] * 2
    sazonal_real = reguas.loc[reguas["braco"] == NOME_DO_BRACO_REGUA_SAZONAL, "real"].tolist()
    assert sazonal_real == [10.0 * 60 + 1.0, 10.0 * 70 + 1.0]


def test_reguas_persistencia_recua_h_semanas_diferente_por_horizonte() -> None:
    serie = montar_serie_sintetica()
    grade = pd.concat(
        [
            montar_previsoes_do_modelo([80], horizonte=1),
            montar_previsoes_do_modelo([80], horizonte=3),
        ],
        ignore_index=True,
    )

    reguas = montar_previsoes_das_reguas(grade, serie)

    persistencia = reguas.loc[reguas["braco"] == NOME_DO_BRACO_PERSISTENCIA].set_index("h")["previsto"]
    assert persistencia.loc[1] == 10.0 * 79 + 1.0
    assert persistencia.loc[3] == 10.0 * 77 + 1.0


def test_reguas_ignoram_linhas_duplicadas_da_grade() -> None:
    serie = montar_serie_sintetica()
    grade = montar_previsoes_do_modelo([60, 60, 70], horizonte=1)

    reguas = montar_previsoes_das_reguas(grade, serie)

    assert len(reguas.loc[reguas["braco"] == NOME_DO_BRACO_PERSISTENCIA]) == 2


def test_reguas_exigem_h_e_data_alvo() -> None:
    serie = montar_serie_sintetica()
    with pytest.raises(KeyError, match="h"):
        montar_previsoes_das_reguas(pd.DataFrame({"data_alvo": [data_da_posicao(60)]}), serie)


def test_reguas_com_grade_vazia_devolvem_tabela_vazia_com_as_colunas() -> None:
    serie = montar_serie_sintetica()
    grade_vazia = montar_previsoes_do_modelo([60]).iloc[0:0]  # vazia, mas com os tipos certos

    reguas = montar_previsoes_das_reguas(grade_vazia, serie)

    assert len(reguas) == 0
    assert list(reguas.columns) == ["h", "data_alvo", "real", "previsto", "braco"]


# --------------------------------------------------------------------------- resumo


def test_resumo_tem_n_mae_r2_por_braco_e_horizonte_na_ordem_certa() -> None:
    modelo_h2 = montar_previsoes_do_modelo([60, 61, 62], horizonte=2, braco="B")
    modelo_h1 = montar_previsoes_do_modelo([60, 61, 62, 63], horizonte=1, braco="B")
    outro_braco = montar_previsoes_do_modelo([60, 61], horizonte=1, braco="A")
    previsoes = pd.concat([modelo_h2, modelo_h1, outro_braco], ignore_index=True)

    resumo = resumir_metricas_por_horizonte_e_braco(previsoes)

    assert list(resumo.columns) == list(COLUNAS_DO_RESUMO)
    assert resumo[["braco", "h"]].values.tolist() == [["B", 1], ["B", 2], ["A", 1]]
    assert resumo["n"].tolist() == [4, 3, 2]
    assert resumo["mae"].tolist() == pytest.approx([10.0, 10.0, 10.0])
    assert resumo["n"].dtype.kind == "i"


def test_resumo_exige_as_colunas_e_recusa_ausente() -> None:
    sem_previsto = pd.DataFrame({"braco": ["x"], "h": [1], "real": [1.0]})
    with pytest.raises(KeyError, match="previsto"):
        resumir_metricas_por_horizonte_e_braco(sem_previsto)

    com_ausente = pd.DataFrame({"braco": ["x", "x"], "h": [1, 1], "real": [1.0, 2.0], "previsto": [1.0, np.nan]})
    with pytest.raises(ValueError, match="ausente"):
        resumir_metricas_por_horizonte_e_braco(com_ausente)


def test_resumo_de_tabela_vazia_tem_so_o_cabecalho() -> None:
    vazia = pd.DataFrame({"braco": [], "h": [], "real": [], "previsto": []})
    resumo = resumir_metricas_por_horizonte_e_braco(vazia)
    assert len(resumo) == 0
    assert list(resumo.columns) == list(COLUNAS_DO_RESUMO)


def test_resumo_na_janela_recorta_por_data_alvo_antes_de_medir() -> None:
    primeira = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    ultima = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
    datas = [primeira - UMA_SEMANA, primeira, ultima, ultima + UMA_SEMANA]
    erros = [1000.0, 4.0, 6.0, 1000.0]
    previsoes = pd.DataFrame(
        {
            "h": 1,
            "data_alvo": datas,
            "real": [100.0, 100.0, 100.0, 100.0],
            "previsto": [100.0 + erro for erro in erros],
            "braco": "x",
        }
    )

    resumo = resumir_na_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)

    assert resumo["n"].tolist() == [2]
    assert resumo["mae"].tolist() == pytest.approx([5.0])


def test_regua_sem_o_ano_anterior_tem_n_menor_que_o_modelo() -> None:
    """A regua e medida so onde existe; o n mostra quantas semanas ela nao cobre."""
    serie = montar_serie_sintetica()
    modelo = montar_previsoes_do_modelo([40, 51, 60, 70], horizonte=1)
    reguas = montar_previsoes_das_reguas(modelo, serie)

    resumo = resumir_metricas_por_horizonte_e_braco(pd.concat([modelo, reguas], ignore_index=True))

    n_por_braco = resumo.set_index("braco")["n"].to_dict()
    assert n_por_braco["referencia"] == 4
    assert n_por_braco[NOME_DO_BRACO_REGUA_SAZONAL] == 2
    assert n_por_braco[NOME_DO_BRACO_PERSISTENCIA] == 4
