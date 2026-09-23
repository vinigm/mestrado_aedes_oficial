"""Figuras desenhadas especificamente para os slides.

A figura da página de dados empilha seis painéis num formato alto. Num slide
16:9 ela encolhe até ficar ilegível, então aqui as mesmas séries são
redesenhadas em formato **largo e baixo**, quebradas em duas figuras:

  1. vetor e casos — o par que sustenta a pergunta da pesquisa;
  2. clima e ENSO — o contexto que alimenta o modelo;
  3. o zoom de duas temporadas, com a subida de cada série marcada por seta —
     a figura que exemplifica a ordem em que as duas curvas sobem.

Uso:
    python3 figuras_slides.py

⚠️ Este módulo NÃO toca `pagina_web/figuras_site.py` nem as imagens dele. Ele
escreve só em `NOVO_HTML/saida/imagens/`.
"""

import dataclasses
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

# A cor das barras de mosquito na figura combinada. É a paleta do gerador
# antigo, repetida aqui de propósito: a figura anotada substitui a original no
# slide, e mudar a cor junto faria a troca parecer outro gráfico.
COR_VETOR_EM_BARRA = "#3B78B0"

# As temporadas em que a subida do vetor antecede a dos casos. Cada temporada
# vai de julho de um ano a junho do seguinte, porque o verão epidemiológico
# atravessa a virada do ano-calendário.
TEMPORADAS_ANOTADAS = (2022, 2023, 2024, 2025)

# O zoom mostra só estas temporadas. Duas bastam para o olho pegar o padrão, e
# a janela curta deixa cada seta grande o suficiente para ser vista do fundo
# da sala — que é o ponto do slide, já que a leitura aqui é visual e não
# quantitativa.
TEMPORADAS_DO_ZOOM = (2022, 2023)
MES_DE_INICIO_DA_TEMPORADA = 7

# A seta marca só o trecho central da rampa de subida, entre estas duas frações
# do pico da temporada. Começar em 0 faria a seta nascer no chão, onde a série
# ainda oscila por ruído; terminar em 1 cobriria o próprio pico.
# Antes de procurar a rampa, a série é suavizada por média móvel. A contagem
# de mosquito oscila muito de uma semana para a outra: na temporada 2023 ela
# sobe, cai pela metade e sobe de novo, e o trecho contíguo acima do limiar
# acaba começando colado no pico — a seta nasceria em cima do pico, dizendo o
# contrário do que o olho vê. A janela é centrada porque aqui a figura
# DESCREVE o passado; nada nela alimenta previsão.
#
# ⚠️ A suavização serve só para posicionar a seta. As séries desenhadas são
# as originais, sem nenhum tratamento.
SEMANAS_DA_SUAVIZACAO_DA_RAMPA = 5

FRACAO_DE_INICIO_DA_RAMPA = 0.35
FRACAO_DE_FIM_DA_RAMPA = 0.80

# Quanto a seta sobe acima da curva, em fração do topo do eixo, para não ficar
# escondida dentro das barras.
FOLGA_VERTICAL_DA_SETA = 0.03

# Curvatura da seta. Negativo inclina para a direita, acompanhando a subida.
CURVATURA_DA_SETA = -0.12

# Todas as setas têm o mesmo tamanho, medido em fração do eixo nos dois
# sentidos. Deixar cada seta crescer junto com a rampa que ela comenta faria o
# leitor comparar tamanhos, quando o que interessa comparar é só a POSIÇÃO
# horizontal: quem sobe antes.
#
# ⚠️ O comprimento horizontal é fração da JANELA, não um número de semanas:
# seis semanas somem numa figura de catorze anos e viram uma seta deitada numa
# figura de duas temporadas. Em fração, a seta tem o mesmo aspecto nas duas.
COMPRIMENTO_DA_SETA_EM_FRACAO_DA_LARGURA = 0.022
COMPRIMENTO_DA_SETA_EM_FRACAO_DA_ALTURA = 0.16

# Quanto o topo do eixo sobe antes das setas serem desenhadas. Sem essa folga,
# a seta de uma temporada cuja rampa começa colada no pico — 2023 no vetor —
# nasce acima do topo e simplesmente não aparece na figura.
FOLGA_DO_TOPO_PARA_AS_SETAS = 0.10


@dataclasses.dataclass(frozen=True)
class RampaDeSubida:
    """O trecho de subida de uma série dentro de uma temporada.

    Attributes:
        data_de_inicio: Semana em que a série cruza a fração inicial do pico.
        valor_de_inicio: O valor da série nessa semana.
        data_de_fim: Semana em que a série cruza a fração final do pico.
        valor_de_fim: O valor da série nessa semana.
    """

    data_de_inicio: pd.Timestamp
    valor_de_inicio: float
    data_de_fim: pd.Timestamp
    valor_de_fim: float


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


def _recortar_temporada(tabela: pd.DataFrame, ano_do_verao: int) -> pd.DataFrame:
    """Recorta a temporada epidemiológica que termina no ano informado.

    A temporada vai de julho do ano anterior a junho do ano informado, porque
    o verão de transmissão atravessa a virada do ano-calendário — recortar por
    ano civil partiria o mesmo surto em dois.

    Args:
        tabela: A tabela semanal completa.
        ano_do_verao: O ano em que o verão da temporada termina.

    Returns:
        As semanas da temporada, na ordem original.
    """
    datas = tabela["data_inicio_semana_epidemi"]
    inicio_da_temporada = pd.Timestamp(
        ano_do_verao - 1, MES_DE_INICIO_DA_TEMPORADA, 1
    )
    fim_da_temporada = pd.Timestamp(ano_do_verao, MES_DE_INICIO_DA_TEMPORADA, 1)

    dentro_da_temporada = (datas >= inicio_da_temporada) & (datas < fim_da_temporada)

    return tabela[dentro_da_temporada]


def _recuar_ate_cruzar_o_limiar(
    serie: pd.Series, posicao_do_pico: int, limiar: float
) -> int:
    """Anda do pico para trás enquanto a série se mantiver acima do limiar.

    Serve para achar onde a rampa de subida começa. O caminho é contíguo de
    propósito: parar no primeiro mergulho abaixo do limiar evita capturar um
    repique isolado de semanas antes como se fosse o início da mesma subida.

    Args:
        serie: A série da temporada, com índice reiniciado em zero.
        posicao_do_pico: A posição do valor máximo da temporada.
        limiar: O valor abaixo do qual a subida é considerada não iniciada.

    Returns:
        A posição mais antiga da rampa contígua acima do limiar.
    """
    posicao = posicao_do_pico

    while posicao > 0 and serie.iloc[posicao - 1] >= limiar:
        posicao -= 1

    return posicao


def localizar_rampa_de_subida(
    temporada: pd.DataFrame, nome_da_coluna: str
) -> RampaDeSubida:
    """Mede onde uma série começa e onde termina de subir numa temporada.

    A rampa é definida por dois pontos medidos, não escolhidos a olho: a semana
    em que a série cruza `FRACAO_DE_INICIO_DA_RAMPA` do pico da temporada e a
    semana em que cruza `FRACAO_DE_FIM_DA_RAMPA`. É sobre esse trecho que a
    seta da figura é desenhada.

    A busca acontece sobre a série suavizada por média móvel de
    `SEMANAS_DA_SUAVIZACAO_DA_RAMPA` semanas, e os valores devolvidos são os
    da série suavizada — o que faz a seta pousar na tendência, e não numa
    semana isolada que subiu ou caiu sozinha.

    Args:
        temporada: As semanas de uma temporada.
        nome_da_coluna: A série a medir.

    Returns:
        Os dois extremos da rampa, com data e valor.

    Raises:
        KeyError: Se a coluna não existir na tabela.
        ValueError: Se a temporada não tiver nenhuma semana com valor.
    """
    if nome_da_coluna not in temporada.columns:
        raise KeyError(f"Coluna ausente na tabela: {nome_da_coluna!r}")

    serie_original = temporada[nome_da_coluna].reset_index(drop=True)
    datas = temporada["data_inicio_semana_epidemi"].reset_index(drop=True)

    if serie_original.dropna().empty:
        raise ValueError(f"Temporada sem valor em {nome_da_coluna!r}.")

    serie = serie_original.rolling(
        SEMANAS_DA_SUAVIZACAO_DA_RAMPA, center=True, min_periods=1
    ).mean()

    posicao_do_pico = int(serie.idxmax())
    valor_do_pico = float(serie.iloc[posicao_do_pico])

    posicao_de_inicio = _recuar_ate_cruzar_o_limiar(
        serie, posicao_do_pico, valor_do_pico * FRACAO_DE_INICIO_DA_RAMPA
    )
    posicao_de_fim = _recuar_ate_cruzar_o_limiar(
        serie, posicao_do_pico, valor_do_pico * FRACAO_DE_FIM_DA_RAMPA
    )

    return RampaDeSubida(
        data_de_inicio=datas.iloc[posicao_de_inicio],
        valor_de_inicio=float(serie.iloc[posicao_de_inicio]),
        data_de_fim=datas.iloc[posicao_de_fim],
        valor_de_fim=float(serie.iloc[posicao_de_fim]),
    )


def _abrir_espaco_no_topo(eixo) -> None:
    """Sobe o teto do eixo para as setas caberem dentro da área desenhada.

    As setas são desenhadas acima da curva que comentam. Quando a rampa de uma
    temporada começa perto do pico, a seta nasceria fora da figura e sumiria
    sem aviso. Subir o teto resolve isso sem tocar em nenhum dado: as séries
    continuam desenhadas exatamente onde estavam, só sobra ar em cima.

    Args:
        eixo: O painel a ajustar.
    """
    base_do_eixo, topo_do_eixo = eixo.get_ylim()
    altura_atual = topo_do_eixo - base_do_eixo

    eixo.set_ylim(
        base_do_eixo, topo_do_eixo + altura_atual * FOLGA_DO_TOPO_PARA_AS_SETAS
    )


def _desenhar_seta_de_subida(eixo, rampa: RampaDeSubida, cor: str) -> None:
    """Desenha a seta curta que marca onde uma série começou a subir.

    A seta nasce na semana medida de início da rampa e tem tamanho fixo em
    relação à janela desenhada, igual para todas. O que ela comunica é a
    posição no tempo — em que semana aquela curva começou a subir — e não a
    intensidade da subida, que já está desenhada pela própria série.

    A base fica deslocada para cima em relação à curva, por uma fração do topo
    do eixo, para não se perder dentro das barras ou da linha que comenta.

    Args:
        eixo: O painel em que a série está desenhada — o eixo da esquerda para
            o mosquito, o da direita para os casos, já que a figura usa dois.
        rampa: Os extremos medidos da subida.
        cor: A cor da série comentada, para a seta se identificar sozinha.
    """
    topo_do_eixo = eixo.get_ylim()[1]
    folga = topo_do_eixo * FOLGA_VERTICAL_DA_SETA

    # O eixo do tempo é medido em dias do matplotlib, então a fração da janela
    # vira um deslocamento em dias antes de voltar a ser uma data.
    inicio_da_janela, fim_da_janela = eixo.get_xlim()
    largura_da_janela_em_dias = fim_da_janela - inicio_da_janela
    avanco_em_dias = (
        largura_da_janela_em_dias * COMPRIMENTO_DA_SETA_EM_FRACAO_DA_LARGURA
    )

    data_da_base = rampa.data_de_inicio
    altura_da_base = rampa.valor_de_inicio + folga

    data_da_ponta = data_da_base + pd.Timedelta(days=avanco_em_dias)
    altura_da_ponta = altura_da_base + (
        topo_do_eixo * COMPRIMENTO_DA_SETA_EM_FRACAO_DA_ALTURA
    )

    eixo.annotate(
        "",
        xy=(data_da_ponta, altura_da_ponta),
        xytext=(data_da_base, altura_da_base),
        arrowprops={
            "arrowstyle": "-|>,head_width=0.32,head_length=0.66",
            "color": cor,
            "linewidth": 2.6,
            "shrinkA": 0,
            "shrinkB": 0,
            "connectionstyle": f"arc3,rad={CURVATURA_DA_SETA}",
        },
    )


def desenhar_zoom_das_subidas(tabela: pd.DataFrame) -> pathlib.Path:
    """Amplia duas temporadas para mostrar a ordem em que as curvas sobem.

    É a versão de perto da figura completa: mesmas séries, mesmas cores, só
    que recortada em `TEMPORADAS_DO_ZOOM`. A pergunta que ela responde é
    visual — quem sobe primeiro — e não quantitativa, então a figura não traz
    número nenhum além dos eixos.

    ⚠️ As setas são leitura de gráfico. Elas dizem que a subida do vetor
    aparece antes, não quantas semanas antes com intervalo de confiança.

    Args:
        tabela: A tabela semanal.

    Returns:
        O caminho do arquivo gravado.

    Raises:
        ValueError: Se o recorte das temporadas do zoom ficar vazio.
    """
    primeiro_ano_do_zoom = min(TEMPORADAS_DO_ZOOM)
    ultimo_ano_do_zoom = max(TEMPORADAS_DO_ZOOM)

    inicio_do_zoom = pd.Timestamp(
        primeiro_ano_do_zoom - 1, MES_DE_INICIO_DA_TEMPORADA, 1
    )
    fim_do_zoom = pd.Timestamp(ultimo_ano_do_zoom, MES_DE_INICIO_DA_TEMPORADA, 1)

    datas_completas = tabela["data_inicio_semana_epidemi"]
    dentro_do_zoom = (datas_completas >= inicio_do_zoom) & (
        datas_completas < fim_do_zoom
    )
    recorte = tabela[dentro_do_zoom]

    if recorte.empty:
        raise ValueError(
            f"Nenhuma semana entre {inicio_do_zoom.date()} e {fim_do_zoom.date()}."
        )

    datas = recorte["data_inicio_semana_epidemi"]

    figura, eixo_do_vetor = plt.subplots(figsize=(LARGURA_DA_FIGURA, 4.4))
    eixo_dos_casos = eixo_do_vetor.twinx()

    eixo_do_vetor.bar(
        datas,
        recorte["aedes_aegypti"],
        width=5,
        color=COR_VETOR_EM_BARRA,
        alpha=0.5,
        label="Aedes aegypti capturados",
    )
    eixo_dos_casos.plot(
        datas,
        recorte["casos_confirmados"],
        color=COR_CASOS,
        linewidth=2.4,
        label="Casos confirmados de dengue",
    )

    eixo_do_vetor.set_ylabel(
        "Mosquitos capturados", color=COR_VETOR_EM_BARRA, fontsize=11
    )
    eixo_dos_casos.set_ylabel(
        "Casos confirmados de dengue", color=COR_CASOS, fontsize=11
    )
    eixo_do_vetor.tick_params(axis="y", labelcolor=COR_VETOR_EM_BARRA, labelsize=10)
    eixo_dos_casos.tick_params(axis="y", labelcolor=COR_CASOS, labelsize=10)
    eixo_do_vetor.tick_params(axis="x", labelsize=11, colors=COR_TEXTO)
    eixo_do_vetor.grid(True, color=COR_GRADE, linewidth=0.8)
    eixo_do_vetor.set_axisbelow(True)

    for lado in ("top",):
        eixo_do_vetor.spines[lado].set_visible(False)
        eixo_dos_casos.spines[lado].set_visible(False)

    _abrir_espaco_no_topo(eixo_do_vetor)
    _abrir_espaco_no_topo(eixo_dos_casos)

    for ano_do_verao in TEMPORADAS_DO_ZOOM:
        temporada = _recortar_temporada(tabela, ano_do_verao)

        rampa_do_vetor = localizar_rampa_de_subida(temporada, "aedes_aegypti")
        rampa_dos_casos = localizar_rampa_de_subida(temporada, "casos_confirmados")

        _desenhar_seta_de_subida(eixo_do_vetor, rampa_do_vetor, COR_VETOR_EM_BARRA)
        _desenhar_seta_de_subida(eixo_dos_casos, rampa_dos_casos, COR_CASOS)

    marcas_do_vetor, rotulos_do_vetor = eixo_do_vetor.get_legend_handles_labels()
    marcas_dos_casos, rotulos_dos_casos = eixo_dos_casos.get_legend_handles_labels()
    eixo_do_vetor.legend(
        marcas_do_vetor + marcas_dos_casos,
        rotulos_do_vetor + rotulos_dos_casos,
        loc="upper left",
        fontsize=11,
        framealpha=0.92,
    )

    figura.tight_layout()
    caminho = PASTA_DE_IMAGENS / "slide_zoom_das_subidas.png"
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

    caminhos_gerados = (
        desenhar_vetor_e_casos(tabela),
        desenhar_clima(tabela),
        desenhar_zoom_das_subidas(tabela),
    )

    for caminho in caminhos_gerados:
        print(f"  {caminho.name}")


if __name__ == "__main__":
    main()
