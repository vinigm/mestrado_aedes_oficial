"""Trava do walk-forward (ciclo 2, parte 2): h=1 e h=12, folha 5 e folha 20.

Roda o laco novo (`aedes.walk_forward.executar_walk_forward`) sobre a tabela
certificada e grava `resultados/ciclo2/previsoes_trava.csv`, que o teste
`testes/test_walk_forward_diferencial.py` compara com as previsoes salvas do
codigo antigo (`testes/referencia_antiga/previsoes_referencia.csv`).

Os dois bracos e os nomes sao os do gabarito:
    - `referencia`:        FOLHA_5  (min_samples_leaf = 5), o modelo do painel;
    - `HistGB_folha20_M1`: FOLHA_20 (min_samples_leaf = 20), o braco do bloco 7.

Como rodar (de dentro de `projeto_final/`), em segundo plano porque leva alguns
minutos (cerca de 0,45 s por retreino, 284 a 295 retreinos por horizonte):

    PYTHONDONTWRITEBYTECODE=1 nohup python3 -B -m experimentos.trava_walk_forward \
        > resultados/ciclo2/trava_walk_forward.log 2>&1 &
"""

import pathlib
import time

import pandas as pd

from aedes.configuracao import (
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
    ConfiguracaoModelo,
)
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes
from aedes.variaveis import montar_matriz_do_horizonte
from aedes.walk_forward import executar_walk_forward

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_DA_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DE_SAIDA = PASTA_DO_PROJETO / "resultados" / "ciclo2"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes_trava.csv"

HORIZONTES_DA_TRAVA = (1, 12)
NOME_DO_BRACO_FOLHA_5 = "referencia"
NOME_DO_BRACO_FOLHA_20 = "HistGB_folha20_M1"
COLUNA_DO_BRACO = "braco"


def listar_bracos() -> list[tuple[str, ConfiguracaoModelo]]:
    """Os dois bracos da trava, com o nome que eles tem no gabarito."""
    return [
        (NOME_DO_BRACO_FOLHA_5, FOLHA_5),
        (NOME_DO_BRACO_FOLHA_20, FOLHA_20),
    ]


def carregar_tabela_cortada() -> pd.DataFrame:
    """Le a tabela certificada (hash conferido) e aplica o corte de maturidade."""
    conteudo_em_bytes = CAMINHO_DA_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    tabela_cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)
    return tabela_cortada


def rodar_trava() -> pd.DataFrame:
    """Roda os 2 horizontes x 2 bracos e junta as previsoes numa tabela so."""
    tabela_cortada = carregar_tabela_cortada()
    previsoes_de_cada_corrida: list[pd.DataFrame] = []

    for nome_do_braco, configuracao_modelo in listar_bracos():
        for horizonte in HORIZONTES_DA_TRAVA:
            matriz = montar_matriz_do_horizonte(
                tabela_cortada, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
            )
            inicio = time.perf_counter()
            previsoes = executar_walk_forward(
                matriz, horizonte, configuracao_modelo, CONFIGURACAO_AVALIACAO
            )
            segundos = time.perf_counter() - inicio
            print(
                f"braco={nome_do_braco} h={horizonte:2d} linhas_da_matriz={len(matriz)} "
                f"previsoes={len(previsoes)} tempo={segundos:.1f}s",
                flush=True,
            )
            previsoes[COLUNA_DO_BRACO] = nome_do_braco
            previsoes_de_cada_corrida.append(previsoes)

    return pd.concat(previsoes_de_cada_corrida, ignore_index=True)


def main() -> None:
    """Roda a trava e grava `resultados/ciclo2/previsoes_trava.csv`."""
    inicio_total = time.perf_counter()
    previsoes_da_trava = rodar_trava()
    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    previsoes_da_trava.to_csv(CAMINHO_DAS_PREVISOES, index=False)
    segundos_total = time.perf_counter() - inicio_total
    print(
        f"Gravado {CAMINHO_DAS_PREVISOES.name}: {len(previsoes_da_trava)} linhas em {segundos_total:.1f}s.",
        flush=True,
    )


if __name__ == "__main__":
    main()
