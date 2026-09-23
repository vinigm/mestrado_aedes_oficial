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

# Formato largo: a mesma proporção do palco do slide, para a figura ocupá-lo
# sem sobrar faixa branca nas laterais.
LARGURA_DA_FIGURA = 15.0


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
    eixo.set_title(titulo, fontsize=12, fontweight="bold", color=COR_TEXTO, pad=8)
    eixo.set_ylabel(rotulo_y, fontsize=9.5, color=COR_TEXTO)
    eixo.grid(True, axis="y", color=COR_GRADE, linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors=COR_TEXTO, labelsize=9)

    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        eixo.spines[lado].set_color(COR_GRADE)


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
        2, 1, figsize=(LARGURA_DA_FIGURA, 6.4), sharex=True,
        gridspec_kw={"hspace": 0.42},
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

    figura, eixos = plt.subplots(
        4, 1, figsize=(LARGURA_DA_FIGURA, 7.6), sharex=True,
        gridspec_kw={"hspace": 0.55},
    )

    eixos[0].bar(datas, tabela["precip_total_mm"], width=6, color=COR_CLIMA, alpha=0.75)
    _preparar_painel(eixos[0], "Chuva — total da semana", "mm/semana")

    eixos[1].plot(datas, tabela["temp_media"], color=COR_CLIMA, linewidth=1.0)
    _preparar_painel(eixos[1], "Temperatura média", "°C")

    eixos[2].plot(datas, tabela["umid_media"], color=COR_CLIMA, linewidth=1.0)
    _preparar_painel(eixos[2], "Umidade relativa média", "%")

    eixos[3].axhline(0, color=COR_APAGADO, linewidth=0.8, linestyle=":")
    eixos[3].plot(datas, tabela["oni"], color=COR_ENSO, linewidth=1.2)
    _preparar_painel(eixos[3], "ENSO — índice ONI (El Niño e La Niña)", "índice ONI")

    for eixo in eixos:
        _marcar_enchente(eixo)

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
