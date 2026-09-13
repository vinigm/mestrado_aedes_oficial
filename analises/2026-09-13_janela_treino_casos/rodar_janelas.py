"""

Ablacao de janela de treino para o alvo CASOS.

Pre-declarado em PRE_DECLARACAO.md. A Rodada 4 de 29/08 respondeu isso para o
alvo densidade do VETOR (treinar desde 2012 vence). Para CASOS nunca foi feito,
e nao e a mesma pergunta: os casos so existem desde fev/2018, e a epidemiologia
mudou demais no periodo (2020+2021 somam 109 casos; 2024+2025 somam 43.827).

Quatro regimes, mesmo modelo, mesmas semanas de teste. So a janela muda.

Uso:  python rodar_janelas.py

"""

import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PACOTE = PASTA.parents[1] / "modelagem_aedes"
GRID = PASTA.parent / "2026-08-30_grid_completo"
sys.path.insert(0, str(PACOTE))
sys.path.insert(0, str(GRID))

import numpy as np
import pandas as pd

from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio.features import construir_alvo_horizonte
from motor import corte_temporal
from rodar_grid import ALGORITMOS, montar_dados_e_conjuntos, montar_parametros

SAIDAS = PASTA / "saidas"
HORIZONTES = (1, 4, 8, 12)
MINIMO_TREINO = 104
ALGORITMO, ALPHA, CONJUNTO = "hist_gradient_boosting", 0.85, "M1_com_vetor"

# A janela deslizante conta as ultimas N linhas UTILIZAVEIS, nao as ultimas N
# semanas antes da origem. Motivo: o corte temporal ja removeu as h-1 semanas
# mais recentes, entao "ultimas 104 semanas antes da origem" entregaria so ~93
# linhas em h=12 e o regime nunca alcancaria o minimo de treino.
REGIMES = {
    "expansivel_total": {"desde": None, "ultimas_linhas": None},
    "expansivel_2020": {"desde": pd.Timestamp("2020-01-01"), "ultimas_linhas": None},
    "deslizante_4anos": {"desde": None, "ultimas_linhas": 208},
    "deslizante_2anos": {"desde": None, "ultimas_linhas": 104},
}


def aplicar_regime(treino: pd.DataFrame, regime: dict) -> pd.DataFrame:
    """Recorta o treino ja liberado pelo corte temporal, conforme o regime."""
    if regime["desde"] is not None:
        treino = treino[treino["data"] >= regime["desde"]]
    if regime["ultimas_linhas"] is not None:
        treino = treino.tail(regime["ultimas_linhas"])
    return treino


def preparar(horizonte: int) -> pd.DataFrame:
    """Monta a tabela valida do horizonte, igual ao grid."""
    tabela, conjuntos = montar_dados_e_conjuntos()
    colunas = conjuntos[CONJUNTO] + ["alvo_sin", "alvo_cos"]
    dados = construir_alvo_horizonte(tabela, CIDADE_REGRESSAO.coluna_alvo, horizonte)
    validos = (dados.dropna(subset=colunas + ["y_h"]).sort_values("data").reset_index(drop=True))
    return validos, colunas


def cortes_comuns(validos: pd.DataFrame, horizonte: int) -> list[int]:
    """

    Os cortes em que TODOS os regimes tem pelo menos MINIMO_TREINO linhas.

    Sem isso os regimes seriam avaliados em semanas diferentes, e a comparacao
    misturaria efeito da janela com efeito da amostra.

    """
    aceitos = []
    for indice in range(MINIMO_TREINO, len(validos)):
        origem = validos["data"].to_numpy()[indice]
        liberado = corte_temporal.selecionar_treino_ja_respondido(validos, origem, horizonte)
        if all(len(aplicar_regime(liberado, r)) >= MINIMO_TREINO for r in REGIMES.values()):
            aceitos.append(indice)
    return aceitos


def main() -> None:
    SAIDAS.mkdir(parents=True, exist_ok=True)
    inicio_total = time.time()
    parametros = montar_parametros(ALGORITMO, ALPHA)
    ficha = ALGORITMOS[ALGORITMO]
    linhas = []

    for horizonte in HORIZONTES:
        validos, colunas = preparar(horizonte)
        cortes = cortes_comuns(validos, horizonte)
        print(f"h={horizonte:2d}: {len(validos)} linhas validas | {len(cortes)} cortes comuns "
              f"({validos['data'].to_numpy()[cortes[0]]} em diante)", flush=True)

        for nome_regime, regime in REGIMES.items():
            inicio = time.time()
            for indice in cortes:
                teste = validos.iloc[indice:indice + 1]
                origem = teste["data"].to_numpy()[0]
                liberado = corte_temporal.selecionar_treino_ja_respondido(validos, origem, horizonte)
                treino = aplicar_regime(liberado, regime)

                modelo = ficha["classe"](**parametros)
                modelo.fit(treino[colunas], treino["y_h"])
                previsao = float(modelo.predict(teste[colunas])[0])
                linhas.append({
                    "regime": nome_regime, "h": horizonte,
                    "data_alvo": origem + np.timedelta64(horizonte * 7, "D"),
                    "real": float(teste["y_h"].to_numpy()[0]), "pred": max(previsao, 0.0),
                    "n_treino": len(treino),
                })
            print(f"    {nome_regime:18s} {(time.time() - inicio) / 60:5.1f} min", flush=True)

    pd.DataFrame(linhas).to_csv(SAIDAS / "janelas_previsoes.csv", index=False)
    print(f"\nCONCLUIDO em {(time.time() - inicio_total) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
