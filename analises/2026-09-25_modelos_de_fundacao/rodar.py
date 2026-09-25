"""Modelos de fundação (zero-shot) para dengue em Porto Alegre.

Contrato: PRE_DECLARACAO.md (a leitura obrigatória, escrita em 25/09/2026, ANTES de
qualquer previsão real com dado do projeto). Ambiente: AMBIENTE.md — este script só
roda com o interpretador de /Users/viniciusguerra/.venvs/aedes_modelos_fundacao/.

Pergunta do teste: um modelo pré-treinado em milhões de séries de outras áreas, sem
treinar na nossa série, prevê casos de dengue de Porto Alegre em até 3 meses melhor que
a regra "mesma semana do ano passado" e melhor que o `B0` (HistGB, folha mínima 20, com
vetor) do bloco 7 da bateria noturna de 23/09/2026?

Quatro braços, todos em modo zero-shot, configuração padrão da biblioteca, CPU:
    bolt_casos             — Chronos-Bolt base, só a série de casos.
    c2_casos                — Chronos-2, só a série de casos.
    c2_casos_clima          — Chronos-2, casos + clima (temp_media, temp_max,
                               umid_media, pressao_media) como past_covariates.
    c2_casos_clima_vetor    — Chronos-2, casos + clima + vetor
                               (aedes_aegypti_por_armadilha) como past_covariates.

Este arquivo NÃO importa nada do pacote `modelagem_aedes` nem do harness da bateria
noturna: ambos puxam dependências (scikit-learn em versão diferente, MLflow, etc.) que
não existem neste ambiente isolado. Os CSVs de entrada são lidos diretamente.

Uso:
    python rodar.py --smoke   # 5 origens da avaliação, todos os braços, sem gravar CSV
    python rodar.py --rodar   # bateria completa — cara, ver PRE_DECLARACAO.md
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy import stats


# ---------------------------------------------------------------------------
# 1. CAMINHOS E CONSTANTES DO CONTRATO
# ---------------------------------------------------------------------------

CAMINHO_DESTA_PASTA = Path(__file__).resolve().parent

CAMINHO_TABELA_FINAL = Path(
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/modelagem_aedes/dados/entradas/"
    "tabela_modelagem/tabela_final.csv"
)

CAMINHO_PREVISOES_B0 = Path(
    "/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/"
    "Meu Drive/Mestrado/Pesquisa/Meu_Projeto/analises/2026-09-23_bateria_noturna/"
    "bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv"
)

PASTA_SAIDAS = CAMINHO_DESTA_PASTA / "saidas"
PASTA_SAIDAS_SMOKE = PASTA_SAIDAS

# Colunas da tabela de insumos (tabela_final.csv).
COLUNA_DATA = "data_inicio_semana_epidemi"
COLUNA_CASOS = "casos_confirmados"
COLUNAS_CLIMA = ["temp_media", "temp_max", "umid_media", "pressao_media"]
COLUNA_VETOR = "aedes_aegypti_por_armadilha"

# Regra de construção do contexto, fixada na seção 2 da pré-declaração.
DATA_INICIO_CONTEXTO = pd.Timestamp("2018-02-18")

# Corte que define a "avaliação" (métrica primária, Wilcoxon, Holm) na seção 4.
DATA_CORTE_AVALIACAO = pd.Timestamp("2024-01-01")

# Horizontes exigidos pela seção 2: os mesmos pares (h, data_alvo) do B0.
HORIZONTES_SEMANAS = [1, 4, 8, 12]
PASSOS_PREVISTOS_POR_ORIGEM = 12  # Chronos prevê os 12 passos de uma vez (seção 2).

# Quantis previstos: o quantil de decisão do projeto (0,85) e a mediana, para as
# leituras descritivas da seção 4.
QUANTIL_MEDIANA = 0.5
QUANTIL_DECISAO = 0.85
QUANTIS_PREVISTOS = [QUANTIL_MEDIANA, QUANTIL_DECISAO]

NOME_BRACO_B0 = "HistGB_folha20_M1"
# A régua sazonal é calculada da própria série: casos em data_alvo - 52 semanas.
# ⚠️ Correção de 25/09/2026, antes da rodada: a primeira versão lia o braço
# "referencia" do bloco 7, que é o MODELO adotado, não a régua. A revisão
# pré-rodada achou o erro e a trava 5 o confirmou.
SEMANAS_DO_PASSO_SAZONAL = 52

NOMES_BRACOS_CHRONOS = [
    "bolt_casos",
    "c2_casos",
    "c2_casos_clima",
    "c2_casos_clima_vetor",
]

# Revisões travadas em AMBIENTE.md — nunca deixar `from_pretrained` resolver sozinho
# a revisão mais recente do repositório.
REVISAO_CHRONOS2 = "29ec3766d36d6f73f0696f85560a422f50e8498c"
REVISAO_CHRONOS_BOLT = "5d9f166d69f47aef3401367a7b842e78fe97b121"

REPOSITORIO_CHRONOS2 = "amazon/chronos-2"
REPOSITORIO_CHRONOS_BOLT = "amazon/chronos-bolt-base"

# Âncoras da seção 3, trava 5 — o B0 e a régua sazonal já rodados na bateria noturna
# precisam reproduzir estes MAE antes de qualquer leitura nova ser aceita.
MAE_ANCORA_B0_POR_HORIZONTE = {1: 133.6, 4: 199.6, 8: 223.2, 12: 243.8}
MAE_ANCORA_REGUA_POR_HORIZONTE = {1: 202.1, 4: 213.2, 8: 216.2, 12: 217.8}

# As âncoras têm 1 casa decimal no texto da pré-declaração; a folga absoluta cobre o
# arredondamento de leitura sem mascarar uma divergência real de dado ou pipeline.
# Decisão do agente (não coberta pela pré-declaração) — ver 'desvios_e_decisoes'.
TOLERANCIA_ABSOLUTA_ANCORA_MAE = 0.15

ALPHA_HOLM = 0.05

# Amostragem determinística das origens do smoke test (seção "o que o script faz").
N_ORIGENS_SMOKE = 5
SEMENTE_SORTEIO_SMOKE = 42


@dataclasses.dataclass(frozen=True)
class ConfiguracaoModeloFundacao:
    """Identifica um modelo de fundação a carregar via `from_pretrained`.

    Args:
        repositorio_huggingface: nome do repositório no HuggingFace Hub.
        revisao: hash de commit travado em AMBIENTE.md, para reprodutibilidade.
    """

    repositorio_huggingface: str
    revisao: str


CONFIGURACAO_CHRONOS2 = ConfiguracaoModeloFundacao(
    repositorio_huggingface=REPOSITORIO_CHRONOS2,
    revisao=REVISAO_CHRONOS2,
)
CONFIGURACAO_CHRONOS_BOLT = ConfiguracaoModeloFundacao(
    repositorio_huggingface=REPOSITORIO_CHRONOS_BOLT,
    revisao=REVISAO_CHRONOS_BOLT,
)


@dataclasses.dataclass(frozen=True)
class ParDeAvaliacao:
    """Um par (h, data_alvo) do B0, com origem e comparadores já resolvidos.

    Args:
        horizonte_semanas: horizonte de previsão h, em {1, 4, 8, 12}.
        data_alvo: semana que está sendo prevista.
        origem: `data_alvo - h` semanas — última data que qualquer braço pode ver.
        real: caso confirmado observado em `data_alvo`.
        previsto_b0: previsão do quantil 0,85 do B0 (HistGB_folha20_M1) para este par.
        previsto_regua: régua sazonal, casos confirmados em `data_alvo - 52` semanas.
    """

    horizonte_semanas: int
    data_alvo: pd.Timestamp
    origem: pd.Timestamp
    real: float
    previsto_b0: float
    previsto_regua: float


@dataclasses.dataclass(frozen=True)
class PrevisaoDeUmBraco:
    """Previsão de um braço para uma origem, nos 12 passos do horizonte.

    Args:
        origem: última data usada como contexto.
        ultima_data_do_contexto: repetida por braço para a trava 2 (sem futuro),
            gravada junto de cada previsão no CSV final.
        serie_q050: mediana prevista, passos 1 a 12 à frente da origem.
        serie_q085: quantil 0,85 previsto, passos 1 a 12 à frente da origem, já com
            o piso em zero aplicado (previsão negativa vira 0).
    """

    origem: pd.Timestamp
    ultima_data_do_contexto: pd.Timestamp
    serie_q050: np.ndarray
    serie_q085: np.ndarray


# ---------------------------------------------------------------------------
# 2. LEITURA DOS DADOS (só leitura, nunca gravação nas pastas de entrada)
# ---------------------------------------------------------------------------


def carregar_serie_temporal(caminho_tabela_final: Path) -> pd.DataFrame:
    """Carrega a tabela semanal de casos, clima e vetor.

    Args:
        caminho_tabela_final: caminho do `tabela_final.csv` do pipeline principal.

    Returns:
        DataFrame indexado por `COLUNA_DATA` (datetime, ordenado, semanal contínuo),
        com as colunas de casos, clima e vetor. Nulos do CSV (campo vazio) chegam
        como `NaN`, sem nenhum preenchimento — o tratamento de `NaN` é decidido em
        cada função de construção de covariável.

    Raises:
        KeyError: se alguma coluna obrigatória não estiver presente no CSV.
    """
    colunas_obrigatorias = {COLUNA_DATA, COLUNA_CASOS, COLUNA_VETOR}
    colunas_obrigatorias.update(COLUNAS_CLIMA)

    tabela_bruta = pd.read_csv(caminho_tabela_final)

    colunas_ausentes = colunas_obrigatorias.difference(tabela_bruta.columns)
    if colunas_ausentes:
        raise KeyError(f"Colunas obrigatórias ausentes em tabela_final.csv: {sorted(colunas_ausentes)}")

    tabela_bruta[COLUNA_DATA] = pd.to_datetime(tabela_bruta[COLUNA_DATA])
    tabela_ordenada = tabela_bruta.sort_values(COLUNA_DATA).set_index(COLUNA_DATA)

    diferencas_entre_semanas = tabela_ordenada.index.to_series().diff().dropna().unique()
    if len(diferencas_entre_semanas) != 1 or diferencas_entre_semanas[0] != pd.Timedelta(weeks=1):
        raise ValueError(
            "tabela_final.csv não é uma série semanal contínua: "
            f"passos encontrados = {diferencas_entre_semanas}"
        )

    return tabela_ordenada


def carregar_pares_de_avaliacao(
    caminho_previsoes_b0: Path,
    horizontes_semanas: list[int],
    nome_braco_b0: str,
    casos_confirmados: pd.Series,
) -> list[ParDeAvaliacao]:
    """Lê os pares (h, data_alvo) do B0 e calcula a régua sazonal de cada um.

    Estes pares definem EXATAMENTE o que os braços do Chronos devem prever (seção 2
    da pré-declaração): a origem de cada previsão é `data_alvo - h` semanas.

    Args:
        caminho_previsoes_b0: CSV `previsoes_por_braco.csv` do bloco 7 da bateria
            noturna, com colunas h, data_alvo, real, previsto, braco.
        horizontes_semanas: horizontes a manter, em {1, 4, 8, 12}.
        nome_braco_b0: rótulo do B0 dentro desse CSV (`HistGB_folha20_M1`).
        casos_confirmados: série semanal de casos indexada por data, de onde sai
            a régua: o valor em `data_alvo - 52` semanas.

    Returns:
        Lista de `ParDeAvaliacao`, um por (h, data_alvo), com o real e os dois
        comparadores já casados.

    Raises:
        KeyError: se colunas obrigatórias não estiverem presentes.
        ValueError: se a régua sazonal ficar vazia em algum par. A régua de
            25/09 mediu 0 pares vazios, então um vazio aqui indica dado mudado.
    """
    colunas_obrigatorias = {"h", "data_alvo", "real", "previsto", "braco"}

    previsoes_brutas = pd.read_csv(caminho_previsoes_b0)

    colunas_ausentes = colunas_obrigatorias.difference(previsoes_brutas.columns)
    if colunas_ausentes:
        raise KeyError(f"Colunas obrigatórias ausentes em previsoes_por_braco.csv: {sorted(colunas_ausentes)}")

    previsoes_brutas["data_alvo"] = pd.to_datetime(previsoes_brutas["data_alvo"])
    previsoes_dos_horizontes = previsoes_brutas[previsoes_brutas["h"].isin(horizontes_semanas)]

    previsoes_b0 = previsoes_dos_horizontes[previsoes_dos_horizontes["braco"] == nome_braco_b0]

    chave_b0 = set(zip(previsoes_b0["h"], previsoes_b0["data_alvo"]))

    previsoes_b0_indexadas = previsoes_b0.set_index(["h", "data_alvo"])
    atraso_sazonal = pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)

    pares_de_avaliacao: list[ParDeAvaliacao] = []

    for horizonte_semanas, data_alvo in sorted(chave_b0):
        linha_b0 = previsoes_b0_indexadas.loc[(horizonte_semanas, data_alvo)]
        semana_um_ano_antes = data_alvo - atraso_sazonal
        previsto_regua = float(casos_confirmados.get(semana_um_ano_antes, np.nan))
        if np.isnan(previsto_regua):
            raise ValueError(f"Régua sazonal vazia para h={horizonte_semanas}, data_alvo={data_alvo.date()}.")

        origem = data_alvo - pd.Timedelta(weeks=horizonte_semanas)

        par = ParDeAvaliacao(
            horizonte_semanas=horizonte_semanas,
            data_alvo=data_alvo,
            origem=origem,
            real=float(linha_b0["real"]),
            previsto_b0=float(linha_b0["previsto"]),
            previsto_regua=previsto_regua,
        )
        pares_de_avaliacao.append(par)

    return pares_de_avaliacao


# ---------------------------------------------------------------------------
# 3. TRAVAS DA SEÇÃO 3 — verificadas ANTES de qualquer leitura de resultado
# ---------------------------------------------------------------------------


def verificar_trava_pareamento(
    pares_de_avaliacao: list[ParDeAvaliacao],
    data_corte_avaliacao: pd.Timestamp,
    horizontes_semanas: list[int],
) -> None:
    """Trava 1: cada horizonte tem 102 semanas na avaliação (data_alvo >= corte).

    Raises:
        ValueError: se algum horizonte não tiver exatamente 102 pares na avaliação.
    """
    contagem_por_horizonte: dict[int, int] = {}
    for horizonte_semanas in horizontes_semanas:
        pares_do_horizonte_na_avaliacao = [
            par
            for par in pares_de_avaliacao
            if par.horizonte_semanas == horizonte_semanas and par.data_alvo >= data_corte_avaliacao
        ]
        contagem_por_horizonte[horizonte_semanas] = len(pares_do_horizonte_na_avaliacao)

    horizontes_fora_do_esperado = {
        horizonte_semanas: contagem
        for horizonte_semanas, contagem in contagem_por_horizonte.items()
        if contagem != 102
    }
    if horizontes_fora_do_esperado:
        raise ValueError(f"Trava 1 (pareamento) falhou. Contagens fora de 102: {horizontes_fora_do_esperado}")


def verificar_trava_sem_futuro(ultima_data_do_contexto: pd.Timestamp, origem: pd.Timestamp) -> None:
    """Trava 2: a última data do contexto de qualquer previsão é exatamente a origem.

    Raises:
        ValueError: se a última data do contexto for diferente da origem.
    """
    if ultima_data_do_contexto != origem:
        raise ValueError(
            "Trava 2 (sem futuro no contexto) falhou: "
            f"última data do contexto = {ultima_data_do_contexto}, origem = {origem}."
        )


def verificar_trava_coerencia(serie_q050: np.ndarray, serie_q085: np.ndarray) -> None:
    """Trava 4: q0,85 >= q0,5 em toda previsão.

    Raises:
        ValueError: se algum passo tiver q0,85 < q0,5.
    """
    if np.any(serie_q085 < serie_q050):
        passos_incoerentes = np.nonzero(serie_q085 < serie_q050)[0]
        raise ValueError(f"Trava 4 (coerência de quantis) falhou nos passos: {passos_incoerentes.tolist()}")


def verificar_trava_ancoras(
    pares_de_avaliacao: list[ParDeAvaliacao],
    data_corte_avaliacao: pd.Timestamp,
    horizontes_semanas: list[int],
    mae_ancora_b0: dict[int, float],
    mae_ancora_regua: dict[int, float],
    tolerancia_absoluta: float,
) -> None:
    """Trava 5: o B0 e a régua sazonal reproduzem o MAE âncora da pré-declaração.

    Recalcula o MAE do quantil 0,85 do B0 e da régua diretamente dos pares lidos
    (sem reaproveitar nenhum número já publicado), e compara contra as âncoras
    fixadas na seção 3 antes de qualquer leitura nova ser aceita.

    Raises:
        ValueError: se alguma âncora divergir além da tolerância.
    """
    divergencias: list[str] = []

    for horizonte_semanas in horizontes_semanas:
        pares_do_horizonte = [
            par
            for par in pares_de_avaliacao
            if par.horizonte_semanas == horizonte_semanas and par.data_alvo >= data_corte_avaliacao
        ]
        reais = np.array([par.real for par in pares_do_horizonte])
        previstos_b0 = np.array([par.previsto_b0 for par in pares_do_horizonte])
        previstos_regua = np.array([par.previsto_regua for par in pares_do_horizonte])

        mae_b0_medido = calcular_mae(reais, previstos_b0)
        mae_regua_medido = calcular_mae(reais, previstos_regua)

        diferenca_b0 = abs(mae_b0_medido - mae_ancora_b0[horizonte_semanas])
        diferenca_regua = abs(mae_regua_medido - mae_ancora_regua[horizonte_semanas])

        if diferenca_b0 > tolerancia_absoluta:
            divergencias.append(
                f"h={horizonte_semanas}: MAE B0 medido {mae_b0_medido:.2f} "
                f"!= âncora {mae_ancora_b0[horizonte_semanas]:.2f}"
            )
        if diferenca_regua > tolerancia_absoluta:
            divergencias.append(
                f"h={horizonte_semanas}: MAE régua medido {mae_regua_medido:.2f} "
                f"!= âncora {mae_ancora_regua[horizonte_semanas]:.2f}"
            )

    if divergencias:
        raise ValueError("Trava 5 (âncoras dos comparadores) falhou: " + "; ".join(divergencias))


# ---------------------------------------------------------------------------
# 4. CONSTRUÇÃO DE CONTEXTO E COVARIÁVEIS PARA UMA ORIGEM
# ---------------------------------------------------------------------------


def construir_contexto_de_casos(
    serie_temporal: pd.DataFrame,
    origem: pd.Timestamp,
    data_inicio_contexto: pd.Timestamp,
) -> pd.Series:
    """Recorta a série de casos de `data_inicio_contexto` até `origem`, inclusive.

    Args:
        serie_temporal: tabela semanal carregada por `carregar_serie_temporal`.
        origem: última semana visível para a previsão (nada depois entra).
        data_inicio_contexto: início fixo do contexto, 18/02/2018 (seção 2).

    Returns:
        Série de `casos_confirmados`, ordenada por data, de `data_inicio_contexto`
        até `origem` inclusive.

    Raises:
        ValueError: se `origem` não existir na série temporal.
    """
    if origem not in serie_temporal.index:
        raise ValueError(f"Origem {origem} não existe em tabela_final.csv.")

    contexto_de_casos = serie_temporal.loc[data_inicio_contexto:origem, COLUNA_CASOS]
    return contexto_de_casos


def construir_covariaveis_passadas(
    serie_temporal: pd.DataFrame,
    origem: pd.Timestamp,
    data_inicio_contexto: pd.Timestamp,
    nomes_das_colunas: list[str],
) -> dict[str, np.ndarray]:
    """Recorta as covariáveis passadas no mesmo intervalo do contexto de casos.

    Args:
        serie_temporal: tabela semanal carregada por `carregar_serie_temporal`.
        origem: última semana visível para a previsão.
        data_inicio_contexto: início fixo do contexto, 18/02/2018.
        nomes_das_colunas: nomes das covariáveis a recortar (clima e/ou vetor).

    Returns:
        Dicionário nome da covariável -> array 1-d, alinhado ponta a ponta com o
        contexto de casos. Buracos do dado original (ex.: enchente de 2024 no
        vetor) chegam como `NaN`, sem nenhum preenchimento.
    """
    covariaveis_passadas: dict[str, np.ndarray] = {}

    for nome_da_coluna in nomes_das_colunas:
        serie_da_covariavel = serie_temporal.loc[data_inicio_contexto:origem, nome_da_coluna]
        covariaveis_passadas[nome_da_coluna] = serie_da_covariavel.to_numpy(dtype=np.float32)

    return covariaveis_passadas


def truncar_previsao_negativa(valores_previstos: np.ndarray) -> np.ndarray:
    """Aplica o piso em zero da seção 2: previsão negativa vira 0.

    Args:
        valores_previstos: array de previsões, de qualquer quantil.

    Returns:
        Mesmo array, com todo valor negativo substituído por 0.0.
    """
    return np.maximum(valores_previstos, 0.0)


# ---------------------------------------------------------------------------
# 5. CARGA DOS MODELOS E PREVISÃO POR BRAÇO
# ---------------------------------------------------------------------------


def carregar_pipeline_chronos2(configuracao: ConfiguracaoModeloFundacao):
    """Carrega o Chronos-2 em CPU, na revisão travada em AMBIENTE.md."""
    from chronos import Chronos2Pipeline

    inicio = time.time()
    pipeline = Chronos2Pipeline.from_pretrained(
        configuracao.repositorio_huggingface,
        revision=configuracao.revisao,
        device_map="cpu",
    )
    print(
        f"[carga] Chronos-2 ({configuracao.repositorio_huggingface}@{configuracao.revisao[:8]}) "
        f"carregado em {time.time() - inicio:.1f}s.",
        flush=True,
    )
    return pipeline


def carregar_pipeline_chronos_bolt(configuracao: ConfiguracaoModeloFundacao):
    """Carrega o Chronos-Bolt base em CPU, na revisão travada em AMBIENTE.md."""
    from chronos import BaseChronosPipeline

    inicio = time.time()
    pipeline = BaseChronosPipeline.from_pretrained(
        configuracao.repositorio_huggingface,
        revision=configuracao.revisao,
        device_map="cpu",
    )
    print(
        f"[carga] Chronos-Bolt ({configuracao.repositorio_huggingface}@{configuracao.revisao[:8]}) "
        f"carregado em {time.time() - inicio:.1f}s.",
        flush=True,
    )
    return pipeline


def prever_braco_bolt_casos(
    pipeline_bolt,
    contexto_de_casos: pd.Series,
    origem: pd.Timestamp,
) -> PrevisaoDeUmBraco:
    """Prevê os 12 passos do braço `bolt_casos` (Chronos-Bolt, só casos).

    O Chronos-Bolt não aceita covariáveis (AMBIENTE.md) — este braço usa só a
    série de casos, exatamente como o `c2_casos` do Chronos-2.
    """
    tensor_de_contexto = torch.tensor(contexto_de_casos.to_numpy(dtype=np.float32))

    quantis_previstos, _ = pipeline_bolt.predict_quantiles(
        [tensor_de_contexto],
        prediction_length=PASSOS_PREVISTOS_POR_ORIGEM,
        quantile_levels=QUANTIS_PREVISTOS,
    )

    serie_q050 = quantis_previstos[0][:, 0].numpy()
    serie_q085 = quantis_previstos[0][:, 1].numpy()

    return PrevisaoDeUmBraco(
        origem=origem,
        ultima_data_do_contexto=contexto_de_casos.index.max(),
        serie_q050=serie_q050,
        serie_q085=truncar_previsao_negativa(serie_q085),
    )


def prever_braco_chronos2(
    pipeline_chronos2,
    contexto_de_casos: pd.Series,
    origem: pd.Timestamp,
    covariaveis_passadas: dict[str, np.ndarray] | None,
) -> PrevisaoDeUmBraco:
    """Prevê os 12 passos de um braço do Chronos-2 (com ou sem covariáveis).

    Args:
        pipeline_chronos2: `Chronos2Pipeline` já carregado.
        contexto_de_casos: série de casos de 18/02/2018 até a origem, inclusive.
        origem: última semana visível para a previsão.
        covariaveis_passadas: dicionário de covariáveis passadas (clima e/ou
            vetor), no formato exigido por `Chronos2Pipeline.predict`, ou `None`
            para o braço `c2_casos` (só casos, sem covariável nenhuma).
    """
    tensor_alvo = torch.tensor(contexto_de_casos.to_numpy(dtype=np.float32))

    if covariaveis_passadas is None:
        entrada = [tensor_alvo]
    else:
        covariaveis_em_tensor = {
            nome_da_covariavel: torch.tensor(valores)
            for nome_da_covariavel, valores in covariaveis_passadas.items()
        }
        entrada = [{"target": tensor_alvo, "past_covariates": covariaveis_em_tensor}]

    quantis_previstos, _ = pipeline_chronos2.predict_quantiles(
        entrada,
        prediction_length=PASSOS_PREVISTOS_POR_ORIGEM,
        quantile_levels=QUANTIS_PREVISTOS,
    )

    # Shape (n_variates=1, prediction_length, n_quantis); univariado aqui sempre.
    serie_q050 = quantis_previstos[0][0, :, 0].numpy()
    serie_q085 = quantis_previstos[0][0, :, 1].numpy()

    return PrevisaoDeUmBraco(
        origem=origem,
        ultima_data_do_contexto=contexto_de_casos.index.max(),
        serie_q050=serie_q050,
        serie_q085=truncar_previsao_negativa(serie_q085),
    )


def prever_todos_os_bracos_para_origem(
    pipeline_bolt,
    pipeline_chronos2,
    serie_temporal: pd.DataFrame,
    origem: pd.Timestamp,
) -> dict[str, PrevisaoDeUmBraco]:
    """Roda os 4 braços do Chronos para uma única origem.

    Monta o contexto de casos e as covariáveis uma vez, e reaproveita para os
    quatro braços — cada um usa um subconjunto diferente das mesmas séries.

    Returns:
        Dicionário nome do braço -> `PrevisaoDeUmBraco`, com os 12 passos.
    """
    contexto_de_casos = construir_contexto_de_casos(serie_temporal, origem, DATA_INICIO_CONTEXTO)
    verificar_trava_sem_futuro(contexto_de_casos.index.max(), origem)

    covariaveis_de_clima = construir_covariaveis_passadas(
        serie_temporal, origem, DATA_INICIO_CONTEXTO, COLUNAS_CLIMA
    )
    covariaveis_de_clima_e_vetor = construir_covariaveis_passadas(
        serie_temporal, origem, DATA_INICIO_CONTEXTO, COLUNAS_CLIMA + [COLUNA_VETOR]
    )

    previsoes_por_braco: dict[str, PrevisaoDeUmBraco] = {}

    previsoes_por_braco["bolt_casos"] = prever_braco_bolt_casos(pipeline_bolt, contexto_de_casos, origem)
    previsoes_por_braco["c2_casos"] = prever_braco_chronos2(
        pipeline_chronos2, contexto_de_casos, origem, covariaveis_passadas=None
    )
    previsoes_por_braco["c2_casos_clima"] = prever_braco_chronos2(
        pipeline_chronos2, contexto_de_casos, origem, covariaveis_passadas=covariaveis_de_clima
    )
    previsoes_por_braco["c2_casos_clima_vetor"] = prever_braco_chronos2(
        pipeline_chronos2, contexto_de_casos, origem, covariaveis_passadas=covariaveis_de_clima_e_vetor
    )

    for previsao_do_braco in previsoes_por_braco.values():
        verificar_trava_coerencia(previsao_do_braco.serie_q050, previsao_do_braco.serie_q085)

    return previsoes_por_braco


def testar_aceitacao_de_nan_em_past_covariates(
    pipeline_chronos2,
    serie_temporal: pd.DataFrame,
    origem_com_nan_no_vetor: pd.Timestamp,
) -> tuple[bool, str]:
    """Testa empiricamente se o Chronos-2 aceita `NaN` em `past_covariates`.

    A pré-declaração proíbe inventar solução caso não aceite (seção 2): este teste
    só relata o que aconteceu, para o orquestrador decidir e registrar emenda.

    Args:
        pipeline_chronos2: `Chronos2Pipeline` já carregado.
        serie_temporal: tabela semanal carregada por `carregar_serie_temporal`.
        origem_com_nan_no_vetor: uma origem cujo contexto de vetor contém `NaN`
            (ex.: qualquer origem posterior a 12/05/2024, dentro da enchente).

    Returns:
        Tupla (aceitou, mensagem). `aceitou` é `True` se `predict_quantiles` rodou
        sem lançar exceção; `mensagem` traz a exceção completa quando não aceitou.
    """
    contexto_de_casos = construir_contexto_de_casos(serie_temporal, origem_com_nan_no_vetor, DATA_INICIO_CONTEXTO)
    covariaveis_com_vetor = construir_covariaveis_passadas(
        serie_temporal, origem_com_nan_no_vetor, DATA_INICIO_CONTEXTO, [COLUNA_VETOR]
    )

    quantidade_de_nan = int(np.isnan(covariaveis_com_vetor[COLUNA_VETOR]).sum())
    if quantidade_de_nan == 0:
        return (
            False,
            f"Origem {origem_com_nan_no_vetor.date()} não tem NaN no vetor dentro do contexto; "
            "teste inconclusivo, escolher outra origem.",
        )

    try:
        prever_braco_chronos2(
            pipeline_chronos2,
            contexto_de_casos,
            origem_com_nan_no_vetor,
            covariaveis_passadas=covariaveis_com_vetor,
        )
    except Exception as erro:  # noqa: BLE001 — relatar qualquer falha, sem filtrar tipo.
        mensagem = f"Chronos-2 REJEITOU NaN em past_covariates ({quantidade_de_nan} NaN no contexto): {erro!r}"
        return False, mensagem

    mensagem = f"Chronos-2 ACEITOU NaN em past_covariates ({quantidade_de_nan} NaN no contexto do vetor)."
    return True, mensagem


# ---------------------------------------------------------------------------
# 6. MÉTRICAS, TESTE ESTATÍSTICO E CORREÇÃO DE HOLM
# ---------------------------------------------------------------------------


def calcular_mae(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """Erro absoluto médio entre o real e o previsto."""
    erros_absolutos = np.abs(valores_reais - valores_previstos)
    return float(np.mean(erros_absolutos))


def calcular_perda_quantilica(
    valores_reais: np.ndarray,
    valores_previstos: np.ndarray,
    quantil: float,
) -> float:
    """Perda quantílica (pinball loss) média no quantil informado.

    Args:
        valores_reais: valores observados.
        valores_previstos: previsão do quantil informado.
        quantil: nível do quantil previsto, entre 0 e 1.

    Returns:
        Perda quantílica média: `quantil * erro` quando `real >= previsto`, e
        `(quantil - 1) * erro` quando `real < previsto`.
    """
    erro = valores_reais - valores_previstos
    perda_por_semana = np.maximum(quantil * erro, (quantil - 1.0) * erro)
    return float(np.mean(perda_por_semana))


def calcular_cobertura_do_quantil(valores_reais: np.ndarray, valores_previstos_no_quantil: np.ndarray) -> float:
    """Fração de semanas em que o real ficou abaixo do quantil previsto."""
    return float(np.mean(valores_reais < valores_previstos_no_quantil))


def testar_wilcoxon_pareado(erro_absoluto_a: np.ndarray, erro_absoluto_b: np.ndarray) -> float:
    """Wilcoxon bilateral pareado entre o erro absoluto de dois braços.

    Se todas as diferenças forem zero, `scipy.stats.wilcoxon` lança `ValueError`;
    a pré-declaração (seção 4) define que, nesse caso, p = 1.

    Returns:
        p-valor bilateral do teste.
    """
    diferencas = erro_absoluto_a - erro_absoluto_b
    if np.all(diferencas == 0):
        return 1.0

    resultado_do_teste = stats.wilcoxon(erro_absoluto_a, erro_absoluto_b, alternative="two-sided")
    return float(resultado_do_teste.pvalue)


def aplicar_correcao_holm(p_valores: list[float]) -> list[float]:
    """Correção de Holm-Bonferroni (step-down), reimplementada do zero.

    Args:
        p_valores: p-valores brutos, na ordem em que serão reportados.

    Returns:
        p-valores ajustados, na MESMA ordem de `p_valores` (não na ordem
        ordenada internamente pelo algoritmo).
    """
    numero_de_comparacoes = len(p_valores)
    indices_ordenados_por_p_valor = sorted(
        range(numero_de_comparacoes),
        key=p_valores.__getitem__,
    )

    p_valores_ajustados_ordenados: list[float] = []
    maior_ajuste_ate_agora = 0.0

    for posicao_no_ranking, indice_original in enumerate(indices_ordenados_por_p_valor):
        fator_de_holm = numero_de_comparacoes - posicao_no_ranking
        ajuste_da_posicao = p_valores[indice_original] * fator_de_holm
        maior_ajuste_ate_agora = max(maior_ajuste_ate_agora, ajuste_da_posicao)
        p_valores_ajustados_ordenados.append(min(maior_ajuste_ate_agora, 1.0))

    p_valores_ajustados: list[float] = [0.0] * numero_de_comparacoes
    for posicao_no_ranking, indice_original in enumerate(indices_ordenados_por_p_valor):
        p_valores_ajustados[indice_original] = p_valores_ajustados_ordenados[posicao_no_ranking]

    return p_valores_ajustados


# ---------------------------------------------------------------------------
# 7. SELEÇÃO DE ORIGENS PARA O SMOKE TEST
# ---------------------------------------------------------------------------


def selecionar_pares_para_smoke_test(
    pares_de_avaliacao: list[ParDeAvaliacao],
    data_corte_avaliacao: pd.Timestamp,
    quantidade_de_origens: int,
    semente: int,
) -> list[ParDeAvaliacao]:
    """Sorteia pares (h, data_alvo) da avaliação para o smoke test.

    Sorteio determinístico (semente fixa): a mesma chamada sempre devolve os
    mesmos pares, para que a trava de determinismo (seção 3) seja verificável.

    Args:
        pares_de_avaliacao: todos os pares (h, data_alvo) do B0, já carregados.
        data_corte_avaliacao: só pares com `data_alvo >= data_corte_avaliacao`
            entram no sorteio.
        quantidade_de_origens: quantos pares sortear.
        semente: semente do gerador aleatório.

    Returns:
        Lista de `ParDeAvaliacao` sorteados, ordenada por (h, data_alvo).
    """
    pares_na_avaliacao = [par for par in pares_de_avaliacao if par.data_alvo >= data_corte_avaliacao]

    gerador_aleatorio = np.random.default_rng(semente)
    indices_sorteados = gerador_aleatorio.choice(
        len(pares_na_avaliacao),
        size=quantidade_de_origens,
        replace=False,
    )

    pares_sorteados = [pares_na_avaliacao[indice] for indice in sorted(indices_sorteados)]
    return pares_sorteados


# ---------------------------------------------------------------------------
# 8. SMOKE TEST
# ---------------------------------------------------------------------------


def executar_smoke_test() -> None:
    """Roda o smoke test: 5 origens da avaliação, todos os braços.

    Imprime as previsões e o resultado da checagem de NaN em past_covariates.
    Verifica as travas 2 (sem futuro) e 4 (coerência de quantis) em cada
    previsão. NÃO grava CSV de resultado final — só um log em texto, para
    conferência humana. Não roda a trava 1 (pareamento completo) nem a trava 5
    (âncoras), que exigem os pares completos da avaliação — só o `--rodar` os
    verifica antes de ler qualquer resultado, como manda a seção 3.
    """
    print("=== SMOKE TEST — modelos de fundação ===", flush=True)

    inicio_do_smoke = time.time()

    serie_temporal = carregar_serie_temporal(CAMINHO_TABELA_FINAL)
    pares_de_avaliacao = carregar_pares_de_avaliacao(
        CAMINHO_PREVISOES_B0, HORIZONTES_SEMANAS, NOME_BRACO_B0, serie_temporal[COLUNA_CASOS]
    )
    print(f"[dados] {len(pares_de_avaliacao)} pares (h, data_alvo) carregados do B0.", flush=True)

    pares_sorteados = selecionar_pares_para_smoke_test(
        pares_de_avaliacao, DATA_CORTE_AVALIACAO, N_ORIGENS_SMOKE, SEMENTE_SORTEIO_SMOKE
    )
    print(f"[dados] {len(pares_sorteados)} pares sorteados para o smoke test:", flush=True)
    for par in pares_sorteados:
        print(
            f"    h={par.horizonte_semanas:2d}  data_alvo={par.data_alvo.date()}  "
            f"origem={par.origem.date()}  real={par.real:.1f}  "
            f"B0={par.previsto_b0:.1f}  régua={par.previsto_regua:.1f}",
            flush=True,
        )

    pipeline_bolt = carregar_pipeline_chronos_bolt(CONFIGURACAO_CHRONOS_BOLT)
    pipeline_chronos2 = carregar_pipeline_chronos2(CONFIGURACAO_CHRONOS2)

    print("\n[nan] Checando se o Chronos-2 aceita NaN em past_covariates...", flush=True)
    origem_com_nan_no_vetor = max(par.origem for par in pares_sorteados)
    aceitou_nan, mensagem_do_teste_de_nan = testar_aceitacao_de_nan_em_past_covariates(
        pipeline_chronos2, serie_temporal, origem_com_nan_no_vetor
    )
    print(f"[nan] {mensagem_do_teste_de_nan}", flush=True)
    if not aceitou_nan:
        print(
            "[nan] PARADO por instrução da pré-declaração: não inventar solução para o NaN. "
            "O orquestrador decide e registra emenda antes de qualquer previsão real do braço com vetor.",
            flush=True,
        )
        return

    print("\n[previsao] Previsão dos 4 braços para cada origem sorteada:", flush=True)
    previsoes_da_primeira_passada: dict[pd.Timestamp, dict[str, PrevisaoDeUmBraco]] = {}

    for par in pares_sorteados:
        inicio_do_par = time.time()
        previsoes_do_par = prever_todos_os_bracos_para_origem(
            pipeline_bolt, pipeline_chronos2, serie_temporal, par.origem
        )
        previsoes_da_primeira_passada[par.origem] = previsoes_do_par

        print(
            f"  origem={par.origem.date()} (h={par.horizonte_semanas}, "
            f"data_alvo={par.data_alvo.date()}, real={par.real:.1f}) "
            f"— {time.time() - inicio_do_par:.2f}s",
            flush=True,
        )
        for nome_do_braco in NOMES_BRACOS_CHRONOS:
            previsao = previsoes_do_par[nome_do_braco]
            passo_do_horizonte = par.horizonte_semanas - 1
            q050_no_horizonte = previsao.serie_q050[passo_do_horizonte]
            q085_no_horizonte = previsao.serie_q085[passo_do_horizonte]
            print(
                f"      {nome_do_braco:<22} q0.50={q050_no_horizonte:8.2f}  q0.85={q085_no_horizonte:8.2f}",
                flush=True,
            )

    print("\n[determinismo] Repetindo a previsão das mesmas origens (trava 3)...", flush=True)
    divergencias_de_determinismo: list[str] = []

    for par in pares_sorteados:
        previsoes_repetidas = prever_todos_os_bracos_para_origem(
            pipeline_bolt, pipeline_chronos2, serie_temporal, par.origem
        )
        previsoes_originais = previsoes_da_primeira_passada[par.origem]

        for nome_do_braco in NOMES_BRACOS_CHRONOS:
            q085_original = previsoes_originais[nome_do_braco].serie_q085
            q085_repetido = previsoes_repetidas[nome_do_braco].serie_q085
            if not np.array_equal(q085_original, q085_repetido):
                divergencias_de_determinismo.append(f"origem={par.origem.date()} braco={nome_do_braco}")

    if divergencias_de_determinismo:
        print(f"[determinismo] TRAVA 3 FALHOU em: {divergencias_de_determinismo}", flush=True)
    else:
        print("[determinismo] Trava 3 OK — resultado idêntico na repetição.", flush=True)

    print(f"\n=== SMOKE TEST concluído em {time.time() - inicio_do_smoke:.1f}s ===", flush=True)


# ---------------------------------------------------------------------------
# 9. BATERIA COMPLETA (--rodar) — NÃO EXECUTADA NESTA RODADA
# ---------------------------------------------------------------------------


def verificar_trava_determinismo(
    pipeline_bolt,
    pipeline_chronos2,
    serie_temporal: pd.DataFrame,
    pares_de_avaliacao: list[ParDeAvaliacao],
    previsoes_por_origem: dict[pd.Timestamp, dict[str, "PrevisaoDeUmBraco"]],
) -> None:
    """Trava 3: 5 origens sorteadas, previstas de novo, dão resultado idêntico.

    Acrescentada à rodada completa em 25/09/2026 por apontamento da revisão
    pré-rodada: antes ela só existia no smoke test.

    Raises:
        RuntimeError: se algum braço der q0,85 diferente na repetição.
    """
    pares_sorteados = selecionar_pares_para_smoke_test(
        pares_de_avaliacao, DATA_CORTE_AVALIACAO, N_ORIGENS_SMOKE, SEMENTE_SORTEIO_SMOKE
    )
    divergencias_de_determinismo: list[str] = []

    for par in pares_sorteados:
        previsoes_repetidas = prever_todos_os_bracos_para_origem(
            pipeline_bolt, pipeline_chronos2, serie_temporal, par.origem
        )
        previsoes_originais = previsoes_por_origem[par.origem]

        for nome_do_braco in NOMES_BRACOS_CHRONOS:
            q085_original = previsoes_originais[nome_do_braco].serie_q085
            q085_repetido = previsoes_repetidas[nome_do_braco].serie_q085
            if not np.array_equal(q085_original, q085_repetido):
                divergencias_de_determinismo.append(f"origem={par.origem.date()} braco={nome_do_braco}")

    if divergencias_de_determinismo:
        raise RuntimeError(f"Trava 3 falhou: {divergencias_de_determinismo}")


def executar_bateria_completa() -> None:
    """Roda a bateria completa: todos os pares do B0, travas 1 e 5, métricas,
    Wilcoxon + Holm das famílias H1/H2/H3, leituras descritivas, CSVs e figura.

    Esta função implementa o contrato da pré-declaração na íntegra, mas não foi
    executada nesta entrega — a tarefa pediu explicitamente só o smoke test. Uma
    rodada completa cobre ~300 origens distintas em 4 braços e deve ser avisada
    ANTES, com estimativa medida (regra global de rodada longa de CPU).
    """
    inicio_da_bateria = time.time()

    serie_temporal = carregar_serie_temporal(CAMINHO_TABELA_FINAL)
    pares_de_avaliacao = carregar_pares_de_avaliacao(
        CAMINHO_PREVISOES_B0, HORIZONTES_SEMANAS, NOME_BRACO_B0, serie_temporal[COLUNA_CASOS]
    )

    verificar_trava_pareamento(pares_de_avaliacao, DATA_CORTE_AVALIACAO, HORIZONTES_SEMANAS)
    verificar_trava_ancoras(
        pares_de_avaliacao,
        DATA_CORTE_AVALIACAO,
        HORIZONTES_SEMANAS,
        MAE_ANCORA_B0_POR_HORIZONTE,
        MAE_ANCORA_REGUA_POR_HORIZONTE,
        TOLERANCIA_ABSOLUTA_ANCORA_MAE,
    )
    print("[travas] Travas 1 e 5 OK — pareamento e âncoras conferem.", flush=True)

    pipeline_bolt = carregar_pipeline_chronos_bolt(CONFIGURACAO_CHRONOS_BOLT)
    pipeline_chronos2 = carregar_pipeline_chronos2(CONFIGURACAO_CHRONOS2)

    origens_unicas = sorted({par.origem for par in pares_de_avaliacao})
    print(f"[previsao] {len(origens_unicas)} origens distintas a prever, 4 braços cada.", flush=True)

    previsoes_por_origem: dict[pd.Timestamp, dict[str, PrevisaoDeUmBraco]] = {}
    for numero_da_origem, origem in enumerate(origens_unicas, start=1):
        inicio_da_origem = time.time()
        previsoes_por_origem[origem] = prever_todos_os_bracos_para_origem(
            pipeline_bolt, pipeline_chronos2, serie_temporal, origem
        )
        if numero_da_origem % 25 == 0 or numero_da_origem == len(origens_unicas):
            print(
                f"    {numero_da_origem}/{len(origens_unicas)} origens previstas "
                f"({time.time() - inicio_da_origem:.2f}s a última).",
                flush=True,
            )

    verificar_trava_determinismo(pipeline_bolt, pipeline_chronos2, serie_temporal, pares_de_avaliacao, previsoes_por_origem)
    print("[travas] Trava 3 OK — 5 origens repetidas deram resultado idêntico.", flush=True)

    linhas_do_csv_de_previsoes = montar_linhas_do_csv_de_previsoes(
        pares_de_avaliacao, previsoes_por_origem, NOMES_BRACOS_CHRONOS
    )
    tabela_de_previsoes = pd.DataFrame(linhas_do_csv_de_previsoes)

    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    caminho_csv_previsoes = PASTA_SAIDAS / "previsoes_por_braco.csv"
    tabela_de_previsoes.to_csv(caminho_csv_previsoes, index=False)
    print(f"[gravação] {caminho_csv_previsoes} gravado ({len(tabela_de_previsoes)} linhas).", flush=True)

    # O CSV grava as datas como texto ISO; as comparações pareiam com os pares do
    # B0, que têm datas em datetime. Sem a conversão, o merge por data_alvo falha.
    for coluna_de_data in ("origem", "data_alvo", "ultima_data_do_contexto"):
        tabela_de_previsoes[coluna_de_data] = pd.to_datetime(tabela_de_previsoes[coluna_de_data])

    calcular_e_gravar_familias_de_teste(tabela_de_previsoes, pares_de_avaliacao)
    calcular_e_gravar_leituras_descritivas(tabela_de_previsoes, pares_de_avaliacao)
    gravar_figura_mae_por_horizonte(tabela_de_previsoes, pares_de_avaliacao)

    print(f"[fim] Bateria completa em {time.time() - inicio_da_bateria:.1f}s.", flush=True)


def montar_linhas_do_csv_de_previsoes(
    pares_de_avaliacao: list[ParDeAvaliacao],
    previsoes_por_origem: dict[pd.Timestamp, dict[str, PrevisaoDeUmBraco]],
    nomes_dos_bracos: list[str],
) -> list[dict]:
    """Monta as linhas do CSV final: h, origem, data_alvo, contexto, real, quantis, braço."""
    linhas: list[dict] = []

    for par in pares_de_avaliacao:
        previsoes_da_origem = previsoes_por_origem[par.origem]
        passo_do_horizonte = par.horizonte_semanas - 1

        for nome_do_braco in nomes_dos_bracos:
            previsao = previsoes_da_origem[nome_do_braco]
            linha = {
                "h": par.horizonte_semanas,
                "origem": par.origem.date().isoformat(),
                "data_alvo": par.data_alvo.date().isoformat(),
                "ultima_data_do_contexto": previsao.ultima_data_do_contexto.date().isoformat(),
                "real": par.real,
                "q050": float(previsao.serie_q050[passo_do_horizonte]),
                "q085": float(previsao.serie_q085[passo_do_horizonte]),
                "braco": nome_do_braco,
            }
            linhas.append(linha)

    return linhas


def calcular_e_gravar_familias_de_teste(
    tabela_de_previsoes: pd.DataFrame,
    pares_de_avaliacao: list[ParDeAvaliacao],
) -> None:
    """Famílias H1, H2 e H3 da seção 4: Wilcoxon pareado + Holm, MAE q0,85."""
    tabela_de_pares = pd.DataFrame(
        {
            "h": [par.horizonte_semanas for par in pares_de_avaliacao],
            "data_alvo": [par.data_alvo for par in pares_de_avaliacao],
            "real": [par.real for par in pares_de_avaliacao],
            "previsto_b0": [par.previsto_b0 for par in pares_de_avaliacao],
            "previsto_regua": [par.previsto_regua for par in pares_de_avaliacao],
        }
    )
    tabela_de_pares_na_avaliacao = tabela_de_pares[tabela_de_pares["data_alvo"] >= DATA_CORTE_AVALIACAO]

    tabela_dos_bracos_na_avaliacao = tabela_de_previsoes.merge(
        tabela_de_pares_na_avaliacao[["h", "data_alvo"]],
        left_on=["h", "data_alvo"],
        right_on=["h", "data_alvo"],
    )

    linhas_h1: list[dict] = []
    linhas_h2: list[dict] = []
    linhas_h3: list[dict] = []

    for horizonte_semanas in HORIZONTES_SEMANAS:
        pares_do_horizonte = tabela_de_pares_na_avaliacao[tabela_de_pares_na_avaliacao["h"] == horizonte_semanas]
        erro_absoluto_regua = np.abs(pares_do_horizonte["real"] - pares_do_horizonte["previsto_regua"]).to_numpy()
        erro_absoluto_b0 = np.abs(pares_do_horizonte["real"] - pares_do_horizonte["previsto_b0"]).to_numpy()

        for nome_do_braco in NOMES_BRACOS_CHRONOS:
            previsoes_do_braco = tabela_dos_bracos_na_avaliacao[
                (tabela_dos_bracos_na_avaliacao["braco"] == nome_do_braco)
                & (tabela_dos_bracos_na_avaliacao["h"] == horizonte_semanas)
            ].sort_values("data_alvo")

            erro_absoluto_braco = np.abs(previsoes_do_braco["real"] - previsoes_do_braco["q085"]).to_numpy()

            if horizonte_semanas in (4, 8, 12):
                p_valor_h1 = testar_wilcoxon_pareado(erro_absoluto_braco, erro_absoluto_regua)
                linhas_h1.append({"braco": nome_do_braco, "h": horizonte_semanas, "p_bruto": p_valor_h1})

            p_valor_h2 = testar_wilcoxon_pareado(erro_absoluto_braco, erro_absoluto_b0)
            linhas_h2.append({"braco": nome_do_braco, "h": horizonte_semanas, "p_bruto": p_valor_h2})

        previsoes_com_vetor = tabela_dos_bracos_na_avaliacao[
            (tabela_dos_bracos_na_avaliacao["braco"] == "c2_casos_clima_vetor")
            & (tabela_dos_bracos_na_avaliacao["h"] == horizonte_semanas)
        ].sort_values("data_alvo")
        previsoes_sem_vetor = tabela_dos_bracos_na_avaliacao[
            (tabela_dos_bracos_na_avaliacao["braco"] == "c2_casos_clima")
            & (tabela_dos_bracos_na_avaliacao["h"] == horizonte_semanas)
        ].sort_values("data_alvo")

        erro_absoluto_com_vetor = np.abs(previsoes_com_vetor["real"] - previsoes_com_vetor["q085"]).to_numpy()
        erro_absoluto_sem_vetor = np.abs(previsoes_sem_vetor["real"] - previsoes_sem_vetor["q085"]).to_numpy()
        p_valor_h3 = testar_wilcoxon_pareado(erro_absoluto_com_vetor, erro_absoluto_sem_vetor)
        linhas_h3.append({"h": horizonte_semanas, "p_bruto": p_valor_h3})

    gravar_familia_com_holm(linhas_h1, "familia_h1_bate_regua.csv")
    gravar_familia_com_holm(linhas_h2, "familia_h2_melhora_b0.csv")
    gravar_familia_com_holm(linhas_h3, "familia_h3_vetor_no_chronos2.csv")


def gravar_familia_com_holm(linhas: list[dict], nome_do_arquivo: str) -> None:
    """Aplica Holm sobre os p-valores brutos de uma família e grava o CSV."""
    tabela_da_familia = pd.DataFrame(linhas)
    tabela_da_familia["p_holm"] = aplicar_correcao_holm(tabela_da_familia["p_bruto"].tolist())

    caminho_do_arquivo = PASTA_SAIDAS / nome_do_arquivo
    tabela_da_familia.to_csv(caminho_do_arquivo, index=False)
    print(f"[gravação] {caminho_do_arquivo} gravado ({len(tabela_da_familia)} linhas).", flush=True)


def calcular_e_gravar_leituras_descritivas(
    tabela_de_previsoes: pd.DataFrame,
    pares_de_avaliacao: list[ParDeAvaliacao],
) -> None:
    """Leituras descritivas da seção 4: MAE da mediana, perda quantílica,
    cobertura, MAE por ano do alvo e por faixa de `real`."""
    tabela_de_previsoes_com_data = tabela_de_previsoes.copy()
    tabela_de_previsoes_com_data["data_alvo"] = pd.to_datetime(tabela_de_previsoes_com_data["data_alvo"])
    tabela_de_previsoes_com_data["ano_do_alvo"] = tabela_de_previsoes_com_data["data_alvo"].dt.year

    linhas_descritivas: list[dict] = []

    for nome_do_braco in NOMES_BRACOS_CHRONOS:
        previsoes_do_braco = tabela_de_previsoes_com_data[tabela_de_previsoes_com_data["braco"] == nome_do_braco]

        for horizonte_semanas in HORIZONTES_SEMANAS:
            previsoes_do_horizonte = previsoes_do_braco[previsoes_do_braco["h"] == horizonte_semanas]

            reais = previsoes_do_horizonte["real"].to_numpy()
            q050 = previsoes_do_horizonte["q050"].to_numpy()
            q085 = previsoes_do_horizonte["q085"].to_numpy()

            linha = {
                "braco": nome_do_braco,
                "h": horizonte_semanas,
                "mae_mediana": calcular_mae(reais, q050),
                "perda_quantilica_085": calcular_perda_quantilica(reais, q085, QUANTIL_DECISAO),
                "cobertura_q085": calcular_cobertura_do_quantil(reais, q085),
                "mae_calibracao_2022_2023": calcular_mae_por_intervalo_de_anos(
                    previsoes_do_horizonte, 2022, 2023
                ),
                "mae_real_maior_ou_igual_100": calcular_mae_por_faixa_de_real(
                    previsoes_do_horizonte, real_minimo=100.0
                ),
                "mae_real_menor_que_100": calcular_mae_por_faixa_de_real(
                    previsoes_do_horizonte, real_maximo=100.0
                ),
            }
            linhas_descritivas.append(linha)

            for ano in sorted(previsoes_do_horizonte["ano_do_alvo"].unique()):
                previsoes_do_ano = previsoes_do_horizonte[previsoes_do_horizonte["ano_do_alvo"] == ano]
                linhas_descritivas.append(
                    {
                        "braco": nome_do_braco,
                        "h": horizonte_semanas,
                        "ano_do_alvo": int(ano),
                        "mae_do_ano": calcular_mae(
                            previsoes_do_ano["real"].to_numpy(), previsoes_do_ano["q085"].to_numpy()
                        ),
                    }
                )

    tabela_descritiva = pd.DataFrame(linhas_descritivas)
    caminho_do_arquivo = PASTA_SAIDAS / "leituras_descritivas.csv"
    tabela_descritiva.to_csv(caminho_do_arquivo, index=False)
    print(f"[gravação] {caminho_do_arquivo} gravado ({len(tabela_descritiva)} linhas).", flush=True)


def calcular_mae_por_intervalo_de_anos(
    previsoes_do_horizonte: pd.DataFrame,
    ano_minimo: int,
    ano_maximo: int,
) -> float:
    """MAE do q0,85 restrito a `data_alvo` com ano entre `ano_minimo` e `ano_maximo`."""
    mascara_do_intervalo = (previsoes_do_horizonte["ano_do_alvo"] >= ano_minimo) & (
        previsoes_do_horizonte["ano_do_alvo"] <= ano_maximo
    )
    previsoes_do_intervalo = previsoes_do_horizonte[mascara_do_intervalo]
    return calcular_mae(previsoes_do_intervalo["real"].to_numpy(), previsoes_do_intervalo["q085"].to_numpy())


def calcular_mae_por_faixa_de_real(
    previsoes_do_horizonte: pd.DataFrame,
    real_minimo: float | None = None,
    real_maximo: float | None = None,
) -> float:
    """MAE do q0,85 restrito a uma faixa de `real` (>= mínimo e/ou < máximo)."""
    previsoes_da_faixa = previsoes_do_horizonte
    if real_minimo is not None:
        previsoes_da_faixa = previsoes_da_faixa[previsoes_da_faixa["real"] >= real_minimo]
    if real_maximo is not None:
        previsoes_da_faixa = previsoes_da_faixa[previsoes_da_faixa["real"] < real_maximo]
    return calcular_mae(previsoes_da_faixa["real"].to_numpy(), previsoes_da_faixa["q085"].to_numpy())


def gravar_figura_mae_por_horizonte(
    tabela_de_previsoes: pd.DataFrame,
    pares_de_avaliacao: list[ParDeAvaliacao],
) -> None:
    """Figura com o MAE do q0,85 por horizonte: os 4 braços, o B0 e a régua tracejada."""
    import matplotlib.pyplot as figura_matplotlib  # import tardio: só a bateria completa desenha figura.

    tabela_de_pares = pd.DataFrame(
        {
            "h": [par.horizonte_semanas for par in pares_de_avaliacao],
            "data_alvo": [par.data_alvo for par in pares_de_avaliacao],
            "real": [par.real for par in pares_de_avaliacao],
            "previsto_b0": [par.previsto_b0 for par in pares_de_avaliacao],
            "previsto_regua": [par.previsto_regua for par in pares_de_avaliacao],
        }
    )
    tabela_de_pares_na_avaliacao = tabela_de_pares[tabela_de_pares["data_alvo"] >= DATA_CORTE_AVALIACAO]

    tabela_de_previsoes_com_data = tabela_de_previsoes.copy()
    tabela_de_previsoes_com_data["data_alvo"] = pd.to_datetime(tabela_de_previsoes_com_data["data_alvo"])
    tabela_dos_bracos_na_avaliacao = tabela_de_previsoes_com_data.merge(
        tabela_de_pares_na_avaliacao[["h", "data_alvo"]],
        on=["h", "data_alvo"],
    )

    figura, eixo = figura_matplotlib.subplots(figsize=(8, 5))

    for nome_do_braco in NOMES_BRACOS_CHRONOS:
        maes_por_horizonte: list[float] = []
        for horizonte_semanas in HORIZONTES_SEMANAS:
            previsoes_do_braco_e_horizonte = tabela_dos_bracos_na_avaliacao[
                (tabela_dos_bracos_na_avaliacao["braco"] == nome_do_braco)
                & (tabela_dos_bracos_na_avaliacao["h"] == horizonte_semanas)
            ]
            mae_do_horizonte = calcular_mae(
                previsoes_do_braco_e_horizonte["real"].to_numpy(),
                previsoes_do_braco_e_horizonte["q085"].to_numpy(),
            )
            maes_por_horizonte.append(mae_do_horizonte)
        eixo.plot(HORIZONTES_SEMANAS, maes_por_horizonte, marker="o", label=nome_do_braco)

    maes_do_b0 = [MAE_ANCORA_B0_POR_HORIZONTE[h] for h in HORIZONTES_SEMANAS]
    maes_da_regua = [MAE_ANCORA_REGUA_POR_HORIZONTE[h] for h in HORIZONTES_SEMANAS]
    eixo.plot(HORIZONTES_SEMANAS, maes_do_b0, marker="s", label="B0 (HistGB folha20)", color="black")
    eixo.plot(HORIZONTES_SEMANAS, maes_da_regua, linestyle="--", label="régua sazonal", color="gray")

    eixo.set_xlabel("horizonte (semanas)")
    eixo.set_ylabel("MAE do q0,85 (casos confirmados)")
    eixo.set_title("Modelos de fundação zero-shot x B0 x régua sazonal — avaliação 2024+")
    eixo.legend()
    figura.tight_layout()

    caminho_da_figura = PASTA_SAIDAS / "figura_mae_por_horizonte.png"
    figura.savefig(caminho_da_figura, dpi=150)
    print(f"[gravação] {caminho_da_figura} gravado.", flush=True)


# ---------------------------------------------------------------------------
# 10. METADADOS DOS MODELOS (data de publicação no HuggingFace)
# ---------------------------------------------------------------------------


def registrar_datas_de_publicacao_dos_modelos() -> None:
    """Consulta `model_info` no HuggingFace Hub para os dois repositórios.

    A pré-declaração (seção 6) afirma que o Chronos-2 é de outubro/2025 e o
    Chronos-Bolt de fim de 2024 — a ameaça de contaminação do pré-treino
    depende dessas datas. Este print serve para conferir ou contestar a
    afirmação com o dado oficial do Hub.
    """
    from huggingface_hub import model_info

    for repositorio, revisao in (
        (REPOSITORIO_CHRONOS2, REVISAO_CHRONOS2),
        (REPOSITORIO_CHRONOS_BOLT, REVISAO_CHRONOS_BOLT),
    ):
        informacoes_do_modelo = model_info(repositorio, revision=revisao)
        print(
            f"[hub] {repositorio}@{revisao[:8]} — "
            f"created_at={informacoes_do_modelo.created_at} "
            f"last_modified={informacoes_do_modelo.last_modified}",
            flush=True,
        )


# ---------------------------------------------------------------------------
# 11. ORQUESTRAÇÃO (CLI)
# ---------------------------------------------------------------------------


def construir_analisador_de_argumentos() -> argparse.ArgumentParser:
    """Define a CLI: `--smoke` ou `--rodar`, mutuamente exclusivos."""
    analisador = argparse.ArgumentParser(description=__doc__)
    grupo_mutuamente_exclusivo = analisador.add_mutually_exclusive_group(required=True)
    grupo_mutuamente_exclusivo.add_argument(
        "--smoke", action="store_true", help="5 origens da avaliação, todos os braços, sem gravar CSV final."
    )
    grupo_mutuamente_exclusivo.add_argument(
        "--rodar", action="store_true", help="Bateria completa — cara, ver PRE_DECLARACAO.md."
    )
    return analisador


def main() -> None:
    analisador = construir_analisador_de_argumentos()
    argumentos = analisador.parse_args()

    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)

    if argumentos.smoke:
        registrar_datas_de_publicacao_dos_modelos()
        executar_smoke_test()
        return

    if argumentos.rodar:
        registrar_datas_de_publicacao_dos_modelos()
        executar_bateria_completa()
        return


if __name__ == "__main__":
    main()
