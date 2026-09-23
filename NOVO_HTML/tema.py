"""Design system do site novo.

Reproduz a linguagem visual do painel de sortimento usado como referência:
duas colunas de navegação em azul-marinho (primária e secundária) e uma área
de conteúdo em fundo branco, com tipografia sem serifa e números tabulares.

Este módulo carrega apenas a folha de estilo. A montagem do HTML fica em
`layout.py`, e o texto de cada página em `paginas/`.
"""

# Largura das duas colunas de navegação, em pixels. Ficam aqui porque o JS de
# recolher o menu também precisa delas, e um valor só evita divergência.
LARGURA_NAV_PRIMARIA = 256
LARGURA_NAV_SECUNDARIA = 236

# Largura máxima do texto corrido na área de conteúdo. Acima disso a linha fica
# longa demais para leitura confortável.
LARGURA_MAXIMA_CONTEUDO = 1320


FOLHA_DE_ESTILO = """
*{box-sizing:border-box}

:root{
  /* Navegação — o azul-marinho das duas colunas da esquerda. */
  --nav1-fundo:#0E2033;
  --nav2-fundo:#142A42;
  --nav-texto:#C3CFDE;
  --nav-texto-forte:#FFFFFF;
  --nav-rotulo:#77899E;
  --nav-borda:rgba(255,255,255,.09);
  --nav-hover:rgba(255,255,255,.07);

  /* Conteúdo — fundo branco, tinta escura, cinzas de apoio. */
  --fundo:#FFFFFF;
  --elevado:#F7F9FB;
  --tinta:#16202C;
  --tinta-suave:#3E4C5C;
  --muted:#6B7A8C;
  --faint:#93A2B3;
  --borda:#E3E8EE;
  --borda-forte:#CBD4DE;

  /* Acento e semântica. */
  --acento:#1B6EF3;
  --acento-escuro:#1559C9;
  --acento-suave:#EAF2FE;
  --bom:#1F7A4D;
  --bom-suave:#E8F5EE;
  --atencao:#B4761C;
  --atencao-suave:#FDF3E3;
  --critico:#C0392B;
  --critico-suave:#FCECEA;
  --serie:#C94F60;

  --raio:10px;
  --raio-g:14px;
  --sombra:0 1px 2px rgba(16,32,51,.05), 0 8px 24px -16px rgba(16,32,51,.22);

  --fonte:-apple-system,BlinkMacSystemFont,"SF Pro Text","Inter","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --fonte-dados:"SF Mono","JetBrains Mono",Menlo,Consolas,"Liberation Mono",monospace;
}

html{scroll-behavior:smooth}

body{
  margin:0;
  background:var(--fundo);
  color:var(--tinta);
  font-family:var(--fonte);
  font-size:15.5px;
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}

h1,h2,h3,h4{font-family:var(--fonte); font-weight:650; line-height:1.2; color:var(--tinta); margin:0}
h1{font-size:1.85rem; letter-spacing:-.02em}
h2{font-size:1.28rem; letter-spacing:-.012em}
h3{font-size:1.03rem; letter-spacing:-.006em}
p{margin:0 0 .9rem; max-width:74ch}
a{color:var(--acento); text-decoration:none}
a:hover{text-decoration:underline; text-underline-offset:2px}
strong,b{font-weight:640; color:var(--tinta)}
code{font-family:var(--fonte-dados); font-size:.86em; background:var(--elevado);
  border:1px solid var(--borda); border-radius:5px; padding:.1em .38em; color:var(--tinta-suave)}

/* ------------------------------------------------------------------ casca */

#casca{display:flex; align-items:stretch; min-height:100vh}

/* ------------------------------------------------- coluna de navegação 1 */

#navPrimaria{
  flex:0 0 """ + str(LARGURA_NAV_PRIMARIA) + """px;
  width:""" + str(LARGURA_NAV_PRIMARIA) + """px;
  background:var(--nav1-fundo);
  position:sticky; top:0; align-self:flex-start; height:100vh;
  display:flex; flex-direction:column; overflow:hidden;
  transition:flex-basis .16s ease, width .16s ease;
  z-index:6;
}

.marca{display:flex; gap:10px; align-items:center; padding:18px 16px 14px}
.marcaSelo{
  flex:0 0 30px; width:30px; height:30px; border-radius:8px;
  background:var(--acento); color:#fff;
  display:flex; align-items:center; justify-content:center;
}
.marcaMosquito{width:21px; height:21px; display:block}
.marcaTexto{min-width:0}
.marcaNome{color:var(--nav-texto-forte); font-weight:640; font-size:.93rem; line-height:1.25;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
.marcaSub{color:var(--nav-rotulo); font-size:.73rem; line-height:1.3;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis}

.navRolagem{flex:1 1 auto; overflow-y:auto; overflow-x:hidden; padding:2px 0 10px}

.navRotulo{
  color:var(--nav-rotulo); font-size:.685rem; font-weight:700;
  letter-spacing:.13em; text-transform:uppercase;
  padding:14px 18px 7px;
}

.navItem{
  display:flex; align-items:center; gap:10px;
  margin:1px 10px; padding:8px 10px; border-radius:9px;
  color:var(--nav-texto); font-size:.885rem; font-weight:500;
  text-decoration:none; white-space:nowrap; overflow:hidden;
}
.navItem:hover{background:var(--nav-hover); color:var(--nav-texto-forte); text-decoration:none}
.navItem.ativo{background:var(--acento); color:#fff; font-weight:600}
.navItem.ativo:hover{background:var(--acento)}
.navIcone{flex:0 0 17px; width:17px; height:17px; opacity:.85}
.navItem.ativo .navIcone{opacity:1}
.navRotuloItem{overflow:hidden; text-overflow:ellipsis}

.navFilho{padding-left:28px; font-size:.855rem}

/* Filete que separa grupos no menu. O respiro é generoso de propósito: é
   ele que diz que o que vem depois é de outra natureza. */
.navDivisor{height:1px; background:var(--nav-borda); margin:34px 18px}

.navRodape{
  border-top:1px solid var(--nav-borda); padding:11px 18px;
  color:var(--nav-rotulo); font-size:.8rem; cursor:pointer; user-select:none;
  white-space:nowrap; overflow:hidden;
}
.navRodape:hover{color:var(--nav-texto)}

/* --------------------------------------------------- coluna de navegação 2 */

#navSecundaria{
  flex:0 0 """ + str(LARGURA_NAV_SECUNDARIA) + """px;
  width:""" + str(LARGURA_NAV_SECUNDARIA) + """px;
  background:var(--nav2-fundo);
  position:sticky; top:0; align-self:flex-start; height:100vh;
  display:flex; flex-direction:column; overflow:hidden; z-index:5;
}
.nav2Rolagem{flex:1 1 auto; overflow-y:auto; padding:22px 0 16px}
.nav2Rotulo{
  color:var(--nav-rotulo); font-size:.685rem; font-weight:700;
  letter-spacing:.13em; text-transform:uppercase; padding:0 18px 9px;
}
.nav2Item{
  display:flex; align-items:center; gap:10px;
  margin:1px 10px; padding:8px 11px; border-radius:9px;
  color:var(--nav-texto); font-size:.885rem; font-weight:500;
  text-decoration:none; white-space:nowrap; overflow:hidden;
}
.nav2Item:hover{background:var(--nav-hover); color:var(--nav-texto-forte); text-decoration:none}
.nav2Item.ativo{background:var(--acento); color:#fff; font-weight:600}
.nav2Icone{flex:0 0 15px; width:15px; height:15px; opacity:.8}
.nav2Item.ativo .nav2Icone{opacity:1}
.nav2Texto{overflow:hidden; text-overflow:ellipsis}

/* ------------------------------------------------------ área de conteúdo */

#areaConteudo{flex:1 1 auto; min-width:0; background:var(--fundo);
  display:flex; flex-direction:column; min-height:100vh}
.conteudoInterno{flex:1 1 auto; width:100%;
  max-width:""" + str(LARGURA_MAXIMA_CONTEUDO) + """px; padding:26px 38px 64px}

.trilha{color:var(--muted); font-size:.83rem; margin:0 0 20px}
.trilha b{color:var(--tinta-suave); font-weight:600}

.cabecalhoPagina{margin:0 0 24px}
.cabecalhoPagina h1{margin:0 0 8px}
.cabecalhoPagina .resumo{color:var(--tinta-suave); font-size:1.02rem; max-width:78ch; margin:0}

/* Régua de números no topo da página, como no painel de referência:
   rótulo pequeno em versalete, número grande, nota fina embaixo. */
.regua{display:flex; flex-wrap:wrap; gap:38px; padding:20px 0 24px;
  border-top:1px solid var(--borda); border-bottom:1px solid var(--borda); margin:0 0 30px}
.metrica{min-width:0}
.metricaRotulo{color:var(--muted); font-size:.685rem; font-weight:700;
  letter-spacing:.11em; text-transform:uppercase; margin:0 0 6px}
.metricaValor{font-size:1.6rem; font-weight:680; letter-spacing:-.022em;
  font-variant-numeric:tabular-nums; line-height:1.15; color:var(--tinta)}
.metricaNota{color:var(--muted); font-size:.79rem; margin-top:4px}

/* O respiro entre seções é o dobro do original: com poucas seções por página,
   o vão é o que diz onde um assunto acaba e outro começa. */
.secao{scroll-margin-top:22px; padding:8px 0 68px}
.secao:last-child{padding-bottom:40px}
.secaoTitulo{display:flex; align-items:baseline; gap:11px; margin:0 0 6px}
.secaoTitulo h2{margin:0}
.secaoOrdem{color:var(--faint); font-size:.78rem; font-weight:700;
  font-variant-numeric:tabular-nums}
.secaoIntro{color:var(--tinta-suave); margin:0 0 18px; max-width:78ch}

.cartao{background:var(--fundo); border:1px solid var(--borda); border-radius:var(--raio-g);
  padding:18px 20px; box-shadow:var(--sombra)}
.cartaoRotulo{color:var(--muted); font-size:.685rem; font-weight:700;
  letter-spacing:.11em; text-transform:uppercase; margin:0 0 8px}
.cartao h3{margin:0 0 6px}
.cartao p:last-child{margin-bottom:0}

.grade{display:grid; gap:16px; margin:0 0 18px}
.grade2{grid-template-columns:repeat(2,minmax(0,1fr))}
.grade3{grid-template-columns:repeat(3,minmax(0,1fr))}
.grade4{grid-template-columns:repeat(4,minmax(0,1fr))}

/* Faixa de aviso — separa o que é fato medido do que é hipótese ou ressalva. */
.aviso{border-left:3px solid var(--borda-forte); background:var(--elevado);
  border-radius:0 var(--raio) var(--raio) 0; padding:13px 16px; margin:0 0 18px}
.aviso .avisoRotulo{font-size:.685rem; font-weight:700; letter-spacing:.11em;
  text-transform:uppercase; color:var(--muted); margin:0 0 5px}
.aviso p{margin:0; max-width:78ch}
.aviso.bom{border-left-color:var(--bom); background:var(--bom-suave)}
.aviso.bom .avisoRotulo{color:var(--bom)}
.aviso.atencao{border-left-color:var(--atencao); background:var(--atencao-suave)}
.aviso.atencao .avisoRotulo{color:var(--atencao)}
.aviso.critico{border-left-color:var(--critico); background:var(--critico-suave)}
.aviso.critico .avisoRotulo{color:var(--critico)}
.aviso.info{border-left-color:var(--acento); background:var(--acento-suave)}
.aviso.info .avisoRotulo{color:var(--acento-escuro)}

.figura{margin:0 0 20px; border:1px solid var(--borda); border-radius:var(--raio-g);
  overflow:hidden; background:var(--fundo); box-shadow:var(--sombra)}
.figuraTopo{padding:14px 18px 0}
.figuraTopo h3{margin:0 0 3px}
.figuraTopo .figuraSub{color:var(--muted); font-size:.85rem; margin:0}
.figura img{display:block; width:100%; height:auto; padding:10px 14px 0}
.figuraLegenda{color:var(--muted); font-size:.83rem; padding:10px 18px 15px; margin:0;
  border-top:1px solid var(--borda); margin-top:10px; background:var(--elevado)}

/* Tabela sem moldura: o dado é a moldura. Nada de caixa arredondada com
   sombra em volta, nada de rolagem interna — a tabela ocupa a largura toda e
   cresce até onde precisar, e quem rola é a página. */
.tabelaEnvelope{margin:0 0 26px}
.tabelaRolavel{overflow-x:auto}
table.tabela{border-collapse:collapse; width:100%; font-size:.86rem}
table.tabela th{background:transparent; color:var(--muted); text-align:left;
  font-weight:600; font-size:.74rem; letter-spacing:.04em;
  padding:7px 14px 9px; border-bottom:1px solid var(--borda-forte); white-space:nowrap}
table.tabela td{padding:8px 14px; border-bottom:1px solid var(--borda);
  color:var(--tinta-suave); vertical-align:top}
table.tabela tbody tr:last-child td{border-bottom:1px solid var(--borda-forte)}
table.tabela tbody tr:hover{background:var(--elevado)}
table.tabela td:first-child{color:var(--tinta)}
td.num,th.num{text-align:right; font-variant-numeric:tabular-nums; font-family:var(--fonte-dados)}
td.ordem{color:var(--faint); font-variant-numeric:tabular-nums; width:38px}
code.nomeColuna{white-space:nowrap}

/* Célula com a lista de algoritmos, em duas colunas: um cenário tem nove, e
   em linha única eles atravessariam a tabela inteira. Com duas colunas os
   nove caem em quatro linhas cheias mais uma. */
.celulaModelos{display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
  gap:2px 14px; font-size:.8rem; color:var(--muted); line-height:1.5}

/* Etiqueta de grupo: diz de qual família a coluna ou a fonte vem. */
.etiqueta{display:inline-block; font-size:.7rem; font-weight:650; padding:2px 8px;
  border-radius:20px; white-space:nowrap; border:1px solid transparent}
.etiqueta.vetor{background:var(--acento-suave); color:var(--acento-escuro); border-color:#CFE1FD}
.etiqueta.alvo{background:var(--critico-suave); color:var(--critico); border-color:#F6D5D1}
.etiqueta.clima{background:var(--bom-suave); color:var(--bom); border-color:#CFE8DA}
.etiqueta.contexto{background:var(--elevado); color:var(--muted); border-color:var(--borda)}

/* Faixa de título entre filetes, para abrir um diagrama de largura cheia. */
.faixa{border-top:2px solid var(--acento); border-bottom:2px solid var(--acento);
  padding:13px 0; margin:0 0 20px; text-align:center}
/* max-width:none anula o limite de 74ch que todo <p> herda: sem isso o título
   centraliza dentro do parágrafo estreito, e não dentro da faixa. */
.faixaTitulo{color:var(--acento-escuro); font-size:.9rem; font-weight:700;
  letter-spacing:.17em; text-transform:uppercase; margin:0; max-width:none}

/* Diagrama do caminho dos dados: etapas em cartão, ligadas por setas. */
.fluxo{display:flex; align-items:stretch; gap:10px; margin:0 0 26px; flex-wrap:nowrap}
.fluxoEtapa{flex:1 1 0; min-width:0; background:var(--fundo);
  border:1px solid var(--borda); border-left:4px solid var(--acento);
  border-radius:var(--raio); padding:14px 16px; box-shadow:var(--sombra)}
.fluxoNome{font-weight:680; font-size:.97rem; color:var(--tinta); margin:0 0 5px}
.fluxoTexto{color:var(--muted); font-size:.85rem; line-height:1.45}
.fluxoSeta{flex:0 0 auto; display:flex; align-items:center; color:var(--acento);
  font-size:1.15rem; font-weight:700}

/* Quatro etapas lado a lado só cabem em tela larga. Abaixo disso viram duas
   linhas de duas, e no celular uma coluna só — a seta some junto, porque
   apontar para baixo confundiria a leitura do caminho. */
@media (max-width:1180px){
  .fluxo{flex-wrap:wrap; gap:12px}
  .fluxoEtapa{flex:1 1 calc(50% - 24px)}
  .fluxoSeta{display:none}
}
@media (max-width:640px){
  .fluxoEtapa{flex:1 1 100%}
}

/* Virada de escopo: o que o projeto é hoje, o que ele passa a ser, e o que
   entra junto na virada. A terceira caixa PENDE da segunda em vez de vir
   depois dela na linha: ela não é a etapa seguinte no tempo, é o insumo que
   torna a segunda possível. Desenhar as três em fila diria a coisa errada. */
.virada{display:grid; grid-template-columns:1fr auto 1fr; align-items:stretch;
  gap:14px; margin:0}
.viradaCaixa{background:var(--fundo); border:1px solid var(--borda);
  border-radius:var(--raio); padding:15px 17px; box-shadow:var(--sombra)}
.viradaCaixa.eFuturo{border-color:var(--acento); border-width:1.5px}
.viradaCaixa.eInsumo{border-color:var(--bom); border-width:1.5px;
  background:var(--bom-suave); box-shadow:none}
.viradaRotulo{font-size:.72rem; font-weight:700; letter-spacing:.07em;
  text-transform:uppercase; color:var(--faint); margin:0 0 6px}
.viradaCaixa.eFuturo .viradaRotulo{color:var(--acento)}
.viradaCaixa.eInsumo .viradaRotulo{color:var(--bom)}
.viradaTexto{font-size:.95rem; font-weight:640; color:var(--tinta);
  line-height:1.35; margin:0}
.viradaSeta{display:flex; align-items:center; color:var(--acento);
  font-size:1.35rem; font-weight:700}

/* O ramo repete a grade de três colunas da linha de cima só para herdar o
   alinhamento: a caixa do insumo precisa nascer sob a caixa do futuro. */
.viradaDerivacao{display:grid; grid-template-columns:1fr auto 1fr; gap:14px}
.viradaRamo{grid-column:3; display:flex; align-items:flex-start; gap:2px;
  padding-left:20px}
.viradaRamoSeta{flex:0 0 auto; width:52px; height:58px; color:var(--bom)}
.viradaRamo .viradaCaixa{flex:1 1 auto; margin-top:18px}

/* Em tela estreita a derivação lateral vira empilhamento: manter a coluna 3
   num espaço que não existe jogaria a caixa para fora da vista. */
@media (max-width:820px){
  .virada,.viradaDerivacao{grid-template-columns:1fr}
  .viradaSeta{justify-content:center}
  .viradaRamo{grid-column:1; padding-left:0}
}

/* Gráfico de linhas. O SVG só tem viewBox, então sem um teto de largura ele
   estica até a página inteira e as linhas ficam esparramadas. */
.grafico{max-width:620px; margin:0 0 22px}
.graficoTitulo{font-weight:640; font-size:.9rem; margin:0 0 6px; color:var(--tinta)}
.grafico svg{display:block; width:100%; height:auto}
.graficoLegenda{margin-top:6px; font-size:.8rem; color:var(--muted);
  display:flex; flex-wrap:wrap; gap:4px 14px}

/* Cartão de horizonte: o prazo em versalete no topo, o R² grande no meio e
   as outras duas medidas embaixo, em linha. A barra colorida no topo indica
   de relance se aquele prazo ainda é confiável. */
.cardHorizonte{position:relative; background:var(--fundo); border:1px solid var(--borda);
  border-radius:var(--raio-g); padding:18px 18px 16px; box-shadow:var(--sombra); overflow:hidden}
.cardHorizonte::before{content:""; position:absolute; top:0; left:0; right:0; height:4px;
  background:var(--faixa, var(--acento))}
.cardPrazo{color:var(--tinta); font-size:1.62rem; font-weight:690;
  letter-spacing:-.02em; margin:2px 0 14px; line-height:1.1}
.cardR2{font-size:1.45rem; font-weight:650; letter-spacing:-.02em;
  font-variant-numeric:tabular-nums; line-height:1; color:var(--tinta-suave)}
.cardR2Rotulo{color:var(--muted); font-size:.78rem; margin:5px 0 14px}
.cardMedidas{display:flex; gap:18px; border-top:1px solid var(--borda); padding-top:11px}
.cardMedida{min-width:0}
.cardMedidaValor{font-weight:650; font-size:.97rem; font-variant-numeric:tabular-nums;
  color:var(--tinta-suave)}
.cardMedidaRotulo{color:var(--faint); font-size:.71rem; margin-top:1px}

/* Vários gráficos lado a lado: cada um perde o teto de 620px e divide a
   largura disponível, para que as curvas sejam comparadas de relance. */
.graficosLadoALado{display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
  gap:20px; margin:0 0 22px}
.graficosLadoALado .grafico{max-width:none; margin:0}
.graficosLadoALado .graficoTitulo{font-size:.83rem}
.graficosLadoALado .graficoLegenda{font-size:.75rem}

@media (max-width:1100px){
  .graficosLadoALado{grid-template-columns:1fr; gap:14px}
  .graficosLadoALado .grafico{max-width:620px}
}

/* Linha do tempo do que entrou no treino: barra segmentada + legenda. */
.linhaDoTreino{max-width:760px; margin:0 0 24px}
.linhaDoTreino svg{display:block; width:100%; height:auto}
.legendaDaLinhaDoTreino{display:grid; gap:5px; margin-top:8px;
  font-size:.82rem; color:var(--tinta-suave)}
.itemDaLinhaDoTreino{display:flex; align-items:baseline; gap:8px}
.marcaDaLinhaDoTreino{flex:0 0 11px; width:11px; height:11px; border-radius:3px;
  border:1px solid rgba(16,32,51,.12); transform:translateY(1px)}

.lista{margin:0 0 16px; padding-left:20px}
.lista li{margin:0 0 7px; color:var(--tinta-suave); max-width:76ch}
.lista li::marker{color:var(--faint)}

.rodape{border-top:1px solid var(--borda); color:var(--muted); font-size:.81rem;
  padding:16px 38px 26px; margin-top:auto}

/* ------------------------------------------------------------ responsivo */

@media (max-width:1100px){
  .grade3,.grade4{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:900px){
  #casca{flex-direction:column}
  #navPrimaria,#navSecundaria{position:static; height:auto; width:100%; flex:none}
  .navRolagem,.nav2Rolagem{max-height:none}
  .conteudoInterno{padding:20px 18px 48px}
  .grade2,.grade3,.grade4{grid-template-columns:1fr}
  .regua{gap:24px}
}
"""


# O JS é mínimo de propósito: marca no menu secundário a seção visível e filtra
# o menu primário pela busca. Nada aqui muda conteúdo, só navegação.
SCRIPT_DE_NAVEGACAO = """
(function(){
  var itensSecundarios = Array.prototype.slice.call(
    document.querySelectorAll('#navSecundaria .nav2Item[data-ancora]')
  );
  var secoes = itensSecundarios
    .map(function(item){ return document.getElementById(item.dataset.ancora); })
    .filter(Boolean);

  function marcarSecaoVisivel(){
    if (!secoes.length) { return; }
    var limite = window.scrollY + 140;
    var indiceAtivo = 0;
    for (var i = 0; i < secoes.length; i++) {
      if (secoes[i].offsetTop <= limite) { indiceAtivo = i; }
    }
    for (var j = 0; j < itensSecundarios.length; j++) {
      itensSecundarios[j].classList.toggle('ativo', j === indiceAtivo);
    }
  }

  window.addEventListener('scroll', marcarSecaoVisivel, {passive:true});
  window.addEventListener('resize', marcarSecaoVisivel);
  marcarSecaoVisivel();

  var rodapeMenu = document.getElementById('navRodape');
  if (rodapeMenu) {
    rodapeMenu.addEventListener('click', function(){
      var primaria = document.getElementById('navPrimaria');
      var recolhida = primaria.style.flexBasis === '62px';
      primaria.style.flexBasis = recolhida ? '""" + str(LARGURA_NAV_PRIMARIA) + """px' : '62px';
      primaria.style.width = recolhida ? '""" + str(LARGURA_NAV_PRIMARIA) + """px' : '62px';
    });
  }
})();
"""
