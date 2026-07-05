"""

Junta os arquivos .xlsx da raspagem num historico so (base_armadilhas_concatenada.csv).

A mesma semana aparece em varios arquivos (coletas em dias diferentes). Pra cada
semana, fica so com o arquivo "mais completo" — o que tem MAIS mosquito capturado;
em caso de empate, o de data mais recente. Depois empilha as armadilhas (uma linha
por inspecao) so dos arquivos escolhidos.

IMPORTANTE: este arquivo SO LE os .xlsx da raspagem (os dados que nao podem ser
perdidos). Ele nunca escreve nem apaga nada na pasta Raspagem.

"""

import glob
import os
import re

import pandas as pd

from config import settings

# O nome do arquivo carrega a data da coleta, a semana e quantos mosquitos tem.
# Ex.: dados_aedes_20250106_weekid02_137mosquitos.xlsx
PADRAO_NOME_ARQUIVO = re.compile(r"dados_aedes_(\d{8})_weekid(\d+)_(\d+)mosquitos")


def indexar_arquivos() -> pd.DataFrame:
    """

    Le so o NOME de cada arquivo pra montar um indice (sem abrir os Excel ainda).

    De cada nome tira a data da coleta, o numero da semana e quantos mosquitos o
    nome diz que tem.

    Returns:
        Um indice com uma linha por arquivo, em ordem de semana e data.

    """
    caminhos = sorted(glob.glob(str(settings.PASTA_RASPAGEM_ARQUIVOS / "dados_aedes_*.xlsx")))
    linhas = []
    for caminho in caminhos:
        nome = os.path.basename(caminho)
        casou = PADRAO_NOME_ARQUIVO.search(nome)
        if not casou:
            print("NAO casou com o padrao:", nome)
            continue
        data_texto, semana, mosquitos = casou.groups()
        linhas.append(
            {
                "arquivo": nome,
                "data_coleta": pd.to_datetime(data_texto, format="%Y%m%d"),
                "week_id": int(semana),
                "mosquitos_nome": int(mosquitos),
            }
        )
    return pd.DataFrame(linhas).sort_values(["week_id", "data_coleta"]).reset_index(drop=True)


def abrir_e_recontar(indice: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """

    Abre cada arquivo e conta os mosquitos de verdade (sem confiar so no nome).

    Guarda cada arquivo aberto em memoria pra reusar depois na hora de empilhar.

    Args:
        indice: O indice dos arquivos (de indexar_arquivos).

    Returns:
        O indice com a coluna mosquitos_real, e um dicionario nome -> tabela aberta.

    """
    tabelas_por_arquivo = {}
    contagens_reais = []
    for _, linha in indice.iterrows():
        tabela = pd.read_excel(settings.PASTA_RASPAGEM_ARQUIVOS / linha["arquivo"])
        tabelas_por_arquivo[linha["arquivo"]] = tabela
        contagens_reais.append(int(tabela["total_mosquitos"].sum()))

    indice = indice.copy()
    indice["mosquitos_real"] = contagens_reais
    return indice, tabelas_por_arquivo


def selecionar_um_por_semana(indice: pd.DataFrame) -> pd.DataFrame:
    """

    Escolhe um arquivo por semana: o de mais mosquito (empate: o mais recente).

    Returns:
        O indice com uma linha por semana, em ordem de data de coleta.

    """
    return (
        indice.sort_values(
            ["week_id", "mosquitos_real", "data_coleta"], ascending=[True, False, False]
        )
        .drop_duplicates(subset="week_id", keep="first")
        .sort_values("data_coleta")
        .reset_index(drop=True)
    )


def concatenar_selecionados(
    selecionados: pd.DataFrame,
    tabelas_por_arquivo: dict,
) -> pd.DataFrame:
    """

    Empilha as armadilhas dos arquivos escolhidos, guardando de onde cada linha veio.

    Args:
        selecionados: O indice ja com um arquivo por semana.
        tabelas_por_arquivo: As tabelas abertas (de abrir_e_recontar).

    Returns:
        A base de armadilhas (uma linha por inspecao), ja sem as semanas repetidas.

    """
    partes = []
    for _, linha in selecionados.iterrows():
        tabela = tabelas_por_arquivo[linha["arquivo"]].copy()
        tabela["arquivo_origem"] = linha["arquivo"]
        tabela["data_coleta"] = linha["data_coleta"]
        partes.append(tabela)
    return pd.concat(partes, ignore_index=True)


def consolidar_raspagem() -> pd.DataFrame:
    """

    Faz a consolidacao completa da raspagem, do indice ate a base final.

    Returns:
        A base de armadilhas concatenada (um arquivo por semana, uma linha por inspecao).

    """
    indice = indexar_arquivos()
    indice, tabelas_por_arquivo = abrir_e_recontar(indice)
    selecionados = selecionar_um_por_semana(indice)
    print(f"{len(indice)} arquivos -> {len(selecionados)} semanas selecionadas", flush=True)
    return concatenar_selecionados(selecionados, tabelas_por_arquivo)
