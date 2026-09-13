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
COR_CLIMA = "#6E8B5A"
COR_ENSO = "#8A7AA8"
COR_CRITICO = "#B0574B"
COR_ATENCAO = "#B07D33"

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


# Desenha o que existe para modelar: tres series alinhadas no mesmo eixo de tempo.
def _marcar_periodo_sem_dado(eixo, datas, primeira_data_com_dado, texto) -> None:
    """

    Sombreia o trecho em que a serie simplesmente nao existe, e escreve por que.

    Existe porque duas series do painel (casos e ENSO) so comecam em 2018,
    enquanto mosquito e clima cobrem os 14 anos. Sem a marcacao, o grafico
    sugeriria que nao houve dengue nem El Nino antes de 2018 - o que e falso:
    o que falta e a CAPTURA do dado, nao o fenomeno.

    Args:
        eixo: O painel a marcar.
        datas: A coluna de datas da tabela_final.
        primeira_data_com_dado: Onde a serie de fato comeca.
        texto: A explicacao curta escrita dentro da area sombreada.

    """
    eixo.axvspan(datas.min(), primeira_data_com_dado,
                 color=COR_TREINO, alpha=0.55, zorder=0)
    limite_inferior, limite_superior = eixo.get_ylim()
    altura_do_texto = limite_inferior + (limite_superior - limite_inferior) * 0.62
    eixo.text(datas.min() + pd.Timedelta(days=120), altura_do_texto, texto,
              fontsize=8.5, color="#6b6b6b", va="center")


def _titular_painel(eixo, titulo, rotulo_do_eixo_y) -> None:
    """

    Poe o titulo alinhado a esquerda em cima do painel, no lugar de confiar so
    no rotulo vertical do eixo.

    O rotulo vertical sozinho obriga quem le a virar a cabeca e nao tem espaco
    para a unidade nem para a ressalva. Numa figura projetada em reuniao, o
    titulo horizontal e o que se le primeiro.

    Args:
        eixo: O painel.
        titulo: A frase curta que aparece acima do painel.
        rotulo_do_eixo_y: O nome da grandeza, em duas linhas, no eixo vertical.

    """
    eixo.set_title(titulo, fontsize=10, loc="left", pad=6, color="#2b2b2b")
    eixo.set_ylabel(rotulo_do_eixo_y, fontsize=8.5)


def desenhar_series_para_modelar(tabela: pd.DataFrame) -> None:
    """

    Mostra TUDO que existe para modelar, painel a painel, no mesmo eixo de tempo.

    Eixo compartilhado de proposito: e o que deixa ver, sem esforco, que o
    mosquito e o clima cobrem 14 anos enquanto os casos so existem de 2018 -
    e que so 2022 em diante ha epidemia de verdade. E essa defasagem que limita
    a janela util de qualquer modelo que cruze as tres coisas.

    Os seis paineis, e por que cada um esta aqui:

      1. VETOR - a densidade (femeas por armadilha inspecionada), nao a contagem
         bruta: e a variavel que o modelo usa. Contagem bruta subiria e desceria
         junto com o numero de armadilhas instaladas.
      2. CASOS - o alvo do modelo, decidido por medicao em 30/08/2026.
      3. CHUVA - o pico de 281,8 mm cai exatamente na enchente de mai/2024 e
         explica, sozinho, a interrupcao da vistoria que aparece no painel 1.
      4. TEMPERATURA - o unico clima que o painel mostrava antes desta versao.
      5. UMIDADE - entra porque sobrevivencia do mosquito adulto depende dela.
      6. ENSO - a unica familia de features novas que passou no teste de 30/08.

    ATENCAO AO QUE A FIGURA NAO DIZ. Os paineis estao empilhados no mesmo tempo
    para comparacao VISUAL; nenhum deles afirma correlacao testada. A
    configuracao de referencia usa k=6 colunas de clima escolhidas
    automaticamente, e nao as 22 que existem na tabela.

    Args:
        tabela: A tabela_final, uma linha por semana.

    """
    datas = tabela["data_inicio_semana_epidemi"]
    figura, eixos = plt.subplots(
        6, 1, figsize=(15.5, 11.2), sharex=True,
        gridspec_kw={"height_ratios": [1.35, 1.35, 0.82, 0.82, 0.82, 0.82],
                     "hspace": 0.55},
    )

    # --- 1. densidade do vetor (o protagonista entomologico) ---
    eixos[0].fill_between(datas, tabela["aedes_aegypti_por_armadilha"],
                          color=COR_SECRETARIA, alpha=0.28, linewidth=0)
    eixos[0].plot(datas, tabela["aedes_aegypti_por_armadilha"],
                  color=COR_SECRETARIA, linewidth=1.0)
    _titular_painel(eixos[0], "Vetor — densidade de Aedes aegypti (o que a armadilha mede)",
                    "femeas por\narmadilha")

    # --- 2. casos confirmados (o alvo) ---
    eixos[1].fill_between(datas, tabela["casos_confirmados"],
                          color=COR_CASOS, alpha=0.25, linewidth=0)
    eixos[1].plot(datas, tabela["casos_confirmados"], color=COR_CASOS, linewidth=1.1)
    _titular_painel(eixos[1], "Casos confirmados de dengue (o alvo do modelo)",
                    "casos\nconfirmados")
    primeira_semana_com_caso = tabela.loc[tabela["casos_confirmados"].notna(),
                                          "data_inicio_semana_epidemi"].min()
    _marcar_periodo_sem_dado(eixos[1], datas, primeira_semana_com_caso,
                             "sem serie de casos\nantes de 2018")

    # --- 3. chuva (em barras: e total acumulado da semana, nao trajetoria) ---
    eixos[2].bar(datas, tabela["precip_total_mm"], width=6,
                 color=COR_CLIMA, alpha=0.65, linewidth=0)
    _titular_painel(eixos[2], "Chuva — total da semana (o pico de 281,8 mm e a enchente)",
                    "precipitacao\n(mm/semana)")

    # --- 4. temperatura ---
    eixos[3].plot(datas, tabela["temp_media"], color=COR_CLIMA, linewidth=0.9)
    _titular_painel(eixos[3], "Temperatura media", "temperatura\nmedia (C)")

    # --- 5. umidade ---
    eixos[4].plot(datas, tabela["umid_media"], color=COR_CLIMA, linewidth=0.9)
    _titular_painel(eixos[4], "Umidade relativa media", "umidade\nmedia (%)")

    # --- 6. ENSO (so 2018+, e a figura precisa dizer isso) ---
    eixos[5].axhline(0, color="#9a9a9a", linewidth=0.7, linestyle=":", zorder=0)
    eixos[5].plot(datas, tabela["oni"], color=COR_ENSO, linewidth=1.1)
    _titular_painel(eixos[5], "ENSO — indice ONI (El Nino e La Nina)", "indice\nONI")
    primeira_semana_com_enso = tabela.loc[tabela["oni"].notna(),
                                          "data_inicio_semana_epidemi"].min()
    _marcar_periodo_sem_dado(eixos[5], datas, primeira_semana_com_enso,
                             "sem captura de ENSO\nantes de 2018")
    eixos[5].set_xlabel("semana epidemiologica", fontsize=9)

    # A enchente de maio/2024 atravessa os seis paineis: foi evento real, nao
    # falha de coleta, e aparece como buraco na serie de vistoria do painel 1.
    for eixo in eixos:
        eixo.axvline(DATA_ENCHENTE, color=COR_CRITICO, linestyle="--",
                     linewidth=1.1, alpha=0.75, zorder=1)
        eixo.grid(alpha=0.25)
        eixo.set_axisbelow(True)
        for lado in ("top", "right"):
            eixo.spines[lado].set_visible(False)

    eixos[0].text(DATA_ENCHENTE + pd.Timedelta(days=40),
                  tabela["aedes_aegypti_por_armadilha"].max() * 0.88,
                  "enchente\nmai/2024", fontsize=8.5, color=COR_CRITICO)

    figura.subplots_adjust(left=0.055, right=0.995, top=0.965, bottom=0.045)
    figura.savefig(PASTA_IMAGENS / "series_para_modelar.png", dpi=150)
    plt.close(figura)


# Desenha o que a armadilha captura alem do Aedes aegypti, e o esforco de coleta.
def desenhar_riqueza_da_armadilha(tabela: pd.DataFrame) -> None:
    """

    Mostra os tres taxons que a armadilha captura e o esforco de coleta por tras.

    Por que esta figura existe: a armadilha do MI-Aedes conta TRES taxons e o
    projeto modela um. O Culex aparece em 717 das 718 semanas, com 159.683
    individuos contra 237.450 do Aedes aegypti - quase o mesmo volume.

    O CULEX NAO TRANSMITE DENGUE. Ele nao entra como preditor de caso; entra
    como contexto de captura. Se numa semana o Culex sobe e o Aegypti nao, isso
    separa "havia mais mosquito" de "a vistoria foi mais intensa naquela semana".

    O painel de baixo e o motivo de o modelo usar densidade e nao contagem: o
    numero de armadilhas ativas foi de 14 a 1.436 por semana ao longo da serie.
    Contagem bruta sobe e desce junto com esse numero, sem que a infestacao
    tenha mudado.

    A escala do painel de cima e logaritmica porque os tres taxons diferem em
    ordens de grandeza; em escala linear o albopictus vira uma linha colada no
    zero. Soma-se 1 antes do log para nao perder as semanas de contagem zero.

    Args:
        tabela: A tabela_final, uma linha por semana.

    """
    datas = tabela["data_inicio_semana_epidemi"]
    figura, eixos = plt.subplots(
        2, 1, figsize=(15.5, 6.4), sharex=True,
        gridspec_kw={"height_ratios": [1.5, 1.0], "hspace": 0.42},
    )

    taxons_desenhados = [
        ("aedes_aegypti", "Aedes aegypti — vetor da dengue", COR_SECRETARIA, "-", 1.1),
        ("aedes_albopictus", "Aedes albopictus — vetor secundario", COR_ENSO, "-", 0.9),
        ("culex_sp", "Culex sp. — NAO transmite dengue (contexto de captura)",
         "#9A9384", "--", 0.9),
    ]
    for coluna, rotulo, cor, estilo, espessura in taxons_desenhados:
        eixos[0].plot(datas, tabela[coluna] + 1, color=cor, linestyle=estilo,
                      linewidth=espessura, label=rotulo)
    eixos[0].set_yscale("log")
    _titular_painel(eixos[0], "A armadilha captura tres taxons — o projeto modela um",
                    "individuos por semana\n(escala log, +1)")
    eixos[0].legend(fontsize=8.5, frameon=False, ncol=3, loc="upper left")

    eixos[1].fill_between(datas, tabela["numero_de_armadilhas"],
                          color=COR_ATENCAO, alpha=0.30, linewidth=0)
    eixos[1].plot(datas, tabela["numero_de_armadilhas"], color=COR_ATENCAO,
                  linewidth=0.9)
    _titular_painel(eixos[1],
                    "Esforco de coleta — de 14 a 1.436 armadilhas por semana "
                    "(por isso o modelo usa densidade, nao contagem)",
                    "armadilhas\nativas")
    eixos[1].set_xlabel("semana epidemiologica", fontsize=9)

    for eixo in eixos:
        eixo.axvline(DATA_ENCHENTE, color=COR_CRITICO, linestyle="--",
                     linewidth=1.1, alpha=0.75, zorder=1)
        eixo.grid(alpha=0.25)
        eixo.set_axisbelow(True)
        for lado in ("top", "right"):
            eixo.spines[lado].set_visible(False)

    figura.subplots_adjust(left=0.055, right=0.995, top=0.93, bottom=0.085)
    figura.savefig(PASTA_IMAGENS / "riqueza_da_armadilha.png", dpi=150)
    plt.close(figura)


# Desenha o ciclo anual: todos os anos sobrepostos na mesma escala de semana.
def desenhar_ciclo_anual(tabela: pd.DataFrame) -> None:
    """

    Sobrepoe os anos numa unica escala de semana do ano, para mostrar que a
    dengue em Porto Alegre liga e desliga sempre na mesma epoca.

    E o que justifica o modelo receber a posicao da semana no calendario como
    variavel, e tambem o que explica por que a climatologia sozinha nao basta:
    a FORMA se repete todo ano, mas a ALTURA muda em ordens de grandeza -
    de 489 casos em 2019 a 24.793 em 2025.

    A escala do eixo vertical e logaritmica justamente por isso: em escala
    linear, os anos de poucos casos viram uma linha reta colada no zero.

    Args:
        tabela: A tabela_final, uma linha por semana.

    """
    trabalho = tabela.dropna(subset=["casos_confirmados"]).copy()
    trabalho["ano"] = trabalho["data_inicio_semana_epidemi"].dt.year
    trabalho["semana_do_ano"] = (
        trabalho["data_inicio_semana_epidemi"].dt.isocalendar().week.astype(int)
    )

    # So os anos com epidemia de verdade; os demais poluiriam sem informar.
    totais_por_ano = trabalho.groupby("ano")["casos_confirmados"].sum()
    anos_relevantes = sorted(totais_por_ano[totais_por_ano > 300].index)

    figura, eixo = plt.subplots(figsize=(15.5, 4.6))
    tons = [COR_TREINO, "#9FB8D0", COR_SECRETARIA, COR_ATENCAO, COR_CASOS]

    for posicao, ano in enumerate(anos_relevantes):
        do_ano = trabalho[trabalho["ano"] == ano].sort_values("semana_do_ano")
        total = int(totais_por_ano[ano])
        eixo.plot(do_ano["semana_do_ano"], do_ano["casos_confirmados"].clip(lower=0.5),
                  label=f"{ano} ({total:,} casos)".replace(",", "."),
                  color=tons[posicao % len(tons)],
                  linewidth=2.4 if ano >= 2024 else 1.4,
                  alpha=1.0 if ano >= 2024 else 0.8)

    eixo.set_yscale("log")
    eixo.set_xlabel("semana do ano", fontsize=9)
    eixo.set_ylabel("casos confirmados (escala log)", fontsize=9)
    eixo.set_title("O ciclo se repete; a altura muda em ordens de grandeza",
                   fontsize=12, pad=12)
    eixo.set_xlim(1, 52)
    eixo.legend(fontsize=8.5, frameon=False, ncol=2, loc="upper right")
    eixo.grid(alpha=0.25)
    eixo.set_axisbelow(True)
    for lado in ("top", "right"):
        eixo.spines[lado].set_visible(False)

    figura.tight_layout()
    figura.savefig(PASTA_IMAGENS / "ciclo_anual.png", dpi=150)
    plt.close(figura)


# Desenha a cobertura de cada fonte de dados ao longo do tempo.
def desenhar_cobertura_fontes(tabela: pd.DataFrame) -> None:
    """

    Mostra, numa linha do tempo, de quando ate quando cada fonte tem dado.

    Cada faixa horizontal e uma fonte. O trecho colorido marca as semanas com
    dado; os buracos aparecem como falhas na faixa. E o jeito de enxergar de
    uma vez que o mosquito cobre 14 anos, o clima passou a cobrir o mesmo
    periodo depois da recaptura, e os casos so existem de 2018 em diante - que
    e o que limita a janela util de qualquer modelo que cruze as tres coisas.

    Args:
        tabela: A tabela_final, uma linha por semana.

    """
    faixas = [
        ("Mosquito (armadilhas)", "aedes_aegypti_por_armadilha", COR_SECRETARIA),
        ("Clima (NASA POWER)", "temp_media", COR_CLIMA),
        ("Casos confirmados (SINAN)", "casos_confirmados", COR_CASOS),
        ("El Nino / La Nina (NOAA)", "oni", COR_ENSO),
    ]

    figura, eixo = plt.subplots(figsize=(11, 3.4))
    datas = tabela["data_inicio_semana_epidemi"]

    for posicao, (rotulo, coluna, cor) in enumerate(faixas):
        tem_dado = tabela[coluna].notna()
        altura = len(faixas) - posicao

        # Fundo cinza: a extensao total possivel, para o buraco ficar visivel.
        eixo.barh(altura, datas.max() - datas.min(), left=datas.min(),
                  height=0.55, color=COR_TREINO, zorder=1)

        # Cada semana com dado vira um tracinho; semanas sem dado deixam falha.
        eixo.barh([altura] * int(tem_dado.sum()), pd.Timedelta(days=7),
                  left=datas[tem_dado], height=0.55, color=cor, zorder=2)

        total = int(tem_dado.sum())
        eixo.text(datas.max() + pd.Timedelta(days=60), altura,
                  f"{total} sem.", va="center", ha="left", fontsize=9,
                  color=cor, fontweight="bold")

    eixo.set_yticks(range(1, len(faixas) + 1))
    eixo.set_yticklabels([rotulo for rotulo, _, _ in reversed(faixas)], fontsize=9)
    eixo.set_xlim(datas.min() - pd.Timedelta(days=60),
                  datas.max() + pd.Timedelta(days=420))
    eixo.set_ylim(0.4, len(faixas) + 0.6)
    eixo.set_title("Cobertura de cada fonte, semana a semana", fontsize=11, pad=10)
    eixo.grid(axis="x", alpha=0.3)
    eixo.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        eixo.spines[lado].set_visible(False)

    figura.tight_layout()
    figura.savefig(PASTA_IMAGENS / "cobertura_fontes.png", dpi=150)
    plt.close(figura)


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
    desenhar_cobertura_fontes(tabela)
    desenhar_series_para_modelar(tabela)
    desenhar_riqueza_da_armadilha(tabela)
    desenhar_ciclo_anual(tabela)
    desenhar_vetor_por_semana(tabela)
    desenhar_vetor_vs_casos(tabela)
    desenhar_walkforward()
    print("Figuras gravadas em", PASTA_IMAGENS)


if __name__ == "__main__":
    main()
