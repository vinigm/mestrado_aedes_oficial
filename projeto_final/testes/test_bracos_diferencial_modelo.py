"""Diferencial COM modelo treinado: os bracos novos reproduzem o codigo antigo e a referencia, em uma celula cada.

Duas celulas completas do walk-forward (cada uma ~30 s com `OMP_NUM_THREADS=1`), escolhidas para provar o que
as travas da pre-declaracao exigem, sem rodar a etapa inteira:

    1. TRAVA 2 (em h = 1): `sem_vetor`, folha 20, comparado ao braco `HistGB_folha20_M0` do codigo antigo
       (`testes/referencia_antiga/previsoes_por_braco_original.csv`). Mesmo conjunto de (h, data_alvo)
       (307 linhas em h = 1, que o `completo` nao tem: sao as semanas sem vetor) e diferenca < 1e-9.
    2. PREMISSA DA E1 (em h = 12): `completo`, folha 5, com a matriz cortada em `data_alvo <= 31/12/2023` ANTES
       do laco, igual as previsoes de `resultados/referencia/previsoes.csv` na calibracao (n = 182), diferenca < 1e-9.

Se o `OMP_NUM_THREADS` nao for 1, o resultado e o mesmo, so bem mais lento.
"""

import pathlib

import pandas as pd
import pytest

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import comparar_previsoes_com_gabarito
from aedes.configuracao import (
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.walk_forward import executar_walk_forward
from aedes.walk_forward_com_corte import recortar_matriz_ate_a_data_alvo

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
CAMINHO_DA_REFERENCIA = PASTA_DO_PROJETO / "resultados" / "referencia" / "previsoes.csv"
CAMINHO_DO_GABARITO_POR_BRACO = PASTA_DO_PROJETO / "testes" / "referencia_antiga" / "previsoes_por_braco_original.csv"

CHAVE = ["h", "data_alvo"]
TOLERANCIA = 1e-9


@pytest.fixture(scope="module")
def tabela_cortada() -> pd.DataFrame:
    """A tabela certificada, validada e com o corte de maturidade de 12 semanas."""
    conteudo_em_bytes = CAMINHO_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


def test_trava_2_sem_vetor_folha_20_h1_reproduz_o_braco_antigo_histgb_folha20_m0(
    tabela_cortada: pd.DataFrame,
) -> None:
    """307 previsoes em h = 1, mesmas (h, data_alvo) e `previsto` com diferenca < 1e-9 do gabarito antigo."""
    horizonte = 1
    matriz = montar_matriz_do_braco(
        tabela_cortada, horizonte, "sem_vetor", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    previsoes = executar_walk_forward(matriz, horizonte, FOLHA_20, CONFIGURACAO_AVALIACAO)

    gabarito = pd.read_csv(CAMINHO_DO_GABARITO_POR_BRACO, parse_dates=["data_alvo"])
    do_braco_antigo = gabarito["braco"] == "HistGB_folha20_M0"
    do_horizonte = gabarito["h"] == horizonte
    gabarito_do_horizonte = gabarito.loc[do_braco_antigo & do_horizonte]

    resultado = comparar_previsoes_com_gabarito(previsoes, gabarito_do_horizonte, CHAVE, TOLERANCIA)
    assert resultado.linhas_novas == 307
    assert resultado.linhas_do_gabarito == 307
    assert resultado.linhas_so_nas_novas == 0
    assert resultado.linhas_so_no_gabarito == 0
    assert resultado.diferenca_maxima_do_real == 0.0
    assert resultado.passou, resultado


def test_premissa_da_e1_completo_folha_5_h12_com_matriz_cortada_reproduz_a_referencia_na_calibracao(
    tabela_cortada: pd.DataFrame,
) -> None:
    """Matriz cortada em `data_alvo <= 2023-12-31` antes do laco: 182 previsoes iguais as da referencia na calibracao."""
    horizonte = 12
    matriz_inteira = montar_matriz_do_braco(
        tabela_cortada, horizonte, "completo", CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    matriz_da_calibracao = recortar_matriz_ate_a_data_alvo(matriz_inteira, CONFIGURACAO_AVALIACAO.fim_da_calibracao)
    previsoes = executar_walk_forward(matriz_da_calibracao, horizonte, FOLHA_5, CONFIGURACAO_AVALIACAO)

    referencia = pd.read_csv(CAMINHO_DA_REFERENCIA, parse_dates=["data_origem", "data_alvo"])
    da_folha_5 = referencia["braco"] == "referencia"
    do_horizonte = referencia["h"] == horizonte
    na_calibracao = referencia["data_alvo"] <= CONFIGURACAO_AVALIACAO.fim_da_calibracao
    referencia_na_calibracao = referencia.loc[da_folha_5 & do_horizonte & na_calibracao]

    resultado = comparar_previsoes_com_gabarito(previsoes, referencia_na_calibracao, CHAVE, TOLERANCIA)
    assert resultado.linhas_novas == 182
    assert resultado.linhas_so_nas_novas == 0
    assert resultado.linhas_so_no_gabarito == 0
    assert resultado.passou, resultado
