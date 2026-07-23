"""

Monta o site do projeto (paginas HTML) a partir do que o MLflow gravou e dos
textos em conteudo.py. E o COMANDO principal desta pasta: rode

    python gerar.py

e ele reescreve as paginas dentro de 'site/'. Abra 'site/index.html' no
navegador. Rodou um modelo novo (python main.py --experimento ...)? Rode este
gerador de novo que o painel se atualiza.

Tudo aqui e feito na mao com Python puro: le a pasta mlruns, formata os numeros,
desenha os graficos em SVG e escreve o HTML. Sem servidor, sem dependencia
externa — o site e so um punhado de arquivos que voce abre ou manda por email.

"""

import argparse
import datetime
import html
import re
from pathlib import Path

import conteudo
import leitor_mlflow
import markdown_simples

# Onde as coisas ficam: esta pasta, a mlruns do projeto ao lado, e a saida.
PASTA_AQUI = Path(__file__).resolve().parent
PASTA_MLRUNS = PASTA_AQUI.parent / "modelagem_aedes" / "mlruns"
PASTA_SITE = PASTA_AQUI / "site"
PASTA_PAGINAS = PASTA_AQUI / "paginas"

# Enderecos das paginas fixas (nao dar esses nomes a paginas novas em paginas/).
NOMES_RESERVADOS = {"index", "objetivo", "dados", "resultados"}

# Cores das linhas dos graficos (uma por serie). Legiveis nos dois temas.
CORES_SERIES = ["#0E7C66", "#C07A12", "#1E6FB0", "#B23A3A", "#6C4CB3", "#2E8B57"]

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

# As paginas do site: (arquivo, chave de navegacao, titulo do menu).
PAGINAS = [
    ("index.html", "inicio", "Inicio"),
    ("objetivo.html", "objetivo", "Objetivo"),
    ("dados.html", "dados", "Dados"),
    ("cenarios.html", "cenarios", "Cenários"),
    ("resultados.html", "resultados", "Resultados"),
]

CSS = """
*{box-sizing:border-box}
:root{
  --fundo:#F4F6F5; --superficie:#ffffff; --elevado:#FBFCFC;
  --tinta:#111C18; --tinta-suave:#39473F; --muted:#586862; --faint:#8B9A94;
  --borda:#DEE5E2; --linha-grade:#E7ECEA;
  --acento:#0E7C66; --acento-forte:#0B5E4E; --acento-suave:#E3F0EC;
  --bom:#2E8B57; --atencao:#B7770F; --critico:#B23A3A;
  --raio:14px; --raio-p:9px; --largura:1060px;
  --sombra:0 1px 2px rgba(17,28,24,.05);
  --fonte-titulo:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --fonte-corpo:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --fonte-dados:"SF Mono","JetBrains Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme:dark){
  :root{
    --fundo:#0D1512; --superficie:#141E1A; --elevado:#18241F;
    --tinta:#E9F0EC; --tinta-suave:#C3D0CA; --muted:#9DB0A8; --faint:#6E8078;
    --borda:#26332D; --linha-grade:#233029;
    --acento:#43BBA0; --acento-forte:#6FD3BC; --acento-suave:#12332B;
    --bom:#5FB98A; --atencao:#E0A64B; --critico:#E07A7A;
    --sombra:0 1px 2px rgba(0,0,0,.28);
  }
}
:root[data-theme="dark"]{
  --fundo:#0D1512; --superficie:#141E1A; --elevado:#18241F;
  --tinta:#E9F0EC; --tinta-suave:#C3D0CA; --muted:#9DB0A8; --faint:#6E8078;
  --borda:#26332D; --linha-grade:#233029;
  --acento:#43BBA0; --acento-forte:#6FD3BC; --acento-suave:#12332B;
  --bom:#5FB98A; --atencao:#E0A64B; --critico:#E07A7A;
  --sombra:0 1px 2px rgba(0,0,0,.28);
}
:root[data-theme="light"]{
  --fundo:#F4F6F5; --superficie:#ffffff; --elevado:#FBFCFC;
  --tinta:#111C18; --tinta-suave:#39473F; --muted:#586862; --faint:#8B9A94;
  --borda:#DEE5E2; --linha-grade:#E7ECEA;
  --acento:#0E7C66; --acento-forte:#0B5E4E; --acento-suave:#E3F0EC;
  --bom:#2E8B57; --atencao:#B7770F; --critico:#B23A3A;
  --sombra:0 1px 2px rgba(17,28,24,.05);
}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--fundo); color:var(--tinta);
  font-family:var(--fonte-corpo); font-size:16.5px; line-height:1.6;
  -webkit-font-smoothing:antialiased;
}
a{color:var(--acento-forte); text-underline-offset:2px}
h1,h2,h3{font-family:var(--fonte-titulo); font-weight:600; line-height:1.15; text-wrap:balance; color:var(--tinta)}
h1{font-size:2.35rem; margin:.1em 0 .3em; letter-spacing:-.01em}
h2{font-size:1.5rem; margin:0 0 .5rem}
h3{font-size:1.12rem; margin:0 0 .35rem}
p{margin:0 0 1rem; max-width:66ch}
.eyebrow{font-size:.72rem; text-transform:uppercase; letter-spacing:.13em; color:var(--acento-forte); font-weight:700; margin:0 0 .5rem}

.barra{position:sticky; top:0; z-index:20; background:color-mix(in srgb, var(--superficie) 88%, transparent);
  backdrop-filter:saturate(1.4) blur(8px); border-bottom:1px solid var(--borda)}
.barra-interna{max-width:var(--largura); margin:0 auto; padding:.65rem 1.4rem; display:flex; align-items:center; gap:1rem}
.marca{display:flex; align-items:center; gap:.6rem; font-weight:700; color:var(--tinta); text-decoration:none; margin-right:auto}
.marca .ponto{width:11px; height:11px; border-radius:50%; background:var(--acento); box-shadow:0 0 0 3px var(--acento-suave)}
.marca span{font-size:.92rem; letter-spacing:-.01em}
.nav-links{display:flex; gap:.2rem; flex-wrap:wrap}
.nav-links a{color:var(--muted); text-decoration:none; font-size:.9rem; font-weight:600; padding:.35rem .7rem; border-radius:99px}
.nav-links a:hover{color:var(--tinta); background:var(--acento-suave)}
.nav-links a[aria-current="page"]{color:var(--acento-forte); background:var(--acento-suave)}
.tema{border:1px solid var(--borda); background:var(--superficie); color:var(--muted); width:34px; height:34px;
  border-radius:99px; cursor:pointer; font-size:1rem; line-height:1; display:grid; place-items:center}
.tema:hover{color:var(--tinta); border-color:var(--acento)}

.container{max-width:var(--largura); margin:0 auto; padding:2.4rem 1.4rem 4rem}
.secao{margin:2.6rem 0}
.hero{padding:1rem 0 .4rem; position:relative}
.hero .sub{font-size:1.12rem; color:var(--muted); max-width:60ch; margin-top:-.2rem}
.onda{width:100%; height:74px; margin:1.3rem 0 .2rem; display:block; opacity:.9}

.kpis{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.9rem; margin:1.4rem 0}
.kpi{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1rem 1.1rem; box-shadow:var(--sombra)}
.kpi .valor{font-family:var(--fonte-dados); font-size:1.7rem; font-weight:600; color:var(--tinta); font-variant-numeric:tabular-nums; letter-spacing:-.02em}
.kpi .rotulo{font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); margin-top:.15rem}

.cartoes{display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:1rem}
.cartao{display:block; background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio);
  padding:1.2rem 1.25rem; text-decoration:none; color:inherit; box-shadow:var(--sombra); transition:border-color .15s, transform .15s}
a.cartao:hover{border-color:var(--acento); transform:translateY(-2px)}
.cartao h3{color:var(--tinta)}
.cartao p{color:var(--muted); font-size:.94rem; margin:0}
.cartao .seta{color:var(--acento-forte); font-weight:700; margin-top:.6rem; display:inline-block; font-size:.9rem}

.fluxo{display:flex; flex-wrap:wrap; gap:.5rem; align-items:stretch; margin:1.2rem 0}
.fluxo .passo{flex:1 1 180px; background:var(--elevado); border:1px solid var(--borda); border-radius:var(--raio-p); padding:.85rem 1rem}
.fluxo .passo b{display:block; color:var(--tinta); font-size:.95rem}
.fluxo .passo small{color:var(--muted)}
.fluxo .seta{display:grid; place-items:center; color:var(--faint); font-size:1.2rem; padding:0 .1rem}
@media (max-width:640px){ .fluxo .seta{transform:rotate(90deg)} }

.grade-fontes{display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:1rem}
.fonte{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1.15rem 1.2rem; box-shadow:var(--sombra)}
.fonte h3{display:flex; align-items:center; gap:.5rem; color:var(--tinta)}
.fonte .papel{color:var(--tinta-suave); font-size:.95rem; margin:.4rem 0 .6rem}
.fonte .origem{color:var(--muted); font-size:.85rem; margin:0}
.chips{display:flex; flex-wrap:wrap; gap:.35rem; margin-bottom:.2rem}
.chip{font-size:.72rem; font-weight:600; color:var(--muted); background:var(--elevado); border:1px solid var(--borda); border-radius:99px; padding:.16rem .55rem}
.badge{font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; padding:.16rem .5rem; border-radius:99px}
.badge.vital{color:#fff; background:var(--critico)}

.callout{background:var(--acento-suave); border:1px solid color-mix(in srgb, var(--acento) 30%, var(--borda)); border-left:4px solid var(--acento);
  border-radius:var(--raio-p); padding:1.1rem 1.25rem; margin:1.3rem 0}
.callout .eyebrow{color:var(--acento-forte)}
.callout p{margin:0; color:var(--tinta)}

.lista-metodo{display:grid; gap:.8rem; margin:1.2rem 0; padding:0; list-style:none}
.lista-metodo li{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio-p); padding:1rem 1.15rem}
.lista-metodo b{color:var(--tinta)}
.lista-metodo p{margin:.3rem 0 0; color:var(--muted); font-size:.94rem}

.cenario{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio); padding:1.4rem 1.5rem; margin:1.4rem 0; box-shadow:var(--sombra)}
.cenario-topo{display:flex; flex-wrap:wrap; align-items:baseline; gap:.6rem; margin-bottom:.2rem}
.cenario-topo h2{margin:0}
.cenario .pergunta{color:var(--muted); margin:.1rem 0 .2rem}
.cenario .tecnico{font-family:var(--fonte-dados); font-size:.76rem; color:var(--faint)}
.cenario .descricao{color:var(--tinta-suave); font-size:.95rem; max-width:70ch}

.tabela-rolavel{overflow-x:auto; margin:1rem 0; border:1px solid var(--borda); border-radius:var(--raio-p)}
table.tabela{width:100%; border-collapse:collapse; font-size:.9rem}
table.tabela th, table.tabela td{padding:.6rem .8rem; text-align:right; white-space:nowrap; border-bottom:1px solid var(--borda)}
table.tabela th:first-child, table.tabela td:first-child{text-align:left}
table.tabela thead th{background:var(--elevado); color:var(--muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.05em; font-weight:700; position:sticky; top:0}
table.tabela tbody tr:last-child td{border-bottom:none}
table.tabela td.num{font-family:var(--fonte-dados); font-variant-numeric:tabular-nums}
table.tabela td.melhor{color:var(--acento-forte); font-weight:700; background:var(--acento-suave)}
table.tabela td.melhor::after{content:" ✓"; font-size:.8em}
.modelo-nome{display:flex; align-items:center; gap:.5rem}
.pastilha{font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em; padding:.12rem .5rem; border-radius:99px; background:var(--acento-suave); color:var(--acento-forte)}
.status{font-size:.78rem; color:var(--muted)}
.status.concluido::before{content:"● "; color:var(--bom)}
.status.falhou::before{content:"● "; color:var(--critico)}

.grafico{margin:1.2rem 0 .4rem}
.grafico .titulo-graf{font-size:.8rem; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); font-weight:700; margin-bottom:.5rem}
.grafico svg{width:100%; height:auto; max-width:720px; display:block}
.grafico .grade{stroke:var(--linha-grade); stroke-width:1}
.grafico .eixo{fill:var(--muted); font-family:var(--fonte-dados); font-size:11px}
.grafico .eixo-titulo{fill:var(--faint); font-family:var(--fonte-corpo); font-size:11px}
.legenda{display:flex; flex-wrap:wrap; gap:.9rem; margin-top:.5rem; font-size:.82rem; color:var(--tinta-suave)}
.legenda span{display:inline-flex; align-items:center; gap:.35rem}
.legenda i{width:14px; height:3px; border-radius:2px; display:inline-block}

details.detalhes{margin-top:.7rem; border-top:1px dashed var(--borda); padding-top:.6rem}
details.detalhes summary{cursor:pointer; color:var(--acento-forte); font-weight:600; font-size:.9rem; list-style:none}
details.detalhes summary::-webkit-details-marker{display:none}
details.detalhes summary::before{content:"▸ "; }
details.detalhes[open] summary::before{content:"▾ "; }
.grupo-param{margin:.9rem 0}
.grupo-param h4{margin:0 0 .3rem; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); font-family:var(--fonte-corpo)}
table.params{width:100%; border-collapse:collapse; font-size:.85rem}
table.params td{padding:.28rem .6rem; border-bottom:1px solid var(--borda); vertical-align:top}
table.params td:first-child{color:var(--muted); width:45%}
table.params td:last-child{font-family:var(--fonte-dados); color:var(--tinta); text-align:right; font-variant-numeric:tabular-nums; word-break:break-word}

.vazio{text-align:center; color:var(--muted); background:var(--superficie); border:1px dashed var(--borda); border-radius:var(--raio); padding:3rem 1.5rem}
.vazio code{background:var(--elevado); padding:.15rem .45rem; border-radius:6px; font-family:var(--fonte-dados); font-size:.85em}

footer{border-top:1px solid var(--borda); margin-top:3rem}
.rodape{max-width:var(--largura); margin:0 auto; padding:1.6rem 1.4rem; color:var(--muted); font-size:.84rem; display:flex; flex-wrap:wrap; gap:.4rem 1.4rem; justify-content:space-between}

.acordeao{display:flex; flex-direction:column; gap:.6rem; margin-top:1.3rem}
.cenario-item{background:var(--superficie); border:1px solid var(--borda); border-radius:var(--raio)}
.cenario-item>summary{list-style:none; cursor:pointer; padding:1rem 1.2rem; display:flex; align-items:center; gap:.7rem}
.cenario-item>summary::-webkit-details-marker{display:none}
.cenario-item>summary::before{content:"\\25B8"; color:var(--acento); font-size:.85rem; transition:transform .15s}
.cenario-item[open]>summary::before{transform:rotate(90deg)}
.cenario-item[open]>summary{border-bottom:1px solid var(--borda)}
.cenario-item .titulo-cen{font-family:var(--fonte-titulo); font-size:1.08rem; font-weight:600; color:var(--tinta); margin-right:auto}
.cenario-item .corpo{padding:1.1rem 1.2rem}
.cenario-item .pergunta-cen{color:var(--muted); font-size:.9rem; margin:0 0 1rem}
.tag{font-size:.72rem; font-weight:700; padding:.18rem .6rem; border-radius:99px; white-space:nowrap}
.tag.rodado{background:var(--acento-suave); color:var(--acento-forte)}
.tag.pendente{background:var(--elevado); color:var(--muted); border:1px solid var(--borda)}
.modelos-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:.9rem}
.modelo-card{border:1px solid var(--borda); border-radius:var(--raio-p); padding:.9rem 1rem; background:var(--elevado)}
.modelo-cab{margin-bottom:.7rem}
.stats{display:flex; flex-wrap:wrap; gap:1.1rem; margin-bottom:.8rem}
.stat .v{font-family:var(--fonte-dados); font-size:1.2rem; font-weight:600; color:var(--tinta); font-variant-numeric:tabular-nums; letter-spacing:-.01em}
.stat .r{font-size:.66rem; text-transform:uppercase; letter-spacing:.05em; color:var(--muted)}
.nao-rodado{color:var(--muted); font-size:.92rem; margin:0}
.nao-rodado code{background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.1em .4em; font-family:var(--fonte-dados); font-size:.85em}

.conteudo-md{max-width:70ch}
.conteudo-md h2{margin:1.8rem 0 .6rem}
.conteudo-md h3{margin:1.3rem 0 .4rem}
.conteudo-md p{color:var(--tinta-suave)}
.conteudo-md ul,.conteudo-md ol{color:var(--tinta-suave); padding-left:1.3rem; margin:0 0 1rem}
.conteudo-md li{margin:.3rem 0}
.conteudo-md blockquote{margin:1.1rem 0; padding:.7rem 1.1rem; border-left:4px solid var(--acento);
  background:var(--acento-suave); border-radius:0 var(--raio-p) var(--raio-p) 0; color:var(--tinta)}
.conteudo-md code{font-family:var(--fonte-dados); font-size:.88em; background:var(--elevado); border:1px solid var(--borda); border-radius:6px; padding:.08em .4em}
.conteudo-md img{max-width:100%; height:auto; border-radius:var(--raio-p); border:1px solid var(--borda); margin:.6rem 0}
.conteudo-md hr{border:none; border-top:1px solid var(--borda); margin:1.9rem 0}
.conteudo-md a{color:var(--acento-forte)}

:focus-visible{outline:2px solid var(--acento); outline-offset:2px; border-radius:4px}
@media (prefers-reduced-motion:reduce){*{transition:none !important; scroll-behavior:auto !important}}
@media print{
  .barra,.tema,footer{display:none}
  body{background:#fff; font-size:11pt}
  .cenario,.kpi,.fonte,.cartao{break-inside:avoid; box-shadow:none}
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
def barra_navegacao(ativo: str, menu: list) -> str:
    links = []
    for arquivo, chave, titulo in menu:
        atual = ' aria-current="page"' if chave == ativo else ""
        links.append(f'<a href="{arquivo}"{atual}>{escapar(titulo)}</a>')
    return (
        '<div class="barra"><div class="barra-interna">'
        f'<a class="marca" href="index.html"><span class="ponto"></span>'
        f'<span>{escapar(conteudo.PROJETO["titulo"])}</span></a>'
        f'<nav class="nav-links">{"".join(links)}</nav>'
        '<button class="tema" onclick="alternarTema()" aria-label="Alternar tema claro/escuro" title="Tema claro/escuro">◑</button>'
        "</div></div>"
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


# Monta o cartao completo de um cenario (titulo, tabela, grafico e detalhes).
def cartao_do_cenario(cenario) -> str:
    info = conteudo.CENARIOS.get(cenario.nome, {})
    titulo = info.get("titulo", cenario.nome)
    pergunta = info.get("pergunta", "")
    descricao = info.get("descricao", "")

    metricas = metricas_do_cenario(cenario)
    partes = [
        '<section class="cenario">',
        f'<div class="cenario-topo"><h2>{escapar(titulo)}</h2>'
        f'<span class="tecnico">{escapar(cenario.nome)}</span></div>',
    ]
    if pergunta:
        partes.append(f'<p class="pergunta">{escapar(pergunta)}</p>')
    if descricao:
        partes.append(f'<p class="descricao">{escapar(descricao)}</p>')
    partes.append(tabela_comparativa(cenario, metricas))
    partes.append(dados_do_grafico(cenario))
    for modelo in cenario.modelos:
        partes.append(detalhes_do_modelo(modelo))
    partes.append("</section>")
    return "".join(partes)


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


# Uma linha suave de "previsao" so pra dar identidade ao topo da pagina inicial.
def onda_decorativa() -> str:
    return (
        '<svg class="onda" viewBox="0 0 720 74" preserveAspectRatio="none" aria-hidden="true">'
        '<path d="M0,55 C90,52 120,20 200,24 C280,28 300,60 380,56 C460,52 480,14 560,18 C640,22 670,44 720,40" '
        'fill="none" stroke="var(--acento)" stroke-width="2.4" opacity=".5"/>'
        '<path d="M0,64 C90,62 130,44 210,46 C300,48 320,68 400,66 C480,64 500,40 580,42 C650,44 680,58 720,55" '
        'fill="none" stroke="var(--atencao)" stroke-width="2" opacity=".35" stroke-dasharray="4 5"/>'
        "</svg>"
    )


# Monta a pagina inicial (visao geral + indicadores + atalhos).
def pagina_inicio(cenarios) -> str:
    projeto = conteudo.PROJETO
    objetivo = conteudo.OBJETIVO
    cartoes = [
        ("objetivo.html", "Objetivo", "Por que este trabalho existe e como ele testa as previsoes."),
        ("dados.html", "Dados", "As fontes usadas: mosquito, clima, casos e El Nino."),
        ("resultados.html", "Resultados", "O painel dos experimentos: modelos, ajustes e notas."),
    ]
    atalhos = "".join(
        f'<a class="cartao" href="{arq}"><h3>{escapar(t)}</h3><p>{escapar(d)}</p><span class="seta">Abrir →</span></a>'
        for arq, t, d in cartoes
    )
    return (
        '<section class="hero">'
        f'<p class="eyebrow">{escapar(projeto["instituicao"])} · {escapar(projeto["local"])}</p>'
        f"<h1>{escapar(objetivo['frase'])}</h1>"
        f'<p class="sub">{escapar(projeto["subtitulo"])}</p>'
        f"{onda_decorativa()}"
        "</section>"
        f"{indicadores_gerais(cenarios)}"
        f'<section class="secao"><div class="cartoes">{atalhos}</div></section>'
        f'<section class="secao"><p class="eyebrow">O caminho dos dados</p>{diagrama_fluxo()}</section>'
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
        f'<ul class="lista-metodo">{metodo}</ul></section>'
    )


# Monta a pagina de dados (um cartao por fonte + o que sai da juncao).
def pagina_dados() -> str:
    cartoes = []
    for fonte in conteudo.FONTES_DADOS:
        badge = '<span class="badge vital">insubstituivel</span>' if fonte.get("vital") else ""
        cartoes.append(
            '<div class="fonte">'
            f'<div class="chips"><span class="chip">{escapar(fonte["periodo"])}</span>'
            f'<span class="chip">{escapar(fonte["cadencia"])}</span></div>'
            f'<h3>{escapar(fonte["nome"])} {badge}</h3>'
            f'<p class="papel">{escapar(fonte["papel"])}</p>'
            f'<p class="origem">Fonte: {escapar(fonte["origem"])}</p>'
            "</div>"
        )
    final = conteudo.TABELA_FINAL
    return (
        '<section class="hero"><p class="eyebrow">Dados</p>'
        "<h1>As fontes que alimentam as previsoes</h1>"
        '<p class="sub">Tudo e medido semana a semana e depois juntado numa tabela unica.</p></section>'
        f'<section class="secao"><div class="grade-fontes">{"".join(cartoes)}</div></section>'
        '<section class="secao"><div class="callout">'
        f'<p class="eyebrow">O que sai da juncao — {escapar(final["nome"])}</p>'
        f'<p>{escapar(final["papel"])}</p></div></section>'
        f'<section class="secao"><p class="eyebrow">O caminho dos dados</p>{diagrama_fluxo()}</section>'
    )


# Monta a pagina de resultados (o painel: um cartao por cenario).
def pagina_resultados(cenarios) -> str:
    cabeca = (
        '<section class="hero"><p class="eyebrow">Resultados</p>'
        "<h1>Painel dos experimentos</h1>"
        '<p class="sub">Cada cenario e uma pergunta; dentro dele, cada modelo treinado com suas notas e ajustes.</p></section>'
    )
    if not cenarios:
        return (
            cabeca
            + '<div class="vazio"><p>Ainda nao ha execucoes registradas.</p>'
            "<p>Rode um experimento com <code>python main.py --experimento cidade_regressao</code> "
            "e depois <code>python gerar.py</code> aqui pra atualizar o painel.</p></div>"
        )
    corpo = indicadores_gerais(cenarios)
    corpo += (
        '<div class="callout"><p class="eyebrow">Como ler</p>'
        "<p><strong>Erro medio (MAE)</strong>: quantos casos, em media, a previsao erra — quanto menor, melhor. "
        "<strong>R²</strong>: o quanto o modelo explica os altos e baixos — quanto mais perto de 1, melhor. "
        "O melhor de cada coluna aparece destacado (✓).</p></div>"
    )
    corpo += "".join(cartao_do_cenario(c) for c in cenarios)
    return cabeca + corpo


# As metricas de um modelo, na ordem preferida e sem as escondidas.
def _metricas_visiveis(modelo) -> list:
    presentes = [m for m in modelo.metricas if m not in conteudo.METRICAS_ESCONDIDAS]
    ordenadas = [m for m in PREFERENCIA_METRICAS if m in presentes]
    ordenadas += [m for m in presentes if m not in ordenadas]
    return ordenadas


# Monta o cartao enxuto de um modelo: nome, resultados em destaque e hiperparametros.
def cartao_modelo_simples(modelo) -> str:
    stats = "".join(
        f'<div class="stat"><div class="v">{formatar_numero(modelo.metricas[m])}</div>'
        f'<div class="r">{escapar(rotulo_metrica(m))}</div></div>'
        for m in _metricas_visiveis(modelo)
    )
    hiper = [(chave.replace("modelo.", ""), valor) for chave, valor in modelo.parametros.items() if chave.startswith("modelo.")]
    linhas = "".join(f"<tr><td>{escapar(nome)}</td><td>{escapar(valor)}</td></tr>" for nome, valor in hiper)
    tabela = f'<table class="params">{linhas}</table>' if hiper else ""
    return (
        '<div class="modelo-card">'
        f'<div class="modelo-cab"><span class="pastilha">{escapar(modelo.nome)}</span></div>'
        f'<div class="stats">{stats}</div>{tabela}</div>'
    )


# Monta um item do acordeao: um cenario que abre e mostra seus modelos.
def item_do_cenario(nome: str, cenario) -> str:
    """

    Cada cenario vira uma faixa que se abre ao clicar. Se ele ja foi rodado,
    mostra um cartao por modelo (com resultados e hiperparametros). Se ainda nao
    foi rodado, mostra uma nota curta com o comando pra rodar.

    """
    info = conteudo.CENARIOS.get(nome, {})
    titulo = info.get("titulo", nome)
    pergunta = f'<p class="pergunta-cen">{escapar(info["pergunta"])}</p>' if info.get("pergunta") else ""

    if cenario and cenario.modelos:
        quantidade = len(cenario.modelos)
        tag = f'<span class="tag rodado">{quantidade} modelo{"s" if quantidade > 1 else ""}</span>'
        cartoes = "".join(cartao_modelo_simples(modelo) for modelo in cenario.modelos)
        corpo = f'{pergunta}<div class="modelos-grid">{cartoes}</div>'
    else:
        tag = '<span class="tag pendente">nao rodado</span>'
        corpo = (
            f'{pergunta}<p class="nao-rodado">Ainda nao foi rodado. Rode '
            f"<code>python3 main.py --experimento {escapar(nome)}</code> e depois "
            "<code>python3 gerar.py</code> pra ver os modelos e resultados aqui.</p>"
        )

    return (
        '<details class="cenario-item">'
        f'<summary><span class="titulo-cen">{escapar(titulo)}</span>{tag}</summary>'
        f'<div class="corpo">{corpo}</div></details>'
    )


# Monta a pagina de cenarios (o acordeao com todos os cenarios do projeto).
def pagina_cenarios(cenarios) -> str:
    por_nome = {c.nome: c for c in cenarios}
    nomes = list(conteudo.CENARIOS.keys())
    for cenario in cenarios:
        if cenario.nome not in nomes:
            nomes.append(cenario.nome)
    itens = "".join(item_do_cenario(nome, por_nome.get(nome)) for nome in nomes)
    return (
        '<section class="hero"><p class="eyebrow">Cenarios</p>'
        "<h1>Os cenarios do projeto</h1>"
        '<p class="sub">Clique num cenario pra abrir os modelos usados, os hiperparametros e os resultados.</p></section>'
        f'<section class="secao"><div class="acordeao">{itens}</div></section>'
    )


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

    menu = list(PAGINAS) + [(p["arquivo"], p["chave"], p["titulo"]) for p in extras]

    fixas = {
        "index.html": ("Inicio", "inicio", pagina_inicio(cenarios)),
        "objetivo.html": ("Objetivo", "objetivo", pagina_objetivo()),
        "dados.html": ("Dados", "dados", pagina_dados()),
        "cenarios.html": ("Cenários", "cenarios", pagina_cenarios(cenarios)),
        "resultados.html": ("Resultados", "resultados", pagina_resultados(cenarios)),
    }
    for arquivo, (titulo, ativo, corpo) in fixas.items():
        (pasta_site / arquivo).write_text(documento(titulo, ativo, corpo, gerado_em, menu), encoding="utf-8")

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
    print(f"Cenarios: {len(cenarios)} | Modelos: {total_modelos} | Paginas extras: {len(extras)}")
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
