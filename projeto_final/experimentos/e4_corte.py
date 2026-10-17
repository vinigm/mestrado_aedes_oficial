"""E4: sensibilidade do corte temporal (descritiva, sem teste estatistico).

Pre-declaracao: `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, secao 6.
Roda o `completo` e o `sem_vetor`, folha 5, 12 horizontes, com o corte ingenuo do
treino PELA DATA DA PERGUNTA (`data_origem < t`, que deixa entrar rotulos
posteriores a `t`) e compara, nas mesmas semanas, com o corte pela RESPOSTA
(`s + h <= t`) da E2. Em h = 1 as duas regras coincidem; a variacao de h = 1 tem
de ser exatamente zero.

Exige a E2 pronta: `resultados/ciencia/E2_ablacao/previsoes.csv` e
`travas.json` com `todas_passaram = true` (a E2 so vale se as travas passaram).
O corte pela resposta NAO e recalculado: vem de la.

Grava em `resultados/ciencia/E4_corte/`:
    - `parciais/previsoes_<braco>_h<hh>.csv`: um por (braco, h);
    - `previsoes.csv`: braco, folha, h, data_origem, data_alvo, real, previsto, corte
      (corte = `pergunta`);
    - `comparacao.csv`: braco, h, n, mae_corte_resposta, mae_corte_pergunta,
      variacao_pct, r2_corte_resposta, r2_corte_pergunta (janela de avaliacao,
      mesmas semanas nos dois lados);
    - `E4_corte.log`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`)

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 nohup python3 -B -m experimentos.e4_corte \\
        --bracos completo > /dev/null 2>&1 &
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.e4_corte --so-juntar

Parciais existentes sao pulados; `--refazer` forca. Com os 24 parciais, o proprio
script junta e compara.
"""

import argparse
import json
import pathlib
import sys
import time

import pandas as pd

from aedes.bracos import montar_matriz_do_braco
from aedes.comparacoes import comparar_cortes
from aedes.configuracao import (
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
    FOLHA_5,
)
from aedes.metricas import COLUNA_DO_BRACO, COLUNA_DO_HORIZONTE
from aedes.walk_forward_com_corte import RegraDeCorte, executar_walk_forward_com_corte
from experimentos.comum_ciencia import (
    PASTA_DA_CIENCIA,
    RegistradorDeLog,
    carregar_tabela_cortada,
    gravar_parcial,
    validar_horizontes,
)

PASTA_DE_SAIDA = PASTA_DA_CIENCIA / "E4_corte"
PASTA_DOS_PARCIAIS = PASTA_DE_SAIDA / "parciais"
CAMINHO_DAS_PREVISOES = PASTA_DE_SAIDA / "previsoes.csv"
CAMINHO_DA_COMPARACAO = PASTA_DE_SAIDA / "comparacao.csv"
REGISTRADOR = RegistradorDeLog(PASTA_DE_SAIDA / "E4_corte.log")

PASTA_DA_E2 = PASTA_DA_CIENCIA / "E2_ablacao"
CAMINHO_DAS_PREVISOES_DA_E2 = PASTA_DA_E2 / "previsoes.csv"
CAMINHO_DAS_TRAVAS_DA_E2 = PASTA_DA_E2 / "travas.json"

BRACOS_DA_E4 = ("completo", "sem_vetor")
FOLHA_DA_E4 = 5
COLUNA_DA_FOLHA = "folha"
COLUNA_DO_CORTE = "corte"
COLUNAS_DO_ARQUIVO_DE_PREVISOES = (
    COLUNA_DO_BRACO,
    COLUNA_DA_FOLHA,
    COLUNA_DO_HORIZONTE,
    COLUNA_DATA_DE_ORIGEM,
    COLUNA_DATA_ALVO,
    "real",
    "previsto",
    COLUNA_DO_CORTE,
)


def exigir_a_e2_pronta() -> None:
    """Confirma que a E2 terminou e que as travas dela passaram.

    Raises:
        FileNotFoundError: Se `previsoes.csv` ou `travas.json` da E2 nao existirem.
        RuntimeError: Se as travas da E2 nao tiverem passado na etapa completa.
    """
    for caminho in (CAMINHO_DAS_PREVISOES_DA_E2, CAMINHO_DAS_TRAVAS_DA_E2):
        if not caminho.exists():
            raise FileNotFoundError(f"A E4 exige a E2 pronta; falta {caminho}")
    with open(CAMINHO_DAS_TRAVAS_DA_E2, encoding="utf-8") as arquivo:
        travas = json.load(arquivo)
    travas_passaram = travas.get("todas_passaram") is True
    etapa_completa = travas.get("escopo") == "etapa_completa"
    if not (travas_passaram and etapa_completa):
        raise RuntimeError(
            "As travas da E2 nao constam como aprovadas na etapa completa "
            f"(escopo={travas.get('escopo')!r}, todas_passaram={travas.get('todas_passaram')!r})."
        )


def caminho_do_parcial(nome_do_braco: str, horizonte: int) -> pathlib.Path:
    """Caminho do parcial de um braco e um horizonte."""
    return PASTA_DOS_PARCIAIS / f"previsoes_{nome_do_braco}_h{horizonte:02d}.csv"


def rodar_um_pedaco(nome_do_braco: str, horizonte: int, tabela_cortada: pd.DataFrame) -> pd.DataFrame:
    """Roda o walk-forward com o corte pela PERGUNTA (folha 5) de um braco e um horizonte."""
    matriz = montar_matriz_do_braco(
        tabela_cortada, horizonte, nome_do_braco, CONFIGURACAO_VARIAVEIS, CONFIGURACAO_DADOS
    )
    inicio = time.perf_counter()
    previsoes = executar_walk_forward_com_corte(
        matriz, horizonte, FOLHA_5, CONFIGURACAO_AVALIACAO, RegraDeCorte.PERGUNTA
    )
    segundos = time.perf_counter() - inicio

    previsoes[COLUNA_DO_BRACO] = nome_do_braco
    previsoes[COLUNA_DA_FOLHA] = FOLHA_DA_E4
    previsoes[COLUNA_DO_CORTE] = RegraDeCorte.PERGUNTA.value
    previsoes = previsoes[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]
    REGISTRADOR.registrar(
        f"pedaco braco={nome_do_braco} folha={FOLHA_DA_E4} h={horizonte:2d} corte=pergunta "
        f"linhas_da_matriz={len(matriz)} previsoes={len(previsoes)} tempo={segundos:.1f}s"
    )
    return previsoes


def listar_parciais_faltantes() -> list[pathlib.Path]:
    """Parciais que ainda nao existem entre os 24 esperados (2 bracos x 12 horizontes)."""
    faltantes: list[pathlib.Path] = []
    for nome_do_braco in BRACOS_DA_E4:
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            caminho = caminho_do_parcial(nome_do_braco, horizonte)
            if not caminho.exists():
                faltantes.append(caminho)
    return faltantes


def juntar_parciais() -> pd.DataFrame:
    """Junta os 24 parciais na ordem braco, horizonte.

    Raises:
        FileNotFoundError: Se algum parcial nao existir.
    """
    faltantes = listar_parciais_faltantes()
    if faltantes:
        nomes = ", ".join(caminho.name for caminho in faltantes[:5])
        raise FileNotFoundError(f"{len(faltantes)} parcial(is) ausente(s), ex.: {nomes}")

    tabelas: list[pd.DataFrame] = []
    for nome_do_braco in BRACOS_DA_E4:
        for horizonte in CONFIGURACAO_AVALIACAO.horizontes:
            parcial = pd.read_csv(
                caminho_do_parcial(nome_do_braco, horizonte),
                parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
            )
            tabelas.append(parcial)
    return pd.concat(tabelas, ignore_index=True)[list(COLUNAS_DO_ARQUIVO_DE_PREVISOES)]


def ler_previsoes_da_e2_para_comparar() -> pd.DataFrame:
    """Previsoes da E2 (corte pela resposta) de `completo` e `sem_vetor`, folha 5."""
    previsoes_da_e2 = pd.read_csv(CAMINHO_DAS_PREVISOES_DA_E2, parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO])
    da_folha_5 = previsoes_da_e2[COLUNA_DA_FOLHA] == FOLHA_DA_E4
    dos_bracos_da_e4 = previsoes_da_e2[COLUNA_DO_BRACO].isin(BRACOS_DA_E4)
    return previsoes_da_e2.loc[da_folha_5 & dos_bracos_da_e4].reset_index(drop=True)


def juntar_e_comparar(inicio_da_rodada: float) -> None:
    """Junta os parciais, grava `previsoes.csv` e `comparacao.csv`."""
    exigir_a_e2_pronta()
    previsoes_pela_pergunta = juntar_parciais()
    previsoes_pela_resposta = ler_previsoes_da_e2_para_comparar()
    comparacao = comparar_cortes(previsoes_pela_resposta, previsoes_pela_pergunta, CONFIGURACAO_AVALIACAO)

    previsoes_pela_pergunta.to_csv(CAMINHO_DAS_PREVISOES, index=False)
    comparacao.to_csv(CAMINHO_DA_COMPARACAO, index=False)

    segundos = time.perf_counter() - inicio_da_rodada
    REGISTRADOR.registrar(
        f"juncao: {len(previsoes_pela_pergunta)} previsoes em {CAMINHO_DAS_PREVISOES.name}; "
        f"{len(comparacao)} linhas em {CAMINHO_DA_COMPARACAO.name}; tempo deste processo={segundos:.1f}s"
    )


def ler_argumentos() -> argparse.Namespace:
    """Le `--bracos`, `--horizontes`, `--refazer` e `--so-juntar`."""
    leitor = argparse.ArgumentParser(description="E4: sensibilidade do corte temporal, em pedacos.")
    leitor.add_argument("--bracos", nargs="+", choices=BRACOS_DA_E4, default=None,
                        help="Bracos a rodar. Sem isso, roda os dois.")
    leitor.add_argument("--horizontes", type=int, nargs="+", default=None,
                        help="Horizontes a rodar (1 a 12). Sem isso, roda todos.")
    leitor.add_argument("--refazer", action="store_true", help="Recalcula parciais que ja existem.")
    leitor.add_argument("--so-juntar", action="store_true",
                        help="Nao treina nada: junta os 24 parciais ja gravados e compara.")
    argumentos = leitor.parse_args()
    if argumentos.horizontes is not None:
        try:
            validar_horizontes(argumentos.horizontes)
        except ValueError as erro:
            leitor.error(str(erro))
    return argumentos


def main() -> int:
    """Roda os pedacos pedidos e, se os 24 parciais existirem, junta e compara."""
    inicio_da_rodada = time.perf_counter()
    argumentos = ler_argumentos()
    exigir_a_e2_pronta()

    if not argumentos.so_juntar:
        bracos = tuple(argumentos.bracos) if argumentos.bracos else BRACOS_DA_E4
        horizontes = argumentos.horizontes or list(CONFIGURACAO_AVALIACAO.horizontes)
        tabela_cortada = carregar_tabela_cortada()
        REGISTRADOR.registrar(f"inicio: bracos={list(bracos)} horizontes={horizontes}")
        for nome_do_braco in bracos:
            for horizonte in horizontes:
                caminho = caminho_do_parcial(nome_do_braco, horizonte)
                if caminho.exists() and not argumentos.refazer:
                    REGISTRADOR.registrar(f"pulado (parcial ja existe): {caminho.name}")
                    continue
                previsoes = rodar_um_pedaco(nome_do_braco, horizonte, tabela_cortada)
                gravar_parcial(previsoes, caminho)

    faltantes = listar_parciais_faltantes()
    if faltantes:
        REGISTRADOR.registrar(f"fim do pedaco: faltam {len(faltantes)} de 24 parciais; juncao adiada.")
        return 0
    juntar_e_comparar(inicio_da_rodada)
    return 0


if __name__ == "__main__":
    sys.exit(main())
