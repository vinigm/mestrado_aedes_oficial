"""Teste diferencial do ciclo 2 (parte 1): as 12 matrizes novas contra o gabarito do codigo antigo.

Entrada: `dados/tabela_final.csv` (hash e esquema validados por
`aedes.dados.montar_tabela_a_partir_dos_bytes`), depois do corte de maturidade
de 12 semanas.
Gabarito: `testes/referencia_antiga/matriz_h01.csv ... matriz_h12.csv`, gerado
pelo codigo antigo (`harness.montar_features_do_braco` + a preparacao de
`harness.rodar_walk_forward`) por
`analises/2026-10-12_referencia_para_o_pacote/gerar_referencia.py`, com o
clima congelado. Nenhum modelo foi treinado para gerar o gabarito.

O que tem de ser identico, em cada um dos 12 horizontes:
    - as mesmas linhas, na mesma ordem (`data_origem` e `data_alvo` exatas);
    - as mesmas 25 colunas, na mesma ordem (data_origem, data_alvo, as 22
      variaveis do modelo e y_h);
    - os mesmos valores, com tolerancia absoluta de 1e-12 (o gabarito passou
      por um CSV, que guarda os numeros em texto);
    - ausentes nas mesmas posicoes (nenhuma: a matriz sai sem ausentes).
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.variaveis import montar_matriz_do_horizonte

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_CLIMA_CONGELADO = PASTA_DO_GABARITO / "colunas_clima_congeladas.txt"

HORIZONTES = CONFIGURACAO_AVALIACAO.horizontes
TOLERANCIA_ABSOLUTA = 1e-12
TOLERANCIA_RELATIVA = 0.0

# Ancoras de contagem (tarefa do ciclo 2 e gabarito): 399 linhas em h=1,
# uma a menos a cada horizonte, 388 em h=12.
LINHAS_VALIDAS_EM_H1 = 399
LINHAS_VALIDAS_EM_H12 = 388
PRIMEIRA_DATA_DE_ORIGEM = pd.Timestamp("2018-03-18")
QUANTIDADE_DE_COLUNAS_DA_MATRIZ = 25
QUANTIDADE_DE_VARIAVEIS_DO_MODELO = 22


def caminho_da_matriz_do_gabarito(horizonte: int) -> pathlib.Path:
    """Caminho do CSV do gabarito de um horizonte (`matriz_h01.csv` ... `matriz_h12.csv`)."""
    return PASTA_DO_GABARITO / f"matriz_h{horizonte:02d}.csv"


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def matrizes_novas(tabela_cortada: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """As 12 matrizes montadas pelo pacote novo, indexadas pelo horizonte."""
    matrizes: dict[int, pd.DataFrame] = {}
    for horizonte in HORIZONTES:
        matrizes[horizonte] = montar_matriz_do_horizonte(
            tabela_cortada, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
        )
    return matrizes


@pytest.fixture(scope="module")
def matrizes_do_gabarito() -> dict[int, pd.DataFrame]:
    """As 12 matrizes do codigo antigo, lidas dos CSVs de referencia."""
    matrizes: dict[int, pd.DataFrame] = {}
    for horizonte in HORIZONTES:
        matrizes[horizonte] = pd.read_csv(
            caminho_da_matriz_do_gabarito(horizonte),
            parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
        )
    return matrizes


def test_o_gabarito_tem_as_ancoras_esperadas(
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """Sanidade do proprio gabarito: 399 linhas em h=1, 388 em h=12, 25 colunas, sem ausentes."""
    assert len(matrizes_do_gabarito[1]) == LINHAS_VALIDAS_EM_H1
    assert len(matrizes_do_gabarito[12]) == LINHAS_VALIDAS_EM_H12
    for horizonte in HORIZONTES:
        matriz = matrizes_do_gabarito[horizonte]
        assert matriz.shape[1] == QUANTIDADE_DE_COLUNAS_DA_MATRIZ
        assert matriz.isna().sum().sum() == 0


def test_a_matriz_nova_tem_as_ancoras_de_linhas(
    matrizes_novas: dict[int, pd.DataFrame],
) -> None:
    """399 linhas validas em h=1 e 388 em h=12; a primeira origem e 18/03/2018."""
    assert len(matrizes_novas[1]) == LINHAS_VALIDAS_EM_H1
    assert len(matrizes_novas[12]) == LINHAS_VALIDAS_EM_H12
    for horizonte in HORIZONTES:
        primeira_origem = matrizes_novas[horizonte][COLUNA_DATA_DE_ORIGEM].iloc[0]
        assert primeira_origem == PRIMEIRA_DATA_DE_ORIGEM


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_mesmas_linhas_e_datas_do_gabarito(
    horizonte: int,
    matrizes_novas: dict[int, pd.DataFrame],
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """Mesmo numero de linhas e mesmas `data_origem` e `data_alvo`, na mesma ordem."""
    nova = matrizes_novas[horizonte]
    gabarito = matrizes_do_gabarito[horizonte]

    assert len(nova) == len(gabarito)
    np.testing.assert_array_equal(
        nova[COLUNA_DATA_DE_ORIGEM].to_numpy(),
        gabarito[COLUNA_DATA_DE_ORIGEM].to_numpy(),
    )
    np.testing.assert_array_equal(
        nova[COLUNA_DATA_ALVO].to_numpy(),
        gabarito[COLUNA_DATA_ALVO].to_numpy(),
    )


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_mesmas_colunas_na_mesma_ordem(
    horizonte: int,
    matrizes_novas: dict[int, pd.DataFrame],
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """As 25 colunas, na ordem do modelo: data_origem, data_alvo, 22 variaveis, y_h."""
    colunas_novas = list(matrizes_novas[horizonte].columns)
    colunas_do_gabarito = list(matrizes_do_gabarito[horizonte].columns)

    assert colunas_novas == colunas_do_gabarito
    assert colunas_novas[0] == COLUNA_DATA_DE_ORIGEM
    assert colunas_novas[1] == COLUNA_DATA_ALVO
    assert colunas_novas[-1] == COLUNA_DO_ALVO
    variaveis_do_modelo = colunas_novas[2:-1]
    assert len(variaveis_do_modelo) == QUANTIDADE_DE_VARIAVEIS_DO_MODELO
    assert tuple(variaveis_do_modelo) == CONFIGURACAO_VARIAVEIS.nomes_das_variaveis


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_mesmos_valores_com_tolerancia_de_1e_12(
    horizonte: int,
    matrizes_novas: dict[int, pd.DataFrame],
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """Valores das 22 variaveis e de y_h iguais ao gabarito (atol 1e-12), NaN nas mesmas posicoes."""
    nova = matrizes_novas[horizonte]
    gabarito = matrizes_do_gabarito[horizonte]
    colunas_de_valores = list(gabarito.columns[2:])

    valores_novos = nova[colunas_de_valores].to_numpy(dtype="float64")
    valores_do_gabarito = gabarito[colunas_de_valores].to_numpy(dtype="float64")

    np.testing.assert_array_equal(np.isnan(valores_novos), np.isnan(valores_do_gabarito))
    np.testing.assert_allclose(
        valores_novos,
        valores_do_gabarito,
        rtol=TOLERANCIA_RELATIVA,
        atol=TOLERANCIA_ABSOLUTA,
        equal_nan=True,
    )


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_dtypes_iguais_aos_do_gabarito(
    horizonte: int,
    matrizes_novas: dict[int, pd.DataFrame],
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """Datas como data e todo o resto em float64, como no gabarito lido do CSV."""
    nova = matrizes_novas[horizonte]
    gabarito = matrizes_do_gabarito[horizonte]
    assert list(nova.dtypes.astype(str)) == list(gabarito.dtypes.astype(str))


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_matriz_sem_ausentes_e_indice_renumerado(
    horizonte: int, matrizes_novas: dict[int, pd.DataFrame]
) -> None:
    """Sem nenhum ausente, indice 0..n-1 e datas estritamente crescentes."""
    matriz = matrizes_novas[horizonte]
    assert matriz.isna().sum().sum() == 0
    assert matriz.index.tolist() == list(range(len(matriz)))
    assert matriz[COLUNA_DATA_DE_ORIGEM].is_monotonic_increasing
    assert matriz[COLUNA_DATA_DE_ORIGEM].is_unique


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_data_alvo_e_a_origem_mais_h_semanas(
    horizonte: int, matrizes_novas: dict[int, pd.DataFrame]
) -> None:
    """`data_alvo = data_origem + h semanas` em toda linha."""
    matriz = matrizes_novas[horizonte]
    diferenca = matriz[COLUNA_DATA_ALVO] - matriz[COLUNA_DATA_DE_ORIGEM]
    assert (diferenca == pd.Timedelta(weeks=horizonte)).all()


def test_y_h_e_o_caso_da_semana_alvo_na_serie_apos_o_corte(
    tabela_cortada: pd.DataFrame, matrizes_novas: dict[int, pd.DataFrame]
) -> None:
    """`y_h` de cada linha e o caso da semana `data_alvo` da propria tabela cortada (h=1 e h=12)."""
    casos_por_data = tabela_cortada.set_index(CONFIGURACAO_DADOS.coluna_de_data)[
        CONFIGURACAO_DADOS.coluna_de_casos
    ]
    for horizonte in (1, 12):
        matriz = matrizes_novas[horizonte]
        casos_na_data_alvo = casos_por_data.reindex(matriz[COLUNA_DATA_ALVO]).to_numpy()
        np.testing.assert_array_equal(matriz[COLUNA_DO_ALVO].to_numpy(), casos_na_data_alvo)


def test_nenhum_alvo_cai_nas_semanas_apagadas_pelo_corte(
    matrizes_novas: dict[int, pd.DataFrame],
) -> None:
    """A ultima `data_alvo` com `y_h` e 01/02/2026: depois dela o corte apagou os casos."""
    ultima_semana_mantida = pd.Timestamp("2026-02-01")
    for horizonte in HORIZONTES:
        ultima_data_alvo = matrizes_novas[horizonte][COLUNA_DATA_ALVO].max()
        assert ultima_data_alvo == ultima_semana_mantida


def test_clima_da_configuracao_e_o_congelado_do_gabarito() -> None:
    """As 6 colunas de clima da configuracao, na ordem, sao as do arquivo congelado."""
    texto = CAMINHO_CLIMA_CONGELADO.read_text(encoding="utf-8")
    nomes_congelados = texto.split()
    nomes_da_configuracao = []
    for variavel_de_clima in CONFIGURACAO_VARIAVEIS.variaveis_de_clima:
        nomes_da_configuracao.append(variavel_de_clima.nome)
    assert nomes_da_configuracao == nomes_congelados
    assert len(nomes_congelados) == 6


def test_a_tabela_de_entrada_nao_foi_modificada(tabela_cortada: pd.DataFrame) -> None:
    """Montar matrizes nao altera a tabela cortada (funcao pura): colunas e casos intactos."""
    copia_antes = tabela_cortada.copy()
    montar_matriz_do_horizonte(tabela_cortada, 6, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    pd.testing.assert_frame_equal(tabela_cortada, copia_antes, check_exact=True)
