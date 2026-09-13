"""

As 22 configuracoes do grid de 30/08 que ainda faltam rodar corrigidas.

Oito ja rodaram de manha (rodar_corrigido.py + rodar_corrigido_padrao.py) e
mostraram que o vazamento NAO era neutro: com vetor apanhou ~2x mais que sem
vetor, e a perda quantilica ~2x mais que a padrao. Como esses sao os dois
ingredientes da configuracao vencedora, o ranking das 30 precisa ser remedido
inteiro - e o criterio pre-declarado (EMENDA E1.2) de fato reprovou.

Este script completa as 30. A lista sai do proprio ranking de 30/08, tirando
as 8 ja feitas, para nao haver chance de esquecer ou duplicar configuracao.

Uso:  python rodar_grid_restante.py

"""

import sys
import time
import traceback
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_GRID_ORIGINAL = PASTA_ANALISE.parent / "2026-08-30_grid_completo"
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"

sys.path.insert(0, str(PASTA_PACOTE))
sys.path.insert(0, str(PASTA_GRID_ORIGINAL))

import numpy as np
import pandas as pd

from rodar_corrigido import HORIZONTES, rodar_celula
from rodar_grid import montar_dados_e_conjuntos

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
CAMINHO_CHECKPOINT = PASTA_SAIDAS / "corrigido_previsoes_restante.csv"
CAMINHO_RANKING = PASTA_GRID_ORIGINAL / "saidas" / "grid_ranking_completo.csv"
JA_RODADAS = PASTA_SAIDAS / "corrigido_previsoes_parciais.csv", PASTA_SAIDAS / "corrigido_previsoes_padrao.csv"


def alpha_da_perda(rotulo_perda: str) -> float | None:
    """Converte o rotulo da perda no valor de alpha ('padrao' -> None)."""
    if rotulo_perda == "padrao":
        return None
    return float(rotulo_perda.removeprefix("quantil_"))


def listar_configuracoes_que_faltam() -> list[tuple]:
    """

    Devolve as configuracoes do ranking de 30/08 que ainda nao rodaram corrigidas.

    Returns:
        Lista de (posicao, algoritmo, alpha, conjunto), em ordem de ranking.

    """
    ranking = pd.read_csv(CAMINHO_RANKING)
    feitas = pd.concat([pd.read_csv(caminho) for caminho in JA_RODADAS], ignore_index=True)
    chaves_feitas = set(
        feitas[["algoritmo", "perda", "conjunto"]].drop_duplicates()
        .itertuples(index=False, name=None)
    )

    faltando = []
    for linha in ranking.itertuples(index=False):
        if (linha.algoritmo, linha.perda, linha.conjunto) in chaves_feitas:
            continue
        faltando.append((linha.pos, linha.algoritmo, alpha_da_perda(linha.perda), linha.conjunto))
    return faltando


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    if CAMINHO_CHECKPOINT.exists():
        print(f"ABORTADO: {CAMINHO_CHECKPOINT.name} ja existe.", flush=True)
        return

    configuracoes = listar_configuracoes_que_faltam()
    total_celulas = len(configuracoes) * len(HORIZONTES)
    print(f"faltavam {len(configuracoes)} configuracoes de 30 | {total_celulas} celulas", flush=True)
    if len(configuracoes) != 22:
        print(f"ATENCAO: esperava 22 configuracoes, achei {len(configuracoes)}. "
              f"Conferir antes de confiar no resultado.", flush=True)

    tabela, conjuntos = montar_dados_e_conjuntos()

    contador = 0
    falhas = 0
    for posicao, nome_algoritmo, alpha, rotulo_conjunto in configuracoes:
        for horizonte in HORIZONTES:
            contador += 1
            rotulo_perda = "padrao" if alpha is None else f"quantil_{alpha:.2f}"
            rotulo = (f"pos{posicao:02d} | {nome_algoritmo} | {rotulo_perda} | "
                      f"{rotulo_conjunto} | h={horizonte}")
            inicio = time.time()
            try:
                previsoes = rodar_celula(
                    tabela, conjuntos[rotulo_conjunto], nome_algoritmo, alpha, horizonte
                )
                previsoes["algoritmo"] = nome_algoritmo
                previsoes["perda"] = rotulo_perda
                previsoes["conjunto"] = rotulo_conjunto
                previsoes["pos_ranking_30_08"] = posicao

                cabecalho = not CAMINHO_CHECKPOINT.exists()
                previsoes.to_csv(CAMINHO_CHECKPOINT, mode="a", header=cabecalho, index=False)
                print(f"[{contador:3d}/{total_celulas}] {rotulo}: {len(previsoes)} semanas "
                      f"({(time.time() - inicio) / 60:.1f} min)", flush=True)
            except Exception as erro:
                falhas += 1
                print(f"[{contador:3d}/{total_celulas}] {rotulo}: FALHOU - {erro}", flush=True)
                traceback.print_exc()

    duracao = (time.time() - momento_inicial) / 60
    print(f"\nCONCLUIDO: {contador - falhas} de {total_celulas} | falhas: {falhas} | "
          f"{duracao:.1f} min ({duracao / 60:.1f} h)", flush=True)


if __name__ == "__main__":
    main()
