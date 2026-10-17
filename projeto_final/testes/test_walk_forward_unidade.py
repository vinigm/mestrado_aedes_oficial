"""Testes de unidade do walk-forward (`aedes.walk_forward`) em dados sinteticos pequenos.

Cobrem as regras do laco, nao os numeros do artigo (esses sao do teste diferencial):
    - o treino da origem `t` nunca ve `data_alvo > t`;
    - numero de previsoes = linhas depois do treino minimo (e com passo > 1);
    - retreino do zero a cada origem (um modelo novo por previsao);
    - determinismo com a mesma semente;
    - a previsao nao depende de rotulo que ainda nao existia em `t`;
    - matriz com buraco: o corte e por DATA, nao por posicao;
    - validacoes de entrada e matriz vazia.
"""

import dataclasses

import numpy as np
import pandas as pd
import pytest

import aedes.walk_forward as walk_forward
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DO_ALVO,
    CONFIGURACAO_AVALIACAO,
    FOLHA_5,
    FOLHA_20,
)
from aedes.walk_forward import (
    COLUNAS_DAS_PREVISOES,
    criar_modelo,
    executar_walk_forward,
    nomes_das_variaveis_da_matriz,
    validar_matriz_para_walk_forward,
)

PRIMEIRA_ORIGEM = pd.Timestamp("2020-01-05")
UMA_SEMANA = pd.Timedelta(weeks=1)

# Treino minimo pequeno dos testes: 15 linhas deixam h=12 com treino (15 - 12 + 1 = 4 linhas).
TREINO_MINIMO_DO_TESTE = 15

# Modelo pequeno so para os testes ficarem rapidos; as regras do laco nao dependem dele.
MODELO_PEQUENO = dataclasses.replace(FOLHA_5, nome="histgb_teste", numero_de_iteracoes=20, folha_minima=2)
AVALIACAO_PEQUENA = dataclasses.replace(CONFIGURACAO_AVALIACAO, treino_minimo_em_semanas=TREINO_MINIMO_DO_TESTE)


def montar_matriz_sintetica(
    quantidade_de_linhas: int,
    horizonte: int,
    semanas_de_origem_puladas: tuple[int, ...] = (),
) -> pd.DataFrame:
    """Matriz no formato de `montar_matriz_do_horizonte`, com 2 variaveis e um alvo conhecido.

    `semanas_de_origem_puladas` apaga linhas (como o `dropna` apaga as semanas
    da enchente), deixando buracos na grade de origens e renumerando o indice.
    """
    gerador = np.random.default_rng(123)
    posicoes = np.arange(quantidade_de_linhas)
    datas_de_origem = PRIMEIRA_ORIGEM + posicoes * UMA_SEMANA
    variavel_a = gerador.normal(size=quantidade_de_linhas)
    variavel_b = gerador.normal(size=quantidade_de_linhas)
    alvo = 3.0 * variavel_a - 2.0 * variavel_b + gerador.normal(scale=0.1, size=quantidade_de_linhas)

    matriz = pd.DataFrame(
        {
            COLUNA_DATA_DE_ORIGEM: datas_de_origem,
            COLUNA_DATA_ALVO: datas_de_origem + horizonte * UMA_SEMANA,
            "variavel_a": variavel_a,
            "variavel_b": variavel_b,
            COLUNA_DO_ALVO: alvo,
        }
    )
    if len(semanas_de_origem_puladas) > 0:
        matriz = matriz.drop(index=list(semanas_de_origem_puladas))
    return matriz.reset_index(drop=True)


class ModeloEspiao:
    """Modelo falso: guarda o treino que recebeu e preve sempre 0 (so para inspecionar o laco)."""

    instancias_criadas: list["ModeloEspiao"] = []

    def __init__(self) -> None:
        self.variaveis_do_treino: pd.DataFrame | None = None
        self.alvo_do_treino: pd.Series | None = None
        self.variaveis_do_teste: pd.DataFrame | None = None
        ModeloEspiao.instancias_criadas.append(self)

    def fit(self, variaveis: pd.DataFrame, alvo: pd.Series) -> "ModeloEspiao":
        self.variaveis_do_treino = variaveis
        self.alvo_do_treino = alvo
        return self

    def predict(self, variaveis: pd.DataFrame) -> np.ndarray:
        self.variaveis_do_teste = variaveis
        return np.zeros(len(variaveis))


@pytest.fixture
def espioes(monkeypatch: pytest.MonkeyPatch) -> list[ModeloEspiao]:
    """Troca a criacao do modelo pelo espiao e devolve a lista de modelos criados."""
    ModeloEspiao.instancias_criadas = []

    def criar_modelo_espiao(configuracao_modelo: object) -> ModeloEspiao:
        return ModeloEspiao()

    monkeypatch.setattr(walk_forward, "criar_modelo", criar_modelo_espiao)
    return ModeloEspiao.instancias_criadas


# --------------------------------------------------------------------------- saida


@pytest.mark.parametrize("horizonte", [1, 4, 12])
def test_numero_de_previsoes_e_linhas_menos_treino_minimo(horizonte: int) -> None:
    matriz = montar_matriz_sintetica(40, horizonte)
    previsoes = executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    assert len(previsoes) == 40 - TREINO_MINIMO_DO_TESTE


def test_passo_maior_que_um_pula_origens() -> None:
    matriz = montar_matriz_sintetica(40, 2)
    avaliacao_com_passo = dataclasses.replace(AVALIACAO_PEQUENA, passo_do_retreino_em_semanas=3)
    previsoes = executar_walk_forward(matriz, 2, MODELO_PEQUENO, avaliacao_com_passo)
    origens_esperadas = list(range(TREINO_MINIMO_DO_TESTE, 40, 3))
    assert len(previsoes) == len(origens_esperadas)
    datas_esperadas = matriz[COLUNA_DATA_DE_ORIGEM].iloc[origens_esperadas].to_numpy()
    np.testing.assert_array_equal(previsoes[COLUNA_DATA_DE_ORIGEM].to_numpy(), datas_esperadas)


def test_colunas_datas_e_real_da_saida() -> None:
    horizonte = 3
    matriz = montar_matriz_sintetica(30, horizonte)
    previsoes = executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)

    assert list(previsoes.columns) == list(COLUNAS_DAS_PREVISOES)
    assert (previsoes["h"] == horizonte).all()
    assert previsoes["real"].dtype == np.float64
    assert previsoes["previsto"].dtype == np.float64

    linhas_de_teste = matriz.iloc[TREINO_MINIMO_DO_TESTE:]
    np.testing.assert_array_equal(
        previsoes[COLUNA_DATA_DE_ORIGEM].to_numpy(),
        linhas_de_teste[COLUNA_DATA_DE_ORIGEM].to_numpy(),
    )
    # A previsao e para a semana `origem + horizonte`.
    np.testing.assert_array_equal(
        previsoes[COLUNA_DATA_ALVO].to_numpy(),
        (linhas_de_teste[COLUNA_DATA_DE_ORIGEM] + horizonte * UMA_SEMANA).to_numpy(),
    )
    np.testing.assert_array_equal(previsoes["real"].to_numpy(), linhas_de_teste[COLUNA_DO_ALVO].to_numpy())


def test_matriz_de_entrada_nao_e_modificada() -> None:
    matriz = montar_matriz_sintetica(30, 2)
    copia = matriz.copy(deep=True)
    executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    pd.testing.assert_frame_equal(matriz, copia)


def test_matriz_sem_linhas_depois_do_treino_minimo_devolve_vazio_com_colunas() -> None:
    matriz = montar_matriz_sintetica(TREINO_MINIMO_DO_TESTE, 2)  # exatamente o treino minimo: nenhuma origem de teste
    previsoes = executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    assert previsoes.empty
    assert list(previsoes.columns) == list(COLUNAS_DAS_PREVISOES)


def test_uma_unica_origem_de_teste() -> None:
    matriz = montar_matriz_sintetica(TREINO_MINIMO_DO_TESTE + 1, 2)
    previsoes = executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    assert len(previsoes) == 1
    assert previsoes[COLUNA_DATA_DE_ORIGEM].iloc[0] == matriz[COLUNA_DATA_DE_ORIGEM].iloc[TREINO_MINIMO_DO_TESTE]


# --------------------------------------------------------------------------- corte temporal


@pytest.mark.parametrize("horizonte", [1, 5, 12])
def test_o_treino_da_origem_t_nunca_ve_data_alvo_posterior_a_t(
    horizonte: int, espioes: list[ModeloEspiao]
) -> None:
    matriz = montar_matriz_sintetica(40, horizonte)
    previsoes = executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)

    assert len(espioes) == len(previsoes)
    for modelo, data_de_origem in zip(espioes, previsoes[COLUNA_DATA_DE_ORIGEM]):
        indices_do_treino = modelo.variaveis_do_treino.index
        datas_do_alvo_no_treino = matriz.loc[indices_do_treino, COLUNA_DATA_ALVO]
        assert (datas_do_alvo_no_treino <= data_de_origem).all()


def test_treino_da_primeira_origem_tem_linhas_menos_horizonte_mais_um(
    espioes: list[ModeloEspiao],
) -> None:
    # Grade densa, origem de teste na posicao do treino minimo: entram as posicoes 0..(minimo - h).
    for horizonte in (1, 4, 12):
        espioes.clear()
        matriz = montar_matriz_sintetica(40, 12)
        matriz = matriz.copy()
        matriz[COLUNA_DATA_ALVO] = matriz[COLUNA_DATA_DE_ORIGEM] + horizonte * UMA_SEMANA
        executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)
        primeiro_modelo = espioes[0]
        linhas_esperadas = TREINO_MINIMO_DO_TESTE - horizonte + 1
        assert len(primeiro_modelo.variaveis_do_treino) == linhas_esperadas


def test_com_buraco_o_corte_e_por_data_e_nao_por_posicao(espioes: list[ModeloEspiao]) -> None:
    # Apaga 3 origens consecutivas (como a enchente de 2024). Recuar `h` POSICOES nao e recuar `h` SEMANAS.
    horizonte = 4
    matriz = montar_matriz_sintetica(40, horizonte, semanas_de_origem_puladas=(6, 7, 8))
    previsoes = executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)

    for modelo, data_de_origem in zip(espioes, previsoes[COLUNA_DATA_DE_ORIGEM]):
        indices_do_treino = modelo.variaveis_do_treino.index
        datas_do_alvo_no_treino = matriz.loc[indices_do_treino, COLUNA_DATA_ALVO]
        assert (datas_do_alvo_no_treino <= data_de_origem).all()

        # E nao falta nenhuma linha ja respondida: o treino e TODAS as com data_alvo <= t.
        todas_as_respondidas = matriz.index[matriz[COLUNA_DATA_ALVO] <= data_de_origem]
        assert list(indices_do_treino) == list(todas_as_respondidas)


def test_retreino_do_zero_um_modelo_novo_por_origem(espioes: list[ModeloEspiao]) -> None:
    matriz = montar_matriz_sintetica(30, 2)
    previsoes = executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    assert len(espioes) == len(previsoes)
    identidades = {id(modelo) for modelo in espioes}
    assert len(identidades) == len(espioes)


def test_ordem_das_colunas_no_fit_e_no_predict_e_a_da_matriz(espioes: list[ModeloEspiao]) -> None:
    matriz = montar_matriz_sintetica(20, 2)
    executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    assert list(espioes[0].variaveis_do_treino.columns) == ["variavel_a", "variavel_b"]
    assert list(espioes[0].variaveis_do_teste.columns) == ["variavel_a", "variavel_b"]


def test_a_previsao_nao_depende_de_rotulo_que_ainda_nao_existia() -> None:
    """Modelo REAL: trocar o `y_h` das linhas ainda sem resposta na origem nao muda a previsao dela."""
    horizonte = 6
    matriz = montar_matriz_sintetica(30, horizonte)
    primeira_posicao_de_teste = TREINO_MINIMO_DO_TESTE

    matriz_com_futuro_trocado = matriz.copy()
    # Linhas de posicao > minimo - h ainda nao tinham resposta em t = posicao do minimo (inclui a propria linha de teste).
    posicoes_sem_resposta = matriz.index[matriz.index > primeira_posicao_de_teste - horizonte]
    matriz_com_futuro_trocado.loc[posicoes_sem_resposta, COLUNA_DO_ALVO] = 1.0e6

    previsoes = executar_walk_forward(matriz, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    previsoes_trocadas = executar_walk_forward(
        matriz_com_futuro_trocado, horizonte, MODELO_PEQUENO, AVALIACAO_PEQUENA
    )

    assert previsoes["previsto"].iloc[0] == previsoes_trocadas["previsto"].iloc[0]


# --------------------------------------------------------------------------- determinismo e modelo


def test_mesma_semente_mesma_previsao_bit_a_bit() -> None:
    matriz = montar_matriz_sintetica(40, 3)
    primeira = executar_walk_forward(matriz, 3, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    segunda = executar_walk_forward(matriz, 3, MODELO_PEQUENO, AVALIACAO_PEQUENA)
    pd.testing.assert_frame_equal(primeira, segunda, check_exact=True)


def test_criar_modelo_usa_a_configuracao_e_cria_um_novo_a_cada_chamada() -> None:
    modelo_a = criar_modelo(FOLHA_5)
    modelo_b = criar_modelo(FOLHA_5)
    assert modelo_a is not modelo_b
    assert modelo_a.get_params()["min_samples_leaf"] == 5
    assert criar_modelo(FOLHA_20).get_params()["min_samples_leaf"] == 20
    assert modelo_a.get_params()["random_state"] == 42
    assert modelo_a.get_params()["loss"] == "quantile"
    assert modelo_a.get_params()["quantile"] == 0.85


def test_o_modelo_preve_algo_proximo_do_alvo_em_dado_facil() -> None:
    matriz = montar_matriz_sintetica(60, 1)
    modelo_de_media = dataclasses.replace(MODELO_PEQUENO, perda="squared_error", numero_de_iteracoes=100)
    previsoes = executar_walk_forward(matriz, 1, modelo_de_media, AVALIACAO_PEQUENA)
    erro_medio = float(np.mean(np.abs(previsoes["real"] - previsoes["previsto"])))
    desvio_do_alvo = float(np.std(matriz[COLUNA_DO_ALVO]))
    assert erro_medio < desvio_do_alvo


# --------------------------------------------------------------------------- validacoes


@pytest.mark.parametrize("horizonte_invalido", [0, -1, 1.5, True, "2", None])
def test_horizonte_invalido_levanta_erro(horizonte_invalido: object) -> None:
    matriz = montar_matriz_sintetica(20, 2)
    with pytest.raises(ValueError, match="horizonte"):
        executar_walk_forward(matriz, horizonte_invalido, MODELO_PEQUENO, AVALIACAO_PEQUENA)


@pytest.mark.parametrize("coluna", [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, COLUNA_DO_ALVO])
def test_coluna_obrigatoria_ausente_levanta_keyerror(coluna: str) -> None:
    matriz = montar_matriz_sintetica(20, 2).drop(columns=[coluna])
    with pytest.raises(KeyError, match=coluna):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_ausente_em_variavel_levanta_erro() -> None:
    matriz = montar_matriz_sintetica(20, 2)
    matriz.loc[5, "variavel_a"] = np.nan
    with pytest.raises(ValueError, match="ausente"):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_ausente_no_alvo_levanta_erro() -> None:
    matriz = montar_matriz_sintetica(20, 2)
    matriz.loc[19, COLUNA_DO_ALVO] = np.nan
    with pytest.raises(ValueError, match="ausente"):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_datas_de_origem_fora_de_ordem_levantam_erro() -> None:
    matriz = montar_matriz_sintetica(20, 2)
    matriz = matriz.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="crescente"):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_data_alvo_de_outro_horizonte_levanta_erro() -> None:
    matriz = montar_matriz_sintetica(20, 3)
    with pytest.raises(ValueError, match="data_alvo"):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_matriz_sem_variaveis_levanta_erro() -> None:
    matriz = montar_matriz_sintetica(20, 2).drop(columns=["variavel_a", "variavel_b"])
    with pytest.raises(ValueError, match="nenhuma variavel"):
        executar_walk_forward(matriz, 2, MODELO_PEQUENO, AVALIACAO_PEQUENA)


def test_origem_sem_treino_levanta_erro_claro() -> None:
    # Com treino minimo 1 e horizonte 12, a origem da posicao 1 ainda nao tem nenhuma linha respondida.
    matriz = montar_matriz_sintetica(20, 12)
    avaliacao_sem_folga = dataclasses.replace(AVALIACAO_PEQUENA, treino_minimo_em_semanas=1)
    with pytest.raises(ValueError, match="Nenhuma linha de treino"):
        executar_walk_forward(matriz, 12, MODELO_PEQUENO, avaliacao_sem_folga)


def test_nomes_das_variaveis_seguem_a_ordem_da_matriz() -> None:
    matriz = montar_matriz_sintetica(12, 2)
    assert nomes_das_variaveis_da_matriz(matriz) == ["variavel_a", "variavel_b"]
    matriz_com_ordem_trocada = matriz[
        [COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO, "variavel_b", "variavel_a", COLUNA_DO_ALVO]
    ]
    assert validar_matriz_para_walk_forward(matriz_com_ordem_trocada, 2) == ["variavel_b", "variavel_a"]
