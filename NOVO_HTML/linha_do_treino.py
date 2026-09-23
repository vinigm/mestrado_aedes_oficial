"""Linha do tempo do que entrou no treino do cenário adotado.

A página de dados mostra de quando até quando cada fonte tem dado. Esta figura
responde outra pergunta, e só ela importa para o cenário adotado: **de qual
período o modelo realmente aprendeu, e qual período ele foi avaliado**.

São coisas diferentes. A série de captura tem 14 anos, mas o modelo não pode
aprender em semana sem alvo, não é avaliado enquanto não junta o histórico
mínimo, e não treina com as semanas recentes cujo número de casos ainda não
fechou. O desenho abaixo separa esses quatro trechos.
"""

import dataclasses
import datetime

import layout


@dataclasses.dataclass(frozen=True)
class TrechoDaLinhaDoTempo:
    """Um período com um papel específico no treino.

    Attributes:
        inicio: Primeiro dia do trecho.
        fim: Último dia do trecho.
        titulo: Nome curto do papel, usado na legenda.
        descricao: O que acontece nesse trecho, em uma linha.
        cor: Cor de preenchimento da barra.
    """

    inicio: datetime.date
    fim: datetime.date
    titulo: str
    descricao: str
    cor: str


# Datas do cenário adotado, lidas da configuração e da tabela de modelagem.
# Ficam nomeadas porque entram tanto no desenho quanto na legenda.
INICIO_DA_SERIE_DE_CAPTURA = datetime.date(2012, 9, 23)
PRIMEIRA_SEMANA_COM_CASO = datetime.date(2018, 2, 18)
FIM_DO_TREINO_MINIMO = datetime.date(2020, 2, 16)
INICIO_DO_CORTE_DE_MATURIDADE = datetime.date(2026, 2, 1)
ULTIMA_SEMANA_COM_CASO = datetime.date(2026, 4, 26)

# Fim do eixo. Passa da última semana com caso para a barra não encostar na
# borda direita do desenho.
FIM_DO_EIXO = datetime.date(2026, 12, 31)


TRECHOS = (
    TrechoDaLinhaDoTempo(
        inicio=INICIO_DA_SERIE_DE_CAPTURA,
        fim=PRIMEIRA_SEMANA_COM_CASO,
        titulo="Fora do treino",
        descricao="há mosquito e clima, mas não há casos para aprender",
        cor="#E3E8EE",
    ),
    TrechoDaLinhaDoTempo(
        inicio=PRIMEIRA_SEMANA_COM_CASO,
        fim=FIM_DO_TREINO_MINIMO,
        titulo="Só treino",
        descricao="as 104 semanas de histórico mínimo, antes da 1ª previsão",
        cor="#AFC9F2",
    ),
    TrechoDaLinhaDoTempo(
        inicio=FIM_DO_TREINO_MINIMO,
        fim=INICIO_DO_CORTE_DE_MATURIDADE,
        titulo="Treino e avaliação",
        descricao="o walk-forward avança aqui, semana a semana",
        cor="#1B6EF3",
    ),
    TrechoDaLinhaDoTempo(
        inicio=INICIO_DO_CORTE_DE_MATURIDADE,
        fim=ULTIMA_SEMANA_COM_CASO,
        titulo="Corte de maturidade",
        descricao="casos apagados do treino: o número ainda não fechou",
        cor="#E8B96A",
    ),
)


# Medidas do desenho, em unidades da viewBox.
LARGURA_DO_DESENHO = 720
ALTURA_DO_DESENHO = 132
MARGEM_ESQUERDA = 8
MARGEM_DIREITA = 8
TOPO_DA_BARRA = 28
ALTURA_DA_BARRA = 34


def _posicao_horizontal(data: datetime.date) -> float:
    """Converte uma data na coordenada X dentro da área de desenho.

    Args:
        data: A data a posicionar.

    Returns:
        A coordenada X, em unidades da viewBox.
    """
    dias_totais = (FIM_DO_EIXO - INICIO_DA_SERIE_DE_CAPTURA).days
    dias_ate_a_data = (data - INICIO_DA_SERIE_DE_CAPTURA).days
    largura_util = LARGURA_DO_DESENHO - MARGEM_ESQUERDA - MARGEM_DIREITA

    return MARGEM_ESQUERDA + largura_util * dias_ate_a_data / dias_totais


def _barra_de_um_trecho(trecho: TrechoDaLinhaDoTempo) -> str:
    """Desenha o retângulo de um trecho da linha do tempo."""
    x_inicial = _posicao_horizontal(trecho.inicio)
    x_final = _posicao_horizontal(trecho.fim)
    largura = max(x_final - x_inicial, 1.0)

    return (
        f'<rect x="{x_inicial:.1f}" y="{TOPO_DA_BARRA}" '
        f'width="{largura:.1f}" height="{ALTURA_DA_BARRA}" '
        f'fill="{trecho.cor}"><title>{layout.escapar(trecho.titulo)}</title></rect>'
    )


def _marcas_de_ano() -> str:
    """Desenha o traço e o rótulo de cada ano no eixo horizontal."""
    partes = []
    base_da_barra = TOPO_DA_BARRA + ALTURA_DA_BARRA

    for ano in range(2013, 2027):
        x = _posicao_horizontal(datetime.date(ano, 1, 1))
        partes.append(
            f'<line x1="{x:.1f}" y1="{base_da_barra}" '
            f'x2="{x:.1f}" y2="{base_da_barra + 4}" '
            'stroke="#CBD4DE" stroke-width="1"/>'
        )
        partes.append(
            f'<text x="{x:.1f}" y="{base_da_barra + 16}" text-anchor="middle" '
            'font-size="9.5" fill="#93A2B3">'
            f"{ano}</text>"
        )

    return "".join(partes)


def _legenda() -> str:
    """Monta a legenda, um item por trecho, abaixo do desenho."""
    itens = []
    for trecho in TRECHOS:
        itens.append(
            '<div class="itemDaLinhaDoTreino">'
            f'<span class="marcaDaLinhaDoTreino" style="background:{trecho.cor}"></span>'
            f"<b>{layout.escapar(trecho.titulo)}</b> — "
            f"{layout.escapar(trecho.descricao)}</div>"
        )

    return f'<div class="legendaDaLinhaDoTreino">{"".join(itens)}</div>'


def montar() -> str:
    """Monta a figura inteira: título, barra segmentada, eixo e legenda.

    Returns:
        O HTML pronto para entrar na página.
    """
    barras = []
    for trecho in TRECHOS:
        barras.append(_barra_de_um_trecho(trecho))

    svg = (
        f'<svg viewBox="0 0 {LARGURA_DO_DESENHO} {ALTURA_DO_DESENHO}" role="img" '
        'aria-label="Período usado para treinar e avaliar o modelo">'
        f'{"".join(barras)}{_marcas_de_ano()}'
        "</svg>"
    )

    return (
        '<div class="linhaDoTreino">'
        '<div class="graficoTitulo">O período que o modelo usou</div>'
        f"{svg}{_legenda()}"
        "</div>"
    )
