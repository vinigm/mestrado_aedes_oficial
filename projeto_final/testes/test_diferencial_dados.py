"""Teste diferencial do ciclo 1: o corte de maturidade novo contra o gabarito do codigo antigo.

Entrada: `dados/tabela_final.csv` (hash e esquema validados por
`aedes.dados.montar_tabela_a_partir_dos_bytes`).
Gabarito: `testes/referencia_antiga/serie_casos_apos_corte.csv`, gerado pelo
codigo antigo (`surto.aplicar_corte_maturidade`) por
`analises/2026-10-12_referencia_para_o_pacote/gerar_referencia.py`.
Tolerancia: nenhuma. Igualdade exata, inclusive das posicoes de NaN.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import CONFIGURACAO_DADOS
from aedes.dados import (
    aplicar_corte_de_maturidade,
    montar_tabela_a_partir_dos_bytes,
    obter_ultima_semana_com_caso,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
CAMINHO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga" / "serie_casos_apos_corte.csv"

COLUNA_DE_DATA = CONFIGURACAO_DADOS.coluna_de_data
COLUNA_DE_CASOS = CONFIGURACAO_DADOS.coluna_de_casos

SEMANAS_COM_CASO_ANTES_DO_CORTE = 428
SEMANAS_COM_CASO_DEPOIS_DO_CORTE = 416
SEMANAS_APAGADAS = 12
PRIMEIRA_SEMANA_COM_CASO = pd.Timestamp("2018-02-18")
ULTIMA_SEMANA_COM_CASO = pd.Timestamp("2026-04-26")
ULTIMA_SEMANA_MANTIDA = pd.Timestamp("2026-02-01")
PRIMEIRA_SEMANA_APAGADA = pd.Timestamp("2026-02-08")


@pytest.fixture(scope="module")
def tabela_crua() -> pd.DataFrame:
    """A tabela certificada, lida dos bytes e validada (hash e esquema)."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    return montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def tabela_cortada(tabela_crua: pd.DataFrame) -> pd.DataFrame:
    """A tabela depois do corte de maturidade de 12 semanas."""
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def gabarito() -> pd.DataFrame:
    """Serie de casos depois do corte, como o codigo antigo a entrega ao modelo."""
    return pd.read_csv(CAMINHO_GABARITO, parse_dates=[COLUNA_DE_DATA])


def test_ancoras_da_tabela_crua(tabela_crua: pd.DataFrame) -> None:
    """725 x 36, 428 semanas com caso, de 18/02/2018 a 26/04/2026, grade desde 23/09/2012."""
    assert tabela_crua.shape == (725, 36)
    assert tabela_crua[COLUNA_DE_DATA].iloc[0] == pd.Timestamp("2012-09-23")

    casos_nao_nulos = tabela_crua[COLUNA_DE_CASOS].notna().sum()
    assert casos_nao_nulos == SEMANAS_COM_CASO_ANTES_DO_CORTE

    semanas_com_caso = tabela_crua.dropna(subset=[COLUNA_DE_CASOS])
    primeira_com_caso = semanas_com_caso[COLUNA_DE_DATA].min()
    assert primeira_com_caso == PRIMEIRA_SEMANA_COM_CASO

    ultima_com_caso = obter_ultima_semana_com_caso(tabela_crua, CONFIGURACAO_DADOS)
    assert ultima_com_caso == ULTIMA_SEMANA_COM_CASO


def test_mesmas_datas_do_gabarito(
    tabela_cortada: pd.DataFrame, gabarito: pd.DataFrame
) -> None:
    """As 725 datas do corte novo sao, na mesma ordem, as do gabarito."""
    assert len(gabarito) == 725
    datas_novas = tabela_cortada[COLUNA_DE_DATA].to_numpy()
    datas_do_gabarito = gabarito[COLUNA_DE_DATA].to_numpy()
    np.testing.assert_array_equal(datas_novas, datas_do_gabarito)


def test_mesmos_valores_do_gabarito_com_nan_nas_mesmas_posicoes(
    tabela_cortada: pd.DataFrame, gabarito: pd.DataFrame
) -> None:
    """Igualdade exata dos casos, sem tolerancia; NaN exatamente onde o gabarito tem NaN."""
    casos_novos = tabela_cortada[COLUNA_DE_CASOS].to_numpy(dtype="float64")
    casos_do_gabarito = gabarito[COLUNA_DE_CASOS].to_numpy(dtype="float64")

    posicoes_nan_novas = np.isnan(casos_novos)
    posicoes_nan_do_gabarito = np.isnan(casos_do_gabarito)
    np.testing.assert_array_equal(posicoes_nan_novas, posicoes_nan_do_gabarito)

    np.testing.assert_array_equal(casos_novos, casos_do_gabarito)


def test_ultima_semana_mantida_e_416_nao_nulos(tabela_cortada: pd.DataFrame) -> None:
    """Mantem 01/02/2026 como ultima semana com caso; 416 semanas nao nulas depois do corte."""
    ultima_mantida = obter_ultima_semana_com_caso(tabela_cortada, CONFIGURACAO_DADOS)
    assert ultima_mantida == ULTIMA_SEMANA_MANTIDA

    casos_nao_nulos = tabela_cortada[COLUNA_DE_CASOS].notna().sum()
    assert casos_nao_nulos == SEMANAS_COM_CASO_DEPOIS_DO_CORTE


def test_as_12_semanas_apagadas_sao_de_08_02_a_26_04_de_2026(
    tabela_crua: pd.DataFrame, tabela_cortada: pd.DataFrame
) -> None:
    """Foram apagadas exatamente 12 semanas com caso, de 08/02/2026 a 26/04/2026, como NaN (nunca 0)."""
    tinha_caso_antes = tabela_crua[COLUNA_DE_CASOS].notna()
    ficou_sem_caso = tabela_cortada[COLUNA_DE_CASOS].isna()
    mascara_apagadas = tinha_caso_antes & ficou_sem_caso

    datas_apagadas = tabela_crua.loc[mascara_apagadas, COLUNA_DE_DATA]
    assert len(datas_apagadas) == SEMANAS_APAGADAS
    assert datas_apagadas.min() == PRIMEIRA_SEMANA_APAGADA
    assert datas_apagadas.max() == ULTIMA_SEMANA_COM_CASO

    nenhuma_semana_nova_com_caso = not (
        tabela_crua[COLUNA_DE_CASOS].isna() & tabela_cortada[COLUNA_DE_CASOS].notna()
    ).any()
    assert nenhuma_semana_nova_com_caso

    casos_mantidos_antes = tabela_crua.loc[tabela_cortada[COLUNA_DE_CASOS].notna(), COLUNA_DE_CASOS]
    casos_mantidos_depois = tabela_cortada.loc[tabela_cortada[COLUNA_DE_CASOS].notna(), COLUNA_DE_CASOS]
    np.testing.assert_array_equal(casos_mantidos_antes.to_numpy(), casos_mantidos_depois.to_numpy())


def test_demais_colunas_nao_mudaram(
    tabela_crua: pd.DataFrame, tabela_cortada: pd.DataFrame
) -> None:
    """Todas as colunas, menos a de casos, saem identicas; ordem, indice e dtypes iguais."""
    assert list(tabela_cortada.columns) == list(tabela_crua.columns)
    pd.testing.assert_index_equal(tabela_cortada.index, tabela_crua.index)

    colunas_sem_casos = [nome for nome in tabela_crua.columns if nome != COLUNA_DE_CASOS]
    assert len(colunas_sem_casos) == 35
    pd.testing.assert_frame_equal(
        tabela_cortada[colunas_sem_casos],
        tabela_crua[colunas_sem_casos],
        check_dtype=True,
        check_exact=True,
    )


def test_tabela_crua_nao_foi_modificada_pelo_corte(tabela_crua: pd.DataFrame) -> None:
    """Depois de cortar, a tabela de entrada ainda tem os 428 casos e a ultima semana de 26/04/2026."""
    casos_antes = tabela_crua[COLUNA_DE_CASOS].copy()

    aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)

    pd.testing.assert_series_equal(tabela_crua[COLUNA_DE_CASOS], casos_antes)
    assert tabela_crua[COLUNA_DE_CASOS].notna().sum() == SEMANAS_COM_CASO_ANTES_DO_CORTE
