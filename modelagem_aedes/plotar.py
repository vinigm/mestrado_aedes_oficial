"""

Programa que gera os graficos dos experimentos, usando os arquivos de resultados que ja foram calculados.

Rode depois do main.py: e ele quem cria esses arquivos, dentro da pasta
dados/saidas/resultados. Os graficos ficam salvos em dados/saidas/figuras.

Como usar: python plotar.py

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # deixa o Python achar os arquivos desta pasta, como config e relatorio

from relatorio import graficos


def main() -> None:
    caminhos_gerados = graficos.gerar_todas_figuras()
    for caminho in caminhos_gerados:
        print("figura salva:", caminho)


if __name__ == "__main__":
    main()
