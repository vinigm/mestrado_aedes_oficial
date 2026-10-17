"""Diagnostico: de onde vem a diferenca de ~1 ulp entre meu retreino e as previsoes salvas da E1 (q=0,85, h=4)."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from comum_cert import *

tabela = carregar_tabela_cortada()
h, q = 4, 0.85
inteira = montar_matriz_completa(tabela, h)
trunc = inteira.loc[inteira[COLUNA_ALVO_DATA] <= FIM_DA_CALIBRACAO].reset_index(drop=True)
salvas = pd.read_csv(PASTA_DA_CIENCIA / "E1_quantil" / "previsoes.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA])
salvas = salvas[(salvas.quantil == q) & (salvas.h == h)].set_index(COLUNA_ORIGEM)
meu = pd.read_csv(PASTA_DA_CERTIFICACAO / "parciais_e1" / "meu_q085_h04.csv", parse_dates=[COLUNA_ORIGEM, COLUNA_ALVO_DATA]).set_index(COLUNA_ORIGEM)
dif = (meu["previsto"] - salvas["previsto"]).abs()
ruins = dif[dif > 0].sort_values(ascending=False)
print("origens com dif>0:", len(ruins), "de", len(dif), "| maior previsto entre elas:", meu.loc[ruins.index, "previsto"].abs().max(), "| menor:", meu.loc[ruins.index, "previsto"].abs().min())
print("dif / ulp(previsto), max:", float((ruins / np.spacing(meu.loc[ruins.index, "previsto"].abs())).max()))
vars_ = nomes_das_variaveis(trunc)
for data in list(ruins.index[:3]):
    pos = int(np.flatnonzero((trunc[COLUNA_ORIGEM] == data).to_numpy())[0])
    a = prever_uma_origem(trunc, pos, h, 5, q)
    b = prever_uma_origem(trunc, pos, h, 5, q)
    # DataFrame como entrada (como o laco certificado)
    t = trunc.iloc[:pos + 1]
    treino = t[(t[COLUNA_ORIGEM] + pd.Timedelta(weeks=h)) <= data]
    m = criar_modelo_proprio(5, q)
    m.fit(treino[vars_], treino[COLUNA_Y])
    c = float(m.predict(trunc.iloc[[pos]][vars_])[0])
    print(data.date(), "meu(np) =", repr(a), "| de novo =", repr(b), "| DataFrame =", repr(c), "| salvo =", repr(float(salvas.loc[data, 'previsto'])))
