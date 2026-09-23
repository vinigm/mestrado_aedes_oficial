"""Figuras desenhadas especificamente para os slides.

A figura da página de dados empilha seis painéis num formato alto. Num slide
16:9 ela encolhe até ficar ilegível, então aqui as mesmas séries são
redesenhadas em formato **largo e baixo**, quebradas em duas figuras:

  1. vetor e casos — o par que sustenta a pergunta da pesquisa;
  2. clima e ENSO — o contexto que alimenta o modelo.

Uso:
    python3 figuras_slides.py

⚠️ Este módulo NÃO toca `pagina_web/figuras_site.py` nem as imagens dele. Ele
escreve só em `NOVO_HTML/saida/imagens/`.
"""

import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent

CAMINHO_DA_TABELA = (
    PASTA_DESTE_ARQUIVO.parent
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "tabela_modelagem"
    / "tabela_final.csv"
)

PASTA_DE_IMAGENS = PASTA_DESTE_ARQUIVO / "saida" / "imagens"

# Cores do tema do site novo, para que figura e página falem a mesma língua.
COR_VETOR = "#1B6EF3"
COR_CASOS = "#C0392B"
COR_CLIMA = "#1F7A4D"
COR_ENSO = "#8E44AD"
COR_GRADE = "#E3E8EE"
COR_TEXTO = "#3E4C5C"
COR_APAGADO = "#93A2B3"

# A semana em que a enchente interrompeu as vistorias de campo.
DATA_DA_ENCHENTE = pd.Timestamp("2024-05-05")

# A caixa que o palco do slide reserva para uma figura mede 1008 x 367 px na
# tela, ou seja, proporção 2,75. Figura mais alta que isso não é cortada: ela
# encolhe até a ALTURA caber e deixa faixa branca dos dois lados. A figura de
# clima, em 1,83, chegava a desperdiçar um terço da largura disponível.
#
# O tamanho em polegadas tem um efeito que não é óbvio. Como o navegador reduz
# a imagem até ela caber na altura da caixa, o fator de redução é
# `altura_da_caixa / (altura_da_figura * dpi)` — quanto MENOR a figura em
# polegadas, menos ela é reduzida e MAIOR fica o texto na tela. Por isso a
# largura caiu de 15 para 13: a figura ocupa a mesma área e a legenda cresce.
PROPORCAO_DA_CAIXA_DO_SLIDE = 2.75
LARGURA_DA_FIGURA = 13.0
ALTURA_DA_FIGURA = LARGURA_DA_FIGURA / PROPORCAO_DA_CAIXA_DO_SLIDE

def carregar_tabela() -> pd.DataFrame:
    """Lê a tabela semanal que alimenta os modelos.

    Returns:
        A tabela com a coluna de data já convertida.

    Raises:
        FileNotFoundError: Se a tabela não estiver no caminho esperado.
    """
    if not CAMINHO_DA_TABELA.is_file():
        raise FileNotFoundError(f"Tabela não encontrada: {CAMINHO_DA_TABELA}")

    return pd.read_csv(CAMINHO_DA_TABELA, parse_dates=["data_inicio_semana_epidemi"])


def _preparar_painel(eixo, titulo: str, rotulo_y: str) -> None:
    """Aplica a mesma moldura visual a todos os painéis.

    Args:
        eixo: O painel a preparar.
        titulo: Título curto, centralizado acima do painel.
        rotulo_y: Nome da grandeza no eixo vertical.
    """
    eixo.set_title(titulo, fontsize=13, fontweight="bold", color=COR_TEXTO, pad=6)
    eixo.set_ylabel(rotulo_y, fontsize=10, color=COR_TEXTO)
    eixo.grid(True, axis="y", color=COR_GRADE, linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors=COR_TEXTO, labelsize=9.5)

    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        eixo.spines[lado].set_color(COR_GRADE)


def _marcar_todos_os_anos(eixos, anos_entre_marcas: int = 1) -> None:
    """Põe uma marca por ano no eixo do tempo, e o rótulo em TODOS os painéis.

    Duas coisas são consertadas aqui, e as duas custam leitura em apresentação:

    - sem locator explícito o matplotlib escolhe sozinho o espaçamento e acaba
      marcando de dois em dois anos, o que obriga a contar quadradinhos para
      saber onde se está;
    - com `sharex=True`, só o painel de baixo recebe rótulo. Quem olha o painel
      de cima projetado numa tela precisa descer os olhos até o fim da figura
      para se situar, e numa banca isso não acontece.

    Args:
        eixos: A lista de painéis da figura.
        anos_entre_marcas: De quantos em quantos anos marcar. Fica em 1 no
            painel que ocupa a largura toda; sobe para 2 quando a figura tem
            duas colunas, porque catorze rótulos não cabem em meia largura
            sem se sobreporem.
    """
    for eixo in eixos:
        eixo.xaxis.set_major_locator(mdates.YearLocator(anos_entre_marcas))
        eixo.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        eixo.tick_params(axis="x", labelbottom=True, labelsize=9.5)


def _marcar_enchente(eixo) -> None:
    """Marca a semana da enchente de maio de 2024, que parou as vistorias."""
    eixo.axvline(
        DATA_DA_ENCHENTE, color=COR_CASOS, linestyle="--", linewidth=1.1, alpha=0.6
    )


def _marcar_periodo_sem_dado(eixo, datas, primeira_data_com_dado, texto: str) -> None:
    """Sombreia o trecho anterior ao início de uma série, e o nomeia.

    Args:
        eixo: O painel.
        datas: A coluna de datas da tabela.
        primeira_data_com_dado: Onde a série começa de fato.
        texto: O que dizer dentro da faixa sombreada.
    """
    eixo.axvspan(
        datas.min(), primeira_data_com_dado, color=COR_APAGADO, alpha=0.16, linewidth=0
    )
    eixo.text(
        datas.min() + (primeira_data_com_dado - datas.min()) / 2,
        eixo.get_ylim()[1] * 0.62,
        texto,
        fontsize=9,
        color=COR_TEXTO,
        ha="center",
    )


def desenhar_vetor_e_casos(tabela: pd.DataFrame) -> pathlib.Path:
    """Desenha o par que sustenta a pergunta da pesquisa.

    Dois painéis no mesmo eixo de tempo: a densidade do vetor em cima e os
    casos confirmados embaixo. É a figura em que a defasagem entre as duas
    curvas fica visível.

    Args:
        tabela: A tabela semanal.

    Returns:
        O caminho do arquivo gravado.
    """
    datas = tabela["data_inicio_semana_epidemi"]

    figura, eixos = plt.subplots(
        2, 1, figsize=(LARGURA_DA_FIGURA, ALTURA_DA_FIGURA), sharex=True,
        gridspec_kw={"hspace": 0.46},
    )

    eixos[0].fill_between(
        datas, tabela["aedes_aegypti_por_armadilha"], color=COR_VETOR, alpha=0.22,
        linewidth=0,
    )
    eixos[0].plot(
        datas, tabela["aedes_aegypti_por_armadilha"], color=COR_VETOR, linewidth=1.2
    )
    _preparar_painel(
        eixos[0], "Densidade de Aedes aegypti — o que a armadilha mede",
        "fêmeas por\narmadilha",
    )
    _marcar_enchente(eixos[0])

    eixos[1].fill_between(
        datas, tabela["casos_confirmados"], color=COR_CASOS, alpha=0.22, linewidth=0
    )
    eixos[1].plot(datas, tabela["casos_confirmados"], color=COR_CASOS, linewidth=1.2)
    _preparar_painel(
        eixos[1], "Casos confirmados de dengue — o alvo do modelo", "casos\nconfirmados"
    )
    _marcar_enchente(eixos[1])

    _marcar_todos_os_anos(eixos)

    semanas_com_caso = tabela.dropna(subset=["casos_confirmados"])
    if not semanas_com_caso.empty:
        _marcar_periodo_sem_dado(
            eixos[1],
            datas,
            semanas_com_caso["data_inicio_semana_epidemi"].min(),
            "sem série de casos antes de 2018",
        )

    figura.tight_layout()
    caminho = PASTA_DE_IMAGENS / "slide_vetor_e_casos.png"
    figura.savefig(caminho, dpi=150, facecolor="white")
    plt.close(figura)

    return caminho


def desenhar_clima(tabela: pd.DataFrame) -> pathlib.Path:
    """Desenha o contexto climático que alimenta o modelo.

    Args:
        tabela: A tabela semanal.

    Returns:
        O caminho do arquivo gravado.
    """
    datas = tabela["data_inicio_semana_epidemi"]

    # Grade 2x2, e não quatro painéis empilhados. A caixa do slide tem altura
    # fixa: empilhados, os quatro dividem 367 px de tela e sobram cerca de 65
    # px de área de desenho para cada um, depois do título e dos rótulos — o
    # título de um encostava nos anos do de cima. Em duas colunas cada painel
    # fica com mais que o dobro de altura, e aí cabe eixo do tempo em todos,
    # que é o que a figura precisa mostrar.
    figura, grade = plt.subplots(
        2, 2, figsize=(LARGURA_DA_FIGURA, ALTURA_DA_FIGURA),
        gridspec_kw={"hspace": 0.62, "wspace": 0.20},
    )
    paineis = grade.flatten()

    paineis[0].bar(datas, tabela["precip_total_mm"], width=6, color=COR_CLIMA, alpha=0.75)
    _preparar_painel(paineis[0], "Chuva — total da semana", "mm/semana")

    paineis[1].plot(datas, tabela["temp_media"], color=COR_CLIMA, linewidth=1.0)
    _preparar_painel(paineis[1], "Temperatura média", "°C")

    paineis[2].plot(datas, tabela["umid_media"], color=COR_CLIMA, linewidth=1.0)
    _preparar_painel(paineis[2], "Umidade relativa média", "%")

    paineis[3].axhline(0, color=COR_APAGADO, linewidth=0.8, linestyle=":")
    paineis[3].plot(datas, tabela["oni"], color=COR_ENSO, linewidth=1.2)
    _preparar_painel(paineis[3], "ENSO — índice ONI (El Niño e La Niña)", "índice ONI")

    for painel in paineis:
        _marcar_enchente(painel)

    _marcar_todos_os_anos(paineis, anos_entre_marcas=2)

    figura.tight_layout()
    caminho = PASTA_DE_IMAGENS / "slide_clima.png"
    figura.savefig(caminho, dpi=150, facecolor="white")
    plt.close(figura)

    return caminho


def main() -> None:
    """Gera as duas figuras dos slides."""
    PASTA_DE_IMAGENS.mkdir(parents=True, exist_ok=True)

    tabela = carregar_tabela()

    for caminho in (desenhar_vetor_e_casos(tabela), desenhar_clima(tabela)):
        print(f"  {caminho.name}")


if __name__ == "__main__":
    main()
