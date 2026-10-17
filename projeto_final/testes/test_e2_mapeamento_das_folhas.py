"""A E2 associa a folha 5 ao `FOLHA_5` e a folha 20 ao `FOLHA_20`, e nada mais (nunca trocadas).

Lacuna achada na certificacao: um mutante que trocava as folhas em `experimentos/e2_ablacao.py` nao era pego
por nenhum teste. Aqui o mapeamento e conferido de tres jeitos: (1) o dicionario, (2) a identidade das
configuracoes (`folha_minima` 5 e 20, so isso as diferencia) e (3) a configuracao que `rodar_um_pedaco`
realmente entrega ao walk-forward para a folha pedida (com o walk-forward trocado por um espiao, sem treinar).

Nada do projeto e escrito: o log da E2 e redirecionado para `tmp_path`.
"""

import pathlib

import pandas as pd
import pytest

import experimentos.e2_ablacao as e2
from aedes.configuracao import FOLHA_5, FOLHA_20, ConfiguracaoModelo
from experimentos.comum_ciencia import RegistradorDeLog


def test_folha_5_e_folha_20_sao_distintas_so_pela_folha_minima() -> None:
    assert FOLHA_5.folha_minima == 5
    assert FOLHA_20.folha_minima == 20
    assert FOLHA_5 != FOLHA_20


def test_o_dicionario_da_e2_associa_cada_folha_a_sua_configuracao() -> None:
    assert set(e2.MODELOS_POR_FOLHA) == {5, 20}
    assert e2.MODELOS_POR_FOLHA[5] is FOLHA_5
    assert e2.MODELOS_POR_FOLHA[20] is FOLHA_20
    assert e2.MODELOS_POR_FOLHA[5].folha_minima == 5
    assert e2.MODELOS_POR_FOLHA[20].folha_minima == 20


@pytest.mark.parametrize("folha, configuracao_esperada", [(5, FOLHA_5), (20, FOLHA_20)])
def test_rodar_um_pedaco_entrega_ao_walk_forward_a_configuracao_da_folha_pedida(
    folha: int,
    configuracao_esperada: ConfiguracaoModelo,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuracoes_recebidas: list[ConfiguracaoModelo] = []

    def montar_matriz_falsa(tabela_cortada, horizonte, nome_do_braco, configuracao_variaveis, configuracao_dados):
        return pd.DataFrame({"data_origem": [], "data_alvo": [], "real": [], "a": [], "b": [], "c": []})

    def executar_walk_forward_espiao(matriz, horizonte, configuracao_do_modelo, configuracao_avaliacao):
        configuracoes_recebidas.append(configuracao_do_modelo)
        return pd.DataFrame(
            {
                "h": [horizonte],
                "data_origem": [pd.Timestamp("2024-01-07")],
                "data_alvo": [pd.Timestamp("2024-01-14")],
                "real": [1.0],
                "previsto": [2.0],
            }
        )

    monkeypatch.setattr(e2, "montar_matriz_do_braco", montar_matriz_falsa)
    monkeypatch.setattr(e2, "executar_walk_forward", executar_walk_forward_espiao)
    monkeypatch.setattr(e2, "REGISTRADOR", RegistradorDeLog(tmp_path / "E2_ablacao.log"))

    previsoes = e2.rodar_um_pedaco("completo", folha, 1, pd.DataFrame())

    assert len(configuracoes_recebidas) == 1
    assert configuracoes_recebidas[0] is configuracao_esperada
    assert configuracoes_recebidas[0].folha_minima == folha
    assert list(previsoes["folha"]) == [folha]
    assert list(previsoes["braco"]) == ["completo"]
