"""Certificacao E7 - retreino independente de celulas de quantil, sklearn direto.

Matriz: testes/referencia_antiga/matriz_hXX.csv (gabarito do codigo antigo, ja sem NaN).
Walk-forward proprio: origem i (posicao 0-based) de 104 ate o fim, passo 1; treino = linhas com
data_origem + h semanas <= data da origem do teste; modelo novo a cada origem.
Uso: python3 -B retreino.py f:q:h [f:q:h ...]   (f = folha minima 5 ou 20)
"""
import sys, pathlib
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

RAIZ = pathlib.Path(__file__).resolve().parents[3]
SAIDA = pathlib.Path(__file__).resolve().parent / "retreino"

def rodar(folha: int, q: float, h: int) -> None:
    destino = SAIDA / f"retreino_f{folha}_q{round(q*100):03d}_h{h:02d}.csv"
    if destino.exists():
        return
    m = pd.read_csv(RAIZ / "testes" / "referencia_antiga" / f"matriz_h{h:02d}.csv",
                    parse_dates=["data_origem", "data_alvo"], float_precision="round_trip")
    cols = [c for c in m.columns if c not in ("data_origem", "data_alvo", "y_h")]
    assert len(cols) == 22
    linhas = []
    for i in range(104, len(m)):
        t = m.loc[i, "data_origem"]
        tr = m[m["data_origem"] + pd.Timedelta(weeks=h) <= t]
        mod = HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=250, learning_rate=0.05,
                                            max_leaf_nodes=15, min_samples_leaf=folha, random_state=42)
        mod.fit(tr[cols], tr["y_h"])
        p = float(mod.predict(m.loc[[i], cols])[0])
        linhas.append((folha, q, h, t, m.loc[i, "data_alvo"], m.loc[i, "y_h"], p))
    out = pd.DataFrame(linhas, columns=["folha", "quantil", "h", "data_origem", "data_alvo", "real", "previsto_bruto"])
    tmp = destino.with_suffix(".tmp")
    out.to_csv(tmp, index=False, float_format="%.17g")
    tmp.rename(destino)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        f, q, h = arg.split(":")
        rodar(int(f), float(q), int(h))
