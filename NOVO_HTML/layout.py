"""Montagem do HTML: a casca das páginas e os blocos reutilizáveis.

Uma página é sempre a mesma casca — menu primário, menu secundário e área de
conteúdo — com um corpo diferente. Este módulo entrega essa casca e os blocos
que o corpo usa (régua de números, cartão, aviso, figura, tabela e seção), para
que nenhuma página precise escrever HTML solto nem repetir classe de CSS.
"""

import dataclasses
import html

import icones
import navegacao
import tema


@dataclasses.dataclass(frozen=True)
class Metrica:
    """Um número de destaque na régua do topo da página.

    Attributes:
        rotulo: O que o número mede, em poucas palavras.
        valor: O número já formatado para leitura.
        nota: Linha fina de contexto, opcional.
    """

    rotulo: str
    valor: str
    nota: str = ""


# Tons possíveis de um aviso, do mais neutro ao mais grave. O tom escolhe a cor
# da borda e do fundo; o conteúdo é responsabilidade de quem chama.
TONS_DE_AVISO = ("info", "bom", "atencao", "critico")

# Famílias de dado usadas nas etiquetas coloridas das tabelas.
FAMILIAS_DE_DADO = ("vetor", "alvo", "clima", "contexto")


def escapar(texto: str) -> str:
    """Escapa texto que vai para dentro do HTML, incluindo aspas."""
    return html.escape(str(texto), quote=True)


# --------------------------------------------------------------- navegação


def _item_do_menu_primario(
    pagina: navegacao.PaginaDoSite,
    chave_ativa: str,
) -> str:
    """Monta uma linha do menu primário, marcando-a quando for a página aberta."""
    classe = "navItem ativo" if pagina.chave == chave_ativa else "navItem"
    icone = icones.icone_de_menu(pagina.icone)
    rotulo = escapar(pagina.titulo_no_menu)

    return (
        f'<a class="{classe}" href="{escapar(pagina.arquivo)}">'
        f'{icone}<span class="navRotuloItem">{rotulo}</span></a>'
    )


def montar_menu_primario(chave_ativa: str) -> str:
    """Coluna escura da esquerda: identidade e a lista de páginas.

    Args:
        chave_ativa: Chave da página aberta, para destacar o item certo.

    Returns:
        O HTML completo da coluna primária.
    """
    identidade = navegacao.IDENTIDADE_DO_SITE

    linhas_de_menu = []
    for pagina in navegacao.PAGINAS_DO_SITE:
        linhas_de_menu.append(_item_do_menu_primario(pagina, chave_ativa))

    return (
        '<nav id="navPrimaria">'
        '<div class="marca">'
        f'<div class="marcaSelo">{icones.mosquito("marcaMosquito")}</div>'
        '<div class="marcaTexto">'
        f'<div class="marcaNome">{escapar(identidade["nome"])}</div>'
        f'<div class="marcaSub">{escapar(identidade["subtitulo"])}</div>'
        "</div></div>"
        '<div class="navRolagem">'
        '<div class="navRotulo">Navegação</div>'
        f'{"".join(linhas_de_menu)}'
        "</div>"
        '<div class="navRodape" id="navRodape">&laquo; Recolher menu</div>'
        "</nav>"
    )


def montar_menu_secundario(pagina: navegacao.PaginaDoSite) -> str:
    """Coluna ao lado: as seções da página aberta, que acompanham a rolagem.

    Args:
        pagina: A página aberta, de onde saem as seções.

    Returns:
        O HTML completo da coluna secundária.
    """
    itens = []
    for posicao, secao in enumerate(pagina.secoes):
        classe = "nav2Item ativo" if posicao == 0 else "nav2Item"
        icone = icones.icone_de_submenu("relogio")
        itens.append(
            f'<a class="{classe}" href="#{escapar(secao.ancora)}" '
            f'data-ancora="{escapar(secao.ancora)}">'
            f'{icone}<span class="nav2Texto">{escapar(secao.rotulo_do_menu())}</span></a>'
        )

    return (
        '<nav id="navSecundaria"><div class="nav2Rolagem">'
        f'<div class="nav2Rotulo">{escapar(pagina.rotulo_do_submenu)}</div>'
        f'{"".join(itens)}'
        "</div></nav>"
    )


# ------------------------------------------------------ blocos de conteúdo


def montar_regua(metricas: list[Metrica]) -> str:
    """Faixa de números no topo da página, separada por filetes.

    Args:
        metricas: Os números de destaque, na ordem de leitura.

    Returns:
        O HTML da régua, ou string vazia quando não há número a mostrar.
    """
    if not metricas:
        return ""

    blocos = []
    for metrica in metricas:
        nota = ""
        if metrica.nota:
            nota = f'<div class="metricaNota">{escapar(metrica.nota)}</div>'

        blocos.append(
            '<div class="metrica">'
            f'<div class="metricaRotulo">{escapar(metrica.rotulo)}</div>'
            f'<div class="metricaValor">{escapar(metrica.valor)}</div>'
            f"{nota}</div>"
        )

    return f'<div class="regua">{"".join(blocos)}</div>'


def montar_secao(
    secao: navegacao.SecaoDaPagina,
    ordem: int,
    intro: str,
    corpo: str,
) -> str:
    """Bloco de conteúdo com âncora, para o menu secundário encontrar.

    Args:
        secao: A seção declarada em `navegacao.py`.
        ordem: Posição da seção na página, mostrada ao lado do título.
        intro: Frase de abertura em texto simples. Pode vir vazia.
        corpo: HTML já montado do miolo da seção.

    Returns:
        O HTML da seção inteira.
    """
    abertura = ""
    if intro:
        abertura = f'<p class="secaoIntro">{intro}</p>'

    return (
        f'<section class="secao" id="{escapar(secao.ancora)}">'
        '<div class="secaoTitulo">'
        f'<span class="secaoOrdem">{ordem:02d}</span>'
        f"<h2>{escapar(secao.titulo)}</h2>"
        "</div>"
        f"{abertura}{corpo}</section>"
    )


def montar_cartao(rotulo: str, titulo: str, corpo: str) -> str:
    """Caixa com borda para uma ideia fechada.

    Args:
        rotulo: Versalete pequeno no topo. Pode vir vazio.
        titulo: Título do cartão. Pode vir vazio.
        corpo: HTML do miolo, normalmente um ou dois parágrafos.

    Returns:
        O HTML do cartão.
    """
    partes = []
    if rotulo:
        partes.append(f'<div class="cartaoRotulo">{escapar(rotulo)}</div>')
    if titulo:
        partes.append(f"<h3>{escapar(titulo)}</h3>")
    partes.append(corpo)

    return f'<div class="cartao">{"".join(partes)}</div>'


def montar_grade(cartoes: list[str], colunas: int) -> str:
    """Dispõe cartões em grade.

    Args:
        cartoes: HTML de cada cartão, já montado.
        colunas: Quantas colunas usar. Aceita de 2 a 4.

    Returns:
        O HTML da grade.

    Raises:
        ValueError: Se o número de colunas não tiver classe CSS correspondente.
    """
    if colunas not in (2, 3, 4):
        raise ValueError(f"Grade aceita 2, 3 ou 4 colunas; veio {colunas}.")

    return f'<div class="grade grade{colunas}">{"".join(cartoes)}</div>'


def montar_aviso(tom: str, rotulo: str, texto: str) -> str:
    """Faixa lateral colorida que separa fato medido de ressalva.

    O tom é a única coisa que muda a cor, e ele existe para que fato e hipótese
    nunca apareçam com o mesmo peso visual.

    Args:
        tom: Um dos valores de `TONS_DE_AVISO`.
        rotulo: Versalete curto, como "Fato medido" ou "Ressalva".
        texto: HTML do corpo do aviso.

    Returns:
        O HTML do aviso.

    Raises:
        ValueError: Se o tom não for reconhecido.
    """
    if tom not in TONS_DE_AVISO:
        raise ValueError(f"Tom {tom!r} desconhecido. Use um de {TONS_DE_AVISO}.")

    return (
        f'<div class="aviso {tom}">'
        f'<div class="avisoRotulo">{escapar(rotulo)}</div>'
        f"<p>{texto}</p></div>"
    )


def montar_figura(
    arquivo: str,
    titulo: str,
    subtitulo: str,
    legenda: str,
) -> str:
    """Imagem em largura cheia, com título em cima e legenda embaixo.

    Args:
        arquivo: Caminho da imagem, relativo à página gerada.
        titulo: Título curto acima da imagem.
        subtitulo: Uma linha de contexto abaixo do título. Pode vir vazia.
        legenda: Texto explicativo no rodapé da figura. Pode vir vazio.

    Returns:
        O HTML da figura.
    """
    topo = ""
    if titulo:
        topo = f"<h3>{escapar(titulo)}</h3>"
    if subtitulo:
        topo += f'<p class="figuraSub">{escapar(subtitulo)}</p>'
    if topo:
        topo = f'<div class="figuraTopo">{topo}</div>'

    rodape = ""
    if legenda:
        rodape = f'<p class="figuraLegenda">{legenda}</p>'

    return (
        '<figure class="figura">'
        f"{topo}"
        f'<img src="{escapar(arquivo)}" alt="{escapar(titulo)}" loading="lazy">'
        f"{rodape}</figure>"
    )


def montar_etiqueta(texto: str, familia: str) -> str:
    """Pastilha colorida que diz de qual família o dado vem.

    Args:
        texto: O rótulo visível.
        familia: Um dos valores de `FAMILIAS_DE_DADO`.

    Returns:
        O HTML da etiqueta.

    Raises:
        ValueError: Se a família não for reconhecida.
    """
    if familia not in FAMILIAS_DE_DADO:
        raise ValueError(
            f"Família {familia!r} desconhecida. Use uma de {FAMILIAS_DE_DADO}."
        )

    return f'<span class="etiqueta {familia}">{escapar(texto)}</span>'


def montar_tabela(cabecalhos: list[str], linhas: list[list[str]]) -> str:
    """Tabela com cabeçalho fixo na rolagem.

    As células entram como HTML já montado, porque várias delas carregam
    etiquetas e `<code>`. Quem chama é responsável por escapar o texto simples.

    Args:
        cabecalhos: Títulos das colunas.
        linhas: Uma lista por linha, com uma célula por coluna.

    Returns:
        O HTML da tabela dentro do envelope rolável.

    Raises:
        ValueError: Se alguma linha não tiver o mesmo número de colunas do
            cabeçalho, o que indicaria tabela desalinhada.
    """
    quantidade_de_colunas = len(cabecalhos)

    for posicao, linha in enumerate(linhas):
        if len(linha) != quantidade_de_colunas:
            raise ValueError(
                f"Linha {posicao} tem {len(linha)} células, "
                f"mas o cabeçalho tem {quantidade_de_colunas} colunas."
            )

    # O cabeçalho entra como HTML já montado, igual às células: há tabelas em
    # que a cor da coluna faz parte da informação (ver a página do cenário
    # adotado, onde a cor liga a coluna ao gráfico correspondente).
    celulas_de_cabecalho = []
    for titulo in cabecalhos:
        celulas_de_cabecalho.append(f"<th>{titulo}</th>")

    linhas_montadas = []
    for linha in linhas:
        celulas = []
        for celula in linha:
            celulas.append(f"<td>{celula}</td>")
        linhas_montadas.append(f'<tr>{"".join(celulas)}</tr>')

    return (
        '<div class="tabelaEnvelope"><div class="tabelaRolavel">'
        '<table class="tabela">'
        f'<thead><tr>{"".join(celulas_de_cabecalho)}</tr></thead>'
        f'<tbody>{"".join(linhas_montadas)}</tbody>'
        "</table></div></div>"
    )


def montar_faixa(titulo: str) -> str:
    """Título centralizado entre dois filetes, para abrir um bloco de destaque."""
    return f'<div class="faixa"><p class="faixaTitulo">{escapar(titulo)}</p></div>'


def montar_fluxo(etapas: list[tuple[str, str]]) -> str:
    """Diagrama de etapas em sequência, ligadas por setas.

    Serve para mostrar um caminho — de onde o dado vem até onde ele chega —
    sem exigir que o leitor monte a sequência a partir de texto corrido.

    Args:
        etapas: Uma tupla `(nome, descricao)` por etapa, na ordem do caminho.

    Returns:
        O HTML do diagrama.

    Raises:
        ValueError: Se vier menos de duas etapas, caso em que não há caminho
            a desenhar.
    """
    if len(etapas) < 2:
        raise ValueError(f"Um fluxo precisa de 2 etapas ou mais; vieram {len(etapas)}.")

    blocos = []
    for posicao, (nome, descricao) in enumerate(etapas):
        if posicao > 0:
            blocos.append('<div class="fluxoSeta">&rarr;</div>')

        blocos.append(
            '<div class="fluxoEtapa">'
            f'<p class="fluxoNome">{escapar(nome)}</p>'
            f'<div class="fluxoTexto">{escapar(descricao)}</div>'
            "</div>"
        )

    return f'<div class="fluxo">{"".join(blocos)}</div>'


def montar_lista(itens: list[str]) -> str:
    """Lista de tópicos. Cada item entra como HTML já montado."""
    itens_montados = []
    for item in itens:
        itens_montados.append(f"<li>{item}</li>")

    return f'<ul class="lista">{"".join(itens_montados)}</ul>'


# ------------------------------------------------------------- a casca toda


def montar_documento(
    pagina: navegacao.PaginaDoSite,
    metricas: list[Metrica],
    corpo: str,
    gerado_em: str,
) -> str:
    """Monta o HTML completo de uma página.

    Args:
        pagina: A página sendo gerada, com título, resumo e seções.
        metricas: Números de destaque da régua. Pode vir vazio.
        corpo: HTML das seções, já montado na ordem.
        gerado_em: Data de geração, mostrada no rodapé.

    Returns:
        O documento HTML inteiro, pronto para gravar em disco.
    """
    menu_primario = montar_menu_primario(pagina.chave)
    regua = montar_regua(metricas)

    # Página sem resumo não deve render um parágrafo vazio, que abriria um vão
    # entre o título e a régua de números.
    resumo = ""
    if pagina.resumo:
        resumo = f'<p class="resumo">{escapar(pagina.resumo)}</p>'

    return (
        "<!doctype html>"
        '<html lang="pt-BR"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        # O painel é republicado a cada rodada, e quem já visitou uma versão
        # anterior recebia a cópia em cache ao voltar pela página inicial. Estas
        # três linhas mandam o navegador revalidar antes de reusar.
        '<meta http-equiv="Cache-Control" content="no-cache, must-revalidate">'
        '<meta http-equiv="Pragma" content="no-cache">'
        '<meta http-equiv="Expires" content="0">'
        f"<title>{escapar(pagina.titulo_no_menu)} — Aedes aegypti e dengue em Porto Alegre</title>"
        f"<style>{tema.FOLHA_DE_ESTILO}</style>"
        "</head><body>"
        '<div id="casca">'
        f"{menu_primario}"
        '<main id="areaConteudo"><div class="conteudoInterno">'
        '<p class="trilha">Mestrado PPGC · UFRGS &nbsp;·&nbsp; Porto Alegre, RS '
        f"&nbsp;·&nbsp; <b>{escapar(pagina.titulo_no_menu)}</b></p>"
        '<header class="cabecalhoPagina">'
        f"<h1>{escapar(pagina.titulo)}</h1>"
        f"{resumo}"
        "</header>"
        f"{regua}{corpo}"
        "</div>"
        f'<footer class="rodape">Painel de acompanhamento da pesquisa · '
        f"gerado em {escapar(gerado_em)}</footer>"
        "</main></div>"
        f"<script>{tema.SCRIPT_DE_NAVEGACAO}</script>"
        "</body></html>"
    )
