"""Monta a tabela da rodada 'notificacoes como alvo'.

Junta a tabela_final oficial (vetor e clima ate 09/08/2026) com a serie
semanal do CEVS (Confirmados e Notificacoes), por (ano, semana)
epidemiologicos. NAO altera o pipeline oficial nem os arquivos de entrada:
so le e grava dentro desta pasta de analise.

Protocolo: PRE_DECLARACAO.md, secoes 2 e 4 (TRAVA 2).
"""

import pathlib

import pandas as pd

PASTA_DESTA_ANALISE = pathlib.Path(__file__).resolve().parent
PASTA_DO_PROJETO = PASTA_DESTA_ANALISE.parent.parent

CAMINHO_TABELA_FINAL = (
    PASTA_DO_PROJETO
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "tabela_modelagem"
    / "tabela_final.csv"
)
CAMINHO_CEVS = (
    PASTA_DO_PROJETO
    / "analises"
    / "2026-09-25_novas_fontes_oficiais"
    / "dados"
    / "cevs_poa_dengue_semanal_por_medida.csv"
)
CAMINHO_SAIDA = PASTA_DESTA_ANALISE / "dados" / "tabela_cevs.csv"

# TRAVA 2 do protocolo: os totais anuais de confirmados e notificacoes do
# CEVS que a tabela montada tem de reproduzir, para provar que a fonte e a
# juncao estao corretas antes de rodar qualquer braco.
TOTAIS_ANUAIS_ESPERADOS = {
    "confirmados": {2022: 5142, 2023: 6318, 2024: 16764, 2025: 22504, 2026: 11},
    "notificacoes": {2022: 7263, 2023: 9759, 2024: 31101, 2025: 57167, 2026: 4085},
}


def carregar_tabela_final_oficial() -> pd.DataFrame:
    """Le a tabela_final oficial, exatamente como `acesso.fontes.carregar_tabela_final`.

    Reproduz aqui em vez de importar o pipeline porque o objetivo desta
    analise e nao tocar em `modelagem_aedes/` (ver regras da tarefa). So
    renomeia a coluna de data e a de casos, e ordena por data — igual ao
    original, o suficiente para o braco T0 ser bit-identico ao que o
    harness produziria chamando o pipeline oficial.
    """
    tabela = pd.read_csv(
        CAMINHO_TABELA_FINAL, parse_dates=["data_inicio_semana_epidemi"]
    ).rename(
        columns={
            "data_inicio_semana_epidemi": "data",
            "casos_confirmados": "casos",
        }
    )
    return tabela.sort_values("data").reset_index(drop=True)


def carregar_serie_cevs_por_medida(nome_da_medida: str) -> pd.DataFrame:
    """Le a serie semanal do CEVS de uma medida (Confirmados ou Notificacoes).

    Args:
        nome_da_medida: O rotulo exato da medida na coluna 'medida' do CSV do
            CEVS ('Confirmados' ou 'Notificações').

    Returns:
        Uma linha por semana epidemiologica, com 'ano', 'semana' e a
        contagem daquela medida.
    """
    cevs_bruto = pd.read_csv(CAMINHO_CEVS)
    da_medida = cevs_bruto[cevs_bruto["medida"] == nome_da_medida].copy()
    da_medida = da_medida.rename(
        columns={
            "ano_epidemiologico": "ano",
            "semana_epidemiologica": "semana",
            "qt_casos": nome_da_medida,
        }
    )
    return da_medida[["ano", "semana", nome_da_medida]]


def juntar_cevs_na_tabela_final(
    tabela_final: pd.DataFrame,
    confirmados_cevs: pd.DataFrame,
    notificacoes_cevs: pd.DataFrame,
) -> pd.DataFrame:
    """Junta as duas series do CEVS na tabela_final por (ano, semana).

    A junção é feita à esquerda, preservando toda linha e ordem da
    tabela_final. Semana sem registro no CEVS (a maioria de 2012 a 2014,
    antes do CEVS existir) entra como 0 nas duas colunas, conforme o
    protocolo (PRE_DECLARACAO.md, secao 2).

    Returns:
        A tabela_final com duas colunas novas: 'cevs_confirmados' e
        'cevs_notificacoes'.
    """
    tabela_com_cevs = tabela_final.merge(
        confirmados_cevs, on=["ano", "semana"], how="left"
    ).merge(notificacoes_cevs, on=["ano", "semana"], how="left")

    tabela_com_cevs = tabela_com_cevs.rename(
        columns={
            "Confirmados": "cevs_confirmados",
            "Notificações": "cevs_notificacoes",
        }
    )
    tabela_com_cevs["cevs_confirmados"] = tabela_com_cevs["cevs_confirmados"].fillna(0)
    tabela_com_cevs["cevs_notificacoes"] = tabela_com_cevs["cevs_notificacoes"].fillna(
        0
    )
    return tabela_com_cevs


def conferir_trava_totais_anuais(tabela_com_cevs: pd.DataFrame) -> bool:
    """TRAVA 2: confere se os totais anuais batem com o protocolo.

    A tabela_final oficial vai so ate 09/08/2026 (semana epidemiologica 32),
    por desenho (secao 2 da PRE_DECLARACAO): a juncao NAO adiciona semanas
    novas ao grid. O CEVS de 2026 usado para escrever o protocolo ia ate a
    semana 37 (baixado em 25/09/2026), entao o total de 2026 dentro da
    tabela montada e necessariamente MENOR que o do protocolo — nao por
    erro de juncao, e sim pelo corte de data da propria tabela_final.

    Investigado em 25/09/2026: a diferenca de 2026 (11 → 10 confirmados,
    4.085 → 4.056 notificacoes) fecha exatamente com as semanas 33 a 37
    (1 confirmado, 29 notificacoes), que ficam fora do grid. Por isso a
    trava, para 2026, confere contra o total RECALCULADO so nas semanas
    presentes na tabela_final, e nao contra o numero fixo do protocolo.

    Returns:
        True se 2022-2025 baterem exatamente e 2026 bater com o total
        restrito ao alcance real da tabela_final.
    """
    cevs_bruto = pd.read_csv(CAMINHO_CEVS)
    semana_maxima_2026_na_tabela = int(
        tabela_com_cevs.loc[tabela_com_cevs["ano"] == 2026, "semana"].max()
    )
    totais_esperados_ajustados = {
        medida: dict(totais) for medida, totais in TOTAIS_ANUAIS_ESPERADOS.items()
    }
    for medida, nome_medida_cevs in (
        ("confirmados", "Confirmados"),
        ("notificacoes", "Notificações"),
    ):
        do_cevs_2026 = cevs_bruto[
            (cevs_bruto["medida"] == nome_medida_cevs)
            & (cevs_bruto["ano_epidemiologico"] == 2026)
            & (cevs_bruto["semana_epidemiologica"] <= semana_maxima_2026_na_tabela)
        ]
        totais_esperados_ajustados[medida][2026] = int(do_cevs_2026["qt_casos"].sum())

    print("\n  TRAVA 2 — totais anuais do CEVS na tabela montada")
    print(
        f"    (2026 na tabela_final vai so ate a semana {semana_maxima_2026_na_tabela}; "
        "o total de 2026 abaixo esta recalculado so nessa janela)"
    )
    tudo_bate = True
    for medida, coluna in (
        ("confirmados", "cevs_confirmados"),
        ("notificacoes", "cevs_notificacoes"),
    ):
        totais_por_ano = tabela_com_cevs.groupby("ano")[coluna].sum()
        for ano, esperado in totais_esperados_ajustados[medida].items():
            obtido = int(totais_por_ano.get(ano, 0))
            bate = obtido == esperado
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "<<< DIVERGE"
            print(f"    {medida:>13} {ano}  esperado {esperado:6d}  obtido {obtido:6d}  {marca}")
    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def main() -> None:
    """Monta a tabela_cevs.csv e confere a TRAVA 2 antes de gravar."""
    tabela_final = carregar_tabela_final_oficial()
    confirmados_cevs = carregar_serie_cevs_por_medida("Confirmados")
    notificacoes_cevs = carregar_serie_cevs_por_medida("Notificações")

    tabela_com_cevs = juntar_cevs_na_tabela_final(
        tabela_final, confirmados_cevs, notificacoes_cevs
    )

    semanas_sem_confirmados_no_cevs = int(
        tabela_final.merge(confirmados_cevs, on=["ano", "semana"], how="left")[
            "Confirmados"
        ]
        .isna()
        .sum()
    )
    semanas_sem_notificacoes_no_cevs = int(
        tabela_final.merge(notificacoes_cevs, on=["ano", "semana"], how="left")[
            "Notificações"
        ]
        .isna()
        .sum()
    )
    print(
        f"  semanas sem registro no CEVS (viram 0): "
        f"confirmados {semanas_sem_confirmados_no_cevs} de {len(tabela_final)} · "
        f"notificacoes {semanas_sem_notificacoes_no_cevs} de {len(tabela_final)}"
    )

    valido = conferir_trava_totais_anuais(tabela_com_cevs)
    if not valido:
        raise SystemExit(
            "TRAVA 2 INVALIDA — os totais anuais do CEVS nao bateram. "
            "Investigar antes de gravar a tabela ou rodar qualquer braco."
        )

    CAMINHO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    tabela_com_cevs.to_csv(CAMINHO_SAIDA, index=False)
    print(f"\n  tabela gravada em {CAMINHO_SAIDA} — {len(tabela_com_cevs)} linhas")


if __name__ == "__main__":
    main()
