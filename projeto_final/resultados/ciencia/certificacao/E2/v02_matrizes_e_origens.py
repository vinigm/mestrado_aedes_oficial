"""Item 2: matrizes de so_vetor, sem_casos e so_calendario (h=1 e h=12) montadas do zero;
linhas/datas/real conferidos contra os parciais salvos; 2 origens de cada, folhas 5 e 20,
retreinadas e comparadas com o previsto salvo. Controle negativo: corte ingenuo e coluna casos extra."""
import json
import numpy as np
import pandas as pd
import minha_receita as R

PARC = R.RAIZ / "resultados/ciencia/E2_ablacao/parciais"
t = R.carregar_tabela_cortada()
saida = {}
for braco in ("so_vetor", "sem_casos", "so_calendario"):
    for h in (1, 12):
        m = R.matriz_do_braco(t, h, braco)
        cols = [c for c in m.columns if c not in ("data_origem", "data_alvo", "y_h")]
        for folha in (5, 20):
            sv = pd.read_csv(PARC / f"previsoes_{braco}_folha{folha}_h{h:02d}.csv", parse_dates=["data_origem", "data_alvo"])
            esperado = m.iloc[104:][["data_origem", "data_alvo"]].reset_index(drop=True)
            datas_ok = bool((sv["data_origem"].values == esperado["data_origem"].values).all()
                            and (sv["data_alvo"].values == esperado["data_alvo"].values).all()
                            and len(sv) == len(esperado))
            real_ok = bool(np.array_equal(sv["real"].values, m.iloc[104:]["y_h"].values))
            # 2 origens: a primeira (pos 104) e a primeira dentro da janela de avaliacao
            pos_janela = int(m.index[m["data_alvo"] >= pd.Timestamp("2024-01-07")][0])
            for pos in (104, pos_janela + 20):
                p, ntr = R.prever_uma_origem(m, h, pos, folha)
                salvo = float(sv.loc[sv["data_origem"] == m.loc[pos, "data_origem"], "previsto"].iloc[0])
                saida[f"{braco}|h{h}|f{folha}|pos{pos}"] = dict(
                    colunas_modelo=len(cols), linhas_matriz=len(m), datas_ok=datas_ok, real_ok=real_ok,
                    n_treino=ntr, meu=p, salvo=salvo, dif=abs(p - salvo))
                print(braco, h, folha, pos, "datas_ok", datas_ok, "real_ok", real_ok, "dif", abs(p - salvo), flush=True)
# controles negativos (h=12, so_vetor, folha 5, uma origem da janela)
m = R.matriz_do_braco(t, 12, "so_vetor")
pos = int(m.index[m["data_alvo"] >= pd.Timestamp("2024-01-07")][0]) + 20
sv = pd.read_csv(PARC / "previsoes_so_vetor_folha5_h12.csv", parse_dates=["data_origem", "data_alvo"])
salvo = float(sv.loc[sv["data_origem"] == m.loc[pos, "data_origem"], "previsto"].iloc[0])
p_ing, _ = R.prever_uma_origem(m, 12, pos, 5, corte="ingenuo")
tt = R.todas_as_variaveis(t, 12)
m2 = m.merge(tt[["data_origem", "casos"]], on="data_origem", how="left")
cols2 = [c for c in m2.columns if c not in ("data_origem", "data_alvo", "y_h")]
p_casos, _ = R.prever_uma_origem(m2, 12, pos, 5, colunas=cols2)
saida["controle_negativo_so_vetor_h12_f5"] = dict(salvo=salvo, corte_ingenuo=p_ing, dif_ingenuo=abs(p_ing - salvo),
                                                   com_coluna_casos=p_casos, dif_com_casos=abs(p_casos - salvo))
print("controle", saida["controle_negativo_so_vetor_h12_f5"])
json.dump(saida, open("v02_resultado.json", "w"), indent=1, default=str)
print("max dif origens:", max(v["dif"] for k, v in saida.items() if "dif" in v))
