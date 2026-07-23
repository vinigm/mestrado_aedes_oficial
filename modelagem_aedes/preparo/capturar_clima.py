"""

Baixa o clima de Porto Alegre do NASA POWER e entrega ja juntado por semana.

Pega o clima dia a dia (chuva, temperatura, umidade, orvalho, pressao, sol e
vento) do site publico da NASA (nao precisa de senha nem chave) e junta os dias
em semanas, do mesmo jeito que o resto do projeto conta a semana (comecando no
domingo). O resultado (clima_nasa_power_semanal.csv) e uma das pecas que a
montagem da tabela_final usa.

Baixa da internet ao vivo, entao precisa de conexao. As datas do passado sao
sempre iguais; so as semanas mais recentes podem mudar um pouco (a NASA ajusta os
dados novos depois de um tempo).

"""

import datetime

import pandas as pd
import requests

# Ponto no centro de Porto Alegre e o primeiro domingo do bloco de dados da Marilia.
LATITUDE, LONGITUDE = -30.03, -51.23
INICIO_PADRAO = "20181230"

# O codigo de cada medida no NASA POWER e o nome simples que a gente da pra ela.
MEDIDAS = {
    "PRECTOTCORR": "precipitacao_mm",
    "T2MDEW": "ponto_orvalho",
    "T2M": "temperatura_media",
    "T2M_MIN": "temperatura_minima",
    "T2M_MAX": "temperatura_maxima",
    "RH2M": "umidade_relativa",
    "PS": "pressao_kpa",
    "ALLSKY_SFC_SW_DWN": "radiacao_solar",
    "WS10M": "vento_10m",
}


# Baixa o clima dia a dia do NASA POWER e devolve a tabela ja com nomes simples.
def _baixar_diario(inicio: str, fim: str) -> pd.DataFrame:
    """

    Chama a API do NASA POWER pedindo todas as medidas de uma vez, monta a tabela
    com um dia por linha, troca o codigo de "sem dado" (-999) por vazio e renomeia
    as colunas para os nomes simples do projeto.

    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    resposta = requests.get(url, params={
        "parameters": ",".join(MEDIDAS),
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": inicio,
        "end": fim,
        "format": "JSON",
    }, timeout=120)
    resposta.raise_for_status()
    medidas = resposta.json()["properties"]["parameter"]

    diario = pd.DataFrame({codigo: medidas[codigo] for codigo in MEDIDAS})
    diario.index = pd.to_datetime(diario.index, format="%Y%m%d")
    diario = diario.sort_index()
    diario = diario.replace(-999.0, pd.NA)   # -999 e o codigo do NASA POWER pra "sem dado"
    diario.index.name = "data"
    return diario.rename(columns=MEDIDAS)


# Junta os dias em semanas (comecando no domingo) e resume cada medida.
def _juntar_por_semana(diario: pd.DataFrame) -> pd.DataFrame:
    """

    Para cada semana calcula o minimo, a media e o maximo (e somas/contagens onde
    faz sentido) de cada medida. A semana comeca no domingo, do mesmo jeito que as
    outras tabelas do projeto. Fica so com as semanas que tem os 7 dias completos.

    """
    domingo = diario.index - pd.to_timedelta((diario.index.weekday + 1) % 7, unit="D")
    grupos = diario.assign(data_inicio_semana_epidemi=domingo).groupby("data_inicio_semana_epidemi")
    semanal = pd.DataFrame({
        "n_dias": grupos.size(),
        # chuva
        "precip_total_mm": grupos["precipitacao_mm"].sum(min_count=1),
        "precip_max_dia_mm": grupos["precipitacao_mm"].max(),
        "precip_media_dia_mm": grupos["precipitacao_mm"].mean(),
        "dias_de_chuva": grupos["precipitacao_mm"].apply(lambda serie: int((serie >= 1).sum())),
        # temperatura
        "temp_media": grupos["temperatura_media"].mean(),
        "temp_min": grupos["temperatura_minima"].min(),
        "temp_max": grupos["temperatura_maxima"].max(),
        "temp_amplitude_media": grupos["temperatura_maxima"].mean() - grupos["temperatura_minima"].mean(),
        # ponto de orvalho
        "orvalho_min": grupos["ponto_orvalho"].min(),
        "orvalho_media": grupos["ponto_orvalho"].mean(),
        "orvalho_max": grupos["ponto_orvalho"].max(),
        # umidade
        "umid_min": grupos["umidade_relativa"].min(),
        "umid_media": grupos["umidade_relativa"].mean(),
        "umid_max": grupos["umidade_relativa"].max(),
        # pressao
        "pressao_min": grupos["pressao_kpa"].min(),
        "pressao_media": grupos["pressao_kpa"].mean(),
        "pressao_max": grupos["pressao_kpa"].max(),
        # radiacao solar
        "radiacao_min": grupos["radiacao_solar"].min(),
        "radiacao_media": grupos["radiacao_solar"].mean(),
        "radiacao_max": grupos["radiacao_solar"].max(),
        # vento
        "vento_media": grupos["vento_10m"].mean(),
        "vento_max": grupos["vento_10m"].max(),
    }).reset_index()
    semanal = semanal[semanal["n_dias"] == 7].drop(columns="n_dias")   # so as semanas com os 7 dias
    return semanal


# Baixa o clima do NASA POWER e devolve a tabela semanal pronta para a montagem.
def capturar_clima(inicio: str = INICIO_PADRAO, fim: str | None = None) -> pd.DataFrame:
    """

    E a porta de entrada do modulo: baixa o clima dia a dia e devolve ele ja
    juntado por semana. Sem uma data final (fim), pega ate hoje, para sempre
    trazer as semanas mais recentes.

    """
    if fim is None:
        fim = datetime.date.today().strftime("%Y%m%d")
    diario = _baixar_diario(inicio, fim)
    return _juntar_por_semana(diario)
