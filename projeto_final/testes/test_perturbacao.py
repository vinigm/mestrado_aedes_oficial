"""Testes de `aedes.perturbacao`: a perturbacao do ultimo bit para o piso de ruido.

Unidade (matriz sintetica):
    - so as colunas CONTINUAS mudam (contagens inteiras, datas e `y_h` ficam como estao);
    - cada celula continua vira exatamente `nextafter(x, +inf)` ou `nextafter(x, -inf)`
      (diferenca de 1 ulp, nem mais nem menos), com as duas direcoes presentes;
    - determinismo por semente e sementes diferentes dando matrizes diferentes;
    - zeros: perturbados por padrao (literal da pre-declaracao) e preservados com `perturbar_zeros=False`;
    - a matriz de entrada nao e modificada; entradas invalidas.
    - `alinhar_matriz_do_gabarito`: troca so as variaveis e recusa linhas, colunas, datas ou alvo diferentes.

Dados reais:
    - as 17 colunas continuas e as 5 inteiras (casos e lags) do `completo`;
    - o gabarito `matriz_hXX.csv` alinha com a matriz do pacote nos 12 horizontes e difere dela
      so no ultimo bit (a diferenca de arredondamento que o achado do ciclo 3 observou).
"""

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
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.perturbacao import (
    alinhar_matriz_do_gabarito,
    identificar_colunas_continuas,
    perturbar_ultimo_bit,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"

PRIMEIRA_ORIGEM = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)
QUANTIDADE_DE_LINHAS = 200

COLUNAS_CONTINUAS_ESPERADAS_DO_COMPLETO = {
    "casos_mm4", "sem_sin", "sem_cos",
    "temp_media_lag4", "umid_media", "temp_media_lag3", "temp_max", "pressao_media_lag3", "pressao_media_lag4",
    "aedes_aegypti_por_armadilha", "aedes_aegypti_por_armadilha_lag1", "aedes_aegypti_por_armadilha_lag2",
    "aedes_aegypti_por_armadilha_lag3", "aedes_aegypti_por_armadilha_lag4", "vetor_mm4",
    "alvo_sin", "alvo_cos",
}
COLUNAS_INTEIRAS_ESPERADAS_DO_COMPLETO = {"casos", "casos_lag1", "casos_lag2", "casos_lag3", "casos_lag4"}


def montar_matriz_sintetica() -> pd.DataFrame:
    """Matriz com: contagem inteira, duas continuas (uma com zeros exatos e uma so com zeros e inteiros), datas e alvo.

    Colunas: `contagem` (inteiros), `continua_a` (normais), `continua_com_zeros` (metade zeros),
    `quase_inteira` (so valores inteiros, parece continua mas nao e), e `y_h`.
    """
    gerador = np.random.default_rng(7)
    posicoes = np.arange(QUANTIDADE_DE_LINHAS)
    datas_de_origem = PRIMEIRA_ORIGEM + posicoes * UMA_SEMANA
    continua_com_zeros = gerador.normal(size=QUANTIDADE_DE_LINHAS)
    continua_com_zeros[::2] = 0.0
    return pd.DataFrame(
        {
            COLUNA_DATA_DE_ORIGEM: datas_de_origem,
            COLUNA_DATA_ALVO: datas_de_origem + 2 * UMA_SEMANA,
            "contagem": gerador.integers(0, 50, size=QUANTIDADE_DE_LINHAS).astype(float),
            "continua_a": gerador.normal(size=QUANTIDADE_DE_LINHAS) * 10.0,
            "continua_com_zeros": continua_com_zeros,
            "quase_inteira": gerador.integers(0, 3, size=QUANTIDADE_DE_LINHAS).astype(float),
            COLUNA_DO_ALVO: gerador.integers(0, 100, size=QUANTIDADE_DE_LINHAS).astype(float),
        }
    )


COLUNAS_CONTINUAS_SINTETICAS = ["continua_a", "continua_com_zeros"]
COLUNAS_QUE_NAO_PODEM_MUDAR = [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, "contagem", "quase_inteira", COLUNA_DO_ALVO]


# ---------------------------------------------------------------------------
# identificar_colunas_continuas
# ---------------------------------------------------------------------------


def test_so_coluna_com_valor_nao_inteiro_e_continua() -> None:
    """Contagem e coluna de inteiros (mesmo com zeros) ficam de fora; `continua_*` entram, na ordem das colunas."""
    assert identificar_colunas_continuas(montar_matriz_sintetica()) == COLUNAS_CONTINUAS_SINTETICAS


def test_uma_unica_celula_nao_inteira_basta_para_a_coluna_ser_continua() -> None:
    """'Ao menos um valor nao inteiro'."""
    matriz = montar_matriz_sintetica()
    matriz.loc[5, "quase_inteira"] = 1.5
    assert "quase_inteira" in identificar_colunas_continuas(matriz)


def test_ausente_ou_infinito_em_variavel_e_rejeitado() -> None:
    """A perturbacao so faz sentido numa matriz sem ausente (saida do walk-forward valido)."""
    com_nan = montar_matriz_sintetica()
    com_nan.loc[3, "continua_a"] = np.nan
    with pytest.raises(ValueError, match="ausente ou infinito"):
        identificar_colunas_continuas(com_nan)

    com_infinito = montar_matriz_sintetica()
    com_infinito.loc[3, "continua_a"] = np.inf
    with pytest.raises(ValueError, match="ausente ou infinito"):
        perturbar_ultimo_bit(com_infinito, 1)


def test_matriz_sem_as_colunas_de_datas_ou_alvo_e_rejeitada() -> None:
    """KeyError claro quando falta `y_h`."""
    sem_alvo = montar_matriz_sintetica().drop(columns=[COLUNA_DO_ALVO])
    with pytest.raises(KeyError):
        identificar_colunas_continuas(sem_alvo)
    with pytest.raises(KeyError):
        perturbar_ultimo_bit(sem_alvo, 1)


# ---------------------------------------------------------------------------
# perturbar_ultimo_bit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("semente", [1, 2, 3, 4])
def test_so_as_colunas_continuas_mudam(semente: int) -> None:
    """Datas, contagens (inteiras), `quase_inteira` e `y_h` saem identicos; as continuas mudam em TODAS as celulas."""
    matriz = montar_matriz_sintetica()
    perturbada = perturbar_ultimo_bit(matriz, semente)

    for nome_da_coluna in COLUNAS_QUE_NAO_PODEM_MUDAR:
        assert np.array_equal(perturbada[nome_da_coluna].to_numpy(), matriz[nome_da_coluna].to_numpy()), nome_da_coluna
    for nome_da_coluna in COLUNAS_CONTINUAS_SINTETICAS:
        celulas_iguais = perturbada[nome_da_coluna].to_numpy() == matriz[nome_da_coluna].to_numpy()
        assert not celulas_iguais.any(), nome_da_coluna


@pytest.mark.parametrize("semente", [1, 2, 3, 4])
def test_cada_celula_continua_vira_exatamente_um_ulp_para_cima_ou_para_baixo(semente: int) -> None:
    """`novo == nextafter(x, +inf)` ou `novo == nextafter(x, -inf)`: nem metade de um ulp, nem dois."""
    matriz = montar_matriz_sintetica()
    perturbada = perturbar_ultimo_bit(matriz, semente)

    for nome_da_coluna in COLUNAS_CONTINUAS_SINTETICAS:
        originais = matriz[nome_da_coluna].to_numpy()
        novos = perturbada[nome_da_coluna].to_numpy()
        um_ulp_para_cima = np.nextafter(originais, np.inf)
        um_ulp_para_baixo = np.nextafter(originais, -np.inf)
        e_para_cima = novos == um_ulp_para_cima
        e_para_baixo = novos == um_ulp_para_baixo
        assert (e_para_cima | e_para_baixo).all(), nome_da_coluna
        # As duas direcoes aparecem (200 celulas, probabilidade de uma so direcao ~ 2^-199).
        assert e_para_cima.any(), nome_da_coluna
        assert e_para_baixo.any(), nome_da_coluna


def test_a_diferenca_em_cada_celula_nao_passa_de_um_ulp_relativo() -> None:
    """Para valores nao nulos: |novo - x| <= 1 ulp de x (`np.spacing`)."""
    matriz = montar_matriz_sintetica()
    perturbada = perturbar_ultimo_bit(matriz, 3)
    originais = matriz["continua_a"].to_numpy()
    novos = perturbada["continua_a"].to_numpy()
    diferencas = np.abs(novos - originais)
    assert (diferencas <= np.spacing(np.abs(originais))).all()
    assert (diferencas > 0.0).all()


def test_a_mesma_semente_da_sempre_a_mesma_matriz() -> None:
    """Determinismo."""
    matriz = montar_matriz_sintetica()
    primeira = perturbar_ultimo_bit(matriz, 2)
    segunda = perturbar_ultimo_bit(matriz, 2)
    pd.testing.assert_frame_equal(primeira, segunda, check_exact=True)


def test_sementes_diferentes_dao_matrizes_diferentes() -> None:
    """As quatro sementes da pre-declaracao produzem quatro matrizes distintas."""
    matriz = montar_matriz_sintetica()
    perturbadas = [perturbar_ultimo_bit(matriz, semente) for semente in (1, 2, 3, 4)]
    for posicao_a in range(4):
        for posicao_b in range(posicao_a + 1, 4):
            iguais = np.array_equal(
                perturbadas[posicao_a]["continua_a"].to_numpy(),
                perturbadas[posicao_b]["continua_a"].to_numpy(),
            )
            assert not iguais, (posicao_a + 1, posicao_b + 1)


def test_a_direcao_sorteada_nao_e_sempre_a_mesma_entre_colunas() -> None:
    """Um gerador percorre as colunas em sequencia: duas colunas identicas recebem direcoes DIFERENTES."""
    matriz = montar_matriz_sintetica()
    matriz["continua_b"] = matriz["continua_a"]
    perturbada = perturbar_ultimo_bit(matriz, 1)
    assert not np.array_equal(perturbada["continua_a"].to_numpy(), perturbada["continua_b"].to_numpy())


def test_zeros_exatos_sao_perturbados_por_padrao_conforme_a_pre_declaracao() -> None:
    """Literal: um zero vira +-5e-324 (o menor denormal)."""
    matriz = montar_matriz_sintetica()
    perturbada = perturbar_ultimo_bit(matriz, 1)
    celulas_zero = matriz["continua_com_zeros"].to_numpy() == 0.0
    assert celulas_zero.sum() == QUANTIDADE_DE_LINHAS // 2
    novos_no_lugar_dos_zeros = np.abs(perturbada["continua_com_zeros"].to_numpy()[celulas_zero])
    assert (novos_no_lugar_dos_zeros == 5e-324).all()


def test_com_perturbar_zeros_falso_os_zeros_ficam_e_o_resto_muda() -> None:
    """`perturbar_zeros=False`: zeros intactos; as demais celulas continuas mudam um ulp."""
    matriz = montar_matriz_sintetica()
    perturbada = perturbar_ultimo_bit(matriz, 1, perturbar_zeros=False)
    originais = matriz["continua_com_zeros"].to_numpy()
    novos = perturbada["continua_com_zeros"].to_numpy()
    celulas_zero = originais == 0.0
    assert (novos[celulas_zero] == 0.0).all()
    assert (novos[~celulas_zero] != originais[~celulas_zero]).all()
    assert (perturbada["continua_a"].to_numpy() != matriz["continua_a"].to_numpy()).all()


def test_a_matriz_de_entrada_nao_e_modificada_e_a_saida_tem_mesmas_colunas_indice_e_dtypes() -> None:
    """Pureza e formato preservado."""
    matriz = montar_matriz_sintetica()
    copia = matriz.copy(deep=True)
    perturbada = perturbar_ultimo_bit(matriz, 4)
    pd.testing.assert_frame_equal(matriz, copia, check_exact=True)
    assert list(perturbada.columns) == list(matriz.columns)
    assert perturbada.index.equals(matriz.index)
    assert (perturbada.dtypes == matriz.dtypes).all()


@pytest.mark.parametrize("semente_invalida", ["1", 1.5, True, None])
def test_semente_que_nao_e_inteiro_e_rejeitada(semente_invalida: object) -> None:
    """A semente tem de ser inteiro (e nao bool)."""
    with pytest.raises(ValueError, match="semente"):
        perturbar_ultimo_bit(montar_matriz_sintetica(), semente_invalida)  # type: ignore[arg-type]


def test_matriz_sem_nenhuma_coluna_continua_volta_igual() -> None:
    """So contagens: nada a perturbar, a matriz sai igual (copia)."""
    matriz = montar_matriz_sintetica().drop(columns=COLUNAS_CONTINUAS_SINTETICAS)
    perturbada = perturbar_ultimo_bit(matriz, 1)
    pd.testing.assert_frame_equal(perturbada, matriz, check_exact=True)
    assert perturbada is not matriz


# ---------------------------------------------------------------------------
# alinhar_matriz_do_gabarito
# ---------------------------------------------------------------------------


def gabarito_parecido_com_a_matriz(matriz: pd.DataFrame) -> pd.DataFrame:
    """Copia com as variaveis alteradas no ultimo bit, como o CSV do gabarito, e as colunas embaralhadas."""
    gabarito = matriz.copy(deep=True)
    gabarito["continua_a"] = np.nextafter(gabarito["continua_a"].to_numpy(), np.inf)
    colunas_embaralhadas = list(reversed(list(gabarito.columns)))
    return gabarito[colunas_embaralhadas]


def test_o_alinhamento_traz_as_variaveis_do_gabarito_e_mantem_datas_alvo_e_ordem_do_pacote() -> None:
    """A saida tem as colunas na ordem do PACOTE e os valores de variavel do GABARITO."""
    matriz = montar_matriz_sintetica()
    gabarito = gabarito_parecido_com_a_matriz(matriz)
    alinhada = alinhar_matriz_do_gabarito(matriz, gabarito)

    assert list(alinhada.columns) == list(matriz.columns)
    assert np.array_equal(alinhada["continua_a"].to_numpy(), gabarito["continua_a"].to_numpy())
    assert not np.array_equal(alinhada["continua_a"].to_numpy(), matriz["continua_a"].to_numpy())
    for nome_da_coluna in [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, COLUNA_DO_ALVO, "contagem"]:
        assert np.array_equal(alinhada[nome_da_coluna].to_numpy(), matriz[nome_da_coluna].to_numpy())


def test_o_alinhamento_recusa_colunas_linhas_datas_ou_alvo_diferentes() -> None:
    """Qualquer desalinhamento levanta ValueError, sem tentar consertar."""
    matriz = montar_matriz_sintetica()

    com_coluna_a_menos = gabarito_parecido_com_a_matriz(matriz).drop(columns=["continua_a"])
    with pytest.raises(ValueError, match="Colunas diferentes"):
        alinhar_matriz_do_gabarito(matriz, com_coluna_a_menos)

    com_linha_a_menos = gabarito_parecido_com_a_matriz(matriz).iloc[:-1]
    with pytest.raises(ValueError, match="linhas"):
        alinhar_matriz_do_gabarito(matriz, com_linha_a_menos)

    com_data_trocada = gabarito_parecido_com_a_matriz(matriz)
    com_data_trocada.loc[10, COLUNA_DATA_DE_ORIGEM] = pd.Timestamp("1999-01-03")
    with pytest.raises(ValueError, match=COLUNA_DATA_DE_ORIGEM):
        alinhar_matriz_do_gabarito(matriz, com_data_trocada)

    com_alvo_diferente = gabarito_parecido_com_a_matriz(matriz)
    com_alvo_diferente.loc[10, COLUNA_DO_ALVO] = 12345.0
    with pytest.raises(ValueError, match=COLUNA_DO_ALVO):
        alinhar_matriz_do_gabarito(matriz, com_alvo_diferente)


def test_o_alinhamento_nao_modifica_a_matriz_do_pacote() -> None:
    """Funcao pura."""
    matriz = montar_matriz_sintetica()
    copia = matriz.copy(deep=True)
    alinhar_matriz_do_gabarito(matriz, gabarito_parecido_com_a_matriz(matriz))
    pd.testing.assert_frame_equal(matriz, copia, check_exact=True)


# ---------------------------------------------------------------------------
# Dados reais
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.mark.parametrize("horizonte", [1, 12])
def test_as_colunas_continuas_do_completo_sao_as_17_esperadas(tabela_cortada: pd.DataFrame, horizonte: int) -> None:
    """Casos e as 4 defasagens (contagens) ficam de fora; as demais 17 variaveis sao continuas."""
    matriz = montar_matriz_do_braco(tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    continuas = identificar_colunas_continuas(matriz)
    assert set(continuas) == COLUNAS_CONTINUAS_ESPERADAS_DO_COMPLETO
    assert len(continuas) == 17
    assert COLUNAS_INTEIRAS_ESPERADAS_DO_COMPLETO.isdisjoint(continuas)


def test_a_perturbacao_da_matriz_real_so_toca_as_17_continuas(tabela_cortada: pd.DataFrame) -> None:
    """Na matriz real do `completo` (h = 4): datas, `y_h` e as 5 contagens idem; as 17 continuas a 1 ulp."""
    matriz = montar_matriz_do_braco(tabela_cortada, 4, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    perturbada = perturbar_ultimo_bit(matriz, 1)

    for nome_da_coluna in matriz.columns:
        antes = matriz[nome_da_coluna].to_numpy()
        depois = perturbada[nome_da_coluna].to_numpy()
        if nome_da_coluna in COLUNAS_CONTINUAS_ESPERADAS_DO_COMPLETO:
            assert not (antes == depois).any(), nome_da_coluna
            diferenca_maxima_em_ulps = np.max(np.abs(depois - antes) / np.spacing(np.abs(antes) + (antes == 0.0)))
            assert diferenca_maxima_em_ulps <= 1.0 + 1e-12, nome_da_coluna
        else:
            assert np.array_equal(antes, depois), nome_da_coluna


@pytest.mark.parametrize("horizonte", CONFIGURACAO_AVALIACAO.horizontes)
def test_o_gabarito_csv_alinha_com_a_matriz_do_pacote_e_difere_so_no_ultimo_bit(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
) -> None:
    """A perturbacao `csv` e viavel nos 12 horizontes: mesmas linhas e colunas; variaveis diferem em < 1e-12."""
    matriz_do_pacote = montar_matriz_do_braco(
        tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    caminho = PASTA_DO_GABARITO / f"matriz_h{horizonte:02d}.csv"
    matriz_do_gabarito = pd.read_csv(caminho, parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO])

    alinhada = alinhar_matriz_do_gabarito(matriz_do_pacote, matriz_do_gabarito)
    assert list(alinhada.columns) == list(matriz_do_pacote.columns)

    for nome_da_variavel in CONFIGURACAO_VARIAVEIS.nomes_das_variaveis:
        diferenca = np.abs(alinhada[nome_da_variavel].to_numpy() - matriz_do_pacote[nome_da_variavel].to_numpy())
        assert diferenca.max() < 1e-12, (horizonte, nome_da_variavel)
    for nome_da_coluna in COLUNAS_INTEIRAS_ESPERADAS_DO_COMPLETO:
        assert np.array_equal(alinhada[nome_da_coluna].to_numpy(), matriz_do_pacote[nome_da_coluna].to_numpy())
