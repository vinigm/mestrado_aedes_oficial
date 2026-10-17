"""Testes da E6b: a grade de 30 configuracoes (fabrica de modelos, truncagem, laco, resumo e ranking).

Cinco blocos:
    1. as 30 configuracoes, rotulos e a fabrica de modelos com os hiperparametros do codigo antigo
       (comparados com o construtor DIRETO do scikit-learn / LightGBM, parametro a parametro);
    2. a truncagem da previsao em zero e o laco de uma celula, em matrizes sinteticas;
    3. o resumo e o ranking, com conta a mao e em dados reais do antigo:
       aplicados as previsoes salvas pelo antigo (`e6b_corrigido_previsoes_*.csv`), reproduzem as ancoras
       da pre-declaracao (42,02; 42,52; 42,71; 42,71; 46,17; 47,00; 58,45) e as posicoes 1 a 4 e 30;
    4. DIFERENCIAIS COM MODELO (matriz truncada nas primeiras origens, rapidos): a celula HistGB q0,85 M1
       sem truncar e IGUAL, bit a bit, ao `executar_walk_forward` do pacote e, com tolerancia de 1e-12, a
       referencia certificada em h = 1 e h = 12 (truncada em zero, quando a grade trunca); e as celulas
       GradientBoosting e LightGBM reproduzem as previsoes salvas pelo antigo.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from aedes.bracos import montar_matriz_do_braco
from aedes.configuracao import (
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    ConfiguracaoAvaliacao,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.grade import (
    ALGORITMO_GBR,
    ALGORITMO_HISTGB,
    ALGORITMO_LIGHTGBM,
    CONJUNTO_M0,
    CONJUNTO_M1,
    ConfiguracaoDaGrade,
    classificar_periodo,
    construir_ranking_da_grade,
    criar_modelo_da_grade,
    executar_walk_forward_da_grade,
    montar_as_30_configuracoes,
    montar_parametros_da_grade,
    resumir_previsoes_da_grade,
    rotulo_da_perda_para_quantil,
    truncar_previsao_em_zero,
)
from aedes.walk_forward import executar_walk_forward

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DOS_GABARITOS = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_DA_REFERENCIA = PASTA_DO_PROJETO / "resultados" / "referencia" / "previsoes.csv"

FIM_DA_CALIBRACAO = CONFIGURACAO_AVALIACAO.fim_da_calibracao
TOLERANCIA_CONTRA_A_REFERENCIA = 1e-12


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def previsoes_do_antigo() -> pd.DataFrame:
    """As previsoes das 30 configuracoes salvas pelo antigo (`pred` renomeado para `previsto`)."""
    tabelas: list[pd.DataFrame] = []
    for sufixo in ("parciais", "padrao", "restante"):
        caminho = PASTA_DOS_GABARITOS / f"e6b_corrigido_previsoes_{sufixo}.csv"
        tabelas.append(pd.read_csv(caminho, parse_dates=["data_alvo"], float_precision="round_trip"))
    juntas = pd.concat(tabelas, ignore_index=True)
    return juntas.rename(columns={"pred": "previsto"})


@pytest.fixture(scope="module")
def referencia_certificada() -> pd.DataFrame:
    """As previsoes certificadas do ciclo 3 (folha 5 = `referencia`)."""
    referencia = pd.read_csv(
        CAMINHO_DA_REFERENCIA, parse_dates=["data_origem", "data_alvo"], float_precision="round_trip"
    )
    return referencia.loc[referencia["braco"] == "referencia"]


# ---------------------------------------------------------------------------
# 1. As 30 configuracoes e a fabrica de modelos
# ---------------------------------------------------------------------------


def test_a_grade_tem_30_configuracoes_unicas_na_ordem_do_antigo() -> None:
    """3 algoritmos x 5 perdas x 2 conjuntos; ordem: algoritmo, perda (padrao, 0,70, 0,80, 0,85, 0,90), M0 antes de M1."""
    configuracoes = montar_as_30_configuracoes()
    assert len(configuracoes) == 30
    rotulos = [configuracao.rotulo() for configuracao in configuracoes]
    assert len(set(rotulos)) == 30
    assert rotulos[0] == "hist_gradient_boosting|padrao|M0_sem_vetor"
    assert rotulos[1] == "hist_gradient_boosting|padrao|M1_com_vetor"
    assert rotulos[2] == "hist_gradient_boosting|quantil_0.70|M0_sem_vetor"
    assert rotulos[-1] == "lightgbm|quantil_0.90|M1_com_vetor"
    algoritmos_na_ordem = [configuracao.algoritmo for configuracao in configuracoes]
    assert algoritmos_na_ordem[:10] == [ALGORITMO_HISTGB] * 10
    assert algoritmos_na_ordem[10:20] == [ALGORITMO_GBR] * 10
    assert algoritmos_na_ordem[20:] == [ALGORITMO_LIGHTGBM] * 10


def test_rotulo_da_perda_e_sua_inversa() -> None:
    """`padrao` <-> None; `quantil_0.85` <-> 0,85; rotulo invalido levanta ValueError."""
    assert ConfiguracaoDaGrade(ALGORITMO_HISTGB, None, CONJUNTO_M1).rotulo_da_perda() == "padrao"
    assert ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.7, CONJUNTO_M1).rotulo_da_perda() == "quantil_0.70"
    assert rotulo_da_perda_para_quantil("padrao") is None
    assert rotulo_da_perda_para_quantil("quantil_0.85") == 0.85
    with pytest.raises(ValueError):
        rotulo_da_perda_para_quantil("quantil")


def test_configuracao_invalida_e_rejeitada_na_criacao() -> None:
    """Algoritmo, conjunto ou quantil fora da grade levantam ValueError."""
    with pytest.raises(ValueError):
        ConfiguracaoDaGrade("xgboost", 0.85, CONJUNTO_M1)
    with pytest.raises(ValueError):
        ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, "M2")
    with pytest.raises(ValueError):
        ConfiguracaoDaGrade(ALGORITMO_HISTGB, 1.0, CONJUNTO_M1)


# Hiperparametros do antigo, transcritos de `analises/2026-08-30_grid_completo/rodar_grid.py:48-153`.
PARAMETROS_ANTIGOS_DO_HISTGB = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
}
PARAMETROS_ANTIGOS_DO_GBR = {
    "n_estimators": 250,
    "learning_rate": 0.05,
    "max_depth": 3,
    "min_samples_leaf": 5,
    "random_state": 42,
}
PARAMETROS_ANTIGOS_DO_LIGHTGBM = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "verbose": -1,
    "n_jobs": -1,
    "random_state": 42,
}


@pytest.mark.parametrize("quantil", [None, 0.70, 0.80, 0.85, 0.90])
def test_o_histgb_da_grade_tem_exatamente_os_parametros_do_construtor_do_antigo(quantil: float | None) -> None:
    """`get_params()` do modelo da grade == o do `HistGradientBoostingRegressor(**parametros do antigo)`, os 15 campos."""
    parametros_do_antigo = dict(PARAMETROS_ANTIGOS_DO_HISTGB)
    if quantil is None:
        parametros_do_antigo["loss"] = "squared_error"
    else:
        parametros_do_antigo["loss"] = "quantile"
        parametros_do_antigo["quantile"] = quantil
    do_antigo = HistGradientBoostingRegressor(**parametros_do_antigo)

    da_grade = criar_modelo_da_grade(ConfiguracaoDaGrade(ALGORITMO_HISTGB, quantil, CONJUNTO_M1))
    assert isinstance(da_grade, HistGradientBoostingRegressor)
    assert da_grade.get_params() == do_antigo.get_params()


@pytest.mark.parametrize("quantil", [None, 0.70, 0.80, 0.85, 0.90])
def test_o_gbr_da_grade_tem_exatamente_os_parametros_do_construtor_do_antigo(quantil: float | None) -> None:
    """GradientBoosting: 250 arvores, taxa 0,05, profundidade 3, folha minima 5, `alpha` so na perda quantilica."""
    parametros_do_antigo = dict(PARAMETROS_ANTIGOS_DO_GBR)
    if quantil is None:
        parametros_do_antigo["loss"] = "squared_error"
    else:
        parametros_do_antigo["loss"] = "quantile"
        parametros_do_antigo["alpha"] = quantil
    do_antigo = GradientBoostingRegressor(**parametros_do_antigo)

    da_grade = criar_modelo_da_grade(ConfiguracaoDaGrade(ALGORITMO_GBR, quantil, CONJUNTO_M0))
    assert isinstance(da_grade, GradientBoostingRegressor)
    assert da_grade.get_params() == do_antigo.get_params()


@pytest.mark.parametrize("quantil", [None, 0.70, 0.80, 0.85, 0.90])
def test_o_lightgbm_da_grade_tem_exatamente_os_parametros_do_construtor_do_antigo(quantil: float | None) -> None:
    """LightGBM: 300 arvores, taxa 0,05, 31 folhas, folha minima 20, `n_jobs=-1`, `objective` e `alpha` da perda."""
    parametros_do_antigo = dict(PARAMETROS_ANTIGOS_DO_LIGHTGBM)
    if quantil is None:
        parametros_do_antigo["objective"] = "regression"
    else:
        parametros_do_antigo["objective"] = "quantile"
        parametros_do_antigo["alpha"] = quantil
    do_antigo = LGBMRegressor(**parametros_do_antigo)

    da_grade = criar_modelo_da_grade(ConfiguracaoDaGrade(ALGORITMO_LIGHTGBM, quantil, CONJUNTO_M1))
    assert isinstance(da_grade, LGBMRegressor)
    assert da_grade.get_params() == do_antigo.get_params()


def test_a_perda_quadratica_nao_passa_quantil_nem_alpha() -> None:
    """O antigo so passava o quantil na perda quantilica: nas chaves da perda padrao nao ha `quantile` nem `alpha`."""
    assert "quantile" not in montar_parametros_da_grade(ALGORITMO_HISTGB, None)
    assert "alpha" not in montar_parametros_da_grade(ALGORITMO_GBR, None)
    assert "alpha" not in montar_parametros_da_grade(ALGORITMO_LIGHTGBM, None)
    assert montar_parametros_da_grade(ALGORITMO_HISTGB, 0.85)["quantile"] == 0.85
    assert montar_parametros_da_grade(ALGORITMO_GBR, 0.85)["alpha"] == 0.85


def test_o_histgb_q085_da_grade_tem_os_mesmos_parametros_da_folha_5_do_pacote() -> None:
    """A celula de referencia da grade usa a mesma configuracao do pacote (`FOLHA_5`): mesmos 15 parametros."""
    parametros_da_grade = montar_parametros_da_grade(ALGORITMO_HISTGB, 0.85)
    assert parametros_da_grade == FOLHA_5.parametros_do_sklearn()


def test_algoritmo_desconhecido_e_erro() -> None:
    """Pedir parametros de um algoritmo fora da grade levanta ValueError."""
    with pytest.raises(ValueError):
        montar_parametros_da_grade("xgboost", 0.85)


# ---------------------------------------------------------------------------
# 2. Truncagem e laco, em matrizes sinteticas
# ---------------------------------------------------------------------------


def test_truncar_em_zero_zera_o_negativo_e_preserva_o_resto() -> None:
    """`max(previsao, 0.0)`: negativo vira 0; zero e positivo ficam; NaN fica NaN; -0.0 fica como o antigo (-0.0)."""
    assert truncar_previsao_em_zero(-3.5) == 0.0
    assert truncar_previsao_em_zero(0.0) == 0.0
    assert truncar_previsao_em_zero(2.25) == 2.25
    assert truncar_previsao_em_zero(-1e-300) == 0.0
    assert np.isnan(truncar_previsao_em_zero(float("nan")))
    assert truncar_previsao_em_zero(float("inf")) == float("inf")
    assert np.signbit(truncar_previsao_em_zero(-0.0))  # `max(-0.0, 0.0)` devolve o primeiro, como no antigo


def montar_matriz_sintetica(
    quantidade_de_linhas: int,
    horizonte: int,
    media_do_alvo: float,
    semente: int,
) -> pd.DataFrame:
    """Matriz de um horizonte, sem ausente, em ordem cronologica: 2 variaveis e o alvo em torno de `media_do_alvo`."""
    gerador = np.random.default_rng(semente)
    datas_de_origem = pd.date_range("2020-01-05", periods=quantidade_de_linhas, freq="7D")
    return pd.DataFrame(
        {
            "data_origem": datas_de_origem,
            "data_alvo": datas_de_origem + pd.Timedelta(weeks=horizonte),
            "x1": gerador.normal(size=quantidade_de_linhas),
            "x2": gerador.normal(size=quantidade_de_linhas),
            "y_h": media_do_alvo + gerador.normal(scale=1.0, size=quantidade_de_linhas),
        }
    )


AVALIACAO_CURTA = ConfiguracaoAvaliacao(
    horizontes=(1,),
    treino_minimo_em_semanas=30,
    passo_do_retreino_em_semanas=1,
    fim_da_calibracao=pd.Timestamp("2023-12-31"),
    primeira_data_alvo_avaliada=pd.Timestamp("2024-01-07"),
    ultima_data_alvo_avaliada=pd.Timestamp("2026-02-01"),
)


def test_com_alvo_negativo_a_celula_truncada_e_o_maximo_com_zero_da_nao_truncada() -> None:
    """Perda quadratica com alvo em torno de -50: a previsao crua e negativa; truncada, vira 0; resto identico."""
    matriz = montar_matriz_sintetica(40, 1, -50.0, semente=1)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, None, CONJUNTO_M1)
    sem_truncar = executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=False)
    truncada = executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=True)
    assert (sem_truncar["previsto"] < 0).all()
    assert (truncada["previsto"] == 0.0).all()
    pd.testing.assert_frame_equal(
        truncada.drop(columns=["previsto"]), sem_truncar.drop(columns=["previsto"]), check_exact=True
    )


def test_com_alvo_positivo_a_truncagem_nao_muda_nada() -> None:
    """Alvo em torno de +50: nenhuma previsao negativa, as duas celulas saem iguais bit a bit."""
    matriz = montar_matriz_sintetica(40, 1, 50.0, semente=2)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_GBR, 0.80, CONJUNTO_M1)
    sem_truncar = executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=False)
    truncada = executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=True)
    pd.testing.assert_frame_equal(truncada, sem_truncar, check_exact=True)


def test_o_laco_devolve_uma_linha_por_origem_de_teste_com_as_colunas_do_pacote() -> None:
    """Origens de `treino_minimo` ate a ultima linha, passo 1; colunas h, data_origem, data_alvo, real, previsto."""
    matriz = montar_matriz_sintetica(36, 1, 10.0, semente=3)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    previsoes = executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=True)
    assert list(previsoes.columns) == ["h", "data_origem", "data_alvo", "real", "previsto"]
    assert len(previsoes) == 36 - 30
    assert previsoes["data_origem"].iloc[0] == matriz["data_origem"].iloc[30]
    assert previsoes["data_alvo"].iloc[0] == matriz["data_alvo"].iloc[30]
    assert previsoes["real"].iloc[0] == matriz["y_h"].iloc[30]


def test_o_laco_da_grade_nao_deixa_entrar_no_treino_linha_cuja_resposta_e_posterior_a_origem() -> None:
    """Regra da RESPOSTA: com h = 3, alterar o alvo das 2 linhas imediatamente anteriores a origem nao muda a previsao."""
    horizonte = 3
    matriz = montar_matriz_sintetica(34, horizonte, 10.0, semente=4)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    original = executar_walk_forward_da_grade(matriz, horizonte, configuracao, AVALIACAO_CURTA, truncar_em_zero=False)

    alterada = matriz.copy()
    # A origem de teste na posicao 30 usa so as linhas com data_origem + 3 semanas <= data_origem[30]: ate a posicao 27.
    alterada.loc[28:29, "y_h"] = 1e6
    refeita = executar_walk_forward_da_grade(alterada, horizonte, configuracao, AVALIACAO_CURTA, truncar_em_zero=False)
    assert original["previsto"].iloc[0] == refeita["previsto"].iloc[0]


def test_matriz_sem_a_coluna_do_alvo_levanta_keyerror() -> None:
    """A validacao de entrada e a do walk-forward do pacote."""
    matriz = montar_matriz_sintetica(36, 1, 10.0, semente=5).drop(columns=["y_h"])
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    with pytest.raises(KeyError):
        executar_walk_forward_da_grade(matriz, 1, configuracao, AVALIACAO_CURTA, truncar_em_zero=True)


# ---------------------------------------------------------------------------
# 3. Periodo, resumo e ranking
# ---------------------------------------------------------------------------


def test_o_periodo_e_calibracao_ate_31_12_2023_inclusive_e_avaliacao_depois() -> None:
    """Limite do antigo: `data_alvo > 2023-12-31` e avaliacao; o proprio 31/12/2023 e calibracao."""
    datas = pd.Series(pd.to_datetime(["2023-12-24", "2023-12-31", "2024-01-07", "2025-06-01"]))
    periodos = classificar_periodo(datas, FIM_DA_CALIBRACAO)
    assert list(periodos) == ["calibracao", "calibracao", "avaliacao", "avaliacao"]


def montar_previsoes_de_conta_a_mao() -> pd.DataFrame:
    """Duas configuracoes A e B, h = 1 e 4, calibracao e avaliacao, com valores que permitem conta a mao."""
    linhas: list[dict[str, object]] = []

    def acrescentar(perda: str, horizonte: int, data: str, real: float, previsto: float) -> None:
        linhas.append(
            {
                "algoritmo": "hist_gradient_boosting",
                "perda": perda,
                "conjunto": "M1_com_vetor",
                "h": horizonte,
                "data_alvo": pd.Timestamp(data),
                "real": real,
                "previsto": previsto,
            }
        )

    # Configuracao `quantil_0.85`: calibracao h=1 erros 2 e 4 (MAE 3); h=4 erros 10 e 20 (MAE 15) -> MAE_cal = 9.
    acrescentar("quantil_0.85", 1, "2023-06-04", 10.0, 12.0)
    acrescentar("quantil_0.85", 1, "2023-06-11", 10.0, 6.0)
    acrescentar("quantil_0.85", 4, "2023-06-04", 50.0, 60.0)
    acrescentar("quantil_0.85", 4, "2023-06-11", 50.0, 30.0)
    # Avaliacao h=1: real 200 (pico), previsto 150; real 100 (NAO e pico: o limite e estrito >100), previsto 130.
    acrescentar("quantil_0.85", 1, "2024-02-04", 200.0, 150.0)
    acrescentar("quantil_0.85", 1, "2024-02-11", 100.0, 130.0)
    # Configuracao `padrao`: calibracao h=1 erro 8; h=4 erro 12 -> MAE_cal = 10 (pior que 9).
    acrescentar("padrao", 1, "2023-06-04", 10.0, 18.0)
    acrescentar("padrao", 4, "2023-06-04", 50.0, 62.0)
    acrescentar("padrao", 1, "2024-02-04", 200.0, 100.0)
    acrescentar("padrao", 4, "2024-02-04", 200.0, 100.0)
    return pd.DataFrame(linhas)


def test_o_resumo_separa_periodos_e_calcula_mae_n_e_pico_a_mao() -> None:
    """MAE, n, vies e captura no pico da avaliacao: so a semana de real 200 e pico (o 100 nao passa de 100)."""
    resumo = resumir_previsoes_da_grade(montar_previsoes_de_conta_a_mao(), FIM_DA_CALIBRACAO)
    chave = (resumo["perda"] == "quantil_0.85") & (resumo["h"] == 1)
    calibracao = resumo.loc[chave & (resumo["periodo"] == "calibracao")].iloc[0]
    assert calibracao["n"] == 2
    assert calibracao["mae"] == 3.0
    assert np.isnan(calibracao["vies_pico"])  # nenhuma semana com real > 100 na calibracao
    avaliacao = resumo.loc[chave & (resumo["periodo"] == "avaliacao")].iloc[0]
    assert avaliacao["n"] == 2
    assert avaliacao["mae"] == (50.0 + 30.0) / 2
    assert avaliacao["vies_pico"] == 150.0 - 200.0
    assert avaliacao["captura_pico"] == 150.0 / 200.0


def test_o_ranking_ordena_pelo_mae_de_calibracao_e_calcula_a_diferenca_percentual() -> None:
    """quantil_0.85 (MAE_cal 9) fica na frente de padrao (10); `dif_pct` do 2o = (10/9 - 1) * 100."""
    resumo = resumir_previsoes_da_grade(montar_previsoes_de_conta_a_mao(), FIM_DA_CALIBRACAO)
    ranking = construir_ranking_da_grade(resumo)
    assert list(ranking["pos"]) == [1, 2]
    assert list(ranking["perda"]) == ["quantil_0.85", "padrao"]
    assert ranking["mae_cal"].iloc[0] == 9.0
    assert ranking["mae_cal"].iloc[1] == 10.0
    assert ranking["dif_pct"].iloc[0] == 0.0
    assert ranking["dif_pct"].iloc[1] == pytest.approx((10.0 / 9.0 - 1.0) * 100.0, rel=1e-12)
    assert ranking["mae_aval"].iloc[1] == 100.0


def test_o_ranking_so_usa_os_horizontes_pedidos_na_media_de_calibracao() -> None:
    """Com `horizontes_do_ranking=(1,)`, o MAE_cal e so o de h = 1 (3 e 8)."""
    resumo = resumir_previsoes_da_grade(montar_previsoes_de_conta_a_mao(), FIM_DA_CALIBRACAO)
    ranking = construir_ranking_da_grade(resumo, horizontes_do_ranking=(1,))
    assert ranking["mae_cal"].iloc[0] == 3.0
    assert ranking["mae_cal"].iloc[1] == 8.0


def test_empate_de_mae_de_calibracao_fica_em_ordem_alfabetica_de_algoritmo_perda_e_conjunto() -> None:
    """Ordenacao estavel sobre a tabela agrupada: MAE_cal identico mantem a ordem (algoritmo, perda, conjunto)."""
    linhas = []
    for perda in ("quantil_0.90", "quantil_0.70"):
        for horizonte in (1, 4):
            linhas.append(
                {
                    "algoritmo": "lightgbm",
                    "perda": perda,
                    "conjunto": "M1_com_vetor",
                    "h": horizonte,
                    "data_alvo": pd.Timestamp("2023-06-04"),
                    "real": 10.0,
                    "previsto": 14.0,
                }
            )
    for perda in ("quantil_0.90", "quantil_0.70"):
        linhas.append(
            {
                "algoritmo": "lightgbm",
                "perda": perda,
                "conjunto": "M1_com_vetor",
                "h": 1,
                "data_alvo": pd.Timestamp("2024-02-04"),
                "real": 1.0,
                "previsto": 2.0,
            }
        )
    ranking = construir_ranking_da_grade(resumir_previsoes_da_grade(pd.DataFrame(linhas), FIM_DA_CALIBRACAO))
    assert list(ranking["mae_cal"]) == [4.0, 4.0]
    assert list(ranking["perda"]) == ["quantil_0.70", "quantil_0.90"]


def test_resumo_sem_coluna_obrigatoria_levanta_keyerror() -> None:
    """Falta `conjunto`: KeyError com o nome da coluna."""
    previsoes = montar_previsoes_de_conta_a_mao().drop(columns=["conjunto"])
    with pytest.raises(KeyError, match="conjunto"):
        resumir_previsoes_da_grade(previsoes, FIM_DA_CALIBRACAO)


def test_o_ranking_das_previsoes_do_antigo_reproduz_as_ancoras_da_predeclaracao(
    previsoes_do_antigo: pd.DataFrame,
) -> None:
    """DIFERENCIAL SEM MODELO: ranking dos 35.490 previsoes salvas = ancoras de 12/10 (42,02 ... 58,45) e posicoes."""
    resumo = resumir_previsoes_da_grade(previsoes_do_antigo, FIM_DA_CALIBRACAO)
    ranking = construir_ranking_da_grade(resumo)
    assert len(ranking) == 30

    def linha_de(algoritmo: str, perda: str, conjunto: str) -> pd.Series:
        escolha = (
            (ranking["algoritmo"] == algoritmo) & (ranking["perda"] == perda) & (ranking["conjunto"] == conjunto)
        )
        return ranking.loc[escolha].iloc[0]

    primeiro = linha_de(ALGORITMO_HISTGB, "quantil_0.85", CONJUNTO_M1)
    assert primeiro["pos"] == 1
    assert round(primeiro["mae_cal"], 2) == 42.02
    segundo = linha_de(ALGORITMO_HISTGB, "quantil_0.80", CONJUNTO_M0)
    assert (segundo["pos"], round(segundo["mae_cal"], 2)) == (2, 42.52)
    terceiro = linha_de(ALGORITMO_HISTGB, "quantil_0.80", CONJUNTO_M1)
    assert (terceiro["pos"], round(terceiro["mae_cal"], 2)) == (3, 42.71)
    quarto = linha_de(ALGORITMO_GBR, "quantil_0.80", CONJUNTO_M1)
    assert (quarto["pos"], round(quarto["mae_cal"], 2)) == (4, 42.71)
    assert round(linha_de(ALGORITMO_HISTGB, "padrao", CONJUNTO_M1)["mae_cal"], 2) == 46.17
    assert round(linha_de(ALGORITMO_LIGHTGBM, "padrao", CONJUNTO_M1)["mae_cal"], 2) == 47.00
    ultimo = linha_de(ALGORITMO_LIGHTGBM, "quantil_0.90", CONJUNTO_M1)
    assert (ultimo["pos"], round(ultimo["mae_cal"], 2)) == (30, 58.45)


def test_o_resumo_das_previsoes_do_antigo_tem_30_configuracoes_4_horizontes_2_periodos(
    previsoes_do_antigo: pd.DataFrame,
) -> None:
    """30 x 4 x 2 = 240 linhas; a avaliacao de todos tem n = 102 (h = 1) ... e a calibracao n varia por conjunto."""
    resumo = resumir_previsoes_da_grade(previsoes_do_antigo, FIM_DA_CALIBRACAO)
    assert len(resumo) == 240
    avaliacao_do_m1 = resumo.loc[(resumo["periodo"] == "avaliacao") & (resumo["conjunto"] == CONJUNTO_M1)]
    assert set(avaliacao_do_m1["n"]) == {102}


# ---------------------------------------------------------------------------
# 4. Diferenciais com modelo (matriz truncada nas primeiras origens)
# ---------------------------------------------------------------------------

LINHAS_DA_MATRIZ_TRUNCADA = 112  # 8 origens de teste (treino minimo de 104)


def montar_matriz_truncada(tabela_cortada: pd.DataFrame, horizonte: int, conjunto: str) -> pd.DataFrame:
    """As primeiras 112 linhas da matriz do conjunto: o treino de cada origem so olha linhas anteriores, entao
    as 8 previsoes sao as mesmas que as da matriz inteira."""
    nome_do_braco = {CONJUNTO_M0: "sem_vetor", CONJUNTO_M1: "completo"}[conjunto]
    matriz = montar_matriz_do_braco(
        tabela_cortada, horizonte, nome_do_braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    return matriz.iloc[:LINHAS_DA_MATRIZ_TRUNCADA].reset_index(drop=True)


@pytest.mark.parametrize("horizonte", [1, 12])
def test_celula_histgb_q085_m1_sem_truncar_e_igual_bit_a_bit_ao_walk_forward_do_pacote(
    tabela_cortada: pd.DataFrame, horizonte: int
) -> None:
    """Mesmo laco, mesmo modelo: a celula da grade (sem truncar) e `executar_walk_forward(FOLHA_5)` sao identicos."""
    matriz = montar_matriz_truncada(tabela_cortada, horizonte, CONJUNTO_M1)
    do_pacote = executar_walk_forward(matriz, horizonte, FOLHA_5, CONFIGURACAO_AVALIACAO)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    da_grade = executar_walk_forward_da_grade(
        matriz, horizonte, configuracao, CONFIGURACAO_AVALIACAO, truncar_em_zero=False
    )
    assert len(da_grade) == LINHAS_DA_MATRIZ_TRUNCADA - CONFIGURACAO_AVALIACAO.treino_minimo_em_semanas
    pd.testing.assert_frame_equal(da_grade, do_pacote, check_exact=True)


@pytest.mark.parametrize("horizonte", [1, 12])
def test_celula_histgb_q085_m1_reproduz_a_referencia_certificada_com_e_sem_truncagem(
    tabela_cortada: pd.DataFrame, referencia_certificada: pd.DataFrame, horizonte: int
) -> None:
    """Contra `resultados/referencia/previsoes.csv`: sem truncar, igual a referencia; truncada, igual a `max(ref, 0)`.

    A referencia certificada e reproduzida com diferenca ate ~2e-13 (nao exatamente 0: o proprio
    `executar_walk_forward` de hoje tem a mesma diferenca de ~4e-16 a 2e-13 contra ela, ver o relatorio da
    E6b); a tolerancia do teste e 1e-12, bem abaixo da trava de 1e-9 da pre-declaracao.
    """
    matriz = montar_matriz_truncada(tabela_cortada, horizonte, CONJUNTO_M1)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    sem_truncar = executar_walk_forward_da_grade(
        matriz, horizonte, configuracao, CONFIGURACAO_AVALIACAO, truncar_em_zero=False
    )
    truncada = executar_walk_forward_da_grade(
        matriz, horizonte, configuracao, CONFIGURACAO_AVALIACAO, truncar_em_zero=True
    )

    da_referencia = referencia_certificada.loc[referencia_certificada["h"] == horizonte]
    pareadas = sem_truncar.merge(da_referencia, on="data_origem", suffixes=("_grade", "_referencia"))
    assert len(pareadas) == len(sem_truncar)
    diferenca_sem_truncar = (pareadas["previsto_grade"] - pareadas["previsto_referencia"]).abs()
    assert diferenca_sem_truncar.max() < TOLERANCIA_CONTRA_A_REFERENCIA

    pareadas_truncadas = truncada.merge(da_referencia, on="data_origem", suffixes=("_grade", "_referencia"))
    referencia_truncada = np.maximum(pareadas_truncadas["previsto_referencia"], 0.0)
    diferenca_truncada = (pareadas_truncadas["previsto_grade"] - referencia_truncada).abs()
    assert diferenca_truncada.max() < TOLERANCIA_CONTRA_A_REFERENCIA


CELULAS_DO_ANTIGO = [
    (ALGORITMO_GBR, 0.85, CONJUNTO_M1, 1),
    (ALGORITMO_GBR, None, CONJUNTO_M0, 12),
    (ALGORITMO_LIGHTGBM, 0.85, CONJUNTO_M1, 1),
    (ALGORITMO_LIGHTGBM, 0.90, CONJUNTO_M0, 12),
    (ALGORITMO_HISTGB, 0.80, CONJUNTO_M0, 12),
    (ALGORITMO_HISTGB, None, CONJUNTO_M1, 1),
]


@pytest.mark.parametrize("algoritmo,quantil,conjunto,horizonte", CELULAS_DO_ANTIGO)
def test_celulas_da_grade_reproduzem_as_previsoes_salvas_pelo_antigo(
    tabela_cortada: pd.DataFrame,
    previsoes_do_antigo: pd.DataFrame,
    algoritmo: str,
    quantil: float | None,
    conjunto: str,
    horizonte: int,
) -> None:
    """As 8 primeiras origens de varias celulas (3 algoritmos, perdas e conjuntos) iguais ao CSV do antigo, diferenca < 1e-9."""
    matriz = montar_matriz_truncada(tabela_cortada, horizonte, conjunto)
    configuracao = ConfiguracaoDaGrade(algoritmo, quantil, conjunto)
    novas = executar_walk_forward_da_grade(
        matriz, horizonte, configuracao, CONFIGURACAO_AVALIACAO, truncar_em_zero=True
    )

    do_antigo = previsoes_do_antigo.loc[
        (previsoes_do_antigo["algoritmo"] == algoritmo)
        & (previsoes_do_antigo["perda"] == configuracao.rotulo_da_perda())
        & (previsoes_do_antigo["conjunto"] == conjunto)
        & (previsoes_do_antigo["h"] == horizonte)
    ]
    pareadas = novas.merge(do_antigo, on="data_alvo", suffixes=("_novo", "_antigo"))
    assert len(pareadas) == len(novas) == 8
    diferenca = (pareadas["previsto_novo"] - pareadas["previsto_antigo"]).abs()
    assert diferenca.max() < 1e-9
    assert (pareadas["real_novo"] - pareadas["real_antigo"]).abs().max() < 1e-9
