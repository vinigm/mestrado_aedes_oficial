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
        A tabela_final, uma linha por semana, em ordem de data.

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
    # Ordena so por data. Antes a tabela vinha de dois blocos (Marilia e
    # raspagem) que tambem eram, por coincidencia, dois blocos no tempo
    # (Marilia 2019-2023 antes da raspagem 2025+), entao ordenar por fonte e
    # depois por data dava, de quebra, a ordem cronologica certa. Agora a
    # coluna 'fonte' so marca de onde veio o dado (secretaria ou raspagem;
    # ver dominio/montagem_tabela.py) numa serie semanal UNICA e continua, e
    # "raspagem" vem antes de "secretaria" em ordem alfabetica mas DEPOIS
    # dela no tempo (2026 e o periodo mais novo) - ordenar por fonte primeiro
    # inverteria a tabela inteira. Por isso agora e so por data.
    return tabela_final.sort_values("data").reset_index(drop=True)



# --- Arquivos usados pra montar a tabela_final (abertos como estao, sem mexer) ---


# Abre o parquet certificado da Secretaria com as capturas de mosquito por
# armadilha (2012 ate hoje, uma linha por inspecao; ja inclui 2026 em diante a
# partir da raspagem - ver preparo/unificar_arquivos_secretaria.py). E a fonte
# do vetor usada pela tabela_final desde 16/08/2026, e tambem a fonte do
# experimento bairro_surto desde entao (ver dominio/features_bairro.py e
# pipeline.rodar_bairro_surto), no lugar das capturas da Marilia.
def carregar_secretaria_armadilhas() -> pd.DataFrame:
    return pd.read_parquet(settings.CAMINHO_SECRETARIA_ARMADILHAS, engine="pyarrow")



# Abre o arquivo ja pronto com as capturas de mosquito de 2025 pra frente (uma
# linha por armadilha). NAO alimenta mais a tabela_final desde 16/08/2026 (ver
# carregar_secretaria_armadilhas); o parquet da Secretaria ja incorpora esses
# dados. Fica aqui pra quem quiser ler o arquivo antigo por fora do fluxo.
def carregar_raspagem_consolidada() -> pd.DataFrame:
    return pd.read_csv(settings.CAMINHO_RASPAGEM_CONSOLIDADA, parse_dates=["data_coleta"])



# Abre o historico antigo de capturas de mosquito, de 2019 a 2023 (uma linha
# por armadilha; dados da Marilia). NAO alimenta mais a tabela_final desde
# 16/08/2026 (ver carregar_secretaria_armadilhas) NEM o experimento
# bairro_surto desde entao (ver carregar_capturas_marilia_por_ano, mais
# abaixo); guardado so pra quem quiser reler o arquivo antigo por fora do
# fluxo, ou comparar com a base certificada.
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
    em numero (trocando a virgula por ponto quando precisa). NAO e mais o
    ponto de partida do modelo por bairro (ver carregar_secretaria_armadilhas);
    guardado pra quem quiser reler ou comparar com a base certificada.

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



def carregar_tabela_final_com_casos_notificados() -> pd.DataFrame:
    """

    Abre a tabela_final trocando o alvo: no lugar dos casos CONFIRMADOS do
    SINAN, entram os casos NOTIFICADOS do InfoDengue.

    Serve aos experimentos que preveem surto sobre a serie de notificados
    (decisao de 29/08/2026; ver analises/2026-08-29_rodadas_notificados_zonas/
    PRE_DECLARACAO.md). O motivo nao e so estatistico: a taxa de confirmacao em
    Porto Alegre caiu de 99,6% (2023) para 42,0% (2025), entao "confirmado"
    virou medida administrativa, e a serie encolheu por motivo burocratico e
    nao epidemiologico. Notificado e o que a vigilancia enxerga em tempo real,
    e e sobre ele que um alarme operacional teria de agir.

    O casamento e pela data de inicio da semana. As duas fontes usam a mesma
    convencao (semana comecando no domingo) e concordam sobre qual SE
    corresponde a qual domingo - conferido em 29/08/2026: 715 semanas em comum,
    ZERO divergencia de SE.

    A coluna 'casos' passa a ser os notificados. A coluna 'casos_confirmados'
    NAO fica na tabela: sair com as duas seria convite a vazamento (o
    confirmado e uma funcao do notificado da mesma semana, entao ele entraria
    como feature quase-perfeita do proprio alvo se algum prefixo o pegasse).

    As semanas da grade sem cobertura do InfoDengue ficam com 'casos' vazio
    (NaN), nunca zero - o InfoDengue vai ate 31/05/2026 e a tabela_final vai
    ate 09/08/2026, entao as ultimas semanas ficam sem alvo, do mesmo jeito que
    ja acontece com os confirmados.

    Returns:
        A tabela_final, uma linha por semana, em ordem de data, com a coluna
        'casos' contendo os NOTIFICADOS do InfoDengue.

    """
    tabela_final = pd.read_csv(
        settings.CAMINHO_TABELA_FINAL,
        parse_dates=["data_inicio_semana_epidemi"],
    ).rename(columns={"data_inicio_semana_epidemi": "data"})

    # O confirmado sai da tabela: ele e quase uma funcao do notificado da mesma
    # semana e nao pode sobrar por perto quando o alvo e o notificado.
    tabela_final = tabela_final.drop(columns=["casos_confirmados"])

    infodengue = pd.read_csv(settings.CAMINHO_INFODENGUE, parse_dates=["data_iniSE"])
    casos_notificados = infodengue[["data_iniSE", "casos"]].rename(
        columns={"data_iniSE": "data"}
    )

    tabela_com_notificados = tabela_final.merge(casos_notificados, on="data", how="left")
    return tabela_com_notificados.sort_values("data").reset_index(drop=True)
