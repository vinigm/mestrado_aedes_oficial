"""

Junta os arquivos anuais de captura de mosquito da Marilia num arquivo so.

Le os saida_2019.csv ... saida_2023.csv (um por ano, separados por ponto e
virgula), empilha tudo e guarda de qual arquivo cada linha veio. O resultado
(base_dados_marilia.csv) e o historico antigo de mosquito que a montagem da
tabela_final usa.

"""

import glob
import os

import pandas as pd

from config import settings


def consolidar_marilia() -> pd.DataFrame:
    """

    Le e empilha os arquivos anuais da Marilia, guardando a origem de cada linha.

    Returns:
        A tabela com todos os anos juntos, no formato original da Marilia mais a
        coluna arquivo_origem (o nome do arquivo de onde a linha veio).

    """
    caminhos = sorted(glob.glob(str(settings.PASTA_DADOS_MARILIA / "saida_*.csv")))
    partes = []
    for caminho in caminhos:
        parte = pd.read_csv(caminho, sep=";", parse_dates=["Data Inicio", "Data Fim"])
        parte["arquivo_origem"] = os.path.basename(caminho)
        partes.append(parte)
    return pd.concat(partes, ignore_index=True)
