"""Gera a Figura S2 do material suplementar: desempenho por temporada, de 1 a 12 semanas.

O que mostra: tres paineis lado a lado (uma linha, tres colunas), com o horizonte (1 a 12 semanas)
no eixo x, abrindo as 102 semanas-alvo da avaliacao (07/01/2024 a 01/02/2026) por TEMPORADA
(ano da `data_alvo`: 2024 e 2025; as 5 semanas de janeiro de 2026 ficam fora), para o modelo
composto (E3, N = 13) e para a regua sazonal:
    (a) R2, calculado dentro de cada temporada;
    (b) fracao do pico (%) = media(previsto) / media(real) nas semanas com real > 100 casos;
    (c) alarme (%) = sensibilidade = semanas com real > L e previsto > L, sobre as semanas com
        real > L (semanas de Alerta); L = valor exato de `E5_alarme/razao.json` (447,0654).

Decisao do Vinicius em 17/10/2026: esse conteudo fica SO no suplementar (nao vai para o texto do
artigo), no formato de um slide dele, acrescentando a regua sazonal. Como a tabela suplementar
`gerar_tabela_temporadas.py`, e uma analise feita DEPOIS da avaliacao e nao pre-declarada: nao
altera nenhum numero do artigo.

Forma: cor = temporada (2024 laranja #D9632B, 2025 azul #2A78D6, par seguro para daltonismo);
estilo = modelo (composto: linha cheia com marcador; regua sazonal: tracejada, sem marcador).
Legenda unica acima dos paineis. Estilo visual da Figura 3 (layout "opcao A").

Reaproveita, SEM copiar, as funcoes ja conferidas de `gerar_tabela_temporadas.py` (hash da tabela,
leitura do composto N = 13, regua = casos de `data_alvo` - 52 semanas, L, e as metricas de um
grupo de semanas). Esse script nao e alterado.

Entradas (SOMENTE LEITURA):
    - `resultados/ciencia/E3_composto/previsoes.csv` (so N == 13);
    - `dados/tabela_final.csv` (sha256 conferido contra `dados/tabela_final.sha256`);
    - `resultados/ciencia/E5_alarme/razao.json` (L exato).
Saidas:
    - `figuras/figuraS2_temporadas.pdf` (vetorial, sem data de criacao) e `.png` (200 dpi);
    - copia dos dois em `entregas/artigo/figuras/`.
Ancoras numericas (composto / regua) em `ANCORAS_DA_FIGURA`; se divergirem, o script PARA e nao
grava nada. Nenhum modelo e treinado.

Rodar, de dentro de projeto_final/:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_figuraS2_temporadas.py
"""

import dataclasses
import logging
import shutil
import sys
from pathlib import Path
from typing import NamedTuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (o backend precisa ser escolhido antes)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import Formatter  # noqa: E402

PASTA_DAS_FIGURAS = Path(__file__).resolve().parent
# O script e rodado pelo caminho do arquivo; sem isto `gerar_tabela_temporadas` nao seria achado.
sys.path.insert(0, str(PASTA_DAS_FIGURAS))

import gerar_tabela_temporadas as tabela  # noqa: E402

LOGGER = logging.getLogger("figuraS2_temporadas")

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
NOME_DA_FIGURA = "figuraS2_temporadas"
PASTA_DE_ENTREGA_DAS_FIGURAS = tabela.PASTA_DA_PESQUISA / "entregas" / "artigo" / "figuras"

# ----------------------------------------------------------------------------------------------
# Definicoes de negocio
# ----------------------------------------------------------------------------------------------
HORIZONTES = tuple(range(1, 13))
TEMPORADAS = tabela.TEMPORADAS_DA_TABELA
NOMES_DOS_MODELOS = ("composto", "regua")

COLUNA_DO_R2 = "r2"
COLUNA_DA_FRACAO_DO_PICO = "fracao_do_pico_em_pct"
COLUNA_DO_ALARME = "alarme_em_pct"


class ChaveDaSerie(NamedTuple):
    """Identifica uma linha do grafico: um modelo em uma temporada."""

    modelo: str
    temporada: int


class ChaveDoPonto(NamedTuple):
    """Identifica um ponto: um modelo, uma temporada e um horizonte."""

    modelo: str
    temporada: int
    horizonte: int


@dataclasses.dataclass(frozen=True)
class AncoraDaFigura:
    """Valores esperados (calculados antes) de um horizonte em uma temporada, ja arredondados.

    Attributes:
        horizonte: Horizonte em semanas.
        temporada: Ano da `data_alvo`.
        r2_composto: R2 do composto, 2 casas.
        r2_regua: R2 da regua, 2 casas.
        fracao_do_pico_composto_em_pct: Fracao do pico do composto, em % inteiro.
        fracao_do_pico_regua_em_pct: Fracao do pico da regua, em % inteiro.
        alertas_detectados_composto: Semanas de Alerta reconhecidas pelo composto.
        alertas_detectados_regua: Semanas de Alerta reconhecidas pela regua.
        semanas_de_alerta: Semanas de Alerta da temporada (iguais nos dois modelos).
    """

    horizonte: int
    temporada: int
    r2_composto: float
    r2_regua: float
    fracao_do_pico_composto_em_pct: int
    fracao_do_pico_regua_em_pct: int
    alertas_detectados_composto: int
    alertas_detectados_regua: int
    semanas_de_alerta: int


ANCORAS_DA_FIGURA = (
    AncoraDaFigura(1, 2024, 0.85, 0.27, 76, 25, 9, 4, 10),
    AncoraDaFigura(1, 2025, 0.91, 0.79, 94, 75, 14, 13, 14),
    AncoraDaFigura(4, 2024, 0.56, 0.28, 54, 31, 12, 7, 13),
    AncoraDaFigura(4, 2025, 0.75, 0.79, 78, 75, 14, 13, 14),
    AncoraDaFigura(12, 2024, 0.01, 0.24, 23, 34, 1, 8, 14),
    AncoraDaFigura(12, 2025, 0.73, 0.79, 61, 75, 11, 13, 14),
)

# ----------------------------------------------------------------------------------------------
# Estilo (mesmo da Figura 3, "opcao A"; cor = temporada, estilo = modelo)
# ----------------------------------------------------------------------------------------------
COR_DE_2024 = "#D9632B"
COR_DE_2025 = "#2A78D6"
CORES_DAS_TEMPORADAS = {2024: COR_DE_2024, 2025: COR_DE_2025}
COR_DO_TEXTO = "#3A3936"
COR_DA_GRADE = "#E6E5E1"
COR_DA_SUPERFICIE = "#FFFFFF"

LARGURA_DA_FIGURA_EM_POLEGADAS = 5.4
ALTURA_DA_FIGURA_EM_POLEGADAS = 2.3
RESOLUCAO_DO_PNG_EM_DPI = 200

FAMILIA_DA_FONTE = "serif"
FONTE_SERIFADA = "STIXGeneral"
FONTE_DAS_FORMULAS = "stix"
TAMANHO_BASE_DA_FONTE = 8.0
TAMANHO_DO_TITULO = 7.5
TAMANHO_DOS_TICKS = 7.5
TAMANHO_DA_LEGENDA = 7.5

ESPESSURA_DAS_BORDAS_E_MARCAS = 0.6
COMPRIMENTO_DAS_MARCAS = 2.5
ESPESSURA_DA_GRADE = 0.6
AFASTAMENTO_DO_TITULO = 4.0

LIMITE_ESQUERDO_DO_EIXO_X = 0.5
LIMITE_DIREITO_DO_EIXO_X = 12.5
HORIZONTES_COM_MARCA_NO_EIXO_X = (1, 4, 8, 12)
ROTULO_DO_EIXO_X = "horizonte (semanas)"

# Camadas (zorder): grade < regua < composto.
CAMADA_DA_GRADE = 1
CAMADA_DA_REGUA = 2
CAMADA_DO_COMPOSTO = 3


@dataclasses.dataclass(frozen=True)
class EstiloDoModelo:
    """Aparencia de um modelo (a mesma nas duas temporadas; a cor vem da temporada)."""

    rotulo_na_legenda: str
    estilo_da_linha: str | tuple[float, tuple[float, ...]]
    marcador: str | None
    largura_da_linha: float
    tamanho_do_marcador: float
    camada: int


ESTILOS_DOS_MODELOS = {
    "composto": EstiloDoModelo(
        rotulo_na_legenda="Composto",
        estilo_da_linha="-",
        marcador="o",
        largura_da_linha=1.5,
        tamanho_do_marcador=3.0,
        camada=CAMADA_DO_COMPOSTO,
    ),
    "regua": EstiloDoModelo(
        rotulo_na_legenda="Régua",
        estilo_da_linha=(0, (4.0, 2.0)),
        marcador=None,
        largura_da_linha=1.2,
        tamanho_do_marcador=0.0,
        camada=CAMADA_DA_REGUA,
    ),
}

# Ordem da legenda: composto e regua de 2024, depois composto e regua de 2025.
ORDEM_DA_LEGENDA = (
    ChaveDaSerie("composto", 2024),
    ChaveDaSerie("regua", 2024),
    ChaveDaSerie("composto", 2025),
    ChaveDaSerie("regua", 2025),
)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDoPainel:
    """O que cada painel mostra e como o eixo y e desenhado.

    Attributes:
        coluna_da_metrica: Coluna da tabela de metricas desenhada no painel.
        titulo: Titulo do painel, alinhado a esquerda (aceita formula do mathtext).
        limite_inferior_do_eixo_y: Limite de baixo do eixo y.
        limite_superior_do_eixo_y: Limite de cima do eixo y.
        posicoes_dos_ticks_y: Valores marcados no eixo y (e onde ficam as linhas de grade).
        casas_decimais_dos_ticks: Casas decimais dos rotulos do eixo y.
    """

    coluna_da_metrica: str
    titulo: str
    limite_inferior_do_eixo_y: float
    limite_superior_do_eixo_y: float
    posicoes_dos_ticks_y: tuple[float, ...]
    casas_decimais_dos_ticks: int


PAINEIS = (
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DO_R2,
        titulo="(a) $R^2$",
        limite_inferior_do_eixo_y=-0.1,
        limite_superior_do_eixo_y=1.0,
        posicoes_dos_ticks_y=(0.0, 0.25, 0.5, 0.75, 1.0),
        casas_decimais_dos_ticks=2,
    ),
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DA_FRACAO_DO_PICO,
        titulo="(b) Fração do pico (%)",
        limite_inferior_do_eixo_y=0.0,
        limite_superior_do_eixo_y=100.0,
        posicoes_dos_ticks_y=(0.0, 25.0, 50.0, 75.0, 100.0),
        casas_decimais_dos_ticks=0,
    ),
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DO_ALARME,
        # Quebra de linha: o titulo inteiro nao cabe na largura de um painel.
        titulo="(c) Alarme (% das\nsemanas de Alerta)",
        limite_inferior_do_eixo_y=0.0,
        limite_superior_do_eixo_y=100.0,
        posicoes_dos_ticks_y=(0.0, 25.0, 50.0, 75.0, 100.0),
        casas_decimais_dos_ticks=0,
    ),
)


# ==============================================================================================
# Metricas (puras, sobre as funcoes ja conferidas da tabela suplementar)
# ==============================================================================================
def calcular_metricas_de_todos_os_pontos(previsoes: pd.DataFrame, limiar_do_alarme: float) -> dict[ChaveDoPonto, tabela.MetricasDoGrupo]:
    """Metricas de cada modelo, temporada (2024, 2025) e horizonte (1 a 12).

    Args:
        previsoes: Saida de `preparar_previsoes_com_a_regua` (com `previsto_regua` e `temporada`).
        limiar_do_alarme: L, em casos por semana.

    Returns:
        Dicionario (modelo, temporada, horizonte) -> `MetricasDoGrupo`.

    Raises:
        ValueError: Se algum grupo for vazio, os tamanhos divergirem ou o R2 for indefinido (vindo
            de `calcular_metricas_do_grupo`).
    """
    metricas_por_ponto: dict[ChaveDoPonto, tabela.MetricasDoGrupo] = {}
    for horizonte in HORIZONTES:
        do_horizonte = previsoes.loc[previsoes[tabela.COLUNA_DO_HORIZONTE] == horizonte]
        for temporada in TEMPORADAS:
            da_temporada = do_horizonte.loc[do_horizonte[tabela.COLUNA_DA_TEMPORADA] == temporada]
            valores_reais = da_temporada[tabela.COLUNA_DO_REAL].to_numpy(dtype=float)
            previsto_do_composto = da_temporada[tabela.COLUNA_DO_PREVISTO_DO_COMPOSTO].to_numpy(dtype=float)
            previsto_da_regua = da_temporada[tabela.COLUNA_DO_PREVISTO_DA_REGUA].to_numpy(dtype=float)

            chave_do_composto = ChaveDoPonto("composto", temporada, horizonte)
            chave_da_regua = ChaveDoPonto("regua", temporada, horizonte)
            metricas_por_ponto[chave_do_composto] = tabela.calcular_metricas_do_grupo(
                valores_reais, previsto_do_composto, limiar_do_alarme
            )
            metricas_por_ponto[chave_da_regua] = tabela.calcular_metricas_do_grupo(
                valores_reais, previsto_da_regua, limiar_do_alarme
            )
    return metricas_por_ponto


def calcular_sensibilidade_do_alarme_em_pct(metricas: tabela.MetricasDoGrupo) -> float:
    """Alertas detectados sobre semanas de Alerta, em %.

    Raises:
        ValueError: Se o grupo nao tiver nenhuma semana de Alerta (a razao ficaria indefinida).
    """
    if metricas.semanas_de_alerta == 0:
        raise ValueError("Sensibilidade indefinida: temporada sem semana de Alerta.")
    return 100.0 * metricas.alertas_detectados / metricas.semanas_de_alerta


def montar_tabela_de_pontos(metricas_por_ponto: dict[ChaveDoPonto, tabela.MetricasDoGrupo]) -> pd.DataFrame:
    """Uma linha por (modelo, temporada, horizonte), com as tres metricas desenhadas.

    Raises:
        ValueError: Se a fracao do pico for NaN (temporada sem semana com mais de 100 casos).
    """
    linhas: list[dict[str, object]] = []
    for chave, metricas in metricas_por_ponto.items():
        if np.isnan(metricas.fracao_do_pico):
            raise ValueError(f"Fracao do pico indefinida em {chave}.")
        linhas.append(
            {
                "modelo": chave.modelo,
                "temporada": chave.temporada,
                "h": chave.horizonte,
                COLUNA_DO_R2: metricas.r2,
                COLUNA_DA_FRACAO_DO_PICO: 100.0 * metricas.fracao_do_pico,
                COLUNA_DO_ALARME: calcular_sensibilidade_do_alarme_em_pct(metricas),
            }
        )
    pontos = pd.DataFrame(linhas)
    return pontos.sort_values(["modelo", "temporada", "h"]).reset_index(drop=True)


# ==============================================================================================
# Ancoras e validacoes
# ==============================================================================================
def conferir_ancoras(metricas_por_ponto: dict[ChaveDoPonto, tabela.MetricasDoGrupo]) -> None:
    """Para se alguma ancora (R2, fracao do pico, alarme em h = 1, 4 e 12) divergir.

    Raises:
        ValueError: Lista todas as divergencias, com o valor medido e o esperado.
    """
    divergencias: list[str] = []
    for ancora in ANCORAS_DA_FIGURA:
        composto = metricas_por_ponto[ChaveDoPonto("composto", ancora.temporada, ancora.horizonte)]
        regua = metricas_por_ponto[ChaveDoPonto("regua", ancora.temporada, ancora.horizonte)]
        rotulo = f"h={ancora.horizonte} {ancora.temporada}"
        medidos_e_esperados = [
            ("R2 composto", tabela.arredondar_com_casas(composto.r2, 2), ancora.r2_composto),
            ("R2 regua", tabela.arredondar_com_casas(regua.r2, 2), ancora.r2_regua),
            (
                "fracao do pico composto (%)",
                tabela.arredondar_para_inteiro(100.0 * composto.fracao_do_pico),
                ancora.fracao_do_pico_composto_em_pct,
            ),
            (
                "fracao do pico regua (%)",
                tabela.arredondar_para_inteiro(100.0 * regua.fracao_do_pico),
                ancora.fracao_do_pico_regua_em_pct,
            ),
            ("alertas detectados composto", composto.alertas_detectados, ancora.alertas_detectados_composto),
            ("alertas detectados regua", regua.alertas_detectados, ancora.alertas_detectados_regua),
            ("semanas de Alerta composto", composto.semanas_de_alerta, ancora.semanas_de_alerta),
            ("semanas de Alerta regua", regua.semanas_de_alerta, ancora.semanas_de_alerta),
        ]
        for nome_da_medida, valor_medido, valor_esperado in medidos_e_esperados:
            if valor_medido != valor_esperado:
                divergencias.append(f"{rotulo} {nome_da_medida}: medido {valor_medido}, esperado {valor_esperado}")

    if divergencias:
        texto_das_divergencias = "\n  ".join(divergencias)
        raise ValueError(f"Ancoras divergentes ({len(divergencias)}):\n  {texto_das_divergencias}")
    LOGGER.info("Ancoras conferidas: %d (horizonte x temporada), todas iguais.", len(ANCORAS_DA_FIGURA))


def validar_cobertura_dos_12_horizontes(previsoes: pd.DataFrame) -> None:
    """Confere 12 horizontes x 102 semanas-alvo distintas na janela (a leitura da tabela so valida 6).

    Raises:
        ValueError: Se faltar horizonte ou algum tiver numero de semanas diferente de 102 ou repetidas.
    """
    horizontes_encontrados = tuple(sorted(pd.unique(previsoes[tabela.COLUNA_DO_HORIZONTE])))
    if horizontes_encontrados != HORIZONTES:
        raise ValueError(f"Horizontes {horizontes_encontrados}, esperado {HORIZONTES}.")
    for horizonte in HORIZONTES:
        do_horizonte = previsoes.loc[previsoes[tabela.COLUNA_DO_HORIZONTE] == horizonte]
        total_de_linhas = len(do_horizonte)
        semanas_distintas = do_horizonte[tabela.COLUNA_DA_DATA_ALVO].nunique()
        if total_de_linhas != tabela.SEMANAS_DA_JANELA_POR_HORIZONTE or semanas_distintas != total_de_linhas:
            raise ValueError(f"h={horizonte}: {total_de_linhas} linhas e {semanas_distintas} semanas distintas.")


def validar_limites_dos_eixos(pontos: pd.DataFrame) -> None:
    """Confere que nenhum ponto cai fora do eixo y fixo de cada painel (nada pode ser cortado).

    Raises:
        ValueError: Se algum valor desenhado ficar fora dos limites do painel.
    """
    for painel in PAINEIS:
        valores_desenhados = pontos[painel.coluna_da_metrica].to_numpy(dtype=float)
        menor_valor = float(np.min(valores_desenhados))
        maior_valor = float(np.max(valores_desenhados))
        fora_dos_limites = (
            menor_valor < painel.limite_inferior_do_eixo_y or maior_valor > painel.limite_superior_do_eixo_y
        )
        LOGGER.info("Painel %s: valores em [%.4g, %.4g].", painel.coluna_da_metrica, menor_valor, maior_valor)
        if fora_dos_limites:
            raise ValueError(
                f"Painel {painel.titulo!r}: valores [{menor_valor:.4g}, {maior_valor:.4g}] fora do eixo "
                f"[{painel.limite_inferior_do_eixo_y}, {painel.limite_superior_do_eixo_y}]."
            )


# ==============================================================================================
# Figura
# ==============================================================================================
class FormatadorDeTicksComVirgula(Formatter):
    """Rotulos de tick em portugues: virgula decimal, numero fixo de casas."""

    def __init__(self, casas_decimais: int) -> None:
        self.casas_decimais = casas_decimais

    def __call__(self, x: float, pos: int | None = None) -> str:
        texto_com_ponto = f"{x:.{self.casas_decimais}f}"
        return texto_com_ponto.replace(".", ",")


def configurar_estilo_global() -> None:
    """Fonte serifada (STIX), bordas e marcas finas, PDF com fontes embutidas e fundo explicito."""
    parametros = {
        "font.family": FAMILIA_DA_FONTE,
        "font.serif": [FONTE_SERIFADA],
        "mathtext.fontset": FONTE_DAS_FORMULAS,
        "font.size": TAMANHO_BASE_DA_FONTE,
        "axes.titlesize": TAMANHO_DO_TITULO,
        "axes.labelsize": TAMANHO_BASE_DA_FONTE,
        "xtick.labelsize": TAMANHO_DOS_TICKS,
        "ytick.labelsize": TAMANHO_DOS_TICKS,
        "axes.edgecolor": COR_DO_TEXTO,
        "axes.linewidth": ESPESSURA_DAS_BORDAS_E_MARCAS,
        "xtick.color": COR_DO_TEXTO,
        "ytick.color": COR_DO_TEXTO,
        "xtick.major.width": ESPESSURA_DAS_BORDAS_E_MARCAS,
        "ytick.major.width": ESPESSURA_DAS_BORDAS_E_MARCAS,
        "xtick.major.size": COMPRIMENTO_DAS_MARCAS,
        "ytick.major.size": COMPRIMENTO_DAS_MARCAS,
        "axes.formatter.use_locale": False,
        "pdf.fonttype": 42,
        "figure.facecolor": COR_DA_SUPERFICIE,
        "axes.facecolor": COR_DA_SUPERFICIE,
        "savefig.facecolor": COR_DA_SUPERFICIE,
    }
    plt.rcParams.update(parametros)


def desenhar_serie(eixo: Axes, horizontes: np.ndarray, valores: np.ndarray, chave: ChaveDaSerie) -> None:
    """Desenha uma linha: cor da temporada, estilo do modelo (marcador preenchido com a cor)."""
    estilo = ESTILOS_DOS_MODELOS[chave.modelo]
    cor = CORES_DAS_TEMPORADAS[chave.temporada]
    eixo.plot(
        horizontes,
        valores,
        color=cor,
        linestyle=estilo.estilo_da_linha,
        linewidth=estilo.largura_da_linha,
        marker=estilo.marcador,
        markersize=estilo.tamanho_do_marcador,
        markeredgecolor=cor,
        markerfacecolor=cor,
        zorder=estilo.camada,
        # Marcadores em 0% e 100% ficariam cortados pela borda do eixo; os valores não mudam.
        clip_on=False,
    )


def configurar_eixos_do_painel(eixo: Axes, painel: ConfiguracaoDoPainel) -> None:
    """Eixos e grade: grade so no eixo y, sem bordas de cima e da direita, x = 1, 4, 8, 12."""
    eixo.set_xlim(LIMITE_ESQUERDO_DO_EIXO_X, LIMITE_DIREITO_DO_EIXO_X)
    eixo.set_xticks(list(HORIZONTES_COM_MARCA_NO_EIXO_X))
    eixo.set_xlabel(ROTULO_DO_EIXO_X, color=COR_DO_TEXTO)

    eixo.set_ylim(painel.limite_inferior_do_eixo_y, painel.limite_superior_do_eixo_y)
    eixo.set_yticks(list(painel.posicoes_dos_ticks_y))
    eixo.yaxis.set_major_formatter(FormatadorDeTicksComVirgula(painel.casas_decimais_dos_ticks))

    eixo.set_title(painel.titulo, loc="left", color=COR_DO_TEXTO, pad=AFASTAMENTO_DO_TITULO)
    eixo.grid(axis="y", color=COR_DA_GRADE, linewidth=ESPESSURA_DA_GRADE, zorder=CAMADA_DA_GRADE)
    eixo.grid(axis="x", visible=False)
    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)


def montar_legenda(figura: Figure) -> None:
    """Legenda unica, acima dos paineis, numa linha: Composto 2024, Regua 2024, Composto 2025, Regua 2025."""
    entradas: list[Line2D] = []
    for chave in ORDEM_DA_LEGENDA:
        estilo = ESTILOS_DOS_MODELOS[chave.modelo]
        cor = CORES_DAS_TEMPORADAS[chave.temporada]
        entradas.append(
            Line2D(
                [],
                [],
                color=cor,
                linestyle=estilo.estilo_da_linha,
                linewidth=estilo.largura_da_linha,
                marker=estilo.marcador,
                markersize=estilo.tamanho_do_marcador,
                markeredgecolor=cor,
                markerfacecolor=cor,
                label=f"{estilo.rotulo_na_legenda} {chave.temporada}",
            )
        )
    legenda = figura.legend(
        handles=entradas,
        loc="outside upper center",
        ncols=len(entradas),
        frameon=False,
        fontsize=TAMANHO_DA_LEGENDA,
        handlelength=2.6,
        columnspacing=1.6,
    )
    for texto in legenda.get_texts():
        texto.set_color(COR_DO_TEXTO)


def montar_figura(pontos: pd.DataFrame) -> Figure:
    """Monta a figura de tres paineis lado a lado (R2, fracao do pico, alarme).

    Args:
        pontos: Saida de `montar_tabela_de_pontos`.

    Returns:
        A figura pronta para gravar.
    """
    figura = plt.figure(
        figsize=(LARGURA_DA_FIGURA_EM_POLEGADAS, ALTURA_DA_FIGURA_EM_POLEGADAS),
        layout="constrained",
    )
    eixos = figura.subplots(nrows=1, ncols=len(PAINEIS))

    horizontes = np.array(HORIZONTES)
    for eixo, painel in zip(eixos, PAINEIS):
        configurar_eixos_do_painel(eixo, painel)
        for chave in ORDEM_DA_LEGENDA:
            do_modelo = pontos["modelo"] == chave.modelo
            da_temporada = pontos["temporada"] == chave.temporada
            da_serie = pontos.loc[do_modelo & da_temporada].sort_values("h")
            valores_desenhados = da_serie[painel.coluna_da_metrica].to_numpy(dtype=float)
            desenhar_serie(eixo, horizontes, valores_desenhados, chave)

    montar_legenda(figura)
    return figura


# ==============================================================================================
# Saidas (I/O)
# ==============================================================================================
def gravar_figura(figura: Figure) -> tuple[Path, Path]:
    """Grava PDF (vetorial, sem data de criacao) e PNG (200 dpi) em `figuras/`; devolve os caminhos."""
    caminho_do_pdf = PASTA_DAS_FIGURAS / f"{NOME_DA_FIGURA}.pdf"
    caminho_do_png = PASTA_DAS_FIGURAS / f"{NOME_DA_FIGURA}.png"
    figura.savefig(caminho_do_pdf, metadata={"CreationDate": None})
    figura.savefig(caminho_do_png, dpi=RESOLUCAO_DO_PNG_EM_DPI, metadata={"Software": None})
    LOGGER.info("Gravados %s e %s.", caminho_do_pdf.name, caminho_do_png.name)
    return caminho_do_pdf, caminho_do_png


def copiar_para_a_pasta_do_artigo(caminhos: tuple[Path, ...]) -> None:
    """Copia os arquivos para `entregas/artigo/figuras/` (a pasta precisa existir).

    Raises:
        FileNotFoundError: Se a pasta de destino nao existir.
    """
    if not PASTA_DE_ENTREGA_DAS_FIGURAS.is_dir():
        raise FileNotFoundError(f"Pasta de entrega ausente: {PASTA_DE_ENTREGA_DAS_FIGURAS}")
    for caminho_de_origem in caminhos:
        caminho_de_destino = PASTA_DE_ENTREGA_DAS_FIGURAS / caminho_de_origem.name
        shutil.copyfile(caminho_de_origem, caminho_de_destino)
        LOGGER.info("Copiado para %s", caminho_de_destino)


# ==============================================================================================
# Orquestracao
# ==============================================================================================
def principal() -> None:
    """Confere hash e entradas, calcula as metricas, confere as ancoras, desenha e grava a figura."""
    # O log e configurado so neste logger: no raiz, o fontTools (usado ao embutir fontes no PDF)
    # despejaria centenas de linhas de depuracao.
    manipulador_de_log = logging.StreamHandler(sys.stdout)
    manipulador_de_log.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(manipulador_de_log)
    LOGGER.setLevel(logging.INFO)
    tabela.LOGGER.addHandler(manipulador_de_log)
    tabela.LOGGER.setLevel(logging.INFO)
    configurar_estilo_global()

    tabela.conferir_hash_da_tabela_final(tabela.ARQUIVO_DA_TABELA_FINAL, tabela.ARQUIVO_DO_HASH_DA_TABELA_FINAL)
    previsoes_do_composto = tabela.ler_previsoes_do_composto(tabela.ARQUIVO_DAS_PREVISOES_DO_COMPOSTO)
    casos_por_semana = tabela.ler_casos_por_semana(tabela.ARQUIVO_DA_TABELA_FINAL)
    limiar_do_alarme = tabela.ler_limiar_do_alarme(tabela.ARQUIVO_DA_RAZAO_DO_ALARME)

    validar_cobertura_dos_12_horizontes(previsoes_do_composto)
    tabela.conferir_real_contra_a_tabela(previsoes_do_composto, casos_por_semana)
    previsoes = tabela.preparar_previsoes_com_a_regua(previsoes_do_composto, casos_por_semana)

    metricas_por_ponto = calcular_metricas_de_todos_os_pontos(previsoes, limiar_do_alarme)
    conferir_ancoras(metricas_por_ponto)

    pontos = montar_tabela_de_pontos(metricas_por_ponto)
    validar_limites_dos_eixos(pontos)

    figura = montar_figura(pontos)
    caminhos_gravados = gravar_figura(figura)
    plt.close(figura)
    copiar_para_a_pasta_do_artigo(caminhos_gravados)


if __name__ == "__main__":
    principal()
