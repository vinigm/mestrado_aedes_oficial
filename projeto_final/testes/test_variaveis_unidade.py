"""Testes de unidade de `aedes.variaveis` com tabelas sinteticas (sem ler arquivo).

Cada teste monta uma tabela pequena de domingos consecutivos, com valores que
permitem conferir a mao uma defasagem, uma media movel, a sazonalidade e o
alvo. Cobre: valores, propagacao de ausentes, linhas descartadas, tabelas
vazias e de uma linha, erros de entrada, indice nao sequencial, infinito e
ausencia de estado global.
"""

import dataclasses

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    ConfiguracaoVariaveis,
)
from aedes.variaveis import (
    calcular_seno_e_cosseno_da_semana,
    construir_variaveis_de_origem,
    montar_matriz_do_horizonte,
    validar_tabela_para_variaveis,
)

PRIMEIRO_DOMINGO_SINTETICO = pd.Timestamp("2020-01-05")
COLUNA_DE_DATA = CONFIGURACAO_DADOS.coluna_de_data
COLUNA_DE_CASOS = CONFIGURACAO_DADOS.coluna_de_casos
NOME_DO_VETOR = CONFIGURACAO_VARIAVEIS.coluna_do_vetor
SEMANAS_POR_ANO = CONFIGURACAO_VARIAVEIS.semanas_por_ano
PRIMEIRA_LINHA_COMPLETA = 4  # defasagem 4 (casos, vetor, clima) exige 4 semanas de historico


def domingo_da_posicao(semanas: int) -> pd.Timestamp:
    """Domingo da semana de posicao `semanas` na grade sintetica."""
    return PRIMEIRO_DOMINGO_SINTETICO + semanas * pd.Timedelta(weeks=1)


def montar_tabela_sintetica(
    semanas: int,
    casos: list[float] | None = None,
    vetor: list[float] | None = None,
    semana_epidemiologica: list[float] | None = None,
) -> pd.DataFrame:
    """Tabela de domingos consecutivos com valores conhecidos.

    Por padrao: casos = 10, 20, 30...; vetor = 1,0 + 0,5 * posicao; semana
    epidemiologica = 1, 2, 3...; clima crescente e distinto por coluna.
    """
    posicoes = np.arange(semanas, dtype="float64")
    casos_padrao = 10.0 * (posicoes + 1.0)
    vetor_padrao = 1.0 + 0.5 * posicoes
    semana_padrao = posicoes + 1.0
    tabela = pd.DataFrame(
        {
            COLUNA_DE_DATA: pd.date_range(PRIMEIRO_DOMINGO_SINTETICO, periods=semanas, freq="W-SUN"),
            "semana": semana_padrao if semana_epidemiologica is None else semana_epidemiologica,
            COLUNA_DE_CASOS: casos_padrao if casos is None else np.array(casos, dtype="float64"),
            "temp_media": 15.0 + posicoes,
            "temp_max": 20.0 + 2.0 * posicoes,
            "umid_media": 60.0 + 3.0 * posicoes,
            "pressao_media": 1010.0 + 0.1 * posicoes,
            NOME_DO_VETOR: vetor_padrao if vetor is None else np.array(vetor, dtype="float64"),
        }
    )
    return tabela


def matriz_do_horizonte(tabela: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Atalho: monta a matriz com as configuracoes padrao."""
    return montar_matriz_do_horizonte(
        tabela, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )


# ---------------------------------------------------------------------------
# Valores calculados a mao
# ---------------------------------------------------------------------------


def test_valores_de_uma_linha_conferidos_a_mao() -> None:
    """h = 2, tabela de 20 semanas: a linha da posicao 10 tem cada variavel igual ao calculo manual."""
    tabela = montar_tabela_sintetica(20)
    horizonte = 2
    matriz = matriz_do_horizonte(tabela, horizonte)

    posicao_de_origem = 10
    data_de_origem = domingo_da_posicao(posicao_de_origem)
    linha = matriz[matriz[COLUNA_DATA_DE_ORIGEM] == data_de_origem]
    assert len(linha) == 1
    linha = linha.iloc[0]

    # casos(p) = 10 * (p + 1); vetor(p) = 1 + 0,5 * p; semana(p) = p + 1.
    assert linha["casos"] == 110.0
    assert linha["casos_lag1"] == 100.0
    assert linha["casos_lag4"] == 70.0
    assert linha["casos_mm4"] == pytest.approx((110.0 + 100.0 + 90.0 + 80.0) / 4.0)
    assert linha[NOME_DO_VETOR] == 6.0
    assert linha[f"{NOME_DO_VETOR}_lag2"] == 5.0
    assert linha["vetor_mm4"] == pytest.approx((6.0 + 5.5 + 5.0 + 4.5) / 4.0)
    assert linha["temp_media_lag4"] == 15.0 + 6.0
    assert linha["temp_media_lag3"] == 15.0 + 7.0
    assert linha["umid_media"] == 60.0 + 3.0 * 10.0
    assert linha["temp_max"] == 20.0 + 2.0 * 10.0
    assert linha["pressao_media_lag3"] == pytest.approx(1010.0 + 0.1 * 7.0)
    assert linha["pressao_media_lag4"] == pytest.approx(1010.0 + 0.1 * 6.0)
    assert linha["sem_sin"] == pytest.approx(np.sin(2 * np.pi * 11.0 / 52.0))
    assert linha["sem_cos"] == pytest.approx(np.cos(2 * np.pi * 11.0 / 52.0))
    assert linha["alvo_sin"] == pytest.approx(np.sin(2 * np.pi * 13.0 / 52.0))
    assert linha["alvo_cos"] == pytest.approx(np.cos(2 * np.pi * 13.0 / 52.0))
    assert linha[COLUNA_DO_ALVO] == 130.0
    assert linha[COLUNA_DATA_ALVO] == domingo_da_posicao(posicao_de_origem + horizonte)


def test_linhas_validas_comecam_na_posicao_4_e_terminam_h_semanas_antes_do_fim() -> None:
    """Sem ausentes na entrada: sobram as origens de 4 a n - 1 - h."""
    tabela = montar_tabela_sintetica(20)
    for horizonte in (1, 5, 12):
        matriz = matriz_do_horizonte(tabela, horizonte)
        assert len(matriz) == 20 - horizonte - PRIMEIRA_LINHA_COMPLETA
        primeira_origem = matriz[COLUNA_DATA_DE_ORIGEM].iloc[0]
        ultima_origem = matriz[COLUNA_DATA_DE_ORIGEM].iloc[-1]
        assert primeira_origem == domingo_da_posicao(PRIMEIRA_LINHA_COMPLETA)
        assert ultima_origem == domingo_da_posicao(20 - 1 - horizonte)


def test_a_sazonalidade_do_alvo_usa_a_semana_epidemiologica_e_nao_a_data() -> None:
    """Com semana 52, 53 e 1 no meio da serie, o alvo usa o numero da semana-alvo (53 inclusive)."""
    semanas_epidemiologicas = [48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    tabela = montar_tabela_sintetica(12, semana_epidemiologica=semanas_epidemiologicas)
    matriz = matriz_do_horizonte(tabela, 2)

    # Origem na posicao 4 (semana 52): alvo na posicao 6 (semana 1).
    primeira_linha = matriz.iloc[0]
    assert primeira_linha["sem_sin"] == pytest.approx(np.sin(2 * np.pi * 52.0 / 52.0))
    assert primeira_linha["alvo_sin"] == pytest.approx(np.sin(2 * np.pi * 1.0 / 52.0))
    # Origem na posicao 5 (semana 53): o cosseno usa 53/52 de volta, sem reduzir a semana 1.
    segunda_linha = matriz.iloc[1]
    assert segunda_linha["sem_cos"] == pytest.approx(np.cos(2 * np.pi * 53.0 / 52.0))
    assert segunda_linha["alvo_sin"] == pytest.approx(np.sin(2 * np.pi * 2.0 / 52.0))


def test_seno_e_cosseno_da_semana_com_ausente_dao_ausente() -> None:
    """Semana ausente gera seno e cosseno ausentes (nada e preenchido)."""
    semana = pd.Series([1.0, np.nan, 13.0])
    sazonalidade = calcular_seno_e_cosseno_da_semana(semana, 52, "seno", "cosseno")

    assert list(sazonalidade.columns) == ["seno", "cosseno"]
    assert sazonalidade["seno"].isna().tolist() == [False, True, False]
    assert sazonalidade["cosseno"].iloc[2] == pytest.approx(np.cos(2 * np.pi * 13.0 / 52.0))
    assert sazonalidade["seno"].iloc[2] == pytest.approx(1.0)


def test_construir_variaveis_de_origem_devolve_as_20_variaveis_sem_o_alvo() -> None:
    """As variaveis de origem sao 20; `alvo_sin`, `alvo_cos` e `y_h` so entram na matriz do horizonte."""
    tabela = montar_tabela_sintetica(15)
    variaveis = construir_variaveis_de_origem(tabela, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)

    assert variaveis.shape == (15, 20)
    assert "alvo_sin" not in variaveis.columns
    assert "alvo_cos" not in variaveis.columns
    assert COLUNA_DO_ALVO not in variaveis.columns
    assert variaveis.index.equals(tabela.index)
    # Sem ordem relevante: o conjunto e o das 22 menos as duas do alvo.
    esperado = set(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis) - {"alvo_sin", "alvo_cos"}
    assert set(variaveis.columns) == esperado


# ---------------------------------------------------------------------------
# Ausentes
# ---------------------------------------------------------------------------


def test_casos_apagados_no_fim_tiram_as_origens_sem_alvo_e_as_com_casos_ausentes() -> None:
    """Corte de maturidade: ultimas 3 semanas sem caso. h = 2 deixa de fora 5 origens no fim."""
    casos = [10.0 * (posicao + 1) for posicao in range(17)] + [np.nan, np.nan, np.nan]
    tabela = montar_tabela_sintetica(20, casos=casos)
    matriz = matriz_do_horizonte(tabela, 2)

    # Origens validas: 4 .. 14 (a origem 14 tem y_h na posicao 16; a 15 teria y_h na 17, ausente).
    assert matriz[COLUNA_DATA_DE_ORIGEM].iloc[-1] == domingo_da_posicao(14)
    assert len(matriz) == 14 - PRIMEIRA_LINHA_COMPLETA + 1
    assert matriz.isna().sum().sum() == 0


def test_ausente_no_vetor_derruba_as_5_semanas_que_o_usam() -> None:
    """Vetor ausente na posicao 10: caem as origens 10 (valor), 11 a 13 (lags 1-3 e media), 14 (lag 4)."""
    vetor = [1.0 + 0.5 * posicao for posicao in range(25)]
    vetor[10] = np.nan
    tabela = montar_tabela_sintetica(25, vetor=vetor)
    matriz = matriz_do_horizonte(tabela, 1)

    datas_das_origens = set(matriz[COLUNA_DATA_DE_ORIGEM])
    for posicao_derrubada in range(10, 15):
        assert domingo_da_posicao(posicao_derrubada) not in datas_das_origens
    assert domingo_da_posicao(9) in datas_das_origens
    assert domingo_da_posicao(15) in datas_das_origens
    assert len(matriz) == 25 - 1 - PRIMEIRA_LINHA_COMPLETA - 5


def test_media_movel_nao_preenche_ausente_no_meio_da_janela() -> None:
    """`rolling(4).mean()` sem `min_periods`: janela com ausente da ausente, e volta quando o ausente sai."""
    casos = [10.0 * (posicao + 1) for posicao in range(12)]
    casos[6] = np.nan
    tabela = montar_tabela_sintetica(12, casos=casos)
    variaveis = construir_variaveis_de_origem(tabela, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)

    media_movel = variaveis["casos_mm4"]
    assert media_movel.iloc[:3].isna().all()
    assert media_movel.iloc[5] == pytest.approx((30.0 + 40.0 + 50.0 + 60.0) / 4.0)
    assert media_movel.iloc[6:10].isna().all()
    assert media_movel.iloc[10] == pytest.approx((80.0 + 90.0 + 100.0 + 110.0) / 4.0)


def test_infinito_no_vetor_nao_e_filtrado_pelo_pacote_so_pelo_rolling_do_pandas() -> None:
    """Infinito no vetor: `dropna` nao o remove; as linhas caem so onde a media movel vira NaN.

    No pandas 3.0.2, `rolling(4).mean()` devolve NaN em toda janela que contem
    infinito (igual ao codigo antigo, que usa a mesma chamada). Com infinito na
    posicao 8, a media movel e NaN nas origens 8 a 11 (essas linhas caem); a
    origem 12 (defasagem 4 ve o infinito, mas a janela 9-12 nao) PERMANECE,
    com infinito na variavel `_lag4`.
    """
    vetor = [1.0 + 0.5 * posicao for posicao in range(15)]
    vetor[8] = np.inf
    tabela = montar_tabela_sintetica(15, vetor=vetor)
    matriz = matriz_do_horizonte(tabela, 1)

    datas_das_origens = set(matriz[COLUNA_DATA_DE_ORIGEM])
    for posicao_derrubada in range(8, 12):
        assert domingo_da_posicao(posicao_derrubada) not in datas_das_origens

    linha_da_origem_12 = matriz[matriz[COLUNA_DATA_DE_ORIGEM] == domingo_da_posicao(12)]
    assert len(linha_da_origem_12) == 1
    assert np.isinf(linha_da_origem_12[f"{NOME_DO_VETOR}_lag4"].iloc[0])


def test_tabela_toda_sem_caso_devolve_matriz_vazia_com_as_25_colunas() -> None:
    """Sem nenhum caso, nenhuma linha e valida; as colunas saem iguais."""
    casos = [np.nan] * 12
    tabela = montar_tabela_sintetica(12, casos=casos)
    matriz = matriz_do_horizonte(tabela, 3)

    assert matriz.empty
    assert list(matriz.columns) == [
        COLUNA_DATA_DE_ORIGEM,
        COLUNA_DATA_ALVO,
        *CONFIGURACAO_VARIAVEIS.nomes_das_variaveis,
        COLUNA_DO_ALVO,
    ]
    assert len(matriz.columns) == 25


# ---------------------------------------------------------------------------
# Formato, vazio, uma linha, indice
# ---------------------------------------------------------------------------


def test_ordem_das_colunas_e_a_da_configuracao() -> None:
    """data_origem, data_alvo, as 22 na ordem da configuracao e y_h."""
    matriz = matriz_do_horizonte(montar_tabela_sintetica(20), 4)
    esperado = [
        COLUNA_DATA_DE_ORIGEM,
        COLUNA_DATA_ALVO,
        *CONFIGURACAO_VARIAVEIS.nomes_das_variaveis,
        COLUNA_DO_ALVO,
    ]
    assert list(matriz.columns) == esperado


def test_indice_da_saida_e_renumerado_a_partir_de_zero() -> None:
    """Depois do `dropna` o indice volta a 0..n-1."""
    matriz = matriz_do_horizonte(montar_tabela_sintetica(20), 2)
    assert matriz.index.tolist() == list(range(len(matriz)))


def test_indice_nao_sequencial_da_entrada_nao_muda_o_resultado() -> None:
    """A tabela com indice embaralhado/deslocado gera a mesma matriz (o calculo e por posicao)."""
    tabela = montar_tabela_sintetica(20)
    tabela_com_indice_estranho = tabela.copy()
    tabela_com_indice_estranho.index = pd.Index(np.arange(20)[::-1] * 7 + 1000)

    esperado = matriz_do_horizonte(tabela, 3)
    obtido = matriz_do_horizonte(tabela_com_indice_estranho, 3)

    pd.testing.assert_frame_equal(obtido, esperado, check_exact=True)


def test_tabela_vazia_devolve_matriz_vazia() -> None:
    """Zero linhas (com os tipos certos) devolve zero linhas e as 25 colunas."""
    tabela = montar_tabela_sintetica(5).iloc[0:0]
    matriz = matriz_do_horizonte(tabela, 2)
    assert matriz.empty
    assert len(matriz.columns) == 25


def test_tabela_de_uma_linha_devolve_matriz_vazia() -> None:
    """Uma unica semana nao tem historico nem alvo."""
    matriz = matriz_do_horizonte(montar_tabela_sintetica(1), 1)
    assert matriz.empty


def test_horizonte_maior_que_a_tabela_devolve_matriz_vazia() -> None:
    """Se h passa do fim da tabela, nenhuma linha tem alvo."""
    matriz = matriz_do_horizonte(montar_tabela_sintetica(10), 12)
    assert matriz.empty


def test_as_origens_de_h_diferentes_sao_prefixos_uma_da_outra() -> None:
    """Aumentar h so remove origens do fim: as primeiras linhas de h=1 e h=3 coincidem nas datas de origem."""
    tabela = montar_tabela_sintetica(30)
    origens_h1 = matriz_do_horizonte(tabela, 1)[COLUNA_DATA_DE_ORIGEM].tolist()
    origens_h3 = matriz_do_horizonte(tabela, 3)[COLUNA_DATA_DE_ORIGEM].tolist()
    assert origens_h1[: len(origens_h3)] == origens_h3
    assert len(origens_h1) - len(origens_h3) == 2


def test_a_tabela_de_entrada_nao_e_modificada() -> None:
    """Funcao pura: a tabela recebida fica igual (colunas, valores e indice)."""
    tabela = montar_tabela_sintetica(20)
    copia_antes = tabela.copy()
    matriz_do_horizonte(tabela, 4)
    pd.testing.assert_frame_equal(tabela, copia_antes, check_exact=True)


# ---------------------------------------------------------------------------
# Erros de entrada
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("horizonte_invalido", [0, -1, 1.5, True, None, "3"])
def test_horizonte_invalido_levanta_erro(horizonte_invalido: object) -> None:
    """Horizonte: inteiro >= 1 (bool nao conta)."""
    with pytest.raises(ValueError, match="horizonte"):
        matriz_do_horizonte(montar_tabela_sintetica(10), horizonte_invalido)


@pytest.mark.parametrize(
    "coluna_ausente",
    [COLUNA_DE_DATA, COLUNA_DE_CASOS, "semana", NOME_DO_VETOR, "temp_media", "temp_max", "umid_media", "pressao_media"],
)
def test_coluna_ausente_levanta_keyerror(coluna_ausente: str) -> None:
    """Falta de qualquer coluna que a receita consome e erro com o nome da coluna."""
    tabela = montar_tabela_sintetica(10).drop(columns=[coluna_ausente])
    with pytest.raises(KeyError, match=coluna_ausente):
        matriz_do_horizonte(tabela, 2)


def test_grade_com_buraco_levanta_erro() -> None:
    """Semana faltando na grade: o `shift` por posicao erraria, entao a funcao recusa."""
    tabela = montar_tabela_sintetica(12).drop(index=[5]).reset_index(drop=True)
    with pytest.raises(ValueError, match="grade"):
        matriz_do_horizonte(tabela, 2)


def test_datas_fora_de_ordem_levantam_erro() -> None:
    """Datas em ordem decrescente nao sao uma grade semanal crescente."""
    tabela = montar_tabela_sintetica(12).iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="grade"):
        matriz_do_horizonte(tabela, 2)


def test_data_que_nao_e_do_tipo_data_levanta_erro() -> None:
    """A coluna de data como texto e erro."""
    tabela = montar_tabela_sintetica(12)
    tabela[COLUNA_DE_DATA] = tabela[COLUNA_DE_DATA].astype(str)
    with pytest.raises(ValueError, match="data"):
        validar_tabela_para_variaveis(tabela, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)


def test_data_ausente_levanta_erro() -> None:
    """NaT na coluna de data e erro."""
    tabela = montar_tabela_sintetica(12)
    tabela.loc[3, COLUNA_DE_DATA] = pd.NaT
    with pytest.raises(ValueError, match="ausentes"):
        validar_tabela_para_variaveis(tabela, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)


# ---------------------------------------------------------------------------
# Sem estado global (o defeito do codigo antigo)
# ---------------------------------------------------------------------------


def configuracao_com_defasagens_1_e_2() -> ConfiguracaoVariaveis:
    """Configuracao alternativa: so 2 defasagens de casos e de vetor (18 variaveis)."""
    nomes_removidos = {
        "casos_lag3",
        "casos_lag4",
        f"{NOME_DO_VETOR}_lag3",
        f"{NOME_DO_VETOR}_lag4",
    }
    nomes_restantes = []
    for nome in CONFIGURACAO_VARIAVEIS.nomes_das_variaveis:
        if nome not in nomes_removidos:
            nomes_restantes.append(nome)
    return dataclasses.replace(
        CONFIGURACAO_VARIAVEIS,
        defasagens_de_casos=(1, 2),
        defasagens_do_vetor=(1, 2),
        nomes_das_variaveis=tuple(nomes_restantes),
    )


def test_defasagens_sao_parametro_e_configuracoes_diferentes_nao_se_afetam() -> None:
    """Alternar entre a configuracao padrao e a de 2 defasagens nao muda o resultado de nenhuma.

    O codigo antigo trocava `features.LAGS_SEMANAS` (variavel de modulo) em
    execucao; chamar uma configuracao depois da outra contaminava a seguinte.
    Aqui cada chamada recebe a sua configuracao e nada sobra entre elas.
    """
    tabela = montar_tabela_sintetica(30)
    alternativa = configuracao_com_defasagens_1_e_2()

    padrao_antes = montar_matriz_do_horizonte(tabela, 3, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    com_duas_defasagens = montar_matriz_do_horizonte(tabela, 3, alternativa, CONFIGURACAO_DADOS)
    padrao_depois = montar_matriz_do_horizonte(tabela, 3, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    alternativa_depois = montar_matriz_do_horizonte(tabela, 3, alternativa, CONFIGURACAO_DADOS)

    pd.testing.assert_frame_equal(padrao_antes, padrao_depois, check_exact=True)
    pd.testing.assert_frame_equal(com_duas_defasagens, alternativa_depois, check_exact=True)

    assert padrao_antes.shape[1] == 25
    assert com_duas_defasagens.shape[1] == 21
    assert "casos_lag3" in padrao_antes.columns
    assert "casos_lag3" not in com_duas_defasagens.columns


def test_defasagens_alternativas_deslocam_menos_historico() -> None:
    """Com defasagem maxima 2 (mas clima ainda com lag 4), a primeira linha valida continua na posicao 4.

    O clima congelado segue com atraso de 4 semanas, entao o inicio da matriz nao muda;
    o que muda e o numero de colunas.
    """
    tabela = montar_tabela_sintetica(20)
    alternativa = configuracao_com_defasagens_1_e_2()
    matriz = montar_matriz_do_horizonte(tabela, 2, alternativa, CONFIGURACAO_DADOS)
    assert matriz[COLUNA_DATA_DE_ORIGEM].iloc[0] == domingo_da_posicao(4)


def test_o_modulo_nao_tem_variavel_de_defasagem_para_trocar() -> None:
    """Nenhum nome do modulo se parece com a variavel global do antigo (`LAGS_SEMANAS`)."""
    import aedes.variaveis as modulo_variaveis

    nomes_do_modulo = dir(modulo_variaveis)
    assert "LAGS_SEMANAS" not in nomes_do_modulo
    assert "JANELA_MEDIA_MOVEL_SEMANAS" not in nomes_do_modulo
