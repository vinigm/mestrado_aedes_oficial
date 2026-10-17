"""Gera a NOVA Figura 3 do artigo, centrada no MODELO COMPOSTO.

O que mostra: tres paineis lado a lado (uma linha, tres colunas), todos com o mesmo eixo de
horizonte (1 a 12 semanas), comparando o modelo composto com a regua sazonal nas MESMAS 102
semanas-alvo por horizonte (07/01/2024 a 01/02/2026):
    (a) erro absoluto medio (MAE, casos por semana);
    (b) R2 por horizonte;
    (c) fracao do pico alcancada, em %.
Layout "opcao A", aprovado pelo Vinicius em 17/10/2026 (so a estetica mudou; dados, calculos,
ancoras e validacoes sao os mesmos da versao empilhada, guardada em
`figuras/_antes_2026-10-17_gerar_figura3_composto.py.txt`).

Modelo composto (experimento E3, N = 13): em cada semana usa a folha 5 ou a folha 20, conforme o
erro das ultimas 13 semanas. As folhas 5 e 20 sozinhas e a persistencia NAO entram nesta figura.

Fracao do pico alcancada (a antiga "captura do pico" do seminario, definida em
`analises/2026-09-13_metrica_de_alarme/README.md`):
    media(previsto) / media(real), so nas semanas-alvo com real > 100 casos.
Antes de aplicar ao composto, o script REPRODUZ quatro numeros do slide do seminario com as
previsoes das folhas 5 e 20 (`resultados/referencia/previsoes.csv`); se nao baterem, aborta.

Forma: uma serie = uma cor em todos os paineis (composto: azul, linha cheia com marcador; regua
sazonal: cinza escuro, tracejada, sem marcador); nunca dois eixos y; sem caixa de legenda (rotulos
diretos no painel (a)); grade horizontal clara. Em cada painel, uma faixa cinza clara cobre os
horizontes em que a regua e melhor que o composto, do cruzamento (menos 0,5) ate o fim do eixo
(calculado dos dados: o menor h tal que a regua e melhor em todos os horizontes de h ate 12; se
nao houver, nenhuma faixa e desenhada).

Entradas (somente leitura, certificadas):
    - `resultados/ciencia/E3_composto/previsoes.csv` e `resumo.csv`;
    - `resultados/referencia/previsoes.csv` e `metricas.csv`;
    - `dados/tabela_final.csv` (hash conferido, com o corte de maturidade), de onde a funcao
      certificada `aedes.metricas.montar_previsoes_das_reguas` tira a regua sazonal.
Saidas (novas, nao sobrescrevem nenhum arquivo anterior):
    - `resultados/ciencia/E3_composto/metricas_descritivas.csv`;
    - `figuras/figura3_composto_por_horizonte.pdf` (vetorial) e `.png` (200 dpi).
Nenhum modelo e treinado.

Rodar, de dentro de projeto_final/:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_figura3_composto.py
"""

import dataclasses
import logging
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
from matplotlib.ticker import Formatter  # noqa: E402

PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
# O script e rodado pelo caminho do arquivo; sem isto o pacote `aedes` nao seria encontrado.
sys.path.insert(0, str(PASTA_DO_PACOTE))

from aedes.configuracao import CONFIGURACAO_AVALIACAO, CONFIGURACAO_DADOS  # noqa: E402
from aedes.dados import aplicar_corte_de_maturidade, montar_tabela_a_partir_dos_bytes  # noqa: E402
from aedes.metricas import (  # noqa: E402
    NOME_DO_BRACO_REGUA_SAZONAL,
    erro_absoluto_medio,
    montar_previsoes_das_reguas,
    r_quadrado,
    recortar_janela_de_avaliacao,
)

LOGGER = logging.getLogger("figura3_composto")

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
ARQUIVO_DA_TABELA = PASTA_DO_PACOTE / "dados" / "tabela_final.csv"
PASTA_DO_COMPOSTO = PASTA_DO_PACOTE / "resultados" / "ciencia" / "E3_composto"
ARQUIVO_DAS_PREVISOES_DO_COMPOSTO = PASTA_DO_COMPOSTO / "previsoes.csv"
ARQUIVO_DO_RESUMO_DO_COMPOSTO = PASTA_DO_COMPOSTO / "resumo.csv"
ARQUIVO_DAS_METRICAS_DESCRITIVAS = PASTA_DO_COMPOSTO / "metricas_descritivas.csv"
PASTA_DA_REFERENCIA = PASTA_DO_PACOTE / "resultados" / "referencia"
ARQUIVO_DAS_PREVISOES_DA_REFERENCIA = PASTA_DA_REFERENCIA / "previsoes.csv"
ARQUIVO_DAS_METRICAS_DA_REFERENCIA = PASTA_DA_REFERENCIA / "metricas.csv"
PASTA_DAS_FIGURAS = PASTA_DO_PACOTE / "figuras"
NOME_DA_FIGURA = "figura3_composto_por_horizonte"

# ----------------------------------------------------------------------------------------------
# Definicoes de negocio
# ----------------------------------------------------------------------------------------------
NUMERO_DE_MODELOS_DO_COMPOSTO = 13
HORIZONTES = tuple(range(1, 13))
SEMANAS_POR_HORIZONTE_NA_JANELA = 102
# Semana de pico = semana-alvo com mais de 100 casos confirmados (convencao do projeto).
LIMIAR_DE_PICO_EM_CASOS = 100.0

NOME_DO_MODELO_COMPOSTO = "composto"
NOME_DA_REGUA_SAZONAL = NOME_DO_BRACO_REGUA_SAZONAL

NOME_DO_BRACO_FOLHA_5 = "referencia"
NOME_DO_BRACO_FOLHA_20 = "HistGB_folha20_M1"

COLUNA_DO_HORIZONTE = "h"
COLUNA_DA_DATA_ALVO = "data_alvo"
COLUNA_DA_DATA_DE_ORIGEM = "data_origem"
COLUNA_DO_REAL = "real"
COLUNA_DO_PREVISTO = "previsto"
COLUNA_DO_NUMERO_DE_MODELOS = "N"
COLUNA_DO_MODELO = "modelo"
COLUNA_DO_N = "n"
COLUNA_DO_MAE = "mae"
COLUNA_DO_R2 = "r2"
COLUNA_DA_FRACAO_DO_PICO = "fracao_pico"
COLUNA_DAS_SEMANAS_DE_PICO = "n_semanas_acima_de_100"
COLUNAS_DAS_METRICAS_DESCRITIVAS = (
    COLUNA_DO_HORIZONTE,
    COLUNA_DO_MODELO,
    COLUNA_DO_N,
    COLUNA_DO_MAE,
    COLUNA_DO_R2,
    COLUNA_DA_FRACAO_DO_PICO,
    COLUNA_DAS_SEMANAS_DE_PICO,
)

# ----------------------------------------------------------------------------------------------
# Ancoras numericas (calculadas antes; se divergirem, o script PARA e nao forca nada)
# ----------------------------------------------------------------------------------------------
# MAE do composto (N = 13), arredondado a 2 casas; MAE da regua sazonal, a 3 casas.
ANCORAS_DO_MAE_DO_COMPOSTO = {1: 102.33, 4: 205.73, 8: 233.51, 12: 260.14}
TOLERANCIA_DAS_ANCORAS_DO_COMPOSTO = 0.005
ANCORAS_DO_MAE_DA_REGUA = {1: 202.108, 4: 213.176, 8: 216.167, 12: 217.784}
TOLERANCIA_DAS_ANCORAS_DA_REGUA = 0.0005
# Fracao do pico do slide do seminario (3 casas): (braco, h) -> valor.
ANCORAS_DO_SLIDE_DA_FRACAO_DO_PICO = {
    (NOME_DO_BRACO_FOLHA_5, 1): 0.886,
    (NOME_DO_BRACO_FOLHA_20, 4): 0.706,
    (NOME_DO_BRACO_FOLHA_20, 8): 0.510,
    (NOME_DO_BRACO_FOLHA_20, 12): 0.504,
}
TOLERANCIA_DO_SLIDE = 0.0005
# Comparacoes com arquivos certificados: mesma conta, so ponto flutuante.
TOLERANCIA_ENTRE_ARQUIVOS = 1e-9

# ----------------------------------------------------------------------------------------------
# Estilo (layout "opcao A", aprovado em 17/10/2026)
# ----------------------------------------------------------------------------------------------
COR_DO_COMPOSTO = "#2A78D6"
COR_DA_REGUA = "#4A4A48"
COR_DO_TEXTO = "#3A3936"
COR_DA_GRADE = "#E6E5E1"
COR_DA_FAIXA_DE_CRUZAMENTO = "#F1F0EC"
COR_DA_SUPERFICIE = "#FFFFFF"

LARGURA_DA_FIGURA_EM_POLEGADAS = 5.4
ALTURA_DA_FIGURA_EM_POLEGADAS = 2.15
RESOLUCAO_DO_PNG_EM_DPI = 200

FAMILIA_DA_FONTE = "serif"
FONTE_SERIFADA = "STIXGeneral"
FONTE_DAS_FORMULAS = "stix"
TAMANHO_BASE_DA_FONTE = 8.0
TAMANHO_DO_TITULO = 8.5
TAMANHO_DOS_TICKS = 7.5
TAMANHO_DO_ROTULO_DIRETO = 7.5

ESPESSURA_DAS_BORDAS_E_MARCAS = 0.6
COMPRIMENTO_DAS_MARCAS = 2.5
ESPESSURA_DA_GRADE = 0.6
AFASTAMENTO_DO_TITULO = 4.0

LIMITE_ESQUERDO_DO_EIXO_X = 0.5
LIMITE_DIREITO_DO_EIXO_X = 12.5
HORIZONTES_COM_MARCA_NO_EIXO_X = (1, 4, 8, 12)
# A faixa começa meia semana antes do horizonte de cruzamento, para cobrir o ponto inteiro.
MEIA_SEMANA_ANTES_DO_CRUZAMENTO = 0.5
ROTULO_DO_EIXO_X = "horizonte (semanas)"

# Camadas (zorder): faixa < grade < regua < composto.
CAMADA_DA_FAIXA = 0
CAMADA_DA_GRADE = 1
CAMADA_DA_REGUA = 2
CAMADA_DO_COMPOSTO = 3

# Rotulos diretos (so no painel (a), o do MAE): posicao horizontal em unidades de h, e deslocamento
# vertical, em casos por semana, a partir do ultimo ponto da propria serie (posicao calculada dos
# dados, nunca fixa). O do composto fica acima do ultimo ponto; o da regua, abaixo do fim da linha.
POSICAO_HORIZONTAL_DOS_ROTULOS_DIRETOS = 12.3
DESLOCAMENTO_DO_ROTULO_DO_COMPOSTO_EM_CASOS = 14.0
DESLOCAMENTO_DO_ROTULO_DA_REGUA_EM_CASOS = -30.0


@dataclasses.dataclass(frozen=True)
class EstiloDaSerie:
    """Aparencia de uma serie; a mesma em todos os paineis (uma serie = uma cor).

    Attributes:
        nome_do_modelo: Valor da coluna `modelo` desta serie.
        rotulo_direto: Texto escrito ao lado da linha, no painel (a).
        deslocamento_do_rotulo_em_casos: Soma ao valor do ultimo ponto (em casos por semana)
            para dar a altura do rotulo direto.
        cor: Cor da linha e do marcador.
        estilo_da_linha: Estilo do matplotlib ("-" ou tupla de tracejado).
        marcador: Marcador do matplotlib; None se a serie nao tem marcador.
        largura_da_linha: Espessura da linha.
        tamanho_do_marcador: Tamanho do marcador.
        camada: `zorder` da linha.
    """

    nome_do_modelo: str
    rotulo_direto: str
    deslocamento_do_rotulo_em_casos: float
    cor: str
    estilo_da_linha: str | tuple[float, tuple[float, ...]]
    marcador: str | None
    largura_da_linha: float
    tamanho_do_marcador: float
    camada: int


ESTILO_DO_COMPOSTO = EstiloDaSerie(
    nome_do_modelo=NOME_DO_MODELO_COMPOSTO,
    rotulo_direto="composto",
    deslocamento_do_rotulo_em_casos=DESLOCAMENTO_DO_ROTULO_DO_COMPOSTO_EM_CASOS,
    cor=COR_DO_COMPOSTO,
    estilo_da_linha="-",
    marcador="o",
    largura_da_linha=1.5,
    tamanho_do_marcador=3.2,
    camada=CAMADA_DO_COMPOSTO,
)
ESTILO_DA_REGUA = EstiloDaSerie(
    nome_do_modelo=NOME_DA_REGUA_SAZONAL,
    rotulo_direto="régua sazonal",
    deslocamento_do_rotulo_em_casos=DESLOCAMENTO_DO_ROTULO_DA_REGUA_EM_CASOS,
    cor=COR_DA_REGUA,
    estilo_da_linha=(0, (4.0, 2.0)),
    marcador=None,
    largura_da_linha=1.2,
    tamanho_do_marcador=0.0,
    camada=CAMADA_DA_REGUA,
)
ESTILOS_DAS_SERIES = (ESTILO_DO_COMPOSTO, ESTILO_DA_REGUA)


@dataclasses.dataclass(frozen=True)
class ConfiguracaoDoPainel:
    """O que cada painel mostra e como o eixo y e desenhado.

    Attributes:
        coluna_da_metrica: Coluna de `metricas_descritivas.csv` desenhada no painel.
        titulo: Titulo do painel, alinhado a esquerda (aceita formula do mathtext).
        fator_de_escala: Multiplica a metrica antes de desenhar (100 para mostrar em %).
        maior_e_melhor: True se um valor maior e melhor (R2, fracao do pico); False para o MAE.
        limite_inferior_do_eixo_y: Limite de baixo do eixo y (na unidade desenhada).
        limite_superior_do_eixo_y: Limite de cima do eixo y (na unidade desenhada).
        posicoes_dos_ticks_y: Valores marcados no eixo y (e onde ficam as linhas de grade).
        casas_decimais_dos_ticks: Casas decimais dos rotulos do eixo y.
        tem_rotulos_diretos: True no painel que traz os nomes das series ao lado das linhas.
    """

    coluna_da_metrica: str
    titulo: str
    fator_de_escala: float
    maior_e_melhor: bool
    limite_inferior_do_eixo_y: float
    limite_superior_do_eixo_y: float
    posicoes_dos_ticks_y: tuple[float, ...]
    casas_decimais_dos_ticks: int
    tem_rotulos_diretos: bool


PAINEIS = (
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DO_MAE,
        titulo="(a) MAE (casos/semana)",
        fator_de_escala=1.0,
        maior_e_melhor=False,
        limite_inferior_do_eixo_y=0.0,
        limite_superior_do_eixo_y=300.0,
        posicoes_dos_ticks_y=(0.0, 100.0, 200.0, 300.0),
        casas_decimais_dos_ticks=0,
        tem_rotulos_diretos=True,
    ),
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DO_R2,
        titulo="(b) $R^2$",
        fator_de_escala=1.0,
        maior_e_melhor=True,
        limite_inferior_do_eixo_y=0.3,
        limite_superior_do_eixo_y=1.0,
        posicoes_dos_ticks_y=(0.4, 0.6, 0.8, 1.0),
        casas_decimais_dos_ticks=1,
        tem_rotulos_diretos=False,
    ),
    ConfiguracaoDoPainel(
        coluna_da_metrica=COLUNA_DA_FRACAO_DO_PICO,
        titulo="(c) Fração do pico (%)",
        fator_de_escala=100.0,
        maior_e_melhor=True,
        limite_inferior_do_eixo_y=0.0,
        limite_superior_do_eixo_y=100.0,
        posicoes_dos_ticks_y=(0.0, 25.0, 50.0, 75.0, 100.0),
        casas_decimais_dos_ticks=0,
        tem_rotulos_diretos=False,
    ),
)


class FracaoDoPico(NamedTuple):
    """Resultado da fracao do pico em um conjunto de semanas."""

    fracao: float
    semanas_de_pico: int


# ==============================================================================================
# Leitura (I/O)
# ==============================================================================================
def ler_previsoes(caminho: Path) -> pd.DataFrame:
    """Le um CSV de previsoes certificado, com datas em formato de data e floats sem perda.

    Args:
        caminho: Arquivo `previsoes.csv`.

    Returns:
        DataFrame como veio do arquivo; `data_origem` e `data_alvo` viram datas.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    previsoes = pd.read_csv(
        caminho,
        float_precision="round_trip",
        parse_dates=[COLUNA_DA_DATA_DE_ORIGEM, COLUNA_DA_DATA_ALVO],
    )
    LOGGER.info("Lido %s: %d linhas.", caminho.name, len(previsoes))
    return previsoes


def ler_tabela_de_metricas(caminho: Path) -> pd.DataFrame:
    """Le um CSV de metricas (`metricas.csv` ou `resumo.csv`) com floats sem perda.

    Raises:
        FileNotFoundError: Se o arquivo nao existir.
    """
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de entrada ausente: {caminho}")
    metricas = pd.read_csv(caminho, float_precision="round_trip")
    LOGGER.info("Lido %s: %d linhas.", caminho.name, len(metricas))
    return metricas


def carregar_casos_por_data() -> pd.Series:
    """Serie semanal de casos, com o corte de maturidade, indexada pela data da semana.

    Usa as funcoes certificadas de `aedes.dados`: confere o hash da tabela, valida o esquema e
    apaga os casos das ultimas semanas (ainda nao confirmadas). E a mesma serie da qual a regua
    sazonal foi calculada em `resultados/referencia/metricas.csv`.

    Raises:
        FileNotFoundError: Se a tabela nao existir.
        ValueError: Se o hash ou o esquema da tabela divergirem.
    """
    if not ARQUIVO_DA_TABELA.exists():
        raise FileNotFoundError(f"Tabela de dados ausente: {ARQUIVO_DA_TABELA}")
    conteudo_em_bytes = ARQUIVO_DA_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    tabela_cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)

    datas_das_semanas = pd.DatetimeIndex(tabela_cortada[CONFIGURACAO_DADOS.coluna_de_data])
    casos_das_semanas = tabela_cortada[CONFIGURACAO_DADOS.coluna_de_casos].to_numpy(dtype=float)
    casos_por_data = pd.Series(casos_das_semanas, index=datas_das_semanas)
    LOGGER.info("Serie de casos cortada pela maturidade: %d semanas.", len(casos_por_data))
    return casos_por_data


# ==============================================================================================
# Preparo das previsoes (puro)
# ==============================================================================================
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


def validar_cobertura_da_janela(previsoes: pd.DataFrame, nome_da_tabela: str) -> None:
    """Confere 12 horizontes x 102 semanas-alvo distintas, sem ausente, na janela de avaliacao.

    Raises:
        ValueError: Se faltar horizonte, se algum horizonte nao tiver 102 semanas distintas
            ou se `real` ou `previsto` tiver ausente ou infinito.
    """
    horizontes_encontrados = tuple(sorted(pd.unique(previsoes[COLUNA_DO_HORIZONTE])))
    if horizontes_encontrados != HORIZONTES:
        raise ValueError(f"{nome_da_tabela}: horizontes {horizontes_encontrados}, esperado {HORIZONTES}.")

    for horizonte in HORIZONTES:
        do_horizonte = previsoes.loc[previsoes[COLUNA_DO_HORIZONTE] == horizonte]
        semanas_distintas = do_horizonte[COLUNA_DA_DATA_ALVO].nunique()
        total_de_linhas = len(do_horizonte)
        if total_de_linhas != SEMANAS_POR_HORIZONTE_NA_JANELA or semanas_distintas != total_de_linhas:
            raise ValueError(
                f"{nome_da_tabela}: h={horizonte} tem {total_de_linhas} linhas e {semanas_distintas} "
                f"semanas distintas; esperado {SEMANAS_POR_HORIZONTE_NA_JANELA} e sem repeticao."
            )

    valores_reais = previsoes[COLUNA_DO_REAL].to_numpy(dtype=float)
    valores_previstos = previsoes[COLUNA_DO_PREVISTO].to_numpy(dtype=float)
    if not (np.isfinite(valores_reais).all() and np.isfinite(valores_previstos).all()):
        raise ValueError(f"{nome_da_tabela}: `real` ou `previsto` com ausente ou infinito.")


def selecionar_previsoes_do_composto(previsoes_do_e3: pd.DataFrame) -> pd.DataFrame:
    """Previsoes do composto com N = 13, so na janela de avaliacao (07/01/2024 a 01/02/2026).

    O arquivo do E3 traz tres variantes (N = 8, 13 e 26) e todas as origens do walk-forward; a
    janela, por `data_alvo`, e a mesma das metricas certificadas.

    Args:
        previsoes_do_e3: Conteudo de `E3_composto/previsoes.csv`.

    Returns:
        DataFrame com `h`, `data_alvo`, `real`, `previsto`, ordenado por `h` e `data_alvo`
        (1.224 linhas: 12 horizontes x 102 semanas).

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se a cobertura da janela nao for 12 x 102.
    """
    colunas_obrigatorias = (
        COLUNA_DO_NUMERO_DE_MODELOS,
        COLUNA_DO_HORIZONTE,
        COLUNA_DA_DATA_ALVO,
        COLUNA_DO_REAL,
        COLUNA_DO_PREVISTO,
    )
    validar_colunas(previsoes_do_e3, colunas_obrigatorias, "E3_composto/previsoes.csv")

    do_composto_escolhido = previsoes_do_e3[COLUNA_DO_NUMERO_DE_MODELOS] == NUMERO_DE_MODELOS_DO_COMPOSTO
    previsoes_do_composto = previsoes_do_e3.loc[do_composto_escolhido]
    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes_do_composto, CONFIGURACAO_AVALIACAO)

    colunas_mantidas = [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    previsoes_ordenadas = previsoes_na_janela[colunas_mantidas].sort_values(
        [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO]
    )
    previsoes_ordenadas = previsoes_ordenadas.reset_index(drop=True)
    validar_cobertura_da_janela(previsoes_ordenadas, "composto N=13")
    return previsoes_ordenadas


def selecionar_previsoes_de_um_braco_na_janela(previsoes_da_referencia: pd.DataFrame, nome_do_braco: str) -> pd.DataFrame:
    """Previsoes de uma folha (braco de `referencia/previsoes.csv`) na janela de avaliacao.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se a cobertura da janela nao for 12 x 102.
    """
    colunas_obrigatorias = (
        "braco",
        COLUNA_DO_HORIZONTE,
        COLUNA_DA_DATA_ALVO,
        COLUNA_DO_REAL,
        COLUNA_DO_PREVISTO,
    )
    validar_colunas(previsoes_da_referencia, colunas_obrigatorias, "referencia/previsoes.csv")

    do_braco = previsoes_da_referencia["braco"] == nome_do_braco
    previsoes_do_braco = previsoes_da_referencia.loc[do_braco]
    previsoes_na_janela = recortar_janela_de_avaliacao(previsoes_do_braco, CONFIGURACAO_AVALIACAO)
    previsoes_ordenadas = previsoes_na_janela.sort_values([COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO])
    previsoes_ordenadas = previsoes_ordenadas.reset_index(drop=True)
    validar_cobertura_da_janela(previsoes_ordenadas, f"braco {nome_do_braco}")
    return previsoes_ordenadas


def montar_previsoes_da_regua_sazonal(
    previsoes_do_composto: pd.DataFrame,
    casos_por_data: pd.Series,
) -> pd.DataFrame:
    """Regua sazonal na MESMA grade (h, data_alvo) do composto, pela funcao certificada.

    A regua prediz os casos de `data_alvo - 52 semanas`. Alem de montar, confere que a regua cobre
    as 102 semanas de cada horizonte (nenhuma semana saiu por falta de ano anterior) e que o
    `real` da regua coincide com o `real` do composto em cada semana.

    Args:
        previsoes_do_composto: Saida de `selecionar_previsoes_do_composto`.
        casos_por_data: Serie de casos cortada pela maturidade.

    Returns:
        DataFrame com `h`, `data_alvo`, `real`, `previsto`, ordenado por `h` e `data_alvo`.

    Raises:
        ValueError: Se a cobertura nao for 12 x 102 ou o `real` divergir do composto.
    """
    previsoes_das_reguas = montar_previsoes_das_reguas(previsoes_do_composto, casos_por_data)
    e_regua_sazonal = previsoes_das_reguas["braco"] == NOME_DA_REGUA_SAZONAL
    previsoes_da_regua = previsoes_das_reguas.loc[e_regua_sazonal]

    colunas_mantidas = [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO, COLUNA_DO_REAL, COLUNA_DO_PREVISTO]
    previsoes_ordenadas = previsoes_da_regua[colunas_mantidas].sort_values(
        [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO]
    )
    previsoes_ordenadas = previsoes_ordenadas.reset_index(drop=True)
    validar_cobertura_da_janela(previsoes_ordenadas, "regua sazonal")

    mesma_grade_e_mesmo_real = previsoes_do_composto[
        [COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO, COLUNA_DO_REAL]
    ].equals(previsoes_ordenadas[[COLUNA_DO_HORIZONTE, COLUNA_DA_DATA_ALVO, COLUNA_DO_REAL]])
    if not mesma_grade_e_mesmo_real:
        raise ValueError("A grade (h, data_alvo) ou o `real` da regua diverge do composto.")
    return previsoes_ordenadas


# ==============================================================================================
# Metricas (puras)
# ==============================================================================================
def calcular_fracao_do_pico(
    valores_reais: pd.Series | np.ndarray,
    valores_previstos: pd.Series | np.ndarray,
    limiar_de_pico: float = LIMIAR_DE_PICO_EM_CASOS,
) -> FracaoDoPico:
    """Fracao do pico alcancada: media(previsto) / media(real) nas semanas com real > limiar.

    Mede se o modelo acerta o TAMANHO da epidemia nas semanas de pico: 1,0 = media prevista igual
    a media real; 0,5 = o modelo previu, em media, metade do que aconteceu. Nao e metrica de
    alarme (ver `analises/2026-09-13_metrica_de_alarme/README.md`).

    Args:
        valores_reais: Casos confirmados observados.
        valores_previstos: Previsoes pareadas por posicao com os reais.
        limiar_de_pico: Uma semana e de pico se `real` for ESTRITAMENTE maior que isto.

    Returns:
        `FracaoDoPico` com a fracao e a quantidade de semanas de pico. Sem nenhuma semana de pico,
        a fracao e NaN.

    Raises:
        ValueError: Se os tamanhos diferirem ou houver ausente ou infinito.
    """
    reais = np.asarray(valores_reais, dtype=float)
    previstos = np.asarray(valores_previstos, dtype=float)
    if reais.shape != previstos.shape or reais.ndim != 1:
        raise ValueError(f"Reais {reais.shape} e previstos {previstos.shape} devem ser 1-D e do mesmo tamanho.")
    if not (np.isfinite(reais).all() and np.isfinite(previstos).all()):
        raise ValueError("Reais ou previstos com ausente ou infinito.")

    semanas_de_pico = reais > limiar_de_pico
    quantidade_de_semanas_de_pico = int(semanas_de_pico.sum())
    if quantidade_de_semanas_de_pico == 0:
        return FracaoDoPico(fracao=float("nan"), semanas_de_pico=0)

    media_real_no_pico = float(np.mean(reais[semanas_de_pico]))
    media_prevista_no_pico = float(np.mean(previstos[semanas_de_pico]))
    return FracaoDoPico(
        fracao=media_prevista_no_pico / media_real_no_pico,
        semanas_de_pico=quantidade_de_semanas_de_pico,
    )


def calcular_metricas_por_horizonte(previsoes: pd.DataFrame, nome_do_modelo: str) -> pd.DataFrame:
    """MAE, R2 e fracao do pico por horizonte, sobre as linhas recebidas (uma janela ja recortada).

    Args:
        previsoes: DataFrame com `h`, `real` e `previsto`.
        nome_do_modelo: Rotulo gravado na coluna `modelo`.

    Returns:
        DataFrame com as colunas de `COLUNAS_DAS_METRICAS_DESCRITIVAS`, uma linha por horizonte.

    Raises:
        KeyError: Se faltar coluna.
        ValueError: Se houver ausente ou infinito (vindo das funcoes de metrica).
    """
    validar_colunas(previsoes, (COLUNA_DO_HORIZONTE, COLUNA_DO_REAL, COLUNA_DO_PREVISTO), nome_do_modelo)

    linhas_das_metricas: list[dict[str, object]] = []
    for horizonte in sorted(pd.unique(previsoes[COLUNA_DO_HORIZONTE])):
        do_horizonte = previsoes.loc[previsoes[COLUNA_DO_HORIZONTE] == horizonte]
        valores_reais = do_horizonte[COLUNA_DO_REAL]
        valores_previstos = do_horizonte[COLUNA_DO_PREVISTO]
        fracao_do_pico = calcular_fracao_do_pico(valores_reais, valores_previstos)
        linhas_das_metricas.append(
            {
                COLUNA_DO_HORIZONTE: int(horizonte),
                COLUNA_DO_MODELO: nome_do_modelo,
                COLUNA_DO_N: len(do_horizonte),
                COLUNA_DO_MAE: erro_absoluto_medio(valores_reais, valores_previstos),
                COLUNA_DO_R2: r_quadrado(valores_reais, valores_previstos),
                COLUNA_DA_FRACAO_DO_PICO: fracao_do_pico.fracao,
                COLUNA_DAS_SEMANAS_DE_PICO: fracao_do_pico.semanas_de_pico,
            }
        )
    return pd.DataFrame(linhas_das_metricas, columns=list(COLUNAS_DAS_METRICAS_DESCRITIVAS))


def encontrar_horizonte_de_cruzamento(
    horizontes: np.ndarray,
    valores_do_composto: np.ndarray,
    valores_da_regua: np.ndarray,
    maior_e_melhor: bool,
) -> int | None:
    """Horizonte a partir do qual a regua e melhor que o composto, e continua melhor ate o fim.

    Percorre os horizontes do ultimo para o primeiro e para na primeira vez que o composto nao
    perde. O resultado e o primeiro horizonte da sequencia final de horizontes em que a regua
    vence. Empate nao conta como a regua ser melhor.

    Args:
        horizontes: Horizontes em ordem crescente.
        valores_do_composto: Metrica do composto, um valor por horizonte.
        valores_da_regua: Metrica da regua sazonal, um valor por horizonte.
        maior_e_melhor: True se valor maior e melhor (R2, fracao do pico); False para o MAE.

    Returns:
        O horizonte de cruzamento; None se a regua nao vence no ultimo horizonte ou se vence em
        todos (nesse caso nao ha cruzamento: a regua nunca perdeu).

    Raises:
        ValueError: Se os vetores tiverem tamanhos diferentes ou forem vazios.
    """
    if not (len(horizontes) == len(valores_do_composto) == len(valores_da_regua)) or len(horizontes) == 0:
        raise ValueError("Horizontes e metricas devem ter o mesmo tamanho, nao vazio.")

    if maior_e_melhor:
        regua_vence = valores_da_regua > valores_do_composto
    else:
        regua_vence = valores_da_regua < valores_do_composto

    posicao_do_cruzamento = len(horizontes)
    for posicao in range(len(horizontes) - 1, -1, -1):
        if not regua_vence[posicao]:
            break
        posicao_do_cruzamento = posicao

    nenhum_horizonte_da_sequencia_final = posicao_do_cruzamento == len(horizontes)
    regua_vence_em_todos = posicao_do_cruzamento == 0
    if nenhum_horizonte_da_sequencia_final or regua_vence_em_todos:
        return None
    return int(horizontes[posicao_do_cruzamento])


# ==============================================================================================
# Ancoras e conferencias contra os arquivos certificados
# ==============================================================================================
def extrair_serie_da_metrica(metricas: pd.DataFrame, nome_do_modelo: str, coluna_da_metrica: str) -> pd.Series:
    """Metrica de um modelo, indexada por horizonte (h crescente)."""
    do_modelo = metricas.loc[metricas[COLUNA_DO_MODELO] == nome_do_modelo]
    do_modelo = do_modelo.sort_values(COLUNA_DO_HORIZONTE)
    return pd.Series(do_modelo[coluna_da_metrica].to_numpy(), index=do_modelo[COLUNA_DO_HORIZONTE].to_numpy())


def conferir_ancoras_do_mae(metricas: pd.DataFrame) -> None:
    """Para se o MAE do composto ou o da regua divergir das ancoras de h = 1, 4, 8 e 12.

    Raises:
        ValueError: Na primeira ancora que divergir.
    """
    mae_do_composto = extrair_serie_da_metrica(metricas, NOME_DO_MODELO_COMPOSTO, COLUNA_DO_MAE)
    mae_da_regua = extrair_serie_da_metrica(metricas, NOME_DA_REGUA_SAZONAL, COLUNA_DO_MAE)

    for horizonte, valor_esperado in ANCORAS_DO_MAE_DO_COMPOSTO.items():
        valor_medido = float(mae_do_composto.loc[horizonte])
        if abs(valor_medido - valor_esperado) > TOLERANCIA_DAS_ANCORAS_DO_COMPOSTO:
            raise ValueError(f"Ancora do composto h={horizonte}: medido {valor_medido}, esperado {valor_esperado}.")
    for horizonte, valor_esperado in ANCORAS_DO_MAE_DA_REGUA.items():
        valor_medido = float(mae_da_regua.loc[horizonte])
        if abs(valor_medido - valor_esperado) > TOLERANCIA_DAS_ANCORAS_DA_REGUA:
            raise ValueError(f"Ancora da regua h={horizonte}: medido {valor_medido}, esperado {valor_esperado}.")
    LOGGER.info("Ancoras de MAE (composto e regua, h 1/4/8/12) conferidas.")


def conferir_com_arquivos_certificados(
    metricas: pd.DataFrame,
    metricas_da_referencia: pd.DataFrame,
    resumo_do_composto: pd.DataFrame,
) -> None:
    """Compara a regua com `referencia/metricas.csv` e o MAE do composto com `E3_composto/resumo.csv`.

    A regua sazonal (MAE, R2 e n) deve ser identica a certificada; o MAE e o n do composto N = 13
    devem ser identicos ao resumo do E3. Tolerancia: `TOLERANCIA_ENTRE_ARQUIVOS`.

    Raises:
        KeyError: Se faltar coluna ou linha nos arquivos certificados.
        ValueError: Se algum valor divergir.
    """
    validar_colunas(metricas_da_referencia, ("braco", "h", "n", "mae", "r2"), "referencia/metricas.csv")
    validar_colunas(resumo_do_composto, ("N", "h", "n", "mae"), "E3_composto/resumo.csv")

    da_regua = metricas_da_referencia.loc[metricas_da_referencia["braco"] == NOME_DA_REGUA_SAZONAL]
    da_regua = da_regua.sort_values("h").reset_index(drop=True)
    regua_medida = metricas.loc[metricas[COLUNA_DO_MODELO] == NOME_DA_REGUA_SAZONAL]
    regua_medida = regua_medida.sort_values(COLUNA_DO_HORIZONTE).reset_index(drop=True)
    for nome_da_coluna in ("n", "mae", "r2"):
        diferenca_maxima = float(np.max(np.abs(regua_medida[nome_da_coluna] - da_regua[nome_da_coluna])))
        if diferenca_maxima > TOLERANCIA_ENTRE_ARQUIVOS:
            raise ValueError(f"Regua: `{nome_da_coluna}` difere de referencia/metricas.csv em {diferenca_maxima}.")

    do_composto = resumo_do_composto.loc[resumo_do_composto["N"] == NUMERO_DE_MODELOS_DO_COMPOSTO]
    do_composto = do_composto.sort_values("h").reset_index(drop=True)
    composto_medido = metricas.loc[metricas[COLUNA_DO_MODELO] == NOME_DO_MODELO_COMPOSTO]
    composto_medido = composto_medido.sort_values(COLUNA_DO_HORIZONTE).reset_index(drop=True)
    for nome_da_coluna in ("n", "mae"):
        diferenca_maxima = float(np.max(np.abs(composto_medido[nome_da_coluna] - do_composto[nome_da_coluna])))
        if diferenca_maxima > TOLERANCIA_ENTRE_ARQUIVOS:
            raise ValueError(f"Composto: `{nome_da_coluna}` difere de E3_composto/resumo.csv em {diferenca_maxima}.")
    LOGGER.info("Regua e composto identicos aos arquivos certificados (tolerancia %.0e).", TOLERANCIA_ENTRE_ARQUIVOS)


def validar_definicao_da_fracao_do_pico(previsoes_da_referencia: pd.DataFrame) -> None:
    """Reproduz os numeros do slide do seminario com as folhas 5 e 20, antes de usar a definicao.

    O slide mostrou a "captura do pico" da folha 5 em h = 1 (0,886) e da folha 20 em h = 4, 8 e 12
    (0,706, 0,510 e 0,504). A definicao so e usada no composto se reproduzir esses quatro numeros.

    Raises:
        ValueError: Se algum numero do slide nao for reproduzido (tolerancia: arredondamento a
            3 casas, `TOLERANCIA_DO_SLIDE`).
    """
    for (nome_do_braco, horizonte), valor_do_slide in ANCORAS_DO_SLIDE_DA_FRACAO_DO_PICO.items():
        previsoes_do_braco = selecionar_previsoes_de_um_braco_na_janela(previsoes_da_referencia, nome_do_braco)
        do_horizonte = previsoes_do_braco.loc[previsoes_do_braco[COLUNA_DO_HORIZONTE] == horizonte]
        fracao_do_pico = calcular_fracao_do_pico(do_horizonte[COLUNA_DO_REAL], do_horizonte[COLUNA_DO_PREVISTO])
        LOGGER.info(
            "Slide: %s h=%d fracao do pico = %.4f (slide: %.3f; %d semanas de pico).",
            nome_do_braco,
            horizonte,
            fracao_do_pico.fracao,
            valor_do_slide,
            fracao_do_pico.semanas_de_pico,
        )
        if abs(fracao_do_pico.fracao - valor_do_slide) > TOLERANCIA_DO_SLIDE:
            raise ValueError(
                f"Definicao da fracao do pico nao reproduz o slide: {nome_do_braco} h={horizonte} "
                f"deu {fracao_do_pico.fracao:.4f}, slide {valor_do_slide:.3f}."
            )


def validar_limites_dos_eixos(metricas: pd.DataFrame) -> None:
    """Confere que nenhum ponto cai fora do eixo y fixo de cada painel (nada pode ser cortado).

    Raises:
        ValueError: Se algum valor desenhado ficar fora dos limites do painel.
    """
    for painel in PAINEIS:
        valores_desenhados = metricas[painel.coluna_da_metrica].to_numpy(dtype=float) * painel.fator_de_escala
        menor_valor = float(np.min(valores_desenhados))
        maior_valor = float(np.max(valores_desenhados))
        fora_dos_limites = (
            menor_valor < painel.limite_inferior_do_eixo_y or maior_valor > painel.limite_superior_do_eixo_y
        )
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


def desenhar_serie(eixo: Axes, horizontes: np.ndarray, valores: np.ndarray, estilo: EstiloDaSerie) -> None:
    """Desenha uma serie com o estilo fixo do modelo (mesma cor e traco em todos os paineis).

    O marcador, quando existe, e preenchido com a propria cor da linha.
    """
    eixo.plot(
        horizontes,
        valores,
        color=estilo.cor,
        linestyle=estilo.estilo_da_linha,
        linewidth=estilo.largura_da_linha,
        marker=estilo.marcador,
        markersize=estilo.tamanho_do_marcador,
        markeredgecolor=estilo.cor,
        markerfacecolor=estilo.cor,
        zorder=estilo.camada,
    )


def desenhar_faixa_de_cruzamento(eixo: Axes, horizonte_de_cruzamento: int) -> None:
    """Faixa cinza clara, atras das linhas, dos horizontes em que a regua e melhor.

    Cobre de `horizonte_de_cruzamento - 0,5` ate o limite direito do eixo.
    """
    inicio_da_faixa = horizonte_de_cruzamento - MEIA_SEMANA_ANTES_DO_CRUZAMENTO
    eixo.axvspan(
        inicio_da_faixa,
        LIMITE_DIREITO_DO_EIXO_X,
        color=COR_DA_FAIXA_DE_CRUZAMENTO,
        linewidth=0,
        zorder=CAMADA_DA_FAIXA,
    )


def desenhar_rotulos_diretos(eixo: Axes, metricas: pd.DataFrame, painel: ConfiguracaoDoPainel) -> None:
    """Escreve o nome de cada serie ao lado da linha, no lugar de uma caixa de legenda.

    A altura de cada rotulo vem do valor do ultimo horizonte da propria serie (na unidade
    desenhada) mais o deslocamento do estilo; o texto fica alinhado a direita.
    """
    for estilo in ESTILOS_DAS_SERIES:
        serie = extrair_serie_da_metrica(metricas, estilo.nome_do_modelo, painel.coluna_da_metrica)
        valor_do_ultimo_horizonte = float(serie.to_numpy(dtype=float)[-1]) * painel.fator_de_escala
        altura_do_rotulo = valor_do_ultimo_horizonte + estilo.deslocamento_do_rotulo_em_casos
        eixo.text(
            POSICAO_HORIZONTAL_DOS_ROTULOS_DIRETOS,
            altura_do_rotulo,
            estilo.rotulo_direto,
            color=COR_DO_TEXTO,
            ha="right",
            fontsize=TAMANHO_DO_ROTULO_DIRETO,
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


def montar_figura(
    metricas: pd.DataFrame,
    horizontes_de_cruzamento: dict[str, int | None],
) -> Figure:
    """Monta a figura de tres paineis lado a lado (MAE, R2, fracao do pico).

    Args:
        metricas: Saida de `calcular_metricas_por_horizonte` para o composto e a regua.
        horizontes_de_cruzamento: Coluna da metrica -> horizonte de cruzamento (None = sem faixa).

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

        horizonte_de_cruzamento = horizontes_de_cruzamento[painel.coluna_da_metrica]
        if horizonte_de_cruzamento is not None:
            desenhar_faixa_de_cruzamento(eixo, horizonte_de_cruzamento)

        for estilo in ESTILOS_DAS_SERIES:
            serie = extrair_serie_da_metrica(metricas, estilo.nome_do_modelo, painel.coluna_da_metrica)
            valores_desenhados = serie.to_numpy(dtype=float) * painel.fator_de_escala
            desenhar_serie(eixo, horizontes, valores_desenhados, estilo)

        if painel.tem_rotulos_diretos:
            desenhar_rotulos_diretos(eixo, metricas, painel)
    return figura


# ==============================================================================================
# Saidas (I/O)
# ==============================================================================================
def gravar_metricas_descritivas(metricas: pd.DataFrame) -> None:
    """Grava `metricas_descritivas.csv` (floats com precisao total); sobrescreve so este arquivo."""
    metricas.to_csv(ARQUIVO_DAS_METRICAS_DESCRITIVAS, index=False)
    LOGGER.info("Gravado %s (%d linhas).", ARQUIVO_DAS_METRICAS_DESCRITIVAS, len(metricas))


def gravar_figura(figura: Figure) -> None:
    """Grava PDF (vetorial, tamanho final, sem data de criacao) e PNG (200 dpi) da figura."""
    caminho_do_pdf = PASTA_DAS_FIGURAS / f"{NOME_DA_FIGURA}.pdf"
    caminho_do_png = PASTA_DAS_FIGURAS / f"{NOME_DA_FIGURA}.png"
    figura.savefig(caminho_do_pdf, metadata={"CreationDate": None})
    figura.savefig(caminho_do_png, dpi=RESOLUCAO_DO_PNG_EM_DPI, metadata={"Software": None})
    LOGGER.info("Gravados %s e %s.", caminho_do_pdf.name, caminho_do_png.name)


# ==============================================================================================
# Orquestracao
# ==============================================================================================
def calcular_horizontes_de_cruzamento(metricas: pd.DataFrame) -> dict[str, int | None]:
    """Horizonte de cruzamento de cada painel, calculado das metricas (nunca digitado)."""
    horizontes = np.array(HORIZONTES)
    horizontes_de_cruzamento: dict[str, int | None] = {}
    for painel in PAINEIS:
        serie_do_composto = extrair_serie_da_metrica(metricas, NOME_DO_MODELO_COMPOSTO, painel.coluna_da_metrica)
        serie_da_regua = extrair_serie_da_metrica(metricas, NOME_DA_REGUA_SAZONAL, painel.coluna_da_metrica)
        horizonte_de_cruzamento = encontrar_horizonte_de_cruzamento(
            horizontes,
            serie_do_composto.to_numpy(dtype=float),
            serie_da_regua.to_numpy(dtype=float),
            painel.maior_e_melhor,
        )
        horizontes_de_cruzamento[painel.coluna_da_metrica] = horizonte_de_cruzamento
        LOGGER.info("Cruzamento em %s: h = %s.", painel.coluna_da_metrica, horizonte_de_cruzamento)
    return horizontes_de_cruzamento


def principal() -> None:
    """Valida a definicao e as ancoras, calcula as metricas, grava o CSV e desenha a figura."""
    # O log e configurado so no logger deste script: no logger raiz, o fontTools (que o matplotlib
    # usa ao embutir fontes no PDF) despejaria centenas de linhas de depuracao.
    manipulador_de_log = logging.StreamHandler(sys.stdout)
    manipulador_de_log.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(manipulador_de_log)
    LOGGER.setLevel(logging.INFO)
    configurar_estilo_global()

    previsoes_do_e3 = ler_previsoes(ARQUIVO_DAS_PREVISOES_DO_COMPOSTO)
    resumo_do_composto = ler_tabela_de_metricas(ARQUIVO_DO_RESUMO_DO_COMPOSTO)
    previsoes_da_referencia = ler_previsoes(ARQUIVO_DAS_PREVISOES_DA_REFERENCIA)
    metricas_da_referencia = ler_tabela_de_metricas(ARQUIVO_DAS_METRICAS_DA_REFERENCIA)
    casos_por_data = carregar_casos_por_data()

    # A definicao da fracao do pico so vale se reproduzir o slide; aborta antes de qualquer saida.
    validar_definicao_da_fracao_do_pico(previsoes_da_referencia)

    previsoes_do_composto = selecionar_previsoes_do_composto(previsoes_do_e3)
    previsoes_da_regua = montar_previsoes_da_regua_sazonal(previsoes_do_composto, casos_por_data)

    metricas_do_composto = calcular_metricas_por_horizonte(previsoes_do_composto, NOME_DO_MODELO_COMPOSTO)
    metricas_da_regua = calcular_metricas_por_horizonte(previsoes_da_regua, NOME_DA_REGUA_SAZONAL)
    metricas = pd.concat([metricas_do_composto, metricas_da_regua], ignore_index=True)

    conferir_ancoras_do_mae(metricas)
    conferir_com_arquivos_certificados(metricas, metricas_da_referencia, resumo_do_composto)
    validar_limites_dos_eixos(metricas)

    horizontes_de_cruzamento = calcular_horizontes_de_cruzamento(metricas)
    figura = montar_figura(metricas, horizontes_de_cruzamento)

    gravar_metricas_descritivas(metricas)
    gravar_figura(figura)
    plt.close(figura)


if __name__ == "__main__":
    principal()
