"""

O teste decisivo do vetor: 15 pares M0 x M1, pareados por data_alvo.

Cada par e o MESMO algoritmo com a MESMA perda, mudando so a presenca das
colunas do vetor. Diebold-Mariano com correcao HLN sobre os erros absolutos
pareados, e Holm sobre a familia inteira de 60 comparacoes (15 pares x 4
horizontes), como manda a PRE_DECLARACAO_FASE2.

Uso:  python vetor_pareado_final.py

"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA.parents[1] / "modelagem_aedes"))

from avaliacao.correcao_multipla import corrigir_holm
from avaliacao.diebold_mariano import teste_diebold_mariano

FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")


def carregar(pasta_saidas: Path, nomes: tuple[str, ...]) -> pd.DataFrame:
    partes = [pd.read_csv(pasta_saidas / n) for n in nomes if (pasta_saidas / n).exists()]
    dados = pd.concat(partes, ignore_index=True)
    dados["data_alvo"] = pd.to_datetime(dados["data_alvo"])
    return dados


def comparar(previsoes: pd.DataFrame, rotulo: str) -> pd.DataFrame:
    """Pareia M0 e M1 por data_alvo e roda Diebold-Mariano em cada par."""
    aval = previsoes[previsoes["data_alvo"] > FIM_DA_CALIBRACAO]
    linhas = []
    for (algoritmo, perda, horizonte), grupo in aval.groupby(["algoritmo", "perda", "h"]):
        m0 = grupo[grupo.conjunto == "M0_sem_vetor"][["data_alvo", "real", "pred"]]
        m1 = grupo[grupo.conjunto == "M1_com_vetor"][["data_alvo", "real", "pred"]]
        if m0.empty or m1.empty:
            continue
        par = m0.merge(m1, on=["data_alvo", "real"], suffixes=("_m0", "_m1"))
        erro_m0 = (par.real - par.pred_m0).abs().to_numpy()
        erro_m1 = (par.real - par.pred_m1).abs().to_numpy()
        # o DM do projeto recebe os erros com sinal; ganho > 0 = M1 erra menos
        resultado = teste_diebold_mariano(
            (par.real - par.pred_m0).to_numpy(),
            (par.real - par.pred_m1).to_numpy(),
            horizonte, tipo_erro="absoluto",
        )
        linhas.append({
            "algoritmo": algoritmo, "perda": perda, "h": horizonte, "n": len(par),
            "MAE_M0": erro_m0.mean(), "MAE_M1": erro_m1.mean(),
            "ganho": erro_m0.mean() - erro_m1.mean(),
            "p_bruto": resultado.valor_p,
        })
    tabela = pd.DataFrame(linhas)
    tabela["p_holm"] = corrigir_holm(tabela.p_bruto.to_numpy())
    tabela["origem"] = rotulo
    return tabela


novo = carregar(PASTA / "saidas", ("corrigido_previsoes_parciais.csv",
                                   "corrigido_previsoes_padrao.csv",
                                   "corrigido_previsoes_restante.csv"))
antigo = carregar(PASTA.parent / "2026-08-30_grid_completo" / "saidas",
                  ("grid_previsoes_parciais.csv",))

depois, antes = comparar(novo, "corrigido"), comparar(antigo, "original")
pd.set_option("display.width", 200)

for rotulo, tabela in (("ORIGINAL (com vazamento)", antes), ("CORRIGIDO", depois)):
    print(f"\n{'=' * 78}\n{rotulo}: {len(tabela)} comparacoes pareadas ({tabela.n.iloc[0]} semanas cada)\n{'=' * 78}")
    print(f"  o vetor erra menos em {int((tabela.ganho > 0).sum())} de {len(tabela)}")
    print(f"  menor p bruto: {tabela.p_bruto.min():.4f} | menor p Holm: {tabela.p_holm.min():.4f} | "
          f"sobrevivem a Holm: {int((tabela.p_holm < 0.05).sum())}")
    print("\n  por horizonte:")
    print(tabela.groupby("h").agg(vence=("ganho", lambda s: f"{int((s > 0).sum())}/{len(s)}"),
                                  ganho_medio=("ganho", "mean"),
                                  menor_p=("p_bruto", "min")).round(3).to_string())

print(f"\n{'=' * 78}\nOS 15 PARES EM h=12, CORRIGIDO (onde o efeito era alegado)\n{'=' * 78}")
h12 = depois[depois.h == 12].sort_values("ganho", ascending=False)
print(h12[["algoritmo", "perda", "n", "MAE_M0", "MAE_M1", "ganho", "p_bruto", "p_holm"]].round(3).to_string(index=False))

comp = antes.merge(depois, on=["algoritmo", "perda", "h"], suffixes=("_antes", "_depois"))
print(f"\n  ganho medio em h=12: {comp[comp.h==12].ganho_antes.mean():.2f} (antes) -> "
      f"{comp[comp.h==12].ganho_depois.mean():.2f} (depois)")
depois.to_csv(PASTA / "saidas" / "vetor_pareado_60_comparacoes.csv", index=False)
print(f"\n  salvo em saidas/vetor_pareado_60_comparacoes.csv")
