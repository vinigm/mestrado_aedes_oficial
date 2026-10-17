"""E2: ablacao por fonte x horizonte (8 bracos x folhas 5 e 20 x 12 horizontes = 192 walk-forwards).

Pre-declaracao: `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, secao 4.
Corte do treino pela RESPOSTA, quantil 0,85 (o `FOLHA_5` e o `FOLHA_20` do pacote).
Este script so mede MAE descritivo na janela PROPRIA de cada braco; nao faz teste
estatistico (Diebold-Mariano, Holm e bootstrap sao de outra etapa).

Grava em `resultados/ciencia/E2_ablacao/`:
    - `parciais/previsoes_<braco>_folha<f>_h<hh>.csv`: um por (braco, folha, h);
    - `previsoes.csv`: braco, folha, h, data_origem, data_alvo, real, previsto
      (todas as origens do walk-forward, nao so a janela);
    - `mae_descritivo.csv`: braco, folha, h, n_janela, mae (janela de avaliacao,
      07/01/2024 a 01/02/2026, por `data_alvo`; n varia por braco: os bracos
      sem vetor ganham as semanas da enchente);
    - `travas.json`: TRAVA 1 (`completo` folha 5 e folha 20 = referencia do ciclo 3)
      e TRAVA 2 (`sem_vetor` folha 20 = `HistGB_folha20_M0` do codigo antigo),
      diferenca < 1e-9 casando (h, data_alvo);
    - `E2_ablacao.log`.

Se uma trava falhar, a etapa PARA: grava `previsoes.csv` e `travas.json` para
diagnostico, NAO grava `mae_descritivo.csv` e termina com codigo de saida 1
("nenhum resultado e lido antes", pre-declaracao secao 8).

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    # um pedaco, em segundo plano, com log; um processo por fatia:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e2_ablacao \\
        --bracos completo sem_vetor --folhas 20 > /dev/null 2>&1 &

    # conferir as travas assim que `completo` (folhas 5 e 20) e `sem_vetor` (folha 20)
    # tiverem os 12 horizontes (antes de rodar o resto):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e2_ablacao --so-travas

    # juntar (exige os 192 parciais):
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e2_ablacao --so-juntar

Parciais que ja existem sao pulados; `--refazer` forca o recalculo. Ao terminar um
pedaco, se os 192 parciais existem, o proprio script junta e mede.
"""

import argparse
import dataclasses
import pathlib
import sys
import time

import pandas as pd

from aedes.bracos import NOMES_DOS_BRACOS, montar_matriz_do_braco
from aedes.comparacoes import (
    ResultadoDaTrava,
    calcular_mae_na_janela,
    comparar_previsoes_com_gabarito,
)
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
from aedes.walk_forward import executar_walk_forward
from experimentos.comum_ciencia import (
    NOME_DA_REFERENCIA_FOLHA_5,
    NOME_DA_REFERENCIA_FOLHA_20,
    NOME_DO_GABARITO_SEM_VETOR_FOLHA_20,
    PASTA_DA_CIENCIA,
    TOLERANCIA_DAS_TRAVAS,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_json_de_forma_atomica,
    gravar_parcial,
    ler_gabarito_por_braco_antigo,
    ler_previsoes_da_referencia,
    validar_horizontes,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "E2_ablacao"
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DO_MAE = PASTA_DE_SAIDA / "mae_descritivo.csv"
CAMINHO_DAS_TRAVAS = PASTA_DE_SAIDA / "travas.json"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E2_ablacao.log")

COLUNA_DA_FOLHA = "folha"
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (
    COLUNA_DO_BRACO,
    COLUNA_DA_FOLHA,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    "real",
    "previsto",
)
COLUNAS_DO_MAE_DESCRITIVO = (COLUNA_DO_BRACO, COLUNA_DA_FOLHA, COLUNA_DO_HORIZONTE, "n_janela", "mae")

MODELOS_POR_FOLHA: dict[int, ConfiguracaoModelo] = {5: FOLHA_5, 20: FOLHA_20}
CHAVE_DAS_TRAVAS = [COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO]

BRACO_DA_TRAVA_2 = "sem_vetor"
FOLHA_DA_TRAVA_2 = 20


def caminho_do_parcial(nome_do_braco: str, folha: int, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de um braco, uma folha e um horizonte."""
    return PASTA_DOS_PARCIAIS / f"previsoes_{nome_do_braco}_folha{folha}_h{horizonte:02d}.csv"


def rodar_um_pedaco(
    nome_do_braco: str,
    folha: int,
    horizonte: int,
    tabela_cortada: pd.DataFrame,
) -> pd.DataFrame:
    """Roda o walk-forward (corte pela resposta) de um braco, uma folha e um horizonte.

    Returns:
        Previsoes com as colunas de `COLUNAS_DO_ARQUIVO_DE_PREVISOES`.
    """
    matriz = montar_matriz_do_braco(
        tabela_cortada, horizonte, nome_do_braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    inicio = time.perf_counter()
    previsoes = executar_walk_forward(matriz, horizonte, MODELOS_POR_FOLHA[folha], CONFIGURACAO_AVALIACAO)
    segundos = time.perf_counter() - inicio

    previsoes[COLUNA_DO_BRACO] = nome_do_braco
    previsoes[COLUNA_DA_FOLHA] = folha
    previsoes = previsoes[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]
    REGISTRADOR.registrar(
        f"pedaco braco={nome_do_braco} folha={folha} h={horizonte:2d} "
        f"linhas_da_matriz={len(matriz)} colunas_do_modelo={matriz.shape[1] - 3} "
        f"previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes(
    bracos: tuple[str, ...],
    folhas: tuple[int, ...],
) -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os esperados (bracos x folhas x 12 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for nome_do_braco in bracos:
        for folha in folhas:
            for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
                caminho = caminho_do_parcial(nome_do_braco, folha, horizonte)
                if not caminho.exists():
                    faltantes.append(caminho)
    return faltantes


def juntar_parciais(bracos: tuple[str, ...], folhas: tuple[int, ...]) -> pd.DataFrame:
    """Junta os parciais na ordem braco (ordem da pre-declaracao), folha, horizonte.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes(bracos, folhas)
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:5])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for nome_do_braco in bracos:
        for folha in folhas:
            for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
                parcial = pd.read_csv(
                    caminho_do_parcial(nome_do_braco, folha, horizonte),
                    parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
                )
                tabelas.append(parcial)
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def selecionar_braco_e_folha(previsoes: pd.DataFrame, nome_do_braco: str, folha: int) -> pd.DataFrame:
    """Linhas de um braco e uma folha."""
    do_braco = previsoes[COLUNA_DO_BRACO] == nome_do_braco
    da_folha = previsoes[COLUNA_DA_FOLHA] == folha
    return previsoes.loc[do_braco & da_folha]


def resumir_trava(resultado: ResultadoDaTrava, descricao_do_gabarito: str) -> dict[str, object]:
    """Converte o resultado da trava em dicionario para o JSON."""
    conteudo = dataclasses.asdict(resultado)
    conteudo["gabarito"] = descricao_do_gabarito
    return conteudo


def avaliar_travas(previsoes: pd.DataFrame, escopo: str) -> dict[str, object]:
    """Trava 1 (completo folhas 5 e 20 x referencia) e trava 2 (sem_vetor folha 20 x gabarito antigo).

    Args:
        previsoes: Previsoes da E2; precisa conter ao menos `completo` (folhas 5 e 20) e
            `sem_vetor` folha 20, com os 12 horizontes.
        escopo: Texto livre no JSON (`so_travas` ou `etapa_completa`).

    Returns:
        Dicionario com cada trava e `todas_passaram`.
    """
    referencia = ler_previsoes_da_referencia()
    gabarito_antigo = ler_gabarito_por_braco_antigo()

    referencia_folha_5 = referencia.loc[referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_FOLHA_5]
    referencia_folha_20 = referencia.loc[referencia[COLUNA_DO_BRACO] == NOME_DA_REFERENCIA_FOLHA_20]
    do_gabarito_sem_vetor = gabarito_antigo.loc[
        gabarito_antigo[COLUNA_DO_BRACO] == NOME_DO_GABARITO_SEM_VETOR_FOLHA_20
    ]

    trava_1_folha_5 = comparar_previsoes_com_gabarito(
        selecionar_braco_e_folha(previsoes, "completo", 5),
        referencia_folha_5,
        CHAVE_DAS_TRAVAS,
        TOLERANCIA_DAS_TRAVAS,
    )
    trava_1_folha_20 = comparar_previsoes_com_gabarito(
        selecionar_braco_e_folha(previsoes, "completo", 20),
        referencia_folha_20,
        CHAVE_DAS_TRAVAS,
        TOLERANCIA_DAS_TRAVAS,
    )
    trava_2 = comparar_previsoes_com_gabarito(
        selecionar_braco_e_folha(previsoes, BRACO_DA_TRAVA_2, FOLHA_DA_TRAVA_2),
        do_gabarito_sem_vetor,
        CHAVE_DAS_TRAVAS,
        TOLERANCIA_DAS_TRAVAS,
    )

    todas_passaram = trava_1_folha_5.passou and trava_1_folha_20.passou and trava_2.passou
    return {
        "escopo": escopo,
        "trava_1_completo_folha5": resumir_trava(
            trava_1_folha_5, f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_5}"
        ),
        "trava_1_completo_folha20": resumir_trava(
            trava_1_folha_20, f"resultados/referencia/previsoes.csv, braco {NOME_DA_REFERENCIA_FOLHA_20}"
        ),
        "trava_2_sem_vetor_folha20": resumir_trava(
            trava_2,
            "testes/referencia_antiga/previsoes_por_braco_original.csv, "
            f"braco {NOME_DO_GABARITO_SEM_VETOR_FOLHA_20}",
        ),
        "todas_passaram": bool(todas_passaram),
    }


def calcular_mae_descritivo(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE e n na janela de avaliacao, por braco, folha e horizonte (cada braco na sua janela)."""
    linhas: list[dict[str, object]] = []
    for nome_do_braco in pd.unique(previsoes[COLUNA_DO_BRACO]):
        do_braco = previsoes.loc[previsoes[COLUNA_DO_BRACO] == nome_do_braco]
        for folha in sorted(pd.unique(do_braco[COLUNA_DA_FOLHA])):
            da_folha = do_braco.loc[do_braco[COLUNA_DA_FOLHA] == folha]
            for horizonte in sorted(pd.unique(da_folha[COLUNA_DO_HORIZONTE])):
                do_horizonte = da_folha.loc[da_folha[COLUNA_DO_HORIZONTE] == horizonte]
                quantidade_na_janela, mae = calcular_mae_na_janela(do_horizonte, CONFIGURACAO_AVALIACAO)
                linhas.append(
                    {
                        COLUNA_DO_BRACO: nome_do_braco,
                        COLUNA_DA_FOLHA: int(folha),
                        COLUNA_DO_HORIZONTE: int(horizonte),
                        "n_janela": quantidade_na_janela,
                        "mae": mae,
                    }
                )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_MAE_DESCRITIVO))


def checar_travas_antecipadas() -> int:
    """`--so-travas`: confere as travas com os parciais de `completo` e `sem_vetor` ja prontos.

    Returns:
        0 se todas passaram, 1 se alguma falhou, 2 se faltarem parciais.
    """
    precisa_de = (("completo", (5, 20)), (BRACO_DA_TRAVA_2, (FOLHA_DA_TRAVA_2,)))
    faltantes: list[pathlib.Path] = []
    for nome_do_braco, folhas in precisa_de:
        faltantes.extend(listar_parciais_faltantes((nome_do_braco,), folhas))
    if faltantes:
        REGISTRADOR.registrar(f"so-travas: faltam {len(faltantes)} parciais (ex.: {faltantes[0].name}).")
        return 2

    previsoes_de_completo = juntar_parciais(("completo",), (5, 20))
    previsoes_de_sem_vetor = juntar_parciais((BRACO_DA_TRAVA_2,), (FOLHA_DA_TRAVA_2,))
    previsoes = pd.concat([previsoes_de_completo, previsoes_de_sem_vetor], ignore_index=True)
    travas = avaliar_travas(previsoes, escopo="so_travas")
    gravar_json_de_forma_atomica(travas, CAMINHO_DAS_TRAVAS)
    REGISTRADOR.registrar(f"so-travas: todas_passaram={travas['todas_passaram']} (detalhe em {CAMINHO_DAS_TRAVAS.name}).")
    return 0 if travas["todas_passaram"] else 1


def juntar_e_medir(inicio_da_rodada: float) -> int:
    """Junta os 192 parciais, confere as travas e (so se passarem) grava o MAE descritivo.

    Returns:
        0 se tudo passou, 1 se alguma trava falhou.
    """
    previsoes = juntar_parciais(NOMES_DOS_BRACOS, tuple(sorted(MODELOS_POR_FOLHA)))
    previsoes.to_csv(CAMINHO_DAS_PREVISOES, index=False)

    travas = avaliar_travas(previsoes, escopo="etapa_completa")
    gravar_json_de_forma_atomica(travas, CAMINHO_DAS_TRAVAS)

    if not travas["todas_passaram"]:
        REGISTRADOR.registrar(
            "TRAVA FALHOU: a etapa para. previsoes.csv e travas.json gravados para diagnostico; "
            "mae_descritivo.csv NAO foi gerado e nenhum resultado deve ser lido."
        )
        return 1

    mae_descritivo = calcular_mae_descritivo(previsoes)
    mae_descritivo.to_csv(CAMINHO_DO_MAE, index=False)
    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao: {len(previsoes)} previsoes em {CAMINHO_DAS_PREVISOES.name}; travas OK; "
        f"{len(mae_descritivo)} linhas em {CAMINHO_DO_MAE.name}; tempo deste processo={segundos:.1f}s"
    )
    return 0


def ler_argumentos() -> argparse.Namespace:
    """Le `--bracos`, `--folhas`, `--horizontes`, `--refazer`, `--so-juntar` e `--so-travas`."""
    leitor = argparse.ArgumentParser(description="E2: ablacao por fonte x horizonte, em pedacos.")
    leitor.add_argument("--bracos", nargs="+", choices=NOMES_DOS_BRACOS, default=None,
                        help="Bracos a rodar. Sem isso, roda os 8.")
    leitor.add_argument("--folhas", type=int, nargs="+", choices=sorted(MODELOS_POR_FOLHA), default=None,
                        help="Folhas a rodar (5 e/ou 20). Sem isso, roda as duas.")
    leitor.add_argument("--horizontes", type=int, nargs="+", default=None,
                        help="Horizontes a rodar (1 a 12). Sem isso, roda todos.")
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true",
                        help="Nao treina nada: junta os 192 parciais ja gravados, confere as travas e mede.")
    leitor.add_argument("--so-travas", action="store_true",
                        help="Nao treina nada: confere as travas com os parciais de completo e sem_vetor.")
    argumentos = leitor.parse_args()
    if argumentos.horizontes is not None:
        try:
            validar_horizontes(argumentos.horizontes)
        except ValueError as erro:
            leitor.error(str(erro))
    return argumentos


def main() -> int:
    """Roda os pedacos pedidos e, se os 192 parciais existirem, junta, confere as travas e mede."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()

    if argumentos.so_travas:
        return checar_travas_antecipadas()

    if not argumentos.so_juntar:
        bracos = tuple(argumentos.bracos) if argumentos.bracos else NOMES_DOS_BRACOS
        folhas = tuple(argumentos.folhas) if argumentos.folhas else tuple(sorted(MODELOS_POR_FOLHA))
        horizontes = argumentos.horizontes or list(CONFIGURACAO_AVALIACAO.horizontes)
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio: bracos={list(bracos)} folhas={list(folhas)} horizontes={horizontes}")
        for nome_do_braco in bracos:
            for folha in folhas:
                for horizonte in horizontes:
                    caminho = caminho_do_parcial(nome_do_braco, folha, horizonte)
                    if caminho.exists() and not argumentos.refazer:
                        REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                        continue
                    previsoes = rodar_um_pedaco(nome_do_braco, folha, horizonte, tabela_cortada)
                    gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes(NOMES_DOS_BRACOS, tuple(sorted(MODELOS_POR_FOLHA)))
    if faltantes:
        total = len(NOMES_DOS_BRACOS) * len(MODELOS_POR_FOLHA) * len(CONFIGURACAO_AVALIACAO.horizontes)
        REGISTRADOR.registrar(f"fim do pedaco: faltam {len(faltantes)} de {total} parciais; juncao adiada.")
        return 0
    return juntar_e_medir(inicio_da_rodada)


if __name__ == "__main__":
    sys.exit(main())
