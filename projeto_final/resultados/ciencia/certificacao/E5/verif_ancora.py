import json, pandas as pd
RAIZ="/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto/projeto_final/"
t=pd.read_csv(RAIZ+"dados/tabela_final.csv",usecols=lambda c: c in ("fonte","data_inicio_semana_epidemi","casos_confirmados"))
print(t.fonte.value_counts().to_dict())
t["ano"]=pd.to_datetime(t.data_inicio_semana_epidemi).dt.year
s=t[t.ano.between(2018,2023)].groupby("ano").casos_confirmados.sum()
print("tabela por ano (semana iniciada):",s.to_dict(),"total",int(s.sum()))
m=json.load(open("razao_por_arquivo_e_ano.json"))
mine={}
for a,v in m.items():
    for k,c in v["por_ano_sintoma"].items():
        mine.setdefault(int(k),[0,0]); mine[int(k)][0]+=c[0]; mine[int(k)][1]+=c[1]
for k in sorted(mine): print(k,"DENGBR notif",mine[k][0],"resid",mine[k][1], "tabela", s.get(k))
tot=sum(mine[k][0] for k in range(2018,2024)); print("num 18-23 (todos arquivos)",tot,"dif vs 12785",tot-12785,(tot-12785)/12785*100)
