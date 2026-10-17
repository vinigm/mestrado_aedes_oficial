"""Gera a tabela suplementar "abertura por temporada" (composto x regua sazonal, 2024 e 2025).

Analise feita DEPOIS da avaliacao e NAO pre-declarada (aprovada pelo Vinicius em 17/10/2026): ela
nao altera nenhum numero do artigo; so reabre, por temporada (ano da `data_alvo`), as metricas que
o corpo do texto traz para as 102 semanas juntas.

Para cada horizonte (1, 2, 3, 4, 8 e 12 semanas) e cada temporada (2024 e 2025) calcula, para o
modelo composto (E3, N = 13) e para a regua sazonal, nas semanas-alvo da temporada:
    - MAE = media de |real - previsto|;
    - R2 = 1 - SSE / SST, com a media do real NA PROPRIA temporada;
    - fracao do pico = media(previsto) / media(real), so nas semanas com real > 100 casos;
    - alarme = semanas com real > L e previsto > L, sobre as semanas com real > L (Alerta),
      com L = 447,0654 (= 421 x 1,0619, limiar do plano convertido para a escala da notificacao).
A regua sazonal preve os casos da semana `data_alvo` - 52 semanas (364 dias), lidos de
`dados/tabela_final.csv` (coluna `casos_confirmados`).

As 5 semanas-alvo de janeiro de 2026 (fim da janela de avaliacao, 01/02/2026) ficam FORA da tabela:
a temporada e o ano da `data_alvo` e a tabela traz so 2024 e 2025. Elas entram apenas na
conferencia contra os arquivos certificados do alarme (a soma de 2024 + 2025 + jan/2026 tem de
reproduzir os totais da janela inteira).

Entradas (SOMENTE LEITURA, certificadas):
    - `resultados/ciencia/E3_composto/previsoes.csv` (so N == 13);
    - `dados/tabela_final.csv` (sha256 conferido contra `dados/tabela_final.sha256`);
    - `resultados/ciencia/E5_alarme/razao.json` (L exato), `alarme.csv`, `alarme_reguas.csv` e
      `alarme_h12.csv` (so para a conferencia).
Saida (unica):
    - `entregas/artigo/tabelas/tabelaS_temporadas.tex` (so o ambiente `table`, sem \\section).

Ancoras numericas (calculadas antes) estao em `ANCORAS_DAS_LINHAS`; se qualquer uma divergir, o
script PARA com a diferenca e nao grava a tabela. Nenhum modelo e treinado.

Rodar, de dentro de projeto_final/:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_tabela_temporadas.py
"""

import dataclasses
import hashlib
import json
import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("tabela_temporadas")

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
PASTA_DA_PESQUISA = PASTA_DO_PACOTE.parents[1]

ARQUIVO_DA_TABELA_FINAL = PASTA_DO_PACOTE / "dados" / "tabela_final.csv"
ARQUIVO_DO_HASH_DA_TABELA_FINAL = PASTA_DO_PACOTE / "dados" / "tabela_final.sha256"
ARQUIVO_DAS_PREVISOES_DO_COMPOSTO = PASTA_DO_PACOTE / "resultados" / "ciencia" / "E3_composto" / "previsoes.csv"
PASTA_DO_ALARME = PASTA_DO_PACOTE / "resultados" / "ciencia" / "E5_alarme"
ARQUIVO_DA_RAZAO_DO_ALARME = PASTA_DO_ALARME / "razao.json"
ARQUIVO_DO_ALARME_DO_COMPOSTO = PASTA_DO_ALARME / "alarme.csv"
ARQUIVO_DO_ALARME_DAS_REGUAS = PASTA_DO_ALARME / "alarme_reguas.csv"
ARQUIVO_DO_ALARME_EM_H12 = PASTA_DO_ALARME / "alarme_h12.csv"
ARQUIVO_DE_SAIDA = PASTA_DA_PESQUISA / "entregas" / "artigo" / "tabelas" / "tabelaS_temporadas.tex"

CAMINHO_DO_SCRIPT_PARA_O_COMENTARIO = "Meu_Projeto/projeto_final/figuras/gerar_tabela_temporadas.py"
DATA_DA_GERACAO = "17/10/2026"

# ----------------------------------------------------------------------------------------------
# Definicoes do artigo
# ----------------------------------------------------------------------------------------------
NUMERO_DE_MODELOS_DO_COMPOSTO = 13
PRIMEIRA_DATA_ALVO_AVALIADA = pd.Timestamp("2024-01-07")
ULTIMA_DATA_ALVO_AVALIADA = pd.Timestamp("2026-02-01")
SEMANAS_DA_JANELA_POR_HORIZONTE = 102

HORIZONTES_DA_TABELA = (1, 2, 3, 4, 8, 12)
TEMPORADAS_DA_TABELA = (2024, 2025)
TEMPORADA_FORA_DA_TABELA = 2026
SEMANAS_DA_TEMPORADA_FORA_DA_TABELA = 5
TEMPORADAS_DA_JANELA = TEMPORADAS_DA_TABELA + (TEMPORADA_FORA_DA_TABELA,)

SEMANAS_DO_PASSO_SAZONAL = 52
# Semana de pico = semana-alvo com MAIS de 100 casos confirmados (convencao do projeto).
LIMIAR_DE_PICO_EM_CASOS = 100.0
LIMIAR_DO_ALARME_ARREDONDADO = 447.0654
TOLERANCIA_DO_LIMIAR_ARREDONDADO = 5e-5
# Horizontes conferidos contra os arquivos certificados do alarme.
HORIZONTES_DA_CONFERENCIA_DO_ALARME = (1, 4, 8, 12)

NOME_DO_BRACO_DO_COMPOSTO_NO_ALARME = "composto_N13"
NOME_DO_BRACO_DA_REGUA_NO_ALARME = "regua_sazonal"
TOLERANCIA_DO_LIMIAR_ENTRE_ARQUIVOS = 1e-6
TOLERANCIA_DO_REAL_CONTRA_A_TABELA = 1e-9

COLUNA_DO_NUMERO_DE_MODELOS = "N"
COLUNA_DO_HORIZONTE = "h"
COLUNA_DA_DATA_ALVO = "data_alvo"
COLUNA_DO_REAL = "real"
COLUNA_DO_PREVISTO_DO_COMPOSTO = "previsto"
COLUNA_DO_PREVISTO_DA_REGUA = "previsto_regua"
COLUNA_DA_TEMPORADA = "temporada"
COLUNA_DA_DATA_DA_SEMANA_NA_TABELA = "data_inicio_semana_epidemi"
COLUNA_DOS_CASOS_NA_TABELA = "casos_confirmados"

# ----------------------------------------------------------------------------------------------
# Apresentacao
# ----------------------------------------------------------------------------------------------
ROTULO_DO_ALARME_X_DE_Y = "{detectadas} de {alerta}"
SEPARADOR_DAS_DUAS_SERIES = " / "


class ChaveDaLinha(NamedTuple):
    """Identifica uma linha da tabela: um horizonte em uma temporada."""

    horizonte: int
    temporada: int


@dataclasses.dataclass(frozen=True)
class MetricasDoGrupo:
    """Metricas de UM modelo em UMA temporada de UM horizonte.

    Attributes:
        n_de_semanas: Semanas-alvo avaliadas no grupo.
        mae: Media de |real - previsto|, em casos por semana.
        r2: 1 - SSE / SST, com a media do real do proprio grupo.
        fracao_do_pico: media(previsto) / media(real) nas semanas com real > 100.
        semanas_de_alerta: Semanas com real > L.
        alertas_detectados: Semanas com real > L e previsto > L.
        alarmes_falsos: Semanas com real <= L e previsto > L.
    """

    n_de_semanas: int
    mae: float
    r2: float
    fracao_do_pico: float
    semanas_de_alerta: int
    alertas_detectados: int
    alarmes_falsos: int


@dataclasses.dataclass(frozen=True)
class ParDeMetricas:
    """Metricas do composto e da regua sazonal no mesmo grupo de semanas."""

    composto: MetricasDoGrupo
    regua: MetricasDoGrupo


@dataclasses.dataclass(frozen=True)
class AncoraDaLinha:
    """Valores esperados (calculados antes) de uma linha da tabela, ja arredondados como na tabela.

    Attributes:
        horizonte: Horizonte em semanas.
        temporada: Ano da `data_alvo`.
        n_de_semanas: Semanas da linha; None quando a ancora nao informa.
        mae_composto: MAE do composto, inteiro.
        mae_regua: MAE da regua, inteiro.
        r2_composto: R2 do composto, 2 casas.
        r2_regua: R2 da regua, 2 casas.
        fracao_do_pico_composto_em_pct: Fracao do pico do composto, em % inteiro.
        fracao_do_pico_regua_em_pct: Fracao do pico da regua, em % inteiro.
        alertas_detectados_composto: Semanas de Alerta reconhecidas pelo composto.
        alertas_detectados_regua: Semanas de Alerta reconhecidas pela regua.
        semanas_de_alerta: Semanas de Alerta da linha (o mesmo para os dois modelos).
    """

    horizonte: int
    temporada: int
    n_de_semanas: int | None
    mae_composto: int
    mae_regua: int
    r2_composto: float
    r2_regua: float
    fracao_do_pico_composto_em_pct: int
    fracao_do_pico_regua_em_pct: int
    alertas_detectados_composto: int
    alertas_detectados_regua: int
    semanas_de_alerta: int


ANCORAS_DAS_LINHAS = (
    AncoraDaLinha(
        horizonte=1,
        temporada=2024,
        n_de_semanas=45,
        mae_composto=102,
        mae_regua=245,
        r2_composto=0.85,
        r2_regua=0.27,
        fracao_do_pico_composto_em_pct=76,
        fracao_do_pico_regua_em_pct=25,
        alertas_detectados_composto=9,
        alertas_detectados_regua=4,
        semanas_de_alerta=10,
    ),
    AncoraDaLinha(
        horizonte=1,
        temporada=2025,
        n_de_semanas=52,
        mae_composto=111,
        mae_regua=180,
        r2_composto=0.91,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=94,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=14,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=2,
        temporada=2024,
        n_de_semanas=None,
        mae_composto=173,
        mae_regua=246,
        r2_composto=0.63,
        r2_regua=0.28,
        fracao_do_pico_composto_em_pct=61,
        fracao_do_pico_regua_em_pct=28,
        alertas_detectados_composto=10,
        alertas_detectados_regua=5,
        semanas_de_alerta=11,
    ),
    AncoraDaLinha(
        horizonte=2,
        temporada=2025,
        n_de_semanas=None,
        mae_composto=210,
        mae_regua=180,
        r2_composto=0.72,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=84,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=14,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=3,
        temporada=2024,
        n_de_semanas=None,
        mae_composto=150,
        mae_regua=267,
        r2_composto=0.71,
        r2_regua=0.28,
        fracao_do_pico_composto_em_pct=64,
        fracao_do_pico_regua_em_pct=29,
        alertas_detectados_composto=12,
        alertas_detectados_regua=6,
        semanas_de_alerta=12,
    ),
    AncoraDaLinha(
        horizonte=3,
        temporada=2025,
        n_de_semanas=None,
        mae_composto=258,
        mae_regua=180,
        r2_composto=0.63,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=78,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=14,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=4,
        temporada=2024,
        n_de_semanas=None,
        mae_composto=204,
        mae_regua=271,
        r2_composto=0.56,
        r2_regua=0.28,
        fracao_do_pico_composto_em_pct=54,
        fracao_do_pico_regua_em_pct=31,
        alertas_detectados_composto=12,
        alertas_detectados_regua=7,
        semanas_de_alerta=13,
    ),
    AncoraDaLinha(
        horizonte=4,
        temporada=2025,
        n_de_semanas=None,
        mae_composto=225,
        mae_regua=180,
        r2_composto=0.75,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=78,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=14,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=8,
        temporada=2024,
        n_de_semanas=None,
        mae_composto=251,
        mae_regua=277,
        r2_composto=0.37,
        r2_regua=0.25,
        fracao_do_pico_composto_em_pct=41,
        fracao_do_pico_regua_em_pct=34,
        alertas_detectados_composto=9,
        alertas_detectados_regua=8,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=8,
        temporada=2025,
        n_de_semanas=None,
        mae_composto=237,
        mae_regua=180,
        r2_composto=0.64,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=55,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=14,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=12,
        temporada=2024,
        n_de_semanas=None,
        mae_composto=332,
        mae_regua=281,
        r2_composto=0.01,
        r2_regua=0.24,
        fracao_do_pico_composto_em_pct=23,
        fracao_do_pico_regua_em_pct=34,
        alertas_detectados_composto=1,
        alertas_detectados_regua=8,
        semanas_de_alerta=14,
    ),
    AncoraDaLinha(
        horizonte=12,
        temporada=2025,
        n_de_semanas=None,
        mae_composto=220,
        mae_regua=180,
        r2_composto=0.73,
        r2_regua=0.79,
        fracao_do_pico_composto_em_pct=61,
        fracao_do_pico_regua_em_pct=75,
        alertas_detectados_composto=11,
        alertas_detectados_regua=13,
        semanas_de_alerta=14,
    ),
)


# ==============================================================================================
# Leitura (I/O)
# ==============================================================================================
def conferir_hash_da_tabela_final(caminho_da_tabela: Path, caminho_do_hash: Path) -> None:
    """Confere o sha256 de `tabela_final.csv` contra o arquivo `.sha256` certificado.

    Args:
        caminho_da_tabela: `dados/tabela_final.csv`.
        caminho_do_hash: `dados/tabela_final.sha256` (formato `hash  nome_do_arquivo`).

    Raises:
        FileNotFoundError: Se algum dos dois arquivos nao existir.
        ValueError: Se o arquivo de hash estiver vazio ou o hash divergir.
    """
    for caminho in (caminho_da_tabela, caminho_do_hash):
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")

    conteudo_do_arquivo_de_hash = caminho_do_hash.read_text(encoding="utf-8").split()
    if not conteudo_do_arquivo_de_hash:
        raise ValueError(f"Arquivo de hash vazio: {caminho_do_hash}")
    hash_certificado = conteudo_do_arquivo_de_hash[0].lower()

    bytes_da_tabela = caminho_da_tabela.read_bytes()
    hash_medido = hashlib.sha256(bytes_da_tabela).hexdigest()
    if hash_medido != hash_certificado:
        raise ValueError(f"sha256 de {caminho_da_tabela.name} diverge: medido {hash_medido}, certificado {hash_certificado}.")
    LOGGER.info("sha256 de %s conferido: %s", caminho_da_tabela.name, hash_medido)


def validar_colunas(tabela: pd.DataFrame, colunas_obrigatorias: tuple[str, ...], nome_da_tabela: str) -> None:
    """Garante que a tabela tenha as colunas exigidas.

    Raises:
        KeyError: Se alguma coluna obrigatoria estiver ausente.
    """
    colunas_ausentes = []
    for nome_da_coluna in colunas_obrigatorias:
        if nome_da_coluna not in tabela.columns:
            colunas_ausentes.append(nome_da_coluna)
    if colunas_ausentes:
        raise KeyError(f"Colunas ausentes em {nome_da_tabela}: {colunas_ausentes}")


def ler_previsoes_do_composto(caminho: Path) -> pd.DataFrame:
    """Previsoes do composto (N = 13) nas semanas-alvo da janela de avaliacao.

    O arquivo do E3 traz tres variantes (N = 8, 13 e 26) e todas as origens do walk-forward; aqui
    ficam so N = 13 e as `data_alvo` de 07/01/2024 a 01/02/2026 (limites incluidos).

    Args:
        caminho: `E3_composto/previsoes.csv`.

    Returns:
        DataFrame com `h`, `data_alvo`, `real` e `previsto`, ordenado por `h` e `data_alvo`.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
        KeyError: Se faltar coluna.
        ValueError: Se a janela nao tiver 102 semanas distintas por horizonte, ou se `real` ou
            `previsto` tiver ausente ou infinito.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    previsoes_do_e3 = pd.read_csv(caminho, float_precision="round_trip", parse_dates=[COLUNA_DA_DATA_ALVO])
    LOGGER.info("Lido %s: %d linhas.", caminho.name, len(previsoes_do_e3))

    colunas_obrigatorias = (
        COLUNA_DO_NUMERO_DE_MODELOS,
        COLUNA_DO_HORIZONTE,
        COLUNA_DA_DATA_ALVO,
        COLUNA_DO_REAL,
        COLUNA_DO_PREVISTO_DO_COMPOSTO,
    )
    validar_colunas(previsoes_do_e3, colunas_obrigatorias, caminho.name)

    e_composto_de_13 = previsoes_do_e3[COLUNA_DO_NUMERO_DE_MODELOS] == NUMERO_DE_MODELOS_DO_COMPOSTO
    depois_do_inicio = previsoes_do_e3[COLUNA_DA_DATA_ALVO] >= PRIMEIRA_DATA_ALVO_AVALIADA
    antes_do_fim = previsoes_do_e3[COLUNA_DA_DATA_ALVO] <= ULTIMA_DATA_ALVO_AVALIADA
    previsoes_na_janela = previsoes_do_e3.loc[e_composto_de_13 & depois_do_inicio & antes_do_fim]

    colunas_mantidas = [
        COLUNA_DO_HORIZONTE,
        COLUNA_DA_DATA_ALVO,
        COLUNA_DO_REAL,
        COLUNA_DO_PREVISTO_DO_COMPOSTO,
    ]
    previsoes_ordenadas = previsoes_na_janela[colunas_mantidas].sort_values(
        [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO]
    )
    previsoes_ordenadas = previsoes_ordenadas.reset_index(drop=True)

    valores_reais = previsoes_ordenadas[COLUNA_DO_REAL].to_numpy(dtype=float)
    valores_previstos = previsoes_ordenadas[COLUNA_DO_PREVISTO_DO_COMPOSTO].to_numpy(dtype=float)
    if not (np.isfinite(valores_reais).all() and np.isfinite(valores_previstos).all()):
        raise ValueError("Composto N=13: `real` ou `previsto` com ausente ou infinito.")

    for horizonte in HORIZONTES_DA_TABELA:
        do_horizonte = previsoes_ordenadas.loc[previsoes_ordenadas[COLUNA_DO_HORIZONTE] == horizonte]
        semanas_distintas = do_horizonte[COLUNA_DA_DATA_ALVO].nunique()
        total_de_linhas = len(do_horizonte)
        semanas_corretas = total_de_linhas == SEMANAS_DA_JANELA_POR_HORIZONTE
        sem_repeticao = semanas_distintas == total_de_linhas
        if not (semanas_corretas and sem_repeticao):
            raise ValueError(
                f"Composto N=13, h={horizonte}: {total_de_linhas} linhas e {semanas_distintas} semanas "
                f"distintas; esperado {SEMANAS_DA_JANELA_POR_HORIZONTE} e sem repeticao."
            )
    return previsoes_ordenadas


def ler_casos_por_semana(caminho: Path) -> pd.Series:
    """Casos confirmados por semana de `tabela_final.csv`, indexados pela data da semana.

    Nao aplica o corte de maturidade: as semanas usadas aqui (`data_alvo` ate 01/02/2026 e
    `data_alvo` - 52 semanas, ate 02/02/2025) ficam todas antes do corte (que comeca depois de
    01/02/2026), e o script confere que o `real` do E3 coincide com esta serie.

    Args:
        caminho: `dados/tabela_final.csv` (hash ja conferido).

    Returns:
        Series float com indice de datas (domingos) sem repeticao.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver data repetida.
    """
    colunas_lidas = [COLUNA_DA_DATA_DA_SEMANA_NA_TABELA, COLUNA_DOS_CASOS_NA_TABELA]
    tabela_final = pd.read_csv(
        caminho,
        usecols=colunas_lidas,
        parse_dates=[COLUNA_DA_DATA_DA_SEMANA_NA_TABELA],
        float_precision="round_trip",
    )
    LOGGER.info("Lido %s: %d semanas.", caminho.name, len(tabela_final))

    datas_das_semanas = pd.DatetimeIndex(tabela_final[COLUNA_DA_DATA_DA_SEMANA_NA_TABELA])
    if datas_das_semanas.has_duplicates:
        raise ValueError(f"{caminho.name}: data de semana repetida.")
    casos_das_semanas = tabela_final[COLUNA_DOS_CASOS_NA_TABELA].to_numpy(dtype=float)
    return pd.Series(casos_das_semanas, index=datas_das_semanas)


def ler_limiar_do_alarme(caminho: Path) -> float:
    """Limiar L exato do alarme (421 x razao notificacao/residencia), de `razao.json`.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
        KeyError: Se faltar a chave `L`.
        ValueError: Se L diferir de 447,0654 (valor do artigo) alem do arredondamento.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    limiar_exato = float(conteudo["L"])
    diferenca_para_o_valor_do_artigo = abs(limiar_exato - LIMIAR_DO_ALARME_ARREDONDADO)
    if diferenca_para_o_valor_do_artigo > TOLERANCIA_DO_LIMIAR_ARREDONDADO:
        raise ValueError(f"L de {caminho.name} = {limiar_exato}, esperado {LIMIAR_DO_ALARME_ARREDONDADO}.")
    LOGGER.info("Limiar do alarme (de %s): L = %.10f.", caminho.name, limiar_exato)
    return limiar_exato


def ler_alarme_certificado(caminhos: tuple[Path, ...]) -> pd.DataFrame:
    """Junta os CSVs certificados do alarme (E5, E5b e E5c) em uma tabela so.

    Raises:
        FileNotFoundError: Se algum arquivo nao existir.
        KeyError: Se faltar coluna.
    """
    tabelas_lidas: list[pd.DataFrame] = []
    for caminho in caminhos:
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
        tabela_do_arquivo = pd.read_csv(caminho, float_precision="round_trip")
        colunas_obrigatorias = ("braco", "h", "limiar", "n", "semanas_de_surto", "VP", "FN", "FP")
        validar_colunas(tabela_do_arquivo, colunas_obrigatorias, caminho.name)
        tabelas_lidas.append(tabela_do_arquivo)
        LOGGER.info("Lido %s: %d linhas.", caminho.name, len(tabela_do_arquivo))
    return pd.concat(tabelas_lidas, ignore_index=True)


# ==============================================================================================
# Preparo das previsoes (puro)
# ==============================================================================================
def montar_previsao_da_regua_sazonal(datas_alvo: pd.Series, casos_por_semana: pd.Series) -> np.ndarray:
    """Regua sazonal: previsao da semana `data_alvo` = casos de `data_alvo` - 52 semanas.

    Args:
        datas_alvo: Semanas-alvo (Timestamps).
        casos_por_semana: Casos por semana, indexados pela data da semana.

    Returns:
        Array float com a previsao da regua, na ordem de `datas_alvo`.

    Raises:
        ValueError: Se alguma semana de 52 semanas antes nao existir na serie ou estiver sem caso.
    """
    atraso_sazonal = pd.Timedelta(weeks=SEMANAS_DO_PASSO_SAZONAL)
    datas_um_ano_antes = pd.DatetimeIndex(datas_alvo - atraso_sazonal)
    previsao_da_regua = casos_por_semana.reindex(datas_um_ano_antes).to_numpy(dtype=float)
    if not np.isfinite(previsao_da_regua).all():
        raise ValueError("Regua sazonal: ha semana de 52 semanas antes ausente ou sem caso na serie.")
    return previsao_da_regua


def conferir_real_contra_a_tabela(previsoes: pd.DataFrame, casos_por_semana: pd.Series) -> None:
    """Confere que o `real` do E3 e igual aos casos da `tabela_final.csv` na `data_alvo`.

    Raises:
        ValueError: Na primeira divergencia acima da tolerancia.
    """
    datas_alvo = pd.DatetimeIndex(previsoes[COLUNA_DA_DATA_ALVO])
    casos_na_data_alvo = casos_por_semana.reindex(datas_alvo).to_numpy(dtype=float)
    reais_do_e3 = previsoes[COLUNA_DO_REAL].to_numpy(dtype=float)
    diferenca_maxima = float(np.nanmax(np.abs(casos_na_data_alvo - reais_do_e3)))
    tem_semana_sem_caso = bool(np.isnan(casos_na_data_alvo).any())
    if tem_semana_sem_caso or diferenca_maxima > TOLERANCIA_DO_REAL_CONTRA_A_TABELA:
        raise ValueError(f"`real` do E3 diverge de {COLUNA_DOS_CASOS_NA_TABELA}: diferenca maxima {diferenca_maxima}.")
    LOGGER.info("`real` do E3 == casos da tabela_final na data_alvo (diferenca maxima %.1e).", diferenca_maxima)


def preparar_previsoes_com_a_regua(previsoes_do_composto: pd.DataFrame, casos_por_semana: pd.Series) -> pd.DataFrame:
    """Acrescenta a previsao da regua sazonal e a temporada (ano da `data_alvo`).

    Args:
        previsoes_do_composto: Saida de `ler_previsoes_do_composto`.
        casos_por_semana: Casos por semana da tabela final.

    Returns:
        Copia com as colunas `previsto_regua` e `temporada` a mais.
    """
    previsoes = previsoes_do_composto.copy()
    previsoes[COLUNA_DO_PREVISTO_DA_REGUA] = montar_previsao_da_regua_sazonal(
        previsoes[COLUNA_DA_DATA_ALVO],
        casos_por_semana,
    )
    previsoes[COLUNA_DA_TEMPORADA] = previsoes[COLUNA_DA_DATA_ALVO].dt.year
    return previsoes


# ==============================================================================================
# Metricas (puras)
# ==============================================================================================
def calcular_mae(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """Erro absoluto medio: media de |real - previsto|, em casos por semana."""
    erros_absolutos = np.abs(valores_reais - valores_previstos)
    return float(np.mean(erros_absolutos))


def calcular_r2_dentro_do_grupo(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """R2 = 1 - SSE / SST, com a media do real calculada SO nas semanas recebidas.

    Raises:
        ValueError: Se houver menos de 2 semanas ou a serie real for constante (SST = 0).
    """
    if len(valores_reais) < 2:
        raise ValueError("R2 pede ao menos 2 semanas.")
    media_do_real = float(np.mean(valores_reais))
    soma_dos_quadrados_residuais = float(np.sum((valores_reais - valores_previstos) ** 2))
    soma_dos_quadrados_totais = float(np.sum((valores_reais - media_do_real) ** 2))
    if soma_dos_quadrados_totais == 0.0:
        raise ValueError("R2 indefinido: serie real constante no grupo.")
    return 1.0 - soma_dos_quadrados_residuais / soma_dos_quadrados_totais


def calcular_fracao_do_pico(valores_reais: np.ndarray, valores_previstos: np.ndarray) -> float:
    """media(previsto) / media(real) nas semanas com real ESTRITAMENTE maior que 100 casos.

    Returns:
        A fracao; NaN se o grupo nao tiver nenhuma semana com real > 100 (acontece em jan/2026,
        que nao entra na tabela; `formatar_fracao_do_pico` recusa NaN).
    """
    semanas_de_pico = valores_reais > LIMIAR_DE_PICO_EM_CASOS
    if not semanas_de_pico.any():
        return float("nan")
    media_real_no_pico = float(np.mean(valores_reais[semanas_de_pico]))
    media_prevista_no_pico = float(np.mean(valores_previstos[semanas_de_pico]))
    return media_prevista_no_pico / media_real_no_pico


def calcular_metricas_do_grupo(
    valores_reais: np.ndarray,
    valores_previstos: np.ndarray,
    limiar_do_alarme: float,
) -> MetricasDoGrupo:
    """Todas as metricas de um modelo em um grupo de semanas-alvo.

    Alerta: semana com real > L. Detectado: Alerta com previsto > L. Falso: real <= L com
    previsto > L (comparacoes estritas, como no alarme certificado).

    Args:
        valores_reais: Casos confirmados observados nas semanas do grupo.
        valores_previstos: Previsoes do modelo, pareadas por posicao com os reais.
        limiar_do_alarme: L, em casos por semana.

    Returns:
        `MetricasDoGrupo` preenchido.

    Raises:
        ValueError: Se os tamanhos diferirem ou o grupo for vazio.
    """
    if valores_reais.shape != valores_previstos.shape or valores_reais.ndim != 1:
        raise ValueError("Reais e previstos devem ser 1-D e do mesmo tamanho.")
    if len(valores_reais) == 0:
        raise ValueError("Grupo vazio.")

    real_acima_do_limiar = valores_reais > limiar_do_alarme
    previsto_acima_do_limiar = valores_previstos > limiar_do_alarme
    alertas_detectados = real_acima_do_limiar & previsto_acima_do_limiar
    alarmes_falsos = (~real_acima_do_limiar) & previsto_acima_do_limiar

    return MetricasDoGrupo(
        n_de_semanas=len(valores_reais),
        mae=calcular_mae(valores_reais, valores_previstos),
        r2=calcular_r2_dentro_do_grupo(valores_reais, valores_previstos),
        fracao_do_pico=calcular_fracao_do_pico(valores_reais, valores_previstos),
        semanas_de_alerta=int(real_acima_do_limiar.sum()),
        alertas_detectados=int(alertas_detectados.sum()),
        alarmes_falsos=int(alarmes_falsos.sum()),
    )


def calcular_metricas_por_horizonte_e_temporada(
    previsoes: pd.DataFrame,
    limiar_do_alarme: float,
) -> dict[ChaveDaLinha, ParDeMetricas]:
    """Metricas do composto e da regua para cada horizonte da tabela e cada temporada da janela.

    Inclui a temporada fora da tabela (jan/2026) so para a conferencia do alarme.

    Args:
        previsoes: Saida de `preparar_previsoes_com_a_regua`.
        limiar_do_alarme: L, em casos por semana.

    Returns:
        Dicionario (horizonte, temporada) -> `ParDeMetricas`.

    Raises:
        ValueError: Se algum grupo for vazio ou a temporada de jan/2026 nao tiver 5 semanas.
    """
    metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas] = {}
    for horizonte in HORIZONTES_DA_TABELA:
        do_horizonte = previsoes.loc[previsoes[COLUNA_DO_HORIZONTE] == horizonte]
        for temporada in TEMPORADAS_DA_JANELA:
            da_temporada = do_horizonte.loc[do_horizonte[COLUNA_DA_TEMPORADA] == temporada]
            valores_reais = da_temporada[COLUNA_DO_REAL].to_numpy(dtype=float)
            previsto_do_composto = da_temporada[COLUNA_DO_PREVISTO_DO_COMPOSTO].to_numpy(dtype=float)
            previsto_da_regua = da_temporada[COLUNA_DO_PREVISTO_DA_REGUA].to_numpy(dtype=float)

            metricas_do_composto = calcular_metricas_do_grupo(valores_reais, previsto_do_composto, limiar_do_alarme)
            metricas_da_regua = calcular_metricas_do_grupo(valores_reais, previsto_da_regua, limiar_do_alarme)
            chave = ChaveDaLinha(horizonte=horizonte, temporada=temporada)
            metricas_por_linha[chave] = ParDeMetricas(composto=metricas_do_composto, regua=metricas_da_regua)

        chave_de_jan_2026 = ChaveDaLinha(horizonte=horizonte, temporada=TEMPORADA_FORA_DA_TABELA)
        semanas_de_jan_2026 = metricas_por_linha[chave_de_jan_2026].composto.n_de_semanas
        if semanas_de_jan_2026 != SEMANAS_DA_TEMPORADA_FORA_DA_TABELA:
            raise ValueError(
                f"h={horizonte}: {semanas_de_jan_2026} semanas-alvo em 2026; a legenda diz "
                f"{SEMANAS_DA_TEMPORADA_FORA_DA_TABELA}."
            )
    return metricas_por_linha


# ==============================================================================================
# Arredondamento e conferencias
# ==============================================================================================
def arredondar_para_inteiro(valor: float) -> int:
    """Arredonda para o inteiro mais proximo (o mesmo valor impresso na tabela e conferido nas ancoras)."""
    return int(round(valor))


def arredondar_com_casas(valor: float, casas: int) -> float:
    """Arredonda para `casas` casas decimais; normaliza -0,0 para 0,0."""
    valor_arredondado = round(valor, casas)
    return valor_arredondado + 0.0


def conferir_ancoras_das_linhas(metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas]) -> None:
    """Para se alguma linha da tabela divergir das ancoras, na primeira divergencia.

    Raises:
        KeyError: Se faltar a linha de uma ancora.
        ValueError: Na primeira ancora que divergir, com o valor medido e o esperado.
    """
    divergencias: list[str] = []
    for ancora in ANCORAS_DAS_LINHAS:
        chave = ChaveDaLinha(horizonte=ancora.horizonte, temporada=ancora.temporada)
        par = metricas_por_linha[chave]
        composto = par.composto
        regua = par.regua
        rotulo = f"h={ancora.horizonte} {ancora.temporada}"

        medidos_e_esperados = [
            ("MAE composto", arredondar_para_inteiro(composto.mae), ancora.mae_composto),
            ("MAE regua", arredondar_para_inteiro(regua.mae), ancora.mae_regua),
            ("R2 composto", arredondar_com_casas(composto.r2, 2), ancora.r2_composto),
            ("R2 regua", arredondar_com_casas(regua.r2, 2), ancora.r2_regua),
            (
                "fracao do pico composto (%)",
                arredondar_para_inteiro(100.0 * composto.fracao_do_pico),
                ancora.fracao_do_pico_composto_em_pct,
            ),
            (
                "fracao do pico regua (%)",
                arredondar_para_inteiro(100.0 * regua.fracao_do_pico),
                ancora.fracao_do_pico_regua_em_pct,
            ),
            ("alertas detectados composto", composto.alertas_detectados, ancora.alertas_detectados_composto),
            ("alertas detectados regua", regua.alertas_detectados, ancora.alertas_detectados_regua),
            ("semanas de Alerta (composto)", composto.semanas_de_alerta, ancora.semanas_de_alerta),
            ("semanas de Alerta (regua)", regua.semanas_de_alerta, ancora.semanas_de_alerta),
        ]
        if ancora.n_de_semanas is not None:
            medidos_e_esperados.append(("n (composto)", composto.n_de_semanas, ancora.n_de_semanas))
            medidos_e_esperados.append(("n (regua)", regua.n_de_semanas, ancora.n_de_semanas))

        for nome_da_medida, valor_medido, valor_esperado in medidos_e_esperados:
            if valor_medido != valor_esperado:
                divergencias.append(f"{rotulo} {nome_da_medida}: medido {valor_medido}, esperado {valor_esperado}")

    if divergencias:
        texto_das_divergencias = "\n  ".join(divergencias)
        raise ValueError(f"Ancoras divergentes ({len(divergencias)}):\n  {texto_das_divergencias}")
    LOGGER.info("Ancoras conferidas: %d linhas (horizonte x temporada), todas iguais.", len(ANCORAS_DAS_LINHAS))


def somar_alarme_da_janela(
    metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas],
    horizonte: int,
    modelo: str,
) -> dict[str, int]:
    """Soma as contagens de alarme de 2024 + 2025 + jan/2026 para um horizonte e um modelo.

    Args:
        metricas_por_linha: Saida de `calcular_metricas_por_horizonte_e_temporada`.
        horizonte: Horizonte em semanas.
        modelo: "composto" ou "regua".

    Returns:
        Dicionario com `n`, `semanas_de_surto`, `VP`, `FN` e `FP` da janela inteira.

    Raises:
        ValueError: Se `modelo` for desconhecido.
    """
    if modelo not in ("composto", "regua"):
        raise ValueError(f"Modelo desconhecido: {modelo!r}")

    total_de_semanas = 0
    total_de_alertas = 0
    total_detectados = 0
    total_de_falsos = 0
    for temporada in TEMPORADAS_DA_JANELA:
        chave = ChaveDaLinha(horizonte=horizonte, temporada=temporada)
        par = metricas_por_linha[chave]
        if modelo == "composto":
            metricas = par.composto
        else:
            metricas = par.regua
        total_de_semanas += metricas.n_de_semanas
        total_de_alertas += metricas.semanas_de_alerta
        total_detectados += metricas.alertas_detectados
        total_de_falsos += metricas.alarmes_falsos

    return {
        "n": total_de_semanas,
        "semanas_de_surto": total_de_alertas,
        "VP": total_detectados,
        "FN": total_de_alertas - total_detectados,
        "FP": total_de_falsos,
    }


def conferir_alarme_contra_arquivos_certificados(
    metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas],
    alarme_certificado: pd.DataFrame,
    limiar_do_alarme: float,
) -> None:
    """A soma 2024 + 2025 + jan/2026 tem de reproduzir os totais certificados da janela inteira.

    Compara n, semanas de Alerta, VP, FN e FP do composto (`composto_N13`) e da regua sazonal em
    h = 1, 4, 8 e 12, no limiar L (as linhas do limiar 421 dos arquivos de regua nao entram).

    Raises:
        ValueError: Se faltar linha certificada, houver mais de uma, ou algum total divergir.
    """
    busca_por_modelo = (
        ("composto", NOME_DO_BRACO_DO_COMPOSTO_NO_ALARME),
        ("regua", NOME_DO_BRACO_DA_REGUA_NO_ALARME),
    )
    divergencias: list[str] = []
    linhas_conferidas = 0
    for horizonte in HORIZONTES_DA_CONFERENCIA_DO_ALARME:
        for modelo, nome_do_braco in busca_por_modelo:
            e_o_braco = alarme_certificado["braco"] == nome_do_braco
            e_o_horizonte = alarme_certificado["h"] == horizonte
            no_limiar_l = (alarme_certificado["limiar"] - limiar_do_alarme).abs() < TOLERANCIA_DO_LIMIAR_ENTRE_ARQUIVOS
            linhas_certificadas = alarme_certificado.loc[e_o_braco & e_o_horizonte & no_limiar_l]
            if len(linhas_certificadas) != 1:
                raise ValueError(
                    f"Alarme certificado: {len(linhas_certificadas)} linhas para {nome_do_braco}, h={horizonte}, "
                    f"L={limiar_do_alarme:.4f}; esperado 1."
                )
            linha_certificada = linhas_certificadas.iloc[0]
            totais_medidos = somar_alarme_da_janela(metricas_por_linha, horizonte, modelo)

            for nome_da_contagem, valor_medido in totais_medidos.items():
                valor_certificado = int(linha_certificada[nome_da_contagem])
                if valor_medido != valor_certificado:
                    divergencias.append(
                        f"{nome_do_braco} h={horizonte} {nome_da_contagem}: soma das temporadas {valor_medido}, "
                        f"certificado {valor_certificado}"
                    )
            linhas_conferidas += 1

    if divergencias:
        texto_das_divergencias = "\n  ".join(divergencias)
        raise ValueError(f"Alarme divergente do certificado ({len(divergencias)}):\n  {texto_das_divergencias}")
    LOGGER.info(
        "Alarme conferido: soma de 2024 + 2025 + jan/2026 == certificado (n, Alertas, VP, FN, FP) em %d linhas "
        "(composto e regua x h=1/4/8/12).",
        linhas_conferidas,
    )


# ==============================================================================================
# Formatacao em LaTeX (pura)
# ==============================================================================================
def formatar_decimal_br(valor: float, casas: int) -> str:
    """Numero com virgula decimal; negativo vira `$-$` (sinal tipografico de menos no LaTeX)."""
    valor_arredondado = arredondar_com_casas(valor, casas)
    texto_do_modulo = f"{abs(valor_arredondado):.{casas}f}".replace(".", ",")
    if valor_arredondado < 0.0:
        return f"$-${texto_do_modulo}"
    return texto_do_modulo


def formatar_mae(metricas: MetricasDoGrupo) -> str:
    """MAE em casos por semana, inteiro."""
    return str(arredondar_para_inteiro(metricas.mae))


def formatar_r2(metricas: MetricasDoGrupo) -> str:
    """R2 com 2 casas e virgula decimal."""
    return formatar_decimal_br(metricas.r2, 2)


def formatar_fracao_do_pico(metricas: MetricasDoGrupo) -> str:
    """Fracao do pico em % inteiro, com `\\%` do LaTeX.

    Raises:
        ValueError: Se a fracao for NaN (grupo sem semana de pico), que nao pode ir para a tabela.
    """
    if np.isnan(metricas.fracao_do_pico):
        raise ValueError("Fracao do pico indefinida (sem semana com mais de 100 casos) em linha da tabela.")
    fracao_em_pct = arredondar_para_inteiro(100.0 * metricas.fracao_do_pico)
    return f"{fracao_em_pct}\\%"


def formatar_alarme(metricas: MetricasDoGrupo) -> str:
    """Alertas detectados no formato "x de y" (y = semanas de Alerta da temporada)."""
    return ROTULO_DO_ALARME_X_DE_Y.format(
        detectadas=metricas.alertas_detectados,
        alerta=metricas.semanas_de_alerta,
    )


def juntar_composto_e_regua(texto_do_composto: str, texto_da_regua: str) -> str:
    """Celula da tabela: primeiro o composto, depois a regua sazonal."""
    return texto_do_composto + SEPARADOR_DAS_DUAS_SERIES + texto_da_regua


def montar_linha_da_tabela(horizonte: int, temporada: int, par: ParDeMetricas, e_a_primeira_do_horizonte: bool) -> str:
    """Uma linha do `tabular`: horizonte (so na primeira linha do bloco), temporada, n e as 4 celulas."""
    composto = par.composto
    regua = par.regua
    if composto.n_de_semanas != regua.n_de_semanas:
        raise ValueError(f"h={horizonte} {temporada}: n do composto e da regua diferem.")

    if e_a_primeira_do_horizonte:
        celula_do_horizonte = f"\\multirow{{{len(TEMPORADAS_DA_TABELA)}}}{{*}}{{{horizonte}}}"
    else:
        celula_do_horizonte = ""

    celulas = [
        celula_do_horizonte,
        str(temporada),
        str(composto.n_de_semanas),
        juntar_composto_e_regua(formatar_mae(composto), formatar_mae(regua)),
        juntar_composto_e_regua(formatar_r2(composto), formatar_r2(regua)),
        juntar_composto_e_regua(formatar_fracao_do_pico(composto), formatar_fracao_do_pico(regua)),
        juntar_composto_e_regua(formatar_alarme(composto), formatar_alarme(regua)),
    ]
    return " & ".join(celulas) + " \\\\"


def montar_corpo_da_tabela(metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas]) -> str:
    """Linhas do `tabular`, um bloco por horizonte, separados por `\\addlinespace`."""
    linhas: list[str] = []
    for posicao_do_horizonte, horizonte in enumerate(HORIZONTES_DA_TABELA):
        if posicao_do_horizonte > 0:
            linhas.append("\\addlinespace")
        for posicao_da_temporada, temporada in enumerate(TEMPORADAS_DA_TABELA):
            chave = ChaveDaLinha(horizonte=horizonte, temporada=temporada)
            e_a_primeira_do_horizonte = posicao_da_temporada == 0
            linhas.append(montar_linha_da_tabela(horizonte, temporada, metricas_por_linha[chave], e_a_primeira_do_horizonte))
    return "\n".join(linhas)


def montar_texto_latex(metricas_por_linha: dict[ChaveDaLinha, ParDeMetricas]) -> str:
    """Texto completo do `.tex`: comentario de origem e o ambiente `table` (sem \\section)."""
    corpo_da_tabela = montar_corpo_da_tabela(metricas_por_linha)
    return rf"""% Tabela suplementar: abertura por temporada (composto x regua sazonal, 2024 e 2025).
% GERADA POR SCRIPT em {DATA_DA_GERACAO}: {CAMINHO_DO_SCRIPT_PARA_O_COMENTARIO}. Nao editar a mao; rodar o script de novo.
% Analise feita depois da avaliacao e nao pre-declarada (aprovada pelo Vinicius em 17/10/2026).
% Entradas: resultados/ciencia/E3_composto/previsoes.csv (N = 13), dados/tabela_final.csv (sha256 conferido).
\begin{{table}}[!htbp]
\centering
\footnotesize
\caption{{Abertura por temporada, feita depois da avaliação e não pré-declarada: composto e régua sazonal em 2024 e
2025, nas semanas-alvo de cada ano. $R^2$ calculado dentro de cada temporada; fração do pico: média das previsões
$\div$ média dos casos nas semanas com mais de 100 casos; alarme: semanas de Alerta (casos acima de $L = 447$)
reconhecidas. As 5 semanas-alvo de janeiro de 2026 ficam fora da abertura.}}
\label{{tab:s_temporadas}}
\setlength{{\tabcolsep}}{{4pt}}
\resizebox{{\linewidth}}{{!}}{{%
\begin{{tabular}}{{clccccc}}
\toprule
Horizonte & Temporada & $n$ & \multicolumn{{4}}{{c}}{{Composto / régua sazonal}} \\
\cmidrule(l){{4-7}}
(semanas) & & & MAE & $R^2$ & Fração do pico & Alarme \\
\midrule
{corpo_da_tabela}
\bottomrule
\end{{tabular}}%
}}
\end{{table}}
"""


# ==============================================================================================
# Escrita (I/O)
# ==============================================================================================
def gravar_texto(texto: str, caminho: Path) -> None:
    """Grava o `.tex` em UTF-8 (a pasta de destino precisa existir; reescrever e idempotente).

    Raises:
        FileNotFoundError: Se a pasta de destino nao existir.
    """
    if not caminho.parent.is_dir():
        raise FileNotFoundError(f"Pasta de saida ausente: {caminho.parent}")
    caminho.write_text(texto, encoding="utf-8")
    LOGGER.info("Gravado %s (%d caracteres).", caminho, len(texto))


# ==============================================================================================
# Orquestracao
# ==============================================================================================
def main() -> None:
    """Le as entradas certificadas, confere ancoras e arquivos de alarme, e grava a tabela."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    conferir_hash_da_tabela_final(ARQUIVO_DA_TABELA_FINAL, ARQUIVO_DO_HASH_DA_TABELA_FINAL)
    previsoes_do_composto = ler_previsoes_do_composto(ARQUIVO_DAS_PREVISOES_DO_COMPOSTO)
    casos_por_semana = ler_casos_por_semana(ARQUIVO_DA_TABELA_FINAL)
    limiar_do_alarme = ler_limiar_do_alarme(ARQUIVO_DA_RAZAO_DO_ALARME)
    caminhos_do_alarme = (
        ARQUIVO_DO_ALARME_DO_COMPOSTO,
        ARQUIVO_DO_ALARME_DAS_REGUAS,
        ARQUIVO_DO_ALARME_EM_H12,
    )
    alarme_certificado = ler_alarme_certificado(caminhos_do_alarme)

    conferir_real_contra_a_tabela(previsoes_do_composto, casos_por_semana)
    previsoes = preparar_previsoes_com_a_regua(previsoes_do_composto, casos_por_semana)
    metricas_por_linha = calcular_metricas_por_horizonte_e_temporada(previsoes, limiar_do_alarme)

    conferir_ancoras_das_linhas(metricas_por_linha)
    conferir_alarme_contra_arquivos_certificados(metricas_por_linha, alarme_certificado, limiar_do_alarme)

    texto_latex = montar_texto_latex(metricas_por_linha)
    gravar_texto(texto_latex, ARQUIVO_DE_SAIDA)
    print(texto_latex)


if __name__ == "__main__":
    main()
