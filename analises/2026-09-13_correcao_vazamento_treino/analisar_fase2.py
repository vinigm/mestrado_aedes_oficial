"""

Le os resultados da FASE 2 e aplica os criterios de PRE_DECLARACAO_FASE2.md.

Escrito ANTES de a rodada terminar, de proposito: o criterio nao pode ser
escolhido depois de ver o numero.

Uso:  python analisar_fase2.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
SAIDAS = PASTA / "saidas"
ANTES = SAIDAS / "resultados_antes_da_correcao"
GRID_ORIGINAL = PASTA.parent / "2026-08-30_grid_completo" / "saidas"
R29 = PASTA.parent / "2026-08-29_rodadas_notificados_zonas" / "saidas"

LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
CHAVES = ["algoritmo", "perda", "conjunto"]
pd.set_option("display.width", 220)


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def carregar_corrigido() -> pd.DataFrame:
    """Junta as previsoes das tres bateladas do grid corrigido."""
    nomes = ("corrigido_previsoes_parciais.csv", "corrigido_previsoes_padrao.csv",
             "corrigido_previsoes_restante.csv")
    partes = [pd.read_csv(SAIDAS / nome) for nome in nomes if (SAIDAS / nome).exists()]
    dados = pd.concat(partes, ignore_index=True)
    dados["data_alvo"] = pd.to_datetime(dados["data_alvo"])
    return dados


def metricas(grupo: pd.DataFrame) -> pd.Series:
    real, pred = grupo["real"].to_numpy(), grupo["pred"].to_numpy()
    e_pico = real > LIMITE_PICO
    return pd.Series({
        "n": len(grupo),
        "MAE": np.abs(pred - real).mean(),
        "R2": 1 - ((real - pred) ** 2).sum() / ((real - real.mean()) ** 2).sum(),
        "captura_pico": pred[e_pico].mean() / real[e_pico].mean() if e_pico.any() else np.nan,
    })


def resumir(previsoes: pd.DataFrame) -> pd.DataFrame:
    dados = previsoes.copy()
    dados["periodo"] = np.where(dados["data_alvo"] > FIM_DA_CALIBRACAO, "avaliacao", "calibracao")
    return dados.groupby(CHAVES + ["h", "periodo"]).apply(metricas, include_groups=False).reset_index()


# ---------------------------------------------------------------- CONTROLE
def checar_controle(novo: pd.DataFrame) -> bool:
    """h=1 nao tem linha contaminada: tem de sair identico ao original."""
    titulo("CONTROLE (§4): h=1 tem de reproduzir o original")
    original = pd.read_csv(GRID_ORIGINAL / "grid_previsoes_parciais.csv")
    original["data_alvo"] = pd.to_datetime(original["data_alvo"])
    par = original.merge(novo, on=CHAVES + ["h", "data_alvo"], suffixes=("_org", "_novo"))
    h1 = par[par.h == 1]
    maior_diferenca = (h1.pred_org - h1.pred_novo).abs().max()
    print(f"  celulas de h=1 comparadas: {h1.groupby(CHAVES).ngroups} | pontos: {len(h1)}")
    print(f"  diferenca maxima: {maior_diferenca:.10f}")
    passou = maior_diferenca < 0.01
    print(f"  {'PASSOU' if passou else '*** FALHOU - NAO INTERPRETAR NADA DESTA FASE ***'}")
    return passou


# ------------------------------------------------------------------- GRID
def analisar_grid(novo: pd.DataFrame) -> None:
    titulo("BLOCO A — o ranking das 30 configuracoes, corrigido")
    resumo = resumir(novo)
    calibracao = resumo[resumo.periodo == "calibracao"]
    ranking = calibracao.groupby(CHAVES).MAE.mean().sort_values().reset_index()
    ranking["pos_nova"] = range(1, len(ranking) + 1)

    antigo = pd.read_csv(GRID_ORIGINAL / "grid_ranking_completo.csv")[CHAVES + ["pos", "MAE_cal"]]
    comparado = ranking.merge(antigo.rename(columns={"pos": "pos_antiga"}), on=CHAVES)
    comparado["desloc"] = comparado.pos_antiga - comparado.pos_nova
    comparado["piora_%"] = (comparado.MAE / comparado.MAE_cal - 1) * 100

    print(f"  configuracoes medidas: {len(comparado)} de 30")
    print(comparado[["pos_nova", "pos_antiga", "desloc", "algoritmo", "perda", "conjunto",
                     "MAE_cal", "MAE", "piora_%"]].round(2).to_string(index=False))

    vencedora = comparado.iloc[0]
    print(f"\n  VENCEDORA CORRIGIDA: {vencedora.algoritmo} | {vencedora.perda} | "
          f"{vencedora.conjunto}  (era a {int(vencedora.pos_antiga)}a)")
    if len(comparado) == 30:
        print(f"  Spearman entre as ordens: "
              f"{comparado.pos_antiga.corr(comparado.pos_nova, method='spearman'):.3f}")

    print("\n  -- a perda importa mais que o algoritmo? --")
    for conjunto in ("M1_com_vetor", "M0_sem_vetor"):
        for algoritmo in comparado.algoritmo.unique():
            fatia = comparado[(comparado.conjunto == conjunto) & (comparado.algoritmo == algoritmo)]
            padrao = fatia[fatia.perda == "padrao"]
            quantis = fatia[fatia.perda != "padrao"]
            if padrao.empty or quantis.empty:
                continue
            melhor = quantis.MAE.min()
            print(f"    {algoritmo:24s} {conjunto}: melhor quantil {melhor:.2f} x "
                  f"padrao {padrao.MAE.iloc[0]:.2f}  -> vantagem "
                  f"{(padrao.MAE.iloc[0] / melhor - 1) * 100:5.1f} pp  (antes: "
                  f"{(padrao.MAE_cal.iloc[0] / quantis.MAE_cal.min() - 1) * 100:5.1f} pp)")

    print("\n  -- com vetor x sem vetor, pareado por algoritmo e perda --")
    largo = comparado.pivot_table(index=["algoritmo", "perda"], columns="conjunto",
                                  values=["MAE", "MAE_cal"])
    if ("MAE", "M0_sem_vetor") in largo.columns and ("MAE", "M1_com_vetor") in largo.columns:
        vence_antes = (largo[("MAE_cal", "M1_com_vetor")] < largo[("MAE_cal", "M0_sem_vetor")]).sum()
        vence_depois = (largo[("MAE", "M1_com_vetor")] < largo[("MAE", "M0_sem_vetor")]).sum()
        print(f"    o vetor vencia em {vence_antes} de {len(largo)} pares; agora vence em {vence_depois}")


# --------------------------------------------------------------- RODADAS
def analisar_rodada_4() -> None:
    titulo("BLOCO C — janela de treino (criterio: 2012 vence em 3 de 4?)")
    novo, antigo = SAIDAS / "rodada_4_ablacao_resumo.csv", R29 / "rodada_4_ablacao_resumo.csv"
    if not novo.exists():
        print("  ainda nao rodou"); return
    for rotulo, caminho in (("ANTES", antigo), ("DEPOIS", novo)):
        tabela = pd.read_csv(caminho).pivot_table(index="h", columns="regime", values="MAE")
        vitorias = (tabela.idxmin(axis=1) == "expansivel_2012").sum()
        print(f"  {rotulo}: expansivel_2012 vence em {vitorias} de {len(tabela)} horizontes")
        print(tabela.round(2).to_string())
    print("  -> criterio: 3 de 4 mantem citavel; 2 ou menos vira indeterminado")


def analisar_rodada_3() -> None:
    titulo("BLOCO D — ranking espacial (criterio: a celula que o modelo vencia sobrevive?)")
    novo, antigo = SAIDAS / "rodada_3_ranking_resumo.csv", R29 / "rodada_3_ranking_resumo.csv"
    if not novo.exists():
        print("  ainda nao rodou"); return
    for rotulo, caminho in (("ANTES", antigo), ("DEPOIS", novo)):
        tabela = pd.read_csv(caminho)
        tabela["modelo_vence"] = tabela.spearman_modelo_mediana > tabela.spearman_persistencia_mediana
        print(f"  {rotulo}: modelo vence a persistencia em {int(tabela.modelo_vence.sum())} de {len(tabela)}")
        print(tabela[["k", "h", "spearman_modelo_mediana", "spearman_persistencia_mediana",
                      "spearman_climatologia_mediana", "modelo_vence"]].round(3).to_string(index=False))


def analisar_surto() -> None:
    titulo("BLOCO E — alarme de surto (criterio: os negativos se mantem?)")
    oficiais = PASTA.parents[1] / "modelagem_aedes" / "dados" / "saidas" / "resultados"
    for nome in ("deteccao_surto_mcnemar.csv", "surto_notificados_mcnemar.csv"):
        print(f"\n  -- {nome} --")
        for rotulo, pasta in (("ANTES", ANTES), ("DEPOIS", oficiais)):
            caminho = pasta / nome
            if not caminho.exists():
                print(f"    {rotulo}: ausente"); continue
            tabela = pd.read_csv(caminho)
            coluna_p = "p_holm" if "p_holm" in tabela.columns else "p"
            favoravel = (tabela.vetor_certo_clima_errado > tabela.clima_certo_vetor_errado).sum()
            print(f"    {rotulo}: vetor favorecido em {favoravel} de {len(tabela)} | "
                  f"menor {coluna_p} = {tabela[coluna_p].min():.4f} | "
                  f"sobrevive a Holm: {(tabela[coluna_p] < 0.05).sum()}")


def main() -> None:
    novo = carregar_corrigido()
    celulas = novo.groupby(CHAVES + ["h"]).ngroups
    print(f"celulas corrigidas disponiveis: {celulas} (esperado 120 no fim)")
    if checar_controle(novo):
        analisar_grid(novo)
    analisar_rodada_4()
    analisar_rodada_3()
    analisar_surto()


if __name__ == "__main__":
    main()
