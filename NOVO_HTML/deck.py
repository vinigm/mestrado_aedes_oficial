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
        rotulo: Versalete no topo, que situa o slide dentro da apresentação.
        titulo: A frase que o slide defende. Uma por slide.
        corpo: HTML do miolo, já montado com os blocos de `layout`.
        nota: Lembrete para quem apresenta. Fica só no código — a página
            mostra apenas a apresentação.
    """

    rotulo: str
    titulo: str
    corpo: str
    nota: str = ""


FOLHA_DE_ESTILO_DO_DECK = """
.deck{margin:0 0 20px}

.deckPalco{position:relative; background:var(--fundo);
  border:1px solid var(--borda); border-radius:var(--raio-g);
  box-shadow:var(--sombra); overflow:hidden;
  aspect-ratio:16/9; min-height:420px}

.deckSlide{position:absolute; inset:0; padding:40px 48px;
  display:none; flex-direction:column; overflow:auto}
.deckSlide.ativo{display:flex}

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
}
"""


SCRIPT_DO_DECK = """
(function(){
  var slides = Array.prototype.slice.call(document.querySelectorAll('.deckSlide'));
  if (!slides.length) { return; }

  var pontos = Array.prototype.slice.call(document.querySelectorAll('.deckPonto'));
  var contador = document.getElementById('deckContador');
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
        if not slide.rotulo:
            classe += " capa"

        rotulo = ""
        if slide.rotulo:
            rotulo = f'<p class="deckRotulo">{layout.escapar(slide.rotulo)}</p>'

        blocos_de_slide.append(
            f'<section class="{classe}" id="slide-{posicao + 1}">'
            f"{rotulo}"
            f'<h2 class="deckTitulo">{layout.escapar(slide.titulo)}</h2>'
            f'<div class="deckCorpo">{slide.corpo}</div>'
            "</section>"
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
        f'<div class="deckPalco">{"".join(blocos_de_slide)}</div>'
        f"{barra}"
        "</div>"
    )
