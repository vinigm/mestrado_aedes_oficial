titulo: Cenario Principal
ordem: 25

<div class="veredito atencao"><span class="vRot">Pagina de acompanhamento</span><p>Nao e resultado final. Serve para controle proprio e para mostrar o andamento. Numeros de <b>30/08/2026</b> — vao mudar. A versao oficial sera montada depois, para a apresentacao.</p></div>

## Como chegamos ate aqui

<div class="jornada">
<div class="jPasso" data-t="1"><span class="jNum">01</span><div class="jTopo">Primeira base e modelo inicial</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">LightGBM</span></div><div class="jHeroRot">R&sup2; = <b>0,447</b> &middot; MAE = <b>56,8</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Serie entomologica</span><ul><li><b>276 semanas</b> descontinuas</li><li>Interrupcao de <b>114 semanas</b></li><li>dez/2018 a jun/2023, retomada em ago/2025</li></ul></div><div class="jBloco"><span class="jRot">Base integrada</span><ul><li>Mosquitos em armadilhas</li><li>Clima</li><li>Casos de dengue</li><li>El Nino</li></ul></div></div></div>
<div class="jPasso" data-t="2"><span class="jNum">02</span><div class="jTopo">Testando outros modelos e cenarios</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">9 cenarios</span><span class="jLinha">9 modelos</span></div><div class="jHeroRot">Melhor R&sup2; = <b>0,476</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Algoritmos</span><ul><li><b>Boosting:</b> LightGBM, GB, HistGB</li><li><b>Bagging:</b> RandomForest, ExtraTrees</li><li><b>Outros:</b> Ridge, ElasticNet, KNN, SVR</li></ul></div><div class="jBloco"><span class="jRot">Cenarios</span><ul><li>Regressao de casos</li><li>Contribuicao do vetor</li><li>Deteccao de surto</li><li>Densidade por bairro</li><li>Confronto com a literatura</li></ul></div></div></div>
<div class="jPasso" data-t="3"><span class="jNum">03</span><div class="jTopo">Serie historica oficial</div><div class="jHero"><div class="jHeroNum">276 &rarr; 725</div><div class="jHeroRot">semanas &middot; cessao pela Secretaria</div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Escopo</span><ul><li>Serie oficial <b>2012 a 2025</b></li><li>2026 segue por coleta propria</li><li><b>A interrupcao deixa de existir</b></li></ul></div><div class="jBloco"><span class="jRot">Auditoria previa</span><ul><li>Inversao dia/mes corrigida</li><li>222 duplicatas removidas</li><li>Validacao cruzada: <b>divergencia nula</b></li></ul></div></div></div>
<div class="jPasso" data-t="4"><span class="jNum">04</span><div class="jTopo">Reexecucao sobre a serie completa</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">Melhor modelo:</span><span class="jLinha">HistGradientBoosting</span></div><div class="jHeroRot">R&sup2; <b>0,447</b> &rarr; <b>0,737</b></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Resultados</span><ul><li>Ganho <b>atribuivel a cobertura</b></li><li>Vence as referencias nos <b>12 horizontes</b></li><li><b>Nada resiste</b> a correcao multipla</li><li>Bairro descartado: <b>31% de ruido</b></li></ul></div></div></div>
<div class="jPasso" data-t="5"><span class="jNum">05</span><div class="jTopo">Delimitacao do escopo</div><div class="jHero"><div class="jHeroNum">120</div><div class="jHeroRot">execucoes &middot; 30 configuracoes</div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Diagnostico</span><ul><li>Resultados sem convergencia</li><li>Faltava criterio de selecao</li></ul></div><div class="jBloco"><span class="jRot">Procedimento</span><ul><li>Escopo reduzido a <b>um cenario</b></li><li>Vies do pico diagnosticado</li><li>Primeira hipotese <b>refutada</b></li><li>Protocolo declarado antes</li></ul></div></div></div>
<div class="jPasso" data-t="6"><span class="jNum">06</span><div class="jTopo">Configuracao vigente</div><div class="jHero"><div class="jHeroNum"><span class="jLinha">Captura do pico</span></div><div class="jPorH"><span class="jH">1 sem</span><span class="jDe">75%</span><span class="jSeta2">&rarr;</span><span class="jPara">85%</span><span class="jH">1 mes</span><span class="jDe">65%</span><span class="jSeta2">&rarr;</span><span class="jPara">83%</span><span class="jH">2 mes</span><span class="jDe">57%</span><span class="jSeta2">&rarr;</span><span class="jPara">63%</span><span class="jH">3 mes</span><span class="jDe">46%</span><span class="jSeta2">&rarr;</span><span class="jPara">62%</span></div></div><div class="jCorpo"><div class="jBloco"><span class="jRot">Selecionada</span><ul><li><b>HistGradientBoosting</b></li><li>Perda quantilica <b>0,80</b></li><li>Com variaveis de vetor</li></ul></div><div class="jBloco"><span class="jRot">Contra a primeira configuracao</span><ul><li>Mesmas semanas de avaliacao</li><li>R&sup2; em 3 meses: <b>0,541</b> &rarr; <b>0,758</b></li></ul></div></div></div>
</div>

## A configuracao de referencia

<div class="fichaModelo">
<div class="fmTitulo">HistGradientBoosting &middot; perda quantilica 0,80 &middot; com mosquito</div>
<div class="fmLinha"><span class="fmRot">Algoritmo</span><span class="fmVal"><b>HistGradientBoostingRegressor</b><br>scikit-learn</span></div>
<div class="fmLinha"><span class="fmRot">Funcao de perda</span><span class="fmVal"><div class="fmParams"><div class="fmParam"><span class="fmChave">loss</span><span class="fmIgual">=</span><span class="fmNum">"quantile"</span></div><div class="fmParam"><span class="fmChave">quantile</span><span class="fmIgual">=</span><span class="fmNum">0.80</span></div></div></span></div>
<div class="fmLinha"><span class="fmRot">Hiperparametros</span><span class="fmVal"><div class="fmParams"><div class="fmParam"><span class="fmChave">max_iter</span><span class="fmIgual">=</span><span class="fmNum">250</span></div><div class="fmParam"><span class="fmChave">learning_rate</span><span class="fmIgual">=</span><span class="fmNum">0.05</span></div><div class="fmParam"><span class="fmChave">max_leaf_nodes</span><span class="fmIgual">=</span><span class="fmNum">15</span></div><div class="fmParam"><span class="fmChave">min_samples_leaf</span><span class="fmIgual">=</span><span class="fmNum">5</span></div><div class="fmParam"><span class="fmChave">random_state</span><span class="fmIgual">=</span><span class="fmNum">42</span></div></div></span></div>
<div class="fmLinha"><span class="fmRot">Variaveis</span><span class="fmVal">nucleo + <b>6 de clima</b> + <b>6 de mosquito</b> &nbsp;<span class="chip">conjunto M1</span></span></div>
<div class="fmLinha"><span class="fmRot">Alvo</span><span class="fmVal">casos de dengue <b>confirmados</b> (SINAN), nivel cidade</span></div>
<div class="fmLinha"><span class="fmRot">Horizontes</span><span class="fmVal">1 a 12 semanas</span></div>
<div class="fmLinha"><span class="fmRot">Validacao</span><span class="fmVal"><b>Walk-forward</b> — treina so com o passado, preve uma semana, repete</span></div>
</div>

## O que o numero significa

<div class="cards">
<div class="card acento"><div class="cardRot">Nao e</div><div class="cardTxt">O numero <b>esperado</b> de casos.</div></div>
<div class="card acento"><div class="cardRot">E</div><div class="cardTxt">Um <b>patamar</b> que so sera ultrapassado em <b>20%</b> das vezes.</div></div>
<div class="card bom"><div class="cardRot">Serve para</div><div class="cardTxt"><b>Alarme.</b> Subestimar custa mais caro que superestimar.</div></div>
<div class="card critico"><div class="cardRot">Cuidado</div><div class="cardTxt">E enviesado para cima <b>de proposito</b>. Dizer isso sempre que o numero aparecer.</div></div>
</div>

## O achado metodologico

<div class="cards">
<div class="card"><div class="cardRot">Trocar de algoritmo</div><div class="cardNum">+16,5%</div><div class="cardTxt">do melhor para o pior dos tres testados.</div></div>
<div class="card critico"><div class="cardRot">Trocar a funcao de perda</div><div class="cardNum">+20,2%</div><div class="cardTxt">no <b>mesmo</b> algoritmo. Custa mais caro.</div></div>
<div class="card atencao"><div class="cardRot">Perda padrao no ranking</div><div class="cardNum">10&ordf;–23&ordf;</div><div class="cardTxt">as 6 configuracoes de perda padrao, de 30. Nenhuma no top 9.</div></div>
</div>

<div class="veredito"><span class="vRot">A conclusao</span><p>A <b>funcao de perda importa mais que a escolha do algoritmo</b>. O projeto passou meses comparando 9 algoritmos, e o ganho maior estava numa linha de configuracao que ninguem tinha mexido. O mesmo HistGradientBoosting com perda padrao cai para o <b>20&ordm; lugar</b>.</p></div>

## Quanto se ganhou, e de onde veio

Comparacao entre a **primeira configuracao** (LightGBM, perda padrao, sem vetor) e a **atual**, medidas nas **mesmas semanas** de avaliacao. A diferenca e so de modelagem: nenhuma das duas recebeu dado que a outra nao tivesse.

| horizonte | primeira configuracao | atual | ganho |
|---|---|---|---|
| 1 semana | 75% | **85%** | +10 pp |
| **1 mes** | 65% | **83%** | **+18 pp** |
| 2 meses | 57% | **63%** | +6 pp |
| **3 meses** | 46% | **62%** | **+16 pp** |

*(captura do pico; R&sup2; em 3 meses vai de 0,541 para 0,758)*

### De onde veio o ganho, passo a passo

Decomposicao em **um mes**, acrescentando uma mudanca por vez:

| passo | captura do pico | efeito |
|---|---|---|
| Primeira configuracao | 64,7% | — |
| + trocar o algoritmo para HistGradientBoosting | 79,8% | **+15,1 pp** |
| + acrescentar as variaveis de vetor | 69,9% | **&minus;9,9 pp** |
| + calibrar a funcao de perda | **83,2%** | **+13,3 pp** |

<div class="veredito atencao"><span class="vRot">O que a decomposicao revela</span><p>O vetor, sozinho e sem calibracao, <b>derruba a captura do pico em 10 pontos</b> — ele melhora o erro medio e piora o topo. So nao prejudica porque a perda quantilica vem depois e corrige justamente o topo, com folga. <b>E um efeito de interacao</b>: as duas mudancas isoladas nao entregam o que entregam juntas. Isso nao aparecia nas analises anteriores, que mediram o vetor por MAE e por Diebold-Mariano, nunca por captura de pico.</p></div>

## Desempenho por horizonte

Medido em 2024+, periodo que **nao participou** da escolha da configuracao.

<div class="cards">
<div class="card bom"><div class="cardRot">1 semana</div><div class="cardNum">85%</div><div class="cardTxt">do pico capturado &middot; R&sup2; 0,88<br>era 82% com perda padrao</div></div>
<div class="card bom"><div class="cardRot">1 mes</div><div class="cardNum">83%</div><div class="cardTxt">do pico capturado &middot; R&sup2; 0,78<br>era 70% &mdash; <b>maior ganho</b></div></div>
<div class="card atencao"><div class="cardRot">2 meses</div><div class="cardNum">63%</div><div class="cardTxt">do pico capturado &middot; R&sup2; 0,72<br>era 65% &mdash; <b>diferenca dentro do ruido</b></div></div>
<div class="card atencao"><div class="cardRot">3 meses</div><div class="cardNum">62%</div><div class="cardTxt">do pico capturado &middot; R&sup2; 0,76<br>era 58% com perda padrao</div></div>
</div>

<div class="veredito atencao"><span class="vRot">Como ler estes numeros</span><p>O ganho da calibracao <b>nao e uniforme</b>: concentra-se em <b>um mes</b> (70% para 83%). Em <b>dois meses</b> a diferenca de dois pontos esta <b>dentro do ruido</b> — o intervalo de confianca da diferenca por semana de pico e <b>[-87; +55] casos</b>, e cruza zero. A mesma configuracao com outros valores de quantil sobe e desce nesse horizonte sem padrao, e nos demais algoritmos o efeito e positivo. <b>Nao ha piora; ha ausencia de ganho mensuravel.</b></p></div>

### Contra as reguas simples

| horizonte | modelo | repetir o valor de hoje | media historica da epoca |
|---|---|---|---|
| 1 semana | 0,85 | **0,89** | 0,14 |
| 1 mes | **0,76** | 0,42 | 0,08 |
| 2 meses | **0,74** | −0,48 | −0,07 |
| 3 meses | **0,64** | −1,08 | −0,20 |

Valor negativo = pior que chutar a media de todas as semanas. **Em 1 semana o modelo perde** para a regra "vai ter o mesmo tanto de hoje" — nesse horizonte ninguem precisa de modelo.

## Os dados

![Cobertura de cada fonte, semana a semana](imagens/cobertura_fontes.png)

<div class="cards">
<div class="card acento"><div class="cardRot">Mosquito &middot; armadilhas</div><div class="cardNum">718</div><div class="cardTxt">semanas, set/2012 a ago/2026. Secretaria ate 2025, raspagem propria depois — <b>sem vao entre as duas</b>.</div></div>
<div class="card bom"><div class="cardRot">Clima &middot; NASA POWER</div><div class="cardNum">725</div><div class="cardTxt">semanas. Cobria so <b>388</b> ate a recaptura de 29/08.</div></div>
<div class="card critico"><div class="cardRot">Casos &middot; SINAN</div><div class="cardNum">428</div><div class="cardTxt">semanas, fev/2018 a abr/2026. <b>E o gargalo</b> — limita a janela util de tudo.</div></div>
<div class="card"><div class="cardRot">El Nino &middot; NOAA</div><div class="cardNum">434</div><div class="cardTxt">semanas, 2018+. Cobre exatamente o periodo dos casos, entao <b>nao descarta nenhuma linha</b>.</div></div>
</div>

<div class="veredito"><span class="vRot">O que o grafico mostra</span><p>Mosquito e clima cobrem os <b>14 anos</b>. Os casos so existem de <b>2018</b> em diante — e sao eles que definem quanto dado o modelo realmente pode usar. Os cortes finos na faixa do mosquito sao as <b>7 semanas sem vistoria</b>: a virada de 2017/18, uma semana de 2022 e as <b>tres semanas da enchente de maio/2024</b>.</p></div>

A variavel de mosquito e **femeas de *Aedes aegypti* divididas pelas armadilhas efetivamente inspecionadas** na semana. So femeas, porque macho nao transmite.

## O mosquito: o que mostra e o que nao prova

<div class="cards">
<div class="card bom"><div class="cardRot">Em 3 meses</div><div class="cardNum">15 de 15</div><div class="cardTxt">combinacoes de algoritmo e perda melhoram com mosquito.</div></div>
<div class="card critico"><div class="cardRot">Em 1 semana</div><div class="cardNum">0 de 15</div><div class="cardTxt">piora em todas. Coerente: o mosquito e sinal <b>antecedente</b>.</div></div>
<div class="card acento"><div class="cardRot">No topo do grid</div><div class="cardNum">8 de 10</div><div class="cardTxt">das melhores configuracoes usam mosquito.</div></div>
<div class="card critico"><div class="cardRot">Sobrevivem ao teste</div><div class="cardNum">0 de 60</div><div class="cardTxt">comparacoes pareadas passam na correcao para multiplas comparacoes.</div></div>
</div>

<div class="veredito critico"><span class="vRot">A ressalva que precisa ir junto</span><p>A direcao e <b>consistente</b>; a prova <b>nao existe</b>. As duas coisas precisam ser ditas na mesma frase. Em horizonte longo o mosquito e o preditor individual mais forte disponivel (correlacao de <b>0,61 a 0,62</b> entre 4 e 8 semanas, contra 0,27 a 0,40 do clima) — e ainda assim nao fecha estatisticamente.</p></div>

## Testado e descartado

Tudo abaixo foi testado com regras escritas **antes** de rodar, e reprovado por medicao.

| tentativa | resultado |
|---|---|
| alvo em casos **notificados** | pior — R² 0,42 contra 0,76 em 3 meses |
| alvo corrigido por **nowcasting** | e a **mesma serie** que notificados: identica em 99,1% das semanas |
| **Tweedie** como funcao de perda | piora o vies do pico em 2 e 3 meses |
| mes-alvo como variavel **categorica** | neutro |
| **log** no alvo | piora bastante o vies |
| **lags anuais** (52 e 104 semanas) | piora 2 e 3 meses |
| **anomalia climatica** contra a media historica | piora 3 meses |
| **acumulo** de chuva e calor em 8 e 12 semanas | piora 3 meses |
| indicadores de transmissao do InfoDengue (`Rt` e outros) | ganho de 0,004 — nulo |
| **cortar a serie** e usar so 2022 em diante | treinaria nas 2 menores epidemias para prever as 2 maiores |
| **El Nino / La Nina** | ✅ **unica aprovada** — ganho de ~7% em 2 meses |

O El Nino passou em teste isolado e **ainda nao foi validado dentro do grid** — e candidato, nao faz parte da configuracao.

## Limitacoes

<div class="cards">
<div class="card critico"><div class="cardRot">Amostra de epidemias</div><div class="cardNum">2</div><div class="cardTxt">temporadas grandes: <b>2024 e 2025</b>. E disso que o modelo aprende magnitude.</div></div>
<div class="card critico"><div class="cardRot">Sorotipo preenchido</div><div class="cardNum">0,33%</div><div class="cardTxt">de 56.624 casos. <b>43 registros em 2025.</b> O campo existe, o dado nao.</div></div>
<div class="card atencao"><div class="cardRot">Taxa de confirmacao</div><div class="cardNum">73% &rarr; 38%</div><div class="cardTxt">de 2022 a 2025. <b>O alvo mudou de significado</b> no meio da serie.</div></div>
<div class="card atencao"><div class="cardRot">Clima futuro</div><div class="cardNum">indisponivel</div><div class="cardTxt">os casos de t+12 vem do clima de t+4 a t+8, que <b>ainda nao aconteceu</b>.</div></div>
</div>

O grupo InfoDengue declara as **mesmas limitacoes** de sorotipo e imunidade no Relatorio Tecnico 02/2026 — vira citacao, nao fraqueza do trabalho.

<div class="veredito atencao"><span class="vRot">Sobre a escolha da configuracao</span><p>Trinta configuracoes competiram. Escolher a melhor entre trinta garante que <b>parte da vantagem e sorte</b>. As tres primeiras sao o mesmo algoritmo variando so o quantil (0,80 &middot; 0,85 &middot; 0,70), separadas por <b>2% a 4%</b> — estatisticamente indistinguiveis. A afirmacao honesta e <b>"a melhor entre as 30 testadas"</b>, nunca "a melhor possivel".</p></div>

## As 22 variaveis do modelo

O que entra de fato no `HistGradientBoosting`, na ordem em que o motor monta.

| grupo | variavel | o que e |
|---|---|---|
| **Autorregressivo** | `casos` | casos da semana atual |
| | `casos_lag1` a `casos_lag4` | casos de 1 a 4 semanas atras |
| | `casos_mm4` | media movel de 4 semanas |
| **Sazonalidade** | `sem_sin` · `sem_cos` | epoca do ano da semana atual |
| | `alvo_sin` · `alvo_cos` | epoca do ano da **semana prevista** |
| **Clima** | `temp_media_lag4` | temperatura media, 4 semanas atras |
| | `umid_media` | umidade media da semana |
| | `temp_media_lag3` | temperatura media, 3 semanas atras |
| | `temp_max` | temperatura maxima da semana |
| | `pressao_media_lag3` | pressao media, 3 semanas atras |
| | `pressao_media_lag4` | pressao media, 4 semanas atras |
| **Mosquito** | `aedes_aegypti_por_armadilha` | densidade da semana atual |
| | `..._lag1` a `..._lag4` | densidade de 1 a 4 semanas atras |
| | `vetor_mm4` | media movel de 4 semanas |

As **6 de clima nao sao fixas**: sao as melhores de 22 candidatas, escolhidas por ganho antes de cada rodada. As demais colunas de clima ficam de fora de proposito — mais variaveis, com ~300 semanas de treino, viram ruido.

**Fora do modelo, de proposito:** identificadores (`fonte`, `SE`, `data`, `ano`, `semana`), contagens brutas de mosquito (`aedes_aegypti`, `numero_de_armadilhas`), as outras especies (`aedes_albopictus`, `culex_sp`) e a marca `denominador_aproximado` — esta ultima porque em 16/08 ela vazou como feature e quebrou o modelo.

## Proximos passos

1. Gravar a configuracao de referencia no codigo — hoje ela existe so nas analises datadas.
2. Validar o El Nino dentro do grid completo, e nao isolado.
3. Teste focado em 3 meses com cinco sementes, para medir bem o efeito do mosquito e ver se ele depende da inicializacao.
4. Confirmar na temporada **2026-2027** — o unico dado ainda nao usado, e o unico caminho para transformar indicio em achado com prova.
