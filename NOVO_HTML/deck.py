"""Motor de slides: monta um deck navegável dentro de uma página do site.

Cada slide é um bloco em proporção 16:9, com um só por vez na tela. A navegação
é por seta do teclado, clique nos botões ou clique no ponto do rodapé — e o
número do slide entra na URL, para que um slide específico possa ser aberto
direto por link.

O deck é feito para projetar. Isso manda no desenho: fonte grande, pouco texto
por slide, e nenhum elemento que dependa de passar o mouse por cima.
"""

import dataclasses

import layout


@dataclasses.dataclass(frozen=True)
class Slide:
    """Um slide do deck.

    Attributes:
        topico: A que parte da apresentação o slide pertence. É o que o índice
            horizontal destaca. Vazio deixa o slide fora do índice — é o caso
            da capa. Vários slides podem compartilhar o mesmo tópico.
        titulo: A frase que o slide defende. Uma por slide.
        corpo: HTML do miolo, já montado com os blocos de `layout`.
        nota: Lembrete para quem apresenta. Fica só no código — a página
            mostra apenas a apresentação.
        e_figura: Quando True, o slide é desenhado para uma figura grande: o
            título encolhe e a imagem ocupa a altura que sobra.
        e_denso: Quando True, o slide encolhe fonte e respiro — para tabela
            longa que de outro modo não caberia no palco.
        rotulo_curto: Nome do slide na trilha de progresso, em duas ou três
            palavras. Vazio repete o tópico.
    """

    topico: str
    titulo: str
    corpo: str
    nota: str = ""
    e_figura: bool = False
    e_denso: bool = False
    rotulo_curto: str = ""


FOLHA_DE_ESTILO_DO_DECK = """
.deck{margin:0 0 20px}

.deckPalco{position:relative; background:var(--fundo);
  border:1px solid var(--borda); border-radius:var(--raio-g);
  box-shadow:var(--sombra); overflow:hidden;
  aspect-ratio:16/9; min-height:440px;
  display:flex; flex-direction:column}

.deckTela{position:relative; flex:1 1 auto; min-height:0}

.deckSlide{position:absolute; inset:0; padding:32px 48px 40px;
  display:none; flex-direction:column; overflow:auto}
.deckSlide.ativo{display:flex}

/* Índice horizontal: uma trilha contínua com um marcador por tópico. A linha
   cinza atravessa tudo; a linha azul por cima cresce conforme a apresentação
   avança, e é o JS que mede a largura dela. Tópico já visto fica com o
   marcador cheio; os que ainda vêm ficam esmaecidos. */
/* Sem borda inferior: o fundo mais claro já separa o índice do slide, e a
   borda encontrava o canto arredondado do palco deixando um degrau à vista. */
.deckIndice{position:relative; display:flex; gap:2px; padding:14px 40px 10px;
  background:var(--elevado)}

.deckIndiceTrilha{position:absolute; top:0; height:2px; left:0; width:0;
  background:var(--borda); border-radius:2px}
.deckIndiceProgresso{position:absolute; top:0; height:2px; left:0; width:0;
  background:var(--acento); border-radius:2px;
  transition:width .22s ease}

.deckIndiceItem{position:relative; z-index:1; flex:1 1 0; min-width:0;
  display:flex; flex-direction:column; align-items:center; gap:8px}

.deckIndiceMarca{width:10px; height:10px; border-radius:50%;
  background:var(--fundo); border:2px solid var(--borda-forte);
  transition:background .18s ease, border-color .18s ease, transform .18s ease}
.deckIndiceItem.passado .deckIndiceMarca{background:var(--acento);
  border-color:var(--acento)}
.deckIndiceItem.atual .deckIndiceMarca{background:var(--acento);
  border-color:var(--acento); transform:scale(1.35);
  box-shadow:0 0 0 4px rgba(27,110,243,.16)}

.deckIndiceRotulos{display:flex; flex-direction:column; align-items:center;
  gap:1px; max-width:100%; min-width:0}
.deckIndiceTopico{font-size:.5rem; font-weight:600; letter-spacing:.05em;
  text-transform:uppercase; color:#C6D0DB; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; max-width:100%; transition:color .18s ease}
.deckIndiceTexto{font-size:.58rem; font-weight:650; color:#B6C2D0;
  text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  max-width:100%; transition:color .18s ease}
.deckIndiceItem.passado .deckIndiceTopico{color:#AEBAC7}
.deckIndiceItem.passado .deckIndiceTexto{color:var(--muted)}
.deckIndiceItem.atual .deckIndiceTopico{color:var(--acento)}
.deckIndiceItem.atual .deckIndiceTexto{color:var(--acento-escuro); font-weight:700}

.deckNumero{position:absolute; right:22px; bottom:16px; color:var(--faint);
  font-size:.78rem; font-variant-numeric:tabular-nums}

.deckRotulo{color:var(--acento-escuro); font-size:.72rem; font-weight:700;
  letter-spacing:.15em; text-transform:uppercase; margin:0 0 10px}
.deckTitulo{font-size:1.72rem; font-weight:680; letter-spacing:-.02em;
  line-height:1.16; margin:0 0 22px; color:var(--tinta); max-width:26ch}
.deckCorpo{flex:1 1 auto; min-height:0}
.deckCorpo p{font-size:1.02rem; max-width:62ch}
.deckCorpo .cartao{padding:14px 16px}
.deckCorpo .cartao h3{font-size:.97rem}
.deckCorpo .grade{gap:12px; margin-bottom:12px}
.deckCorpo table.tabela{font-size:.92rem}
.deckCorpo .aviso{padding:11px 14px; margin-bottom:12px}

/* A virada divide o palco com uma tabela de quatro linhas. Sem encolher, o
   ramo pendurado cai fora do slide e o palco ganha barra de rolagem. */
.deckCorpo .virada{gap:10px}
.deckCorpo .viradaCaixa{padding:10px 13px}
.deckCorpo .viradaTexto{font-size:.85rem}
.deckCorpo .viradaRotulo{font-size:.63rem; margin-bottom:4px}
.deckCorpo .viradaRamo .viradaCaixa{margin-top:8px}
.deckCorpo .viradaRamo::before{bottom:52%}
.deckCorpo .viradaRamoSeta{padding-top:8px}
.deckCorpo table.tabela + .virada{margin-top:4px}

/* Card ancorado ao pé de uma figura: cada pixel que ele economiza vira altura
   para a imagem que ele comenta. */
.deckFiguraCheia .aviso{flex:0 0 auto; margin:8px 0 0; padding:9px 13px;
  font-size:.88rem}

/* Slide cuja mensagem É a figura: ela ocupa o corpo inteiro e encolhe junto
   com o palco, para caber na altura sem rolagem. */
.deckSlide.figura .deckTitulo{font-size:1.32rem; margin-bottom:12px}
.deckFiguraCheia{height:100%; display:flex; flex-direction:column; min-height:0}
.deckFiguraCheia img{flex:1 1 auto; min-height:0; width:100%;
  object-fit:contain; object-position:top}
.deckFiguraCheia .deckFiguraLegenda{flex:0 0 auto; color:var(--muted);
  font-size:.82rem; padding-top:8px}

/* Crédito da fonte, no pé do slide: presente para quem procurar, discreto
   para quem não estiver procurando. */
.fonteDoSlide{color:var(--faint); font-size:.78rem; margin:10px 0 0}

/* Tabela longa num slide: fonte e respiro menores, para nove linhas caberem
   no palco sem rolagem. */
.deckSlide.densa .deckTitulo{font-size:1.4rem; margin-bottom:14px}
.deckSlide.densa table.tabela{font-size:.82rem}
.deckSlide.densa table.tabela td{padding:5px 12px}
.deckSlide.densa table.tabela th{padding:5px 12px 6px}

/* Agenda: um tópico por linha, numeração destacada. */
.listaAgenda{list-style:none; margin:0; padding:0}
.listaAgenda li{font-size:1.18rem; color:var(--tinta-suave); padding:7px 0;
  border-bottom:1px solid var(--borda)}
.listaAgenda li:last-child{border-bottom:none}
.listaAgenda b{color:var(--acento); font-variant-numeric:tabular-nums}

/* Capa: sem versalete, título ocupando o palco. */
.deckSlide.capa{justify-content:center}
.deckSlide.capa .deckTitulo{font-size:2.5rem; max-width:22ch; margin-bottom:16px}
.deckSlide.capa .deckCorpo{flex:0 0 auto}

.deckBarra{display:flex; align-items:center; gap:14px; margin-top:12px}
.deckBotao{flex:0 0 auto; width:34px; height:34px; border-radius:9px;
  border:1px solid var(--borda); background:var(--fundo); color:var(--tinta-suave);
  font-size:1rem; cursor:pointer; display:flex; align-items:center;
  justify-content:center; font-family:var(--fonte)}
.deckBotao:hover:not(:disabled){background:var(--elevado); color:var(--tinta)}
.deckBotao:disabled{opacity:.35; cursor:default}

.deckPontos{flex:1 1 auto; display:flex; gap:6px; flex-wrap:wrap}
.deckPonto{width:9px; height:9px; border-radius:50%; border:none; padding:0;
  background:var(--borda-forte); cursor:pointer}
.deckPonto.ativo{background:var(--acento)}
.deckPonto:hover{background:var(--acento-escuro)}

.deckContador{flex:0 0 auto; color:var(--muted); font-size:.83rem;
  font-variant-numeric:tabular-nums}

@media print{
  .deckBarra{display:none}
  .deckPalco{aspect-ratio:auto; min-height:0; border:none; box-shadow:none;
    page-break-after:always; overflow:visible; height:auto}
  .deckSlide{display:flex !important; position:static; padding:28px 0}
  #navPrimaria{display:none}
  .conteudoInterno{padding:0; max-width:none}
}

@media (max-width:900px){
  .deckPalco{aspect-ratio:auto; min-height:0}
  .deckSlide{position:static; padding:24px 20px}
  .deckSlide:not(.ativo){display:none}
  .deckTitulo{font-size:1.32rem}
  .deckSlide.capa .deckTitulo{font-size:1.7rem}
  .deckIndice{display:none}
}
"""


SCRIPT_DO_DECK = """
(function(){
  var slides = Array.prototype.slice.call(document.querySelectorAll('.deckSlide'));
  if (!slides.length) { return; }

  var pontos = Array.prototype.slice.call(document.querySelectorAll('.deckPonto'));
  var contador = document.getElementById('deckContador');
  var itensDoIndice = Array.prototype.slice.call(
    document.querySelectorAll('.deckIndiceItem')
  );
  var progressoDoIndice = document.getElementById('deckIndiceProgresso');
  var trilhaDoIndice = document.querySelector('.deckIndiceTrilha');

  // Centro de um marcador, medido em relação à barra do índice. As linhas se
  // alinham por ele, e não por um pixel fixo no CSS: assim continuam centradas
  // quando o tamanho da bolinha, a fonte ou o padding mudarem.
  function centroDoMarcador(item){
    var barra = item.parentElement.getBoundingClientRect();
    var marca = item.querySelector('.deckIndiceMarca').getBoundingClientRect();
    return {
      x: (marca.left + marca.width / 2) - barra.left,
      y: (marca.top + marca.height / 2) - barra.top,
    };
  }
  var anterior = document.getElementById('deckAnterior');
  var proximo = document.getElementById('deckProximo');
  var atual = 0;

  function mostrar(indice, trocarEndereco){
    atual = Math.max(0, Math.min(indice, slides.length - 1));

    for (var i = 0; i < slides.length; i++) {
      slides[i].classList.toggle('ativo', i === atual);
    }
    for (var j = 0; j < pontos.length; j++) {
      pontos[j].classList.toggle('ativo', j === atual);
    }
    var posicaoDoTopico = -1;
    for (var t = 0; t < itensDoIndice.length; t++) {
      if (parseInt(itensDoIndice[t].dataset.slide, 10) === atual) { posicaoDoTopico = t; }
    }
    for (var u = 0; u < itensDoIndice.length; u++) {
      itensDoIndice[u].classList.toggle('atual', u === posicaoDoTopico);
      itensDoIndice[u].classList.toggle(
        'passado', posicaoDoTopico >= 0 && u < posicaoDoTopico
      );
    }

    // As duas linhas vão de marcador a marcador: a cinza do primeiro ao
    // último, a azul do primeiro até o atual. Ancorar no centro da bolinha, e
    // não na borda da barra, é o que faz a linha terminar exatamente nela.
    if (itensDoIndice.length) {
      var centroDoPrimeiro = centroDoMarcador(itensDoIndice[0]);
      var centroDoUltimo = centroDoMarcador(itensDoIndice[itensDoIndice.length - 1]);
      var alturaDaLinha = 2;
      var topoDaLinha = centroDoPrimeiro.y - alturaDaLinha / 2;

      if (trilhaDoIndice) {
        trilhaDoIndice.style.left = centroDoPrimeiro.x + 'px';
        trilhaDoIndice.style.top = topoDaLinha + 'px';
        trilhaDoIndice.style.width = (centroDoUltimo.x - centroDoPrimeiro.x) + 'px';
      }

      if (progressoDoIndice) {
        progressoDoIndice.style.left = centroDoPrimeiro.x + 'px';
        progressoDoIndice.style.top = topoDaLinha + 'px';
        var ateOnde = posicaoDoTopico >= 0
          ? centroDoMarcador(itensDoIndice[posicaoDoTopico]).x - centroDoPrimeiro.x
          : 0;
        progressoDoIndice.style.width = Math.max(0, ateOnde) + 'px';
      }
    }

    contador.textContent = (atual + 1) + ' / ' + slides.length;
    anterior.disabled = (atual === 0);
    proximo.disabled = (atual === slides.length - 1);

    if (trocarEndereco) {
      history.replaceState(null, '', '#slide-' + (atual + 1));
    }
  }

  anterior.addEventListener('click', function(){ mostrar(atual - 1, true); });
  proximo.addEventListener('click', function(){ mostrar(atual + 1, true); });

  for (var p = 0; p < pontos.length; p++) {
    (function(indice){
      pontos[indice].addEventListener('click', function(){ mostrar(indice, true); });
    })(p);
  }

  document.addEventListener('keydown', function(evento){
    if (evento.key === 'ArrowRight' || evento.key === 'PageDown') {
      mostrar(atual + 1, true);
    } else if (evento.key === 'ArrowLeft' || evento.key === 'PageUp') {
      mostrar(atual - 1, true);
    }
  });

  window.addEventListener('resize', function(){ mostrar(atual, false); });

  var pedido = parseInt((location.hash.match(/slide-(\\d+)/) || [])[1], 10);
  mostrar(isNaN(pedido) ? 0 : pedido - 1, false);
})();
"""


def _indice_horizontal(slides: list[Slide]) -> str:
    """A trilha de progresso no topo do palco, com um marcador por slide.

    Cada marcador traz o tópico em cima e o nome curto do slide embaixo, para
    que a trilha diga não só em que parte a apresentação está, mas em que
    slide daquela parte. A capa fica de fora: ela não é conteúdo.

    Args:
        slides: Os slides, na ordem da apresentação.

    Returns:
        O HTML da trilha, ou string vazia se nenhum slide tiver tópico.
    """
    itens = []
    for posicao, slide in enumerate(slides):
        if not slide.topico:
            continue

        nome_curto = slide.rotulo_curto if slide.rotulo_curto else slide.topico

        itens.append(
            f'<div class="deckIndiceItem" data-slide="{posicao}">'
            '<span class="deckIndiceMarca"></span>'
            '<span class="deckIndiceRotulos">'
            f'<span class="deckIndiceTopico">{layout.escapar(slide.topico)}</span>'
            f'<span class="deckIndiceTexto">{layout.escapar(nome_curto)}</span>'
            "</span></div>"
        )

    if not itens:
        return ""

    return (
        '<div class="deckIndice">'
        '<div class="deckIndiceTrilha"></div>'
        '<div class="deckIndiceProgresso" id="deckIndiceProgresso"></div>'
        f'{"".join(itens)}'
        "</div>"
    )


def montar(slides: list[Slide]) -> str:
    """Monta o deck inteiro: palco, slides e barra de navegação.

    Args:
        slides: Os slides, na ordem da apresentação.

    Returns:
        O HTML do deck.

    Raises:
        ValueError: Se a lista vier vazia, caso em que não há o que montar.
    """
    if not slides:
        raise ValueError("Um deck precisa de pelo menos um slide.")

    blocos_de_slide = []
    pontos = []

    for posicao, slide in enumerate(slides):
        classe = "deckSlide ativo" if posicao == 0 else "deckSlide"
        if not slide.topico:
            classe += " capa"
        if slide.e_figura:
            classe += " figura"
        if slide.e_denso:
            classe += " densa"

        rotulo = ""
        if slide.topico:
            rotulo = f'<p class="deckRotulo">{layout.escapar(slide.topico)}</p>'

        numero = (
            f'<div class="deckNumero">{posicao + 1}</div>' if slide.topico else ""
        )

        blocos_de_slide.append(
            f'<section class="{classe}" id="slide-{posicao + 1}" '
            f'data-topico="{layout.escapar(slide.topico)}">'
            f"{rotulo}"
            f'<h2 class="deckTitulo">{layout.escapar(slide.titulo)}</h2>'
            f'<div class="deckCorpo">{slide.corpo}</div>'
            f"{numero}</section>"
        )

        classe_do_ponto = "deckPonto ativo" if posicao == 0 else "deckPonto"
        pontos.append(
            f'<button class="{classe_do_ponto}" type="button" '
            f'aria-label="Slide {posicao + 1}"></button>'
        )

    barra = (
        '<div class="deckBarra">'
        '<button class="deckBotao" id="deckAnterior" type="button" '
        'aria-label="Slide anterior">&larr;</button>'
        '<button class="deckBotao" id="deckProximo" type="button" '
        'aria-label="Próximo slide">&rarr;</button>'
        f'<div class="deckPontos">{"".join(pontos)}</div>'
        f'<div class="deckContador" id="deckContador">1 / {len(slides)}</div>'
        "</div>"
    )

    return (
        '<div class="deck">'
        '<div class="deckPalco">'
        f"{_indice_horizontal(slides)}"
        f'<div class="deckTela">{"".join(blocos_de_slide)}</div>'
        "</div>"
        f"{barra}"
        "</div>"
    )
