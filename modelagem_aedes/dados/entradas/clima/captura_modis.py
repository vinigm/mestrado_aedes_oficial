"""

Este arquivo e um teste: baixa dados de satelite (o MODIS, da NASA) direto da
internet, sem precisar de senha ou login. E uma pasta so pra testar, da pra
apagar depois.

Baixa duas coisas para Porto Alegre, usando um ponto central da cidade:
- Quanto de verde tem na vegetacao (NDVI e EVI), atualizado a cada 16 dias,
  junto com um numero que diz se aquele dado e confiavel (pixel_reliability)
- A temperatura da superficie do chao de dia e de noite (LST), atualizada a
  cada 8 dias, ja convertida para graus Celsius

O site que fornece os dados so deixa pedir um numero limitado de datas de
cada vez, entao o codigo pede aos poucos, em varios pedidos.

No final, salva dois arquivos dentro da pasta output/: modis_ndvi_evi.csv e
modis_lst.csv

"""

import os
import requests
import pandas as pd

LAT, LON = -30.03, -51.23
B = "https://modis.ornl.gov/rst/api/v1"
H = {"Accept": "application/json"}
OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)


def lista_datas(produto, ini="2019-01-01"):
    d = requests.get(f"{B}/{produto}/dates", params={"latitude": LAT, "longitude": LON},
                     headers=H, timeout=60).json()["dates"]
    return [x["modis_date"] for x in d if x["calendar_date"] >= ini]



def banda(produto, band, modis_dates, chunk=10):  # o site so deixa pedir 10 datas de cada vez
    out = {}
    for i in range(0, len(modis_dates), chunk):
        sub = modis_dates[i:i + chunk]
        r = requests.get(f"{B}/{produto}/subset", headers=H, timeout=180, params={
            "latitude": LAT, "longitude": LON, "band": band,
            "startDate": sub[0], "endDate": sub[-1], "kmAboveBelow": 0, "kmLeftRight": 0}).json()
        for x in r["subset"]:
            out[x["calendar_date"]] = x["data"][0]
    return out


# --- Verde da vegetacao: NDVI e EVI (produto MOD13Q1) ---
md13 = lista_datas("MOD13Q1")
veg = pd.DataFrame({
    "ndvi": pd.Series(banda("MOD13Q1", "250m_16_days_NDVI", md13)) * 0.0001,
    "evi": pd.Series(banda("MOD13Q1", "250m_16_days_EVI", md13)) * 0.0001,
    "pixel_reliability": pd.Series(banda("MOD13Q1", "250m_16_days_pixel_reliability", md13)),
})
veg.index = pd.to_datetime(veg.index); veg.index.name = "data"
veg[["ndvi", "evi"]] = veg[["ndvi", "evi"]].mask(veg[["ndvi", "evi"]] < -0.2)
veg = veg.sort_index().reset_index()
veg.to_csv(os.path.join(OUT, "modis_ndvi_evi.csv"), index=False)

# --- Temperatura da superficie de dia e de noite (produto MOD11A2) ---
md11 = lista_datas("MOD11A2")
lst = pd.DataFrame({
    "lst_dia_c": pd.Series(banda("MOD11A2", "LST_Day_1km", md11)) * 0.02 - 273.15,
    "lst_noite_c": pd.Series(banda("MOD11A2", "LST_Night_1km", md11)) * 0.02 - 273.15,
})
lst.index = pd.to_datetime(lst.index); lst.index.name = "data"
lst = lst.mask((lst < -100) | (lst > 80)).sort_index().reset_index()
lst.to_csv(os.path.join(OUT, "modis_lst.csv"), index=False)

print("NDVI/EVI:", veg.shape, "|", veg["data"].min().date(), "->", veg["data"].max().date(),
      "| nulos ndvi:", int(veg["ndvi"].isna().sum()))
print("LST:", lst.shape, "|", lst["data"].min().date(), "->", lst["data"].max().date(),
      "| nulos dia:", int(lst["lst_dia_c"].isna().sum()))
print("\namostra NDVI/EVI (final):")
print(veg.tail(4).to_string(index=False))
print("amostra LST (final):")
print(lst.tail(4).to_string(index=False))
