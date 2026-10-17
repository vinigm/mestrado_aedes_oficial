"""Pecas comuns da certificacao adversarial da E1 e do piso de ruido (codigo independente).

Nao importa experimentos/e1_quantil.py, experimentos/piso_de_ruido.py nem aedes/perturbacao.py.
Usa dos modulos certificados SO a montagem da matriz (aedes.dados, aedes.variaveis, aedes.configuracao).
O laco de treino e proprio, direto com scikit-learn.
"""

import os
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PASTA_DO_PROJETO))

from aedes.configuracao import (  # noqa: E402
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes  # noqa: E402
from aedes.variaveis import montar_matriz_do_horizonte  # noqa: E402

PASTA_DA_CERTIFICACAO = pathlib.Path(__file__).resolve().parent
PASTA_DA_CIENCIA = PASTA_DO_PROJETO / "resultados" / "ciencia"
CAMINHO_DA_REFERENCIA = PASTA_DO_PROJETO / "resultados" / "referencia" / "previsoes.csv"
PASTA_DO_GABARITO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"

COLUNA_ORIGEM = "data_origem"
COLUNA_ALVO_DATA = "data_alvo"
COLUNA_Y = "y_h"
COLUNAS_FORA_DAS_VARIAVEIS = (COLUNA_ORIGEM, COLUNA_ALVO_DATA, COLUNA_Y)

FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
INICIO_DA_JANELA = pd.Timestamp("2024-01-07")
FIM_DA_JANELA = pd.Timestamp("2026-02-01")
TREINO_MINIMO = 104


def carregar_tabela_cortada() -> pd.DataFrame:
    """Le dados/tabela_final.csv (hash conferido por aedes.dados) e aplica o corte de maturidade."""
    caminho = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
    conteudo_em_bytes = caminho.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    return aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)


def montar_matriz_completa(tabela_cortada: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Matriz do braco completo (22 variaveis) de um horizonte, pelo modulo certificado."""
    return montar_matriz_do_horizonte(tabela_cortada, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)


def criar_modelo_proprio(minimo_por_folha: int, quantil: float) -> HistGradientBoostingRegressor:
    """HistGB escrito aqui a partir dos hiperparametros do enunciado (demais = padrao do sklearn)."""
    return HistGradientBoostingRegressor(
        loss="quantile",
        quantile=quantil,
        max_iter=250,
        learning_rate=0.05,
        max_leaf_nodes=15,
        min_samples_leaf=minimo_por_folha,
        random_state=42,
    )


def nomes_das_variaveis(matriz: pd.DataFrame) -> list[str]:
    """Colunas da matriz que sao variaveis do modelo, na ordem da matriz."""
    nomes: list[str] = []
    for nome in matriz.columns:
        if nome not in COLUNAS_FORA_DAS_VARIAVEIS:
            nomes.append(str(nome))
    return nomes


def prever_uma_origem(
    matriz: pd.DataFrame,
    posicao_da_origem: int,
    horizonte: int,
    minimo_por_folha: int,
    quantil: float,
) -> float:
    """Treina so com linhas cuja resposta ja era conhecida na origem (data_origem + h <= t) e preve a origem."""
    variaveis = nomes_das_variaveis(matriz)
    datas_de_origem = matriz[COLUNA_ORIGEM].to_numpy(dtype="datetime64[ns]")
    data_da_origem = datas_de_origem[posicao_da_origem]
    atraso = np.timedelta64(7 * horizonte, "D")
    mascara_do_treino = (datas_de_origem + atraso) <= data_da_origem
    matriz_de_treino = matriz.loc[mascara_do_treino, variaveis].to_numpy(dtype=float)
    alvo_de_treino = matriz.loc[mascara_do_treino, COLUNA_Y].to_numpy(dtype=float)
    linha_de_teste = matriz.iloc[[posicao_da_origem]][variaveis].to_numpy(dtype=float)
    modelo = criar_modelo_proprio(minimo_por_folha, quantil)
    modelo.fit(matriz_de_treino, alvo_de_treino)
    return float(modelo.predict(linha_de_teste)[0])


def walk_forward_proprio(
    matriz: pd.DataFrame,
    horizonte: int,
    minimo_por_folha: int,
    quantil: float,
) -> pd.DataFrame:
    """Walk-forward completo (passo 1, treino minimo 104): colunas data_origem, data_alvo, real, previsto."""
    linhas: list[dict[str, object]] = []
    for posicao in range(TREINO_MINIMO, len(matriz)):
        previsto = prever_uma_origem(matriz, posicao, horizonte, minimo_por_folha, quantil)
        linhas.append(
            {
                COLUNA_ORIGEM: matriz[COLUNA_ORIGEM].iloc[posicao],
                COLUNA_ALVO_DATA: matriz[COLUNA_ALVO_DATA].iloc[posicao],
                "real": float(matriz[COLUNA_Y].iloc[posicao]),
                "previsto": previsto,
            }
        )
    return pd.DataFrame(linhas)


def gravar_csv_atomico(tabela: pd.DataFrame, caminho: pathlib.Path) -> None:
    """Grava o CSV num temporario e renomeia."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + f".tmp{os.getpid()}")
    tabela.to_csv(temporario, index=False)
    os.replace(temporario, caminho)


def mae(reais: np.ndarray, previstos: np.ndarray) -> float:
    """Erro absoluto medio."""
    return float(np.mean(np.abs(reais - previstos)))


def ler_referencia() -> pd.DataFrame:
    """resultados/referencia/previsoes.csv com datas convertidas."""
    return pd.read_csv(CAMINHO_DA_REFERENCIA, parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA])
