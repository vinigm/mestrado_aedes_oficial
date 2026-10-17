"""Gera a Figura 1 do artigo e a Figura S1 do material suplementar (versões DEFINITIVAS, pelo pacote).

O que mostra:
    Figura 1: três painéis empilhados com o mesmo eixo de tempo, de fev/2018 a fev/2026: casos confirmados de dengue por
        semana, fêmeas de Aedes aegypti por vistoria (MI-Aedes) e temperatura média semanal (NASA POWER). A faixa cinza
        marca o período de avaliação (07/01/2024 a 01/02/2026).
    Figura S1: as quatro variáveis meteorológicas de base (temperatura média, temperatura máxima, umidade relativa média
        e pressão média), no mesmo período e com a mesma faixa.

De onde lê: `dados/tabela_final.csv` (sha256 e esquema conferidos por `aedes.dados`), com o corte de maturidade
aplicado uma vez, como em todo o pacote. O período do gráfico e a faixa da avaliação vêm de `aedes.configuracao`
(nada de datas de memória): o gráfico começa na primeira semana com caso e termina na última semana-alvo avaliada
(01/02/2026); a faixa vai da primeira à última semana-alvo avaliada.

Forma (skill de visualização, mesma da versão preliminar de 10/10/2026): medidas em escalas diferentes viram pequenos
múltiplos empilhados com o mesmo eixo de tempo, nunca dois eixos y. Uma série por painel, então o título do painel
nomeia a série e não há legenda. Buracos no dado do vetor (21/08/2022 e as três semanas da enchente de 2024) ficam
visíveis, sem interpolação. Regra do Vinicius (10/10/2026): em série temporal empilhada, os ANOS aparecem no eixo x de
CADA painel.

Saída: PDF e PNG em `figuras/` e uma cópia dos PDFs em `entregas/artigo/figuras/` (as preliminares ficam intactas).

Este script não importa nenhum código antigo (`modelagem_aedes`, `analises/`); o gabarito de desenho foi apenas lido.

Rodar, de qualquer pasta:
    PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B figuras/gerar_figura1.py
"""

import dataclasses
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402  (o backend precisa ser escolhido antes)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402

PASTA_DO_PACOTE = Path(__file__).resolve().parents[1]
# O script e rodado pelo caminho do arquivo; sem isto o pacote `aedes` nao seria encontrado.
sys.path.insert(0, str(PASTA_DO_PACOTE))

from aedes.configuracao import (  # noqa: E402
    CONFIGURACAO_AVALIACAO,
    CONFIGURACAO_DADOS,
    CONFIGURACAO_VARIAVEIS,
)
from aedes.dados import (  # noqa: E402
    aplicar_corte_de_maturidade,
    montar_tabela_a_partir_dos_bytes,
)

# ----------------------------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------------------------
ARQUIVO_DA_TABELA = PASTA_DO_PACOTE / "dados" / "tabela_final.csv"
PASTA_DAS_FIGURAS = PASTA_DO_PACOTE / "figuras"
PASTA_DO_PESQUISA = PASTA_DO_PACOTE.parents[1]
PASTA_DAS_FIGURAS_DO_ARTIGO = PASTA_DO_PESQUISA / "entregas" / "artigo" / "figuras"

# ----------------------------------------------------------------------------------------------
# Ancoras (calculadas antes; se divergirem, o script PARA e nao forca nada)
# ----------------------------------------------------------------------------------------------
SEMANAS_ESPERADAS_NO_GRAFICO = 416
PRIMEIRA_SEMANA_ESPERADA_NO_GRAFICO = pd.Timestamp("2018-02-18")
ULTIMA_SEMANA_ESPERADA_NO_GRAFICO = pd.Timestamp("2026-02-01")
INICIO_ESPERADO_DA_FAIXA_DA_AVALIACAO = pd.Timestamp("2024-01-07")

# ----------------------------------------------------------------------------------------------
# Desenho (herdado do gabarito da figura preliminar)
# ----------------------------------------------------------------------------------------------
# Paleta de referencia da skill de visualizacao (slots 1 a 3, validados para pequenos multiplos).
COR_CASOS = "#2a78d6"
COR_VETOR = "#eb6834"
COR_TEMPERATURA = "#1baf7a"
COR_TEXTO_PRIMARIO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_GRADE = "#e4e3df"
COR_SOMBRA_AVALIACAO = "#efeeea"

LARGURA_EM_POLEGADAS = 7.0
ALTURA_DA_FIGURA_1_EM_POLEGADAS = 6.2
ALTURA_DA_FIGURA_S1_EM_POLEGADAS = 7.6
RESOLUCAO_DO_PNG = 200

# Eventos de referencia da Figura 1 (pedido do Vinicius, 17/10/2026): linhas verticais em todos os paineis, rotulo so no de cima.
DATA_DA_DECLARACAO_DE_PANDEMIA = pd.Timestamp("2020-03-11")  # OMS declara a pandemia de COVID-19
DATA_DA_ENCHENTE_EM_PORTO_ALEGRE = pd.Timestamp("2024-05-05")
ROTULO_DA_PANDEMIA = "pandemia"
ROTULO_DA_ENCHENTE = "enchente"
COR_LINHA_DE_EVENTO = "#8c8b87"  # cinza medio, discreto
ESPESSURA_LINHA_DE_EVENTO = 0.8
TRACEJADO_LINHA_DE_EVENTO = (0, (4, 3))
TAMANHO_ROTULO_DE_EVENTO = 7.5
POSICAO_Y_ROTULO_DE_EVENTO = 0.97  # fracao da altura do painel (coordenada do eixo), junto ao topo
AFASTAMENTO_X_ROTULO_DE_EVENTO_EM_DIAS = 12


@dataclasses.dataclass(frozen=True)
class EventoDeReferencia:
    """Marco temporal desenhado como linha vertical: data e rótulo curto (o rótulo só aparece no painel de cima)."""

    data: pd.Timestamp
    rotulo: str


EVENTOS_DE_REFERENCIA = (
    EventoDeReferencia(data=DATA_DA_DECLARACAO_DE_PANDEMIA, rotulo=ROTULO_DA_PANDEMIA),
    EventoDeReferencia(data=DATA_DA_ENCHENTE_EM_PORTO_ALEGRE, rotulo=ROTULO_DA_ENCHENTE),
)


@dataclasses.dataclass(frozen=True)
class Painel:
    """Um painel de série temporal: coluna da tabela, título, unidade do eixo y e cor.

    Attributes:
        coluna: Coluna da `tabela_final.csv` desenhada.
        titulo: Título à esquerda, acima do painel (nomeia a série; não há legenda).
        unidade: Rótulo do eixo y.
        cor: Cor da linha.
    """

    coluna: str
    titulo: str
    unidade: str
    cor: str


@dataclasses.dataclass(frozen=True)
class Figura:
    """Uma figura: nome do arquivo (sem extensão), painéis de cima para baixo e altura."""

    nome_do_arquivo: str
    paineis: tuple[Painel, ...]
    altura_em_polegadas: float
    com_eventos_de_referencia: bool = False


def montar_painel_dos_casos() -> Painel:
    """Painel dos casos confirmados (coluna de casos da configuração de dados)."""
    return Painel(
        coluna=CONFIGURACAO_DADOS.coluna_de_casos,
        titulo="Casos confirmados de dengue por semana",
        unidade="casos",
        cor=COR_CASOS,
    )


def montar_painel_do_vetor() -> Painel:
    """Painel das fêmeas por vistoria (coluna do vetor da configuração de variáveis)."""
    return Painel(
        coluna=CONFIGURACAO_VARIAVEIS.coluna_do_vetor,
        titulo=r"Fêmeas de $\it{Aedes\ aegypti}$ por vistoria (MI-Aedes)",
        unidade="fêmeas/vistoria",
        cor=COR_VETOR,
    )


def montar_paineis_do_clima() -> tuple[Painel, ...]:
    """Painéis das quatro colunas de clima de base, na ordem de leitura do artigo.

    Os títulos são rótulos de apresentação; as COLUNAS vêm da configuração (as de origem das 6 variáveis congeladas).

    Raises:
        KeyError: Se a configuração usar uma coluna de clima sem título definido aqui.
        RuntimeError: Se a configuração não tiver exatamente as 4 colunas de base esperadas.
    """
    titulo_e_unidade_por_coluna = {
        "temp_media": ("Temperatura média semanal", "°C"),
        "temp_max": ("Temperatura máxima da semana", "°C"),
        "umid_media": ("Umidade relativa média semanal", "%"),
        "pressao_media": ("Pressão média semanal na superfície", "kPa"),
    }

    colunas_de_clima_da_configuracao = set()
    for variavel in CONFIGURACAO_VARIAVEIS.variaveis_de_clima:
        colunas_de_clima_da_configuracao.add(variavel.coluna_de_origem)

    colunas_sem_titulo = colunas_de_clima_da_configuracao.difference(titulo_e_unidade_por_coluna)
    if colunas_sem_titulo:
        raise KeyError(f"Colunas de clima sem título na figura S1: {sorted(colunas_sem_titulo)}")
    if len(colunas_de_clima_da_configuracao) != 4:
        raise RuntimeError(
            f"Esperadas 4 colunas de clima de base, a configuração tem {sorted(colunas_de_clima_da_configuracao)}."
        )

    paineis: list[Painel] = []
    for coluna, (titulo, unidade) in titulo_e_unidade_por_coluna.items():
        if coluna in colunas_de_clima_da_configuracao:
            paineis.append(Painel(coluna=coluna, titulo=titulo, unidade=unidade, cor=COR_TEMPERATURA))
    return tuple(paineis)


def montar_figuras() -> tuple[Figura, ...]:
    """Define a Figura 1 (casos, vetor, temperatura média) e a Figura S1 (as 4 variáveis de clima)."""
    painel_da_temperatura_media = Painel(
        coluna="temp_media",
        titulo="Temperatura média semanal (NASA POWER)",
        unidade="°C",
        cor=COR_TEMPERATURA,
    )
    figura_1 = Figura(
        nome_do_arquivo="figura1_series",
        paineis=(montar_painel_dos_casos(), montar_painel_do_vetor(), painel_da_temperatura_media),
        altura_em_polegadas=ALTURA_DA_FIGURA_1_EM_POLEGADAS,
        com_eventos_de_referencia=True,
    )
    figura_s1 = Figura(
        nome_do_arquivo="figuraS1_clima",
        paineis=montar_paineis_do_clima(),
        altura_em_polegadas=ALTURA_DA_FIGURA_S1_EM_POLEGADAS,
    )
    return (figura_1, figura_s1)


def carregar_tabela_do_grafico() -> pd.DataFrame:
    """Lê a tabela certificada, aplica o corte de maturidade e recorta o período do gráfico.

    O período vai da primeira semana com caso até a última semana-alvo avaliada (`aedes.configuracao`).

    Returns:
        As semanas do gráfico (416), na ordem cronológica.

    Raises:
        ValueError: Se o sha256 ou o esquema divergirem do snapshot certificado.
        RuntimeError: Se o período ou o número de semanas divergirem das âncoras.
    """
    conteudo_em_bytes = ARQUIVO_DA_TABELA.read_bytes()
    tabela_crua = montar_tabela_a_partir_dos_bytes(conteudo_em_bytes, CONFIGURACAO_DADOS)
    tabela_cortada = aplicar_corte_de_maturidade(tabela_crua, CONFIGURACAO_DADOS)

    coluna_de_data = CONFIGURACAO_DADOS.coluna_de_data
    coluna_de_casos = CONFIGURACAO_DADOS.coluna_de_casos
    semanas_com_caso = tabela_cortada.dropna(subset=[coluna_de_casos])
    inicio_do_grafico = semanas_com_caso[coluna_de_data].min()
    fim_do_grafico = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada

    datas = tabela_cortada[coluna_de_data]
    no_periodo_do_grafico = datas.between(inicio_do_grafico, fim_do_grafico)
    tabela_do_grafico = tabela_cortada[no_periodo_do_grafico]

    divergencias = []
    if inicio_do_grafico != PRIMEIRA_SEMANA_ESPERADA_NO_GRAFICO:
        divergencias.append(f"início {inicio_do_grafico.date()} != {PRIMEIRA_SEMANA_ESPERADA_NO_GRAFICO.date()}")
    if fim_do_grafico != ULTIMA_SEMANA_ESPERADA_NO_GRAFICO:
        divergencias.append(f"fim {fim_do_grafico.date()} != {ULTIMA_SEMANA_ESPERADA_NO_GRAFICO.date()}")
    if len(tabela_do_grafico) != SEMANAS_ESPERADAS_NO_GRAFICO:
        divergencias.append(f"{len(tabela_do_grafico)} semanas != {SEMANAS_ESPERADAS_NO_GRAFICO}")
    primeira_data_da_faixa = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    if primeira_data_da_faixa != INICIO_ESPERADO_DA_FAIXA_DA_AVALIACAO:
        divergencias.append(
            f"faixa começa em {primeira_data_da_faixa.date()} != {INICIO_ESPERADO_DA_FAIXA_DA_AVALIACAO.date()}"
        )
    if divergencias:
        raise RuntimeError("A configuração ou os dados divergem das âncoras da figura: " + "; ".join(divergencias))

    return tabela_do_grafico


def desenhar_painel(eixo: Axes, tabela: pd.DataFrame, painel: Painel) -> None:
    """Desenha uma série com a faixa da avaliação ao fundo; semana sem dado fica como buraco (sem interpolar)."""
    coluna_de_data = CONFIGURACAO_DADOS.coluna_de_data
    inicio_da_faixa = CONFIGURACAO_AVALIACAO.primeira_data_alvo_avaliada
    fim_da_faixa = CONFIGURACAO_AVALIACAO.ultima_data_alvo_avaliada

    eixo.axvspan(inicio_da_faixa, fim_da_faixa, color=COR_SOMBRA_AVALIACAO, zorder=0, linewidth=0)
    eixo.plot(tabela[coluna_de_data], tabela[painel.coluna], color=painel.cor, linewidth=1.2, zorder=2)
    eixo.set_title(painel.titulo, loc="left", fontsize=9.5, color=COR_TEXTO_PRIMARIO, pad=4)
    eixo.set_ylabel(painel.unidade, fontsize=8.5, color=COR_TEXTO_SECUNDARIO)
    eixo.grid(axis="y", color=COR_GRADE, linewidth=0.6)
    eixo.tick_params(colors=COR_TEXTO_SECUNDARIO, labelsize=8, length=0)
    for lado in ["top", "right", "left"]:
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(COR_GRADE)


def desenhar_eventos_de_referencia(eixo: Axes, eventos: tuple[EventoDeReferencia, ...], com_rotulo: bool) -> None:
    """Desenha uma linha vertical por evento, atrás das séries; o rótulo (opcional) fica junto ao topo, à direita da linha."""
    afastamento_do_rotulo = pd.Timedelta(days=AFASTAMENTO_X_ROTULO_DE_EVENTO_EM_DIAS)
    for evento in eventos:
        eixo.axvline(
            evento.data,
            color=COR_LINHA_DE_EVENTO,
            linewidth=ESPESSURA_LINHA_DE_EVENTO,
            linestyle=TRACEJADO_LINHA_DE_EVENTO,
            zorder=1,
        )
        if com_rotulo:
            eixo.text(
                evento.data + afastamento_do_rotulo,
                POSICAO_Y_ROTULO_DE_EVENTO,
                evento.rotulo,
                transform=eixo.get_xaxis_transform(),
                ha="left",
                va="top",
                fontsize=TAMANHO_ROTULO_DE_EVENTO,
                color=COR_TEXTO_SECUNDARIO,
                zorder=3,
            )


def gerar_figura(tabela: pd.DataFrame, figura_a_gerar: Figura) -> list[Path]:
    """Desenha os painéis empilhados e grava PDF e PNG em `figuras/`.

    Os anos aparecem no eixo x de CADA painel. O PDF sai sem data de criação, para o arquivo ser idêntico a cada
    execução com os mesmos dados.

    Returns:
        Os caminhos dos dois arquivos gravados (PDF e PNG).
    """
    figura, eixos = plt.subplots(
        len(figura_a_gerar.paineis),
        1,
        figsize=(LARGURA_EM_POLEGADAS, figura_a_gerar.altura_em_polegadas),
        sharex=True,
    )
    for posicao_do_painel, (eixo, painel) in enumerate(zip(eixos, figura_a_gerar.paineis)):
        desenhar_painel(eixo, tabela, painel)
        if figura_a_gerar.com_eventos_de_referencia:
            e_painel_de_cima = posicao_do_painel == 0
            desenhar_eventos_de_referencia(eixo, EVENTOS_DE_REFERENCIA, com_rotulo=e_painel_de_cima)

    # O rotulo da faixa sombreada vai na legenda da figura, no texto: dentro do painel ele cruzava o pico de 2025.
    eixos[-1].xaxis.set_major_locator(mdates.YearLocator())
    eixos[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    # Com sharex, so o painel de baixo mostra os anos por padrao; aqui todos mostram (cada painel se le sozinho).
    for eixo in eixos:
        eixo.tick_params(axis="x", labelbottom=True)
    figura.tight_layout(h_pad=1.6)

    PASTA_DAS_FIGURAS.mkdir(parents=True, exist_ok=True)
    caminho_do_pdf = PASTA_DAS_FIGURAS / f"{figura_a_gerar.nome_do_arquivo}.pdf"
    caminho_do_png = PASTA_DAS_FIGURAS / f"{figura_a_gerar.nome_do_arquivo}.png"
    figura.savefig(caminho_do_pdf, metadata={"CreationDate": None, "Producer": None})
    figura.savefig(caminho_do_png, dpi=RESOLUCAO_DO_PNG)
    plt.close(figura)
    return [caminho_do_pdf, caminho_do_png]


def copiar_pdf_para_o_artigo(caminho_do_pdf: Path) -> Path:
    """Copia o PDF para `entregas/artigo/figuras/` (nunca apaga nem sobrescreve as preliminares: nomes diferentes)."""
    PASTA_DAS_FIGURAS_DO_ARTIGO.mkdir(parents=True, exist_ok=True)
    destino = PASTA_DAS_FIGURAS_DO_ARTIGO / caminho_do_pdf.name
    shutil.copy2(caminho_do_pdf, destino)
    return destino


def main() -> None:
    """Carrega os dados, desenha as duas figuras e copia os PDFs para a pasta do artigo."""
    tabela = carregar_tabela_do_grafico()
    for figura_a_gerar in montar_figuras():
        caminho_do_pdf, caminho_do_png = gerar_figura(tabela, figura_a_gerar)
        destino_no_artigo = copiar_pdf_para_o_artigo(caminho_do_pdf)
        print(
            f"{figura_a_gerar.nome_do_arquivo}: {len(figura_a_gerar.paineis)} painéis, {len(tabela)} semanas "
            f"({tabela[CONFIGURACAO_DADOS.coluna_de_data].min().date()} a "
            f"{tabela[CONFIGURACAO_DADOS.coluna_de_data].max().date()})"
        )
        print(f"  {caminho_do_pdf.name}, {caminho_do_png.name} -> {PASTA_DAS_FIGURAS}")
        print(f"  cópia do PDF -> {destino_no_artigo}")


if __name__ == "__main__":
    main()
