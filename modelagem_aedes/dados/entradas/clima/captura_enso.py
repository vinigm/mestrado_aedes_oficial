"""

Este e um script de teste (fica numa pasta descartavel, pode ser apagado) que
baixa da internet os numeros do El Nino / La Nina, direto do site do governo
americano que cuida do clima (NOAA).

Ele pega dois indicadores: o ONI e o quanto a temperatura do mar na regiao
Nino 3.4 fica fora do normal. No final junta os dois e salva um valor por
mes no arquivo output/enso_mensal.csv. Depois, em outra parte do projeto,
o valor de cada mes e copiado pra cada semana daquele mes, pra poder juntar
com a tabela semanal (que e organizada por ano e semana).

"""

import os
import io
import requests
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)

# Baixa o indicador da regiao Nino 3.4, um valor por mes (o quanto a
# temperatura do mar fica fora do normal)
nino_txt = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii", timeout=60).text
nino = pd.read_csv(io.StringIO(nino_txt), sep=r"\s+")
# A tabela baixada vem com varias colunas de temperatura; a ultima e a que
# a gente quer, a da regiao Nino 3.4
nino = nino.rename(columns={nino.columns[0]: "ano", nino.columns[1]: "mes"})
nino34 = nino[["ano", "mes"]].copy()
nino34["nino34_anom"] = nino.iloc[:, -1].astype(float)

# O indicador ONI vem agrupado de 3 em 3 meses; aqui a gente pega o mes do
# meio de cada grupo
oni_txt = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", timeout=60).text
oni = pd.read_csv(io.StringIO(oni_txt), sep=r"\s+")
mes_da_seas = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni["mes"] = oni["SEAS"].map(mes_da_seas)
oni = oni.rename(columns={"YR": "ano", "ANOM": "oni"})[["ano", "mes", "oni"]]

enso = nino34.merge(oni, on=["ano", "mes"], how="outer").sort_values(["ano", "mes"])
enso = enso[(enso["ano"] >= 2018) & (enso["ano"] <= 2026)].reset_index(drop=True)
enso.to_csv(os.path.join(OUT, "enso_mensal.csv"), index=False)

print("ENSO mensal:", enso.shape, "|", f"{enso.ano.min()}-{enso.ano.max()}")
print("últimos meses:")
print(enso.tail(8).to_string(index=False))
