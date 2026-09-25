"""Régua de regras simples contra os modelos ja rodados da bateria noturna.

Pergunta que este script responde: os modelos de previsao de casos de dengue
do projeto batem tres regras simples de previsao, sem nenhum aprendizado de
maquina? A resposta vira a regua oficial das proximas rodadas.

Este script NAO treina nenhum modelo novo. So le previsoes ja gravadas em
disco (`previsoes_por_braco.csv` dos blocos 5 e 7 da bateria noturna de
23/09/2026) e a tabela semanal de casos (`tabela_final.csv`), e a partir dela
calcula tres regras de bom senso — persistencia, sazonal e climatologia — para
comparar contra os 9 bracos de modelo ja existentes.

⚠️ NAO le nem toca em `arquivos_secretaria_saude_poa/` (dados pessoais).
⚠️ NAO roda `preparar_dados.py`. NAO usa git.
"""

import dataclasses
import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, r2_score

# ============================================================================
# CAMINHOS (somente leitura nas entradas; gravacao restrita a este teste)
# ============================================================================

PASTA_DESTE_TESTE = pathlib.Path(__file__).resolve().parent
PASTA_DO_PROJETO = PASTA_DESTE_TESTE.parent.parent
PASTA_DE_SAIDAS = PASTA_DESTE_TESTE / "saidas"

CAMINHO_BLOCO_7 = (
    PASTA_DO_PROJETO
    / "analises/2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20"
    / "saidas/previsoes_por_braco.csv"
)
CAMINHO_BLOCO_5 = (
    PASTA_DO_PROJETO
    / "analises/2026-09-23_bateria_noturna/bloco_5_algoritmos"
    / "saidas/previsoes_por_braco.csv"
)
CAMINHO_TABELA_FINAL = (
    PASTA_DO_PROJETO
    / "modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv"
)

COLUNA_DATA_ALVO_ORIGEM = "data_alvo"
COLUNA_H_ORIGEM = "h"
COLUNA_REAL_ORIGEM = "real"
COLUNA_PREVISTO_ORIGEM = "previsto"
COLUNA_BRACO_ORIGEM = "braco"

COLUNA_DATA_SEMANA = "data_inicio_semana_epidemi"
COLUNA_CASOS = "casos_confirmados"

# Braco do bloco 5 que e, na pratica, a mesma configuracao da referencia do
# bloco 7 (HistGB, quantil 0,85, com vetor). Precisa ser CONFERIDO, nunca
# assumido: e o motivo da funcao `conferir_duplicata_historgb_m1`.
NOME_REFERENCIA_BLOCO_7 = "referencia"
NOME_DUPLICATA_ESPERADA_BLOCO_5 = "HistGB_M1"


# ============================================================================
# CONSTANTES DE NEGOCIO
# ============================================================================

INICIO_CALIBRACAO_EPIDEMICA = pd.Timestamp("2022-01-01")
INICIO_DA_AVALIACAO = pd.Timestamp("2024-01-01")

NOME_PERIODO_CALIBRACAO = "calibracao"
NOME_PERIODO_CALIBRACAO_EPIDEMICA = "calibracao_epidemica"
NOME_PERIODO_AVALIACAO = "avaliacao"
# Os tres periodos NAO particionam as semanas: calibracao_epidemica e um
# subconjunto de calibracao. Sao tres recortes pedidos separadamente, nao tres
# fatias mutuamente exclusivas.
NOMES_DOS_PERIODOS = (
    NOME_PERIODO_CALIBRACAO,
    NOME_PERIODO_CALIBRACAO_EPIDEMICA,
    NOME_PERIODO_AVALIACAO,
)

HORIZONTES_DO_PROJETO = tuple(range(1, 13))
HORIZONTES_DA_COMPARACAO_PAREADA = (1, 4, 8, 12)
HORIZONTES_DO_TETO = (4, 8, 12)

QUANTIL_DA_PERDA_QUANTILICA = 0.85
NIVEL_DE_SIGNIFICANCIA = 0.05
SEMANAS_DO_PASSO_SAZONAL = 52

NOME_REGRA_PERSISTENCIA = "persistencia"
NOME_REGRA_SAZONAL = "sazonal"
NOME_REGRA_CLIMATOLOGIA = "climatologia"
NOMES_DAS_REGRAS_SIMPLES = (
    NOME_REGRA_PERSISTENCIA,
    NOME_REGRA_SAZONAL,
    NOME_REGRA_CLIMATOLOGIA,
)

ENTIDADE_TIPO_MODELO = "modelo"
ENTIDADE_TIPO_REGRA = "regra"

TOLERANCIA_DE_DIVERGENCIA_REAL = 1e-6


# ============================================================================
# ANCORAS NUMERICAS (medidas pelo orquestrador em 25/09/2026)
#
# Avaliacao = data_alvo >= 2024-01-01, 102 semanas por horizonte. O script TEM
# que reproduzir estes numeros. Se algum divergir, a regra do projeto e
# INVESTIGAR a causa e relatar — nunca ajustar o calculo para bater.
# ============================================================================

ANCORAS_MAE_AVALIACAO = {
    (1, "referencia"): 98.0,
    (1, "HistGB_folha20_M1"): 133.6,
    (1, NOME_REGRA_PERSISTENCIA): 83.3,
    (1, NOME_REGRA_SAZONAL): 202.1,
    (4, "referencia"): 219.7,
    (4, "HistGB_folha20_M1"): 199.6,
    (4, NOME_REGRA_PERSISTENCIA): 279.0,
    (4, NOME_REGRA_SAZONAL): 213.2,
    (8, "referencia"): 272.6,
    (8, "HistGB_folha20_M1"): 223.2,
    (8, NOME_REGRA_PERSISTENCIA): 531.0,
    (8, NOME_REGRA_SAZONAL): 216.2,
    (12, "referencia"): 278.8,
    (12, "HistGB_folha20_M1"): 243.8,
    (12, NOME_REGRA_PERSISTENCIA): 697.5,
    (12, NOME_REGRA_SAZONAL): 217.8,
}

ANCORAS_PERDA_QUANTILICA_AVALIACAO = {
    (1, "referencia"): 62.1,
    (1, "HistGB_folha20_M1"): 71.2,
    (1, NOME_REGRA_PERSISTENCIA): 45.3,
    (1, NOME_REGRA_SAZONAL): 157.3,
    (4, "referencia"): 151.5,
    (4, "HistGB_folha20_M1"): 135.9,
    (4, NOME_REGRA_PERSISTENCIA): 152.6,
    (4, NOME_REGRA_SAZONAL): 166.9,
    (8, "referencia"): 218.6,
    (8, "HistGB_folha20_M1"): 182.1,
    (8, NOME_REGRA_PERSISTENCIA): 282.7,
    (8, NOME_REGRA_SAZONAL): 169.5,
    (12, "referencia"): 227.1,
    (12, "HistGB_folha20_M1"): 191.2,
    (12, NOME_REGRA_PERSISTENCIA): 366.8,
    (12, NOME_REGRA_SAZONAL): 170.6,
}

# MAE em h=12 por ano do alvo: (ano, braco) -> mae esperado.
ANCORAS_MAE_H12_POR_ANO = {
    (2022, "referencia"): 110.6,
    (2022, "HistGB_folha20_M1"): 119.2,
    (2022, NOME_REGRA_SAZONAL): 116.4,
    (2023, "referencia"): 70.1,
    (2023, "HistGB_folha20_M1"): 65.8,
    (2023, NOME_REGRA_SAZONAL): 78.4,
    (2024, "referencia"): 353.6,
    (2024, "HistGB_folha20_M1"): 322.3,
    (2024, NOME_REGRA_SAZONAL): 281.0,
    (2025, "referencia"): 238.8,
    (2025, "HistGB_folha20_M1"): 196.3,
    (2025, NOME_REGRA_SAZONAL): 180.0,
    (2026, "referencia"): 21.7,
    (2026, "HistGB_folha20_M1"): 30.7,
    (2026, NOME_REGRA_SAZONAL): 42.2,
}

ANCORAS_N_H12_POR_ANO = {
    2022: 47,
    2023: 53,
    2024: 45,
    2025: 52,
    2026: 5,
}

ANCORAS_TETO_HISTORICO = {
    2024: 879.0,
    2025: 1855.0,
}

ANCORAS_TETO_PREVISAO_H12 = {
    (2024, "referencia"): 364.0,
    (2024, "HistGB_folha20_M1"): 525.0,
    (2025, "referencia"): 1399.0,
    (2025, "HistGB_folha20_M1"): 1614.0,
}

TOLERANCIA_DE_MAE = 0.2
TOLERANCIA_DE_PERDA_QUANTILICA = 0.2
TOLERANCIA_DE_TETO = 1.0

BRACOS_DA_FIGURA = ("referencia", "HistGB_folha20_M1", "LightGBM_M1")


# ============================================================================
# ESTRUTURAS DE CONFIGURACAO E RESULTADO
# ============================================================================


@dataclasses.dataclass(frozen=True)
class MetricasPrevisao:
    """Metricas de qualidade de um conjunto de previsoes pareadas com o real.

    Attributes:
        mae: Erro absoluto medio.
        perda_quantilica: Perda quantilica pinball no quantil 0,85, media de
            max(0,85*d, -0,15*d) com d = real - previsto. Penaliza mais a
            subestimacao do que a superestimacao, coerente com a perda usada
            para treinar o cenario adotado.
        r2: Coeficiente de determinacao.
        n: Quantidade de semanas usadas no calculo.
    """

    mae: float
    perda_quantilica: float
    r2: float
    n: int


@dataclasses.dataclass(frozen=True)
class ResultadoComparacaoPareada:
    """Resultado de comparar um braco contra uma regra simples, pareado.

    Attributes:
        entidade: Nome do braco de modelo comparado.
        regra: Nome da regra simples usada como controle.
        horizonte: Horizonte h da comparacao.
        mae_entidade: MAE do braco de modelo nas semanas pareadas.
        mae_regra: MAE da regra simples nas mesmas semanas.
        reducao_percentual_mae: Quanto o modelo reduziu o MAE frente a regra.
            Negativo significa que o modelo piorou frente a regra.
        n_pareado: Quantidade de semanas em comum entre os dois.
        p_bruto: p-valor do teste de Wilcoxon bilateral, antes de Holm.
    """

    entidade: str
    regra: str
    horizonte: int
    mae_entidade: float
    mae_regra: float
    reducao_percentual_mae: float
    n_pareado: int
    p_bruto: float


# ============================================================================
# CARREGAMENTO
# ============================================================================


def carregar_previsoes_dos_bracos() -> pd.DataFrame:
    """Le e empilha as previsoes dos blocos 5 e 7 da bateria noturna.

    Cada linha de entrada e uma previsao de um braco de modelo (algoritmo e
    hiperparametros ja fixados na rodada de 23/09/2026) para um horizonte h e
    uma data_alvo. Este script nao re-treina nada: so consome esses CSVs.

    Returns:
        DataFrame com colunas h (int), data_alvo (Timestamp), real (float),
        previsto (float) e braco (str), com os 9 bracos dos dois blocos
        empilhados. A coluna `entidade_tipo` marca todas as linhas como
        "modelo", para diferenciar das linhas das regras simples que serao
        adicionadas depois.

    Raises:
        FileNotFoundError: Se algum dos dois CSVs de origem nao existir.
    """
    if not CAMINHO_BLOCO_7.exists():
        raise FileNotFoundError(f"CSV do bloco 7 nao encontrado: {CAMINHO_BLOCO_7}")

    if not CAMINHO_BLOCO_5.exists():
        raise FileNotFoundError(f"CSV do bloco 5 nao encontrado: {CAMINHO_BLOCO_5}")

    previsoes_bloco_7 = pd.read_csv(CAMINHO_BLOCO_7, parse_dates=[COLUNA_DATA_ALVO_ORIGEM])
    previsoes_bloco_5 = pd.read_csv(CAMINHO_BLOCO_5, parse_dates=[COLUNA_DATA_ALVO_ORIGEM])

    previsoes_empilhadas = pd.concat(
        [previsoes_bloco_7, previsoes_bloco_5],
        ignore_index=True,
    )
    previsoes_empilhadas["entidade_tipo"] = ENTIDADE_TIPO_MODELO
    previsoes_empilhadas = previsoes_empilhadas.rename(
        columns={COLUNA_BRACO_ORIGEM: "entidade_nome"}
    )

    print(
        f"Previsoes carregadas: {len(previsoes_empilhadas)} linhas, "
        f"{previsoes_empilhadas['entidade_nome'].nunique()} bracos distintos."
    )
    return previsoes_empilhadas


def carregar_serie_semanal_de_casos() -> tuple[dict[pd.Timestamp, float], pd.Timestamp, pd.Timestamp]:
    """Le a tabela semanal e valida que ela e uma serie continua de 7 em 7 dias.

    A regua de regras simples depende de olhar semanas passadas por indice de
    data (origem = data_alvo - h semanas). Isso so e seguro se a serie nao
    tiver buracos nem datas duplicadas — por isso a validacao roda antes de
    qualquer calculo.

    Returns:
        Uma tupla com:
        - dicionario data (Timestamp) -> casos_confirmados (float, pode ser
          NaN nas 297 semanas vazias descritas no brief: antes de 2018 e nas
          semanas mais recentes, ainda sem contagem fechada);
        - a menor data da serie;
        - a maior data da serie.

    Raises:
        FileNotFoundError: Se `tabela_final.csv` nao existir.
        ValueError: Se houver data duplicada ou um intervalo diferente de 7
            dias entre semanas consecutivas.
    """
    if not CAMINHO_TABELA_FINAL.exists():
        raise FileNotFoundError(f"Tabela final nao encontrada: {CAMINHO_TABELA_FINAL}")

    tabela_final = pd.read_csv(CAMINHO_TABELA_FINAL, parse_dates=[COLUNA_DATA_SEMANA])
    tabela_final = tabela_final.sort_values(COLUNA_DATA_SEMANA).reset_index(drop=True)

    datas_duplicadas = tabela_final[COLUNA_DATA_SEMANA].duplicated().sum()
    if datas_duplicadas > 0:
        raise ValueError(
            f"{datas_duplicadas} datas duplicadas em {COLUNA_DATA_SEMANA} — "
            "a serie precisa ser unica por semana para a regua funcionar."
        )

    intervalos_entre_semanas = tabela_final[COLUNA_DATA_SEMANA].diff().dropna()
    intervalos_fora_do_padrao = intervalos_entre_semanas[
        intervalos_entre_semanas != pd.Timedelta(days=7)
    ]
    if len(intervalos_fora_do_padrao) > 0:
        raise ValueError(
            f"{len(intervalos_fora_do_padrao)} intervalos entre semanas "
            "diferentes de 7 dias — a serie tem buraco(s) e a regua de "
            "regras simples (que anda por data) ficaria incorreta."
        )

    casos_por_data = dict(
        zip(tabela_final[COLUNA_DATA_SEMANA], tabela_final[COLUNA_CASOS])
    )
    data_minima = tabela_final[COLUNA_DATA_SEMANA].min()
    data_maxima = tabela_final[COLUNA_DATA_SEMANA].max()

    quantidade_de_semanas_vazias = tabela_final[COLUNA_CASOS].isna().sum()
    print(
        f"Serie semanal validada: {len(tabela_final)} semanas continuas de "
        f"{data_minima.date()} a {data_maxima.date()}, "
        f"{quantidade_de_semanas_vazias} com casos_confirmados vazio."
    )
    return casos_por_data, data_minima, data_maxima


# ============================================================================
# VERIFICACOES OBRIGATORIAS (antes de qualquer calculo de metrica)
# ============================================================================


@dataclasses.dataclass(frozen=True)
class ResultadoVerificacaoDuplicata:
    """Resultado de conferir se HistGB_M1 (bloco 5) duplica a referencia (bloco 7).

    Attributes:
        n_linhas_em_comum: Quantas linhas (h, data_alvo) os dois bracos tem
            em comum.
        n_linhas_referencia: Total de linhas do braco referencia.
        n_linhas_duplicata: Total de linhas do braco HistGB_M1 do bloco 5.
        maior_diferenca_absoluta_previsto: Maior |previsto_ref - previsto_m1|
            entre as linhas em comum.
        maior_diferenca_absoluta_real: Maior |real_ref - real_m1| entre as
            linhas em comum.
        e_duplicata_exata: True se as previsoes e os reais batem exatamente
            (diferenca zero) em todas as linhas em comum, e a cobertura de
            linhas e identica nos dois lados.
    """

    n_linhas_em_comum: int
    n_linhas_referencia: int
    n_linhas_duplicata: int
    maior_diferenca_absoluta_previsto: float
    maior_diferenca_absoluta_real: float
    e_duplicata_exata: bool


def conferir_duplicata_historgb_m1(previsoes: pd.DataFrame) -> ResultadoVerificacaoDuplicata:
    """Confere, sem assumir, que HistGB_M1 do bloco 5 e a referencia do bloco 7.

    O brief afirma que as duas rodadas usam a mesma configuracao (HistGB,
    folha minima 5, quantil 0,85, com vetor). Esta funcao mede a diferenca
    real entre as previsoes das duas, em vez de aceitar a afirmacao.

    Args:
        previsoes: Previsoes empilhadas dos 9 bracos (saida de
            `carregar_previsoes_dos_bracos`).

    Returns:
        O resultado da conferencia, incluindo se a duplicata e exata.
    """
    referencia = previsoes[previsoes["entidade_nome"] == NOME_REFERENCIA_BLOCO_7]
    duplicata = previsoes[previsoes["entidade_nome"] == NOME_DUPLICATA_ESPERADA_BLOCO_5]

    colunas_de_juncao = [COLUNA_H_ORIGEM, COLUNA_DATA_ALVO_ORIGEM]
    pareado = referencia.merge(
        duplicata,
        on=colunas_de_juncao,
        suffixes=("_ref", "_dup"),
    )

    diferenca_previsto = np.abs(
        pareado[f"{COLUNA_PREVISTO_ORIGEM}_ref"] - pareado[f"{COLUNA_PREVISTO_ORIGEM}_dup"]
    )
    diferenca_real = np.abs(
        pareado[f"{COLUNA_REAL_ORIGEM}_ref"] - pareado[f"{COLUNA_REAL_ORIGEM}_dup"]
    )

    cobertura_identica = (
        len(pareado) == len(referencia) and len(pareado) == len(duplicata)
    )
    duplicata_exata = (
        cobertura_identica
        and diferenca_previsto.max() == 0.0
        and diferenca_real.max() == 0.0
    )

    resultado = ResultadoVerificacaoDuplicata(
        n_linhas_em_comum=len(pareado),
        n_linhas_referencia=len(referencia),
        n_linhas_duplicata=len(duplicata),
        maior_diferenca_absoluta_previsto=float(diferenca_previsto.max()),
        maior_diferenca_absoluta_real=float(diferenca_real.max()),
        e_duplicata_exata=duplicata_exata,
    )

    print(
        "Conferencia HistGB_M1(bloco5) == referencia(bloco7): "
        f"{resultado.n_linhas_em_comum} linhas em comum de "
        f"{resultado.n_linhas_referencia} (ref) / {resultado.n_linhas_duplicata} (dup), "
        f"maior diff previsto={resultado.maior_diferenca_absoluta_previsto:.6f}, "
        f"maior diff real={resultado.maior_diferenca_absoluta_real:.6f} — "
        f"{'DUPLICATA EXATA' if resultado.e_duplicata_exata else 'DIVERGE, INVESTIGAR'}"
    )
    return resultado


def conferir_consistencia_do_real(
    previsoes: pd.DataFrame,
    casos_por_data: dict[pd.Timestamp, float],
) -> pd.DataFrame:
    """Confere se a coluna `real` das previsoes bate com `casos_confirmados`.

    A ancora do brief exige zero divergencias: `real` em cada linha de
    previsao tem que ser igual a `casos_confirmados` na `data_alvo` daquela
    linha, para qualquer braco.

    Args:
        previsoes: Previsoes empilhadas dos 9 bracos.
        casos_por_data: Serie semanal de casos indexada por data.

    Returns:
        As linhas de `previsoes` cujo `real` diverge de `casos_confirmados`
        (vazio quando tudo bate). Cada linha do retorno traz o valor
        encontrado na tabela final, para facilitar a investigacao.
    """
    casos_esperados = previsoes[COLUNA_DATA_ALVO_ORIGEM].map(casos_por_data)
    diferenca_absoluta = np.abs(previsoes[COLUNA_REAL_ORIGEM] - casos_esperados)

    mascara_diverge = diferenca_absoluta > TOLERANCIA_DE_DIVERGENCIA_REAL
    linhas_divergentes = previsoes[mascara_diverge].copy()
    linhas_divergentes["casos_confirmados_na_tabela_final"] = casos_esperados[mascara_diverge]

    print(
        f"Consistencia real vs casos_confirmados: {mascara_diverge.sum()} "
        f"divergencia(s) em {len(previsoes)} linhas (esperado: 0)."
    )
    return linhas_divergentes


# ============================================================================
# AS TRES REGRAS SIMPLES
# ============================================================================


def calcular_regra_persistencia(
    horizonte: int,
    data_alvo: pd.Timestamp,
    casos_por_data: dict[pd.Timestamp, float],
) -> float:
    """Regra 1 — persistencia: repete o ultimo caso conhecido na origem.

    A semana de origem e `data_alvo - h` semanas: e exatamente o mesmo numero
    que o modelo recebe como atributo (lag h de casos_confirmados), entao a
    comparacao usa a mesma informacao que o modelo tem disponivel.

    Args:
        horizonte: h, quantas semanas a frente da origem esta o alvo.
        data_alvo: Semana que esta sendo prevista.
        casos_por_data: Serie semanal de casos indexada por data.

    Returns:
        `casos_confirmados` na semana de origem, ou NaN se a semana de
        origem nao tiver contagem fechada (ou nao existir na serie).
    """
    semana_de_origem = data_alvo - pd.Timedelta(weeks=horizonte)
    return casos_por_data.get(semana_de_origem, np.nan)


def calcular_regra_sazonal(
    data_alvo: pd.Timestamp,
    casos_por_data: dict[pd.Timestamp, float],
) -> float:
    """Regra 2 — sazonal: repete o caso de exatamente um ano antes.

    Usa `data_alvo - 52` semanas. Como h vai de 1 a 12, esse numero tem pelo
    menos 40 semanas de idade na semana de origem: ja era conhecido e maduro
    quando a previsao seria feita, entao a regra nao usa informacao do
    futuro.

    Args:
        data_alvo: Semana que esta sendo prevista.
        casos_por_data: Serie semanal de casos indexada por data.

    Returns:
        `casos_confirmados` na semana `data_alvo - 52` semanas, ou NaN se
        essa semana nao tiver contagem fechada.
    """
    semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    return casos_por_data.get(semana_um_ano_antes, np.nan)


def calcular_regra_climatologia(
    data_alvo: pd.Timestamp,
    casos_por_data: dict[pd.Timestamp, float],
    data_minima_da_serie: pd.Timestamp,
) -> float:
    """Regra 3 — climatologia: media dos mesmos-periodo de todos os anos passados.

    Anda de 52 em 52 semanas para tras (k = 1, 2, 3, ...) a partir de
    `data_alvo`, empilhando `casos_confirmados` de cada ano anterior,
    enquanto a data candidata nao passar do inicio da serie. So entram no
    calculo as semanas com contagem fechada (nao vazias).

    Usar passos fixos de 52 semanas ignora os anos de 53 semanas: e uma
    simplificacao deliberada, a mesma que a regra sazonal usa.

    Args:
        data_alvo: Semana que esta sendo prevista.
        casos_por_data: Serie semanal de casos indexada por data.
        data_minima_da_serie: Menor data existente na serie semanal —
            marca onde a busca para tras deve parar.

    Returns:
        A media dos valores nao vazios encontrados, ou NaN se nenhum dos
        anos anteriores tiver contagem fechada nessa semana-do-ano.
    """
    valores_de_anos_anteriores: list[float] = []

    passo = 1
    while True:
        data_candidata = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL * passo)
        if data_candidata < data_minima_da_serie:
            break

        caso_do_ano_anterior = casos_por_data.get(data_candidata, np.nan)
        if pd.notna(caso_do_ano_anterior):
            valores_de_anos_anteriores.append(caso_do_ano_anterior)

        passo += 1

    if len(valores_de_anos_anteriores) == 0:
        return np.nan

    return float(np.mean(valores_de_anos_anteriores))


def montar_previsoes_das_regras_simples(
    pares_h_data_alvo: pd.DataFrame,
    casos_por_data: dict[pd.Timestamp, float],
    data_minima_da_serie: pd.Timestamp,
) -> pd.DataFrame:
    """Aplica as tres regras simples a cada combinacao (h, data_alvo) da referencia.

    As regras nao dependem do braco de modelo: o VALOR de cada regra depende
    so de h e data_alvo. Mas a grade de (h, data_alvo) sobre a qual a metrica
    "padrao" das regras e calculada precisa vir de algum lugar — e aqui ela
    vem das proprias linhas do braco `referencia`, nao da uniao de todos os 9
    bracos.

    ⚠️ Decisao de desenho, tomada apos investigar uma divergencia contra as
    ancoras (ver `desvios_e_decisoes` no retorno estruturado e o README): os
    4 bracos M0 (sem vetor) cobrem 7 semanas a mais que os bracos M1/
    referencia em alguns horizontes (ex.: maio-junho/2024 em h=1), porque
    modelos que NAO usam o vetor nao sao afetados por um buraco nas colunas
    do vetor que derruba essas semanas do `dropna` dos modelos M1. Usar a
    uniao dos 9 bracos como grade das regras infla o n da regra com semanas
    que a referencia nunca viu, e diverge das ancoras (medido: MAE da
    persistencia em h=1 sobe de 83,3 para 100,2). Usar a grade da propria
    referencia reproduz as ancoras exatamente. As comparacoes pareadas
    (Wilcoxon) continuam corretas de qualquer forma, porque pareiam por
    data_alvo por construcao — a diferenca so aparece na metrica "solta" da
    regra, sem braco de comparacao.

    Args:
        pares_h_data_alvo: DataFrame com as colunas h e data_alvo, uma linha
            por combinacao unica presente no braco `referencia`.
        casos_por_data: Serie semanal de casos indexada por data.
        data_minima_da_serie: Menor data existente na serie semanal.

    Returns:
        DataFrame em formato longo, com colunas h, data_alvo, entidade_tipo
        ("regra"), entidade_nome (persistencia | sazonal | climatologia),
        real (casos_confirmados na propria data_alvo) e previsto (o valor da
        regra, podendo ser NaN quando a regra nao pode ser calculada naquela
        linha).
    """
    linhas_das_regras: list[dict[str, object]] = []

    for _, par in pares_h_data_alvo.iterrows():
        horizonte = int(par[COLUNA_H_ORIGEM])
        data_alvo = par[COLUNA_DATA_ALVO_ORIGEM]
        real_na_data_alvo = casos_por_data.get(data_alvo, np.nan)

        previsao_persistencia = calcular_regra_persistencia(
            horizonte, data_alvo, casos_por_data
        )
        previsao_sazonal = calcular_regra_sazonal(data_alvo, casos_por_data)
        previsao_climatologia = calcular_regra_climatologia(
            data_alvo, casos_por_data, data_minima_da_serie
        )

        linhas_das_regras.append(
            {
                COLUNA_H_ORIGEM: horizonte,
                COLUNA_DATA_ALVO_ORIGEM: data_alvo,
                "entidade_tipo": ENTIDADE_TIPO_REGRA,
                "entidade_nome": NOME_REGRA_PERSISTENCIA,
                COLUNA_REAL_ORIGEM: real_na_data_alvo,
                COLUNA_PREVISTO_ORIGEM: previsao_persistencia,
            }
        )
        linhas_das_regras.append(
            {
                COLUNA_H_ORIGEM: horizonte,
                COLUNA_DATA_ALVO_ORIGEM: data_alvo,
                "entidade_tipo": ENTIDADE_TIPO_REGRA,
                "entidade_nome": NOME_REGRA_SAZONAL,
                COLUNA_REAL_ORIGEM: real_na_data_alvo,
                COLUNA_PREVISTO_ORIGEM: previsao_sazonal,
            }
        )
        linhas_das_regras.append(
            {
                COLUNA_H_ORIGEM: horizonte,
                COLUNA_DATA_ALVO_ORIGEM: data_alvo,
                "entidade_tipo": ENTIDADE_TIPO_REGRA,
                "entidade_nome": NOME_REGRA_CLIMATOLOGIA,
                COLUNA_REAL_ORIGEM: real_na_data_alvo,
                COLUNA_PREVISTO_ORIGEM: previsao_climatologia,
            }
        )

    previsoes_das_regras = pd.DataFrame(linhas_das_regras)
    print(
        f"Regras simples calculadas para {len(pares_h_data_alvo)} pares "
        f"(h, data_alvo) unicos, {len(previsoes_das_regras)} linhas no total."
    )
    return previsoes_das_regras


def relatar_linhas_vazias_por_regra(previsoes_das_regras: pd.DataFrame) -> pd.DataFrame:
    """Conta, por regra e por horizonte, quantas linhas ficaram sem previsao.

    O brief exige que uma regra vazia numa linha saia SO daquela comparacao,
    e que isso seja contado e relatado — nunca escondido.

    Args:
        previsoes_das_regras: Saida de `montar_previsoes_das_regras_simples`.

    Returns:
        DataFrame com entidade_nome, h, n_total, n_vazias e n_validas.
    """
    linhas_do_relatorio: list[dict[str, object]] = []

    for nome_da_regra in NOMES_DAS_REGRAS_SIMPLES:
        regra_selecionada = previsoes_das_regras[
            previsoes_das_regras["entidade_nome"] == nome_da_regra
        ]
        for horizonte in HORIZONTES_DO_PROJETO:
            do_horizonte = regra_selecionada[regra_selecionada[COLUNA_H_ORIGEM] == horizonte]
            n_vazias = do_horizonte[COLUNA_PREVISTO_ORIGEM].isna().sum()
            linhas_do_relatorio.append(
                {
                    "entidade_nome": nome_da_regra,
                    COLUNA_H_ORIGEM: horizonte,
                    "n_total": len(do_horizonte),
                    "n_vazias": int(n_vazias),
                    "n_validas": len(do_horizonte) - int(n_vazias),
                }
            )

    return pd.DataFrame(linhas_do_relatorio)


# ============================================================================
# CLASSIFICACAO DE PERIODO E CALCULO DE METRICAS
# ============================================================================


def selecionar_periodo(
    medicoes: pd.DataFrame,
    nome_do_periodo: str,
) -> pd.DataFrame:
    """Filtra as medicoes pelo recorte temporal pedido.

    Args:
        medicoes: DataFrame com a coluna data_alvo.
        nome_do_periodo: Um de "calibracao", "calibracao_epidemica" ou
            "avaliacao". Note que calibracao_epidemica e um SUBCONJUNTO de
            calibracao — os tres recortes nao formam uma particao.

    Returns:
        As linhas de `medicoes` que caem dentro do periodo pedido.

    Raises:
        ValueError: Se o nome do periodo nao for reconhecido.
    """
    if nome_do_periodo == NOME_PERIODO_CALIBRACAO:
        return medicoes[medicoes[COLUNA_DATA_ALVO_ORIGEM] < INICIO_DA_AVALIACAO]

    if nome_do_periodo == NOME_PERIODO_CALIBRACAO_EPIDEMICA:
        dentro_do_inicio = medicoes[COLUNA_DATA_ALVO_ORIGEM] >= INICIO_CALIBRACAO_EPIDEMICA
        antes_da_avaliacao = medicoes[COLUNA_DATA_ALVO_ORIGEM] < INICIO_DA_AVALIACAO
        return medicoes[dentro_do_inicio & antes_da_avaliacao]

    if nome_do_periodo == NOME_PERIODO_AVALIACAO:
        return medicoes[medicoes[COLUNA_DATA_ALVO_ORIGEM] >= INICIO_DA_AVALIACAO]

    raise ValueError(f"Periodo desconhecido: {nome_do_periodo}")


def calcular_metricas_previsao(valores_reais: pd.Series, valores_previstos: pd.Series) -> MetricasPrevisao:
    """Calcula MAE, perda quantilica 0,85, R2 e n para um conjunto pareado.

    Linhas com previsto vazio ja devem ter sido removidas por quem chama esta
    funcao (ver `relatar_linhas_vazias_por_regra`): aqui a entrada e assumida
    completa.

    Args:
        valores_reais: Casos confirmados observados.
        valores_previstos: Previsoes a avaliar (de um modelo ou de uma regra).

    Returns:
        As quatro metricas. Quando ha menos de 2 pontos, R2 nao e bem
        definido pelo sklearn (retorna um valor degenerado); o n baixo fica
        visivel na propria tabela para quem for interpretar o resultado.
    """
    n_pontos = len(valores_reais)

    if n_pontos == 0:
        return MetricasPrevisao(mae=np.nan, perda_quantilica=np.nan, r2=np.nan, n=0)

    mae = mean_absolute_error(valores_reais, valores_previstos)

    diferenca = valores_reais.to_numpy() - valores_previstos.to_numpy()
    perda_quantilica = float(
        np.mean(
            np.maximum(
                QUANTIL_DA_PERDA_QUANTILICA * diferenca,
                (QUANTIL_DA_PERDA_QUANTILICA - 1.0) * diferenca,
            )
        )
    )

    if n_pontos >= 2:
        r2 = r2_score(valores_reais, valores_previstos)
    else:
        r2 = np.nan

    return MetricasPrevisao(mae=float(mae), perda_quantilica=perda_quantilica, r2=float(r2), n=n_pontos)


def montar_tabela_de_metricas_por_periodo(medicoes: pd.DataFrame) -> pd.DataFrame:
    """Metricas por entidade (modelo ou regra), horizonte e periodo.

    Args:
        medicoes: DataFrame longo com entidade_tipo, entidade_nome, h,
            data_alvo, real e previsto, ja sem as linhas vazias das regras.

    Returns:
        Uma linha por (entidade_tipo, entidade_nome, h, periodo), com mae,
        perda_quantilica, r2 e n.
    """
    linhas_da_tabela: list[dict[str, object]] = []

    entidades_distintas = medicoes[["entidade_tipo", "entidade_nome"]].drop_duplicates()

    for _, entidade in entidades_distintas.iterrows():
        medicoes_da_entidade = medicoes[
            (medicoes["entidade_tipo"] == entidade["entidade_tipo"])
            & (medicoes["entidade_nome"] == entidade["entidade_nome"])
        ]

        for horizonte in HORIZONTES_DO_PROJETO:
            medicoes_do_horizonte = medicoes_da_entidade[
                medicoes_da_entidade[COLUNA_H_ORIGEM] == horizonte
            ]

            for nome_do_periodo in NOMES_DOS_PERIODOS:
                medicoes_do_periodo = selecionar_periodo(medicoes_do_horizonte, nome_do_periodo)
                metricas = calcular_metricas_previsao(
                    medicoes_do_periodo[COLUNA_REAL_ORIGEM],
                    medicoes_do_periodo[COLUNA_PREVISTO_ORIGEM],
                )

                linhas_da_tabela.append(
                    {
                        "entidade_tipo": entidade["entidade_tipo"],
                        "entidade_nome": entidade["entidade_nome"],
                        COLUNA_H_ORIGEM: horizonte,
                        "periodo": nome_do_periodo,
                        "mae": metricas.mae,
                        "perda_quantilica_085": metricas.perda_quantilica,
                        "r2": metricas.r2,
                        "n": metricas.n,
                    }
                )

    return pd.DataFrame(linhas_da_tabela)


def montar_tabela_de_metricas_por_ano(medicoes: pd.DataFrame) -> pd.DataFrame:
    """Metricas por entidade, horizonte e ano do alvo (data_alvo.year).

    Args:
        medicoes: DataFrame longo, ja sem as linhas vazias das regras.

    Returns:
        Uma linha por (entidade_tipo, entidade_nome, h, ano_do_alvo), com
        mae, perda_quantilica, r2 e n.
    """
    medicoes_com_ano = medicoes.copy()
    medicoes_com_ano["ano_do_alvo"] = medicoes_com_ano[COLUNA_DATA_ALVO_ORIGEM].dt.year

    linhas_da_tabela: list[dict[str, object]] = []
    entidades_distintas = medicoes_com_ano[["entidade_tipo", "entidade_nome"]].drop_duplicates()
    anos_distintos = sorted(medicoes_com_ano["ano_do_alvo"].unique())

    for _, entidade in entidades_distintas.iterrows():
        medicoes_da_entidade = medicoes_com_ano[
            (medicoes_com_ano["entidade_tipo"] == entidade["entidade_tipo"])
            & (medicoes_com_ano["entidade_nome"] == entidade["entidade_nome"])
        ]

        for horizonte in HORIZONTES_DO_PROJETO:
            medicoes_do_horizonte = medicoes_da_entidade[
                medicoes_da_entidade[COLUNA_H_ORIGEM] == horizonte
            ]

            for ano in anos_distintos:
                medicoes_do_ano = medicoes_do_horizonte[
                    medicoes_do_horizonte["ano_do_alvo"] == ano
                ]
                metricas = calcular_metricas_previsao(
                    medicoes_do_ano[COLUNA_REAL_ORIGEM],
                    medicoes_do_ano[COLUNA_PREVISTO_ORIGEM],
                )

                linhas_da_tabela.append(
                    {
                        "entidade_tipo": entidade["entidade_tipo"],
                        "entidade_nome": entidade["entidade_nome"],
                        COLUNA_H_ORIGEM: horizonte,
                        "ano_do_alvo": int(ano),
                        "mae": metricas.mae,
                        "perda_quantilica_085": metricas.perda_quantilica,
                        "r2": metricas.r2,
                        "n": metricas.n,
                    }
                )

    return pd.DataFrame(linhas_da_tabela)


# ============================================================================
# SKILL SCORE
# ============================================================================


def calcular_skill_scores(tabela_de_metricas_por_periodo: pd.DataFrame) -> pd.DataFrame:
    """Skill score dos 9 bracos de modelo contra as regras simples.

    Skill score = 1 - MAE_modelo / MAE_regra. Positivo significa que o modelo
    bate a regra; negativo significa que a regra bate o modelo.

    Calcula duas coisas por linha de modelo (entidade_tipo == "modelo"):
    - skill contra a melhor regra daquele h e periodo (menor MAE entre as
      tres regras simples);
    - skill contra cada regra especifica, em colunas separadas.

    Args:
        tabela_de_metricas_por_periodo: Saida de
            `montar_tabela_de_metricas_por_periodo`.

    Returns:
        As linhas de modelo da tabela de entrada, acrescidas de
        mae_melhor_regra, nome_melhor_regra, skill_vs_melhor_regra e uma
        coluna skill_vs_<regra> para cada uma das tres regras simples.
    """
    linhas_de_regra = tabela_de_metricas_por_periodo[
        tabela_de_metricas_por_periodo["entidade_tipo"] == ENTIDADE_TIPO_REGRA
    ]
    linhas_de_modelo = tabela_de_metricas_por_periodo[
        tabela_de_metricas_por_periodo["entidade_tipo"] == ENTIDADE_TIPO_MODELO
    ].copy()

    colunas_skill_por_regra: dict[str, list[float]] = {}
    for nome_da_regra in NOMES_DAS_REGRAS_SIMPLES:
        colunas_skill_por_regra[f"skill_vs_{nome_da_regra}"] = []

    maes_da_melhor_regra: list[float] = []
    nomes_da_melhor_regra: list[str] = []
    skills_vs_melhor_regra: list[float] = []

    for _, linha_do_modelo in linhas_de_modelo.iterrows():
        regras_do_mesmo_corte = linhas_de_regra[
            (linhas_de_regra[COLUNA_H_ORIGEM] == linha_do_modelo[COLUNA_H_ORIGEM])
            & (linhas_de_regra["periodo"] == linha_do_modelo["periodo"])
        ]

        indice_da_melhor_regra = regras_do_mesmo_corte["mae"].idxmin()
        melhor_regra = regras_do_mesmo_corte.loc[indice_da_melhor_regra]

        maes_da_melhor_regra.append(melhor_regra["mae"])
        nomes_da_melhor_regra.append(melhor_regra["entidade_nome"])
        skills_vs_melhor_regra.append(1.0 - linha_do_modelo["mae"] / melhor_regra["mae"])

        for nome_da_regra in NOMES_DAS_REGRAS_SIMPLES:
            regra_especifica = regras_do_mesmo_corte[
                regras_do_mesmo_corte["entidade_nome"] == nome_da_regra
            ]
            mae_da_regra_especifica = regra_especifica["mae"].to_numpy()[0]
            skill_contra_essa_regra = 1.0 - linha_do_modelo["mae"] / mae_da_regra_especifica
            colunas_skill_por_regra[f"skill_vs_{nome_da_regra}"].append(skill_contra_essa_regra)

    linhas_de_modelo["mae_melhor_regra"] = maes_da_melhor_regra
    linhas_de_modelo["nome_melhor_regra"] = nomes_da_melhor_regra
    linhas_de_modelo["skill_vs_melhor_regra"] = skills_vs_melhor_regra

    for nome_da_coluna, valores in colunas_skill_por_regra.items():
        linhas_de_modelo[nome_da_coluna] = valores

    return linhas_de_modelo


# ============================================================================
# COMPARACAO PAREADA (WILCOXON + HOLM)
# ============================================================================


def comparar_braco_contra_regra_pareado(
    medicoes_da_avaliacao: pd.DataFrame,
    nome_do_braco: str,
    nome_da_regra: str,
    horizonte: int,
) -> ResultadoComparacaoPareada:
    """Compara um braco de modelo contra uma regra simples, pareado por data_alvo.

    O pareamento por data_alvo garante que os dois lados estao sendo julgados
    exatamente nas mesmas semanas — condicao do projeto para qualquer
    comparacao entre modelos valer.

    Args:
        medicoes_da_avaliacao: Medicoes (modelos e regras) ja restritas ao
            periodo de avaliacao.
        nome_do_braco: Braco de modelo a testar.
        nome_da_regra: Regra simples usada como controle.
        horizonte: Horizonte h da comparacao.

    Returns:
        O resultado da comparacao, com p bruto do teste de Wilcoxon
        bilateral.

    Raises:
        ValueError: Se nao sobrar nenhuma semana em comum apos o pareamento.
    """
    do_horizonte = medicoes_da_avaliacao[medicoes_da_avaliacao[COLUNA_H_ORIGEM] == horizonte]

    do_braco = do_horizonte[do_horizonte["entidade_nome"] == nome_do_braco]
    da_regra = do_horizonte[do_horizonte["entidade_nome"] == nome_da_regra]

    pareado = do_braco.merge(
        da_regra,
        on=COLUNA_DATA_ALVO_ORIGEM,
        suffixes=("_braco", "_regra"),
    )
    if len(pareado) == 0:
        raise ValueError(
            f"Nenhuma semana em comum entre {nome_do_braco} e {nome_da_regra} "
            f"em h={horizonte}."
        )

    erro_do_braco = np.abs(
        pareado[f"{COLUNA_REAL_ORIGEM}_braco"] - pareado[f"{COLUNA_PREVISTO_ORIGEM}_braco"]
    )
    erro_da_regra = np.abs(
        pareado[f"{COLUNA_REAL_ORIGEM}_regra"] - pareado[f"{COLUNA_PREVISTO_ORIGEM}_regra"]
    )

    if np.allclose(erro_do_braco, erro_da_regra):
        p_bruto = 1.0
    else:
        _, p_bruto = stats.wilcoxon(erro_do_braco, erro_da_regra)

    mae_do_braco = float(np.mean(erro_do_braco))
    mae_da_regra = float(np.mean(erro_da_regra))

    return ResultadoComparacaoPareada(
        entidade=nome_do_braco,
        regra=nome_da_regra,
        horizonte=horizonte,
        mae_entidade=mae_do_braco,
        mae_regra=mae_da_regra,
        reducao_percentual_mae=100.0 * (mae_da_regra - mae_do_braco) / mae_da_regra,
        n_pareado=len(pareado),
        p_bruto=float(p_bruto),
    )


def corrigir_por_holm(p_brutos: list[float]) -> list[float]:
    """Aplica a correcao de Holm sobre a familia inteira de p-valores.

    Holm ordena os p do menor para o maior e exige que o i-esimo sobreviva a
    um limiar que vai afrouxando, com o p corrigido de cada posicao nunca
    podendo ser menor que o da posicao anterior (monotonia).

    Args:
        p_brutos: Todos os p-valores da familia, na ordem original de
            entrada. Passar a familia inteira de uma vez e obrigatorio — Holm
            sobre um subconjunto infla a significancia do resto.

    Returns:
        Os p-valores corrigidos, na MESMA ordem de `p_brutos`.
    """
    quantidade_de_testes = len(p_brutos)
    indices_ordenados_por_p = sorted(
        range(quantidade_de_testes), key=lambda indice: p_brutos[indice]
    )

    p_corrigidos_na_ordem_original = [0.0] * quantidade_de_testes
    maior_p_ate_agora = 0.0

    for posicao, indice_original in enumerate(indices_ordenados_por_p):
        p_ajustado = min(1.0, p_brutos[indice_original] * (quantidade_de_testes - posicao))
        maior_p_ate_agora = max(maior_p_ate_agora, p_ajustado)
        p_corrigidos_na_ordem_original[indice_original] = maior_p_ate_agora

    return p_corrigidos_na_ordem_original


def montar_tabela_de_comparacoes_pareadas(medicoes: pd.DataFrame) -> pd.DataFrame:
    """Monta a familia de 72 comparacoes (9 bracos x 2 regras x 4 horizontes).

    Args:
        medicoes: DataFrame longo com modelos e regras, na avaliacao e fora
            dela (a funcao filtra a avaliacao internamente).

    Returns:
        Uma linha por comparacao, com p_bruto, p_holm e reducao percentual
        de MAE.
    """
    medicoes_da_avaliacao = selecionar_periodo(medicoes, NOME_PERIODO_AVALIACAO)

    nomes_dos_bracos_de_modelo = sorted(
        medicoes_da_avaliacao[medicoes_da_avaliacao["entidade_tipo"] == ENTIDADE_TIPO_MODELO][
            "entidade_nome"
        ].unique()
    )

    regras_de_controle = (NOME_REGRA_PERSISTENCIA, NOME_REGRA_SAZONAL)

    resultados: list[ResultadoComparacaoPareada] = []
    for nome_do_braco in nomes_dos_bracos_de_modelo:
        for nome_da_regra in regras_de_controle:
            for horizonte in HORIZONTES_DA_COMPARACAO_PAREADA:
                resultado = comparar_braco_contra_regra_pareado(
                    medicoes_da_avaliacao, nome_do_braco, nome_da_regra, horizonte
                )
                resultados.append(resultado)

    p_brutos = []
    for resultado in resultados:
        p_brutos.append(resultado.p_bruto)
    p_corrigidos = corrigir_por_holm(p_brutos)

    linhas_da_tabela: list[dict[str, object]] = []
    for resultado, p_holm in zip(resultados, p_corrigidos):
        linhas_da_tabela.append(
            {
                "braco": resultado.entidade,
                "regra_de_controle": resultado.regra,
                COLUNA_H_ORIGEM: resultado.horizonte,
                "mae_braco": resultado.mae_entidade,
                "mae_regra": resultado.mae_regra,
                "reducao_percentual_mae": resultado.reducao_percentual_mae,
                "n_pareado": resultado.n_pareado,
                "p_bruto": resultado.p_bruto,
                "p_holm": p_holm,
                "significativo_5pct": p_holm < NIVEL_DE_SIGNIFICANCIA,
            }
        )

    tabela = pd.DataFrame(linhas_da_tabela)
    print(
        f"Familia de Holm: {len(tabela)} comparacoes "
        f"({len(nomes_dos_bracos_de_modelo)} bracos x {len(regras_de_controle)} regras x "
        f"{len(HORIZONTES_DA_COMPARACAO_PAREADA)} horizontes)."
    )
    return tabela


# ============================================================================
# TETO (maior previsao vs maior caso ja visto)
# ============================================================================


def montar_tabela_de_teto(
    medicoes: pd.DataFrame,
    casos_por_data: dict[pd.Timestamp, float],
) -> pd.DataFrame:
    """Compara a maior previsao do ano com o maior caso ja visto antes dele.

    Um modelo (ou regra) que nunca preveja acima do maior pico historico
    conhecido ate aquele momento esta, na pratica, incapaz de sinalizar um
    surto inedito — mesmo que o MAE medio pareca bom.

    Args:
        medicoes: DataFrame longo com modelos e regras, com a coluna
            data_alvo.
        casos_por_data: Serie semanal completa de casos (usada para calcular
            o teto historico, que olha para tras de qualquer ano presente
            nas previsoes).

    Returns:
        Uma linha por (ano_do_alvo, entidade_nome, h), com a maior previsao
        do ano, o teto historico anterior aquele ano e a diferenca.
    """
    datas_da_serie = np.array(list(casos_por_data.keys()))
    casos_da_serie = np.array(list(casos_por_data.values()), dtype=float)

    medicoes_com_ano = medicoes.copy()
    medicoes_com_ano["ano_do_alvo"] = medicoes_com_ano[COLUNA_DATA_ALVO_ORIGEM].dt.year

    anos_distintos = sorted(medicoes_com_ano["ano_do_alvo"].unique())
    entidades_distintas = medicoes_com_ano[["entidade_tipo", "entidade_nome"]].drop_duplicates()

    linhas_da_tabela: list[dict[str, object]] = []

    for ano in anos_distintos:
        inicio_do_ano = pd.Timestamp(year=int(ano), month=1, day=1)
        mascara_antes_do_ano = datas_da_serie < inicio_do_ano
        casos_antes_do_ano = casos_da_serie[mascara_antes_do_ano]
        casos_antes_do_ano_nao_vazios = casos_antes_do_ano[~np.isnan(casos_antes_do_ano)]

        if len(casos_antes_do_ano_nao_vazios) == 0:
            teto_historico = np.nan
        else:
            teto_historico = float(np.max(casos_antes_do_ano_nao_vazios))

        for _, entidade in entidades_distintas.iterrows():
            medicoes_da_entidade_no_ano = medicoes_com_ano[
                (medicoes_com_ano["entidade_tipo"] == entidade["entidade_tipo"])
                & (medicoes_com_ano["entidade_nome"] == entidade["entidade_nome"])
                & (medicoes_com_ano["ano_do_alvo"] == ano)
            ]

            for horizonte in HORIZONTES_DO_TETO:
                do_horizonte = medicoes_da_entidade_no_ano[
                    medicoes_da_entidade_no_ano[COLUNA_H_ORIGEM] == horizonte
                ]
                previsoes_validas = do_horizonte[COLUNA_PREVISTO_ORIGEM].dropna()

                if len(previsoes_validas) == 0:
                    maior_previsao_do_ano = np.nan
                else:
                    maior_previsao_do_ano = float(previsoes_validas.max())

                linhas_da_tabela.append(
                    {
                        "ano_do_alvo": int(ano),
                        "entidade_tipo": entidade["entidade_tipo"],
                        "entidade_nome": entidade["entidade_nome"],
                        COLUNA_H_ORIGEM: horizonte,
                        "maior_previsao_do_ano": maior_previsao_do_ano,
                        "teto_historico_antes_do_ano": teto_historico,
                        "previsao_ultrapassa_teto": (
                            maior_previsao_do_ano > teto_historico
                            if pd.notna(maior_previsao_do_ano) and pd.notna(teto_historico)
                            else False
                        ),
                    }
                )

    return pd.DataFrame(linhas_da_tabela)


# ============================================================================
# CONFERENCIA DAS ANCORAS NUMERICAS
# ============================================================================


def conferir_ancoras_numericas(
    tabela_de_metricas_por_periodo: pd.DataFrame,
    tabela_de_metricas_por_ano: pd.DataFrame,
    tabela_de_teto: pd.DataFrame,
) -> pd.DataFrame:
    """Compara os numeros calculados com as ancoras medidas em 25/09/2026.

    Nunca ajusta o calculo para bater: so relata a diferenca. Uma divergencia
    aqui e sinal de investigar a causa, nao de mudar a formula ate o numero
    coincidir.

    Args:
        tabela_de_metricas_por_periodo: Saida de
            `montar_tabela_de_metricas_por_periodo`.
        tabela_de_metricas_por_ano: Saida de
            `montar_tabela_de_metricas_por_ano`.
        tabela_de_teto: Saida de `montar_tabela_de_teto`.

    Returns:
        Uma linha por ancora conferida, com o valor esperado, o valor
        calculado, a diferenca e se ela ficou dentro da tolerancia.
    """
    linhas_da_conferencia: list[dict[str, object]] = []

    metricas_avaliacao = tabela_de_metricas_por_periodo[
        tabela_de_metricas_por_periodo["periodo"] == NOME_PERIODO_AVALIACAO
    ]

    for (horizonte, nome_da_entidade), mae_esperado in ANCORAS_MAE_AVALIACAO.items():
        linha_calculada = metricas_avaliacao[
            (metricas_avaliacao[COLUNA_H_ORIGEM] == horizonte)
            & (metricas_avaliacao["entidade_nome"] == nome_da_entidade)
        ]
        mae_calculado = float(linha_calculada["mae"].to_numpy()[0])
        diferenca = abs(mae_calculado - mae_esperado)
        linhas_da_conferencia.append(
            {
                "ancora": "mae_avaliacao",
                "h": horizonte,
                "entidade": nome_da_entidade,
                "valor_esperado": mae_esperado,
                "valor_calculado": mae_calculado,
                "diferenca_absoluta": diferenca,
                "dentro_da_tolerancia": diferenca < TOLERANCIA_DE_MAE,
            }
        )

    for (horizonte, nome_da_entidade), perda_esperada in ANCORAS_PERDA_QUANTILICA_AVALIACAO.items():
        linha_calculada = metricas_avaliacao[
            (metricas_avaliacao[COLUNA_H_ORIGEM] == horizonte)
            & (metricas_avaliacao["entidade_nome"] == nome_da_entidade)
        ]
        perda_calculada = float(linha_calculada["perda_quantilica_085"].to_numpy()[0])
        diferenca = abs(perda_calculada - perda_esperada)
        linhas_da_conferencia.append(
            {
                "ancora": "perda_quantilica_085_avaliacao",
                "h": horizonte,
                "entidade": nome_da_entidade,
                "valor_esperado": perda_esperada,
                "valor_calculado": perda_calculada,
                "diferenca_absoluta": diferenca,
                "dentro_da_tolerancia": diferenca < TOLERANCIA_DE_PERDA_QUANTILICA,
            }
        )

    metricas_h12_por_ano = tabela_de_metricas_por_ano[
        tabela_de_metricas_por_ano[COLUNA_H_ORIGEM] == 12
    ]
    for (ano, nome_da_entidade), mae_esperado in ANCORAS_MAE_H12_POR_ANO.items():
        linha_calculada = metricas_h12_por_ano[
            (metricas_h12_por_ano["ano_do_alvo"] == ano)
            & (metricas_h12_por_ano["entidade_nome"] == nome_da_entidade)
        ]
        mae_calculado = float(linha_calculada["mae"].to_numpy()[0])
        n_calculado = int(linha_calculada["n"].to_numpy()[0])
        diferenca = abs(mae_calculado - mae_esperado)
        linhas_da_conferencia.append(
            {
                "ancora": "mae_h12_por_ano",
                "h": 12,
                "entidade": f"{nome_da_entidade} ({ano})",
                "valor_esperado": mae_esperado,
                "valor_calculado": mae_calculado,
                "diferenca_absoluta": diferenca,
                "dentro_da_tolerancia": (
                    diferenca < TOLERANCIA_DE_MAE
                    and n_calculado == ANCORAS_N_H12_POR_ANO[ano]
                ),
            }
        )

    for ano, teto_esperado in ANCORAS_TETO_HISTORICO.items():
        linha_calculada = tabela_de_teto[
            (tabela_de_teto["ano_do_alvo"] == ano) & (tabela_de_teto[COLUNA_H_ORIGEM] == 12)
        ]
        teto_calculado = float(linha_calculada["teto_historico_antes_do_ano"].to_numpy()[0])
        diferenca = abs(teto_calculado - teto_esperado)
        linhas_da_conferencia.append(
            {
                "ancora": "teto_historico",
                "h": None,
                "entidade": str(ano),
                "valor_esperado": teto_esperado,
                "valor_calculado": teto_calculado,
                "diferenca_absoluta": diferenca,
                "dentro_da_tolerancia": diferenca < TOLERANCIA_DE_TETO,
            }
        )

    for (ano, nome_da_entidade), previsao_esperada in ANCORAS_TETO_PREVISAO_H12.items():
        linha_calculada = tabela_de_teto[
            (tabela_de_teto["ano_do_alvo"] == ano)
            & (tabela_de_teto["entidade_nome"] == nome_da_entidade)
            & (tabela_de_teto[COLUNA_H_ORIGEM] == 12)
        ]
        previsao_calculada = float(linha_calculada["maior_previsao_do_ano"].to_numpy()[0])
        diferenca = abs(previsao_calculada - previsao_esperada)
        linhas_da_conferencia.append(
            {
                "ancora": "maior_previsao_h12",
                "h": 12,
                "entidade": f"{nome_da_entidade} ({ano})",
                "valor_esperado": previsao_esperada,
                "valor_calculado": previsao_calculada,
                "diferenca_absoluta": diferenca,
                "dentro_da_tolerancia": diferenca < TOLERANCIA_DE_TETO,
            }
        )

    tabela_de_conferencia = pd.DataFrame(linhas_da_conferencia)
    n_divergentes = (~tabela_de_conferencia["dentro_da_tolerancia"]).sum()
    print(
        f"Conferencia de ancoras: {len(tabela_de_conferencia)} ancoras, "
        f"{n_divergentes} divergente(s)."
    )
    if n_divergentes > 0:
        print(tabela_de_conferencia[~tabela_de_conferencia["dentro_da_tolerancia"]])

    return tabela_de_conferencia


# ============================================================================
# FIGURA
# ============================================================================


def gerar_figura_skill_score(tabela_de_skill: pd.DataFrame, caminho_da_figura: pathlib.Path) -> None:
    """Gera a figura de skill score contra a melhor regra, por horizonte.

    Uma linha por braco selecionado (referencia, HistGB_folha20_M1 e
    LightGBM_M1), no periodo de avaliacao, com uma linha horizontal em zero
    separando "bate a melhor regra" de "perde para a melhor regra".

    Args:
        tabela_de_skill: Saida de `calcular_skill_scores`.
        caminho_da_figura: Onde gravar o PNG.
    """
    skill_da_avaliacao = tabela_de_skill[tabela_de_skill["periodo"] == NOME_PERIODO_AVALIACAO]

    figura, eixo = plt.subplots(figsize=(9, 5.5))

    for nome_do_braco in BRACOS_DA_FIGURA:
        skill_do_braco = skill_da_avaliacao[
            skill_da_avaliacao["entidade_nome"] == nome_do_braco
        ].sort_values(COLUNA_H_ORIGEM)
        eixo.plot(
            skill_do_braco[COLUNA_H_ORIGEM],
            skill_do_braco["skill_vs_melhor_regra"],
            marker="o",
            label=nome_do_braco,
        )

    eixo.axhline(0.0, color="black", linewidth=1.0, linestyle="--")
    eixo.set_xlabel("Horizonte h (semanas)")
    eixo.set_ylabel("Skill score vs. melhor regra simples")
    eixo.set_title(
        "Skill score na avaliacao (data_alvo >= 2024-01-01)\n"
        "Positivo = modelo bate a melhor regra simples naquele h"
    )
    eixo.set_xticks(list(HORIZONTES_DO_PROJETO))
    eixo.legend()
    eixo.grid(True, alpha=0.3)

    figura.tight_layout()
    figura.savefig(caminho_da_figura, dpi=150)
    plt.close(figura)

    print(f"Figura gravada em {caminho_da_figura}")


# ============================================================================
# ORQUESTRACAO
# ============================================================================


def main() -> None:
    """Roda a regua inteira: carrega, calcula, confere ancoras e grava saidas."""
    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)

    previsoes_dos_modelos = carregar_previsoes_dos_bracos()
    casos_por_data, data_minima_da_serie, data_maxima_da_serie = carregar_serie_semanal_de_casos()

    resultado_duplicata = conferir_duplicata_historgb_m1(previsoes_dos_modelos)
    linhas_divergentes_do_real = conferir_consistencia_do_real(previsoes_dos_modelos, casos_por_data)

    # A grade de (h, data_alvo) das regras usa as linhas do braco referencia,
    # nao a uniao dos 9 bracos — ver a docstring de
    # `montar_previsoes_das_regras_simples` para a investigacao que levou a
    # essa escolha.
    pares_h_data_alvo_da_referencia = previsoes_dos_modelos[
        previsoes_dos_modelos["entidade_nome"] == NOME_REFERENCIA_BLOCO_7
    ][[COLUNA_H_ORIGEM, COLUNA_DATA_ALVO_ORIGEM]].drop_duplicates()
    previsoes_das_regras = montar_previsoes_das_regras_simples(
        pares_h_data_alvo_da_referencia, casos_por_data, data_minima_da_serie
    )
    relatorio_de_linhas_vazias = relatar_linhas_vazias_por_regra(previsoes_das_regras)

    medicoes_completas = pd.concat(
        [previsoes_dos_modelos, previsoes_das_regras],
        ignore_index=True,
    )
    medicoes_sem_vazias = medicoes_completas.dropna(subset=[COLUNA_PREVISTO_ORIGEM]).copy()

    tabela_de_metricas_por_periodo = montar_tabela_de_metricas_por_periodo(medicoes_sem_vazias)
    tabela_de_metricas_por_ano = montar_tabela_de_metricas_por_ano(medicoes_sem_vazias)
    tabela_de_skill = calcular_skill_scores(tabela_de_metricas_por_periodo)
    tabela_de_comparacoes_pareadas = montar_tabela_de_comparacoes_pareadas(medicoes_sem_vazias)
    tabela_de_teto = montar_tabela_de_teto(medicoes_sem_vazias, casos_por_data)

    tabela_de_conferencia_de_ancoras = conferir_ancoras_numericas(
        tabela_de_metricas_por_periodo, tabela_de_metricas_por_ano, tabela_de_teto
    )

    tabela_de_metricas_por_periodo.to_csv(
        PASTA_DE_SAIDAS / "metricas_por_horizonte_e_periodo.csv", index=False
    )
    tabela_de_metricas_por_ano.to_csv(
        PASTA_DE_SAIDAS / "metricas_por_horizonte_e_ano.csv", index=False
    )
    tabela_de_skill.to_csv(PASTA_DE_SAIDAS / "skill_score_vs_regras.csv", index=False)
    tabela_de_comparacoes_pareadas.to_csv(
        PASTA_DE_SAIDAS / "comparacoes_pareadas_holm.csv", index=False
    )
    tabela_de_teto.to_csv(PASTA_DE_SAIDAS / "teto_previsao_vs_historico.csv", index=False)
    relatorio_de_linhas_vazias.to_csv(
        PASTA_DE_SAIDAS / "linhas_vazias_por_regra.csv", index=False
    )
    linhas_divergentes_do_real.to_csv(
        PASTA_DE_SAIDAS / "divergencias_real_vs_casos_confirmados.csv", index=False
    )
    tabela_de_conferencia_de_ancoras.to_csv(
        PASTA_DE_SAIDAS / "conferencia_ancoras_numericas.csv", index=False
    )

    gerar_figura_skill_score(
        tabela_de_skill, PASTA_DE_SAIDAS / "figura_skill_score_por_horizonte.png"
    )

    print("\nResumo final:")
    print(f"  Duplicata HistGB_M1/referencia exata: {resultado_duplicata.e_duplicata_exata}")
    print(f"  Divergencias real vs casos_confirmados: {len(linhas_divergentes_do_real)}")
    print(
        f"  Ancoras fora da tolerancia: "
        f"{(~tabela_de_conferencia_de_ancoras['dentro_da_tolerancia']).sum()} "
        f"de {len(tabela_de_conferencia_de_ancoras)}"
    )
    print(f"  CSVs e figura gravados em {PASTA_DE_SAIDAS}")


if __name__ == "__main__":
    main()
