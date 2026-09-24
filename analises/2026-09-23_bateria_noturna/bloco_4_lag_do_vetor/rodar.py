"""Bloco 4 — janela de lag longa so no vetor.

O teste de 23/09 (analises/2026-09-23_janela_de_lag/) estendeu a janela de
lag de TODAS as colunas juntas e nao achou ganho. Mas a importancia por bloco
medida no mesmo dia mostrou o vetor crescendo com o horizonte: embaralhar o
bloco derruba 0,528 de R2 em h=8 e 0,642 em h=12, enquanto o nucleo de casos
derruba 0,339 em h=8.

Se o sinal longo mora no vetor, estender tudo junto dilui: os lags extras de
casos e de clima entram como ruido correlacionado. Este bloco estende SO o
vetor, deixando casos e clima com os 4 lags de sempre. Protocolo em
PRE_DECLARACAO.md.
"""

import pathlib
import sys

import pandas as pd

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

COLUNA_DO_VETOR = "aedes_aegypti_por_armadilha"
LAGS_EXTRAS_DO_VETOR = (6, 8, 10, 12)

NOMES_DOS_LAGS_EXTRAS = tuple(
    f"{COLUNA_DO_VETOR}_lag{semanas}" for semanas in LAGS_EXTRAS_DO_VETOR
)


def acrescentar_lags_longos_do_vetor(tabela: pd.DataFrame) -> pd.DataFrame:
    """Cria as defasagens de 6 a 12 semanas, so para a densidade do vetor.

    Args:
        tabela: A tabela ja com as features temporais do pipeline.

    Returns:
        Uma copia com as quatro colunas novas.
    """
    dados = tabela.copy()
    for semanas, nome in zip(LAGS_EXTRAS_DO_VETOR, NOMES_DOS_LAGS_EXTRAS):
        dados[nome] = dados[COLUNA_DO_VETOR].shift(semanas)

    return dados


BRACOS = (
    harness.Braco("A_referencia", descricao="as 20 colunas do cenario adotado"),
    harness.Braco(
        "B_vetor_ate_8",
        colunas_extras=NOMES_DOS_LAGS_EXTRAS[:2],
        descricao="vetor com lags 6 e 8; casos e clima com 1 a 4",
    ),
    harness.Braco(
        "C_vetor_ate_12",
        colunas_extras=NOMES_DOS_LAGS_EXTRAS,
        descricao="vetor com lags 6, 8, 10 e 12; casos e clima com 1 a 4",
    ),
)


def main() -> None:
    """Roda os tres bracos, valida a referencia e compara."""
    print("=" * 78)
    print("BLOCO 4 — janela de lag longa so no vetor")
    print("=" * 78, flush=True)

    previsoes = harness.executar_bateria(
        BRACOS,
        PASTA_DE_SAIDAS,
        construir_extras=acrescentar_lags_longos_do_vetor,
        colunas_reservadas=NOMES_DOS_LAGS_EXTRAS,
    )
    valido = harness.conferir_trava_de_validacao(previsoes, "A_referencia")
    if not valido:
        print("\n  BLOCO INVALIDO: a referencia nao reproduziu o painel.", flush=True)
        return

    harness.relatar_comparacoes(
        previsoes,
        braco_referencia="A_referencia",
        horizontes_da_familia=(1, 4, 8, 12),
        horizontes_de_decisao=(8, 12),
        pasta_de_saidas=PASTA_DE_SAIDAS,
    )


if __name__ == "__main__":
    main()
