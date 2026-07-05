"""

Este e o programa que monta a tabela_final inteira, do zero.

Ele pega os arquivos que cada fonte de dados ja deixou prontos, junta tudo numa
tabela so e salva o resultado. Rode este arquivo sempre que tiver dado novo
(por exemplo, semanas novas de captura de mosquito) pra atualizar a tabela que
os experimentos usam depois.

Uso: python montar.py

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # faz o python enxergar as pastas config, acesso etc que ficam do lado deste arquivo

from acesso import fontes
from config import settings
from dominio import montagem_tabela


def main() -> None:
    df_raspagem = fontes.carregar_raspagem_consolidada()
    df_marilia = fontes.carregar_marilia_consolidada()
    df_clima = fontes.carregar_clima()
    df_casos = fontes.carregar_casos_nivel_caso()
    df_enso = fontes.carregar_enso()

    tabela_final = montagem_tabela.montar_tabela_final(
        df_raspagem, df_marilia, df_clima, df_casos, df_enso
    )

    settings.CAMINHO_TABELA_FINAL.parent.mkdir(parents=True, exist_ok=True)
    tabela_final.to_csv(settings.CAMINHO_TABELA_FINAL, index=False)
    print("salvo:", settings.CAMINHO_TABELA_FINAL)
    print("linhas x colunas:", tabela_final.shape)


if __name__ == "__main__":
    main()
