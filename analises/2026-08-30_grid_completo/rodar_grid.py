"""

Grid completo: algoritmo x perda x conjunto de features x horizonte.

Pre-declarado em PRE_DECLARACAO.md antes de rodar. 120 execucoes de
walk-forward (3 algoritmos x 5 perdas x 2 conjuntos x 4 horizontes), passo=1.

Duas decisoes de robustez, porque a rodada e longa e ninguem estara olhando:

  - CHECKPOINT: cada celula do grid e gravada em disco assim que termina. Se o
    processo morrer no meio, nada do que ja rodou se perde e da para retomar.
  - NAO PARA NO ERRO: se uma celula falhar, ela e registrada como falha e o
    grid continua. Uma combinacao que quebra nao pode derrubar as outras 119.

Uso:  python rodar_grid.py

"""

import sys
import time
import traceback
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"
sys.path.insert(0, str(PASTA_PACOTE))

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor

from acesso import fontes
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio import features, selecao_features, surto
from dominio.features import construir_alvo_horizonte

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
CAMINHO_CHECKPOINT = PASTA_SAIDAS / "grid_previsoes_parciais.csv"

HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1
LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
ALPHAS = (0.70, 0.80, 0.85, 0.90)

# Hiperparametros de cada algoritmo, identicos aos do projeto
# (config/experimentos/cidade_regressao_modelos.py e cidade_regressao.py).
ALGORITMOS = {
    "hist_gradient_boosting": {
        "classe": HistGradientBoostingRegressor,
        "parametros": {"max_iter": 250, "learning_rate": 0.05, "max_leaf_nodes": 15,
                       "min_samples_leaf": 5, "random_state": 42},
        "chave_perda": "loss",
        "nome_perda_padrao": "squared_error",
        "nome_perda_quantil": "quantile",
        "chave_alpha": "quantile",
    },
    "gradient_boosting": {
        "classe": GradientBoostingRegressor,
        "parametros": {"n_estimators": 250, "learning_rate": 0.05, "max_depth": 3,
                       "min_samples_leaf": 5, "random_state": 42},
        "chave_perda": "loss",
        "nome_perda_padrao": "squared_error",
        "nome_perda_quantil": "quantile",
        "chave_alpha": "alpha",
    },
    "lightgbm": {
        "classe": LGBMRegressor,
        "parametros": {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31,
                       "min_child_samples": 20, "verbose": -1, "n_jobs": -1, "random_state": 42},
        "chave_perda": "objective",
        "nome_perda_padrao": "regression",
        "nome_perda_quantil": "quantile",
        "chave_alpha": "alpha",
    },
}


def montar_dados_e_conjuntos() -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Reproduz o preparo do cenario 1 e devolve a tabela e os dois conjuntos."""
    config = CIDADE_REGRESSAO

    tabela = fontes.carregar_tabela_final()
    tabela = surto.aplicar_corte_maturidade(tabela, config.semanas_corte_maturidade)
    tabela = features.construir_features_temporais(tabela)

    colunas_nucleo, colunas_clima, colunas_vetor = selecao_features.separar_grupos_de_features(
        tabela, config.colunas_ignorar, config.padroes_vetor, config.padroes_clima
    )
    ranking_clima = selecao_features.selecionar_clima_por_ganho(
        tabela, colunas_nucleo, colunas_clima, config.coluna_alvo,
        config.horizontes_selecao_clima, config.modelo_selecao_clima,
        config.fracao_treino_selecao,
    )
    clima_enxuto = ranking_clima.head(6).index.tolist()

    conjuntos = {
        "M0_sem_vetor": colunas_nucleo + clima_enxuto,
        "M1_com_vetor": colunas_nucleo + clima_enxuto + colunas_vetor,
    }
    return tabela, conjuntos


def montar_parametros(nome_algoritmo: str, alpha: float | None) -> dict:
    """Monta os parametros do algoritmo com a perda pedida (padrao ou quantil)."""
    ficha = ALGORITMOS[nome_algoritmo]
    parametros = dict(ficha["parametros"])

    if alpha is None:
        parametros[ficha["chave_perda"]] = ficha["nome_perda_padrao"]
    else:
        parametros[ficha["chave_perda"]] = ficha["nome_perda_quantil"]
        parametros[ficha["chave_alpha"]] = alpha

    return parametros


def rodar_celula(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    nome_algoritmo: str,
    alpha: float | None,
    horizonte: int,
) -> pd.DataFrame:
    """Walk-forward de uma celula do grid."""
    config = CIDADE_REGRESSAO
    ficha = ALGORITMOS[nome_algoritmo]

    dados = construir_alvo_horizonte(tabela, config.coluna_alvo, horizonte)
    colunas_usadas = colunas_modelo + ["alvo_sin", "alvo_cos"]

    validos = (
        dados.dropna(subset=colunas_usadas + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )
    parametros = montar_parametros(nome_algoritmo, alpha)

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), PASSO_TESTE):
        treino = validos.iloc[:indice_corte]
        teste = validos.iloc[indice_corte:indice_corte + 1]

        modelo = ficha["classe"](**parametros)
        modelo.fit(treino[colunas_usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[colunas_usadas])[0])

        data_alvo = teste["data"].to_numpy()[0] + np.timedelta64(horizonte * 7, "D")
        linhas.append({
            "h": horizonte,
            "data_alvo": data_alvo,
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    tabela, conjuntos = montar_dados_e_conjuntos()

    perdas = [("padrao", None)]
    for alpha in ALPHAS:
        perdas.append((f"quantil_{alpha:.2f}", alpha))

    total_celulas = len(ALGORITMOS) * len(perdas) * len(conjuntos) * len(HORIZONTES)
    print(f"grid: {total_celulas} celulas | passo={PASSO_TESTE}", flush=True)
    print(f"M0={len(conjuntos['M0_sem_vetor'])} colunas | "
          f"M1={len(conjuntos['M1_com_vetor'])} colunas\n", flush=True)

    contador = 0
    falhas = 0
    for nome_algoritmo in ALGORITMOS:
        for rotulo_perda, alpha in perdas:
            for rotulo_conjunto, colunas in conjuntos.items():
                for horizonte in HORIZONTES:
                    contador += 1
                    rotulo = f"{nome_algoritmo} | {rotulo_perda} | {rotulo_conjunto} | h={horizonte}"
                    inicio = time.time()

                    try:
                        previsoes = rodar_celula(
                            tabela, colunas, nome_algoritmo, alpha, horizonte
                        )
                        previsoes["algoritmo"] = nome_algoritmo
                        previsoes["perda"] = rotulo_perda
                        previsoes["conjunto"] = rotulo_conjunto

                        # Checkpoint: grava a celula assim que ela termina.
                        cabecalho = not CAMINHO_CHECKPOINT.exists()
                        previsoes.to_csv(
                            CAMINHO_CHECKPOINT, mode="a", header=cabecalho, index=False
                        )

                        print(f"[{contador:3d}/{total_celulas}] {rotulo}: "
                              f"{len(previsoes)} semanas ({(time.time() - inicio) / 60:.1f} min)",
                              flush=True)
                    except Exception as erro:
                        falhas += 1
                        print(f"[{contador:3d}/{total_celulas}] {rotulo}: FALHOU — {erro}",
                              flush=True)
                        traceback.print_exc()

    duracao_total = (time.time() - momento_inicial) / 60
    print(f"\nGRID CONCLUIDO: {contador - falhas} de {total_celulas} | falhas: {falhas}",
          flush=True)
    print(f"tempo total: {duracao_total:.1f} min ({duracao_total / 60:.1f} h)", flush=True)
    print(f"previsoes em: {CAMINHO_CHECKPOINT}", flush=True)


if __name__ == "__main__":
    main()
