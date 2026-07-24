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
NOMES_RESERVADOS = {"index", "objetivo", "dados", "cenarios", "resultados"}

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
# nao e mais uma pagina propria: virou uma secao da inicial, entao o link e uma
# ancora (#dados) que rola ate la.
PAGINAS = [
    ("index.html", "inicio", "Inicio"),
    ("objetivo.html", "objetivo", "Objetivo"),
    ("index.html#dados", "dados", "Dados"),
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
@media (prefers-color-scheme:dark){
  :root{
    --fundo:#0B1411; --superficie:#121C18; --elevado:#17221D;
    --tinta:#EAF1ED; --tinta-suave:#C6D2CC; --muted:#95A89F; --faint:#66786F;
    --borda:#233029; --borda-forte:#31423A; --linha-grade:#1E2A24;
    --acento:#43BFA3; --acento-forte:#6FD6BF; --acento-suave:#10312A;
    --bom:#5FB98A; --atencao:#E0A64B; --critico:#E07A7A;
    --sombra:0 1px 2px rgba(0,0,0,.3), 0 8px 24px -14px rgba(0,0,0,.5);
  }
}
:root[data-theme="dark"]{
  --fundo:#211E20; --superficie:#2A2628; --elevado:#332E30;
  --tinta:#EDE7E1; --tinta-suave:#D3C9C2; --muted:#A79E98; --faint:#7C736E;
  --borda:#3C3739; --borda-forte:#4C4649; --linha-grade:#332E30;
  --acento:#AF9AC9; --acento-forte:#C6B5DC; --acento-suave:#342B41;
  --bom:#8FA875; --atencao:#D6A455; --critico:#D08579;
  --sombra:0 1px 2px rgba(0,0,0,.3), 0 8px 24px -14px rgba(0,0,0,.5);
}
:root[data-theme="light"]{
  --fundo:#EAE4DD; --superficie:#FBF8F4; --elevado:#F2ECE4;
  --tinta:#332F30; --tinta-suave:#4E4849; --muted:#666161; --faint:#948C87;
  --borda:#DDD4C9; --borda-forte:#C7BBAC; --linha-grade:#E4DCD1;
  --acento:#AF9AC9; --acento-forte:#6A5391; --acento-suave:#ECE6F3;
  --bom:#6E8B5A; --atencao:#B07D33; --critico:#B0574B;
  --sombra:0 1px 2px rgba(14,26,22,.04), 0 6px 20px -12px rgba(14,26,22,.14);
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

.barra{position:fixed; top:0; left:0; bottom:0; width:240px; z-index:20; overflow-y:auto;
  background:var(--superficie); border-right:1px solid var(--borda); display:flex; flex-direction:column; padding:1.5rem 1.1rem}
.barra-interna{display:flex; flex-direction:column; gap:1.4rem; flex:1}
.marca{display:flex; align-items:flex-start; gap:.55rem; font-weight:700; color:var(--tinta); text-decoration:none; line-height:1.25}
.marca .ponto{width:10px; height:10px; border-radius:50%; background:var(--acento); box-shadow:0 0 0 3px var(--acento-suave); margin-top:.35rem; flex:none}
.marca span{font-size:.92rem; letter-spacing:-.01em}
.nav-links{display:flex; flex-direction:column; gap:.15rem}
.nav-links a{color:var(--muted); text-decoration:none; font-size:.92rem; font-weight:600; padding:.55rem .8rem; border-radius:10px; border-left:3px solid transparent; transition:color .15s, background .15s}
.nav-links a:hover{color:var(--tinta); background:var(--elevado)}
.nav-links a[aria-current="page"]{color:var(--acento-forte); background:var(--acento-suave); border-left-color:var(--acento)}
.nav-links a.grupo{margin-top:1rem; color:var(--tinta); font-family:var(--fonte-titulo); font-size:1.02rem; font-weight:600}
.nav-links a.grupo[aria-current="page"]{color:var(--acento-forte)}
.nav-links a.sub{padding:.4rem .8rem .4rem 1.5rem; font-size:.85rem; font-weight:500}
.nav-links a.sub[aria-current="page"]{font-weight:700}
.nav-secao{font-size:.66rem; text-transform:uppercase; letter-spacing:.12em; color:var(--faint); font-weight:700; margin:1.1rem 0 .3rem .8rem}
.nav-secao.sub-secao{margin:.75rem 0 .2rem .8rem; color:var(--acento-forte)}
.tema{margin-top:auto; align-self:flex-start; border:1px solid var(--borda); background:var(--superficie); color:var(--muted);
  height:36px; padding:0 .85rem; border-radius:10px; cursor:pointer; font-size:.85rem; display:inline-flex; align-items:center; gap:.5rem; transition:color .15s, border-color .15s}
.tema:hover{color:var(--tinta); border-color:var(--acento)}

.container{margin-left:240px; max-width:1600px; padding:2.6rem clamp(1.6rem,3.5vw,3.5rem) 4.5rem}
.secao{margin:3rem 0}
.secao > .eyebrow{margin-bottom:1rem}

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

.fluxo{display:flex; flex-wrap:wrap; gap:.55rem; align-items:stretch; margin:1.2rem 0}
.fluxo .passo{flex:1 1 175px; background:var(--elevado); border:1px solid var(--borda); border-radius:var(--raio-p); padding:.95rem 1.05rem}
.fluxo .passo b{display:block; color:var(--tinta); font-size:.95rem; margin-bottom:.15rem}
.fluxo .passo small{color:var(--muted)}
.fluxo .seta{display:grid; place-items:center; color:var(--acento); font-size:1.15rem; padding:0 .1rem}
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
.linha-tempo .gap-rot{fill:var(--atencao); font-family:var(--fonte-corpo); font-size:11px; font-weight:700}

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

footer{border-top:1px solid var(--borda); margin-top:3.5rem; margin-left:240px}
.rodape{max-width:1600px; margin:0; padding:1.8rem clamp(1.6rem,3.5vw,3.5rem); color:var(--muted); font-size:.83rem; display:flex; flex-wrap:wrap; gap:.4rem 1.4rem; justify-content:space-between}

@media (max-width:880px){
  .barra{position:static; width:auto; height:auto; flex-direction:row; align-items:center; overflow:visible; border-right:none; border-bottom:1px solid var(--borda); padding:.7rem 1.2rem}
  .barra-interna{flex-direction:row; align-items:center; gap:.7rem 1.1rem; flex-wrap:wrap}
  .marca{margin-right:auto}
  .marca span{font-size:.85rem}
  .marca .ponto{margin-top:.25rem}
  .nav-links{flex-direction:row; flex-wrap:wrap}
  .nav-links a{border-left:none; padding:.35rem .7rem; border-radius:99px}
  .nav-links a[aria-current="page"]{border-left-color:transparent}
  .tema{margin-top:0}
  .container, footer{margin-left:0}
  .rodape{padding-left:1.4rem; padding-right:1.4rem}
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

.tabela-dados{width:100%; border-collapse:collapse; font-size:.93rem}
.tabela-dados thead th{text-align:left; font-size:.7rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-weight:700; padding:.6rem .9rem; border-bottom:1px solid var(--borda-forte); white-space:nowrap}
.tabela-dados td{text-align:left; padding:.9rem; border-bottom:1px solid var(--borda); vertical-align:top}
.tabela-dados tbody tr:last-child td{border-bottom:none}
.tabela-dados tbody tr{transition:background .12s}
.tabela-dados tbody tr:hover{background:var(--elevado)}
.tabela-dados .fonte-nome{font-weight:700; color:var(--tinta); display:flex; align-items:center; gap:.5rem; flex-wrap:wrap}
.tabela-dados .fonte-desc{color:var(--muted); font-size:.85rem; margin-top:.25rem; max-width:46ch}
.tabela-dados .cobertura, .tabela-dados .freq{white-space:nowrap; color:var(--tinta-suave)}
.tabela-dados .origem-cel{color:var(--muted); font-size:.88rem}
.tag-papel{font-size:.72rem; font-weight:700; padding:.16rem .58rem; border-radius:99px; white-space:nowrap}
.tag-papel.vetor{background:var(--acento-suave); color:var(--acento-forte)}
.tag-papel.alvo{background:var(--acento-forte); color:var(--superficie)}
.tag-papel.clima{background:var(--elevado); color:var(--muted); border:1px solid var(--borda)}
.tag-papel.contexto{background:var(--elevado); color:var(--faint); border:1px solid var(--borda)}

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

:focus-visible{outline:2px solid var(--acento); outline-offset:2px; border-radius:4px}
@media (prefers-reduced-motion:reduce){*{transition:none !important; scroll-behavior:auto !important}}
@media print{
  .barra,.tema,footer{display:none}
  body{background:#fff; font-size:11pt}
  .cenario,.kpi,.fonte,.cartao,.cenario-item{break-inside:avoid; box-shadow:none}
}
"""

# Script no <head>: aplica o tema salvo antes de desenhar (evita piscar).
JS_INICIAL = "(function(){try{var t=localStorage.getItem('tema');if(t){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();"

# Script do botao de tema: alterna claro/escuro e lembra a escolha.
JS_TEMA = (
    "function alternarTema(){var r=document.documentElement;var e=r.getAttribute('data-theme');"
    "if(!e){e=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}"
    "var n=e==='dark'?'light':'dark';r.setAttribute('data-theme',n);try{localStorage.setItem('tema',n);}catch(e){}}"
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


# Monta a barra de navegacao do topo, marcando a pagina atual.
def barra_navegacao(ativo: str, menu: dict) -> str:
    def link(arquivo, chave, titulo, classe=""):
        atual = ' aria-current="page"' if chave == ativo else ""
        cls = f' class="{classe}"' if classe else ""
        return f'<a href="{arquivo}"{atual}{cls}>{escapar(titulo)}</a>'

    partes = [link(*item) for item in menu["fixas"]]
    partes.append(link("cenarios.html", "cenarios", "Cenarios", "grupo"))
    for grupo_nome, itens in menu["grupos_cenarios"]:
        partes.append(f'<div class="nav-secao sub-secao">{escapar(grupo_nome)}</div>')
        partes += [link(arquivo, chave, titulo, "sub") for arquivo, chave, titulo in itens]
    if menu["extras"]:
        partes.append('<div class="nav-secao">Paginas</div>')
        partes += [link(*item) for item in menu["extras"]]
    return (
        '<aside class="barra"><div class="barra-interna">'
        f'<a class="marca" href="index.html"><span class="ponto"></span>'
        f'<span>{escapar(conteudo.PROJETO["titulo"])}</span></a>'
        f'<nav class="nav-links">{"".join(partes)}</nav>'
        '<button class="tema" onclick="alternarTema()" aria-label="Alternar tema claro/escuro" title="Tema claro/escuro">◑ Tema</button>'
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
        f"<script>{JS_INICIAL}</script>\n"
        "</head>\n<body>\n"
        f"{barra_navegacao(ativo, menu)}\n"
        f'<main class="container">\n{corpo}\n</main>\n'
        f"{rodape(gerado_em)}\n"
        f"<script>{JS_TEMA}</script>\n"
        "</body>\n</html>\n"
    )


# Desenha o diagrama do caminho dos dados (fontes -> montagem -> ... -> painel).
def diagrama_fluxo() -> str:
    partes = []
    for indice, (titulo, detalhe) in enumerate(conteudo.FLUXO):
        if indice:
            partes.append('<div class="seta">→</div>')
        partes.append(f'<div class="passo"><b>{escapar(titulo)}</b><small>{escapar(detalhe)}</small></div>')
    return f'<div class="fluxo">{"".join(partes)}</div>'


# Embute uma figura (imagem da pasta imagens/) com uma legenda embaixo.
def figura(arquivo: str, titulo: str, legenda: str) -> str:
    return (
        '<figure class="figura">'
        f'<img src="imagens/{arquivo}" alt="{escapar(titulo)}" loading="lazy">'
        f"<figcaption>{escapar(legenda)}</figcaption></figure>"
    )


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


# Desenha a linha do tempo das capturas de mosquito (dois blocos + o vao sem dados).
def linha_do_tempo_dados() -> str:
    """

    Mostra, numa regua de 2019 a 2026, os dois pedacos de dados de mosquito (o
    historico da Marilia, 2019-2023, e a raspagem, de 2025 em diante) e o vao de
    ~2 anos entre eles, quando nao houve captura. E o mesmo desenho que aparece na
    apresentacao, ligando o site ao material do orientador.

    """
    largura, altura = 760, 104
    esq, dir_ = 10, 10
    ano_inicio, ano_fim = 2019, 2026.6
    area = largura - esq - dir_

    def px(ano):
        return esq + (ano - ano_inicio) / (ano_fim - ano_inicio) * area

    y_barra, alt_barra = 50, 26
    blocos = [
        (2019, 2023.3, "Marilia 2019-2023", "var(--acento)", "bloco"),
        (2023.3, 2025.6, "sem captura (~2 anos)", "var(--acento-suave)", "gap"),
        (2025.6, 2026.6, "raspagem", "var(--acento)", "bloco"),
    ]
    partes = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="Linha do tempo das capturas de mosquito">']
    partes.append(f'<text class="ano" x="{esq}" y="18">Capturas de mosquito ao longo do tempo</text>')
    for inicio, fim, rotulo, cor, tipo in blocos:
        xa, xb = px(inicio), px(fim)
        meio = (xa + xb) / 2
        if tipo == "gap":
            partes.append(f'<rect x="{xa:.0f}" y="{y_barra}" width="{xb - xa:.0f}" height="{alt_barra}" rx="6" fill="{cor}" stroke="var(--atencao)" stroke-dasharray="4 4"/>')
            partes.append(f'<text class="gap-rot" x="{meio:.0f}" y="{y_barra - 8}" text-anchor="middle">{rotulo}</text>')
        else:
            partes.append(f'<rect x="{xa:.0f}" y="{y_barra}" width="{xb - xa:.0f}" height="{alt_barra}" rx="6" fill="{cor}"/>')
            partes.append(f'<text class="bloco-rot" x="{meio:.0f}" y="{y_barra + alt_barra / 2 + 4:.0f}" text-anchor="middle">{rotulo}</text>')
    for ano in range(2019, 2027):
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

    cabeca = (
        '<section class="hero"><p class="eyebrow">Cenario</p>'
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
        ("objetivo.html", "Objetivo", "Por que este trabalho existe e como ele testa as previsoes.", "Abrir →"),
        ("#dados", "Dados", "As fontes usadas: mosquito, clima, casos e El Nino.", "Ver abaixo ↓"),
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
        # A antiga pagina de Dados, agora embutida aqui (a ancora #dados leva pra ca).
        '<section class="secao" id="dados"><p class="eyebrow">Dados</p>'
        "<h2>As fontes que alimentam as previsoes</h2>"
        '<p class="lead" style="margin-top:.35rem">Tudo e medido semana a semana e depois juntado numa tabela unica.</p></section>'
        f"{secoes_dados()}"
    )


# Monta a pagina do objetivo (a pergunta central e como ela e testada).
def pagina_objetivo() -> str:
    objetivo = conteudo.OBJETIVO
    paragrafos = "".join(f"<p>{escapar(p)}</p>" for p in objetivo["paragrafos"])
    metodo = "".join(
        f'<li><b>{escapar(titulo)}</b><p>{escapar(texto)}</p></li>'
        for titulo, texto in objetivo["como_testa"]
    )
    return (
        '<section class="hero"><p class="eyebrow">Objetivo</p>'
        f"<h1>{escapar(objetivo['frase'])}</h1></section>"
        f'<section class="secao">{paragrafos}</section>'
        '<section class="secao"><div class="callout">'
        '<p class="eyebrow">A pergunta central</p>'
        f"<p><strong>{escapar(objetivo['pergunta_central'])}</strong></p>"
        f"<p style=\"margin-top:.6rem;color:var(--tinta-suave)\">{escapar(objetivo['pergunta_explica'])}</p>"
        "</div></section>"
        '<section class="secao"><h2>Como as previsoes sao testadas</h2>'
        f'<ul class="lista-metodo">{metodo}</ul>'
        f'{figura("walkforward.png", "Validacao walk-forward", "Validacao walk-forward: em cada corte o modelo treina so com o passado e preve ate 12 semanas a frente, e depois compara com o real. Ele nunca ve o futuro que tenta prever.")}</section>'
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
        f'<section class="secao"><p class="eyebrow">O caminho dos dados</p>{diagrama_fluxo()}</section>'
        f'<section class="secao"><p class="eyebrow">As fontes</p>{tabela}</section>'
        f'<section class="secao"><p class="eyebrow">O que compoe o clima</p>{tabela_colunas_clima()}</section>'
        f'<section class="secao"><p class="eyebrow">A serie do mosquito</p>{figura("vetor_por_semana.png", "Aedes aegypti capturados por semana", "Aedes aegypti capturados por semana em POA. Dois blocos: Marilia (2019-2023) e a raspagem propria (2025-2026), com o vao de ~2 anos sem captura no meio.")}</section>'
        f'<section class="secao"><p class="eyebrow">A limitacao dos dados</p>{figura("vetor_vs_casos.png", "Mosquito capturado x casos de dengue", "Mosquito capturado x casos de dengue confirmados. Os dois maiores surtos (2024 e 2025) caem justo no vao sem dado de mosquito — a limitacao central da pesquisa.")}</section>'
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
    for grupo_nome, itens in agrupar_cenarios(ordem_dos_cenarios(cenarios)):
        cartoes = []
        for nome in itens:
            info = conteudo.CENARIOS.get(nome, {})
            titulo = info.get("titulo", nome)
            pergunta = info.get("pergunta", "")
            cenario = por_nome.get(nome)
            if cenario and cenario.modelos:
                quantidade = len(cenario.modelos)
                marca = f'{quantidade} modelo{"s" if quantidade > 1 else ""} &rarr;'
            else:
                marca = "nao rodado &rarr;"
            cartoes.append(
                f'<a class="cartao" href="cenario-{escapar(nome)}.html"><h3>{escapar(titulo)}</h3>'
                f'<p>{escapar(pergunta)}</p><span class="seta">{marca}</span></a>'
            )
        corpo += (
            f'<section class="secao"><p class="eyebrow">{escapar(grupo_nome)}</p>'
            f'<div class="cartoes">{"".join(cartoes)}</div></section>'
        )
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
        "objetivo.html": ("Objetivo", "objetivo", pagina_objetivo()),
        "cenarios.html": ("Cenários", "cenarios", pagina_cenarios(cenarios)),
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
