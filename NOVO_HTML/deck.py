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

/* No estilo de projecao a faixa de graficos ganha ar em cima, separando-a da
   tabela, e perde a margem de baixo quando e o ultimo elemento do slide —
   ali ela so empurrava o conteudo para longe da borda inferior. O espaco que
   sobra vai para a altura dos proprios graficos. */
.deckPalco.semMoldura .graficosLadoALado{margin-top:18px}
.deckPalco.semMoldura .graficosLadoALado:last-child{margin-bottom:0}

/* Palco sem moldura: sai a borda, o arredondamento e a sombra, e o slide
   passa a ocupar a tela sem o contorno de cartao. Num deck que vai a projecao
   a moldura nao serve para nada — ela so existe para separar o deck do resto
   da pagina, e numa apresentacao nao ha resto. */
.deckPalco.semMoldura{border:none; border-radius:0; box-shadow:none}

.deckTela{position:relative; flex:1 1 auto; min-height:0; overflow:hidden}

/* O slide e uma TELA FIXA de 1280x720, como um slide de apresentacao de
   verdade. O tamanho nao muda com a janela: o que muda e a escala aplicada
   pelo script, que encolhe tudo junto para caber no palco.

   Por que assim: antes o slide era fluido e tinha `overflow:auto`. Numa janela
   estreita o conteudo transbordava e virava rolagem — o que num PDF ou num
   projetor significa conteudo cortado. Com tela fixa, o que cabe no desenho
   cabe em qualquer tamanho, e o que nao cabe aparece como problema na hora de
   montar o slide, nao na hora de apresentar. */
.deckSlide{position:absolute; top:0; left:0;
  width:1280px; height:720px; padding:40px 56px 48px;
  transform-origin:top left;
  display:none; flex-direction:column; overflow:hidden}
.deckSlide.ativo{display:flex}

/* Linha de legenda sob uma tabela, para explicar o que aparece no grafico
   seguinte sem gastar a altura de um aviso inteiro. */
.deckNotaDeGrafico{margin:6px 0 2px; font-size:.78rem; color:var(--muted)}

/* Duas colunas: documento a esquerda, leitura do documento a direita. Serve
   para por uma imagem de prova ao lado da tabela que a traduz. */
.deckDuasColunas{display:grid; grid-template-columns:1.35fr 1fr; gap:22px;
  align-items:start; min-height:0}
.deckDuasColunas img{width:100%; height:auto; display:block;
  border:1px solid var(--borda); border-radius:6px}
.deckFonte{margin:6px 0 0; font-size:.68rem; color:var(--faint)}

/* Formula matematica montada a mao, porque o site nao carrega renderizador.
   A fracao e empilhada com uma borda fazendo as vezes do traco. */
.deckFormula{display:flex; align-items:center; justify-content:center;
  gap:14px; margin:18px 0 6px; font-size:1.15rem; color:var(--tinta)}
.deckFormulaTermo{display:flex; flex-direction:column; align-items:center; gap:3px}
.deckFormulaValor{font-weight:700; font-variant-numeric:tabular-nums}
.deckFormulaRotulo{font-size:.62rem; font-weight:600; letter-spacing:.03em;
  text-transform:uppercase; color:var(--muted); white-space:nowrap}
.deckFormulaOperador{font-size:1.25rem; color:var(--muted)}
.deckFracao{display:flex; flex-direction:column; align-items:center;
  font-variant-numeric:tabular-nums}
.deckFracaoTopo{padding:0 8px 2px; font-weight:700}
.deckFracaoBase{padding:2px 8px 0; font-weight:700;
  border-top:1.5px solid var(--tinta)}
.deckFormulaResultado .deckFormulaValor{font-size:1.75rem; color:var(--acento)}

/* Dois blocos com uma seta entre eles, para slide de transicao: o da esquerda
   e o que ja existe, o da direita e o que vai ser construido com ele. */
.deckFluxoDeDois{display:flex; align-items:center; justify-content:center;
  gap:34px; padding:10px 0; height:100%}
.deckFluxoBloco{flex:1 1 0; max-width:420px; display:flex; flex-direction:column;
  justify-content:center; gap:10px; padding:34px 30px;
  border:2px solid var(--borda-forte); border-radius:var(--raio-g);
  background:var(--fundo); text-align:center}
.deckFluxoBloco.destaque{border-color:var(--acento); background:var(--acento-suave)}
.deckFluxoTitulo{font-size:1.3rem; font-weight:700; color:var(--tinta);
  line-height:1.2}
.deckFluxoBloco.destaque .deckFluxoTitulo{color:var(--acento-escuro)}
.deckFluxoTexto{font-size:.92rem; color:var(--muted); line-height:1.35}
.deckFluxoSeta{display:flex; align-items:center; font-size:2.6rem;
  color:var(--acento); font-weight:300}

/* Duas tabelas lado a lado, para comparar dois sistemas sem empilhar colunas
   pareadas numa tabela so — que foi o que confundiu na primeira versao. */
.deckTabelasLadoALado{display:grid; grid-template-columns:1fr 1fr; gap:20px;
  align-items:start; margin-top:20px}
.deckTabelaRotulo{margin:0 0 5px; font-size:.78rem; font-weight:700;
  letter-spacing:.04em; text-transform:uppercase}

/* Segunda linha de um rotulo de tabela, para separar a PERGUNTA da medida que
   a responde: a pergunta fica em negrito e a medida, aqui, menor e mais leve.
   Sem isso as duas leituras disputam o mesmo peso e a coluna vira ruido. */
.deckSubrotulo{display:block; font-weight:400; font-size:.82em;
  color:var(--muted); letter-spacing:0}

/* A regua historica que fica sob uma tabela, mostrando de que trecho da serie
   veio o treino e qual trecho foi avaliado. O `height:auto` e proposital: o
   desenho mantem a propria proporcao e so acompanha a largura da coluna, para
   que o texto dentro dele nao estique junto. */
/* O rotulo da SEGUNDA regua precisa de ar acima, senao ele encosta no eixo de
   anos da primeira e as duas figuras leem como uma so. */
.deckRotuloDaSegundaRegua{margin-top:14px}
/* A linha de numeros sob o titulo de cada regua. Todo o texto que vivia DENTRO
   do desenho veio para ca: o grafico le-se de longe, os numeros de perto. */
/* A coluna das dificuldades do slide de proximos passos: ela e ressalva, e nao
   um terceiro cenario, entao vem sem cor de fundo e com o texto mais leve. */
.oQueTrava{color:var(--muted); font-size:.93em}

/* O selo dos estudos que rodam em producao, e nao so em artigo: no panorama da
   literatura sao dois de seis, e essa e a informacao mais dura do slide. */
.seloOperacional{display:inline-block; margin-left:8px; padding:1px 7px;
  border-radius:9px; background:#E8F1FE; color:#12559C; font-size:.66rem;
  font-weight:700; letter-spacing:.04em; text-transform:uppercase;
  vertical-align:middle}

/* A tabela chegou a ser apertada para caber com a ressalva embaixo; com a
   ressalva fora, sobraram 163px e eles voltaram para o espacamento — este slide
   e sete linhas de texto, e precisa ser lido de longe. */
.panoramaDaLiteratura table{font-size:.94rem}
/* As duas tabelas do panorama — as referencias e a nossa — dividem a MESMA
   grade de larguras, senao as colunas nao se alinhariam de uma para a outra e a
   separacao viraria confusao. */
.panoramaDaLiteratura table{table-layout:fixed}
.panoramaDaLiteratura th:nth-child(1), .panoramaDaLiteratura td:nth-child(1){width:13%}
.panoramaDaLiteratura th:nth-child(2), .panoramaDaLiteratura td:nth-child(2){width:12%}
.panoramaDaLiteratura th:nth-child(3), .panoramaDaLiteratura td:nth-child(3){width:8%}
.panoramaDaLiteratura th:nth-child(4), .panoramaDaLiteratura td:nth-child(4){width:19%}
.panoramaDaLiteratura th:nth-child(5), .panoramaDaLiteratura td:nth-child(5){width:24%}
/* A coluna das condicoes e comentario, nao dado: vem mais leve, para nao
   disputar a leitura com o veredito ao lado. */
.condicoesDoEstudo{color:var(--muted); font-size:.92em}

/* A tabela deste projeto vem abaixo, com o cabecalho escondido: as colunas ja
   foram nomeadas acima, e repeti-las so encheria o slide. */
.rotuloDesteProjeto{margin:18px 0 4px; font-size:.72rem; font-weight:700;
  letter-spacing:.06em; text-transform:uppercase; color:#12559C}
.tabelaDesteProjeto thead{display:none}
.tabelaDesteProjeto table{background:#F4F7FB}
.tabelaDesteProjeto td{border-top:1px solid #D6E0EC; border-bottom:none}
.linhaDesteProjeto{color:#12559C}
/* A coluna da serie nao quebra: "23 anos · até 2021" em duas linhas desalinha a
   tabela inteira, e ela e estreita o bastante para isso acontecer. */
.serieDoEstudo{white-space:nowrap}
.panoramaDaLiteratura table td, .panoramaDaLiteratura table th{line-height:1.45;
  padding:7px 11px}


/* A regua e a sua tabela dividem a linha: a figura diz o QUANTO e a tabela diz
   o TANTO. `align-items:center` alinha as duas pelo meio, porque elas nunca tem
   exatamente a mesma altura. */
.reguaComTabela{display:grid; grid-template-columns:1fr 386px; gap:20px;
  align-items:center; margin-top:4px}
.reguaComTabela svg{display:block; width:100%; height:auto}
/* A tabela ao lado da regua vem COMPACTA: com o espacamento normal do deck ela
   media 239px contra os 184px da figura, e o slide estourava. */
.reguaComTabela table td, .reguaComTabela table th{padding:3px 9px}
.reguaComTabela table{font-size:.85rem}
/* O que mandava na altura da tabela era a ENTRELINHA herdada do corpo, de 1,6 —
   nao o padding nem a fonte. Com 1,25 a tabela passou de 179px para caber ao
   lado da figura. */
.reguaComTabela table td, .reguaComTabela table th{line-height:1.25}

/* Um paragrafo a esquerda e uma figura a direita, dividindo a largura. Existe
   para aproveitar o espaco que sobra embaixo de uma tabela alta: em largura
   cheia o texto ocupa tres linhas e deixa metade do slide vazia. */
/* A figura leva mais largura que o texto: ela e o que precisa ser lido de
   longe, e o paragrafo apenas acompanha.

   ⚠️ A margem do topo precisa ser MAIOR que a margem de baixo da tabela acima
   (26px), porque as duas colapsam e vence a maior. Um valor menor que 26 nao
   afasta nada — foi o que aconteceu com os 8px da primeira versao. */
.deckTextoEFigura{display:grid; grid-template-columns:43% 1fr; gap:20px;
  align-items:center; margin:44px 0 0}
.deckTextoEFigura p{margin:0}
.deckTextoEFigura img{display:block; width:100%; height:auto}

/* Linha vencedora: retangulo bem claro e translucido, marcando em qual
   horizonte aquele sistema leva. O fundo vai nas celulas, e nao no <tr>,
   porque linha de tabela nao aceita border-radius. */
.linhaVencedora td{background:rgba(27,110,243,.055);
  box-shadow:inset 0 1px 0 rgba(27,110,243,.16),
             inset 0 -1px 0 rgba(27,110,243,.16)}
.linhaVencedora td:first-child{box-shadow:inset 1px 1px 0 rgba(27,110,243,.16),
  inset 0 -1px 0 rgba(27,110,243,.16)}
.linhaVencedora td:last-child{box-shadow:inset -1px 1px 0 rgba(27,110,243,.16),
  inset 0 -1px 0 rgba(27,110,243,.16)}

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

/* Trilha POR SECAO: uma marca por slide, agrupadas pelo topico, com o nome
   do topico aparecendo UMA vez por grupo. Resolve o impasse entre as duas
   versoes anteriores — a com rotulo em cada slide repetia "RESULTADOS" onze
   vezes, e a so com bolinhas nao dizia em que parte da apresentacao se esta.

   Os grupos tem largura igual; quem conta o peso de cada parte e a densidade
   de marcas dentro dele. */
.deckIndice.porSecao{display:flex; gap:18px; align-items:flex-start;
  padding:12px 40px 10px}
/* `fit-content` no minimo: uma secao de UM slide ficaria com 55px e cortaria
   "Proximos passos" em "PROXIMO...". Assim o grupo nunca fica menor que o
   proprio nome, e a proporcionalidade continua valendo no espaco que sobra. */
/* Todas as secoes com a MESMA largura, e nao proporcional ao numero de slides.
   A versao proporcional foi tentada em 27/09/2026: ela contava o peso de cada
   parte, mas deixava a barra irregular, com Resultados ocupando metade e as
   secoes de um slide espremidas. O Vinicius preferiu a regua uniforme.

   `min-width:fit-content` continua como piso: sem ele, "Proximos passos"
   cortava em "PROXIMO...". */
.deckSecao{flex:1 1 0; display:flex; flex-direction:column; align-items:center;
  gap:7px; min-width:fit-content}
.deckSecaoMarcas{display:flex; align-items:center; justify-content:center;
  gap:6px; width:100%; height:12px}
.deckSecaoNome{font-size:.5rem; font-weight:700; letter-spacing:.06em;
  text-transform:uppercase; color:#C6D0DB; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; max-width:100%; transition:color .18s ease}
.deckSecao.ativa .deckSecaoNome{color:var(--acento)}
.deckSecao.vista .deckSecaoNome{color:#AEBAC7}

/* A marca e um TRACO, e nao uma bolinha: em grupo, tracos verticais leem como
   uma regua de progresso, e circulos leem como uma lista de itens soltos. */
.deckIndice.porSecao .deckIndiceItem{flex:0 0 auto}
.deckIndice.porSecao .deckIndiceMarca{width:2px; height:10px; border:none;
  border-radius:1px; background:var(--borda-forte)}
.deckIndice.porSecao .deckIndiceItem.passado .deckIndiceMarca{
  background:#A9C9F7}
.deckIndice.porSecao .deckIndiceItem.atual .deckIndiceMarca{
  background:var(--acento); height:14px; transform:none; box-shadow:none}

/* Trilha so com bolinhas: alem de perder os rotulos, ela perde tambem o azul
   forte. Sem texto ao redor, a linha cheia no acento virava o elemento mais
   chamativo da tela, competindo com o proprio slide. Aqui ela fica num azul
   bem mais claro — continua legivel como progresso, e para de gritar. */
.deckIndice.soBolinhas .deckIndiceProgresso{background:#A9C9F7}
.deckIndice.soBolinhas .deckIndiceItem.passado .deckIndiceMarca{
  background:#A9C9F7; border-color:#A9C9F7}
.deckIndice.soBolinhas .deckIndiceItem.atual .deckIndiceMarca{
  background:#7FAEF2; border-color:#7FAEF2;
  box-shadow:0 0 0 4px rgba(27,110,243,.10)}

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



/* Card ancorado ao pé de uma figura: cada pixel que ele economiza vira altura
   para a imagem que ele comenta. */
.deckFiguraCheia .aviso{flex:0 0 auto; margin:8px 0 0; padding:9px 13px;
  font-size:.88rem}

/* Slide cuja mensagem É a figura: ela ocupa o corpo inteiro e encolhe junto
   com o palco, para caber na altura sem rolagem. */
/* 🔴 COLISAO DE CSS, e nao um estilo escolhido: o deck poe a classe `figura`
   no proprio <section> do slide, e o tema do site ja tem `.figura` para um
   componente de cartao — com borda de 1px, raio de 14px, sombra e margem
   inferior de 20px. Tudo isso vazava para dentro do slide, e era so nos slides
   de figura que aparecia o contorno.

   Aqui o vazamento e anulado no estilo de projecao. ⚠️ A colisao continua
   existindo nos outros decks; a correcao de raiz e renomear a classe do deck
   para algo com prefixo, o que mexe em todos eles. */
.deckPalco.semMoldura .deckSlide.figura{border:none; border-radius:0;
  box-shadow:none; margin:0}

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

/* A copia da trilha que so existe na impressao. Na tela ela fica escondida —
   quem manda ali e a barra do topo do palco, que o JS anima. */
.deckTrilhaImpressa{display:none}

/* O botao de salvar em PDF. Ele chama `window.print()`, e quem faz o trabalho
   e o `@media print` abaixo, que poe cada slide numa pagina de 1280x720.
   ⚠️ **Nao existe baixar direto**: uma pagina HTML nao gera PDF sozinha. As
   bibliotecas que "baixam" (jsPDF, html2pdf) RASTERIZAM o conteudo — os SVGs
   dos graficos virariam imagem, o texto deixaria de ser selecionavel e o
   arquivo ficaria muito maior. Pela impressao o PDF sai vetorial. Por isso o
   rotulo diz "Salvar em PDF", e nao "Baixar": o botao abre o dialogo, e quem
   salva e o usuario. */
.deckBotaoPdf{flex:0 0 auto; margin-left:auto; padding:7px 14px;
  border:1px solid var(--borda-forte); border-radius:9px; background:var(--cartao);
  color:var(--muted); font:inherit; font-size:.8rem; font-weight:600;
  cursor:pointer}
.deckBotaoPdf:hover{background:var(--elevado); color:var(--tinta);
  border-color:var(--acento)}

/* A impressao vira o PDF da apresentacao: uma pagina por slide, no mesmo
   1280x720 da tela fixa. Tres coisas precisam ser desfeitas aqui, e todas com
   `!important`, porque o JS de escala escreve `transform` INLINE em cada slide:
   a escala, o posicionamento absoluto e o `display:none` dos inativos. */
@media print{
  /* O tamanho da pagina vai em POLEGADAS, nao em pixels: o Chrome ignora
     `size` em px e cai no papel do dialogo — na pratica A4 paisagem, que tem
     1123px de largura contra os 1280px do slide. O resultado era o slide
     reduzido para caber na largura, com uma faixa branca de ~160px embaixo.
     13,333in x 7,5in sao exatamente 1280x720 a 96dpi, e e tambem o tamanho de
     um slide widescreen de PowerPoint. */
  @page{size:13.333in 7.5in; margin:0}
  /* Qualquer sobra de altura depois do ultimo slide — uma margem, um padding,
     um `min-height` — vira uma pagina em branco no fim do PDF. Por isso os
     containers sao zerados aqui, e nao so escondidos. */
  html, body{margin:0 !important; padding:0 !important; background:#fff;
    height:auto !important; min-height:0 !important}
  .conteudoInterno, .deck, .deckPalco, .deckTela{margin:0 !important;
    padding:0 !important; min-height:0 !important}

  /* 🔴 A pagina do PDF tem sempre 1280px, mas o Chrome avalia as media queries
     de LARGURA pela janela, e nao pela pagina. Numa janela estreita — que e o
     caso comum, e o do `--headless`, que abre em 800px — as regras de tela
     pequena disparam NO MEIO da impressao e quebram o slide: os tres graficos
     lado a lado empilham e ganham `max-width:620px`, o que estoura os 720px de
     altura e sai cortado no PDF. As regras abaixo desfazem, uma a uma, tudo o
     que as media queries de 640 a 1180px mexem no deck. */
  .graficosLadoALado{grid-auto-flow:column !important;
    grid-auto-columns:minmax(0,1fr) !important; gap:20px !important}
  .graficosLadoALado .grafico{max-width:none !important}
  .grade2{grid-template-columns:repeat(2,minmax(0,1fr)) !important}
  .grade3{grid-template-columns:repeat(3,minmax(0,1fr)) !important}
  .grade4{grid-template-columns:repeat(4,minmax(0,1fr)) !important}
  .fluxo{flex-wrap:nowrap !important}
  .fluxoEtapa{flex:1 1 0 !important}
  .fluxoSeta{display:flex !important}
  .deckTitulo{font-size:1.72rem !important}
  .deckSlide.capa .deckTitulo{font-size:2.5rem !important}
  /* O `.rodape` do site vinha DEPOIS do deck e, como o ultimo slide quebra
     pagina, ganhava uma 22a pagina so para ele. */
  .deckBarra, #navPrimaria, .rodape{display:none !important}
  /* A trilha do topo do palco sai — quem aparece e a copia que o JS poe dentro
     de cada slide, ja com a secao daquela pagina acesa. */
  .deckPalco > .deckIndice{display:none !important}
  /* A copia ocupa o lugar do respiro que o slide tinha no topo: o padding cai
     de 40px para 6px e a barra come 34px, entao o titulo continua comecando na
     mesma altura de antes e nenhum slide perde espaco de conteudo. */
  /* 🔴 A trilha sai do FLUXO e vai para o topo absoluto do slide. No fluxo ela
     era o primeiro filho de um flex column, e nos slides centralizados — a capa
     e o fecho — descia para o meio da pagina junto com o resto. Absoluta, ela
     fica no topo em todos, e de quebra nao consome altura nenhuma: cabe dentro
     dos 40px de padding que o slide ja tinha, entao nenhum slide perde espaco
     de conteudo (o 10, que tem 13px de folga, era o teste). */
  /* 🔴 O orcamento e de 46px de padding no topo, e nao mais: medido slide a
     slide, em 52px o slide 14 ja estoura. Como a barra precisa caber ai DENTRO
     e ainda sobrar separacao visivel ate o rotulo do slide, ela vem menor no
     papel do que na tela — nome e marcas reduzidos. */
  .deckTrilhaImpressa{display:block !important; position:absolute;
    top:3px; left:56px; right:56px}
  .deckTrilhaImpressa .deckIndice{display:flex !important; padding:0 0 3px;
    background:none; border-bottom:1px solid var(--borda)}
  /* O rotulo do slide sai no papel: ele repete, em texto, a mesma secao que a
     barra ja mostra acesa logo acima — e era ele que colidia com os nomes da
     trilha. Sem ele o titulo sobe e o slide ganha o espaco de volta. */
  .deckSlide .deckRotulo{display:none !important}
  .deckTrilhaImpressa .deckSecaoNome{font-size:.42rem}
  .deckTrilhaImpressa .deckIndice.porSecao .deckIndiceMarca{height:7px}
  .deckTrilhaImpressa .deckSecaoMarcas{margin-bottom:3px}
  .deck, .deckPalco, .deckTela{display:block !important; position:static !important;
    aspect-ratio:auto; min-height:0; height:auto; border:none; box-shadow:none;
    overflow:visible !important; background:#fff}
  /* `position:relative` e o que ancora a trilha absoluta acima. O `scale` da o
     respiro que faltava: o conteudo foi desenhado para preencher 1280x720 numa
     projecao, e no papel isso fica sufocado. A 88% sobra uma margem de ~6% em
     volta, e o layout interno nao muda — o `transform` e visual, a caixa
     continua com 1280x720 e uma pagina por slide. */
  .deckSlide{display:flex !important; position:relative !important;
    transform:scale(.88) !important; transform-origin:center center;
    width:1280px; height:720px; padding:50px 56px 48px; overflow:hidden;
    page-break-before:always; break-before:page}
  /* A quebra vai ANTES de cada slide, e nao depois. Com `break-after` o ultimo
     slide quebrava a pagina no fim e o PDF saia com uma 22a pagina em branco —
     e o `:last-child{break-after:auto}` nao dava conta. Quebrando antes, o
     primeiro slide e a excecao e nao sobra nada no fim. */
  .deckSlide:first-child{page-break-before:auto; break-before:auto}
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
// Escala os slides para que a tela fixa de 1280x720 caiba no palco, do mesmo
// jeito que um projetor encaixa um slide de apresentacao. Roda na carga, a
// cada mudanca de tamanho da janela e quando o menu lateral recolhe.
(function ajustarEscalaDosSlides() {
  var LARGURA_DA_TELA = 1280;
  var ALTURA_DA_TELA = 720;

  function aplicar() {
    var tela = document.querySelector(".deckTela");
    if (!tela) return;
    var escala = Math.min(
      tela.clientWidth / LARGURA_DA_TELA,
      tela.clientHeight / ALTURA_DA_TELA
    );
    var sobra = (tela.clientWidth - LARGURA_DA_TELA * escala) / 2;
    var slides = document.querySelectorAll(".deckSlide");
    for (var i = 0; i < slides.length; i++) {
      slides[i].style.transform =
        "translateX(" + sobra.toFixed(1) + "px) scale(" + escala.toFixed(4) + ")";
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", aplicar);
  } else {
    aplicar();
  }
  window.addEventListener("resize", aplicar);
})();

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
    var trilha = item.closest('.deckIndice');
    var barra = trilha.getBoundingClientRect();
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

    // A seção do slide atual fica destacada, e as anteriores marcadas como
    // vistas. É o que faz o nome do tópico acender quando se entra nele.
    var secoes = document.querySelectorAll('.deckSecao');
    for (var v = 0; v < secoes.length; v++) {
      var marcasDaSecao = secoes[v].querySelectorAll('.deckIndiceItem');
      var temAtual = false;
      var todasPassadas = marcasDaSecao.length > 0;
      for (var w = 0; w < marcasDaSecao.length; w++) {
        if (marcasDaSecao[w].classList.contains('atual')) { temAtual = true; }
        if (!marcasDaSecao[w].classList.contains('passado')) { todasPassadas = false; }
      }
      secoes[v].classList.toggle('ativa', temAtual);
      secoes[v].classList.toggle('vista', todasPassadas && !temAtual);
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

  // No PDF a trilha precisa aparecer em TODA pagina, e cada uma com a sua
  // secao acesa. Ela nao pode ser copiada pronta: o JS posiciona as duas
  // linhas em pixels, medindo o DOM, entao um HTML estatico sairia com a barra
  // sem linha nenhuma. A saida e passar por cada slide, deixar o proprio
  // `mostrar()` pintar a barra de verdade, e so entao clonar o resultado — com
  // os estilos ja calculados — para dentro daquele slide.
  function prepararTrilhaParaImpressao() {
    var trilha = document.querySelector('.deckPalco > .deckIndice');
    if (!trilha) { return; }

    var slidesDoDeck = document.querySelectorAll('.deckSlide');
    var voltarPara = atual;
    var copias = [];

    // 🔴 As duas linhas da trilha sao posicionadas em PIXELS, medidos do DOM.
    // Se a barra for medida com a largura que ela tem no palco e depois colada
    // num slide de outra largura, a linha para no meio do caminho. Por isso a
    // barra original e posta, ANTES de medir, exatamente nas condicoes que tera
    // no PDF: 1168px de largura — 1280 do slide menos os 56px de cada margem —
    // e o mesmo padding. Ao fim tudo volta ao que era.
    var LARGURA_NO_PDF = 1168;
    var estiloOriginal = trilha.getAttribute('style') || '';
    trilha.style.width = LARGURA_NO_PDF + 'px';
    trilha.style.padding = '0 0 4px';

    for (var i = 0; i < slidesDoDeck.length; i++) {
      mostrar(i, false);
      copias.push(trilha.outerHTML);
    }

    trilha.setAttribute('style', estiloOriginal);
    mostrar(voltarPara, false);

    for (var j = 0; j < slidesDoDeck.length; j++) {
      var antiga = slidesDoDeck[j].querySelector('.deckTrilhaImpressa');
      if (antiga) { antiga.remove(); }
      var caixa = document.createElement('div');
      caixa.className = 'deckTrilhaImpressa';
      caixa.innerHTML = copias[j];
      // O id repetido em 21 copias quebraria `getElementById`, que o JS da
      // navegacao usa para achar a barra de verdade.
      var comId = caixa.querySelectorAll('[id]');
      for (var k = 0; k < comId.length; k++) { comId[k].removeAttribute('id'); }
      slidesDoDeck[j].insertBefore(caixa, slidesDoDeck[j].firstChild);
    }
  }

  window.addEventListener('beforeprint', prepararTrilhaParaImpressao);

  // Salvar em PDF e a impressao do navegador: quem faz o trabalho e o
  // `@media print`, que poe cada slide numa pagina de 1280x720.
  var baixarPdf = document.getElementById('deckBaixarPdf');
  if (baixarPdf) {
    baixarPdf.addEventListener('click', function(){
      prepararTrilhaParaImpressao();
      window.print();
    });
  }

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


def _indice_por_secao(slides: list[Slide]) -> str:
    """Monta a trilha agrupada por tópico, com uma marca por slide.

    Cada tópico vira um grupo. Dentro dele há uma marca por slide, e o nome do
    tópico aparece uma vez só, embaixo. Todos os grupos têm a **mesma largura**:
    o que conta quanto da apresentação cada parte ocupa é a quantidade de
    marcas dentro do grupo, não o tamanho dele.

    Slides sem tópico — a capa e o fecho — ficam de fora: o campo vazio é o que
    os marca como página sem rótulo e sem número, e nenhum dos dois é etapa da
    apresentação.

    Args:
        slides: Os slides, na ordem da apresentação.

    Returns:
        O HTML da trilha, ou string vazia se não houver slide nenhum.
    """
    grupos: list[tuple[str, list[int]]] = []
    for posicao, slide in enumerate(slides):
        # A capa e o fecho ficam de fora: o campo `topico` vazio é o que marca
        # os dois como página sem rótulo, e nenhum dos dois é etapa da
        # apresentação — um é a porta, o outro é a saída.
        if not slide.topico:
            continue
        nome_da_secao = slide.topico
        if grupos and grupos[-1][0] == nome_da_secao:
            grupos[-1][1].append(posicao)
        else:
            grupos.append((nome_da_secao, [posicao]))

    if not grupos:
        return ""

    blocos = []
    for topico, posicoes in grupos:
        marcas = "".join(
            f'<div class="deckIndiceItem" data-slide="{posicao}">'
            '<span class="deckIndiceMarca"></span></div>'
            for posicao in posicoes
        )
        blocos.append(
            '<div class="deckSecao">'
            f'<div class="deckSecaoMarcas">{marcas}</div>'
            f'<span class="deckSecaoNome">{layout.escapar(topico)}</span>'
            "</div>"
        )

    return (
        '<div class="deckIndice porSecao">'
        '<div class="deckIndiceTrilha"></div>'
        '<div class="deckIndiceProgresso" id="deckIndiceProgresso"></div>'
        f'{"".join(blocos)}'
        "</div>"
    )


def _indice_horizontal(slides: list[Slide], mostrar_rotulos: bool = True) -> str:
    """A trilha de progresso no topo do palco, com um marcador por slide.

    Cada marcador traz o tópico em cima e o nome curto do slide embaixo, para
    que a trilha diga não só em que parte a apresentação está, mas em que
    slide daquela parte. A capa fica de fora: ela não é conteúdo.

    Args:
        slides: Os slides, na ordem da apresentação.
        mostrar_rotulos: Quando False, a trilha fica só com as bolinhas, sem
            tópico nem nome de slide.

            ⚠️ Existe porque num deck longo os rótulos poluem mais do que
            orientam: o tópico se repetia onze vezes seguidas e os nomes
            curtos não cabiam, saindo truncados com reticências. Só as
            bolinhas dizem o que importa na trilha — onde estou e quanto
            falta. O tópico e o título continuam no próprio slide.

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
            + (
                '<span class="deckIndiceRotulos">'
                f'<span class="deckIndiceTopico">{layout.escapar(slide.topico)}</span>'
                f'<span class="deckIndiceTexto">{layout.escapar(nome_curto)}</span>'
                "</span>"
                if mostrar_rotulos
                else ""
            )
            + "</div>"
        )

    if not itens:
        return ""

    classe_do_indice = "deckIndice" if mostrar_rotulos else "deckIndice soBolinhas"
    return (
        f'<div class="{classe_do_indice}">'
        '<div class="deckIndiceTrilha"></div>'
        '<div class="deckIndiceProgresso" id="deckIndiceProgresso"></div>'
        f'{"".join(itens)}'
        "</div>"
    )


def montar(slides: list[Slide], estilo_de_projecao: bool = False) -> str:
    """Monta o deck inteiro: palco, slides e barra de navegação.

    Args:
        slides: Os slides, na ordem da apresentação.
        estilo_de_projecao: Quando True, o deck é montado para ser
            projetado, e não para ser lido dentro do site. Três coisas mudam
            juntas, e elas só fazem sentido juntas:

              - a trilha perde os rótulos e fica só com as bolinhas;
              - o palco perde a borda, o arredondamento e a sombra de cartão,
                porque numa apresentação não há o que separar do deck;
              - a trilha vira uma régua agrupada por tópico: uma marca por
                slide, e o nome do tópico uma vez por grupo.

    Returns:
        O HTML do deck.

    Raises:
        ValueError: Se a lista vier vazia, caso em que não há o que montar.
    """
    classe_do_palco = "deckPalco semMoldura" if estilo_de_projecao else "deckPalco"

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
        '<button class="deckBotaoPdf" id="deckBaixarPdf" type="button" '
        'title="Abre a impressão do navegador. Escolha &quot;Salvar como PDF&quot;, '
        'com margens &quot;Nenhuma&quot; e sem cabeçalho e rodapé.">'
        "Salvar em PDF</button>"
        "</div>"
    )

    return (
        '<div class="deck">'
        f'<div class="{classe_do_palco}">'
        + (
            _indice_por_secao(slides)
            if estilo_de_projecao
            else _indice_horizontal(slides)
        )
        + f'<div class="deckTela">{"".join(blocos_de_slide)}</div>'
        + "</div>"
        f"{barra}"
        "</div>"
    )
