"""

Monta o site do projeto (paginas HTML) a partir do que o MLflow gravou e dos
textos em conteudo.py. E o COMANDO principal desta pasta: rode

    python gerar.py

e ele reescreve as paginas dentro de 'docs/' (na raiz do repositorio). Abra
'docs/index.html' no navegador. Essa pasta 'docs/' e tambem o que o GitHub Pages
publica na internet (Settings > Pages > main /docs), entao dar commit nela ja
atualiza o site publico. Rodou um modelo novo (python main.py --experimento ...)?
Rode este gerador de novo que o painel se atualiza.

Tudo aqui e feito na mao com Python puro: le a pasta mlruns, formata os numeros,
desenha os graficos em SVG e escreve o HTML. Sem servidor, sem dependencia
externa — o site e so um punhado de arquivos que voce abre ou manda por email.

"""

import argparse
import datetime
import html
import re
import shutil
import unicodedata
from pathlib import Path

import conteudo
import leitor_mlflow
import markdown_simples

# Onde as coisas ficam: esta pasta, a mlruns do projeto ao lado, e a saida.
# A saida e 'docs/' na RAIZ do repositorio, que e a pasta que o GitHub Pages
# publica (Settings > Pages > main /docs) — assim, gerar + commitar ja atualiza
# o site publico.
PASTA_AQUI = Path(__file__).resolve().parent
PASTA_MLRUNS = PASTA_AQUI.parent / "modelagem_aedes" / "mlruns"
PASTA_SITE = PASTA_AQUI.parent / "docs"
PASTA_PAGINAS = PASTA_AQUI / "paginas"

# Enderecos das paginas fixas (nao dar esses nomes a paginas novas em paginas/).
NOMES_RESERVADOS = {"index", "objetivo", "dados", "cenarios", "resultados", "metodologia", "diario"}

# Cores das linhas dos graficos (uma por serie). Da paleta Pearl, legiveis nos dois temas.
CORES_SERIES = ["#9179B8", "#C79A5B", "#A5937B", "#6E8B5A", "#B0574B", "#5B84A6"]

# Ordem preferida das metricas na tabela comparativa (o resto vem depois).
PREFERENCIA_METRICAS = [
    "MAE_media",
    "RMSE_media",
    "R2_media",
    "acuracia_media",
    "auc_media",
    "f1_media",
    "recall_media",
    "precisao_media",
]

# Nome bonito das colunas de resultado usadas nos graficos.
ROTULO_COLUNA = {"mae": "Erro medio (MAE)", "rmse": "Erro (RMSE)", "r2": "R²"}

# As paginas do site: (arquivo, chave de navegacao, titulo do menu). "Dados"
# saiu do menu — virou uma secao da propria pagina inicial (a home tem o card
# "Dados" que rola ate la).
PAGINAS = [
    ("index.html", "inicio", "Inicio"),
    ("metodologia.html", "metodologia", "Metodologia"),
]

CSS = """
*{box-sizing:border-box}
:root{
  --fundo:#EAE4DD; --superficie:#FBF8F4; --elevado:#F2ECE4;
  --tinta:#332F30; --tinta-suave:#4E4849; --muted:#666161; --faint:#948C87;
  --borda:#DDD4C9; --borda-forte:#C7BBAC; --linha-grade:#E4DCD1;
  --acento:#AF9AC9; --acento-forte:#6A5391; --acento-suave:#ECE6F3;
  --bom:#6E8B5A; --atencao:#B07D33; --critico:#B0574B;
  --raio:16px; --raio-p:10px; --largura:1080px;
  --sombra:0 1px 2px rgba(14,26,22,.04), 0 6px 20px -12px rgba(14,26,22,.14);
  --fonte-titulo:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --fonte-corpo:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --fonte-dados:"SF Mono","JetBrains Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--fundo); color:var(--tinta);
  font-family:var(--fonte-corpo); font-size:16.5px; line-height:1.62;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
a{color:var(--acento-forte); text-underline-offset:2px}
h1,h2,h3,h4{font-family:var(--fonte-titulo); font-weight:600; line-height:1.14; text-wrap:balance; color:var(--tinta)}
h1{font-size:clamp(2.1rem,1.4rem + 2.6vw,3rem); margin:.1em 0 .35em; letter-spacing:-.015em}
h2{font-size:1.55rem; margin:0 0 .5rem; letter-spacing:-.01em}
h3{font-size:1.13rem; margin:0 0 .35rem}
p{margin:0 0 1rem; max-width:66ch}
strong{color:var(--tinta)}
.eyebrow{font-size:.73rem; text-transform:uppercase; letter-spacing:.16em; color:var(--acento-forte); font-weight:700; margin:0 0 .7rem}

/* Layout lado a lado (padrao do otimizador de sortimento): sidebar sticky + conteudo */
#appShell{display:flex; align-items:flex-start; min-height:100vh}
#mainArea{flex:1 1 auto; min-width:0; display:flex; flex-direction:column; min-height:100vh}
#sideNav{flex:0 0 262px; width:262px; box-sizing:border-box; position:sticky; top:0; align-self:flex-start;
  height:100vh; background:var(--superficie); border-right:1px solid var(--borda);
  display:flex; flex-direction:column; transition:flex-basis .16s ease, width .16s ease; overflow:hidden; z-index:5}
.sidenav-inner{flex:1 1 auto; overflow-y:auto; overflow-x:hidden; padding:16px 12px}
.barra-topo{display:contents}
.menu-hamburguer{display:none; align-items:center; gap:.4rem; border:1px solid var(--borda-forte); background:var(--superficie); color:var(--tinta); font-family:inherit; font-size:.9rem; font-weight:600; padding:.5rem .8rem; border-radius:8px; cursor:pointer}
.menu-hamburguer:hover{border-color:var(--acento)}
.marca{display:flex; align-items:flex-start; gap:.5rem; text-decoration:none; color:var(--tinta); padding:2px 8px 14px; line-height:1.25}
.marca .ponto{width:9px; height:9px; border-radius:50%; background:var(--acento); box-shadow:0 0 0 3px var(--acento-suave); margin-top:.32rem; flex:none}
.marca span{font-size:.85rem; font-weight:700; letter-spacing:-.01em}
.sidenav-title{font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.6px; color:var(--muted); padding:2px 8px 10px}
.sidenav-tree{display:flex; flex-direction:column; gap:1px}
.sn-group{display:flex; flex-direction:column}
.sn-node{display:flex; align-items:center; gap:6px; width:100%; text-align:left; padding:7px 8px;
  border:none; background:none; color:var(--tinta); font-size:13px; font-weight:500; font-family:inherit;
  border-radius:6px; cursor:pointer; line-height:1.3; text-decoration:none}
.sn-node:hover{background:var(--elevado)}
.sn-arrow{display:inline-block; width:11px; flex:none; font-size:9px; color:var(--muted); transition:transform .15s ease; text-align:center}
.sn-node.sn-open>.sn-arrow{transform:rotate(90deg)}
.sn-label{overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.sn-children{display:none; flex-direction:column; gap:1px; margin-left:9px; border-left:1px solid var(--borda); padding-left:8px; margin-top:1px; margin-bottom:2px}
.sn-children.open{display:flex}
.sn-node.sn-leaf{font-size:12.5px; font-weight:500; color:var(--muted)}
.sn-node.sn-leaf:hover{color:var(--tinta)}
/* hierarquia de menu: topo (maior + negrito), cabecalho de grupo (maiuscula), folha (menor + clara) */
.sidenav-tree > .sn-node, .sidenav-tree > .sn-group > .sn-toggle{font-size:13.5px; font-weight:700; color:var(--tinta)}
.sn-children .sn-toggle{font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--muted)}
.sn-node.sn-active{background:var(--acento-suave); color:var(--acento-forte); font-weight:700}
.sidenav-rodape{flex:none; display:flex; flex-direction:column; border-top:1px solid var(--borda)}
.sidenav-acao{border:none; background:var(--superficie); color:var(--muted); font-size:12px; padding:11px 12px;
  display:flex; align-items:center; gap:8px; cursor:pointer; font-family:inherit; text-align:left; width:100%; transition:background .15s, color .15s}
.sidenav-acao:hover{background:var(--elevado); color:var(--tinta)}
.sidenav-acao + .sidenav-acao{border-top:1px solid var(--borda)}
.sn-icon{font-size:14px; flex:none; width:16px; text-align:center}
#appShell.sn-collapsed #sideNav{flex-basis:48px; width:48px}
#appShell.sn-collapsed .sidenav-title,
#appShell.sn-collapsed .sidenav-tree,
#appShell.sn-collapsed .marca span,
#appShell.sn-collapsed .sn-acao-texto{display:none}
#appShell.sn-collapsed .sidenav-inner{padding:16px 4px}
#appShell.sn-collapsed .sidenav-acao{padding:11px 4px; justify-content:center}

.wrap{max-width:1440px; margin:0 auto; width:100%; padding:2.4rem clamp(1.4rem,3vw,3.2rem) 4.5rem}
.secao{margin:3rem 0}
.secao > .eyebrow{margin-bottom:1rem}

/* Faixa: separador de secao bem marcado (titulo centralizado entre duas linhas) */
.faixa{text-align:center; margin:3rem 0 1.6rem; padding:.8rem 0; border-top:2px solid var(--acento-forte); border-bottom:2px solid var(--acento-forte)}
.faixa span{font-family:var(--fonte-titulo); font-size:1.4rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--acento-forte)}
.secao > .faixa:first-child{margin-top:0}

.hero{padding:1.4rem 0 .6rem; position:relative}
.hero .sub, .lead{font-size:1.18rem; line-height:1.5; color:var(--muted); max-width:64ch; margin:.4rem 0 0}
.hero .lead strong{color:var(--tinta-suave)}
.secao[id]{scroll-margin-top:1.5rem}

.kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:1rem; margin:1.6rem 0}
.kpi{position:relative; background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1.15rem 1.2rem; box-shadow:var(--sombra); overflow:hidden}
.kpi::before{content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--acento); opacity:.85}
.kpi .valor{font-family:var(--fonte-dados); font-size:1.9rem; font-weight:600; color:var(--tinta); font-variant-numeric:tabular-nums; letter-spacing:-.03em; line-height:1.1}
.kpi .rotulo{font-size:.73rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-top:.3rem}

.cartoes{display:grid; grid-template-columns:repeat(auto-fit,minmax(235px,1fr)); gap:1rem}
.cartao{display:flex; flex-direction:column; background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio);
  padding:1.35rem 1.4rem; text-decoration:none; color:inherit; box-shadow:var(--sombra); transition:border-color .18s, transform .18s, box-shadow .18s}
a.cartao:hover{border-color:var(--acento); transform:translateY(-3px); box-shadow:0 1px 2px rgba(14,26,22,.05), 0 14px 30px -16px rgba(12,110,91,.4)}
.cartao h3{color:var(--tinta)}
.cartao p{color:var(--muted); font-size:.94rem; margin:0 0 .8rem}
.cartao .seta{color:var(--acento-forte); font-weight:700; margin-top:auto; display:inline-block; font-size:.9rem}

.fluxo{display:flex; flex-wrap:wrap; gap:.6rem; align-items:stretch; margin:1.2rem 0}
.fluxo .passo{position:relative; flex:1 1 175px; background:var(--superficie); border:1px solid var(--borda-forte); border-radius:var(--raio-p); padding:.95rem 1.05rem 1rem 1.2rem; box-shadow:var(--sombra); overflow:hidden}
.fluxo .passo::before{content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--acento)}
.fluxo .passo b{display:block; color:var(--tinta); font-size:.98rem; font-weight:700; margin-bottom:.2rem}
.fluxo .passo small{color:var(--muted)}
.fluxo .seta{display:grid; place-items:center; color:var(--acento-forte); font-size:1.3rem; font-weight:700; padding:0 .15rem}
@media (max-width:640px){ .fluxo .seta{transform:rotate(90deg)} }

.grade-fontes{display:grid; grid-template-columns:repeat(auto-fit,minmax(265px,1fr)); gap:1rem}
.fonte{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1.2rem 1.3rem; box-shadow:var(--sombra); transition:border-color .18s, transform .18s}
.fonte:hover{border-color:var(--borda-forte); transform:translateY(-2px)}
.fonte h3{display:flex; align-items:center; flex-wrap:wrap; gap:.5rem; color:var(--tinta)}
.fonte .papel{color:var(--tinta-suave); font-size:.95rem; margin:.5rem 0 .7rem}
.fonte .origem{color:var(--muted); font-size:.84rem; margin:0}
.chips{display:flex; flex-wrap:wrap; gap:.35rem; margin-bottom:.5rem}
.chip{font-size:.71rem; font-weight:600; color:var(--muted); background:var(--elevado); border:1px solid var(--borda); border-radius:99px; padding:.18rem .6rem}
.badge{font-size:.66rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; padding:.18rem .5rem; border-radius:99px}
.badge.vital{color:#fff; background:var(--critico)}

.callout{background:var(--acento-suave); border:1px solid color-mix(in srgb, var(--acento) 28%, var(--borda)); border-left:4px solid var(--acento);
  border-radius:var(--raio-p); padding:1.15rem 1.3rem; margin:1.4rem 0}
.callout .eyebrow{color:var(--acento-forte); margin-bottom:.4rem}
.callout p{margin:0; color:var(--tinta); max-width:74ch}

.lista-metodo{display:grid; gap:.9rem; margin:1.3rem 0; padding:0; list-style:none; counter-reset:passo}
.lista-metodo li{position:relative; background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio-p); padding:1.1rem 1.2rem 1.1rem 3.2rem}
.lista-metodo li::before{counter-increment:passo; content:counter(passo); position:absolute; left:1rem; top:1.05rem; width:1.6rem; height:1.6rem; border-radius:50%; background:var(--acento-suave); color:var(--acento-forte); font-family:var(--fonte-dados); font-weight:700; font-size:.85rem; display:grid; place-items:center}
.lista-metodo b{color:var(--tinta)}
.lista-metodo p{margin:.3rem 0 0; color:var(--muted); font-size:.94rem}

.cenario{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1.6rem 1.7rem; margin:1.5rem 0; box-shadow:var(--sombra)}
.cenario-topo{display:flex; flex-wrap:wrap; align-items:baseline; gap:.7rem; margin-bottom:.2rem}
.cenario-topo h2{margin:0}
.cenario .pergunta{color:var(--muted); margin:.1rem 0 .2rem; font-size:1.02rem}
.cenario .tecnico{font-family:var(--fonte-dados); font-size:.75rem; color:var(--faint)}
.cenario .descricao{color:var(--tinta-suave); font-size:.95rem; max-width:74ch}

.tabela-rolavel{overflow-x:auto; margin:1.1rem 0; border:1px solid var(--borda); border-radius:var(--raio-p)}
table.tabela{width:100%; border-collapse:collapse; font-size:.9rem}
table.tabela th, table.tabela td{padding:.62rem .85rem; text-align:right; white-space:nowrap; border-bottom:1px solid var(--borda)}
table.tabela th:first-child, table.tabela td:first-child{text-align:left}
table.tabela thead th{background:var(--elevado); color:var(--muted); font-size:.72rem; text-transform:uppercase; letter-spacing:.05em; font-weight:700; position:sticky; top:0}
table.tabela tbody tr{transition:background .12s}
table.tabela tbody tr:hover{background:var(--elevado)}
table.tabela tbody tr:last-child td{border-bottom:none}
table.tabela td.num{font-family:var(--fonte-dados); font-variant-numeric:tabular-nums}
table.tabela td.melhor{color:var(--acento-forte); font-weight:700; background:var(--acento-suave)}
table.tabela td.melhor::after{content:" ✓"; font-size:.8em}
.modelo-nome{font-weight:600; color:var(--tinta)}
.pastilha{font-family:var(--fonte-dados); font-size:.72rem; font-weight:600; padding:.14rem .55rem; border-radius:99px; background:var(--acento-suave); color:var(--acento-forte)}
.status{font-size:.76rem; color:var(--muted); margin-top:.15rem}
.status.concluido::before{content:"● "; color:var(--bom)}
.status.falhou::before{content:"● "; color:var(--critico)}

/* Ranking em barras (comparacao visual dos modelos) */
.ranking{display:flex; flex-direction:column; gap:.5rem; margin:1.2rem 0}
.ranking .titulo-graf{font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); font-weight:700; margin-bottom:.2rem}
.ranking-linha{display:grid; grid-template-columns:minmax(120px,auto) 1fr auto; align-items:center; gap:.7rem}
.ranking-nome{font-size:.86rem; color:var(--tinta-suave); text-align:right; font-variant-numeric:tabular-nums}
.ranking-trilho{background:var(--elevado); border-radius:99px; height:16px; overflow:hidden; border:1px solid var(--borda)}
.ranking-barra{height:100%; background:color-mix(in srgb, var(--acento) 55%, var(--superficie)); border-radius:99px}
.ranking-linha.top .ranking-barra{background:var(--acento)}
.ranking-linha.top .ranking-nome{color:var(--tinta); font-weight:700}
.ranking-valor{font-family:var(--fonte-dados); font-size:.85rem; font-variant-numeric:tabular-nums; color:var(--tinta); min-width:3.4em; text-align:right}
.ranking-linha.top .ranking-valor{color:var(--acento-forte); font-weight:700}

.grafico{margin:1.3rem 0 .4rem}
.grafico .titulo-graf{font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); font-weight:700; margin-bottom:.5rem}
.grafico svg{width:100%; height:auto; max-width:740px; display:block}
.grafico .grade{stroke:var(--linha-grade); stroke-width:1}
.grafico .eixo{fill:var(--muted); font-family:var(--fonte-dados); font-size:11px}
.grafico .eixo-titulo{fill:var(--faint); font-family:var(--fonte-corpo); font-size:11px}
.legenda{display:flex; flex-wrap:wrap; gap:.9rem; margin-top:.6rem; font-size:.82rem; color:var(--tinta-suave)}
.legenda span{display:inline-flex; align-items:center; gap:.4rem}
.legenda i{width:14px; height:3px; border-radius:2px; display:inline-block}

/* Linha do tempo dos dados */
.linha-tempo{margin:1.3rem 0 .4rem}
.linha-tempo svg{width:100%; height:auto; max-width:760px; display:block}
.linha-tempo .bloco-rot{fill:#fff; font-family:var(--fonte-corpo); font-size:12px; font-weight:700}
.linha-tempo .ano{fill:var(--muted); font-family:var(--fonte-dados); font-size:11px}
.linha-tempo .marca-rot{fill:var(--atencao); font-family:var(--fonte-corpo); font-size:11px; font-weight:700}

details.detalhes{margin-top:.8rem; border-top:1px dashed var(--borda); padding-top:.7rem}
details.detalhes summary{cursor:pointer; color:var(--acento-forte); font-weight:600; font-size:.9rem; list-style:none}
details.detalhes summary::-webkit-details-marker{display:none}
details.detalhes summary::before{content:"▸ "; }
details.detalhes[open] summary::before{content:"▾ "; }
.grupo-param{margin:1rem 0}
.grupo-param h4{margin:0 0 .35rem; font-size:.76rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-family:var(--fonte-corpo)}
table.params{width:100%; border-collapse:collapse; font-size:.85rem}
table.params td{padding:.3rem .6rem; border-bottom:1px solid var(--borda); vertical-align:top}
table.params td:first-child{color:var(--muted); width:45%}
table.params td:last-child{font-family:var(--fonte-dados); color:var(--tinta); text-align:right; font-variant-numeric:tabular-nums; word-break:break-word}

.vazio{text-align:center; color:var(--muted); background:var(--superficie); border:1px dashed var(--borda-forte); border-radius:var(--raio); padding:3rem 1.5rem}
.vazio code{background:var(--elevado); padding:.15rem .45rem; border-radius:6px; font-family:var(--fonte-dados); font-size:.85em}

footer{border-top:1px solid var(--borda); margin-top:auto}
.rodape{max-width:1440px; margin:0 auto; width:100%; padding:1.8rem clamp(1.4rem,3vw,3.2rem); color:var(--muted); font-size:.83rem; display:flex; flex-wrap:wrap; gap:.4rem 1.4rem; justify-content:space-between}

@media (max-width:760px){
  #appShell{flex-direction:column}
  /* Sidebar vira uma barra fixa no topo; a arvore so aparece ao tocar em "Menu" */
  #sideNav{position:sticky; top:0; flex-basis:auto; width:100%; height:auto; max-height:none; border-right:none; border-bottom:1px solid var(--borda-forte); overflow:visible; z-index:30; box-shadow:var(--sombra)}
  #appShell.sn-collapsed #sideNav{flex-basis:auto; width:100%}
  .sidenav-inner{padding:0; overflow:visible}
  .barra-topo{display:flex; align-items:center; justify-content:space-between; padding:.55rem .9rem .55rem 1rem}
  .marca{padding:0; align-items:center}
  .menu-hamburguer{display:inline-flex}
  .sidenav-title{display:none}
  .sidenav-tree{display:none; padding:.4rem 1rem 1rem; border-top:1px solid var(--borda); max-height:72vh; overflow-y:auto}
  #sideNav.nav-aberto .sidenav-tree{display:flex}
  .sidenav-rodape{display:none}
  .wrap{padding-top:1.8rem}
}

.acordeao{display:flex; flex-direction:column; gap:.7rem; margin-top:1.4rem}
.cenario-item{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); box-shadow:var(--sombra); transition:border-color .15s}
.cenario-item[open]{border-color:var(--borda-forte)}
.cenario-item>summary{list-style:none; cursor:pointer; padding:1.1rem 1.3rem; display:flex; align-items:center; gap:.8rem}
.cenario-item>summary::-webkit-details-marker{display:none}
.cenario-item>summary::before{content:"▸"; color:var(--acento); font-size:.85rem; transition:transform .18s; flex:none}
.cenario-item[open]>summary::before{transform:rotate(90deg)}
.cenario-item[open]>summary{border-bottom:1px solid var(--borda)}
.cenario-item .titulo-cen{font-family:var(--fonte-titulo); font-size:1.14rem; font-weight:600; color:var(--tinta); margin-right:auto}
.cenario-item .destaque{font-family:var(--fonte-dados); font-size:.8rem; color:var(--muted); white-space:nowrap}
.cenario-item .destaque b{color:var(--acento-forte)}
.cenario-item .corpo{padding:1.2rem 1.3rem}
.cenario-item .pergunta-cen{color:var(--muted); font-size:.95rem; margin:0 0 1.1rem}
.tag{font-size:.71rem; font-weight:700; padding:.2rem .62rem; border-radius:99px; white-space:nowrap}
.tag.rodado{background:var(--acento-suave); color:var(--acento-forte)}
.tag.pendente{background:var(--elevado); color:var(--muted); border:1px solid var(--borda)}
.modelos-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(245px,1fr)); gap:.9rem}
.modelo-card{border:1px solid var(--borda); border-radius:var(--raio-p); padding:1rem 1.1rem; background:var(--elevado)}
.modelo-card.campeao{border-color:var(--acento); box-shadow:inset 0 0 0 1px var(--acento)}
.modelo-cab{display:flex; align-items:center; gap:.5rem; margin-bottom:.8rem}
.modelo-cab .coroa{font-size:.9rem}
.stats{display:flex; flex-wrap:wrap; gap:1.2rem; margin-bottom:.4rem}
.stat .v{font-family:var(--fonte-dados); font-size:1.25rem; font-weight:600; color:var(--tinta); font-variant-numeric:tabular-nums; letter-spacing:-.01em}
.stat .r{font-size:.65rem; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin-top:.1rem}
.nao-rodado{color:var(--muted); font-size:.92rem; margin:0}
.nao-rodado code{background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.1em .4em; font-family:var(--fonte-dados); font-size:.85em}

.conteudo-md{max-width:70ch}
.conteudo-md h2{margin:2rem 0 .6rem}
.conteudo-md h3{margin:1.4rem 0 .4rem}
.conteudo-md p{color:var(--tinta-suave)}
.conteudo-md ul,.conteudo-md ol{color:var(--tinta-suave); padding-left:1.3rem; margin:0 0 1rem}
.conteudo-md li{margin:.3rem 0}
.conteudo-md blockquote{margin:1.2rem 0; padding:.8rem 1.1rem; border-left:4px solid var(--acento);
  background:var(--acento-suave); border-radius:0 var(--raio-p) var(--raio-p) 0; color:var(--tinta)}
.conteudo-md code{font-family:var(--fonte-dados); font-size:.88em; background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.08em .4em}
.conteudo-md img{max-width:100%; height:auto; border-radius:var(--raio-p); border:1px solid var(--borda); margin:.6rem 0}
.conteudo-md hr{border:none; border-top:1px solid var(--borda); margin:2rem 0}
.conteudo-md a{color:var(--acento-forte)}

.tabela-dados{width:100%; border-collapse:collapse; font-size:.93rem; border:1px solid var(--borda-forte); border-radius:var(--raio-p); overflow:hidden}
.tabela-dados thead th{text-align:left; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; color:#fff; font-weight:700; padding:.8rem .9rem; background:var(--acento-forte); white-space:nowrap}
.tabela-dados td{text-align:left; padding:.9rem; border-bottom:1px solid var(--borda); vertical-align:top}
.tabela-dados tbody tr:last-child td{border-bottom:none}
.tabela-dados tbody tr{transition:background .12s; background:var(--superficie)}
.tabela-dados tbody tr:nth-child(even){background:color-mix(in srgb, var(--acento) 16%, var(--superficie))}
.tabela-dados tbody tr:hover{background:var(--acento-suave)}
.tabela-dados .fonte-nome{font-weight:700; color:var(--tinta); display:flex; align-items:center; gap:.5rem; flex-wrap:wrap}
.tabela-dados .fonte-desc{color:var(--muted); font-size:.85rem; margin-top:.25rem; max-width:46ch}
.tabela-dados .cobertura, .tabela-dados .freq{white-space:nowrap; color:var(--tinta-suave)}
.tabela-dados .origem-cel{color:var(--muted); font-size:.88rem}
/* Dicionario de dados: uma linha por coluna da tabela_final */
table.tabela-dic td{padding:.6rem .9rem}
table.tabela-dic .dic-num{font-family:var(--fonte-dados); font-size:.8rem; color:var(--faint); text-align:right; width:1%; white-space:nowrap}
.dic-col{font-family:var(--fonte-dados); font-size:.82rem; color:var(--tinta); background:var(--elevado); border:1px solid var(--borda-forte); border-radius:5px; padding:.12rem .45rem; white-space:nowrap}
.dic-unid{font-family:var(--fonte-dados); font-size:.82rem; color:var(--muted); white-space:nowrap}

.tag-papel{font-size:.72rem; font-weight:700; padding:.16rem .58rem; border-radius:99px; white-space:nowrap}
.tag-papel.vetor{background:var(--acento-suave); color:var(--acento-forte)}
.tag-papel.alvo{background:var(--acento-forte); color:var(--superficie)}
.tag-papel.clima{background:var(--elevado); color:var(--tinta-suave); border:1px solid var(--borda-forte)}
.tag-papel.contexto{background:var(--elevado); color:var(--muted); border:1px solid var(--borda-forte)}

/* Detalhamento do clima: cada tema e as colunas que ele gera */
.clima-intro{color:var(--tinta-suave); max-width:74ch; margin:0 0 1rem}
.clima-rodape{color:var(--muted); font-size:.9rem; margin:1rem 0 0; max-width:74ch}
.clima-rodape strong{color:var(--tinta)}
table.tabela-clima td{vertical-align:middle}
table.tabela-clima .clima-tema{font-weight:700; color:var(--tinta); white-space:nowrap; width:1%; padding-right:1.4rem}
table.tabela-clima .clima-emoji{margin-right:.15rem}
.clima-chips{display:flex; flex-wrap:wrap; gap:.4rem}
table.tabela-clima code{font-family:var(--fonte-dados); font-size:.82rem; background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.14rem .5rem; color:var(--tinta-suave); white-space:nowrap}

/* Ficha de dados do cenario: o que entra e o que muda entre os testes */
table.tabela-ficha .ficha-rot{font-weight:700; color:var(--tinta); white-space:nowrap; width:1%; padding-right:1.8rem; vertical-align:top}
table.tabela-ficha .ficha-val{color:var(--tinta-suave)}
table.tabela-ficha tr.ficha-compara td{background:var(--acento-suave); border-top:1px solid color-mix(in srgb, var(--acento) 28%, var(--borda))}
table.tabela-ficha tr.ficha-compara .ficha-rot{color:var(--acento-forte)}
table.tabela-ficha tr.ficha-compara .ficha-val{color:var(--tinta); font-weight:600}
table.tabela-ficha tr.ficha-compara:hover td{background:var(--acento-suave)}

.figura{margin:1.5rem 0; border:1px solid var(--borda); border-radius:var(--raio); overflow:hidden; box-shadow:var(--sombra)}
.figura img{display:block; width:100%; height:auto; background:#fff}
.figura figcaption{padding:.75rem 1.1rem; font-size:.86rem; color:var(--muted); background:var(--superficie); border-top:1px solid var(--borda)}

/* Esquemas (diagramas SVG desenhados na mao) da pagina de Metodologia */
.esquema{margin:1.3rem 0; border:1px solid var(--borda); border-radius:var(--raio-p); background:var(--superficie); padding:1.3rem 1.4rem 1rem; box-shadow:var(--sombra)}
.esquema svg{width:100%; height:auto; max-width:600px; display:block; margin:0 auto}
.esquema .cap{font-size:.84rem; color:var(--muted); margin:.7rem auto 0; text-align:center; max-width:60ch}
.esquema .svg-rot{fill:var(--tinta-suave); font-family:var(--fonte-corpo); font-size:13px}
.esquema .svg-sub{fill:var(--muted); font-family:var(--fonte-corpo); font-size:11px}

/* Objetivo central em destaque + os dois caminhos de modelo (regressao/classificacao) */
.obj-central{background:linear-gradient(180deg,var(--acento-suave),var(--superficie)); border:1px solid color-mix(in srgb, var(--acento) 30%, var(--borda)); border-left:4px solid var(--acento); border-radius:var(--raio-p); padding:1.4rem 1.5rem; margin:1.1rem 0}
.obj-central .eyebrow{color:var(--acento-forte); margin-bottom:.5rem}
.obj-central p{margin:0; font-size:1.18rem; line-height:1.45; color:var(--tinta); max-width:70ch; font-family:var(--fonte-titulo)}
.dois-caminhos{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; margin:1.2rem 0}
.caminho{border:1px solid var(--borda); border-radius:var(--raio-p); background:var(--superficie); padding:1.2rem 1.3rem; box-shadow:var(--sombra)}
.caminho h3{font-size:1.05rem; margin:.6rem 0 .3rem}
.caminho p{margin:0; color:var(--muted); font-size:.92rem}
.caminho .saida{margin-top:.8rem; font-family:var(--fonte-dados); font-size:.82rem; color:var(--tinta-suave); background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.4rem .7rem; display:inline-block}

/* Pagina de cenarios como ARVORE de hierarquia (raiz -> grupos -> cenarios),
   com linhas conectoras desenhadas pelos ::before/::after de cada item. */
.arvore{margin:1.8rem 0 .5rem}
.arv-raiz{display:inline-flex; align-items:center; gap:.6rem; font-family:var(--fonte-titulo); font-weight:600;
  font-size:1.55rem; text-transform:uppercase; letter-spacing:.03em; color:var(--tinta); padding:0 0 .5rem}
.arv-raiz .ponto{width:12px; height:12px; border-radius:50%; background:var(--acento); box-shadow:0 0 0 4px var(--acento-suave); flex:none}
.arvore ul{list-style:none; margin:0; padding-left:24px; position:relative}
.arvore > ul{padding-left:12px}
.arvore li{position:relative; padding:5px 0 5px 8px}
.arvore li::before{content:""; position:absolute; left:-12px; top:0; bottom:0; width:2px; background:var(--borda-forte)}
.arvore li:last-child::before{bottom:auto; height:22px}
.arvore li::after{content:""; position:absolute; left:-12px; top:22px; width:16px; height:2px; background:var(--borda-forte)}
.arv-grupo{display:inline-block; font-weight:700; color:var(--acento-forte); font-size:1rem; text-transform:uppercase; letter-spacing:.05em; padding:6px 2px 4px}
.arv-folha{display:inline-flex; flex-direction:column; align-items:flex-start; gap:.4rem; max-width:660px; text-decoration:none; color:var(--tinta);
  padding:10px 15px; border:1px solid var(--borda); border-radius:5px; background:var(--superficie); box-shadow:var(--sombra);
  transition:border-color .14s, background .14s, transform .14s}
.arv-folha:hover{border-color:var(--acento); background:var(--acento-suave); transform:translateX(2px)}
.arv-linha{display:flex; align-items:baseline; gap:.55rem}
.arv-tag{font-size:.62rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; padding:.2rem .5rem; border-radius:4px; white-space:nowrap; flex:none}
.arv-tag.reg{background:var(--acento-suave); color:var(--acento-forte)}
.arv-tag.clf{background:color-mix(in srgb, var(--atencao) 20%, transparent); color:var(--atencao)}
.arv-tag.mix{background:var(--elevado); color:var(--muted); border:1px solid var(--borda)}
.arv-folha .arv-nome{font-size:.84rem; font-weight:600}
.arv-folha .arv-meta{font-size:.71rem; color:var(--muted); font-family:var(--fonte-dados)}
.arv-mods{list-style:none; margin:.05rem 0 0; padding:0 0 0 4px; font-family:var(--fonte-dados); font-size:.72rem; color:var(--muted)}
.arv-mods li{position:relative; padding:1px 0 1px 14px}
.arv-mods li::before{content:""; position:absolute; left:0; top:0; bottom:0; width:1px; background:var(--borda-forte)}
.arv-mods li:last-child::before{bottom:auto; height:10px}
.arv-mods li::after{content:""; position:absolute; left:0; top:10px; width:9px; height:1px; background:var(--borda-forte)}
.arv-folha.vazia{opacity:.62}
.arv-folha.vazia .arv-nome{font-weight:500; color:var(--muted)}

/* Diario de atividades: timeline com bolinhas + secoes (padrao do otimizador) */
.di-topo{margin:0 0 1.6rem}
.di-busca{width:100%; max-width:440px; font-family:var(--fonte-corpo); font-size:.95rem; color:var(--tinta); background:var(--superficie); border:1px solid var(--borda-forte); border-radius:8px; padding:.6rem .9rem}
.di-busca::placeholder{color:var(--faint)}
.di-busca:focus{outline:none; border-color:var(--acento); box-shadow:0 0 0 3px var(--acento-suave)}
.diaCont{margin-top:.6rem; font-size:.8rem; color:var(--muted)}
.diaItem{position:relative; padding:0 0 26px 22px; border-left:2px solid var(--borda-forte)}
.diaItem:last-child{border-left-color:transparent; padding-bottom:0}
.diaItem::before{content:""; position:absolute; left:-6px; top:9px; width:10px; height:10px; border-radius:50%; background:var(--acento); border:2px solid var(--fundo)}
.diaData{display:inline-block; font-size:12px; font-weight:700; letter-spacing:.05em; color:var(--acento-forte); text-transform:uppercase;
  background:var(--acento-suave); border:1px solid color-mix(in srgb, var(--acento) 32%, var(--borda));
  border-radius:var(--raio-p); padding:5px 11px; margin-bottom:11px}
.diaData .dow{color:var(--muted); font-weight:600; letter-spacing:.02em}
.diaSecao{font-size:10.5px; font-weight:700; letter-spacing:.07em; text-transform:uppercase; color:var(--faint); margin:0 0 4px}
.diaLista + .diaSecao{margin-top:12px}
.diaSecao.prox{color:var(--acento-forte)}
.diaSecao.cor-modelos{color:var(--bom)}
.diaSecao.cor-dados{color:var(--atencao)}
.diaLista{list-style:none; margin:0 0 0 1px; padding:0}
.diaLista>li{position:relative; padding:3px 0 3px 15px; font-size:13.5px; line-height:1.6; color:var(--tinta-suave)}
.diaLista>li::before{content:""; position:absolute; left:0; top:12px; width:5px; height:5px; border-radius:50%; border:1.5px solid var(--faint)}
.diaLista.prox>li::before{border-color:var(--acento); background:var(--acento-suave)}
.diaLista.cor-modelos>li::before{border-color:var(--bom); background:color-mix(in srgb, var(--bom) 18%, transparent)}
.diaLista.cor-dados>li::before{border-color:var(--atencao); background:color-mix(in srgb, var(--atencao) 18%, transparent)}
.diaSub{list-style:none; margin:4px 0 3px; padding:0}
.diaSub li{position:relative; padding:2px 0 2px 14px; font-size:12.8px; line-height:1.55; color:var(--muted)}
.diaSub li::before{content:""; position:absolute; left:0; top:11px; width:7px; height:1.5px; border-radius:1px; background:var(--borda-forte)}
.diaLista.cor-modelos .diaSub li::before{background:color-mix(in srgb, var(--bom) 60%, var(--borda-forte))}
.diaLista.cor-dados .diaSub li::before{background:color-mix(in srgb, var(--atencao) 60%, var(--borda-forte))}
.diaLista.prox .diaSub li::before{background:var(--acento)}
.diaVazio,.diaSemRegistro{color:var(--muted); font-size:14px; padding:10px 0}

:focus-visible{outline:2px solid var(--acento); outline-offset:2px; border-radius:4px}
@media (prefers-reduced-motion:reduce){*{transition:none !important; scroll-behavior:auto !important}}
@media print{
  #sideNav,footer{display:none}
  body{background:#fff; font-size:11pt}
  .cenario,.kpi,.fonte,.cartao,.cenario-item{break-inside:avoid; box-shadow:none}
}
"""

# Script do menu lateral: abre/fecha os grupos (setinha) e recolhe a sidebar
# inteira (botao "Recolher menu"), lembrando o estado recolhido entre paginas.
JS_MENU = (
    "(function(){"
    "document.querySelectorAll('.sn-toggle').forEach(function(b){"
    "b.addEventListener('click',function(){var k=b.parentNode.querySelector('.sn-children');"
    "if(k){b.classList.toggle('sn-open');k.classList.toggle('open');}});});"
    "var s=document.getElementById('appShell'),c=document.getElementById('recolherMenu');"
    "try{if(localStorage.getItem('menuRecolhido')==='1'&&s)s.classList.add('sn-collapsed');}catch(e){}"
    "if(c&&s){c.addEventListener('click',function(){s.classList.toggle('sn-collapsed');"
    "try{localStorage.setItem('menuRecolhido',s.classList.contains('sn-collapsed')?'1':'0');}catch(e){}});}"
    "var h=document.getElementById('menuHamburguer'),sn=document.getElementById('sideNav');"
    "if(h&&sn){h.addEventListener('click',function(){sn.classList.toggle('nav-aberto');});}"
    "var db=document.getElementById('diarioBusca');"
    "if(db){var dias=[].slice.call(document.querySelectorAll('.diaItem')),"
    "ct=document.getElementById('diarioCont'),vz=document.getElementById('diarioVazio');"
    "function semAc(s){return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}"
    "db.addEventListener('input',function(){var termos=semAc(db.value.trim()).split(/\\s+/).filter(Boolean),n=0;"
    "dias.forEach(function(l){var b=l.getAttribute('data-busca');"
    "var ok=termos.every(function(t){return b.indexOf(t)>=0;});l.style.display=ok?'':'none';if(ok)n++;});"
    "if(ct)ct.textContent=termos.length?(n+' de '+dias.length+' dias'):(dias.length+' dias registrados');"
    "if(vz)vz.hidden=n>0;});}"
    "})();"
)


# Atalho pra escapar texto que vai pro HTML.
def escapar(texto) -> str:
    return html.escape(str(texto))


# Formata um numero pra leitura (inteiro, ou com 2-3 casas conforme o tamanho).
def formatar_numero(valor) -> str:
    if valor is None or valor == "":
        return "—"
    try:
        numero = float(valor)
    except (ValueError, TypeError):
        return escapar(valor)
    if numero == int(numero) and abs(numero) < 1e6:
        return f"{int(numero)}"
    tamanho = abs(numero)
    if tamanho >= 100:
        return f"{numero:.1f}"
    if tamanho >= 1:
        return f"{numero:.2f}"
    return f"{numero:.3f}"


# Formata uma data/hora no jeito brasileiro (ou travessao se nao houver).
def formatar_data(momento) -> str:
    return momento.strftime("%d/%m/%Y %H:%M") if momento else "—"


# Formata uma duracao em segundos de forma curta (s / min / h).
def formatar_duracao(segundos) -> str:
    if segundos is None:
        return "—"
    total = int(round(segundos))
    if total < 60:
        return f"{total}s"
    minutos, resto = divmod(total, 60)
    if minutos < 60:
        return f"{minutos}min {resto}s"
    horas, minutos = divmod(minutos, 60)
    return f"{horas}h {minutos}min"


# Diz se, para essa metrica, um valor MENOR e melhor (erro) ou maior (acerto).
def menor_e_melhor(nome_metrica: str) -> bool:
    baixo = nome_metrica.lower()
    return "mae" in baixo or "rmse" in baixo or "erro" in baixo


# Devolve o nome bonito de uma metrica de resumo (ou o proprio nome).
def rotulo_metrica(chave: str) -> str:
    if chave in conteudo.ROTULOS_METRICAS:
        return conteudo.ROTULOS_METRICAS[chave]
    return chave.replace("_media", "").replace("_", " ").upper()


# Monta o menu lateral (arvore): folhas (Inicio, Objetivo, Cenarios, Metodo) e
# os grupos de cenarios como nos recolhiveis. O grupo que contem a pagina atual
# ja abre aberto; a folha atual fica destacada. No padrao do otimizador de
# sortimento: titulo "Navegacao", arvore e, no rodape, tema + recolher menu.
def barra_navegacao(ativo: str, menu: dict) -> str:
    def folha(arquivo, chave, titulo, topo=True):
        atual = ' aria-current="page"' if chave == ativo else ""
        classe = "sn-node" + ("" if topo else " sn-leaf") + (" sn-active" if chave == ativo else "")
        espaco = '<span class="sn-arrow"></span>' if topo else ""
        return f'<a class="{classe}" href="{arquivo}"{atual}>{espaco}<span class="sn-label">{escapar(titulo)}</span></a>'

    partes = [folha(*item) for item in menu["fixas"]]

    # "Cenarios" e um grupo de topo que contem os 3 sub-grupos (cada um com seus
    # cenarios) e um atalho "Ver todos" pra pagina indice. Todos ja vem ABERTOS
    # por padrao (nao precisa clicar); o clique so serve pra recolher, se quiser.
    sub = [folha("cenarios.html", "cenarios", "Ver todos", topo=False)]
    for grupo_nome, itens in menu["grupos_cenarios"]:
        filhos = "".join(folha(arquivo, chave, titulo, topo=False) for arquivo, chave, titulo in itens)
        sub.append(
            '<div class="sn-group">'
            '<button class="sn-node sn-toggle sn-open" type="button">'
            f'<span class="sn-arrow">&#9656;</span><span class="sn-label">{escapar(grupo_nome)}</span></button>'
            f'<div class="sn-children open">{filhos}</div>'
            "</div>"
        )
    partes.append(
        '<div class="sn-group">'
        '<button class="sn-node sn-toggle sn-open" type="button">'
        '<span class="sn-arrow">&#9656;</span><span class="sn-label">Cenarios</span></button>'
        f'<div class="sn-children open">{"".join(sub)}</div>'
        "</div>"
    )
    partes += [folha(*item) for item in menu["extras"]]
    partes.append(folha("diario.html", "diario", "Diario de atividades"))

    return (
        '<aside id="sideNav"><div class="sidenav-inner">'
        '<div class="barra-topo">'
        '<a class="marca" href="index.html"><span class="ponto"></span>'
        f'<span>{escapar(conteudo.PROJETO["titulo"])}</span></a>'
        '<button class="menu-hamburguer" id="menuHamburguer" type="button" aria-label="Abrir ou fechar o menu">&#9776; Menu</button>'
        "</div>"
        '<div class="sidenav-title">Navega&ccedil;&atilde;o</div>'
        f'<nav class="sidenav-tree" aria-label="Navegacao do projeto">{"".join(partes)}</nav>'
        "</div>"
        '<div class="sidenav-rodape">'
        '<button class="sidenav-acao" id="recolherMenu" type="button" title="Recolher menu">'
        '<span class="sn-icon">&laquo;</span><span class="sn-acao-texto">Recolher menu</span></button>'
        "</div></aside>"
    )


# Monta o rodape com o carimbo de quando o site foi gerado.
def rodape(gerado_em: str) -> str:
    projeto = conteudo.PROJETO
    return (
        "<footer><div class=\"rodape\">"
        f"<span>{escapar(projeto['autor'])} · {escapar(projeto['instituicao'])}</span>"
        f"<span>Painel gerado a partir do MLflow local · {escapar(gerado_em)}</span>"
        "</div></footer>"
    )


# Envelopa o conteudo numa pagina HTML completa (cabecalho, tema, rodape).
def documento(titulo: str, ativo: str, corpo: str, gerado_em: str, menu: list) -> str:
    projeto = conteudo.PROJETO
    return (
        "<!doctype html>\n"
        '<html lang="pt-br">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escapar(titulo)} — {escapar(projeto['titulo'])}</title>\n"
        f"<style>{CSS}</style>\n"
        "</head>\n<body>\n"
        '<div id="appShell">\n'
        f"{barra_navegacao(ativo, menu)}\n"
        '<div id="mainArea">\n'
        f'<main class="wrap">\n{corpo}\n</main>\n'
        f"{rodape(gerado_em)}\n"
        "</div>\n</div>\n"
        f"<script>{JS_MENU}</script>\n"
        "</body>\n</html>\n"
    )


# Desenha um diagrama de passos em caixas ligadas por setas (fluxo horizontal).
def diagrama_passos(passos) -> str:
    partes = []
    for indice, (titulo, detalhe) in enumerate(passos):
        if indice:
            partes.append('<div class="seta">→</div>')
        partes.append(f'<div class="passo"><b>{escapar(titulo)}</b><small>{escapar(detalhe)}</small></div>')
    return f'<div class="fluxo">{"".join(partes)}</div>'


# O caminho dos dados (fontes -> montagem -> ... -> painel), usado na home.
def diagrama_fluxo() -> str:
    return diagrama_passos(conteudo.FLUXO)


# Embute uma figura (imagem da pasta imagens/) com uma legenda embaixo.
def figura(arquivo: str, titulo: str, legenda: str) -> str:
    return (
        '<figure class="figura">'
        f'<img src="imagens/{arquivo}" alt="{escapar(titulo)}" loading="lazy">'
        f"<figcaption>{escapar(legenda)}</figcaption></figure>"
    )


# Faixa separadora de secao: um titulo em maiuscula, centralizado entre duas
# linhas horizontais, pra demarcar bem uma secao da outra.
def faixa(titulo: str) -> str:
    return f'<div class="faixa"><span>{escapar(titulo)}</span></div>'


# Desenha a tabela do que compoe o "clima": cada tema e as colunas que gera.
def tabela_colunas_clima() -> str:
    """

    Abre a caixa-preta do "clima": mostra, tema por tema, quais colunas o modelo
    recebe (chuva, temperatura, orvalho...). O total e contado na hora, entao o
    rodape acompanha sozinho se um tema mudar. Serve pra tirar a duvida de quantas
    colunas de clima existem de verdade.

    """
    dados = conteudo.COLUNAS_CLIMA
    linhas = []
    total = 0
    for emoji, tema, colunas in dados["temas"]:
        total += len(colunas)
        chips = "".join(f"<code>{escapar(c)}</code>" for c in colunas)
        linhas.append(
            "<tr>"
            f'<td class="clima-tema"><span class="clima-emoji">{emoji}</span>{escapar(tema)}</td>'
            f'<td><div class="clima-chips">{chips}</div></td>'
            "</tr>"
        )
    rodape = (
        f'Sao <strong>{total} colunas</strong>, todas do <strong>{escapar(dados["fonte"])}</strong> '
        f'({escapar(dados["nota_agregacao"])}). {escapar(dados["nota_lag"])}'
    )
    return (
        f'<p class="clima-intro">{escapar(dados["intro"])}</p>'
        '<div class="tabela-rolavel"><table class="tabela-dados tabela-clima">'
        "<thead><tr><th>Tema</th><th>Colunas</th></tr></thead>"
        f'<tbody>{"".join(linhas)}</tbody></table></div>'
        f'<p class="clima-rodape">{rodape}</p>'
    )


# Desenha a ficha de dados de um cenario: o que entra e o que muda entre os testes.
def ficha_de_dados(nome: str) -> str:
    """

    Uma tabelinha uniforme no topo de cada cenario, com as mesmas linhas em todos
    (alvo, clima, mosquito, El Nino, corte, horizontes). A ultima linha, "O que
    muda", e a diferenca entre os testes daquele cenario e fica destacada. Como a
    estrutura e igual em todo cenario, da pra comparar duas paginas so batendo o
    olho. Devolve vazio se o cenario nao tiver ficha no conteudo.

    """
    ficha = conteudo.FICHA_DADOS.get(nome)
    if not ficha:
        return ""
    linhas = []
    for rotulo, valor in ficha:
        destaque = " ficha-compara" if rotulo == "O que muda" else ""
        linhas.append(
            f'<tr class="{destaque.strip()}">'
            f'<td class="ficha-rot">{escapar(rotulo)}</td>'
            f'<td class="ficha-val">{escapar(valor)}</td></tr>'
        )
    return (
        '<section class="secao"><p class="eyebrow">Os dados deste cenario</p>'
        '<div class="tabela-rolavel"><table class="tabela-dados tabela-ficha">'
        "<thead><tr><th>Ingrediente</th><th>Como entra aqui</th></tr></thead>"
        f'<tbody>{"".join(linhas)}</tbody></table></div></section>'
    )


# Desenha o dicionario de dados: uma linha por coluna da tabela_final, com o
# grupo (etiqueta colorida), a descricao e a unidade. Cobre todas as colunas.
def tabela_dicionario() -> str:
    linhas = []
    for indice, (coluna, grupo, descricao, unidade) in enumerate(conteudo.DICIONARIO_COLUNAS, 1):
        g = grupo.lower()
        if g.startswith("vetor"):
            cls = "vetor"
        elif g.startswith("alvo"):
            cls = "alvo"
        elif g.startswith("clima") or g.startswith("el nino"):
            cls = "clima"
        else:
            cls = "contexto"
        linhas.append(
            "<tr>"
            f'<td class="dic-num">{indice}</td>'
            f'<td><code class="dic-col">{escapar(coluna)}</code></td>'
            f'<td><span class="tag-papel {cls}">{escapar(grupo)}</span></td>'
            f"<td>{escapar(descricao)}</td>"
            f'<td class="dic-unid">{escapar(unidade)}</td>'
            "</tr>"
        )
    return (
        '<div class="tabela-rolavel"><table class="tabela-dados tabela-dic">'
        "<thead><tr><th>#</th><th>Coluna</th><th>Grupo</th><th>O que e</th><th>Unidade</th></tr></thead>"
        f'<tbody>{"".join(linhas)}</tbody></table></div>'
    )


# Desenha um ranking dos modelos em barras horizontais (o melhor em destaque).
def grafico_barras(itens: list, menor_melhor: bool, rotulo: str) -> str:
    """

    Recebe uma lista de (nome, valor) e monta barras horizontais ordenadas do
    melhor pro pior. A barra e RELATIVA (o melhor fica cheio, o pior curtinho),
    pra a comparacao saltar aos olhos; o numero de verdade fica na ponta. So faz
    sentido com 2 modelos ou mais.

    """
    itens = [(nome, valor) for nome, valor in itens if valor is not None]
    if len(itens) < 2:
        return ""
    itens.sort(key=lambda par: par[1], reverse=not menor_melhor)
    valores = [valor for _, valor in itens]
    menor, maior = min(valores), max(valores)
    faixa = (maior - menor) or 1.0

    linhas = []
    for indice, (nome, valor) in enumerate(itens):
        proporcao = (maior - valor) / faixa if menor_melhor else (valor - menor) / faixa
        largura = 8 + proporcao * 92   # de 8% (pior) a 100% (melhor)
        classe = "ranking-linha top" if indice == 0 else "ranking-linha"
        linhas.append(
            f'<div class="{classe}">'
            f'<div class="ranking-nome">{escapar(nome)}</div>'
            f'<div class="ranking-trilho"><div class="ranking-barra" style="width:{largura:.0f}%"></div></div>'
            f'<div class="ranking-valor">{formatar_numero(valor)}</div></div>'
        )
    return f'<div class="ranking"><div class="titulo-graf">Ranking por {escapar(rotulo)}</div>{"".join(linhas)}</div>'


# Desenha a linha do tempo das capturas de mosquito (serie continua, sem vao).
def linha_do_tempo_dados() -> str:
    """

    Mostra, numa regua de 2012 a 2026, a serie de mosquito inteira, sem vao: o
    bloco da Secretaria Municipal de Saude (2012-2025, historico oficial
    corrigido e certificado) seguido do bloco da raspagem propria (2026 em
    diante, continuacao corrente da mesma serie). Uma marca separada assinala
    a enchente de maio de 2024, quando a vistoria de armadilhas parou por 3
    semanas por causa da cheia — nao e um vao de fonte, e um evento pontual.

    """
    largura, altura = 760, 104
    esq, dir_ = 10, 10
    ano_inicio, ano_fim = 2012, 2026.7
    area = largura - esq - dir_

    def px(ano):
        return esq + (ano - ano_inicio) / (ano_fim - ano_inicio) * area

    y_barra, alt_barra = 50, 26
    blocos = [
        (2012.7, 2025.9, "Secretaria (2012-2025)", "var(--acento)"),
        (2025.9, 2026.7, "raspagem propria (2026+)", "var(--acento-forte)"),
    ]
    # A enchente caiu justo na virada abril/maio de 2024 (semanas 28/04, 05/05 e 12/05).
    ano_enchente = 2024.33
    partes = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="Linha do tempo das capturas de mosquito">']
    partes.append(f'<text class="ano" x="{esq}" y="18">Capturas de mosquito ao longo do tempo (serie continua)</text>')
    for inicio, fim, rotulo, cor in blocos:
        xa, xb = px(inicio), px(fim)
        meio = (xa + xb) / 2
        partes.append(f'<rect x="{xa:.0f}" y="{y_barra}" width="{xb - xa:.0f}" height="{alt_barra}" rx="6" fill="{cor}"/>')
        partes.append(f'<text class="bloco-rot" x="{meio:.0f}" y="{y_barra + alt_barra / 2 + 4:.0f}" text-anchor="middle">{rotulo}</text>')
    x_enchente = px(ano_enchente)
    partes.append(f'<line x1="{x_enchente:.0f}" y1="{y_barra - 4}" x2="{x_enchente:.0f}" y2="{y_barra + alt_barra + 4}" stroke="var(--atencao)" stroke-width="2" stroke-dasharray="3 3"/>')
    partes.append(f'<text class="marca-rot" x="{x_enchente:.0f}" y="{y_barra - 8}" text-anchor="middle">enchente mai/2024</text>')
    for ano in range(2012, 2027, 2):
        partes.append(f'<text class="ano" x="{px(ano):.0f}" y="{altura - 4}" text-anchor="middle">{ano}</text>')
    partes.append("</svg>")
    return f'<div class="linha-tempo">{"".join(partes)}</div>'


# Desenha um grafico de linhas em SVG a partir de varias series de pontos.
def grafico_linhas(series: dict, rotulo_x: str, rotulo_y: str) -> str:
    """

    Recebe um dicionario {nome_da_linha: [(x, y), ...]} e devolve um SVG pronto.
    Faz na mao: acha o minimo e o maximo, encaixa os pontos na area de desenho,
    poe uma grade leve, os numeros dos eixos e uma bolinha destacando o ultimo
    ponto de cada linha. Devolve vazio se nao houver dados.

    """
    series = {nome: pontos for nome, pontos in series.items() if pontos}
    if not series:
        return ""

    todos_x = sorted({x for pontos in series.values() for x, _ in pontos})
    todos_y = [y for pontos in series.values() for _, y in pontos]
    minimo_y, maximo_y = min(todos_y), max(todos_y)
    if minimo_y == maximo_y:
        minimo_y, maximo_y = minimo_y - 1, maximo_y + 1
    folga = (maximo_y - minimo_y) * 0.08
    minimo_y, maximo_y = minimo_y - folga, maximo_y + folga

    largura, altura = 720, 320
    esq, dir_, topo, base = 56, 16, 18, 44
    area_l = largura - esq - dir_
    area_a = altura - topo - base

    def px(x):
        if len(todos_x) == 1:
            return esq + area_l / 2
        return esq + (x - todos_x[0]) / (todos_x[-1] - todos_x[0]) * area_l

    def py(y):
        return topo + (maximo_y - y) / (maximo_y - minimo_y) * area_a

    partes = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{escapar(rotulo_y)} por {escapar(rotulo_x)}">']

    # Grade horizontal + numeros do eixo Y.
    for passo in range(5):
        valor = minimo_y + (maximo_y - minimo_y) * passo / 4
        y = py(valor)
        partes.append(f'<line class="grade" x1="{esq}" y1="{y:.1f}" x2="{largura - dir_}" y2="{y:.1f}"/>')
        partes.append(f'<text class="eixo" x="{esq - 8}" y="{y + 3:.1f}" text-anchor="end">{formatar_numero(valor)}</text>')

    # Numeros do eixo X (os horizontes).
    for x in todos_x:
        partes.append(f'<text class="eixo" x="{px(x):.1f}" y="{altura - base + 18}" text-anchor="middle">{formatar_numero(x)}</text>')
    partes.append(f'<text class="eixo-titulo" x="{esq + area_l / 2:.1f}" y="{altura - 6}" text-anchor="middle">{escapar(rotulo_x)}</text>')

    # As linhas de cada serie, com bolinha no ultimo ponto.
    for indice, (nome, pontos) in enumerate(series.items()):
        cor = CORES_SERIES[indice % len(CORES_SERIES)]
        pontos = sorted(pontos)
        caminho = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in pontos)
        partes.append(f'<polyline fill="none" stroke="{cor}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round" points="{caminho}"/>')
        for x, y in pontos:
            partes.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="2.6" fill="{cor}"/>')
        ux, uy = pontos[-1]
        partes.append(f'<circle cx="{px(ux):.1f}" cy="{py(uy):.1f}" r="4.4" fill="{cor}" stroke="var(--superficie)" stroke-width="2"/>')

    partes.append("</svg>")

    # Legenda com o nome de cada linha.
    itens = []
    for indice, nome in enumerate(series):
        cor = CORES_SERIES[indice % len(CORES_SERIES)]
        itens.append(f'<span><i style="background:{cor}"></i>{escapar(nome)}</span>')
    legenda = f'<div class="legenda">{"".join(itens)}</div>'

    return f'<div class="grafico"><div class="titulo-graf">{escapar(rotulo_y)} por {escapar(rotulo_x)}</div>{"".join(partes)}{legenda}</div>'


# Converte um texto de celula em numero, ou None se nao der.
def _numero(texto):
    try:
        return float(texto)
    except (ValueError, TypeError):
        return None


# Acha, numa lista de colunas, a primeira que bate com um dos nomes procurados.
def _achar_coluna(colunas, procurados):
    mapa = {c.lower(): c for c in colunas}
    for nome in procurados:
        if nome in mapa:
            return mapa[nome]
    return None


# A partir dos modelos de um cenario, monta as series pro grafico por horizonte.
def dados_do_grafico(cenario) -> str:
    """

    Cada modelo guarda uma tabela de resultado (o CSV anexado). Se essa tabela
    tiver a coluna de horizonte e uma coluna de erro/acerto, da pra desenhar um
    grafico de "metrica por horizonte". A regra: se ha varios modelos, cada
    linha do grafico e um modelo (comparacao direta); se ha um modelo so mas com
    varios conjuntos, cada linha e um conjunto. Sem coluna de horizonte, nao
    desenha nada.

    """
    referencia = None
    for modelo in cenario.modelos:
        for tabela in modelo.tabelas.values():
            coluna_x = _achar_coluna(tabela["colunas"], ["h", "horizonte"])
            coluna_metrica = _achar_coluna(tabela["colunas"], ["mae", "rmse", "r2"])
            if coluna_x and coluna_metrica:
                referencia = (coluna_x, coluna_metrica)
                break
        if referencia:
            break
    if not referencia:
        return ""

    coluna_x, coluna_metrica = referencia
    rotulo_y = ROTULO_COLUNA.get(coluna_metrica.lower(), coluna_metrica)

    def series_de(linhas, rotulo_linha):
        por_x = {}
        for linha in linhas:
            x = _numero(linha.get(coluna_x))
            y = _numero(linha.get(coluna_metrica))
            if x is not None and y is not None:
                por_x.setdefault(x, []).append(y)
        return rotulo_linha, [(x, sum(v) / len(v)) for x, v in sorted(por_x.items())]

    series = {}
    if len(cenario.modelos) > 1:
        for modelo in cenario.modelos:
            for tabela in modelo.tabelas.values():
                if _achar_coluna(tabela["colunas"], ["h", "horizonte"]):
                    nome, pontos = series_de(tabela["linhas"], modelo.nome)
                    series[nome] = pontos
                    break
    else:
        modelo = cenario.modelos[0]
        tabela = next((t for t in modelo.tabelas.values() if _achar_coluna(t["colunas"], ["h", "horizonte"])), None)
        if not tabela:
            return ""
        coluna_conjunto = _achar_coluna(tabela["colunas"], ["conjunto", "grupo"])
        conjuntos = {linha.get(coluna_conjunto) for linha in tabela["linhas"]} if coluna_conjunto else set()
        if coluna_conjunto and len(conjuntos) > 1:
            for conjunto in sorted(c for c in conjuntos if c is not None):
                linhas = [linha for linha in tabela["linhas"] if linha.get(coluna_conjunto) == conjunto]
                nome, pontos = series_de(linhas, conjunto)
                series[nome] = pontos
        else:
            nome, pontos = series_de(tabela["linhas"], modelo.nome)
            series[nome] = pontos

    return grafico_linhas(series, "horizonte (semanas)", rotulo_y)


# Descobre, em ordem, quais metricas de resumo entram na tabela comparativa.
def metricas_do_cenario(cenario) -> list:
    presentes = set()
    for modelo in cenario.modelos:
        presentes.update(modelo.metricas)
    presentes -= conteudo.METRICAS_ESCONDIDAS
    ordenadas = [m for m in PREFERENCIA_METRICAS if m in presentes]
    ordenadas += sorted(presentes - set(ordenadas))
    return ordenadas


# Monta a tabela que compara os modelos de um cenario (destaca o melhor de cada).
def tabela_comparativa(cenario, metricas) -> str:
    melhores = {}
    for metrica in metricas:
        valores = [m.metricas[metrica] for m in cenario.modelos if metrica in m.metricas]
        if valores:
            melhores[metrica] = min(valores) if menor_e_melhor(metrica) else max(valores)

    cabecalho = ["Modelo"] + [rotulo_metrica(m) for m in metricas] + ["Duracao", "Quando"]
    linhas_html = [f"<th>{escapar(c)}</th>" for c in cabecalho]
    corpo = []
    for modelo in cenario.modelos:
        celulas = [f'<td><span class="modelo-nome">{escapar(modelo.nome)}</span><div class="status {escapar(modelo.status)}">{escapar(modelo.status)}</div></td>']
        for metrica in metricas:
            valor = modelo.metricas.get(metrica)
            classe = "num"
            if metrica in melhores and valor is not None and abs(valor - melhores[metrica]) < 1e-9 and len(cenario.modelos) > 1:
                classe = "num melhor"
            celulas.append(f'<td class="{classe}">{formatar_numero(valor)}</td>')
        celulas.append(f'<td class="num">{formatar_duracao(modelo.duracao_segundos)}</td>')
        celulas.append(f'<td class="num">{formatar_data(modelo.fim)}</td>')
        corpo.append(f"<tr>{''.join(celulas)}</tr>")

    return (
        '<div class="tabela-rolavel"><table class="tabela">'
        f"<thead><tr>{''.join(linhas_html)}</tr></thead>"
        f"<tbody>{''.join(corpo)}</tbody></table></div>"
    )


# Monta uma tabelinha de parametros (chave -> valor) com titulo.
def _tabela_parametros(titulo, itens) -> str:
    if not itens:
        return ""
    linhas = "".join(f"<tr><td>{escapar(nome)}</td><td>{escapar(valor)}</td></tr>" for nome, valor in itens)
    return f'<div class="grupo-param"><h4>{escapar(titulo)}</h4><table class="params">{linhas}</table></div>'


# Mostra os detalhes de um modelo: parametros agrupados + a tabela de resultado.
def detalhes_do_modelo(modelo) -> str:
    do_modelo, do_clima, da_config = [], [], []
    for chave, valor in modelo.parametros.items():
        if chave.startswith("modelo_selecao_clima"):
            do_clima.append((chave.replace("modelo_selecao_clima.", "").replace("modelo_selecao_clima_", ""), valor))
        elif chave.startswith("modelo") and chave not in {"modelo_nome"}:
            do_modelo.append((chave.replace("modelo.", "").replace("modelo_", ""), valor))
        else:
            da_config.append((conteudo.ROTULOS_PARAMETROS.get(chave, chave), valor))

    grupos = (
        _tabela_parametros("Modelo e ajustes", do_modelo)
        + _tabela_parametros("Escolha das colunas de clima", do_clima)
        + _tabela_parametros("Configuracao do experimento", da_config)
    )

    tabelas = []
    for nome_arquivo, tabela in modelo.tabelas.items():
        cabecalho = "".join(f"<th>{escapar(c)}</th>" for c in tabela["colunas"])
        linhas = []
        for linha in tabela["linhas"]:
            celulas = "".join(f'<td class="num">{formatar_numero(linha.get(c))}</td>' for c in tabela["colunas"])
            linhas.append(f"<tr>{celulas}</tr>")
        tabelas.append(
            f'<div class="grupo-param"><h4>{escapar(nome_arquivo)}</h4>'
            '<div class="tabela-rolavel"><table class="tabela">'
            f"<thead><tr>{cabecalho}</tr></thead><tbody>{''.join(linhas)}</tbody></table></div></div>"
        )

    return (
        f'<details class="detalhes"><summary>Detalhes de {escapar(modelo.nome)}</summary>'
        f"{grupos}{''.join(tabelas)}</details>"
    )


# Devolve os cenarios na ordem de exibicao: primeiro na ordem dos grupos, depois
# o que sobrar do conteudo e, por fim, os que so existem no mlflow.
def ordem_dos_cenarios(cenarios) -> list:
    nomes = []
    for _, membros in conteudo.GRUPOS_CENARIOS:
        for nome in membros:
            if nome not in nomes:
                nomes.append(nome)
    for nome in conteudo.CENARIOS:
        if nome not in nomes:
            nomes.append(nome)
    for cenario in cenarios:
        if cenario.nome not in nomes:
            nomes.append(cenario.nome)
    return nomes


# O rotulo curto de um cenario no menu (o "menu", senao o titulo, senao o nome).
def rotulo_menu_cenario(nome: str) -> str:
    info = conteudo.CENARIOS.get(nome, {})
    return info.get("menu") or info.get("titulo") or nome


# Agrupa uma lista de nomes de cenario em [(grupo, [nomes...]), ...], seguindo os
# grupos do conteudo; o que nao cair em nenhum grupo vai para um grupo "Outros".
def agrupar_cenarios(nomes: list) -> list:
    restantes = list(nomes)
    grupos = []
    for grupo_nome, membros in conteudo.GRUPOS_CENARIOS:
        itens = [nome for nome in membros if nome in restantes]
        if itens:
            grupos.append((grupo_nome, itens))
            for nome in itens:
                restantes.remove(nome)
    if restantes:
        grupos.append(("Outros", restantes))
    return grupos


# Monta a pagina isolada de UM cenario (capa + ranking + tabela + grafico + detalhes).
def pagina_cenario(nome: str, cenario) -> str:
    """

    Cada cenario ganha sua propria pagina, so com os testes dele: no topo a
    pergunta que ele responde; depois o ranking dos modelos, a tabela comparativa
    e o grafico por horizonte; no fim, os detalhes (hiperparametros e a tabela
    completa) de cada modelo. Se o cenario ainda nao foi rodado, mostra o comando.

    """
    info = conteudo.CENARIOS.get(nome, {})
    titulo = info.get("titulo", nome)
    pergunta = info.get("pergunta", "")
    descricao = info.get("descricao", "")

    tipo = info.get("tipo", "")
    eyebrow = f"Cenario &middot; {escapar(tipo)}" if tipo else "Cenario"
    cabeca = (
        f'<section class="hero"><p class="eyebrow">{eyebrow}</p>'
        f"<h1>{escapar(titulo)}</h1>"
        + (f'<p class="lead">{escapar(pergunta)}</p>' if pergunta else "")
        + f'<p class="tecnico" style="margin-top:.7rem">{escapar(nome)}</p></section>'
    )
    ficha = ficha_de_dados(nome)
    if not (cenario and cenario.modelos):
        return (
            cabeca + ficha
            + '<div class="vazio"><p>Este cenario ainda nao foi rodado.</p>'
            f"<p>Rode <code>python3 main.py --experimento {escapar(nome)}</code> e depois "
            "<code>python3 gerar.py</code> pra ver os modelos e resultados aqui.</p></div>"
        )

    metricas = metricas_do_cenario(cenario)
    corpo = f'<p class="descricao">{escapar(descricao)}</p>' if descricao else ""
    corpo += ficha
    if len(cenario.modelos) > 1 and metricas:
        primaria = metricas[0]
        itens = [(modelo.nome, modelo.metricas.get(primaria)) for modelo in cenario.modelos]
        corpo += grafico_barras(itens, menor_e_melhor(primaria), rotulo_metrica(primaria))
    corpo += tabela_comparativa(cenario, metricas)
    corpo += dados_do_grafico(cenario)
    corpo += '<section class="secao"><p class="eyebrow">Detalhes de cada modelo</p>'
    corpo += "".join(detalhes_do_modelo(modelo) for modelo in cenario.modelos)
    corpo += "</section>"
    return cabeca + corpo


# Monta os indicadores gerais (quantos cenarios, quantos modelos, melhor R²...).
def indicadores_gerais(cenarios) -> str:
    total_cenarios = len(cenarios)
    total_modelos = sum(len(c.modelos) for c in cenarios)

    melhor_r2 = None
    ultima = None
    for cenario in cenarios:
        for modelo in cenario.modelos:
            if "R2_media" in modelo.metricas:
                valor = modelo.metricas["R2_media"]
                melhor_r2 = valor if melhor_r2 is None else max(melhor_r2, valor)
            if modelo.fim and (ultima is None or modelo.fim > ultima):
                ultima = modelo.fim

    cartoes = [
        ("Cenarios", str(total_cenarios)),
        ("Modelos treinados", str(total_modelos)),
        ("Melhor R²", formatar_numero(melhor_r2) if melhor_r2 is not None else "—"),
        ("Ultima execucao", ultima.strftime("%d/%m/%Y") if ultima else "—"),
    ]
    itens = "".join(f'<div class="kpi"><div class="valor">{escapar(v)}</div><div class="rotulo">{escapar(r)}</div></div>' for r, v in cartoes)
    return f'<div class="kpis">{itens}</div>'


# Monta a pagina inicial: capa + indicadores + atalhos e, embaixo, a antiga
# pagina de Dados embutida (Inicio e Dados viraram uma pagina so).
def pagina_inicio(cenarios) -> str:
    projeto = conteudo.PROJETO
    objetivo = conteudo.OBJETIVO
    cartoes = [
        ("metodologia.html", "Metodologia", "O objetivo do trabalho e como as previsoes sao feitas e testadas.", "Abrir →"),
        ("metodologia.html#dados", "Dados", "As fontes usadas: mosquito, clima, casos e El Nino.", "Abrir →"),
        ("cenarios.html", "Cenarios", "Cada pergunta do projeto e os modelos treinados nela.", "Abrir →"),
    ]
    atalhos = "".join(
        f'<a class="cartao" href="{arq}"><h3>{escapar(t)}</h3><p>{escapar(d)}</p><span class="seta">{escapar(s)}</span></a>'
        for arq, t, d, s in cartoes
    )
    return (
        '<section class="hero">'
        f'<p class="eyebrow">{escapar(projeto["instituicao"])} · {escapar(projeto["local"])}</p>'
        f"<h1>{escapar(objetivo['frase'])}</h1>"
        f'<p class="lead">{escapar(projeto["subtitulo"])}. Este painel reune os dados, o objetivo e os resultados dos experimentos num lugar so.</p>'
        "</section>"
        f"{indicadores_gerais(cenarios)}"
        f'<section class="secao"><div class="cartoes">{atalhos}</div></section>'
    )


# Desenha (SVG na mao) os horizontes de previsao: hoje -> 4, 8 e 12 semanas.
def svg_horizonte() -> str:
    x0, x1, y = 70, 540, 72

    def px(sem):
        return x0 + (x1 - x0) * sem / 12

    meses = {4: "1 mes", 8: "2 meses", 12: "3 meses"}
    p = ['<svg viewBox="0 0 600 150" role="img" aria-label="Horizontes de previsao">']
    p.append(f'<line x1="{x0}" y1="{y}" x2="{x1 + 12}" y2="{y}" stroke="var(--borda-forte)" stroke-width="2" stroke-dasharray="6 5"/>')
    p.append(f'<circle cx="{x0}" cy="{y}" r="6" fill="var(--tinta)"/>')
    p.append(f'<text class="svg-rot" x="{x0}" y="{y + 28}" text-anchor="middle" font-weight="700">hoje</text>')
    for sem in (4, 8, 12):
        x = px(sem)
        p.append(f'<circle cx="{x:.0f}" cy="{y}" r="5" fill="var(--acento)"/>')
        p.append(f'<text class="svg-rot" x="{x:.0f}" y="{y - 16}" text-anchor="middle">{sem} semanas</text>')
        p.append(f'<text class="svg-sub" x="{x:.0f}" y="{y + 28}" text-anchor="middle">{meses[sem]}</text>')
    p.append("</svg>")
    return "".join(p)


# Monta a pagina de Metodologia: junta o objetivo e o metodo num lugar so, com
# poucos textos e muitos esquemas (o objetivo, a pergunta central, o caminho dos
# dados e como as previsoes sao testadas).
def pagina_metodologia() -> str:
    obj = conteudo.OBJETIVO
    return (
        '<section class="hero"><p class="eyebrow">Metodologia</p>'
        "<h1>Metodologia</h1>"
        f'<p class="lead">{escapar(obj["frase"])}</p></section>'
        # A pergunta central + o objetivo em destaque, com os horizontes ilustrando o "1, 2 e 3 meses".
        f'<section class="secao">{faixa("A pergunta e o objetivo")}'
        '<div class="callout" style="margin-top:0">'
        f'<p><strong>{escapar(obj["pergunta_central"])}</strong></p></div>'
        '<div class="obj-central"><p class="eyebrow">Objetivo central</p>'
        f'<p>{escapar(obj["objetivo_central"])}</p></div>'
        f'<div class="esquema">{svg_horizonte()}'
        '<div class="cap">Os tres horizontes de antecedencia: 4, 8 e 12 semanas — ou seja, 1, 2 e 3 meses a frente.</div></div>'
        "</section>"
        # Os dois tipos de modelo usados.
        f'<section class="secao">{faixa("Dois caminhos de modelo")}'
        '<div class="dois-caminhos">'
        '<div class="caminho"><span class="arv-tag reg">Regressao</span>'
        "<h3>Quantos casos vao ter?</h3><p>Preve o numero de casos de dengue.</p>"
        '<span class="saida">saida: um numero (ex.: 320 casos)</span></div>'
        '<div class="caminho"><span class="arv-tag clf">Classificacao</span>'
        "<h3>Vai ter surto?</h3><p>Preve se vai passar do limite de surto.</p>"
        '<span class="saida">saida: sim / nao</span></div>'
        "</div></section>"
        # Como as previsoes sao testadas (validacao honesta + provas estatisticas).
        f'<section class="secao">{faixa("Como testamos")}'
        f'{figura("walkforward.png", "Validacao walk-forward", "Em cada corte, o modelo treina so com o passado e preve ate 12 semanas a frente; depois compara com o real. Nunca ve o futuro que tenta prever.")}'
        '<p class="lead" style="font-size:1rem; margin-top:1.2rem">Para saber se uma diferenca e real (e nao sorte), usamos testes estatisticos: <strong>McNemar</strong> no alarme de surto e <strong>Diebold-Mariano</strong> no erro de previsao.</p>'
        "</section>"
        # Os dados (movidos da home): tudo que alimenta os modelos, no fim da metodologia.
        f'<section class="secao" id="dados">{faixa("Dados do projeto")}'
        '<p class="lead" style="margin-top:0">Tudo e medido semana a semana e depois juntado numa tabela unica.</p></section>'
        f"{secoes_dados()}"
    )


# Monta as secoes de dados (fluxo + fontes + clima + graficos), SEM capa propria,
# pra serem embutidas na pagina inicial (Inicio e Dados viraram uma pagina so).
def secoes_dados() -> str:
    linhas = []
    for fonte in conteudo.FONTES_DADOS:
        badge = ' <span class="badge vital">insubstituivel</span>' if fonte.get("vital") else ""
        tipo = fonte.get("tipo", "")
        tag = f'<span class="tag-papel {escapar(tipo)}">{escapar(tipo)}</span>' if tipo else ""
        linhas.append(
            "<tr>"
            f'<td><div class="fonte-nome">{escapar(fonte["nome"])}{badge}</div></td>'
            f'<td class="cobertura">{escapar(fonte["periodo"])}</td>'
            f'<td class="freq">{escapar(fonte["cadencia"])}</td>'
            f"<td>{tag}</td>"
            f'<td class="origem-cel">{escapar(fonte["origem"])}</td>'
            "</tr>"
        )
    tabela = (
        '<div class="tabela-rolavel"><table class="tabela-dados">'
        "<thead><tr><th>Fonte</th><th>Cobertura</th><th>Frequencia</th><th>Papel</th><th>Origem</th></tr></thead>"
        f'<tbody>{"".join(linhas)}</tbody></table></div>'
    )
    return (
        f'<section class="secao">{faixa("O caminho dos dados")}{diagrama_fluxo()}</section>'
        f'<section class="secao">{faixa("Fontes utilizadas")}{tabela}</section>'
        f'<section class="secao">{faixa("O que compoe o clima")}{tabela_colunas_clima()}</section>'
        f'<section class="secao">{faixa("A serie do mosquito")}{figura("vetor_por_semana.png", "Aedes aegypti capturados por semana", "Aedes aegypti capturados por semana em POA, serie continua de 2012 a 2026: o historico oficial da Secretaria Municipal de Saude seguido da raspagem propria, sem vao entre as duas fontes. Sao 718 semanas com dado (23/09/2012 a 09/08/2026), 636.587 inspecoes de armadilha e 236.166 femeas capturadas; faltam so 7 semanas em 14 anos, 3 delas a enchente de maio de 2024, quando as vistorias pararam.")}</section>'
        f'<section class="secao">{faixa("Limitacoes atuais")}{figura("vetor_vs_casos.png", "Mosquito capturado x casos de dengue", "Mosquito capturado x casos de dengue confirmados. Os surtos de 2024 e 2025 agora tem mosquito medido ao lado — a limitacao que sobra e outra: casos e clima so cobrem 2018 em diante, e a serie ainda tem cerca de 2 epidemias grandes para comparar, o que limita o poder estatistico dos testes.")}</section>'
        f'<section class="secao">{faixa("Dicionario de dados usados na tabela final de features")}'
        '<p class="lead" style="font-size:1rem; margin-top:0">Cada linha e uma coluna da <strong>tabela_final</strong> — o arquivo unico que junta tudo por semana e alimenta os modelos.</p>'
        f"{tabela_dicionario()}</section>"
    )


_DIAS_SEMANA = ("Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo")
_MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro")


# A partir de uma data AAAA-MM-DD, devolve (DD/MM/AAAA, dia_da_semana, mes_por_extenso).
def _partes_data(iso: str):
    try:
        ano, mes, dia = (int(x) for x in iso.split("-"))
        d = datetime.date(ano, mes, dia)
        return f"{dia:02d}/{mes:02d}/{ano}", _DIAS_SEMANA[d.weekday()], _MESES[mes - 1]
    except (ValueError, IndexError):
        return iso, "", ""


# Tira acentos e baixa a caixa (pra busca do diario bater "julho" com "Julho" etc.).
def _sem_acento(texto: str) -> str:
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()


# Monta um item da lista do diario. O item pode ser uma frase solta ou um topico
# com sub-topicos: nesse caso ele vem como {"texto": ..., "sub": [...]} e os
# sub-topicos aparecem recuados, com um tracinho em vez da bolinha.
def _item_diario(item) -> str:
    if isinstance(item, str):
        return f"<li>{escapar(item)}</li>"

    texto = item["texto"]
    sub_topicos = item.get("sub", [])
    if not sub_topicos:
        return f"<li>{escapar(texto)}</li>"

    linhas_de_dentro = ""
    for sub in sub_topicos:
        linhas_de_dentro += f"<li>{escapar(sub)}</li>"
    return f'<li>{escapar(texto)}<ul class="diaSub">{linhas_de_dentro}</ul></li>'


# Junta num texto so tudo o que esta escrito num item do diario (a frase e, se
# houver, os sub-topicos). Serve para a busca da pagina achar as palavras que
# estao dentro dos sub-topicos tambem.
def _texto_do_item(item) -> str:
    if isinstance(item, str):
        return item

    partes = [item["texto"]]
    partes.extend(item.get("sub", []))
    return " ".join(partes)


# Monta um bloco do diario (rotulo + lista de itens); vazio se nao houver itens.
def _bloco_diario(rotulo: str, itens: list, classe: str = "") -> str:
    if not itens:
        return ""

    lis = ""
    for item in itens:
        lis += _item_diario(item)
    return f'<div class="diaSecao {classe}">{escapar(rotulo)}</div><ul class="diaLista {classe}">{lis}</ul>'


# Monta a pagina "Diario de atividades": timeline com um bloco por dia (data +
# dia da semana, as atividades e "Proximos passos") e busca por data, mes ou
# palavra (sem acento, varios termos ao mesmo tempo). As atividades do dia podem
# estar numa lista so ou separadas por assunto, com um titulo para cada assunto.
def pagina_diario() -> str:
    entradas = conteudo.DIARIO
    if not entradas:
        corpo = '<div class="vazio"><p>Ainda sem registros. Adicione dias em <code>DIARIO</code> no conteudo.py.</p></div>'
    else:
        blocos = []
        for e in entradas:
            data_br, dia_sem, mes_nome = _partes_data(e["data"])
            feito = e.get("feito", [])
            proximos = e.get("proximos", [])
            blocos_por_assunto = e.get("blocos", [])

            # As atividades do dia podem vir de duas formas: soltas numa lista
            # ("feito") ou separadas por assunto ("blocos", cada um com titulo e
            # itens). Quando ha blocos, cada assunto ganha seu proprio titulo.
            if blocos_por_assunto:
                atividades_html = ""
                itens_das_atividades = []
                for bloco in blocos_por_assunto:
                    # A cor do bloco e opcional e vira uma classe da folha de
                    # estilo: "modelos" virou "cor-modelos". Bloco sem cor fica
                    # no cinza padrao.
                    nome_da_cor = bloco.get("cor", "")
                    if nome_da_cor:
                        classe_do_bloco = f"cor-{nome_da_cor}"
                    else:
                        classe_do_bloco = ""
                    atividades_html += _bloco_diario(bloco["titulo"], bloco["itens"], classe_do_bloco)
                    itens_das_atividades.extend(bloco["itens"])
            else:
                atividades_html = _bloco_diario("Atividades realizadas", feito)
                itens_das_atividades = list(feito)

            textos_para_busca = [data_br, dia_sem, mes_nome, e["data"]]
            for item in itens_das_atividades:
                textos_para_busca.append(_texto_do_item(item))
            for item in proximos:
                textos_para_busca.append(_texto_do_item(item))

            busca = _sem_acento(" ".join(textos_para_busca))
            secoes = atividades_html + _bloco_diario("Proximos passos", proximos, "prox")
            if not secoes:
                secoes = '<p class="diaSemRegistro">Sem registro.</p>'
            blocos.append(
                f'<div class="diaItem" data-busca="{escapar(busca)}">'
                f'<div class="diaData">{escapar(data_br)} <span class="dow">&middot; {escapar(dia_sem)}</span></div>'
                f"{secoes}</div>"
            )
        corpo = (
            '<div class="di-topo">'
            '<input type="search" id="diarioBusca" class="di-busca" placeholder="buscar: 27/07, julho, raspagem, secretaria..." aria-label="Buscar no diario">'
            f'<div class="diaCont" id="diarioCont">{len(entradas)} dias registrados</div>'
            "</div>"
            f'<div class="diaTimeline">{"".join(blocos)}</div>'
            '<p class="diaVazio" id="diarioVazio" hidden>Nenhum dia encontrado.</p>'
        )
    return (
        '<section class="hero"><p class="eyebrow">Diario</p>'
        "<h1>Diario de atividades</h1>"
        '<p class="lead">O que foi sendo feito no projeto, dia a dia. Busque por data, mes ou palavra.</p></section>'
        f'<section class="secao">{corpo}</section>'
    )


# Monta a pagina "Cenarios": um indice com um cartao por cenario (leva pra pagina de cada um).
def pagina_cenarios(cenarios) -> str:
    """

    E a porta de entrada dos cenarios: mostra os indicadores gerais e um cartao
    por cenario, cada um levando pra pagina isolada daquele cenario. Os que ainda
    nao foram rodados aparecem marcados.

    """
    por_nome = {c.nome: c for c in cenarios}
    cabeca = (
        '<section class="hero"><p class="eyebrow">Cenarios</p>'
        "<h1>Os cenarios do projeto</h1>"
        '<p class="lead">Cada cenario e uma pergunta. Clique num deles pra ver os modelos, os resultados e os ajustes daquele teste.</p></section>'
    )
    corpo = indicadores_gerais(cenarios) if cenarios else ""
    ramos = []
    for grupo_nome, itens in agrupar_cenarios(ordem_dos_cenarios(cenarios)):
        folhas = []
        for nome in itens:
            info = conteudo.CENARIOS.get(nome, {})
            rotulo = info.get("rotulo") or info.get("titulo", nome)
            pergunta = info.get("pergunta", "")
            tipo = info.get("tipo", "")
            tbaixo = tipo.lower()
            classe_tag = "mix" if ("regress" in tbaixo and "classif" in tbaixo) else "clf" if "classif" in tbaixo else "reg"
            etiqueta = f'<span class="arv-tag {classe_tag}">{escapar(tipo)}</span>' if tipo else ""
            cenario = por_nome.get(nome)
            if cenario and cenario.modelos:
                quantidade = len(cenario.modelos)
                meta = f'{quantidade} modelo{"s" if quantidade > 1 else ""}'
                lista = "".join(f"<li>{escapar(modelo.nome)}</li>" for modelo in cenario.modelos)
                corpo_mods = f'<span class="arv-meta">{meta}</span><ul class="arv-mods">{lista}</ul>'
                vazia = ""
            else:
                corpo_mods = '<span class="arv-meta">nao rodado</span>'
                vazia = " vazia"
            folhas.append(
                f'<li><a class="arv-folha{vazia}" href="cenario-{escapar(nome)}.html" title="{escapar(pergunta)}">'
                f'<span class="arv-linha">{etiqueta}<span class="arv-nome">{escapar(rotulo)}</span></span>'
                f'{corpo_mods}</a></li>'
            )
        ramos.append(
            f'<li><span class="arv-grupo">{escapar(grupo_nome)}</span>'
            f'<ul>{"".join(folhas)}</ul></li>'
        )
    arvore = (
        '<div class="arvore">'
        '<div class="arv-raiz"><span class="ponto"></span>Cenarios do projeto</div>'
        f'<ul>{"".join(ramos)}</ul></div>'
    )
    corpo += f'<section class="secao">{arvore}</section>'
    return cabeca + corpo


# Transforma o nome do arquivo num endereco de pagina (tira o numero de ordem).
def _apelido(nome_arquivo: str) -> str:
    nome = re.sub(r"^\d+[_-]", "", nome_arquivo)
    nome = re.sub(r"[^0-9A-Za-z_-]+", "-", nome).strip("-").lower()
    if not nome or nome in NOMES_RESERVADOS:
        nome = f"{nome or 'pagina'}-pagina"
    return nome


# Le o cabecalho opcional (titulo: / ordem:) do topo de um arquivo .md.
def _ler_cabecalho(bruto: str, nome_arquivo: str):
    """

    Deixa a pessoa escolher o titulo do menu e a posicao dele escrevendo, nas
    PRIMEIRAS linhas do arquivo, "titulo: ..." e "ordem: ...". Os dois sao
    opcionais: sem titulo, usa o nome do arquivo; sem ordem, a pagina entra no
    fim do menu. O resto do arquivo e o conteudo.

    """
    titulo = None
    ordem = 100
    linhas = bruto.replace("\r\n", "\n").split("\n")
    corte = 0
    while corte < len(linhas):
        achou = re.match(r"^(titulo|ordem)\s*:\s*(.+)$", linhas[corte].strip(), re.IGNORECASE)
        if not achou:
            break
        if achou.group(1).lower() == "titulo":
            titulo = achou.group(2).strip()
        else:
            try:
                ordem = int(achou.group(2).strip())
            except ValueError:
                pass
        corte += 1

    corpo = "\n".join(linhas[corte:]).strip("\n")
    if titulo is None:
        titulo = re.sub(r"^\d+[_-]", "", nome_arquivo).replace("_", " ").replace("-", " ").strip().capitalize()
    return titulo, ordem, corpo


# Le a pasta 'paginas/' e transforma cada .md numa pagina pronta pro site.
def carregar_paginas_extras(pasta_paginas: Path) -> list:
    """

    Cada arquivo .md que voce poe na pasta 'paginas/' vira uma pagina do site, ja
    aparecendo no menu. E o jeito de ir crescendo o site do projeto sem mexer em
    codigo: escreveu o arquivo, rodou o gerador, a pagina aparece.

    """
    if not pasta_paginas.is_dir():
        return []

    paginas = []
    for arquivo in sorted(pasta_paginas.iterdir()):
        if arquivo.suffix.lower() != ".md":
            continue
        titulo, ordem, corpo = _ler_cabecalho(arquivo.read_text(encoding="utf-8"), arquivo.stem)
        apelido = _apelido(arquivo.stem)
        paginas.append({
            "arquivo": f"{apelido}.html",
            "chave": apelido,
            "titulo": titulo,
            "ordem": ordem,
            "html": markdown_simples.para_html(corpo),
        })

    paginas.sort(key=lambda pagina: (pagina["ordem"], pagina["titulo"]))
    return paginas


# Le tudo, monta as paginas (fixas + as da pasta paginas/) e grava em 'site/'.
def gerar(pasta_mlruns: Path, pasta_site: Path, pasta_paginas: Path) -> None:
    """

    E o passo a passo do comando: le os cenarios do mlruns e as paginas extras,
    monta o menu com todas, escreve cada pagina e carimba a data/hora da geracao
    no rodape pra ficar claro quando o painel foi atualizado pela ultima vez.

    """
    cenarios = leitor_mlflow.carregar_cenarios(pasta_mlruns)
    extras = carregar_paginas_extras(pasta_paginas)
    gerado_em = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pasta_site.mkdir(parents=True, exist_ok=True)

    # Arquivo vazio que diz ao GitHub Pages pra servir os arquivos como estao
    # (sem passar pelo Jekyll, que ignoraria coisas comecando com "_").
    (pasta_site / ".nojekyll").write_text("", encoding="utf-8")

    # Copia as imagens (graficos) pra dentro do site, pra ele ficar auto-contido.
    pasta_imagens = PASTA_AQUI / "imagens"
    if pasta_imagens.is_dir():
        (pasta_site / "imagens").mkdir(exist_ok=True)
        for imagem in pasta_imagens.glob("*.png"):
            shutil.copy2(imagem, pasta_site / "imagens" / imagem.name)

    por_nome = {c.nome: c for c in cenarios}
    nomes = ordem_dos_cenarios(cenarios)
    menu = {
        "fixas": list(PAGINAS),
        "grupos_cenarios": [
            (grupo_nome, [(f"cenario-{nome}.html", f"cen-{nome}", rotulo_menu_cenario(nome)) for nome in itens])
            for grupo_nome, itens in agrupar_cenarios(nomes)
        ],
        "extras": [(p["arquivo"], p["chave"], p["titulo"]) for p in extras],
    }

    fixas = {
        "index.html": ("Inicio", "inicio", pagina_inicio(cenarios)),
        "metodologia.html": ("Metodologia", "metodologia", pagina_metodologia()),
        "cenarios.html": ("Cenários", "cenarios", pagina_cenarios(cenarios)),
        "diario.html": ("Diario de atividades", "diario", pagina_diario()),
    }
    for arquivo, (titulo, ativo, corpo) in fixas.items():
        (pasta_site / arquivo).write_text(documento(titulo, ativo, corpo, gerado_em, menu), encoding="utf-8")

    for nome in nomes:
        info = conteudo.CENARIOS.get(nome, {})
        corpo = pagina_cenario(nome, por_nome.get(nome))
        (pasta_site / f"cenario-{nome}.html").write_text(
            documento(info.get("titulo", nome), f"cen-{nome}", corpo, gerado_em, menu), encoding="utf-8"
        )

    for extra in extras:
        corpo = (
            '<section class="hero"><p class="eyebrow">Pagina do projeto</p>'
            f'<h1>{escapar(extra["titulo"])}</h1></section>'
            f'<section class="secao conteudo-md">{extra["html"]}</section>'
        )
        (pasta_site / extra["arquivo"]).write_text(
            documento(extra["titulo"], extra["chave"], corpo, gerado_em, menu), encoding="utf-8"
        )

    total_modelos = sum(len(c.modelos) for c in cenarios)
    print(f"Site gerado em: {pasta_site}")
    print(f"Cenarios: {len(nomes)} ({len(cenarios)} rodados) | Modelos: {total_modelos} | Paginas extras: {len(extras)}")
    print(f"Abra: {(pasta_site / 'index.html').as_uri()}")


# Ponto de entrada: aceita caminhos opcionais e chama a geracao.
def main() -> None:
    analisador = argparse.ArgumentParser(description="Gera o site do projeto a partir do MLflow local")
    analisador.add_argument("--mlruns", default=str(PASTA_MLRUNS), help="pasta mlruns do projeto")
    analisador.add_argument("--saida", default=str(PASTA_SITE), help="pasta onde escrever o site")
    analisador.add_argument("--paginas", default=str(PASTA_PAGINAS), help="pasta com as paginas .md extras")
    argumentos = analisador.parse_args()
    gerar(Path(argumentos.mlruns), Path(argumentos.saida), Path(argumentos.paginas))


if __name__ == "__main__":
    main()
