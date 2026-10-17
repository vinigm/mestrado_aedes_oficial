import pandas as pd, numpy as np, hashlib, csv, pathlib, json
PF = pathlib.Path(".").resolve()
P = pd.read_csv(PF/"resultados/referencia/previsoes.csv", parse_dates=["data_origem","data_alvo"])
ini, fim = pd.Timestamp("2024-01-07"), pd.Timestamp("2026-02-01")
out = {"bracos": sorted(P.braco.unique().tolist())}
for br, nome in (("referencia","folha5"),("HistGB_folha20_M1","folha20")):
    d = P[P.braco==br]
    out[f"{nome}_n_por_h_total"] = {int(h): int(n) for h,n in d.groupby("h").size().items() if h in (1,12)}
    j = d[(d.data_alvo>=ini)&(d.data_alvo<=fim)]
    out[f"{nome}_n_janela_por_h"] = sorted(set(j.groupby("h").size()))
    out[f"{nome}_mae_janela_h1_4_8_12"] = [round(float((j[j.h==h].real-j[j.h==h].previsto).abs().mean()),3) for h in (1,4,8,12)]
    if nome=="folha5":
        c = d[d.data_alvo<=pd.Timestamp("2023-12-31")]
        out["folha5_n_calib_h1_4_8_12"] = [int((c.h==h).sum()) for h in (1,4,8,12)]
        out["folha5_mae_calib_h1_4_8_12"] = [round(float((c[c.h==h].real-c[c.h==h].previsto).abs().mean()),3) for h in (1,4,8,12)]
M = pd.read_csv(PF/"resultados/referencia/metricas.csv")
out["metricas_cols"] = list(M.columns)
out["metricas_n_linhas"] = len(M)
# gabarito manifest
gd = PF/"testes/referencia_antiga"
man = {r["arquivo"]:(int(r["bytes"]),r["sha256"]) for r in csv.DictReader(open(gd/"MANIFESTO.csv",newline=""))}
ruins=[a for a,(b,h) in man.items() if not (gd/a).exists() or (gd/a).stat().st_size!=b or hashlib.sha256((gd/a).read_bytes()).hexdigest()!=h]
out["gabarito_manifesto_n"]=len(man); out["gabarito_divergentes"]=ruins
out["gabarito_nao_listados"]=sorted(p.name for p in gd.iterdir() if p.name not in man and p.name!="MANIFESTO.csv")
pathlib.Path(__file__).with_name("referencia_resultado.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
print(json.dumps(out,indent=2,ensure_ascii=False))
