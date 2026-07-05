"""

Este e o arquivo que voce roda pra disparar um experimento. Ele escolhe o
experimento pedido, manda rodar e guarda as tabelas de resultado na pasta de
saidas.

Uso:  python main.py --experimento cidade_deteccao_surto
      python main.py --experimento cidade_regressao

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # deixa o Python achar as pastas do projeto (config, acesso, etc.) na hora de importar

import argparse

import pandas as pd

from config import settings
from config.experimentos.bairro_surto import BAIRRO_SURTO
from config.experimentos.cidade_deteccao_surto import CIDADE_DETECCAO_SURTO
from config.experimentos.cidade_diebold import CIDADE_DIEBOLD
from config.experimentos.cidade_lift_vetor import CIDADE_LIFT_VETOR
from config.experimentos.cidade_regressao import CIDADE_REGRESSAO
from config.experimentos.cidade_regressao_com_enso import CIDADE_REGRESSAO_COM_ENSO
from config.experimentos.cidade_regressao_sem_enso import CIDADE_REGRESSAO_SEM_ENSO
from config.experimentos.comparacao_literatura import COMPARACAO_LITERATURA
from pipeline import (
    rodar_bairro_surto,
    rodar_cidade_deteccao_surto,
    rodar_cidade_diebold,
    rodar_comparacao_literatura,
    rodar_regressao_conjuntos_fixos,
    rodar_regressao_selecao_clima,
)

# Lista dos experimentos que existem: cada nome liga a configuracao dele com a
# funcao que roda esse experimento e devolve as tabelas prontas (uma tabela pra
# cada arquivo de saida).
EXPERIMENTOS = {
    "cidade_deteccao_surto": (CIDADE_DETECCAO_SURTO, rodar_cidade_deteccao_surto),
    "cidade_regressao": (CIDADE_REGRESSAO, rodar_regressao_selecao_clima),
    "cidade_regressao_sem_enso": (CIDADE_REGRESSAO_SEM_ENSO, rodar_regressao_selecao_clima),
    "cidade_regressao_com_enso": (CIDADE_REGRESSAO_COM_ENSO, rodar_regressao_selecao_clima),
    "cidade_lift_vetor": (CIDADE_LIFT_VETOR, rodar_regressao_conjuntos_fixos),
    "cidade_diebold": (CIDADE_DIEBOLD, rodar_cidade_diebold),
    "comparacao_literatura": (COMPARACAO_LITERATURA, rodar_comparacao_literatura),
    "bairro_surto": (BAIRRO_SURTO, rodar_bairro_surto),
}


def main() -> None:
    analisador = argparse.ArgumentParser(description="Modelagem preditiva Aedes/dengue POA")
    analisador.add_argument(
        "--experimento",
        default="cidade_deteccao_surto",
        choices=list(EXPERIMENTOS),
        help="qual experimento rodar",
    )
    argumentos = analisador.parse_args()

    pd.set_option("display.width", 170)
    configuracao, rodar_experimento = EXPERIMENTOS[argumentos.experimento]
    saidas = rodar_experimento(configuracao)

    settings.PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    for nome_arquivo, dataframe in saidas.items():
        caminho_saida = settings.PASTA_RESULTADOS / nome_arquivo
        dataframe.to_csv(caminho_saida, index=False)
        print("salvo:", caminho_saida)


if __name__ == "__main__":
    main()
