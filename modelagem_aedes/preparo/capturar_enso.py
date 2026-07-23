"""

Baixa os numeros do El Nino / La Nina (ENSO) do NOAA e entrega um valor por mes.

Pega dois indicadores do site do governo americano que cuida do clima (NOAA): o
ONI e o quanto a temperatura do mar na regiao Nino 3.4 fica fora do normal. Junta
os dois num valor por mes (enso_mensal.csv). Depois, na montagem, o valor de cada
mes e copiado para cada semana daquele mes, para juntar com a tabela semanal.

Baixa da internet ao vivo, entao precisa de conexao. As datas do passado sao
sempre iguais.

"""

import datetime
import io

import pandas as pd
import requests

ANO_INICIO_PADRAO = 2018

# O ONI vem de 3 em 3 meses (a "estacao"); aqui a gente pega o mes do meio de cada grupo.
MES_DA_ESTACAO = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


# Baixa a anomalia de temperatura do mar na regiao Nino 3.4 (um valor por mes).
def _baixar_nino34() -> pd.DataFrame:
    texto = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii", timeout=60).text
    tabela = pd.read_csv(io.StringIO(texto), sep=r"\s+")
    tabela = tabela.rename(columns={tabela.columns[0]: "ano", tabela.columns[1]: "mes"})
    nino34 = tabela[["ano", "mes"]].copy()
    nino34["nino34_anom"] = tabela.iloc[:, -1].astype(float)   # a ultima coluna e a da regiao Nino 3.4
    return nino34


# Baixa o indicador ONI e passa a estacao de 3 meses para o mes do meio.
def _baixar_oni() -> pd.DataFrame:
    texto = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", timeout=60).text
    oni = pd.read_csv(io.StringIO(texto), sep=r"\s+")
    oni["mes"] = oni["SEAS"].map(MES_DA_ESTACAO)
    return oni.rename(columns={"YR": "ano", "ANOM": "oni"})[["ano", "mes", "oni"]]


# Baixa o ENSO do NOAA e devolve os dois indicadores juntos, um valor por mes.
def capturar_enso(ano_inicio: int = ANO_INICIO_PADRAO, ano_fim: int | None = None) -> pd.DataFrame:
    """

    E a porta de entrada do modulo: baixa os dois indicadores (Nino 3.4 e ONI),
    junta pelo ano e mes e recorta no periodo do projeto. Sem um ano final, vai
    ate o ano de hoje.

    """
    if ano_fim is None:
        ano_fim = datetime.date.today().year
    nino34 = _baixar_nino34()
    oni = _baixar_oni()
    enso = nino34.merge(oni, on=["ano", "mes"], how="outer").sort_values(["ano", "mes"])
    enso = enso[(enso["ano"] >= ano_inicio) & (enso["ano"] <= ano_fim)].reset_index(drop=True)
    return enso
