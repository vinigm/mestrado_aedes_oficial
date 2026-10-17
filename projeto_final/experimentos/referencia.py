"""Experimento de referencia (ciclo 3): walk-forward completo, 12 horizontes x folhas 5 e 20.

Roda o laco do pacote (`aedes.walk_forward.executar_walk_forward`) sobre a tabela
certificada e grava, em `resultados/referencia/`:
    - `previsoes.csv`: h, data_origem, data_alvo, real, previsto, braco
      (todas as origens do walk-forward, nao so a janela de avaliacao);
    - `metricas.csv`: braco, h, n, mae, r2 na janela de avaliacao
      (07/01/2024 a 01/02/2026, n = 102), para os dois modelos e para as duas
      reguas (`regua_sazonal` e `persistencia`);
    - `referencia.log`: uma linha por pedaco rodado e o resumo da juncao.

Os bracos tem os nomes do gabarito (`testes/referencia_antiga/`):
    - `referencia`:        FOLHA_5  (min_samples_leaf = 5), o modelo do painel;
    - `HistGB_folha20_M1`: FOLHA_20 (min_samples_leaf = 20).

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

A rodada inteira leva cerca de 40 minutos em um processo so (folha 5: ~120-150 s
por horizonte; folha 20: ~70-80 s). O limite de um comando em primeiro plano e de
10 minutos, entao a rodada e fatiada em pedacos com `--folha` e `--horizontes`.
Cada pedaco grava um parcial em `resultados/referencia/parciais/` (escrita
atomica) e, ao terminar, se os 24 parciais ja existem, o proprio script junta
tudo em `previsoes.csv` e `metricas.csv`.

    # um pedaco, em primeiro plano (< 8 min):
    PYTHONDONTWRITEBYTECODE=1 python3 -B -m experimentos.referencia --folha 5 --horizontes 1 2 3

    # a rodada toda, em segundo plano, com log:
    PYTHONDONTWRITEBYTECODE=1 nohup python3 -B -m experimentos.referencia > /dev/null 2>&1 &

    # so juntar os parciais ja existentes (exige os 24) e medir:
    PYTHONDONTWRITEBYTECODE=1 python3 -B -m experimentos.referencia --so-juntar

Sem argumentos, roda as duas folhas e os 12 horizontes (um processo, ~40 min).
"""

import argparse
import os
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
from aedes.metricas import (
    COLUNA_DO_BRACO,
    montar_previsoes_das_reguas,
    recortar_janela_de_avaliacao,
    resumir_metricas_por_horizonte_e_braco,
)
from aedes.variaveis import montar_matriz_do_horizonte
from aedes.walk_forward import COLUNAS_DAS_PREVISOES, executar_walk_forward

PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
CAMINHO_DA_TABELA = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
PASTA_DE_SAIDA = PASTA_DO_PROJETO / "resultados" / "referencia"
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DAS_METRICAS = PASTA_DE_SAIDA / "metricas.csv"
CAMINHO_DO_LOG = PASTA_DE_SAIDA / "referencia.log"

NOME_DO_BRACO_FOLHA_5 = "referencia"
NOME_DO_BRACO_FOLHA_20 = "HistGB_folha20_M1"

# Folha -> (nome do braco no gabarito, configuracao do modelo). Ordem = ordem no CSV final.
BRACOS_POR_FOLHA: dict[int, tuple[str, ConfiguracaoModelo]] = {
    5: (NOME_DO_BRACO_FOLHA_5, FOLHA_5),
    20: (NOME_DO_BRACO_FOLHA_20, FOLHA_20),
}
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (*COLUNAS_DAS_PREVISOES, COLUNA_DO_BRACO)


def registrar_no_log(mensagem: str) -> None:
    """Escreve a mensagem na tela e acrescenta uma linha em `referencia.log`.

    Cada linha e gravada de uma vez em modo de acrescimo, entao pedacos rodando
    em processos paralelos nao embaralham o log.
    """
    carimbo = time.strftime("%Y-%m-%d %H:%M:%S")
    linha = f"{carimbo} {mensagem}"
    print(linha, flush=True)
    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    with open(CAMINHO_DO_LOG, "a", encoding="utf-8") as arquivo_do_log:
        arquivo_do_log.write(linha + "\n")


def carregar_tabela_cortada() -> pd.DataFrame:
    """Le a tabela certificada (hash conferido) e aplica o corte de maturidade."""
    conteudo_em_bytes = CAMINHO_DA_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    tabela_cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)
    return tabela_cortada


def caminho_do_parcial(folha: int, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de uma folha e um horizonte."""
    return PASTA_DOS_PARCIAIS / f"previsoes_folha{folha}_h{horizonte:02d}.csv"


def gravar_parcial(previsoes: pd.DataFrame, caminho: pathlib.Path) -> None:
    """Grava o CSV num arquivo temporario e o renomeia, para ninguem ler um parcial pela metade."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho_temporario = caminho.with_name(caminho.name + f".tmp{os.getpid()}")
    previsoes.to_csv(caminho_temporario, index=False)
    os.replace(caminho_temporario, caminho)


def rodar_um_pedaco(folha: int, horizonte: int, tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """Roda o walk-forward de uma folha e um horizonte e devolve as previsoes com o braco."""
    nome_do_braco, configuracao_do_modelo = BRACOS_POR_FOLHA[folha]
    matriz = montar_matriz_do_horizonte(tabela_cortada, horizonte, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS)
    inicio = time.perf_counter()
    previsoes = executar_walk_forward(matriz, horizonte, configuracao_do_modelo, CONFIGURACAO_AVALIACAO)
    segundos = time.perf_counter() - inicio
    previsoes[COLUNA_DO_BRACO] = nome_do_braco
    registrar_no_log(
        f"pedaco braco={nome_do_braco} folha={folha} h={horizonte:2d} "
        f"linhas_da_matriz={len(matriz)} previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes() -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os 24 esperados (2 folhas x 12 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for folha in BRACOS_POR_FOLHA:
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            caminho = caminho_do_parcial(folha, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def juntar_parciais() -> pd.DataFrame:
    """Junta os 24 parciais em um DataFrame: folha 5 (h 1..12) e depois folha 20 (h 1..12).

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes()
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:5])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for folha in BRACOS_POR_FOLHA:
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            parcial = pd.read_csv(
                caminho_do_parcial(folha, horizonte),
                parse_dates=["data_origem", "data_alvo"],
            )
            tabelas.append(parcial)
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def calcular_metricas(previsoes: pd.DataFrame, tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """MAE, R2 e n por braco e horizonte na janela de avaliacao, com as duas reguas.

    As reguas usam a grade (h, data_alvo) do braco `referencia` na janela e a
    serie de casos JA cortada pela maturidade.
    """
    coluna_de_data = CONFIGURACAO_DADOS.coluna_de_data
    coluna_de_casos = CONFIGURACAO_DADOS.coluna_de_casos
    casos_por_data = pd.Series(
        tabela_cortada[coluna_de_casos].to_numpy(dtype=float),
        index=pd.DatetimeIndex(tabela_cortada[coluna_de_data]),
    )

    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes, CONFIGURACAO_AVALIACAO)
    do_braco_de_referencia = previsoes_na_janela[COLUNA_DO_BRACO] == NOME_DO_BRACO_FOLHA_5
    grade_da_referencia = previsoes_na_janela.loc[do_braco_de_referencia]
    previsoes_das_reguas = montar_previsoes_das_reguas(grade_da_referencia, casos_por_data)

    previsoes_para_medir = pd.concat([previsoes_na_janela, previsoes_das_reguas], ignore_index=True)
    return resumir_metricas_por_horizonte_e_braco(previsoes_para_medir)


def juntar_e_medir(inicio_da_rodada: float) -> None:
    """Junta os parciais, grava `previsoes.csv` e `metricas.csv` e registra o resumo no log."""
    previsoes = juntar_parciais()
    tabela_cortada = carregar_tabela_cortada()
    metricas = calcular_metricas(previsoes, tabela_cortada)

    previsoes.to_csv(CAMINHO_DAS_PREVISOES, index=False)
    metricas.to_csv(CAMINHO_DAS_METRICAS, index=False)

    segundos = time.perf_counter() - inicio_da_rodada
    registrar_no_log(
        f"juncao: {len(previsoes)} previsoes em {CAMINHO_DAS_PREVISOES.name}; "
        f"{len(metricas)} linhas em {CAMINHO_DAS_METRICAS.name}; tempo deste processo={segundos:.1f}s"
    )


def ler_argumentos() -> argparse.Namespace:
    """Le `--folha`, `--horizontes` e `--so-juntar` da linha de comando."""
    descricao = "Walk-forward de referencia (12 horizontes x folhas 5 e 20), em pedacos."
    leitor = argparse.ArgumentParser(description=descricao)
    leitor.add_argument(
        "--folha",
        type=int,
        choices=sorted(BRACOS_POR_FOLHA),
        default=None,
        help="Folha minima do modelo (5 ou 20). Sem isso, roda as duas.",
    )
    leitor.add_argument(
        "--horizontes",
        type=int,
        nargs="+",
        default=None,
        help="Horizontes a rodar (1 a 12). Sem isso, roda todos.",
    )
    leitor.add_argument(
        "--so-juntar",
        action="store_true",
        help="Nao treina nada: junta os 24 parciais ja gravados e mede.",
    )
    argumentos = leitor.parse_args()

    if argumentos.horizontes is not None:
        horizontes_invalidos = [h for h in argumentos.horizontes if h not in CONFIGURACAO_AVALIACAO.horizontes]
        if horizontes_invalidos:
            leitor.error(f"horizontes fora de 1..12: {horizontes_invalidos}")
    return argumentos


def main() -> None:
    """Roda os pedacos pedidos e, se os 24 parciais existirem, junta e mede."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()

    if not argumentos.so_juntar:
        folhas = [argumentos.folha] if argumentos.folha is not None else sorted(BRACOS_POR_FOLHA)
        horizontes = argumentos.horizontes or list(CONFIGURACAO_AVALIACAO.horizontes)
        tabela_cortada = carregar_tabela_cortada()
        registrar_no_log(f"inicio: folhas={folhas} horizontes={horizontes}")
        for folha in folhas:
            for horizonte in horizontes:
                previsoes = rodar_um_pedaco(folha, horizonte, tabela_cortada)
                gravar_parcial(previsoes, caminho_do_parcial(folha, horizonte))

    faltantes = listar_parciais_faltantes()
    if faltantes:
        registrar_no_log(f"fim do pedaco: faltam {len(faltantes)} de 24 parciais; juncao adiada.")
        return
    juntar_e_medir(inicio_da_rodada)


if __name__ == "__main__":
    main()
