"""Montagem independente da tabela e dos conjuntos (certificacao E6)."""
import numpy as np, pandas as pd
RAIZ = "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
PROJ = f"{RAIZ}/projeto_final"
CLIMA6 = ["temp_media_lag4","umid_media","temp_media_lag3","temp_max","pressao_media_lag3","pressao_media_lag4"]
def tabela():
    t = pd.read_csv(f"{PROJ}/dados/tabela_final.csv", parse_dates=["data_inicio_semana_epidemi"])
    t = t.rename(columns={"data_inicio_semana_epidemi":"data","casos_confirmados":"casos"})
    ult = t.dropna(subset=["casos"])["data"].max()
    t.loc[t["data"] > ult - pd.Timedelta(weeks=12), "casos"] = np.nan
    for c in ["casos","aedes_aegypti_por_armadilha","temp_media","precip_total_mm","orvalho_media","umid_media","pressao_media"]:
        for l in (1,2,3,4): t[f"{c}_lag{l}"] = t[c].shift(l)
    t["casos_mm4"] = t["casos"].rolling(4).mean()
    t["vetor_mm4"] = t["aedes_aegypti_por_armadilha"].rolling(4).mean()
    a = 2*np.pi*t["semana"]/52
    t["sem_sin"] = np.sin(a); t["sem_cos"] = np.cos(a)
    return t
IGN = ("fonte","SE","data","ano","semana","interpolado","denominador_aproximado","aedes_aegypti","aedes_albopictus","culex_sp","numero_de_armadilhas","nino34_anom","oni")
def grupos(t):
    todas = [c for c in t.columns if c not in IGN]
    vetor = [c for c in todas if any(p in c for p in ("aedes","armadilha","vetor"))]
    clima = [c for c in todas if any(p in c for p in ("temp","precip","orvalho","umid","pressao","radiacao","vento","dias_de_chuva"))]
    nucleo = [c for c in todas if c not in vetor and c not in clima]
    return nucleo, clima, vetor
def validos(t, h, cols):
    d = t.copy(); d["y_h"] = t["casos"].shift(-h)
    a = 2*np.pi*t["semana"].shift(-h)/52
    d["alvo_sin"] = np.sin(a); d["alvo_cos"] = np.cos(a)
    cs = cols + ["alvo_sin","alvo_cos"]
    v = d.dropna(subset=cs+["y_h"]).sort_values("data").reset_index(drop=True)
    return v, cs
def treino_corrigido(v, i, h):
    """linhas cuja resposta (data + h semanas) ja aconteceu na data de origem do teste."""
    origem = v["data"].iloc[i]
    return v[v["data"] + pd.Timedelta(weeks=h) <= origem]
