"""

Um tradutor de Markdown SIMPLES para HTML, feito na mao, so com o que a gente
usa nas paginas do projeto: titulos, paragrafos, listas, negrito, italico,
links, imagens, citacao, linha divisoria, trecho de codigo e tabelas.

Nao e um Markdown completo — e de proposito: assim a pagina_web nao depende de
nenhuma biblioteca de fora e o codigo fica facil de entender. Se um dia precisar
de mais, da pra crescer aqui.

Markdown, pra quem nunca viu, e um jeito de escrever texto com marquinhas: '#'
vira titulo, '-' vira lista, '**palavra**' fica em negrito, e por ai vai.

"""

import html
import re


# Traduz os pedacos "dentro da linha" (negrito, italico, link, imagem, codigo).
def _inline(texto: str) -> str:
    """

    Primeiro guarda os trechos de codigo (entre crases) num canto, pra ninguem
    mexer neles. Depois escapa o texto (pra '<' e '&' nao quebrarem o HTML) e so
    entao troca as marquinhas por HTML. No fim, devolve os trechos de codigo.

    """
    guardados = []

    def guardar(achado):
        guardados.append(achado.group(1))
        return f"\x00{len(guardados) - 1}\x00"

    texto = re.sub(r"`([^`]+)`", guardar, texto)
    texto = html.escape(texto)
    texto = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", texto)

    def devolver(achado):
        return "<code>" + html.escape(guardados[int(achado.group(1))]) + "</code>"

    return re.sub(r"\x00(\d+)\x00", devolver, texto)


# Diz se a linha e o separador de cabecalho de uma tabela ( |---|---| ).
def _e_separador_de_tabela(linha: str) -> bool:
    if "|" not in linha:
        return False
    miolo = linha.strip().strip("|")
    celulas = [celula.strip() for celula in miolo.split("|")]
    if not celulas:
        return False
    for celula in celulas:
        if not re.fullmatch(r":?-{2,}:?", celula):
            return False
    return True


# Quebra "| a | b |" na lista ['a', 'b'].
def _celulas_da_linha(linha: str) -> list[str]:
    return [celula.strip() for celula in linha.strip().strip("|").split("|")]


def _montar_tabela(linhas_da_tabela: list[str]) -> str:
    """

    Monta o HTML de uma tabela escrita no formato de canos (pipes).

    A primeira linha e o cabecalho, a segunda e o separador (|---|---|) e o
    resto sao os dados. Linhas com menos celulas que o cabecalho recebem
    celulas vazias no fim, para a tabela nao ficar torta; celulas a mais sao
    descartadas.

    Args:
        linhas_da_tabela: As linhas cruas, comecando pelo cabecalho.

    Returns:
        O HTML da tabela pronto.

    """
    cabecalho = _celulas_da_linha(linhas_da_tabela[0])
    numero_de_colunas = len(cabecalho)

    celulas_cabecalho = "".join(f"<th>{_inline(titulo)}</th>" for titulo in cabecalho)
    partes = [f"<thead><tr>{celulas_cabecalho}</tr></thead>"]

    linhas_de_dados = []
    for linha in linhas_da_tabela[2:]:
        celulas = _celulas_da_linha(linha)
        celulas = (celulas + [""] * numero_de_colunas)[:numero_de_colunas]
        celulas_html = "".join(f"<td>{_inline(celula)}</td>" for celula in celulas)
        linhas_de_dados.append(f"<tr>{celulas_html}</tr>")

    if linhas_de_dados:
        partes.append("<tbody>" + "".join(linhas_de_dados) + "</tbody>")

    # 'tabela' herda o visual do site; 'tabela-md' corrige o alinhamento: a
    # folha de estilo base alinha tudo a direita e proibe quebra de linha,
    # porque foi feita para tabela de numeros - aqui o conteudo e texto.
    return ('<div class="tabelaRolavel">'
            '<table class="tabela tabela-md">' + "".join(partes) + "</table></div>")


# Traduz um texto Markdown inteiro em HTML (linha por linha, juntando blocos).
def para_html(markdown_texto: str) -> str:
    """

    Le linha por linha e vai montando os blocos: titulos, listas, citacoes e
    paragrafos. Linha em branco fecha o bloco atual. As funcoes 'fechar_*' juntam
    o que estava acumulado e guardam o pedaco de HTML pronto.

    """
    linhas = markdown_texto.replace("\r\n", "\n").split("\n")
    blocos = []
    paragrafo = []
    citacao = []
    lista = None

    def fechar_paragrafo():
        nonlocal paragrafo
        if paragrafo:
            blocos.append("<p>" + _inline(" ".join(paragrafo)) + "</p>")
            paragrafo = []

    def fechar_lista():
        nonlocal lista
        if lista:
            etiqueta, itens = lista
            corpo = "".join(f"<li>{_inline(item)}</li>" for item in itens)
            blocos.append(f"<{etiqueta}>{corpo}</{etiqueta}>")
            lista = None

    def fechar_citacao():
        nonlocal citacao
        if citacao:
            blocos.append("<blockquote>" + _inline(" ".join(citacao)) + "</blockquote>")
            citacao = []

    def fechar_tudo():
        fechar_paragrafo()
        fechar_lista()
        fechar_citacao()

    indice = 0
    while indice < len(linhas):
        crua = linhas[indice].rstrip()
        if not crua.strip():
            fechar_tudo()
            indice += 1
            continue

        # Tabela: a linha atual tem canos e a proxima e o separador |---|---|.
        proxima = linhas[indice + 1].rstrip() if indice + 1 < len(linhas) else ""
        if "|" in crua and _e_separador_de_tabela(proxima):
            fechar_tudo()
            fim = indice + 2
            while fim < len(linhas) and "|" in linhas[fim] and linhas[fim].strip():
                fim += 1
            blocos.append(_montar_tabela([linha.rstrip() for linha in linhas[indice:fim]]))
            indice = fim
            continue

        titulo = re.match(r"^(#{1,6})\s+(.*)$", crua)
        item_pontos = re.match(r"^[-*]\s+(.*)$", crua)
        item_numero = re.match(r"^\d+\.\s+(.*)$", crua)

        if titulo:
            fechar_tudo()
            nivel = len(titulo.group(1))
            blocos.append(f"<h{nivel}>{_inline(titulo.group(2))}</h{nivel}>")
        elif re.match(r"^(-{3,}|\*{3,})$", crua):
            fechar_tudo()
            blocos.append("<hr>")
        elif crua.startswith(">"):
            fechar_paragrafo()
            fechar_lista()
            citacao.append(crua[1:].strip())
        elif item_pontos:
            fechar_paragrafo()
            fechar_citacao()
            if not lista or lista[0] != "ul":
                fechar_lista()
                lista = ("ul", [])
            lista[1].append(item_pontos.group(1))
        elif item_numero:
            fechar_paragrafo()
            fechar_citacao()
            if not lista or lista[0] != "ol":
                fechar_lista()
                lista = ("ol", [])
            lista[1].append(item_numero.group(1))
        else:
            fechar_lista()
            fechar_citacao()
            paragrafo.append(crua.strip())

        indice += 1

    fechar_tudo()
    return "\n".join(blocos)
