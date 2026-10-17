"""Testes de `aedes.walk_forward_com_corte`: o laco com a regra de corte do treino como parametro.

Unidade (matrizes sinteticas):
    - RESPOSTA libera so linhas com `data_alvo <= t`; PERGUNTA libera `data_origem < t`
      e, por isso, deixa entrar linhas de rotulo posterior a `t`;
    - a linha de teste (`s = t`) fica fora nas duas regras (o `<=` seria vazamento do alvo);
    - em h = 1 as duas regras coincidem; o corte e por DATA (matriz com buraco), nunca por posicao;
    - `recortar_matriz_ate_a_data_alvo`: limite inclusivo, indice preservado;
    - entradas invalidas.

Diferencial (matriz real do `completo`, truncada para ficar rapido):
    - RESPOSTA reproduz `executar_walk_forward` bit a bit (h = 1 e h = 12);
    - PERGUNTA em h = 1 reproduz a RESPOSTA bit a bit, e em h = 12 DIFERE (o vazamento existe);
    - recortar a matriz em `data_alvo <= limite` antes do laco da as mesmas previsoes (bit a bit)
      que rodar tudo e filtrar depois (a premissa da E1).
"""

import dataclasses
import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.bracos import montar_matriz_do_braco
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.walk_forward import executar_walk_forward
from aedes.walk_forward_com_corte import (
    RegraDeCorte,
    executar_walk_forward_com_corte,
    recortar_matriz_ate_a_data_alvo,
    selecionar_treino_pela_regra,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"

PRIMEIRA_ORIGEM = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)
TREINO_MINIMO_DO_TESTE = 15

MODELO_PEQUENO = dataclasses.replace(FOLHA_5, nome="histgb_teste", numero_de_iteracoes=20, folha_minima=2)
AVALIACAO_PEQUENA = dataclasses.replace(CONFIGURACAO_AVALIACAO, treino_minimo_em_semanas=TREINO_MINIMO_DO_TESTE)


def montar_matriz_sintetica(
    quantidade_de_linhas: int,
    horizonte: int,
    posicoes_puladas: tuple[int, ...] = (),
) -> pd.DataFrame:
    """Matriz no formato de `montar_matriz_do_horizonte`, com 2 variaveis; buracos apagam linhas.

    O alvo e uma funcao conhecida das variaveis mais um termo da posicao, para o treino ter o que aprender.
    """
    gerador = np.random.default_rng(321)
    posicoes = np.arange(quantidade_de_linhas)
    datas_de_origem = PRIMEIRA_ORIGEM + posicoes * UMA_SEMANA
    variavel_a = gerador.normal(size=quantidade_de_linhas)
    variavel_b = gerador.normal(size=quantidade_de_linhas)
    matriz = pd.DataFrame(
        {
            COLUNA_DATA_DE_ORIGEM: datas_de_origem,
            COLUNA_DATA_ALVO: datas_de_origem + horizonte * UMA_SEMANA,
            "variavel_a": variavel_a,
            "variavel_b": variavel_b,
            COLUNA_DO_ALVO: 3.0 * variavel_a - variavel_b + 0.1 * posicoes,
        }
    )
    if posicoes_puladas:
        matriz = matriz.drop(index=list(posicoes_puladas)).reset_index(drop=True)
    return matriz


def origem_da_posicao(posicao: int) -> pd.Timestamp:
    """Data de origem da linha de posicao `posicao` na matriz sintetica sem buracos."""
    return PRIMEIRA_ORIGEM + posicao * UMA_SEMANA


# ---------------------------------------------------------------------------
# selecionar_treino_pela_regra
# ---------------------------------------------------------------------------


def test_resposta_libera_so_o_que_ja_tinha_resposta_em_t() -> None:
    """h = 3, t = linha 20: entram as linhas 0..17 (resposta em s + 3 <= 20)."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    treino = selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 3, RegraDeCorte.RESPOSTA)
    assert list(treino.index) == list(range(0, 18))
    assert (treino[COLUNA_DATA_ALVO] <= origem_da_posicao(20)).all()


def test_pergunta_libera_as_linhas_anteriores_a_t_e_deixa_entrar_rotulo_do_futuro() -> None:
    """h = 3, t = linha 20: entram 0..19; as linhas 18 e 19 tem `data_alvo` (21 e 22) POSTERIOR a t."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    treino = selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 3, RegraDeCorte.PERGUNTA)
    assert list(treino.index) == list(range(0, 20))
    linhas_com_rotulo_do_futuro = treino.loc[treino[COLUNA_DATA_ALVO] > origem_da_posicao(20)]
    assert list(linhas_com_rotulo_do_futuro.index) == [18, 19]


@pytest.mark.parametrize("regra", [RegraDeCorte.RESPOSTA, RegraDeCorte.PERGUNTA])
def test_a_linha_de_teste_nunca_entra_no_treino(regra: RegraDeCorte) -> None:
    """A origem `t` fica de fora nas duas regras: incluir `s = t` poria o alvo do teste no treino."""
    matriz = montar_matriz_sintetica(30, horizonte=2)
    treino = selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 2, regra)
    assert origem_da_posicao(20) not in set(treino[COLUNA_DATA_DE_ORIGEM])


def test_em_h1_as_duas_regras_liberam_exatamente_as_mesmas_linhas() -> None:
    """Numa grade semanal, `s + 1 semana <= t` equivale a `s < t`."""
    matriz = montar_matriz_sintetica(30, horizonte=1)
    for posicao in (15, 20, 29):
        pela_resposta = selecionar_treino_pela_regra(matriz, origem_da_posicao(posicao), 1, RegraDeCorte.RESPOSTA)
        pela_pergunta = selecionar_treino_pela_regra(matriz, origem_da_posicao(posicao), 1, RegraDeCorte.PERGUNTA)
        assert list(pela_resposta.index) == list(pela_pergunta.index)


def test_o_corte_e_por_data_e_nao_por_posicao_com_buraco_na_matriz() -> None:
    """Linhas 10 e 11 apagadas (como a enchente): a PERGUNTA em t = 20 libera as linhas de data < t, nao 'as 20 primeiras'."""
    matriz = montar_matriz_sintetica(30, horizonte=4, posicoes_puladas=(10, 11))
    data_do_teste = origem_da_posicao(20)
    treino = selecionar_treino_pela_regra(matriz, data_do_teste, 4, RegraDeCorte.PERGUNTA)
    assert (treino[COLUNA_DATA_DE_ORIGEM] < data_do_teste).all()
    quantidade_esperada = int((matriz[COLUNA_DATA_DE_ORIGEM] < data_do_teste).sum())
    assert len(treino) == quantidade_esperada == 18


def test_primeira_origem_da_matriz_sem_linha_anterior_devolve_vazio() -> None:
    """Primeira data da matriz: PERGUNTA (`s < t`) nao libera nada."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    treino = selecionar_treino_pela_regra(matriz, origem_da_posicao(0), 3, RegraDeCorte.PERGUNTA)
    assert len(treino) == 0


def test_a_selecao_nao_modifica_a_matriz() -> None:
    """Funcao pura."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    copia = matriz.copy(deep=True)
    selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 3, RegraDeCorte.PERGUNTA)
    pd.testing.assert_frame_equal(matriz, copia)


def test_regra_que_nao_e_um_enum_e_rejeitada() -> None:
    """Texto no lugar do `RegraDeCorte` levanta ValueError (nao cai em 'qualquer regra desconhecida = resposta')."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    with pytest.raises(ValueError, match="RegraDeCorte"):
        selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 3, "pergunta")  # type: ignore[arg-type]


def test_horizonte_e_data_invalidos_sao_rejeitados_nas_duas_regras() -> None:
    """A validacao do modulo certificado vale tambem para a PERGUNTA."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    for regra in (RegraDeCorte.RESPOSTA, RegraDeCorte.PERGUNTA):
        with pytest.raises(ValueError, match="horizonte"):
            selecionar_treino_pela_regra(matriz, origem_da_posicao(20), 0, regra)
        with pytest.raises(ValueError, match="NaT"):
            selecionar_treino_pela_regra(matriz, pd.NaT, 3, regra)
    sem_a_coluna = matriz.drop(columns=[COLUNA_DATA_DE_ORIGEM])
    with pytest.raises(KeyError):
        selecionar_treino_pela_regra(sem_a_coluna, origem_da_posicao(20), 3, RegraDeCorte.PERGUNTA)


# ---------------------------------------------------------------------------
# recortar_matriz_ate_a_data_alvo
# ---------------------------------------------------------------------------


def test_recorte_ate_a_data_alvo_inclui_o_limite_e_exclui_a_semana_seguinte() -> None:
    """Limite inclusivo: a linha cuja `data_alvo` e exatamente o limite fica; a de uma semana depois sai."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    limite = matriz[COLUNA_DATA_ALVO].iloc[19]
    recorte = recortar_matriz_ate_a_data_alvo(matriz, limite)
    assert len(recorte) == 20
    assert recorte[COLUNA_DATA_ALVO].max() == limite
    assert matriz[COLUNA_DATA_ALVO].iloc[20] > limite


def test_o_recorte_preserva_o_indice_e_nao_modifica_a_matriz() -> None:
    """O indice nao e renumerado e a matriz original fica intacta."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    copia = matriz.copy(deep=True)
    recorte = recortar_matriz_ate_a_data_alvo(matriz, matriz[COLUNA_DATA_ALVO].iloc[9])
    assert list(recorte.index) == list(range(10))
    pd.testing.assert_frame_equal(matriz, copia)


def test_recorte_com_limite_antes_de_tudo_devolve_vazio_e_com_limite_depois_devolve_tudo() -> None:
    """Casos extremos."""
    matriz = montar_matriz_sintetica(30, horizonte=3)
    assert len(recortar_matriz_ate_a_data_alvo(matriz, pd.Timestamp("1999-01-01"))) == 0
    assert len(recortar_matriz_ate_a_data_alvo(matriz, pd.Timestamp("2100-01-01"))) == 30


def test_recorte_sem_a_coluna_data_alvo_e_rejeitado() -> None:
    """KeyError claro."""
    matriz = montar_matriz_sintetica(30, horizonte=3).drop(columns=[COLUNA_DATA_ALVO])
    with pytest.raises(KeyError):
        recortar_matriz_ate_a_data_alvo(matriz, pd.Timestamp("2020-06-01"))


# ---------------------------------------------------------------------------
# executar_walk_forward_com_corte (sintetico)
# ---------------------------------------------------------------------------


def test_o_laco_com_resposta_e_identico_ao_laco_certificado_em_matriz_com_buraco() -> None:
    """Sintetico com buraco, h = 4: mesmas linhas de saida e `previsto` igual bit a bit."""
    matriz = montar_matriz_sintetica(60, horizonte=4, posicoes_puladas=(30, 31, 32))
    certificado = executar_walk_forward(matriz, 4, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    com_corte = executar_walk_forward_com_corte(matriz, 4, MODELO_PEQUENO, AVALIACAO_PEQUENA, RegraDeCorte.RESPOSTA)
    pd.testing.assert_frame_equal(com_corte, certificado, check_exact=True)


def test_o_laco_com_pergunta_usa_o_mesmo_conjunto_de_origens_mas_previsoes_diferentes() -> None:
    """A regra muda o treino, nao as origens: mesmas datas, e o `previsto` difere em h = 4."""
    matriz = montar_matriz_sintetica(60, horizonte=4)
    pela_resposta = executar_walk_forward_com_corte(matriz, 4, MODELO_PEQUENO, AVALIACAO_PEQUENA, RegraDeCorte.RESPOSTA)
    pela_pergunta = executar_walk_forward_com_corte(matriz, 4, MODELO_PEQUENO, AVALIACAO_PEQUENA, RegraDeCorte.PERGUNTA)
    assert list(pela_resposta[COLUNA_DATA_DE_ORIGEM]) == list(pela_pergunta[COLUNA_DATA_DE_ORIGEM])
    assert list(pela_resposta["real"]) == list(pela_pergunta["real"])
    assert not np.array_equal(pela_resposta["previsto"].to_numpy(), pela_pergunta["previsto"].to_numpy())


def test_regra_invalida_no_laco_e_rejeitada() -> None:
    """Validado antes de qualquer treino."""
    matriz = montar_matriz_sintetica(60, horizonte=4)
    with pytest.raises(ValueError, match="RegraDeCorte"):
        executar_walk_forward_com_corte(matriz, 4, MODELO_PEQUENO, AVALIACAO_PEQUENA, "resposta")  # type: ignore[arg-type]


def test_matriz_vazia_depois_do_treino_minimo_devolve_previsoes_vazias_com_as_colunas() -> None:
    """Matriz menor que o treino minimo: nenhuma origem de teste."""
    matriz = montar_matriz_sintetica(TREINO_MINIMO_DO_TESTE, horizonte=2)
    previsoes = executar_walk_forward_com_corte(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA, RegraDeCorte.PERGUNTA)
    assert len(previsoes) == 0
    assert list(previsoes.columns) == ["h", COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, "real", "previsto"]


# ---------------------------------------------------------------------------
# Diferencial com a matriz real do `completo` (truncada)
# ---------------------------------------------------------------------------

LINHAS_DA_MATRIZ_TRUNCADA = 130  # 104 de treino minimo + 26 origens de teste: rapido, mas com treino real.


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


def matriz_real_truncada(tabela_cortada: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """As primeiras 130 linhas da matriz do `completo` no horizonte (sem buraco: a enchente e de 2024)."""
    matriz = montar_matriz_do_braco(tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    return matriz.iloc[:LINHAS_DA_MATRIZ_TRUNCADA].copy()


@pytest.mark.parametrize("horizonte", [1, 12])
def test_resposta_reproduz_o_walk_forward_certificado_bit_a_bit(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
) -> None:
    """Modelo real (folha 5, 250 iteracoes), matriz real truncada: previsto IDENTICO (sem tolerancia)."""
    matriz = matriz_real_truncada(tabela_cortada, horizonte)
    certificado = executar_walk_forward(matriz, horizonte, FOLHA_5, CONFIGURACAO_AVALIACAO)
    com_corte = executar_walk_forward_com_corte(matriz, horizonte, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.RESPOSTA)

    assert len(certificado) == LINHAS_DA_MATRIZ_TRUNCADA - CONFIGURACAO_AVALIACAO.treino_minimo_em_semanas
    pd.testing.assert_frame_equal(com_corte, certificado, check_exact=True)


def test_pergunta_em_h1_e_igual_a_resposta_e_em_h12_difere(tabela_cortada: pd.DataFrame) -> None:
    """h = 1: as regras coincidem (bit a bit). h = 12: 11 linhas de rotulo futuro entram e o previsto muda."""
    matriz_h1 = matriz_real_truncada(tabela_cortada, 1)
    resposta_h1 = executar_walk_forward_com_corte(matriz_h1, 1, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.RESPOSTA)
    pergunta_h1 = executar_walk_forward_com_corte(matriz_h1, 1, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.PERGUNTA)
    pd.testing.assert_frame_equal(pergunta_h1, resposta_h1, check_exact=True)

    matriz_h12 = matriz_real_truncada(tabela_cortada, 12)
    resposta_h12 = executar_walk_forward_com_corte(matriz_h12, 12, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.RESPOSTA)
    pergunta_h12 = executar_walk_forward_com_corte(matriz_h12, 12, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.PERGUNTA)
    assert list(pergunta_h12[COLUNA_DATA_DE_ORIGEM]) == list(resposta_h12[COLUNA_DATA_DE_ORIGEM])
    diferenca = np.abs(pergunta_h12["previsto"].to_numpy() - resposta_h12["previsto"].to_numpy())
    assert diferenca.max() > 0.0


@pytest.mark.parametrize("horizonte", [4, 12])
def test_recortar_antes_do_laco_da_as_mesmas_previsoes_que_filtrar_depois(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
) -> None:
    """A premissa da E1: rodar a matriz cortada em `data_alvo <= limite` == rodar tudo e filtrar `data_alvo <= limite`.

    Matriz real INTEIRA do `completo`, modelo pequeno (a premissa nao depende do modelo; ele so
    precisa ser deterministico), limite no meio da serie, comparacao sem tolerancia.
    """
    matriz_inteira = montar_matriz_do_braco(
        tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    limite = pd.Timestamp("2021-12-26")
    modelo_pequeno = dataclasses.replace(FOLHA_5, nome="histgb_teste", numero_de_iteracoes=30)

    tudo = executar_walk_forward(matriz_inteira, horizonte, modelo_pequeno, CONFIGURACAO_AVALIACAO)
    tudo_filtrado = tudo.loc[tudo[COLUNA_DATA_ALVO] <= limite].reset_index(drop=True)

    matriz_recortada = recortar_matriz_ate_a_data_alvo(matriz_inteira, limite)
    recortado = executar_walk_forward(matriz_recortada, horizonte, modelo_pequeno, CONFIGURACAO_AVALIACAO)

    assert len(recortado) > 20
    assert len(recortado) < len(tudo)
    pd.testing.assert_frame_equal(recortado, tudo_filtrado, check_exact=True)
