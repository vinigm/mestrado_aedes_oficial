titulo: Por onde comecar
ordem: 5

<div class="veredito"><span class="vRot">Bem-vindo</span><p>Esta pagina e um <b>roteiro de leitura</b>. O site tem bastante coisa, e nem tudo tem o mesmo peso. Aqui esta o caminho curto, em ordem, com o tempo de cada parada.</p></div>

## Em uma frase

O projeto usa **aprendizado de maquina** para prever o numero de **casos de dengue em Porto Alegre**, semana a semana, a partir dos dados de **captura de mosquitos** das armadilhas da prefeitura, de **clima** e do **historico de casos** do SINAN.

## O caminho curto — 15 minutos

<div class="cards">
<div class="card acento"><div class="cardRot">1 &middot; comece aqui &middot; 8 min</div><div class="cardTxt"><b><a href="cenario_principal_2.html">Cenario Principal 2</a></b><br>E a pagina principal e a mais atual. Tem os dados, o modelo escolhido, os resultados ja corrigidos, as limitacoes e, no fim, as rotas possiveis para o artigo.</div></div>
<div class="card bom"><div class="cardRot">2 &middot; 3 min</div><div class="cardTxt"><b><a href="metodologia.html">Metodologia</a></b><br>Como a validacao e feita, por que o protocolo e declarado antes de rodar, e o que conta como resultado.</div></div>
<div class="card"><div class="cardRot">3 &middot; 4 min</div><div class="cardTxt"><b><a href="cenarios.html">Ver todos os cenarios</a></b><br>Cada experimento com seus numeros, lidos direto do MLflow. Serve para conferir qualquer afirmacao.</div></div>
</div>

<div class="veredito atencao"><span class="vRot">Se for ler so uma coisa</span><p>Leia a <b><a href="cenario_principal_2.html">Cenario Principal 2</a></b>. Tudo o mais no site e detalhe ou historico.</p></div>

## O que voce vai encontrar em cada lugar

| Pagina | O que responde |
|---|---|
| **[Cenario Principal 2](cenario_principal_2.html)** | O que o modelo faz hoje, quanto ele acerta, e o que ainda nao sabemos |
| [Cenario Principal](cenario_principal.html) | ⚠️ **Registro historico.** Os numeros sao de 30/08 e estao superados — a pagina traz o aviso no topo |
| [Metodologia](metodologia.html) | Como os resultados sao produzidos e validados |
| [Ver todos os cenarios](cenarios.html) | Um card por experimento, com metricas do MLflow |
| [Modelos testados](modelos_testados.html) | A lista de algoritmos e configuracoes ja avaliados |
| [Diario de atividades](diario.html) | O que foi feito, dia a dia |

## Tres coisas que ajudam a ler os numeros

<div class="cards">
<div class="card"><div class="cardRot">A previsao e um patamar</div><div class="cardTxt">O modelo usa <b>perda quantilica</b>: o numero que ele devolve nao e a media esperada, e um <b>patamar</b> ultrapassado em 15% das vezes. E enviesado para cima <b>de proposito</b>, porque subestimar surto custa mais caro.</div></div>
<div class="card"><div class="cardRot">Treina so com o passado</div><div class="cardTxt">Para prever uma semana, o modelo so ve dados anteriores a ela. E a simulacao honesta de uso real, chamada <b>walk-forward</b>.</div></div>
<div class="card"><div class="cardRot">Nada e "significativo" sem correcao</div><div class="cardTxt">Quando se testa muita coisa, alguma da certo por sorte. Aqui so vira afirmacao o que sobrevive a <b>correcao de multiplas comparacoes</b>.</div></div>
</div>

## O que ja da para afirmar, e o que nao

<div class="cards">
<div class="card bom"><div class="cardRot">Da para afirmar</div><div class="cardTxt">O modelo <b>sinaliza a chegada</b> da epidemia com ate um mes de antecedencia, acertando <b>97%</b> das semanas de surto.</div></div>
<div class="card atencao"><div class="cardRot">Com ressalva</div><div class="cardTxt">Ele <b>subestima o tamanho</b> do pico em 30% a 60%. Serve para alarme, nao para dimensionar leito ou equipe.</div></div>
<div class="card critico"><div class="cardRot">Nao da para afirmar</div><div class="cardTxt">Que os dados de <b>mosquito melhoram</b> a previsao de casos. Ate agora, nao de forma demonstravel — e essa e a pergunta central em aberto.</div></div>
</div>

## Estado do site

Atualizado em **21/09/2026**. E um painel de acompanhamento, nao uma publicacao: serve para o autor controlar o andamento e para mostrar o trabalho em curso.

⚠️ **Quatro dos nove cenarios** ainda exibem numeros medidos antes da correcao de 13/09/2026: *o ganho do mosquito*, *com El Nino*, *sem apagar semanas* e *por bairro*. Os demais ja estao corrigidos. A pagina **Cenario Principal 2** usa apenas numeros corrigidos.
