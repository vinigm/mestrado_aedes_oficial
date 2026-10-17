"""Testes do corte temporal (`aedes.corte_temporal`): bordas sinteticas e o gabarito real.

Regra sob teste (copiada de `modelagem_aedes/motor/corte_temporal.py:61-65`):
a linha de origem `s` entra no treino se `s + h semanas <= t`, onde `t` e a
data de origem do teste. Ou seja: a linha cuja resposta cai em `t` ENTRA; a
que cai em `t + 1 semana` NAO.

Parte 1 (sintetica): bordas, buracos na matriz, vazio, erros.
Parte 2 (gabarito): as 12 matrizes do codigo antigo, primeira origem com 104
linhas validas e todas as origens do walk-forward.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
)
from aedes.corte_temporal import selecionar_treino_ja_respondido

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_PREVISOES_DE_REFERENCIA = PASTA_DO_GABARITO / "previsoes_referencia.csv"

PRIMEIRO_DOMINGO_SINTETICO = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)
COLUNA_DE_POSICAO = "posicao_sintetica"
HORIZONTES = CONFIGURACAO_AVALIACAO.horizontes
TREINO_MINIMO = CONFIGURACAO_AVALIACAO.treino_minimo_em_semanas


def montar_matriz_sintetica(
    posicoes_das_semanas: list[int], horizonte: int
) -> pd.DataFrame:
    """Matriz minima: so as colunas de data e uma coluna que guarda a posicao da semana.

    A semana de posicao `p` e o domingo `PRIMEIRO_DOMINGO_SINTETICO + p semanas`.
    Passar uma lista com buracos simula as semanas descartadas pelo `dropna`.
    """
    datas_de_origem = []
    for posicao in posicoes_das_semanas:
        datas_de_origem.append(PRIMEIRO_DOMINGO_SINTETICO + posicao * UMA_SEMANA)
    matriz = pd.DataFrame(
        {
            COLUNA_DATA_DE_ORIGEM: pd.to_datetime(datas_de_origem),
            COLUNA_DATA_ALVO: pd.to_datetime(datas_de_origem) + horizonte * UMA_SEMANA,
            COLUNA_DE_POSICAO: posicoes_das_semanas,
        }
    )
    return matriz


def data_da_posicao(posicao: int) -> pd.Timestamp:
    """Domingo da semana de posicao `posicao` na grade sintetica."""
    return PRIMEIRO_DOMINGO_SINTETICO + posicao * UMA_SEMANA


# ---------------------------------------------------------------------------
# Parte 1: sinteticos
# ---------------------------------------------------------------------------


def test_linha_cuja_resposta_cai_exatamente_em_t_entra_e_a_da_semana_seguinte_nao() -> None:
    """s + h == t entra; s + h == t + 1 semana nao entra (h = 3, t = semana 10)."""
    horizonte = 3
    matriz = montar_matriz_sintetica(list(range(0, 21)), horizonte)
    origem_do_teste = data_da_posicao(10)

    treino = selecionar_treino_ja_respondido(matriz, origem_do_teste, horizonte)

    posicoes_do_treino = treino[COLUNA_DE_POSICAO].tolist()
    assert posicoes_do_treino == list(range(0, 8))
    assert 7 in posicoes_do_treino
    assert 8 not in posicoes_do_treino


def test_borda_exata_com_h_igual_a_1() -> None:
    """h = 1: a linha da semana anterior a t entra; a da propria semana t nao."""
    matriz = montar_matriz_sintetica(list(range(0, 11)), 1)

    treino = selecionar_treino_ja_respondido(matriz, data_da_posicao(5), 1)

    assert treino[COLUNA_DE_POSICAO].tolist() == [0, 1, 2, 3, 4]


def test_borda_exata_com_h_igual_a_12() -> None:
    """h = 12: a linha 12 semanas antes de t entra; a 11 semanas antes nao."""
    matriz = montar_matriz_sintetica(list(range(0, 41)), 12)

    treino = selecionar_treino_ja_respondido(matriz, data_da_posicao(30), 12)

    posicoes_do_treino = treino[COLUNA_DE_POSICAO].tolist()
    assert posicoes_do_treino[-1] == 18
    assert 19 not in posicoes_do_treino
    assert len(posicoes_do_treino) == 19


def test_nenhuma_linha_de_treino_tem_resposta_depois_de_t() -> None:
    """Para varios t e h: `data_alvo` maxima do treino e <= t, e a proxima linha tem `data_alvo` > t."""
    for horizonte in (1, 4, 12):
        matriz = montar_matriz_sintetica(list(range(0, 60)), horizonte)
        for posicao_do_teste in range(5, 60, 7):
            origem_do_teste = data_da_posicao(posicao_do_teste)
            treino = selecionar_treino_ja_respondido(matriz, origem_do_teste, horizonte)
            if treino.empty:
                continue
            assert treino[COLUNA_DATA_ALVO].max() <= origem_do_teste
            linhas_fora_do_treino = matriz.loc[~matriz.index.isin(treino.index)]
            assert (linhas_fora_do_treino[COLUNA_DATA_ALVO] > origem_do_teste).all()


def test_o_corte_e_por_data_e_nao_por_posicao_quando_a_matriz_tem_buraco() -> None:
    """Com buraco nas ultimas h semanas, recuar h POSICOES erraria; por data acerta.

    Semanas 11, 12 e 13 foram descartadas (como a enchente de 2024). Para
    t = semana 15 e h = 3, entram as semanas com s + 3 <= 15, ou seja s <= 12:
    de 0 a 10 (11 e 12 nao existem). A forma curta `iloc[:pos(t) - h + 1]`
    cortaria uma linha a mais (a semana 10).
    """
    horizonte = 3
    posicoes_validas = list(range(0, 11)) + list(range(14, 21))
    matriz = montar_matriz_sintetica(posicoes_validas, horizonte)

    treino = selecionar_treino_ja_respondido(matriz, data_da_posicao(15), horizonte)
    assert treino[COLUNA_DE_POSICAO].tolist() == list(range(0, 11))

    posicao_de_t_na_matriz = posicoes_validas.index(15)
    corte_por_posicao = matriz.iloc[: posicao_de_t_na_matriz - horizonte + 1]
    assert corte_por_posicao[COLUNA_DE_POSICAO].tolist() == list(range(0, 10))
    assert len(corte_por_posicao) < len(treino)


def test_matriz_vazia_devolve_recorte_vazio_com_as_mesmas_colunas() -> None:
    """Matriz sem linhas: treino vazio, mesmas colunas."""
    matriz_vazia = montar_matriz_sintetica([], 4)

    treino = selecionar_treino_ja_respondido(matriz_vazia, data_da_posicao(10), 4)

    assert treino.empty
    assert list(treino.columns) == list(matriz_vazia.columns)


def test_t_anterior_a_todas_as_respostas_devolve_treino_vazio() -> None:
    """Se nenhuma resposta aconteceu ainda, nada entra no treino."""
    matriz = montar_matriz_sintetica(list(range(10, 20)), 4)

    treino = selecionar_treino_ja_respondido(matriz, data_da_posicao(12), 4)

    assert treino.empty


def test_uma_unica_linha() -> None:
    """Matriz de uma linha: entra se a resposta cai em t ou antes, nao entra se cai depois."""
    matriz = montar_matriz_sintetica([5], 2)

    entra_em_t = selecionar_treino_ja_respondido(matriz, data_da_posicao(7), 2)
    nao_entra_antes = selecionar_treino_ja_respondido(matriz, data_da_posicao(6), 2)

    assert entra_em_t[COLUNA_DE_POSICAO].tolist() == [5]
    assert nao_entra_antes.empty


def test_indice_original_e_preservado_no_recorte() -> None:
    """O recorte mantem o indice da matriz (recorte por `.loc`), inclusive se nao for sequencial."""
    matriz = montar_matriz_sintetica(list(range(0, 10)), 2)
    matriz.index = pd.Index([100, 90, 80, 70, 60, 50, 40, 30, 20, 10])

    treino = selecionar_treino_ja_respondido(matriz, data_da_posicao(5), 2)

    assert treino.index.tolist() == [100, 90, 80, 70]
    assert treino[COLUNA_DE_POSICAO].tolist() == [0, 1, 2, 3]


def test_a_matriz_de_entrada_nao_e_modificada() -> None:
    """Funcao pura: a matriz recebida fica igual depois da chamada."""
    matriz = montar_matriz_sintetica(list(range(0, 15)), 3)
    copia_antes = matriz.copy()

    selecionar_treino_ja_respondido(matriz, data_da_posicao(9), 3)

    pd.testing.assert_frame_equal(matriz, copia_antes, check_exact=True)


def test_nao_le_a_coluna_data_alvo() -> None:
    """A regra usa `data_origem + h`: uma matriz sem `data_alvo` funciona igual."""
    matriz = montar_matriz_sintetica(list(range(0, 15)), 3)
    matriz_sem_data_alvo = matriz.drop(columns=[COLUNA_DATA_ALVO])

    com_data_alvo = selecionar_treino_ja_respondido(matriz, data_da_posicao(9), 3)
    sem_data_alvo = selecionar_treino_ja_respondido(matriz_sem_data_alvo, data_da_posicao(9), 3)

    assert com_data_alvo.index.tolist() == sem_data_alvo.index.tolist()


def test_aceita_timestamp_e_datetime64_como_data_de_origem() -> None:
    """O codigo antigo passava `numpy.datetime64`; as duas formas dao o mesmo treino."""
    matriz = montar_matriz_sintetica(list(range(0, 20)), 4)
    origem_como_timestamp = data_da_posicao(12)
    origem_como_numpy = np.datetime64(origem_como_timestamp)

    com_timestamp = selecionar_treino_ja_respondido(matriz, origem_como_timestamp, 4)
    com_numpy = selecionar_treino_ja_respondido(matriz, origem_como_numpy, 4)

    assert com_timestamp.index.tolist() == com_numpy.index.tolist()
    assert len(com_timestamp) == 9


@pytest.mark.parametrize("horizonte_invalido", [0, -1, 1.5, True, None, "3"])
def test_horizonte_invalido_levanta_erro(horizonte_invalido: object) -> None:
    """Horizonte tem de ser inteiro >= 1 (bool nao conta)."""
    matriz = montar_matriz_sintetica(list(range(0, 10)), 2)
    with pytest.raises(ValueError, match="horizonte"):
        selecionar_treino_ja_respondido(matriz, data_da_posicao(5), horizonte_invalido)


def test_coluna_data_origem_ausente_levanta_keyerror() -> None:
    """Sem `data_origem` a regra nao pode ser aplicada."""
    matriz = montar_matriz_sintetica(list(range(0, 10)), 2)
    matriz_sem_origem = matriz.drop(columns=[COLUNA_DATA_DE_ORIGEM])
    with pytest.raises(KeyError, match=COLUNA_DATA_DE_ORIGEM):
        selecionar_treino_ja_respondido(matriz_sem_origem, data_da_posicao(5), 2)


def test_data_de_origem_do_teste_ausente_levanta_erro() -> None:
    """NaT como data do teste e erro explicito (nao treino vazio em silencio)."""
    matriz = montar_matriz_sintetica(list(range(0, 10)), 2)
    with pytest.raises(ValueError, match="NaT"):
        selecionar_treino_ja_respondido(matriz, pd.NaT, 2)


# ---------------------------------------------------------------------------
# Parte 2: gabarito do codigo antigo
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def matrizes_do_gabarito() -> dict[int, pd.DataFrame]:
    """As 12 matrizes do codigo antigo (CSV de referencia), indexadas pelo horizonte."""
    matrizes: dict[int, pd.DataFrame] = {}
    for horizonte in HORIZONTES:
        caminho = PASTA_DO_GABARITO / f"matriz_h{horizonte:02d}.csv"
        matrizes[horizonte] = pd.read_csv(
            caminho, parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO]
        )
    return matrizes


def contar_linhas_respondidas_por_forca_bruta(
    matriz: pd.DataFrame, origem_do_teste: pd.Timestamp, horizonte: int
) -> int:
    """Conta, linha a linha em Python puro, quantas tem origem + h semanas <= t."""
    quantidade = 0
    for data_de_origem in matriz[COLUNA_DATA_DE_ORIGEM]:
        data_da_resposta = data_de_origem + horizonte * UMA_SEMANA
        if data_da_resposta <= origem_do_teste:
            quantidade += 1
    return quantidade


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_primeira_origem_tem_104_semanas_validas_antes_e_treino_de_105_menos_h(
    horizonte: int, matrizes_do_gabarito: dict[int, pd.DataFrame]
) -> None:
    """A primeira origem de teste e a 105a linha valida; o treino tem 105 - h linhas.

    Antes dela ha exatamente 104 linhas validas (o treino minimo), contiguas
    desde 18/03/2018; as `h - 1` mais recentes ainda nao tem resposta em t.
    """
    matriz = matrizes_do_gabarito[horizonte]
    primeira_origem_de_teste = matriz[COLUNA_DATA_DE_ORIGEM].iloc[TREINO_MINIMO]

    linhas_antes = matriz[matriz[COLUNA_DATA_DE_ORIGEM] < primeira_origem_de_teste]
    assert len(linhas_antes) == TREINO_MINIMO

    treino = selecionar_treino_ja_respondido(matriz, primeira_origem_de_teste, horizonte)

    assert len(treino) == TREINO_MINIMO + 1 - horizonte
    assert len(treino) == contar_linhas_respondidas_por_forca_bruta(
        matriz, primeira_origem_de_teste, horizonte
    )
    assert treino[COLUNA_DATA_ALVO].max() <= primeira_origem_de_teste


def test_h1_na_primeira_origem_o_treino_tem_exatamente_104_linhas(
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """h = 1: todas as 104 linhas anteriores a primeira origem ja tem resposta em t."""
    matriz = matrizes_do_gabarito[1]
    primeira_origem_de_teste = matriz[COLUNA_DATA_DE_ORIGEM].iloc[TREINO_MINIMO]

    treino = selecionar_treino_ja_respondido(matriz, primeira_origem_de_teste, 1)

    assert len(treino) == TREINO_MINIMO


def test_h12_na_primeira_origem_o_treino_tem_93_linhas(
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """h = 12: das 104 linhas anteriores, so 93 ja tem resposta em t."""
    matriz = matrizes_do_gabarito[12]
    primeira_origem_de_teste = matriz[COLUNA_DATA_DE_ORIGEM].iloc[TREINO_MINIMO]

    treino = selecionar_treino_ja_respondido(matriz, primeira_origem_de_teste, 12)

    assert len(treino) == 93


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_em_todas_as_origens_nenhuma_resposta_do_treino_e_posterior_a_t(
    horizonte: int, matrizes_do_gabarito: dict[int, pd.DataFrame]
) -> None:
    """Para cada origem do walk-forward: treino so com `data_alvo <= t`, maximal e igual a forca bruta."""
    matriz = matrizes_do_gabarito[horizonte]
    quantidade_anterior = 0

    for posicao_do_teste in range(TREINO_MINIMO, len(matriz)):
        origem_do_teste = matriz[COLUNA_DATA_DE_ORIGEM].iloc[posicao_do_teste]
        treino = selecionar_treino_ja_respondido(matriz, origem_do_teste, horizonte)

        assert (treino[COLUNA_DATA_ALVO] <= origem_do_teste).all()
        linhas_fora = matriz.loc[~matriz.index.isin(treino.index)]
        assert (linhas_fora[COLUNA_DATA_ALVO] > origem_do_teste).all()

        assert len(treino) == contar_linhas_respondidas_por_forca_bruta(
            matriz, origem_do_teste, horizonte
        )
        # O treino so cresce a medida que t avanca.
        assert len(treino) >= quantidade_anterior
        quantidade_anterior = len(treino)


@pytest.mark.parametrize("horizonte", HORIZONTES)
def test_a_primeira_origem_bate_com_a_primeira_previsao_salva(
    horizonte: int, matrizes_do_gabarito: dict[int, pd.DataFrame]
) -> None:
    """A 105a linha da matriz e a primeira previsao salva da bateria de 23/09 (os dois bracos).

    Tambem confere o numero de previsoes: linhas da matriz menos 104.
    """
    previsoes = pd.read_csv(CAMINHO_PREVISOES_DE_REFERENCIA, parse_dates=[COLUNA_DATA_ALVO])
    matriz = matrizes_do_gabarito[horizonte]
    primeira_data_alvo_de_teste = matriz[COLUNA_DATA_ALVO].iloc[TREINO_MINIMO]

    for nome_do_braco in previsoes["braco"].unique():
        do_braco = previsoes[(previsoes["braco"] == nome_do_braco) & (previsoes["h"] == horizonte)]
        assert do_braco[COLUNA_DATA_ALVO].min() == primeira_data_alvo_de_teste
        assert len(do_braco) == len(matriz) - TREINO_MINIMO


def test_em_h12_o_corte_por_data_difere_do_corte_por_posicao_no_gabarito(
    matrizes_do_gabarito: dict[int, pd.DataFrame],
) -> None:
    """Prova no dado real que o corte por posicao erraria: ha origens em que as duas formas divergem.

    Se nunca divergissem, a regra "por data" seria so estilo; o buraco da
    enchente de 2024 faz recuar 12 posicoes valer mais de 12 semanas.
    """
    horizonte = 12
    matriz = matrizes_do_gabarito[horizonte]
    origens_em_que_divergem = 0

    for posicao_do_teste in range(TREINO_MINIMO, len(matriz)):
        origem_do_teste = matriz[COLUNA_DATA_DE_ORIGEM].iloc[posicao_do_teste]
        treino_por_data = selecionar_treino_ja_respondido(matriz, origem_do_teste, horizonte)
        treino_por_posicao = matriz.iloc[: posicao_do_teste - horizonte + 1]
        if len(treino_por_data) != len(treino_por_posicao):
            origens_em_que_divergem += 1

    assert origens_em_que_divergem > 0
