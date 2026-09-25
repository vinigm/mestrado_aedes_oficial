"""Braços LASSO da bateria SARIMA+LASSO+ensemble — 25/09/2026.

Protocolo completo em PRE_DECLARACAO.md (leitura obrigatória, é o contrato desta
rodada). Este script roda os dois braços `lasso` (20 colunas do B0, com vetor)
e `lasso_M0` (as mesmas 14 sem as 6 do vetor): regressão quantílica 0,85 com
penalização L1, alvo em log1p(casos).

Roda no `python3` do sistema (3.14), o mesmo do resto do pipeline.

REUSO, não reimplementação:
    - `harness.montar_features_do_braco` (bateria noturna) monta as colunas,
      idêntico ao que monta as do B0;
    - `rodar.rodar_walk_forward_customizado` (bateria de formulação do alvo)
      é o laço de walk-forward, com o mesmo corte de treino pela data da
      RESPOSTA;
    - `rodar.RegressaoQuantilicaLinearLog` (o V5, já certificado) — este
      script só herda dela e parametriza o `alpha`, que no V5 é fixo em 0.

⚠️ NÃO altera nada fora desta pasta. `harness.py` e `rodar.py` são só
importados, nunca editados.

Uso:

    python rodar_lasso.py --smoke                # 2 bracos x 4 horizontes, ultimas 5 origens
    python rodar_lasso.py --provar-equivalencia   # alpha=0 == V5_linear_log em h=12 (ultimas 20 origens)
    python rodar_lasso.py --cronometro            # 1 celula completa (lasso, h=12, 1 alpha)
    python rodar_lasso.py --rodar-tudo            # bateria completa (NAO RODAR nesta entrega)
"""

import argparse
import dataclasses
import pathlib
import sys
import time
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

# ============================================================================
# CAMINHOS E IMPORTS REUTILIZADOS (só leitura — harness.py e rodar.py nunca
# são editados por este script)
# ============================================================================

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DO_PROJETO = PASTA_DESTE_ARQUIVO.parent.parent
PASTA_BATERIA_NOTURNA = PASTA_DO_PROJETO / "analises/2026-09-23_bateria_noturna"
PASTA_BATERIA_FORMULACAO = PASTA_DO_PROJETO / "analises/2026-09-25_bateria_formulacao_do_alvo"

for pasta_a_importar in (PASTA_BATERIA_NOTURNA, PASTA_BATERIA_FORMULACAO):
    if str(pasta_a_importar) not in sys.path:
        sys.path.insert(0, str(pasta_a_importar))

import harness  # noqa: E402  (harness.py já ajusta o sys.path para modelagem_aedes)
import rodar as bateria_formulacao_do_alvo  # noqa: E402  (o rodar.py da bateria de 25/09, só importado)

CAMINHO_V5_LINEAR_LOG = PASTA_BATERIA_FORMULACAO / "saidas/previsoes_por_braco.csv"
NOME_DO_BRACO_V5_NO_ARQUIVO = "V5_linear_log"

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

# ============================================================================
# CONSTANTES DE NEGÓCIO (seção 2 da pré-declaração, braços lasso e lasso_M0)
# ============================================================================

HORIZONTES_DA_BATERIA = (1, 4, 8, 12)
QUANTIL_DE_REFERENCIA = 0.85
GRADE_DE_ALPHA = (0.001, 0.01, 0.1)
ALPHA_DA_EQUIVALENCIA_COM_V5 = 0.0
ALPHA_DEMONSTRATIVO_DO_SMOKE = 0.01

INICIO_CALIBRACAO_EPIDEMICA = pd.Timestamp("2022-01-01")
INICIO_DA_AVALIACAO = harness.INICIO_DA_AVALIACAO  # 2024-01-01, mesma constante do projeto

NOME_DO_BRACO_LASSO = "lasso"
NOME_DO_BRACO_LASSO_M0 = "lasso_M0"

N_ORIGENS_DO_SMOKE = 5
HORIZONTE_DO_CRONOMETRO = 12
ULTIMAS_ORIGENS_DA_EQUIVALENCIA = 20
TOLERANCIA_RELATIVA_DA_EQUIVALENCIA = 1e-8

TOLERANCIA_NUMERICA_DE_COEFICIENTE_ZERO = 1e-10


@dataclasses.dataclass(frozen=True)
class BracoLasso:
    """Um dos dois braços desta bateria — só muda se o vetor entra ou não.

    Attributes:
        nome: Identificador nas saídas ('lasso' ou 'lasso_M0').
        sem_vetor: Remove as 6 colunas do grupo vetor quando True (M0).
    """

    nome: str
    sem_vetor: bool


BRACOS_LASSO: tuple[BracoLasso, ...] = (
    BracoLasso(NOME_DO_BRACO_LASSO, sem_vetor=False),
    BracoLasso(NOME_DO_BRACO_LASSO_M0, sem_vetor=True),
)


# ============================================================================
# A CLASSE DO V5, PARAMETRIZADA EM ALPHA (herda fit/predict sem tocar neles)
# ============================================================================


class RegressaoQuantilicaLinearLogComAlpha(bateria_formulacao_do_alvo.RegressaoQuantilicaLinearLog):
    """A `RegressaoQuantilicaLinearLog` do V5, com penalização L1 parametrizável.

    O V5 (bateria de formulação do alvo, 25/09/2026, já certificado) fixa
    `alpha=0.0` no `QuantileRegressor`. Esta bateria precisa escolher o alpha
    por horizonte (seção 2 da pré-declaração), então esta subclasse só troca
    o regressor interno — `fit` e `predict`, com o log1p seletivo e a
    padronização ajustada só no treino, continuam exatamente os da classe-mãe.
    Com `alpha=0.0` os dois ficam operacionalmente idênticos: é essa
    equivalência que `provar_equivalencia_com_v5` testa.
    """

    def __init__(self, colunas_para_log1p: list[str], quantil: float, alpha: float) -> None:
        super().__init__(colunas_para_log1p=colunas_para_log1p, quantil=quantil)
        self._regressor = QuantileRegressor(quantile=quantil, alpha=alpha, solver="highs")


def construir_fabrica_de_modelo_lasso(alpha: float) -> Callable[[list[str]], object]:
    """Fábrica de `RegressaoQuantilicaLinearLogComAlpha` para um alpha fixo.

    O walk-forward reusado (`rodar_walk_forward_customizado`) cria uma
    instância nova do modelo a cada corte, chamando `braco.criar_modelo(colunas)`
    — esta função nomeada devolve essa fábrica já fechada sobre o alpha
    escolhido para o horizonte corrente.

    Args:
        alpha: Penalização L1 fixada para todos os cortes desta chamada.

    Returns:
        Uma função que recebe as colunas finais do braço e devolve o modelo.
    """

    def fabrica_do_modelo(colunas_do_modelo: list[str]) -> RegressaoQuantilicaLinearLogComAlpha:
        colunas_para_log1p = bateria_formulacao_do_alvo.identificar_colunas_para_log1p(colunas_do_modelo)
        return RegressaoQuantilicaLinearLogComAlpha(
            colunas_para_log1p=colunas_para_log1p,
            quantil=QUANTIL_DE_REFERENCIA,
            alpha=alpha,
        )

    return fabrica_do_modelo


# ============================================================================
# MONTAGEM DE FEATURES E DO BRAÇO DA BATERIA REUSADA
# ============================================================================


def montar_features_do_braco_lasso(
    tabela_bruta: pd.DataFrame, braco: BracoLasso
) -> tuple[pd.DataFrame, list[str]]:
    """Aplica o motor compartilhado (harness) com as regras do braço.

    Args:
        tabela_bruta: A tabela semanal sem corte nem features.
        braco: 'lasso' (com vetor) ou 'lasso_M0' (sem vetor).

    Returns:
        A tabela pronta e as colunas do modelo (20 ou 14, conforme o braço).
    """
    braco_harness = harness.Braco(nome=braco.nome, sem_vetor=braco.sem_vetor)
    tabela, colunas_do_modelo, _ = harness.montar_features_do_braco(tabela_bruta, braco_harness)
    return tabela, colunas_do_modelo


def montar_braco_da_bateria_reusada(
    braco: BracoLasso, alpha: float
) -> "bateria_formulacao_do_alvo.BracoDaBateria":
    """Empacota o braço lasso no formato que `rodar_walk_forward_customizado` espera.

    A formulação é sempre a bruta (o alvo em casos, sem âncora nem resíduo):
    quem transforma para log1p é a própria `RegressaoQuantilicaLinearLogComAlpha`,
    por dentro do `fit`/`predict`.
    """
    return bateria_formulacao_do_alvo.BracoDaBateria(
        nome=braco.nome,
        descricao=f"regressao quantilica L1, alpha={alpha}",
        sem_vetor=braco.sem_vetor,
        colunas_extras_harness=(),
        formulacao=bateria_formulacao_do_alvo.FORMULACAO_BRUTA,
        criar_modelo=construir_fabrica_de_modelo_lasso(alpha),
    )


def rodar_walk_forward_do_lasso(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    horizonte: int,
    braco: BracoLasso,
    alpha: float,
    limite_de_ultimas_origens: int | None = None,
) -> pd.DataFrame:
    """Roda o walk-forward reusado com um alpha fixo, para um braço e horizonte.

    Args:
        tabela: Tabela já com as features do braço (ver `montar_features_do_braco_lasso`).
        colunas_do_modelo: As colunas do braço.
        horizonte: h, em semanas.
        braco: 'lasso' ou 'lasso_M0'.
        alpha: Penalização L1 fixa nesta chamada.
        limite_de_ultimas_origens: Quando preenchido, roda só as últimas N
            origens (usado pelo `--smoke`).

    Returns:
        Uma linha por origem avaliada, com h, data_alvo, real e previsto
        (já em casos, nunca negativo).
    """
    braco_da_bateria = montar_braco_da_bateria_reusada(braco, alpha)
    return bateria_formulacao_do_alvo.rodar_walk_forward_customizado(
        tabela,
        colunas_do_modelo,
        horizonte,
        braco_da_bateria,
        limite_de_ultimas_origens=limite_de_ultimas_origens,
    )


# ============================================================================
# ESCOLHA DO ALPHA (seção 2 da pré-declaração)
# ============================================================================


def calcular_perda_quantilica_085(reais: pd.Series, previstos: pd.Series) -> float:
    """Perda pinball no quantil 0,85 — a mesma métrica que o `QuantileRegressor` otimiza.

    Reproduz a fórmula de `rodar._perda_quantilica` (bateria de formulação do
    alvo), reimplementada aqui — e não importada — porque aquele nome começa
    com underscore (privado ao módulo de origem).
    """
    diferenca = reais.to_numpy() - previstos.to_numpy()
    return float(
        np.mean(np.maximum(QUANTIL_DE_REFERENCIA * diferenca, (QUANTIL_DE_REFERENCIA - 1.0) * diferenca))
    )


def _perda_do_candidato_de_alpha(candidato: tuple[float, float]) -> float:
    """Chave de ordenação: a perda quantílica de um candidato a alpha."""
    return candidato[1]


def escolher_alpha_de_menor_perda(perda_quantilica_por_alpha: dict[float, float]) -> float:
    """O alpha da grade com menor perda quantílica 0,85 na calibração epidêmica."""
    candidatos_ordenados = sorted(perda_quantilica_por_alpha.items(), key=_perda_do_candidato_de_alpha)
    alpha_vencedor, _ = candidatos_ordenados[0]
    return alpha_vencedor


@dataclasses.dataclass(frozen=True)
class ResultadoDaSelecaoDeAlpha:
    """O que sai de escolher o alpha de um braço num horizonte.

    Attributes:
        alpha_escolhido: O vencedor da grade {0,001 · 0,01 · 0,1}.
        previsoes: O walk-forward completo já rodado com `alpha_escolhido` —
            reusado como previsão final, sem re-rodar o horizonte outra vez.
        perda_quantilica_por_alpha: A perda de cada candidato, para auditoria.
    """

    alpha_escolhido: float
    previsoes: pd.DataFrame
    perda_quantilica_por_alpha: dict[float, float]


def selecionar_alpha_e_previsoes(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    braco: BracoLasso,
    horizonte: int,
) -> ResultadoDaSelecaoDeAlpha:
    """Roda a grade de alpha inteira e escolhe o vencedor pela seção 2.

    Cada candidato roda o walk-forward completo (todas as origens do
    horizonte) porque a perda de calibração (2022–2024) só existe dentro
    dessa corrida — não há atalho que pule direto para o período de
    calibração sem repetir o mesmo laço que a avaliação usa depois.

    Args:
        tabela: Tabela já com as features do braço.
        colunas_do_modelo: As colunas do braço.
        braco: 'lasso' ou 'lasso_M0'.
        horizonte: h, em semanas.

    Returns:
        O alpha vencedor, as previsões completas já rodadas com ele, e a
        perda de cada candidato.
    """
    previsoes_por_alpha: dict[float, pd.DataFrame] = {}
    perda_quantilica_por_alpha: dict[float, float] = {}

    for alpha_candidato in GRADE_DE_ALPHA:
        previsoes_do_candidato = rodar_walk_forward_do_lasso(
            tabela, colunas_do_modelo, horizonte, braco, alpha_candidato
        )
        previsoes_por_alpha[alpha_candidato] = previsoes_do_candidato

        na_calibracao_epidemica = previsoes_do_candidato[
            (previsoes_do_candidato["data_alvo"] >= INICIO_CALIBRACAO_EPIDEMICA)
            & (previsoes_do_candidato["data_alvo"] < INICIO_DA_AVALIACAO)
        ]
        perda_quantilica_por_alpha[alpha_candidato] = calcular_perda_quantilica_085(
            na_calibracao_epidemica["real"], na_calibracao_epidemica["previsto"]
        )

    alpha_escolhido = escolher_alpha_de_menor_perda(perda_quantilica_por_alpha)
    return ResultadoDaSelecaoDeAlpha(
        alpha_escolhido=alpha_escolhido,
        previsoes=previsoes_por_alpha[alpha_escolhido],
        perda_quantilica_por_alpha=perda_quantilica_por_alpha,
    )


def contar_colunas_zeradas_na_ultima_origem(
    tabela: pd.DataFrame, colunas_do_modelo: list[str], horizonte: int, braco: BracoLasso, alpha: float
) -> int:
    """Quantas colunas o LASSO zera, ajustado uma vez na última origem do horizonte.

    Reproduz o mesmo recorte de treino que `rodar_walk_forward_customizado`
    usa na última iteração, mas ajusta o modelo uma única vez para poder
    inspecionar `coef_` — o walk-forward reusado não expõe o modelo treinado
    de cada corte, só a previsão.

    Args:
        tabela: Tabela já com as features do braço.
        colunas_do_modelo: As colunas do braço.
        horizonte: h, em semanas.
        braco: 'lasso' ou 'lasso_M0'.
        alpha: Penalização L1 já escolhida para este horizonte.

    Returns:
        Quantas colunas ficaram com coeficiente exatamente zero (dentro da
        tolerância numérica), no ajuste da última origem.
    """
    coluna_alvo = harness.CIDADE_REFERENCIA.coluna_alvo
    dados_do_horizonte = harness.construir_alvo_horizonte(tabela, coluna_alvo, horizonte)
    features_com_sazonalidade = colunas_do_modelo + ["alvo_sin", "alvo_cos"]

    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    ultimo_indice_de_corte = list(
        range(
            harness.CIDADE_REFERENCIA.minimo_semanas_treino,
            len(dados_validos),
            harness.CIDADE_REFERENCIA.passo,
        )
    )[-1]
    teste = dados_validos.iloc[ultimo_indice_de_corte : ultimo_indice_de_corte + 1]
    data_do_teste = teste["data"].to_numpy()[0]
    treino = harness.corte_temporal.selecionar_treino_ja_respondido(dados_validos, data_do_teste, horizonte)

    modelo = construir_fabrica_de_modelo_lasso(alpha)(colunas_do_modelo)
    modelo.fit(treino[features_com_sazonalidade], treino["y_h"])

    coeficientes = modelo._regressor.coef_  # noqa: SLF001 — diagnostico interno, so leitura.
    colunas_zeradas = np.abs(coeficientes) < TOLERANCIA_NUMERICA_DE_COEFICIENTE_ZERO
    return int(np.sum(colunas_zeradas))


# ============================================================================
# SMOKE TEST
# ============================================================================


def rodar_smoke_test(tabela_bruta: pd.DataFrame) -> None:
    """--smoke: os 2 braços x 4 horizontes, últimas 5 origens, alpha demonstrativo fixo.

    Não roda a grade de alpha: 5 origens em 2026 não alcançam a janela de
    calibração (2022–2024) que a escolha de alpha exige. Usa
    `ALPHA_DEMONSTRATIVO_DO_SMOKE` só para provar que o walk-forward e o
    modelo rodam sem erro — a escolha de verdade é exercida em
    `--provar-equivalencia` (alpha=0) e na bateria completa.
    """
    for braco in BRACOS_LASSO:
        tabela, colunas_do_modelo = montar_features_do_braco_lasso(tabela_bruta, braco)
        print(f"\n[smoke] {braco.nome}  ({len(colunas_do_modelo)} colunas)", flush=True)

        for horizonte in HORIZONTES_DA_BATERIA:
            inicio = time.perf_counter()
            previsoes = rodar_walk_forward_do_lasso(
                tabela, colunas_do_modelo, horizonte, braco,
                ALPHA_DEMONSTRATIVO_DO_SMOKE, limite_de_ultimas_origens=N_ORIGENS_DO_SMOKE,
            )
            duracao = time.perf_counter() - inicio
            print(f"  h={horizonte}", flush=True)
            print(previsoes.to_string(index=False), flush=True)
            print(f"  [smoke] {braco.nome} h={horizonte}  {duracao:.2f}s", flush=True)

    print("\n[smoke] TODOS OS BRACOS E HORIZONTES RODARAM SEM ERRO.", flush=True)


# ============================================================================
# EQUIVALÊNCIA COM O V5 (alpha=0)
# ============================================================================


def carregar_previsoes_do_v5(caminho: pathlib.Path, horizonte: int) -> pd.DataFrame:
    """Lê as previsões já certificadas do V5_linear_log, num horizonte."""
    if not caminho.exists():
        raise FileNotFoundError(f"Previsoes do V5 nao encontradas: {caminho}")

    previsoes_de_todos_os_bracos = pd.read_csv(caminho, parse_dates=["data_alvo"])
    previsoes_do_v5 = previsoes_de_todos_os_bracos[
        (previsoes_de_todos_os_bracos["braco"] == NOME_DO_BRACO_V5_NO_ARQUIVO)
        & (previsoes_de_todos_os_bracos["h"] == horizonte)
    ]
    return previsoes_do_v5.sort_values("data_alvo").reset_index(drop=True)


def provar_equivalencia_com_v5(tabela_bruta: pd.DataFrame) -> None:
    """Prova que este LASSO com alpha=0 reproduz o V5_linear_log em h=12.

    Compara as últimas 20 origens com `np.testing.assert_allclose`, rtol=1e-8
    — exigência explícita do brief desta bateria.

    Raises:
        AssertionError: Se as datas ou as previsões divergirem.
    """
    horizonte = 12
    braco_lasso = BRACOS_LASSO[0]
    if braco_lasso.nome != NOME_DO_BRACO_LASSO:
        raise ValueError("BRACOS_LASSO[0] deveria ser o braco 'lasso' (com vetor).")

    tabela, colunas_do_modelo = montar_features_do_braco_lasso(tabela_bruta, braco_lasso)

    print("\n[equivalencia] rodando LASSO alpha=0 (h=12, todas as origens)...", flush=True)
    inicio = time.perf_counter()
    previsoes_alpha_zero = rodar_walk_forward_do_lasso(
        tabela, colunas_do_modelo, horizonte, braco_lasso, ALPHA_DA_EQUIVALENCIA_COM_V5
    )
    duracao = time.perf_counter() - inicio
    print(f"[equivalencia] {len(previsoes_alpha_zero)} origens, {duracao:.1f}s", flush=True)

    previsoes_do_v5 = carregar_previsoes_do_v5(CAMINHO_V5_LINEAR_LOG, horizonte)

    ultimas_do_lasso = previsoes_alpha_zero.tail(ULTIMAS_ORIGENS_DA_EQUIVALENCIA).reset_index(drop=True)
    ultimas_do_v5 = previsoes_do_v5.tail(ULTIMAS_ORIGENS_DA_EQUIVALENCIA).reset_index(drop=True)

    pd.testing.assert_series_equal(
        ultimas_do_lasso["data_alvo"], ultimas_do_v5["data_alvo"], check_names=False,
    )
    np.testing.assert_allclose(
        ultimas_do_lasso["previsto"].to_numpy(),
        ultimas_do_v5["previsto"].to_numpy(),
        rtol=TOLERANCIA_RELATIVA_DA_EQUIVALENCIA,
    )
    print(
        "[equivalencia] OK — LASSO alpha=0 == V5_linear_log "
        f"(ultimas {ULTIMAS_ORIGENS_DA_EQUIVALENCIA} origens, h=12, rtol={TOLERANCIA_RELATIVA_DA_EQUIVALENCIA})."
    )


# ============================================================================
# CRONÔMETRO
# ============================================================================


def cronometrar_celula_completa(
    tabela_bruta: pd.DataFrame, braco: BracoLasso, horizonte: int, alpha: float
) -> tuple[pd.DataFrame, float]:
    """Roda uma célula completa (um alpha fixo, todas as origens) e cronometra."""
    tabela, colunas_do_modelo = montar_features_do_braco_lasso(tabela_bruta, braco)
    inicio = time.perf_counter()
    previsoes = rodar_walk_forward_do_lasso(tabela, colunas_do_modelo, horizonte, braco, alpha)
    duracao = time.perf_counter() - inicio
    return previsoes, duracao


# ============================================================================
# BATERIA COMPLETA (não executada nesta entrega — só implementada)
# ============================================================================


def rodar_bateria_completa(tabela_bruta: pd.DataFrame) -> None:
    """Roda os 2 braços x 4 horizontes com a grade de alpha e grava `previsoes_lasso.csv`.

    ⚠️ NÃO EXECUTADO nesta entrega — o brief pediu só smoke test, prova de
    equivalência e cronômetro. Ver `desvios_e_decisoes` no retorno estruturado
    da tarefa.
    """
    previsoes_de_tudo: list[pd.DataFrame] = []
    resumo_dos_alphas: list[dict[str, object]] = []

    for braco in BRACOS_LASSO:
        tabela, colunas_do_modelo = montar_features_do_braco_lasso(tabela_bruta, braco)

        for horizonte in HORIZONTES_DA_BATERIA:
            marca = time.perf_counter()
            resultado_da_selecao = selecionar_alpha_e_previsoes(tabela, colunas_do_modelo, braco, horizonte)
            n_colunas_zeradas = contar_colunas_zeradas_na_ultima_origem(
                tabela, colunas_do_modelo, horizonte, braco, resultado_da_selecao.alpha_escolhido
            )

            previsoes_do_braco = resultado_da_selecao.previsoes.copy()
            previsoes_do_braco["braco"] = braco.nome
            previsoes_de_tudo.append(previsoes_do_braco)

            resumo_dos_alphas.append(
                {
                    "braco": braco.nome,
                    "h": horizonte,
                    "alpha_escolhido": resultado_da_selecao.alpha_escolhido,
                    "n_colunas_zeradas_ultima_origem": n_colunas_zeradas,
                    "n_colunas_do_modelo": len(colunas_do_modelo),
                    **{
                        f"perda_alpha_{alpha}": perda
                        for alpha, perda in resultado_da_selecao.perda_quantilica_por_alpha.items()
                    },
                }
            )
            print(
                f"[{braco.nome}] h={horizonte:2d}  alpha={resultado_da_selecao.alpha_escolhido}  "
                f"{n_colunas_zeradas}/{len(colunas_do_modelo)} colunas zeradas  "
                f"{time.perf_counter() - marca:6.1f}s",
                flush=True,
            )

    todas_as_previsoes = pd.concat(previsoes_de_tudo, ignore_index=True)
    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    todas_as_previsoes.to_csv(PASTA_DE_SAIDAS / "previsoes_lasso.csv", index=False)
    pd.DataFrame(resumo_dos_alphas).to_csv(PASTA_DE_SAIDAS / "alphas_escolhidos_lasso.csv", index=False)
    print(f"Gravado: previsoes_lasso.csv ({len(todas_as_previsoes)} linhas)", flush=True)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--provar-equivalencia", action="store_true", dest="provar_equivalencia")
    parser.add_argument("--cronometro", action="store_true")
    parser.add_argument("--rodar-tudo", action="store_true", dest="rodar_tudo")
    argumentos = parser.parse_args()

    nenhuma_acao_pedida = not any(
        [argumentos.smoke, argumentos.provar_equivalencia, argumentos.cronometro, argumentos.rodar_tudo]
    )
    if nenhuma_acao_pedida:
        parser.print_help()
        return

    tabela_bruta = harness.carregar_tabela_bruta()

    if argumentos.smoke:
        rodar_smoke_test(tabela_bruta)

    if argumentos.provar_equivalencia:
        provar_equivalencia_com_v5(tabela_bruta)

    if argumentos.cronometro:
        braco_lasso = BRACOS_LASSO[0]
        previsoes, duracao = cronometrar_celula_completa(
            tabela_bruta, braco_lasso, HORIZONTE_DO_CRONOMETRO, ALPHA_DEMONSTRATIVO_DO_SMOKE
        )
        PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
        previsoes.to_csv(PASTA_DE_SAIDAS / f"cronometro_lasso_h{HORIZONTE_DO_CRONOMETRO}.csv", index=False)
        print(
            f"[cronometro] {braco_lasso.nome} h={HORIZONTE_DO_CRONOMETRO}, alpha={ALPHA_DEMONSTRATIVO_DO_SMOKE}, "
            f"{len(previsoes)} origens: {duracao:.1f}s ({duracao / max(len(previsoes), 1):.3f}s/origem)"
        )

    if argumentos.rodar_tudo:
        rodar_bateria_completa(tabela_bruta)


if __name__ == "__main__":
    main()
