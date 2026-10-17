"""Por que previsoes.csv != concat(parciais)? Hipotese: read_csv padrao do pandas nao e exato (1 ulp)."""
import numpy as np, pandas as pd, minha_receita as R
E2 = R.RAIZ / "resultados/ciencia/E2_ablacao"
BR = ["completo", "sem_casos", "sem_clima", "sem_vetor", "so_casos", "so_clima", "so_vetor", "so_calendario"]
fast, exact = [], []
for b in BR:
    for f in (5, 20):
        for h in range(1, 13):
            p = E2 / "parciais" / f"previsoes_{b}_folha{f}_h{h:02d}.csv"
            fast.append(pd.read_csv(p)); exact.append(pd.read_csv(p, float_precision="round_trip"))
fast = pd.concat(fast, ignore_index=True); exact = pd.concat(exact, ignore_index=True)
prev_fast = pd.read_csv(E2 / "previsoes.csv"); prev_exact = pd.read_csv(E2 / "previsoes.csv", float_precision="round_trip")
d = lambda a, b: float(np.abs(a.values - b.values).max())
print("n linhas com leitura rapida != exata nos parciais:", int((fast.previsto != exact.previsto).sum()), "max", d(fast.previsto, exact.previsto))
print("previsoes.csv(exato) vs parciais(exato): n diferentes", int((prev_exact.previsto.values != exact.previsto.values).sum()), "max", d(prev_exact.previsto, exact.previsto))
print("previsoes.csv(exato) vs parciais(exato) colunas nao-previsto iguais:", all((prev_exact[c].astype(str).values == exact[c].astype(str).values).all() for c in prev_exact.columns if c != "previsto"))
