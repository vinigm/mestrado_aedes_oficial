"""

CLI que prepara os arquivos crus ANTES da montagem.

Faz cinco coisas: consolida o historico da Marilia (junta os arquivos anuais),
filtra os casos de dengue confirmados de Porto Alegre dos arquivos do governo
(SINAN), junta os arquivos da raspagem (um por semana), baixa o clima do NASA
POWER e baixa o El Nino/La Nina (ENSO) do NOAA. Rode quando chegarem dados novos;
depois rode montar.py pra refazer a tabela_final.

Uso:  python preparar_dados.py

Obs 1: a consolidacao da raspagem SO LE os .xlsx (os dados que nao podem ser
perdidos) e escreve so o resultado juntado; nunca mexe nos arquivos originais.

Obs 2: o clima e o ENSO sao baixados da internet ao vivo. Se estiver sem conexao,
esses dois passos avisam e sao pulados (o arquivo que ja existe e mantido) — as
consolidacoes locais nao dependem deles.

"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # deixa o Python achar as pastas do projeto

from config import settings
from preparo import (
    capturar_clima,
    capturar_enso,
    consolidar_marilia,
    consolidar_raspagem,
    consolidar_sinan,
)


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

    print("\n== baixando o clima do NASA POWER (internet, pode levar 1-2 min) ==")
    try:
        clima = capturar_clima.capturar_clima()
        salvar(clima, settings.CAMINHO_CLIMA_SEMANAL)
    except Exception as erro:
        print(f"[aviso] nao deu pra baixar o clima ({erro}); mantendo o arquivo que ja existe.")

    print("\n== baixando o El Nino/La Nina (ENSO) do NOAA (internet) ==")
    try:
        enso = capturar_enso.capturar_enso()
        salvar(enso, settings.CAMINHO_ENSO)
    except Exception as erro:
        print(f"[aviso] nao deu pra baixar o ENSO ({erro}); mantendo o arquivo que ja existe.")


if __name__ == "__main__":
    main()
