"""

Investiga a contradicao entre os dois alvos na deteccao de surto.

O problema, encontrado em 29/08/2026: com casos CONFIRMADOS o vetor parece
ajudar muito (P90 h=12: 4 x 24, p arredondado para 0,000); com casos
NOTIFICADOS, na mesma pergunta e com o dobro da amostra, ele nao ajuda e ate
inverte (14 x 10, p=0,541).

Escolher o alvo depois de ver os dois resultados seria pesca. Este script
existe para decidir a questao com evidencia, e nao com preferencia. Ele mede
tres coisas:

  1. o p-valor exato dos confirmados e o que sobra dele apos correcao multipla
     - primeiro sobre as 6 comparacoes daquele experimento, depois sobre as 12
       do dia inteiro (a pergunta e a mesma nos dois alvos);
  2. a ESTABILIDADE do sinal entre execucoes do MESMO alvo: em 16/08 o
     significativo era h=8; hoje, com 18% mais dados, virou h=12;
  3. o quanto as duas series concordam sobre QUAIS semanas foram surto - se
     elas discordam muito, "surto de confirmado" e "surto de notificado" nao
     sao o mesmo evento, e nao ha contradicao nenhuma: sao perguntas diferentes.

Uso:  python investigar_contradicao_alvos.py

"""

import sys
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from avaliacao.correcao_multipla import corrigir_holm
from config import settings

PASTA_RESULTADOS = PASTA_PACOTE / "dados" / "saidas" / "resultados"
PASTA_ANTES = PASTA_ANALISE / "resultados_ANTES"

# Minimo de semanas de historico antes de classificar uma semana como surto,
# igual ao protocolo do teste C de 16/08 (percentil expansivel, so passado).
MINIMO_SEMANAS_HISTORICO = 52
PERCENTIL_SURTO = 90


def recalcular_p_exato(mcnemar: pd.DataFrame) -> pd.DataFrame:
    """

    Recalcula o p-valor binomial exato de cada comparacao de McNemar.

    O CSV do experimento antigo grava o p ja arredondado para 3 casas, e um
    "0,000" pode ser qualquer coisa abaixo de 0,0005 - o que muda o resultado
    da correcao multipla. Aqui o p e refeito a partir das contagens brutas,
    que estao gravadas.

    """
    recalculado = mcnemar.copy()

    valores_p = []
    for _, linha in recalculado.iterrows():
        clima_ganha = int(linha["clima_certo_vetor_errado"])
        vetor_ganha = int(linha["vetor_certo_clima_errado"])
        discordantes = clima_ganha + vetor_ganha

        if discordantes == 0:
            valores_p.append(1.0)
            continue

        menor = min(clima_ganha, vetor_ganha)
        valores_p.append(binomtest(menor, discordantes, 0.5).pvalue)

    recalculado["discordantes"] = (
        recalculado["clima_certo_vetor_errado"] + recalculado["vetor_certo_clima_errado"]
    )
    recalculado["p_exato"] = valores_p
    return recalculado


def marcar_surto_percentil_expansivel(casos: pd.Series) -> pd.Series:
    """

    Marca cada semana como surto usando percentil calculado SO com o passado.

    Replica o protocolo do projeto: nada de olhar o futuro. As primeiras
    MINIMO_SEMANAS_HISTORICO semanas ficam sem classificacao (NaN), porque nao
    ha historico suficiente para definir o limiar.

    """
    marcacoes = []
    for posicao in range(len(casos)):
        historico = casos.iloc[:posicao].dropna()

        if len(historico) < MINIMO_SEMANAS_HISTORICO or pd.isna(casos.iloc[posicao]):
            marcacoes.append(np.nan)
            continue

        limiar = np.percentile(historico, PERCENTIL_SURTO)
        marcacoes.append(float(casos.iloc[posicao] >= limiar))

    return pd.Series(marcacoes, index=casos.index)


def main() -> None:
    print("=" * 88)
    print("1. O p-valor dos CONFIRMADOS sobrevive a correcao multipla?")
    print("=" * 88)

    confirmados = recalcular_p_exato(pd.read_csv(PASTA_RESULTADOS / "deteccao_surto_mcnemar.csv"))
    confirmados["alvo"] = "confirmados"
    confirmados["p_holm_6"] = corrigir_holm(confirmados["p_exato"].to_numpy())

    colunas = ["alvo", "pctl", "h", "n", "n_pos", "clima_certo_vetor_errado",
               "vetor_certo_clima_errado", "discordantes", "p_exato", "p_holm_6"]
    print(confirmados[colunas].round(5).to_string(index=False))

    notificados = pd.read_csv(PASTA_RESULTADOS / "surto_notificados_mcnemar.csv")
    notificados = recalcular_p_exato(notificados)
    notificados["alvo"] = "notificados"

    print("\n--- as 12 comparacoes do dia juntas (mesma pergunta, dois alvos) ---")
    todas = pd.concat(
        [confirmados[colunas[:-1]], notificados[colunas[:-1]]], ignore_index=True
    )
    todas["p_holm_12"] = corrigir_holm(todas["p_exato"].to_numpy())
    print(todas.round(5).to_string(index=False))

    sobrevivem_6 = int((confirmados["p_holm_6"] < 0.05).sum())
    sobrevivem_12 = int((todas["p_holm_12"] < 0.05).sum())
    print(f"\nsobrevivem a Holm entre as 6 do experimento: {sobrevivem_6}")
    print(f"sobrevivem a Holm entre as 12 do dia:        {sobrevivem_12}")

    print("\n" + "=" * 88)
    print("2. O sinal e ESTAVEL entre execucoes do MESMO alvo (confirmados)?")
    print("=" * 88)

    antes = recalcular_p_exato(pd.read_csv(PASTA_ANTES / "deteccao_surto_mcnemar.csv"))
    comparacao_execucoes = antes[["pctl", "h", "n", "clima_certo_vetor_errado",
                                  "vetor_certo_clima_errado", "p_exato"]].merge(
        confirmados[["pctl", "h", "n", "clima_certo_vetor_errado",
                     "vetor_certo_clima_errado", "p_exato"]],
        on=["pctl", "h"], suffixes=("_16ago", "_30ago"),
    )
    print(comparacao_execucoes.round(5).to_string(index=False))
    print("\nMesmo alvo, mesma pipeline, so 18% mais semanas.")

    print("\n" + "=" * 88)
    print("3. As duas series concordam sobre QUAIS semanas foram surto?")
    print("=" * 88)

    tabela = pd.read_csv(
        settings.CAMINHO_TABELA_FINAL, parse_dates=["data_inicio_semana_epidemi"], low_memory=False
    ).sort_values("data_inicio_semana_epidemi").reset_index(drop=True)

    infodengue = pd.read_csv(settings.CAMINHO_INFODENGUE, parse_dates=["data_iniSE"])
    tabela = tabela.merge(
        infodengue[["data_iniSE", "casos"]].rename(
            columns={"data_iniSE": "data_inicio_semana_epidemi", "casos": "casos_notificados"}
        ),
        on="data_inicio_semana_epidemi",
        how="left",
    )

    tabela["surto_confirmados"] = marcar_surto_percentil_expansivel(tabela["casos_confirmados"])
    tabela["surto_notificados"] = marcar_surto_percentil_expansivel(tabela["casos_notificados"])

    comparaveis = tabela.dropna(subset=["surto_confirmados", "surto_notificados"])
    print(f"semanas classificaveis nas DUAS series: {len(comparaveis)}")

    tabela_cruzada = pd.crosstab(
        comparaveis["surto_confirmados"], comparaveis["surto_notificados"],
        rownames=["surto p/ CONFIRMADOS"], colnames=["surto p/ NOTIFICADOS"],
    )
    print("\n" + tabela_cruzada.to_string())

    concordancia = (
        comparaveis["surto_confirmados"] == comparaveis["surto_notificados"]
    ).mean()
    ambos_surto = int(
        ((comparaveis["surto_confirmados"] == 1) & (comparaveis["surto_notificados"] == 1)).sum()
    )
    so_confirmados = int(
        ((comparaveis["surto_confirmados"] == 1) & (comparaveis["surto_notificados"] == 0)).sum()
    )
    so_notificados = int(
        ((comparaveis["surto_confirmados"] == 0) & (comparaveis["surto_notificados"] == 1)).sum()
    )

    print(f"\nconcordancia geral: {concordancia:.1%}")
    print(f"semanas de surto nas duas: {ambos_surto}")
    print(f"surto SO para confirmados: {so_confirmados}")
    print(f"surto SO para notificados: {so_notificados}")

    if ambos_surto + so_confirmados + so_notificados > 0:
        jaccard = ambos_surto / (ambos_surto + so_confirmados + so_notificados)
        print(f"sobreposicao (Jaccard) entre as duas definicoes de surto: {jaccard:.1%}")

    todas.to_csv(PASTA_ANALISE / "saidas" / "contradicao_alvos_mcnemar.csv", index=False)
    comparaveis[[
        "data_inicio_semana_epidemi", "casos_confirmados", "casos_notificados",
        "surto_confirmados", "surto_notificados",
    ]].to_csv(PASTA_ANALISE / "saidas" / "contradicao_alvos_semanas_surto.csv", index=False)
    print("\nCSVs gravados em saidas/")


if __name__ == "__main__":
    main()
