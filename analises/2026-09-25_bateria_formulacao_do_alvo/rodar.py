"""Bateria de formulação do alvo — 25/09/2026.

Protocolo completo em PRE_DECLARACAO.md (leitura obrigatória, é o contrato
desta rodada). Este script testa se a forma como o modelo RECEBE o alvo e os
atributos (bruto x log x resíduo sobre a âncora sazonal x modelo linear x
mistura com a régua) destrava a informação sazonal que o HistGB de folha
mínima 20 (B0) não usa — sem repetir nenhum teste já feito e reprovado na
bateria noturna de 23/09/2026.

⚠️ NÃO altera nada do pipeline (`modelagem_aedes/`) nem do motor compartilhado
(`harness.py`, só leitura). NÃO lê `arquivos_secretaria_saude_poa/`. NÃO roda
`preparar_dados.py`. NÃO usa git.

Nove braços, quatro horizontes (h = 1, 4, 8, 12), quantil 0,85 em todos:

    referencia             cenário adotado, folha mínima 5           (trava 1)
    B0                     HistGB folha mínima 20, com vetor          (trava 2, base de tudo)
    V1_alvo_log            treina em log1p(casos), devolve expm1
    V2_ancora_atributo     + coluna 'ancora' (casos há 52 semanas)
    V3_ancora_residuo      alvo = log1p(casos) − log1p(ancora)
    V3_ancora_residuo_M0   V3 sem as colunas do vetor
    V4_crescimento_vetor   + velocidade do vetor (1 e 4 semanas)
    V5_linear_log          regressão quantílica linear, em log
    V6_mistura             0,5×B0 + 0,5×régua sazonal, sem treino

Uso:

    python rodar.py --smoke                    # todos os braços, últimas 5 origens de h=12
    python rodar.py --provar-ancora            # prova o sinal da âncora com datas explícitas
    python rodar.py --provar-equivalencia       # B0 próprio == harness.rodar_walk_forward
    python rodar.py --cronometro-b0             # 1 célula completa de B0 em h=12
    python rodar.py --cronometro-v5             # 1 célula completa de V5 em h=12
    python rodar.py --bracos B0,V1_alvo_log      # roda um subconjunto (4 horizontes), grava parcial
    python rodar.py --consolidar                # junta os parciais, confere travas, F1/F2/F3

NÃO RODAR a bateria completa (`--bracos` com todos os 9) sem autorização —
autorização de 25/09/2026 cobre rodar, mas o brief desta entrega pede só
smoke test e cronômetro.
"""

import argparse
import dataclasses
import os
import pathlib
import sys
import time
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import QuantileRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

# ============================================================================
# CAMINHOS E IMPORTS DO MOTOR COMPARTILHADO
# ============================================================================

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_BATERIA_NOTURNA = PASTA_DESTE_ARQUIVO.parent / "2026-09-23_bateria_noturna"
if str(PASTA_BATERIA_NOTURNA) not in sys.path:
    sys.path.insert(0, str(PASTA_BATERIA_NOTURNA))

import harness  # noqa: E402  (harness.py já ajusta o sys.path para modelagem_aedes)
from config.modelo import EspecificacaoModelo  # noqa: E402

PASTA_DE_SAIDAS = PASTA_DESTE_ARQUIVO / "saidas"

CAMINHO_BLOCO_7 = (
    PASTA_DESTE_ARQUIVO.parent
    / "2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv"
)

# ============================================================================
# CONSTANTES DE NEGÓCIO
# ============================================================================

HORIZONTES_DA_BATERIA = (1, 4, 8, 12)
SEMANAS_DO_PASSO_SAZONAL = 52
QUANTIL_DE_REFERENCIA = 0.85
NIVEL_DE_SIGNIFICANCIA = 0.05
LIMITE_REAL_ALTO = 100.0
INICIO_CALIBRACAO_EPIDEMICA = pd.Timestamp("2022-01-01")

COLUNA_VETOR_BASE = "aedes_aegypti_por_armadilha"

# Colunas que NUNCA disputam vaga de clima em nenhum braço: só entram no
# modelo do braço que as pedir explicitamente (V4 pede as duas de
# crescimento; a âncora entra à parte, calculada por horizonte).
COLUNAS_RESERVADAS = ("crescimento_vetor_1sem", "crescimento_vetor_4sem", "ancora")

NOME_DO_BRACO_V6 = "V6_mistura"
DESCRICAO_DO_BRACO_V6 = "media 0,5/0,5 entre B0 e a regra sazonal, sem treino"

# As travas (seção 3 da pré-declaração). Se alguma divergir, a rodada é
# inválida e nada é lido — nunca ajustar o cálculo para bater.
PAINEL_REFERENCIA = harness.PAINEL_PUBLICADO
TOLERANCIA_DE_MAE = 0.2
ANCORAS_MAE_B0_AVALIACAO = {1: 133.6, 4: 199.6, 8: 223.2, 12: 243.8}
ANCORAS_N_B0_AVALIACAO = 102

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


# ============================================================================
# COLUNAS EXTRAS RESERVADAS (rodam em TODOS os braços; só entram no modelo
# do braço que as pedir — ver harness.montar_features_do_braco)
# ============================================================================


def construir_colunas_de_crescimento_do_vetor(tabela: pd.DataFrame) -> pd.DataFrame:
    """Adiciona as duas colunas de velocidade do vetor usadas pelo braço V4.

    crescimento_vetor_1sem = log1p(v_t) − log1p(v_t−1)
    crescimento_vetor_4sem = log1p(v_t) − log1p(v_t−4)
    com v = aedes_aegypti_por_armadilha. Roda para todos os braços (ver
    harness.montar_features_do_braco), mas as colunas ficam reservadas —
    só entram no modelo do braço que as pedir em colunas_extras.

    Args:
        tabela: Tabela do braço, já com corte de maturidade e features do
            harness aplicados, em ordem cronológica.

    Returns:
        Uma cópia da tabela com as duas colunas novas.
    """
    tabela_com_crescimento = tabela.copy()
    log1p_do_vetor = np.log1p(tabela_com_crescimento[COLUNA_VETOR_BASE])
    tabela_com_crescimento["crescimento_vetor_1sem"] = log1p_do_vetor - log1p_do_vetor.shift(1)
    tabela_com_crescimento["crescimento_vetor_4sem"] = log1p_do_vetor - log1p_do_vetor.shift(4)
    return tabela_com_crescimento


# ============================================================================
# FORMULAÇÃO DO ALVO (como o alvo é preparado para treino e revertido depois)
# ============================================================================


def preparar_alvo_bruto(dados_de_treino: pd.DataFrame) -> pd.Series:
    """B0, referência, V2 e V4: o alvo de treino é o próprio y_h, sem transformação."""
    return dados_de_treino["y_h"]


def inverter_previsao_identidade(previsao_bruta: float, ancora: float | None) -> float:
    """Nenhuma transformação a desfazer — a previsão do modelo já é 'casos'."""
    return previsao_bruta


def preparar_alvo_log1p(dados_de_treino: pd.DataFrame) -> pd.Series:
    """V1: o modelo treina em log1p(casos), para aprender erro relativo."""
    return np.log1p(dados_de_treino["y_h"])


def inverter_previsao_log1p(previsao_bruta: float, ancora: float | None) -> float:
    """V1: devolve expm1 da previsão em log. Previsão negativa vira 0."""
    previsao_em_casos = float(np.expm1(previsao_bruta))
    return max(0.0, previsao_em_casos)


def preparar_alvo_residuo_sobre_ancora(dados_de_treino: pd.DataFrame) -> pd.Series:
    """V3 e V3_M0: o modelo aprende o desvio, em log, entre o alvo e a âncora."""
    return np.log1p(dados_de_treino["y_h"]) - np.log1p(dados_de_treino["ancora"])


def inverter_previsao_residuo_sobre_ancora(previsao_bruta: float, ancora: float | None) -> float:
    """V3 e V3_M0: soma o resíduo previsto à âncora e desfaz o log1p.

    Raises:
        ValueError: Se a âncora do teste não foi fornecida — o braço não
            pode inverter a previsão sem ela.
    """
    if ancora is None:
        raise ValueError("Formulação com resíduo sobre âncora exige a âncora do teste.")
    previsao_em_casos = float(np.expm1(previsao_bruta + np.log1p(ancora)))
    return max(0.0, previsao_em_casos)


@dataclasses.dataclass(frozen=True)
class FormulacaoDoAlvo:
    """Como um braço prepara o alvo de treino e reverte a previsão para 'casos'.

    Attributes:
        nome: Identificador da formulação, só para logs.
        usa_ancora: Se True, o walk-forward calcula a coluna 'ancora' para
            este horizonte e a inclui nas features e no dropna.
        preparar_alvo: Recebe o recorte de treino (com 'y_h' e, se usa_ancora,
            'ancora') e devolve a série que o modelo vê como alvo.
        inverter_previsao: Recebe a previsão bruta do modelo e a âncora do
            teste (None se usa_ancora é False) e devolve a previsão em casos.
    """

    nome: str
    usa_ancora: bool
    preparar_alvo: Callable[[pd.DataFrame], pd.Series]
    inverter_previsao: Callable[[float, float | None], float]


FORMULACAO_BRUTA = FormulacaoDoAlvo("bruto", False, preparar_alvo_bruto, inverter_previsao_identidade)
FORMULACAO_COM_ANCORA_COMO_ATRIBUTO = FormulacaoDoAlvo(
    "ancora_atributo", True, preparar_alvo_bruto, inverter_previsao_identidade
)
FORMULACAO_LOG = FormulacaoDoAlvo("log", False, preparar_alvo_log1p, inverter_previsao_log1p)
FORMULACAO_RESIDUO_SOBRE_ANCORA = FormulacaoDoAlvo(
    "residuo_sobre_ancora", True, preparar_alvo_residuo_sobre_ancora, inverter_previsao_residuo_sobre_ancora
)


# ============================================================================
# V5 — REGRESSÃO QUANTÍLICA LINEAR EM LOG (classe própria, protocolo fit/predict)
# ============================================================================


class RegressaoQuantilicaLinearLog:
    """Regressão quantílica linear 0,85 sobre colunas em log1p e padronizadas.

    Implementa fit/predict no padrão do scikit-learn para caber no mesmo
    laço de walk-forward usado pelos modelos em árvore.

    Regras da pré-declaração (braço V5):
        - log1p nas colunas que começam com 'casos' e nas colunas do vetor;
        - StandardScaler ajustado só no treino de cada corte;
        - QuantileRegressor(quantile=0.85, alpha=0.0, solver='highs');
        - alvo em log1p(casos); previsão final = max(0, expm1(previsão)).

    Attributes:
        colunas_para_log1p: Nomes das colunas de entrada que recebem log1p
            antes da padronização.
    """

    def __init__(self, colunas_para_log1p: list[str], quantil: float) -> None:
        self.colunas_para_log1p = colunas_para_log1p
        self._escalador = StandardScaler()
        self._regressor = QuantileRegressor(quantile=quantil, alpha=0.0, solver="highs")

    def _aplicar_log1p_nas_colunas_marcadas(self, entradas: pd.DataFrame) -> pd.DataFrame:
        """Aplica log1p só nas colunas marcadas, preservando as demais."""
        entradas_transformadas = entradas.copy()
        for nome_da_coluna in self.colunas_para_log1p:
            entradas_transformadas[nome_da_coluna] = np.log1p(entradas_transformadas[nome_da_coluna])
        return entradas_transformadas

    def fit(self, entradas: pd.DataFrame, alvo: pd.Series) -> "RegressaoQuantilicaLinearLog":
        """Ajusta o escalador e o regressor num único corte de treino."""
        entradas_em_log = self._aplicar_log1p_nas_colunas_marcadas(entradas)
        entradas_padronizadas = self._escalador.fit_transform(entradas_em_log)
        alvo_em_log = np.log1p(alvo)
        self._regressor.fit(entradas_padronizadas, alvo_em_log)
        return self

    def predict(self, entradas: pd.DataFrame) -> np.ndarray:
        """Prevê em casos, nunca negativo."""
        entradas_em_log = self._aplicar_log1p_nas_colunas_marcadas(entradas)
        entradas_padronizadas = self._escalador.transform(entradas_em_log)
        previsao_em_log = self._regressor.predict(entradas_padronizadas)
        previsao_em_casos = np.expm1(previsao_em_log)
        return np.maximum(0.0, previsao_em_casos)


def identificar_colunas_para_log1p(colunas_do_modelo: list[str]) -> list[str]:
    """Colunas do V5 que recebem log1p: as de 'casos' e as do grupo vetor.

    Args:
        colunas_do_modelo: As colunas finais do braço V5 (núcleo + clima +
            vetor, sem a sazonalidade do alvo).

    Returns:
        O subconjunto de colunas_do_modelo que começa com 'casos' ou contém
        algum padrão do grupo vetor do cenário adotado.
    """
    colunas_para_log1p: list[str] = []
    for nome_da_coluna in colunas_do_modelo:
        e_coluna_de_casos = nome_da_coluna.startswith("casos")
        e_coluna_de_vetor = False
        for padrao_de_vetor in harness.CIDADE_REFERENCIA.padroes_vetor:
            if padrao_de_vetor in nome_da_coluna:
                e_coluna_de_vetor = True
        if e_coluna_de_casos or e_coluna_de_vetor:
            colunas_para_log1p.append(nome_da_coluna)
    return colunas_para_log1p


# ============================================================================
# FÁBRICAS DE MODELO (uma instância nova a cada corte do walk-forward)
# ============================================================================


def criar_modelo_referencia(colunas_do_modelo: list[str]) -> object:
    """A ficha do cenário adotado (HistGB, folha mínima 5)."""
    return harness.CIDADE_REFERENCIA.modelo.criar()


def criar_modelo_b0(colunas_do_modelo: list[str]) -> object:
    """A ficha HistGB folha mínima 20 — base de todas as comparações desta bateria."""
    return HISTGB_FOLHA_20.criar()


def criar_modelo_v5(colunas_do_modelo: list[str]) -> object:
    """A regressão quantílica linear em log do braço V5."""
    colunas_para_log1p = identificar_colunas_para_log1p(colunas_do_modelo)
    return RegressaoQuantilicaLinearLog(colunas_para_log1p=colunas_para_log1p, quantil=QUANTIL_DE_REFERENCIA)


# ============================================================================
# OS NOVE BRAÇOS
# ============================================================================


@dataclasses.dataclass(frozen=True)
class BracoDaBateria:
    """Um braço treinado da bateria de formulação do alvo.

    Attributes:
        nome: Identificador nas saídas e nos CSVs.
        descricao: Uma linha dizendo o que o braço investiga.
        sem_vetor: Remove as colunas do vetor (o M0 do V3).
        colunas_extras_harness: Colunas de `construir_colunas_de_crescimento_do_vetor`
            que entram no modelo deste braço (só V4 usa).
        formulacao: Como o alvo é preparado e a previsão revertida.
        criar_modelo: Fábrica do modelo, recebendo as colunas finais do braço.
    """

    nome: str
    descricao: str
    sem_vetor: bool
    colunas_extras_harness: tuple[str, ...]
    formulacao: FormulacaoDoAlvo
    criar_modelo: Callable[[list[str]], object]


BRACOS_TREINADOS: tuple[BracoDaBateria, ...] = (
    BracoDaBateria(
        "referencia", "cenario adotado, folha minima 5 (trava 1)",
        False, (), FORMULACAO_BRUTA, criar_modelo_referencia,
    ),
    BracoDaBateria(
        "B0", "HistGB folha minima 20, com vetor (trava 2, base de tudo)",
        False, (), FORMULACAO_BRUTA, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V1_alvo_log", "treina em log1p(casos), devolve expm1",
        False, (), FORMULACAO_LOG, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V2_ancora_atributo", "ancora (casos ha 52 semanas) como atributo extra",
        False, (), FORMULACAO_COM_ANCORA_COMO_ATRIBUTO, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V3_ancora_residuo", "alvo = residuo log sobre a ancora sazonal",
        False, (), FORMULACAO_RESIDUO_SOBRE_ANCORA, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V3_ancora_residuo_M0", "V3 sem as colunas do vetor",
        True, (), FORMULACAO_RESIDUO_SOBRE_ANCORA, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V4_crescimento_vetor", "+ velocidade do vetor em 1 e 4 semanas",
        False, ("crescimento_vetor_1sem", "crescimento_vetor_4sem"), FORMULACAO_BRUTA, criar_modelo_b0,
    ),
    BracoDaBateria(
        "V5_linear_log", "regressao quantilica linear, em log",
        False, (), FORMULACAO_BRUTA, criar_modelo_v5,
    ),
)

BRACOS_POR_NOME: dict[str, BracoDaBateria] = {}
for _braco in BRACOS_TREINADOS:
    BRACOS_POR_NOME[_braco.nome] = _braco


# ============================================================================
# MONTAGEM DE FEATURES (reusa harness.montar_features_do_braco)
# ============================================================================


def montar_features_para_braco(
    tabela_bruta: pd.DataFrame, braco: BracoDaBateria
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Aplica o motor compartilhado com as regras desta bateria.

    Reusa harness.montar_features_do_braco para o corte de maturidade, os
    lags e a seleção de clima (idêntica em todos os braços, por construção:
    ver README/desvios). Adiciona as colunas de crescimento do vetor como
    reservadas — só entram no modelo do braço que as pede.

    Returns:
        A tabela pronta (sem a coluna 'ancora', calculada depois por
        horizonte), as colunas do modelo e o clima escolhido.
    """
    braco_harness = harness.Braco(
        nome=braco.nome,
        sem_vetor=braco.sem_vetor,
        colunas_extras=braco.colunas_extras_harness,
        descricao=braco.descricao,
    )
    return harness.montar_features_do_braco(
        tabela_bruta,
        braco_harness,
        construir_extras=construir_colunas_de_crescimento_do_vetor,
        colunas_reservadas=COLUNAS_RESERVADAS,
    )


# ============================================================================
# O WALK-FORWARD PRÓPRIO
# ============================================================================


def rodar_walk_forward_customizado(
    tabela: pd.DataFrame,
    colunas_do_modelo: list[str],
    horizonte: int,
    braco: BracoDaBateria,
    limite_de_ultimas_origens: int | None = None,
) -> pd.DataFrame:
    """Walk-forward próprio, espelhando harness.rodar_walk_forward.

    Reproduz o mesmo corte de treino pela data da RESPOSTA
    (`corte_temporal.selecionar_treino_ja_respondido`), o mesmo
    `minimo_semanas_treino`/`passo` do CIDADE_REFERENCIA e as mesmas colunas
    `alvo_sin`/`alvo_cos` — mas aceita formulação do alvo (log, resíduo sobre
    âncora) e uma coluna de âncora calculada especificamente para este
    horizonte. Quando `braco.formulacao.usa_ancora` é False e a formulação é
    bruta (braço B0), este laço é operacionalmente idêntico ao do harness —
    é essa equivalência que `provar_equivalencia_com_harness` testa.

    Args:
        tabela: Tabela do braço (pós corte de maturidade e features do
            harness), única por braço, reutilizada para todos os horizontes.
        colunas_do_modelo: Colunas base do braço (sem 'ancora').
        horizonte: h, quantas semanas à frente.
        braco: A configuração do braço (formulação do alvo, fábrica do modelo).
        limite_de_ultimas_origens: Quando preenchido, roda só as últimas N
            origens da grade válida (usado pelo `--smoke`).

    Returns:
        Uma linha por origem avaliada, com h, data_alvo, real e previsto, já
        na escala de casos.
    """
    tabela_do_horizonte = tabela.copy()
    colunas_do_modelo_do_horizonte = list(colunas_do_modelo)
    coluna_alvo = harness.CIDADE_REFERENCIA.coluna_alvo

    if braco.formulacao.usa_ancora:
        semanas_de_recuo = SEMANAS_DO_PASSO_SAZONAL - horizonte
        tabela_do_horizonte["ancora"] = tabela_do_horizonte[coluna_alvo].shift(semanas_de_recuo)
        colunas_do_modelo_do_horizonte.append("ancora")

    dados_do_horizonte = harness.construir_alvo_horizonte(tabela_do_horizonte, coluna_alvo, horizonte)
    features_com_sazonalidade = colunas_do_modelo_do_horizonte + ["alvo_sin", "alvo_cos"]

    dados_validos = (
        dados_do_horizonte.dropna(subset=features_com_sazonalidade + ["y_h"])
        .sort_values("data")
        .reset_index(drop=True)
    )

    indices_de_corte = list(
        range(
            harness.CIDADE_REFERENCIA.minimo_semanas_treino,
            len(dados_validos),
            harness.CIDADE_REFERENCIA.passo,
        )
    )
    if limite_de_ultimas_origens is not None:
        indices_de_corte = indices_de_corte[-limite_de_ultimas_origens:]

    linhas: list[dict[str, object]] = []
    for indice_do_corte in indices_de_corte:
        teste = dados_validos.iloc[indice_do_corte : indice_do_corte + 1]
        data_do_teste = teste["data"].to_numpy()[0]

        treino = harness.corte_temporal.selecionar_treino_ja_respondido(dados_validos, data_do_teste, horizonte)

        alvo_de_treino = braco.formulacao.preparar_alvo(treino)

        modelo = braco.criar_modelo(colunas_do_modelo_do_horizonte)
        modelo.fit(treino[features_com_sazonalidade], alvo_de_treino)
        previsao_bruta = float(modelo.predict(teste[features_com_sazonalidade])[0])

        ancora_do_teste = None
        if braco.formulacao.usa_ancora:
            ancora_do_teste = float(teste["ancora"].to_numpy()[0])

        previsao_final = braco.formulacao.inverter_previsao(previsao_bruta, ancora_do_teste)

        linhas.append(
            {
                "h": horizonte,
                "data_alvo": pd.Timestamp(data_do_teste) + pd.Timedelta(weeks=horizonte),
                "real": float(teste["y_h"].to_numpy()[0]),
                "previsto": float(previsao_final),
            }
        )

    return pd.DataFrame(linhas)


# ============================================================================
# V6 — MISTURA PÓS-HOC (sem treino)
# ============================================================================


def construir_dicionario_casos_por_data(tabela_bruta: pd.DataFrame) -> dict[pd.Timestamp, float]:
    """Série semanal de casos indexada por data, para a régua sazonal e o V6."""
    return dict(zip(tabela_bruta["data"], tabela_bruta[harness.CIDADE_REFERENCIA.coluna_alvo]))


def calcular_previsao_da_regua_sazonal(data_alvo: pd.Timestamp, casos_por_data: dict) -> float:
    """A régua sazonal: repete o caso confirmado de exatamente 52 semanas antes."""
    semana_um_ano_antes = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    return casos_por_data.get(semana_um_ano_antes, np.nan)


def calcular_previsoes_do_v6_mistura(previsoes_do_b0: pd.DataFrame, casos_por_data: dict) -> pd.DataFrame:
    """V6: média simples e fixa (peso 0,5) entre o B0 e a régua sazonal.

    Sem treino: calculada depois, a partir das previsões já prontas do B0.
    Linhas cuja régua sazonal não existe (âncora fora da série) saem da
    comparação — a mistura não pode ser calculada sem os dois lados.
    """
    linhas: list[dict[str, object]] = []
    for _, linha_do_b0 in previsoes_do_b0.iterrows():
        ancora_sazonal = calcular_previsao_da_regua_sazonal(linha_do_b0["data_alvo"], casos_por_data)
        if pd.isna(ancora_sazonal):
            continue
        previsao_da_mistura = 0.5 * linha_do_b0["previsto"] + 0.5 * ancora_sazonal
        linhas.append(
            {
                "h": linha_do_b0["h"],
                "data_alvo": linha_do_b0["data_alvo"],
                "real": linha_do_b0["real"],
                "previsto": previsao_da_mistura,
            }
        )
    return pd.DataFrame(linhas)


# ============================================================================
# SMOKE TEST
# ============================================================================


def rodar_smoke_test(tabela_bruta: pd.DataFrame) -> None:
    """--smoke: roda todos os nove braços só nas últimas 5 origens de h=12."""
    horizonte_do_smoke = 12
    n_origens_do_smoke = 5

    previsoes_por_braco: dict[str, pd.DataFrame] = {}

    for braco in BRACOS_TREINADOS:
        inicio = time.perf_counter()
        tabela, colunas_do_modelo, clima_escolhido = montar_features_para_braco(tabela_bruta, braco)
        previsoes = rodar_walk_forward_customizado(
            tabela, colunas_do_modelo, horizonte_do_smoke, braco,
            limite_de_ultimas_origens=n_origens_do_smoke,
        )
        previsoes_por_braco[braco.nome] = previsoes
        duracao = time.perf_counter() - inicio
        print(f"\n[smoke] {braco.nome}  ({len(colunas_do_modelo)} colunas · clima={clima_escolhido})", flush=True)
        print(previsoes.to_string(index=False), flush=True)
        print(f"[smoke] {braco.nome}  {duracao:.1f}s", flush=True)

    casos_por_data = construir_dicionario_casos_por_data(tabela_bruta)
    previsoes_v6 = calcular_previsoes_do_v6_mistura(previsoes_por_braco["B0"], casos_por_data)
    print(f"\n[smoke] {NOME_DO_BRACO_V6}", flush=True)
    print(previsoes_v6.to_string(index=False), flush=True)

    print("\n[smoke] TODOS OS BRACOS RODARAM SEM ERRO.", flush=True)


# ============================================================================
# PROVA DO SINAL DA ÂNCORA
# ============================================================================


def provar_sinal_da_ancora(tabela_bruta: pd.DataFrame) -> None:
    """Mostra 3 linhas com datas explícitas provando data_ancora = data_alvo − 52 semanas.

    Raises:
        AssertionError: Se alguma das 3 linhas não bater com a fórmula.
    """
    braco_com_ancora = BRACOS_POR_NOME["V3_ancora_residuo"]
    tabela, _, _ = montar_features_para_braco(tabela_bruta, braco_com_ancora)

    horizonte = 12
    semanas_de_recuo = SEMANAS_DO_PASSO_SAZONAL - horizonte

    print(f"\n[prova da ancora] h={horizonte}, semanas_de_recuo=52-h={semanas_de_recuo}")
    print(f"{'data_origem':>12}  {'data_alvo':>12}  {'data_da_ancora':>15}  {'data_alvo - 52sem':>18}  ok?")

    linhas_com_ancora_valida = tabela.dropna(subset=[harness.CIDADE_REFERENCIA.coluna_alvo]).reset_index(drop=True)
    posicoes_de_amostra = (200, 300, 400)

    for posicao in posicoes_de_amostra:
        data_origem = pd.Timestamp(linhas_com_ancora_valida.loc[posicao, "data"])
        data_alvo = data_origem + pd.Timedelta(weeks=horizonte)
        data_esperada_pela_definicao = data_alvo - pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
        data_da_ancora_pelo_shift = data_origem - pd.Timedelta(weeks=semanas_de_recuo)

        bate = data_da_ancora_pelo_shift == data_esperada_pela_definicao
        print(
            f"{data_origem.date()}  {data_alvo.date()}      {data_da_ancora_pelo_shift.date()}         "
            f"{data_esperada_pela_definicao.date()}          {bate}"
        )
        assert bate, (
            f"Ancora nao bate: origem={data_origem.date()} deu ancora "
            f"{data_da_ancora_pelo_shift.date()}, esperado {data_esperada_pela_definicao.date()}"
        )

    print("[prova da ancora] OK — data_da_ancora == data_alvo - 52 semanas nas 3 linhas.")


# ============================================================================
# PROVA DE EQUIVALÊNCIA COM O HARNESS
# ============================================================================


def provar_equivalencia_com_harness(tabela_bruta: pd.DataFrame) -> None:
    """Prova que o walk-forward próprio reproduz harness.rodar_walk_forward.

    Roda o braço B0 em h=12 pelas duas implementações (rodando a célula
    completa nas duas, porque o corte de treino pela data da resposta olha
    para toda a `dados_validos` — não dá para restringir a "últimas N
    origens" sem repetir o cálculo do walk-forward inteiro) e compara as
    últimas 20 origens com `np.testing.assert_allclose`, rtol=1e-10.

    Raises:
        AssertionError: Se as datas ou as previsões divergirem.
    """
    braco_b0 = BRACOS_POR_NOME["B0"]
    tabela, colunas_do_modelo, _ = montar_features_para_braco(tabela_bruta, braco_b0)

    print("\n[equivalencia] rodando harness.rodar_walk_forward (B0, h=12, todas as origens)...", flush=True)
    inicio_harness = time.perf_counter()
    previsoes_harness = harness.rodar_walk_forward(tabela, colunas_do_modelo, 12, HISTGB_FOLHA_20)
    duracao_harness = time.perf_counter() - inicio_harness
    print(f"[equivalencia] harness: {len(previsoes_harness)} semanas, {duracao_harness:.1f}s", flush=True)

    print("[equivalencia] rodando o walk-forward proprio (B0, h=12, todas as origens)...", flush=True)
    inicio_proprio = time.perf_counter()
    previsoes_proprias = rodar_walk_forward_customizado(tabela, colunas_do_modelo, 12, braco_b0)
    duracao_propria = time.perf_counter() - inicio_proprio
    print(f"[equivalencia] proprio: {len(previsoes_proprias)} semanas, {duracao_propria:.1f}s", flush=True)

    ultimas_20_harness = previsoes_harness.tail(20).reset_index(drop=True)
    ultimas_20_proprias = previsoes_proprias.tail(20).reset_index(drop=True)

    pd.testing.assert_series_equal(
        ultimas_20_harness["data_alvo"], ultimas_20_proprias["data_alvo"], check_names=False,
    )
    np.testing.assert_allclose(
        ultimas_20_proprias["previsto"].to_numpy(),
        ultimas_20_harness["previsto"].to_numpy(),
        rtol=1e-10,
    )
    print(
        "[equivalencia] OK — walk-forward proprio == harness.rodar_walk_forward "
        "(ultimas 20 origens, h=12, rtol=1e-10)."
    )


# ============================================================================
# CRONÔMETRO
# ============================================================================


def cronometrar_celula(
    tabela_bruta: pd.DataFrame, braco: BracoDaBateria, horizonte: int
) -> tuple[pd.DataFrame, float]:
    """Roda uma célula completa (todas as origens) e cronometra o tempo total."""
    tabela, colunas_do_modelo, _ = montar_features_para_braco(tabela_bruta, braco)
    inicio = time.perf_counter()
    previsoes = rodar_walk_forward_customizado(tabela, colunas_do_modelo, horizonte, braco)
    duracao = time.perf_counter() - inicio
    return previsoes, duracao


# ============================================================================
# RODAR UM SUBCONJUNTO DE BRAÇOS (para paralelizar em vários processos)
# ============================================================================


def rodar_bracos_e_gravar_parcial(nomes_dos_bracos: list[str], tabela_bruta: pd.DataFrame) -> None:
    """Roda os braços pedidos, nos 4 horizontes, e grava um CSV próprio.

    Permite paralelizar a bateria em vários processos: cada chamada grava um
    arquivo `previsoes_parcial__<bracos>.csv` independente; `--consolidar`
    depois junta todos.

    Args:
        nomes_dos_bracos: Nomes de BRACOS_TREINADOS, mais opcionalmente
            'V6_mistura' (calculado sem treino a partir do B0).
        tabela_bruta: A tabela semanal sem corte nem features.

    Raises:
        ValueError: Se algum nome não for reconhecido, ou se 'V6_mistura'
            for pedido sem que 'B0' também esteja nesta chamada.
    """
    nomes_treinados = [nome for nome in nomes_dos_bracos if nome != NOME_DO_BRACO_V6]
    pede_v6 = NOME_DO_BRACO_V6 in nomes_dos_bracos

    for nome in nomes_treinados:
        if nome not in BRACOS_POR_NOME:
            raise ValueError(f"Braco desconhecido: {nome}. Validos: {sorted(BRACOS_POR_NOME)} + {NOME_DO_BRACO_V6}")

    if pede_v6 and "B0" not in nomes_treinados:
        raise ValueError("V6_mistura precisa que 'B0' rode na MESMA chamada (nao ha leitura de parcial alheio).")

    previsoes_de_todos: list[pd.DataFrame] = []
    resumo_dos_bracos: list[dict[str, object]] = []
    previsoes_do_b0: pd.DataFrame | None = None

    for nome in nomes_treinados:
        braco = BRACOS_POR_NOME[nome]
        tabela, colunas_do_modelo, clima_escolhido = montar_features_para_braco(tabela_bruta, braco)
        previsoes_do_braco: list[pd.DataFrame] = []

        for horizonte in HORIZONTES_DA_BATERIA:
            marca = time.perf_counter()
            previsoes = rodar_walk_forward_customizado(tabela, colunas_do_modelo, horizonte, braco)
            previsoes["braco"] = braco.nome
            previsoes_do_braco.append(previsoes)
            previsoes_de_todos.append(previsoes)
            print(
                f"[{braco.nome}] h={horizonte:2d}  {len(previsoes):3d} sem  {time.perf_counter() - marca:6.1f}s",
                flush=True,
            )

        if nome == "B0":
            previsoes_do_b0 = pd.concat(previsoes_do_braco, ignore_index=True)

        resumo_dos_bracos.append(
            {
                "braco": braco.nome,
                "descricao": braco.descricao,
                "n_features": len(colunas_do_modelo),
                "clima_escolhido": " | ".join(clima_escolhido),
                "sem_vetor": braco.sem_vetor,
            }
        )

    if pede_v6:
        casos_por_data = construir_dicionario_casos_por_data(tabela_bruta)
        previsoes_v6 = calcular_previsoes_do_v6_mistura(previsoes_do_b0, casos_por_data)
        previsoes_v6["braco"] = NOME_DO_BRACO_V6
        previsoes_de_todos.append(previsoes_v6)
        resumo_dos_bracos.append(
            {
                "braco": NOME_DO_BRACO_V6,
                "descricao": DESCRICAO_DO_BRACO_V6,
                "n_features": None,
                "clima_escolhido": "",
                "sem_vetor": False,
            }
        )

    todas = pd.concat(previsoes_de_todos, ignore_index=True)
    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    sufixo_do_arquivo = "_".join(nomes_dos_bracos)
    todas.to_csv(PASTA_DE_SAIDAS / f"previsoes_parcial__{sufixo_do_arquivo}.csv", index=False)
    pd.DataFrame(resumo_dos_bracos).to_csv(PASTA_DE_SAIDAS / f"resumo_parcial__{sufixo_do_arquivo}.csv", index=False)
    print(f"Gravado: previsoes_parcial__{sufixo_do_arquivo}.csv ({len(todas)} linhas)", flush=True)


# ============================================================================
# CONSOLIDAÇÃO: TRAVAS, FAMÍLIAS F1/F2/F3, LEITURAS DESCRITIVAS, FIGURA
# ============================================================================


def conferir_trave_2_b0(previsoes: pd.DataFrame) -> bool:
    """Trave 2 — B0 reproduz o HistGB_folha20_M1 do bloco 7, exatamente."""
    avaliacao_b0 = previsoes[(previsoes["braco"] == "B0") & (previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO)]

    print("\n  TRAVA 2 — B0 contra o HistGB_folha20_M1 do bloco 7")
    tudo_bate = True
    for horizonte, mae_esperado in ANCORAS_MAE_B0_AVALIACAO.items():
        celula = avaliacao_b0[avaliacao_b0["h"] == horizonte]
        if celula.empty:
            print(f"    h={horizonte:2d}  SEM DADOS")
            tudo_bate = False
            continue
        mae = mean_absolute_error(celula["real"], celula["previsto"])
        bate = len(celula) == ANCORAS_N_B0_AVALIACAO and abs(mae - mae_esperado) < TOLERANCIA_DE_MAE
        tudo_bate = tudo_bate and bate
        marca = "ok" if bate else "<<< DIVERGE"
        print(
            f"    h={horizonte:2d}  MAE {mae:7.1f} (esperado {mae_esperado:6.1f})  "
            f"n={len(celula):3d} (esperado {ANCORAS_N_B0_AVALIACAO})  {marca}"
        )
    print(f"    veredito: {'VALIDO' if tudo_bate else 'INVALIDO'}")
    return tudo_bate


def conferir_trave_3_clima_identico(tabela_bruta: pd.DataFrame) -> bool:
    """Trave 3 — o clima escolhido é idêntico em todos os braços treinados."""
    climas: dict[str, list[str]] = {}
    for braco in BRACOS_TREINADOS:
        _, _, clima_escolhido = montar_features_para_braco(tabela_bruta, braco)
        climas[braco.nome] = clima_escolhido

    climas_distintos = set(tuple(clima) for clima in climas.values())
    tudo_igual = len(climas_distintos) == 1

    print("\n  TRAVE 3 — clima escolhido, por braço")
    for nome, clima in climas.items():
        print(f"    {nome:>22}: {clima}")
    print(f"    veredito: {'VALIDO' if tudo_igual else 'INVALIDO'}")
    return tudo_igual


def conferir_travas(previsoes: pd.DataFrame, tabela_bruta: pd.DataFrame) -> bool:
    """As três travas da seção 3, na ordem. Se alguma falhar, a rodada é inválida."""
    trave_1 = harness.conferir_trava_de_validacao(previsoes, "referencia")
    trave_2 = conferir_trave_2_b0(previsoes)
    trave_3 = conferir_trave_3_clima_identico(tabela_bruta)
    return trave_1 and trave_2 and trave_3


NOMES_VARIANTES_F1 = (
    "V1_alvo_log", "V2_ancora_atributo", "V3_ancora_residuo",
    "V4_crescimento_vetor", "V5_linear_log", NOME_DO_BRACO_V6,
)
NOMES_ENTIDADES_F2 = ("B0",) + NOMES_VARIANTES_F1
HORIZONTES_F2 = (4, 8, 12)


def _comparacoes_para_dataframe(comparacoes: list) -> pd.DataFrame:
    """Aplica Holm sobre a família e devolve uma tabela pronta para gravar."""
    p_corrigidos = harness.corrigir_por_holm(comparacoes)
    linhas: list[dict[str, object]] = []
    for comparacao in comparacoes:
        linhas.append(
            {
                "braco": comparacao.braco,
                "h": comparacao.horizonte,
                "mae_referencia": comparacao.mae_referencia,
                "mae_variante": comparacao.mae_variante,
                "reducao_percentual": comparacao.reducao_percentual(),
                "semanas_pareadas": comparacao.semanas_pareadas,
                "p_bruto": comparacao.p_bruto,
                "p_holm": p_corrigidos[f"{comparacao.braco}:{comparacao.horizonte}"],
            }
        )
    return pd.DataFrame(linhas)


def montar_familia_f1(previsoes_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """F1 — a variante melhora o B0? 6 variantes x 4 horizontes = 24 comparações."""
    comparacoes = []
    for nome_da_variante in NOMES_VARIANTES_F1:
        for horizonte in HORIZONTES_DA_BATERIA:
            comparacoes.append(harness.comparar_pareado(previsoes_avaliacao, "B0", nome_da_variante, horizonte))
    return _comparacoes_para_dataframe(comparacoes)


def montar_familia_f2(previsoes_avaliacao_com_regua: pd.DataFrame) -> pd.DataFrame:
    """F2 — a variante bate a régua sazonal? 7 entidades x 3 horizontes = 21 comparações."""
    comparacoes = []
    for nome_da_entidade in NOMES_ENTIDADES_F2:
        for horizonte in HORIZONTES_F2:
            comparacoes.append(
                harness.comparar_pareado(previsoes_avaliacao_com_regua, "regua_sazonal", nome_da_entidade, horizonte)
            )
    return _comparacoes_para_dataframe(comparacoes)


def montar_familia_f3(previsoes_avaliacao: pd.DataFrame) -> pd.DataFrame:
    """F3 — o vetor vale dentro do V3? 1 par x 4 horizontes = 4 comparações."""
    comparacoes = []
    for horizonte in HORIZONTES_DA_BATERIA:
        comparacoes.append(
            harness.comparar_pareado(previsoes_avaliacao, "V3_ancora_residuo_M0", "V3_ancora_residuo", horizonte)
        )
    return _comparacoes_para_dataframe(comparacoes)


def montar_previsoes_da_regua_sazonal(pares_h_data_alvo: pd.DataFrame, casos_por_data: dict) -> pd.DataFrame:
    """Gera as previsões da régua sazonal para o conjunto (h, data_alvo) pedido."""
    linhas: list[dict[str, object]] = []
    for _, par in pares_h_data_alvo.iterrows():
        data_alvo = par["data_alvo"]
        previsto = calcular_previsao_da_regua_sazonal(data_alvo, casos_por_data)
        linhas.append(
            {
                "h": int(par["h"]),
                "data_alvo": data_alvo,
                "real": casos_por_data.get(data_alvo, np.nan),
                "previsto": previsto,
                "braco": "regua_sazonal",
            }
        )
    previsoes_da_regua = pd.DataFrame(linhas)
    return previsoes_da_regua.dropna(subset=["previsto"])


def _perda_quantilica(reais: pd.Series, previstos: pd.Series) -> float:
    """Perda pinball no quantil de referência (0,85), a mesma que o modelo otimiza."""
    diferenca = reais.to_numpy() - previstos.to_numpy()
    return float(
        np.mean(np.maximum(QUANTIL_DE_REFERENCIA * diferenca, (QUANTIL_DE_REFERENCIA - 1.0) * diferenca))
    )


def gerar_leitura_calibracao_epidemica(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE e perda quantílica em 2022-01-01 ≤ data_alvo < 2024-01-01, por braço e h."""
    no_periodo = previsoes[
        (previsoes["data_alvo"] >= INICIO_CALIBRACAO_EPIDEMICA) & (previsoes["data_alvo"] < harness.INICIO_DA_AVALIACAO)
    ]
    linhas: list[dict[str, object]] = []
    for chave, grupo in no_periodo.groupby(["braco", "h"]):
        nome_do_braco, horizonte = chave
        linhas.append(
            {
                "braco": nome_do_braco,
                "h": horizonte,
                "mae": mean_absolute_error(grupo["real"], grupo["previsto"]),
                "perda_quantilica_085": _perda_quantilica(grupo["real"], grupo["previsto"]),
                "n": len(grupo),
            }
        )
    return pd.DataFrame(linhas)


def gerar_leitura_mae_por_ano(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE por ano do alvo (data_alvo.year), por braço e h."""
    previsoes_com_ano = previsoes.copy()
    previsoes_com_ano["ano_do_alvo"] = previsoes_com_ano["data_alvo"].dt.year
    linhas: list[dict[str, object]] = []
    for chave, grupo in previsoes_com_ano.groupby(["braco", "h", "ano_do_alvo"]):
        nome_do_braco, horizonte, ano = chave
        linhas.append(
            {
                "braco": nome_do_braco,
                "h": horizonte,
                "ano_do_alvo": int(ano),
                "mae": mean_absolute_error(grupo["real"], grupo["previsto"]),
                "n": len(grupo),
            }
        )
    return pd.DataFrame(linhas)


def gerar_leitura_mae_por_faixa_de_real(previsoes: pd.DataFrame) -> pd.DataFrame:
    """MAE separado em semanas com real >= 100 e real < 100, na avaliação."""
    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO].copy()
    avaliacao["faixa_de_real"] = np.where(avaliacao["real"] >= LIMITE_REAL_ALTO, "real >= 100", "real < 100")
    linhas: list[dict[str, object]] = []
    for chave, grupo in avaliacao.groupby(["braco", "h", "faixa_de_real"]):
        nome_do_braco, horizonte, faixa = chave
        linhas.append(
            {
                "braco": nome_do_braco,
                "h": horizonte,
                "faixa_de_real": faixa,
                "mae": mean_absolute_error(grupo["real"], grupo["previsto"]),
                "n": len(grupo),
            }
        )
    return pd.DataFrame(linhas)


def gerar_leituras_descritivas(previsoes: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """As leituras descritivas da seção 4, sem teste de hipótese."""
    return {
        "calibracao_epidemica": gerar_leitura_calibracao_epidemica(previsoes),
        "mae_por_ano": gerar_leitura_mae_por_ano(previsoes),
        "mae_por_faixa_de_real": gerar_leitura_mae_por_faixa_de_real(previsoes),
    }


def gerar_figura_mae_por_horizonte(previsoes: pd.DataFrame, previsoes_da_regua: pd.DataFrame) -> None:
    """MAE por horizonte de cada braço, na avaliação, com a régua sazonal tracejada."""
    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO]
    avaliacao_regua = previsoes_da_regua[previsoes_da_regua["data_alvo"] >= harness.INICIO_DA_AVALIACAO]

    figura, eixo = plt.subplots(figsize=(9, 6))
    for nome_do_braco in sorted(avaliacao["braco"].unique()):
        do_braco = avaliacao[avaliacao["braco"] == nome_do_braco]
        maes_por_horizonte = []
        for horizonte in HORIZONTES_DA_BATERIA:
            do_horizonte = do_braco[do_braco["h"] == horizonte]
            maes_por_horizonte.append(mean_absolute_error(do_horizonte["real"], do_horizonte["previsto"]))
        eixo.plot(HORIZONTES_DA_BATERIA, maes_por_horizonte, marker="o", label=nome_do_braco)

    maes_da_regua = []
    for horizonte in HORIZONTES_DA_BATERIA:
        do_horizonte = avaliacao_regua[avaliacao_regua["h"] == horizonte]
        maes_da_regua.append(mean_absolute_error(do_horizonte["real"], do_horizonte["previsto"]))
    eixo.plot(HORIZONTES_DA_BATERIA, maes_da_regua, marker="s", linestyle="--", color="black", label="regua_sazonal")

    eixo.set_xlabel("horizonte (semanas)")
    eixo.set_ylabel("MAE (casos/semana), avaliacao 2024+")
    eixo.set_title("Bateria de formulacao do alvo — MAE por horizonte")
    eixo.legend(fontsize=8, loc="upper left")
    figura.tight_layout()

    PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
    figura.savefig(PASTA_DE_SAIDAS / "figura_mae_por_horizonte.png", dpi=150)
    plt.close(figura)


def consolidar_e_analisar() -> None:
    """Junta os CSVs parciais, confere as travas e faz as comparações F1/F2/F3.

    ⚠️ NÃO EXECUTADO nesta entrega (só smoke test e cronômetro foram
    rodados) — ver desvios_e_decisoes.
    """
    arquivos_parciais = sorted(PASTA_DE_SAIDAS.glob("previsoes_parcial__*.csv"))
    if not arquivos_parciais:
        raise FileNotFoundError("Nenhum previsoes_parcial__*.csv em saidas/. Rode --bracos antes de consolidar.")

    partes = []
    for arquivo in arquivos_parciais:
        partes.append(pd.read_csv(arquivo, parse_dates=["data_alvo"]))
    previsoes = pd.concat(partes, ignore_index=True).drop_duplicates(subset=["braco", "h", "data_alvo"])
    previsoes.to_csv(PASTA_DE_SAIDAS / "previsoes_por_braco.csv", index=False)

    tabela_bruta = harness.carregar_tabela_bruta()

    valido = conferir_travas(previsoes, tabela_bruta)
    if not valido:
        print("\nBATERIA INVALIDA — travas nao bateram. Nada foi lido.", flush=True)
        return

    casos_por_data = construir_dicionario_casos_por_data(tabela_bruta)
    avaliacao = previsoes[previsoes["data_alvo"] >= harness.INICIO_DA_AVALIACAO]

    pares_h_data_alvo = avaliacao[["h", "data_alvo"]].drop_duplicates()
    previsoes_da_regua = montar_previsoes_da_regua_sazonal(pares_h_data_alvo, casos_por_data)
    avaliacao_com_regua = pd.concat([avaliacao, previsoes_da_regua], ignore_index=True)

    familia_f1 = montar_familia_f1(avaliacao)
    familia_f2 = montar_familia_f2(avaliacao_com_regua)
    familia_f3 = montar_familia_f3(avaliacao)

    familia_f1.to_csv(PASTA_DE_SAIDAS / "familia_f1_variante_vs_b0.csv", index=False)
    familia_f2.to_csv(PASTA_DE_SAIDAS / "familia_f2_variante_vs_regua_sazonal.csv", index=False)
    familia_f3.to_csv(PASTA_DE_SAIDAS / "familia_f3_vetor_dentro_do_v3.csv", index=False)

    leituras = gerar_leituras_descritivas(previsoes)
    for nome_da_leitura, tabela_da_leitura in leituras.items():
        tabela_da_leitura.to_csv(PASTA_DE_SAIDAS / f"leitura_{nome_da_leitura}.csv", index=False)

    gerar_figura_mae_por_horizonte(previsoes, previsoes_da_regua)
    print("\nConsolidacao concluida. CSVs e figura gravados em saidas/.", flush=True)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--smoke", action="store_true", help="Todos os bracos, ultimas 5 origens de h=12.")
    parser.add_argument("--provar-ancora", action="store_true", dest="provar_ancora")
    parser.add_argument("--provar-equivalencia", action="store_true", dest="provar_equivalencia")
    parser.add_argument("--cronometro-b0", action="store_true", dest="cronometro_b0")
    parser.add_argument("--cronometro-v5", action="store_true", dest="cronometro_v5")
    parser.add_argument("--bracos", type=str, default=None, help="Nomes separados por virgula (ex.: B0,V1_alvo_log).")
    parser.add_argument("--consolidar", action="store_true")
    argumentos = parser.parse_args()

    nenhuma_acao_pedida = not any(
        [
            argumentos.smoke, argumentos.provar_ancora, argumentos.provar_equivalencia,
            argumentos.cronometro_b0, argumentos.cronometro_v5, argumentos.bracos, argumentos.consolidar,
        ]
    )
    if nenhuma_acao_pedida:
        parser.print_help()
        return

    if argumentos.consolidar:
        consolidar_e_analisar()
        return

    tabela_bruta = harness.carregar_tabela_bruta()

    if argumentos.smoke:
        rodar_smoke_test(tabela_bruta)

    if argumentos.provar_ancora:
        provar_sinal_da_ancora(tabela_bruta)

    if argumentos.provar_equivalencia:
        provar_equivalencia_com_harness(tabela_bruta)

    if argumentos.cronometro_b0:
        braco_b0 = BRACOS_POR_NOME["B0"]
        previsoes, duracao = cronometrar_celula(tabela_bruta, braco_b0, 12)
        tag_de_threads = os.environ.get("OMP_NUM_THREADS", "padrao")
        PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
        previsoes.to_csv(PASTA_DE_SAIDAS / f"cronometro_b0_h12_threads_{tag_de_threads}.csv", index=False)
        print(f"[cronometro] B0 h=12, {len(previsoes)} semanas, OMP_NUM_THREADS={tag_de_threads}: {duracao:.1f}s")

    if argumentos.cronometro_v5:
        braco_v5 = BRACOS_POR_NOME["V5_linear_log"]
        previsoes, duracao = cronometrar_celula(tabela_bruta, braco_v5, 12)
        PASTA_DE_SAIDAS.mkdir(parents=True, exist_ok=True)
        previsoes.to_csv(PASTA_DE_SAIDAS / "cronometro_v5_h12.csv", index=False)
        print(f"[cronometro] V5 h=12, {len(previsoes)} semanas: {duracao:.1f}s")

    if argumentos.bracos:
        nomes_dos_bracos = argumentos.bracos.split(",")
        rodar_bracos_e_gravar_parcial(nomes_dos_bracos, tabela_bruta)


if __name__ == "__main__":
    main()
