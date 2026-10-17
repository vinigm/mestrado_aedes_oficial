"""Testes das configuracoes do ciclo 2: variaveis, modelo e avaliacao.

Conferem tres coisas:
    1. coerencia interna (a configuracao rejeita o que e incoerente);
    2. imutabilidade (dataclasses frozen, sem estado a trocar em execucao);
    3. fidelidade ao codigo antigo: nomes e ordem das 22 variaveis, clima
       congelado, hiperparametros (inclusive os do padrao do scikit-learn) e
       janela de avaliacao (102 semanas por horizonte nas previsoes salvas).
"""

import dataclasses
import pathlib

import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingRegressor

from aedes.configuracao import (
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
    ConfiguracaoAvaliacao,
    ConfiguracaoModelo,
    ConfiguracaoVariaveis,
    VariavelDeClima,
    nome_da_variavel_defasada,
)

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"

# Parametros que o codigo antigo passa ao HistGradientBoostingRegressor, copiados
# literalmente de `modelagem_aedes/config/experimentos/cidade_referencia.py:72-84`
# (folha 5) e de
# `analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/rodar.py:30-42`
# (folha 20). Tudo que NAO esta aqui fica no padrao do scikit-learn.
PARAMETROS_DO_CODIGO_ANTIGO_FOLHA_5 = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 5,
    "random_state": 42,
    "loss": "quantile",
    "quantile": 0.85,
}
PARAMETROS_DO_CODIGO_ANTIGO_FOLHA_20 = {
    "max_iter": 250,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "random_state": 42,
    "loss": "quantile",
    "quantile": 0.85,
}

SEMANAS_AVALIADAS_POR_HORIZONTE = 102


# ---------------------------------------------------------------------------
# ConfiguracaoVariaveis
# ---------------------------------------------------------------------------


def test_nomes_e_ordem_das_22_variaveis_sao_os_do_cabecalho_do_gabarito() -> None:
    """A ordem do modelo na configuracao e o cabecalho de `matriz_h01.csv` (sem datas e sem y_h)."""
    cabecalho = pd.read_csv(PASTA_DO_GABARITO / "matriz_h01.csv", nrows=0)
    colunas_do_gabarito = list(cabecalho.columns)
    variaveis_do_gabarito = colunas_do_gabarito[2:-1]

    assert len(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis) == 22
    assert list(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis) == variaveis_do_gabarito


def test_a_configuracao_padrao_tem_defasagens_1_a_4_e_janela_4() -> None:
    """Defasagens de casos e de vetor 1..4, media movel de 4 semanas, divisor 52."""
    assert CONFIGURACAO_VARIAVEIS.defasagens_de_casos == (1, 2, 3, 4)
    assert CONFIGURACAO_VARIAVEIS.defasagens_do_vetor == (1, 2, 3, 4)
    assert CONFIGURACAO_VARIAVEIS.janela_da_media_movel == 4
    assert CONFIGURACAO_VARIAVEIS.semanas_por_ano == 52
    assert CONFIGURACAO_VARIAVEIS.nome_da_media_movel_de_casos() == "casos_mm4"
    assert CONFIGURACAO_VARIAVEIS.nome_da_media_movel_do_vetor() == "vetor_mm4"


def test_a_receita_gera_exatamente_os_nomes_da_lista() -> None:
    """Os nomes gerados pela receita e os da lista final formam o mesmo conjunto."""
    gerados = set(CONFIGURACAO_VARIAVEIS.nomes_gerados_pela_receita())
    listados = set(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis)
    assert gerados == listados


def test_o_clima_congelado_tem_6_colunas_com_origem_e_defasagem() -> None:
    """Origem e defasagem de cada uma das 6 colunas de clima."""
    esperado = [
        ("temp_media_lag4", "temp_media", 4),
        ("umid_media", "umid_media", 0),
        ("temp_media_lag3", "temp_media", 3),
        ("temp_max", "temp_max", 0),
        ("pressao_media_lag3", "pressao_media", 3),
        ("pressao_media_lag4", "pressao_media", 4),
    ]
    medido = []
    for variavel_de_clima in CONFIGURACAO_VARIAVEIS.variaveis_de_clima:
        medido.append(
            (
                variavel_de_clima.nome,
                variavel_de_clima.coluna_de_origem,
                variavel_de_clima.defasagem_em_semanas,
            )
        )
    assert medido == esperado


def test_nome_da_variavel_defasada() -> None:
    """`casos` e 2 viram `casos_lag2`."""
    assert nome_da_variavel_defasada("casos", 2) == "casos_lag2"


def test_configuracao_de_variaveis_e_imutavel() -> None:
    """Atribuir a um campo de uma dataclass frozen levanta erro (nada de estado trocado em execucao)."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONFIGURACAO_VARIAVEIS.defasagens_de_casos = (1, 2)  # type: ignore[misc]


def test_nome_faltando_na_lista_e_rejeitado() -> None:
    """Retirar um nome gerado pela receita da lista final e erro."""
    nomes_sem_um = tuple(
        nome for nome in CONFIGURACAO_VARIAVEIS.nomes_das_variaveis if nome != "casos_lag4"
    )
    with pytest.raises(ValueError, match="casos_lag4"):
        dataclasses.replace(CONFIGURACAO_VARIAVEIS, nomes_das_variaveis=nomes_sem_um)


def test_nome_sobrando_na_lista_e_rejeitado() -> None:
    """Nome que a receita nao gera, na lista final, e erro."""
    nomes_com_extra = CONFIGURACAO_VARIAVEIS.nomes_das_variaveis + ("precip_total_mm",)
    with pytest.raises(ValueError, match="precip_total_mm"):
        dataclasses.replace(CONFIGURACAO_VARIAVEIS, nomes_das_variaveis=nomes_com_extra)


def test_nome_repetido_na_lista_e_rejeitado() -> None:
    """Dois nomes iguais na lista final sao erro."""
    nomes = list(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis)
    nomes[1] = nomes[0]
    with pytest.raises(ValueError, match="repetido"):
        dataclasses.replace(CONFIGURACAO_VARIAVEIS, nomes_das_variaveis=tuple(nomes))


@pytest.mark.parametrize("defasagens_invalidas", [(0, 1), (-1,), (1, 1), (1.5,), (True,)])
def test_defasagem_invalida_e_rejeitada(defasagens_invalidas: tuple) -> None:
    """Defasagem tem de ser inteiro >= 1 e sem repeticao."""
    with pytest.raises(ValueError, match="defasagens_de_casos"):
        dataclasses.replace(CONFIGURACAO_VARIAVEIS, defasagens_de_casos=defasagens_invalidas)


@pytest.mark.parametrize("janela_invalida", [0, -4, 4.0, True])
def test_janela_invalida_e_rejeitada(janela_invalida: object) -> None:
    """A janela da media movel tem de ser inteiro >= 1."""
    with pytest.raises(ValueError, match="janela_da_media_movel"):
        dataclasses.replace(CONFIGURACAO_VARIAVEIS, janela_da_media_movel=janela_invalida)


def test_variavel_de_clima_com_nome_incoerente_e_rejeitada() -> None:
    """O nome tem de ser a origem (defasagem 0) ou origem_lagK."""
    with pytest.raises(ValueError, match="incoerente"):
        VariavelDeClima("temp_media_lag3", "temp_media", 4)
    with pytest.raises(ValueError, match="incoerente"):
        VariavelDeClima("temp_max_lag1", "temp_max", 0)


def test_variavel_de_clima_com_defasagem_negativa_e_rejeitada() -> None:
    """Defasagem de clima negativa (olhar o futuro) e erro."""
    with pytest.raises(ValueError, match="defasagem_em_semanas"):
        VariavelDeClima("temp_max", "temp_max", -1)


def test_configuracao_alternativa_so_com_defasagens_1_e_2_e_valida() -> None:
    """Uma configuracao com outras defasagens existe sem mexer na padrao (nada e global)."""
    nomes_removidos = {
        "casos_lag3",
        "casos_lag4",
        "aedes_aegypti_por_armadilha_lag3",
        "aedes_aegypti_por_armadilha_lag4",
    }
    nomes_restantes = tuple(
        nome for nome in CONFIGURACAO_VARIAVEIS.nomes_das_variaveis if nome not in nomes_removidos
    )
    alternativa = dataclasses.replace(
        CONFIGURACAO_VARIAVEIS,
        defasagens_de_casos=(1, 2),
        defasagens_do_vetor=(1, 2),
        nomes_das_variaveis=nomes_restantes,
    )
    assert isinstance(alternativa, ConfiguracaoVariaveis)
    assert len(alternativa.nomes_das_variaveis) == 18
    assert CONFIGURACAO_VARIAVEIS.defasagens_de_casos == (1, 2, 3, 4)
    assert len(CONFIGURACAO_VARIAVEIS.nomes_das_variaveis) == 22


# ---------------------------------------------------------------------------
# ConfiguracaoModelo
# ---------------------------------------------------------------------------


def test_as_duas_folhas_so_diferem_na_folha_minima_e_no_nome() -> None:
    """FOLHA_5 e FOLHA_20 tem os mesmos hiperparametros, exceto `folha_minima` (5 x 20) e `nome`."""
    campos_que_diferem = []
    for campo in dataclasses.fields(ConfiguracaoModelo):
        valor_da_folha_5 = getattr(FOLHA_5, campo.name)
        valor_da_folha_20 = getattr(FOLHA_20, campo.name)
        if valor_da_folha_5 != valor_da_folha_20:
            campos_que_diferem.append(campo.name)

    assert sorted(campos_que_diferem) == ["folha_minima", "nome"]
    assert FOLHA_5.folha_minima == 5
    assert FOLHA_20.folha_minima == 20


def test_hiperparametros_do_modelo_de_referencia() -> None:
    """Quantil 0,85, 250 iteracoes, taxa 0,05, 15 folhas, semente 42."""
    for configuracao in (FOLHA_5, FOLHA_20):
        assert configuracao.perda == "quantile"
        assert configuracao.quantil == 0.85
        assert configuracao.numero_de_iteracoes == 250
        assert configuracao.taxa_de_aprendizado == 0.05
        assert configuracao.maximo_de_folhas == 15
        assert configuracao.semente_aleatoria == 42


@pytest.mark.parametrize(
    ("configuracao", "parametros_do_codigo_antigo"),
    [
        (FOLHA_5, PARAMETROS_DO_CODIGO_ANTIGO_FOLHA_5),
        (FOLHA_20, PARAMETROS_DO_CODIGO_ANTIGO_FOLHA_20),
    ],
)
def test_o_modelo_novo_tem_os_mesmos_parametros_do_antigo_inclusive_os_padroes(
    configuracao: ConfiguracaoModelo, parametros_do_codigo_antigo: dict[str, object]
) -> None:
    """`get_params()` completo (todos os parametros, inclusive early_stopping) e identico ao do antigo.

    O antigo passa 7 parametros e deixa o resto no padrao do sklearn instalado;
    o novo escreve tudo. Se o padrao do sklearn mudar (ou se um valor da
    configuracao for digitado errado), este teste falha. Nenhum modelo e treinado.
    """
    modelo_antigo = HistGradientBoostingRegressor(**parametros_do_codigo_antigo)
    modelo_novo = HistGradientBoostingRegressor(**configuracao.parametros_do_sklearn())

    assert modelo_novo.get_params() == modelo_antigo.get_params()


def test_a_parada_antecipada_automatica_fica_desligada_com_a_matriz_deste_projeto() -> None:
    """`early_stopping='auto'` so liga com mais de 10.000 amostras; a matriz tem menos de 400."""
    assert FOLHA_5.parada_antecipada == "auto"
    amostras_maximas_da_matriz = 400
    limite_do_auto_do_sklearn = 10_000
    assert amostras_maximas_da_matriz <= limite_do_auto_do_sklearn


def test_parametros_do_sklearn_devolve_um_dicionario_novo_a_cada_chamada() -> None:
    """Alterar o dicionario devolvido nao altera a configuracao nem a proxima chamada."""
    primeiro = FOLHA_5.parametros_do_sklearn()
    primeiro["min_samples_leaf"] = 999
    segundo = FOLHA_5.parametros_do_sklearn()
    assert segundo["min_samples_leaf"] == 5
    assert FOLHA_5.folha_minima == 5


def test_configuracao_do_modelo_e_imutavel() -> None:
    """Dataclass frozen: trocar o quantil em execucao e erro."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        FOLHA_5.quantil = 0.5  # type: ignore[misc]


@pytest.mark.parametrize("quantil_invalido", [0.0, 1.0, -0.1, 1.5])
def test_quantil_fora_do_intervalo_e_rejeitado(quantil_invalido: float) -> None:
    """O quantil tem de estar estritamente entre 0 e 1."""
    with pytest.raises(ValueError, match="quantil"):
        dataclasses.replace(FOLHA_5, quantil=quantil_invalido)


@pytest.mark.parametrize(
    ("campo", "valor_invalido"),
    [
        ("numero_de_iteracoes", 0),
        ("taxa_de_aprendizado", 0.0),
        ("maximo_de_folhas", 1),
        ("folha_minima", 0),
        ("maximo_de_bins", 1),
    ],
)
def test_hiperparametro_impossivel_e_rejeitado(campo: str, valor_invalido: object) -> None:
    """Iteracoes, taxa, folhas, folha minima e bins fora do dominio sao erro na criacao."""
    with pytest.raises(ValueError, match=campo):
        dataclasses.replace(FOLHA_5, **{campo: valor_invalido})


# ---------------------------------------------------------------------------
# ConfiguracaoAvaliacao
# ---------------------------------------------------------------------------


def test_a_avaliacao_padrao() -> None:
    """Horizontes 1 a 12, treino minimo 104, retreino semanal, janelas de 2024-01-07 a 2026-02-01."""
    assert CONFIGURACAO_AVALIACAO.horizontes == tuple(range(1, 13))
    assert CONFIGURACAO_AVALIACAO.treino_minimo_em_semanas == 104
    assert CONFIGURACAO_AVALIACAO.passo_do_retreino_em_semanas == 1
    assert CONFIGURACAO_AVALIACAO.fim_da_calibracao == pd.Timestamp("2023-12-31")
    assert CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada == pd.Timestamp("2024-01-07")
    assert CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada == pd.Timestamp("2026-02-01")


def test_configuracao_de_avaliacao_e_imutavel() -> None:
    """Dataclass frozen."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONFIGURACAO_AVALIACAO.treino_minimo_em_semanas = 52  # type: ignore[misc]


def test_a_janela_da_avaliacao_pega_102_semanas_por_horizonte_e_braco() -> None:
    """Nas previsoes salvas da bateria de 23/09: 102 semanas-alvo na janela, em cada braco e horizonte.

    Tambem confere que a janela comeca no primeiro domingo depois do fim da
    calibracao (nenhuma data-alvo cai no intervalo entre as duas) e termina na
    ultima data-alvo salva.
    """
    previsoes = pd.read_csv(PASTA_DO_GABARITO / "previsoes_referencia.csv", parse_dates=["data_alvo"])
    primeira = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    ultima = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
    fim_da_calibracao = CONFIGURACAO_AVALIACAO.fim_da_calibracao

    dentro_da_janela = previsoes[(previsoes["data_alvo"] >= primeira) & (previsoes["data_alvo"] <= ultima)]
    contagens = dentro_da_janela.groupby(["braco", "h"]).size()
    assert len(contagens) == 2 * 12
    assert (contagens == SEMANAS_AVALIADAS_POR_HORIZONTE).all()

    entre_calibracao_e_avaliacao = previsoes[
        (previsoes["data_alvo"] > fim_da_calibracao) & (previsoes["data_alvo"] < primeira)
    ]
    assert entre_calibracao_e_avaliacao.empty
    assert previsoes["data_alvo"].max() == ultima
    assert dentro_da_janela["data_alvo"].min() == primeira


@pytest.mark.parametrize("horizontes_invalidos", [(), (0, 1), (2, 1), (1, 1), (1.5,), (True,)])
def test_horizontes_invalidos_sao_rejeitados(horizontes_invalidos: tuple) -> None:
    """Horizontes: nao vazio, inteiros >= 1, crescentes e sem repeticao."""
    with pytest.raises(ValueError, match="horizontes"):
        dataclasses.replace(CONFIGURACAO_AVALIACAO, horizontes=horizontes_invalidos)


@pytest.mark.parametrize("campo", ["treino_minimo_em_semanas", "passo_do_retreino_em_semanas"])
@pytest.mark.parametrize("valor_invalido", [0, -1, 1.5, True])
def test_treino_minimo_e_passo_invalidos_sao_rejeitados(campo: str, valor_invalido: object) -> None:
    """Treino minimo e passo: inteiros >= 1."""
    with pytest.raises(ValueError, match=campo):
        dataclasses.replace(CONFIGURACAO_AVALIACAO, **{campo: valor_invalido})


def test_datas_fora_de_ordem_sao_rejeitadas() -> None:
    """fim da calibracao < primeira avaliada <= ultima avaliada."""
    with pytest.raises(ValueError, match="fora de ordem"):
        dataclasses.replace(
            CONFIGURACAO_AVALIACAO, fim_da_calibracao=pd.Timestamp("2024-01-07")
        )
    with pytest.raises(ValueError, match="fora de ordem"):
        dataclasses.replace(
            CONFIGURACAO_AVALIACAO, ultima_data_alvo_avaliada=pd.Timestamp("2023-12-31")
        )
    assert isinstance(CONFIGURACAO_AVALIACAO, ConfiguracaoAvaliacao)
