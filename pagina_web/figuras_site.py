"""

Desenha as figuras do painel a partir da tabela_final (a serie completa de
mosquito, clima e casos). Este script SO desenha; o gerar.py so copia os PNGs
que aparecem aqui dentro de pagina_web/imagens/.

Rode direto com:

    python3 figuras_site.py

Ele le a tabela_final.csv e grava os 3 PNGs em imagens/. Nao mexe em nenhum
dado de entrada (so leitura) nem na pasta docs/ (isso e trabalho do gerar.py).

"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Caminho da tabela unica que alimenta os modelos (so leitura, nunca gravacao).
PASTA_AQUI = Path(__file__).resolve().parent
CAMINHO_TABELA_FINAL = (
    PASTA_AQUI.parent
    / "modelagem_aedes"
    / "dados"
    / "entradas"
    / "tabela_modelagem"
    / "tabela_final.csv"
)
PASTA_IMAGENS = PASTA_AQUI / "imagens"

# Cores usadas nas duas fontes de mosquito, pra bater com o resto do site.
COR_SECRETARIA = "#3B78B0"
COR_RASPAGEM = "#D97B29"
COR_CASOS = "#C0392B"
COR_TREINO = "#D8DEE6"
COR_JANELA_PREVISTA = "#1E7A6E"

# A enchente de maio de 2024: as vistorias de armadilha pararam por 3 semanas
# (28/04, 05/05 e 12/05) por causa da cheia. Nao e falta de fonte, e um evento
# pontual que vale marcar nos graficos que mostram a serie inteira.
DATA_ENCHENTE = pd.Timestamp("2024-05-05")


# Le a tabela_final e devolve o DataFrame com a data ja em formato de data.
def carregar_tabela_final() -> pd.DataFrame:
    """

    Serve de entrada para as tres figuras. A tabela tem uma linha por semana
    epidemiologica, com a coluna 'fonte' dizendo se aquela semana veio da
    Secretaria Municipal de Saude (historico 2012-2025) ou da raspagem propria
    (2026 em diante). Semanas sem nenhuma fonte (fonte vazia) sao semanas sem
    vistoria registrada, incluindo as da enchente de maio de 2024.

    Returns:
        DataFrame com a coluna 'data_inicio_semana_epidemi' como data.

    """
    tabela = pd.read_csv(
        CAMINHO_TABELA_FINAL,
        parse_dates=["data_inicio_semana_epidemi"],
    )
    return tabela


# Desenha a serie semanal de mosquito, colorida por fonte, sem nenhum vao.
def desenhar_vetor_por_semana(tabela: pd.DataFrame) -> None:
    """

    Um grafico de linha so, cobrindo 2012 a 2026 inteiro: o trecho da
    Secretaria e o trecho da raspagem propria aparecem cada um na sua cor,
    ligados na mesma linha do tempo, sem area de "sem dado" no meio.

    Args:
        tabela: tabela_final ja carregada (ver carregar_tabela_final).

    """
    figura, eixo = plt.subplots(figsize=(14, 5))

    dados_secretaria = tabela[tabela["fonte"] == "secretaria"]
    dados_raspagem = tabela[tabela["fonte"] == "raspagem"]

    eixo.plot(
        dados_secretaria["data_inicio_semana_epidemi"],
        dados_secretaria["aedes_aegypti"],
        marker="o",
        markersize=2,
        linewidth=1,
        color=COR_SECRETARIA,
        label=f"secretaria ({len(dados_secretaria)} sem.)",
    )
    eixo.plot(
        dados_raspagem["data_inicio_semana_epidemi"],
        dados_raspagem["aedes_aegypti"],
        marker="o",
        markersize=2,
        linewidth=1,
        color=COR_RASPAGEM,
        label=f"raspagem propria ({len(dados_raspagem)} sem.)",
    )
    eixo.axvline(DATA_ENCHENTE, color="#B0574B", linestyle="--", linewidth=1, alpha=0.7)
    eixo.text(
        DATA_ENCHENTE,
        eixo.get_ylim()[1] * 0.95,
        " enchente mai/2024",
        color="#B0574B",
        fontsize=9,
        va="top",
    )

    eixo.set_title("Aedes aegypti capturados por semana - POA (serie continua 2012-2026)")
    eixo.set_xlabel("semana epidemiologica")
    eixo.set_ylabel("Aedes aegypti (soma na semana)")
    eixo.legend(loc="upper left")
    eixo.grid(alpha=0.3)

    figura.tight_layout()
    figura.savefig(PASTA_IMAGENS / "vetor_por_semana.png", dpi=150)
    plt.close(figura)


# Desenha o mosquito semanal contra os casos confirmados, em dois eixos.
def desenhar_vetor_vs_casos(tabela: pd.DataFrame) -> None:
    """

    Mostra o mosquito (barras, eixo esquerdo) e os casos confirmados de dengue
    (linha vermelha, eixo direito) na mesma semana. Com a serie completa, os
    surtos de 2024 e 2025 finalmente tem contagem de mosquito ao lado, o que
    antes nao existia (a base antiga so tinha mosquito ate 2023).

    Args:
        tabela: tabela_final ja carregada (ver carregar_tabela_final).

    """
    figura, eixo_vetor = plt.subplots(figsize=(14, 5))
    eixo_casos = eixo_vetor.twinx()

    eixo_vetor.bar(
        tabela["data_inicio_semana_epidemi"],
        tabela["aedes_aegypti"],
        width=5,
        color=COR_SECRETARIA,
        alpha=0.5,
        label="Aedes aegypti capturados",
    )
    eixo_casos.plot(
        tabela["data_inicio_semana_epidemi"],
        tabela["casos_confirmados"],
        color=COR_CASOS,
        linewidth=1.6,
        label="Casos confirmados de dengue",
    )

    eixo_vetor.set_title("Aedes aegypti capturados vs. casos confirmados de dengue - Porto Alegre")
    eixo_vetor.set_xlabel("semana epidemiologica")
    eixo_vetor.set_ylabel("Mosquitos capturados", color=COR_SECRETARIA)
    eixo_casos.set_ylabel("Casos confirmados de dengue", color=COR_CASOS)
    eixo_vetor.tick_params(axis="y", labelcolor=COR_SECRETARIA)
    eixo_casos.tick_params(axis="y", labelcolor=COR_CASOS)
    eixo_vetor.grid(alpha=0.3)

    linhas_vetor, rotulos_vetor = eixo_vetor.get_legend_handles_labels()
    linhas_casos, rotulos_casos = eixo_casos.get_legend_handles_labels()
    eixo_vetor.legend(linhas_vetor + linhas_casos, rotulos_vetor + rotulos_casos, loc="upper left")

    figura.tight_layout()
    figura.savefig(PASTA_IMAGENS / "vetor_vs_casos.png", dpi=150)
    plt.close(figura)


# Um corte de exemplo do walk-forward: onde ele comeca a prever e ate onde vai.
def _cortes_de_exemplo() -> list:
    """

    Lista fixa de datas de corte so para ILUSTRAR o walk-forward no grafico
    (o walk-forward real do experimento roda em toda semana da serie, nao so
    nestas). Espalhadas por 2020 a 2026, como pedido, ja que sao os anos onde
    da pra mostrar tanto cortes antigos quanto recentes na mesma figura.

    Returns:
        Lista de (rotulo, data_do_corte).

    """
    return [
        ("corte jan/20", pd.Timestamp("2020-01-15")),
        ("corte jan/21", pd.Timestamp("2021-01-15")),
        ("corte jan/22", pd.Timestamp("2022-01-15")),
        ("corte jan/23", pd.Timestamp("2023-01-15")),
        ("corte jan/24", pd.Timestamp("2024-01-15")),
        ("corte jan/25", pd.Timestamp("2025-01-15")),
        ("corte jan/26", pd.Timestamp("2026-01-15")),
        ("corte mar/26", pd.Timestamp("2026-03-15")),
    ]


# Desenha o diagrama do walk-forward: treino que expande + janela prevista.
def desenhar_walkforward() -> None:
    """

    Uma barra por corte de exemplo: o treino (cinza) sempre comeca no inicio
    da serie continua (2012) e cresce ate a data do corte; depois vem a janela
    de 12 semanas prevista (verde) e o proprio corte (tracinho vermelho). Sem
    area de "sem dado", porque a serie usada no treino agora e continua.

    """
    inicio_serie = pd.Timestamp("2012-09-23")
    semanas_previstas = 12
    cortes = _cortes_de_exemplo()

    figura, eixo = plt.subplots(figsize=(14, 6.5))

    for posicao, (rotulo, data_corte) in enumerate(cortes):
        fim_janela = data_corte + pd.Timedelta(weeks=semanas_previstas)
        eixo.barh(posicao, data_corte - inicio_serie, left=inicio_serie, height=0.55, color=COR_TREINO)
        eixo.barh(posicao, fim_janela - data_corte, left=data_corte, height=0.55, color=COR_JANELA_PREVISTA)
        eixo.plot([data_corte, data_corte], [posicao - 0.3, posicao + 0.3], color="#C0392B", linewidth=2.5)

    eixo.set_yticks(range(len(cortes)))
    eixo.set_yticklabels([rotulo for rotulo, _ in cortes])
    eixo.invert_yaxis()
    eixo.set_title(
        "Como treinamos e testamos - validacao walk-forward\n"
        "o modelo nunca ve o futuro que preve (serie continua 2012-2026)",
        fontsize=14,
        fontweight="bold",
        loc="left",
    )

    barra_treino = plt.Rectangle((0, 0), 1, 1, color=COR_TREINO)
    barra_janela = plt.Rectangle((0, 0), 1, 1, color=COR_JANELA_PREVISTA)
    linha_corte = plt.Line2D([0], [0], color="#C0392B", linewidth=2.5)
    eixo.legend(
        [barra_treino, barra_janela, linha_corte],
        [
            "Historico de treino (expande a cada corte)",
            f"Ate {semanas_previstas} semanas previstas -> comparadas com o real",
            'Corte = o que o modelo ve como "hoje"',
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=1,
        frameon=False,
    )

    figura.tight_layout()
    figura.savefig(PASTA_IMAGENS / "walkforward.png", dpi=150, bbox_inches="tight")
    plt.close(figura)


# Roda as tres figuras em sequencia e confirma que os arquivos foram gravados.
def main() -> None:
    """

    Ponto de entrada do script: carrega a tabela_final uma vez e desenha as
    tres figuras usadas no painel. Nao valida o PNG gerado (isso e feito
    separadamente, abrindo o arquivo com PIL, fora deste script).

    """
    tabela = carregar_tabela_final()
    desenhar_vetor_por_semana(tabela)
    desenhar_vetor_vs_casos(tabela)
    desenhar_walkforward()
    print("Figuras gravadas em", PASTA_IMAGENS)


if __name__ == "__main__":
    main()
