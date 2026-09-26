"""Rodada A da segunda bateria noturna — os resultados principais em 2026.

Protocolo pre-declarado em `../PRE_DECLARACAO.md`, secao A (com as duas emendas de
25/09/2026, 23h30 e 23h50). Este script NAO re-treina nada por conta propria: ele
reusa o motor `harness.py` da bateria noturna de 23/09/2026 (nao alterado) para
rodar o walk-forward dos 8 bracos, e acrescenta:

  - uma trava propria, com as ancoras RECALCULADAS na tabela oficial atualizada
    (97,4 em h=1 e 280,0 em h=12, ate 01/02/2026 - ver o adendo da
    `2026-09-25_atualizacao_dados_2026/CERTIFICACAO.md`);
  - a regua sazonal (repete o caso de 52 semanas antes), que nao e um modelo e
    por isso nao passa pelo harness;
  - as familias A1 (vetor com folha 20) e A2 (modelo contra a regua), com
    Wilcoxon pareado e Holm;
  - a contagem descritiva de alarmes falsos (A3).

⚠️ NAO altera `harness.py`, nem os blocos da bateria de 23/09, nem nenhuma outra
analise. So le. Grava so dentro desta pasta (`saidas/`).
"""

import dataclasses
import logging
import pathlib
import sys

import matplotlib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend precisa ser fixado antes)

# ---------------------------------------------------------------------------
# CAMINHOS
# ---------------------------------------------------------------------------

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DA_BATERIA_NOTURNA_23_09 = PASTA_DESTE_ARQUIVO.parent.parent / "2026-09-23_bateria_noturna"
PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

sys.path.insert(0, str(PASTA_DA_BATERIA_NOTURNA_23_09))
import harness  # noqa: E402  motor da bateria noturna de 23/09, SO LEITURA.
from config.modelo import EspecificacaoModelo  # noqa: E402


# ---------------------------------------------------------------------------
# OS MODELOS DOS OUTROS BRACOS (folha 20, LightGBM, GradientBoosting)
#
# Hiperparametros copiados literalmente de
# `bloco_5_algoritmos/rodar.py:34-62` e `bloco_7_vetor_com_folha_20/rodar.py:30-42`,
# conferidos linha a linha contra os arquivos originais. Nao sao reimportados
# por modulo dinamico para manter este script auditavel sem depender de efeitos
# colaterais de outro arquivo; a fonte da verdade dos hiperparametros continua
# sendo aqueles dois arquivos, que nao foram alterados.
# ---------------------------------------------------------------------------

QUANTIL_DE_REFERENCIA = 0.85

HISTGB_FOLHA_20 = EspecificacaoModelo(
    nome="histgb_folha20",
    classe=HistGradientBoostingRegressor,
    parametros={
        "max_iter": 250,
        "learning_rate": 0.05,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 20,
        "random_state": 42,
        "loss": "quantile",
        "quantile": QUANTIL_DE_REFERENCIA,
    },
)

GRADIENT_BOOSTING_QUANTIL = EspecificacaoModelo(
    nome="gradient_boosting_quantil",
    classe=GradientBoostingRegressor,
    parametros={
        "n_estimators": 250,
        "learning_rate": 0.05,
        "max_depth": 3,
        "min_samples_leaf": 5,
        "random_state": 42,
        "loss": "quantile",
        "alpha": QUANTIL_DE_REFERENCIA,
    },
)

LIGHTGBM_QUANTIL = EspecificacaoModelo(
    nome="lightgbm_quantil",
    classe=LGBMRegressor,
    parametros={
        "n_estimators": 300,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_child_samples": 20,
        "verbose": -1,
        "n_jobs": -1,
        "random_state": 42,
        "objective": "quantile",
        "alpha": QUANTIL_DE_REFERENCIA,
    },
)


# ---------------------------------------------------------------------------
# OS 8 BRACOS DA SEGUNDA BATERIA + a regua sazonal (nao e um braco de modelo)
# ---------------------------------------------------------------------------

NOME_CENARIO_ADOTADO = "HistGB_M1"
NOME_HISTGB_FOLHA20_M1 = "HistGB_folha20_M1"
NOME_REGUA_SAZONAL = "regua_sazonal"

BRACOS = (
    harness.Braco(NOME_CENARIO_ADOTADO, descricao="cenario adotado: HistGB folha 5, com vetor"),
    harness.Braco("HistGB_M0", sem_vetor=True, descricao="HistGB folha 5, sem vetor"),
    harness.Braco(
        NOME_HISTGB_FOLHA20_M1, modelo=HISTGB_FOLHA_20, descricao="HistGB folha 20, com vetor"
    ),
    harness.Braco(
        "HistGB_folha20_M0", modelo=HISTGB_FOLHA_20, sem_vetor=True,
        descricao="HistGB folha 20, sem vetor",
    ),
    harness.Braco("LightGBM_M1", modelo=LIGHTGBM_QUANTIL, descricao="LightGBM, com vetor"),
    harness.Braco(
        "LightGBM_M0", modelo=LIGHTGBM_QUANTIL, sem_vetor=True, descricao="LightGBM, sem vetor"
    ),
    harness.Braco("GradBoost_M1", modelo=GRADIENT_BOOSTING_QUANTIL, descricao="GradBoost, com vetor"),
    harness.Braco(
        "GradBoost_M0", modelo=GRADIENT_BOOSTING_QUANTIL, sem_vetor=True,
        descricao="GradBoost, sem vetor",
    ),
)

HORIZONTES_DO_PROJETO = tuple(range(1, 13))


# ---------------------------------------------------------------------------
# TRAVA — ancoras recalculadas na tabela oficial atualizada (emenda de 25/09,
# 23h50). NAO usa `harness.conferir_trava_de_validacao`: aquela funcao trava
# contra o PAINEL PUBLICADO antigo (98,0/278,7), sem teto de data. Aqui o teto
# e 01/02/2026 e as ancoras sao as novas.
# ---------------------------------------------------------------------------

FIM_DA_TRAVA = pd.Timestamp("2026-02-01")
TOLERANCIA_DA_TRAVA = 0.2
ANCORAS_DA_TRAVA = {1: 97.4, 12: 280.0}


def conferir_trava_segunda_bateria(previsoes: pd.DataFrame) -> tuple[bool, pd.DataFrame]:
    """Confere o cenario adotado contra as ancoras recalculadas de 25/09/2026.

    Reproduz, para cada horizonte, o MAE do braco `HistGB_M1` nas semanas
    `harness.INICIO_DA_AVALIACAO <= data_alvo <= FIM_DA_TRAVA`. Em h=1 e h=12
    o valor precisa bater a ancora com tolerancia `TOLERANCIA_DA_TRAVA`; em
    h=4 e h=8 nao ha ancora publicada ainda — o valor e so registrado, como
    pede a pre-declaracao.

    Args:
        previsoes: Previsoes de todos os bracos, saida de
            `harness.executar_bateria`.

    Returns:
        Uma tupla (trava_valida, tabela_de_registro). `trava_valida` e True
        somente se h=1 e h=12 baterem dentro da tolerancia.
    """
    do_cenario_adotado = previsoes[
        (previsoes["braco"] == NOME_CENARIO_ADOTADO)
        & (previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO)
        & (previsoes["data_alvo"] <= FIM_DA_TRAVA)
    ]

    linhas_de_registro = []
    trava_valida = True

    for horizonte in HORIZONTES_DO_PROJETO:
        do_horizonte = do_cenario_adotado[do_cenario_adotado["h"] == horizonte]
        if do_horizonte.empty:
            continue

        mae_medido = mean_absolute_error(do_horizonte["real"], do_horizonte["previsto"])
        ancora = ANCORAS_DA_TRAVA.get(horizonte)

        if ancora is None:
            bate = None
        else:
            bate = abs(mae_medido - ancora) < TOLERANCIA_DA_TRAVA
            trava_valida = trava_valida and bate

        linhas_de_registro.append(
            {
                "h": horizonte,
                "mae_medido": mae_medido,
                "ancora": ancora,
                "n_semanas": len(do_horizonte),
                "bate_a_tolerancia": bate,
            }
        )

    tabela_de_registro = pd.DataFrame(linhas_de_registro)
    print("\nTRAVA — cenario adotado, ate 01/02/2026, tabela oficial atualizada")
    print(tabela_de_registro.to_string(index=False))
    print(f"veredito h=1/h=12: {'VALIDA' if trava_valida else 'INVALIDA'}")
    return trava_valida, tabela_de_registro


# ---------------------------------------------------------------------------
# REGUA SAZONAL — repete o caso confirmado de 52 semanas antes da data_alvo.
#
# Formula identica a `calcular_regra_sazonal` de
# `../../2026-09-25_regua_regras_simples/calcular_regua.py:514-534`. Copiada
# aqui (e nao importada) porque aquele script e uma analise completa, nao uma
# biblioteca, e a formula em si e as 10 linhas abaixo, ja revisadas naquele
# teste.
# ---------------------------------------------------------------------------

SEMANAS_DO_PASSO_SAZONAL = 52


def calcular_regra_sazonal(
    data_alvo: pd.Timestamp, casos_por_data: dict[pd.Timestamp, float]
) -> float:
    """O caso confirmado de exatamente 52 semanas antes de `data_alvo`.

    Args:
        data_alvo: Semana que esta sendo prevista.
        casos_por_data: Serie semanal de casos confirmados, indexada por data.

    Returns:
        `casos_confirmados` na semana `data_alvo - 52` semanas, ou NaN se essa
        semana nao tiver contagem fechada na serie.
    """
    semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    return casos_por_data.get(semana_um_ano_antes, np.nan)


def montar_casos_por_data(tabela_bruta: pd.DataFrame) -> dict[pd.Timestamp, float]:
    """Constroi o dicionario data -> casos_confirmados a partir da tabela bruta.

    `harness.carregar_tabela_bruta()` ja renomeia as colunas originais
    (`fontes.carregar_tabela_final`): a data fica em "data" e os casos em
    "casos". Ver `acesso/fontes.py:59-67`.

    Args:
        tabela_bruta: Saida de `harness.carregar_tabela_bruta()`.

    Returns:
        Dicionario indexado por data, com os casos confirmados (pode ser NaN
        nas semanas sem contagem fechada).
    """
    return dict(zip(tabela_bruta["data"], tabela_bruta["casos"]))


def adicionar_regua_sazonal(
    previsoes_dos_modelos: pd.DataFrame, casos_por_data: dict[pd.Timestamp, float]
) -> pd.DataFrame:
    """Acrescenta as linhas da regua sazonal ao conjunto de previsoes dos modelos.

    A grade (h, data_alvo) da regua e a UNIAO de todos os 8 bracos de modelo:
    isso garante que qualquer comparacao pareada modelo-x-regua encontre a
    data que precisar, sem depender de qual braco foi escolhido como grade.

    Args:
        previsoes_dos_modelos: Previsoes de todos os bracos de modelo (saida
            de `harness.executar_bateria`).
        casos_por_data: Serie semanal de casos confirmados, indexada por data.

    Returns:
        `previsoes_dos_modelos` com as linhas da regua sazonal acrescentadas
        (mesmas colunas: h, data_alvo, real, previsto, braco).
    """
    pares_unicos = previsoes_dos_modelos[["h", "data_alvo"]].drop_duplicates()

    linhas_da_regua = []
    for _, par in pares_unicos.iterrows():
        data_alvo = par["data_alvo"]
        linhas_da_regua.append(
            {
                "h": int(par["h"]),
                "data_alvo": data_alvo,
                "real": casos_por_data.get(data_alvo, np.nan),
                "previsto": calcular_regra_sazonal(data_alvo, casos_por_data),
                "braco": NOME_REGUA_SAZONAL,
            }
        )

    previsoes_da_regua = pd.DataFrame(linhas_da_regua)
    print(f"Regua sazonal calculada para {len(previsoes_da_regua)} linhas (h, data_alvo) unicos.")
    return pd.concat([previsoes_dos_modelos, previsoes_da_regua], ignore_index=True)


# ---------------------------------------------------------------------------
# RECORTES TEMPORAIS
#
# "2024-2025" e "2026" NAO particionam tudo (existe dado de 2018-2023 fora
# dos dois). "tudo" e o walk-forward inteiro, sem filtro de data_alvo -
# decisao registrada no retorno estruturado, por ambiguidade do brief.
# ---------------------------------------------------------------------------

INICIO_RECORTE_2024_2025 = pd.Timestamp("2024-01-01")
FIM_RECORTE_2024_2025 = pd.Timestamp("2025-12-31")
INICIO_RECORTE_2026 = pd.Timestamp("2026-01-01")
FIM_RECORTE_2026 = pd.Timestamp("2026-04-19")

NOME_RECORTE_2024_2025 = "2024-2025"
NOME_RECORTE_2026 = "2026"
NOME_RECORTE_TUDO = "tudo"
NOMES_DOS_RECORTES = (NOME_RECORTE_2024_2025, NOME_RECORTE_2026, NOME_RECORTE_TUDO)


def selecionar_recorte(medicoes: pd.DataFrame, nome_do_recorte: str) -> pd.DataFrame:
    """Filtra as medicoes pelo recorte temporal pedido.

    Args:
        medicoes: DataFrame com a coluna data_alvo.
        nome_do_recorte: Um de "2024-2025", "2026" ou "tudo".

    Returns:
        As linhas de `medicoes` dentro do recorte.

    Raises:
        ValueError: Se o nome do recorte nao for reconhecido.
    """
    if nome_do_recorte == NOME_RECORTE_2024_2025:
        dentro_do_inicio = medicoes["data_alvo"] >= INICIO_RECORTE_2024_2025
        dentro_do_fim = medicoes["data_alvo"] <= FIM_RECORTE_2024_2025
        return medicoes[dentro_do_inicio & dentro_do_fim]

    if nome_do_recorte == NOME_RECORTE_2026:
        dentro_do_inicio = medicoes["data_alvo"] >= INICIO_RECORTE_2026
        dentro_do_fim = medicoes["data_alvo"] <= FIM_RECORTE_2026
        return medicoes[dentro_do_inicio & dentro_do_fim]

    if nome_do_recorte == NOME_RECORTE_TUDO:
        return medicoes

    raise ValueError(f"Recorte desconhecido: {nome_do_recorte}")


# ---------------------------------------------------------------------------
# METRICAS.CSV — MAE descritivo por braco, horizonte e recorte
# ---------------------------------------------------------------------------


def montar_metricas_por_recorte(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE de cada braco (e da regua), em cada horizonte e recorte.

    Args:
        previsoes: Previsoes de todos os bracos, com a regua ja acrescentada.

    Returns:
        Uma linha por (braco, h, recorte), com mae e n de semanas usadas
        (linhas com `previsto` vazio, como pode acontecer na regua sazonal
        nas primeiras 52 semanas da serie, sao excluidas do calculo do MAE).
    """
    linhas_da_tabela = []
    bracos_distintos = sorted(previsoes["braco"].unique())

    for braco in bracos_distintos:
        do_braco = previsoes[previsoes["braco"] == braco]

        for horizonte in HORIZONTES_DO_PROJETO:
            do_horizonte = do_braco[do_braco["h"] == horizonte]

            for nome_do_recorte in NOMES_DOS_RECORTES:
                do_recorte = selecionar_recorte(do_horizonte, nome_do_recorte)
                do_recorte_valido = do_recorte.dropna(subset=["previsto", "real"])

                if len(do_recorte_valido) == 0:
                    mae = np.nan
                else:
                    mae = mean_absolute_error(
                        do_recorte_valido["real"], do_recorte_valido["previsto"]
                    )

                linhas_da_tabela.append(
                    {
                        "braco": braco,
                        "h": horizonte,
                        "recorte": nome_do_recorte,
                        "mae": mae,
                        "n_semanas": len(do_recorte_valido),
                    }
                )

    return pd.DataFrame(linhas_da_tabela)


# ---------------------------------------------------------------------------
# FAMILIA A1 — com folha minima 20, o vetor reduz o erro de 3 meses?
#   Pares M1 x M0 no HistGB folha 20 e no LightGBM, em h=8 e h=12.
#   Decisao pre-declarada (recorte "2026"): confirma se MAE(M1) < MAE(M0) nos
#   DOIS algoritmos em h=12, com p de Holm < 0,05.
# ---------------------------------------------------------------------------

PARES_DO_VETOR_FOLHA_20 = (
    ("HistGB_folha20_M1", "HistGB_folha20_M0"),
    ("LightGBM_M1", "LightGBM_M0"),
)
HORIZONTES_A1 = (8, 12)
NIVEL_DE_SIGNIFICANCIA = 0.05


def comparar_par_pareado(
    previsoes: pd.DataFrame, nome_com_vetor: str, nome_sem_vetor: str, horizonte: int
) -> dict[str, object]:
    """Compara um par (com vetor, sem vetor) num horizonte, pareado por data_alvo.

    Args:
        previsoes: Previsoes ja restritas ao recorte de interesse.
        nome_com_vetor: Nome do braco M1 (com as colunas de vetor).
        nome_sem_vetor: Nome do braco M0 (sem as colunas de vetor).
        horizonte: Horizonte h da comparacao.

    Returns:
        Um dicionario com as MAE dos dois lados, a reducao percentual do
        vetor (positivo = com vetor errou menos), o p bruto de Wilcoxon e o
        numero de semanas pareadas. Vazio (todas as chaves com None) se nao
        houver nenhuma semana em comum.
    """
    do_horizonte = previsoes[previsoes["h"] == horizonte]
    do_com_vetor = do_horizonte[do_horizonte["braco"] == nome_com_vetor]
    do_sem_vetor = do_horizonte[do_horizonte["braco"] == nome_sem_vetor]

    pareado = do_com_vetor.merge(
        do_sem_vetor, on="data_alvo", suffixes=("_com_vetor", "_sem_vetor")
    )
    if pareado.empty:
        return {
            "com_vetor": nome_com_vetor,
            "sem_vetor": nome_sem_vetor,
            "horizonte": horizonte,
            "mae_com_vetor": np.nan,
            "mae_sem_vetor": np.nan,
            "reducao_percentual_do_vetor": np.nan,
            "p_bruto": np.nan,
            "n_pareado": 0,
        }

    erro_com_vetor = np.abs(pareado["real_com_vetor"] - pareado["previsto_com_vetor"])
    erro_sem_vetor = np.abs(pareado["real_sem_vetor"] - pareado["previsto_sem_vetor"])

    if np.allclose(erro_com_vetor, erro_sem_vetor):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_com_vetor, erro_sem_vetor)

    mae_com_vetor = float(np.mean(erro_com_vetor))
    mae_sem_vetor = float(np.mean(erro_sem_vetor))
    reducao_percentual_do_vetor = 100.0 * (mae_sem_vetor - mae_com_vetor) / mae_sem_vetor

    return {
        "com_vetor": nome_com_vetor,
        "sem_vetor": nome_sem_vetor,
        "horizonte": horizonte,
        "mae_com_vetor": mae_com_vetor,
        "mae_sem_vetor": mae_sem_vetor,
        "reducao_percentual_do_vetor": reducao_percentual_do_vetor,
        "p_bruto": float(p_bruto),
        "n_pareado": len(pareado),
    }


def corrigir_por_holm(p_brutos: list[float]) -> list[float]:
    """Correcao de Holm sobre uma familia de p-valores.

    Copia da mesma implementacao de `harness.corrigir_por_holm` /
    `2026-09-25_regua_regras_simples/calcular_regua.py:1035-1063`: ordena os p
    do menor para o maior e aplica o limiar crescente, com monotonia (o p
    corrigido de uma posicao nunca e menor que o da posicao anterior).

    Args:
        p_brutos: Todos os p-valores da familia, na ordem original.

    Returns:
        Os p-valores corrigidos, na MESMA ordem de `p_brutos`.
    """
    quantidade_de_testes = len(p_brutos)
    indices_ordenados_por_p = sorted(range(quantidade_de_testes), key=lambda i: p_brutos[i])

    p_corrigidos_na_ordem_original = [0.0] * quantidade_de_testes
    maior_p_ate_agora = 0.0

    for posicao, indice_original in enumerate(indices_ordenados_por_p):
        p_ajustado = min(1.0, p_brutos[indice_original] * (quantidade_de_testes - posicao))
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        p_corrigidos_na_ordem_original[indice_original] = maior_p_ate_agora

    return p_corrigidos_na_ordem_original


def montar_familia_a1(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Familia A1: o vetor com folha 20, nos dois algoritmos, em h=8 e h=12.

    A decisao pre-declarada usa SO o recorte "2026" (a familia de 4 exigida
    pelo protocolo). Os recortes "2024-2025" e "tudo" sao calculados tambem,
    como pede a tarefa, mas de forma descritiva: cada um recebe a SUA PROPRIA
    correcao de Holm sobre as suas 4 comparacoes, sem misturar com o recorte
    de decisao (misturar infla a familia alem do que foi pre-declarado).

    Args:
        previsoes: Previsoes de todos os bracos, com a regua ja acrescentada.

    Returns:
        Uma linha por (recorte, com_vetor, sem_vetor, horizonte), com o p de
        Holm calculado DENTRO do recorte.
    """
    linhas_de_todos_os_recortes = []

    for nome_do_recorte in NOMES_DOS_RECORTES:
        do_recorte = selecionar_recorte(previsoes, nome_do_recorte)

        comparacoes_do_recorte = []
        for nome_com_vetor, nome_sem_vetor in PARES_DO_VETOR_FOLHA_20:
            for horizonte in HORIZONTES_A1:
                comparacoes_do_recorte.append(
                    comparar_par_pareado(do_recorte, nome_com_vetor, nome_sem_vetor, horizonte)
                )

        p_brutos = [c["p_bruto"] for c in comparacoes_do_recorte]
        p_holm = corrigir_por_holm(p_brutos)

        for comparacao, p_holm_da_linha in zip(comparacoes_do_recorte, p_holm):
            linha = dict(comparacao)
            linha["recorte"] = nome_do_recorte
            linha["p_holm"] = p_holm_da_linha
            linha["significativo_5pct"] = p_holm_da_linha < NIVEL_DE_SIGNIFICANCIA
            linhas_de_todos_os_recortes.append(linha)

    tabela = pd.DataFrame(linhas_de_todos_os_recortes)

    print("\nFAMILIA A1 — vetor com folha 20 (recorte de decisao: '2026')")
    print(
        tabela[
            ["recorte", "com_vetor", "horizonte", "mae_com_vetor", "mae_sem_vetor",
             "reducao_percentual_do_vetor", "p_holm", "significativo_5pct"]
        ].to_string(index=False)
    )

    do_recorte_2026 = tabela[tabela["recorte"] == NOME_RECORTE_2026]
    do_h12 = do_recorte_2026[do_recorte_2026["horizonte"] == 12]
    a1_confirma = bool(
        (do_h12["mae_com_vetor"] < do_h12["mae_sem_vetor"]).all()
        and (do_h12["significativo_5pct"]).all()
    )
    print(f"VEREDITO A1 (recorte 2026, h=12, os dois algoritmos): {'CONFIRMA' if a1_confirma else 'NAO confirma'}")

    return tabela


# ---------------------------------------------------------------------------
# FAMILIA A2 — o modelo erra menos que a regua num ano atipico?
#   Pares (cenario adotado, regua) e (folha 20 M1, regua), em h=4 e h=12.
# ---------------------------------------------------------------------------

PARES_MODELO_CONTRA_REGUA = (
    (NOME_CENARIO_ADOTADO, NOME_REGUA_SAZONAL),
    (NOME_HISTGB_FOLHA20_M1, NOME_REGUA_SAZONAL),
)
HORIZONTES_A2 = (4, 12)


def comparar_modelo_contra_regua(
    previsoes: pd.DataFrame, nome_do_modelo: str, nome_da_regua: str, horizonte: int
) -> dict[str, object]:
    """Compara um modelo contra a regua sazonal num horizonte, pareado por data_alvo.

    Linhas em que a regua nao tem previsao (as primeiras 52 semanas da serie)
    saem do pareamento, porque o merge e por data_alvo com ambos os lados
    exigindo previsto nao vazio.

    Args:
        previsoes: Previsoes ja restritas ao recorte de interesse.
        nome_do_modelo: Braco de modelo a testar.
        nome_da_regua: Nome do braco da regua sazonal.
        horizonte: Horizonte h da comparacao.

    Returns:
        Dicionario com as MAE dos dois lados, a reducao percentual do modelo
        sobre a regua (positivo = modelo errou menos), p bruto e n pareado.
    """
    do_horizonte = previsoes[previsoes["h"] == horizonte]
    do_modelo = do_horizonte[do_horizonte["braco"] == nome_do_modelo].dropna(subset=["previsto"])
    da_regua = do_horizonte[do_horizonte["braco"] == nome_da_regua].dropna(subset=["previsto"])

    pareado = do_modelo.merge(da_regua, on="data_alvo", suffixes=("_modelo", "_regua"))
    if pareado.empty:
        return {
            "modelo": nome_do_modelo,
            "regua": nome_da_regua,
            "horizonte": horizonte,
            "mae_modelo": np.nan,
            "mae_regua": np.nan,
            "reducao_percentual_do_modelo": np.nan,
            "p_bruto": np.nan,
            "n_pareado": 0,
        }

    erro_do_modelo = np.abs(pareado["real_modelo"] - pareado["previsto_modelo"])
    erro_da_regua = np.abs(pareado["real_regua"] - pareado["previsto_regua"])

    if np.allclose(erro_do_modelo, erro_da_regua):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_do_modelo, erro_da_regua)

    mae_modelo = float(np.mean(erro_do_modelo))
    mae_regua = float(np.mean(erro_da_regua))
    reducao_percentual_do_modelo = 100.0 * (mae_regua - mae_modelo) / mae_regua

    return {
        "modelo": nome_do_modelo,
        "regua": nome_da_regua,
        "horizonte": horizonte,
        "mae_modelo": mae_modelo,
        "mae_regua": mae_regua,
        "reducao_percentual_do_modelo": reducao_percentual_do_modelo,
        "p_bruto": float(p_bruto),
        "n_pareado": len(pareado),
    }


def montar_familia_a2(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Familia A2: modelo contra a regua sazonal, em h=4 e h=12.

    Mesma logica de recortes da familia A1: decisao no recorte "2026", Holm
    calculado separadamente dentro de cada recorte.

    Args:
        previsoes: Previsoes de todos os bracos, com a regua ja acrescentada.

    Returns:
        Uma linha por (recorte, modelo, horizonte).
    """
    linhas_de_todos_os_recortes = []

    for nome_do_recorte in NOMES_DOS_RECORTES:
        do_recorte = selecionar_recorte(previsoes, nome_do_recorte)

        comparacoes_do_recorte = []
        for nome_do_modelo, nome_da_regua in PARES_MODELO_CONTRA_REGUA:
            for horizonte in HORIZONTES_A2:
                comparacoes_do_recorte.append(
                    comparar_modelo_contra_regua(do_recorte, nome_do_modelo, nome_da_regua, horizonte)
                )

        p_brutos = [c["p_bruto"] for c in comparacoes_do_recorte]
        p_holm = corrigir_por_holm(p_brutos)

        for comparacao, p_holm_da_linha in zip(comparacoes_do_recorte, p_holm):
            linha = dict(comparacao)
            linha["recorte"] = nome_do_recorte
            linha["p_holm"] = p_holm_da_linha
            linha["significativo_5pct"] = p_holm_da_linha < NIVEL_DE_SIGNIFICANCIA
            linhas_de_todos_os_recortes.append(linha)

    tabela = pd.DataFrame(linhas_de_todos_os_recortes)

    print("\nFAMILIA A2 — modelo contra a regua sazonal (recorte de decisao: '2026')")
    print(
        tabela[
            ["recorte", "modelo", "horizonte", "mae_modelo", "mae_regua",
             "reducao_percentual_do_modelo", "p_holm", "significativo_5pct"]
        ].to_string(index=False)
    )

    return tabela


# ---------------------------------------------------------------------------
# A3 — alarmes falsos em 2026, descritivo (sem teste de hipotese)
#
# Evento de alarme: previsto > limiar (mesma direcao de
# `2026-09-25_alarme_contra_canal_endemico/rodar.py:564`, `previsto > limite`).
# Os 4 limiares sao cruzados com os 4 horizontes (nao ha uma correspondencia
# 1-para-1 no brief nem na pre-declaracao: 421 e 702 sao definidos como "corte
# de uma semana so", sem amarrar a um horizonte especifico) — decisao
# registrada no retorno estruturado.
# ---------------------------------------------------------------------------

LIMIARES_DE_ALARME = (100.0, 140.0, 421.0, 702.0)


def montar_alarmes_2026(previsoes: pd.DataFrame) -> pd.DataFrame:
    """Conta alarmes emitidos e alarmes falsos em 2026, por braco/limiar/h.

    Alarme falso: o braco previu acima do limiar, mas o real ficou no limiar
    ou abaixo. So entram linhas com `previsto` e `real` nao vazios.

    Args:
        previsoes: Previsoes de todos os bracos, com a regua ja acrescentada.

    Returns:
        Uma linha por (braco, limiar, h), com contagens de alarmes emitidos,
        alarmes falsos, verdadeiros positivos e surtos reais no recorte 2026.
    """
    do_recorte_2026 = selecionar_recorte(previsoes, NOME_RECORTE_2026)
    bracos_distintos = sorted(do_recorte_2026["braco"].unique())

    linhas_da_tabela = []
    for braco in bracos_distintos:
        do_braco = do_recorte_2026[do_recorte_2026["braco"] == braco]

        for horizonte in HORIZONTES_DO_PROJETO:
            do_horizonte = do_braco[do_braco["h"] == horizonte].dropna(subset=["previsto", "real"])

            for limiar in LIMIARES_DE_ALARME:
                alarme_emitido = do_horizonte["previsto"] > limiar
                surto_real = do_horizonte["real"] > limiar

                n_alarmes_emitidos = int(alarme_emitido.sum())
                n_surtos_reais = int(surto_real.sum())
                n_verdadeiros_positivos = int((alarme_emitido & surto_real).sum())
                n_alarmes_falsos = int((alarme_emitido & ~surto_real).sum())

                linhas_da_tabela.append(
                    {
                        "braco": braco,
                        "h": horizonte,
                        "limiar": limiar,
                        "n_semanas": len(do_horizonte),
                        "n_alarmes_emitidos": n_alarmes_emitidos,
                        "n_alarmes_falsos": n_alarmes_falsos,
                        "n_verdadeiros_positivos": n_verdadeiros_positivos,
                        "n_surtos_reais": n_surtos_reais,
                    }
                )

    return pd.DataFrame(linhas_da_tabela)


# ---------------------------------------------------------------------------
# FIGURA — real x previsto em 2026, um painel por horizonte
# ---------------------------------------------------------------------------

BRACOS_DA_FIGURA = (NOME_CENARIO_ADOTADO, NOME_HISTGB_FOLHA20_M1, NOME_REGUA_SAZONAL)
HORIZONTES_DA_FIGURA = (1, 4, 8, 12)


def gerar_figura_2026(previsoes: pd.DataFrame, caminho_da_figura: pathlib.Path) -> None:
    """Gera um painel 2x2 (um por horizonte) com o real e 3 bracos, em 2026.

    Args:
        previsoes: Previsoes de todos os bracos, com a regua ja acrescentada.
        caminho_da_figura: Onde salvar o PNG.
    """
    do_recorte_2026 = selecionar_recorte(previsoes, NOME_RECORTE_2026)

    figura, eixos = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    eixos_em_sequencia = eixos.flatten()

    for indice, horizonte in enumerate(HORIZONTES_DA_FIGURA):
        eixo = eixos_em_sequencia[indice]
        do_horizonte = do_recorte_2026[do_recorte_2026["h"] == horizonte]

        do_cenario_adotado = do_horizonte[do_horizonte["braco"] == NOME_CENARIO_ADOTADO]
        if not do_cenario_adotado.empty:
            eixo.plot(
                do_cenario_adotado["data_alvo"], do_cenario_adotado["real"],
                color="black", linewidth=2, label="real",
            )

        for braco in BRACOS_DA_FIGURA:
            do_braco = do_horizonte[do_horizonte["braco"] == braco].dropna(subset=["previsto"])
            if do_braco.empty:
                continue
            eixo.plot(do_braco["data_alvo"], do_braco["previsto"], marker="o", markersize=3, label=braco)

        for limiar in LIMIARES_DE_ALARME:
            eixo.axhline(limiar, color="gray", linestyle="--", linewidth=0.5)

        eixo.set_title(f"h={horizonte}")
        eixo.set_ylabel("casos/semana")

    eixos_em_sequencia[0].legend(fontsize=8, loc="upper left")
    figura.suptitle("Rodada A — real x previsto em 2026 (recorte 01/01 a 19/04/2026)")
    figura.autofmt_xdate()
    figura.tight_layout()
    figura.savefig(caminho_da_figura, dpi=120)
    plt.close(figura)
    print(f"Figura gravada em {caminho_da_figura}")


# ---------------------------------------------------------------------------
# ORQUESTRACAO
# ---------------------------------------------------------------------------


def main() -> None:
    """Roda os 8 bracos, confere a trava, monta a regua e as familias A1/A2/A3."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger(__name__)

    print("=" * 78)
    print("RODADA A — segunda bateria noturna: os resultados principais em 2026")
    print("=" * 78, flush=True)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    previsoes_dos_modelos = harness.executar_bateria(BRACOS, PASTA_DE_SAIDAS)

    trava_valida, tabela_da_trava = conferir_trava_segunda_bateria(previsoes_dos_modelos)
    tabela_da_trava.to_csv(PASTA_DE_SAIDAS / "trava.csv", index=False)

    if not trava_valida:
        log.error(
            "TRAVA FALHOU — investigando, nao forcando. Previsoes e trava.csv ja "
            "gravados em saidas/ para a investigacao; familias A1/A2/A3 NAO rodam."
        )
        return

    tabela_bruta = harness.carregar_tabela_bruta()
    casos_por_data = montar_casos_por_data(tabela_bruta)
    previsoes = adicionar_regua_sazonal(previsoes_dos_modelos, casos_por_data)
    previsoes.to_csv(PASTA_DE_SAIDAS / "previsoes_por_braco.csv", index=False)

    metricas = montar_metricas_por_recorte(previsoes)
    metricas.to_csv(PASTA_DE_SAIDAS / "metricas.csv", index=False)

    familia_a1 = montar_familia_a1(previsoes)
    familia_a1.to_csv(PASTA_DE_SAIDAS / "familia_a1.csv", index=False)

    familia_a2 = montar_familia_a2(previsoes)
    familia_a2.to_csv(PASTA_DE_SAIDAS / "familia_a2.csv", index=False)

    alarmes = montar_alarmes_2026(previsoes)
    alarmes.to_csv(PASTA_DE_SAIDAS / "alarmes_2026.csv", index=False)

    gerar_figura_2026(previsoes, PASTA_DE_SAIDAS / "figura_2026.png")

    print("\nCONCLUIDO.")


if __name__ == "__main__":
    main()
