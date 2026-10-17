"""E7: previsoes de varios quantis e a correcao de cruzamentos.

Cada quantil e treinado por um HistGB SEPARADO; nada garante que, numa mesma
origem, os 7 valores saiam em ordem crescente. A correcao e a do antigo
(`analises/2026-09-26_wis_na_tabela_restaurada/rodar.py:ordenar_quantis_cruzados`):
ordenar os 7 valores da origem e devolve-los na ordem dos niveis (rearranjo
isotonico). Nenhum numero novo e inventado: so troca de lugar.

Funcoes puras: nao leem nem gravam arquivo.
"""

import numpy as np
import pandas as pd

from aedes.configuracao import COLUNA_DATA_ALVO
from aedes.metricas import COLUNA_DO_PREVISTO
from aedes.walk_forward import COLUNA_DO_HORIZONTE

# Os 7 niveis do WIS (pre-declaracao E7). A mediana (0,50) e o centro; os pares
# (0,25 ; 0,75), (0,10 ; 0,90) e (0,05 ; 0,95) sao os intervalos de 50, 80 e 90%.
QUANTIS_DO_WIS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
# Quantil que a E7 treina so para a TRAVA (reproduzir a referencia certificada).
QUANTIL_DA_TRAVA = 0.85
HORIZONTES_DA_TRAVA = (1, 4, 8, 12)

COLUNA_DA_FOLHA = "folha"
COLUNA_DO_QUANTIL = "quantil"
COLUNA_DO_PREVISTO_BRUTO = "previsto_bruto"
COLUNA_DO_CRUZAMENTO = "cruzamento_corrigido"
COLUNAS_DA_ORIGEM = [COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]
TOLERANCIA_DO_NIVEL_DO_QUANTIL = 1e-12


def ordenar_quantis_cruzados(
    previsoes_por_quantil: pd.DataFrame,
    quantis: tuple[float, ...] = QUANTIS_DO_WIS,
) -> pd.DataFrame:
    """Rearranja os quantis de cada origem em ordem crescente e marca as origens que cruzaram.

    Uma ORIGEM e (folha, h, data_alvo). Cada origem deve ter EXATAMENTE uma
    linha por nivel de `quantis`. Os valores originais ficam em `previsto_bruto`;
    `previsto` recebe os mesmos valores, ordenados do menor para o maior e
    atribuidos aos niveis em ordem crescente. `cruzamento_corrigido` e verdadeiro
    em todas as linhas da origem em que algum quantil superior era MENOR que o
    anterior (igualdade nao e cruzamento: `diff >= 0` esta em ordem).

    Args:
        previsoes_por_quantil: Colunas `folha`, `h`, `data_alvo`, `quantil`,
            `previsto` (e quaisquer outras, que sao mantidas), uma linha por
            origem e nivel.
        quantis: Os niveis esperados em cada origem.

    Returns:
        DataFrame NOVO ordenado por (folha, h, data_alvo, quantil), com as
        colunas de entrada, `previsto_bruto` e `cruzamento_corrigido`.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver `previsto` ausente ou infinito, se alguma origem
            nao tiver exatamente os niveis esperados, ou se os niveis forem repetidos.
    """
    colunas_necessarias = [*COLUNAS_DA_ORIGEM, COLUNA_DO_QUANTIL, COLUNA_DO_PREVISTO]
    colunas_ausentes = sorted(set(colunas_necessarias) - set(previsoes_por_quantil.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes nas previsoes por quantil: {colunas_ausentes}")

    niveis_ordenados = np.array(sorted(quantis), dtype=float)
    quantidade_de_niveis = len(niveis_ordenados)
    if len(set(quantis)) != quantidade_de_niveis:
        raise ValueError(f"quantis repetidos: {quantis!r}.")

    valores = previsoes_por_quantil[COLUNA_DO_PREVISTO].to_numpy(dtype=float)
    if not np.isfinite(valores).all():
        raise ValueError("previsto com valor ausente ou infinito.")

    ordenado = previsoes_por_quantil.sort_values([*COLUNAS_DA_ORIGEM, COLUNA_DO_QUANTIL]).reset_index(drop=True)
    quantidade_de_linhas = len(ordenado)
    if quantidade_de_linhas % quantidade_de_niveis != 0:
        raise ValueError(
            f"{quantidade_de_linhas} linhas nao e multiplo de {quantidade_de_niveis} niveis: "
            "ha origem incompleta."
        )

    niveis_por_origem = ordenado[COLUNA_DO_QUANTIL].to_numpy(dtype=float).reshape(-1, quantidade_de_niveis)
    niveis_conferem = np.allclose(
        niveis_por_origem, niveis_ordenados[np.newaxis, :], rtol=0.0, atol=TOLERANCIA_DO_NIVEL_DO_QUANTIL
    )
    if not niveis_conferem:
        raise ValueError(f"Alguma origem nao tem exatamente os niveis {list(niveis_ordenados)}.")

    horizontes_por_origem = ordenado[COLUNA_DO_HORIZONTE].to_numpy().reshape(-1, quantidade_de_niveis)
    folhas_por_origem = ordenado[COLUNA_DA_FOLHA].to_numpy().reshape(-1, quantidade_de_niveis)
    datas_por_origem = ordenado[COLUNA_DATA_ALVO].to_numpy().reshape(-1, quantidade_de_niveis)
    for nome_da_chave, chaves_por_origem in (
        (COLUNA_DO_HORIZONTE, horizontes_por_origem),
        (COLUNA_DA_FOLHA, folhas_por_origem),
        (COLUNA_DATA_ALVO, datas_por_origem),
    ):
        if not (chaves_por_origem == chaves_por_origem[:, [0]]).all():
            raise ValueError(f"Origem com {nome_da_chave} misturado: faltam ou sobram niveis.")

    valores_brutos = ordenado[COLUNA_DO_PREVISTO].to_numpy(dtype=float).reshape(-1, quantidade_de_niveis)
    valores_ordenados = np.sort(valores_brutos, axis=1)
    diferencas_entre_niveis = np.diff(valores_brutos, axis=1)
    origem_ja_em_ordem = np.all(diferencas_entre_niveis >= 0, axis=1)
    cruzamento_por_origem = ~origem_ja_em_ordem

    ordenado[COLUNA_DO_PREVISTO_BRUTO] = ordenado[COLUNA_DO_PREVISTO]
    ordenado[COLUNA_DO_PREVISTO] = valores_ordenados.reshape(-1)
    ordenado[COLUNA_DO_CRUZAMENTO] = np.repeat(cruzamento_por_origem, quantidade_de_niveis)
    return ordenado


def contar_origens_com_cruzamento(previsoes_ordenadas: pd.DataFrame) -> pd.DataFrame:
    """Quantas origens precisaram de rearranjo, por folha e horizonte.

    Args:
        previsoes_ordenadas: Saida de `ordenar_quantis_cruzados`.

    Returns:
        DataFrame com `folha`, `h`, `origens`, `com_cruzamento`, `fracao`.

    Raises:
        KeyError: Se faltar coluna.
    """
    colunas_necessarias = [*COLUNAS_DA_ORIGEM, COLUNA_DO_CRUZAMENTO]
    colunas_ausentes = sorted(set(colunas_necessarias) - set(previsoes_ordenadas.columns))
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes: {colunas_ausentes}")

    cruzou_por_origem = previsoes_ordenadas.groupby(COLUNAS_DA_ORIGEM, sort=True)[COLUNA_DO_CRUZAMENTO].any()
    linhas: list[dict[str, object]] = []
    por_folha_e_horizonte = cruzou_por_origem.groupby(level=[COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE], sort=True)
    for (folha, horizonte), cruzou in por_folha_e_horizonte:
        origens = len(cruzou)
        com_cruzamento = int(cruzou.sum())
        linhas.append(
            {
                COLUNA_DA_FOLHA: folha,
                COLUNA_DO_HORIZONTE: horizonte,
                "origens": origens,
                "com_cruzamento": com_cruzamento,
                "fracao": com_cruzamento / origens,
            }
        )
    return pd.DataFrame(linhas, columns=[COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE, "origens", "com_cruzamento", "fracao"])
