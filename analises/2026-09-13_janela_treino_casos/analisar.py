"""

Aplica os criterios de PRE_DECLARACAO.md aos resultados da ablacao de janela.

Escrito antes de a rodada terminar, de proposito.

Uso:  python analisar.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
LIMITE_SURTO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
pd.set_option("display.width", 200)


def metricas(grupo: pd.DataFrame) -> pd.Series:
    real, pred = grupo["real"].to_numpy(), grupo["pred"].to_numpy()
    e_surto, alarme = real > LIMITE_SURTO, pred > LIMITE_SURTO
    return pd.Series({
        "n": len(grupo),
        "MAE": np.abs(pred - real).mean(),
        "R2": 1 - ((real - pred) ** 2).sum() / ((real - real.mean()) ** 2).sum(),
        "sensibilidade": (e_surto & alarme).sum() / e_surto.sum() if e_surto.any() else np.nan,
        "n_treino_mediano": grupo["n_treino"].median(),
    })


dados = pd.read_csv(PASTA / "saidas" / "janelas_previsoes.csv", parse_dates=["data_alvo"])
aval = dados[dados["data_alvo"] > FIM_DA_CALIBRACAO]

print("=" * 84)
print("CONTROLE (§4): as semanas avaliadas sao as MESMAS nos 4 regimes?")
print("=" * 84)
for horizonte in sorted(dados.h.unique()):
    conjuntos = {r: set(g.data_alvo) for r, g in dados[dados.h == horizonte].groupby("regime")}
    tamanhos = {len(v) for v in conjuntos.values()}
    iguais = len(set.union(*conjuntos.values())) == len(set.intersection(*conjuntos.values()))
    print(f"  h={horizonte:2d}: {tamanhos} semanas por regime | identicas: {iguais}")

print("\n" + "=" * 84)
print("CONTROLE (§4): expansivel_total reproduz o grid de 13/09 nas semanas comuns?")
print("=" * 84)
GRID = PASTA.parent / "2026-09-13_correcao_vazamento_treino" / "saidas"
nomes = ("corrigido_previsoes_parciais.csv", "corrigido_previsoes_padrao.csv",
         "corrigido_previsoes_restante.csv")
grid = pd.concat([pd.read_csv(GRID / n) for n in nomes], ignore_index=True)
grid["data_alvo"] = pd.to_datetime(grid["data_alvo"])
grid = grid[(grid.algoritmo == "hist_gradient_boosting") & (grid.perda == "quantil_0.85")
            & (grid.conjunto == "M1_com_vetor")][["h", "data_alvo", "real", "pred"]]
meu = dados[dados.regime == "expansivel_total"][["h", "data_alvo", "real", "pred"]]
par = grid.merge(meu, on=["h", "data_alvo", "real"], suffixes=("_grid", "_meu"))
maior = (par.pred_grid - par.pred_meu).abs().max()
print(f"  semanas pareadas com o grid: {len(par)}")
print(f"  diferenca maxima de previsao: {maior:.10f}")
if maior < 0.01:
    print("  PASSOU — o expansivel_total e mesmo o protocolo do grid, so com inicio mais tarde.")
else:
    print("  *** FALHOU — ha diferenca de implementacao. NAO INTERPRETAR O RESTO. ***")

print("\n" + "=" * 84)
print(f"RESULTADO — avaliacao (data_alvo > {FIM_DA_CALIBRACAO.date()})")
print("=" * 84)
resumo = aval.groupby(["h", "regime"]).apply(metricas, include_groups=False).reset_index()
print(resumo.round(3).to_string(index=False))

print("\n" + "=" * 84)
print("CRITERIO (§5): quem vence por horizonte, pelo menor MAE")
print("=" * 84)
largo = resumo.pivot(index="h", columns="regime", values="MAE")
print(largo.round(2).to_string())
vitorias = largo.idxmin(axis=1).value_counts()
print("\n  vitorias por regime:")
for regime, n in vitorias.items():
    print(f"    {regime:20s} {n} de {len(largo)} horizontes")

campeao = vitorias.index[0]
n_vitorias = int(vitorias.iloc[0])
print(f"\n  MAE medio geral: ")
for regime, valor in resumo.groupby("regime").MAE.mean().sort_values().items():
    print(f"    {regime:20s} {valor:.2f}")

print("\n  -> VEREDITO PELO CRITERIO PRE-DECLARADO:")
if campeao == "expansivel_total" and n_vitorias >= 3:
    print("     expansivel_total vence em 3+ horizontes -> a pratica atual esta CERTA,")
    print("     o assunto FECHA, e passa a valer para os dois alvos.")
elif n_vitorias >= 3:
    print(f"     {campeao} vence em {n_vitorias} horizontes -> ACHADO RELEVANTE: a epidemiologia")
    print("     mudou o bastante para historia antiga atrapalhar. Exige rodada de confirmacao")
    print("     antes de virar decisao.")
else:
    print(f"     dividido ({dict(vitorias)}) -> INDETERMINADO. A pratica atual permanece")
    print("     por inercia, e isso fica declarado como tal.")

resumo.to_csv(PASTA / "saidas" / "janelas_resumo.csv", index=False)
print(f"\nsalvo em saidas/janelas_resumo.csv")
