"""Compara recontagem independente x contador, e confere tabela_final.csv. So contagens."""
import pathlib, pandas as pd
R = pathlib.Path(__file__).resolve().parent
N = R.parent
PF = N.parents[1]
a = pd.read_csv(N / "contagens_por_arquivo.csv"); b = pd.read_csv(R / "recontagem_por_arquivo.csv")
m = a.merge(b, on="arquivo")
for x, y in [("total_fichas", "total"), ("confirmadas", "conf"), ("inconclusivas", "incl"), ("em_aberto", "aberto"), ("outros_x", "outros_y")]:
    xx = x if x in m else "outros_x"
print("DIF por arquivo (colunas total,conf,incl,aberto,outros):")
d = pd.DataFrame({"arquivo": m.arquivo, "total": m.total_fichas - m.total, "conf": m.confirmadas - m.conf,
                  "incl": m.inconclusivas - m.incl, "aberto": m.em_aberto - m.aberto, "outros": m.outros_x - m.outros_y})
print(d.to_string(index=False)); print("soma abs:", d.drop(columns="arquivo").abs().sum().sum())
a2 = pd.read_csv(N / "contagens_por_ano_de_sintomas.csv"); b2 = pd.read_csv(R / "recontagem_por_ano_set.csv")
m2 = a2.merge(b2, left_on="ano_dos_sintomas", right_on="ano", how="outer")
d2 = pd.DataFrame({"ano": m2.ano_dos_sintomas, "conf": m2.confirmadas - m2.conf, "incl": m2.inconclusivas - m2.incl,
                   "aberto": m2.em_aberto - m2.aberto, "outros_": m2.outros_x - m2.outros_y, "total": m2.total_fichas - m2.total})
print("DIF por ano:"); print(d2.to_string(index=False)); print("soma abs:", d2.drop(columns="ano").abs().sum().sum())
print("linhas ano:", len(a2), len(b2))
# tabela_final x semanas confirmadas
t = pd.read_csv(PF / "dados" / "tabela_final.csv")
t["SE"] = t["SE"].astype(str)
print("tabela: soma casos", t.casos_confirmados.sum(), "linhas com caso nao nulo", t.casos_confirmados.notna().sum())
tt = t.groupby("ano").casos_confirmados.sum(min_count=1)
print("tabela por ano (coluna ano):"); print(tt.dropna().to_string())
for rot in ("jun", "set"):
    s = pd.read_csv(R / f"recontagem_semanas_confirmadas_{rot}.csv", dtype={"SEM_PRI": str})
    mm = t[["SE", "data_inicio_semana_epidemi", "casos_confirmados"]].merge(s, left_on="SE", right_on="SEM_PRI", how="outer")
    mm["confirmadas"] = mm.confirmadas.fillna(0)
    ser = mm[mm.casos_confirmados.notna()]
    dif = ser[ser.casos_confirmados != ser.confirmadas]
    print(f"--- versao {rot}: soma recontada {int(s.confirmadas.sum())}; semanas da tabela com caso != recontagem: {len(dif)}")
    if len(dif): print(dif.to_string(index=False))
    fora = mm[mm.casos_confirmados.isna() & (mm.confirmadas > 0)]
    print(f"semanas recontadas com caso mas sem valor na tabela: {len(fora)}; soma {int(fora.confirmadas.sum())}")
    if len(fora): print(fora[["SE", "confirmadas"]].to_string(index=False))
    print("2026 por semana (tabela vs recontagem):")
    print(mm[mm.SE.astype(str).str.startswith("2026") & ((mm.confirmadas > 0) | (mm.casos_confirmados.fillna(0) > 0))][["SE", "casos_confirmados", "confirmadas"]].to_string(index=False))
print("ultima SE com valor na tabela:", t[t.casos_confirmados.notna()].SE.iloc[-1], t[t.casos_confirmados.notna()].data_inicio_semana_epidemi.iloc[-1])
print("tabela 2026: ultima linha SE", t.SE.iloc[-1], "casos NaN em 2026 apos ultima:", t[(t.ano == 2026)].casos_confirmados.isna().sum(), "de", (t.ano == 2026).sum())
