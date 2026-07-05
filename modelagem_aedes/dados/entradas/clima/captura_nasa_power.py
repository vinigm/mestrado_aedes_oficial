"""

TESTE de captura - baixa o clima dia a dia do NASA POWER para Porto Alegre e junta os dias em semanas (mesma semana usada no resto do projeto).
Fonte: https://power.larc.nasa.gov/api (site publico da NASA, nao precisa de senha nem chave). Essa pasta e so um teste, pode apagar depois.

O que baixa: chuva, ponto de orvalho, temperatura (media, minima e maxima), umidade, pressao do ar, luz do sol (radiacao) e vento.
Salva dois arquivos dentro da pasta output: um com os dados dia a dia (clima_nasa_power_diario.csv) e outro com os dados juntados por semana (clima_nasa_power_semanal.csv).
A semana comeca no domingo, do mesmo jeito que as outras tabelas do projeto contam a semana.

"""

import os
import requests
import pandas as pd

LAT, LON = -30.03, -51.23        # Porto Alegre (bem no centro da cidade)
INICIO, FIM = "20181230", "20260610"   # pega desde o primeiro domingo do bloco de dados da Marilia ate a raspagem mais recente
PARAMS = ["PRECTOTCORR", "T2MDEW", "T2M", "T2M_MIN", "T2M_MAX", "RH2M", "PS", "ALLSKY_SFC_SW_DWN", "WS10M"]

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)

url = "https://power.larc.nasa.gov/api/temporal/daily/point"
resp = requests.get(url, params={
    "parameters": ",".join(PARAMS), "community": "AG",
    "longitude": LON, "latitude": LAT, "start": INICIO, "end": FIM, "format": "JSON",
}, timeout=120)
resp.raise_for_status()
par = resp.json()["properties"]["parameter"]

# monta a tabela com os dados dia a dia
df = pd.DataFrame({p: par[p] for p in PARAMS})
df.index = pd.to_datetime(df.index, format="%Y%m%d")
df = df.sort_index()
df = df.replace(-999.0, pd.NA)   # esse numero e o codigo que a NASA POWER usa quando nao tem dado (a gente troca por vazio)
df.index.name = "data"

diario = df.rename(columns={
    "PRECTOTCORR": "precipitacao_mm", "T2MDEW": "ponto_orvalho", "T2M": "temperatura_media",
    "T2M_MIN": "temperatura_minima", "T2M_MAX": "temperatura_maxima", "RH2M": "umidade_relativa",
    "PS": "pressao_kpa", "ALLSKY_SFC_SW_DWN": "radiacao_solar", "WS10M": "vento_10m",
})
diario.to_csv(os.path.join(OUT, "clima_nasa_power_diario.csv"))

# junta os dias em semanas (cada semana comeca no domingo daquele dia ou do dia anterior, do jeito que o projeto conta a semana)
# e calcula o minimo, a media e o maximo (e somas ou contagens quando faz sentido) de cada coisa medida por dia.
dom = diario.index - pd.to_timedelta((diario.index.weekday + 1) % 7, unit="D")
g = diario.assign(data_inicio_semana_epidemi=dom).groupby("data_inicio_semana_epidemi")
semanal = pd.DataFrame({
    "n_dias": g.size(),
    # chuva
    "precip_total_mm": g["precipitacao_mm"].sum(min_count=1),
    "precip_max_dia_mm": g["precipitacao_mm"].max(),
    "precip_media_dia_mm": g["precipitacao_mm"].mean(),
    "dias_de_chuva": g["precipitacao_mm"].apply(lambda s: int((s >= 1).sum())),
    # temperatura
    "temp_media": g["temperatura_media"].mean(),
    "temp_min": g["temperatura_minima"].min(),
    "temp_max": g["temperatura_maxima"].max(),
    "temp_amplitude_media": g["temperatura_maxima"].mean() - g["temperatura_minima"].mean(),
    # ponto de orvalho
    "orvalho_min": g["ponto_orvalho"].min(),
    "orvalho_media": g["ponto_orvalho"].mean(),
    "orvalho_max": g["ponto_orvalho"].max(),
    # umidade
    "umid_min": g["umidade_relativa"].min(),
    "umid_media": g["umidade_relativa"].mean(),
    "umid_max": g["umidade_relativa"].max(),
    # pressao
    "pressao_min": g["pressao_kpa"].min(),
    "pressao_media": g["pressao_kpa"].mean(),
    "pressao_max": g["pressao_kpa"].max(),
    # radiacao solar
    "radiacao_min": g["radiacao_solar"].min(),
    "radiacao_media": g["radiacao_solar"].mean(),
    "radiacao_max": g["radiacao_solar"].max(),
    # vento
    "vento_media": g["vento_10m"].mean(),
    "vento_max": g["vento_10m"].max(),
}).reset_index()
semanal = semanal[semanal["n_dias"] == 7].drop(columns="n_dias")   # fica so com as semanas que tem os 7 dias completos
semanal.to_csv(os.path.join(OUT, "clima_nasa_power_semanal.csv"), index=False)

print("diário:", diario.shape, "|", diario.index.min().date(), "->", diario.index.max().date())
print("semanal (completas):", semanal.shape, "(", semanal.shape[1] - 1, "variáveis )")
print("colunas:", [c for c in semanal.columns if c != "data_inicio_semana_epidemi"])
print("\namostra semanal (jan/2025):")
cols_amostra = ["data_inicio_semana_epidemi", "precip_total_mm", "precip_max_dia_mm", "dias_de_chuva",
                "temp_min", "temp_max", "orvalho_media", "umid_media", "pressao_media"]
print(semanal[(semanal["data_inicio_semana_epidemi"] >= "2025-01-01") &
              (semanal["data_inicio_semana_epidemi"] <= "2025-02-10")][cols_amostra].to_string(index=False))
