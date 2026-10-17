"""Verificacao 2: retreina por conta propria (laco proprio, sklearn direto) a E1.

Modo `amostra`: q em {0,50, 0,90} x h em {1, 12} x 3 origens (inicio, meio e fim da calibracao), com a matriz INTEIRA
(sem truncagem) e com a matriz TRUNCADA em data_alvo <= 2023-12-31; compara os dois entre si e com as previsoes salvas.
Modo `completo`: refaz as 20 celulas (5 quantis x 4 horizontes) com a matriz truncada e compara com as salvas.
"""

import json
import sys
import time

import numpy as np
import pandas as pd

from comum_cert import (
    COLUNA_ALVO_DATA,
    COLUNA_ORIGEM,
    FIM_DA_CALIBRACAO,
    PASTA_DA_CERTIFICACAO,
    PASTA_DA_CIENCIA,
    TREINO_MINIMO,
    carregar_tabela_cortada,
    gravar_csv_atomico,
    montar_matriz_completa,
    prever_uma_origem,
    walk_forward_proprio,
)

modo = sys.argv[1]
tabela = carregar_tabela_cortada()
salvas = pd.read_csv(PASTA_DA_CIENCIA / "E1_quantil" / "previsoes.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA])
MINIMO_FOLHA_5 = 5


def previsto_salvo(quantil: float, horizonte: int, data_origem: pd.Timestamp) -> float:
    recorte = salvas.loc[
        (salvas["quantil"] == quantil) & (salvas["h"] == horizonte) & (salvas[COLUNA_ORIGEM] == data_origem)
    ]
    assert len(recorte) == 1, (quantil, horizonte, data_origem, len(recorte))
    return float(recorte["previsto"].iloc[0])


resultado: dict[str, object] = {}
if modo == "amostra":
    linhas: list[dict[str, object]] = []
    for quantil in (0.5, 0.9):
        for horizonte in (1, 12):
            matriz_inteira = montar_matriz_completa(tabela, horizonte)
            mascara_cal = matriz_inteira[COLUNA_ALVO_DATA] <= FIM_DA_CALIBRACAO
            matriz_truncada = matriz_inteira.loc[mascara_cal].reset_index(drop=True)
            ultima_posicao = len(matriz_truncada) - 1
            posicoes = [TREINO_MINIMO, (TREINO_MINIMO + ultima_posicao) // 2, ultima_posicao]
            for rotulo, posicao in zip(("inicio", "meio", "fim"), posicoes):
                data_origem = matriz_inteira[COLUNA_ORIGEM].iloc[posicao]
                assert data_origem == matriz_truncada[COLUNA_ORIGEM].iloc[posicao]
                sem_truncagem = prever_uma_origem(matriz_inteira, posicao, horizonte, MINIMO_FOLHA_5, quantil)
                com_truncagem = prever_uma_origem(matriz_truncada, posicao, horizonte, MINIMO_FOLHA_5, quantil)
                salvo = previsto_salvo(quantil, horizonte, data_origem)
                linhas.append(
                    {
                        "quantil": quantil,
                        "h": horizonte,
                        "origem": rotulo,
                        "data_origem": str(data_origem.date()),
                        "data_alvo": str(matriz_inteira[COLUNA_ALVO_DATA].iloc[posicao].date()),
                        "meu_sem_truncagem": sem_truncagem,
                        "meu_com_truncagem": com_truncagem,
                        "salvo": salvo,
                        "dif_vs_salvo": abs(sem_truncagem - salvo),
                        "dif_truncagem": abs(sem_truncagem - com_truncagem),
                    }
                )
                print(linhas[-1], flush=True)
    tabela_amostra = pd.DataFrame(linhas)
    tabela_amostra.to_csv(PASTA_DA_CERTIFICACAO / "verif_2_amostra.csv", index=False)
    resultado["n_fits"] = int(len(tabela_amostra))
    resultado["dif_max_vs_salvo"] = float(tabela_amostra["dif_vs_salvo"].max())
    resultado["dif_max_truncagem"] = float(tabela_amostra["dif_truncagem"].max())
    resultado["ultima_data_alvo_da_amostra"] = str(tabela_amostra["data_alvo"].max())
    (PASTA_DA_CERTIFICACAO / "verif_2_amostra.json").write_text(json.dumps(resultado, indent=2))
    print(resultado)
else:
    pasta_parciais = PASTA_DA_CERTIFICACAO / "parciais_e1"
    comparacoes: list[dict[str, object]] = []
    for quantil in (0.5, 0.7, 0.8, 0.85, 0.9):
        for horizonte in (1, 4, 8, 12):
            caminho = pasta_parciais / f"meu_q{round(quantil * 100):03d}_h{horizonte:02d}.csv"
            inicio = time.perf_counter()
            if caminho.exists():
                meu = pd.read_csv(caminho, parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA])
            else:
                matriz_inteira = montar_matriz_completa(tabela, horizonte)
                matriz_truncada = matriz_inteira.loc[matriz_inteira[COLUNA_ALVO_DATA] <= FIM_DA_CALIBRACAO].reset_index(drop=True)
                meu = walk_forward_proprio(matriz_truncada, horizonte, MINIMO_FOLHA_5, quantil)
                gravar_csv_atomico(meu, caminho)
            salvo = salvas.loc[(salvas["quantil"] == quantil) & (salvas["h"] == horizonte)]
            cruz = meu.merge(salvo, on=[COLUNA_ORIGEM, COLUNA_ALVO_DATA], how="outer", suffixes=("_meu", "_salvo"), indicator=True)
            ambos = cruz.loc[cruz["_merge"] == "both"]
            comparacoes.append(
                {
                    "quantil": quantil,
                    "h": horizonte,
                    "n_meu": int(len(meu)),
                    "n_salvo": int(len(salvo)),
                    "so_meu": int((cruz["_merge"] == "left_only").sum()),
                    "so_salvo": int((cruz["_merge"] == "right_only").sum()),
                    "dif_max_previsto": float((ambos["previsto_meu"] - ambos["previsto_salvo"]).abs().max()),
                    "dif_max_real": float((ambos["real_meu"] - ambos["real_salvo"]).abs().max()),
                    "mae_meu": float(np.mean(np.abs(meu["real"] - meu["previsto"]))),
                    "segundos": time.perf_counter() - inicio,
                }
            )
            print(comparacoes[-1], flush=True)
    tabela_comp = pd.DataFrame(comparacoes)
    tabela_comp.to_csv(PASTA_DA_CERTIFICACAO / "verif_2_completo.csv", index=False)
    maes_meu = tabela_comp.groupby("quantil")["mae_meu"].mean()
    resultado["dif_max_previsto"] = float(tabela_comp["dif_max_previsto"].max())
    resultado["dif_max_real"] = float(tabela_comp["dif_max_real"].max())
    resultado["so_meu_ou_salvo"] = int(tabela_comp["so_meu"].sum() + tabela_comp["so_salvo"].sum())
    resultado["mae_medio_meu"] = {str(q): float(v) for q, v in maes_meu.items()}
    (PASTA_DA_CERTIFICACAO / "verif_2_completo.json").write_text(json.dumps(resultado, indent=2))
    print(resultado)
