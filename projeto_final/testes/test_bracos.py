"""Testes de `aedes.bracos`: os 8 bracos da ablacao e a matriz de cada um.

Unidade (tabelas sinteticas):
    - os blocos tem 6, 6, 6 e 4 variaveis e juntos sao as 22 do modelo;
    - cada braco recebe as colunas certas, NA ORDEM de `nomes_das_variaveis`;
    - o `dropna` olha so as colunas do proprio braco (a regra que a trava 2 exige);
    - erros de entrada (braco, horizonte, grade com buraco).

Diferencial (dados reais):
    - o braco `completo` e identico, bit a bit, a `montar_matriz_do_horizonte`
      nos 12 horizontes (colunas, ordem, valores, dtypes, indice);
    - em cada braco, os valores das colunas coincidem, bit a bit, com os do
      `completo` nas origens que os dois tem (so o conjunto de linhas muda);
    - o braco `sem_vetor` recupera exatamente as semanas sem vetor.
"""

import dataclasses
import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.bracos import (
    BLOCO_CALENDARIO,
    BLOCO_CASOS,
    BLOCO_CLIMA,
    BLOCO_VETOR,
    BRACOS,
    NOMES_DOS_BRACOS,
    Braco,
    montar_matriz_do_braco,
    nomes_das_variaveis_do_bloco,
    nomes_das_variaveis_do_braco,
    obter_braco,
)
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.variaveis import construir_variaveis_de_origem, montar_matriz_do_horizonte

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"

COLUNA_DE_DATA = CONFIGURACAO_DADOS.coluna_de_data
COLUNA_DE_CASOS = CONFIGURACAO_DADOS.coluna_de_casos
NOME_DO_VETOR = CONFIGURACAO_VARIAVEIS.coluna_do_vetor
PRIMEIRO_DOMINGO_SINTETICO = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)

QUANTIDADE_DE_VARIAVEIS_POR_BRACO = {
    "completo": 22,
    "sem_casos": 16,
    "sem_clima": 16,
    "sem_vetor": 16,
    "so_casos": 10,
    "so_clima": 10,
    "so_vetor": 10,
    "so_calendario": 4,
}


def montar_tabela_sintetica(semanas: int) -> pd.DataFrame:
    """Tabela de domingos consecutivos sem nenhum ausente (casos 10, 20, 30...; vetor 1,0 + 0,5 por semana)."""
    posicoes = np.arange(semanas, dtype="float64")
    return pd.DataFrame(
        {
            COLUNA_DE_DATA: pd.date_range(PRIMEIRO_DOMINGO_SINTETICO, periods=semanas, freq="W-SUN"),
            "semana": posicoes + 1.0,
            COLUNA_DE_CASOS: 10.0 * (posicoes + 1.0),
            "temp_media": 15.0 + posicoes,
            "temp_max": 20.0 + 2.0 * posicoes,
            "umid_media": 60.0 + 3.0 * posicoes,
            "pressao_media": 1010.0 + 0.1 * posicoes,
            NOME_DO_VETOR: 1.0 + 0.5 * posicoes,
        }
    )


def matriz_do_braco(tabela: pd.DataFrame, horizonte: int, nome_do_braco: str) -> pd.DataFrame:
    """Atalho: monta a matriz do braco com as configuracoes padrao."""
    return montar_matriz_do_braco(tabela, horizonte, nome_do_braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)


def datas_de_origem_da_matriz(matriz: pd.DataFrame) -> set[pd.Timestamp]:
    """Conjunto das datas de origem de uma matriz."""
    return set(matriz[COLUNA_DATA_DE_ORIGEM])


# ---------------------------------------------------------------------------
# Definicao dos bracos e dos blocos
# ---------------------------------------------------------------------------


def test_os_oito_bracos_estao_na_ordem_da_pre_declaracao() -> None:
    """completo, sem_casos, sem_clima, sem_vetor, so_casos, so_clima, so_vetor, so_calendario."""
    assert NOMES_DOS_BRACOS == (
        "completo",
        "sem_casos",
        "sem_clima",
        "sem_vetor",
        "so_casos",
        "so_clima",
        "so_vetor",
        "so_calendario",
    )


def test_os_blocos_tem_6_6_6_e_4_variaveis_e_juntos_sao_as_22_do_modelo() -> None:
    """Casos 6, clima 6, vetor 6, calendario 4; sem sobreposicao; a uniao e `nomes_das_variaveis`."""
    tamanhos_esperados = {BLOCO_CASOS: 6, BLOCO_CLIMA: 6, BLOCO_VETOR: 6, BLOCO_CALENDARIO: 4}
    todos_os_nomes: list[str] = []
    for bloco, tamanho in tamanhos_esperados.items():
        nomes_do_bloco = nomes_das_variaveis_do_bloco(bloco, CONFIGURACAO_VARIAVEIS)
        assert len(nomes_do_bloco) == tamanho, bloco
        todos_os_nomes.extend(nomes_do_bloco)

    assert len(set(todos_os_nomes)) == 22
    assert set(todos_os_nomes) == set(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis)


def test_o_conteudo_de_cada_bloco_bate_com_a_tabela_1_do_artigo() -> None:
    """Nomes exatos de cada bloco, conferidos a mao contra a Tabela 1."""
    assert set(nomes_das_variaveis_do_bloco(BLOCO_CASOS, CONFIGURACAO_VARIAVEIS)) == {
        "casos", "casos_lag1", "casos_lag2", "casos_lag3", "casos_lag4", "casos_mm4",
    }
    assert set(nomes_das_variaveis_do_bloco(BLOCO_CLIMA, CONFIGURACAO_VARIAVEIS)) == {
        "temp_media_lag4", "umid_media", "temp_media_lag3", "temp_max", "pressao_media_lag3", "pressao_media_lag4",
    }
    assert set(nomes_das_variaveis_do_bloco(BLOCO_VETOR, CONFIGURACAO_VARIAVEIS)) == {
        "aedes_aegypti_por_armadilha",
        "aedes_aegypti_por_armadilha_lag1",
        "aedes_aegypti_por_armadilha_lag2",
        "aedes_aegypti_por_armadilha_lag3",
        "aedes_aegypti_por_armadilha_lag4",
        "vetor_mm4",
    }
    assert set(nomes_das_variaveis_do_bloco(BLOCO_CALENDARIO, CONFIGURACAO_VARIAVEIS)) == {
        "sem_sin", "sem_cos", "alvo_sin", "alvo_cos",
    }


def test_bloco_desconhecido_e_rejeitado() -> None:
    """`nomes_das_variaveis_do_bloco` com bloco inexistente levanta ValueError."""
    with pytest.raises(ValueError, match="Bloco desconhecido"):
        nomes_das_variaveis_do_bloco("el_nino", CONFIGURACAO_VARIAVEIS)


@pytest.mark.parametrize("nome_do_braco", NOMES_DOS_BRACOS)
def test_quantidade_de_variaveis_de_cada_braco(nome_do_braco: str) -> None:
    """completo 22; tirar uma fonte deixa 16; uma fonte so deixa 10; so o calendario deixa 4."""
    nomes = nomes_das_variaveis_do_braco(nome_do_braco, CONFIGURACAO_VARIAVEIS)
    assert len(nomes) == QUANTIDADE_DE_VARIAVEIS_POR_BRACO[nome_do_braco]
    assert len(set(nomes)) == len(nomes)


@pytest.mark.parametrize("nome_do_braco", NOMES_DOS_BRACOS)
def test_as_variaveis_de_cada_braco_seguem_a_ordem_oficial_do_modelo(nome_do_braco: str) -> None:
    """A ordem das colunas e a de `nomes_das_variaveis`, filtrada (treinar e prever usam a mesma)."""
    nomes_do_braco = nomes_das_variaveis_do_braco(nome_do_braco, CONFIGURACAO_VARIAVEIS)
    nomes_na_ordem_oficial = []
    for nome_da_variavel in CONFIGURACAO_VARIAVEIS.nomes_das_variaveis:
        if nome_da_variavel in nomes_do_braco:
            nomes_na_ordem_oficial.append(nome_da_variavel)
    assert nomes_do_braco == nomes_na_ordem_oficial


def test_ordem_exata_das_colunas_do_so_vetor_e_do_sem_vetor() -> None:
    """Conferencia literal da ordem: o calendario da origem vem antes do vetor, o do alvo depois."""
    assert nomes_das_variaveis_do_braco("so_vetor", CONFIGURACAO_VARIAVEIS) == [
        "sem_sin",
        "sem_cos",
        "aedes_aegypti_por_armadilha",
        "aedes_aegypti_por_armadilha_lag1",
        "aedes_aegypti_por_armadilha_lag2",
        "aedes_aegypti_por_armadilha_lag3",
        "aedes_aegypti_por_armadilha_lag4",
        "vetor_mm4",
        "alvo_sin",
        "alvo_cos",
    ]
    nomes_do_sem_vetor = nomes_das_variaveis_do_braco("sem_vetor", CONFIGURACAO_VARIAVEIS)
    assert nomes_do_sem_vetor[:8] == [
        "casos", "casos_lag1", "casos_lag2", "casos_lag3", "casos_lag4", "casos_mm4", "sem_sin", "sem_cos",
    ]
    assert nomes_do_sem_vetor[-2:] == ["alvo_sin", "alvo_cos"]


def test_o_calendario_esta_em_todos_os_bracos() -> None:
    """Pre-declaracao, secao 4: K entra em todos os bracos."""
    nomes_do_calendario = nomes_das_variaveis_do_bloco(BLOCO_CALENDARIO, CONFIGURACAO_VARIAVEIS)
    for braco in BRACOS:
        nomes_do_braco = nomes_das_variaveis_do_braco(braco.nome, CONFIGURACAO_VARIAVEIS)
        for nome_do_calendario in nomes_do_calendario:
            assert nome_do_calendario in nomes_do_braco, (braco.nome, nome_do_calendario)


def test_braco_sem_calendario_e_rejeitado() -> None:
    """Um braco sem o bloco calendario viola a pre-declaracao."""
    with pytest.raises(ValueError, match="calendario"):
        Braco("so_casos_sem_calendario", (BLOCO_CASOS,))


def test_braco_com_bloco_desconhecido_ou_repetido_e_rejeitado() -> None:
    """Bloco fora dos quatro ou repetido levanta ValueError na criacao."""
    with pytest.raises(ValueError, match="Bloco desconhecido"):
        Braco("com_enso", (BLOCO_CALENDARIO, "enso"))
    with pytest.raises(ValueError, match="repetido"):
        Braco("repetido", (BLOCO_CALENDARIO, BLOCO_CASOS, BLOCO_CASOS))


def test_obter_braco_devolve_o_braco_e_rejeita_nome_desconhecido() -> None:
    """Busca por nome."""
    assert obter_braco("sem_vetor").blocos == (BLOCO_CASOS, BLOCO_CLIMA, BLOCO_CALENDARIO)
    with pytest.raises(ValueError, match="Braco desconhecido"):
        obter_braco("so_enso")
    with pytest.raises(ValueError, match="Braco desconhecido"):
        nomes_das_variaveis_do_braco("so_enso", CONFIGURACAO_VARIAVEIS)


def test_braco_e_imutavel() -> None:
    """A dataclass e frozen: trocar os blocos de um braco depois de criado e erro."""
    braco = obter_braco("completo")
    with pytest.raises(dataclasses.FrozenInstanceError):
        braco.nome = "outro"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Matriz de cada braco (tabelas sinteticas)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nome_do_braco", NOMES_DOS_BRACOS)
def test_colunas_da_matriz_sao_datas_variaveis_do_braco_e_alvo(nome_do_braco: str) -> None:
    """`data_origem`, `data_alvo`, as variaveis do braco na ordem oficial e `y_h`."""
    matriz = matriz_do_braco(montar_tabela_sintetica(30), 3, nome_do_braco)
    nomes_do_braco = nomes_das_variaveis_do_braco(nome_do_braco, CONFIGURACAO_VARIAVEIS)
    assert list(matriz.columns) == [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, *nomes_do_braco, COLUNA_DO_ALVO]


def test_o_dropna_olha_so_as_colunas_do_braco_ausente_no_vetor() -> None:
    """Vetor ausente na posicao 15: o sem_vetor (e o so_casos) MANTEM as origens que o completo perde.

    O vetor ausente em 15 contamina o vetor das origens 15 a 19 (valor, lags 1-4)
    e a media movel das origens 15 a 18. O `completo` e o `so_vetor` perdem 15 a 19;
    os bracos sem vetor nao perdem nenhuma.
    """
    tabela = montar_tabela_sintetica(40)
    tabela.loc[15, NOME_DO_VETOR] = np.nan
    horizonte = 2

    origens_perdidas = {PRIMEIRO_DOMINGO_SINTETICO + posicao * UMA_SEMANA for posicao in range(15, 20)}
    origens_do_completo = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, "completo"))
    origens_do_sem_vetor = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, "sem_vetor"))
    origens_do_so_casos = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, "so_casos"))
    origens_do_so_vetor = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, "so_vetor"))

    assert origens_perdidas.isdisjoint(origens_do_completo)
    assert origens_perdidas.isdisjoint(origens_do_so_vetor)
    assert origens_perdidas <= origens_do_sem_vetor
    assert origens_perdidas <= origens_do_so_casos
    assert len(origens_do_sem_vetor) == len(origens_do_completo) + len(origens_perdidas)


def test_o_dropna_olha_so_as_colunas_do_braco_ausente_no_clima() -> None:
    """`temp_max` ausente na posicao 12 (sem defasagem): so a origem 12 sai, e so dos bracos com clima."""
    tabela = montar_tabela_sintetica(40)
    tabela.loc[12, "temp_max"] = np.nan
    origem_afetada = PRIMEIRO_DOMINGO_SINTETICO + 12 * UMA_SEMANA
    horizonte = 2

    for nome_do_braco in ("completo", "sem_casos", "sem_vetor", "so_clima"):
        origens = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, nome_do_braco))
        assert origem_afetada not in origens, nome_do_braco
    for nome_do_braco in ("sem_clima", "so_casos", "so_vetor", "so_calendario"):
        origens = datas_de_origem_da_matriz(matriz_do_braco(tabela, horizonte, nome_do_braco))
        assert origem_afetada in origens, nome_do_braco


def test_o_alvo_ausente_derruba_a_linha_em_todos_os_bracos() -> None:
    """Casos ausentes no fim (corte de maturidade): sem `y_h`, a origem sai de TODOS os bracos."""
    tabela = montar_tabela_sintetica(30)
    horizonte = 3
    tabela.loc[26:, COLUNA_DE_CASOS] = np.nan
    ultima_origem_com_alvo = PRIMEIRO_DOMINGO_SINTETICO + 25 * UMA_SEMANA - horizonte * UMA_SEMANA

    for nome_do_braco in NOMES_DOS_BRACOS:
        matriz = matriz_do_braco(tabela, horizonte, nome_do_braco)
        assert matriz[COLUNA_DATA_DE_ORIGEM].max() <= ultima_origem_com_alvo, nome_do_braco
        assert matriz[COLUNA_DO_ALVO].notna().all()


def test_so_calendario_perde_apenas_as_linhas_sem_alvo() -> None:
    """Sem nenhuma variavel de fonte, so o alvo (e a semana-alvo) limitam as linhas: tabela de 30 semanas, h = 3 -> 27 linhas."""
    matriz = matriz_do_braco(montar_tabela_sintetica(30), 3, "so_calendario")
    assert len(matriz) == 27
    assert matriz[COLUNA_DATA_DE_ORIGEM].iloc[0] == PRIMEIRO_DOMINGO_SINTETICO


def test_valores_de_uma_linha_do_sem_vetor_conferidos_a_mao() -> None:
    """h = 2, posicao 10: casos = 110, casos_lag4 = 70, alvo = casos da posicao 12 = 130; o vetor nao aparece."""
    matriz = matriz_do_braco(montar_tabela_sintetica(30), 2, "sem_vetor")
    data_de_origem = PRIMEIRO_DOMINGO_SINTETICO + 10 * UMA_SEMANA
    linha = matriz.loc[matriz[COLUNA_DATA_DE_ORIGEM] == data_de_origem].iloc[0]

    assert linha["casos"] == 110.0
    assert linha["casos_lag4"] == 70.0
    assert linha[COLUNA_DO_ALVO] == 130.0
    assert linha[COLUNA_DATA_ALVO] == data_de_origem + 2 * UMA_SEMANA
    assert NOME_DO_VETOR not in matriz.columns
    assert "vetor_mm4" not in matriz.columns


def test_o_indice_e_renumerado_de_zero_e_a_ordem_e_cronologica() -> None:
    """Como em `montar_matriz_do_horizonte`."""
    tabela = montar_tabela_sintetica(40)
    tabela.loc[15, NOME_DO_VETOR] = np.nan
    matriz = matriz_do_braco(tabela, 2, "completo")
    assert list(matriz.index) == list(range(len(matriz)))
    assert matriz[COLUNA_DATA_DE_ORIGEM].is_monotonic_increasing


def test_a_tabela_de_entrada_nao_e_modificada() -> None:
    """A funcao e pura."""
    tabela = montar_tabela_sintetica(30)
    copia = tabela.copy(deep=True)
    for nome_do_braco in NOMES_DOS_BRACOS:
        matriz_do_braco(tabela, 4, nome_do_braco)
    pd.testing.assert_frame_equal(tabela, copia)


def test_tabela_de_uma_linha_devolve_matriz_vazia_com_as_mesmas_colunas() -> None:
    """Uma unica semana nao tem historico nem alvo; as colunas saem iguais."""
    matriz = matriz_do_braco(montar_tabela_sintetica(1), 1, "sem_vetor")
    assert len(matriz) == 0
    nomes_do_braco = nomes_das_variaveis_do_braco("sem_vetor", CONFIGURACAO_VARIAVEIS)
    assert list(matriz.columns) == [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, *nomes_do_braco, COLUNA_DO_ALVO]


@pytest.mark.parametrize("horizonte_invalido", [0, -1, 1.5, True, "2"])
def test_horizonte_invalido_e_rejeitado(horizonte_invalido: object) -> None:
    """Horizonte tem de ser inteiro >= 1 (e nao bool)."""
    with pytest.raises(ValueError, match="horizonte"):
        matriz_do_braco(montar_tabela_sintetica(30), horizonte_invalido, "completo")  # type: ignore[arg-type]


def test_braco_desconhecido_e_rejeitado_na_montagem() -> None:
    """Nome de braco inexistente levanta ValueError."""
    with pytest.raises(ValueError, match="Braco desconhecido"):
        matriz_do_braco(montar_tabela_sintetica(30), 2, "so_enso")


def test_grade_com_buraco_e_rejeitada() -> None:
    """As defasagens sao por posicao: uma semana faltando na grade e erro (mesma validacao das variaveis)."""
    tabela = montar_tabela_sintetica(30).drop(index=10).reset_index(drop=True)
    with pytest.raises(ValueError, match="grade"):
        matriz_do_braco(tabela, 2, "sem_vetor")


# ---------------------------------------------------------------------------
# Diferencial com os dados reais
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


def comparar_valores_bit_a_bit(coluna_nova: pd.Series, coluna_original: pd.Series) -> bool:
    """Igualdade exata (NaN = NaN), sem tolerancia."""
    return bool(np.array_equal(coluna_nova.to_numpy(), coluna_original.to_numpy(), equal_nan=True))


@pytest.mark.parametrize("horizonte", CONFIGURACAO_AVALIACAO.horizontes)
def test_o_braco_completo_e_identico_bit_a_bit_a_matriz_do_horizonte(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
) -> None:
    """Datas, colunas, ordem, valores (sem tolerancia), dtypes e indice: `completo` == `montar_matriz_do_horizonte`."""
    matriz_original = montar_matriz_do_horizonte(tabela_cortada, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    matriz_do_completo = matriz_do_braco(tabela_cortada, horizonte, "completo")

    assert list(matriz_do_completo.columns) == list(matriz_original.columns)
    assert matriz_do_completo.shape == matriz_original.shape
    assert matriz_do_completo.index.equals(matriz_original.index)
    for nome_da_coluna in matriz_original.columns:
        assert matriz_do_completo[nome_da_coluna].dtype == matriz_original[nome_da_coluna].dtype, nome_da_coluna
        assert comparar_valores_bit_a_bit(matriz_do_completo[nome_da_coluna], matriz_original[nome_da_coluna]), (
            horizonte,
            nome_da_coluna,
        )


@pytest.mark.parametrize("nome_do_braco", NOMES_DOS_BRACOS[1:])
def test_cada_braco_coincide_com_o_completo_nas_origens_em_comum(
    tabela_cortada: pd.DataFrame,
    nome_do_braco: str,
) -> None:
    """Em h = 12 (e h = 1): nas origens que o braco e o completo tem, as colunas do braco sao iguais, bit a bit.

    Mudam as LINHAS (os bracos sem vetor ganham as semanas da enchente), nunca o valor de uma celula.
    """
    for horizonte in (1, 12):
        matriz_do_completo = matriz_do_braco(tabela_cortada, horizonte, "completo")
        matriz_do_outro_braco = matriz_do_braco(tabela_cortada, horizonte, nome_do_braco)
        origens_em_comum = datas_de_origem_da_matriz(matriz_do_completo) & datas_de_origem_da_matriz(
            matriz_do_outro_braco
        )
        assert len(origens_em_comum) > 0

        do_completo = matriz_do_completo.loc[matriz_do_completo[COLUNA_DATA_DE_ORIGEM].isin(origens_em_comum)]
        do_outro = matriz_do_outro_braco.loc[matriz_do_outro_braco[COLUNA_DATA_DE_ORIGEM].isin(origens_em_comum)]
        for nome_da_coluna in matriz_do_outro_braco.columns:
            assert comparar_valores_bit_a_bit(
                do_outro[nome_da_coluna].reset_index(drop=True),
                do_completo[nome_da_coluna].reset_index(drop=True),
            ), (horizonte, nome_do_braco, nome_da_coluna)


def test_o_sem_vetor_recupera_exatamente_as_semanas_sem_vetor(tabela_cortada: pd.DataFrame) -> None:
    """As origens que o `sem_vetor` tem a mais que o `completo` sao exatamente as de vetor incompleto.

    O `completo` exige as 6 variaveis do vetor (valor, 4 defasagens e media movel); o `sem_vetor`
    nao. Logo: origens do `sem_vetor` = origens do `completo` + (origens do `sem_vetor` com
    alguma variavel do vetor ausente). A conta do lado direito sai das variaveis de origem
    calculadas pelo modulo certificado, sem passar por `montar_matriz_do_braco`.
    """
    variaveis_de_origem = construir_variaveis_de_origem(tabela_cortada, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    colunas_do_vetor = nomes_das_variaveis_do_bloco(BLOCO_VETOR, CONFIGURACAO_VARIAVEIS)
    vetor_incompleto = variaveis_de_origem[colunas_do_vetor].isna().any(axis=1)
    datas_da_tabela = tabela_cortada[COLUNA_DE_DATA]
    origens_com_vetor_incompleto = set(datas_da_tabela.loc[vetor_incompleto])

    for horizonte in (1, 12):
        origens_do_completo = datas_de_origem_da_matriz(matriz_do_braco(tabela_cortada, horizonte, "completo"))
        origens_do_sem_vetor = datas_de_origem_da_matriz(matriz_do_braco(tabela_cortada, horizonte, "sem_vetor"))
        origens_extras = origens_do_sem_vetor - origens_do_completo

        assert origens_do_completo <= origens_do_sem_vetor
        assert len(origens_extras) > 0
        assert origens_extras == origens_do_sem_vetor & origens_com_vetor_incompleto
        assert origens_do_completo.isdisjoint(origens_com_vetor_incompleto)
