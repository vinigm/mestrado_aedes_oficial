"""Pecas comuns dos experimentos da ciencia (E1, E2, E4 e piso de ruido).

Cada etapa grava em `resultados/ciencia/<etapa>/` e segue o padrao de
`experimentos/referencia.py`: pedacos fatiados por argumentos, parciais em
escrita atomica, log com carimbo de tempo e juncao quando todos os parciais
existem. Aqui ficam so as partes que as quatro etapas repartem: caminhos,
log, escrita atomica, leitura dos gabaritos e checagem dos argumentos.

Nenhum modulo certificado e alterado: a tabela e os parciais reaproveitam
`experimentos.referencia` por importacao (as funcoes dele nao dependem do log dele).
"""

import json
import os
import pathlib
import time

import pandas as pd

from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
)
from experimentos.referencia import carregar_tabela_cortada, gravar_parcial

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
PASTA_DA_CIENCIA = PASTA_DO_PROJETO / "resultados" / "ciencia"
CAMINHO_DA_REFERENCIA = PASTA_DO_PROJETO / "resultados" / "referencia" / "previsoes.csv"
PASTA_DO_GABARITO_ANTIGO = PASTA_DO_PROJETO / "testes" / "referencia_antiga"
CAMINHO_DO_GABARITO_POR_BRACO = PASTA_DO_GABARITO_ANTIGO / "previsoes_por_braco_original.csv"

# Nomes dos bracos da referencia certificada (ciclo 3), em `resultados/referencia/`.
NOME_DA_REFERENCIA_FOLHA_5 = "referencia"
NOME_DA_REFERENCIA_FOLHA_20 = "HistGB_folha20_M1"
# Braco antigo sem vetor, folha 20 (gabarito da trava 2 da E2).
NOME_DO_GABARITO_SEM_VETOR_FOLHA_20 = "HistGB_folha20_M0"

TOLERANCIA_DAS_TRAVAS = 1e-9

# `carregar_tabela_cortada` e `gravar_parcial` sao reexportados daqui para os scripts das etapas.
REEXPORTADOS_DA_REFERENCIA = (carregar_tabela_cortada, gravar_parcial)


class RegistradorDeLog:
    """Escreve cada mensagem na tela e acrescenta uma linha com carimbo no log da etapa.

    Cada linha e gravada de uma vez, em modo de acrescimo, entao pedacos
    rodando em processos paralelos nao embaralham o log.
    """

    def __init__(self, caminho_do_log: pathlib.Path) -> None:
        """Guarda o caminho do log; a pasta e criada na primeira mensagem."""
        self.caminho_do_log = caminho_do_log

    def registrar(self, mensagem: str) -> None:
        """Imprime a mensagem e acrescenta `carimbo mensagem` ao arquivo de log."""
        carimbo = time.strftime("%Y-%m-%d %H:%M:%S")
        linha = f"{carimbo} {mensagem}"
        print(linha, flush=True)
        self.caminho_do_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.caminho_do_log, "a", encoding="utf-8") as arquivo_do_log:
            arquivo_do_log.write(linha + "\n")


def gravar_json_de_forma_atomica(conteudo: dict[str, object], caminho: pathlib.Path) -> None:
    """Grava o JSON num arquivo temporario e o renomeia, para ninguem ler um arquivo pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho_temporario = caminho.with_name(caminho.name + f".tmp{os.getpid()}")
    with open(caminho_temporario, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, indent=2, ensure_ascii=False)
        arquivo.write("\n")
    os.replace(caminho_temporario, caminho)


def validar_horizontes(horizontes: list[int]) -> list[int]:
    """Confere que os horizontes pedidos estao entre 1 e 12.

    Raises:
        ValueError: Se algum estiver fora dos horizontes da avaliacao.
    """
    invalidos: list[int] = []
    for horizonte in horizontes:
        if horizonte not in CONFIGURACAO_AVALIACAO.horizontes:
            invalidos.append(horizonte)
    if invalidos:
        raise ValueError(f"horizontes fora de 1..12: {invalidos}")
    return horizontes


def ler_previsoes_da_referencia() -> pd.DataFrame:
    """Le `resultados/referencia/previsoes.csv` (ciclo 3), com as datas convertidas.

    Raises:
        FileNotFoundError: Se a referencia nao existir.
    """
    if not CAMINHO_DA_REFERENCIA.exists():
        raise FileNotFoundError(f"Referencia ausente: {CAMINHO_DA_REFERENCIA}")
    return pd.read_csv(CAMINHO_DA_REFERENCIA, parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO])


def ler_gabarito_por_braco_antigo() -> pd.DataFrame:
    """Le `testes/referencia_antiga/previsoes_por_braco_original.csv` (sem `data_origem`)."""
    return pd.read_csv(CAMINHO_DO_GABARITO_POR_BRACO, parse_dates=[COLUNA_DATA_ALVO])


def ler_matriz_do_gabarito_csv(horizonte: int) -> pd.DataFrame:
    """Le `testes/referencia_antiga/matriz_hXX.csv` (a matriz do codigo antigo, passada por texto)."""
    caminho = PASTA_DO_GABARITO_ANTIGO / f"matriz_h{horizonte:02d}.csv"
    return pd.read_csv(caminho, parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO])
