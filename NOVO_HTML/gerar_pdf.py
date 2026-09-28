"""Gera o PDF da apresentação a partir do HTML já pronto em `saida/`.

O que este script entrega: um PDF com **uma página por slide**, cada página com
a barra de andamento no topo e o slide inteiro embaixo, do jeito que a
apresentação aparece na tela.

Por que ele existe, e por que não é mais um `--print-to-pdf` direto
--------------------------------------------------------------------
A primeira versão pedia ao Chrome que imprimisse a página inteira de uma vez e
deixava o `@media print` do `deck.py` cuidar do resto: empilhar os 21 slides,
cada um com `transform:scale(.88)` e uma quebra de página antes. Medido em
27/09/2026, o resultado saía errado em dois pontos:

- **o título batia na barra** — no PDF gerado, o título do slide e os nomes das
  seções ocupavam literalmente a mesma faixa vertical (48,1pt a 69,8pt contra
  49,3pt a 54,6pt, na página 2). A barra era uma cópia clonada por JavaScript e
  posicionada de forma absoluta dentro de um slide transformado, e o Chrome não
  reproduz essa combinação na paginação: medido no DOM o título caía em 50px, e
  no papel caía em 24px;
- **o slide não preenchia a página** — sobrava uma faixa branca embaixo, porque
  a escala de 88% encolhia o slide sem que nada reaproveitasse o espaço.

A estratégia aqui é outra e não depende de nenhum desses truques: em vez de
paginar 21 slides transformados, o script **imprime um slide de cada vez**, e
cada impressão produz uma página só. Não há clone, não há `beforeprint` e não há
quebra de página — a página do PDF é o próprio palco da apresentação, com a
barra de verdade no topo, aquela que o JavaScript do deck já pinta com a seção
acesa.

⚠️ Nada do conteúdo dos slides é tocado. O script injeta um `<style>` na cópia
que vive na memória do navegador; os arquivos em `saida/` continuam como estão,
e o botão "Salvar em PDF" da página segue usando o caminho antigo.

Uso:
    python3 gerar_pdf.py                   → gera o seminário (cópia 2)
    python3 gerar_pdf.py seminario.html    → gera outra página do site
"""

from __future__ import annotations

import base64
import dataclasses
import json
import pathlib
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import fitz
import websocket

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

PASTA_DESTE_ARQUIVO = pathlib.Path(__file__).resolve().parent
PASTA_DE_SAIDA = PASTA_DESTE_ARQUIVO / "saida"
PAGINA_PADRAO = "seminario-copia-2.html"

CAMINHO_DO_CHROME = pathlib.Path(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


@dataclasses.dataclass(frozen=True)
class GeometriaDaPagina:
    """Medidas, em pixels de CSS, da página do PDF e do slide dentro dela.

    O slide foi desenhado como uma tela fixa de 1280x720 — é o que o `deck.py`
    chama de "tela fixa", e é também o tamanho de um slide widescreen de
    PowerPoint. A página do PDF mantém esse mesmo 16:9, e o slide encolhe o
    tanto necessário para caber embaixo da barra de andamento.

    Attributes:
        largura: Largura da página. 1280 mantém o 16:9 com a altura.
        altura: Altura da página.
        largura_do_slide: Largura da tela fixa do slide, antes de qualquer escala.
        altura_do_slide: Altura da tela fixa do slide, antes de qualquer escala.
        respiro_vertical: Folga branca acima e abaixo do slide, dentro do espaço
            que sobra da barra. Sem ela o slide encosta na borda de baixo.
        margem_interna_do_slide: Recuo lateral que o próprio slide já tem por
            dentro (o `padding` de `.deckSlide`). Serve só para alinhar as
            pontas da barra com o texto do slide.
    """

    largura: int = 1280
    altura: int = 720
    largura_do_slide: int = 1280
    altura_do_slide: int = 720
    respiro_vertical: int = 10
    margem_interna_do_slide: int = 56


GEOMETRIA = GeometriaDaPagina()

# 96 pixels de CSS por polegada é a conta que o Chrome usa para converter o
# tamanho da página. 1280x720 vira 13,333in x 7,5in.
PIXELS_POR_POLEGADA = 96

# A janela do navegador precisa ser mais larga que os 1280px da página: o Chrome
# avalia as media queries de LARGURA pela janela, e não pelo papel. Numa janela
# estreita — 800px, que é o padrão do modo headless — as regras de tela pequena
# do site disparam no meio da impressão, empilham os gráficos que deveriam ficar
# lado a lado e estouram a altura do slide.
LARGURA_DA_JANELA = 1560
ALTURA_DA_JANELA = 1000


@dataclasses.dataclass(frozen=True)
class EncaixeDoSlide:
    """Como o slide de 1280x720 se encaixa no espaço que sobra da barra.

    Attributes:
        escala: Fator aplicado ao slide inteiro, entre 0 e 1.
        deslocamento_horizontal: Pixels para a direita, para centrar o slide.
        deslocamento_vertical: Pixels para baixo, para centrar o slide no espaço
            abaixo da barra.
        recuo_lateral_da_barra: Recuo que alinha as pontas da barra com o texto
            do slide já escalado.
    """

    escala: float
    deslocamento_horizontal: float
    deslocamento_vertical: float
    recuo_lateral_da_barra: float


# ---------------------------------------------------------------------------
# Cliente do Chrome DevTools Protocol
# ---------------------------------------------------------------------------


def _achar_porta_livre() -> int:
    """Devolve uma porta local livre para a depuração do Chrome.

    Returns:
        O número da porta.

    Raises:
        RuntimeError: Se nenhuma porta entre 9500 e 9599 estiver livre.
    """
    for porta_candidata in range(9500, 9600):
        with socket.socket() as sonda:
            try:
                sonda.bind(("127.0.0.1", porta_candidata))
            except OSError:
                continue
        return porta_candidata

    raise RuntimeError("Nenhuma porta livre entre 9500 e 9599.")


class Navegador:
    """Um Chrome headless com uma aba, controlado pelo DevTools Protocol.

    O `--print-to-pdf` da linha de comando não serve aqui: ele imprime a página
    inteira de uma vez e não deixa rodar JavaScript entre uma página e outra, que
    é justamente o que precisamos para trocar de slide. Pelo protocolo dá para
    abrir a página, medir o DOM, mudar de slide e imprimir, tudo na mesma aba.
    """

    def __init__(self, largura: int, altura: int) -> None:
        if not CAMINHO_DO_CHROME.exists():
            raise RuntimeError(
                f"Chrome não encontrado em: {CAMINHO_DO_CHROME}\n"
                "Instale o Google Chrome ou ajuste CAMINHO_DO_CHROME."
            )

        self.porta = _achar_porta_livre()
        self.pasta_do_perfil = tempfile.mkdtemp(prefix="chrome-pdf-seminario-")
        self.processo = subprocess.Popen(
            [
                str(CAMINHO_DO_CHROME),
                "--headless=new",
                f"--remote-debugging-port={self.porta}",
                f"--user-data-dir={self.pasta_do_perfil}",
                f"--window-size={largura},{altura}",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                "--allow-file-access-from-files",
                "--hide-scrollbars",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.conexao = self._conectar()
        self.ultimo_identificador = 0
        self.chamar("Page.enable")
        self.chamar("Runtime.enable")

    def _conectar(self, tentativas: int = 150) -> websocket.WebSocket:
        """Espera o Chrome subir e abre o canal de controle da primeira aba.

        Args:
            tentativas: Quantas vezes perguntar pela aba, a cada 0,2 segundo.

        Returns:
            A conexão WebSocket com a aba.

        Raises:
            RuntimeError: Se o Chrome não responder dentro das tentativas.
        """
        endereco_da_lista = f"http://127.0.0.1:{self.porta}/json/list"

        for _ in range(tentativas):
            try:
                resposta = urllib.request.urlopen(endereco_da_lista, timeout=1)
                abas = json.loads(resposta.read())
                abas_de_pagina = [aba for aba in abas if aba.get("type") == "page"]

                if abas_de_pagina:
                    # `suppress_origin`: sem ele a biblioteca manda um cabeçalho
                    # `Origin`, e o Chrome recusa a conexão como se ela viesse de
                    # uma página web qualquer.
                    return websocket.create_connection(
                        abas_de_pagina[0]["webSocketDebuggerUrl"],
                        max_size=400_000_000,
                        suppress_origin=True,
                    )
            except (OSError, ValueError, websocket.WebSocketException):
                pass

            time.sleep(0.2)

        raise RuntimeError("O Chrome não abriu a porta de depuração.")

    def chamar(self, metodo: str, **parametros) -> dict:
        """Executa um comando do protocolo e devolve o resultado.

        Args:
            metodo: Nome do comando, como `Page.printToPDF`.
            **parametros: Parâmetros do comando.

        Returns:
            O campo `result` da resposta.

        Raises:
            RuntimeError: Se o navegador devolver erro para o comando.
        """
        self.ultimo_identificador += 1
        identificador = self.ultimo_identificador

        self.conexao.send(
            json.dumps({"id": identificador, "method": metodo, "params": parametros})
        )

        while True:
            resposta = json.loads(self.conexao.recv())

            if resposta.get("id") != identificador:
                # Eventos do navegador chegam pelo mesmo canal e são ignorados.
                continue

            if "error" in resposta:
                raise RuntimeError(f"{metodo} falhou: {resposta['error']}")

            return resposta.get("result", {})

    def avaliar(self, expressao_javascript: str):
        """Roda JavaScript na página e devolve o valor da última expressão.

        Args:
            expressao_javascript: O código a rodar.

        Returns:
            O valor devolvido, já convertido para tipos de Python.

        Raises:
            RuntimeError: Se o JavaScript lançar exceção.
        """
        resultado = self.chamar(
            "Runtime.evaluate",
            expression=expressao_javascript,
            returnByValue=True,
            awaitPromise=True,
        )

        if resultado.get("exceptionDetails"):
            detalhe = json.dumps(resultado["exceptionDetails"])[:600]
            raise RuntimeError(f"Erro no JavaScript da página: {detalhe}")

        return resultado["result"].get("value")

    def abrir(self, caminho: pathlib.Path, espera_em_segundos: float = 3.0) -> None:
        """Carrega um arquivo local e dá tempo para fontes e imagens entrarem.

        Args:
            caminho: O arquivo HTML.
            espera_em_segundos: Quanto esperar depois do comando de navegação.
        """
        self.chamar("Page.navigate", url=caminho.as_uri())
        time.sleep(espera_em_segundos)

    def fechar(self) -> None:
        """Encerra o navegador e apaga o perfil temporário."""
        try:
            self.conexao.close()
        finally:
            self.processo.terminate()
            try:
                self.processo.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.processo.kill()
            shutil.rmtree(self.pasta_do_perfil, ignore_errors=True)


# ---------------------------------------------------------------------------
# Preparação da página para virar PDF
# ---------------------------------------------------------------------------

# O palco sai de dentro da página do site e passa a ser o único filho visível do
# corpo. Assim o menu lateral, o cabeçalho e o rodapé deixam de disputar espaço,
# e o palco pode receber exatamente os 1280x720 da página do PDF.
#
# ⚠️ O palco é MOVIDO, não copiado: mover preserva os ouvintes de clique e o
# estado que o JavaScript do deck já montou. Uma cópia perderia a barra pintada.
JAVASCRIPT_DE_PREPARACAO = """
(function preparar(){
  var palco = document.querySelector('.deckPalco');
  if (!palco) { return 'sem palco'; }

  document.body.appendChild(palco);
  document.body.classList.add('modoPdf');

  var estilo = document.getElementById('estiloDoPdf');
  if (!estilo) {
    estilo = document.createElement('style');
    estilo.id = 'estiloDoPdf';
    document.body.appendChild(estilo);
  }
  estilo.textContent = ESTILO_AQUI;

  return 'pronto';
})()
"""

# A folha de estilo do modo PDF. Ela vale na tela e na impressão, porque o
# JavaScript do deck mede o DOM para posicionar as duas linhas da barra — se a
# medição acontecer numa geometria e a impressão em outra, a linha azul para no
# meio do caminho.
#
# 🔴 Todas as regras são prefixadas por `body.modoPdf` de propósito. O
# `@media print` do `deck.py` usa `!important` em quase tudo, e entre duas
# declarações `!important` vence a de maior especificidade — um seletor com um
# tipo e três classes ganha do seletor de classe única de lá.
ESTILO_DO_MODO_PDF = """
body.modoPdf{margin:0 !important; padding:0 !important; background:#fff !important;
  width:LARGURA_DA_PAGINApx !important; min-width:0 !important}
body.modoPdf > *:not(.deckPalco){display:none !important}

/* O palco vira a página: o tamanho exato do papel, sem moldura e sem rolagem. */
body.modoPdf .deckPalco{display:flex !important; flex-direction:column !important;
  position:relative !important; width:LARGURA_DA_PAGINApx !important;
  height:ALTURA_DA_PAGINApx !important; aspect-ratio:auto !important;
  min-height:0 !important; margin:0 !important; padding:0 !important;
  border:none !important; border-radius:0 !important; box-shadow:none !important;
  overflow:hidden !important; background:#fff !important}

/* A barra de andamento é a DE VERDADE, a que o deck já mantém no topo do palco
   com a seção acesa — e não a cópia que o modo de impressão antigo clonava. */
body.modoPdf .deckPalco > .deckIndice{display:flex !important;
  padding-left:RECUO_DA_BARRApx !important; padding-right:RECUO_DA_BARRApx !important}
body.modoPdf .deckTrilhaImpressa{display:none !important}

body.modoPdf .deckTela{display:block !important; position:relative !important;
  flex:1 1 auto !important; min-height:0 !important; overflow:hidden !important}

/* O slide volta a ser a tela fixa absoluta de 1280x720, e a escala é a que faz
   ele caber no espaço abaixo da barra. Sem `page-break`: cada impressão gera
   uma página só, e a quebra criava uma folha em branco. */
body.modoPdf .deckSlide{display:none !important; position:absolute !important;
  top:0 !important; left:0 !important;
  width:LARGURA_DO_SLIDEpx !important; height:ALTURA_DO_SLIDEpx !important;
  transform-origin:top left !important;
  transform:translate(DESLOCAMENTO_HORIZONTALpx, DESLOCAMENTO_VERTICALpx)
    scale(ESCALA) !important;
  page-break-before:auto !important; break-before:auto !important}
body.modoPdf .deckSlide.ativo{display:flex !important}

/* O rótulo da seção e os tamanhos de título voltam ao que são na TELA. O modo
   de impressão do `deck.py` escondia o rótulo e forçava 1,72rem em todo título,
   inclusive nos slides de figura, que na tela usam 1,32rem — e um título maior
   do que o previsto empurra o conteúdo para fora do slide. */
body.modoPdf .deckSlide .deckRotulo{display:block !important}
body.modoPdf .deckSlide .deckTitulo{font-size:1.72rem !important}
body.modoPdf .deckSlide.figura .deckTitulo{font-size:1.32rem !important}
body.modoPdf .deckSlide.densa .deckTitulo{font-size:1.4rem !important}
body.modoPdf .deckSlide.capa .deckTitulo{font-size:2.5rem !important}

/* 🔴 A sombra dos cartões perde a segunda camada no PDF, e não é escolha de
   estilo. O tema usa duas:

       --sombra: 0 1px 2px  rgba(16,32,51,.05),
                 0 8px 24px -16px rgba(16,32,51,.22)

   A segunda tem SPREAD NEGATIVO, e o Chrome não sabe escrever isso em vetor:
   em vez do borrão, ele desenha no PDF um retângulo CHAPADO de
   rgba(16,32,51,.22) atrás do cartão. No slide 3 do seminário — o dos quatro
   cartões do fluxo e dos quatro horizontes — os oito retângulos se encostavam
   e viravam uma mancha cinza atrás de tudo. Medido em 27/09/2026, e o defeito
   já estava no PDF antigo: são 8 blocos, o maior com 18.637pt².

   A primeira camada fica: ela também vira retângulo chapado, mas a 5% de
   opacidade e com 2px de deslocamento é invisível. A borda de 1px de cada
   cartão continua fazendo a separação. */
body.modoPdf{--sombra:0 1px 2px rgba(16,32,51,.05) !important}
"""


def montar_folha_de_estilo(encaixe: EncaixeDoSlide) -> str:
    """Preenche a folha de estilo do modo PDF com as medidas calculadas.

    Args:
        encaixe: Escala e deslocamentos do slide dentro da página.

    Returns:
        O CSS pronto para ser injetado na página.
    """
    substituicoes = {
        "LARGURA_DA_PAGINA": str(GEOMETRIA.largura),
        "ALTURA_DA_PAGINA": str(GEOMETRIA.altura),
        "LARGURA_DO_SLIDE": str(GEOMETRIA.largura_do_slide),
        "ALTURA_DO_SLIDE": str(GEOMETRIA.altura_do_slide),
        "DESLOCAMENTO_HORIZONTAL": f"{encaixe.deslocamento_horizontal:.2f}",
        "DESLOCAMENTO_VERTICAL": f"{encaixe.deslocamento_vertical:.2f}",
        "ESCALA": f"{encaixe.escala:.4f}",
        "RECUO_DA_BARRA": f"{encaixe.recuo_lateral_da_barra:.2f}",
    }

    folha = ESTILO_DO_MODO_PDF
    for marcador, valor in substituicoes.items():
        folha = folha.replace(marcador, valor)

    return folha


def calcular_encaixe(altura_da_barra: float) -> EncaixeDoSlide:
    """Descobre a escala do slide, sabendo quanto a barra ocupa no topo.

    A barra fica no fluxo, colada no topo da página; o slide recebe o que sobra,
    menos o respiro de cima e de baixo. Como o slide é mais largo do que alto, é
    sempre a altura que limita — a escala pela largura daria 1,0.

    Args:
        altura_da_barra: Altura medida da barra de andamento, em pixels.

    Returns:
        A escala e os deslocamentos que centram o slide no espaço restante.

    Raises:
        ValueError: Se a barra for tão alta que não sobre espaço para o slide.
    """
    altura_disponivel = GEOMETRIA.altura - altura_da_barra
    altura_util = altura_disponivel - 2 * GEOMETRIA.respiro_vertical

    if altura_util <= 0:
        raise ValueError(
            f"A barra ocupa {altura_da_barra:.0f}px dos {GEOMETRIA.altura}px da "
            "página e não sobra espaço para o slide."
        )

    escala_pela_largura = GEOMETRIA.largura / GEOMETRIA.largura_do_slide
    escala_pela_altura = altura_util / GEOMETRIA.altura_do_slide
    escala = min(escala_pela_largura, escala_pela_altura)

    largura_ocupada = GEOMETRIA.largura_do_slide * escala
    altura_ocupada = GEOMETRIA.altura_do_slide * escala

    deslocamento_horizontal = (GEOMETRIA.largura - largura_ocupada) / 2
    deslocamento_vertical = (altura_disponivel - altura_ocupada) / 2

    # As pontas da barra passam a cair na mesma coluna em que o texto do slide
    # começa: a margem branca do slide mais o recuo que ele já tem por dentro.
    recuo_lateral_da_barra = (
        deslocamento_horizontal + GEOMETRIA.margem_interna_do_slide * escala
    )

    return EncaixeDoSlide(
        escala=escala,
        deslocamento_horizontal=deslocamento_horizontal,
        deslocamento_vertical=deslocamento_vertical,
        recuo_lateral_da_barra=recuo_lateral_da_barra,
    )


def entrar_no_modo_pdf(navegador: Navegador) -> EncaixeDoSlide:
    """Reorganiza a página para o formato do PDF e devolve o encaixe usado.

    A altura da barra não é um número fixo: ela depende de quantas seções o deck
    tem e de como o nome de cada uma quebra. Por isso o modo PDF é montado em
    duas passadas — a primeira com o slide em escala 1, só para medir a barra já
    na largura final de 1280px; a segunda com a escala de verdade.

    Args:
        navegador: A aba com a apresentação carregada.

    Returns:
        O encaixe calculado a partir da altura real da barra.

    Raises:
        RuntimeError: Se a página não tiver um palco de apresentação.
    """
    encaixe_provisorio = EncaixeDoSlide(
        escala=1.0,
        deslocamento_horizontal=0.0,
        deslocamento_vertical=0.0,
        recuo_lateral_da_barra=GEOMETRIA.margem_interna_do_slide,
    )

    situacao = navegador.avaliar(
        JAVASCRIPT_DE_PREPARACAO.replace(
            "ESTILO_AQUI", json.dumps(montar_folha_de_estilo(encaixe_provisorio))
        )
    )

    if situacao != "pronto":
        raise RuntimeError(f"Não foi possível preparar a página: {situacao}")

    altura_da_barra = navegador.avaliar(
        "document.querySelector('.deckPalco > .deckIndice')"
        ".getBoundingClientRect().height"
    )

    encaixe = calcular_encaixe(float(altura_da_barra))

    navegador.avaliar(
        "document.getElementById('estiloDoPdf').textContent = "
        + json.dumps(montar_folha_de_estilo(encaixe))
    )

    return encaixe


# ---------------------------------------------------------------------------
# Impressão
# ---------------------------------------------------------------------------


def contar_slides(navegador: Navegador) -> int:
    """Diz quantos slides a apresentação tem.

    Args:
        navegador: A aba com a apresentação carregada.

    Returns:
        A quantidade de slides.
    """
    return int(navegador.avaliar("document.querySelectorAll('.deckSlide').length"))


def imprimir_um_slide(navegador: Navegador, posicao: int) -> bytes:
    """Mostra um slide e imprime a página correspondente.

    A troca de slide passa pelo próprio botão do deck — clicar no ponto de
    navegação faz o JavaScript acender a seção certa na barra e recalcular, em
    pixels, o comprimento da linha azul de progresso. Reproduzir essa conta aqui
    daria uma barra parada.

    Args:
        navegador: A aba com a apresentação já no modo PDF.
        posicao: Índice do slide, começando em zero.

    Returns:
        O PDF de uma página, em bytes.

    Raises:
        RuntimeError: Se a impressão devolver mais de uma página, sinal de que o
            conteúdo transbordou a altura prevista.
    """
    navegador.avaliar(f"document.querySelectorAll('.deckPonto')[{posicao}].click(); 1")

    # A linha azul da barra tem transição de 0,22s. Imprimir antes dela terminar
    # congela a barra num ponto intermediário.
    time.sleep(0.35)

    resposta = navegador.chamar(
        "Page.printToPDF",
        paperWidth=GEOMETRIA.largura / PIXELS_POR_POLEGADA,
        paperHeight=GEOMETRIA.altura / PIXELS_POR_POLEGADA,
        marginTop=0,
        marginBottom=0,
        marginLeft=0,
        marginRight=0,
        printBackground=True,
        preferCSSPageSize=False,
        displayHeaderFooter=False,
    )

    pdf_do_slide = base64.b64decode(resposta["data"])

    with fitz.open(stream=pdf_do_slide, filetype="pdf") as documento:
        if documento.page_count != 1:
            raise RuntimeError(
                f"O slide {posicao + 1} saiu com {documento.page_count} páginas. "
                "O conteúdo dele transbordou a altura da página."
            )

    return pdf_do_slide


def juntar_paginas(paginas: list[bytes], destino: pathlib.Path) -> None:
    """Costura os PDFs de uma página só num arquivo único.

    Args:
        paginas: Os PDFs, na ordem dos slides.
        destino: Onde gravar o arquivo final.

    Raises:
        ValueError: Se a lista de páginas estiver vazia.
    """
    if not paginas:
        raise ValueError("Não há nenhuma página para juntar.")

    apresentacao = fitz.open()

    for pdf_do_slide in paginas:
        with fitz.open(stream=pdf_do_slide, filetype="pdf") as documento:
            apresentacao.insert_pdf(documento)

    apresentacao.save(str(destino), garbage=4, deflate=True)
    apresentacao.close()


# ---------------------------------------------------------------------------
# Conferência do que saiu
# ---------------------------------------------------------------------------

# Abaixo deste tamanho, em pontos, o texto é rótulo de barra ou legenda de
# gráfico. Acima, é conteúdo do slide. A separação serve para achar colisão
# entre a barra e o título sem depender de onde cada um deveria estar.
TAMANHO_MAXIMO_DO_ROTULO_DA_BARRA = 8.0

# Limites que separam a sombra chapada de um retângulo legítimo do slide. As
# faixas que os gráficos pintam — a cinza de "sem série de casos antes de 2018",
# as verdes e vermelhas de fundo — são claras; a sombra do tema é escura e
# semitransparente. Área em pontos ao quadrado: um cartão de fluxo dá cerca de
# 18.600pt², e nenhuma faixa de gráfico chega perto disso sendo escura.
LUMINANCIA_MAXIMA_DA_SOMBRA = 0.35
OPACIDADE_MINIMA_DA_SOMBRA = 0.10
OPACIDADE_MAXIMA_DA_SOMBRA = 0.60
AREA_MINIMA_DA_MANCHA_EM_PONTOS2 = 3000.0


@dataclasses.dataclass(frozen=True)
class ProblemaEncontrado:
    """Uma falha detectada na conferência do PDF.

    Attributes:
        pagina: Número da página, começando em 1.
        descricao: O que está errado, em uma frase.
    """

    pagina: int
    descricao: str


def conferir_pdf(
    caminho: pathlib.Path, slides_esperados: int, encaixe: EncaixeDoSlide
) -> list[ProblemaEncontrado]:
    """Procura no PDF gravado os defeitos que já apareceram antes.

    São três conferências, e cada uma existe por causa de um erro real de
    27/09/2026: o número de páginas (o modo antigo gerava uma folha em branco no
    fim), o tamanho de cada página (o Chrome caía em A4 paisagem e cortava o
    slide) e a colisão entre a barra e o título.

    Args:
        caminho: O PDF gravado.
        slides_esperados: Quantos slides a apresentação tem.
        encaixe: O encaixe usado, de onde sai a faixa que a barra ocupa.

    Returns:
        A lista de problemas. Vazia quando o PDF está correto.
    """
    problemas: list[ProblemaEncontrado] = []

    largura_esperada_em_pontos = GEOMETRIA.largura * 72 / PIXELS_POR_POLEGADA
    altura_esperada_em_pontos = GEOMETRIA.altura * 72 / PIXELS_POR_POLEGADA

    # O topo do slide, em pontos, é onde a barra termina de valer. Qualquer texto
    # grande acima dessa linha invadiu a faixa da barra.
    topo_do_slide_em_pixels = (
        GEOMETRIA.altura
        - GEOMETRIA.altura_do_slide * encaixe.escala
        - encaixe.deslocamento_vertical
    )
    topo_do_slide_em_pontos = topo_do_slide_em_pixels * 72 / PIXELS_POR_POLEGADA

    documento = fitz.open(str(caminho))

    try:
        if documento.page_count != slides_esperados:
            problemas.append(
                ProblemaEncontrado(
                    pagina=0,
                    descricao=(
                        f"O PDF tem {documento.page_count} páginas e a "
                        f"apresentação tem {slides_esperados} slides."
                    ),
                )
            )

        for numero_da_pagina, pagina in enumerate(documento, start=1):
            largura_medida = round(pagina.rect.width, 1)
            altura_medida = round(pagina.rect.height, 1)

            if (largura_medida, altura_medida) != (
                round(largura_esperada_em_pontos, 1),
                round(altura_esperada_em_pontos, 1),
            ):
                problemas.append(
                    ProblemaEncontrado(
                        pagina=numero_da_pagina,
                        descricao=(
                            f"Página de {largura_medida}x{altura_medida}pt, "
                            f"esperado {largura_esperada_em_pontos:.0f}x"
                            f"{altura_esperada_em_pontos:.0f}pt."
                        ),
                    )
                )

            texto_grande_na_faixa_da_barra = _procurar_texto_acima_da_linha(
                pagina, topo_do_slide_em_pontos
            )

            if texto_grande_na_faixa_da_barra:
                problemas.append(
                    ProblemaEncontrado(
                        pagina=numero_da_pagina,
                        descricao=(
                            "Texto do slide dentro da faixa da barra: "
                            f"{texto_grande_na_faixa_da_barra!r}."
                        ),
                    )
                )

            area_da_mancha = _medir_maior_sombra_chapada(pagina)

            if area_da_mancha > 0:
                problemas.append(
                    ProblemaEncontrado(
                        pagina=numero_da_pagina,
                        descricao=(
                            f"Mancha de sombra chapada de {area_da_mancha:.0f}pt² "
                            "atrás de um cartão."
                        ),
                    )
                )
    finally:
        documento.close()

    return problemas


def _medir_maior_sombra_chapada(pagina) -> float:
    """Mede a maior mancha escura que o Chrome deixou no lugar de uma sombra.

    Quando o Chrome não consegue escrever o borrão de um `box-shadow` em vetor,
    ele o troca por um retângulo chapado e semitransparente do tamanho do cartão.
    Foi o que aconteceu no slide 3 até 27/09/2026. A folha de estilo do modo PDF
    já evita a sombra que causava isso; esta conferência existe para avisar se
    outra sombra do tema voltar a cair no mesmo buraco.

    Args:
        pagina: A página do PDF.

    Returns:
        A área da maior mancha, em pontos ao quadrado, ou 0,0 se não houver.
    """
    maior_area = 0.0

    for desenho in pagina.get_drawings():
        preenchimento = desenho.get("fill")
        opacidade = desenho.get("fill_opacity")

        if preenchimento is None or opacidade is None:
            continue
        if not OPACIDADE_MINIMA_DA_SOMBRA <= opacidade <= OPACIDADE_MAXIMA_DA_SOMBRA:
            continue

        vermelho, verde, azul = preenchimento
        luminancia = 0.2126 * vermelho + 0.7152 * verde + 0.0722 * azul

        if luminancia > LUMINANCIA_MAXIMA_DA_SOMBRA:
            continue

        area = desenho["rect"].width * desenho["rect"].height

        if area >= AREA_MINIMA_DA_MANCHA_EM_PONTOS2 and area > maior_area:
            maior_area = area

    return maior_area


def _procurar_texto_acima_da_linha(pagina, linha_em_pontos: float) -> str:
    """Devolve o primeiro texto de corpo que sobe além da linha informada.

    Args:
        pagina: A página do PDF.
        linha_em_pontos: A altura, em pontos, onde o slide começa.

    Returns:
        O texto invasor, ou string vazia se não houver nenhum.
    """
    for bloco in pagina.get_text("dict")["blocks"]:
        if bloco["type"] != 0:
            continue

        for linha in bloco["lines"]:
            for trecho in linha["spans"]:
                if trecho["size"] <= TAMANHO_MAXIMO_DO_ROTULO_DA_BARRA:
                    continue
                if trecho["bbox"][1] >= linha_em_pontos:
                    continue
                if not trecho["text"].strip():
                    continue

                return trecho["text"].strip()[:40]

    return ""


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------


def gerar_pdf_da_pagina(nome_da_pagina: str) -> pathlib.Path:
    """Gera o PDF de uma página do site e confere o resultado.

    Args:
        nome_da_pagina: O arquivo dentro de `saida/`, como `seminario.html`.

    Returns:
        O caminho do PDF gravado.

    Raises:
        FileNotFoundError: Se a página não existir em `saida/`.
        RuntimeError: Se a conferência final encontrar problemas.
    """
    origem = PASTA_DE_SAIDA / nome_da_pagina

    if not origem.is_file():
        raise FileNotFoundError(
            f"Página não encontrada: {origem}\nRode 'python3 gerar.py' antes."
        )

    destino = PASTA_DE_SAIDA / f"{origem.stem}.pdf"

    print(f"Gerando o PDF de {nome_da_pagina}...")

    navegador = Navegador(largura=LARGURA_DA_JANELA, altura=ALTURA_DA_JANELA)

    try:
        navegador.abrir(origem)
        encaixe = entrar_no_modo_pdf(navegador)
        total_de_slides = contar_slides(navegador)

        print(
            f"   {total_de_slides} slides · slide a {encaixe.escala:.1%} "
            f"da tela fixa, abaixo da barra"
        )

        paginas: list[bytes] = []

        for posicao in range(total_de_slides):
            paginas.append(imprimir_um_slide(navegador, posicao))
    finally:
        navegador.fechar()

    juntar_paginas(paginas, destino)

    problemas = conferir_pdf(destino, total_de_slides, encaixe)

    tamanho_em_megabytes = destino.stat().st_size / 1_000_000
    print(f"   {len(paginas)} páginas · {tamanho_em_megabytes:.1f} MB")

    if problemas:
        for problema in problemas:
            onde = f"página {problema.pagina}" if problema.pagina else "arquivo"
            print(f"   🔴 {onde}: {problema.descricao}")

        raise RuntimeError(f"{len(problemas)} problema(s) no PDF gerado.")

    print("   ✅ páginas no tamanho certo, sem colisão com a barra e sem mancha de sombra")
    print(f"   {destino}")

    return destino


def main() -> int:
    """Ponto de entrada da linha de comando.

    Returns:
        0 quando o PDF sai correto, 1 quando algo falha.
    """
    nome_da_pagina = sys.argv[1] if len(sys.argv) > 1 else PAGINA_PADRAO

    try:
        gerar_pdf_da_pagina(nome_da_pagina)
    except (FileNotFoundError, RuntimeError, ValueError) as erro:
        print(f"🔴 {erro}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
