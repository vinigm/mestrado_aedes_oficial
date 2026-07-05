"""Figura-sintese: sem ENSO, o vetor carrega o horizonte longo.

Le a tabela de resultados dos modelos climaticos SEM ENSO (metricas por
horizonte e por conjunto de features) e monta uma figura de dois paineis:

  - Painel esquerdo: R2 x horizonte para o modelo so-clima (M0_clima6) e para
    o modelo clima+vetor (M1_clima6_vetor). Mostra que o clima puro perde a
    skill nos horizontes longos (R2 <= 0) enquanto o vetor segura.
  - Painel direito: lift marginal do vetor, isto e, a reducao percentual do MAE
    ao adicionar o vetor ao modelo so-clima, barra a barra por horizonte.

Entrada:
  - Bases de dados/tabela_modelagem/clima_enxuto_sem_enso_resultados.csv

Saida:
  - lift_sem_enso.png (gravado no diretorio de trabalho atual)
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------------------------- config
# Nome do subdiretorio que identifica a raiz do projeto (torna o script
# executavel de qualquer subpasta).
MARCADOR_RAIZ = "Raspagem"

# Localizacao da tabela de resultados dentro da raiz do projeto.
SUBDIRETORIO_TABELA_MODELAGEM = ("Bases de dados", "tabela_modelagem")
NOME_ARQUIVO_RESULTADOS = "clima_enxuto_sem_enso_resultados.csv"

# Colunas da tabela de resultados usadas nos pivots.
COLUNA_HORIZONTE = "h"
COLUNA_CONJUNTO = "conjunto"
COLUNA_R2 = "R2"
COLUNA_MAE = "MAE"

# Conjuntos de features comparados na figura (base de 6 variaveis climaticas).
CONJUNTO_SO_CLIMA = "M0_clima6"
CONJUNTO_CLIMA_VETOR = "M1_clima6_vetor"

# Fator de conversao de fracao para porcentagem (lift em %).
PERCENTUAL = 100

# Cores dos elementos do grafico.
COR_SO_CLIMA = "tab:blue"
COR_CLIMA_VETOR = "tab:green"
COR_LIFT_POSITIVO = "tab:green"
COR_LIFT_NEGATIVO = "tab:red"
COR_LINHA_ZERO = "k"
COR_ANOTACAO = "dimgray"

# Rotulos das series do painel de R2.
ROTULO_SO_CLIMA = "M0: só clima-enxuto (sem ENSO)"
ROTULO_CLIMA_VETOR = "M1: clima-enxuto + vetor"

# Faixa de horizontes (semanas a frente) destacada como "horizonte longo".
HORIZONTE_INICIO_DESTAQUE = 5.5
HORIZONTE_FIM_DESTAQUE = 12.5
ALPHA_FAIXA_DESTAQUE = 0.07

# Parametros das linhas de referencia horizontais (y = 0).
LARGURA_LINHA_ZERO = 0.8
ESTILO_LINHA_ZERO_TRACEJADA = "--"

# Anotacao explicativa do painel de R2.
TEXTO_ANOTACAO_R2 = "clima puro perde a skill\n(R² ≤ 0); o vetor segura"
POSICAO_ANOTACAO_R2 = (9, -0.05)
FONTE_ANOTACAO = 9
FONTE_LEGENDA = 9

# Parametros de layout e gravacao da figura.
TAMANHO_FIGURA = (13, 4.5)
ALPHA_GRADE = 0.3
DPI_FIGURA = 110
NOME_ARQUIVO_SAIDA = "lift_sem_enso.png"

# Titulos e nomes dos eixos.
TITULO_R2 = "R² × horizonte (sem ENSO)"
TITULO_LIFT = "Lift marginal do vetor (% redução do MAE), sem ENSO"
ROTULO_EIXO_X = "semanas à frente"
ROTULO_EIXO_Y_R2 = "R²"
ROTULO_EIXO_Y_LIFT = "lift %"


def encontrar_raiz_do_projeto(marcador_de_diretorio: str = MARCADOR_RAIZ) -> Path:
    """Sobe a partir do diretorio atual ate achar a raiz do projeto.

    A raiz e identificada pela presenca de um subdiretorio marcador (por padrao
    'Raspagem'), o que torna o script executavel de qualquer subpasta.

    Args:
        marcador_de_diretorio: Nome do subdiretorio que identifica a raiz.

    Returns:
        Caminho da raiz do projeto.

    Raises:
        FileNotFoundError: Se nenhum diretorio ancestral contiver o marcador.
    """
    diretorio_atual = Path.cwd()
    for diretorio_candidato in [diretorio_atual, *diretorio_atual.parents]:
        if (diretorio_candidato / marcador_de_diretorio).is_dir():
            return diretorio_candidato
    raise FileNotFoundError("raiz nao encontrada")


def carregar_resultados() -> pd.DataFrame:
    """Le a tabela de resultados dos modelos climaticos sem ENSO.

    Returns:
        DataFrame com uma linha por (conjunto de features, horizonte) e as
        metricas MAE e R2.
    """
    raiz_do_projeto = encontrar_raiz_do_projeto()
    diretorio_tabela = raiz_do_projeto.joinpath(*SUBDIRETORIO_TABELA_MODELAGEM)
    caminho_resultados = diretorio_tabela / NOME_ARQUIVO_RESULTADOS
    resultados = pd.read_csv(caminho_resultados)
    return resultados


def pivotar_por_horizonte(resultados: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Pivota a tabela de resultados para metrica x horizonte x conjunto.

    Args:
        resultados: Tabela longa com as colunas de horizonte, conjunto e metrica.
        metrica: Nome da coluna de metrica a espalhar em colunas por conjunto.

    Returns:
        DataFrame indexado pelo horizonte, com uma coluna por conjunto de
        features contendo os valores da metrica.
    """
    tabela_pivotada = resultados.pivot(
        index=COLUNA_HORIZONTE,
        columns=COLUNA_CONJUNTO,
        values=metrica,
    )
    return tabela_pivotada


def calcular_lift_do_vetor(mae_por_horizonte: pd.DataFrame) -> pd.Series:
    """Calcula o lift marginal do vetor (reducao percentual do MAE).

    O lift e a fracao do MAE do modelo so-clima que desaparece ao adicionar o
    vetor, expressa em porcentagem. Valores positivos indicam que o vetor
    reduziu o erro.

    Args:
        mae_por_horizonte: MAE por horizonte, com colunas por conjunto de
            features (deve conter os conjuntos so-clima e clima+vetor).

    Returns:
        Serie de lift percentual indexada pelo horizonte.
    """
    mae_so_clima = mae_por_horizonte[CONJUNTO_SO_CLIMA]
    mae_clima_vetor = mae_por_horizonte[CONJUNTO_CLIMA_VETOR]
    reducao_absoluta = mae_so_clima - mae_clima_vetor
    lift_percentual = reducao_absoluta / mae_so_clima * PERCENTUAL
    return lift_percentual


def escolher_cores_das_barras(lift_percentual: pd.Series) -> np.ndarray:
    """Escolhe a cor de cada barra de lift conforme o sinal.

    Barras com lift estritamente positivo ficam verdes; as demais (lift zero,
    negativo ou ausente) ficam vermelhas, preservando o fallback original.

    Args:
        lift_percentual: Serie de lift percentual por horizonte.

    Returns:
        Array de cores, uma por horizonte, na mesma ordem da serie.
    """
    lift_positivo = lift_percentual > 0
    cores = np.select(
        [lift_positivo],
        [COR_LIFT_POSITIVO],
        default=COR_LIFT_NEGATIVO,
    )
    return cores


def desenhar_painel_r2(eixo: plt.Axes, r2_por_horizonte: pd.DataFrame) -> None:
    """Desenha o painel de R2 x horizonte (so-clima vs clima+vetor).

    Args:
        eixo: Eixo matplotlib onde o painel e desenhado.
        r2_por_horizonte: R2 por horizonte, com colunas por conjunto de features.
    """
    eixo.plot(
        r2_por_horizonte.index,
        r2_por_horizonte[CONJUNTO_SO_CLIMA],
        "o-",
        color=COR_SO_CLIMA,
        label=ROTULO_SO_CLIMA,
    )
    eixo.plot(
        r2_por_horizonte.index,
        r2_por_horizonte[CONJUNTO_CLIMA_VETOR],
        "o-",
        color=COR_CLIMA_VETOR,
        label=ROTULO_CLIMA_VETOR,
    )
    eixo.axhline(
        0,
        color=COR_LINHA_ZERO,
        lw=LARGURA_LINHA_ZERO,
        ls=ESTILO_LINHA_ZERO_TRACEJADA,
    )
    eixo.axvspan(
        HORIZONTE_INICIO_DESTAQUE,
        HORIZONTE_FIM_DESTAQUE,
        color=COR_CLIMA_VETOR,
        alpha=ALPHA_FAIXA_DESTAQUE,
    )
    eixo.annotate(
        TEXTO_ANOTACAO_R2,
        POSICAO_ANOTACAO_R2,
        fontsize=FONTE_ANOTACAO,
        color=COR_ANOTACAO,
        ha="center",
    )
    eixo.set_title(TITULO_R2)
    eixo.set_xlabel(ROTULO_EIXO_X)
    eixo.set_ylabel(ROTULO_EIXO_Y_R2)
    eixo.legend(loc="upper right", fontsize=FONTE_LEGENDA)
    eixo.grid(alpha=ALPHA_GRADE)


def desenhar_painel_lift(eixo: plt.Axes, lift_percentual: pd.Series) -> None:
    """Desenha o painel de lift marginal do vetor (barras por horizonte).

    Args:
        eixo: Eixo matplotlib onde o painel e desenhado.
        lift_percentual: Serie de lift percentual por horizonte.
    """
    cores_das_barras = escolher_cores_das_barras(lift_percentual)
    eixo.bar(lift_percentual.index, lift_percentual, color=cores_das_barras)
    eixo.axhline(0, color=COR_LINHA_ZERO, lw=LARGURA_LINHA_ZERO)
    eixo.axvspan(
        HORIZONTE_INICIO_DESTAQUE,
        HORIZONTE_FIM_DESTAQUE,
        color=COR_CLIMA_VETOR,
        alpha=ALPHA_FAIXA_DESTAQUE,
    )
    eixo.set_title(TITULO_LIFT)
    eixo.set_xlabel(ROTULO_EIXO_X)
    eixo.set_ylabel(ROTULO_EIXO_Y_LIFT)
    eixo.grid(alpha=ALPHA_GRADE)


def montar_figura(
    r2_por_horizonte: pd.DataFrame,
    lift_percentual: pd.Series,
) -> plt.Figure:
    """Monta a figura de dois paineis (R2 e lift do vetor).

    Args:
        r2_por_horizonte: R2 por horizonte, com colunas por conjunto de features.
        lift_percentual: Serie de lift percentual por horizonte.

    Returns:
        Figura matplotlib pronta para ser gravada.
    """
    figura, eixos = plt.subplots(1, 2, figsize=TAMANHO_FIGURA)
    desenhar_painel_r2(eixos[0], r2_por_horizonte)
    desenhar_painel_lift(eixos[1], lift_percentual)
    plt.tight_layout()
    return figura


def gravar_figura(figura: plt.Figure) -> Path:
    """Grava a figura no diretorio de trabalho atual.

    Args:
        figura: Figura matplotlib a gravar.

    Returns:
        Caminho do arquivo PNG gravado.
    """
    caminho_saida = Path.cwd() / NOME_ARQUIVO_SAIDA
    figura.savefig(caminho_saida, dpi=DPI_FIGURA, bbox_inches="tight")
    return caminho_saida


def main() -> None:
    """Le os resultados, monta a figura-sintese e grava o PNG."""
    resultados = carregar_resultados()
    r2_por_horizonte = pivotar_por_horizonte(resultados, COLUNA_R2)
    mae_por_horizonte = pivotar_por_horizonte(resultados, COLUNA_MAE)
    lift_percentual = calcular_lift_do_vetor(mae_por_horizonte)

    figura = montar_figura(r2_por_horizonte, lift_percentual)
    caminho_saida = gravar_figura(figura)
    print("salvo:", caminho_saida)


if __name__ == "__main__":
    main()
