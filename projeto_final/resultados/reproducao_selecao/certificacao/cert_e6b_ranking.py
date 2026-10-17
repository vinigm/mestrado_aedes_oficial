import pandas as pd, numpy as np
RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
OLD = f"{RAIZ}/analises/2026-09-13_correcao_vazamento_treino/saidas"
R = f"{RAIZ}/projeto_final/resultados/reproducao_selecao/E6b_grade30"
old = pd.concat([pd.read_csv(f"{OLD}/corrigido_previsoes_{k}.csv", parse_dates=["data_alvo"], float_precision="round_trip") for k in ("parciais","padrao","restante")], ignore_index=True)
new = pd.read_csv(f"{R}/previsoes.csv", parse_dates=["data_origem","data_alvo"], float_precision="round_trip")
print("old", len(old), "new", len(new), "configs old", old.groupby(["algoritmo","perda","conjunto"]).ngroups, "new", new.groupby(["algoritmo","perda","conjunto"]).ngroups)
print("old dup keys:", old.duplicated(["algoritmo","perda","conjunto","h","data_alvo"]).sum(), "new dup:", new.duplicated(["algoritmo","perda","conjunto","h","data_alvo"]).sum())
k = ["algoritmo","perda","conjunto","h","data_alvo"]
m = old.merge(new, on=k, how="outer", indicator=True, suffixes=("_o","_n"))
print(m["_merge"].value_counts().to_dict())
b = m[m["_merge"]=="both"]
print("dif max pred:", (b["pred"]-b["previsto"]).abs().max(), " dif max real:", (b["real_o"]-b["real_n"]).abs().max())
print("dif max por algoritmo:", (b["pred"]-b["previsto"]).abs().groupby(b["algoritmo"]).max().to_dict())
# truncamento: previsto >=0
print("min previsto new:", new["previsto"].min(), " min pred old:", old["pred"].min())
# origem = alvo - h semanas?
print("origem==alvo-h*7:", ((new["data_alvo"]-new["data_origem"]).dt.days==new["h"]*7).all())
# ranking a partir do CSV antigo (independente)
def ranking(df, pcol):
    df = df.copy()
    df["per"] = np.where(df["data_alvo"] > pd.Timestamp("2023-12-31"), "aval", "cal")
    df["ae"] = (df[pcol]-df["real"]).abs()
    cal = df[df.per=="cal"].groupby(["algoritmo","perda","conjunto","h"])["ae"].mean().groupby(["algoritmo","perda","conjunto"]).agg(["mean","count"])
    av = df[df.per=="aval"].groupby(["algoritmo","perda","conjunto","h"])["ae"].mean().groupby(["algoritmo","perda","conjunto"]).mean()
    out = cal.rename(columns={"mean":"mae_cal"}).join(av.rename("mae_aval")).reset_index().sort_values("mae_cal", kind="mergesort").reset_index(drop=True)
    out["pos"] = out.index+1
    return out
ro = ranking(old, "pred"); rn = ranking(new, "previsto")
ex = pd.read_csv(f"{R}/ranking.csv")
chave = ["algoritmo","perda","conjunto"]
c = ro.merge(rn, on=chave, suffixes=("_old","_new")).merge(ex, on=chave)
print("n configs", len(c), "horizontes cal por config (count):", set(ro["count"]))
print("dif mae_cal old-vs-new:", (c.mae_cal_old-c.mae_cal_new).abs().max(), " vs executor ranking.csv:", (c.mae_cal_new-c.mae_cal).abs().max())
print("dif mae_aval old-vs-new:", (c.mae_aval_old-c.mae_aval_new).abs().max(), " vs executor:", (c.mae_aval_new-c.mae_aval).abs().max())
print("posicao igual old/new/executor:", ((c.pos_old==c.pos_new)&(c.pos_new==c.pos)).all())
print(ro[["pos","algoritmo","perda","conjunto","mae_cal","mae_aval"]].head(5).to_string())
print(ro.set_index(chave).loc[[("hist_gradient_boosting","padrao","M1_com_vetor"),("lightgbm","padrao","M1_com_vetor"),("lightgbm","quantil_0.90","M1_com_vetor")],["pos","mae_cal"]])
print(ro.tail(3)[["pos","algoritmo","perda","conjunto","mae_cal"]])
# ha empates?
print("empates mae_cal:", ro["mae_cal"].duplicated().sum())
# janela de calibracao/avaliacao
print("alvo min/max:", new.data_alvo.min(), new.data_alvo.max())
ro.to_csv("cert_e6b_ranking_recalculado.csv", index=False)
