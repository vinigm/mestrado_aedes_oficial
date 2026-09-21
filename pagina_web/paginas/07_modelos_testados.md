titulo: Modelos testados
ordem: 27

<div class="veredito"><span class="vRot">Para que serve esta pagina</span><p>Lista tudo que ja foi testado no projeto, para que se possa <b>conferir sobreposicao</b> com outras pesquisas do grupo e ver de relance o que ja foi coberto e o que nao foi.</p></div>

## O que o projeto testa

Uma linha da tabela e **uma semana da cidade de Porto Alegre**. O modelo recebe 22 variaveis e responde **quantos casos de dengue havera daqui a 1, 4, 8 ou 12 semanas**.

Treina sempre so com o passado, prevê uma semana, avanca e repete. Isso e o **walk-forward**.

## Os nove algoritmos avaliados

<div class="cards">
<div class="card acento"><div class="cardRot">Boosting &middot; os tres do grid final</div><div class="cardTxt"><b>HistGradientBoosting</b> &middot; <b>GradientBoosting</b> &middot; <b>LightGBM</b><br>sao os que sustentam os resultados atuais</div></div>
<div class="card"><div class="cardRot">Bagging</div><div class="cardTxt">RandomForest &middot; ExtraTrees</div></div>
<div class="card"><div class="cardRot">Lineares</div><div class="cardTxt">Ridge &middot; ElasticNet</div></div>
<div class="card"><div class="cardRot">Outros</div><div class="cardTxt">KNN &middot; SVR</div></div>
</div>

Os seis ultimos foram avaliados na fase inicial e **saíram da rotina em 30/08/2026**, por decisao registrada: o foco passou a ser uma configuracao so.

## O grid que escolheu a configuracao atual

Uma grade completa, sem deixar combinacao de fora:

| Eixo | Opcoes | Quantas |
|---|---|---|
| Algoritmo | HistGradientBoosting · GradientBoosting · LightGBM | 3 |
| Funcao de perda | padrao · quantilica em 0,70 · 0,80 · 0,85 · 0,90 | 5 |
| Conjunto de variaveis | sem mosquito · com mosquito | 2 |

São **30 configuracoes**, cada uma em 4 horizontes: **120 execucoes**. Rodado em 30/08/2026 e **refeito por inteiro em 13/09/2026**, depois da correcao do vazamento temporal.

<div class="cards">
<div class="card bom"><div class="cardRot">A vencedora</div><div class="cardTxt"><b>HistGradientBoosting</b><br>perda quantilica <b>0,85</b><br>com variaveis de mosquito</div></div>
<div class="card"><div class="cardRot">Criterio</div><div class="cardTxt">Menor erro no periodo de <b>calibracao</b>. O periodo de <b>avaliacao</b> ficou guardado como juiz — quem escolhe nao julga.</div></div>
<div class="card atencao"><div class="cardRot">Como citar</div><div class="cardTxt">Sempre <b>"a melhor entre as 30 testadas"</b>, nunca "a melhor possivel".</div></div>
</div>

⚠️ **Os hiperparametros nunca foram buscados.** Todas as 120 execucoes usaram os mesmos valores. E uma lacuna conhecida e declarada.

## Os cenarios de modelagem

Alem da regressao de casos, outras frentes ja rodadas:

| Cenario | O que faz |
|---|---|
| **Regressao de casos** | prevê o numero de casos — e o cenario principal |
| Deteccao de surto | classificacao: vai ou nao passar de um limiar |
| Contribuicao do mosquito | com e sem as variaveis de armadilha, pareado |
| Comparacao com a literatura | replica protocolos de trabalhos de referencia |
| Densidade por bairro | descartado em 16/08/2026: 31% do numero semanal e ruido de amostragem |
| Ranking espacial por zona | prevê a ordem das zonas; a regra simples vence o aprendizado de maquina |
| Janela de treino | expansivel contra deslizante, nos dois alvos |

## Metodos estatisticos usados

<div class="cards">
<div class="card"><div class="cardRot">Diebold-Mariano</div><div class="cardTxt">Compara o erro de dois modelos nas <b>mesmas semanas</b>, com correcao para amostra pequena.</div></div>
<div class="card"><div class="cardRot">McNemar</div><div class="cardTxt">Compara dois classificadores pelas semanas em que eles <b>discordam</b>.</div></div>
<div class="card"><div class="cardRot">Holm</div><div class="cardTxt">Correcao de multiplas comparacoes. Sem sobreviver a ela, nao se escreve "significativo".</div></div>
<div class="card"><div class="cardRot">TOST</div><div class="cardTxt">Teste de <b>equivalencia</b>, para quando a pergunta e "sao parecidos?" e nao "sao diferentes?".</div></div>
<div class="card"><div class="cardRot">Bootstrap em blocos</div><div class="cardTxt">Intervalo de confianca respeitando a autocorrelacao da serie.</div></div>
<div class="card"><div class="cardRot">Spearman</div><div class="cardTxt">Correlacao de ordem, usada na camada espacial.</div></div>
</div>

## O que ainda NAO foi testado

<div class="cards">
<div class="card atencao"><div class="cardRot">Busca de hiperparametros</div><div class="cardTxt">Nenhuma. Todas as execucoes usam os mesmos valores.</div></div>
<div class="card atencao"><div class="cardRot">Redes neurais</div><div class="cardTxt">Nem LSTM, nem Transformer, nem nada de aprendizado profundo.</div></div>
<div class="card atencao"><div class="cardRot">Modelos estatisticos classicos</div><div class="cardTxt">SARIMA e SARIMAX estavam no plano inicial e nao foram executados.</div></div>
<div class="card atencao"><div class="cardRot">Modelos mecanicistas</div><div class="cardTxt">Nada de compartimental (SIR, SEIR) nem de dinamica populacional do vetor.</div></div>
<div class="card atencao"><div class="cardRot">Abordagem espacial em matriz</div><div class="cardTxt">Grade de celulas com propagacao para vizinhas, no estilo bayesiano. <b>Nao usamos.</b></div></div>
<div class="card atencao"><div class="cardRot">Casos por bairro</div><div class="cardTxt">Exigia Comite de Etica e ficou fora do prazo. Os casos existem so em nivel cidade.</div></div>
</div>

<div class="veredito atencao"><span class="vRot">Nota sobre sobreposicao</span><p>O eixo deste trabalho e a <b>serie temporal em nivel cidade</b>, com a densidade de mosquito <b>normalizada por armadilha</b>. Nao ha modelagem espacial em grade, nem uso da localizacao individual das armadilhas, nem casos por bairro.</p></div>
