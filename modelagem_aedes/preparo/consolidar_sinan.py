"""

Tira, dos arquivos do governo, so os casos de dengue confirmados de Porto Alegre.

Le os arquivos nacionais compactados (DENGBR*.csv.zip, que sao enormes), fica so
com as linhas de Porto Alegre e so com os casos confirmados, e junta tudo num
arquivo por caso (casos_confirmados_poa.csv). E o arquivo que a montagem da
tabela_final usa como casos de dengue.

Pra atualizar: baixe um arquivo novo do OpenDataSUS, ponha na pasta bases_governo
e rode de novo.

Corrigido em 25/09/2026: o OpenDataSUS as vezes reexporta o arquivo de um ano
que ja tinhamos (por exemplo, uma versao "_atualizado" mais completa). Antes,
o glob("DENGBR*.csv.zip") batia com as duas versoes do mesmo ano e elas eram
concatenadas sem selecao nenhuma, contando os casos daquele ano em dobro (foi
o que quase aconteceu com o DENGBR26 em 13/09/2026 - ver
selecionar_um_arquivo_por_ano). Agora so entra UM arquivo por ano.

"""

import glob
import os
import re
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

# Padrao do nome dos arquivos do SINAN: "DENGBR" mais os 2 digitos do ano.
PADRAO_ANO_DO_ARQUIVO_SINAN = re.compile(r"DENGBR(\d{2})")

# Marca, no nome do arquivo, uma reexportacao mais nova do mesmo ano (ex.:
# "DENGBR26_atualizado_set26.csv.zip" reexporta o ano do "DENGBR26.csv.zip").
SUFIXO_ARQUIVO_ATUALIZADO = "_atualizado"


def extrair_ano_do_nome_do_arquivo(caminho_zip: str) -> str:
    """Le os 2 digitos do ano no nome de um arquivo DENGBR*.csv.zip.

    Args:
        caminho_zip: Caminho completo do arquivo (ex.: ".../DENGBR26.csv.zip").

    Returns:
        Os 2 digitos do ano, como texto (ex.: "26").

    Raises:
        ValueError: Se o nome do arquivo nao seguir o padrao "DENGBR\\d\\d".
    """
    nome_arquivo = os.path.basename(caminho_zip)
    correspondencia = PADRAO_ANO_DO_ARQUIVO_SINAN.match(nome_arquivo)
    if correspondencia is None:
        raise ValueError(
            f"Nome de arquivo do SINAN fora do padrao esperado (DENGBR + 2 "
            f"digitos do ano): {nome_arquivo}"
        )
    return correspondencia.group(1)


def obter_data_de_modificacao(caminho_zip: str) -> float:
    """Data de modificacao do arquivo no disco (timestamp Unix)."""
    return os.path.getmtime(caminho_zip)


def escolher_arquivo_mais_recente_do_ano(caminhos_do_ano: list[str]) -> str:
    """Escolhe qual arquivo usar quando o mesmo ano tem mais de um DENGBR baixado.

    Acontece quando o governo reexporta o ano corrente com mais casos
    apurados (ex.: DENGBR26.csv.zip de junho/2026 e
    DENGBR26_atualizado_set26.csv.zip de setembro/2026, o mesmo ano com mais
    tempo de apuracao).

    Regra de escolha, em ordem:
        1. Se exatamente um arquivo do ano tiver o sufixo "_atualizado" no
           nome, usa esse (e o caso real do DENGBR26, medido em 13/09/2026:
           confirmados de POA sobem de 12 para 19).
        2. Caso contrario (nenhum arquivo com o sufixo, ou mais de um), usa
           o arquivo com a data de modificacao mais recente no disco - a
           reexportacao mais nova e a que foi baixada por ultimo.

    Nunca junta os dois arquivos do mesmo ano.

    Args:
        caminhos_do_ano: Os caminhos de todos os arquivos DENGBR do mesmo
            ano (2 ou mais; para 1 so, esta funcao nao precisa ser chamada).

    Returns:
        O caminho do arquivo escolhido.
    """
    arquivos_com_sufixo_atualizado = [
        caminho
        for caminho in caminhos_do_ano
        if SUFIXO_ARQUIVO_ATUALIZADO in os.path.basename(caminho).lower()
    ]
    if len(arquivos_com_sufixo_atualizado) == 1:
        return arquivos_com_sufixo_atualizado[0]
    return max(caminhos_do_ano, key=obter_data_de_modificacao)


def selecionar_um_arquivo_por_ano(caminhos_zip: list[str]) -> list[str]:
    """Garante um unico arquivo do SINAN por ano antes da consolidacao.

    Sem esta selecao, dois arquivos do mesmo ano na pasta bases_governo
    seriam concatenados sem deduplicar (consolidar_sinan fazia isso ate
    25/09/2026), contando os casos daquele ano em dobro.

    Registra no log, para cada ano com mais de um arquivo, qual foi escolhido
    e quais foram ignorados (ver escolher_arquivo_mais_recente_do_ano).

    Args:
        caminhos_zip: Todos os arquivos DENGBR*.csv.zip encontrados na pasta,
            em qualquer ordem.

    Returns:
        Um caminho por ano, em ordem crescente de ano.
    """
    caminhos_por_ano: dict[str, list[str]] = {}
    for caminho_zip in caminhos_zip:
        ano_do_arquivo = extrair_ano_do_nome_do_arquivo(caminho_zip)
        if ano_do_arquivo not in caminhos_por_ano:
            caminhos_por_ano[ano_do_arquivo] = []
        caminhos_por_ano[ano_do_arquivo].append(caminho_zip)

    caminhos_selecionados = []
    for ano_do_arquivo in sorted(caminhos_por_ano.keys()):
        caminhos_do_ano = caminhos_por_ano[ano_do_arquivo]

        if len(caminhos_do_ano) == 1:
            caminho_escolhido = caminhos_do_ano[0]
        else:
            caminho_escolhido = escolher_arquivo_mais_recente_do_ano(caminhos_do_ano)
            nomes_do_ano = sorted(os.path.basename(caminho) for caminho in caminhos_do_ano)
            nomes_ignorados = sorted(
                os.path.basename(caminho)
                for caminho in caminhos_do_ano
                if caminho != caminho_escolhido
            )
            print(
                f"Ano 20{ano_do_arquivo}: {len(caminhos_do_ano)} arquivos do SINAN "
                f"encontrados {nomes_do_ano} - usando "
                f"{os.path.basename(caminho_escolhido)}, ignorando {nomes_ignorados}.",
                flush=True,
            )

        caminhos_selecionados.append(caminho_escolhido)

    return caminhos_selecionados


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
    caminhos_zip_brutos = sorted(glob.glob(str(settings.PASTA_SINAN_NACIONAL / "DENGBR*.csv.zip")))
    caminhos_zip = selecionar_um_arquivo_por_ano(caminhos_zip_brutos)
    casos_por_arquivo = []
    for caminho_zip in caminhos_zip:
        casos = filtrar_poa_confirmados(caminho_zip)
        print(f"{os.path.basename(caminho_zip):20s} POA confirmados = {len(casos)}", flush=True)
        casos_por_arquivo.append(casos)
    return pd.concat(casos_por_arquivo, ignore_index=True)
