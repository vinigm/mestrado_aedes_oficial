"""Combinação e avaliação da bateria SARIMA+LASSO+ensemble — 25/09/2026.

Protocolo completo em PRE_DECLARACAO.md (leitura obrigatória, é o contrato desta
rodada). Este script junta os 5 componentes (`B0`, `c2_casos`, `sarima_log`,
`lasso`, régua sazonal), monta `ens_media` e `ens_pesos`, confere as travas da
seção 3 e roda as famílias J1/J2/J3 (Wilcoxon pareado + Holm) da seção 4.

Roda com `~/.venvs/aedes_modelos_fundacao/bin/python` (mesmo venv do SARIMA;
tem pandas, numpy, scipy e sklearn — não precisa do LightGBM do pipeline, que
só entra por `harness.py`, e por isso este script NUNCA importa `harness`
nem `rodar.py`: lê só os CSVs que os outros dois scripts desta bateria
gravam, mais os CSVs já certificados de outras baterias).

⚠️ NÃO altera nada fora desta pasta.

Uso:

    python combinar_e_avaliar.py --smoke        # demo com as ultimas 5 origens de h=12
    python combinar_e_avaliar.py --rodar-tudo    # bateria completa (NAO RODAR nesta entrega:
                                                  # precisa de previsoes_sarima.csv e
                                                  # previsoes_lasso.csv completos, que so
                                                  # existem depois do --rodar-tudo dos outros
                                                  # dois scripts)
"""

import argparse
import dataclasses
import pathlib
import sys
import time

import numpy as np
import pandas as pd
from scipy import stats

# ============================================================================
# CAMINHOS
# ============================================================================

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DO_PROJETO = PASTA_DESTE_ARQUIVO.parent.parent
PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

CAMINHO_TABELA_FINAL = (
    PASTA_DO_PROJETO / "modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv"
)
CAMINHO_PREVISOES_SARIMA = PASTA_DE_SAIDAS / "previsoes_sarima.csv"
CAMINHO_PREVISOES_LASSO = PASTA_DE_SAIDAS / "previsoes_lasso.csv"
CAMINHO_PREVISOES_B0 = (
    PASTA_DO_PROJETO
    / "analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv"
)
CAMINHO_PREVISOES_C2_CASOS = (
    PASTA_DO_PROJETO / "analises/2026-09-25_modelos_de_fundacao/saidas/previsoes_por_braco.csv"
)

# Fallback de --smoke: os CSVs de cronômetro já gravados por rodar_sarima.py
# e rodar_lasso.py (só h=12, todas as origens) — usados para demonstrar a
# combinação sem depender da bateria completa, que não foi rodada nesta
# entrega.
CAMINHO_CRONOMETRO_SARIMA_H12 = PASTA_DE_SAIDAS / "cronometro_sarima_h12.csv"
CAMINHO_CRONOMETRO_LASSO_H12 = PASTA_DE_SAIDAS / "cronometro_lasso_h12.csv"

NOME_DO_BRACO_B0_NO_ARQUIVO = "HistGB_folha20_M1"
NOME_DO_BRACO_C2_NO_ARQUIVO = "c2_casos"

# ============================================================================
# CONSTANTES DE NEGÓCIO (seções 2 a 5 da pré-declaração)
# ============================================================================

HORIZONTES_DA_BATERIA = (1, 4, 8, 12)
QUANTIL_DE_REFERENCIA = 0.85
SEMANAS_DO_PASSO_SAZONAL = 52
INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")
INICIO_CALIBRACAO_EPIDEMICA = pd.Timestamp("2022-01-01")
NIVEL_DE_SIGNIFICANCIA = 0.05
N_ORIGENS_DO_SMOKE = 5

NOME_BRACO_B0 = "B0"
NOME_BRACO_C2_CASOS = "c2_casos"
NOME_BRACO_SARIMA = "sarima_log"
NOME_BRACO_LASSO = "lasso"
NOME_BRACO_LASSO_M0 = "lasso_M0"
NOME_BRACO_REGUA = "regua_sazonal"
NOME_BRACO_ENS_MEDIA = "ens_media"
NOME_BRACO_ENS_PESOS = "ens_pesos"

# Os 5 componentes do ensemble, na ordem em que os pesos são carregados —
# a ordem importa só para a leitura dos vetores de peso, não muda o resultado.
NOMES_DOS_COMPONENTES = (
    NOME_BRACO_B0,
    NOME_BRACO_C2_CASOS,
    NOME_BRACO_SARIMA,
    NOME_BRACO_LASSO,
    NOME_BRACO_REGUA,
)

PASSOS_DA_GRADE_DE_PESOS = 10  # passo 0,1 => 10 passos de 0 a 1, 1.001 combinacoes com 5 componentes
MINIMO_DE_PARES_RESPONDIDOS = 26
TOLERANCIA_DE_EMPATE_NA_PERDA = 1e-12

# Âncoras da seção 3 (trava 3) — MAE na avaliação (data_alvo >= 2024-01-01).
ANCORAS_MAE_B0 = {1: 133.6, 4: 199.6, 8: 223.2, 12: 243.8}
ANCORAS_MAE_REGUA = {1: 202.1, 4: 213.2, 8: 216.2, 12: 217.8}
ANCORAS_MAE_C2_CASOS = {1: 193.6, 4: 255.8, 8: 256.1, 12: 227.2}
ANCORAS_N_POR_HORIZONTE_NA_AVALIACAO = 102
TOLERANCIA_DE_MAE_DA_ANCORA = 0.2

# Famílias da seção 4.
NOMES_VARIANTES_J1 = (NOME_BRACO_SARIMA, NOME_BRACO_LASSO, NOME_BRACO_ENS_MEDIA, NOME_BRACO_ENS_PESOS)
HORIZONTES_J1 = (4, 8, 12)
NOMES_VARIANTES_J2 = NOMES_VARIANTES_J1
HORIZONTES_J2 = HORIZONTES_DA_BATERIA


# ============================================================================
# LEITURA — CADA COMPONENTE, DE ONDE ELE VEM
# ============================================================================


def carregar_serie_semanal_de_casos(caminho_tabela_final: pathlib.Path) -> pd.DataFrame:
    """A série de casos confirmados, usada para calcular a régua sazonal."""
    tabela_bruta = pd.read_csv(caminho_tabela_final, parse_dates=["data_inicio_semana_epidemi"])
    serie_semanal = tabela_bruta[["data_inicio_semana_epidemi", "casos_confirmados"]].rename(
        columns={"data_inicio_semana_epidemi": "data", "casos_confirmados": "casos"}
    )
    return serie_semanal.sort_values("data").reset_index(drop=True)


def calcular_previsao_da_regua_sazonal(
    serie_semanal_de_casos: pd.DataFrame, data_alvo: pd.Timestamp
) -> float:
    """A régua sazonal: casos confirmados na mesma semana, um ano antes."""
    semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    linha_correspondente = serie_semanal_de_casos.loc[
        serie_semanal_de_casos["data"] == semana_um_ano_antes, "casos"
    ]
    if linha_correspondente.empty:
        return np.nan
    return float(linha_correspondente.to_numpy()[0])


def montar_previsoes_da_regua(
    pares_h_data_alvo: pd.DataFrame, serie_semanal_de_casos: pd.DataFrame
) -> pd.DataFrame:
    """Gera a previsão da régua sazonal para cada (h, data_alvo) pedido."""
    linhas: list[dict[str, object]] = []
    for _, par in pares_h_data_alvo.iterrows():
        data_alvo = pd.Timestamp(par["data_alvo"])
        previsto = calcular_previsao_da_regua_sazonal(serie_semanal_de_casos, data_alvo)
        real_da_semana = serie_semanal_de_casos.loc[serie_semanal_de_casos["data"] == data_alvo, "casos"]
        linhas.append(
            {
                "h": int(par["h"]),
                "data_alvo": data_alvo,
                "real": float(real_da_semana.to_numpy()[0]) if not real_da_semana.empty else np.nan,
                "previsto": previsto,
                "braco": NOME_BRACO_REGUA,
            }
        )
    previsoes_da_regua = pd.DataFrame(linhas)
    return previsoes_da_regua.dropna(subset=["previsto"])


def carregar_previsoes_do_b0(caminho: pathlib.Path) -> pd.DataFrame:
    """B0 = HistGB_folha20_M1 do bloco 7 da bateria noturna."""
    previsoes = pd.read_csv(caminho, parse_dates=["data_alvo"])
    do_b0 = previsoes[previsoes["braco"] == NOME_DO_BRACO_B0_NO_ARQUIVO].copy()
    do_b0["braco"] = NOME_BRACO_B0
    return do_b0[["h", "data_alvo", "real", "previsto", "braco"]]


def carregar_previsoes_do_c2_casos(caminho: pathlib.Path) -> pd.DataFrame:
    """c2_casos = o Chronos-2 só com casos, coluna q085 (quantil de referência)."""
    previsoes = pd.read_csv(caminho, parse_dates=["data_alvo"])
    do_c2 = previsoes[previsoes["braco"] == NOME_DO_BRACO_C2_NO_ARQUIVO].copy()
    do_c2 = do_c2.rename(columns={"q085": "previsto"})
    do_c2["braco"] = NOME_BRACO_C2_CASOS
    return do_c2[["h", "data_alvo", "real", "previsto", "braco"]]


def carregar_previsoes_do_sarima(caminho: pathlib.Path) -> pd.DataFrame:
    """sarima_log, no formato longo (h, data_alvo, real, previsto, braco), a partir do q085."""
    previsoes = pd.read_csv(caminho, parse_dates=["data_alvo", "origem", "ultima_data_ajuste"])
    previsoes = previsoes.rename(columns={"q085": "previsto"})
    previsoes["braco"] = NOME_BRACO_SARIMA
    return previsoes[["h", "data_alvo", "real", "previsto", "braco"]]


def carregar_previsoes_do_lasso(caminho: pathlib.Path, nome_do_braco: str) -> pd.DataFrame:
    """`lasso` ou `lasso_M0`, já no formato longo."""
    previsoes = pd.read_csv(caminho, parse_dates=["data_alvo"])
    if "braco" in previsoes.columns:
        previsoes = previsoes[previsoes["braco"] == nome_do_braco].copy()
    else:
        previsoes = previsoes.copy()
        previsoes["braco"] = nome_do_braco
    return previsoes[["h", "data_alvo", "real", "previsto", "braco"]]


@dataclasses.dataclass(frozen=True)
class ConjuntoDeEntrada:
    """Os 4 componentes lidos de arquivo, mais os pares (h, data_alvo) que fixam a grade.

    `lasso_M0` só existe quando o LASSO completo (2 braços) já rodou — em
    `--smoke` fica vazio, porque o cronômetro só rodou o braço `lasso`.
    """

    b0: pd.DataFrame
    c2_casos: pd.DataFrame
    sarima_log: pd.DataFrame
    lasso: pd.DataFrame
    lasso_m0: pd.DataFrame
    pares_h_data_alvo: pd.DataFrame


def montar_conjunto_de_entrada_smoke() -> ConjuntoDeEntrada:
    """--smoke: usa os CSVs de cronômetro (h=12, todas as origens) e recorta as últimas 5.

    A bateria completa (`previsoes_sarima.csv`, `previsoes_lasso.csv`) não foi
    rodada nesta entrega — só smoke test e cronômetro, por instrução do brief.
    Este modo demonstra a combinação com dados REAIS (não sintéticos): as
    previsões do cronômetro de cada script, recortadas às últimas 5 origens.
    """
    if not CAMINHO_CRONOMETRO_SARIMA_H12.exists() or not CAMINHO_CRONOMETRO_LASSO_H12.exists():
        raise FileNotFoundError(
            "Cronometros de SARIMA e/ou LASSO ausentes em saidas/. "
            "Rode 'python rodar_sarima.py --cronometro' e "
            "'python rodar_lasso.py --cronometro' antes de --smoke aqui."
        )

    sarima_h12 = carregar_previsoes_do_sarima(CAMINHO_CRONOMETRO_SARIMA_H12).tail(N_ORIGENS_DO_SMOKE)
    lasso_h12 = carregar_previsoes_do_lasso(CAMINHO_CRONOMETRO_LASSO_H12, NOME_BRACO_LASSO).tail(
        N_ORIGENS_DO_SMOKE
    )

    datas_alvo_do_smoke = sarima_h12["data_alvo"]
    pares_h_data_alvo = pd.DataFrame({"h": 12, "data_alvo": datas_alvo_do_smoke})

    b0_completo = carregar_previsoes_do_b0(CAMINHO_PREVISOES_B0)
    b0_h12 = b0_completo[(b0_completo["h"] == 12) & (b0_completo["data_alvo"].isin(datas_alvo_do_smoke))]

    c2_completo = carregar_previsoes_do_c2_casos(CAMINHO_PREVISOES_C2_CASOS)
    c2_h12 = c2_completo[(c2_completo["h"] == 12) & (c2_completo["data_alvo"].isin(datas_alvo_do_smoke))]

    lasso_m0_vazio = lasso_h12.iloc[0:0].copy()
    lasso_m0_vazio["braco"] = NOME_BRACO_LASSO_M0

    return ConjuntoDeEntrada(
        b0=b0_h12,
        c2_casos=c2_h12,
        sarima_log=sarima_h12,
        lasso=lasso_h12,
        lasso_m0=lasso_m0_vazio,
        pares_h_data_alvo=pares_h_data_alvo,
    )


def montar_conjunto_de_entrada_completo() -> ConjuntoDeEntrada:
    """Bateria completa: lê `previsoes_sarima.csv` e `previsoes_lasso.csv` inteiros.

    ⚠️ NÃO EXECUTADO nesta entrega — exige que os outros dois scripts tenham
    rodado com `--rodar-tudo` antes.
    """
    lasso_completo = pd.read_csv(CAMINHO_PREVISOES_LASSO, parse_dates=["data_alvo"])
    b0_completo = carregar_previsoes_do_b0(CAMINHO_PREVISOES_B0)
    pares_h_data_alvo = b0_completo[["h", "data_alvo"]].drop_duplicates()

    return ConjuntoDeEntrada(
        b0=b0_completo,
        c2_casos=carregar_previsoes_do_c2_casos(CAMINHO_PREVISOES_C2_CASOS),
        sarima_log=carregar_previsoes_do_sarima(CAMINHO_PREVISOES_SARIMA),
        lasso=carregar_previsoes_do_lasso(CAMINHO_PREVISOES_LASSO, NOME_BRACO_LASSO),
        lasso_m0=carregar_previsoes_do_lasso(CAMINHO_PREVISOES_LASSO, NOME_BRACO_LASSO_M0),
        pares_h_data_alvo=pares_h_data_alvo,
    )


# ============================================================================
# MONTAGEM DA TABELA LARGA (uma coluna por componente, para o ensemble)
# ============================================================================


def montar_tabela_larga_dos_componentes(conjunto: ConjuntoDeEntrada) -> pd.DataFrame:
    """Junta os 4 componentes lidos de arquivo numa tabela larga, uma coluna por braço.

    Faz `inner join` por (h, data_alvo): só entram pares em que os 4
    componentes existem — a régua entra depois, calculada sob demanda.

    Returns:
        Colunas: h, data_alvo, real, e uma coluna por nome em
        `NOMES_DOS_COMPONENTES` exceto a régua.
    """
    partes = {
        NOME_BRACO_B0: conjunto.b0,
        NOME_BRACO_C2_CASOS: conjunto.c2_casos,
        NOME_BRACO_SARIMA: conjunto.sarima_log,
        NOME_BRACO_LASSO: conjunto.lasso,
    }

    tabela_larga: pd.DataFrame | None = None
    for nome_do_componente, previsoes_do_componente in partes.items():
        estreita = previsoes_do_componente[["h", "data_alvo", "real", "previsto"]].rename(
            columns={"previsto": nome_do_componente}
        )
        if tabela_larga is None:
            tabela_larga = estreita
        else:
            tabela_larga = tabela_larga.merge(
                estreita.drop(columns=["real"]), on=["h", "data_alvo"], how="inner"
            )

    return tabela_larga.sort_values(["h", "data_alvo"]).reset_index(drop=True)


def acrescentar_coluna_da_regua(
    tabela_larga: pd.DataFrame, serie_semanal_de_casos: pd.DataFrame
) -> pd.DataFrame:
    """Acrescenta a coluna `regua_sazonal` à tabela larga, uma previsão por linha."""
    tabela_com_regua = tabela_larga.copy()
    previsoes_da_regua: list[float] = []
    for data_alvo in tabela_com_regua["data_alvo"]:
        previsoes_da_regua.append(
            calcular_previsao_da_regua_sazonal(serie_semanal_de_casos, pd.Timestamp(data_alvo))
        )
    tabela_com_regua[NOME_BRACO_REGUA] = previsoes_da_regua
    return tabela_com_regua.dropna(subset=[NOME_BRACO_REGUA]).reset_index(drop=True)


# ============================================================================
# PERDA QUANTÍLICA E GRADE DE PESOS
# ============================================================================


def calcular_perda_quantilica_085(reais: np.ndarray, previstos: np.ndarray) -> float:
    """Perda pinball no quantil 0,85 — mesma métrica de `rodar_lasso.py`."""
    diferenca = reais - previstos
    return float(
        np.mean(np.maximum(QUANTIL_DE_REFERENCIA * diferenca, (QUANTIL_DE_REFERENCIA - 1.0) * diferenca))
    )


def gerar_grade_de_pesos_do_ensemble() -> list[tuple[float, float, float, float, float]]:
    """As 1.001 combinações de 5 pesos não negativos que somam 1, passo 0,1.

    Enumera por contagem inteira de passos (0 a 10) para não acumular erro de
    ponto flutuante na soma — só divide por `PASSOS_DA_GRADE_DE_PESOS` no final.
    """
    grade_de_pesos: list[tuple[float, float, float, float, float]] = []

    for passos_b0 in range(PASSOS_DA_GRADE_DE_PESOS + 1):
        for passos_c2 in range(PASSOS_DA_GRADE_DE_PESOS + 1 - passos_b0):
            for passos_sarima in range(PASSOS_DA_GRADE_DE_PESOS + 1 - passos_b0 - passos_c2):
                passos_usados_ate_aqui = passos_b0 + passos_c2 + passos_sarima
                for passos_lasso in range(PASSOS_DA_GRADE_DE_PESOS + 1 - passos_usados_ate_aqui):
                    passos_regua = PASSOS_DA_GRADE_DE_PESOS - passos_usados_ate_aqui - passos_lasso
                    pesos = (
                        passos_b0 / PASSOS_DA_GRADE_DE_PESOS,
                        passos_c2 / PASSOS_DA_GRADE_DE_PESOS,
                        passos_sarima / PASSOS_DA_GRADE_DE_PESOS,
                        passos_lasso / PASSOS_DA_GRADE_DE_PESOS,
                        passos_regua / PASSOS_DA_GRADE_DE_PESOS,
                    )
                    grade_de_pesos.append(pesos)

    return grade_de_pesos


GRADE_DE_PESOS_DO_ENSEMBLE = gerar_grade_de_pesos_do_ensemble()
PESOS_IGUAIS = (0.2, 0.2, 0.2, 0.2, 0.2)
INDICE_DA_REGUA_NOS_PESOS = NOMES_DOS_COMPONENTES.index(NOME_BRACO_REGUA)


def calcular_previsao_combinada(
    componentes: pd.DataFrame, pesos: tuple[float, float, float, float, float]
) -> np.ndarray:
    """Combinação linear dos 5 componentes com os pesos dados, na ordem de `NOMES_DOS_COMPONENTES`."""
    previsao_combinada = np.zeros(len(componentes))
    for indice_do_componente, nome_do_componente in enumerate(NOMES_DOS_COMPONENTES):
        previsao_combinada = previsao_combinada + pesos[indice_do_componente] * componentes[
            nome_do_componente
        ].to_numpy()
    return previsao_combinada


def escolher_pesos_do_ensemble(
    pares_ja_respondidos: pd.DataFrame,
) -> tuple[float, float, float, float, float]:
    """Escolhe os pesos do `ens_pesos` numa origem: menor perda quantílica nos pares já respondidos.

    Regras da seção 2:
        - menos de 26 pares respondidos usa pesos iguais;
        - empate na perda vence a combinação de maior peso na régua.

    Args:
        pares_ja_respondidos: Linhas da tabela larga com `data_alvo <= origem`.

    Returns:
        Os 5 pesos vencedores, na ordem de `NOMES_DOS_COMPONENTES`.
    """
    if len(pares_ja_respondidos) < MINIMO_DE_PARES_RESPONDIDOS:
        return PESOS_IGUAIS

    reais = pares_ja_respondidos["real"].to_numpy()
    melhor_perda: float | None = None
    melhores_pesos = PESOS_IGUAIS

    for pesos_candidatos in GRADE_DE_PESOS_DO_ENSEMBLE:
        previsao_combinada = calcular_previsao_combinada(pares_ja_respondidos, pesos_candidatos)
        perda_do_candidato = calcular_perda_quantilica_085(reais, previsao_combinada)

        e_o_primeiro_candidato = melhor_perda is None
        e_estritamente_melhor = (not e_o_primeiro_candidato) and (
            perda_do_candidato < melhor_perda - TOLERANCIA_DE_EMPATE_NA_PERDA
        )
        e_empate_com_mais_peso_na_regua = (not e_o_primeiro_candidato) and (
            abs(perda_do_candidato - melhor_perda) <= TOLERANCIA_DE_EMPATE_NA_PERDA
            and pesos_candidatos[INDICE_DA_REGUA_NOS_PESOS] > melhores_pesos[INDICE_DA_REGUA_NOS_PESOS]
        )

        if e_o_primeiro_candidato or e_estritamente_melhor or e_empate_com_mais_peso_na_regua:
            melhor_perda = perda_do_candidato
            melhores_pesos = pesos_candidatos

    return melhores_pesos


def montar_previsoes_do_ens_pesos(tabela_larga_com_regua: pd.DataFrame) -> pd.DataFrame:
    """Roda `ens_pesos` em cada (h, data_alvo): escolhe pesos, combina, guarda a previsão.

    Cada horizonte é processado separadamente e em ordem cronológica de
    `data_alvo`, porque "pares já respondidos" só faz sentido dentro do mesmo
    horizonte (trava 2 da seção 3: os pesos da origem usam só pares com
    `data_alvo <= origem`, e `origem = data_alvo - h`).

    Returns:
        h, data_alvo, real, previsto, braco='ens_pesos', mais os 5 pesos
        usados naquela origem (colunas `peso_<componente>`).
    """
    linhas_do_resultado: list[dict[str, object]] = []

    for horizonte in tabela_larga_com_regua["h"].unique():
        do_horizonte = tabela_larga_com_regua[tabela_larga_com_regua["h"] == horizonte].sort_values(
            "data_alvo"
        )

        for _, linha_da_origem in do_horizonte.iterrows():
            origem = pd.Timestamp(linha_da_origem["data_alvo"]) - pd.Timedelta(weeks=int(horizonte))
            pares_ja_respondidos = do_horizonte[do_horizonte["data_alvo"] <= origem]

            pesos_escolhidos = escolher_pesos_do_ensemble(pares_ja_respondidos)
            linha_como_dataframe = pd.DataFrame([linha_da_origem])
            previsao_combinada = calcular_previsao_combinada(linha_como_dataframe, pesos_escolhidos)

            linha_de_saida = {
                "h": int(horizonte),
                "data_alvo": linha_da_origem["data_alvo"],
                "real": float(linha_da_origem["real"]),
                "previsto": float(previsao_combinada[0]),
                "braco": NOME_BRACO_ENS_PESOS,
            }
            for indice_do_componente, nome_do_componente in enumerate(NOMES_DOS_COMPONENTES):
                linha_de_saida[f"peso_{nome_do_componente}"] = pesos_escolhidos[indice_do_componente]
            linhas_do_resultado.append(linha_de_saida)

    return pd.DataFrame(linhas_do_resultado)


def montar_previsoes_do_ens_media(tabela_larga_com_regua: pd.DataFrame) -> pd.DataFrame:
    """`ens_media`: média simples e fixa (peso 0,2) dos 5 componentes, sem depender da origem."""
    pesos_iguais_fixos = PESOS_IGUAIS
    previsao_combinada = calcular_previsao_combinada(tabela_larga_com_regua, pesos_iguais_fixos)

    previsoes = tabela_larga_com_regua[["h", "data_alvo", "real"]].copy()
    previsoes["previsto"] = previsao_combinada
    previsoes["braco"] = NOME_BRACO_ENS_MEDIA
    return previsoes


# ============================================================================
# TRAVAS (seção 3, antes de ler qualquer resultado)
# ============================================================================


def conferir_trava_1_pareamento(previsoes_avaliacao: pd.DataFrame) -> bool:
    """Trave 1 — todo braço tem os mesmos `data_alvo` do B0, 102 por horizonte na avaliação."""
    print("\n  TRAVA 1 — pareamento com o B0 (102 pares por horizonte na avaliacao)")
    tudo_bate = True
    for horizonte in HORIZONTES_DA_BATERIA:
        n_por_braco = previsoes_avaliacao[previsoes_avaliacao["h"] == horizonte].groupby("braco").size()
        for nome_do_braco, n_pares in n_por_braco.items():
            bate = n_pares == ANCORAS_N_POR_HORIZONTE_NA_AVALIACAO
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "<<< DIVERGE"
            print(
                f"    h={horizonte:2d}  {nome_do_braco:>12}  n={n_pares:3d} "
                f"(esperado {ANCORAS_N_POR_HORIZONTE_NA_AVALIACAO})  {marca}"
            )
    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def conferir_trava_2_sem_futuro_no_sarima(previsoes_sarima_brutas: pd.DataFrame) -> bool:
    """Trave 2 (parte SARIMA) — a última data ajustada é sempre a origem, nunca depois dela."""
    origem_esperada = previsoes_sarima_brutas["data_alvo"] - pd.to_timedelta(
        previsoes_sarima_brutas["h"], unit="W"
    )
    bate = (previsoes_sarima_brutas["ultima_data_ajuste"] == origem_esperada).all()
    print("\n  TRAVA 2 (SARIMA) — ultima_data_ajuste == data_alvo - h semanas, em todas as linhas")
    print(f"    veredito: {'VALIDO' if bate else 'INVALIDO'}")
    return bool(bate)


def conferir_trava_3_ancoras(previsoes_avaliacao: pd.DataFrame) -> bool:
    """Trave 3 — B0, régua e c2_casos reproduzem as âncoras da seção 3, por horizonte."""
    ancoras_por_braco = {
        NOME_BRACO_B0: ANCORAS_MAE_B0,
        NOME_BRACO_REGUA: ANCORAS_MAE_REGUA,
        NOME_BRACO_C2_CASOS: ANCORAS_MAE_C2_CASOS,
    }

    print("\n  TRAVA 3 — ancoras de MAE na avaliacao")
    tudo_bate = True
    for nome_do_braco, ancoras_do_braco in ancoras_por_braco.items():
        do_braco = previsoes_avaliacao[previsoes_avaliacao["braco"] == nome_do_braco]
        for horizonte, mae_esperado in ancoras_do_braco.items():
            celula = do_braco[do_braco["h"] == horizonte]
            if celula.empty:
                print(f"    {nome_do_braco:>12}  h={horizonte:2d}  SEM DADOS")
                tudo_bate = False
                continue
            erro_absoluto = np.abs(celula["real"].to_numpy() - celula["previsto"].to_numpy())
            mae = float(np.mean(erro_absoluto))
            bate = abs(mae - mae_esperado) < TOLERANCIA_DE_MAE_DA_ANCORA
            tudo_bate = tudo_bate and bate
            marca = "ok" if bate else "<<< DIVERGE"
            print(f"    {nome_do_braco:>12}  h={horizonte:2d}  MAE {mae:7.1f} (esperado {mae_esperado:6.1f})  {marca}")
    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def conferir_travas(
    previsoes_avaliacao: pd.DataFrame, previsoes_sarima_brutas: pd.DataFrame
) -> bool:
    """As travas verificáveis pelo combinador. Se alguma falhar, nada é lido.

    ⚠️ Travas 4 (determinismo) e 5 (mesmo clima do B0) são estruturais dos
    scripts que PRODUZEM `sarima_log` e `lasso` — `rodar_sarima.py` e
    `rodar_lasso.py` — e não são re-verificáveis aqui sem reimportar
    `harness` (que precisa do LightGBM, ausente neste venv). Documentado em
    `desvios_e_decisoes`.
    """
    trava_1 = conferir_trava_1_pareamento(previsoes_avaliacao)
    trava_2 = conferir_trava_2_sem_futuro_no_sarima(previsoes_sarima_brutas)
    trava_3 = conferir_trava_3_ancoras(previsoes_avaliacao)
    return trava_1 and trava_2 and trava_3


# ============================================================================
# FAMÍLIAS J1 / J2 / J3 (Wilcoxon pareado + Holm) — reusa o motor da bateria noturna
# ============================================================================


@dataclasses.dataclass(frozen=True)
class ComparacaoDaFamilia:
    """Uma comparação pareada por `data_alvo`, no formato que a correção de Holm usa.

    Espelha `harness.ComparacaoPareada`, reimplementada aqui — e não importada
    — porque este script deliberadamente não importa `harness` (evita a
    dependência do LightGBM neste venv).
    """

    braco: str
    horizonte: int
    mae_braco: float
    mae_comparador: float
    p_bruto: float

    def reducao_percentual(self) -> float:
        """Quanto o braço reduziu o MAE em relação ao comparador. Negativo é piora."""
        return 100.0 * (self.mae_comparador - self.mae_braco) / self.mae_comparador


def comparar_pareado_por_data_alvo(
    previsoes_avaliacao: pd.DataFrame, nome_do_comparador: str, nome_do_braco: str, horizonte: int
) -> ComparacaoDaFamilia:
    """Wilcoxon bilateral do erro absoluto, pareado por `data_alvo`, braço x comparador."""
    do_horizonte = previsoes_avaliacao[previsoes_avaliacao["h"] == horizonte]
    do_comparador = do_horizonte[do_horizonte["braco"] == nome_do_comparador]
    do_braco = do_horizonte[do_horizonte["braco"] == nome_do_braco]

    pareado = do_comparador.merge(do_braco, on="data_alvo", suffixes=("_comparador", "_braco"))
    if pareado.empty:
        raise ValueError(f"Nenhuma semana em comum entre {nome_do_comparador} e {nome_do_braco} em h={horizonte}.")

    erro_do_comparador = np.abs(pareado["real_comparador"] - pareado["previsto_comparador"])
    erro_do_braco = np.abs(pareado["real_braco"] - pareado["previsto_braco"])

    if np.allclose(erro_do_comparador, erro_do_braco):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_do_comparador, erro_do_braco)

    return ComparacaoDaFamilia(
        braco=nome_do_braco,
        horizonte=horizonte,
        mae_braco=float(np.mean(erro_do_braco)),
        mae_comparador=float(np.mean(erro_do_comparador)),
        p_bruto=float(p_bruto),
    )


def _p_bruto_da_comparacao(comparacao: ComparacaoDaFamilia) -> float:
    """Chave de ordenação do Holm: o p antes da correção."""
    return comparacao.p_bruto


def corrigir_por_holm(comparacoes: list[ComparacaoDaFamilia]) -> dict[str, float]:
    """Holm sobre a família inteira — mesma regra e mesma implementação de `harness.corrigir_por_holm`."""
    ordenadas = sorted(comparacoes, key=_p_bruto_da_comparacao)
    quantidade = len(ordenadas)

    p_corrigidos: dict[str, float] = {}
    maior_p_ate_agora = 0.0
    for posicao, comparacao in enumerate(ordenadas):
        p_ajustado = min(1.0, comparacao.p_bruto * (quantidade - posicao))
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"] = maior_p_ate_agora

    return p_corrigidos


def montar_tabela_da_familia(comparacoes: list[ComparacaoDaFamilia]) -> pd.DataFrame:
    """Aplica Holm e devolve a tabela pronta para gravar (braço, h, MAE dos dois lados, p)."""
    p_corrigidos = corrigir_por_holm(comparacoes)
    linhas: list[dict[str, object]] = []
    for comparacao in comparacoes:
        linhas.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_braco": comparacao.mae_braco,
                "mae_comparador": comparacao.mae_comparador,
                "reducao_percentual": comparacao.reducao_percentual(),
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"],
            }
        )
    return pd.DataFrame(linhas)


def montar_familia_j1_bate_regua(previsoes_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """J1 — bate a régua? 4 variantes x h(4,8,12) = 12 comparações, Holm sobre 12."""
    comparacoes = []
    for nome_da_variante in NOMES_VARIANTES_J1:
        for horizonte in HORIZONTES_J1:
            comparacoes.append(
                comparar_pareado_por_data_alvo(previsoes_avaliacao, NOME_BRACO_REGUA, nome_da_variante, horizonte)
            )
    return montar_tabela_da_familia(comparacoes)


def montar_familia_j2_melhora_b0(previsoes_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """J2 — melhora o B0? 4 variantes x 4 horizontes = 16 comparações, Holm sobre 16."""
    comparacoes = []
    for nome_da_variante in NOMES_VARIANTES_J2:
        for horizonte in HORIZONTES_J2:
            comparacoes.append(
                comparar_pareado_por_data_alvo(previsoes_avaliacao, NOME_BRACO_B0, nome_da_variante, horizonte)
            )
    return montar_tabela_da_familia(comparacoes)


def montar_familia_j3_vetor_no_lasso(previsoes_avaliacao_com_m0: pd.DataFrame) -> pd.DataFrame:
    """J3 — o vetor vale no LASSO? lasso x lasso_M0 x 4 horizontes = 4 comparações, Holm sobre 4."""
    comparacoes = []
    for horizonte in HORIZONTES_DA_BATERIA:
        comparacoes.append(
            comparar_pareado_por_data_alvo(previsoes_avaliacao_com_m0, NOME_BRACO_LASSO_M0, NOME_BRACO_LASSO, horizonte)
        )
    return montar_tabela_da_familia(comparacoes)


# ============================================================================
# LEITURAS DESCRITIVAS (seção 4, sem teste)
# ============================================================================


def gerar_leitura_pesos_medios_do_ens_pesos(previsoes_do_ens_pesos: pd.DataFrame) -> pd.DataFrame:
    """Os pesos médios do `ens_pesos` por horizonte, na avaliação — quem o ensemble escolhe."""
    colunas_de_peso = [f"peso_{nome}" for nome in NOMES_DOS_COMPONENTES]
    na_avaliacao = previsoes_do_ens_pesos[previsoes_do_ens_pesos["data_alvo"] >= INICIO_DA_AVALIACAO]
    pesos_medios = na_avaliacao.groupby("h")[colunas_de_peso].mean().reset_index()
    return pesos_medios


# ============================================================================
# CRITÉRIOS DE DECISÃO (seção 5) — só impressos no log, nada decide sozinho
# ============================================================================


def imprimir_criterios_de_decisao(
    familia_j1: pd.DataFrame, familia_j2: pd.DataFrame, familia_j3: pd.DataFrame
) -> None:
    """Section 5: bate a régua / melhora o B0 / o vetor vale, tudo em h=12."""
    print("\n  CRITERIOS DE DECISAO (secao 5), h=12")
    for nome_da_variante in NOMES_VARIANTES_J1:
        linha_j1 = familia_j1[(familia_j1["braco"] == nome_da_variante) & (familia_j1["h"] == 12)]
        linha_j2 = familia_j2[(familia_j2["braco"] == nome_da_variante) & (familia_j2["h"] == 12)]

        bate_a_regua = False
        if not linha_j1.empty:
            bate_a_regua = bool(
                (linha_j1["mae_braco"].to_numpy()[0] < linha_j1["mae_comparador"].to_numpy()[0])
                and (linha_j1["p_holm"].to_numpy()[0] < NIVEL_DE_SIGNIFICANCIA)
            )

        melhora_o_b0 = False
        if not linha_j2.empty:
            melhora_o_b0 = bool(
                (linha_j2["mae_braco"].to_numpy()[0] < linha_j2["mae_comparador"].to_numpy()[0])
                and (linha_j2["p_holm"].to_numpy()[0] < NIVEL_DE_SIGNIFICANCIA)
            )

        candidato = bate_a_regua or melhora_o_b0
        print(
            f"    {nome_da_variante:>12}  bate_a_regua={bate_a_regua}  "
            f"melhora_o_b0={melhora_o_b0}  candidato_2026_2027={candidato}"
        )

    linha_j3_h12 = familia_j3[familia_j3["h"] == 12]
    if not linha_j3_h12.empty:
        vetor_vale = bool(
            (linha_j3_h12["mae_braco"].to_numpy()[0] < linha_j3_h12["mae_comparador"].to_numpy()[0])
            and (linha_j3_h12["p_holm"].to_numpy()[0] < NIVEL_DE_SIGNIFICANCIA)
        )
        print(f"    vetor_vale_no_lasso={vetor_vale}")


# ============================================================================
# FIGURA
# ============================================================================


def gerar_figura_mae_por_horizonte(previsoes_avaliacao: pd.DataFrame) -> None:
    """MAE por horizonte, os componentes + ensemble, régua tracejada."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figura, eixo = plt.subplots(figsize=(9, 6))
    nomes_normais = [nome for nome in previsoes_avaliacao["braco"].unique() if nome != NOME_BRACO_REGUA]

    for nome_do_braco in sorted(nomes_normais):
        do_braco = previsoes_avaliacao[previsoes_avaliacao["braco"] == nome_do_braco]
        maes_por_horizonte = []
        for horizonte in HORIZONTES_DA_BATERIA:
            do_horizonte = do_braco[do_braco["h"] == horizonte]
            if do_horizonte.empty:
                maes_por_horizonte.append(np.nan)
                continue
            erro_absoluto = np.abs(do_horizonte["real"].to_numpy() - do_horizonte["previsto"].to_numpy())
            maes_por_horizonte.append(float(np.mean(erro_absoluto)))
        eixo.plot(HORIZONTES_DA_BATERIA, maes_por_horizonte, marker="o", label=nome_do_braco)

    do_regua = previsoes_avaliacao[previsoes_avaliacao["braco"] == NOME_BRACO_REGUA]
    maes_da_regua = []
    for horizonte in HORIZONTES_DA_BATERIA:
        do_horizonte = do_regua[do_regua["h"] == horizonte]
        if do_horizonte.empty:
            maes_da_regua.append(np.nan)
            continue
        erro_absoluto = np.abs(do_horizonte["real"].to_numpy() - do_horizonte["previsto"].to_numpy())
        maes_da_regua.append(float(np.mean(erro_absoluto)))
    eixo.plot(HORIZONTES_DA_BATERIA, maes_da_regua, marker="s", linestyle="--", color="black", label=NOME_BRACO_REGUA)

    eixo.set_xlabel("horizonte (semanas)")
    eixo.set_ylabel("MAE (casos/semana)")
    eixo.set_title("SARIMA + LASSO + ensemble — MAE por horizonte")
    eixo.legend(fontsize=8, loc="upper left")
    figura.tight_layout()

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    figura.savefig(PASTA_DE_SAIDAS / "figura_mae_por_horizonte.png", dpi=150)
    plt.close(figura)


# ============================================================================
# SMOKE TEST
# ============================================================================


def rodar_smoke_test() -> None:
    """--smoke: demo da combinação com dados REAIS das últimas 5 origens de h=12.

    Não roda travas nem famílias com valor estatístico — 5 pares não têm
    poder para Wilcoxon nem reproduzem as âncoras de 102 pares. Demonstra só
    a MECÂNICA: junção dos componentes, `ens_media`, e `ens_pesos` caindo no
    fallback de pesos iguais (5 pares respondidos é menos que o mínimo de 26).
    """
    conjunto = montar_conjunto_de_entrada_smoke()
    serie_semanal_de_casos = carregar_serie_semanal_de_casos(CAMINHO_TABELA_FINAL)

    tabela_larga = montar_tabela_larga_dos_componentes(conjunto)
    tabela_larga_com_regua = acrescentar_coluna_da_regua(tabela_larga, serie_semanal_de_casos)

    print("\n[smoke] tabela larga dos componentes (h=12, ultimas 5 origens)", flush=True)
    print(tabela_larga_com_regua.to_string(index=False), flush=True)

    previsoes_ens_media = montar_previsoes_do_ens_media(tabela_larga_com_regua)
    print("\n[smoke] ens_media", flush=True)
    print(previsoes_ens_media.to_string(index=False), flush=True)

    previsoes_ens_pesos = montar_previsoes_do_ens_pesos(tabela_larga_com_regua)
    print("\n[smoke] ens_pesos (esperado: pesos iguais, so 5 pares respondidos < minimo de 26)", flush=True)
    print(previsoes_ens_pesos.to_string(index=False), flush=True)

    print("\n[smoke] TRAVA 3 nas ultimas 5 origens (nao e a avaliacao inteira — so demonstracao):")
    for nome_do_braco in (NOME_BRACO_B0, NOME_BRACO_C2_CASOS):
        do_braco = tabela_larga_com_regua[["real", nome_do_braco]]
        erro_absoluto = np.abs(do_braco["real"].to_numpy() - do_braco[nome_do_braco].to_numpy())
        print(f"    {nome_do_braco}: MAE nas 5 origens = {np.mean(erro_absoluto):.1f} (so referencia, N pequeno)")

    print("\n[smoke] COMBINACAO RODOU SEM ERRO.", flush=True)


# ============================================================================
# BATERIA COMPLETA (não executada nesta entrega — só implementada)
# ============================================================================


def rodar_bateria_completa() -> None:
    """Junta tudo, confere as travas, roda J1/J2/J3, gera leituras e a figura.

    ⚠️ NÃO EXECUTADO nesta entrega — depende de `previsoes_sarima.csv` e
    `previsoes_lasso.csv` completos, que só existem depois do `--rodar-tudo`
    de `rodar_sarima.py` e `rodar_lasso.py`. Ver `desvios_e_decisoes`.
    """
    conjunto = montar_conjunto_de_entrada_completo()
    serie_semanal_de_casos = carregar_serie_semanal_de_casos(CAMINHO_TABELA_FINAL)

    tabela_larga = montar_tabela_larga_dos_componentes(conjunto)
    tabela_larga_com_regua = acrescentar_coluna_da_regua(tabela_larga, serie_semanal_de_casos)

    previsoes_ens_media = montar_previsoes_do_ens_media(tabela_larga_com_regua)
    previsoes_ens_pesos = montar_previsoes_do_ens_pesos(tabela_larga_com_regua)

    previsoes_dos_componentes: list[pd.DataFrame] = []
    for nome_do_componente in NOMES_DOS_COMPONENTES:
        estreita = tabela_larga_com_regua[["h", "data_alvo", "real", nome_do_componente]].rename(
            columns={nome_do_componente: "previsto"}
        )
        estreita["braco"] = nome_do_componente
        previsoes_dos_componentes.append(estreita)

    previsoes_todas = pd.concat(
        previsoes_dos_componentes
        + [previsoes_ens_media[["h", "data_alvo", "real", "previsto", "braco"]], previsoes_ens_pesos[
            ["h", "data_alvo", "real", "previsto", "braco"]
        ]],
        ignore_index=True,
    )
    previsoes_avaliacao = previsoes_todas[previsoes_todas["data_alvo"] >= INICIO_DA_AVALIACAO]

    # A trava 2 precisa da coluna `ultima_data_ajuste`, que só existe no CSV
    # bruto do SARIMA; o conjunto de entrada já vem no formato longo, sem ela.
    previsoes_sarima_brutas = pd.read_csv(
        CAMINHO_PREVISOES_SARIMA, parse_dates=["data_alvo", "origem", "ultima_data_ajuste"]
    )
    valido = conferir_travas(previsoes_avaliacao, previsoes_sarima_brutas)
    if not valido:
        print("\nBATERIA INVALIDA — travas nao bateram. Nada foi lido.", flush=True)
        return

    familia_j1 = montar_familia_j1_bate_regua(previsoes_avaliacao)
    familia_j2 = montar_familia_j2_melhora_b0(previsoes_avaliacao)

    previsoes_lasso_m0_avaliacao = conjunto.lasso_m0[conjunto.lasso_m0["data_alvo"] >= INICIO_DA_AVALIACAO]
    previsoes_lasso_avaliacao = previsoes_avaliacao[previsoes_avaliacao["braco"] == NOME_BRACO_LASSO]
    previsoes_avaliacao_com_m0 = pd.concat([previsoes_lasso_avaliacao, previsoes_lasso_m0_avaliacao], ignore_index=True)
    familia_j3 = montar_familia_j3_vetor_no_lasso(previsoes_avaliacao_com_m0)

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    # Todas as previsões, inclusive as do ensemble, para as leituras descritivas
    # da seção 4 (acrescentado em 25/09/2026: a primeira versão não gravava).
    previsoes_todas.to_csv(PASTA_DE_SAIDAS / "previsoes_por_braco.csv", index=False)
    familia_j1.to_csv(PASTA_DE_SAIDAS / "familia_j1_bate_regua.csv", index=False)
    familia_j2.to_csv(PASTA_DE_SAIDAS / "familia_j2_melhora_b0.csv", index=False)
    familia_j3.to_csv(PASTA_DE_SAIDAS / "familia_j3_vetor_no_lasso.csv", index=False)

    leitura_pesos_medios = gerar_leitura_pesos_medios_do_ens_pesos(previsoes_ens_pesos)
    leitura_pesos_medios.to_csv(PASTA_DE_SAIDAS / "leitura_pesos_medios_ens_pesos.csv", index=False)

    imprimir_criterios_de_decisao(familia_j1, familia_j2, familia_j3)
    gerar_figura_mae_por_horizonte(previsoes_avaliacao)
    print("\nConsolidacao concluida. CSVs e figura gravados em saidas/.", flush=True)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--rodar-tudo", action="store_true", dest="rodar_tudo")
    argumentos = parser.parse_args()

    nenhuma_acao_pedida = not any([argumentos.smoke, argumentos.rodar_tudo])
    if nenhuma_acao_pedida:
        parser.print_help()
        return

    if argumentos.smoke:
        rodar_smoke_test()

    if argumentos.rodar_tudo:
        rodar_bateria_completa()


if __name__ == "__main__":
    main()
