"""Replica INDEPENDENTE do walk-forward inteiro (todas as origens) para os bracos dados, folhas 5 e 20,
nos horizontes dados; compara bit a bit com os parciais salvos (leitura exata, float_precision=round_trip)."""
import sys, time, json
import numpy as np, pandas as pd
import minha_receita as R
bracos = sys.argv[1].split(","); horizontes = [int(x) for x in sys.argv[2].split(",")]
tag = sys.argv[3]
t = R.carregar_tabela_cortada()
res = {}
pasta = R.RAIZ / "resultados/ciencia/certificacao/E2/replica"
pasta.mkdir(exist_ok=True)
for b in bracos:
    for h in horizontes:
        m = R.matriz_do_braco(t, h, b)
        for f in (5, 20):
            t0 = time.time()
            mine = R.walk_forward(m, h, f)
            mine.to_csv(pasta / f"replica_{b}_folha{f}_h{h:02d}.csv", index=False)
            sv = pd.read_csv(R.RAIZ / f"resultados/ciencia/E2_ablacao/parciais/previsoes_{b}_folha{f}_h{h:02d}.csv",
                             parse_dates=["data_origem", "data_alvo"], float_precision="round_trip")
            mesmas_datas = bool(len(sv) == len(mine) and (sv.data_alvo.values == mine.data_alvo.values).all())
            dif = np.abs(sv.previsto.values - mine.previsto.values) if mesmas_datas else np.array([np.inf])
            res[f"{b}|f{f}|h{h}"] = dict(n=len(mine), mesmas_datas=mesmas_datas, dif_max=float(dif.max()),
                                         n_bit_diferentes=int((dif != 0).sum()), seg=round(time.time() - t0, 1))
            print(b, f, h, res[f"{b}|f{f}|h{h}"], flush=True)
json.dump(res, open(f"v04_resultado_{tag}.json", "w"), indent=1)
