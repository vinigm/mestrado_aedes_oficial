"""

Aqui o programa abre os arquivos de dados e deixa cada um organizado.

Cada funcao abre UM arquivo e devolve uma tabela pronta pra usar (com os nomes
das colunas arrumados e as linhas em ordem). Nesta parte a gente SO abre e
organiza os arquivos — fazer contas e treinar o modelo fica em outras partes
do projeto.

"""

import pandas as pd

from config import settings



def carregar_infodengue() -> pd.DataFrame:
    """

    Abre os dados do InfoDengue de Porto Alegre e deixa no formato do projeto.

    O InfoDengue traz, semana a semana, os casos de dengue e o clima da cidade.
    Aqui a gente separa o ano e a semana de cada linha, marca de onde os dados
    vieram e troca os nomes das colunas de temperatura e umidade pra baterem
    com os outros arquivos.

    Returns:
        A tabela do InfoDengue, uma linha por semana, em ordem de data.

    """
    infodengue = pd.read_csv(settings.CAMINHO_INFODENGUE, parse_dates=["data_iniSE"]).rename(
        columns={"data_iniSE": "data"}
    )
    infodengue = infodengue.sort_values("data").reset_index(drop=True)
    infodengue["ano"] = infodengue["SE"].astype(str).str[:4].astype(int)
    infodengue["semana"] = infodengue["SE"].astype(str).str[4:].astype(int)
    infodengue["fonte"] = "infodengue"
    infodengue["temp_media"] = infodengue["tempmed"]
    infodengue["umid_media"] = infodengue["umidmed"]
    return infodengue



def carregar_tabela_final() -> pd.DataFrame:
    """

    Abre a tabela principal do projeto (a "tabela_final") e a deixa organizada.

    Essa tabela junta, semana a semana, tres coisas: os casos de dengue
    confirmados, a quantidade de mosquito pego nas armadilhas e o clima. Aqui a
    gente so troca o nome da coluna de data e da coluna de casos e poe as linhas
    em ordem. As contas e os ajustes do modelo ficam em outras partes.

    Returns:
        A tabela_final, uma linha por semana, em ordem (por origem dos dados e por data).

    """
    tabela_final = pd.read_csv(
        settings.CAMINHO_TABELA_FINAL,
        parse_dates=["data_inicio_semana_epidemi"],
    ).rename(
        columns={
            "data_inicio_semana_epidemi": "data",
            "casos_confirmados": "casos",
        }
    )
    return tabela_final.sort_values(["fonte", "data"]).reset_index(drop=True)



# --- Arquivos usados pra montar a tabela_final (abertos como estao, sem mexer) ---


# Abre o arquivo ja pronto com as capturas de mosquito de 2025 pra frente (uma linha por armadilha).
def carregar_raspagem_consolidada() -> pd.DataFrame:
    return pd.read_csv(settings.CAMINHO_RASPAGEM_CONSOLIDADA, parse_dates=["data_coleta"])



# Abre o historico antigo de capturas de mosquito, de 2019 a 2023 (uma linha por armadilha; dados da Marilia).
def carregar_marilia_consolidada() -> pd.DataFrame:
    return pd.read_csv(
        settings.CAMINHO_MARILIA_CONSOLIDADA, parse_dates=["Data Inicio", "Data Fim"]
    )



# Abre os dados de clima de cada semana (vem da NASA).
def carregar_clima() -> pd.DataFrame:
    return pd.read_csv(settings.CAMINHO_CLIMA_SEMANAL, parse_dates=["data_inicio_semana_epidemi"])



# Abre a lista de casos de dengue confirmados em Porto Alegre, um caso por linha (dados do SINAN, o sistema do governo).
def carregar_casos_nivel_caso() -> pd.DataFrame:
    return pd.read_csv(settings.CAMINHO_CASOS_NIVEL_CASO, low_memory=False)



# Abre os dados do El Nino / La Nina, mes a mes.
def carregar_enso() -> pd.DataFrame:
    return pd.read_csv(settings.CAMINHO_ENSO)



def carregar_capturas_marilia_por_ano(anos) -> pd.DataFrame:
    """

    Abre e junta os arquivos anuais de captura de mosquito da Marilia (um por ano).

    Cada arquivo tem uma linha por armadilha inspecionada. Aqui a gente junta
    todos num so, padroniza o nome do bairro (tudo em maiusculo e sem espacos
    nas pontas) e transforma latitude, longitude e a contagem de Aedes aegypti
    em numero (trocando a virgula por ponto quando precisa). E o ponto de partida
    do modelo por bairro.

    Args:
        anos: Quais anos abrir (por exemplo, de 2019 a 2023).

    Returns:
        Uma tabela com todas as capturas juntas, uma linha por armadilha.

    """
    capturas_por_ano = []
    for ano in anos:
        capturas_por_ano.append(pd.read_csv(settings.caminho_capturas_marilia(ano), sep=";"))
    capturas = pd.concat(capturas_por_ano, ignore_index=True)

    capturas["bairro"] = capturas["Local"].astype(str).str.upper().str.strip()
    for coluna_numerica in ["Latitude", "Longitude", "Aedes aegypti"]:
        texto_com_ponto = capturas[coluna_numerica].astype(str).str.replace(",", ".", regex=False)
        capturas[coluna_numerica] = pd.to_numeric(texto_com_ponto, errors="coerce")
    return capturas
