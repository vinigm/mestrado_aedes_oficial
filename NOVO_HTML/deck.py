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
    """

    topico: str
    titulo: str
    corpo: str
    nota: str = ""
    e_figura: bool = False
    e_denso: bool = False


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

/* Índice horizontal: mostra os tópicos e onde a apresentação está. O tópico
   atual fica azul e com a barrinha cheia; os já passados ficam em cinza médio,
   e os que ainda vêm, em cinza claro. */
.deckIndice{display:flex; gap:0; border-bottom:1px solid var(--borda);
  padding:0 48px; background:var(--elevado)}
.deckIndiceItem{flex:1 1 0; min-width:0; padding:11px 10px 9px;
  border-bottom:2px solid transparent; font-size:.7rem; font-weight:650;
  letter-spacing:.02em; color:var(--faint); text-align:center;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.deckIndiceItem.passado{color:var(--muted)}
.deckIndiceItem.atual{color:var(--acento-escuro); border-bottom-color:var(--acento)}

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
    var topicoAtual = slides[atual].dataset.topico || '';
    var posicaoDoTopico = -1;
    for (var t = 0; t < itensDoIndice.length; t++) {
      if (itensDoIndice[t].dataset.topico === topicoAtual) { posicaoDoTopico = t; }
    }
    for (var u = 0; u < itensDoIndice.length; u++) {
      itensDoIndice[u].classList.toggle('atual', u === posicaoDoTopico);
      itensDoIndice[u].classList.toggle(
        'passado', posicaoDoTopico >= 0 && u < posicaoDoTopico
      );
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

  var pedido = parseInt((location.hash.match(/slide-(\\d+)/) || [])[1], 10);
  mostrar(isNaN(pedido) ? 0 : pedido - 1, false);
})();
"""


def _topicos_em_ordem(slides: list[Slide]) -> list[str]:
    """Lista os tópicos na ordem em que aparecem, sem repetir.

    Args:
        slides: Os slides do deck.

    Returns:
        Os nomes dos tópicos, uma vez cada. Slide sem tópico (a capa) não
        entra.
    """
    topicos: list[str] = []
    for slide in slides:
        if slide.topico and slide.topico not in topicos:
            topicos.append(slide.topico)

    return topicos


def _indice_horizontal(topicos: list[str]) -> str:
    """A barra de tópicos no topo do palco.

    O item de cada tópico ganha um `data-topico`, e o JS é quem marca qual
    está atual — assim o índice não precisa ser redesenhado a cada slide.

    Args:
        topicos: Os tópicos, na ordem da apresentação.

    Returns:
        O HTML do índice, ou string vazia se não houver tópico.
    """
    if not topicos:
        return ""

    itens = []
    for topico in topicos:
        itens.append(
            f'<div class="deckIndiceItem" data-topico="{layout.escapar(topico)}">'
            f"{layout.escapar(topico)}</div>"
        )

    return f'<div class="deckIndice">{"".join(itens)}</div>'


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

    topicos = _topicos_em_ordem(slides)

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
        f"{_indice_horizontal(topicos)}"
        f'<div class="deckTela">{"".join(blocos_de_slide)}</div>'
        "</div>"
        f"{barra}"
        "</div>"
    )
