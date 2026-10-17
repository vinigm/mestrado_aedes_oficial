"""Testes da E6a: as candidatas de clima, os grupos de colunas e o ranking de ganho do LightGBM.

Quatro blocos:
    1. a tabela das candidatas (42 de clima, 8 do nucleo, 6 do vetor) na tabela certificada, e as colunas
       que o pacote ja usa (clima congelado e nucleo) iguais, bit a bit, as de `construir_variaveis_de_origem`;
    2. `separar_grupos_de_colunas`, a regra de pedacos de nome do codigo antigo, em casos pequenos;
    3. o ranking de ganho, em dados sinteticos com um sinal plantado, e a propriedade central do metodo:
       as linhas fora dos primeiros 60% das linhas validas NAO influenciam o ranking;
    4. a margem entre a 6a e a 7a, a escolha das melhores e a configuracao do LightGBM.
"""

import pathlib

import lightgbm
import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import CONFIGURACAO_DADOS, CONFIGURACAO_VARIAVEIS
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.selecao_clima import (
    COLUNAS_IGNORADAS,
    NOMES_DA_SAZONALIDADE_DO_ALVO,
    MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO,
    MODELO_DE_SELECAO_UM_PROCESSO,
    MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE,
    PADROES_DO_CLIMA,
    PADROES_DO_VETOR,
    GruposDeColunas,
    calcular_ganho_do_horizonte,
    calcular_margem_de_entrada,
    construir_tabela_de_candidatas,
    criar_modelo_de_selecao,
    escolher_as_melhores,
    selecionar_clima_por_ganho,
    separar_grupos_de_colunas,
)
from aedes.variaveis import construir_variaveis_de_origem

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def tabela_de_candidatas(tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """A tabela com as colunas candidatas, montada da tabela certificada."""
    return construir_tabela_de_candidatas(tabela_cortada, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def grupos_da_tabela_certificada(tabela_de_candidatas: pd.DataFrame) -> GruposDeColunas:
    """Os tres grupos de colunas da tabela certificada."""
    return separar_grupos_de_colunas(
        list(tabela_de_candidatas.columns), COLUNAS_IGNORADAS, PADROES_DO_VETOR, PADROES_DO_CLIMA
    )


# ---------------------------------------------------------------------------
# 1. Tabela das candidatas na tabela certificada
# ---------------------------------------------------------------------------


def test_a_tabela_certificada_tem_42_candidatas_de_clima_8_do_nucleo_e_6_do_vetor(
    grupos_da_tabela_certificada: GruposDeColunas,
) -> None:
    """Ancoras do antigo: 22 colunas de clima da tabela + 20 defasagens = 42; nucleo 8; vetor 6."""
    assert len(grupos_da_tabela_certificada.clima) == 42
    assert len(grupos_da_tabela_certificada.nucleo) == 8
    assert len(grupos_da_tabela_certificada.vetor) == 6


def test_o_nucleo_e_o_vetor_tem_os_nomes_e_a_ordem_do_modelo(grupos_da_tabela_certificada: GruposDeColunas) -> None:
    """Nucleo: casos, 4 defasagens, media movel, sen/cos; vetor: a coluna, 4 defasagens e a media movel."""
    assert grupos_da_tabela_certificada.nucleo == [
        "casos",
        "casos_lag1",
        "casos_lag2",
        "casos_lag3",
        "casos_lag4",
        "casos_mm4",
        "sem_sin",
        "sem_cos",
    ]
    assert grupos_da_tabela_certificada.vetor == [
        "aedes_aegypti_por_armadilha",
        "aedes_aegypti_por_armadilha_lag1",
        "aedes_aegypti_por_armadilha_lag2",
        "aedes_aegypti_por_armadilha_lag3",
        "aedes_aegypti_por_armadilha_lag4",
        "vetor_mm4",
    ]


def test_as_candidatas_de_clima_seguem_a_ordem_da_tabela_e_depois_as_defasagens_por_coluna(
    grupos_da_tabela_certificada: GruposDeColunas,
) -> None:
    """A ordem das candidatas (relevante no desempate) e a do antigo: 22 colunas da tabela, depois lags de 5 colunas."""
    clima = grupos_da_tabela_certificada.clima
    assert clima[:4] == ["precip_total_mm", "precip_max_dia_mm", "precip_media_dia_mm", "dias_de_chuva"]
    assert clima[21] == "vento_max"
    assert clima[22:26] == ["temp_media_lag1", "temp_media_lag2", "temp_media_lag3", "temp_media_lag4"]
    assert clima[26:30] == [f"precip_total_mm_lag{defasagem}" for defasagem in (1, 2, 3, 4)]
    assert clima[-4:] == [f"pressao_media_lag{defasagem}" for defasagem in (1, 2, 3, 4)]
    assert len(set(clima)) == 42


def test_as_colunas_ignoradas_nunca_entram_em_nenhum_grupo(grupos_da_tabela_certificada: GruposDeColunas) -> None:
    """`ano`, `semana`, `fonte`, contagens brutas e as colunas de El Nino/La Nina ficam de fora dos tres grupos."""
    todas_as_colunas_dos_grupos = (
        grupos_da_tabela_certificada.nucleo + grupos_da_tabela_certificada.clima + grupos_da_tabela_certificada.vetor
    )
    for nome_ignorado in COLUNAS_IGNORADAS:
        assert nome_ignorado not in todas_as_colunas_dos_grupos


def test_as_colunas_candidatas_que_o_pacote_ja_usa_sao_iguais_bit_a_bit_as_de_construir_variaveis_de_origem(
    tabela_cortada: pd.DataFrame, tabela_de_candidatas: pd.DataFrame
) -> None:
    """As 6 de clima congeladas, o nucleo e o vetor da tabela das candidatas == a receita certificada do pacote."""
    variaveis_do_pacote = construir_variaveis_de_origem(tabela_cortada, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    nomes_em_comum = [
        "casos",
        "casos_lag1",
        "casos_lag2",
        "casos_lag3",
        "casos_lag4",
        "casos_mm4",
        "sem_sin",
        "sem_cos",
        "temp_media_lag4",
        "umid_media",
        "temp_media_lag3",
        "temp_max",
        "pressao_media_lag3",
        "pressao_media_lag4",
        "aedes_aegypti_por_armadilha",
        "aedes_aegypti_por_armadilha_lag1",
        "aedes_aegypti_por_armadilha_lag4",
        "vetor_mm4",
    ]
    for nome in nomes_em_comum:
        pd.testing.assert_series_equal(
            tabela_de_candidatas[nome], variaveis_do_pacote[nome], check_exact=True, check_names=True
        )


def test_a_tabela_das_candidatas_nao_altera_a_tabela_de_entrada(tabela_cortada: pd.DataFrame) -> None:
    """A entrada fica como estava: mesmas colunas e valores (a de data e a de casos nao sao renomeadas la)."""
    antes = tabela_cortada.copy()
    construir_tabela_de_candidatas(tabela_cortada, CONFIGURACAO_DADOS)
    pd.testing.assert_frame_equal(tabela_cortada, antes, check_exact=True)


def test_a_tabela_das_candidatas_exige_a_semana_e_o_vetor(tabela_cortada: pd.DataFrame) -> None:
    """Sem a coluna da semana, a montagem falha com KeyError claro."""
    sem_semana = tabela_cortada.drop(columns=["semana"])
    with pytest.raises(KeyError, match="semana"):
        construir_tabela_de_candidatas(sem_semana, CONFIGURACAO_DADOS)


# ---------------------------------------------------------------------------
# 2. separar_grupos_de_colunas (regra do antigo, em casos pequenos)
# ---------------------------------------------------------------------------


def test_a_coluna_que_casa_com_vetor_e_com_clima_entra_nos_dois_grupos() -> None:
    """Regra do antigo: o grupo de vetor e o de clima sao filtros independentes; so o nucleo exclui os dois."""
    nomes = ["casos", "temp_do_vetor", "umid_media", "vetor_mm4", "casos_lag1"]
    grupos = separar_grupos_de_colunas(nomes, (), ("vetor",), ("temp", "umid"))
    assert grupos.vetor == ["temp_do_vetor", "vetor_mm4"]
    assert grupos.clima == ["temp_do_vetor", "umid_media"]
    assert grupos.nucleo == ["casos", "casos_lag1"]


def test_as_ignoradas_saem_mesmo_quando_o_nome_casa_com_um_padrao() -> None:
    """`ano` e ignorada por nome exato; `temp_x` nao e e entra no clima."""
    grupos = separar_grupos_de_colunas(["temp_ignorada", "temp_x", "y"], ("temp_ignorada",), ("vetor",), ("temp",))
    assert grupos.clima == ["temp_x"]
    assert grupos.nucleo == ["y"]


def test_a_ordem_de_cada_grupo_e_a_das_colunas_da_tabela() -> None:
    """Nao ordena por nome: preserva a ordem de entrada em cada grupo."""
    nomes = ["z_clima_temp", "a_clima_temp", "m_nucleo", "b_nucleo"]
    grupos = separar_grupos_de_colunas(nomes, (), ("vetor",), ("temp",))
    assert grupos.clima == ["z_clima_temp", "a_clima_temp"]
    assert grupos.nucleo == ["m_nucleo", "b_nucleo"]


def test_sem_colunas_os_tres_grupos_ficam_vazios() -> None:
    """Entrada vazia: grupos vazios, sem erro."""
    grupos = separar_grupos_de_colunas([], (), ("vetor",), ("temp",))
    assert (grupos.nucleo, grupos.clima, grupos.vetor) == ([], [], [])


# ---------------------------------------------------------------------------
# 3. Ranking de ganho em dados sinteticos
# ---------------------------------------------------------------------------


def montar_tabela_sintetica(quantidade_de_semanas: int, semente: int) -> tuple[pd.DataFrame, GruposDeColunas]:
    """Tabela de candidatas sintetica: o alvo depende de `clima_forte`; `clima_ruido` e puro ruido.

    Colunas: data, casos, semana, casos_lag1, clima_forte, clima_ruido, sem_sin, sem_cos.
    """
    gerador = np.random.default_rng(semente)
    datas = pd.date_range("2018-01-07", periods=quantidade_de_semanas, freq="7D")
    clima_forte = gerador.normal(size=quantidade_de_semanas)
    clima_ruido = gerador.normal(size=quantidade_de_semanas)
    casos = 50.0 + 30.0 * np.roll(clima_forte, 2) + gerador.normal(scale=2.0, size=quantidade_de_semanas)
    semana = np.arange(quantidade_de_semanas) % 52 + 1
    angulo = 2 * np.pi * semana / 52
    tabela = pd.DataFrame(
        {
            "data": datas,
            "casos": casos,
            "semana": semana,
            "casos_lag1": pd.Series(casos).shift(1),
            "clima_forte": clima_forte,
            "clima_ruido": clima_ruido,
            "sem_sin": np.sin(angulo),
            "sem_cos": np.cos(angulo),
        }
    )
    grupos = GruposDeColunas(
        nucleo=["casos", "casos_lag1", "sem_sin", "sem_cos"],
        clima=["clima_forte", "clima_ruido"],
        vetor=[],
    )
    return tabela, grupos


def test_o_clima_com_sinal_plantado_fica_em_primeiro_no_ranking() -> None:
    """O alvo e funcao de `clima_forte` (defasado); ele tem de ganhar mais que o ruido."""
    tabela, grupos = montar_tabela_sintetica(260, semente=1)
    resultado = selecionar_clima_por_ganho(tabela, grupos, (2, 3), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    assert list(resultado.ranking.index) == ["clima_forte", "clima_ruido"]
    assert resultado.ranking.iloc[0] > resultado.ranking.iloc[1]


def test_o_ranking_e_a_soma_dos_ganhos_dos_horizontes() -> None:
    """`ranking[c] == soma_h ganho_h[c]` para cada candidata, e a tabela por horizonte guarda uma coluna por h."""
    tabela, grupos = montar_tabela_sintetica(260, semente=2)
    resultado = selecionar_clima_por_ganho(tabela, grupos, (1, 4, 8), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    assert list(resultado.ganho_por_horizonte.columns) == ["ganho_h1", "ganho_h4", "ganho_h8"]
    soma_por_candidata = resultado.ganho_por_horizonte.sum(axis=1)
    for nome in grupos.clima:
        assert resultado.ranking[nome] == pytest.approx(float(soma_por_candidata[nome]), rel=1e-12)


def test_o_treino_da_selecao_usa_exatamente_os_primeiros_60_por_cento_das_linhas_validas() -> None:
    """`n_treino = int(0,60 * validas)`: arredonda para BAIXO, e o numero de linhas validas vem do dropna."""
    tabela, grupos = montar_tabela_sintetica(260, semente=3)
    resultado = selecionar_clima_por_ganho(tabela, grupos, (1,), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    validas = resultado.linhas_validas_por_horizonte[1]
    assert resultado.linhas_de_treino_por_horizonte[1] == int(validas * 0.60)
    # casos_lag1 e NaN na 1a semana e y_h e NaN na ultima: 260 - 1 - 1 linhas validas.
    assert validas == 258


def test_linhas_depois_dos_60_por_cento_nao_influenciam_o_ranking() -> None:
    """Propriedade central do metodo: apagar a informacao do final da serie nao muda NENHUM ganho (bit a bit)."""
    tabela, grupos = montar_tabela_sintetica(260, semente=4)
    original = selecionar_clima_por_ganho(tabela, grupos, (1, 4), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)

    alterada = tabela.copy()
    ultimas_linhas = alterada.index >= 200  # bem depois dos primeiros 60% (~155) mais o horizonte
    alterada.loc[ultimas_linhas, "casos"] = 999999.0
    alterada.loc[ultimas_linhas, "clima_forte"] = -999999.0
    alterada.loc[ultimas_linhas, "casos_lag1"] = 999999.0
    refeita = selecionar_clima_por_ganho(alterada, grupos, (1, 4), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)

    pd.testing.assert_series_equal(original.ranking, refeita.ranking, check_exact=True)
    pd.testing.assert_frame_equal(original.ganho_por_horizonte, refeita.ganho_por_horizonte, check_exact=True)


def test_o_ganho_de_um_horizonte_e_a_importancia_por_ganho_do_lightgbm_treinado_nos_primeiros_60_por_cento() -> None:
    """DIFERENCIAL do mecanismo: refaz o treino a mao (mesmas linhas, mesma ordem de colunas) e compara com o ganho devolvido.

    O ganho (`importance_type="gain"`) e um numero continuo; a importancia por contagem de cortes (`split`) e
    inteira e daria outro vetor. A igualdade exata com o `booster_.feature_importance("gain")` prova o tipo.
    """
    tabela, grupos = montar_tabela_sintetica(260, semente=12)
    horizonte = 2
    ganho_do_horizonte, validas, de_treino = calcular_ganho_do_horizonte(
        tabela, grupos, horizonte, 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE
    )

    dados = tabela.copy()
    dados["y_h"] = tabela["casos"].shift(-horizonte)
    angulo_do_alvo = 2 * np.pi * tabela["semana"].shift(-horizonte) / 52
    dados["alvo_sin"] = np.sin(angulo_do_alvo)
    dados["alvo_cos"] = np.cos(angulo_do_alvo)
    nomes = grupos.nucleo + grupos.clima + list(NOMES_DA_SAZONALIDADE_DO_ALVO)
    validos = dados.dropna(subset=[*nomes, "y_h"]).sort_values("data").reset_index(drop=True)
    treino = validos.iloc[: int(len(validos) * 0.60)]
    modelo = lightgbm.LGBMRegressor(**MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE.parametros_do_lightgbm())
    modelo.fit(treino[nomes], treino["y_h"])
    esperado = modelo.booster_.feature_importance(importance_type="gain")

    assert validas == len(validos)
    assert de_treino == len(treino)
    for posicao, nome in enumerate(nomes):
        if nome in grupos.clima:
            assert ganho_do_horizonte[nome] == esperado[posicao]
    # Sanidade: o ganho do sinal plantado nao e um numero inteiro (a contagem de cortes seria).
    assert ganho_do_horizonte["clima_forte"] != round(float(ganho_do_horizonte["clima_forte"]))


def test_com_semente_fixa_e_um_processo_duas_execucoes_dao_o_mesmo_ranking_exato() -> None:
    """A variante 3 da E6a e deterministica: dois treinos seguidos, ganhos identicos."""
    tabela, grupos = montar_tabela_sintetica(260, semente=5)
    primeiro = selecionar_clima_por_ganho(tabela, grupos, (1, 4), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    segundo = selecionar_clima_por_ganho(tabela, grupos, (1, 4), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    pd.testing.assert_series_equal(primeiro.ranking, segundo.ranking, check_exact=True)


def test_a_coluna_que_o_modelo_nao_usa_tem_ganho_zero_e_nao_some_do_ranking() -> None:
    """Candidata constante nunca e usada pelo LightGBM: ganho 0 (`fillna(0)`), mas continua no ranking, no fim."""
    tabela, grupos = montar_tabela_sintetica(260, semente=6)
    tabela["clima_constante"] = 5.0
    grupos_com_constante = GruposDeColunas(
        nucleo=grupos.nucleo, clima=[*grupos.clima, "clima_constante"], vetor=[]
    )
    resultado = selecionar_clima_por_ganho(
        tabela, grupos_com_constante, (1, 4), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE
    )
    assert len(resultado.ranking) == 3
    assert resultado.ranking["clima_constante"] == 0.0
    assert resultado.ranking.index[-1] == "clima_constante"


def test_fracao_de_treino_invalida_e_rejeitada() -> None:
    """Fracao zero, negativa ou acima de 1 levanta ValueError."""
    tabela, grupos = montar_tabela_sintetica(260, semente=7)
    for fracao in (0.0, -0.1, 1.01):
        with pytest.raises(ValueError, match="fracao_de_treino"):
            calcular_ganho_do_horizonte(tabela, grupos, 1, fracao, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)


def test_treino_vazio_e_erro_claro() -> None:
    """Com poucas linhas validas a fracao de treino da zero linhas: erro explicito, nao uma excecao obscura."""
    tabela, grupos = montar_tabela_sintetica(5, semente=8)
    with pytest.raises(ValueError, match="Treino vazio"):
        calcular_ganho_do_horizonte(tabela, grupos, 1, 0.20, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)


def test_sem_horizontes_e_erro() -> None:
    """Lista de horizontes vazia: ValueError."""
    tabela, grupos = montar_tabela_sintetica(100, semente=9)
    with pytest.raises(ValueError, match="horizontes"):
        selecionar_clima_por_ganho(tabela, grupos, (), 0.60, MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)


# ---------------------------------------------------------------------------
# 4. Margem, escolha e configuracao do LightGBM
# ---------------------------------------------------------------------------


def test_escolher_as_melhores_devolve_as_primeiras_na_ordem_do_ranking() -> None:
    """As K primeiras do ranking, na ordem; K invalido levanta ValueError."""
    ranking = pd.Series([9.0, 7.0, 5.0, 3.0], index=["a", "b", "c", "d"])
    assert escolher_as_melhores(ranking, 2) == ["a", "b"]
    assert escolher_as_melhores(ranking, 4) == ["a", "b", "c", "d"]
    for quantidade in (0, 5):
        with pytest.raises(ValueError):
            escolher_as_melhores(ranking, quantidade)


def test_a_margem_de_entrada_e_o_ganho_da_ultima_escolhida_menos_o_da_proxima() -> None:
    """Conta a mao: ranking 100, 80, 60: escolhendo 2, margem = 80 - 60 = 20 e razao 60/80 = 0,75."""
    ranking = pd.Series([100.0, 80.0, 60.0], index=["a", "b", "c"])
    margem = calcular_margem_de_entrada(ranking, 2)
    assert margem["ultima_escolhida"] == "b"
    assert margem["proxima"] == "c"
    assert margem["diferenca"] == 20.0
    assert margem["razao_proxima_sobre_ultima"] == 0.75


def test_a_margem_exige_candidata_de_fora() -> None:
    """Escolher todas as candidatas deixa a margem indefinida: ValueError."""
    ranking = pd.Series([3.0, 2.0], index=["a", "b"])
    with pytest.raises(ValueError):
        calcular_margem_de_entrada(ranking, 2)


def test_a_razao_da_margem_e_nan_quando_o_ganho_da_ultima_escolhida_e_zero() -> None:
    """Sem divisao por zero: razao NaN."""
    ranking = pd.Series([5.0, 0.0, 0.0], index=["a", "b", "c"])
    margem = calcular_margem_de_entrada(ranking, 2)
    assert np.isnan(margem["razao_proxima_sobre_ultima"])


def test_as_tres_variantes_do_modelo_de_selecao_tem_os_parametros_do_antigo() -> None:
    """Antigo: 250 arvores, taxa 0,05, 15 folhas, folha minima 5, verbose -1, n_jobs -1, SEM semente."""
    parametros_antigos = MODELO_DE_SELECAO_IDENTICO_AO_ANTIGO.parametros_do_lightgbm()
    assert parametros_antigos == {
        "n_estimators": 250,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_child_samples": 5,
        "verbose": -1,
        "n_jobs": -1,
    }
    assert "random_state" not in parametros_antigos

    parametros_um_processo = MODELO_DE_SELECAO_UM_PROCESSO.parametros_do_lightgbm()
    assert parametros_um_processo["n_jobs"] == 1
    assert "random_state" not in parametros_um_processo

    parametros_com_semente = MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE.parametros_do_lightgbm()
    assert parametros_com_semente["n_jobs"] == 1
    assert parametros_com_semente["random_state"] == 42


def test_o_modelo_criado_tem_os_hiperparametros_pedidos() -> None:
    """`criar_modelo_de_selecao` traduz a configuracao: os parametros aparecem em `get_params()`."""
    modelo = criar_modelo_de_selecao(MODELO_DE_SELECAO_UM_PROCESSO_COM_SEMENTE)
    parametros = modelo.get_params()
    assert parametros["n_estimators"] == 250
    assert parametros["num_leaves"] == 15
    assert parametros["min_child_samples"] == 5
    assert parametros["random_state"] == 42
    assert parametros["n_jobs"] == 1
