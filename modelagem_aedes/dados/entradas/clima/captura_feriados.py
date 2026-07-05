"""

Este arquivo e um teste: baixa a lista de feriados nacionais do Brasil (usando
o site BrasilAPI) de 2019 a 2026. Essa pasta e so de teste, pode ser apagada
depois.

Alem disso, marca quais feriados sao Carnaval, porque o Carnaval costuma cair
bem na epoca do ano em que a dengue mais aparece. O resultado fica salvo no
arquivo output/feriados_brasil.csv.

"""

import os
import requests
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT, exist_ok=True)

linhas = []
for ano in range(2019, 2027):
    r = requests.get(f"https://brasilapi.com.br/api/feriados/v1/{ano}", timeout=30)
    r.raise_for_status()
    for f in r.json():
        linhas.append({"data": f["date"], "nome": f["name"], "tipo": f["type"], "ano": ano})

fer = pd.DataFrame(linhas)
fer["data"] = pd.to_datetime(fer["data"])
fer["eh_carnaval"] = fer["nome"].str.contains("Carnaval", case=False, na=False)
fer = fer.sort_values("data").reset_index(drop=True)
fer.to_csv(os.path.join(OUT, "feriados_brasil.csv"), index=False)

print("feriados:", fer.shape, "|", fer["data"].min().date(), "->", fer["data"].max().date())
print("Carnavais capturados:")
print(fer[fer["eh_carnaval"]][["data", "nome"]].to_string(index=False))
