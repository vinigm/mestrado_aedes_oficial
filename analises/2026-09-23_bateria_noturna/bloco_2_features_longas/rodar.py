"""Bloco 2 — o teste de features longas de 30/08, refeito sem vazamento.

O teste original adicionou quatro grupos de features ao conjunto de
referencia e mediu se o horizonte longo melhorava. Nenhum passou, mas o
ENSO melhorou h=8 em -7,1% de MAE: o unico sinal positivo do projeto.

Esse numero nasceu com dois defeitos que foram corrigidos depois:
  - o treino era cortado por POSICAO, e nao pela data da resposta;
  - o quantil era 0,80, e a referencia atual e 0,85.

Este bloco refaz os mesmos grupos, com os dois consertos. Protocolo em
PRE_DECLARACAO.md.
"""

import pathlib
import sys

import pandas as pd

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA_DESTE_ARQUIVO.parent))

import harness  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# As tres colunas de clima que recebem norma historica e anomalia, e as duas
# que recebem acumulo. Identicas ao teste de 30/08, para os dois serem
# comparaveis.
COLUNAS_PARA_ANOMALIA = ("temp_media", "precip_total_mm", "umid_media")
COLUNAS_PARA_ACUMULO = ("precip_total_mm", "temp_media")
JANELAS_DE_ACUMULO = (8, 12)

GRUPO_LAGS_ANUAIS = ("casos_lag52", "casos_lag104", "vetor_lag52")
GRUPO_ANOMALIA = tuple(f"{coluna}_anomalia" for coluna in COLUNAS_PARA_ANOMALIA)
GRUPO_ACUMULO = tuple(
    f"{coluna}_acum{janela}"
    for coluna in COLUNAS_PARA_ACUMULO
    for janela in JANELAS_DE_ACUMULO
)
GRUPO_ENSO = ("nino34_anom", "oni")


def calcular_norma_historica(valores: pd.Series) -> pd.Series:
    """Media das ocorrencias ANTERIORES da mesma semana do ano.

    E o que torna a anomalia livre de vazamento: em cada linha, a norma usa
    apenas as vezes em que aquela semana do ano ja aconteceu antes. Usar a
    media da serie inteira faria a feature enxergar o futuro.

    Copiada literalmente do teste de 30/08, onde ja estava correta.
    """
    return valores.expanding().mean().shift(1)


def acrescentar_features_longas(tabela: pd.DataFrame) -> pd.DataFrame:
    """Cria os quatro grupos de features longas do teste de 30/08.

    Args:
        tabela: A tabela ja com as features temporais do pipeline.

    Returns:
        Uma copia com as colunas dos quatro grupos acrescentadas.
    """
    dados = tabela.copy()

    dados["casos_lag52"] = dados["casos"].shift(52)
    dados["casos_lag104"] = dados["casos"].shift(104)
    dados["vetor_lag52"] = dados["aedes_aegypti_por_armadilha"].shift(52)

    semana_do_ano = dados["data"].dt.isocalendar().week.astype(int)
    agrupado_por_semana = dados.groupby(semana_do_ano, group_keys=False)
    for nome_coluna in COLUNAS_PARA_ANOMALIA:
        norma = agrupado_por_semana[nome_coluna].transform(calcular_norma_historica)
        dados[f"{nome_coluna}_anomalia"] = dados[nome_coluna] - norma

    for nome_coluna in COLUNAS_PARA_ACUMULO:
        for janela in JANELAS_DE_ACUMULO:
            dados[f"{nome_coluna}_acum{janela}"] = (
                dados[nome_coluna].rolling(janela).sum()
            )

    # As colunas do ENSO ja estao na tabela; o config so as descarta.
    return dados


BRACOS = (
    harness.Braco("A_referencia", descricao="as 20 colunas do cenario adotado"),
    harness.Braco(
        "A+B_lags_anuais",
        colunas_extras=GRUPO_LAGS_ANUAIS,
        descricao="memoria de 1 e 2 anos atras",
    ),
    harness.Braco(
        "A+C+D_clima_longo",
        colunas_extras=GRUPO_ANOMALIA + GRUPO_ACUMULO,
        descricao="anomalia contra a norma e acumulo de 2-3 meses",
    ),
    harness.Braco(
        "A+E_enso",
        colunas_extras=GRUPO_ENSO,
        descricao="El Nino e La Nina",
    ),
    harness.Braco(
        "A+TUDO",
        colunas_extras=GRUPO_LAGS_ANUAIS + GRUPO_ANOMALIA + GRUPO_ACUMULO + GRUPO_ENSO,
        descricao="os quatro grupos juntos",
    ),
)


def main() -> None:
    """Roda os cinco bracos, valida a referencia e compara."""
    print("=" * 78)
    print("BLOCO 2 — features longas, refeito sem vazamento e com quantil 0,85")
    print("=" * 78, flush=True)

    todas_as_extras = GRUPO_LAGS_ANUAIS + GRUPO_ANOMALIA + GRUPO_ACUMULO + GRUPO_ENSO
    previsoes = harness.executar_bateria(
        BRACOS,
        PASTA_DE_SAIDAS,
        construir_extras=acrescentar_features_longas,
        colunas_reservadas=todas_as_extras,
    )
    valido = harness.conferir_trava_de_validacao(previsoes, "A_referencia")
    if not valido:
        print("\n  BLOCO INVALIDO: a referencia nao reproduziu o painel.")
        print("  Nenhuma comparacao e reportada.", flush=True)
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
