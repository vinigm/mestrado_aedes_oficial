"""Teste diferencial do ciclo 2 (parte 2): o walk-forward novo contra as previsoes do codigo antigo.

Entrada: `resultados/ciclo2/previsoes_trava.csv`, gerado por
`python3 -B -m experimentos.trava_walk_forward` (h = 1 e 12, folha 5 e folha 20).
Gabarito: `testes/referencia_antiga/previsoes_referencia.csv` (colunas h,
data_alvo, real, previsto, braco), gerado pelo codigo antigo por
`analises/2026-10-12_referencia_para_o_pacote/gerar_referencia.py`.

O que tem de ser identico, para cada (h, data_alvo, braco) da trava:
    - o MESMO conjunto de linhas (nem a mais, nem a menos);
    - `real` identico e `previsto` com diferenca maxima < 1e-9;
    - as ancoras: 102 semanas por horizonte na janela de avaliacao e o MAE da
      janela (folha 5: 97,987 em h=1 e 278,818 em h=12; folha 20: 133,626 e 243,765).

Se a trava ainda nao rodou, os testes sao pulados com mensagem clara.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from aedes.configuracao import CONFIGURACAO_AVALIACAO

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_DA_TRAVA = PASTA_DO_PROJETO / "resultados" / "ciclo2" / "previsoes_trava.csv"
CAMINHO_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga" / "previsoes_referencia.csv"

HORIZONTES_DA_TRAVA = (1, 12)
BRACOS = ("referencia", "HistGB_folha20_M1")
CHAVE = ["h", "data_alvo", "braco"]
TOLERANCIA_DO_PREVISTO = 1e-9

# Ancoras da tarefa (MAE na janela de avaliacao), com 3 casas decimais.
QUANTIDADE_DE_SEMANAS_AVALIADAS = 102
MAE_ANCORA = {
    ("referencia", 1): 97.987,
    ("referencia", 12): 278.818,
    ("HistGB_folha20_M1", 1): 133.626,
    ("HistGB_folha20_M1", 12): 243.765,
}
TOLERANCIA_DO_MAE_ANCORA = 5e-4
LINHAS_ESPERADAS_NA_TRAVA = {1: 295, 12: 284}


@pytest.fixture(scope="module")
def previsoes_novas() -> pd.DataFrame:
    """As previsoes da trava, ou pula o teste se ela ainda nao rodou."""
    if not CAMINHO_DA_TRAVA.exists():
        pytest.skip(
            f"{CAMINHO_DA_TRAVA.relative_to(PASTA_DO_PROJETO)} nao existe: rode "
            "`python3 -B -m experimentos.trava_walk_forward` (leva alguns minutos) e repita."
        )
    return pd.read_csv(CAMINHO_DA_TRAVA, parse_dates=["data_alvo"])


@pytest.fixture(scope="module")
def previsoes_do_gabarito() -> pd.DataFrame:
    """As previsoes salvas pelo codigo antigo, so nos horizontes e bracos da trava."""
    gabarito = pd.read_csv(CAMINHO_DO_GABARITO, parse_dates=["data_alvo"])
    horizonte_da_trava = gabarito["h"].isin(HORIZONTES_DA_TRAVA)
    braco_da_trava = gabarito["braco"].isin(BRACOS)
    return gabarito.loc[horizonte_da_trava & braco_da_trava].reset_index(drop=True)


def recortar(previsoes: pd.DataFrame, braco: str, horizonte: int) -> pd.DataFrame:
    """Previsoes de um braco e um horizonte, ordenadas por data_alvo."""
    do_braco = previsoes["braco"] == braco
    do_horizonte = previsoes["h"] == horizonte
    recorte = previsoes.loc[do_braco & do_horizonte]
    return recorte.sort_values("data_alvo").reset_index(drop=True)


def recortar_na_janela_de_avaliacao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """So as semanas-alvo da janela de avaliacao (2024-01-07 a 2026-02-01)."""
    depois_do_inicio = previsoes["data_alvo"] >= CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    antes_do_fim = previsoes["data_alvo"] <= CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada
    return previsoes.loc[depois_do_inicio & antes_do_fim]


def test_a_trava_tem_os_4_conjuntos_e_o_numero_de_linhas_esperado(previsoes_novas: pd.DataFrame) -> None:
    for braco in BRACOS:
        for horizonte in HORIZONTES_DA_TRAVA:
            recorte = recortar(previsoes_novas, braco, horizonte)
            assert len(recorte) == LINHAS_ESPERADAS_NA_TRAVA[horizonte], (braco, horizonte)
    assert set(previsoes_novas["braco"]) == set(BRACOS)
    assert set(previsoes_novas["h"]) == set(HORIZONTES_DA_TRAVA)


def test_mesmas_linhas_do_gabarito(
    previsoes_novas: pd.DataFrame, previsoes_do_gabarito: pd.DataFrame
) -> None:
    """Mesmo conjunto de (h, data_alvo, braco), sem duplicata, nem a mais nem a menos."""
    assert not previsoes_novas.duplicated(subset=CHAVE).any()
    assert not previsoes_do_gabarito.duplicated(subset=CHAVE).any()

    chaves_novas = set(map(tuple, previsoes_novas[CHAVE].to_numpy().tolist()))
    chaves_do_gabarito = set(map(tuple, previsoes_do_gabarito[CHAVE].to_numpy().tolist()))
    so_nas_novas = chaves_novas - chaves_do_gabarito
    so_no_gabarito = chaves_do_gabarito - chaves_novas

    assert not so_nas_novas, f"{len(so_nas_novas)} linha(s) so nas previsoes novas, ex.: {sorted(so_nas_novas)[:3]}"
    assert not so_no_gabarito, f"{len(so_no_gabarito)} linha(s) so no gabarito, ex.: {sorted(so_no_gabarito)[:3]}"


@pytest.mark.parametrize("horizonte", HORIZONTES_DA_TRAVA)
@pytest.mark.parametrize("braco", BRACOS)
def test_previsto_e_real_identicos_ao_gabarito(
    braco: str,
    horizonte: int,
    previsoes_novas: pd.DataFrame,
    previsoes_do_gabarito: pd.DataFrame,
) -> None:
    nova = recortar(previsoes_novas, braco, horizonte)
    antiga = recortar(previsoes_do_gabarito, braco, horizonte)

    assert len(nova) == len(antiga)
    np.testing.assert_array_equal(nova["data_alvo"].to_numpy(), antiga["data_alvo"].to_numpy())
    np.testing.assert_array_equal(nova["real"].to_numpy(), antiga["real"].to_numpy())

    diferenca_maxima = float(np.max(np.abs(nova["previsto"].to_numpy() - antiga["previsto"].to_numpy())))
    assert diferenca_maxima < TOLERANCIA_DO_PREVISTO, (
        f"{braco} h={horizonte}: diferenca maxima de `previsto` = {diferenca_maxima:.3e}"
    )


@pytest.mark.parametrize("horizonte", HORIZONTES_DA_TRAVA)
@pytest.mark.parametrize("braco", BRACOS)
def test_mae_na_janela_de_avaliacao_bate_com_a_ancora(
    braco: str, horizonte: int, previsoes_novas: pd.DataFrame
) -> None:
    recorte = recortar(previsoes_novas, braco, horizonte)
    na_janela = recortar_na_janela_de_avaliacao(recorte)
    assert len(na_janela) == QUANTIDADE_DE_SEMANAS_AVALIADAS

    erros_absolutos = np.abs(na_janela["real"].to_numpy() - na_janela["previsto"].to_numpy())
    mae_da_janela = float(np.mean(erros_absolutos))
    assert mae_da_janela == pytest.approx(MAE_ANCORA[(braco, horizonte)], abs=TOLERANCIA_DO_MAE_ANCORA)
