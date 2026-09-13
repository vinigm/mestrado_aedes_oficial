"""

Compara a rodada corrigida contra a de 30/08, seguindo PRE_DECLARACAO.md.

Pareado por (algoritmo, perda, conjunto, h, data_alvo): os pontos de teste sao
os mesmos nas duas rodadas, entao toda diferenca vem do corte de treino.

Uso:  python comparar.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parent
ORIGINAL = PASTA.parent / "2026-08-30_grid_completo" / "saidas" / "grid_previsoes_parciais.csv"
LIMITE_PICO = 100
FIM_DA_CALIBRACAO = pd.Timestamp("2023-12-31")
CHAVES = ["algoritmo", "perda", "conjunto"]


def carregar_corrigido() -> pd.DataFrame:
    partes = [pd.read_csv(PASTA / "saidas" / nome) for nome in
              ("corrigido_previsoes_parciais.csv", "corrigido_previsoes_padrao.csv")]
    return pd.concat(partes, ignore_index=True)


def metricas(grupo: pd.DataFrame) -> pd.Series:
    real, pred = grupo["real"].to_numpy(), grupo["pred"].to_numpy()
    e_pico = real > LIMITE_PICO
    return pd.Series({
        "n": len(grupo),
        "MAE": np.abs(pred - real).mean(),
        "R2": 1 - ((real - pred) ** 2).sum() / ((real - real.mean()) ** 2).sum(),
        "vies_pico": (pred[e_pico] - real[e_pico]).mean() if e_pico.any() else np.nan,
        "captura_pico": pred[e_pico].mean() / real[e_pico].mean() if e_pico.any() else np.nan,
    })


def resumir(previsoes: pd.DataFrame) -> pd.DataFrame:
    dados = previsoes.copy()
    dados["data_alvo"] = pd.to_datetime(dados["data_alvo"])
    dados["periodo"] = np.where(dados["data_alvo"] > FIM_DA_CALIBRACAO, "avaliacao", "calibracao")
    return (dados.groupby(CHAVES + ["h", "periodo"])
            .apply(metricas, include_groups=False).reset_index())


novo = carregar_corrigido()
original = pd.read_csv(ORIGINAL)
configuracoes = novo[CHAVES].drop_duplicates()
original = original.merge(configuracoes, on=CHAVES)

for tabela in (novo, original):
    tabela["data_alvo"] = pd.to_datetime(tabela["data_alvo"])

pareado = original.merge(novo, on=CHAVES + ["h", "data_alvo"], suffixes=("_org", "_novo"))
print(f"pontos pareados: {len(pareado):,} | original: {len(original):,} | novo: {len(novo):,}")
print(f"perda no pareamento: {len(original) - len(pareado)} pontos\n")

print("=" * 78)
print("CONTROLE (§4 da pre-declaracao): h=1 tem de ser IDENTICO")
print("=" * 78)
h1 = pareado[pareado.h == 1]
dif_h1 = (h1.pred_org - h1.pred_novo).abs()
print(f"  celulas em h=1: {h1.groupby(CHAVES).ngroups} | pontos: {len(h1)}")
print(f"  diferenca maxima de previsao: {dif_h1.max():.10f}")
print(f"  {'CONTROLE PASSOU' if dif_h1.max() < 0.01 else 'CONTROLE FALHOU - ABORTAR LEITURA'}\n")

res_org = resumir(original).rename(columns={"MAE": "MAE_org", "R2": "R2_org",
                                            "vies_pico": "vies_org", "captura_pico": "cap_org"})
res_novo = resumir(novo).rename(columns={"MAE": "MAE_novo", "R2": "R2_novo",
                                         "vies_pico": "vies_novo", "captura_pico": "cap_novo"})
comp = res_org.merge(res_novo, on=CHAVES + ["h", "periodo"], suffixes=("", "_n"))
comp["MAE_var_%"] = (comp.MAE_novo / comp.MAE_org - 1) * 100
comp["R2_var"] = comp.R2_novo - comp.R2_org
comp["cap_var_pp"] = (comp.cap_novo - comp.cap_org) * 100
comp.to_csv(PASTA / "saidas" / "comparacao_antes_depois.csv", index=False)

print("=" * 78)
print("H1 e H2 — A CONFIGURACAO DE REFERENCIA (HistGB quantil 0,80), AVALIACAO 2024+")
print("=" * 78)
ref = comp[(comp.algoritmo == "hist_gradient_boosting") & (comp.perda == "quantil_0.80")
           & (comp.periodo == "avaliacao")].sort_values(["conjunto", "h"])
pd.set_option("display.width", 200)
print(ref[["conjunto", "h", "n", "MAE_org", "MAE_novo", "MAE_var_%", "R2_org", "R2_novo",
           "cap_org", "cap_novo", "cap_var_pp"]].round(3).to_string(index=False))

print("\n" + "=" * 78)
print("H4 — O GANHO DO VETOR (M0 menos M1, em MAE de avaliacao)")
print("=" * 78)
pivo = ref.pivot_table(index="h", columns="conjunto", values=["MAE_org", "MAE_novo"])
ganho = pd.DataFrame({
    "ganho_original": pivo[("MAE_org", "M0_sem_vetor")] - pivo[("MAE_org", "M1_com_vetor")],
    "ganho_corrigido": pivo[("MAE_novo", "M0_sem_vetor")] - pivo[("MAE_novo", "M1_com_vetor")],
})
ganho["sobrou_%"] = ganho.ganho_corrigido / ganho.ganho_original * 100
print(ganho.round(2).to_string())
g12 = ganho.loc[12]
encolhimento = (1 - g12.ganho_corrigido / g12.ganho_original) * 100
print(f"\n  h=12: ganho caiu de {g12.ganho_original:.1f} para {g12.ganho_corrigido:.1f} de MAE "
      f"({encolhimento:.0f}% de encolhimento)")
if encolhimento >= 70:
    print("  -> CRITERIO §5: abaixo de 30% do ganho -> alegacao do vetor em h=12 REFUTADA")
elif encolhimento >= 30:
    print("  -> CRITERIO §5: entre 30% e 70% -> teste focado precisa ser REFEITO")
else:
    print("  -> CRITERIO §5: sobrou >= 70% -> alegacao SOBREVIVE como exploratoria")
print(f"  -> EMENDA E1.5: encolhimento {encolhimento:.0f}% "
      f"{'>= 30% -> Rodada 1 e teste decisivo ENTRAM NA FILA' if encolhimento >= 30 else '< 30% -> dispensas da Rodada 1 e teste decisivo FICAM DE PE'}")

print("\n" + "=" * 78)
print("H3 — O RANKING SOBREVIVE? (criterio da EMENDA E1.2)")
print("=" * 78)
rank_org = (res_org[res_org.periodo == "calibracao"].groupby(CHAVES).MAE_org.mean()
            .sort_values().reset_index())
rank_org["pos_org"] = range(1, len(rank_org) + 1)
rank_novo = (res_novo[res_novo.periodo == "calibracao"].groupby(CHAVES).MAE_novo.mean()
             .sort_values().reset_index())
rank_novo["pos_novo"] = range(1, len(rank_novo) + 1)
rk = rank_org.merge(rank_novo, on=CHAVES)
rk["desloc"] = (rk.pos_org - rk.pos_novo).abs()
rk["rotulo"] = rk.algoritmo.str.replace("_", " ") + " | " + rk.perda + " | " + rk.conjunto.str[:2]
print(rk[["pos_org", "pos_novo", "desloc", "rotulo", "MAE_org", "MAE_novo"]].round(2).to_string(index=False))
spearman = rk.pos_org.corr(rk.pos_novo, method="spearman")
topo_mantido = rk.loc[rk.pos_org == 1, "pos_novo"].iloc[0] == 1
print(f"\n  Spearman: {spearman:.3f} | 1o colocado mantido: {topo_mantido} | "
      f"deslocamento maximo: {rk.desloc.max()} posicoes")

print("\n  -- par 1 x 20 (mesma algoritmo/conjunto, so a perda muda) --")
def mae_cal(perda):
    linha = rank_novo[(rank_novo.algoritmo == "hist_gradient_boosting")
                      & (rank_novo.perda == perda) & (rank_novo.conjunto == "M1_com_vetor")]
    org = rank_org[(rank_org.algoritmo == "hist_gradient_boosting")
                   & (rank_org.perda == perda) & (rank_org.conjunto == "M1_com_vetor")]
    return org.MAE_org.iloc[0], linha.MAE_novo.iloc[0]
q_org, q_novo = mae_cal("quantil_0.80")
p_org, p_novo = mae_cal("padrao")
vant_org = (p_org / q_org - 1) * 100
vant_novo = (p_novo / q_novo - 1) * 100
print(f"  vantagem do quantilico sobre o padrao: {vant_org:.1f} pp (antes) -> {vant_novo:.1f} pp (depois)")

criterios = {
    "1o colocado mantido": topo_mantido,
    "ninguem se move mais de 2 posicoes": rk.desloc.max() <= 2,
    "vantagem do par 1x20 >= 10 pp": vant_novo >= 10,
}
for nome, ok in criterios.items():
    print(f"    [{'OK' if ok else 'FALHOU'}] {nome}")
print(f"\n  -> {'RANKING COMPATIVEL COM ROBUSTO: o grid de 120 NAO precisa ser refeito' if all(criterios.values()) else 'CRITERIO FALHOU: o grid de 120 PRECISA ser refeito'}")
print(f"\nsaida detalhada: saidas/comparacao_antes_depois.csv")
