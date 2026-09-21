titulo: Cenario Principal 2
ordem: 26

<div class="veredito critico"><span class="vRot">Esta pagina substitui a anterior</span><p>Em <b>13/09/2026</b> encontramos um <b>vazamento temporal</b> no codigo de treino. Ele inflava os resultados de horizonte longo e <b>nao era neutro</b>: favorecia justamente as duas escolhas que o projeto tinha adotado. Todos os numeros foram remedidos. A pagina <b>Cenario Principal</b> fica como registro historico — os numeros dela estao superados.</p></div>

## Como chegamos ate aqui

<div class="jornada">
<div class="jPasso" data-t="1"><span class="jNum">01</span><div class="jTopo">Primeira base e modelo inicial</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">LightGBM</span></div><div class="jHeroRot">R&sup2; = <b>0,447</b> &middot; MAE = <b>56,8</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Serie entomologica</span><ul><li><b>276 semanas</b> descontinuas</li><li>Interrupcao de <b>114 semanas</b></li></ul></div><div class="jBloco"><span class="jRot">Base integrada</span><ul><li>Mosquitos em armadilhas</li><li>Clima</li><li>Casos de dengue</li><li>El Nino</li></ul></div></div></div>
<div class="jPasso" data-t="2"><span class="jNum">02</span><div class="jTopo">Testando outros modelos e cenarios</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">9 cenarios</span><span class="jLinha">9 modelos</span></div><div class="jHeroRot">Melhor R&sup2; = <b>0,476</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Algoritmos</span><ul><li><b>Boosting:</b> LightGBM, GB, HistGB</li><li><b>Bagging:</b> RandomForest, ExtraTrees</li><li><b>Outros:</b> Ridge, ElasticNet, KNN, SVR</li></ul></div><div class="jBloco"><span class="jRot">Cenarios</span><ul><li>Regressao de casos</li><li>Contribuicao do vetor</li><li>Deteccao de surto</li><li>Densidade por bairro</li></ul></div></div></div>
<div class="jPasso" data-t="3"><span class="jNum">03</span><div class="jTopo">Serie historica oficial</div><div class="jHero"><div class="jHeroNum">276 &rarr; 725</div><div class="jHeroRot">semanas &middot; cessao pela Secretaria</div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Escopo</span><ul><li>Serie oficial <b>2012 a 2025</b></li><li>2026 segue por coleta propria</li><li><b>A interrupcao deixa de existir</b></li></ul></div><div class="jBloco"><span class="jRot">Auditoria previa</span><ul><li>Inversao dia/mes corrigida</li><li>222 duplicatas removidas</li><li>Validacao cruzada: <b>divergencia nula</b></li></ul></div></div></div>
<div class="jPasso" data-t="4"><span class="jNum">04</span><div class="jTopo">Reexecucao sobre a serie completa</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">Melhor modelo:</span><span class="jLinha">HistGradientBoosting</span></div><div class="jHeroRot">Bairro descartado</div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Resultados</span><ul><li>Ganho <b>atribuivel a cobertura</b></li><li><b>Nada resiste</b> a correcao multipla</li><li>Bairro descartado: <b>31% de ruido</b></li></ul></div></div></div>
<div class="jPasso" data-t="5"><span class="jNum">05</span><div class="jTopo">Delimitacao do escopo</div><div class="jHero"><div class="jHeroNum">120</div><div class="jHeroRot">execucoes &middot; 30 configuracoes</div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Procedimento</span><ul><li>Escopo reduzido a <b>um cenario</b></li><li>Vies do pico diagnosticado</li><li>Primeira hipotese <b>refutada</b></li><li>Protocolo declarado antes</li></ul></div></div></div>
<div class="jPasso" data-t="6"><span class="jNum">06</span><div class="jTopo">Auditoria e vazamento temporal</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">R&sup2; em 3 meses</span></div><div class="jHeroRot"><b>0,758</b> &rarr; <b>0,437</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">O defeito</span><ul><li>Treino cortado pela data da <b>pergunta</b></li><li>Deveria ser pela data da <b>resposta</b></li><li><b>11 semanas</b> vazadas em h=12</li></ul></div><div class="jBloco"><span class="jRot">O reparo</span><ul><li><b>152 celulas</b> re-rodadas</li><li><b>8 controles</b> com diferenca zero</li><li>Regra num lugar so no codigo</li></ul></div></div></div>
<div class="jPasso" data-t="7"><span class="jNum">07</span><div class="jTopo">Configuracao vigente, ja corrigida</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">Alarme</span></div><div class="jPorH"><span class="jH">1 sem</span><span class="jDe">sens</span><span class="jSeta2">&rarr;</span><span class="jPara">97%</span><span class="jH">1 mes</span><span class="jDe">sens</span><span class="jSeta2">&rarr;</span><span class="jPara">97%</span><span class="jH">2 mes</span><span class="jDe">sens</span><span class="jSeta2">&rarr;</span><span class="jPara">82%</span><span class="jH">3 mes</span><span class="jDe">sens</span><span class="jSeta2">&rarr;</span><span class="jPara">77%</span></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Selecionada</span><ul><li><b>HistGradientBoosting</b></li><li>Perda quantilica <b>0,85</b></li><li>Com variaveis de vetor</li></ul></div><div class="jBloco"><span class="jRot">O que mudou</span><ul><li>Era quantil 0,80 &mdash; caiu para <b>3&ordm;</b></li><li>Metrica de alarme <b>substitui</b> a captura do pico</li></ul></div></div></div>
</div>

## O erro que encontramos

Cada linha da tabela de previsao tem **duas datas**: a da **pergunta**, de onde vem as variaveis, e a da **resposta**, que e o horizonte depois. A linha so fica pronta na data da resposta.

O codigo selecionava o treino pela data da **pergunta**. Com isso, as ultimas semanas do treino entravam com a resposta ainda **no futuro** da semana que estava sendo prevista.

<div class="cards">
<div class="card critico"><div class="cardRot">O exemplo concreto</div><div class="cardTxt">Ao prever <b>26/05/2024</b> a partir de <b>03/03/2024</b>, o treino incluia a linha de <b>18/02/2024</b>, cujo rotulo e <b>12/05/2024 = 1.510 casos</b>, o pico da epidemia. Em 03/03 esse numero nao existia.</div></div>
<div class="card atencao"><div class="cardRot">Quanto contamina</div><div class="cardTxt"><b>0</b> semanas em h=1 &middot; <b>3</b> em h=4 &middot; <b>7</b> em h=8 &middot; <b>11</b> em h=12. Sao 5% do treino, mas justamente as <b>vizinhas mais proximas</b> do ponto previsto.</div></div>
<div class="card bom"><div class="cardRot">O reparo</div><div class="cardTxt">So entra a linha cuja <b>resposta</b> ja tinha acontecido. Filtro por <b>data</b>, nunca por posicao — a serie tem buracos.</div></div>
<div class="card acento"><div class="cardRot">Tem nome na literatura</div><div class="cardTxt">Chama-se <b>purging</b>. O scikit-learn tem o parametro <span class="chip">gap</span> em <b>TimeSeriesSplit</b> exatamente para isso.</div></div>
</div>

<div class="veredito"><span class="vRot">O controle que valida tudo</span><p>Em <b>h=1 nenhuma linha e contaminada</b>, entao o resultado corrigido tem de ser <b>identico</b> ao anterior. Verificado em <b>8 experimentos independentes</b>, mais de <b>12.000 pontos</b>, com diferenca de <b>0,0000000000</b>. Toda diferenca nos demais horizontes e o vazamento, nao ruido de ambiente.</p></div>

## Quanto custou

Configuracao de referencia, periodo de avaliacao (2024+), n=102.

| Horizonte | MAE antes | MAE depois | Variacao | R&sup2; antes | R&sup2; depois |
|---|---|---|---|---|---|
| 1 semana | 101,3 | 101,3 | 0,0% | 0,883 | 0,883 |
| 1 mes | 168,4 | 221,4 | **+31,5%** | 0,779 | **0,628** |
| 2 meses | 184,0 | 270,2 | **+46,8%** | 0,724 | **0,450** |
| 3 meses | 179,6 | 273,9 | **+52,5%** | 0,758 | **0,437** |

<div class="veredito critico"><span class="vRot">O vazamento nao era neutro</span><p>Conjuntos <b>com vetor</b> apanharam cerca de <b>2 vezes mais</b> que os sem vetor na correcao (20,5% contra 11,3%). A <b>perda quantilica</b> apanhou quase <b>2 vezes mais</b> que a padrao (28,7% contra 15,8%), no mesmo algoritmo e mesmo conjunto. <b>Vetor e perda quantilica sao exatamente os dois ingredientes da configuracao que o projeto tinha escolhido.</b> O erro estava sustentando as decisoes.</p></div>

## A configuracao de referencia

<div class="fichaModelo">
<div class="fmTitulo">HistGradientBoosting &middot; perda quantilica 0,85 &middot; com mosquito</div>
<div class="fmLinha"><span class="fmRot">Algoritmo</span><span class="fmVal"><b>HistGradientBoostingRegressor</b><br>scikit-learn</span></div>
<div class="fmLinha"><span class="fmRot">Funcao de perda</span><span class="fmVal"><div class="fmParams"><div class="fmParam"><span class="fmChave">loss</span><span class="fmIgual">=</span><span class="fmNum">"quantile"</span></div><div class="fmParam"><span class="fmChave">quantile</span><span class="fmIgual">=</span><span class="fmNum">0.85</span></div></div></span></div>
<div class="fmLinha"><span class="fmRot">Hiperparametros</span><span class="fmVal"><div class="fmParams"><div class="fmParam"><span class="fmChave">max_iter</span><span class="fmIgual">=</span><span class="fmNum">250</span></div><div class="fmParam"><span class="fmChave">learning_rate</span><span class="fmIgual">=</span><span class="fmNum">0.05</span></div><div class="fmParam"><span class="fmChave">max_leaf_nodes</span><span class="fmIgual">=</span><span class="fmNum">15</span></div><div class="fmParam"><span class="fmChave">min_samples_leaf</span><span class="fmIgual">=</span><span class="fmNum">5</span></div><div class="fmParam"><span class="fmChave">random_state</span><span class="fmIgual">=</span><span class="fmNum">42</span></div></div></span></div>
<div class="fmLinha"><span class="fmRot">Corte de treino</span><span class="fmVal">pela data da <b>resposta</b> &nbsp;<span class="chip">corrigido em 13/09/2026</span></span></div>
<div class="fmLinha"><span class="fmRot">Variaveis</span><span class="fmVal">nucleo + <b>6 de clima</b> + <b>6 de mosquito</b> &nbsp;<span class="chip">conjunto M1</span></span></div>
<div class="fmLinha"><span class="fmRot">Alvo</span><span class="fmVal">casos de dengue <b>confirmados</b> (SINAN), nivel cidade</span></div>
<div class="fmLinha"><span class="fmRot">Selecionada por</span><span class="fmVal">menor erro de calibracao entre <b>30 configuracoes</b> &middot; 120 execucoes</span></div>
<div class="fmLinha"><span class="fmRot">Validacao</span><span class="fmVal"><b>Walk-forward</b> — treina so com o passado, preve uma semana, repete</span></div>
</div>

Era a **2a colocada** antes da correcao. A antiga vencedora, com quantil 0,80, caiu para **3o lugar**.

## Desempenho, ja corrigido

| Horizonte | MAE | R&sup2; | Captura do pico |
|---|---|---|---|
| 1 semana | 98,0 | **0,898** | 0,886 |
| 1 mes | 219,7 | **0,628** | 0,702 |
| 2 meses | 272,6 | **0,450** | 0,417 |
| 3 meses | 278,7 | **0,437** | 0,388 |

<div class="veredito atencao"><span class="vRot">Como ler</span><p>O modelo e <b>honesto ate um mes</b>, explicando <b>63%</b> da variacao. Em tres meses explica <b>44%</b>. A degradacao tem causa medida: a autocorrelacao dos casos explica <b>91,5%</b> da variacao em uma semana e <b>0,0%</b> em doze. <b>Nao e defeito do modelo</b> — em tres meses o passado recente simplesmente nao informa mais.</p></div>

## O modelo como alarme

A "captura do pico" mede se o modelo acerta o **tamanho** da epidemia. Para a vigilancia, o que importa e outra coisa: **o alarme toca? quando? quantas vezes a toa?**

| Horizonte | Sensibilidade | Precisao | Falsos por ano |
|---|---|---|---|
| 1 semana | **96,9%** | 91,2% | 1,0 |
| 1 mes | **97,1%** | **94,3%** | **0,7** |
| 2 meses | **81,6%** | 86,1% | 1,7 |
| 3 meses | **76,9%** | 81,1% | 2,3 |

<div class="cards">
<div class="card bom"><div class="cardRot">O que isso muda</div><div class="cardTxt">"Captura de 0,388 em tres meses" soa como fracasso. "<b>Sinaliza 77% das semanas de surto com tres meses de antecedencia, com 81% de precisao</b>" e um instrumento usavel.</div></div>
<div class="card acento"><div class="cardRot">Por que as duas discordam</div><div class="cardTxt">A captura mede o <b>tamanho</b> da epidemia, que o modelo erra para baixo. O alarme so precisa <b>cruzar o limiar</b>. Sao perguntas diferentes, e a operacional e a segunda.</div></div>
<div class="card atencao"><div class="cardRot">A antecedencia nao se estima</div><div class="cardTxt">O horizonte e fixo: um alarme para a semana W em h=8 foi emitido <b>8 semanas antes</b>. A antecedencia <b>e</b> o horizonte.</div></div>
<div class="card critico"><div class="cardRot">A ressalva que anda junto</div><div class="cardTxt">So existem <b>2 episodios</b> no periodo de avaliacao. Nada por episodio pode ser citado. Sao 32 a 39 semanas de surto, e <b>sem teste de significancia</b>.</div></div>
</div>

## O que caiu com a correcao

<div class="cards">
<div class="card critico"><div class="cardRot">A equivalencia clima &times; vetor</div><div class="cardNum">1 de 8</div><div class="cardTxt">Era o <b>nucleo proposto da tese</b>. Fechava em 4 de 8 com a regua errada e no alvo errado. Com a margem pre-declarada e o alvo decidido, fecha em <b>1</b>.</div></div>
<div class="card critico"><div class="cardRot">"A perda importa mais que o algoritmo"</div><div class="cardNum">invertido</div><div class="cardTxt">Era <b>+20,2%</b> contra <b>+16,5%</b>. Corrigido: perda <b>+9,9%</b>, algoritmo <b>+11,8%</b>. E o efeito da perda <b>depende do algoritmo</b>.</div></div>
<div class="card critico"><div class="cardRot">O unico achado que passava em Holm</div><div class="cardNum">p 0,33</div><div class="cardTxt">Confirmados, P90, 3 meses: era <b>4&times;24</b> com p de <b>0,00018</b>. Corrigido, virou <b>10&times;16</b> com p de <b>0,327</b>. Era vazamento.</div></div>
</div>

## O que sobreviveu, e o que apareceu

<div class="cards">
<div class="card bom"><div class="cardRot">Novo resultado que passa em Holm</div><div class="cardNum">p 0,037</div><div class="cardTxt">O vetor <b>piora</b> o alarme de surto em 3 meses: <b>23&times;7</b> a favor do so-clima, com <b>553 semanas</b>. E o <b>unico</b> resultado do projeto que sobrevive a correcao multipla — e e negativo.</div></div>
<div class="card bom"><div class="cardRot">A camada espacial ficou mais forte</div><div class="cardNum">8 de 8</div><div class="cardTxt">A regra simples ("a ordem de hoje vale para daqui a h semanas") vence o aprendizado de maquina em <b>todas</b> as combinacoes. Era 7 de 8.</div></div>
<div class="card acento"><div class="cardRot">O sinal espacial e real</div><div class="cardNum">0,89</div><div class="cardTxt">Spearman da persistencia contra <b>0,46</b> da climatologia. Nenhuma das duas treina, entao <b>nenhuma tinha vazamento</b>.</div></div>
<div class="card acento"><div class="cardRot">Treinar com a serie toda vence</div><div class="cardNum">3 de 4</div><div class="cardTxt">Os 14 anos resgatados <b>melhoram</b> a previsao do vetor. E para o alvo casos a janela rende so <b>3,8%</b> — nao e alavanca importante.</div></div>
</div>

## O mosquito: o veredito atual

<div class="cards">
<div class="card critico"><div class="cardRot">Comparacoes pareadas</div><div class="cardNum">27 de 60</div><div class="cardTxt">15 pares (mesmo algoritmo, mesma perda, so muda o vetor) &times; 4 horizontes. O vetor erra menos na <b>minoria</b>. Era 35 de 60 antes.</div></div>
<div class="card critico"><div class="cardRot">Sobrevivem a Holm</div><div class="cardNum">0</div><div class="cardTxt">Nenhuma das 60. O melhor p bruto e <b>0,0144</b>.</div></div>
<div class="card atencao"><div class="cardRot">Onde ele ganha, ganha mal</div><div class="cardTxt">Em 3 meses vence em 13 de 15 pares. Mas os <b>5 maiores ganhos sao as 5 configuracoes de LightGBM</b>, o pior algoritmo. No melhor algoritmo o ganho fica entre <b>+8,9 e &minus;11,2</b>.</div></div>
<div class="card"><div class="cardRot">A leitura honesta</div><div class="cardTxt">O vetor <b>compensa algoritmo fraco</b>. LightGBM sem vetor erra 286 a 329 em h=12; com vetor cai para 236 a 272, perto do que o HistGB ja faz <b>sem</b> vetor.</div></div>
</div>

<div class="veredito critico"><span class="vRot">O veredito</span><p><b>A rede de armadilhas nao melhora a previsao de casos de dengue em nivel cidade, de forma demonstravel.</b> Quatro desenhos diferentes, nada sobrevive a correcao multipla, e o unico intervalo de confianca que exclui zero aponta <b>contra</b> o vetor. Isso nao e o mesmo que "a armadilha e inutil": mediu-se uma tarefa especifica, e nao utilidade operacional nem controle vetorial.</p></div>

## Uma segunda frente: o alvo esta inflado

Comparamos nossa serie de casos com a **serie oficial da Secretaria Estadual**, por uma API publica do CEVS/RS.

| Ano | Oficial | Nosso (notificacao) | Nosso (residencia) |
|---|---|---|---|
| 2022 | 5.142 | 5.583 (+8,6%) | **5.133 (&minus;0,2%)** |
| 2025 | 22.504 | 24.812 (+10,3%) | **22.479 (&minus;0,1%)** |

Usamos municipio de **notificacao**; o Estado usa municipio de **residencia**. Trocar o campo alinha em **0,2%**. ⏳ Decisao ainda nao tomada — exige regerar a base e refazer as medicoes.

## Limitacoes declaradas

<div class="cards">
<div class="card atencao"><div class="cardRot">Um vazamento ainda aberto</div><div class="cardTxt">As 6 colunas de clima sao escolhidas <b>uma vez</b>, sobre os 60% iniciais, e reaproveitadas em todos os cortes. <b>A correcao de 13/09 nao toca nisso.</b></div></div>
<div class="card atencao"><div class="cardRot">O ranking de clima e instavel</div><div class="cardTxt">Recortando a serie em 2023, <b>4 das 6 colunas mudam</b>. "Estas 6 variaveis sao as que importam" nao e afirmacao defensavel.</div></div>
<div class="card critico"><div class="cardRot">Poucos episodios</div><div class="cardTxt">So <b>2 episodios</b> de surto na avaliacao, e cerca de <b>2 epidemias grandes</b> na serie inteira. Poder estatistico baixo por construcao.</div></div>
<div class="card"><div class="cardRot">A previsao e um patamar</div><div class="cardTxt">Com perda quantilica 0,85, o numero <b>nao e a media esperada</b>: e um patamar ultrapassado em <b>15%</b> das vezes. Enviesado para cima de proposito.</div></div>
<div class="card"><div class="cardRot">Casos so em nivel cidade</div><div class="cardTxt">O banco por bairro exigia Comite de Etica, inviavel no prazo. O eixo espacial e <b>entomologico puro</b>.</div></div>
<div class="card"><div class="cardRot">Casos so desde 2018</div><div class="cardTxt">Mosquito e clima tem <b>14 anos</b>; casos tem <b>8</b>, e epidemia de verdade so a partir de <b>2022</b>.</div></div>
</div>

## Novas rotas para o artigo e a dissertacao

A pergunta original era se a rede de armadilhas ajuda a prever dengue. A evidencia diz que **nao ajuda**, e em horizonte longo **atrapalha** o alarme. Isso nao encerra o trabalho: muda o que ele afirma. Cinco rotas, da mais forte para a mais especulativa.

<div class="cards">
<div class="card acento"><div class="cardRot">Rota 1 &middot; a mais forte</div><div class="cardTxt"><b>O vazamento temporal como contribuicao metodologica.</b><br>Temos o defeito, a medida do quanto ele infla (<b>+52% de MAE em 3 meses</b>) e a demonstracao de que ele <b>nao e neutro</b>: favorece sistematicamente quem usa mais variaveis e perda assimetrica. E um defeito comum na literatura de previsao epidemiologica, e quase nunca reportado.</div></div>
<div class="card acento"><div class="cardRot">Rota 2</div><div class="cardTxt"><b>O negativo bem medido.</b><br>"A rede de armadilhas nao melhora a previsao de casos, e piora o alarme de longo prazo" — com <b>553 semanas</b>, pre-declaracao escrita antes e correcao de multiplas comparacoes. Resultado negativo com poder e publicavel, e e o que falta na area.</div></div>
<div class="card bom"><div class="cardRot">Rota 3 &middot; a entrega operacional</div><div class="cardTxt"><b>O protocolo espacial simples.</b><br>Uma regra de uma linha vence o aprendizado de maquina em <b>8 de 8</b> combinacoes, e o sinal espacial e real (0,89 contra 0,46). Entrega implantavel, transparente, auditavel e sem infraestrutura — para vigilancia isso e vantagem, nao limitacao.</div></div>
<div class="card bom"><div class="cardRot">Rota 4</div><div class="cardTxt"><b>O modelo como alarme, e nao como estimador.</b><br><b>97%</b> de sensibilidade com um mes de antecedencia e menos de <b>1</b> alarme falso por ano. Precisa de mais episodios para confirmar, e a temporada <b>2026-2027</b> e o unico dado ainda nao usado.</div></div>
<div class="card"><div class="cardRot">Rota 5 &middot; a base</div><div class="cardTxt"><b>A serie de 14 anos como contribuicao de dados.</b><br>Resgatada, corrigida, certificada e agora <b>validada contra a serie oficial do Estado</b>. Independe de qualquer modelo, e sustenta as outras quatro rotas.</div></div>
</div>

<div class="veredito"><span class="vRot">A virada de enquadramento</span><p>A tese deixa de ser <b>"a armadilha serve para prever dengue"</b> e passa a ser <b>"medimos quanto ela vale, com protocolo declarado antes, e mostramos por que outros estudos podem ter superestimado"</b>. E menos vendavel e <b>muito mais defensavel</b>.</p></div>

### O que ainda precisa de decisao

1. **Qual rota vira o eixo.** As cinco sao compativeis entre si, mas a dissertacao precisa de uma espinha.
2. **O alvo.** O PEP declara previsao de **abundancia do vetor**; o codigo preve **casos**. E inversao do objeto, nao ajuste, e esta aberto desde junho de 2026.
3. **Municipio de residencia ou de notificacao.** Trocar alinha com o Estado, e exige regerar tudo.
4. **Fechar o vazamento remanescente** da selecao de clima, ou declara-lo como limitacao conhecida.

### O que ja esta pronto para escrever

<div class="cards">
<div class="card bom"><div class="cardRot">Metodo</div><div class="cardTxt">Pre-declaracoes datadas, emendas registradas, <b>8 controles</b> com diferenca zero, e certificacao adversarial em cada mudanca de pipeline.</div></div>
<div class="card bom"><div class="cardRot">Reprodutibilidade</div><div class="cardTxt">Uma pasta datada por teste, cada uma com pergunta, desenho, numeros-ancora e conclusao rotulada. <b>14 pastas</b>, todas com README.</div></div>
<div class="card bom"><div class="cardRot">Honestidade</div><div class="cardTxt">Os resultados que cairam estao documentados <b>com lapide</b>: data, motivo e quem decidiu. Inclusive os que eram nossos.</div></div>
</div>
