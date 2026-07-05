"""Figura do Modelo 6 (deteccao de surto).

Painel A = viabilidade (InfoDengue 2010-26): F1 do LGBM vs baselines por horizonte.
Painel B = lift do vetor (tabela_final): F1 sazonal / so-clima / clima+vetor por horizonte.

Le: Bases de dados/tabela_modelagem/deteccao_surto_resultados.csv
Salva: deteccao_surto.png (ao lado deste script).
"""
import dataclasses
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

# --------------------------------------------------------------------- config
# Percentil de casos que define "surto" cujas metricas sao plotadas. O CSV de
# resultados guarda P90 e P95; a figura usa apenas o P90.
PERCENTIL_SURTO = 90

# Nome do subdiretorio que identifica a raiz do projeto (permite rodar de
# qualquer subpasta subindo ate ele).
MARCADOR_RAIZ = "Raspagem"

# Caminho relativo, a partir da raiz, do CSV de resultados da deteccao de surto.
SUBCAMINHO_RESULTADOS = Path("Bases de dados") / "tabela_modelagem" / "deteccao_surto_resultados.csv"

# Nome do arquivo de figura gravado ao lado deste script.
NOME_ARQUIVO_SAIDA = "deteccao_surto.png"

# Rotulos dos experimentos como aparecem na coluna 'exp' do CSV de resultados.
EXPERIMENTO_VIABILIDADE = "A_infodengue"
EXPERIMENTO_LIFT_VETOR = "B_tabela_final"

# Geometria e estilo compartilhados pelos dois paineis.
LARGURA_ALTURA_FIGURA = (12, 4.6)
RESOLUCAO_DPI = 130
HORIZONTES_EIXO_X = [4, 8, 12]
LIMITE_EIXO_Y = (0, 1)
TRANSPARENCIA_GRADE = 0.3
TAMANHO_FONTE_LEGENDA = 8

# Anotacoes do eixo x do Painel A: posicao y baixa, cinza, fonte pequena.
POSICAO_Y_ANOTACAO_HORIZONTE = 0.02
TAMANHO_FONTE_ANOTACAO = 7
COR_ANOTACAO = "gray"


@dataclasses.dataclass(frozen=True)
class SerieDeModelo:
    """Uma curva do grafico: um modelo e a cor com que ele e desenhado.

    Attributes:
        nome_modelo: Rotulo do modelo, como aparece na coluna 'modelo' do CSV
            e na legenda da figura.
        cor: Cor hexadecimal da linha e dos marcadores.
    """

    nome_modelo: str
    cor: str


@dataclasses.dataclass(frozen=True)
class MarcadorDeHorizonte:
    """Anotacao textual de um horizonte no eixo x do Painel A.

    Attributes:
        horizonte: Posicao no eixo x (semanas a frente) onde o texto aparece.
        rotulo: Texto exibido (ex.: '1 mes').
    """

    horizonte: int
    rotulo: str


# Curvas do Painel A (viabilidade), NA ORDEM em que sao desenhadas e listadas
# na legenda: LGBM clima+autorregressivo, persistencia e sazonal.
SERIES_PAINEL_VIABILIDADE = [
    SerieDeModelo("clima+AR_LGBM", "#1f77b4"),
    SerieDeModelo("persistencia", "#7f7f7f"),
    SerieDeModelo("sazonal", "#ff7f0e"),
]

# Curvas do Painel B (lift do vetor), NA ORDEM em que sao desenhadas e listadas
# na legenda: sazonal, so-clima e clima+vetor.
SERIES_PAINEL_LIFT_VETOR = [
    SerieDeModelo("sazonal", "#ff7f0e"),
    SerieDeModelo("so-clima", "#2ca02c"),
    SerieDeModelo("clima+vetor", "#d62728"),
]

# Marcadores de meses sob as curvas do Painel A.
MARCADORES_HORIZONTE = [
    MarcadorDeHorizonte(4, "1 mes"),
    MarcadorDeHorizonte(8, "2 meses"),
    MarcadorDeHorizonte(12, "3 meses"),
]


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
    """Le o CSV de metricas de deteccao de surto a partir da raiz do projeto.

    Returns:
        DataFrame com as metricas de todos os experimentos, percentis, horizontes
        e modelos gravados pelo script de modelagem.
    """
    raiz_do_projeto = encontrar_raiz_do_projeto()
    caminho_resultados = raiz_do_projeto / SUBCAMINHO_RESULTADOS
    return pd.read_csv(caminho_resultados)


def filtrar_experimento(
    resultados: pd.DataFrame,
    nome_experimento: str,
    percentil: int,
) -> pd.DataFrame:
    """Recorta as linhas de um experimento em um percentil de surto.

    Args:
        resultados: Tabela completa de metricas.
        nome_experimento: Valor da coluna 'exp' a manter.
        percentil: Valor da coluna 'pctl' a manter.

    Returns:
        Subconjunto das linhas do experimento no percentil pedido.
    """
    eh_do_experimento = resultados["exp"] == nome_experimento
    eh_do_percentil = resultados["pctl"] == percentil
    return resultados[eh_do_experimento & eh_do_percentil]


def plotar_series_por_horizonte(
    eixo: plt.Axes,
    dados_do_experimento: pd.DataFrame,
    series: list[SerieDeModelo],
) -> None:
    """Desenha, no eixo, uma curva de F1 por horizonte para cada modelo.

    Cada modelo vira uma linha com marcadores, ordenada por horizonte crescente.
    A ordem das curvas segue a ordem da lista 'series' (que define tambem a ordem
    da legenda).

    Args:
        eixo: Eixo matplotlib onde desenhar as curvas.
        dados_do_experimento: Metricas ja filtradas para um experimento/percentil.
        series: Modelos a desenhar, com suas cores, na ordem desejada.
    """
    for serie in series:
        eh_do_modelo = dados_do_experimento["modelo"] == serie.nome_modelo
        pontos_do_modelo = dados_do_experimento[eh_do_modelo].sort_values("h")
        eixo.plot(
            pontos_do_modelo["h"],
            pontos_do_modelo["f1"],
            marker="o",
            label=serie.nome_modelo,
            color=serie.cor,
        )


def aplicar_estilo_comum(eixo: plt.Axes, titulo: str) -> None:
    """Aplica titulo, rotulos, limites, grade e legenda comuns aos dois paineis.

    Args:
        eixo: Eixo a estilizar.
        titulo: Titulo do painel.
    """
    eixo.set_title(titulo)
    eixo.set_xlabel("horizonte (semanas a frente)")
    eixo.set_ylabel("F1")
    eixo.set_xticks(HORIZONTES_EIXO_X)
    eixo.set_ylim(*LIMITE_EIXO_Y)
    eixo.grid(alpha=TRANSPARENCIA_GRADE)
    eixo.legend(fontsize=TAMANHO_FONTE_LEGENDA)


def plotar_painel_viabilidade(eixo: plt.Axes, resultados: pd.DataFrame) -> None:
    """Desenha o Painel A: viabilidade da deteccao no InfoDengue.

    Args:
        eixo: Eixo do painel A.
        resultados: Tabela completa de metricas.
    """
    dados_viabilidade = filtrar_experimento(
        resultados, EXPERIMENTO_VIABILIDADE, PERCENTIL_SURTO
    )
    plotar_series_por_horizonte(eixo, dados_viabilidade, SERIES_PAINEL_VIABILIDADE)
    titulo_painel_a = (
        f"A) Viabilidade — InfoDengue 2010-26 (surto = P{PERCENTIL_SURTO})\n"
        "F1 de deteccao por horizonte"
    )
    aplicar_estilo_comum(eixo, titulo_painel_a)
    for marcador in MARCADORES_HORIZONTE:
        eixo.annotate(
            marcador.rotulo,
            (marcador.horizonte, POSICAO_Y_ANOTACAO_HORIZONTE),
            ha="center",
            fontsize=TAMANHO_FONTE_ANOTACAO,
            color=COR_ANOTACAO,
        )


def plotar_painel_lift_vetor(eixo: plt.Axes, resultados: pd.DataFrame) -> None:
    """Desenha o Painel B: lift do vetor na deteccao (tabela_final).

    Args:
        eixo: Eixo do painel B.
        resultados: Tabela completa de metricas.
    """
    dados_lift_vetor = filtrar_experimento(
        resultados, EXPERIMENTO_LIFT_VETOR, PERCENTIL_SURTO
    )
    plotar_series_por_horizonte(eixo, dados_lift_vetor, SERIES_PAINEL_LIFT_VETOR)
    titulo_painel_b = (
        f"B) Lift do vetor na deteccao — tabela_final (surto = P{PERCENTIL_SURTO})\n"
        "F1: so-clima vs clima+VETOR"
    )
    aplicar_estilo_comum(eixo, titulo_painel_b)


def montar_figura(resultados: pd.DataFrame) -> plt.Figure:
    """Monta a figura de dois paineis com as metricas de deteccao de surto.

    Args:
        resultados: Tabela completa de metricas.

    Returns:
        A figura matplotlib pronta para ser salva.
    """
    figura, eixos = plt.subplots(1, 2, figsize=LARGURA_ALTURA_FIGURA)
    plotar_painel_viabilidade(eixos[0], resultados)
    plotar_painel_lift_vetor(eixos[1], resultados)
    figura.tight_layout()
    return figura


def salvar_figura(figura: plt.Figure) -> Path:
    """Salva a figura ao lado deste script e devolve o caminho gravado.

    Args:
        figura: Figura a ser gravada.

    Returns:
        Caminho do arquivo PNG gerado.
    """
    caminho_saida = Path(__file__).parent / NOME_ARQUIVO_SAIDA
    figura.savefig(caminho_saida, dpi=RESOLUCAO_DPI, bbox_inches="tight")
    return caminho_saida


def main() -> None:
    """Le os resultados, monta a figura de dois paineis e a salva em PNG."""
    resultados = carregar_resultados()
    figura = montar_figura(resultados)
    caminho_saida = salvar_figura(figura)
    print("figura salva:", caminho_saida)


if __name__ == "__main__":
    main()
