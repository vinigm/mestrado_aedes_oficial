"""Teste diferencial do ciclo 3: a referencia completa contra o gabarito do codigo antigo.

Entrada: `resultados/referencia/previsoes.csv` e `resultados/referencia/metricas.csv`,
gerados por `python3 -B -m experimentos.referencia` (12 horizontes x folhas 5 e 20).
Se a rodada ainda nao existe, os testes sao PULADOS com mensagem clara.

Gabarito (so leitura): `testes/referencia_antiga/`
    - `previsoes_referencia.csv`: h, data_alvo, real, previsto, braco;
    - `metricas_ancora.csv`: braco, h, n, mae, r2 na janela de avaliacao;
    - `serie_casos_apos_corte.csv`: a serie de casos depois do corte de maturidade.

O que tem de bater:
    - previsoes: as 12 h x 2 bracos IDENTICAS ao gabarito, por (h, data_alvo, braco),
      com tolerancia 1e-9 (mesmo conjunto de linhas, `real` identico);
    - metricas: MAE e R2 iguais a `metricas_ancora.csv` (tolerancia 1e-6) e n = 102;
    - reguas: sazonal e persistencia iguais as ancoras do codigo antigo
      (`analises/2026-09-25_regua_regras_simples/`, tolerancia 0,05 no MAE), e
      recalculadas aqui do zero, sem usar `aedes.metricas`, a partir da serie
      do gabarito;
    - as metricas tambem sao refeitas do zero (sklearn) sobre as previsoes do
      GABARITO, para que o teste nao dependa do codigo que esta sendo testado.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, r2_score

from aedes.configuracao import CONFIGURACAO_AVALIACAO

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_DAS_PREVISOES = PASTA_DO_PROJETO / "resultados" / "referencia" / "previsoes.csv"
CAMINHO_DAS_METRICAS = PASTA_DO_PROJETO / "resultados" / "referencia" / "metricas.csv"
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_DO_GABARITO_DAS_PREVISOES = PASTA_DO_GABARITO / "previsoes_referencia.csv"
CAMINHO_DO_GABARITO_DAS_METRICAS = PASTA_DO_GABARITO / "metricas_ancora.csv"
CAMINHO_DO_GABARITO_DA_SERIE = PASTA_DO_GABARITO / "serie_casos_apos_corte.csv"

HORIZONTES = tuple(range(1, 13))
BRACOS_DO_MODELO = ("referencia", "HistGB_folha20_M1")
BRACO_REGUA_SAZONAL = "regua_sazonal"
BRACO_PERSISTENCIA = "persistencia"
CHAVE = ["h", "data_alvo", "braco"]

QUANTIDADE_DE_SEMANAS_AVALIADAS = 102
LINHAS_ESPERADAS_NO_GABARITO = 6948
TOLERANCIA_DO_PREVISTO = 1e-9
TOLERANCIA_DA_METRICA = 1e-6
TOLERANCIA_DA_REGUA = 0.05

# MAE das reguas na janela de avaliacao, por h = 1..12, do codigo antigo
# (`analises/2026-09-25_regua_regras_simples/saidas/metricas_por_horizonte_e_periodo.csv`,
# periodo "avaliacao"). As do README para h = 1, 4, 8, 12 (arredondadas a 0,1):
# sazonal 202,1 / 213,2 / 216,2 / 217,8; persistencia 83,3 / 279,0 / 531,0 / 697,5.
MAE_DA_REGUA_SAZONAL_ANTIGA = (
    202.1078, 202.4118, 211.7745, 213.1765, 213.6471, 213.7843,
    214.1471, 216.1667, 217.2941, 217.4020, 217.6471, 217.7843,
)
MAE_DA_PERSISTENCIA_ANTIGA = (
    83.2941, 153.4510, 214.5588, 278.9510, 343.2549, 405.4020,
    468.3137, 530.9706, 585.5000, 624.2451, 667.6275, 697.4902,
)

# Ancoras da tarefa: MAE e R2 nos horizontes 1, 4, 8, 12 (3 casas).
ANCORAS_DO_MODELO = {
    ("referencia", 1): (97.987, 0.8979),
    ("referencia", 4): (219.669, 0.6285),
    ("referencia", 8): (272.627, 0.4503),
    ("referencia", 12): (278.818, 0.4366),
    ("HistGB_folha20_M1", 1): (133.626, 0.834),
    ("HistGB_folha20_M1", 4): (199.635, 0.717),
    ("HistGB_folha20_M1", 8): (223.183, 0.576),
    ("HistGB_folha20_M1", 12): (243.765, 0.558),
}


@pytest.fixture(scope="module")
def previsoes_novas() -> pd.DataFrame:
    """As previsoes da referencia, ou pula o teste se a rodada ainda nao existe."""
    if not CAMINHO_DAS_PREVISOES.exists():
        pytest.skip(
            f"{CAMINHO_DAS_PREVISOES.relative_to(PASTA_DO_PROJETO)} nao existe: rode "
            "`python3 -B -m experimentos.referencia` (ver o README, Ciclo 3) e repita."
        )
    return pd.read_csv(CAMINHO_DAS_PREVISOES, parse_dates=["data_origem", "data_alvo"])


@pytest.fixture(scope="module")
def metricas_novas() -> pd.DataFrame:
    """As metricas da referencia, ou pula o teste se a rodada ainda nao existe."""
    if not CAMINHO_DAS_METRICAS.exists():
        pytest.skip(
            f"{CAMINHO_DAS_METRICAS.relative_to(PASTA_DO_PROJETO)} nao existe: rode "
            "`python3 -B -m experimentos.referencia` (ver o README, Ciclo 3) e repita."
        )
    return pd.read_csv(CAMINHO_DAS_METRICAS)


@pytest.fixture(scope="module")
def previsoes_do_gabarito() -> pd.DataFrame:
    """As previsoes salvas pelo codigo antigo (12 h x 2 bracos)."""
    return pd.read_csv(CAMINHO_DO_GABARITO_DAS_PREVISOES, parse_dates=["data_alvo"])


@pytest.fixture(scope="module")
def metricas_do_gabarito() -> pd.DataFrame:
    """As metricas-ancora do codigo antigo (MAE, R2 e n por braco e h)."""
    return pd.read_csv(CAMINHO_DO_GABARITO_DAS_METRICAS)


@pytest.fixture(scope="module")
def serie_de_casos_do_gabarito() -> pd.Series:
    """A serie de casos depois do corte de maturidade, indexada pela data da semana."""
    tabela = pd.read_csv(CAMINHO_DO_GABARITO_DA_SERIE, parse_dates=["data_inicio_semana_epidemi"])
    return pd.Series(
        tabela["casos_confirmados"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(tabela["data_inicio_semana_epidemi"]),
    )


def recortar(previsoes: pd.DataFrame, braco: str, horizonte: int) -> pd.DataFrame:
    """Previsoes de um braco e um horizonte, ordenadas por data_alvo."""
    do_braco = previsoes["braco"] == braco
    do_horizonte = previsoes["h"] == horizonte
    recorte = previsoes.loc[do_braco & do_horizonte]
    return recorte.sort_values("data_alvo").reset_index(drop=True)


def recortar_na_janela_de_avaliacao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """So as semanas-alvo da janela de avaliacao (2024-01-07 a 2026-02-01)."""
    depois_do_inicio = previsoes["data_alvo"] >= CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    antes_do_fim = previsoes["data_alvo"] <= CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
    return previsoes.loc[depois_do_inicio & antes_do_fim]


def buscar_metrica(metricas: pd.DataFrame, braco: str, horizonte: int) -> pd.Series:
    """A linha (braco, h) de uma tabela de metricas; erro se nao houver exatamente uma."""
    do_braco = metricas["braco"] == braco
    do_horizonte = metricas["h"] == horizonte
    linhas = metricas.loc[do_braco & do_horizonte]
    assert len(linhas) == 1, f"esperava 1 linha para ({braco}, h={horizonte}), achei {len(linhas)}"
    return linhas.iloc[0]


# --------------------------------------------------------------------------- previsoes


def test_a_referencia_tem_os_24_conjuntos_com_as_colunas_certas(previsoes_novas: pd.DataFrame) -> None:
    assert list(previsoes_novas.columns) == ["h", "data_origem", "data_alvo", "real", "previsto", "braco"]
    assert set(previsoes_novas["braco"]) == set(BRACOS_DO_MODELO)
    assert set(previsoes_novas["h"]) == set(HORIZONTES)
    assert not previsoes_novas[["real", "previsto"]].isna().any().any()
    for braco in BRACOS_DO_MODELO:
        for horizonte in HORIZONTES:
            assert len(recortar(previsoes_novas, braco, horizonte)) > 0, (braco, horizonte)


def test_mesmas_linhas_do_gabarito(previsoes_novas: pd.DataFrame, previsoes_do_gabarito: pd.DataFrame) -> None:
    """Mesmo conjunto de (h, data_alvo, braco), sem duplicata, nem a mais nem a menos."""
    assert len(previsoes_do_gabarito) == LINHAS_ESPERADAS_NO_GABARITO
    assert not previsoes_novas.duplicated(subset=CHAVE).any()
    assert not previsoes_do_gabarito.duplicated(subset=CHAVE).any()

    chaves_novas = set(map(tuple, previsoes_novas[CHAVE].to_numpy().tolist()))
    chaves_do_gabarito = set(map(tuple, previsoes_do_gabarito[CHAVE].to_numpy().tolist()))
    so_nas_novas = chaves_novas - chaves_do_gabarito
    so_no_gabarito = chaves_do_gabarito - chaves_novas

    assert not so_nas_novas, f"{len(so_nas_novas)} linha(s) so nas previsoes novas, ex.: {sorted(so_nas_novas)[:3]}"
    assert not so_no_gabarito, f"{len(so_no_gabarito)} linha(s) so no gabarito, ex.: {sorted(so_no_gabarito)[:3]}"


@pytest.mark.parametrize("horizonte", HORIZONTES)
@pytest.mark.parametrize("braco", BRACOS_DO_MODELO)
def test_previsto_e_real_identicos_ao_gabarito(
    braco: str,
    horizonte: int,
    previsoes_novas: pd.DataFrame,
    previsoes_do_gabarito: pd.DataFrame,
) -> None:
    nova = recortar(previsoes_novas, braco, horizonte)
    antiga = recortar(previsoes_do_gabarito, braco, horizonte)

    assert len(nova) == len(antiga)
    np.testing.assert_array_equal(nova["data_alvo"].to_numpy(), antiga["data_alvo"].to_numpy())
    np.testing.assert_array_equal(nova["real"].to_numpy(), antiga["real"].to_numpy())

    diferenca_maxima = float(np.max(np.abs(nova["previsto"].to_numpy() - antiga["previsto"].to_numpy())))
    assert diferenca_maxima < TOLERANCIA_DO_PREVISTO, (
        f"{braco} h={horizonte}: diferenca maxima de `previsto` = {diferenca_maxima:.3e}"
    )


# --------------------------------------------------------------------------- metricas dos modelos


def test_metricas_tem_os_4_bracos_e_n_102(metricas_novas: pd.DataFrame) -> None:
    assert list(metricas_novas.columns) == ["braco", "h", "n", "mae", "r2"]
    esperados = set(BRACOS_DO_MODELO) | {BRACO_REGUA_SAZONAL, BRACO_PERSISTENCIA}
    assert set(metricas_novas["braco"]) == esperados
    assert len(metricas_novas) == 4 * len(HORIZONTES)
    assert (metricas_novas["n"] == QUANTIDADE_DE_SEMANAS_AVALIADAS).all()


@pytest.mark.parametrize("horizonte", HORIZONTES)
@pytest.mark.parametrize("braco", BRACOS_DO_MODELO)
def test_mae_e_r2_dos_modelos_iguais_a_metricas_ancora(
    braco: str, horizonte: int, metricas_novas: pd.DataFrame, metricas_do_gabarito: pd.DataFrame
) -> None:
    nova = buscar_metrica(metricas_novas, braco, horizonte)
    ancora = buscar_metrica(metricas_do_gabarito, braco, horizonte)

    assert int(nova["n"]) == int(ancora["n"]) == QUANTIDADE_DE_SEMANAS_AVALIADAS
    assert nova["mae"] == pytest.approx(ancora["mae"], abs=TOLERANCIA_DA_METRICA)
    assert nova["r2"] == pytest.approx(ancora["r2"], abs=TOLERANCIA_DA_METRICA)


@pytest.mark.parametrize("braco_e_horizonte", sorted(ANCORAS_DO_MODELO))
def test_ancoras_da_tarefa_nos_horizontes_1_4_8_12(
    braco_e_horizonte: tuple[str, int], metricas_novas: pd.DataFrame
) -> None:
    braco, horizonte = braco_e_horizonte
    mae_esperado, r2_esperado = ANCORAS_DO_MODELO[braco_e_horizonte]
    linha = buscar_metrica(metricas_novas, braco, horizonte)
    assert linha["mae"] == pytest.approx(mae_esperado, abs=5e-4)
    assert linha["r2"] == pytest.approx(r2_esperado, abs=5e-4)


@pytest.mark.parametrize("horizonte", HORIZONTES)
@pytest.mark.parametrize("braco", BRACOS_DO_MODELO)
def test_metricas_refeitas_com_sklearn_sobre_o_gabarito(
    braco: str, horizonte: int, metricas_novas: pd.DataFrame, previsoes_do_gabarito: pd.DataFrame
) -> None:
    """Independente de `aedes.metricas`: sklearn sobre as previsoes do codigo antigo, na janela."""
    do_gabarito = recortar(previsoes_do_gabarito, braco, horizonte)
    na_janela = recortar_na_janela_de_avaliacao(do_gabarito)
    assert len(na_janela) == QUANTIDADE_DE_SEMANAS_AVALIADAS

    mae_refeito = mean_absolute_error(na_janela["real"], na_janela["previsto"])
    r2_refeito = r2_score(na_janela["real"], na_janela["previsto"])
    linha = buscar_metrica(metricas_novas, braco, horizonte)
    assert linha["mae"] == pytest.approx(mae_refeito, abs=TOLERANCIA_DA_METRICA)
    assert linha["r2"] == pytest.approx(r2_refeito, abs=TOLERANCIA_DA_METRICA)


# --------------------------------------------------------------------------- reguas


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_reguas_iguais_as_ancoras_do_codigo_antigo(horizonte: int, metricas_novas: pd.DataFrame) -> None:
    sazonal = buscar_metrica(metricas_novas, BRACO_REGUA_SAZONAL, horizonte)
    persistencia = buscar_metrica(metricas_novas, BRACO_PERSISTENCIA, horizonte)

    assert int(sazonal["n"]) == QUANTIDADE_DE_SEMANAS_AVALIADAS
    assert int(persistencia["n"]) == QUANTIDADE_DE_SEMANAS_AVALIADAS
    assert sazonal["mae"] == pytest.approx(MAE_DA_REGUA_SAZONAL_ANTIGA[horizonte - 1], abs=TOLERANCIA_DA_REGUA)
    assert persistencia["mae"] == pytest.approx(MAE_DA_PERSISTENCIA_ANTIGA[horizonte - 1], abs=TOLERANCIA_DA_REGUA)


def test_reguas_nos_horizontes_1_4_8_12_batem_com_o_readme_da_regua(metricas_novas: pd.DataFrame) -> None:
    """Ancoras de `analises/2026-09-25_regua_regras_simples/README.md`, com 1 casa decimal."""
    sazonal_esperado = {1: 202.1, 4: 213.2, 8: 216.2, 12: 217.8}
    persistencia_esperada = {1: 83.3, 4: 279.0, 8: 531.0, 12: 697.5}
    for horizonte, esperado in sazonal_esperado.items():
        mae = buscar_metrica(metricas_novas, BRACO_REGUA_SAZONAL, horizonte)["mae"]
        assert mae == pytest.approx(esperado, abs=TOLERANCIA_DA_REGUA)
    for horizonte, esperado in persistencia_esperada.items():
        mae = buscar_metrica(metricas_novas, BRACO_PERSISTENCIA, horizonte)["mae"]
        assert mae == pytest.approx(esperado, abs=TOLERANCIA_DA_REGUA)


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_reguas_refeitas_do_zero_a_partir_da_serie_do_gabarito(
    horizonte: int,
    metricas_novas: pd.DataFrame,
    previsoes_do_gabarito: pd.DataFrame,
    serie_de_casos_do_gabarito: pd.Series,
) -> None:
    """Conta com dicionario e laco simples (sem `aedes.metricas`), na grade do braco `referencia`."""
    do_gabarito = recortar(previsoes_do_gabarito, "referencia", horizonte)
    na_janela = recortar_na_janela_de_avaliacao(do_gabarito)
    casos_por_data = serie_de_casos_do_gabarito.to_dict()
    semanas_do_horizonte = pd.Timedelta(weeks=horizonte)
    um_ano = pd.Timedelta(weeks=52)

    erros_do_sazonal: list[float] = []
    erros_da_persistencia: list[float] = []
    for data_alvo in na_janela["data_alvo"]:
        caso_real = casos_por_data[data_alvo]
        caso_do_ano_anterior = casos_por_data.get(data_alvo - um_ano, np.nan)
        caso_da_origem = casos_por_data.get(data_alvo - semanas_do_horizonte, np.nan)
        if not np.isnan(caso_do_ano_anterior):
            erros_do_sazonal.append(abs(caso_real - caso_do_ano_anterior))
        if not np.isnan(caso_da_origem):
            erros_da_persistencia.append(abs(caso_real - caso_da_origem))

    sazonal = buscar_metrica(metricas_novas, BRACO_REGUA_SAZONAL, horizonte)
    persistencia = buscar_metrica(metricas_novas, BRACO_PERSISTENCIA, horizonte)
    assert int(sazonal["n"]) == len(erros_do_sazonal)
    assert int(persistencia["n"]) == len(erros_da_persistencia)
    assert sazonal["mae"] == pytest.approx(float(np.mean(erros_do_sazonal)), abs=TOLERANCIA_DA_METRICA)
    assert persistencia["mae"] == pytest.approx(float(np.mean(erros_da_persistencia)), abs=TOLERANCIA_DA_METRICA)
