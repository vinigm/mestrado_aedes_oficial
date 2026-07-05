"""

Tira, dos arquivos do governo, so os casos de dengue confirmados de Porto Alegre.

Le os arquivos nacionais compactados (DENGBR*.csv.zip, que sao enormes), fica so
com as linhas de Porto Alegre e so com os casos confirmados, e junta tudo num
arquivo por caso (casos_confirmados_poa.csv). E o arquivo que a montagem da
tabela_final usa como casos de dengue.

Pra atualizar: baixe um arquivo novo do OpenDataSUS, ponha na pasta bases_governo
e rode de novo.

"""

import glob
import os
import zipfile

import pandas as pd

from config import settings

# Codigo de Porto Alegre no cadastro de municipios do governo (campo ID_MUNICIP).
CODIGO_MUNICIPIO_POA = 431490

# Codigos que marcam um caso de dengue confirmado (campo CLASSI_FIN do SINAN).
CLASSIFICACOES_CONFIRMADAS = [10, 11, 12]

# Colunas do SINAN que a gente guarda (uma linha por caso).
COLUNAS_SINAN = [
    "SEM_PRI", "SEM_NOT", "DT_SIN_PRI", "DT_NOTIFIC", "NU_ANO", "ID_MUNICIP", "ID_MN_RESI",
    "CLASSI_FIN", "CRITERIO", "EVOLUCAO", "DT_OBITO", "HOSPITALIZ", "CS_SEXO", "NU_IDADE_N",
    "CS_GESTANT", "CS_RACA", "SOROTIPO",
]

# Os arquivos sao grandes demais pra ler de uma vez; leem-se em pedacos deste tamanho.
LINHAS_POR_PEDACO = 300_000


# Le a 1a linha do CSV dentro do zip e decide se o separador e ";" ou ",".
def detectar_separador(caminho_zip):
    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        nome_csv = [nome for nome in arquivo_zip.namelist() if nome.lower().endswith(".csv")][0]
        with arquivo_zip.open(nome_csv) as arquivo:
            primeira_linha = arquivo.readline().decode("latin1")
    if primeira_linha.count(";") > primeira_linha.count(","):
        separador = ";"
    else:
        separador = ","
    return separador, primeira_linha.strip().split(separador)


def filtrar_poa_confirmados(caminho_zip) -> pd.DataFrame:
    """

    Le um arquivo do governo em pedacos e fica so com os casos confirmados de POA.

    Le so as colunas de COLUNAS_SINAN que existem naquele ano, e mantem as linhas
    de Porto Alegre com dengue confirmada. No fim, deixa todas as colunas de
    COLUNAS_SINAN (as que faltarem no ano ficam vazias) mais a origem.

    Returns:
        Uma tabela (um caso por linha) com as colunas de COLUNAS_SINAN mais
        arquivo_origem.

    """
    separador, colunas_do_arquivo = detectar_separador(caminho_zip)
    colunas_a_ler = [coluna for coluna in COLUNAS_SINAN if coluna in colunas_do_arquivo]

    pedacos_filtrados = []
    for pedaco in pd.read_csv(caminho_zip, sep=separador, encoding="latin1", usecols=colunas_a_ler,
                              chunksize=LINHAS_POR_PEDACO, low_memory=False):
        e_de_poa = pd.to_numeric(pedaco["ID_MUNICIP"], errors="coerce") == CODIGO_MUNICIPIO_POA
        e_confirmado = pd.to_numeric(pedaco["CLASSI_FIN"], errors="coerce").isin(
            CLASSIFICACOES_CONFIRMADAS
        )
        pedacos_filtrados.append(pedaco[e_de_poa & e_confirmado])

    casos = pd.concat(pedacos_filtrados, ignore_index=True)
    casos["arquivo_origem"] = os.path.basename(caminho_zip)
    return casos.reindex(columns=COLUNAS_SINAN + ["arquivo_origem"])


def consolidar_sinan() -> pd.DataFrame:
    """

    Filtra todos os arquivos do governo e junta os casos confirmados de POA num so.

    Returns:
        A tabela com todos os casos confirmados de Porto Alegre, um por linha.

    """
    caminhos_zip = sorted(glob.glob(str(settings.PASTA_SINAN_NACIONAL / "DENGBR*.csv.zip")))
    casos_por_arquivo = []
    for caminho_zip in caminhos_zip:
        casos = filtrar_poa_confirmados(caminho_zip)
        print(f"{os.path.basename(caminho_zip):20s} POA confirmados = {len(casos)}", flush=True)
        casos_por_arquivo.append(casos)
    return pd.concat(casos_por_arquivo, ignore_index=True)
