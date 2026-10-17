"""Composto x persistencia (Emenda 6 da pre-declaracao, de 17/10/2026): torna reproduzivel por script uma conta ja feita.

A persistencia repete a ultima semana observada: a previsao para a `data_alvo` e o numero de casos confirmados da
semana de `data_origem`. Esta analise compara o modelo composto (E3, N = 13) com ela nas 102 semanas-alvo da
avaliacao (07/01/2024 a 01/02/2026), nos horizontes de 1, 2, 3, 4, 8 e 12 semanas. E EXPLORATORIA e NAO foi
pre-declarada: foi medida DEPOIS dos resultados e registrada como emenda. Nenhum veredito pre-declarado muda.

Conta, por horizonte (a mesma de `aedes/estatistica.py`, sem retreinar nenhum modelo):
    - `d_t = |real - persistencia| - |real - composto|`; positivo quer dizer que o composto erra menos;
    - p do Diebold-Mariano com a correcao HLN (`diebold_mariano_hln`), bilateral;
    - leitura extra: Newey-West (pesos de Bartlett `1 - k/5`, L = 4), sem a correcao HLN, t de Student com
      `n - 1` graus de liberdade (`calcular_teste_de_newey_west`, a funcao da Emenda 5);
    - Holm (`corrigir_por_holm`) sobre os p do DM-HLN de h = 1, 4, 8 e 12 (a familia da emenda).

Entradas (SOMENTE LEITURA):
    - `resultados/ciencia/E3_composto/previsoes.csv` (so N == 13);
    - `dados/tabela_final.csv` (sha256 conferido contra `dados/tabela_final.sha256`), coluna `casos_confirmados`
      indexada por `data_inicio_semana_epidemi`.
Ancora obrigatoria: o resultado tem de bater com
`analises/2026-10-17_persistencia_exploratorio/composto_x_persistencia.csv` (feito por reimplementacao
independente) com diferenca < 1e-12 em todas as colunas numericas; se nao bater, o script PARA sem gravar nada.
Saidas em `resultados/ciencia/composto_x_persistencia/`: `composto_x_persistencia.csv` e `README.md`.

COMO RODAR (de dentro de `projeto_final/`, sempre `python3`, nunca o `.venv`):

    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B experimentos/composto_x_persistencia.py
"""

import dataclasses
import io
import logging
import pathlib
import sys

import numpy as np
import pandas as pd

# O script e chamado pelo caminho do arquivo (nao por `-m`), entao a raiz do projeto precisa entrar no
# caminho de importacao para que `aedes` e `experimentos` sejam encontrados.
PASTA_DO_PROJETO = pathlib.Path(__file__).resolve().parents[1]
if str(PASTA_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(PASTA_DO_PROJETO))

from aedes.configuracao import (  # noqa: E402
    COLUNA_DATA_ALVO,
    COLUNA_DATA_DE_ORIGEM,
    CONFIGURACAO_DADOS,
)
from aedes.dados import validar_impressao_digital  # noqa: E402
from aedes.estatistica import (  # noqa: E402
    corrigir_por_holm,
    diebold_mariano_hln,
    ganho_percentual,
)
from experimentos.sensibilidade_newey_west import (  # noqa: E402
    LARGURA_DA_JANELA_DE_NEWEY_WEST,
    calcular_teste_de_newey_west,
)

LOGGER = logging.getLogger("composto_x_persistencia")

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
PASTA_DA_PESQUISA_DO_PROJETO = PASTA_DO_PROJETO.parent  # Meu_Projeto/
CAMINHO_DA_TABELA_FINAL = PASTA_DO_PROJETO / "dados" / "tabela_final.csv"
CAMINHO_DO_HASH_DA_TABELA_FINAL = PASTA_DO_PROJETO / "dados" / "tabela_final.sha256"
CAMINHO_DAS_PREVISOES_DO_COMPOSTO = PASTA_DO_PROJETO / "resultados" / "ciencia" / "E3_composto" / "previsoes.csv"
CAMINHO_DA_ANCORA = (
    PASTA_DA_PESQUISA_DO_PROJETO
    / "analises"
    / "2026-10-17_persistencia_exploratorio"
    / "composto_x_persistencia.csv"
)
PASTA_DE_SAIDA = PASTA_DO_PROJETO / "resultados" / "ciencia" / "composto_x_persistencia"
CAMINHO_DA_TABELA_DE_RESULTADOS = PASTA_DE_SAIDA / "composto_x_persistencia.csv"
CAMINHO_DO_README = PASTA_DE_SAIDA / "README.md"

# ----------------------------------------------------------------------------------------------
# Definicoes da comparacao
# ----------------------------------------------------------------------------------------------
NUMERO_DE_MODELOS_DO_COMPOSTO = 13
PRIMEIRA_DATA_ALVO_AVALIADA = pd.Timestamp("2024-01-07")
ULTIMA_DATA_ALVO_AVALIADA = pd.Timestamp("2026-02-01")
SEMANAS_DA_JANELA_POR_HORIZONTE = 102

HORIZONTES_DA_COMPARACAO = (1, 2, 3, 4, 8, 12)
HORIZONTES_DA_FAMILIA_DE_HOLM = (1, 4, 8, 12)

TOLERANCIA_DA_ANCORA = 1e-12
TOLERANCIA_DO_REAL_CONTRA_A_TABELA = 1e-9

COLUNA_DO_NUMERO_DE_MODELOS = "N"
COLUNA_DO_HORIZONTE = "h"
COLUNA_DO_REAL = "real"
COLUNA_DO_PREVISTO_DO_COMPOSTO = "previsto"
COLUNA_DO_PREVISTO_DA_PERSISTENCIA = "previsto_persistencia"
COLUNA_DA_DATA_DA_SEMANA_NA_TABELA = CONFIGURACAO_DADOS.coluna_de_data
COLUNA_DOS_CASOS_NA_TABELA = CONFIGURACAO_DADOS.coluna_de_casos

COLUNAS_DA_TABELA_DE_RESULTADOS = (
    "h",
    "n",
    "mae_composto",
    "mae_persistencia",
    "ganho_pct_composto",
    "p_dm_hln",
    "p_newey_west_L4",
    "p_holm_dm_hln_h1_4_8_12",
)
NOME_DA_COLUNA_DO_P_DM_HLN = "p_dm_hln"
NOME_DA_COLUNA_DO_P_DE_HOLM = "p_holm_dm_hln_h1_4_8_12"


@dataclasses.dataclass(frozen=True)
class ResultadoDoHorizonte:
    """Composto contra persistencia em UM horizonte, nas semanas-alvo da janela de avaliacao.

    Attributes:
        horizonte: Horizonte h, em semanas.
        n: Semanas pareadas.
        mae_composto: Media de |real - composto|, em casos por semana.
        mae_persistencia: Media de |real - persistencia|.
        ganho_pct_composto: `(MAE_persistencia - MAE_composto) / MAE_persistencia * 100`; negativo quando a
            persistencia erra menos.
        p_dm_hln: p bilateral do Diebold-Mariano com correcao HLN.
        p_newey_west: p bilateral de Newey-West (Bartlett, L = 4, sem HLN).
    """

    horizonte: int
    n: int
    mae_composto: float
    mae_persistencia: float
    ganho_pct_composto: float
    p_dm_hln: float
    p_newey_west: float


# ==============================================================================================
# Leitura (I/O)
# ==============================================================================================
def ler_hash_certificado(caminho_do_hash: pathlib.Path) -> str:
    """Primeiro campo de `dados/tabela_final.sha256` (formato `hash  nome_do_arquivo`).

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
        ValueError: Se o arquivo estiver vazio.
    """
    if not caminho_do_hash.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho_do_hash}")
    campos_do_arquivo = caminho_do_hash.read_text(encoding="utf-8").split()
    if len(campos_do_arquivo) == 0:
        raise ValueError(f"Arquivo de hash vazio: {caminho_do_hash}")
    return campos_do_arquivo[0]


def ler_e_conferir_bytes_da_tabela_final(caminho_da_tabela: pathlib.Path, caminho_do_hash: pathlib.Path) -> bytes:
    """Le `tabela_final.csv` em binario e confere o sha256 contra o `.sha256` e contra a configuracao do pacote.

    Args:
        caminho_da_tabela: `dados/tabela_final.csv`.
        caminho_do_hash: `dados/tabela_final.sha256`.

    Returns:
        O conteudo integral do arquivo, ja validado.

    Raises:
        FileNotFoundError: Se algum dos arquivos nao existir.
        ValueError: Se o hash divergir de qualquer das duas fontes.
    """
    if not caminho_da_tabela.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho_da_tabela}")
    hash_do_arquivo_de_hash = ler_hash_certificado(caminho_do_hash)
    conteudo_em_bytes = caminho_da_tabela.read_bytes()
    validar_impressao_digital(conteudo_em_bytes, hash_do_arquivo_de_hash)
    validar_impressao_digital(conteudo_em_bytes, CONFIGURACAO_DADOS.sha256_esperado_da_tabela)
    LOGGER.info("sha256 de %s conferido: %s", caminho_da_tabela.name, hash_do_arquivo_de_hash)
    return conteudo_em_bytes


def ler_previsoes_do_e3(caminho: pathlib.Path) -> pd.DataFrame:
    """Le `E3_composto/previsoes.csv` inteiro, com as datas convertidas e os floats em precisao total.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    previsoes_do_e3 = pd.read_csv(
        caminho,
        float_precision="round_trip",
        parse_dates=[COLUNA_DATA_DE_ORIGEM, COLUNA_DATA_ALVO],
    )
    LOGGER.info("Lido %s: %d linhas.", caminho.name, len(previsoes_do_e3))
    return previsoes_do_e3


def ler_ancora(caminho: pathlib.Path) -> pd.DataFrame:
    """Le o CSV da reimplementacao independente (`analises/2026-10-17_persistencia_exploratorio/`).

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Ancora ausente: {caminho}")
    return pd.read_csv(caminho, float_precision="round_trip")


# ==============================================================================================
# Preparo das previsoes (puro)
# ==============================================================================================
def extrair_casos_por_semana(conteudo_em_bytes: bytes) -> pd.Series:
    """Casos confirmados por semana, indexados pela data de inicio da semana epidemiologica.

    Nao aplica o corte de maturidade: as semanas usadas (origens de 2023 a jan/2026 e semanas-alvo ate
    01/02/2026) ficam antes dele, e `conferir_real_contra_a_tabela` confirma que o `real` do E3 coincide com
    esta serie.

    Args:
        conteudo_em_bytes: Conteudo de `dados/tabela_final.csv`, com o hash ja conferido.

    Returns:
        Series float com indice de datas (domingos) sem repeticao.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver data de semana repetida.
    """
    colunas_lidas = [COLUNA_DA_DATA_DA_SEMANA_NA_TABELA, COLUNA_DOS_CASOS_NA_TABELA]
    tabela_final = pd.read_csv(
        io.BytesIO(conteudo_em_bytes),
        usecols=colunas_lidas,
        parse_dates=[COLUNA_DA_DATA_DA_SEMANA_NA_TABELA],
        float_precision="round_trip",
    )
    datas_das_semanas = pd.DatetimeIndex(tabela_final[COLUNA_DA_DATA_DA_SEMANA_NA_TABELA])
    if datas_das_semanas.has_duplicates:
        raise ValueError("tabela_final.csv: data de semana repetida.")
    casos_das_semanas = tabela_final[COLUNA_DOS_CASOS_NA_TABELA].to_numpy(dtype=float)
    return pd.Series(casos_das_semanas, index=datas_das_semanas)


def recortar_composto_na_janela(previsoes_do_e3: pd.DataFrame) -> pd.DataFrame:
    """Fica com o composto N = 13, os horizontes da comparacao e as `data_alvo` de 07/01/2024 a 01/02/2026.

    Args:
        previsoes_do_e3: `E3_composto/previsoes.csv` inteiro (N = 8, 13 e 26; todas as origens).

    Returns:
        DataFrame ordenado por `h` e `data_alvo`, com indice 0..n-1.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se algum horizonte nao tiver 102 `data_alvo` distintas, ou se `real` ou `previsto`
            tiver ausente ou infinito.
    """
    colunas_obrigatorias = (
        COLUNA_DO_NUMERO_DE_MODELOS,
        COLUNA_DO_HORIZONTE,
        COLUNA_DATA_DE_ORIGEM,
        COLUNA_DATA_ALVO,
        COLUNA_DO_REAL,
        COLUNA_DO_PREVISTO_DO_COMPOSTO,
    )
    colunas_ausentes: list[str] = []
    for nome_da_coluna in colunas_obrigatorias:
        if nome_da_coluna not in previsoes_do_e3.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes em previsoes.csv: {colunas_ausentes}")

    e_composto_de_13 = previsoes_do_e3[COLUNA_DO_NUMERO_DE_MODELOS] == NUMERO_DE_MODELOS_DO_COMPOSTO
    e_horizonte_da_comparacao = previsoes_do_e3[COLUNA_DO_HORIZONTE].isin(HORIZONTES_DA_COMPARACAO)
    depois_do_inicio = previsoes_do_e3[COLUNA_DATA_ALVO] >= PRIMEIRA_DATA_ALVO_AVALIADA
    antes_do_fim = previsoes_do_e3[COLUNA_DATA_ALVO] <= ULTIMA_DATA_ALVO_AVALIADA
    previsoes_na_janela = previsoes_do_e3.loc[
        e_composto_de_13 & e_horizonte_da_comparacao & depois_do_inicio & antes_do_fim
    ]
    previsoes_ordenadas = previsoes_na_janela.sort_values([COLUNA_DO_HORIZONTE, COLUNA_DATA_ALVO])
    previsoes_ordenadas = previsoes_ordenadas.reset_index(drop=True)

    valores_reais = previsoes_ordenadas[COLUNA_DO_REAL].to_numpy(dtype=float)
    valores_previstos = previsoes_ordenadas[COLUNA_DO_PREVISTO_DO_COMPOSTO].to_numpy(dtype=float)
    if not (np.isfinite(valores_reais).all() and np.isfinite(valores_previstos).all()):
        raise ValueError("Composto N=13: `real` ou `previsto` com ausente ou infinito.")

    for horizonte in HORIZONTES_DA_COMPARACAO:
        do_horizonte = previsoes_ordenadas.loc[previsoes_ordenadas[COLUNA_DO_HORIZONTE] == horizonte]
        total_de_linhas = len(do_horizonte)
        semanas_distintas = do_horizonte[COLUNA_DATA_ALVO].nunique()
        semanas_corretas = total_de_linhas == SEMANAS_DA_JANELA_POR_HORIZONTE
        sem_repeticao = semanas_distintas == total_de_linhas
        if not (semanas_corretas and sem_repeticao):
            raise ValueError(
                f"Composto N=13, h={horizonte}: {total_de_linhas} linhas e {semanas_distintas} semanas "
                f"distintas; esperado {SEMANAS_DA_JANELA_POR_HORIZONTE} e sem repeticao."
            )
    return previsoes_ordenadas


def conferir_real_contra_a_tabela(previsoes: pd.DataFrame, casos_por_semana: pd.Series) -> float:
    """Confere que o `real` do E3 e igual aos casos de `tabela_final.csv` na `data_alvo`.

    Returns:
        A maior diferenca absoluta encontrada.

    Raises:
        ValueError: Se alguma `data_alvo` nao existir na tabela ou a diferenca passar da tolerancia.
    """
    datas_alvo = pd.DatetimeIndex(previsoes[COLUNA_DATA_ALVO])
    casos_na_data_alvo = casos_por_semana.reindex(datas_alvo).to_numpy(dtype=float)
    reais_do_e3 = previsoes[COLUNA_DO_REAL].to_numpy(dtype=float)
    if not np.isfinite(casos_na_data_alvo).all():
        raise ValueError("Ha `data_alvo` sem caso em tabela_final.csv.")
    diferenca_maxima = float(np.max(np.abs(casos_na_data_alvo - reais_do_e3)))
    if diferenca_maxima > TOLERANCIA_DO_REAL_CONTRA_A_TABELA:
        raise ValueError(f"`real` do E3 diverge de {COLUNA_DOS_CASOS_NA_TABELA}: diferenca maxima {diferenca_maxima}.")
    LOGGER.info("`real` do E3 == casos da tabela_final na data_alvo (diferenca maxima %.1e).", diferenca_maxima)
    return diferenca_maxima


def conferir_distancia_entre_origem_e_alvo(previsoes: pd.DataFrame) -> None:
    """Confere que `data_alvo - data_origem` e exatamente `h` semanas em toda linha.

    A persistencia le os casos da `data_origem`; se a distancia nao fosse `h` semanas, o comparador deixaria de
    ser "a ultima semana observada h semanas antes".

    Raises:
        ValueError: Se alguma linha tiver outra distancia.
    """
    distancia_em_dias = (previsoes[COLUNA_DATA_ALVO] - previsoes[COLUNA_DATA_DE_ORIGEM]).dt.days.to_numpy()
    distancia_esperada_em_dias = 7 * previsoes[COLUNA_DO_HORIZONTE].to_numpy()
    if not np.array_equal(distancia_em_dias, distancia_esperada_em_dias):
        raise ValueError("Ha linha em que `data_alvo - data_origem` difere de h semanas.")


def acrescentar_previsao_da_persistencia(previsoes: pd.DataFrame, casos_por_semana: pd.Series) -> pd.DataFrame:
    """Acrescenta a previsao da persistencia: casos confirmados da semana de `data_origem`.

    Args:
        previsoes: Saida de `recortar_composto_na_janela`.
        casos_por_semana: Casos por semana, indexados pela data da semana.

    Returns:
        Copia com a coluna `previsto_persistencia` a mais.

    Raises:
        ValueError: Se alguma `data_origem` nao existir na serie ou estiver sem caso.
    """
    datas_de_origem = pd.DatetimeIndex(previsoes[COLUNA_DATA_DE_ORIGEM])
    casos_na_origem = casos_por_semana.reindex(datas_de_origem).to_numpy(dtype=float)
    if not np.isfinite(casos_na_origem).all():
        raise ValueError("Persistencia: ha `data_origem` ausente ou sem caso em tabela_final.csv.")
    previsoes_com_persistencia = previsoes.copy()
    previsoes_com_persistencia[COLUNA_DO_PREVISTO_DA_PERSISTENCIA] = casos_na_origem
    return previsoes_com_persistencia


# ==============================================================================================
# Estatistica (pura)
# ==============================================================================================
def calcular_diferenca_de_perda(
    valores_reais: np.ndarray,
    previsto_do_composto: np.ndarray,
    previsto_da_persistencia: np.ndarray,
) -> np.ndarray:
    """`d_t = |real - persistencia| - |real - composto|`; positivo quer dizer que o composto erra menos.

    Args:
        valores_reais: Casos confirmados nas semanas-alvo, em ordem cronologica.
        previsto_do_composto: Previsoes do composto, mesma ordem.
        previsto_da_persistencia: Previsoes da persistencia, mesma ordem.

    Returns:
        Vetor `d_t`.
    """
    erros_absolutos_do_composto = np.abs(valores_reais - previsto_do_composto)
    erros_absolutos_da_persistencia = np.abs(valores_reais - previsto_da_persistencia)
    return erros_absolutos_da_persistencia - erros_absolutos_do_composto


def calcular_resultado_do_horizonte(previsoes_do_horizonte: pd.DataFrame, horizonte: int) -> ResultadoDoHorizonte:
    """MAE, ganho, p do DM-HLN e p de Newey-West do composto contra a persistencia em um horizonte.

    Args:
        previsoes_do_horizonte: Linhas de um horizonte, ordenadas por `data_alvo`, com o previsto do composto e
            o da persistencia.
        horizonte: Horizonte h (define quantas defasagens o DM-HLN usa).

    Returns:
        O `ResultadoDoHorizonte`.

    Raises:
        ValueError: Se o DM-HLN ficar indefinido (diferenca de perda constante).
    """
    valores_reais = previsoes_do_horizonte[COLUNA_DO_REAL].to_numpy(dtype=float)
    previsto_do_composto = previsoes_do_horizonte[COLUNA_DO_PREVISTO_DO_COMPOSTO].to_numpy(dtype=float)
    previsto_da_persistencia = previsoes_do_horizonte[COLUNA_DO_PREVISTO_DA_PERSISTENCIA].to_numpy(dtype=float)

    erros_absolutos_do_composto = np.abs(valores_reais - previsto_do_composto)
    erros_absolutos_da_persistencia = np.abs(valores_reais - previsto_da_persistencia)
    mae_do_composto = float(erros_absolutos_do_composto.mean())
    mae_da_persistencia = float(erros_absolutos_da_persistencia.mean())
    ganho_do_composto = ganho_percentual(mae_da_persistencia, mae_do_composto)

    diferencas_de_perda = calcular_diferenca_de_perda(valores_reais, previsto_do_composto, previsto_da_persistencia)
    teste_dm_hln = diebold_mariano_hln(diferencas_de_perda, horizonte)
    if not teste_dm_hln.definido:
        raise ValueError(f"DM-HLN indefinido em h={horizonte} (diferenca de perda constante?).")
    teste_newey_west = calcular_teste_de_newey_west(diferencas_de_perda, LARGURA_DA_JANELA_DE_NEWEY_WEST)

    return ResultadoDoHorizonte(
        horizonte=horizonte,
        n=len(diferencas_de_perda),
        mae_composto=mae_do_composto,
        mae_persistencia=mae_da_persistencia,
        ganho_pct_composto=ganho_do_composto,
        p_dm_hln=teste_dm_hln.p_bilateral,
        p_newey_west=teste_newey_west.p_bilateral,
    )


def montar_tabela_de_resultados(previsoes_com_persistencia: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por horizonte, mais o p de Holm sobre h = 1, 4, 8 e 12 (vazio nos demais).

    Args:
        previsoes_com_persistencia: Saida de `acrescentar_previsao_da_persistencia`.

    Returns:
        DataFrame com `COLUNAS_DA_TABELA_DE_RESULTADOS`, na ordem de `HORIZONTES_DA_COMPARACAO`.
    """
    resultados_por_horizonte: dict[int, ResultadoDoHorizonte] = {}
    for horizonte in HORIZONTES_DA_COMPARACAO:
        e_do_horizonte = previsoes_com_persistencia[COLUNA_DO_HORIZONTE] == horizonte
        previsoes_do_horizonte = previsoes_com_persistencia.loc[e_do_horizonte]
        resultados_por_horizonte[horizonte] = calcular_resultado_do_horizonte(previsoes_do_horizonte, horizonte)

    p_brutos_da_familia: list[float] = []
    for horizonte in HORIZONTES_DA_FAMILIA_DE_HOLM:
        p_brutos_da_familia.append(resultados_por_horizonte[horizonte].p_dm_hln)
    p_de_holm_da_familia = corrigir_por_holm(np.array(p_brutos_da_familia, dtype=float))
    p_de_holm_por_horizonte: dict[int, float] = {}
    for posicao, horizonte in enumerate(HORIZONTES_DA_FAMILIA_DE_HOLM):
        p_de_holm_por_horizonte[horizonte] = float(p_de_holm_da_familia[posicao])

    linhas_da_tabela: list[dict[str, float | int]] = []
    for horizonte in HORIZONTES_DA_COMPARACAO:
        resultado = resultados_por_horizonte[horizonte]
        p_de_holm = p_de_holm_por_horizonte.get(horizonte, float("nan"))
        linhas_da_tabela.append(
            {
                "h": resultado.horizonte,
                "n": resultado.n,
                "mae_composto": resultado.mae_composto,
                "mae_persistencia": resultado.mae_persistencia,
                "ganho_pct_composto": resultado.ganho_pct_composto,
                NOME_DA_COLUNA_DO_P_DM_HLN: resultado.p_dm_hln,
                "p_newey_west_L4": resultado.p_newey_west,
                NOME_DA_COLUNA_DO_P_DE_HOLM: p_de_holm,
            }
        )
    return pd.DataFrame(linhas_da_tabela, columns=list(COLUNAS_DA_TABELA_DE_RESULTADOS))


def calcular_maior_diferenca_contra_a_ancora(tabela_de_resultados: pd.DataFrame, ancora: pd.DataFrame) -> float:
    """Maior diferenca absoluta, coluna a coluna, entre o resultado e a ancora independente.

    Confere o nome e a ordem das colunas, os horizontes e a posicao dos vazios (NaN do Holm em h = 2 e 3);
    a diferenca e medida so onde os dois lados tem valor.

    Args:
        tabela_de_resultados: Saida de `montar_tabela_de_resultados`.
        ancora: CSV da reimplementacao independente.

    Returns:
        A maior diferenca absoluta em todas as colunas numericas.

    Raises:
        RuntimeError: Se as colunas, os horizontes ou os vazios divergirem, ou se alguma diferenca for
            maior ou igual a `TOLERANCIA_DA_ANCORA`.
    """
    if list(tabela_de_resultados.columns) != list(ancora.columns):
        raise RuntimeError(
            f"Colunas da ancora divergem: {list(ancora.columns)} contra {list(tabela_de_resultados.columns)}."
        )
    if len(tabela_de_resultados) != len(ancora):
        raise RuntimeError(f"Linhas da ancora: {len(ancora)}; do resultado: {len(tabela_de_resultados)}.")

    maior_diferenca = 0.0
    for nome_da_coluna in tabela_de_resultados.columns:
        valores_medidos = tabela_de_resultados[nome_da_coluna].to_numpy(dtype=float)
        valores_da_ancora = ancora[nome_da_coluna].to_numpy(dtype=float)
        vazios_medidos = np.isnan(valores_medidos)
        vazios_da_ancora = np.isnan(valores_da_ancora)
        if not np.array_equal(vazios_medidos, vazios_da_ancora):
            raise RuntimeError(f"Coluna {nome_da_coluna!r}: os vazios (NaN) nao coincidem com a ancora.")
        com_valor = ~vazios_medidos
        if not com_valor.any():
            continue
        diferencas = np.abs(valores_medidos[com_valor] - valores_da_ancora[com_valor])
        diferenca_da_coluna = float(diferencas.max())
        LOGGER.info("Ancora, coluna %s: diferenca maxima %.3e.", nome_da_coluna, diferenca_da_coluna)
        maior_diferenca = max(maior_diferenca, diferenca_da_coluna)

    if maior_diferenca >= TOLERANCIA_DA_ANCORA:
        raise RuntimeError(f"Resultado nao bate com a ancora: diferenca maxima {maior_diferenca:.3e}.")
    return maior_diferenca


# ==============================================================================================
# README (puro)
# ==============================================================================================
def formatar_p(valor: float) -> str:
    """p-valor para o README: tres casas decimais com virgula, ou `<0,001`; vazio vira travessao."""
    if np.isnan(valor):
        return "—"
    if valor < 0.001:
        return "<0,001"
    return f"{valor:.3f}".replace(".", ",")


def formatar_ganho(valor: float) -> str:
    """Ganho percentual com uma casa, sinal explicito e virgula (sinal de menos tipografico)."""
    texto_do_modulo = f"{abs(valor):.1f}".replace(".", ",")
    if round(valor, 1) < 0.0:
        return f"−{texto_do_modulo}%"
    return f"+{texto_do_modulo}%"


def montar_texto_do_readme(tabela_de_resultados: pd.DataFrame, maior_diferenca_da_ancora: float) -> str:
    """Texto do README: o que e, Emenda 6, metodo, ancora e a tabela dos 6 horizontes."""
    linhas_da_tabela: list[str] = []
    for _, linha in tabela_de_resultados.iterrows():
        mae_do_composto = f"{linha['mae_composto']:.1f}".replace(".", ",")
        mae_da_persistencia = f"{linha['mae_persistencia']:.1f}".replace(".", ",")
        linhas_da_tabela.append(
            f"| {int(linha['h'])} | {mae_do_composto} | {mae_da_persistencia}"
            + f" | {formatar_ganho(linha['ganho_pct_composto'])}"
            + f" | {formatar_p(linha[NOME_DA_COLUNA_DO_P_DM_HLN])}"
            + f" | {formatar_p(linha['p_newey_west_L4'])}"
            + f" | {formatar_p(linha[NOME_DA_COLUNA_DO_P_DE_HOLM])} |"
        )
    corpo_da_tabela = "\n".join(linhas_da_tabela)
    cabecalho_da_tabela = (
        "| h | MAE do composto | MAE da persistência | Ganho do composto | p DM-HLN | p Newey-West "
        "| p de Holm (h = 1, 4, 8, 12) |\n"
        "|---|---|---|---|---|---|---|"
    )
    menor_p_de_holm = float(tabela_de_resultados[NOME_DA_COLUNA_DO_P_DE_HOLM].min())

    return f"""# Composto × persistência (exploratório)

Gerado por `experimentos/composto_x_persistencia.py` (não editar à mão; refazer pelo script).

## O que é

- **Comparação exploratória, não pré-declarada**, registrada como **Emenda 6** da pré-declaração
  (`analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, 17/10/2026, Vinicius), depois de medida.
- **Persistência:** a previsão da semana-alvo é o número de casos confirmados da semana de origem (`data_origem`).
- **Uso:** só no material suplementar (S3), tabela `tabelaS_persistencia.tex`. Nenhum veredito pré-declarado muda.
- Nenhum modelo foi treinado; nenhum módulo ou resultado existente foi alterado.

## Método

- **Composto:** E3, N = 13 (`resultados/ciencia/E3_composto/previsoes.csv`); persistência a partir de
  `dados/tabela_final.csv` (sha256 conferido), coluna `casos_confirmados`.
- **Janela:** semanas-alvo de 07/01/2024 a 01/02/2026, 102 por horizonte; h = 1, 2, 3, 4, 8 e 12.
- **Diferença de perda:** d = |real − persistência| − |real − composto|; positivo = o composto erra menos.
- **DM-HLN:** o método pré-declarado (`aedes/estatistica.py`), bilateral. **Newey-West:** Bartlett, L = 4, sem HLN, t com
  n − 1 g.l. (leitura extra, sem correção de multiplicidade).
- **Holm:** sobre os p do DM-HLN de h = 1, 4, 8 e 12 (a família fixada na Emenda 6); h = 2 e 3 ficam sem correção.

## Âncora

- **Reprodução:** o resultado bate com o CSV medido em 17/10/2026
  (`analises/2026-10-17_persistencia_exploratorio/composto_x_persistencia.csv`) com diferença máxima
  **{maior_diferenca_da_ancora:.1e}** em todas as colunas (limite do script: 1e-12). Aquele CSV foi confirmado por uma
  reimplementação independente, sem o código do projeto, com diferença máxima de 8,9e-16.

## Resultado

{cabecalho_da_tabela}
{corpo_da_tabela}

Ganho = (MAE da persistência − MAE do composto) ÷ MAE da persistência; negativo quando a persistência erra menos.
Valores completos (precisão total) em `composto_x_persistencia.csv`.

## Limites

- **Fato:** o menor p de Holm é {formatar_p(menor_p_de_holm)}; nenhum passa de 0,05.
- **Fato:** a comparação inteira, inclusive a família de Holm (4 testes) e o Newey-West, não foi pré-declarada; a leitura
  é exploratória.
- **Fato:** a persistência usa o dado consolidado, como o resto da avaliação (sem dados da época).
"""


# ==============================================================================================
# Orquestracao
# ==============================================================================================
def main() -> int:
    """Le as entradas certificadas, calcula a comparacao, confere a ancora e grava o CSV e o README.

    Returns:
        0 se terminou; uma excecao interrompe a analise antes de gravar qualquer saida.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    conteudo_da_tabela_final = ler_e_conferir_bytes_da_tabela_final(
        CAMINHO_DA_TABELA_FINAL, CAMINHO_DO_HASH_DA_TABELA_FINAL
    )
    casos_por_semana = extrair_casos_por_semana(conteudo_da_tabela_final)
    previsoes_do_e3 = ler_previsoes_do_e3(CAMINHO_DAS_PREVISOES_DO_COMPOSTO)

    previsoes_na_janela = recortar_composto_na_janela(previsoes_do_e3)
    conferir_real_contra_a_tabela(previsoes_na_janela, casos_por_semana)
    conferir_distancia_entre_origem_e_alvo(previsoes_na_janela)
    previsoes_com_persistencia = acrescentar_previsao_da_persistencia(previsoes_na_janela, casos_por_semana)

    tabela_de_resultados = montar_tabela_de_resultados(previsoes_com_persistencia)

    ancora = ler_ancora(CAMINHO_DA_ANCORA)
    maior_diferenca_da_ancora = calcular_maior_diferenca_contra_a_ancora(tabela_de_resultados, ancora)
    LOGGER.info("Ancora aprovada: diferenca maxima %.3e (limite %.0e).", maior_diferenca_da_ancora, TOLERANCIA_DA_ANCORA)

    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    tabela_de_resultados.to_csv(CAMINHO_DA_TABELA_DE_RESULTADOS, index=False)
    texto_do_readme = montar_texto_do_readme(tabela_de_resultados, maior_diferenca_da_ancora)
    CAMINHO_DO_README.write_text(texto_do_readme, encoding="utf-8")
    LOGGER.info(
        "Gravados %s (%d linhas) e %s.",
        CAMINHO_DA_TABELA_DE_RESULTADOS,
        len(tabela_de_resultados),
        CAMINHO_DO_README,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
