"""Diagnostica a calibracao das faixas de previsao separando por nivel de casos.

Por que existe
--------------
A rodada de WIS de 26/09/2026 reportou dois numeros agregados que assustam:
o intervalo de 50% cobre de 20% a 41% das semanas, e 77% das origens tiveram
quantis cruzados. Os dois sao medias sobre periodos muito diferentes: semanas
de calmaria, em que Porto Alegre passa a maior parte do tempo, e semanas de
epidemia, que sao poucas mas sao as que importam para a vigilancia.

Este script desagrega os mesmos numeros pelas faixas operacionais do Plano
Municipal de Contingencia, para responder: a calibracao e ruim em todo lugar,
ou so onde importa?

O que NAO faz
-------------
Nenhum teste de hipotese, nenhum p-valor, nenhum modelo treinado. E
diagnostico descritivo sobre previsoes ja salvas. Por isso nao abre familia de
correcao multipla nem exige pre-declaracao de hipotese.

Entrada
-------
`../2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`, gerado
pela rodada certificada de 26/09/2026. Colunas usadas: `modelo`, `h`,
`data_alvo`, `quantil`, `real`, `previsto` (ja reordenado), `previsto_bruto`
(antes do reordenamento) e `cruzamento_corrigido`.
"""

from __future__ import annotations

import pathlib

import pandas as pd

# Faixas operacionais. Os limites 140, 421 e 702 sao os pisos de Mobilizacao,
# Alerta e Epidemia do Plano Municipal de Contingencia de Arboviroses 2026 da
# SMS-POA, convertidos para casos por semana na populacao de 1.404.269.
# ATENCAO: sao a metade FIXA do criterio oficial; o plano tambem exige condicao
# sobre o canal estadual. Uso aqui como regua de magnitude, nao como criterio.
LIMITE_MOBILIZACAO = 140
LIMITE_ALERTA = 421
LIMITE_CALMARIA = 20

NOME_CALMARIA = "1. calmaria (0-20)"
NOME_SUBIDA = "2. subida (21-140)"
NOME_MOBILIZACAO = "3. Mobilizacao (141-421)"
NOME_ALERTA = "4. Alerta ou mais (>421)"

QUANTIL_INFERIOR_IC50 = 0.25
QUANTIL_SUPERIOR_IC50 = 0.75
QUANTIL_INFERIOR_IC90 = 0.05
QUANTIL_SUPERIOR_IC90 = 0.95

PASTA_DESTE_SCRIPT = pathlib.Path(__file__).resolve().parent
CAMINHO_PREVISOES = (
    PASTA_DESTE_SCRIPT.parent
    / "2026-09-26_wis_na_tabela_restaurada"
    / "saidas"
    / "previsoes_quantis.csv"
)
PASTA_SAIDAS = PASTA_DESTE_SCRIPT / "saidas"


def classificar_faixa_de_casos(casos_reais: float) -> str:
    """Diz em que faixa operacional uma semana caiu, pelo numero real de casos.

    Args:
        casos_reais: Casos confirmados observados naquela semana.

    Returns:
        O nome da faixa, prefixado por numero para ordenar nas tabelas.
    """
    if casos_reais <= LIMITE_CALMARIA:
        return NOME_CALMARIA
    if casos_reais <= LIMITE_MOBILIZACAO:
        return NOME_SUBIDA
    if casos_reais <= LIMITE_ALERTA:
        return NOME_MOBILIZACAO
    return NOME_ALERTA


def carregar_previsoes(caminho: pathlib.Path) -> pd.DataFrame:
    """Le as previsoes por quantil e marca a faixa de cada linha.

    Args:
        caminho: Caminho de `previsoes_quantis.csv`.

    Returns:
        A tabela com as colunas originais mais `faixa` e `desvio_do_reordenamento`.
    """
    previsoes = pd.read_csv(caminho)
    previsoes["data_alvo"] = pd.to_datetime(previsoes["data_alvo"])
    previsoes["faixa"] = previsoes["real"].apply(classificar_faixa_de_casos)
    previsoes["desvio_do_reordenamento"] = (
        previsoes["previsto"] - previsoes["previsto_bruto"]
    ).abs()
    return previsoes


def medir_cruzamento_por_faixa(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Conta quantas origens tiveram quantis cruzados, e o quanto isso mexeu.

    Uma "origem" e a combinacao (modelo, horizonte, semana alvo): dentro dela
    existem os 7 quantis que podem sair fora de ordem.

    Args:
        previsoes: A tabela de `carregar_previsoes`.

    Returns:
        Uma linha por faixa, com a taxa de origens que cruzaram e o tamanho
        tipico da correcao aplicada.
    """
    chaves_da_origem = ["modelo", "h", "data_alvo", "faixa"]
    por_origem = previsoes.groupby(chaves_da_origem, as_index=False).agg(
        cruzou=("cruzamento_corrigido", "any")
    )
    taxa_de_cruzamento = por_origem.groupby("faixa").agg(
        origens=("cruzou", "size"), taxa_que_cruzou=("cruzou", "mean")
    )

    linhas_corrigidas = previsoes[previsoes["desvio_do_reordenamento"] > 0]
    tamanho_da_correcao = linhas_corrigidas.groupby("faixa").agg(
        linhas_corrigidas=("desvio_do_reordenamento", "size"),
        correcao_mediana=("desvio_do_reordenamento", "median"),
        correcao_p90=("desvio_do_reordenamento", quantil_90),
        casos_reais_medianos=("real", "median"),
    )
    return taxa_de_cruzamento.join(tamanho_da_correcao)


def quantil_90(serie: pd.Series) -> float:
    """Devolve o percentil 90 de uma serie. Existe para evitar lambda no agg."""
    return serie.quantile(0.9)


def medir_cobertura_por_faixa(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Mede quantas vezes o valor real caiu dentro dos intervalos previstos.

    Args:
        previsoes: A tabela de `carregar_previsoes`.

    Returns:
        Uma linha por (modelo, faixa), com a cobertura observada dos intervalos
        de 50% e de 90%. O esperado, se as faixas fossem calibradas, seria
        50% e 90%.
    """
    colunas_da_linha = ["modelo", "h", "data_alvo", "faixa", "real"]
    em_formato_largo = previsoes.pivot_table(
        index=colunas_da_linha, columns="quantil", values="previsto"
    ).reset_index()

    dentro_do_ic50 = (
        em_formato_largo["real"] >= em_formato_largo[QUANTIL_INFERIOR_IC50]
    ) & (em_formato_largo["real"] <= em_formato_largo[QUANTIL_SUPERIOR_IC50])
    dentro_do_ic90 = (
        em_formato_largo["real"] >= em_formato_largo[QUANTIL_INFERIOR_IC90]
    ) & (em_formato_largo["real"] <= em_formato_largo[QUANTIL_SUPERIOR_IC90])

    em_formato_largo["dentro_do_ic50"] = dentro_do_ic50
    em_formato_largo["dentro_do_ic90"] = dentro_do_ic90

    return em_formato_largo.groupby(["modelo", "faixa"]).agg(
        semanas=("real", "size"),
        cobertura_ic50=("dentro_do_ic50", "mean"),
        cobertura_ic90=("dentro_do_ic90", "mean"),
    )


def main() -> None:
    """Roda o diagnostico e grava as duas tabelas em `saidas/`."""
    PASTA_SAIDAS.mkdir(exist_ok=True)
    previsoes = carregar_previsoes(CAMINHO_PREVISOES)
    print(f"Previsoes lidas: {len(previsoes)} linhas, {previsoes['modelo'].nunique()} modelos.")

    cruzamento = medir_cruzamento_por_faixa(previsoes)
    cobertura = medir_cobertura_por_faixa(previsoes)

    cruzamento.to_csv(PASTA_SAIDAS / "cruzamento_por_faixa.csv")
    cobertura.to_csv(PASTA_SAIDAS / "cobertura_por_faixa.csv")

    print("\n=== CRUZAMENTO DE QUANTIS, POR FAIXA ===")
    print(cruzamento.round(1).to_string())
    print("\n=== COBERTURA DOS INTERVALOS, POR FAIXA ===")
    print(cobertura.round(3).to_string())


if __name__ == "__main__":
    main()
