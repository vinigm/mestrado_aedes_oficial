# Parte 9 — Os três argumentos, limitações e próximos passos

## 9.1 De onde vêm os três argumentos e por que esta seção existe

No dia 26/09/2026, antes do seminário de andamento, o **cenário adotado** — o modelo de previsão de casos
de dengue descrito nas seções anteriores deste documento — foi submetido a uma **banca adversarial
simulada**: quatro pareceres independentes (um estatístico, um epidemiologista, um revisor de aprendizado
de máquina e um advogado, cada um interpretado como um papel crítico distinto, não como quatro pessoas
reais) atacaram três frases que o Vinicius havia formulado para defender o trabalho perante a banca real.
O registro completo está em `analises/2026-09-26_banca_adversarial/README.md`. Esta seção traduz esse
registro para o documento final: cita as três frases originais, mostra o que a evidência sustenta e o que
não sustenta em cada uma, entrega a reescrita defensável de cada argumento, expõe um erro que a própria
banca simulada cometeu (e por que isso importa), responde às cinco perguntas mais difíceis que uma banca
real faria, lista todas as limitações conhecidas do trabalho, argumenta o que este projeto fez de
metodologicamente incomum para a área, e fecha com os próximos passos, separando o que é barato do que é
caro.

Antes de entrar nos argumentos, a próxima seção define, uma única vez e com exemplo numérico, cada
instrumento estatístico citado ao longo do texto. Quem já conhece esses instrumentos pode avançar para a
seção 9.3, mas as definições ficam aqui porque esta seção é lida de forma independente das demais.

---

## 9.2 Instrumentos estatísticos usados nesta seção

### 9.2.1 Erro absoluto médio (em inglês *mean absolute error*, abreviado MAE)

É a média da diferença, em módulo (isto é, sempre positiva, ignorando se o modelo errou para cima ou para
baixo), entre o número de casos que de fato aconteceu numa semana e o número que o modelo previu para
aquela mesma semana.

**Fórmula:**

```
MAE = (1/n) * soma, para i = 1 até n, de |y_i - ŷ_i|
```

Onde:
- **n** é o número de semanas avaliadas (o "par" pergunta-resposta);
- **y_i** é o número real de casos confirmados de dengue na semana **i**;
- **ŷ_i** é o número de casos que o modelo previu para a semana **i**, feita a previsão com a informação
  disponível até a data em que a pergunta foi feita (nunca usando informação futura — essa regra é
  detalhada em outra seção deste documento, sob o nome de corte temporal do *walk-forward*, um método de
  avaliação que testa o modelo repetidamente ao longo do tempo, sempre prevendo o futuro a partir do
  passado, nunca embaralhando datas);
- **|·|** é o valor absoluto (o módulo): transforma qualquer diferença negativa em positiva, para que um
  erro de "−300" e um erro de "+300" contem igualmente como erro de 300.

**Exemplo numérico com dados deste projeto:** no horizonte de 3 meses (12 semanas de antecedência, a
notação usada no projeto é **h=12**), o painel oficial de erro do cenário adotado (avaliação entre
01/01/2024 e cerca de 01/02/2026, sobre **284** pares pergunta-resposta) registra **MAE = 278,8**. Isso
não é um número abstrato: nas semanas classificadas na faixa de gravidade "Alerta ou mais" (mais de 421
casos confirmados na semana, um limiar oficial da Prefeitura detalhado na seção 9.7), o número real
mediano (mediana é o valor do meio de uma lista ordenada, metade dos casos fica acima e metade abaixo) foi
de **917 casos** numa semana, e o erro absoluto mediano nessa mesma faixa foi de **539 casos**. Isso
significa que, numa semana típica de pico dentro dessa faixa, com 917 casos reais, o modelo previu por
volta de **378 casos** (917 − 539). É como planejar leitos, testes e equipes de bloqueio para uma cidade
esperando 378 casos e a cidade receber 917 — mais que o dobro da demanda prevista.

### 9.2.2 Coeficiente de determinação (R²)

Mede que fração da variação (subida e descida) do número real de casos, semana a semana, o modelo consegue
acompanhar, comparado com o quão errado seria simplesmente sempre "chutar" a média histórica de casos.

**Fórmula:**

```
R² = 1 − (SS_res / SS_tot)
SS_res = soma, para i = 1 até n, de (y_i − ŷ_i)²
SS_tot = soma, para i = 1 até n, de (y_i − ȳ)²
```

Onde:
- **SS_res** ("soma dos quadrados dos resíduos") é a soma dos erros do modelo, cada um elevado ao quadrado
  (elevar ao quadrado penaliza mais os erros grandes que os pequenos, e garante que erros positivos e
  negativos não se cancelem);
- **SS_tot** ("soma dos quadrados total") é a mesma soma, mas comparando cada valor real **y_i** com a
  média de todos os valores reais **ȳ** (em vez de comparar com a previsão do modelo) — é o erro que se
  cometeria usando a média como previsão ingênua;
- **R² = 1** significaria previsão perfeita; **R² = 0** significaria que o modelo é tão bom quanto sempre
  prever a média; **R²** negativo significaria que o modelo é pior que essa previsão ingênua.

**Exemplo numérico com dados deste projeto:** em h=1 (1 semana de antecedência), **R² = 0,898**: o modelo
explica 89,8% da variação semana a semana dos casos, e erra pouco. Em h=12 (3 meses), **R² = 0,437**: o
modelo ainda acompanha a tendência geral melhor que a média histórica, mas já perde muito da capacidade de
seguir as subidas e descidas finas. Essa queda de 0,898 para 0,437 é o retrato numérico de uma ideia
central deste trabalho: **quanto mais longe no futuro se pergunta, menos o modelo sabe**.

### 9.2.3 Perda quantílica (em inglês *quantile loss*, também chamada de perda *pinball*)

O cenário adotado não tenta prever "o número mais provável" de casos. Ele tenta prever um valor tal que a
probabilidade do número real ficar **abaixo** dele seja um valor escolhido de antemão — um **quantil**. Um
quantil **τ** (a letra grega tau, usada convencionalmente para essa fração) é o valor abaixo do qual cai a
fração **τ** das observações. O quantil 0,5 é a mediana (metade abaixo, metade acima). O quantil 0,85,
usado neste projeto, é o valor abaixo do qual ficam 85% das semanas — ou seja, deliberadamente um valor
**alto**, para reduzir o risco de o modelo prever "de menos" bem no momento em que soar um alarme.

**Fórmula da perda quantílica**, para um quantil-alvo **τ** entre 0 e 1:

```
L_τ(y, q) = (y − q) · τ,        se y ≥ q
L_τ(y, q) = (q − y) · (1 − τ),  se y < q
```

Onde:
- **y** é o valor real observado;
- **q** é o valor previsto para aquele quantil;
- **τ** é o quantil-alvo (0,85 no cenário adotado).

Essa fórmula é assimétrica de propósito: quando **τ** é alto (como 0,85), errar por prever **de menos**
(y ≥ q) custa 0,85 por unidade de erro, enquanto errar por prever **de mais** (y < q) custa só 0,15 por
unidade. Isso empurra o modelo, durante o treino, a preferir previsões mais altas — coerente com o objetivo
de servir de gatilho de alarme, não de estimativa central.

**Exemplo numérico com dados deste projeto:** usando o mesmo caso da faixa "Alerta ou mais" (y = 917,
q ≈ 378, o valor do quantil 0,85 nessa faixa, derivado do erro mediano de 539 já apresentado), e como
y ≥ q:

```
L_0,85(917, 378) = (917 − 378) · 0,85 = 539 · 0,85 = 458,15
```

Se o mesmo erro de 539 tivesse ocorrido na direção contrária (o modelo prevendo 378 a mais do que o real,
ou seja y = 917 e q = 1.456), a perda seria só **539 · 0,15 = 80,85** — quase seis vezes menor. É essa
assimetria que justifica escolher o quantil 0,85 para um modelo que vai virar alarme: o custo de prever
baixo demais é maior, de propósito, que o custo de prever alto demais.

### 9.2.4 Escore de intervalo ponderado (em inglês *weighted interval score*, abreviado WIS)

É a métrica de erro **oficial** usada nos desafios brasileiros de previsão de epidemias (os "sprints" de
previsão, citados nas seções de literatura deste documento). Diferente do MAE, que compara um único número
previsto com o real, o WIS avalia a previsão inteira — um **intervalo de previsão** (uma faixa entre um
valor baixo e um valor alto dentro da qual o modelo diz que o valor real deve cair, com uma probabilidade
declarada, por exemplo 90%) mais o valor central (a mediana). O WIS soma a perda quantílica (seção 9.2.3)
de cada quantil que compõe o intervalo, ponderando cada um.

**Fórmula, para K intervalos de previsão mais a mediana:**

```
WIS = (1 / (K + 0,5)) · [ (1/2)·|y − m|  +  soma, para k = 1 até K, de (w_k · IS_k) ]
```

Onde, para cada intervalo **k** com nível de confiança **(1 − α_k)** (por exemplo, um intervalo de 90% tem
**α_k = 0,10**), limite inferior **l_k** e limite superior **u_k**:

```
IS_k = (u_k − l_k) + (2/α_k)·(l_k − y)·[se y < l_k]  +  (2/α_k)·(y − u_k)·[se y > u_k]
w_k = α_k / 2
```

Em português:
- **y** é o valor real;
- **m** é a previsão central (a mediana, quantil 0,5);
- **K** é a quantidade de intervalos usados (por exemplo, um intervalo de 50% e um de 90% dão K = 2);
- **IS_k** ("escore de intervalo") de cada intervalo é a **largura** do intervalo (**u_k − l_k**) mais uma
  **penalidade extra** se o valor real caiu fora dele — para cima do limite superior ou para baixo do
  limite inferior. Quanto mais estreito o intervalo, menor o primeiro termo, mas quanto mais estreito,
  maior o risco de errar e pagar a penalidade;
- **w_k** é o peso de cada intervalo, proporcional a **α_k** — intervalos mais largos (mais "confiantes",
  como o de 90%) pesam menos na soma que intervalos mais estreitos (como o de 50%).

O WIS resolve, numa métrica só, a tensão entre **dois erros opostos**: um intervalo tão largo que nunca
erra, mas é inútil para decisão (por exemplo, "entre 0 e 5.000 casos"), e um intervalo tão estreito que é
preciso, mas erra o tempo todo. Por isso ele é a métrica oficial dos sprints: pune os dois excessos ao
mesmo tempo.

**Exemplo numérico ilustrativo, construído a partir dos números agregados deste projeto** (não é o
registro exato de uma semana específica, porque as previsões de cada quantil por semana não foram
publicadas individualmente neste documento — é uma reconstrução pedagógica a partir dos números do painel
de calibração por faixa, para mostrar o mecanismo do cálculo):

Usando a faixa "Alerta ou mais" (y = 917), a previsão central m ≈ 378 (o mesmo valor do quantil 0,85 já
usado, adotado aqui como aproximação da mediana para fins didáticos) e um único intervalo de 90%
(K = 1, α₁ = 0,10) com a largura real medida para essa faixa (**592,7**, do painel "Largura do intervalo
contra o erro real"), reconstruindo os limites como simétricos em torno de 378:

```
l_1 = 378 − 592,7/2 = 81,65
u_1 = 378 + 592,7/2 = 674,35
```

Como o valor real (917) caiu **acima** do limite superior (674,35):

```
IS_1 = (674,35 − 81,65) + (2/0,10)·(917 − 674,35)
     = 592,7 + 20 · 242,65
     = 592,7 + 4.853,0
     = 5.445,7

w_1 = 0,10 / 2 = 0,05

WIS = (1 / (1 + 0,5)) · [ (1/2)·|917 − 378| + 0,05 · 5.445,7 ]
    = (1/1,5) · [ 269,5 + 272,285 ]
    = (1/1,5) · 541,785
    = 361,19
```

Esse valor reconstruído (≈ 361) tem a mesma ordem de grandeza dos WIS agregados realmente medidos e
publicados para o cenário adotado (**FATO, medido em 26/09/2026, tabela oficial**: WIS = 101,9 em h=1;
**215,4** em h=4; 288,6 em h=8; 300,7 em h=12), o que confirma que a reconstrução é plausível — mas os
números que sustentam qualquer comparação estatística neste documento são os medidos, não os
reconstruídos. É com esses números medidos que o modelo é comparado contra a **régua climatológica** — uma
previsão ingênua descrita na seção 9.4 — usando o teste estatístico da seção 9.2.6.

### 9.2.5 Sensibilidade, precisão e o índice de Youden

Quando o modelo é usado como **alarme binário** (dispara ou não dispara, em vez de dar um número), há
quatro desfechos possíveis toda vez que se compara o alarme com a realidade numa semana:

- **verdadeiro positivo:** o alarme disparou e realmente houve surto;
- **falso positivo:** o alarme disparou e não houve surto;
- **verdadeiro negativo:** o alarme não disparou e realmente não houve surto;
- **falso negativo:** o alarme não disparou e houve surto (o pior caso: um surto que passou batido).

A **sensibilidade** é a fração dos surtos reais que o alarme conseguiu capturar:

```
sensibilidade = verdadeiros positivos / (verdadeiros positivos + falsos negativos)
```

A **precisão** é a fração dos alarmes disparados que estavam certos:

```
precisão = verdadeiros positivos / (verdadeiros positivos + falsos positivos)
```

O **índice de Youden** (também chamado de estatística J de Youden) resume, num único número entre −1 e 1,
o quanto um alarme é melhor que "jogar uma moeda":

```
J = sensibilidade + especificidade − 1
```

Onde a **especificidade** é a fração das semanas sem surto que o alarme corretamente deixou em silêncio
(verdadeiros negativos / (verdadeiros negativos + falsos positivos)). **J = 0** significa desempenho igual
ao acaso; **J = 1** significa alarme perfeito.

**Exemplo numérico com dados deste projeto:** em h=4 (1 mês de antecedência), o cenário adotado tem
sensibilidade de **97,1%** e Youden de **0,94** contra o evento "semana com mais de 100 casos". Como
**J = sensibilidade + especificidade − 1**, a especificidade fica isolada por:

```
especificidade = J − sensibilidade + 1 = 0,9412 − 0,9706 + 1 = **0,9706**, ou seja 97,1%
```

Ou seja, o modelo não só captura 97,1% dos surtos reais em 1 mês, como também fica em silêncio
corretamente em 96,9% das semanas calmas — os dois lados do alarme funcionam bem **nesse recorte**. A
ressalva "nesse recorte" é o assunto central da seção 9.4: um Youden alto contra um evento não prova, por
si, que o alarme vence outra forma de prever a mesma coisa.

### 9.2.6 Teste de McNemar e correção de Holm para comparações múltiplas

Quando dois métodos de alarme (por exemplo, o cenário adotado e uma regra simples como "dispara se o
mesmo período do ano passado já tinha passado do limiar") são comparados **na mesma semana**, a maioria das
semanas os dois concordam (os dois disparam, ou os dois ficam quietos). O que decide qual método é melhor
são só as semanas em que eles **discordam**. O **teste de McNemar** usa só essas semanas discordantes.

Sejam **b** o número de semanas em que o método A acertou e o método B errou, e **c** o número de semanas
em que foi o contrário. Para amostras pequenas (poucas semanas discordantes, como é o caso aqui), a forma
mais adequada é o **teste exato binomial**: sob a hipótese de que os dois métodos são igualmente bons
(hipótese chamada de **hipótese nula**), o número de vezes que A vence deveria seguir uma distribuição
binomial com **n = b + c** tentativas e probabilidade 0,5 em cada uma — como jogar uma moeda **n** vezes.

**Exemplo numérico com dados deste projeto:** em h=4, comparando o cenário adotado contra a regra "hoje já
passou de 100 casos", há **15** semanas discordantes, das quais o modelo venceu em **13** e a regra em
**2** (b = 13, c = 2, n = 15). O **p-valor** (a probabilidade de observar uma diferença tão grande ou maior
só por acaso, se os dois métodos fossem igualmente bons) do teste exato binomial de duas caudas é:

```
P(X ≤ 2) = soma, para k = 0 até 2, de C(15,k) · 0,5^15
         = [C(15,0) + C(15,1) + C(15,2)] / 2^15
         = [1 + 15 + 105] / 32.768
         = 121 / 32.768
         = 0,003693

p (duas caudas) = 2 · 0,003693 = 0,00739
```

Esse **p ≈ 0,0074** é o **p nominal** — antes de qualquer ajuste. Dois ajustes entram depois: primeiro, um
**bloco-bootstrap** (uma técnica de reamostragem que respeita blocos de semanas consecutivas, em vez de
embaralhar semanas isoladas, porque casos de dengue numa semana são parecidos com os da semana anterior —
essa dependência entre observações vizinhas se chama **autocorrelação**) reestima o p-valor levando em
conta que 15 semanas discordantes não são 15 informações independentes. Segundo, a **correção de Holm**
ajusta o p-valor porque este teste não foi o único feito: o projeto rodou uma família de comparações (24
testes em 26/09/2026), e quanto mais testes se faz, maior a chance de achar "significância" por puro
acaso — a correção de Holm reduz essa chance inflada, tornando cada p-valor individual mais conservador
(mais difícil de ser considerado significativo). O **p final reportado após os dois ajustes é 0,103** —
maior que o nominal de 0,0074, e **acima do limiar convencional de 0,05** abaixo do qual um resultado é
chamado de estatisticamente significativo. Ou seja: mesmo com 13 vitórias em 15 discordâncias, depois de
corrigir pela autocorrelação e pela quantidade de testes feitos, **o resultado não pode ser chamado de
"significativo"**.

Já em h=12, a mesma comparação contra "hoje já passou" tem **37** discordantes, divididos **31 a 6** a
favor do modelo — uma vantagem proporcionalmente parecida, mas com mais observações — e o p final
reportado é **0,00062**, abaixo de 0,05: **esse, sim, é significativo**.

---

## 9.3 Os três argumentos, frase a frase

O Vinicius formulou três argumentos para levar ao seminário. Cada um é reproduzido aqui **literalmente**,
seguido do que a evidência sustenta, do que não sustenta, e da reescrita defensável construída em
`analises/2026-09-26_banca_adversarial/README.md` §2.

### 9.3.1 Argumento 1 (A1)

> "O modelo é fiável para dizer quando estamos em calmaria e excelente para disparar alarmes a 1 mês de
> distância."

**O que a evidência sustenta:**

- A calibração do modelo em semanas de calmaria é um **FATO medido em 26/09/2026**: o intervalo de
  confiança de 90% (uma faixa de previsão dentro da qual se espera, 90 das 100 vezes, que o valor real
  caia) cobriu de fato **90,5%** das **814** semanas classificadas como "calmaria" (0 a 20 casos
  confirmados na semana), quase exatamente o esperado.
- Avaliado pela métrica **oficial dos sprints brasileiros de previsão de epidemias**, o WIS (seção 9.2.4),
  o cenário adotado vence a **régua climatológica** (definida na seção 9.4) em h=4 com **p de Holm menor
  que 0,0001** — um resultado estatístico robusto, não descritivo.
- Na comparação binária contra a regra mais fraca ("hoje já passou de 100"), a direção do efeito favorece
  o modelo (13 de 15 semanas discordantes, seção 9.2.6) — o efeito aponta a favor, mesmo sem fechar
  estatisticamente com essa amostra pequena.

**O que a evidência NÃO sustenta:**

- A palavra "excelente" para o alarme de 1 mês, se entendida como "vence com significância todas as regras
  simples de comparação", **não tem respaldo**: o teste de McNemar com correção de Holm não fecha nem
  contra a regra "hoje já passou de 100" (p = **0,103**) nem contra "o mesmo período do ano passado
  passou de 100" (p = **1,000**) em h=4.
- Em h=12 (3 meses), o modelo **empata** com a regra "o ano passado passou de 100": Youden do modelo entre
  0,66 e 0,78 contra 0,81 da regra, com p de Holm de 0,845 e 1,000 — nenhuma vantagem estatística.
- No estágio de gravidade mais alto testado com evento próprio ("Alerta", mais de 421 casos por semana,
  o limiar oficial do plano municipal, seção 9.7), **nenhuma das 4 combinações testadas em 26/09/2026**
  supera a regra "o ano passado" com significância.

**Reescrita defensável (a usar no seminário, exatamente como está em
`analises/2026-09-26_banca_adversarial/README.md`):**

> "O modelo é bem calibrado em calmaria — o intervalo de 90% cobre 90,5% das 814 semanas calmas — e, a 1
> mês, vence a régua climatológica com significância (WIS, p<0,0001). Contra o calendário do ano passado, o
> efeito aponta a favor mas a amostra ainda não fecha estatisticamente; tratamos isso como resultado em
> aberto, não como vitória geral."

A seção 9.4 detalha por que essas duas comparações (o alarme binário contra as duas réguas, e o WIS contra
a régua climatológica) chegam a conclusões diferentes, sem que isso seja uma contradição.

### 9.3.2 Argumento 2 (A2)

> "Reconhecemos que o modelo subestima sistematicamente a magnitude dos grandes picos epidémicos. Testámos
> as correções matemáticas padrão para a variância (raiz e logaritmo), mas provámos que elas pioram a
> previsão."

**O que a evidência sustenta:**

- A subestimação sistemática dos picos é um **FATO medido**: a **captura do pico** (uma métrica que diz
  que fração do valor máximo de um episódio de surto o modelo consegue captar em sua previsão) em h=12 é
  de **0,388** — o modelo, em média, prevê cerca de **39% da magnitude real** nas semanas de pico. Um
  exemplo concreto: na semana em que os casos reais chegaram a **917** (mediana da faixa "Alerta ou
  mais"), o erro mediano do modelo foi de **539 casos**, o que corresponde a uma previsão de cerca de
  **378 casos** — 41% do valor real, na mesma ordem de grandeza dos 39% medidos pela métrica de captura do
  pico.
- A cobertura dos intervalos de confiança **piora nas quatro faixas de gravidade testadas, sem exceção,
  inclusive na calmaria**, ao aplicar as duas transformações testadas (raiz quadrada e logaritmo): na
  calmaria, a cobertura do intervalo de 90% cai de **90,5%** (sem transformação) para **84,2%** (raiz) e
  **80,5%** (log) — certificado adversarialmente e aprovado em 26/09/2026 (`analises/2026-09-26_transformacao_de_escala/`).
- Uma alternativa diferente, a **calibração conformal** (uma técnica que ajusta a largura dos intervalos
  depois de o modelo já ter sido treinado, para forçar a cobertura observada a bater com a cobertura
  prometida), piora ainda mais o problema pelo lado prático: a cobertura sobe de 50% para 78%, mas o
  número de **falsos alarmes dispara de 15 para 124** por ano — a "correção" resolve a calibração e
  destrói a utilidade do alarme.

**O que a evidência NÃO sustenta:**

- A palavra "provámos" generaliza demais: só **2** transformações foram testadas (raiz quadrada e
  logaritmo), de uma família bem maior de técnicas para lidar com variância crescente (Box-Cox
  generalizada — uma família de transformações que inclui a raiz e o log como casos particulares —,
  transformação de Anscombe, perdas específicas para contagens como Tweedie ou binomial-negativa, e
  calibração conformal por regime de gravidade). Dizer "as correções matemáticas padrão... pioram" sugere
  que o catálogo inteiro foi varrido; só uma fração foi.
- A frase omite uma **exceção real**: em h=4, o erro absoluto médio **melhora** com a transformação raiz
  quadrada, caindo de 219,7 para **205,0** (uma redução de **6,7%**). É um resultado que não pode ser
  escondido só porque atrapalha a narrativa — é exatamente o tipo de seletividade que um revisor de banca
  identificaria e citaria contra o trabalho.

**Reescrita defensável:**

> "Confirmamos subestimação sistemática dos picos — a previsão captura em média 39% da magnitude real nas
> semanas de surto. Testamos, com pré-declaração e certificação adversarial, raiz e logaritmo: as duas
> pioraram a cobertura nas quatro faixas de gravidade, inclusive na calmaria. A única exceção é uma
> melhora pontual de erro em 1 mês, que não compensa a perda de calibração nos extremos."

### 9.3.3 Argumento 3 (A3)

> "O problema não é um defeito de código ou configuração. É uma limitação dos dados históricos, uma vez
> que a série temporal possui apenas 2 epidemias registadas. Nenhum algoritmo de machine learning consegue
> aprender as dinâmicas de eventos extremos apenas com 2 exemplos."

**O que a evidência sustenta:**

- A busca por uma configuração melhor foi ampla, dentro das famílias de modelo testadas: **120**
  configurações sorteadas (60 de HistGB, a sigla de *Histogram-based Gradient Boosting*, um algoritmo de
  aprendizado supervisionado que constrói uma sequência de árvores de decisão simples, cada uma corrigindo
  o erro da anterior — esse processo se chama **boosting** —, agrupando valores contínuos em
  compartimentos de tamanho fixo para acelerar o treino; e 60 de **LightGBM**, uma implementação
  concorrente do mesmo princípio de boosting, com uma estratégia diferente de construir as árvores), mais
  **9 algoritmos** distintos no grid de 30/08/2026, mais **2 modelos de fundação** (Chronos-2 e
  Chronos-Bolt, dois modelos de série temporal pré-treinados em milhões de séries de diferentes domínios,
  usados aqui sem re-treino, chamados de uso "zero-shot"), mais **SARIMA** (um modelo estatístico clássico
  de série temporal que combina autorregressão, integração e médias móveis, com componente sazonal) e
  **LASSO** (um modelo de regressão linear com uma penalidade que zera coeficientes pouco úteis), mais
  **6 formulações diferentes de alvo** — e **nenhum** superou a régua sazonal (definida na seção 9.7) em
  eventos extremos.
- Os modelos de fundação zero-shot também perderam para a régua: Chronos-2 teve **MAE de 227,2** em h=12,
  pior que a régua sazonal (**217,8** na mesma janela de avaliação) — o que reforça que o problema não é
  falta de ajuste fino de hiperparâmetros, já que esses modelos não usam hiperparâmetros ajustados ao
  problema.
- A série de casos confirmados de dengue em Porto Alegre, na janela usada para avaliação, tem de fato
  apenas **2 epidemias documentadas** (2024 e 2025) — **FATO medido em 26/09/2026**: olhando 121 semanas
  desde 2024 e definindo "surto" pelo limiar de 100 casos por semana, há **39 semanas** acima do limiar,
  mas elas formam apenas **2 blocos contíguos** (um bloco = uma sequência de semanas seguidas todas acima
  do limiar), o maior com **20 semanas**. O mesmo padrão de 2 blocos aparece nos limiares mais altos (140,
  421 e 702 casos por semana).

**O que a evidência NÃO sustenta:**

- A frase "nenhum algoritmo de machine learning consegue aprender" é uma **alegação teórica universal, não
  testada por este experimento** — é a leitura mais arriscada, segundo o parecer do revisor de aprendizado
  de máquina simulado. O que foi medido é que **nenhuma das arquiteturas testadas neste projeto** venceu a
  régua; isso não prova nada sobre arquiteturas nunca tentadas (por exemplo, a teoria de valores extremos,
  detalhada na seção 9.9, ou modelos mecanicistas epidemiológicos).
- A frase reduz a causa a uma só (poucos exemplos de epidemia), quando há uma **segunda causa concorrente**
  e igualmente plausível: a **ausência de variáveis-chave** — sorotipo do vírus da dengue circulante (a
  dengue tem 4 sorotipos, e a imunidade de um não protege totalmente contra os outros), nível de imunidade
  já acumulada na população, e mobilidade das pessoas — nenhuma dessas está entre as **20 colunas de
  entrada** do cenário adotado (8 de núcleo sobre casos e sazonalidade, 6 de clima, 6 do vetor mosquito).
  Faltam exemplos **e** faltam variáveis; a frase original menciona só a primeira causa.
- A configuração vencedora da busca de hiperparâmetros (a melhor entre as 120 testadas, chamada aqui de
  **LGB_best**, com nota 160,95, taxa de aprendizado 0,022, 177 árvores, 49 folhas por árvore, folha
  mínima de 10 observações, usando 92% das colunas disponíveis e 81% das semanas de treino a cada rodada,
  com a técnica **extra_trees**, que sorteia os pontos de corte das árvores em vez de otimizá-los, para
  reduzir sobreajuste) foi selecionada **e avaliada dentro da mesma janela de tempo** (2022-2025). Mesmo
  com esse viés a favor dela, ainda perdeu para a régua sazonal (**239,6** contra **226,8** em h=12). Mais
  grave: essa busca inteira rodou numa versão da tabela de dados que **ainda incluía 2026** — dado que foi
  **excluído da avaliação por decisão do Vinicius em 26/09/2026**, porque prever um ano com apenas 19
  casos confirmados até então distorce qualquer métrica de erro. **Esse número precisa ser recalculado
  antes de ser citado com autoridade perante a banca.**

**Reescrita defensável:**

> "Testamos 120 configurações de boosting, 9 algoritmos, 2 modelos de fundação zero-shot, SARIMA, LASSO e
> 6 formulações de alvo — nenhum superou a régua sazonal em eventos extremos. Isso é consistente com uma
> série de apenas duas epidemias documentadas, somada à ausência de sorotipo, imunidade e mobilidade como
> atributos. É limitação de dados para as arquiteturas testadas — não afirmamos que nenhum algoritmo, em
> tese, poderia aprender com dois exemplos."

---

## 9.4 A distinção que salva o A1: dois comparadores, duas métricas

O ponto mais delicado desta seção — e o que mais precisa ficar claro numa apresentação oral, porque é fácil
de confundir sob pressão de perguntas — é que o A1 **não é sustentado pelo alarme binário**. Ele é
sustentado pelo **escore de intervalo ponderado (WIS)**. São coisas diferentes, comparadas contra coisas
diferentes:

| | Comparador | O que ele é | Métrica usada | Resultado |
|---|---|---|---|---|
| ❌ **Não sustenta** "excelente" | Regra binária **"hoje já passou de 100"** ou **"o ano passado passou de 100"** | Uma regra que olha só se um número específico (o valor de hoje, ou o mesmo período do ano passado) já cruzou o limiar de 100 casos — dispara ou não dispara, sem grau | Teste de McNemar com correção de Holm (seção 9.2.6), sobre o alarme binário | p de Holm = **0,103** (h=4, contra "hoje já passou") e **1,000** (h=4, contra "o ano passado") — nenhum significativo |
| ✅ **Sustenta** | **Régua climatológica** | Uma previsão que usa, para cada semana do ano, os quantis (seção 9.2.3) do número de casos que aconteceram naquela mesma semana do calendário epidemiológico, em anos anteriores — é a régua probabilística oficial usada nos sprints brasileiros de previsão | WIS (seção 9.2.4), a métrica oficial dos mesmos sprints | p de Holm **< 0,0001** (h=4) — significativo |

A diferença entre "hoje já passou de 100" / "o ano passado passou de 100" e a "régua climatológica" é que
as duas primeiras são regras **binárias e pontuais** (usam um único número de referência e uma decisão de
sim/não), enquanto a régua climatológica é uma previsão **probabilística e contínua** (dá uma distribuição
inteira de valores plausíveis para cada semana, baseada em vários anos de histórico da mesma época do
ano). O alarme binário testa "quem acerta mais vezes se um limiar foi cruzado". O WIS testa "de quem é a
distribuição de probabilidade mais bem calibrada e mais estreita, considerando o valor real observado". São
perguntas diferentes, e por isso os resultados podem — e neste caso realmente divergem — apontar em
direções diferentes sem se contradizerem.

**A frase honesta e forte, que resume esta seção:** avaliado pela métrica oficial dos sprints brasileiros,
o modelo vence a régua climatológica em 1 mês com **p < 0,0001**. Isso é verdadeiro, é relevante, e **não
depende** do resultado do alarme binário — que continua sendo um resultado em aberto, não uma vitória.

---

## 9.5 Um erro apanhado dentro da própria banca simulada — e a regra que ele gerou

Durante a produção da banca adversarial em 26/09/2026, um dos quatro pareceres simulados (o do
"epidemiologista") cometeu, ele mesmo, o erro que o exercício inteiro existe para prevenir. Na parte do
parecer que ataca os argumentos, o mesmo texto registra corretamente que, em 3 meses (h=12), o modelo
**não vence** a regra "o ano passado passou de 100" com significância. Mas, mais adiante, na parte do
mesmo parecer que tenta escrever uma versão "seguramente defensável" do argumento, o texto afirma que em 1
mês o modelo supera **"com significância tanto 'esperar o surto' quanto a régua sazonal"** — o que é
**falso**: os p de Holm em h=4, contra essas duas regras, são **0,103** e **1,000**, ambos acima do limiar
de 0,05.

Esse deslize foi identificado e registrado no adendo final do README da banca adversarial, com a
conferência independente do arquivo `mcnemar_holm.csv` de 25/09/2026 confirmando os dois p-valores citados
acima. Ele importa por dois motivos:

- **A redação incorreta não pode ser usada em lugar nenhum deste documento ou dos slides do seminário.**
  As três frases válidas são as reescritas da seção 9.3, produzidas sem propagar esse erro.
- **É evidência concreta de que o número "Youden 0,94 contra 0,84" convida ao erro.** Um avaliador com o
  número correto (o p de Holm de 0,103) disponível na mesma página escorregou e escreveu "com
  significância" de qualquer forma. Numa banca real, com a plateia lendo depressa e sob pressão de tempo,
  o mesmo escorregão pode acontecer de novo — inclusive pelo próprio Vinicius, sob a pressão de responder
  a uma pergunta em tempo real.

**Regra que decorre disso, sem exceção:** toda vez que a sensibilidade de **97,1%** (ou o Youden de
**0,94**) do alarme em h=4 aparecer em qualquer slide, texto ou fala deste projeto, ela vem sempre
acompanhada da ressalva "não testado contra as réguas simples com significância estatística". A frase de
efeito não pode circular sozinha.

---

## 9.6 As cinco perguntas mais difíceis que a banca faria

### Pergunta 1 — "Se o teste de McNemar não fecha em h=4 contra as duas réguas (p = 0,103 e p = 1,000), com que direito vocês dizem que o alarme é 'excelente'?"

**Resposta ancorada:** não dizemos mais que o alarme "vence com significância" as réguas binárias. Dizemos
que, pela métrica oficial dos sprints (o WIS), o modelo vence a régua climatológica com **p < 0,0001**, e
que, no alarme binário, o efeito aponta a favor do modelo sob uma amostra pequena (**13 vitórias em 15**
semanas discordantes), mas essa amostra não é grande o bastante para declarar significância. As duas
afirmações — "vence pelo WIS" e "não fecha estatisticamente pelo alarme binário" — coexistem sem
contradição, pela razão detalhada na seção 9.4.

### Pergunta 2 — "Se 'o mesmo período do ano passado passou de 100' empata com o modelo em 3 meses (Youden 0,81 contra 0,66-0,78), qual é o valor incremental de todo esse modelo além de 1 mês?"

**Resposta ancorada:** o ganho comprovado do modelo em 3 meses existe **só** contra a régua mais fraca
("hoje já passou de 100", p de Holm = **0,00062**, significativo). Contra a régua mais forte ("o ano
passado passou de 100"), em 3 meses o resultado é um **empate estatístico** (p de Holm entre 0,845 e
1,000) — não uma vitória. O valor incremental do modelo além de 1 mês, hoje, **é um resultado em aberto**,
não uma vitória a ser anunciada.

### Pergunta 3 — "Por que a teoria de valores extremos (as distribuições GEV e GPD, desenhadas exatamente para eventos raros) nunca foi testada neste projeto?"

**Resposta ancorada:** porque, até 26/09/2026, o esforço de busca foi direcionado às famílias de modelo já
citadas (**120** configurações de boosting, **9** algoritmos no grid geral, **2** modelos de fundação,
SARIMA e LASSO) — nenhuma delas é desenhada especificamente para a cauda extrema de uma distribuição. É
precisamente por essa lacuna que a frase do A3 foi ajustada de "nenhum algoritmo de machine learning
consegue aprender" para "nenhuma das arquiteturas testadas venceu a régua" — a teoria de valores extremos
é detalhada na seção 9.9 como o próximo passo mais citável, e ainda **não** foi tentada.

### Pergunta 4 — "Se só 2 de um número muito maior de transformações de variância foram testadas, como afirmar que 'as correções matemáticas padrão pioram a previsão'?"

**Resposta ancorada:** a frase, na sua versão final (seção 9.3.2), já não usa mais a palavra "padrão" de
forma genérica — ela nomeia exatamente as duas transformações testadas (raiz quadrada e logaritmo) e
reporta que ambas pioraram a cobertura dos intervalos nas **4 faixas de gravidade**, sem exceção. Fica
declarado, na seção 9.7, que uma família maior de transformações (Box-Cox generalizada, Anscombe, perdas
Tweedie ou binomial-negativa) segue sem testar — é uma limitação nomeada, não uma alegação escondida.

### Pergunta 5 — "A configuração vencedora da busca de hiperparâmetros foi escolhida e avaliada dentro do mesmo período de tempo (2022-2025) — esse resultado não é otimista?"

**Resposta ancorada:** sim, é um viés de seleção conhecido e reconhecido (escolher a melhor entre 120
opções, testando todas no mesmo período em que foram escolhidas, tende a superestimar o desempenho da
vencedora). Mesmo com esse viés jogando a favor da configuração vencedora, ela **ainda perdeu** para a
régua sazonal (**239,6** contra **226,8** em h=12). Além disso, essa busca inteira rodou numa tabela de
dados que incluía o ano de 2026 — hoje excluído da avaliação por decisão de 26/09/2026 — então o número
precisa ser **recalculado na tabela corrigida** antes de ser citado como resultado definitivo perante a
banca.

---

## 9.7 Limitações — todas, nomeadas e quantificadas

Esta seção lista **todas** as limitações conhecidas do trabalho até 26/09/2026. Cada uma é um fato
quantificado, não uma frase de cautela genérica.

**1. A série tem apenas 2 blocos contíguos de semanas de surto, em qualquer limiar testado.**
Definindo "bloco contíguo" como uma sequência ininterrupta de semanas todas acima de um limiar de
gravidade, e olhando as 121 semanas avaliadas desde 2024: no limiar de 100 casos por semana há **39**
semanas acima do limiar, mas formando só **2 blocos** (o maior com **20 semanas**, 1 bloco em 2024 e 1 em
2025). O mesmo padrão de exatamente 2 blocos se repete nos limiares de 140, 421 e 702 casos por semana.
Isso significa que, para qualquer método que precise "aprender" como é uma epidemia inteira do começo ao
fim, existem literalmente **2 exemplos completos** disponíveis — não 39 exemplos independentes, porque
semanas dentro do mesmo bloco são fortemente parecidas entre si (autocorrelacionadas, seção 9.2.6).

**2. Ausência de sorotipo circulante, imunidade populacional acumulada e mobilidade como variáveis de entrada.**
Nenhuma das **20 colunas de entrada** do cenário adotado (8 de núcleo, 6 de clima, 6 do vetor mosquito)
captura qual sorotipo do vírus da dengue está circulando, quanto da população já teve dengue recentemente
(o que reduziria o número de pessoas suscetíveis a um novo surto do mesmo sorotipo) ou como as pessoas se
movimentam pela cidade. As três são reconhecidas na literatura epidemiológica como determinantes de
quando e onde uma epidemia de dengue acelera. Essa ausência é uma limitação **concorrente** com a de
poucos exemplos de epidemia (limitação 1) — as duas competem como explicação para por que o modelo
subestima picos, e a evidência atual não separa qual pesa mais.

**3. A seleção das 6 colunas de clima foi feita fora da janela deslizante (o *walk-forward*).**
A escolha de quais 6 variáveis climáticas entram no modelo foi feita usando a série inteira de uma vez, em
vez de ser refeita a cada origem de previsão do *walk-forward* (o método descrito na seção 9.2.1, que
corta o treino sempre pela data da resposta). Isso significa que a informação usada para escolher as 6
colunas pode ter "visto" dados que, numa previsão real feita no passado, ainda não existiam — um risco de
vazamento de informação do futuro para o passado (chamado de vazamento temporal, o mesmo tipo de problema
já corrigido uma vez neste projeto, ver limitação 8). Além disso, o **ranking dessas colunas é instável e
depende de qual alvo se está prevendo** — trocar o alvo muda quais 6 colunas parecem melhores, o que é sinal
de que a seleção não é robusta.

**4. O corte de maturidade das armadilhas (12 semanas) é um valor único, fixo, calculado uma vez.**
As armadilhas do MI-Aedes levam tempo entre a instalação e a primeira contagem confiável de mosquitos —
chamado aqui de "maturidade". O projeto usa um corte fixo de **12 semanas** para considerar uma armadilha
madura. Medido em 2025, a mediana real do tempo de maturidade foi de **10,4 semanas** (abaixo do corte,
como esperado), mas o percentil 90 (o valor abaixo do qual ficam 90% das armadilhas, ou seja, 10% delas
demoram mais que isso) foi de **31,6 semanas** — quase o triplo do corte adotado. Isso significa que, para
uma fração não desprezível das armadilhas, o corte de 12 semanas as classifica como "maduras" antes que
elas de fato estejam produzindo contagens estáveis, e essa fração não é re-medida rotina a rotina — o
corte foi calculado uma única vez e nunca revisitado dinamicamente.

**5. O critério de gravidade usado no projeto simplifica o critério oficial do plano municipal.**
O Plano Municipal de Contingência de Arboviroses 2026 nunca usa um limiar numérico sozinho: o estágio
"Epidemia", por exemplo, exige, no texto literal do plano, estar "acima do Limite Superior Endêmico nas
últimas 4 semanas epidemiológicas **E** taxa de incidência de casos confirmados acima de 50,0 em pelo
menos uma das 4 semanas epidemiológicas" — uma condição **composta**, ligada por "E", não um só número.
Este projeto usa, por simplicidade e para lidar com uma série curta (ver limitação sobre o canal
endêmico, seção 9.9), só a parte numérica sozinha (100, 140, 421 ou 702 casos por semana), sem a condição
adicional sobre o Limite Superior Endêmico (uma média móvel da incidência de casos prováveis do Rio Grande
do Sul inteiro, somada a dois desvios padrão). Isso significa que o desempenho medido do alarme, neste
documento, **não é uma réplica exata** do critério que a Prefeitura de fato usaria para decretar cada
estágio.

**6. A raspagem semanal dos dados do vetor é manual, e o portal MI-Aedes só expõe a semana corrente.**
Não existe automação hoje para capturar os dados de armadilhas toda semana. Como o portal público só
mostra a semana em curso (não um histórico consultável depois), **pular uma semana de raspagem significa
perder aquele dado para sempre** — não há como recuperá-lo depois. Essa é uma limitação operacional, não
estatística, mas com consequência irreversível.

**7. A busca de 120 configurações de hiperparâmetros rodou numa tabela que ainda incluía o ano de 2026.**
Como já detalhado na seção 9.3.3 e na Pergunta 5 da seção 9.6, os números da "configuração vencedora"
(LGB_best, nota 160,95) foram calculados antes da decisão de 26/09/2026 de excluir 2026 da avaliação. O
resultado qualitativo (perde para a régua sazonal) provavelmente se mantém, mas o número exato **precisa
ser recalculado** antes de ser citado com autoridade.

---

## 9.8 O que este trabalho fez que a maioria dos estudos da área não faz

É importante que esta lista não fique subvendida atrás da autocrítica da seção anterior — ela é, ela
própria, parte do argumento de valor do trabalho:

- **Vazamento temporal identificado e quantificado.** Em 13/09/2026, foi encontrado que o treino do
  modelo estava sendo cortado pela data da **pergunta** feita, não pela data em que a **resposta**
  (o número real de casos) ficaria disponível — um erro que deixa o modelo "ver" informação do futuro
  durante o treino. O custo desse erro foi medido, não estimado: **+52% de erro** (MAE) em h=12, com o
  coeficiente de determinação (R², seção 9.2.2) caindo de **0,758** para **0,437** depois da correção.
  **152 células** de resultado tiveram que ser re-executadas.
- **Pré-declaração escrita antes de cada rodada nova de teste**, com hipótese, métrica e critério de
  decisão fixados antes de rodar qualquer número — prática que impede reinterpretar um resultado depois de
  vê-lo.
- **Certificação adversarial por agente independente** em toda mudança de dado ou de pipeline: um segundo
  agente, sem acesso ao código original, tenta **reprovar** o resultado, remedindo do zero, em vez de só
  confirmar que o teste passou.
- **Comparação sistemática contra réguas triviais** (persistência, régua sazonal, régua climatológica,
  "o ano passado passou do limiar") em vez de comparar o modelo só contra si mesmo ou contra outras
  variantes de modelo.
- **Correção de comparações múltiplas** (Holm) em toda família de testes de hipótese, o que é
  frequentemente omitido na literatura da área, inflando a aparência de significância.
- **Resultados negativos publicados no documento vivo do projeto**, em vez de escondidos: o vazamento
  encontrado, a perda para a régua sazonal em 3 meses, o vetor mosquito piorando o alarme em 26/09/2026 —
  todos registrados com a mesma proeminência dos resultados positivos.
- **Uma série de 14 anos de captura de mosquitos resgatada e certificada contra uma fonte independente**
  (a base da pesquisadora Marília, usada como validação cruzada), em vez de usar só os anos mais recentes
  e convenientes.

---

## 9.9 Próximos passos, do mais barato ao mais caro

**Barato (dias, reaproveita pipeline já certificado):**

- **Testar uma família mais ampla de transformações de variância**, além das 2 já testadas (raiz e
  log): a família Box-Cox generalizada (uma família matemática que inclui a raiz quadrada e o logaritmo
  como casos particulares, com um parâmetro ajustável entre eles), a transformação de Anscombe (desenhada
  especificamente para estabilizar a variância de contagens) e perdas específicas para dados de contagem,
  como a família Tweedie ou a binomial-negativa.
- **Re-rodar a busca de 120 configurações de hiperparâmetros sem a contaminação de 2026** — o script já
  existe; é reexecução, não desenho novo.

**Médio (poucos dias a semanas, framework estatístico conhecido mas não usado ainda):**

- **Teoria de valores extremos: as distribuições GEV (distribuição generalizada de valores extremos) e
  GPD (distribuição generalizada de Pareto).** Esta é a lacuna mais citável do trabalho, porque o
  argumento central do A3 é exatamente sobre a raridade dos eventos extremos, e essa é a família
  estatística desenhada especificamente para modelar raridade.

  A **GEV** modela o **máximo** de um bloco de observações (por exemplo, o pico de casos de cada ano), com
  a função de distribuição acumulada:

  ```
  G(x; μ, σ, ξ) = exp{ −[1 + ξ·(x−μ)/σ]^(−1/ξ) },  para 1 + ξ·(x−μ)/σ > 0
  ```

  onde **μ** é um parâmetro de posição (onde o máximo típico se concentra), **σ** é um parâmetro de escala
  (o quanto o máximo varia de bloco para bloco) e **ξ** (a letra grega csi) é o parâmetro de forma, que
  decide se a cauda da distribuição é limitada, exponencial ou pesada (permite valores extremos muito além
  do já observado).

  A **GPD** modela, em vez do máximo de um bloco inteiro, cada **excedência** acima de um limiar alto
  **u** já escolhido (essa abordagem se chama de "picos acima do limiar", em inglês *peaks over
  threshold*):

  ```
  H(y; σ, ξ) = 1 − (1 + ξ·y/σ)^(−1/ξ),  onde y = x − u > 0
  ```

  **Por que essas ferramentas ainda não foram tentadas, e por que a lacuna é honesta, não só uma
  formalidade a marcar como feita:** um ajuste clássico da GEV por blocos exigiria vários **blocos
  independentes** (tipicamente, vários anos, cada um contribuindo um máximo) para estimar com confiança os
  três parâmetros (μ, σ, ξ). Este projeto tem, como já quantificado na limitação 1 da seção 9.7, apenas
  **2 blocos contíguos de epidemia** — o mesmo problema de poucos exemplos que afeta os modelos de
  aprendizado de máquina afetaria também um ajuste ingênuo de GEV por blocos anuais. A GPD é, em teoria,
  mais promissora aqui, porque não precisa de blocos anuais inteiros — ela pode usar cada uma das **39
  semanas** que já ultrapassaram o limiar de 100 casos como uma excedência individual. Mas essas 39 semanas
  vêm de só **2 episódios contíguos**, e são fortemente autocorrelacionadas entre si (seção 9.2.6); um
  ajuste correto de GPD exigiria primeiro "desagrupar" essas excedências (uma técnica chamada
  *declustering*, que mantém só uma excedência representativa por episódio, para não contar a mesma
  epidemia várias vezes como se fossem eventos independentes) — o que reduziria a amostra efetiva de volta
  para perto de **2** pontos. Ainda assim, vale tentar e reportar o resultado, mesmo que a conclusão seja
  "os dados atuais não bastam nem para a ferramenta certa" — essa seria, ela mesma, uma resposta mais
  rigorosa que a frase original do A3.

- **Modelos mecanicistas de dinâmica epidêmica (SIR/SEIR):** uma família de modelos que não aprende
  padrões a partir de exemplos históricos, mas simula diretamente como uma epidemia se espalha, dividindo a
  população em compartimentos (Suscetíveis, Expostos, Infecciosos, Recuperados — daí as siglas SIR e SEIR)
  e movendo pessoas entre eles segundo taxas de transmissão e recuperação. Exige estimar parâmetros
  epidemiológicos específicos da dengue em Porto Alegre (por exemplo, o número básico de reprodução R0, e
  uma estimativa do tamanho da população suscetível a cada sorotipo) — trabalho estimado em **1 a 2
  semanas**.

**Caro (depende de acesso a dado ou colaboração externa que hoje não existe):**

- **Transferência de aprendizado (*transfer learning*) a partir de outra cidade com mais epidemias
  documentadas**, para injetar exemplos de eventos extremos que Porto Alegre não tem na própria série. Isso
  exige acesso a uma base comparável de outra cidade — por exemplo, no mesmo formato usado pelo estudo de
  da Silva et al. 2026, mas de um lugar diferente de Porto Alegre, já que aquele estudo é sobre a mesma
  cidade.
- **As variáveis ausentes da limitação 2 (sorotipo circulante, imunidade populacional, mobilidade), e o
  vírus no próprio mosquito em 2026** dependeriam de dado novo e não público hoje. Esse caminho já foi
  avaliado e **descartado por decisão do Vinicius em 25/09/2026**, porque exigiria solicitar dado
  adicional à Secretaria Municipal de Saúde de Porto Alegre — uma dependência fora do controle do projeto
  no prazo do mestrado. Fica registrada como **limitação declarada**, não como lacuna a fechar agora.
