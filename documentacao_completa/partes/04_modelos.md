# Parte 4 — Todos os modelos e abordagens testados

Esta parte é o catálogo completo de tudo o que já foi treinado, calculado ou comparado neste projeto para
prever casos de dengue em Porto Alegre. Cada item traz, na mesma ordem: o que a técnica é, para quem nunca
ouviu falar dela; como ela funciona por dentro, em termos conceituais; por que o projeto a testou; os
hiperparâmetros exatos usados (um **hiperparâmetro** é um ajuste do algoritmo que a pessoa que modela
escolhe **antes** de treinar — como a profundidade máxima de uma árvore de decisão — e que não é aprendido
a partir dos dados, ao contrário dos parâmetros internos do modelo); o resultado numérico medido; e o
veredito.

Um termo aparece em todo este catálogo e vale a pena fixar já: **série temporal** é um conjunto de medidas
da mesma variável, ordenadas no tempo — aqui, o número de casos confirmados de dengue em Porto Alegre, uma
medida por semana, desde 18/02/2018. Prever uma série temporal é usar o passado dela (e de outras séries
relacionadas, como o clima e a densidade de mosquitos) para estimar um valor futuro ainda não observado.

Outro termo recorrente é **walk-forward**: a forma de testar um modelo de série temporal sem trapacear. Em
vez de misturar semanas passadas e futuras num treino só, o walk-forward treina o modelo apenas com o que
já tinha acontecido até um certo ponto, pede uma previsão para a semana seguinte (ou h semanas à frente),
anota o erro, avança o relógio uma semana e repete o processo — retreinando o modelo a cada passo. É a
simulação mais próxima possível de como o modelo seria usado de verdade, semana a semana, por alguém
fazendo vigilância epidemiológica hoje.

---

## 4.1 O cenário adotado — HistGradientBoosting com perda quantílica

### (a) O que é

O **cenário adotado** é a configuração de modelo que o projeto usa como referência principal desde
13/09/2026, depois da correção do vazamento temporal descrita na Parte 5. Ele é construído sobre o
`HistGradientBoostingRegressor`, um algoritmo de **árvore de decisão em conjunto** (em inglês, *ensemble of
decision trees*) da biblioteca scikit-learn.

Uma **árvore de decisão** é uma sequência de perguntas do tipo "a temperatura média da semana passada foi
maior que 22°C?" que divide os dados em grupos cada vez menores, até chegar numa "folha" — um grupo final
— ao qual se atribui um valor de previsão. Uma árvore sozinha costuma ser um previsor fraco e instável. A
técnica de **boosting** (em português, "reforço") junta muitas árvores pequenas em sequência, e cada árvore
nova é treinada para corrigir o erro que as árvores anteriores ainda deixaram. O resultado final é a soma
das contribuições de todas as árvores da sequência.

### (b) Como funciona por dentro

O `HistGradientBoostingRegressor` ("boosting de gradiente baseado em histogramas", daqui em diante
**HistGB**) é a implementação do scikit-learn inspirada no algoritmo LightGBM (ver §4.4): antes de treinar
qualquer árvore, ele agrupa os valores de cada variável de entrada em um número fixo de faixas (por padrão,
255 faixas, ou *bins*) e passa a trabalhar só com essas faixas, não com o valor contínuo original. Isso
torna o treino muito mais rápido, porque testar "esta faixa ou aquela" ao construir uma árvore é uma
comparação de inteiros pequenos, não de números decimais.

A cada rodada de boosting, o algoritmo calcula o **gradiente** — a direção e o tamanho do erro que uma
correção deveria ter, dado o objetivo escolhido — e treina uma nova árvore rasa para prever esse gradiente.
A soma de todas as árvores, multiplicada por uma taxa de aprendizagem pequena, forma a previsão final.

A peça que diferencia o cenário adotado de um HistGB comum é a **perda quantílica** (em inglês, *quantile
loss* ou *pinball loss*). Por padrão, um modelo de regressão é treinado para minimizar o erro quadrático
médio, o que faz o modelo aprender a prever a **média condicional** — o valor mais provável "no meio da
distribuição". A perda quantílica muda o objetivo: em vez de mirar a média, o modelo passa a mirar um
**quantil** específico da distribuição do alvo.

Um **quantil** é o valor abaixo do qual cai uma certa fração das observações. O quantil 0,50 (a mediana) é
o valor que separa a metade de baixo da metade de cima. O quantil 0,85, que é o usado neste projeto, é o
valor que **85% das observações ficam abaixo dele** — ou, visto de outro ângulo, é um patamar que a
realidade deveria ultrapassar em apenas 15% das semanas, se o modelo estivesse bem calibrado.

A fórmula da perda quantílica para um quantil $\tau$ (nesse projeto, $\tau = 0{,}85$) é:

```
L_τ(y, ŷ) = τ · (y − ŷ),         se y ≥ ŷ  (o modelo previu baixo demais)
L_τ(y, ŷ) = (1 − τ) · (ŷ − y),   se y < ŷ  (o modelo previu alto demais)
```

Onde:

- **y** é o valor real observado (o número de casos confirmados naquela semana);
- **ŷ** é o valor previsto pelo modelo (lê-se "y-chapéu");
- **τ** (a letra grega tau) é o quantil-alvo, um número entre 0 e 1.

**Exemplo numérico trabalhado.** Considere uma semana em que o modelo previu **ŷ = 250 casos** e o valor
real foi **y = 400 casos** (o modelo subestimou). Com $\tau = 0{,}85$:

```
y ≥ ŷ (400 ≥ 250), então:
L_0,85(400, 250) = 0,85 × (400 − 250) = 0,85 × 150 = 127,5
```

Agora considere a semana oposta: o modelo previu **ŷ = 250** e o valor real foi **y = 150** (o modelo
superestimou):

```
y < ŷ (150 < 250), então:
L_0,85(150, 250) = (1 − 0,85) × (250 − 150) = 0,15 × 100 = 15,0
```

**O que este exemplo revela:** para o mesmo tamanho de erro (150 casos, no primeiro caso; 100, no
segundo — mas mesmo se os dois fossem de 100 casos, o resultado seria o mesmo em proporção), a perda por
subestimar é **5,7 vezes maior** que a perda por superestimar (0,85 dividido por 0,15). O modelo é treinado
sob uma penalidade desenhada deliberadamente para ele preferir errar para cima: é mais barato, no critério
de treino, prever alto e a epidemia não vir do que prever baixo e a epidemia vir. Essa escolha reflete uma
**definição de produto** do projeto, não uma limitação técnica: quem decide o valor de $\tau$ está decidindo
quanto custa, na prática de vigilância, subestimar um surto.

⚠️ **RESSALVA — a previsão quantílica não estima a média nem "o valor mais provável".** Ela estima um
patamar que a realidade deve ultrapassar em 15% das semanas, por construção. Qualquer citação de um número
do cenário adotado como "a previsão do modelo", sem qualificar que é um quantil 0,85, está incompleta.

### (c) Por que foi testado

Até 30/08/2026 o projeto usava o LightGBM com a perda padrão porque era o algoritmo com que o projeto tinha
começado a trabalhar, sem nunca ter testado se essa era a melhor escolha disponível, nem se a função de
perda (o objetivo que o modelo tenta minimizar durante o treino) fazia diferença. O grid de 120 execuções
do dia 30/08/2026 (detalhado no §4.2) respondeu às duas perguntas ao mesmo tempo, testando 3 algoritmos × 5
funções de perda × com/sem colunas do vetor, em 4 horizontes de previsão.

### (d) Hiperparâmetros exatos

```python
HistGradientBoostingRegressor(
    max_iter=250,
    learning_rate=0.05,
    max_leaf_nodes=15,
    min_samples_leaf=5,
    random_state=42,
    loss="quantile",
    quantile=0.85,
)
```

- `max_iter=250` — o número de árvores (rodadas de boosting) que compõem o modelo final.
- `learning_rate=0.05` — a taxa de aprendizagem: cada árvore nova contribui só com 5% do seu gradiente
  calculado para a previsão final, o que torna o aprendizado mais lento e mais estável, evitando que uma
  única árvore distorça demais o resultado.
- `max_leaf_nodes=15` — o número máximo de folhas (grupos finais) que cada árvore pode ter. Controla o
  quão complexa cada árvore individual pode ficar.
- `min_samples_leaf=5` — o número mínimo de semanas de treino que precisam cair numa folha para ela ser
  aceita. Se uma divisão deixasse uma folha com menos de 5 semanas, essa divisão é descartada. Este
  hiperparâmetro é o assunto central do §4.3.
- `random_state=42` — a semente do gerador de números aleatórios internos do algoritmo (usada, por
  exemplo, para decidir a ordem de teste de variáveis empatadas). Fixá-la garante que rodar o mesmo código
  duas vezes produza exatamente o mesmo resultado — um requisito de **reprodutibilidade**.
- `loss="quantile"`, `quantile=0.85` — a função de perda quantílica descrita em (b), com $\tau = 0{,}85$.

O conjunto de entrada tem **20 colunas**: 8 de núcleo (o histórico da própria série de casos e variáveis de
sazonalidade, como o número da semana do ano), 6 de clima (temperatura, umidade, pressão e variáveis
correlatas, selecionadas por um processo próprio descrito na Parte 3) e 6 do vetor (a densidade de fêmeas
de *Aedes aegypti* por armadilha — a abreviação em inglês para o mosquito da dengue — e suas defasagens de
1 a 4 semanas, mais uma média móvel de 4 semanas). O alvo é o número de **casos confirmados** de dengue por
semana em Porto Alegre, contabilizados pelo **município de notificação** (o município onde o caso foi
registrado no sistema de saúde, que pode diferir do município de residência da pessoa).

### (e) Resultado numérico

Painel de erro na avaliação, de 01/01/2024 até aproximadamente 01/02/2026:

| Horizonte | Erro absoluto médio (MAE) | Coeficiente de determinação (R²) | Pares avaliados |
|---|---|---|---|
| 1 semana | **98,0** | **0,898** | **102** |
| 4 semanas | **219,7** | **0,628** | **102** |
| 8 semanas | **272,6** | **0,450** | **102** |
| 12 semanas | **278,8** (painel publicado: 278,7) | **0,437** | 284 |

O **erro absoluto médio** (em inglês, *mean absolute error*, abreviado **MAE**) é a média, em módulo, da
diferença entre o que o modelo previu e o que de fato aconteceu:

```
MAE = (1/n) × Σ |y_i − ŷ_i|
```

Onde **n** é o número de semanas avaliadas, **y_i** é o casos real da semana *i* e **ŷ_i** é o valor
previsto para ela. É uma média em **casos por semana** — a mesma unidade do alvo, o que o torna fácil de
interpretar.

**Tradução concreta do MAE de 278,8 em h=12 (previsão para 12 semanas, ou cerca de 3 meses, à frente).** Um
erro médio de 278,8 casos por semana equivale a, numa semana comum de calmaria (poucos casos), o modelo
errar por um múltiplo de tudo o que de fato aconteceu — mas numa semana de pico como a de 30/03/2025, que
teve **2.381 casos** (a maior da série), um erro de 278,8 seria menos de 12% do valor real. O MAE é uma
**média**: ele mistura semanas fáceis de calmaria, onde o erro é de poucos casos, com semanas de epidemia,
onde o erro chega a centenas ou milhares. A Parte 8 detalha essa mistura por faixa de intensidade.

O **coeficiente de determinação** (**R²**, lê-se "erre ao quadrado") mede que fração da variação do valor
real o modelo consegue explicar, numa escala de 0 (o modelo não explica nada, e prever a média histórica
seria igual de bom) a 1 (o modelo acerta perfeitamente todas as semanas):

```
R² = 1 − [ Σ(y_i − ŷ_i)² / Σ(y_i − ȳ)² ]
```

Onde **ȳ** (lê-se "y-barra") é a média de todos os valores reais no período avaliado, e o numerador e o
denominador são, respectivamente, a soma dos quadrados dos erros do modelo e a soma dos quadrados dos
desvios em torno da própria média da série.

**Exemplo numérico trabalhado, com números simplificados para caber em poucas linhas.** Suponha 4 semanas
com valores reais de 10, 400, 20 e 30 casos (média ȳ = 115). Um modelo que previu 15, 350, 25 e 40:

```
Σ(y_i − ŷ_i)² = (10−15)² + (400−350)² + (20−25)² + (30−40)²
              = 25 + 2.500 + 25 + 100 = 2.650

Σ(y_i − ȳ)²  = (10−115)² + (400−115)² + (20−115)² + (30−115)²
              = 11.025 + 81.225 + 9.025 + 7.225 = 108.500

R² = 1 − (2.650 / 108.500) = 1 − 0,0244 = 0,976
```

Um R² de 0,976 nesse exemplo quer dizer que o modelo explica 97,6% da variação da série — ele capturou o
salto grande (de 10 para 400) e errou pouco em proporção. **O R² de 0,437 medido em h=12 diz que o cenário
adotado explica 43,7% da variação em 3 meses** — os outros 56,3% da variação real das 12 semanas seguintes
não são explicados pelo que o modelo sabe hoje. É o R² caindo de 0,898 (h=1) para 0,437 (h=12) que sustenta
a frase "o modelo é honesto até um mês; em 3 meses, explica menos da metade".

### (f) Veredito

✅ **FATO (medido em 30/08/2026, corrigido em 13/09/2026).** O cenário adotado é a **melhor entre 30
configurações testadas** no grid de 30/08/2026 (ver §4.2), não a melhor configuração teoricamente
possível — essa distinção importa porque escolher a melhor entre 30 candidatas garante que parte da
vantagem observada é sorte de amostra, mesmo com a separação entre período de calibração (onde a escolha
foi feita) e período de avaliação (que nunca participou da escolha).

⚠️ **RESSALVA que atravessa todo este catálogo.** O cenário adotado perde para a régua sazonal — a regra
sem aprendizado de máquina descrita no §4.15 — em horizontes de 2 e 3 meses. Nenhum resultado deste
catálogo deve ser lido isoladamente do §4.15.

---

## 4.2 Os 9 algoritmos do grid de 30/08/2026

Antes de fixar o cenário adotado, o projeto comparou **9 algoritmos** de aprendizado de máquina no mesmo
experimento de regressão (a mesma tarefa: prever `casos` da cidade, mesmo conjunto de colunas de entrada,
mesmo corte temporal), para saber se o algoritmo escolhido fazia diferença. Cada algoritmo é apresentado a
seguir, na ordem em que aparece no código do projeto.

Uma observação de método vale para os 9: só **3 dos 9** conseguem ser treinados com a perda quantílica
descrita no §4.1 — `HistGradientBoostingRegressor`, `GradientBoostingRegressor` e o LightGBM — porque só
essas três implementações do scikit-learn e do LightGBM aceitam otimizar diretamente a perda pinball
(`loss="quantile"`). Os outros 6 algoritmos (`ExtraTreesRegressor`, `RandomForestRegressor`, `Ridge`,
`ElasticNet`, `SVR` e `KNeighborsRegressor`) **não têm essa opção embutida**: eles só sabem minimizar o erro
quadrático médio ou variantes dele. Essa não é uma limitação da configuração do projeto — é uma limitação
do próprio método desses algoritmos, e por isso só os 3 primeiros entraram no grid de 120 execuções com
perda quantílica do §4.1. Os 6 restantes foram comparados entre si com a perda padrão, num experimento
separado de comparação de algoritmos, cujos resultados aparecem ao final desta seção.

### 4.2.1 HistGradientBoostingRegressor (HistGB)

**(a) O que é.** Já apresentado em detalhe no §4.1 — a implementação de boosting de gradiente do
scikit-learn baseada em histogramas de 255 faixas por variável.

**(b) Como funciona.** Ver §4.1(b).

**(c) Por que foi testado.** Era um dos 3 candidatos capazes de perda quantílica, e o mais rápido dos três
por causa da discretização em histogramas.

**(d) Hiperparâmetros no grid, com a perda padrão** (antes da escolha do quantil 0,85):

```python
HistGradientBoostingRegressor(
    max_iter=250, learning_rate=0.05, max_leaf_nodes=15,
    min_samples_leaf=5, random_state=42,
)
```

**(e) Resultado.** No ranking das 30 configurações (critério: menor MAE médio no período de calibração, até
31/12/2023 — as 30 configurações são descritas no fim desta seção), a combinação **HistGB + perda
quantílica 0,80 + com colunas do vetor** ficou em 1º lugar (MAE de calibração 33,18); a variante com
$\tau=0{,}85$ ficou em 2º (33,85, a 2,0% de diferença) e acabou escolhida como cenário adotado porque, no
período de **avaliação** — que não participou da escolha —, tinha MAE menor (157,3 contra 158,3) e viés de
pico menor (−268 contra −305). ⚠️ Estes números de MAE (na casa das dezenas) são de uma rodada anterior à
correção do vazamento de 13/09/2026, medida sobre um recorte diferente do painel do §4.1; a ordem relativa
entre as 30 configurações é o que importa aqui, não o valor absoluto.

**(f) Veredito.** ✅ **FATO.** Junto com a escolha da perda quantílica, o HistGB é a base do cenário
adotado (§4.1).

### 4.2.2 GradientBoostingRegressor (GradBoost)

**(a) O que é.** A implementação "clássica" de boosting de gradiente do scikit-learn, anterior ao HistGB.
Também soma árvores em sequência para corrigir o gradiente do erro, mas **sem** a discretização em
histogramas: cada árvore é construída avaliando os valores contínuos originais das variáveis, o que a torna
mais lenta para treinar em bases grandes.

**(b) Como funciona.** Mesma lógica geral do boosting descrita em §4.1(b), mudando apenas o mecanismo
interno de construção de cada árvore (varredura de pontos de corte contínuos, em vez de faixas
pré-computadas).

**(c) Por que foi testado.** Era o segundo dos 3 algoritmos capazes de perda quantílica, e serve de
controle para saber se o ganho de velocidade do HistGB custa alguma coisa em qualidade de previsão.

**(d) Hiperparâmetros:**

```python
GradientBoostingRegressor(
    n_estimators=250, learning_rate=0.05, max_depth=3,
    min_samples_leaf=5, random_state=42,
)
```

Note que aqui o controle de complexidade da árvore é `max_depth=3` (profundidade máxima de 3 níveis de
perguntas), não `max_leaf_nodes` como no HistGB — os dois hiperparâmetros limitam o tamanho da árvore por
caminhos diferentes (profundidade contra número de folhas).

**(e) Resultado.** A melhor configuração de GradBoost (perda quantílica 0,70, com vetor) ficou em 4º lugar
no ranking das 30, a 4,0% do 1º colocado — dentro da faixa que o projeto considera empate técnico. Na perda
padrão, GradBoost também aparece entre os 3 melhores algoritmos (R² médio de calibração de 0,762), atrás
apenas do HistGB (0,779).

**(f) Veredito.** ✅ **FATO.** GradBoost é competitivo com o HistGB, mas nunca chegou a vencê-lo — fica
sempre no bloco das "três primeiras indistinguíveis" descrito no §4.2, nunca isolado em 1º.

### 4.2.3 LightGBM

Descrito em detalhe, com comparação arquitetural completa ao HistGB, no §4.4.

**(c) Por que foi testado no grid.** Era o algoritmo que o projeto usava desde o início, antes de qualquer
comparação sistemática — por isso precisava ser incluído como candidato, não como escolha automática.

**(e) Resultado no grid.** LightGBM ocupa as **10 últimas posições do ranking de 30**, incluindo o último
lugar (LightGBM, quantil 0,90, com vetor: MAE de calibração 53,65, a +61,7% do 1º colocado). Na perda
padrão, é o pior dos 3 candidatos a perda quantílica (R² médio de calibração 0,749, contra 0,779 do HistGB
e 0,762 do GradBoost).

**(f) Veredito.** 🚫 **REFUTADO como melhor algoritmo na calibração**, mas com uma reviravolta importante:
na avaliação (2024+), configurações de LightGBM às vezes lideram (ex.: LightGBM quantil 0,85 com vetor,
MAE de avaliação 156,9, o melhor de toda a tabela) — só que **pior na calibração**, o critério que decide.
🚫 **Trocar para LightGBM pelo desempenho na avaliação foi descartado em 30/08/2026**: usar o período que
serve de juiz para escolher a configuração invalida o próprio protocolo de separação entre calibração e
avaliação.

### 4.2.4 ExtraTreesRegressor (árvores extremamente aleatorizadas)

**(a) O que é.** Um método de **conjunto por agregação (*bagging*)**, e não de boosting: em vez de treinar
árvores em sequência para corrigir o erro umas das outras, o ExtraTrees treina **muitas árvores em
paralelo**, cada uma sobre uma amostra diferente dos dados, e a previsão final é a **média** das previsões
de todas as árvores.

**(b) Como funciona.** A palavra "extremamente aleatorizadas" descreve o que diferencia este algoritmo do
RandomForest (§4.2.5): ao decidir onde cortar uma variável dentro de uma árvore, o RandomForest testa
vários pontos de corte possíveis e escolhe o melhor; o ExtraTrees **sorteia** o ponto de corte, sem testar
qual seria o ótimo. Isso torna cada árvore individual mais fraca, mas mais rápida de treinar, e a
aleatoriedade extra tende a reduzir a tendência das árvores de "decorar" o ruído dos dados de treino (um
fenômeno chamado **sobreajuste**, ou *overfitting*, em que o modelo aprende padrões específicos do conjunto
de treino que não se repetem em dados novos).

**(c) Por que foi testado.** Fazia parte do conjunto de 9 algoritmos comparados na perda padrão, para
verificar se um método de agregação por médias (em vez de correção sequencial) se sairia melhor nesta série.

**(d) Hiperparâmetros:**

```python
ExtraTreesRegressor(
    n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=42,
)
```

`n_estimators=300` é o número de árvores no conjunto (mais que o dobro das 250 usadas nos boostings,
porque árvores de bagging tendem a precisar de mais unidades para estabilizar a média). `n_jobs=-1` diz
para usar todos os núcleos de processamento disponíveis, em paralelo — um detalhe de engenharia, não de
modelagem.

**(e) Resultado.** Não implementa perda quantílica, então não entrou no ranking de 30 configurações do
grid principal; participou apenas do experimento de comparação por perda padrão, onde ficou fora do topo
(os 3 melhores algoritmos na perda padrão foram HistGB, GradBoost e LightGBM, nessa ordem — ver §4.2.9
adiante).

**(f) Veredito.** 🚫 **REFUTADO como candidato principal** — não sustenta a perda quantílica que o cenário
adotado usa, e não superou os 3 algoritmos de boosting na perda padrão.

### 4.2.5 RandomForestRegressor (floresta aleatória)

**(a) O que é.** Também um método de bagging: muitas árvores treinadas em paralelo, cada uma sobre uma
amostra com reposição dos dados de treino (uma técnica chamada *bootstrap*, que sorteia linhas do
treino permitindo repetição), e a previsão final é a média das árvores.

**(b) Como funciona.** Diferente do ExtraTrees, o RandomForest testa de fato os pontos de corte candidatos
em cada variável e escolhe o que mais reduz o erro, em vez de sortear — o que o torna mais lento de treinar
que o ExtraTrees, mas potencialmente mais preciso por árvore individual.

**(c) Por que foi testado.** Foi o primeiro algoritmo alternativo ao LightGBM que o projeto comparou, antes
mesmo do grid de 9 algoritmos — um ponto de partida natural, por ser o método de conjunto mais conhecido
na literatura de aprendizado de máquina aplicada a epidemiologia (o artigo de Benedum et al. 2020, citado
na Parte 6, usa Random Forest como um dos concorrentes).

**(d) Hiperparâmetros:**

```python
RandomForestRegressor(
    n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=42,
)
```

**(e) Resultado.** Como o ExtraTrees, não implementa perda quantílica nativamente, e por isso ficou de fora
do grid de 30 configurações do §4.1. No comparativo de algoritmos com a perda padrão, teve desempenho
inferior aos 3 de boosting.

**(f) Veredito.** 🚫 **REFUTADO como candidato principal**, pela mesma razão do ExtraTrees.

### 4.2.6 Ridge (regressão linear com penalização L2)

**(a) O que é.** Uma **regressão linear**: um modelo que prevê o alvo como uma soma ponderada das
variáveis de entrada, `ŷ = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ`, onde cada `β` (a letra grega beta) é um
coeficiente aprendido a partir dos dados. O Ridge acrescenta uma **penalização L2**: durante o treino, o
algoritmo não só tenta minimizar o erro de previsão, mas também tenta manter os coeficientes `β` pequenos,
somando ao objetivo de treino um termo proporcional à soma dos quadrados dos coeficientes. Isso evita que
o modelo dê peso extremo demais a uma única variável.

**(b) Como funciona.** Quanto maior o hiperparâmetro `alpha`, mais forte a penalização, e mais os
coeficientes são "encolhidos" na direção de zero — mas, ao contrário do LASSO (§4.11), o Ridge nunca zera
um coeficiente por completo, só o reduz.

**(c) Por que foi testado.** Como controle mais simples: se um modelo linear com poucos ajustes já
capturasse a maior parte do sinal, isso seria evidência de que a relação entre as variáveis de entrada e os
casos é aproximadamente linear, e não precisaria da complexidade de uma árvore.

**(d) Hiperparâmetros:**

```python
Pipeline([
    ("escala", StandardScaler()),
    ("modelo", Ridge(alpha=10.0)),
])
```

Modelos lineares, ao contrário de árvores, são sensíveis à **escala** das variáveis — uma variável medida
em milhares (como o número de casos) e outra em unidades (como a densidade de mosquitos por armadilha)
distorceriam os coeficientes se entrassem cruas no modelo. Por isso o Ridge (e os outros três algoritmos
lineares/de distância descritos a seguir) é embrulhado num `Pipeline` que primeiro padroniza cada variável
com o `StandardScaler` (subtrai a média e divide pelo desvio-padrão, deixando todas as variáveis na mesma
escala) antes de treinar.

**(e) Resultado.** Não entrou no ranking de 30 do grid principal (sem perda quantílica); no comparativo de
algoritmos por perda padrão, ficou atrás dos métodos de árvore.

**(f) Veredito.** 🚫 **REFUTADO como candidato principal.** A relação entre as variáveis de entrada e os
casos não é suficientemente linear para que um modelo desta família vença as árvores de boosting.

### 4.2.7 ElasticNet (regressão linear com penalização L1 + L2)

**(a) O que é.** Uma regressão linear que combina as duas penalizações: a L2 do Ridge (que encolhe
coeficientes) e a L1 do LASSO (que pode zerá-los por completo — ver a definição completa de penalização L1
no §4.11). O hiperparâmetro `l1_ratio` controla a mistura entre as duas.

**(b) Como funciona.** Com `l1_ratio=0.5`, a penalização usada neste projeto é metade L1, metade L2 — um
meio-termo entre "encolher todos os coeficientes" (Ridge puro) e "zerar os coeficientes menos úteis"
(LASSO puro).

**(c) Por que foi testado.** Como alternativa ao Ridge que também pudesse simplificar o modelo eliminando
variáveis pouco úteis, sem descartar de vez a penalização L2.

**(d) Hiperparâmetros:**

```python
Pipeline([
    ("escala", StandardScaler()),
    ("modelo", ElasticNet(alpha=1.0, l1_ratio=0.5, max_iter=5000, random_state=42)),
])
```

**(e) Resultado.** Mesma situação do Ridge: sem perda quantílica, fora do ranking de 30; atrás dos métodos
de árvore na comparação de algoritmos.

**(f) Veredito.** 🚫 **REFUTADO como candidato principal**, pela mesma razão do Ridge.

### 4.2.8 KNeighborsRegressor (K vizinhos mais próximos)

**(a) O que é.** Um algoritmo que **não treina um modelo no sentido tradicional**: ele simplesmente guarda
todos os dados de treino, e para prever uma semana nova, procura as **K semanas do passado mais parecidas**
(medindo distância entre os valores das variáveis de entrada, depois de padronizadas) e devolve uma média
(ou média ponderada) dos valores reais dessas K semanas vizinhas.

**(b) Como funciona.** Com `weights="distance"`, os vizinhos mais próximos pesam mais na média do que os
mais distantes — em vez de todos os K vizinhos contarem igual.

**(c) Por que foi testado.** Como método de referência simples e intuitivo: "o que aconteceu em semanas
parecidas com esta?" é uma pergunta que qualquer pessoa de vigilância entenderia sem explicação técnica.

**(d) Hiperparâmetros:**

```python
Pipeline([
    ("escala", StandardScaler()),
    ("modelo", KNeighborsRegressor(n_neighbors=7, weights="distance")),
])
```

`n_neighbors=7` diz que cada previsão é a média ponderada das 7 semanas de treino mais parecidas com a
semana que se quer prever.

**(e) Resultado.** Sem perda quantílica, fora do ranking de 30; atrás dos métodos de árvore na comparação
de algoritmos.

**(f) Veredito.** 🚫 **REFUTADO como candidato principal.**

### 4.2.9 SVR (máquina de vetores de suporte para regressão)

**(a) O que é.** Uma **máquina de vetores de suporte** (em inglês, *support vector machine*, SVM) adaptada
para regressão. A ideia original da SVM veio de classificação: encontrar a fronteira que separa duas
classes com a maior margem possível. Na versão de regressão (SVR), o algoritmo tenta encontrar uma função
que caiba dentro de um "tubo" de tolerância ao redor dos valores reais, penalizando só os pontos que ficam
fora desse tubo.

**(b) Como funciona.** Com o `kernel="rbf"` (função de base radial), o SVR não ajusta uma linha reta, mas
uma superfície flexível: ele transforma implicitamente as variáveis de entrada para um espaço de maior
dimensão, onde relações não lineares no espaço original podem virar relações mais simples. O hiperparâmetro
`epsilon` define a largura do tubo de tolerância (erros menores que ele não são penalizados); `C` controla
o quanto o algoritmo penaliza os pontos que caem fora do tubo — um `C` alto força o modelo a se ajustar
mais aos dados de treino.

**(c) Por que foi testado.** Como candidato não linear que não é baseado em árvores, para diversificar a
família de algoritmos comparados.

**(d) Hiperparâmetros:**

```python
Pipeline([
    ("escala", StandardScaler()),
    ("modelo", SVR(kernel="rbf", C=100.0, epsilon=1.0, gamma="scale")),
])
```

**(e) Resultado.** Sem perda quantílica, fora do ranking de 30; atrás dos métodos de árvore na comparação
de algoritmos.

**(f) Veredito.** 🚫 **REFUTADO como candidato principal.**

### O grid completo: 120 execuções, 30 configurações

Os 3 algoritmos capazes de perda quantílica (HistGB, GradBoost e LightGBM) foram cruzados com **5 funções
de perda** (padrão, e quantílica nos níveis 0,70 / 0,80 / 0,85 / 0,90) e **2 conjuntos de variáveis** (com e
sem as 6 colunas do vetor), formando **3 × 5 × 2 = 30 configurações**. Cada uma foi testada nos **4
horizontes** (1, 4, 8 e 12 semanas), totalizando **120 execuções de walk-forward**, todas concluídas sem
falha em 2h36min de processamento.

A escolha do vencedor usou o **menor MAE médio no período de calibração** (semanas-alvo até 31/12/2023); o
período de **avaliação** (2024 em diante) nunca participou da escolha e serviu só de juiz posterior — a
mesma separação de dados usada em todo o projeto para evitar que a escolha do modelo "veja" o período em
que depois vai ser julgada.

**Os três achados do grid, na ordem em que aparecem no registro original:**

1. **A função de perda importa mais que o algoritmo, na leitura original (revista depois).** Trocar do
   melhor para o pior dos 3 algoritmos custava +16,5% de MAE; trocar de perda quantílica para padrão, mesmo
   algoritmo, custava +20,2%. As 6 configurações de perda padrão ocuparam as posições 10 a 23 de 30 —
   nenhuma entrou no topo 9. ⚠️ **RESSALVA — esta leitura foi revisada em 13/09/2026** (Parte 5, §5.6):
   depois da correção do vazamento temporal, a ordem se inverteu (algoritmo +11,8% contra perda +9,9%), e
   o achado passou a ser rotulado **🚫 REFUTADO**, com a versão mais fraca "a perda tem efeito comparável
   ao do algoritmo, e depende dele" sobrevivendo como leitura válida.

2. **O vetor dominava o topo do ranking, mas sem comprovação estatística.** Oito das dez melhores
   configurações usavam as colunas do vetor; pareado nas mesmas 60 comparações (algoritmo × perda, com e
   sem vetor, nos 4 horizontes), o vetor vencia em 35 de 60, com ganho médio de MAE de +7,88. Nenhuma das
   60 comparações sobreviveu à correção de Holm (melhor p bruto de 0,0025, que virou 0,150 depois da
   correção — ver a definição da correção de Holm no §4.15). Por horizonte, o padrão era mais forte quanto
   maior o prazo: o vetor vencia em 0 de 15 comparações em 1 semana e em 15 de 15 em 3 meses — um padrão
   consistente, mas, sem sobreviver a Holm, **não comprovado**.

3. **As três primeiras configurações são estatisticamente indistinguíveis.** O pódio — HistGB com vetor,
   variando só o valor de $\tau$ entre 0,80, 0,85 e 0,70 — ficou a 2,0% e 3,6% de diferença entre si, dentro
   do limite de empate técnico que o projeto declarou. O melhor GradBoost, em 4º lugar, ficou a +4,0%,
   também dentro dessa faixa.

⚠️ **RESSALVA — a frase correta sobre o cenário adotado é "a melhor entre as 30 testadas, com as três
primeiras estatisticamente indistinguíveis", nunca "a melhor configuração possível".** Escolher a melhor
entre 30 concorrentes garante que parte da vantagem observada do vencedor vem de sorte de amostra — a
separação entre calibração e avaliação reduz esse risco, mas não o elimina.

---

## 4.3 HistGB com folha mínima 20 — e por que a folha mínima mudou tudo

### (a) O que é

Uma variante do mesmo algoritmo HistGB do §4.1, mudando **um único hiperparâmetro**: `min_samples_leaf`
(o número mínimo de semanas de treino que precisam cair em cada folha da árvore) passa de **5** para **20**.

### (b) Como funciona por dentro, e por que essa mudança é tão relevante

Uma folha de árvore com poucas semanas de treino (`min_samples_leaf=5`) pode se ajustar a padrões muito
específicos e raros — inclusive a ruído estatístico que não vai se repetir. Uma folha exigida a ter pelo
menos 20 semanas de treino é obrigada a **generalizar mais**: a previsão daquela folha passa a ser a média
de um grupo maior e mais heterogêneo de semanas passadas, o que suaviza previsões extremas.

Esse ajuste, sozinho, muda o comportamento do modelo em relação ao vetor. Com folha mínima **5** (o cenário
adotado), as colunas do vetor reduzem o erro de 3 meses (h=12) em apenas **+2,2%**, sem significância
estatística. Com folha mínima **20**, a mesma troca de colunas reduz o erro em **+12,3%**, com **p de Holm
0,015** — estatisticamente significativo. O mesmo padrão aparece, ainda mais forte, no LightGBM com folha
20: **+15,5%**, **p de Holm 0,0001**.

**A explicação testada, e não apenas hipotetizada:** com folhas maiores, o modelo perde a capacidade de
"decorar" padrões finos do histórico recente de casos e passa a depender mais de sinais mais estáveis, como
a densidade do vetor. É como comparar dois meteorologistas: um que decora a temperatura exata de cada dia
dos últimos 5 anos (folha 5, se ajusta a cada detalhe) e outro que só sabe a média de cada estação do ano
(folha 20, generaliza mais) — o segundo tende a usar melhor uma pista adicional relevante (o vetor) porque
não tem tantos outros detalhes competindo por atenção dentro do mesmo espaço de decisão.

### (c) Por que foi testado

Na madrugada de 24/09/2026, durante a bateria noturna sem supervisão (pedido do Vinicius às 20h de
23/09/2026: *"fazer testagens de possibilidades que possam nos ajudar a chegar em melhores resultados"*), o
bloco 5 dessa bateria notou que o LightGBM parecia aproveitar melhor o vetor que o HistGB do cenário
adotado. A pergunta natural era: **é o algoritmo (LightGBM em si) ou é um hiperparâmetro que o LightGBM já
usava por padrão** e o HistGB do cenário adotado, não? O bloco 6 investigou os hiperparâmetros do LightGBM
padrão do projeto e viu que seu `min_child_samples` (o equivalente do `min_samples_leaf`) já valia 5 —
igual ao HistGB. Isso não bateu com a hipótese "é a folha", até o bloco 7, pré-declarado só depois de ler os
blocos 5 e 6, isolar exatamente esse hiperparâmetro e confirmar que ele muda o resultado, sozinho, nos dois
algoritmos.

### (d) Hiperparâmetros exatos

```python
HistGradientBoostingRegressor(
    max_iter=250,
    learning_rate=0.05,
    max_leaf_nodes=15,
    min_samples_leaf=20,   # o único hiperparâmetro que muda em relação ao cenário adotado
    random_state=42,
    loss="quantile",
    quantile=0.85,
)
```

### (e) Resultado numérico

MAE na avaliação 2024+, 102 semanas pareadas por horizonte, comparado à régua sazonal e ao cenário adotado
(`referência`, folha 5):

| Horizonte | Cenário adotado (folha 5) | HistGB folha 20 | Régua sazonal |
|---|---|---|---|
| 1 semana | 98,0 | 133,6 | 202,1 |
| 4 semanas | 219,7 | **199,6** | 213,2 |
| 8 semanas | 272,6 | 223,2 | 216,2 |
| 12 semanas | 278,8 | **243,8** | 217,8 |

⚠️ **RESSALVA — esse efeito é carregado pela temporada de 2024.** Separando por ano, o vetor ajuda com
p < 0,01 em todos os horizontes longos em 2024; em 2025, só se repete com significância no LightGBM em 11 e
12 semanas, e em 8 semanas o efeito **inverte de sinal** nos dois algoritmos. O horizonte de 3 meses é o
mais robusto, mantendo a mesma direção nas duas temporadas — mas duas temporadas é uma amostra pequena
demais para fechar a questão.

Além disso, todas as 9 configurações com folha 20 testadas na bateria noturna ficam **~30% piores na
calibração** (2020-2023) e **~11-17% melhores na avaliação** (2024+) — um padrão que favorece
sistematicamente configurações que dependem de pouco histórico epidêmico, porque o walk-forward é
expansivo (o treino só cresce, nunca é substituído) e as primeiras epidemias da série (2022, 2023) tinham
poucas semanas epidêmicas anteriores para aprender com elas.

Na busca aleatória de hiperparâmetros de 25/09/2026 (§4.5) e na segunda bateria noturna de 25-26/09/2026, a
folha 20 apareceu de novo: julgada na temporada de 2026 (excluída da avaliação principal por decisão do
Vinicius em 26/09/2026, ver §4.15), o HistGB folha 20 errou **579** em 3 meses **com** vetor contra **315
sem** vetor, uma **inversão completa de sinal** em relação a 2024-2025 (p de Holm 0,0499).

### (f) Veredito

⚠️ **EXPLORATÓRIO.** O achado "com folha mínima 20, o vetor ajuda a prever 3 meses à frente" nasceu de uma
observação feita depois de ver os dados (não foi pré-declarado antes de qualquer rodada da noite), e o
próprio projeto já documentou uma inversão de sinal na temporada de 2026. 🚫 **Trocar a referência para a
folha 20 foi descartado em 30/08/2026**: no critério de calibração que decide a escolha do projeto, a folha
20 é sistematicamente pior, e trocar de configuração olhando o período de avaliação invalidaria o próprio
protocolo.

---

## 4.4 LightGBM — o que é, e como difere do HistGradientBoosting

### (a) O que é

**LightGBM** (a sigla vem de *Light Gradient Boosting Machine*, "máquina de boosting de gradiente leve") é
uma biblioteca de boosting de árvores desenvolvida pela Microsoft, publicada em 2017, e usada neste projeto
desde antes de qualquer comparação sistemática de algoritmos — era, simplesmente, "o que estava à mão"
quando o projeto começou.

### (b) Como funciona por dentro, e a diferença central com o HistGB

O LightGBM e o HistGB do scikit-learn (§4.1) compartilham a mesma ideia básica: boosting de árvores sobre
histogramas de valores discretizados, em vez de valores contínuos — o HistGB do scikit-learn foi, de fato,
**inspirado** no LightGBM. A diferença mais importante entre os dois está em **como cada árvore cresce**:

- O **HistGB** cresce as árvores **nível a nível** (em inglês, *level-wise*): todas as folhas de uma mesma
  profundidade são divididas antes de passar para a próxima profundidade, mantendo a árvore equilibrada em
  formato.
- O **LightGBM**, por padrão, cresce as árvores **folha a folha** (em inglês, *leaf-wise*): a cada passo, ele
  escolhe dividir a folha que mais reduz o erro, não importa a profundidade em que ela está. Isso costuma
  produzir árvores mais profundas e desbalanceadas, e pode reduzir o erro de treino mais rápido, mas também
  aumenta o risco de sobreajuste — decorar detalhes do treino que não se repetem.

O LightGBM também introduziu duas técnicas próprias para acelerar o treino em bases muito grandes:
**amostragem unilateral baseada em gradiente** (GOSS, do inglês *Gradient-based One-Side Sampling* — mantém
as observações com maior erro e descarta parte das que já estão bem previstas) e **empacotamento exclusivo
de variáveis** (EFB, do inglês *Exclusive Feature Bundling* — junta variáveis esparsas que raramente têm
valor não nulo ao mesmo tempo). Nenhuma das duas foi ativada explicitamente neste projeto (não aparecem nos
hiperparâmetros usados), então essas técnicas não influenciam os resultados aqui relatados — mas fazem
parte do que diferencia o LightGBM do HistGB por dentro.

### (c) Por que foi testado

Era o algoritmo de partida do projeto, então precisava ser incluído como um dos 3 candidatos a perda
quantílica no grid de 30/08/2026 (§4.2), para saber se continuar usando-o fazia sentido diante de
alternativas nunca testadas antes.

### (d) Hiperparâmetros

Configuração-base usada no projeto antes do grid, com perda padrão:

```python
LGBMRegressor(
    n_estimators=250,
    learning_rate=0.05,
    num_leaves=15,
    min_child_samples=5,
    verbose=-1,
    n_jobs=-1,
)
```

`num_leaves` é o equivalente do `max_leaf_nodes` do HistGB; `min_child_samples` é o equivalente do
`min_samples_leaf`. Os dois algoritmos foram configurados com valores nominalmente iguais (15 folhas, 5
amostras mínimas por folha) para tornar a comparação do grid o mais justa possível, mudando só o mecanismo
interno de crescimento da árvore.

### (e) Resultado numérico

No ranking de 30 configurações do grid de 30/08/2026, o LightGBM ocupa as **10 últimas posições**,
incluindo a última (quantil 0,90, com vetor: MAE de calibração 53,65, a +61,7% do 1º colocado). Na
avaliação (2024+), porém, algumas configurações de LightGBM saem na frente — a de quantil 0,85 com vetor
teve o **menor MAE de avaliação de toda a tabela de 30**, 156,9. Essa inversão (pior na calibração, melhor
na avaliação) é exatamente o padrão que levou o projeto a **não trocar** de algoritmo: usar o período de
avaliação para escolher inverteria o próprio protocolo que separa escolha de julgamento.

Fora do grid principal, o LightGBM reaparece em três frentes descritas em outras seções deste catálogo: na
folha mínima 20 (§4.3, onde o vetor passou a ajudar com significância), na busca aleatória de
hiperparâmetros (§4.5, onde produziu a configuração vencedora daquela busca) e no `linear_tree` (§4.6, sua
única variante capaz de extrapolar além do histórico de treino).

### (f) Veredito

🚫 **REFUTADO como melhor algoritmo no critério de calibração**, que é o que decide a escolha do projeto.
⚠️ **Aparece como o algoritmo mais sensível ao hiperparâmetro de folha mínima**, o que o torna o candidato
mais promissor para explorar em rodadas futuras que envolvam ajuste fino de hiperparâmetros — mas nenhuma
dessas explorações (§§4.5 a 4.7) produziu, até 26/09/2026, uma configuração que vencesse a régua sazonal em
3 meses.

---

## 4.5 A busca aleatória de 120 configurações de hiperparâmetros

### (a) O que é

Até 25/09/2026, o projeto só tinha testado hiperparâmetros de forma **manual e limitada**: 18 combinações,
variando 3 valores por vez (a folha mínima do §4.3 sendo o exemplo mais relevante). Uma **busca de
hiperparâmetros** é um processo sistemático para explorar um espaço muito maior de combinações possíveis,
sem testar todas (o que seria caro demais computacionalmente) nem confiar só na intuição de quem modela.

A **busca aleatória** (em inglês, *random search*) é uma dessas estratégias: em vez de testar toda
combinação possível numa grade fixa (o que se chama *grid search*, e que cresce exponencialmente com o
número de hiperparâmetros), a busca aleatória **sorteia** um número fixo de combinações dentro de faixas
predefinidas para cada hiperparâmetro, e escolhe a de melhor desempenho entre as sorteadas.

### (b) Como funciona por dentro, e por que 60 sorteios por família

A justificativa teórica para usar poucos sorteios e ainda assim ter uma boa chance de encontrar uma
configuração próxima da ótima vem do artigo de Bergstra e Bengio (2012), *Random Search for
Hyper-Parameter Optimization*. A lógica é a seguinte: se existe uma **fração γ** (a letra grega gama) do
espaço de configurações que é "boa" (por exemplo, os 5% melhores hiperparâmetros possíveis, γ = 0,05), a
probabilidade de que **pelo menos um** dos *n* sorteios independentes caia dentro dessa fração boa é:

```
P(pelo menos 1 sorteio bom em n tentativas) = 1 − (1 − γ)ⁿ
```

Onde:

- **γ** é a fração do espaço de busca considerada "boa" (aqui, 0,05, ou os 5% melhores);
- **n** é o número de sorteios independentes realizados.

**Exemplo numérico trabalhado, com γ = 0,05 (os 5% melhores) e n = 60 (o número usado no projeto):**

```
P(pelo menos 1 bom em 60) = 1 − (1 − 0,05)^60
                          = 1 − (0,95)^60
                          = 1 − 0,0461
                          = 0,9539
```

**O que este número significa:** com 60 sorteios aleatórios e independentes, há **95,4% de chance** de que
pelo menos uma das configurações sorteadas esteja entre as **5% melhores** de todo o espaço de busca —
mesmo sem nunca ter testado as outras 95% das combinações possíveis. É essa conta que justifica a escolha de
**60 sorteios por família de algoritmo** (60 para HistGB, 60 para LightGBM, 120 no total).

### (c) Por que foi testado

Depois que a formulação do alvo (§4.8), os modelos de fundação (§4.9) e o SARIMA/LASSO/ensemble (§§4.10 a
4.12) não produziram nenhuma configuração capaz de bater a régua sazonal em 3 meses, restava perguntar: será
que o problema é que **nenhum conjunto de hiperparâmetros testado até aqui** foi bom o suficiente, e uma
busca mais ampla encontraria um vencedor?

### (d) Hiperparâmetros exatos — os espaços de busca

A busca rodou com **semente 20260925** (para reprodutibilidade), na noite de 25/09/2026, em 12,6 minutos
com 8 processos em paralelo. Todas as 120 configurações usaram o quantil 0,85, as mesmas 20 colunas do
cenário adotado, `random_state=42` e 1 thread por execução.

**Espaço de busca do HistGB (60 sorteios):**

| Hiperparâmetro | Faixa sorteada |
|---|---|
| `learning_rate` | log-uniforme, de 0,01 a 0,2 |
| `max_iter` | inteiro, de 100 a 600 |
| `max_leaf_nodes` | inteiro, de 4 a 63 |
| `min_samples_leaf` | inteiro, de 5 a 60 |
| `l2_regularization` | 0 com 20% de chance; senão, log-uniforme de 0,001 a 10 |
| `max_features` | uniforme, de 0,4 a 1,0 (fração das colunas usada em cada árvore) |
| `max_depth` | um entre {sem limite, 3, 4, 6, 8} |

Uma faixa **log-uniforme** sorteia números de forma que a chance de cair em qualquer "ordem de grandeza"
dentro da faixa é igual — por exemplo, tão provável cair entre 0,01 e 0,1 quanto entre 0,1 e 1,0. Isso é
usado para hiperparâmetros como a taxa de aprendizagem, onde a diferença entre 0,01 e 0,02 costuma importar
mais que a diferença entre 0,11 e 0,12, mesmo que a distância numérica seja igual nos dois casos.

**Espaço de busca do LightGBM (60 sorteios):**

| Hiperparâmetro | Faixa sorteada |
|---|---|
| `learning_rate` | log-uniforme, de 0,01 a 0,2 |
| `n_estimators` | inteiro, de 100 a 600 |
| `num_leaves` | inteiro, de 4 a 63 |
| `min_child_samples` | inteiro, de 5 a 60 |
| `reg_lambda` | 0 com 20% de chance; senão, log-uniforme de 0,001 a 10 |
| `colsample_bytree` | uniforme, de 0,4 a 1,0 |
| `subsample` | uniforme, de 0,5 a 1,0, com reamostragem a cada árvore |
| `extra_trees` | falso ou verdadeiro (ativa o modo de corte sorteado, como no ExtraTrees do §4.2.4) |

**Critério de escolha da vencedora de cada família:** a nota de cada configuração sorteada é a **média do
MAE em 1 mês e 3 meses**, calculada só sobre os pares com data-alvo entre 01/01/2022 e 31/12/2025 — a
escolha nunca viu a temporada de 2026.

### (e) Resultado numérico

**As vencedoras, escolhidas em 2022-2025:**

| Família | Hiperparâmetros da vencedora | Nota (MAE médio de 1 e 3 meses) |
|---|---|---|
| **LightGBM** | taxa de aprendizagem 0,022 · 177 árvores · 49 folhas · folha mínima 10 · 92% das colunas · 81% das semanas por árvore · `extra_trees` ativado | **160,95** |
| **HistGB** | taxa de aprendizagem 0,197 · 239 árvores · 55 folhas · folha mínima 15 · 51% das colunas · profundidade máxima 8 | **161,74** |

**Julgadas na temporada de 2026** (16 semanas, de janeiro até 19/04/2026 — depois excluída da avaliação
oficial do projeto por decisão do Vinicius em 26/09/2026, porque nenhuma semana de 2026 passou de 3 casos
confirmados e prever um ano tão atípico não é uma tarefa justa para nenhum modelo):

| Modelo | MAE em 1 mês | MAE em 3 meses | Alarmes falsos em 3 meses (limiar 100 casos) | Maior previsão em 3 meses |
|---|---|---|---|---|
| Cenário adotado | 223,8 | 482,9 | 9 de 16 semanas | 1.117 |
| HistGB folha 20 | 601,0 | 579,0 | 11 | 1.299 |
| Vencedora HistGB | 350,1 | 439,7 | 10 | 1.211 |
| Vencedora LightGBM | 234,0 | 540,9 | 9 | 1.205 |
| LightGBM com folhas lineares | **94,2** | **201,6** | **16 de 16** | 208 |
| Régua "o ano passado" | 902,9 | 902,9 | 11 | 2.381 |

**Critério de aprovação:** MAE menor que o cenário adotado **e** menos alarmes falsos **e** p de Holm
menor que 0,05. **Nenhuma das 120 configurações passou.** O menor p de Holm obtido foi **0,17**.

Como registro complementar (não usado para escolher nada, porque a janela 2022-2025 já tinha entrado na
escolha das vencedoras): em 2024-2025, em 3 meses, a vencedora do LightGBM errou **239,6**, contra **293,3**
do cenário adotado, **254,1** do HistGB folha 20 e **226,8** da régua sazonal — **mesmo com a escolha a seu
favor, a vencedora da busca não bate a régua.**

### (f) Veredito

🚫 **REFUTADO como fonte de uma nova configuração de referência.** Depois de 120 sorteios sistemáticos em
dois algoritmos, com um espaço de busca amplo o suficiente para cobrir profundidade, regularização, taxa de
aprendizagem, número de árvores e proporção de colunas e de semanas usadas em cada árvore, **nenhuma
configuração venceu simultaneamente no erro, nos alarmes falsos e com significância estatística**. A
conclusão descritiva mais forte foi negativa: o ajuste de hiperparâmetros, sozinho, não resolve o problema
de fundo descrito no §4.15 — a régua sazonal continua invicta em 3 meses mesmo depois de uma busca ampla.

⚠️ **RESSALVA de janela.** Esta busca rodou numa versão da tabela de dados que ainda incluía a temporada de
2026, hoje excluída da avaliação oficial por decisão do Vinicius de 26/09/2026. Os números de julgamento em
2026 seguem válidos como registro histórico do que foi medido, mas qualquer citação precisa vir com essa
ressalva, e uma nova busca na tabela oficial (sem 2026) ainda não foi feita.

---

## 4.6 `linear_tree` — árvores com folhas lineares

### (a) O que é

`linear_tree` é um recurso do LightGBM (§4.4) que muda o que cada **folha** de uma árvore prevê. Numa árvore
comum (incluindo todas as descritas até aqui neste catálogo), cada folha prevê um **valor constante**: a
média (ou, no caso da perda quantílica, o quantil escolhido) das semanas de treino que caíram naquela
folha. Com `linear_tree=True`, cada folha, em vez de um valor fixo, ajusta uma **pequena regressão linear**
sobre as variáveis de entrada, usando só as semanas de treino que caíram ali.

### (b) Como funciona por dentro, e por que resolveria (em teoria) a não-extrapolação

Uma árvore comum tem um limite estrutural: ela **nunca consegue prever um valor maior que o máximo visto no
treino**, nem menor que o mínimo. Isso acontece porque a previsão de qualquer folha é sempre uma média (ou
quantil) de valores já observados — a árvore nunca "extrapola" para fora do intervalo do que já viu. Esse
foi, inclusive, um mecanismo já **testado e refutado** como causa da subestimação de picos (§4.1(c)): o teto
do treino, medido no cenário adotado, era 1.439 casos, e o pico médio real ficava em 829 — só 5 de 32 picos
ficavam acima desse teto, então a não-extrapolação não explicava a maior parte do viés.

Ainda assim, para os poucos casos em que o teto do treino é de fato ultrapassado (como picos maiores que
qualquer coisa vista antes — o caso de 2024, a primeira epidemia grande da série), uma árvore com folhas
lineares consegue, em teoria, **continuar a tendência** para além do que já foi observado, porque a
regressão linear dentro da folha pode, sim, produzir valores fora do intervalo de treino daquela folha,
seguindo a inclinação aprendida.

### (c) Por que foi testado

Era a hipótese com motivo mais forte da pré-declaração da busca de hiperparâmetros de 25/09/2026: se a
não-extrapolação fosse o gargalo, uma árvore que pudesse extrapolar deveria reduzir o erro nas semanas de
epidemia crescente — exatamente o padrão observado em 2024.

### (d) Hiperparâmetros exatos

`linear_tree=True` foi aplicado sobre a configuração **vencedora do LightGBM** na busca aleatória do §4.5
(taxa de aprendizagem 0,022, 177 árvores, 49 folhas, folha mínima 10, 92% das colunas, 81% das semanas), com
um hiperparâmetro adicional, `linear_lambda` (a penalização L2 sobre os coeficientes das regressões lineares
dentro de cada folha), escolhido entre {0,1 · 1 · 10} pelo mesmo critério de menor MAE médio em 1 e 3 meses
em 2022-2025.

### (e) Resultado numérico

Julgado na temporada de 2026 (16 semanas):

| Métrica | LightGBM com folhas lineares | Cenário adotado |
|---|---|---|
| MAE em 1 mês | **94,2** | 223,8 |
| MAE em 3 meses | **201,6** | 482,9 |
| Alarmes falsos em 3 meses, limiar de 100 casos | **16 de 16 semanas** | 9 de 16 |
| Maior previsão em 3 meses | 208 | 1.117 |

**A explicação do que aconteceu, medida e não hipotética:** as previsões do `linear_tree` ficaram sempre
entre aproximadamente 90 e 210 casos, o tempo todo — ele **não reagiu à calmaria** de 2026 (um ano com
apenas 19 casos confirmados no total), só previu valores moderados de forma praticamente constante. Como o
limiar de alarme do projeto é 100 casos, e as previsões desse modelo raramente ficam abaixo disso, ele
**disparou o alarme em todas as 16 semanas avaliadas** — inclusive nas semanas de calmaria absoluta, com 0
a 3 casos reais.

**Tradução concreta do que "16 de 16 alarmes falsos" significa na prática:** um sistema de vigilância que
seguisse esse modelo em 2026 estaria em estado de alerta de surto **toda semana**, mesmo quando a cidade
teve, ao todo, 19 casos confirmados no ano inteiro. É o equivalente a um detector de fumaça que soa mesmo
sem fogo, o tempo todo — tecnicamente ele "não perderia nenhum incêndio real", mas deixaria de servir para
qualquer decisão prática, porque ninguém consegue distinguir um alarme de verdade de um alarme de rotina.

### (f) Veredito

🚫 **REFUTADO como candidato viável**, apesar do MAE numérico ser o melhor de toda a busca de
hiperparâmetros. O erro baixo em 2026 não veio de o modelo ter entendido a calmaria: veio de ele **nunca
variar o suficiente** para reagir a ela ou a ela deixar de existir. Um alarme que dispara sempre não é um
alarme — é ruído constante, e o critério de decisão do projeto (MAE **e** poucos alarmes falsos **e**
significância) reprova essa configuração no segundo critério, independente do primeiro.

---

## 4.7 Restrição monotônica — o que seria, e por que foi impossível

### (a) O que é

Uma **restrição monotônica** é uma regra imposta ao algoritmo de boosting durante o treino: para uma
variável de entrada específica, a previsão **nunca pode diminuir** (restrição monotônica **crescente**) — ou
nunca pode aumentar (**decrescente**) — quando o valor daquela variável sobe, mantendo todas as outras
variáveis fixas. É uma forma de colocar um conhecimento de domínio (uma regra que se sabe verdadeira sobre
o mundo real) diretamente na estrutura do modelo, em vez de esperar que os dados a ensinem sozinhos.

### (b) Como funcionaria por dentro, em teoria

Sem restrição, uma árvore de boosting pode, em princípio, aprender relações contraintuitivas se o ruído dos
dados de treino sugerir isso por acaso — por exemplo, uma folha específica poderia (por coincidência
estatística) associar mais casos confirmados na semana de origem a uma previsão **menor** para 12 semanas à
frente, mesmo que isso não faça sentido epidemiológico. Uma restrição monotônica crescente sobre as colunas
de `casos` e do `vetor` forçaria a árvore, em cada divisão, a garantir que aumentar essas variáveis nunca
reduza a previsão final.

### (c) Por que foi testado

A hipótese com motivo, registrada na pré-declaração da busca aleatória de 25/09/2026, era que mais vetor e
mais casos hoje **nunca deveriam prever menos casos no futuro** — um limite de bom senso epidemiológico que
o modelo, sem essa restrição, não é obrigado a respeitar.

### (d) O que impediu o teste

`LightGBM 4.6`, a versão da biblioteca usada no projeto, **recusa** combinar restrições monotônicas com a
perda quantílica (`loss="quantile"`). A tentativa de configurar o braço `MONO` (a vencedora geral da busca,
HistGB ou LightGBM, com restrição monotônica crescente nas colunas de casos e de vetor) terminou em erro da
própria biblioteca, e a pré-declaração já previa esse desfecho: *"se o LightGBM não aceitar `linear_tree`
com perda quantílica, o braço é registrado como impossível, sem trocar a perda"* — a mesma regra se aplicou
à restrição monotônica.

### (e) Resultado numérico

Não há resultado numérico: o experimento não pôde ser executado com a configuração pré-declarada.

### (f) Veredito

🚫 **IMPOSSÍVEL, dado o método escolhido.** Esta não é uma **limitação de arquitetura do modelo** — o
conceito de restrição monotônica existe e funciona em outras bibliotecas e com outras funções de perda; é
uma **incompatibilidade de implementação** específica entre a versão 4.6 do LightGBM e a perda pinball. Uma
tentativa futura precisaria trocar de biblioteca (por exemplo, para o XGBoost, que suporta essa combinação
em algumas versões) ou de função de perda, e qualquer uma das duas mudanças alteraria o desenho do
experimento o suficiente para não ser mais um teste isolado deste hiperparâmetro.

---

## 4.8 As seis formulações de alvo — V1 a V6

### O que é uma "formulação de alvo", em geral

Até aqui, todos os modelos deste catálogo preveem diretamente o número de casos confirmados de uma semana
futura, `y_h` (casos na semana h passos à frente da origem da previsão). Uma **formulação de alvo**
diferente muda **o que o modelo aprende a prever**, mesmo usando o mesmo algoritmo por baixo — por exemplo,
prever o **logaritmo** dos casos, ou um **resíduo** (a diferença) em relação a um valor de referência, em
vez do valor bruto. A ideia por trás de reformular o alvo é dar ao modelo uma tarefa mais fácil de aprender,
mesmo que o resultado final, depois de desfazer a transformação, seja convertido de volta para casos.

Todas as seis variantes a seguir foram construídas sobre a mesma base — HistGB com folha mínima 20 e as
colunas do vetor (chamado `B0` nesta rodada, com MAE de 133,6 / 199,6 / 223,2 / 243,8 em h=1/4/8/12 na
avaliação) — mudando **apenas** a forma do alvo. A rodada foi pré-declarada em 25/09/2026, com três famílias
de teste (F1: a variante melhora o B0? F2: a variante bate a régua sazonal? F3: o vetor ainda vale dentro da
variante?), cada uma com correção de Holm sobre suas comparações.

### 4.8.1 V1 — `alvo_log`

**(a) O que é.** Em vez de treinar o modelo para prever `casos` diretamente, o V1 treina para prever
`log(casos + 1)` (o **logaritmo natural** do número de casos, mais 1 — a soma de 1 evita calcular o
logaritmo de zero, que não existe, já que semanas sem nenhum caso confirmado existem na série). A previsão
final é desfeita com a operação inversa, `exp(previsão) − 1`.

**(b) Como funciona.** O logaritmo comprime valores grandes muito mais do que valores pequenos: a distância
entre `log(10)` e `log(100)` é a mesma que entre `log(100)` e `log(1.000)` (ambas valem `log(10) ≈ 2,30`),
enquanto em escala bruta a primeira distância é 90 casos e a segunda é 900. Isso tende a dar menos peso, no
treino, aos erros absolutos grandes em semanas de epidemia, e mais peso relativo aos erros em semanas de
calmaria.

**(c) Por que foi testado.** Era uma das três ideias trazidas pela varredura de literatura de 25/09/2026
como caminho possível para melhorar a previsão em 3 meses.

**(d) Hiperparâmetros.** Mesma base HistGB folha 20 do B0, mudando só o alvo de treino para `log(casos+1)`.

**(e) Resultado numérico.** MAE na avaliação, já convertido de volta para casos: **174,4 / 205,8 / 251,0 /
267,9** em h=1/4/8/12 — em h=12, **9,9% pior** que o B0 (243,8). Separando por faixa de intensidade: nas
semanas com **menos de 100 casos**, o erro **caiu** de 26,4 (B0) para **13,4** (V1); nas semanas com **100
casos ou mais**, o erro **subiu** de 594,9 para **679,1**.

**Tradução concreta:** o V1 ficou melhor em prever a calmaria e pior em prever o pico — exatamente o
padrão que a compressão logarítmica deveria produzir, só que o custo no pico (que é a parte da previsão que
mais importa para vigilância de surto) superou o ganho na calmaria.

**(f) Veredito.** 🚫 **REFUTADO.** Não melhora o B0 com significância em nenhum horizonte, e não bate a
régua sazonal (217,8 em h=12).

### 4.8.2 V2 — `ancora_atributo`

**(a) O que é.** Acrescenta, como mais uma variável de entrada do modelo (não como alvo), o valor de casos
da **mesma semana-alvo do ano anterior** — chamado de "âncora" — dado diretamente ao modelo como uma coluna
extra.

**(b) Como funciona.** A hipótese era que a informação sazonal "chegava desalinhada" ao modelo: o lag de 52
semanas já usado como coluna de entrada é contado a partir da **semana de origem** (quando a previsão é
feita), enquanto a régua sazonal usa a semana **alvo** (a que está sendo prevista) do ano anterior — em
h=12, essas duas datas ficam a 12 semanas de distância uma da outra. O V2 dá ao modelo exatamente o número
que a régua usa, alinhado corretamente com o horizonte de previsão.

**(c) Por que foi testado.** Para testar diretamente a hipótese do desalinhamento, que era a explicação mais
citada no projeto para a régua sazonal vencer o modelo em horizontes longos.

**(d) Hiperparâmetros.** Mesma base B0, com uma coluna adicional `ancora` = casos confirmados na
data-alvo menos 52 semanas.

**(e) Resultado numérico.** MAE em h=12: **300,9**, **23,4% pior** que o B0 (243,8). O estrago concentra-se
em 2025 e 2026:

| Ano do alvo | B0 | V2 |
|---|---|---|
| 2024 | 322,3 | 354,1 |
| 2025 | 196,3 | 272,0 |
| 2026 | 30,7 | **122,6** |

Nas semanas com menos de 100 casos reais, o erro do V2 é **81,9**, contra **26,4** do B0 — mais de três
vezes maior.

**Tradução concreta:** dar ao modelo o número exato do ano anterior fez com que ele passasse a **esperar
uma temporada do mesmo tamanho da anterior**, mesmo em semanas que, de fato, ficaram calmas. É o equivalente
a um planejador de estoque que, tendo visto uma alta demanda em dezembro passado, encomenda o mesmo volume
todo dezembro seguinte, mesmo quando a demanda real daquele ano específico é baixa.

**(f) Veredito.** 🚫 **REFUTADO, e a hipótese motivadora caiu.** A informação sazonal alinhada não faltava:
dando-a ao modelo de forma explícita, ele piorou. **A explicação "a informação sazonal chega desalinhada"
foi refutada no mesmo dia em que foi levantada.**

### 4.8.3 V3 — `ancora_residuo`

**(a) O que é.** Muda o alvo de treino de "casos brutos" para um **resíduo multiplicativo**: em vez de
prever `casos_h`, o modelo prevê `log(casos_h / ancora)` — o quanto os casos futuros crescem ou encolhem em
relação à âncora (o valor do ano anterior). A previsão final é `ancora × exp(previsão)`.

**(b) Como funciona.** A lógica é: "aprenda a taxa de crescimento em relação ao ano passado, e eu multiplico
essa taxa pela âncora para chegar no valor absoluto". É uma abordagem comum em séries com forte
sazonalidade, onde às vezes é mais fácil prever a variação relativa do que o valor absoluto.

**(c) Por que foi testado.** Como uma segunda forma, mais direta, de incorporar a informação da régua
sazonal na própria estrutura do alvo, não apenas como atributo (como no V2).

**(d) Hiperparâmetros.** Mesma base B0, alvo de treino reformulado como descrito em (a).

**(e) Resultado numérico.** 🔴 **Explosão.** MAE em h=12: **824,0**, uma piora de **−238% em relação ao
B0** — o pior resultado de toda a bateria.

**Exemplo numérico trabalhado, reproduzido do zero pela certificação mecânica independente.** Na origem de
previsão referente à data-alvo de **23/03/2025**, a âncora (os casos confirmados na mesma semana de 2024)
era **1.109** — um valor **acima de qualquer âncora que o treino já tinha visto**, cujo máximo histórico até
ali era **879**. O modelo previu um resíduo de **2,25 em escala logarítmica**, o que corresponde a
`exp(2,25) ≈ 9,5` — ou seja, previu que os casos futuros seriam **9,5 vezes** a âncora. Multiplicando:

```
previsão final = ancora × exp(resíduo previsto)
               = 1.109 × 9,5
               ≈ 10.524 casos
```

O valor real observado naquela semana foi **1.801 casos**. O modelo previu quase **6 vezes** o valor real.
A certificação mecânica confirmou que o resíduo previsto de 2,25 estava no percentil 83 do histórico de
resíduos — **não era um valor anômalo isolado**; o problema nasceu do **produto** entre uma âncora já fora
da faixa vista no treino e um fator de crescimento típico, mas alto.

**(f) Veredito.** 🚫 **REFUTADO, com explosão catastrófica.** **Limitação de arquitetura identificada:**
qualquer formulação que **multiplique** uma âncora por um fator de crescimento aprendido herda a
instabilidade de uma série com apenas 4 temporadas epidêmicas na história — quando a âncora sai da faixa já
vista, o produto amplia o erro em vez de moderá-lo.

### 4.8.4 V4 — `crescimento_vetor`

**(a) O que é.** Acrescenta como atributo a **taxa de crescimento** da densidade do vetor nas semanas mais
recentes (a variação percentual da densidade de mosquitos entre a origem e algumas semanas antes dela), em
vez de dar ao modelo apenas os valores absolutos das defasagens.

**(b) Como funciona.** A hipótese era que a **velocidade** de crescimento do vetor (ele está subindo rápido?
devagar? caindo?) carregaria informação que os valores absolutos das defasagens, sozinhos, não capturam.

**(c) Por que foi testado.** Terceira ideia trazida pela varredura de literatura de 25/09/2026.

**(d) Hiperparâmetros.** Mesma base B0, com uma coluna adicional de taxa de crescimento do vetor.

**(e) Resultado numérico.** MAE em h=12: **245,5**, uma variação de **−0,7%** em relação ao B0 (243,8),
com p bruto de 0,86 — nenhum efeito detectável.

**(f) Veredito.** 🚫 **REFUTADO — sem efeito.** O modelo já extrai dos valores das defasagens (as 4 colunas
de densidade do vetor em semanas anteriores) o que a taxa de crescimento tentaria acrescentar; a informação
já estava lá, de forma implícita.

### 4.8.5 V5 — `linear_log`

**(a) O que é.** Uma **regressão linear quantílica**, sem penalização (`alpha=0`), treinada sobre o
logaritmo do alvo, usando as mesmas colunas do B0, incluindo os quatro lags de casos e a média móvel — todas
elas altamente correlacionadas entre si (o que se chama **colinearidade**: quando duas ou mais variáveis de
entrada carregam quase a mesma informação, tornando difícil para um modelo linear separar a contribuição de
cada uma).

**(b) Como funciona.** Uma regressão linear tenta encontrar um coeficiente para cada variável de entrada que
minimize o erro. Quando várias variáveis são quase idênticas entre si (como `casos` e seus lags de 1 a 4
semanas mais a média móvel — todas elas, essencialmente, "o número de casos há pouco tempo"), existem
**infinitas combinações de coeficientes** que produzem quase o mesmo ajuste no treino. Sem penalização
(sem regularização L1 ou L2, ver §4.11), o algoritmo pode escolher coeficientes **enormes e de sinais
opostos** entre essas variáveis colineares — eles se cancelam quase perfeitamente na maior parte dos casos,
mas quando uma semana foge levemente do padrão típico, esse cancelamento se desfaz e a soma explode.

**(c) Por que foi testado.** Pré-declarado como controle negativo: a pré-declaração já previa que a
ausência de penalização poderia causar explosão, e o teste serviria de comparação direta com o LASSO
(§4.11), que usa a mesma família de modelo **com** penalização L1.

**(d) Hiperparâmetros.** `alpha=0` (sem penalização), alvo em `log(casos_h + 1)`, mesmas 20 colunas do B0.

**(e) Resultado numérico.** 🔴 **Explosão.** MAE em h=8: **920,4**. Na certificação mecânica, na origem
referente à data-alvo de **21/04/2024**, o modelo previu **27.257,7 casos** (arredondado para **27.258** no
texto corrido), para uma semana que teve **1.855 casos reais** — quase **15 vezes** o valor real.

**Exemplo numérico trabalhado, ilustrando o mecanismo.** Suponha, de forma simplificada, que o modelo
aprendeu dois coeficientes grandes e opostos para duas colunas quase idênticas — `casos_lag1` (o valor de 1
semana atrás) com coeficiente `+50` e `casos_lag2` (2 semanas atrás) com coeficiente `−48`. Na maior parte
das semanas, `casos_lag1` e `casos_lag2` são parecidos (por exemplo, ambos 100), e a contribuição conjunta é
pequena: `50×100 − 48×100 = 200`. Mas numa semana em que a série sobe rápido (`casos_lag1=150`,
`casos_lag2=90`, uma diferença maior que o normal), a mesma conta dá `50×150 − 48×90 = 7.500 − 4.320 =
3.180` — mais de 15 vezes maior, mesmo com uma mudança modesta nos valores de entrada. É esse tipo de
amplificação, em escala logarítmica e com muito mais que duas colunas envolvidas, que produziu a previsão
de 27 mil casos.

**(f) Veredito.** 🚫 **REFUTADO, com explosão catastrófica — e o teste era um controle negativo
pré-declarado, não uma surpresa.** ⚠️ **RESSALVA — só o `alpha=0` foi testado aqui.** Um modelo linear
**com** penalização (que é exatamente o LASSO, §4.11) foi testado separadamente, em outra rodada.

### 4.8.6 V6 — `mistura`

**(a) O que é.** Uma combinação simples: a previsão final é a **média aritmética** entre a previsão do B0 e
o valor da régua sazonal, com peso de 50% para cada uma.

```
previsão_V6 = 0,5 × previsão_B0 + 0,5 × régua_sazonal
```

**(b) Como funciona.** Não há treino adicional: o V6 é calculado diretamente a partir de duas previsões já
existentes, sem ajustar nenhum parâmetro novo.

**(c) Por que foi testado.** Como a leitura mais direta da observação "a régua sazonal vence o modelo em 3
meses": se as duas previsões captam informações parcialmente diferentes, uma mistura das duas poderia
reduzir o erro de ambas.

**(d) Hiperparâmetros.** Nenhum — apenas o peso fixo de 50/50, sem otimização.

**(e) Resultado numérico.** MAE em h=12: **230,3**, uma melhora de **+5,5%** em relação ao B0 (243,8), sem
significância estatística (p bruto de 0,24). Por ano:

| Ano do alvo | B0 | V6 |
|---|---|---|
| 2022 | 119,2 | 116,4 |
| 2023 | 65,8 | 56,2 |
| 2024 | 322,3 | 301,4 |
| 2025 | 196,3 | 187,4 |

O V6 é melhor que o B0 em **quatro anos seguidos** — a única direção consistente entre as seis variantes —
mas ainda **perde para a régua sazonal pura** em h=12: **230,3 contra 217,8**.

**(f) Veredito.** ⚠️ **EXPLORATÓRIO, não confirmatório.** A melhora é consistente ano a ano, mas pequena e
sem significância estatística. **Leitura, não teste:** metade da régua já melhora o modelo; a régua inteira
seria melhor ainda — o modelo, em 3 meses, parece adicionar pouco ao que a régua sazonal já carrega
sozinha.

### Síntese das seis formulações

🚫 **FATO — nenhuma das seis variantes melhora o modelo com significância, e nenhuma bate a régua sazonal**
em h=12. As quatro comparações que sobreviveram à correção de Holm nesta bateria foram todas **pioras**: V3
em h=1, 8 e 12; V5 em h=8. A explicação "a informação sazonal chega desalinhada" foi levantada e refutada no
mesmo dia. O padrão que emerge, ainda como hipótese e não medido diretamente, é que **o limite parece ser de
dado, não de formulação**: com apenas 4 temporadas epidêmicas na história da série, e cada uma delas maior
que a anterior, nenhuma forma de apresentar esse histórico ao modelo ensina a antecipar o tamanho da
próxima epidemia.

---

## 4.9 Modelos de fundação para série temporal — Chronos-2 e Chronos-Bolt

### (a) O que é um modelo de fundação, e o que significa "zero-shot"

Um **modelo de fundação** (em inglês, *foundation model*) é um modelo de aprendizado profundo pré-treinado
em uma quantidade enorme de dados variados — no caso de modelos de fundação para séries temporais, milhões
de séries de áreas completamente diferentes: vendas de varejo, tráfego de rede, consumo de energia, outras
doenças, dados financeiros. A ideia é que, ao ver tantos padrões diferentes de como séries temporais se
comportam (tendências, sazonalidades, picos, quedas), o modelo aprende uma espécie de "conhecimento geral"
sobre como séries temporais costumam evoluir, que pode ser reaproveitado em uma série nova, nunca vista.

**Zero-shot** ("tiro zero", do inglês) é o modo de uso em que o modelo pré-treinado é aplicado a uma série
nova **sem nenhum ajuste adicional** — sem treinar, nem mesmo parcialmente, com os dados específicos do
projeto. O modelo recebe o histórico da série de Porto Alegre até a data de origem e devolve uma previsão,
usando apenas o que aprendeu com as outras séries do mundo todo.

**Chronos-Bolt** (publicado pela Amazon em novembro de 2024) e **Chronos-2** (publicado em outubro de 2025)
são duas versões de uma família de modelos de fundação para séries temporais, baseados na mesma arquitetura
de rede neural usada em modelos de linguagem (a arquitetura *transformer*, a mesma família de tecnologia por
trás de assistentes de conversação), adaptada para prever números em vez de palavras.

### (b) Como funciona por dentro, e os quatro braços testados

Nenhum dos dois modelos foi treinado ou ajustado com os dados deste projeto — cada previsão viu apenas a
série de casos (e, em alguns braços, de clima e vetor) de Porto Alegre, de 18/02/2018 **até a data de
origem** da previsão, nunca além dela.

| Braço | Modelo | O que ele recebe como entrada |
|---|---|---|
| `bolt_casos` | Chronos-Bolt (nov/2024) | só a série de casos |
| `c2_casos` | Chronos-2 (out/2025) | só a série de casos |
| `c2_casos_clima` | Chronos-2 | casos + temperatura média e máxima, umidade, pressão |
| `c2_casos_clima_vetor` | Chronos-2 | casos + clima + as colunas do vetor |

### (c) Por que foi testado

A régua sazonal (§4.15) já tinha vencido o cenário adotado, e as seis reformulações de alvo do §4.8 não
mudaram esse quadro. A hipótese era que o limite estivesse no **dado disponível**: com apenas 4 temporadas
epidêmicas na história, talvez nenhuma forma de reorganizar essa informação bastasse, mas um modelo que já
viu milhões de curvas de outras áreas pudesse trazer algum conhecimento externo relevante — por exemplo,
sobre como séries com crescimento explosivo costumam se comportar, mesmo sem nunca ter visto dengue.

### (d) Hiperparâmetros / configuração

Não há hiperparâmetros de treino no sentido tradicional (não há treino). A configuração relevante é o
**contexto** (o histórico visto por cada previsão, sempre terminando na origem, nunca ultrapassando-a) e o
**quantil de saída pedido**, 0,85, para manter a comparação coerente com o cenário adotado.

### (e) Resultado numérico

MAE do quantil 0,85, avaliação 2024+, 102 semanas pareadas por horizonte:

| Horizonte | `bolt_casos` | `c2_casos` | `c2_casos_clima` | `c2_casos_clima_vetor` | Cenário adotado (B0) | Régua sazonal |
|---|---|---|---|---|---|---|
| 1 semana | 144,4 | 193,6 | 208,1 | 207,5 | **133,6** | 202,1 |
| 4 semanas | 193,8 | 255,8 | 275,7 | 263,0 | **199,6** | 213,2 |
| 8 semanas | 274,7 | 256,1 | 269,8 | 252,7 | 223,2 | **216,2** |
| 12 semanas | 289,5 | **227,2** | 275,0 | 265,2 | 243,8 | **217,8** |

**Nenhum modelo de fundação bate a régua sazonal em h=12**: o melhor, `c2_casos` (Chronos-2, só com casos),
erra 227,2 contra 217,8 da régua — uma diferença pequena, mas na direção contrária. Comparado ao B0, o
`c2_casos` erra menos (227,2 contra 243,8), mas **sem significância** (p de Holm 0,88).

**O vetor ajuda o Chronos-2, com significância, quando combinado com clima:**

| Horizonte | Chronos-2 com clima, sem vetor | Chronos-2 com clima e vetor | Queda do erro | p de Holm |
|---|---|---|---|---|
| 1 semana | 208,1 | 207,5 | +0,3% | 0,44 |
| 4 semanas | 275,7 | 263,0 | **+4,6%** | **0,005** |
| 8 semanas | 269,8 | 252,7 | **+6,3%** | **0,007** |
| 12 semanas | 275,0 | 265,2 | **+3,6%** | **0,007** |

⚠️ **RESSALVA — esse efeito é da janela de avaliação, não geral.** Separando por ano, o vetor **atrapalha**
o Chronos-2 em 2022 (−4,2%) e 2023 (−2,6%), e **ajuda** em 2024 (+3,9%) e 2025 (+6,6%) — o mesmo padrão de
"o vetor vale mais nas temporadas maiores" já visto com a folha mínima 20 (§4.3).

**Leitura descritiva, não confirmatória — a mediana do Chronos-2 é forte em prazos curtos:**

| Horizonte | Mediana do `c2_casos` | Persistência | Régua sazonal |
|---|---|---|---|
| 1 semana | **67,0** | 83,3 | 202,1 |
| 4 semanas | **136,7** | 279,0 | 213,2 |
| 12 semanas | 261,8 | 697,5 | **217,8** |

A **mediana** (o quantil 0,50, sem o viés deliberado para cima da perda quantílica 0,85) do Chronos-2 bate
as duas regras simples com folga em 1 semana e em 1 mês. Essa é uma comparação **descritiva**: o cenário
adotado do projeto nunca foi medido na mediana, então essa comparação específica com ele não existe.

### (f) Veredito

🚫 **REFUTADO como substituto do cenário adotado, e a régua sazonal segue invicta em 3 meses** — agora
também contra um modelo que nunca viu os dados do projeto, mas já viu milhões de outras séries. ⚠️ **A
hipótese "o limite é de dado, não de algoritmo" ganha peso**: nem o conhecimento externo de um modelo de
fundação bateu a régua em 3 meses. **O padrão do vetor ajudando em temporadas grandes e atrapalhando em
temporadas pequenas aparece agora em três famílias de modelo diferentes** (HistGB folha 20, LightGBM folha
20, Chronos-2 com clima) — deixando de parecer um artefato isolado de um algoritmo específico e virando um
padrão que precisa de explicação.

---

## 4.10 SARIMA

### (a) O que é

**SARIMA** é a sigla, em inglês, para *Seasonal AutoRegressive Integrated Moving Average* — "médias móveis
integradas autorregressivas com sazonalidade". É uma família clássica de modelos estatísticos para séries
temporais, bem anterior ao aprendizado de máquina, que descreve o valor de uma série em função do seu
próprio passado.

Um modelo SARIMA é identificado por 6 números, escritos como SARIMA(p, d, q)(P, D, Q)ₛ:

- **p** — a ordem **autorregressiva** (AR): quantas semanas passadas entram diretamente na equação que
  prevê a semana atual.
- **d** — o número de **diferenciações** necessárias para tornar a série estacionária (uma série é
  **estacionária** quando sua média e sua variância não mudam sistematicamente ao longo do tempo — séries
  com tendência de crescimento não são estacionárias, e diferenciar, isto é, olhar a variação entre uma
  semana e a anterior em vez do valor bruto, costuma remover essa tendência).
- **q** — a ordem de **média móvel** (MA): quantos erros de previsão passados entram na equação.
- **P, D, Q** — as mesmas três ideias (autorregressão, diferenciação, média móvel), aplicadas à parte
  **sazonal** da série, isto é, à relação entre a semana atual e a mesma semana em ciclos anteriores.
- **s** — o período do ciclo sazonal (aqui, 52 semanas, um ano).

### (b) Como funciona por dentro, e a configuração usada

O modelo usado no projeto foi **SARIMA(2,0,0)(0,1,0)₅₂**, ajustado sobre `log(casos + 1)`, **sem
constante**. Em palavras: a parte não sazonal usa uma autorregressão de ordem 2 (`p=2`: a previsão de uma
semana depende diretamente dos valores das duas semanas anteriores, sem diferenciação, `d=0`, e sem
componente de média móvel, `q=0`); a parte sazonal aplica uma diferenciação de 52 semanas (`D=1`: o modelo
olha a variação entre o valor atual e o valor de 52 semanas atrás), sem termos autorregressivos ou de média
móvel sazonais adicionais.

**Em palavras mais simples:** este SARIMA específico é, na prática, **a régua sazonal (§4.15) mais uma
correção autorregressiva de curto prazo**. A diferenciação sazonal faz o modelo partir do valor "de 52
semanas atrás" (o mesmo número que a régua sazonal usa), e o termo AR(2) tenta corrigir esse ponto de
partida usando o desvio das duas semanas mais recentes em relação ao que se esperaria. Sem uma constante no
modelo, essa correção deveria, em teoria, **enfraquecer com o horizonte** e a previsão deveria convergir
para a própria régua sazonal, quanto mais semanas à frente se olhasse.

### (c) Por que foi testado

Um levantamento da literatura de modelos prontos para dengue (feito em 25/09/2026) apontou que SARIMA
venceu 16 outros modelos no pico de uma epidemia em um estudo (Johansson et al. 2019) e que um ARIMA (a
versão sem componente sazonal explícita) venceu Random Forest em 12 semanas em outro (Benedum et al. 2020).

### (d) Hiperparâmetros exatos

```
SARIMA(2, 0, 0)(0, 1, 0)_52, sem constante, ajustado em log(casos + 1)
```

Reajustado em **cada origem** de previsão, com a série de 18/02/2018 até a origem, sempre gerando uma
previsão de 12 passos à frente. O quantil 0,85 de saída foi calculado como
`exp(média_prevista + 1,0364 × erro-padrão_previsto) − 1`, onde **1,0364** é o valor da distribuição normal
padrão que deixa 85% de probabilidade abaixo dele (o quantil 0,85 de uma normal(0,1)) — a forma usual de
extrair um quantil de um modelo que, por padrão, só devolve uma previsão pontual e um intervalo de
confiança em torno dela.

### (e) Resultado numérico

MAE do quantil 0,85, avaliação 2024+: **531,2 / 1.164,7 / 1.965,2 / 1.971,0**, em h=1/4/8/12 — o pior
resultado, disparado, de toda esta rodada comparativa (para comparação, o cenário adotado erra 98,0 / 219,7
/ 272,6 / 278,8 nos mesmos horizontes).

**Por que explodiu, reproduzido do zero pela certificação independente, com diferença de 0,0%.** Na origem
de previsão de **04/02/2024**, com horizonte de 12 semanas, o modelo previu **43.423 casos**, para uma
semana que teve **1.347 casos reais** — mais de **32 vezes** o valor real. Os casos, naquele momento, tinham
saltado de 7 para 80 em 10 semanas — o começo exato da epidemia de 2024. O ajuste do modelo, feito com
aqueles dados, deu um coeficiente autorregressivo AR(1) de **0,635** e AR(2) de **0,310**, cuja soma,
**0,945**, fica muito perto de **1,0** — um valor conhecido em séries temporais como **raiz unitária**, o
limite em que a correção autorregressiva deixa de decair com o tempo e passa a se comportar quase como uma
tendência que se sustenta sozinha. Com o AR tão perto da raiz unitária, a correção **demora cerca de 12
semanas para decair pela metade** — exatamente o horizonte que estava sendo previsto, e por isso ela nunca
chega a convergir de volta para a régua, como a premissa original do teste supunha.

🔴 **Isto refuta uma premissa da própria pré-declaração do teste**, que dizia: *"sem constante, a correção
some com o horizonte e a previsão converge para a régua"*. Com o AR perto da raiz unitária, ela não
converge — o mecanismo assumido estava certo em geral, mas não neste caso específico, onde o ajuste captou
justamente o início de uma epidemia.

Além disso, entre 18 e 20 das 102 semanas de avaliação **falharam em convergir** (o algoritmo de otimização
não encontrou uma solução estável) e, como pré-declarado, essas semanas entraram na avaliação com o valor
da régua sazonal no lugar — o que significa que o SARIMA, mesmo com esse paraquedas, ainda produziu o pior
resultado da rodada.

### (f) Veredito

🚫 **REFUTADO, explode no começo de epidemia.** **Limitação de arquitetura, agora confirmada em quatro
modelos diferentes deste catálogo** (o V3 do §4.8.3, a regressão linear do V5, o SARIMA aqui e o LASSO do
§4.11 a seguir): **um modelo linear ou autorregressivo em escala logarítmica, sem mecanismo de saturação,
não é adequado para esta série.** Uma árvore de decisão não sofre desse problema porque suas folhas
**saturam**: elas nunca preveem além do intervalo de valores vistos no treino (a mesma propriedade que
motivou — sem sucesso — o `linear_tree` do §4.6).

---

## 4.11 LASSO / regressão quantílica linear com penalização L1

### (a) O que é

**LASSO** é a sigla, em inglês, para *Least Absolute Shrinkage and Selection Operator* — um método de
regressão linear com **penalização L1**. Regressão linear, como já descrito no §4.2.6, prevê o alvo como
soma ponderada das variáveis de entrada; a **penalização L1** soma, ao objetivo de treino, um termo
proporcional à soma dos **valores absolutos** dos coeficientes (diferente da penalização L2 do Ridge, que
soma os quadrados). Essa diferença aparentemente pequena tem uma consequência importante: a penalização L1
pode **zerar por completo** o coeficiente de uma variável, removendo-a efetivamente do modelo — o que a
penalização L2 nunca faz sozinha.

Neste projeto, o LASSO foi implementado como uma **regressão quantílica linear** (`QuantileRegressor` do
scikit-learn, com `quantile=0.85`), combinando a perda pinball do §4.1 com a penalização L1 — em vez do
LASSO clássico, que minimiza o erro quadrático.

### (b) Como funciona por dentro, e por que a penalização deveria evitar a explosão do V5

O V5 do §4.8.5 já mostrou o que acontece com uma regressão linear **sem** penalização, sobre colunas
colineares (variáveis que carregam quase a mesma informação, como os quatro lags de casos e a média móvel):
coeficientes gigantes e de sinais opostos, que se cancelam na maior parte do tempo e explodem quando uma
semana foge do padrão. A penalização L1 do LASSO existe justamente para impedir isso: ao punir a soma dos
valores absolutos dos coeficientes, o algoritmo é forçado a manter os coeficientes pequenos, e tende a
**escolher uma única variável entre um grupo de colineares** e zerar as outras, em vez de distribuir pesos
extremos e opostos entre todas elas.

### (c) Por que foi testado

O mesmo levantamento de literatura de 25/09/2026 apontou que um modelo LASSO, do artigo de Shi et al. (2016),
está **em produção em Singapura** e venceu um SARIMA em 12 semanas, com um erro percentual médio absoluto
(MAPE) de 24% contra 29%. Como a regressão linear sem penalização (V5) tinha explodido especificamente por
falta de penalização, o LASSO era o teste natural para saber se a mesma família de modelo, com a peça que
faltava, se comportaria melhor.

### (d) Hiperparâmetros exatos

```python
QuantileRegressor(quantile=0.85, solver="highs")
```

Aplicado sobre `log(casos_h + 1)` como alvo, com as colunas de casos e do vetor também em `log(x + 1)`, e
padronização (`StandardScaler`) ajustada **só no treino** de cada corte de walk-forward — nunca usando
estatísticas de semanas futuras para padronizar. Dois braços foram testados: `lasso` (com as 20 colunas do
cenário adotado, incluindo o vetor) e `lasso_M0` (as mesmas 14 colunas, sem as 6 do vetor).

O hiperparâmetro de penalização, `alpha`, foi escolhido **uma única vez**, numa grade de {0,001 · 0,01 ·
0,1}, pela menor perda quantílica 0,85 medida só na **calibração epidêmica** (01/01/2022 a 31/12/2023),
ficando depois fixo durante toda a avaliação.

### (e) Resultado numérico

MAE do quantil 0,85, avaliação 2024+: **123,2 / 360,1 / 739,2 / 291,5**, em h=1/4/8/12 (braço `lasso`, com
vetor). Em h=1, o LASSO até vence o B0 marginalmente (123,2 contra 133,6), mas em h=8 dispara para 739,2 —
mais de 3 vezes o erro do cenário adotado (223,2) no mesmo horizonte.

**O `alpha` escolhido em todos os horizontes foi 0,001 — o menor valor da grade.** Na prática, isso
significa **quase nenhuma penalização** — o próprio processo de escolha, aplicado aos dados deste projeto,
concluiu que penalizar pouco reduzia melhor a perda quantílica na calibração epidêmica do que penalizar
mais, mesmo sabendo (a posteriori) que isso deixaria o modelo próximo o suficiente de um V5 sem
penalização para também explodir.

**Por que explodiu, reproduzido do zero pela certificação, com diferença de 0,0%.** Na origem de previsão de
**03/03/2024**, com horizonte de 8 semanas, o LASSO previu **15.317 casos**, para uma semana que teve
**1.347 casos reais** — mais de 11 vezes o valor real. O mecanismo é o mesmo do V5 (§4.8.5): a regressão
linear em escala logarítmica extrapolou um ponto de entrada (o início acelerado da epidemia de 2024) que
ficava fora da distribuição de treino, e a penalização de 0,001 não foi forte o suficiente para conter essa
extrapolação.

**O vetor não teve efeito detectável dentro do LASSO:** comparando `lasso` contra `lasso_M0` (sem as
colunas do vetor), o resultado não muda com significância, **p de Holm 0,995**.

### (f) Veredito

🚫 **REFUTADO — explode no começo de epidemia**, apesar da penalização L1 ter existido justamente para
evitar isso. A explicação mais provável, ainda não medida diretamente, é que a penalização escolhida pelo
próprio critério de validação (0,001) acabou sendo fraca demais para esta série específica — um valor de
`alpha` maior, forçado manualmente em vez de escolhido pela calibração epidêmica, poderia se comportar
diferente, mas isso seria um teste novo, não coberto por esta rodada.

---

## 4.12 Conjuntos (*ensembles*) — média simples e pesos aprendidos

### (a) O que é

Um **ensemble** ("conjunto", em português) é uma previsão construída combinando as previsões de **vários
modelos diferentes**, em vez de usar um só. A ideia é que erros de modelos diferentes, se não forem
totalmente parecidos entre si, tendem a se cancelar parcialmente quando combinados, reduzindo o erro da
combinação em relação a qualquer modelo individual.

### (b) Como funciona por dentro — os dois tipos testados

Os cinco componentes usados nos dois ensembles foram: o cenário adotado (**B0**), o Chronos-2 só com casos
(**`c2_casos`**, §4.9), o SARIMA (**`sarima_log`**, §4.10), o LASSO (**`lasso`**, §4.11) e a **régua
sazonal** (§4.15).

- **`ens_media`** — a **média aritmética simples** dos cinco componentes, sem nenhum peso diferenciado.
- **`ens_pesos`** — uma **média ponderada**, em que os pesos de cada componente são recalculados em cada
  origem de previsão, escolhidos numa grade com passo de 0,1 (1.001 combinações possíveis de pesos não
  negativos que somam 1), pela menor perda quantílica 0,85 medida **só sobre os pares já respondidos até
  aquela origem** (nunca usando informação do futuro). Com menos de 26 pares já respondidos, os pesos ficam
  iguais entre os cinco componentes.

### (c) Por que foi testado

A literatura levantada em 25/09/2026 mostrou ensembles vencendo réguas simples em horizontes de 1 a 3 meses
em outros dois estudos (Colón-González et al. 2021, Wu et al. 2025). Testar se a combinação de tudo o que o
projeto já tinha produzido (um modelo de árvore, um modelo de fundação, um método estatístico clássico e um
linear penalizado) superaria cada peça isolada era um passo natural depois de testar cada uma
separadamente.

### (d) Hiperparâmetros

Nenhum hiperparâmetro de treino tradicional — a "aprendizagem" do `ens_pesos` é a busca em grade dos pesos,
recalculada a cada origem, sempre restrita ao que já era conhecido naquele momento.

### (e) Resultado numérico

MAE do quantil 0,85, avaliação 2024+, em h=12: **`ens_media`: 416,0** · **`ens_pesos`: 254,3** · B0: 243,8 ·
régua sazonal: **217,8**. Nenhum dos dois ensembles bate o B0, e nenhum bate a régua.

**Quem o `ens_pesos` escolheu, em média, ao longo da avaliação:**

| Horizonte | B0 | Chronos-2 | SARIMA | LASSO | Régua sazonal |
|---|---|---|---|---|---|
| 1 semana | 0,29 | 0,24 | 0,02 | **0,45** | 0,00 |
| 4 semanas | 0,33 | **0,53** | 0,04 | 0,07 | 0,03 |
| 8 semanas | **0,51** | 0,25 | 0,09 | 0,06 | 0,10 |
| 12 semanas | **0,33** | 0,19 | 0,11 | 0,25 | 0,12 |

**A régua sazonal recebe apenas 0,12 de peso em h=12**, mesmo sendo a de menor MAE na avaliação — porque os
pesos são aprendidos olhando **o passado de cada origem**, e, dentro desse passado (majoritariamente
2022-2023, epidemias menores), a régua sazonal não era, ainda, a melhor opção. O mecanismo de aprendizagem
de pesos "olha para trás" para decidir, e o padrão "a régua vence em 3 meses" só ficou claro, no histórico
do próprio projeto, depois que a epidemia de 2024 aconteceu.

### (f) Veredito

🚫 **REFUTADO — nenhum dos dois ensembles bate a régua sazonal em 3 meses, e nenhum melhora o B0 com
significância.** A combinação de modelos, mesmo diversificada entre árvore, fundação, estatística clássica
e linear penalizado, não superou nenhuma peça individual no horizonte mais importante para vigilância. O
mecanismo de pesos aprendidos, além disso, tem um problema conceitual próprio: ele decide o peso da régua
sazonal olhando para um passado em que ela ainda não tinha se mostrado a melhor opção, o que a subpondera
justamente no horizonte em que ela mais importa.

---

## 4.13 Transformações de escala — raiz quadrada e logaritmo

### (a) O que é

Uma **transformação de escala** aplica uma função matemática ao alvo antes de treinar (e desfaz essa
função depois de prever), na esperança de que o modelo aprenda melhor na escala transformada do que na
escala bruta. Duas transformações clássicas foram testadas: a **raiz quadrada** (`√casos`) e o **logaritmo**
(`log(casos + 1)`, a mesma transformação já usada no V1 do §4.8.1, mas agora testada com foco específico na
**calibração dos intervalos de previsão**, não apenas no erro pontual).

### (b) Como funciona por dentro — a teoria da estabilização de variância

Dados de **contagem** (números inteiros não negativos, como o número de casos confirmados numa semana)
costumam ter uma propriedade estatística chamada **variância que cresce com o nível**: semanas com poucos
casos têm baixa variabilidade absoluta, e semanas com muitos casos têm alta variabilidade absoluta. Um
exemplo clássico da estatística para lidar com isso é a **transformação de Anscombe**
(`√(x + 3/8)`, para dados que seguem aproximadamente uma distribuição de Poisson — uma distribuição de
probabilidade clássica para contagens raras e independentes), desenhada para tornar a variância
aproximadamente **constante** depois da transformação, independentemente do nível da série.

A hipótese testada em 26/09/2026 era que, se a variância dos casos de dengue crescesse dessa forma clássica
com o nível, transformar o alvo por raiz quadrada ou logaritmo faria com que um intervalo de previsão de
largura **constante** na escala transformada voltasse, ao desfazer a transformação, como um intervalo de
largura **proporcional ao nível** na escala de casos — mais estreito na calmaria, mais largo na epidemia,
automaticamente, sem precisar ajustar nada a mais.

### (c) Por que foi testado

A Parte 8 documenta que os intervalos de previsão do cenário adotado têm cobertura muito ruim justamente
nas semanas de maior risco: no estágio "Alerta ou mais" (mais de 421 casos confirmados na semana, um limiar
oficial do plano municipal descrito no §4.15), o intervalo nominal de 90% cobria apenas **17,8%** das
semanas reais. A transformação de escala era a hipótese mais citada na literatura de estatística para esse
tipo de problema de calibração.

### (d) Hiperparâmetros / configuração

Duas variantes, treinadas com o mesmo HistGB do cenário adotado (§4.1), mudando apenas o alvo:

- **`T_raiz`** — alvo `√casos`, previsão desfeita com `(previsão)² `, cortada em zero.
- **`T_log`** — alvo `log(casos + 1)`, previsão desfeita com `exp(previsão) − 1`, cortada em zero.

Os quantis previstos em escala transformada foram reordenados por um procedimento chamado **rearranjo
isotônico** (garante que o quantil 0,90 previsto nunca fique abaixo do quantil 0,50, por exemplo, corrigindo
um problema técnico chamado **cruzamento de quantis**, quando quantis teoricamente ordenados saem
desordenados de um modelo treinado separadamente para cada um) antes de voltar para a escala de casos.

### (e) Resultado numérico

**MAE por horizonte (quantil 0,85), avaliação 2024-01-01 a 2026-02-01, n=102:**

| Horizonte | B0 (referência) | T_raiz | T_log |
|---|---|---|---|
| 1 semana | 98,0 | 103,2 (+5,3%) | 114,5 (+16,8%) |
| 4 semanas | 219,7 | **205,0 (−6,7%)** | 212,9 (−3,1%) |
| 8 semanas | 272,6 | 278,0 (+2,0%) | 284,6 (+4,4%) |
| 12 semanas | 278,8 | 289,2 (+3,7%) | 299,0 (+7,3%) |

Os dois braços melhoram o erro pontual só em h=4, e pioram nos outros três horizontes — h=1 é o mais
afetado, especialmente o `T_log` (+16,8%).

**Cobertura por faixa de intensidade — o resultado que decidiu o veredito, série completa 2020-2026:**

| Faixa de casos reais | Semanas | B0: IC 50% / IC 90% | T_raiz: IC 50% / IC 90% | T_log: IC 50% / IC 90% |
|---|---|---|---|---|
| Calmaria (0-20) | 814 | 59,2% / 90,5% | 51,6% / 84,2% | 51,2% / 80,5% |
| Subida (21-140) | 110 | 18,2% / 63,6% | 14,5% / 55,5% | 16,4% / 48,2% |
| Mobilização (141-421) | 72 | 27,8% / 47,2% | 15,3% / 43,1% | 15,3% / 33,3% |
| **Alerta ou mais (>421)** | 163 | **8,0% / 17,8%** | 6,7% / 15,9% | 3,7% / 13,5% |

A **cobertura** de um intervalo de previsão é a fração de semanas em que o valor real caiu **dentro** do
intervalo previsto; o nominal esperado para um intervalo "de 90%" é que ele cubra 90% das semanas, se
estiver bem calibrado. **A cobertura piorou nas quatro faixas, para os dois braços, sem exceção** — inclusive
na faixa de "Alerta ou mais", onde a transformação deveria ajudar mais, segundo a hipótese original.

**Nenhuma das 8 combinações de braço × horizonte cobriu o pico histórico da série** (a semana de
30/03/2025, com **2.381 casos**, o maior valor já registrado): o limite superior do intervalo de 90%
previsto ficou sempre abaixo do valor real, nos dois braços e em todos os horizontes.

### Por que a hipótese falhou — o diagnóstico completo

A hipótese apostava num mecanismo específico: dado de contagem tem variância que cresce com o nível; em
escala transformada, um intervalo de largura constante volta como intervalo proporcional ao nível. **O
diagnóstico, medido diretamente no B0, mostrou que a aposta estava errada, e o motivo é mensurável:**

| Faixa | Semanas | Real mediano | Largura do IC 90% do B0 | Erro mediano do B0 | Largura que seria necessária | Quanto falta |
|---|---|---|---|---|---|---|
| Calmaria | 814 | 1 | 8,5 | 1,3 | 4 | **0,5×** — larga demais |
| Subida | 110 | 47 | 101,1 | 29,6 | 97 | 1,0× — na medida certa |
| Mobilização | 72 | 247 | 195,6 | 157,8 | 519 | **2,7×** |
| **Alerta ou mais** | 163 | **917** | **592,7** | **539,0** | **1.773** | **3,0×** |

**Tradução concreta desta tabela, faixa por faixa.** Na calmaria, o modelo é **excessivamente cauteloso**: a
largura do intervalo (8,5 casos) já é **o dobro** do que seria necessário para cobrir o erro típico (a
largura necessária seria de apenas 4). Já na faixa de Alerta, é o oposto: numa semana típica dessa faixa,
com **917 casos reais**, o modelo erra por uma mediana de **539 casos** — ou seja, prevê algo perto de 378
(917 menos 539) — mas o intervalo de 90% que ele desenha em torno dessa previsão tem largura de apenas
**592,7 casos**, quando precisaria de **1.773** para cobrir esse erro típico com a confiança prometida. É
como uma prefeitura planejando leitos hospitalares para uma demanda de 378 pacientes e recebendo, na
prática, mais que o dobro.

- **A faixa **já** cresce com o nível**, e cresce bastante: de 8,5 (calmaria) para 592,7 (Alerta), um fator
  de **70 vezes**.
- **Mas o erro cresce ainda mais rápido:** de 1,3 para 539,0, um fator de **415 vezes**.
- **Raiz quadrada e logaritmo comprimem valores altos** — é exatamente essa compressão que faz a faixa
  crescer **mais devagar** ainda, na direção **contrária** à necessária. Isso explica, de forma direta, por
  que a cobertura piorou em todas as faixas para os dois braços.

🔴 **A causa raiz não é de variância — é de viés.** Um erro sistemático de 539 casos sobre um valor real
mediano de 917 (59% do nível) não é ruído espalhado em torno do valor certo; é o modelo **prevendo baixo
demais de forma consistente** — o mesmo viés de subestimação de pico já descrito no §4.1 e medido, com
outra métrica (a "captura do pico"), em 0,388 em h=12. **Alargar o intervalo não conserta viés**: uma faixa
de 1.773 casos de largura, embora cobrisse 90% das semanas de Alerta, iria de cerca de 100 a cerca de 1.900
casos — larga demais para informar qualquer decisão a alguém.

### (f) Veredito

🚫 **REFUTADO — nenhuma das duas transformações resolve o problema de calibração, e o erro por trás da
falha foi identificado.** **Nenhuma transformação de escala resolve falta de epidemia no treino.** O
problema medido não é de distribuição estatística mal ajustada (o que uma transformação poderia corrigir),
é de **nível**: o modelo não consegue prever o **tamanho** de uma epidemia que foge do que já viu, e a raiz
desse limite — ainda **HIPÓTESE, não medida diretamente** — é que a série de treino contém apenas **2
epidemias grandes** (2024 e 2025), poucas o suficiente para que qualquer transformação matemática do alvo
compense.

---

## 4.14 Correção conformal — o que é, e por que a cobertura subir custou caro

### (a) O que é

A **correção conformal** (do inglês *conformal prediction*, "predição conformal") é um método estatístico
que **recalibra**, depois do treino, os intervalos de previsão de qualquer modelo, sem precisar retreiná-lo
— e sem depender de suposições sobre a distribuição dos erros. A ideia central: separar um conjunto de
dados (chamado conjunto de **calibração conformal**, diferente da "calibração" usada em outras partes deste
catálogo para descrever um período temporal) onde já se conhece o valor real, medir o quanto os intervalos
originais erraram nesse conjunto, e usar essa medida de erro para **ajustar a largura** dos intervalos
futuros, de forma que a cobertura empírica (a fração real de semanas cobertas) se aproxime da cobertura
nominal prometida (por exemplo, 90%).

### (b) Como funciona por dentro

No caso mais simples de correção conformal para intervalos de quantil, o método calcula, para cada semana
do conjunto de calibração conformal, o **quanto o valor real ultrapassou** (ou ficou aquém) do intervalo
original previsto. Reúne essas margens de erro numa distribuição empírica, e escolhe um **deslocamento**
(um número fixo a somar ao limite superior do intervalo, e subtrair do limite inferior) que garanta que, no
próprio conjunto de calibração conformal, a cobertura observada bata com a cobertura nominal desejada. Esse
mesmo deslocamento é então aplicado às previsões futuras.

### (c) Por que foi testado

O diagnóstico do §4.13 já tinha mostrado que a cobertura do cenário adotado é ruim justamente nas semanas
de maior risco — no estágio de Alerta, o intervalo nominal de 90% cobria só 17,8% das semanas reais. A
correção conformal é o método padrão da literatura de aprendizado de máquina para corrigir exatamente esse
tipo de descalibração, sem exigir uma transformação do alvo nem um retreino.

### (d) Hiperparâmetros / configuração

Aplicada sobre o cenário adotado, na segunda bateria noturna de 25-26/09/2026, com o objetivo de recalibrar
a cobertura do intervalo de 3 meses (h=12) para o nível nominal.

### (e) Resultado numérico

- **A cobertura subiu**, de **50%** para **78%**, no cenário adotado, em 3 meses (h=12).
- **Mas os alarmes falsos explodiram**: de **15** para **124**, usando o limiar de alarme de 100 casos
  (uma multiplicação por mais de 8 vezes).
- **A perda quantílica piorou em 1 mês**, **−8,7%** com p de Holm menor que 0,001, e melhorou em 3 meses,
  mas sem significância estatística.

**Tradução concreta do custo:** corrigir a cobertura empurrando o limite superior do intervalo para cima,
de forma generalizada, faz o modelo passar a "prever alto" com muito mais frequência — inclusive em
semanas de calmaria absoluta, que antes ficavam corretamente fora do estado de alarme. Um sistema de
vigilância que adotasse essa correção passaria a soar o alarme quase 8 vezes mais vezes ao longo de um ano,
a maioria delas sem um surto de verdade por trás.

### (f) Veredito

🚫 **REFUTADO como implementado — não serve como está.** A correção conformal simples corrige a cobertura
empurrando **toda** a distribuição de previsões para cima, de forma uniforme, em vez de identificar
especificamente as semanas de risco elevado que precisariam de um intervalo mais largo. O resultado é uma
troca ruim: mais cobertura no papel, ao custo de um sistema de alarme que deixa de ser útil na prática. As
faixas de previsão do projeto **continuam precisando de outra forma de calibração** — uma que distinga
faixas de risco, e não apenas desloque tudo para cima.

---

## 4.15 As réguas — por que uma regra trivial é o teste mais duro que um modelo enfrenta

### Por que comparar com uma régua, afinal

Uma **régua** (também chamada, na literatura internacional, de *baseline* ou linha de base) é uma regra de
previsão **sem nenhum aprendizado de máquina**: nenhum parâmetro é ajustado a partir dos dados de treino,
não há hiperparâmetro para escolher, não há risco de sobreajuste. Ela existe para responder a uma pergunta
que antecede qualquer modelagem sofisticada: **o esforço extra de um modelo complexo produz algum ganho
real, ou o mesmo resultado (ou um resultado melhor) já vem de uma regra que qualquer pessoa entenderia em
uma frase?**

Bater uma régua trivial é, paradoxalmente, **o teste mais difícil que um modelo pode enfrentar**, por um
motivo estrutural: uma régua não tem parâmetros para "errar demais" no treino e não tem viés de
otimização — ela captura, de forma direta e sem distorção, exatamente a estrutura mais óbvia e estável dos
dados (a repetição do padrão sazonal, ou a continuidade do valor mais recente). Um modelo complexo só supera
uma régua se conseguir extrair informação **genuinamente adicional**, além dessa estrutura óbvia — e, se não
conseguir, isso é evidência direta de que toda a complexidade adicionada (hiperparâmetros, variáveis de
clima e vetor, funções de perda sofisticadas) não estava comprando nada. Este é o princípio da **parcimônia**
em modelagem estatística: entre duas explicações com desempenho parecido, prefere-se sempre a mais simples.

### As sete réguas testadas neste projeto

**1. Persistência.** Repete o valor mais recente conhecido: a previsão para `h` semanas à frente é
simplesmente o número de casos confirmados na **semana de origem** (a semana em que a previsão está sendo
feita). É a régua mais simples de todas — equivale, na literatura de séries temporais, a um **passeio
aleatório sem deriva** (*random walk*, um modelo em que a melhor previsão para o próximo valor é o valor
atual, sem nenhuma tendência assumida). É também exatamente o mesmo número que o cenário adotado recebe como
uma de suas colunas de entrada (o lag de `h` semanas) — a comparação usa a mesma informação que o modelo já
tem à disposição.

**2. Régua sazonal.** A previsão para uma semana-alvo é o número de casos confirmados na **mesma
semana-alvo, 52 semanas antes** (aproximadamente um ano antes). Captura diretamente a sazonalidade da
dengue: mais casos no verão e outono, poucos no inverno.

**3. Climatologia.** A média de todos os anos anteriores disponíveis, na mesma semana do calendário —
não apenas o ano anterior, mas a **média histórica** daquela época do ano (semanas-alvo em `data_alvo − 52k`,
para `k=1,2,3,...`, usando só os anos com dado disponível).

**4, 5 e 6. Canal endêmico, em três variantes.** O **canal endêmico** é um método clássico de vigilância
epidemiológica: calcula-se, para cada semana do calendário, a média histórica de casos (ou de incidência) e
um limite superior a partir dessa média mais um múltiplo do desvio-padrão histórico (no caso do plano
municipal de Porto Alegre, descrito adiante nesta seção, dois desvios-padrão), formando uma "faixa normal"
esperada. Uma semana é considerada "acima do canal" quando o valor observado ultrapassa esse limite. As três
variantes testadas foram: **"hoje acima do canal"** (o valor na semana de origem já está acima do canal);
**"hoje acima do canal e crescendo"** (acima do canal **e** em tendência de subida — uma regra emprestada de
um estudo sobre 8 países asiáticos, ver a Parte 6); e **"o ano passado acima do canal"** (o valor da mesma
semana, um ano antes, estava acima do canal).

**7. "Hoje já passou" (e sua variante "está crescendo").** Uma regra baseada em limiar fixo, não em canal
estatístico: alarme disparado sempre que o número de casos confirmados **na semana de origem** já ultrapassa
um limiar fixo (100 casos, neste projeto — ver a definição desse limiar mais adiante). A variante "e está
crescendo" soma a exigência de que a série também esteja em tendência de alta. Uma regra correlata, "o ano
passado passou de 100", usa o mesmo limiar aplicado à semana correspondente do ano anterior.

### Por que a régua sazonal e a persistência têm papéis diferentes conforme o horizonte

**Contra a persistência**, os modelos deste projeto ganham forte e com significância estatística em 2 e 3
meses (reduções de 48% a 65% no MAE, com p de Holm menor que 0,0001) — mas em **1 semana** é a
**persistência que vence**, também com significância (p de Holm de 0,021 contra o LightGBM). Isso faz
sentido: em 1 semana, o valor de hoje é, de longe, o melhor preditor possível — a série ainda não teve tempo
de mudar muito, e qualquer complexidade adicional do modelo só introduz ruído.

**Contra a régua sazonal**, o quadro se inverte: em **1 semana**, os modelos ganham com folga e significância
(reduções de 42% a 54%); mas em **4, 8 e 12 semanas**, o placar fica negativo ou perto de zero, **e nunca
significativo** — a régua sazonal empata ou supera os modelos exatamente no horizonte que mais importa para
planejamento de vigilância (3 meses de antecedência).

### O teste mais importante — McNemar sobre o alarme de surto

O **teste de McNemar** é um teste estatístico para comparar dois classificadores binários (que dizem
"sim/surto" ou "não/sem surto") **sobre as mesmas observações**, focando especificamente nas semanas em que
os dois classificadores **discordam** — uma acerta e o outro erra. A tabela relevante conta, entre as
semanas discordantes, quantas o classificador A acertou e o B errou (chamemos de **b**) e quantas foi o
oposto (chamemos de **c**). Sob a hipótese de que os dois classificadores são igualmente bons, esperar-se-ia
que **b** e **c** fossem parecidos; uma diferença grande entre eles é evidência de que um classificador é
sistematicamente melhor que o outro nas situações em que discordam. A estatística do teste, com correção de
continuidade, é:

```
χ² = (|b − c| − 1)² / (b + c)
```

**Exemplo numérico trabalhado, com os números reais deste projeto** (comparação do cenário adotado contra a
régua "hoje já passou de 100 casos", em h=12, evento "surto = mais de 100 casos confirmados na semana"):
**37 semanas discordantes**, divididas **31 a 6** — em 31 delas, o cenário adotado acertou e a régua errou;
em 6, o oposto.

```
χ² = (|31 − 6| − 1)² / (31 + 6) = (25 − 1)² / 37 = 576 / 37 ≈ 15,57
```

Um valor de χ² de 15,57, com 1 grau de liberdade, corresponde a um valor-p muito pequeno (da ordem de
0,00008) — **e é isso que sustenta o p de Holm de 0,00062 reportado para esta comparação**: com uma
diferença tão grande entre os dois lados da tabela (31 contra 6), é muito improvável que essa assimetria
tenha surgido só por acaso, mesmo depois de ajustar o limiar de significância para a família inteira de
comparações (a correção de Holm, explicada logo a seguir).

**O painel completo, avaliação 2024+, 102 semanas, evento "mais de 100 casos confirmados na semana":**

| Horizonte | Comparação | Semanas discordantes | Divisão | p de Holm | Significativo? |
|---|---|---|---|---|---|
| 4 semanas | Cenário adotado × "hoje já passou" | 15 | 13 a 2 | 0,103 | **NÃO** |
| 4 semanas | Cenário adotado × "o ano passado passou" | 7 | 5 a 2 | 1,000 | **NÃO** |
| 12 semanas | Cenário adotado × "hoje já passou" | 37 | 31 a 6 | **0,00062** | **SIM** |
| 12 semanas | Cenário adotado × "o ano passado passou" | 16 | 4 a 12 | 0,845 | **NÃO** |

🔴 **Este é o quadro mais importante deste catálogo de modelos.** Em 3 meses (h=12), o cenário adotado vence
com significância a régua "hoje já passou de 100 casos" — um resultado real e defensável, o único da linha
de comparação por McNemar que sobrevive à correção de Holm. **Mas contra "o ano passado passou de 100
casos", a divisão inverte de sinal (4 a 12, a favor da régua) e o p de Holm é 0,845 — sem nenhuma evidência
de que o modelo vença.** O alarme de 3 meses do cenário adotado **não vence, com significância, todas as
réguas simples** — ele vence a mais fraca delas (olhar só a situação de hoje) e empata, sem vencer, com a
mais forte (repetir o padrão do ano anterior).

**O que é a correção de Holm, e por que ela muda o valor-p.** Quando várias comparações estatísticas são
feitas na mesma rodada (uma "família" de testes), a chance de pelo menos uma delas dar "significativa" por
puro acaso cresce com o número de testes — é o problema de **múltiplas comparações**. A **correção de
Holm** ajusta cada valor-p bruto para compensar isso: ordena os valores-p brutos da família do menor para o
maior, $p_{(1)} \le p_{(2)} \le ... \le p_{(m)}$ (onde $m$ é o número total de testes na família), e o
valor ajustado do menor deles é $p_{(1)} \times m$ (limitado a no máximo 1,0); os seguintes recebem
multiplicadores decrescentes, e o processo garante que nenhum valor ajustado fique menor que o anterior na
ordem.

**Exemplo numérico trabalhado, com um resultado real deste projeto** (o alarme de surto usando notificados,
percentil 90, h=12, descrito na Parte 5): o valor-p bruto medido foi **0,0062**, numa família de **6**
comparações (`m = 6`). Como esse era o menor valor-p da família ($p_{(1)}$), o ajuste de Holm é:

```
p_ajustado = p_(1) × m = 0,0062 × 6 = 0,0372
```

Arredondado, **0,037** — exatamente o valor reportado no projeto. **É por isso que um p de Holm de 0,037
"faz sentido" partindo de um p bruto de 0,0062**: a correção multiplicou o valor bruto pelo número de testes
da família, tornando o critério de significância mais rigoroso na proporção exata de quantas chances o
projeto teve de encontrar algo "significativo" por acaso.

### ⚠️ RESSALVA que precisa acompanhar qualquer leitura destes testes — só existem 2 episódios de surto

**FATO (medido em 26/09/2026).** Olhando as semanas com mais de 100 casos confirmados no período avaliado
(121 semanas desde 2024), elas formam **exatamente 2 blocos contíguos** — um em 2024 (20 semanas seguidas) e
outro em 2025 (19 semanas seguidas) — não 39 eventos independentes, como uma contagem ingênua de "semanas de
surto" sugeriria. O mesmo padrão de **exatamente 2 blocos** se repete com os limiares oficiais do plano
municipal (140, 421 e 702 casos por semana, descritos adiante):

| Limiar (casos/semana) | Semanas acima | Blocos contíguos | Maior bloco | Bloco de 2024 | Bloco de 2025 |
|---|---|---|---|---|---|
| 100 | 39 | **2** | 20 semanas | 20 | 19 |
| 140 | 38 | **2** | 20 | 20 | 18 |
| 421 | 28 | **2** | 14 | 14 | 14 |
| 702 | 23 | **2** | 12 | 11 | 12 |

**Consequência para todo teste estatístico deste catálogo que trate semana como observação independente:**
o McNemar acima, por exemplo, conta 37 semanas discordantes em h=12 como se fossem 37 "chances" separadas —
mas se todas as semanas de um mesmo bloco de epidemia tendem a errar (ou acertar) da mesma forma, o número
de **eventos realmente independentes** por trás desses 37 é muito menor que 37, possivelmente perto de 2. O
valor-p reportado é, quase certamente, **otimista** (menor do que deveria ser) por esse motivo — uma
investigação direta dessa inflação é descrita a seguir.

### O bootstrap em bloco — medindo o quanto o valor-p está otimista

Um **bootstrap em bloco** (em inglês, *block bootstrap*) é uma técnica para reamostrar dados de série
temporal respeitando sua dependência temporal: em vez de sortear semanas individuais (o que quebraria a
estrutura de blocos contíguos de epidemia descrita acima), sorteiam-se **blocos inteiros de semanas
consecutivas**, de um tamanho fixo, com reposição, até reconstituir uma série do mesmo tamanho da original.
Repetindo esse processo milhares de vezes e recalculando o teste estatístico de interesse em cada réplica,
é possível estimar quanto o valor-p nominal (calculado assumindo semanas independentes) se desvia do
valor-p que se obteria respeitando a dependência real dos dados.

Medido em 26/09/2026, com blocos de 4, 8, 13 e 26 semanas, 2.000 reamostragens e semente 20260926: a razão
entre o valor-p do bootstrap e o valor-p nominal foi de **0,0001 a 0,82** na comparação contra "hoje já
passou" (ou seja, o valor-p nominal era, se algo, **conservador** — o teste real seria ainda mais
significativo) — mas de **1,10 a 1,51** em h=4 e de **2,11 a 3,44** em h=12 na comparação contra "o ano
passado passou de 100" (o valor-p nominal era **otimista**, em até 3,44 vezes). Como o veredito contra essa
régua já era negativo (o cenário adotado **não** vence "o ano passado" com significância), essa inflação só
**reforça** essa conclusão negativa — não muda o sentido dela.

⏳ **EM ABERTO.** O teste de McNemar de 13/09/2026 que deu p de Holm 0,037 (descrito na Parte 5, com alvo
notificados e percentil 90) **não pôde passar por este bootstrap**: as previsões semana a semana daquela
rodada específica nunca foram salvas em disco, e refazer o cálculo exigiria retreinar o classificador
inteiro do zero. Até isso ser feito, esse resultado específico deve ser citado com essa ressalva.

### O evento de alarme mais amplo — sensibilidade, precisão e o índice de Youden

Além do teste pareado de McNemar, o projeto também mede o desempenho de alarme de cada regra por quatro
métricas clássicas de um classificador binário, definidas a partir de quatro contagens possíveis: **verdadeiro
positivo** (VP — a regra disse "surto" e houve surto), **falso positivo** (FP — disse "surto" e não houve),
**verdadeiro negativo** (VN — disse "sem surto" e não houve) e **falso negativo** (FN — disse "sem surto" e
houve surto):

```
Sensibilidade = VP / (VP + FN)     — de todos os surtos reais, quantos a regra pegou
Precisão      = VP / (VP + FP)     — de todos os alarmes soados, quantos eram surtos de verdade
Especificidade = VN / (VN + FP)    — de todas as semanas sem surto, quantas a regra corretamente não alarmou
Youden = Sensibilidade + Especificidade − 1
```

O **índice de Youden** varia de −1 (a regra erra sistematicamente, pior que o acaso) a 0 (a regra não é
melhor que jogar uma moeda) a **1** (a regra é perfeita, sem falsos positivos nem falsos negativos). É uma
forma de resumir sensibilidade e especificidade num único número, útil para comparar regras diferentes de
uma vez.

**Exemplo numérico trabalhado, com o cenário adotado em h=4 (1 mês), evento "mais de 100 casos", avaliação
2024+:** sensibilidade de **97,1%** e precisão de **94,3%**, com **0,7 alarmes falsos por ano**. Sem a
contagem exata de verdadeiros negativos disponível neste recorte, o Youden reportado (**0,94**) já
incorpora a especificidade calculada sobre a série completa de semanas avaliadas — um valor muito próximo
de 1,0 (o valor máximo possível) mostra que, em 1 mês, o alarme do cenário adotado é, na prática, quase
perfeito para este evento específico.

**O painel completo, evento "mais de 100 casos", avaliação 2024+, 102 semanas:**

| Regra | h=1: sensibilidade | h=1: Youden | h=4: sensibilidade | h=4: precisão | h=4: falsos/ano | h=4: Youden | h=8: sensibilidade | h=8: precisão | h=8: falsos/ano | h=8: Youden | h=12: sensibilidade | h=12: precisão | h=12: falsos/ano | h=12: Youden |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Cenário adotado | 96,9% | — | 97,1% | 94,3% | 0,7 | **0,94** | 81,6% | 86,1% | 1,7 | — | 76,9% | 81,1% | 2,3 | 0,66 |
| HistGB folha 20 | — | — | 97,1% | — | — | 0,90 | — | — | — | — | 84,6% | 89,2% | — | 0,78 |
| "O ano passado passou de 100" | — | — | 85,3% | — | — | 0,84 | — | — | — | — | 82,1% | 97,0% | — | **0,81** |
| "Hoje já passou de 100" | — | — | 76,5% | — | — | 0,68 | — | — | — | — | 38,5% | 46,9% | — | 0,12 |

(Captura do pico — a razão entre a média das previsões e a média dos valores reais, apenas nas semanas
acima de 100 casos, uma métrica de **nível**, não de alarme — para o cenário adotado: **0,886** em h=1,
0,702 em h=4, 0,417 em h=8 e **0,388** em h=12.)

**Leitura por horizonte:**

- **Em 1 mês (h=4), o cenário adotado é o melhor alarme de todos os testados**, com Youden de 0,94 —
  vence tanto a régua sazonal binarizada quanto a régua de hoje.
- **Em 3 meses (h=12), o cenário adotado (Youden 0,66) perde para a HistGB folha 20 (0,78) e para "o ano
  passado passou de 100" (0,81)** — a régua sazonal, na sua forma de alarme, é competitiva ou superior ao
  cenário adotado no horizonte mais importante para vigilância, embora sem significância suficiente (ver o
  McNemar acima) para que essa vitória seja declarada com confiança estatística.

### Um caso à parte — o alarme contra o estágio "Alerta" do plano municipal

O **Plano Municipal de Contingência de Arboviroses 2026**, da Secretaria Municipal de Saúde de Porto
Alegre, define quatro estágios de resposta epidemiológica com base numa taxa de incidência de casos
confirmados (calculada, por inferência — o plano não declara a base de cálculo explicitamente — como casos
por 100 mil habitantes, sobre uma população de **1.404.269**), sempre combinada com uma condição adicional
sobre o **Limite Superior Endêmico** (a média móvel histórica de casos **prováveis** — não confirmados —
somada a **dois desvios-padrão**, calculada sobre o Rio Grande do Sul inteiro, não apenas Porto Alegre) ou
sobre o **Limite de Alerta** (fixado em 45% abaixo do Limite Superior Endêmico):

| Estágio | Taxa de incidência (por 100 mil, inferida) | Em casos confirmados por semana em Porto Alegre |
|---|---|---|
| Normalidade | abaixo de 10 | abaixo de **140** |
| Mobilização | acima de 10 | acima de **140** |
| Alerta | acima de 30 | acima de **421** |
| Epidemia | acima de 50 **e** acima do Limite Superior Endêmico | acima de **702** |

🔴 **RESSALVA que precisa acompanhar toda citação destes números:** o corte numérico do plano **nunca
aparece sozinho** — ele é sempre exigido **em conjunto (E)** com a condição sobre o Limite de Alerta ou o
Limite Superior Endêmico. O texto literal do plano para o estágio de Epidemia é: *"acima do LSE nas últimas
4 semanas epidemiológicas **E** taxa de incidência de casos confirmados acima de 50,0 em pelo menos uma das
4 semanas epidemiológicas"*. Os cortes de 10, 30 e 50 são sobre casos **confirmados**; os limites (Superior
Endêmico e de Alerta) são sobre casos **prováveis** — duas bases de contagem diferentes, combinadas na
mesma regra.

Testando o alarme contra o evento "mais de 421 casos confirmados na semana" (o estágio de Alerta), na
avaliação de 26/09/2026, pré-declarado: **0 das 4 combinações testadas venceram a régua "o ano passado
passou de 421" com p de Holm menor que 0,05.** O cenário adotado (e também a HistGB folha 20) **vencem**
"hoje já passou de 421" em h=12 com folga: p de Holm de **0,00014** (cenário adotado) e **0,00008** (folha
20), sobre uma família de **24 testes** (16 de 25/09/2026 mais 8 novos comparações desta rodada).

**Leitura, sem confundir as duas comparações:** o alarme de 3 meses do cenário adotado **vence** a regra
mais fraca (olhar só a situação de hoje) tanto no evento de 100 casos quanto no de 421, com significância
nos dois. Mas **perde ou empata**, sem significância a seu favor, contra a regra mais forte (repetir o
padrão do ano anterior), também nos dois eventos. **Este é o padrão central que qualquer citação do alarme
do modelo precisa carregar.**

### O canal endêmico não se adapta bem a séries curtas — Porto Alegre incluída

Uma premissa comum na literatura internacional de canais endêmicos é que eles precisam de **muitos anos de
histórico calmo** para ficarem informativos. O exemplo mais claro vem de Porto Rico, onde a vigilância
contínua de dengue existe **desde 1986**: o limiar epidêmico oficial usado lá é o **percentil 75 de uma
regressão binomial negativa** (um tipo de modelo estatístico para dados de contagem, mais flexível que a
distribuição de Poisson simples, porque permite variância maior que a média) ajustada a **86.282 casos ao
longo de cerca de 38,5 anos** (1986 a 2024), **sem excluir os anos de epidemia** da própria série usada para
calcular o limiar.

Em Porto Alegre, essa premissa não se sustenta: com o período de **2018 a 2021 quase sem casos de dengue**,
o limite do canal endêmico calculado da forma clássica fica em **zero** em muitas semanas fora da temporada.
**FATO (medido em 25/09/2026).** Na semana epidemiológica 39 de 2024, com **7 casos confirmados**, o limite
do canal era **0** — o que faria **qualquer caso, mesmo um único, contar como "acima do canal"**. A versão
em escala logarítmica do canal (testada em 25/09/2026) ajuda, mas não resolve: só fica informativa depois de
alguns anos consecutivos com transmissão de dengue.

⏳ **HIPÓTESE (não verificada com fonte primária lida).** O limiar oficial do Ministério da Saúde brasileiro
para vigilância de dengue (buscas apontaram os valores de 100 ou 300 casos por 100 mil habitantes, sem uma
fonte primária legível encontrada) e a janela exata usada em produção pelo sistema InfoDengue **não devem
ser citados como fato** neste documento, por falta de leitura direta da fonte primária.

### (f) Veredito conjunto das réguas

✅ **FATO — a régua sazonal é, hoje, a linha de base mais difícil que o projeto já testou, e ela segue
invicta em 3 meses contra tudo que foi tentado até 26/09/2026**: o cenário adotado (§4.1), a folha mínima 20
(§4.3), as 120 configurações da busca de hiperparâmetros (§4.5), as seis reformulações de alvo (§4.8), os
dois modelos de fundação (§4.9), o SARIMA (§4.10), o LASSO (§4.11) e os dois ensembles (§4.12).

⚠️ **Em 1 mês o quadro muda, mas é preciso separar duas coisas que NÃO têm o mesmo estatuto:**

- ✅ **COM significância:** pela métrica probabilística — o escore de intervalo ponderado — o cenário
  adotado vence a **régua climatológica** em 1 mês, com valor-p de Holm **menor que 0,0001**.
- 🔴 **SEM significância:** no **alarme**, o índice de Youden do cenário adotado (**0,94**) é maior que o
  das réguas simples (**0,84** e **0,68**), mas essa diferença **não sobrevive** ao teste de McNemar com
  correção de Holm: os valores-p são **0,103** contra "hoje já passou de 100" e **1,000** contra "o ano
  passado passou de 100" (ver o quadro na §4.15). São números descritivos, não vitória demonstrada.

**A causa provável da ausência de significância é falta de poder do teste**, não ausência de efeito: em
h=4 existem apenas **15** e **7** pares discordantes. HIPÓTESE, não fato.

⚠️ **RESSALVA que fecha este catálogo inteiro** — **e é a mais importante dele.** Nenhum destes vereditos é
sobre "o vetor" ou sobre "se a rede de armadilhas serve para algo": são vereditos sobre um instrumento
específico, a previsão do número de casos e o alarme derivado dela, medidos com os dados e o método
disponíveis em 26/09/2026. A pesquisa está em fase exploratória (ver o CLAUDE.md do projeto), e nenhum
resultado deste catálogo — positivo ou negativo — deve ser lido como veredito sobre a pesquisa como um
todo.
