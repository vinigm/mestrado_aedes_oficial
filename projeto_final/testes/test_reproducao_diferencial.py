"""Diferenciais COM modelo treinado: as celulas dos scripts E6b, E6c e E7 reproduzem a referencia certificada.

Cada teste chama o `rodar_um_pedaco` do PROPRIO script (a funcao que a rodada completa usa), com a matriz truncada
nas primeiras 112 linhas (8 origens de teste). Como o treino de cada origem so olha linhas anteriores, essas 8
previsoes sao as mesmas que a matriz inteira dara. Cada celula leva alguns segundos.

    E6b: HistGB q0,85 M1 (previsao TRUNCADA em zero) == `max(referencia, 0)`;
    E6c: a referencia da grade, na fase 1 (matriz cortada na calibracao) e na fase 2 (matriz inteira) == referencia;
    E7:  o q0,85 das folhas 5 e 20 == `referencia` e `HistGB_folha20_M1` (a trava da pre-declaracao).

Tolerancia: 1e-12 (a trava da pre-declaracao e 1e-9). A referencia certificada nao e reproduzida bit a bit nem pelo
proprio `executar_walk_forward` de hoje (diferenca de 4e-16 a 2e-13, independente do numero de threads); a igualdade
EXATA entre o laco do pacote e o das etapas e testada em `test_grade.py`.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

import experimentos.e6b_grade30 as e6b
import experimentos.e6c_grade18 as e6c
import experimentos.e7_wis as e7
from aedes.bracos import montar_matriz_do_braco
from aedes.configuracao import CONFIGURACAO_DADOS
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.grade import ALGORITMO_HISTGB, CONJUNTO_M1, ConfiguracaoDaGrade
from aedes.hiperparametros import NOME_DA_REFERENCIA
from experimentos.comum_reproducao import RegistradorDeLog, ler_previsoes_da_referencia

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
LINHAS_DA_MATRIZ_TRUNCADA = 112
ORIGENS_ESPERADAS = 8
TOLERANCIA = 1e-12


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    tabela_crua = montar_tabela_a_partir_dos_bytes(CAMINHO_TABELA.read_bytes(), CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


@pytest.fixture(scope="module")
def referencia() -> pd.DataFrame:
    """As previsoes certificadas do ciclo 3."""
    return ler_previsoes_da_referencia()


def montar_matriz_do_braco_truncada(*argumentos, **opcoes) -> pd.DataFrame:
    """`montar_matriz_do_braco` devolvendo so as primeiras 112 linhas (as 8 primeiras origens de teste)."""
    matriz = montar_matriz_do_braco(*argumentos, **opcoes)
    return matriz.iloc[:LINHAS_DA_MATRIZ_TRUNCADA].reset_index(drop=True)


def comparar_com_a_referencia(
    previsoes: pd.DataFrame, referencia: pd.DataFrame, nome_do_braco: str, horizonte: int, truncar_em_zero: bool
) -> float:
    """Maior diferenca absoluta do `previsto` contra a referencia do braco e horizonte, casando por `data_origem`."""
    da_referencia = referencia.loc[(referencia["braco"] == nome_do_braco) & (referencia["h"] == horizonte)]
    pareadas = previsoes.merge(da_referencia, on="data_origem", suffixes=("_novo", "_referencia"))
    assert len(pareadas) == len(previsoes) == ORIGENS_ESPERADAS
    previsto_da_referencia = pareadas["previsto_referencia"]
    if truncar_em_zero:
        previsto_da_referencia = np.maximum(previsto_da_referencia, 0.0)
    assert (pareadas["real_novo"] - pareadas["real_referencia"]).abs().max() == 0.0
    return float((pareadas["previsto_novo"] - previsto_da_referencia).abs().max())


@pytest.mark.parametrize("horizonte", [1, 12])
def test_e6b_a_celula_histgb_q085_m1_do_script_reproduz_a_referencia_truncada(
    tabela_cortada: pd.DataFrame,
    referencia: pd.DataFrame,
    horizonte: int,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`e6b.rodar_um_pedaco` (com truncagem em zero) == `max(referencia, 0)`; as colunas sao as do parcial."""
    monkeypatch.setattr(e6b, "REGISTRADOR", RegistradorDeLog(tmp_path / "e6b.log"))
    monkeypatch.setattr(e6b, "montar_matriz_do_braco", montar_matriz_do_braco_truncada)
    configuracao = ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1)
    previsoes = e6b.rodar_um_pedaco(configuracao, horizonte, tabela_cortada)
    assert list(previsoes.columns) == [
        "algoritmo", "perda", "conjunto", "h", "data_origem", "data_alvo", "real", "previsto",
    ]
    assert (previsoes["algoritmo"] == "hist_gradient_boosting").all()
    assert (previsoes["perda"] == "quantil_0.85").all()
    assert (previsoes["conjunto"] == "M1_com_vetor").all()
    assert comparar_com_a_referencia(previsoes, referencia, "referencia", horizonte, True) < TOLERANCIA


@pytest.mark.parametrize("horizonte", [1, 12])
@pytest.mark.parametrize("so_a_calibracao", [True, False])
def test_e6c_a_referencia_da_grade_nas_duas_fases_reproduz_a_referencia(
    tabela_cortada: pd.DataFrame,
    referencia: pd.DataFrame,
    horizonte: int,
    so_a_calibracao: bool,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`e6c.rodar_um_pedaco` da referencia (fase 1 com matriz cortada na calibracao; fase 2 com a inteira) == referencia, sem truncar."""
    monkeypatch.setattr(e6c, "REGISTRADOR", RegistradorDeLog(tmp_path / "e6c.log"))
    monkeypatch.setattr(e6c, "montar_matriz_do_braco", montar_matriz_do_braco_truncada)
    configuracao = e6c.encontrar_configuracao(NOME_DA_REFERENCIA)
    previsoes = e6c.rodar_um_pedaco(configuracao, horizonte, tabela_cortada, so_a_calibracao=so_a_calibracao)
    assert (previsoes["configuracao"] == NOME_DA_REFERENCIA).all()
    assert comparar_com_a_referencia(previsoes, referencia, "referencia", horizonte, False) < TOLERANCIA


@pytest.mark.parametrize("folha,nome_do_braco", [(5, "referencia"), (20, "HistGB_folha20_M1")])
@pytest.mark.parametrize("horizonte", [1, 12])
def test_e7_o_q085_do_script_reproduz_a_referencia_das_duas_folhas(
    tabela_cortada: pd.DataFrame,
    referencia: pd.DataFrame,
    folha: int,
    nome_do_braco: str,
    horizonte: int,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`e7.rodar_um_pedaco` no quantil 0,85 (a trava) == a referencia certificada da folha, sem truncar."""
    monkeypatch.setattr(e7, "REGISTRADOR", RegistradorDeLog(tmp_path / "e7.log"))
    monkeypatch.setattr(e7, "montar_matriz_do_braco", montar_matriz_do_braco_truncada)
    previsoes = e7.rodar_um_pedaco(e7.CelulaDoWis(folha, 0.85, horizonte), tabela_cortada)
    assert list(previsoes.columns) == ["folha", "quantil", "h", "data_origem", "data_alvo", "real", "previsto"]
    assert (previsoes["folha"] == folha).all()
    assert (previsoes["quantil"] == 0.85).all()
    assert comparar_com_a_referencia(previsoes, referencia, nome_do_braco, horizonte, False) < TOLERANCIA


def test_e7_quantis_diferentes_dao_previsoes_diferentes_e_o_quantil_alto_nao_e_menor_que_o_baixo_em_media(
    tabela_cortada: pd.DataFrame, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanidade: o quantil entra de fato no modelo (q0,95 e q0,05 diferem) e, em media nas 8 origens, q0,95 >= q0,05."""
    monkeypatch.setattr(e7, "REGISTRADOR", RegistradorDeLog(tmp_path / "e7.log"))
    monkeypatch.setattr(e7, "montar_matriz_do_braco", montar_matriz_do_braco_truncada)
    baixo = e7.rodar_um_pedaco(e7.CelulaDoWis(5, 0.05, 4), tabela_cortada)
    alto = e7.rodar_um_pedaco(e7.CelulaDoWis(5, 0.95, 4), tabela_cortada)
    assert not np.array_equal(baixo["previsto"].to_numpy(), alto["previsto"].to_numpy())
    assert alto["previsto"].mean() >= baixo["previsto"].mean()


@pytest.mark.parametrize("so_a_calibracao,deve_terminar_na_calibracao", [(True, True), (False, False)])
def test_e6c_a_fase_1_corta_a_matriz_na_calibracao_antes_do_laco_e_a_fase_2_usa_a_matriz_inteira(
    tabela_cortada: pd.DataFrame,
    so_a_calibracao: bool,
    deve_terminar_na_calibracao: bool,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A matriz entregue ao laco termina em 31/12/2023 na fase 1 (a avaliacao nao e vista) e vai alem na fase 2.

    O laco e trocado por um espiao que so guarda a matriz recebida (nenhum modelo e treinado).
    """
    matrizes_recebidas: list[pd.DataFrame] = []

    def espiar_o_laco(matriz, horizonte, configuracao_do_modelo, configuracao_de_avaliacao):
        matrizes_recebidas.append(matriz)
        return pd.DataFrame(columns=["h", "data_origem", "data_alvo", "real", "previsto"])

    monkeypatch.setattr(e6c, "REGISTRADOR", RegistradorDeLog(tmp_path / "e6c.log"))
    monkeypatch.setattr(e6c, "executar_walk_forward", espiar_o_laco)
    configuracao = e6c.encontrar_configuracao(NOME_DA_REFERENCIA)
    e6c.rodar_um_pedaco(configuracao, 8, tabela_cortada, so_a_calibracao=so_a_calibracao)

    assert len(matrizes_recebidas) == 1
    ultima_data_alvo = matrizes_recebidas[0]["data_alvo"].max()
    fim_da_calibracao = pd.Timestamp("2023-12-31")
    if deve_terminar_na_calibracao:
        assert ultima_data_alvo == fim_da_calibracao
    else:
        assert ultima_data_alvo > fim_da_calibracao


def test_e6b_o_script_pede_a_truncagem_em_zero_do_laco(
    tabela_cortada: pd.DataFrame, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A grade corrigida do antigo trunca a previsao em zero: o script tem de pedir `truncar_em_zero=True` ao laco.

    Nas 8 primeiras origens a referencia nao tem previsao negativa, entao o diferencial acima nao distingue com e sem
    truncagem; aqui o laco e trocado por um espiao que so guarda o argumento (nenhum modelo e treinado).
    """
    argumentos_recebidos: list[bool] = []

    def espiar_o_laco(matriz, horizonte, configuracao, configuracao_de_avaliacao, truncar_em_zero):
        argumentos_recebidos.append(truncar_em_zero)
        return pd.DataFrame(columns=["h", "data_origem", "data_alvo", "real", "previsto"])

    monkeypatch.setattr(e6b, "REGISTRADOR", RegistradorDeLog(tmp_path / "e6b.log"))
    monkeypatch.setattr(e6b, "executar_walk_forward_da_grade", espiar_o_laco)
    e6b.rodar_um_pedaco(ConfiguracaoDaGrade(ALGORITMO_HISTGB, 0.85, CONJUNTO_M1), 4, tabela_cortada)
    assert argumentos_recebidos == [True]
