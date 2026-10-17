"""Gera a Figura 3 do artigo (seção 4.1, "O erro ao longo do horizonte").

O que mostra: dois painéis lado a lado, com o mesmo eixo de horizonte (1 a 12 semanas).
    (a) erro absoluto médio (MAE, casos por semana) da configuração principal, da configuração
        exploratória, do modelo composto (N = 13), da régua sazonal e da persistência;
    (b) WIS (janela padrão 07/01/2024 a 01/02/2026) de folha 5 (principal), folha 20
        (exploratória), do composto e da régua climatológica.

Forma (skill de visualização): duas medidas em escalas diferentes -> pequenos múltiplos, nunca dois
eixos y. Identidade não só pela cor: modelos têm marcadores distintos; réguas não têm marcador e
diferem pelo traço (tracejado, pontilhado). Rótulo direto no fim de cada linha e uma legenda única.
A persistência passa de 697 casos em h = 12; o eixo y do painel (a) é cortado em 360 e a linha
sai do gráfico, com um rótulo que informa os valores fora da escala.

Lê somente resultados já certificados (leitura, não escreve neles) e confere as âncoras
numéricas antes de desenhar. Nenhum modelo é treinado.

Rodar, de dentro de projeto_final/:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_figura3.py
"""

import dataclasses
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (o backend precisa ser escolhido antes)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
ARQUIVO_METRICAS = PASTA_DO_PACOTE / "resultados" / "referencia" / "metricas.csv"
ARQUIVO_COMPOSTO = PASTA_DO_PACOTE / "resultados" / "ciencia" / "E3_composto" / "resumo.csv"
ARQUIVO_WIS = PASTA_DO_PACOTE / "resultados" / "wis" / "wis_resumo.csv"
PASTA_DE_SAIDA = PASTA_DO_PACOTE / "figuras"
NOME_DA_FIGURA = "figura3_erro_por_horizonte"

HORIZONTES = list(range(1, 13))
NUMERO_DE_MODELOS_DO_COMPOSTO = 13
JANELA_PADRAO_DO_WIS = "padrao_2024-01-07_a_2026-02-01"

LIMITE_SUPERIOR_MAE = 360.0
LIMITE_SUPERIOR_WIS = 330.0
# Distância mínima, em unidades do eixo y, entre dois rótulos diretos vizinhos.
SEPARACAO_MINIMA_MAE = 20.0
SEPARACAO_MINIMA_WIS = 19.0

# Paleta de referência da skill de visualização (slots 1 a 3) e tons neutros, como na Figura 1.
COR_PRINCIPAL = "#2a78d6"
COR_EXPLORATORIA = "#eb6834"
COR_COMPOSTO = "#1baf7a"
COR_REGUA = "#6b6a66"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_TEXTO_PRIMARIO = "#0b0b0b"
COR_GRADE = "#e4e3df"


@dataclasses.dataclass(frozen=True)
class EstiloDeSerie:
    """Aparência de uma série: o que a identifica além da cor."""

    rotulo_na_legenda: str
    rotulo_direto: str
    cor: str
    marcador: str
    traco: str
    largura: float


ESTILO_PRINCIPAL = EstiloDeSerie("Configuração principal (folha mínima 5)", "principal", COR_PRINCIPAL, "o", "-", 1.6)
ESTILO_EXPLORATORIA = EstiloDeSerie("Configuração exploratória (folha mínima 20)", "exploratória", COR_EXPLORATORIA, "s", "-", 1.6)
ESTILO_COMPOSTO = EstiloDeSerie("Modelo composto (N = 13)", "composto", COR_COMPOSTO, "^", "-", 1.6)
ESTILO_REGUA_SAZONAL = EstiloDeSerie("Régua sazonal", "régua sazonal", COR_REGUA, "", "--", 1.3)
ESTILO_PERSISTENCIA = EstiloDeSerie("Persistência", "persistência", COR_REGUA, "", ":", 1.6)
ESTILO_REGUA_CLIMATOLOGICA = EstiloDeSerie("Régua climatológica", "régua climatológica", COR_REGUA, "", "--", 1.3)

# Âncoras certificadas (tolerância = meia unidade da última casa informada).
ANCORAS_MAE = {
    "referencia": {1: 97.987, 4: 219.669, 8: 272.627, 12: 278.818},
    "regua_sazonal": {1: 202.108, 4: 213.176, 8: 216.167, 12: 217.784},
}
TOLERANCIA_MAE = 5e-4
ANCORAS_COMPOSTO = {1: 102.33, 4: 205.73, 8: 233.51, 12: 260.14}
TOLERANCIA_COMPOSTO = 5e-3
ANCORAS_WIS = {("folha5", 1): 97.0, ("regua_climatologica", 1): 278.3}
TOLERANCIA_WIS = 0.05


def ler_series_de_mae() -> dict[str, np.ndarray]:
    """Lê o MAE por horizonte (h = 1 a 12) de cada braço e do modelo composto N = 13."""
    metricas = pd.read_csv(ARQUIVO_METRICAS, float_precision="round_trip")
    series: dict[str, np.ndarray] = {}
    for braco in ["referencia", "HistGB_folha20_M1", "regua_sazonal", "persistencia"]:
        linhas_do_braco = metricas[metricas["braco"] == braco].sort_values("h")
        horizontes_lidos = linhas_do_braco["h"].tolist()
        if horizontes_lidos != HORIZONTES:
            raise ValueError(f"Braço {braco}: horizontes {horizontes_lidos} em vez de 1 a 12")
        series[braco] = linhas_do_braco["mae"].to_numpy()

    composto = pd.read_csv(ARQUIVO_COMPOSTO, float_precision="round_trip")
    linhas_do_composto = composto[composto["N"] == NUMERO_DE_MODELOS_DO_COMPOSTO].sort_values("h")
    if linhas_do_composto["h"].tolist() != HORIZONTES:
        raise ValueError("Modelo composto N = 13 sem os 12 horizontes")
    series["composto"] = linhas_do_composto["mae"].to_numpy()
    return series


def ler_series_de_wis() -> dict[str, np.ndarray]:
    """Lê o WIS médio por horizonte, na janela padrão, de cada modelo e da régua climatológica."""
    wis = pd.read_csv(ARQUIVO_WIS, float_precision="round_trip")
    wis_na_janela = wis[wis["janela"] == JANELA_PADRAO_DO_WIS]
    series: dict[str, np.ndarray] = {}
    for modelo in ["folha5", "folha20", "composto_N13", "regua_climatologica"]:
        linhas_do_modelo = wis_na_janela[wis_na_janela["modelo"] == modelo].sort_values("h")
        if linhas_do_modelo["h"].tolist() != HORIZONTES:
            raise ValueError(f"WIS de {modelo}: horizontes diferentes de 1 a 12")
        series[modelo] = linhas_do_modelo["wis_medio"].to_numpy()
    return series


def conferir_ancoras(series_mae: dict[str, np.ndarray], series_wis: dict[str, np.ndarray]) -> None:
    """Interrompe se algum valor a plotar divergir das âncoras certificadas."""
    for braco, valores_esperados in ANCORAS_MAE.items():
        for horizonte, esperado in valores_esperados.items():
            lido = series_mae[braco][horizonte - 1]
            if abs(lido - esperado) > TOLERANCIA_MAE:
                raise ValueError(f"Âncora MAE {braco} h={horizonte}: {lido:.4f} ≠ {esperado}")
    for horizonte, esperado in ANCORAS_COMPOSTO.items():
        lido = series_mae["composto"][horizonte - 1]
        if abs(lido - esperado) > TOLERANCIA_COMPOSTO:
            raise ValueError(f"Âncora composto h={horizonte}: {lido:.4f} ≠ {esperado}")
    for (modelo, horizonte), esperado in ANCORAS_WIS.items():
        lido = series_wis[modelo][horizonte - 1]
        if abs(lido - esperado) > TOLERANCIA_WIS:
            raise ValueError(f"Âncora WIS {modelo} h={horizonte}: {lido:.3f} ≠ {esperado}")


def afastar_rotulos(posicoes: dict[str, float], separacao_minima: float) -> dict[str, float]:
    """Afasta rótulos que ficariam um sobre o outro, preservando a ordem vertical.

    Varre de baixo para cima empurrando cada rótulo para pelo menos `separacao_minima` acima do
    anterior, e depois recentra o grupo sobre a posição original média.
    """
    nomes_em_ordem = sorted(posicoes, key=posicoes.get)
    ajustadas: dict[str, float] = {}
    posicao_anterior = None
    for nome in nomes_em_ordem:
        posicao = posicoes[nome]
        if posicao_anterior is not None and posicao < posicao_anterior + separacao_minima:
            posicao = posicao_anterior + separacao_minima
        ajustadas[nome] = posicao
        posicao_anterior = posicao
    deslocamento_medio = np.mean([ajustadas[nome] - posicoes[nome] for nome in nomes_em_ordem])
    for nome in nomes_em_ordem:
        ajustadas[nome] = ajustadas[nome] - deslocamento_medio
    return ajustadas


def formatar_eixos(eixo: plt.Axes, titulo: str, limite_superior: float) -> None:
    """Aplica o estilo recessivo da Figura 1: grade só horizontal, sem moldura."""
    eixo.set_title(titulo, loc="left", fontsize=9, color=COR_TEXTO_PRIMARIO, pad=5)
    eixo.set_xlabel("horizonte (semanas)", fontsize=8.5, color=COR_TEXTO_SECUNDARIO)
    eixo.set_xticks(HORIZONTES)
    eixo.set_xlim(0.7, 12.3)
    eixo.set_ylim(0, limite_superior)
    eixo.grid(axis="y", color=COR_GRADE, linewidth=0.6)
    eixo.set_axisbelow(True)
    eixo.tick_params(colors=COR_TEXTO_SECUNDARIO, labelsize=7.5, length=0)
    for lado in ["top", "right", "left"]:
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(COR_GRADE)


def desenhar_linha(eixo: plt.Axes, valores: np.ndarray, estilo: EstiloDeSerie) -> None:
    """Desenha uma série com seu traço e marcador."""
    marcador = estilo.marcador if estilo.marcador else None
    eixo.plot(
        HORIZONTES,
        valores,
        color=estilo.cor,
        linestyle=estilo.traco,
        linewidth=estilo.largura,
        marker=marcador,
        markersize=3.6,
        markeredgecolor="white",
        markeredgewidth=0.5,
        zorder=3,
    )


def escrever_rotulos_diretos(
    eixo: plt.Axes,
    valores_finais: dict[str, float],
    estilos: dict[str, EstiloDeSerie],
    separacao_minima: float,
) -> None:
    """Escreve o nome de cada série à direita do seu último ponto, sem sobreposição."""
    posicoes_ajustadas = afastar_rotulos(valores_finais, separacao_minima)
    for nome, valor_final in valores_finais.items():
        estilo = estilos[nome]
        eixo.annotate(
            estilo.rotulo_direto,
            xy=(12, valor_final),
            xytext=(12.45, posicoes_ajustadas[nome]),
            textcoords="data",
            fontsize=7.5,
            color=COR_TEXTO_SECUNDARIO,
            va="center",
            ha="left",
            annotation_clip=False,
            arrowprops={"arrowstyle": "-", "color": COR_GRADE, "linewidth": 0.7, "shrinkA": 0, "shrinkB": 2},
        )


def desenhar_painel_mae(eixo: plt.Axes, series_mae: dict[str, np.ndarray]) -> None:
    """Painel (a): MAE por horizonte, com a persistência saindo pelo topo do eixo."""
    estilos_por_serie = {
        "referencia": ESTILO_PRINCIPAL,
        "HistGB_folha20_M1": ESTILO_EXPLORATORIA,
        "composto": ESTILO_COMPOSTO,
        "regua_sazonal": ESTILO_REGUA_SAZONAL,
    }
    for nome, estilo in estilos_por_serie.items():
        desenhar_linha(eixo, series_mae[nome], estilo)
    # A persistência é desenhada inteira; o corte do eixo y a faz sair do gráfico.
    desenhar_linha(eixo, series_mae["persistencia"], ESTILO_PERSISTENCIA)

    valores_finais = {nome: float(series_mae[nome][-1]) for nome in estilos_por_serie}
    escrever_rotulos_diretos(eixo, valores_finais, estilos_por_serie, SEPARACAO_MINIMA_MAE)

    # Valores fora da escala (h = 8 e h = 12), lidos dos dados e não digitados.
    persistencia_em_8 = round(float(series_mae["persistencia"][7]))
    persistencia_em_12 = round(float(series_mae["persistencia"][11]))
    texto_fora_da_escala = f"persistência (pontilhada): {persistencia_em_8} e {persistencia_em_12}\nem 8 e 12 semanas, fora da escala"
    eixo.text(
        6.0,
        LIMITE_SUPERIOR_MAE - 4,
        texto_fora_da_escala,
        fontsize=7.5,
        color=COR_TEXTO_SECUNDARIO,
        va="top",
        ha="left",
        linespacing=1.25,
    )
    formatar_eixos(eixo, "(a) Erro absoluto médio (casos por semana)", LIMITE_SUPERIOR_MAE)


def desenhar_painel_wis(eixo: plt.Axes, series_wis: dict[str, np.ndarray]) -> None:
    """Painel (b): WIS por horizonte dos três modelos e da régua climatológica."""
    estilos_por_serie = {
        "folha5": ESTILO_PRINCIPAL,
        "folha20": ESTILO_EXPLORATORIA,
        "composto_N13": ESTILO_COMPOSTO,
        "regua_climatologica": ESTILO_REGUA_CLIMATOLOGICA,
    }
    for nome, estilo in estilos_por_serie.items():
        desenhar_linha(eixo, series_wis[nome], estilo)
    valores_finais = {nome: float(series_wis[nome][-1]) for nome in estilos_por_serie}
    escrever_rotulos_diretos(eixo, valores_finais, estilos_por_serie, SEPARACAO_MINIMA_WIS)
    formatar_eixos(eixo, "(b) Escore de intervalo ponderado (WIS)", LIMITE_SUPERIOR_WIS)


def montar_legenda(figura: plt.Figure) -> None:
    """Legenda única da figura, com todos os estilos de série."""
    estilos_na_legenda = [
        ESTILO_PRINCIPAL,
        ESTILO_EXPLORATORIA,
        ESTILO_COMPOSTO,
        ESTILO_REGUA_SAZONAL,
        ESTILO_REGUA_CLIMATOLOGICA,
        ESTILO_PERSISTENCIA,
    ]
    elementos: list[Line2D] = []
    for estilo in estilos_na_legenda:
        marcador = estilo.marcador if estilo.marcador else None
        elementos.append(
            Line2D(
                [0],
                [0],
                color=estilo.cor,
                linestyle=estilo.traco,
                linewidth=estilo.largura,
                marker=marcador,
                markersize=4,
                label=estilo.rotulo_na_legenda,
            )
        )
    figura.legend(
        handles=elementos,
        loc="lower center",
        ncol=3,
        fontsize=7.5,
        frameon=False,
        labelcolor=COR_TEXTO_SECUNDARIO,
        handlelength=2.4,
        columnspacing=1.6,
    )


def gerar_figura(series_mae: dict[str, np.ndarray], series_wis: dict[str, np.ndarray]) -> None:
    """Desenha os dois painéis e grava PDF (vetorial) e PNG (200 dpi)."""
    figura = plt.figure(figsize=(7.0, 3.3))
    # Posições manuais [esquerda, base, largura, altura]: deixam à direita de cada painel a
    # faixa dos rótulos diretos (o do painel (b) é mais longo: "régua climatológica").
    eixo_mae = figura.add_axes([0.075, 0.30, 0.31, 0.62])
    eixo_wis = figura.add_axes([0.545, 0.30, 0.285, 0.62])
    desenhar_painel_mae(eixo_mae, series_mae)
    desenhar_painel_wis(eixo_wis, series_wis)
    montar_legenda(figura)
    PASTA_DE_SAIDA.mkdir(parents=True, exist_ok=True)
    for extensao in ["pdf", "png"]:
        caminho_de_saida = PASTA_DE_SAIDA / f"{NOME_DA_FIGURA}.{extensao}"
        figura.savefig(caminho_de_saida, dpi=200)
        print(f"gravado: {caminho_de_saida}")
    plt.close(figura)


def main() -> None:
    series_mae = ler_series_de_mae()
    series_wis = ler_series_de_wis()
    conferir_ancoras(series_mae, series_wis)
    print("âncoras conferidas (MAE principal e régua sazonal, composto, WIS h=1)")
    gerar_figura(series_mae, series_wis)


if __name__ == "__main__":
    main()
