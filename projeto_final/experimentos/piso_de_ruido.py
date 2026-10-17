"""Piso de ruido numerico (pre-declaracao, secao 8b): quanto o MAE se mexe com o ultimo bit da entrada.

Braco `completo`, folhas 5 e 20, h em {1, 4, 8, 12}, walk-forward COMPLETO (corte pela
resposta) com 5 perturbacoes do ultimo bit da matriz:
    - `csv`: a matriz lida de `testes/referencia_antiga/matriz_hXX.csv`, alinhada a do pacote;
    - `s1` a `s4`: +-1 ulp em cada celula das colunas CONTINUAS (`aedes.perturbacao`),
      direcao sorteada por `np.random.default_rng(semente)`.
Para cada perturbacao: MAE na janela de avaliacao (07/01/2024 a 01/02/2026, n = 102);
`delta = |MAE_perturbada - MAE_referencia|`, com a referencia certificada de
`resultados/referencia/previsoes.csv`; `piso[folha, h]` = o maior delta.
Nenhum teste estatistico; so MAE descritivo.

ZEROS: por padrao a perturbacao das sementes segue a pre-declaracao ao pe da letra
(1 ulp em TODA celula continua; um zero vira +-5e-324). Numa coluna como `casos_mm4`
(91 zeros exatos) isso cria tres valores distintos onde havia um. A opcao
`--zeros manter` deixa os zeros exatos intactos e grava em outra pasta
(`piso_de_ruido_zeros_mantidos/`), para comparar. A perturbacao `csv` nao muda com a opcao.

Grava em `resultados/ciencia/piso_de_ruido/`:
    - `parciais/previsoes_<perturbacao>_folha<f>_h<hh>.csv`;
    - `previsoes.csv`: perturbacao, folha, h, data_origem, data_alvo, real, previsto;
    - `mae_por_perturbacao.csv`: perturbacao, folha, h, n, mae, mae_referencia, delta;
    - `piso.csv`: folha, h, piso_de_ruido, perturbacao_do_maximo, duas_vezes_o_piso;
    - `piso_de_ruido.log` (inclui, por horizonte, a lista de colunas continuas).

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.piso_de_ruido \\
        --folha 20 > /dev/null 2>&1 &
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.piso_de_ruido --so-juntar

Parciais existentes sao pulados; `--refazer` forca. Com os 40 parciais, o proprio
script junta e mede.
"""

import argparse
import pathlib
import sys
import time

import pandas as pd

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import calcular_deltas_e_piso_de_ruido, calcular_mae_na_janela
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
    FOLHA_20,
    ConfiguracaoModelo,
)
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE
from aedes.perturbacao import (
    alinhar_matriz_do_gabarito,
    identificar_colunas_continuas,
    perturbar_ultimo_bit,
)
from aedes.walk_forward import executar_walk_forward
from experimentos.comum_ciencia import (
    NOME_DA_REFERENCIA_FOLHA_5,
    NOME_DA_REFERENCIA_FOLHA_20,
    PASTA_DA_CIENCIA,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_parcial,
    ler_matriz_do_gabarito_csv,
    ler_previsoes_da_referencia,
)

HORIZONTES_DO_PISO = (1, 4, 8, 12)
MODELOS_POR_FOLHA: dict[int, ConfiguracaoModelo] = {5: FOLHA_5, 20: FOLHA_20}
NOME_DA_REFERENCIA_POR_FOLHA = {5: NOME_DA_REFERENCIA_FOLHA_5, 20: NOME_DA_REFERENCIA_FOLHA_20}
BRACO_DO_PISO = "completo"

PERTURBACAO_DO_CSV = "csv"
SEMENTES_POR_PERTURBACAO = {"s1": 1, "s2": 2, "s3": 3, "s4": 4}
PERTURBACOES = (PERTURBACAO_DO_CSV, *SEMENTES_POR_PERTURBACAO)

OPCAO_PERTURBAR_ZEROS = "perturbar"
OPCAO_MANTER_ZEROS = "manter"

COLUNA_DA_PERTURBACAO = "perturbacao"
COLUNA_DA_FOLHA = "folha"
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (
    COLUNA_DA_PERTURBACAO,
    COLUNA_DA_FOLHA,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    "real",
    "previsto",
)


def definir_pastas(opcao_de_zeros: str) -> tuple[pathlib.Path, RegistradorDeLog]:
    """Pasta de saida e log conforme a opcao de zeros (padrao: `piso_de_ruido/`)."""
    if opcao_de_zeros == OPCAO_MANTER_ZEROS:
        pasta_de_saida = PASTA_DA_CIENCIA / "piso_de_ruido_zeros_mantidos"
    else:
        pasta_de_saida = PASTA_DA_CIENCIA / "piso_de_ruido"
    registrador = RegistradorDeLog(pasta_de_saida / "piso_de_ruido.log")
    return pasta_de_saida, registrador


def caminho_do_parcial(pasta_de_saida: pathlib.Path, perturbacao: str, folha: int, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de uma perturbacao, uma folha e um horizonte."""
    return pasta_de_saida / "parciais" / f"previsoes_{perturbacao}_folha{folha}_h{horizonte:02d}.csv"


def montar_matriz_perturbada(
    tabela_cortada: pd.DataFrame,
    horizonte: int,
    perturbacao: str,
    opcao_de_zeros: str,
) -> pd.DataFrame:
    """Matriz do `completo` com a perturbacao pedida (`csv` ou `s1` a `s4`).

    Raises:
        ValueError: Se a perturbacao for desconhecida.
    """
    matriz_do_pacote = montar_matriz_do_braco(
        tabela_cortada, horizonte, BRACO_DO_PISO, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    if perturbacao == PERTURBACAO_DO_CSV:
        matriz_do_gabarito = ler_matriz_do_gabarito_csv(horizonte)
        return alinhar_matriz_do_gabarito(matriz_do_pacote, matriz_do_gabarito)
    if perturbacao in SEMENTES_POR_PERTURBACAO:
        perturbar_zeros = opcao_de_zeros == OPCAO_PERTURBAR_ZEROS
        return perturbar_ultimo_bit(matriz_do_pacote, SEMENTES_POR_PERTURBACAO[perturbacao], perturbar_zeros)
    raise ValueError(f"Perturbacao desconhecida {perturbacao!r}; esperado uma de {PERTURBACOES}.")


def rodar_um_pedaco(
    perturbacao: str,
    folha: int,
    horizonte: int,
    tabela_cortada: pd.DataFrame,
    opcao_de_zeros: str,
    registrador: RegistradorDeLog,
) -> pd.DataFrame:
    """Roda o walk-forward completo do `completo` perturbado, de uma folha e um horizonte."""
    matriz = montar_matriz_perturbada(tabela_cortada, horizonte, perturbacao, opcao_de_zeros)
    colunas_continuas = identificar_colunas_continuas(matriz)
    inicio = time.perf_counter()
    previsoes = executar_walk_forward(matriz, horizonte, MODELOS_POR_FOLHA[folha], CONFIGURACAO_AVALIACAO)
    segundos = time.perf_counter() - inicio

    previsoes[COLUNA_DA_PERTURBACAO] = perturbacao
    previsoes[COLUNA_DA_FOLHA] = folha
    previsoes = previsoes[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]
    registrador.registrar(
        f"pedaco perturbacao={perturbacao} folha={folha} h={horizonte:2d} linhas_da_matriz={len(matriz)} "
        f"previsoes={len(previsoes)} tempo={segundos:.1f}s "
        f"continuas({len(colunas_continuas)})={colunas_continuas}"
    )
    return previsoes


def listar_parciais_faltantes(pasta_de_saida: pathlib.Path) -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os 40 esperados (5 perturbacoes x 2 folhas x 4 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for perturbacao in PERTURBACOES:
        for folha in sorted(MODELOS_POR_FOLHA):
            for horizonte in HORIZONTES_DO_PISO:
                caminho = caminho_do_parcial(pasta_de_saida, perturbacao, folha, horizonte)
                if not caminho.exists():
                    faltantes.append(caminho)
    return faltantes


def juntar_parciais(pasta_de_saida: pathlib.Path) -> pd.DataFrame:
    """Junta os 40 parciais na ordem perturbacao, folha, horizonte.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes(pasta_de_saida)
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:5])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for perturbacao in PERTURBACOES:
        for folha in sorted(MODELOS_POR_FOLHA):
            for horizonte in HORIZONTES_DO_PISO:
                parcial = pd.read_csv(
                    caminho_do_parcial(pasta_de_saida, perturbacao, folha, horizonte),
                    parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
                )
                tabelas.append(parcial)
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def calcular_mae_por_perturbacao(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE e n na janela de avaliacao, por perturbacao, folha e horizonte."""
    linhas: list[dict[str, object]] = []
    for perturbacao in PERTURBACOES:
        da_perturbacao = previsoes.loc[previsoes[COLUNA_DA_PERTURBACAO] == perturbacao]
        for folha in sorted(MODELOS_POR_FOLHA):
            da_folha = da_perturbacao.loc[da_perturbacao[COLUNA_DA_FOLHA] == folha]
            for horizonte in HORIZONTES_DO_PISO:
                do_horizonte = da_folha.loc[da_folha[COLUNA_DO_HORIZONTE] == horizonte]
                quantidade_na_janela, mae = calcular_mae_na_janela(do_horizonte, CONFIGURACAO_AVALIACAO)
                linhas.append(
                    {
                        COLUNA_DA_PERTURBACAO: perturbacao,
                        COLUNA_DA_FOLHA: folha,
                        COLUNA_DO_HORIZONTE: horizonte,
                        "n": quantidade_na_janela,
                        "mae": mae,
                    }
                )
    return pd.DataFrame(linhas)


def calcular_mae_da_referencia() -> pd.DataFrame:
    """MAE na janela da referencia certificada (sem perturbacao), por folha e horizonte."""
    referencia = ler_previsoes_da_referencia()
    linhas: list[dict[str, object]] = []
    for folha in sorted(MODELOS_POR_FOLHA):
        da_folha = referencia.loc[referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_POR_FOLHA[folha]]
        for horizonte in HORIZONTES_DO_PISO:
            do_horizonte = da_folha.loc[da_folha[COLUNA_DO_HORIZONTE] == horizonte]
            quantidade_na_janela, mae = calcular_mae_na_janela(do_horizonte, CONFIGURACAO_AVALIACAO)
            linhas.append(
                {
                    COLUNA_DA_FOLHA: folha,
                    COLUNA_DO_HORIZONTE: horizonte,
                    "n": quantidade_na_janela,
                    "mae": mae,
                }
            )
    return pd.DataFrame(linhas)


def conferir_mesmas_semanas_da_referencia(
    mae_por_perturbacao: pd.DataFrame,
    mae_da_referencia: pd.DataFrame,
) -> None:
    """Exige que cada perturbacao seja medida no mesmo numero de semanas da referencia (n = 102).

    Raises:
        ValueError: Se alguma (perturbacao, folha, h) tiver `n` diferente do da referencia.
    """
    referencia = mae_da_referencia.rename(columns={"n": "n_referencia"})[
        [COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE, "n_referencia"]
    ]
    cruzamento = mae_por_perturbacao.merge(referencia, on=[COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE], how="left")
    com_n_diferente = cruzamento.loc[cruzamento["n"] != cruzamento["n_referencia"]]
    if len(com_n_diferente) > 0:
        raise ValueError(
            f"{len(com_n_diferente)} celula(s) com n diferente do da referencia, "
            f"ex.: {com_n_diferente.iloc[0].to_dict()}"
        )


def juntar_e_medir(pasta_de_saida: pathlib.Path, registrador: RegistradorDeLog, inicio_da_rodada: float) -> None:
    """Junta os parciais e grava `previsoes.csv`, `mae_por_perturbacao.csv` e `piso.csv`."""
    previsoes = juntar_parciais(pasta_de_saida)
    mae_por_perturbacao = calcular_mae_por_perturbacao(previsoes)
    mae_da_referencia = calcular_mae_da_referencia()
    conferir_mesmas_semanas_da_referencia(mae_por_perturbacao, mae_da_referencia)
    deltas, piso = calcular_deltas_e_piso_de_ruido(mae_por_perturbacao, mae_da_referencia)

    previsoes.to_csv(pasta_de_saida / "previsoes.csv", index=False)
    deltas.to_csv(pasta_de_saida / "mae_por_perturbacao.csv", index=False)
    piso.to_csv(pasta_de_saida / "piso.csv", index=False)

    segundos = time.perf_counter() - inicio_da_rodada
    registrador.registrar(
        f"juncao: {len(previsoes)} previsoes; {len(deltas)} linhas em mae_por_perturbacao.csv; "
        f"{len(piso)} linhas em piso.csv; tempo deste processo={segundos:.1f}s"
    )


def ler_argumentos() -> argparse.Namespace:
    """Le `--perturbacoes`, `--folha`, `--horizontes`, `--zeros`, `--refazer` e `--so-juntar`."""
    leitor = argparse.ArgumentParser(description="Piso de ruido numerico (pre-declaracao 8b), em pedacos.")
    leitor.add_argument("--perturbacoes", nargs="+", choices=PERTURBACOES, default=None,
                        help="Perturbacoes a rodar. Sem isso, roda as 5.")
    leitor.add_argument("--folha", type=int, choices=sorted(MODELOS_POR_FOLHA), default=None,
                        help="Folha minima do modelo (5 ou 20). Sem isso, roda as duas.")
    leitor.add_argument("--horizontes", type=int, nargs="+", choices=HORIZONTES_DO_PISO, default=None,
                        help="Horizontes a rodar (entre 1 4 8 12). Sem isso, roda os 4.")
    leitor.add_argument("--zeros", choices=(OPCAO_PERTURBAR_ZEROS, OPCAO_MANTER_ZEROS),
                        default=OPCAO_PERTURBAR_ZEROS,
                        help="`perturbar` (padrao, pre-declaracao) ou `manter` os zeros exatos das sementes.")
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true",
                        help="Nao treina nada: junta os 40 parciais ja gravados e mede.")
    return leitor.parse_args()


def main() -> int:
    """Roda os pedacos pedidos e, se os 40 parciais existirem, junta e mede."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()
    pasta_de_saida, registrador = definir_pastas(argumentos.zeros)

    if not argumentos.so_juntar:
        perturbacoes = tuple(argumentos.perturbacoes) if argumentos.perturbacoes else PERTURBACOES
        folhas = (argumentos.folha,) if argumentos.folha is not None else tuple(sorted(MODELOS_POR_FOLHA))
        horizontes = tuple(argumentos.horizontes) if argumentos.horizontes else HORIZONTES_DO_PISO
        tabela_cortada = carregar_tabela_cortada()
        registrador.registrar(
            f"inicio: perturbacoes={list(perturbacoes)} folhas={list(folhas)} horizontes={list(horizontes)} "
            f"zeros={argumentos.zeros}"
        )
        for perturbacao in perturbacoes:
            for folha in folhas:
                for horizonte in horizontes:
                    caminho = caminho_do_parcial(pasta_de_saida, perturbacao, folha, horizonte)
                    if caminho.exists() and not argumentos.refazer:
                        registrador.registrar(f"pulado (parcial ja existe): {caminho.name}")
                        continue
                    previsoes = rodar_um_pedaco(
                        perturbacao, folha, horizonte, tabela_cortada, argumentos.zeros, registrador
                    )
                    gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes(pasta_de_saida)
    if faltantes:
        registrador.registrar(f"fim do pedaco: faltam {len(faltantes)} de 40 parciais; juncao adiada.")
        return 0
    juntar_e_medir(pasta_de_saida, registrador, inicio_da_rodada)
    return 0


if __name__ == "__main__":
    sys.exit(main())
