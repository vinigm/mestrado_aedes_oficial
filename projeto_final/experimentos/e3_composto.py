"""E3: composto que escolhe a folha pelo erro das ultimas N semanas (pre-declaracao, secao 5). Nenhum modelo e treinado.

Le as previsoes da E2 (`completo` folhas 5 e 20), exige as travas da E2 aprovadas, e monta o composto
com N = 13 (primario), 8 e 26 (descritivos) em todos os 12 horizontes. A regra (sem olhar o futuro) esta
em `aedes/composto.py`.

Grava em `resultados/ciencia/E3_composto/`:
    - `previsoes.csv`: N, h, data_origem, data_alvo, real, previsto, folha_escolhida (todas as origens com
      historico suficiente, nao so a janela);
    - `resumo.csv`: N, h, n, mae, fracao_folha20 (janela de avaliacao, por `data_alvo`);
    - `E3_composto.log`.

Ancora: 102 semanas por horizonte na janela; se divergir, o script PARA (codigo de saida 1).

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e3_composto
"""

import json
import sys

import pandas as pd

from aedes.composto import NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA, montar_composto
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
)
from aedes.metricas import (
    COLUNA_DO_BRACO,
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_PREVISTO,
    COLUNA_DO_REAL,
    erro_absoluto_medio,
    recortar_janela_de_avaliacao,
)
from experimentos.comum_ciencia import PASTA_DA_CIENCIA, RegistradorDeLog

PASTA_DA_E2 = PASTA_DA_CIENCIA / "E2_ablacao"
CAMINHO_DAS_PREVISOES_DA_E2 = PASTA_DA_E2 / "previsoes.csv"
CAMINHO_DAS_TRAVAS_DA_E2 = PASTA_DA_E2 / "travas.json"
PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "E3_composto"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DO_RESUMO = PASTA_DE_SAIDA / "resumo.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E3_composto.log")

COLUNA_DA_FOLHA = "folha"
COLUNA_DA_JANELA_N = "N"
BRACO_DO_COMPOSTO = "completo"
JANELA_PRIMARIA = 13
JANELAS_DESCRITIVAS = (8, 26)
JANELAS_DO_COMPOSTO = (JANELA_PRIMARIA, *JANELAS_DESCRITIVAS)
SEMANAS_ESPERADAS_NA_JANELA = 102
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (
    COLUNA_DA_JANELA_N,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    COLUNA_DO_REAL,
    COLUNA_DO_PREVISTO,
    NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA,
)
COLUNAS_DO_RESUMO = (COLUNA_DA_JANELA_N, COLUNA_DO_HORIZONTE, "n", "mae", "fracao_folha20")


def exigir_travas_da_e2_aprovadas() -> None:
    """Para a etapa se `travas.json` da E2 nao existir ou nao mostrar todas as travas aprovadas.

    Raises:
        FileNotFoundError: Se `travas.json` nao existir.
        RuntimeError: Se alguma trava da E2 nao tiver passado.
    """
    if not CAMINHO_DAS_TRAVAS_DA_E2.exists():
        raise FileNotFoundError(f"travas.json da E2 ausente: {CAMINHO_DAS_TRAVAS_DA_E2}")
    with open(CAMINHO_DAS_TRAVAS_DA_E2, encoding="utf-8") as arquivo:
        travas = json.load(arquivo)
    if travas.get("todas_passaram") is not True:
        raise RuntimeError("As travas da E2 nao passaram; a E3 nao roda.")


def ler_previsoes_da_e2() -> pd.DataFrame:
    """Le `previsoes.csv` da E2 com precisao total dos floats e datas convertidas."""
    return pd.read_csv(
        CAMINHO_DAS_PREVISOES_DA_E2,
        parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
        float_precision="round_trip",
    )


def selecionar_completo(previsoes: pd.DataFrame, folha: int, horizonte: int) -> pd.DataFrame:
    """Linhas do braco `completo` de uma folha e um horizonte."""
    e_completo = previsoes[COLUNA_DO_BRACO] == BRACO_DO_COMPOSTO
    e_da_folha = previsoes[COLUNA_DA_FOLHA] == folha
    e_do_horizonte = previsoes[COLUNA_DO_HORIZONTE] == horizonte
    return previsoes.loc[e_completo & e_da_folha & e_do_horizonte]


def montar_todos_os_compostos(previsoes_da_e2: pd.DataFrame) -> pd.DataFrame:
    """Compostos de todas as janelas N e todos os 12 horizontes, empilhados."""
    tabelas: list[pd.DataFrame] = []
    for semanas_recentes in JANELAS_DO_COMPOSTO:
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            da_folha_5 = selecionar_completo(previsoes_da_e2, 5, horizonte)
            da_folha_20 = selecionar_completo(previsoes_da_e2, 20, horizonte)
            composto = montar_composto(da_folha_5, da_folha_20, horizonte, semanas_recentes)
            composto.insert(0, COLUNA_DO_HORIZONTE, horizonte)
            composto.insert(0, COLUNA_DA_JANELA_N, semanas_recentes)
            tabelas.append(composto)
            REGISTRADOR.registrar(
                f"composto N={semanas_recentes} h={horizonte:2d}: {len(composto)} previsoes "
                f"(pares das duas folhas: {len(da_folha_5)})"
            )
    todos = pd.concat(tabelas, ignore_index=True)
    return todos[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def resumir_na_janela(compostos: pd.DataFrame) -> pd.DataFrame:
    """`n`, MAE e fracao de semanas em que o composto usou a folha 20, por N e horizonte, na janela de avaliacao."""
    linhas: list[dict[str, object]] = []
    for semanas_recentes in JANELAS_DO_COMPOSTO:
        do_n = compostos.loc[compostos[COLUNA_DA_JANELA_N] == semanas_recentes]
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            do_horizonte = do_n.loc[do_n[COLUNA_DO_HORIZONTE] == horizonte]
            na_janela = recortar_janela_de_avaliacao(do_horizonte, CONFIGURACAO_AVALIACAO)
            escolheu_a_folha_20 = na_janela[NOME_DA_COLUNA_DA_FOLHA_ESCOLHIDA] == 20
            linhas.append(
                {
                    COLUNA_DA_JANELA_N: semanas_recentes,
                    COLUNA_DO_HORIZONTE: horizonte,
                    "n": len(na_janela),
                    "mae": erro_absoluto_medio(na_janela[COLUNA_DO_REAL], na_janela[COLUNA_DO_PREVISTO]),
                    "fracao_folha20": float(escolheu_a_folha_20.mean()),
                }
            )
    return pd.DataFrame(linhas, columns=list(COLUNAS_DO_RESUMO))


def main() -> int:
    """Monta o composto, confere a ancora de 102 semanas por horizonte e grava previsoes e resumo.

    Returns:
        0 se a ancora bateu; 1 se alguma janela nao tem 102 semanas (nada e gravado como resumo).
    """
    exigir_travas_da_e2_aprovadas()
    previsoes_da_e2 = ler_previsoes_da_e2()
    REGISTRADOR.registrar(f"inicio E3: {len(previsoes_da_e2)} previsoes da E2 lidas; janelas N={list(JANELAS_DO_COMPOSTO)}")

    compostos = montar_todos_os_compostos(previsoes_da_e2)
    compostos.to_csv(CAMINHO_DAS_PREVISOES, index=False)
    resumo = resumir_na_janela(compostos)

    semanas_fora_da_ancora = resumo.loc[resumo["n"] != SEMANAS_ESPERADAS_NA_JANELA]
    if len(semanas_fora_da_ancora) > 0:
        REGISTRADOR.registrar(
            f"ANCORA DIVERGE: {len(semanas_fora_da_ancora)} linha(s) do resumo sem {SEMANAS_ESPERADAS_NA_JANELA} semanas; "
            "resumo.csv NAO gravado."
        )
        REGISTRADOR.registrar(semanas_fora_da_ancora.to_string(index=False))
        return 1

    resumo.to_csv(CAMINHO_DO_RESUMO, index=False)
    REGISTRADOR.registrar(
        f"fim E3: {len(compostos)} previsoes em {CAMINHO_DAS_PREVISOES.name}; "
        f"{len(resumo)} linhas em {CAMINHO_DO_RESUMO.name}; ancora de {SEMANAS_ESPERADAS_NA_JANELA} semanas OK."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
