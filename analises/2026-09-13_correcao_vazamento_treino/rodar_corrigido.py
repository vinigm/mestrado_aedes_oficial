"""

Rodada corrigida: o corte de treino passa a respeitar a data da RESPOSTA.

Pre-declarado em PRE_DECLARACAO.md antes de rodar. Esta e uma replica do
grid de 30/08/2026 com UMA unica alteracao de comportamento: quais linhas
entram no treino a cada passo do walk-forward.

O DEFEITO QUE ESTE SCRIPT CORRIGE

  O grid original seleciona o treino por POSICAO: validos.iloc[:indice_corte],
  isto e, "toda linha cuja PERGUNTA foi feita antes da semana de teste". Mas
  cada linha carrega como rotulo (y_h) o valor de h semanas depois dela. Entao
  as h-1 linhas mais recentes do treino tem rotulo datado DEPOIS da semana que
  esta sendo prevista - informacao que nao existia no momento da previsao.

  Exemplo real, h=12: ao prever 26/05/2024 a partir de 03/03/2024, o treino
  original inclui a linha de 18/02/2024, cujo rotulo e 12/05/2024 = 1.510
  casos, o pico da epidemia.

  A correcao filtra por DATA, nao por posicao: so entra a linha cuja resposta
  ja tinha acontecido na data em que a previsao e feita.

POR QUE FILTRAR POR DATA E NAO POR POSICAO

  A forma curta - iloc[:indice_corte - horizonte + 1] - parece equivalente e
  esta ERRADA: depois do dropna a tabela tem buracos (as semanas da enchente
  de maio/2024 saem do conjunto M1, porque o vetor e NaN nelas). Com buraco,
  recuar 12 POSICOES nao equivale a recuar 12 SEMANAS.

O QUE E MANTIDO IDENTICO AO GRID DE 30/08

  Tabela, corte de maturidade, features, as 6 colunas de clima, os
  hiperparametros e o laco de teste. As tres primeiras vem importadas do
  proprio rodar_grid.py, para que nao exista chance de divergencia por copia.
  Os pontos de teste sao os MESMOS, o que torna a comparacao antes/depois
  pareada por construcao.

Uso:  python rodar_corrigido.py

"""

import sys
import time
import traceback
from pathlib import Path

PASTA_ANALISE = Path(__file__).resolve().parent
PASTA_GRID_ORIGINAL = PASTA_ANALISE.parent / "2026-08-30_grid_completo"
PASTA_PACOTE = PASTA_ANALISE.parents[1] / "modelagem_aedes"

# O pacote do projeto e a pasta do grid original precisam estar no path: o
# setup (tabela, conjuntos, hiperparametros) vem importado de la, nao copiado.
sys.path.insert(0, str(PASTA_PACOTE))
sys.path.insert(0, str(PASTA_GRID_ORIGINAL))

import numpy as np
import pandas as pd

from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from dominio.features import construir_alvo_horizonte
from rodar_grid import ALGORITMOS, montar_dados_e_conjuntos, montar_parametros

PASTA_SAIDAS = PASTA_ANALISE / "saidas"
CAMINHO_CHECKPOINT = PASTA_SAIDAS / "corrigido_previsoes_parciais.csv"

HORIZONTES = (1, 4, 8, 12)
PASSO_TESTE = 1

# As celulas pre-declaradas. Bloco A e a configuracao de referencia (M0 e M1);
# bloco B sao as posicoes 1, 2, 4, 15, 26 e 30 do ranking de 30/08, escolhidas
# antes de rodar para cobrir topo, meio e fundo. As posicoes 1 e 15 sao as
# proprias celulas do bloco A, entao a uniao tem 6 configuracoes.
CONFIGURACOES = (
    # (posicao no ranking de 30/08, algoritmo, alpha, conjunto)
    (1, "hist_gradient_boosting", 0.80, "M1_com_vetor"),
    (15, "hist_gradient_boosting", 0.80, "M0_sem_vetor"),
    (2, "hist_gradient_boosting", 0.85, "M1_com_vetor"),
    (4, "gradient_boosting", 0.70, "M1_com_vetor"),
    (26, "lightgbm", 0.70, "M0_sem_vetor"),
    (30, "lightgbm", 0.90, "M1_com_vetor"),
)


def rodar_celula(
    tabela: pd.DataFrame,
    colunas_modelo: list[str],
    nome_algoritmo: str,
    alpha: float | None,
    horizonte: int,
) -> pd.DataFrame:
    """

    Walk-forward de uma celula, com o corte de treino corrigido.

    Identica a rodar_grid.rodar_celula, exceto pela linha que monta o treino:
    la e um fatiamento por posicao, aqui e um filtro por data da resposta.

    Args:
        tabela: Tabela semanal ja com features e corte de maturidade.
        colunas_modelo: Colunas do conjunto (M0 ou M1).
        nome_algoritmo: Chave em ALGORITMOS.
        alpha: Quantil da perda quantilica, ou None para perda padrao.
        horizonte: Quantas semanas a frente se preve.

    Returns:
        Tabela com uma linha por semana testada: h, data_alvo, real, pred,
        n_treino e n_treino_original (para medir o que a correcao descartou).

    """
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
    atraso_do_horizonte = pd.Timedelta(weeks=horizonte)

    linhas = []
    for indice_corte in range(config.minimo_semanas_treino, len(validos), PASSO_TESTE):
        teste = validos.iloc[indice_corte:indice_corte + 1]
        data_de_origem_do_teste = teste["data"].to_numpy()[0]

        # A CORRECAO. So entra no treino a linha cuja RESPOSTA ja tinha
        # acontecido na data em que esta previsao e feita. O original usava
        # validos.iloc[:indice_corte], que filtra pela data da PERGUNTA.
        linha_ja_respondida = (
            validos["data"] + atraso_do_horizonte <= data_de_origem_do_teste
        )
        treino = validos.loc[linha_ja_respondida]

        modelo = ficha["classe"](**parametros)
        modelo.fit(treino[colunas_usadas], treino["y_h"])
        previsao = float(modelo.predict(teste[colunas_usadas])[0])

        data_alvo = data_de_origem_do_teste + np.timedelta64(horizonte * 7, "D")
        linhas.append({
            "h": horizonte,
            "data_alvo": data_alvo,
            "real": float(teste["y_h"].to_numpy()[0]),
            "pred": max(previsao, 0.0),
            "n_treino": len(treino),
            "n_treino_original": indice_corte,
        })

    return pd.DataFrame(linhas)


def main() -> None:
    momento_inicial = time.time()
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    if CAMINHO_CHECKPOINT.exists():
        print(f"ABORTADO: {CAMINHO_CHECKPOINT.name} ja existe. "
              f"Apague ou renomeie antes de rodar de novo.", flush=True)
        return

    tabela, conjuntos = montar_dados_e_conjuntos()

    total_celulas = len(CONFIGURACOES) * len(HORIZONTES)
    print(f"rodada corrigida: {total_celulas} celulas | passo={PASSO_TESTE}", flush=True)
    print(f"M0={len(conjuntos['M0_sem_vetor'])} colunas | "
          f"M1={len(conjuntos['M1_com_vetor'])} colunas\n", flush=True)

    contador = 0
    falhas = 0
    for posicao, nome_algoritmo, alpha, rotulo_conjunto in CONFIGURACOES:
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
                previsoes.to_csv(
                    CAMINHO_CHECKPOINT, mode="a", header=cabecalho, index=False
                )

                descartadas = (
                    previsoes["n_treino_original"] - previsoes["n_treino"]
                ).max()
                print(f"[{contador:2d}/{total_celulas}] {rotulo}: {len(previsoes)} semanas, "
                      f"ate {descartadas} linhas descartadas do treino "
                      f"({(time.time() - inicio) / 60:.1f} min)", flush=True)
            except Exception as erro:
                falhas += 1
                print(f"[{contador:2d}/{total_celulas}] {rotulo}: FALHOU - {erro}", flush=True)
                traceback.print_exc()

    duracao_total = (time.time() - momento_inicial) / 60
    print(f"\nRODADA CONCLUIDA: {contador - falhas} de {total_celulas} | falhas: {falhas}",
          flush=True)
    print(f"tempo total: {duracao_total:.1f} min", flush=True)
    print(f"previsoes em: {CAMINHO_CHECKPOINT}", flush=True)


if __name__ == "__main__":
    main()
