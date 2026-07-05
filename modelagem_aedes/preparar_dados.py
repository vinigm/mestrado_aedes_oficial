"""

CLI que prepara os arquivos crus ANTES da montagem.

Faz tres coisas: consolida o historico da Marilia (junta os arquivos anuais),
filtra os casos de dengue confirmados de Porto Alegre dos arquivos do governo
(SINAN) e junta os arquivos da raspagem (um por semana). Rode quando chegarem
dados novos; depois rode montar.py pra refazer a tabela_final.

Uso:  python preparar_dados.py

Obs: a consolidacao da raspagem SO LE os .xlsx (os dados que nao podem ser
perdidos) e escreve so o resultado juntado; nunca mexe nos arquivos originais.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # deixa o Python achar as pastas do projeto

from config import settings
from preparo import consolidar_marilia, consolidar_raspagem, consolidar_sinan


# Salva uma tabela num arquivo, criando a pasta se precisar.
def salvar(tabela, caminho) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(caminho, index=False)
    print("salvo:", caminho, "| linhas x colunas:", tabela.shape)


def main() -> None:
    print("== consolidando o historico da Marilia ==")
    marilia = consolidar_marilia.consolidar_marilia()
    salvar(marilia, settings.CAMINHO_MARILIA_CONSOLIDADA)

    print("\n== filtrando os casos confirmados do SINAN (pode levar alguns minutos) ==")
    casos = consolidar_sinan.consolidar_sinan()
    salvar(casos, settings.CAMINHO_CASOS_NIVEL_CASO)

    print("\n== juntando os arquivos da raspagem (abre os .xlsx, pode levar 1-2 min) ==")
    raspagem = consolidar_raspagem.consolidar_raspagem()
    salvar(raspagem, settings.CAMINHO_RASPAGEM_CONSOLIDADA)


if __name__ == "__main__":
    main()
