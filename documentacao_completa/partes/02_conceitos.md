# Parte 2 — Conceitos fundamentais

> Esta seção define, do zero, todo conceito estatístico, de aprendizado de máquina e de epidemiologia
> usado no restante do documento. O leitor não precisa saber nada disso de antemão: cada termo é
> apresentado na primeira vez que aparece, com fórmula, o significado de cada símbolo e um exemplo
> numérico resolvido do começo ao fim com dados reais deste projeto. Onde uma afirmação é um resultado
> medido, ela vem rotulada **FATO (medido em [data])**; onde é uma leitura ainda não testada, vem rotulada
> **HIPÓTESE (não testada)**.

---

## 1. Série temporal e semana epidemiológica

### 1.1 O que é uma série temporal

Uma **série temporal** é um conjunto de medidas da mesma grandeza, feitas em instantes de tempo
sucessivos e ordenados. A ordem importa: trocar a posição de duas observações destrói a informação, ao
contrário de uma tabela comum em que as linhas poderiam, em princípio, ser embaralhadas sem perda.

Neste projeto existem duas séries temporais que são combinadas:

- a **série de captura de mosquitos**, uma medida por semana, desde **23/09/2012**, vinda das armadilhas
  do programa MI-Aedes (rede de armadilhas de monitoramento do mosquito *Aedes aegypti* mantida pela
  Secretaria Municipal de Saúde de Porto Alegre, doravante referida como **SMS-POA**);
- a **série de casos confirmados de dengue**, uma medida por semana, vinda do **SINAN** (Sistema de
  Informação de Agravos de Notificação, o sistema nacional brasileiro onde todo caso suspeito ou
  confirmado de doença de notificação compulsória, como a dengue, é registrado).

As duas séries são unidas numa única tabela, `modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv`,
com uma linha por semana. **FATO (estado em 26/09/2026):** essa tabela tem **725 linhas**, cobrindo da
semana de **23/09/2012** até a semana epidemiológica **17 de 2026**.

### 1.2 O que é a semana epidemiológica, e por que ela não é a semana do calendário

A **semana epidemiológica** (abreviada **SE** a partir daqui) é a unidade de tempo padronizada usada em
vigilância em saúde no Brasil e na maior parte do mundo, definida pelo mesmo padrão usado pelo *Centers
for Disease Control and Prevention* (CDC) norte-americano nos seus boletins MMWR (*Morbidity and Mortality
Weekly Report*) e adotado no Brasil pelo Ministério da Saúde através do SINAN.

A diferença para a semana do calendário civil é dupla:

- **Início fixo no domingo.** Toda semana epidemiológica começa num domingo e termina no sábado seguinte,
  independentemente de em que dia da semana cai o dia 1º de janeiro.
- **Numeração ancorada no ano, não no dia 1º de janeiro.** A semana epidemiológica número 1 de um ano é a
  primeira semana (domingo a sábado) que contém pelo menos 4 dias daquele ano civil. Isso significa que,
  se o dia 1º de janeiro cai numa quinta-feira, sexta-feira ou sábado, os primeiros dias daquele ano ainda
  pertencem, na contagem epidemiológica, à última semana do ano anterior.

Essa regra existe para que toda semana epidemiológica tenha exatamente 7 dias completos e para que
comparações entre anos — "a semana 10 de 2024 contra a semana 10 de 2025" — sejam comparações do mesmo
ponto do ciclo sazonal, o que não aconteceria de forma estável se a semana fosse contada a partir do dia
1º de janeiro de cada ano.

**Como o projeto codifica a semana epidemiológica.** Na tabela oficial, a coluna `SE` guarda o ano e o
número da semana concatenados, sem separador: o valor **201239** significa ano **2012**, semana **39**.
A coluna `data_inicio_semana_epidemi` guarda a data do domingo em que aquela semana começa — para a linha
`SE = 201239`, essa data é **23/09/2012**, que é também a primeira linha de toda a tabela do projeto.

### 1.3 Por que isso importa para o resto do documento

Toda comparação feita neste trabalho — modelo contra modelo, modelo contra régua, ano contra ano — é uma
comparação **pareada por semana epidemiológica** (ver Seção 12 adiante para o conceito de comparação
pareada). Se duas fontes de dados numerassem a semana de forma diferente, uma comparação "semana a semana"
estaria na verdade comparando períodos deslocados, o que inflaria ou esconderia diferenças reais.

---

## 2. O problema de previsão: origem, horizonte e data-alvo

### 2.1 Os três conceitos

Todo o trabalho deste projeto resolve, repetidamente, a mesma pergunta: **dado tudo o que se sabia até uma
certa semana, quantos casos confirmados de dengue vão existir em uma semana futura?** Essa pergunta tem
três partes que precisam de nomes próprios, porque são usadas em todas as seções seguintes.

- **Data de origem.** A semana em que a previsão é feita — a última semana cujos dados (casos, clima,
  captura de mosquito) já estão disponíveis e podem alimentar o modelo.
- **Horizonte** (representado pela letra $h$, medido em semanas). A distância, em número de semanas, entre
  a data de origem e a semana que se quer prever. Este projeto trabalha com quatro horizontes:
  $h = 1$, $h = 4$, $h = 8$ e $h = 12$ semanas.
- **Data-alvo.** A semana que está sendo prevista. Por definição, **data-alvo = data de origem + $h$
  semanas**.

### 2.2 A linha do tempo, desenhada em texto

Para $h = 12$ (o horizonte mais citado neste documento, porque é o que mais interessa para planejamento de
resposta), a linha do tempo é:

```
semana 0                                                          semana 12
(data de origem — tudo                                            (data-alvo — o número
 aqui já é conhecido:                                              que o modelo tenta
 casos, clima e vetor                                               adivinhar)
 até esta semana)
   |---1---|---2---|---3---|---4---|---5---|---6---|---7---|---8---|---9---|--10---|--11---|--12--->
   └───────────────────── 12 semanas de horizonte ─────────────────────────────────────────────────┘
```

Na data de origem, o modelo recebe como entrada apenas o que já aconteceu até ali — os **20 atributos**
descritos na Parte 3 deste documento (casos e sazonalidade, clima e captura do vetor, todos defasados) — e
produz um número que é a estimativa do que vai acontecer 12 semanas depois.

### 2.3 Por que "prever a 12 semanas" significa não usar nada que aconteceu depois

A frase "o modelo prevê a 12 semanas" tem um significado técnico preciso e não negociável: **ao construir a
previsão para a data-alvo, o modelo só pode consultar informação que já existia na data de origem — nunca
informação que só ficou disponível entre a data de origem e a data-alvo.**

Isso parece óbvio, mas é fácil violar sem perceber, porque as *variáveis de entrada* (clima, vetor) têm
defasagens diferentes: uma variável "clima da semana passada" está sempre disponível na data de origem,
mas uma variável "casos confirmados" tem um atraso de notificação — nem todo caso da semana X já está
lançado no SINAN na semana X mesmo. É exatamente esse descuido, cometido não nas variáveis de entrada mas
no recorte do **treino**, que gerou o vazamento temporal descrito na Seção 3.

---

## 3. Janela deslizante com corte pela data da resposta (*walk-forward*)

### 3.1 O que é

**Janela deslizante**, também chamada pelo termo em inglês ***walk-forward*** (literalmente "andar para a
frente"), é o método de avaliação usado neste projeto para simular, de forma honesta, o que teria
acontecido se o modelo estivesse operando ao vivo, semana após semana, no passado.

O procedimento, repetido para cada semana de avaliação:

1. Fixa-se uma **data de origem** no passado.
2. Treina-se o modelo usando **somente** as linhas da tabela cuja informação já era conhecida naquela
   data de origem.
3. Usa-se o modelo treinado para prever a data-alvo (data de origem + $h$ semanas).
4. Compara-se a previsão com o valor real que de fato ocorreu naquela data-alvo.
5. Avança-se a data de origem em uma semana e repete-se todo o processo, retreinando o modelo do zero a
   cada passo.

O nome "janela deslizante" vem do fato de que a fronteira entre "passado conhecido" e "futuro a prever"
desliza para a frente a cada iteração, sempre incluindo mais uma semana de histórico no treino.

### 3.2 Por que se usa esse método, e não uma divisão única treino/teste

Um método mais simples — separar a tabela uma única vez em "70% mais antigo para treinar, 30% mais recente
para testar" — erraria a pergunta que a tese precisa responder, que é operacional: "se este modelo
estivesse rodando toda semana desde 2024, o quão bem ele teria acompanhado uma epidemia que ainda estava
em andamento, sem ver o fim dela?". Só o *walk-forward*, retreinando a cada semana com o que era conhecido
até ali, reproduz essa condição.

### 3.3 A regra central: cortar pela data da **resposta**, não da **pergunta**

Aqui mora a distinção mais importante deste documento, e a fonte do maior erro metodológico já cometido
neste projeto.

Toda linha da tabela de treino carrega **duas datas**:

- a **data de origem** dessa linha (de onde vêm os atributos de entrada daquela observação de treino);
- a **data da resposta** dessa linha, que é a data de origem **mais o horizonte** — a data em que o valor
  que o modelo está tentando aprender a prever de fato aconteceu.

A regra correta, implementada na função `selecionar_treino_ja_respondido` do arquivo
`modelagem_aedes/motor/corte_temporal.py`, é: **uma linha só pode entrar no treino de uma previsão se a
data da resposta dessa linha já tiver acontecido na data de origem da previsão que está sendo feita.** Em
outras palavras, o modelo só pode aprender com exemplos cujo "gabarito" já era conhecido no momento em que
a previsão está sendo construída.

### 3.4 O vazamento temporal de 13/09/2026 — o mecanismo, passo a passo

Até **13/09/2026**, o código do projeto cortava o treino de forma diferente e incorreta: filtrava as linhas
por **posição** na tabela (as `N` linhas mais antigas), o que equivale, silenciosamente, a filtrar pela
**data de origem** de cada linha — não pela data da resposta.

Para um horizonte $h$, isso tem uma consequência exata: as **$h - 1$ linhas mais recentes que entravam no
treino** tinham data de resposta **posterior** à data de origem da previsão que estava sendo feita. Ou
seja, o modelo estava, sem que ninguém tivesse percebido, aprendendo com "gabaritos do futuro".

**FATO (medido em 13/09/2026, documentado em `analises/2026-09-13_correcao_vazamento_treino/`).** Um
exemplo real e concreto, para horizonte $h = 12$:

> Ao prever a data-alvo **26/05/2024** a partir da data de origem **03/03/2024**, o treino sob a regra
> antiga incluía a linha de origem **18/02/2024**. Essa linha, sob o horizonte de 12 semanas, tem como data
> de resposta **12/05/2024** — e o valor de casos confirmados registrado para essa data era **1.510
> casos**, exatamente o **pico da epidemia de 2024**.
>
> Só que, na data de origem real da previsão (**03/03/2024**), a semana de **12/05/2024** ainda estava a
> **dez semanas no futuro**. O número de 1.510 casos simplesmente não existia em 03/03/2024 — ninguém
> tinha como sabê-lo. O modelo, sob a regra antiga, treinava vendo esse número como se já fosse passado.

O efeito prático desse vazamento é o mesmo de "colar a resposta da prova antes de fazer a prova": o modelo
parece acertar mais no passado (porque literalmente decorou pedaços do futuro que vazaram para o treino),
mas essa performance não se sustenta quando o modelo é de fato colocado para prever o futuro de verdade,
onde esse vazamento não pode existir.

**Custo medido do vazamento, na configuração de referência usada naquele teste:** corrigir o corte (passar
a cortar pela data da resposta) custou **+31,5%** de erro absoluto médio (ver Seção 5 adiante) em $h = 4$ e
**+52,5%** em $h = 12$ — arredondado neste documento para **+52%**, conforme o número canônico já
registrado nos documentos vivos do projeto. O coeficiente de determinação (ver Seção 6) em $h = 12$ caiu de
**0,758**, sob a regra vazada, para **0,437**, sob a regra corrigida — o número que aparece hoje no painel
oficial de erro. **152 células de resultado foram re-executadas** para propagar a correção por toda a
bateria de testes do projeto.

### 3.5 Por que isso não é um detalhe técnico menor

Um vazamento temporal não é um bug qualquer: ele infla artificialmente a performance medida do modelo de
uma forma que só aparece quando alguém tenta reproduzir o resultado em produção — ou seja, exatamente
quando o erro é mais caro. É por isso que a regra de corte por data da resposta, e não por posição, é hoje
um **invariante** do projeto (documentado no `CLAUDE.md` raiz do repositório): nenhuma rodada nova pode
reintroduzir esse corte por posição sem correr o mesmo risco.

---

## 4. Árvores de decisão e *boosting*

### 4.1 O que é uma árvore de regressão

Uma **árvore de decisão para regressão** (uma árvore cuja saída é um número contínuo, como "número de
casos", em vez de uma categoria) é um modelo que faz uma previsão através de uma sequência de perguntas
do tipo "sim ou não" sobre os atributos de entrada, organizadas numa estrutura em forma de árvore
invertida: começa numa **raiz** (o topo), faz perguntas em cada **nó interno**, e termina numa **folha**
(o fim de um ramo), onde mora o número que será a previsão.

**Exemplo simplificado, com dados reais deste projeto.** Considere quatro semanas de treino, com o índice
de mosquito por armadilha (`aedes_aegypti_por_armadilha`, a razão entre o número de mosquitos *Aedes
aegypti* fêmea capturados e o número de armadilhas vistoriadas naquela semana) e o número de casos
confirmados 12 semanas depois:

| Semana de origem | Índice de mosquito por armadilha | Casos 12 semanas depois |
|---|---|---|
| 23/09/2012 | 0,057 | (baixo) |
| 30/09/2012 | 0,028 | (baixo) |
| 07/10/2012 | 0,038 | (baixo) |
| 14/10/2012 | 0,060 | (baixo) |

Uma árvore muito simples, de uma única pergunta, poderia ser:

```
                    o índice de mosquito por armadilha
                         é maior que 0,050 ?
                        /                    \
                     SIM                     NÃO
                      |                       |
              folha: previsão A       folha: previsão B
           (média dos casos das       (média dos casos das
            semanas de treino         semanas de treino
            com índice > 0,050)       com índice ≤ 0,050)
```

Uma árvore de verdade, como as usadas neste projeto, encadeia dezenas dessas perguntas, cada uma dividindo
o espaço de possibilidades em regiões cada vez menores, até chegar a uma folha.

### 4.2 O que é um conjunto de árvores e o que o *gradient boosting* faz

Uma única árvore de regressão costuma ser um modelo fraco — impreciso e instável. A solução usada neste
projeto é combinar **muitas árvores pequenas** numa técnica chamada **impulsionamento de gradiente** (em
inglês *gradient boosting*).

A ideia do *gradient boosting*, de forma sequencial:

1. A primeira árvore faz uma previsão inicial simples (por exemplo, a mediana de todos os casos vistos no
   treino).
2. Calcula-se o **erro residual** — quanto cada previsão errou em relação ao valor real.
3. Uma segunda árvore é treinada não para prever o número de casos diretamente, mas para prever **esse
   erro residual**.
4. A previsão da segunda árvore é somada, com um peso pequeno, à previsão da primeira.
5. Repete-se o processo: cada nova árvore aprende a corrigir o que restou de erro depois de todas as
   árvores anteriores, e sua contribuição também entra com peso pequeno.

O resultado final é a soma ponderada de todas as árvores. Cada árvore individual é fraca e simples, mas a
soma de centenas delas, cada uma corrigindo o erro da anterior, forma um modelo forte.

### 4.3 O algoritmo específico usado neste projeto: `HistGradientBoostingRegressor`

O modelo usado como cenário adotado deste projeto é o `HistGradientBoostingRegressor`, uma implementação de
*gradient boosting* disponível na biblioteca **scikit-learn** (uma biblioteca de código aberto para
aprendizado de máquina em linguagem Python). O prefixo "Hist" vem de *histogram-based* — em vez de avaliar
todo valor possível de cada atributo para decidir onde dividir um nó, o algoritmo agrupa os valores em
faixas (um histograma), o que o torna mais rápido em bases de dados maiores, sem mudar a lógica de fundo
descrita acima.

Os hiperparâmetros do cenário adotado (a diferença entre hiperparâmetro e parâmetro é definida na Seção
17) são:

- **`max_iter = 250`**: o número total de árvores que compõem o conjunto — 250 rodadas de correção
  sequencial.
- **`learning_rate = 0,05`** (**taxa de aprendizado**): o peso com que a previsão de cada nova árvore é
  somada às anteriores. Um valor baixo, como 0,05, significa que cada árvore corrige apenas 5% do erro que
  encontrou, deixando o ajuste fino e gradual — isso reduz o risco de o modelo se ajustar demais ao ruído
  de qualquer árvore individual (fenômeno chamado de **sobreajuste**, quando o modelo decora peculiaridades
  do treino que não se repetem em dados novos).
- **`max_leaf_nodes = 15`**: o número máximo de folhas permitido em cada árvore individual — limita a
  complexidade de cada árvore isolada a, no máximo, 15 regiões finais de previsão.
- **`min_samples_leaf = 5`**: toda folha precisa conter pelo menos 5 semanas de treino. Isso impede que uma
  árvore crie uma folha baseada numa única semana atípica (por exemplo, uma única semana de enchente), o
  que reduziria a capacidade do modelo de generalizar.

### 4.4 Por que uma árvore não extrapola — e por que isso importa para prever picos

Este é o ponto mais importante desta seção para entender as limitações medidas do modelo (discutidas na
Parte 4 do documento completo).

Uma árvore de decisão só consegue produzir, como previsão, **valores que já apareceram nas folhas
construídas a partir do treino** — ou seja, médias (ou quantis, ver Seção 7) de subconjuntos de valores
**já observados no passado**. Uma árvore nunca produz um número maior do que o maior valor de treino que
caiu numa folha, porque a folha é, por construção, uma agregação de valores observados.

Isso é fundamentalmente diferente de, por exemplo, uma reta ajustada por regressão linear, que pode
projetar um valor além do que já foi visto, simplesmente estendendo a reta. Uma árvore — e, por extensão,
um conjunto de árvores como o `HistGradientBoostingRegressor` — **não extrapola**: se o treino de uma dada
data de origem nunca viu uma semana com mais de, digamos, 1.500 casos, a árvore não vai prever, para
nenhuma entrada, um número muito acima disso, porque não existe folha com esse valor.

**Por que isso importa para prever picos de epidemia:** o início de uma epidemia nova é, por definição, o
momento em que os casos passam a ultrapassar tudo o que o treino já tinha visto até ali. É exatamente aí
que a limitação estrutural da árvore aparece com mais força — o modelo tende a **subestimar picos que são
maiores do que qualquer pico anterior da série de treino**. Essa é uma leitura consistente com o resultado
medido de captura de pico de **0,388** em $h = 12$ (ver Parte 4), e com a subestimação sistemática discutida
na Seção 16.

---

## 5. Erro absoluto médio (*mean absolute error*, abreviado MAE)

### 5.1 A fórmula

O **erro absoluto médio**, em inglês *mean absolute error* (a partir daqui, MAE), mede o tamanho médio do
erro de uma previsão, em número de casos, sem se importar se o erro foi para cima ou para baixo.

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} \left| y_i - \hat{y}_i \right|
$$

Onde cada símbolo significa:

- $n$ — o número de semanas (pares previsão/real) avaliadas.
- $y_i$ — o valor **real** de casos confirmados na semana $i$.
- $\hat{y}_i$ — o valor **previsto** pelo modelo para a semana $i$.
- $| \cdot |$ — o valor absoluto: transforma qualquer diferença negativa em positiva, para que um erro "3
  casos a menos" e um erro "3 casos a mais" contem igual — ambos como erro de tamanho 3.
- $\sum_{i=1}^{n}$ — a soma de todos os $n$ termos.

### 5.2 Exemplo numérico, com três semanas reais deste projeto

Usando o **cenário adotado** (`HistGB_M1`, com vetor), horizonte $h = 4$, para três semanas consecutivas do
início da temporada de dengue de 2024 (fonte:
`analises/2026-09-25_segunda_bateria_noturna/A_resultados_em_2026/saidas/previsoes_por_braco.csv`):

| Data-alvo | Casos reais ($y_i$) | Previsto ($\hat y_i$) | Erro absoluto $\lvert y_i - \hat y_i \rvert$ |
|---|---|---|---|
| 11/02/2024 | 156 | 86,76 | 69,24 |
| 18/02/2024 | 249 | 349,46 | 100,46 |
| 25/02/2024 | 558 | 468,53 | 89,47 |

$$
\text{MAE} = \frac{69,24 + 100,46 + 89,47}{3} = \frac{259,17}{3} = 86,39
$$

Ou seja, nessas três semanas, o modelo errou, em média, por **86,39 casos** — às vezes para menos (na
semana de 11/02, previu 86,76 quando o real foi 156, um erro de 69,24 casos para baixo), às vezes para
mais (em 18/02, previu 349,46 quando o real foi 249, um erro de 100,46 casos para cima).

### 5.3 Por que o MAE é minimizado pela mediana, não pela média

Este é um fato matemático sobre a função MAE, não uma medida deste projeto: dentro de um conjunto de
valores observados, o número que **minimiza** a soma dos erros absolutos contra todos eles é a **mediana**
desse conjunto (o valor que fica exatamente no meio quando os dados são ordenados), e não a média
aritmética.

A intuição: mover a previsão um pouco em direção a qualquer ponto reduz o erro absoluto de todos os
valores reais que ficam **daquele lado**, e aumenta o erro de todos os que ficam do lado oposto, na mesma
proporção de "um caso por caso movido". O ponto de equilíbrio — onde mover para qualquer lado deixa de
ajudar mais do que atrapalha — é exatamente o ponto que tem metade das observações de cada lado: a
mediana.

**Uma nuance importante deste projeto:** o cenário adotado não prevê a mediana (o quantil 0,50, ver Seção
7) — ele prevê o **quantil 0,85**, uma escolha deliberada de política, explicada em detalhe na Seção 8 e na
Seção 9. Isso significa que o MAE do painel oficial (Seção 5.2 e a tabela de erro da Parte 1) **não é o
menor MAE que o modelo poderia, em tese, alcançar** se estivesse otimizado para minimizar exatamente essa
métrica — ele é o MAE de um modelo que foi deliberadamente enviesado para cima, porque o objetivo real não
é acertar o valor mais provável, e sim errar para o lado mais seguro quando o assunto é vigilância de
surto. Essa é a diferença central entre "métrica de avaliação" (o que se usa para comparar modelos depois
de prontos) e "função de perda de treino" (o que o modelo de fato otimiza durante o ajuste) — elas não
precisam ser a mesma coisa, e neste projeto não são.

---

## 6. Coeficiente de determinação (R²)

### 6.1 A fórmula

O **coeficiente de determinação**, normalmente representado por **R²** (lido "R ao quadrado"), mede que
fração da variação dos valores reais o modelo consegue explicar, numa escala que vai (na prática, para
bons modelos) de 0 a 1.

$$
R^2 = 1 - \frac{\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{n} (y_i - \bar{y})^2}
$$

Onde:

- $y_i$, $\hat{y}_i$ e $n$ têm o mesmo significado da Seção 5.
- $\bar{y}$ — a **média** de todos os valores reais $y_i$ no conjunto avaliado.
- O numerador, $\sum (y_i - \hat{y}_i)^2$, é a soma dos erros do modelo **ao quadrado** — chamada de soma
  dos quadrados dos resíduos.
- O denominador, $\sum (y_i - \bar{y})^2$, é a soma dos quadrados da diferença entre cada valor real e a
  média de todos os valores reais — chamada de soma total dos quadrados. É, na prática, o erro que um
  modelo "preguiçoso", que sempre prevê a média de tudo, cometeria.

Em palavras: R² compara o erro do modelo contra o erro de um modelo trivial que sempre chuta a média. Um
R² de **1** significa erro zero. Um R² de **0** significa que o modelo é tão bom quanto sempre chutar a
média. Um R² **negativo** significa que o modelo é **pior** do que simplesmente chutar a média — o
denominador fica maior que o numerador dividido, mas com o sinal invertido pelo "1 menos".

### 6.2 O que significam os números medidos: 0,898 e 0,437

**FATO (avaliação de 01/01/2024 até aproximadamente 01/02/2026, cenário adotado):**

- Em $h = 1$ (uma semana à frente), **R² = 0,898**: o modelo explica quase 90% da variação semana a semana
  dos casos reais — um ajuste forte, esperado quando o horizonte é curto e a semana de origem já carrega
  muita informação sobre a semana seguinte (a dengue não salta de 50 para 2.000 casos em sete dias).
- Em $h = 12$ (três meses à frente), **R² = 0,437**: o modelo explica menos da metade da variação. Em três
  meses, muita coisa pode mudar — o início ou o fim de uma epidemia, uma chuva atípica — e a informação
  disponível na data de origem perde força explicativa.

### 6.3 Por que o R² pode enganar numa série sazonal

**HIPÓTESE, sustentada pela comparação com as réguas simples (não é uma medição isolada, mas uma leitura
sobre medições já feitas — ver Parte 4):** um R² alto numa série com **forte padrão sazonal**, como a
dengue em Porto Alegre (que sobe e desce com as estações do ano, todo ano, de forma parecida), pode
refletir principalmente a capacidade do modelo de reproduzir esse padrão sazonal repetitivo — e não
necessariamente uma capacidade de prever o que é **novo** e imprevisível em cada temporada (o tamanho
exato do pico, o mês exato em que ele ocorre).

A evidência que sustenta essa leitura: a **régua sazonal** — uma regra simples que apenas repete o valor de
casos que ocorreu na mesma semana do ano anterior, sem nenhum aprendizado de máquina, descrita em detalhe
na Parte 4 — também acompanha o formato sazonal da série. Isso significa que parte do R² alto de qualquer
modelo (inclusive um "chute" tão simples quanto repetir o ano passado) vem de grátis, só por a série ser
sazonal. Um R² isolado, sem comparação com uma régua sazonal, não diz se o modelo está de fato aprendendo
algo além do padrão calendário repetitivo — por isso este projeto reporta R² sempre ao lado do MAE contra
réguas (Parte 4), nunca sozinho.

---

## 7. Quantil

### 7.1 Definição

Um **quantil** de nível $\tau$ (a letra grega *tau*, um número entre 0 e 1) de um conjunto de valores é o
número que **divide** esse conjunto de tal forma que uma fração $\tau$ dos valores fica **igual ou abaixo**
dele, e a fração restante, $1 - \tau$, fica **acima**.

Exemplos de nomes usuais: o quantil 0,50 é a **mediana** (metade abaixo, metade acima). Os quantis 0,25 e
0,75 são chamados de **primeiro e terceiro quartil**. O quantil 0,90 é também chamado de **percentil 90**
(quando expresso em base 100 em vez de base 1).

### 7.2 Exemplo numérico com dados deste projeto

Considere os quatro primeiros valores de captura de *Aedes aegypti* por armadilha da tabela oficial,
ordenados do menor para o maior:

$$
0,027635 \; ; \; \; 0,038402 \; ; \; \; 0,056795 \; ; \; \; 0,059659
$$

O quantil 0,50 (a mediana) desse conjunto de 4 valores fica entre o segundo e o terceiro valor ordenados —
pela convenção usual de interpolação linear, é a média dos dois valores centrais:
$(0,038402 + 0,056795) / 2 = 0,047599$. Isso significa: metade dessas quatro semanas teve captura igual ou
abaixo de 0,047599 por armadilha, e a outra metade, igual ou acima.

### 7.3 O que significa o quantil 0,85 de uma previsão

Quando o cenário adotado deste projeto produz "a previsão do quantil 0,85 para a data-alvo X", o
significado é: **o modelo está estimando o número de casos abaixo do qual, segundo o que ele aprendeu com
o padrão histórico de erro, 85% dos desfechos possíveis para aquela semana deveriam ficar — deixando 15% de
chance de o valor real ficar acima desse número previsto.**

Isso é fundamentalmente diferente de "o modelo acha que o valor mais provável é X". O quantil 0,85 é, por
construção, um número **deliberadamente mais alto** do que o valor mais provável (a mediana, quantil 0,50),
porque ele está reservando uma margem de segurança contra os 15% de cenários em que a realidade supera a
previsão. A razão de se escolher justamente 0,85, e não 0,50, é o assunto central das Seções 8 e 9.

---

## 8. Perda quantílica (*pinball loss*)

### 8.1 O que é uma função de perda

Antes da fórmula: uma **função de perda** é a fórmula que um algoritmo de aprendizado de máquina tenta
**minimizar** durante o treino. É o "placar" que o algoritmo usa para decidir, entre duas previsões
possíveis, qual é melhor. A Seção 5.3 mostrou que a função de perda "erro absoluto" é minimizada pela
mediana. A **perda quantílica**, em inglês ***pinball loss*** (literalmente "perda do pinball", porque o
gráfico dessa função lembra a mesa de um fliperama de pinball, em forma de V assimétrico), generaliza essa
ideia: em vez de mirar sempre a mediana, ela permite mirar **qualquer quantil** $\tau$, penalizando
subestimação e superestimação de formas diferentes.

### 8.2 A fórmula

Para um único par (valor real $y$, valor previsto $\hat{y}$) e um quantil-alvo $\tau$:

$$
L_\tau(y, \hat{y}) =
\begin{cases}
\tau \cdot (y - \hat{y}) & \text{se } y \geq \hat{y} \text{ (o modelo subestimou)} \\
(1 - \tau) \cdot (\hat{y} - y) & \text{se } y < \hat{y} \text{ (o modelo superestimou)}
\end{cases}
$$

Onde:

- $y$ — o valor real observado.
- $\hat{y}$ — o valor previsto pelo modelo, mirando o quantil $\tau$.
- $\tau$ — o quantil-alvo (neste projeto, $\tau = 0,85$ no cenário adotado).
- $1 - \tau$ — o complemento do quantil-alvo (neste projeto, $1 - 0,85 = 0,15$).

Em palavras: quando o modelo prevê **abaixo** do que de fato aconteceu (subestimou, $y \geq \hat{y}$), o
erro é multiplicado por $\tau$. Quando o modelo prevê **acima** do que de fato aconteceu (superestimou,
$y < \hat{y}$), o erro é multiplicado por $1 - \tau$.

### 8.3 Exemplo numérico dos dois lados, com $\tau = 0,85$

**Caso 1 — o modelo subestimou.** Suponha uma semana com $y = 300$ casos reais e uma previsão
$\hat{y} = 200$ (o quantil 0,85 previsto ficou abaixo do que aconteceu):

$$
L_{0,85}(300, 200) = 0,85 \times (300 - 200) = 0,85 \times 100 = 85
$$

**Caso 2 — o modelo superestimou, no mesmo tamanho de erro.** Suponha agora $y = 200$ e $\hat{y} = 300$
(o quantil 0,85 previsto ficou 100 casos acima do que aconteceu):

$$
L_{0,85}(200, 300) = (1 - 0,85) \times (300 - 200) = 0,15 \times 100 = 15
$$

**A mesma distância de 100 casos gera uma penalidade 5,67 vezes maior quando o erro é subestimar do que
quando é superestimar.**

### 8.4 A razão de penalidade e por que ela é uma decisão de política, não uma escolha técnica neutra

A razão entre as duas penalidades é:

$$
\frac{\tau}{1 - \tau} = \frac{0,85}{0,15} = 5,\overline{6} \approx 5,67
$$

Esse número, **5,67**, está literalmente escrito, através da escolha de `quantile=0,85` no código do
cenário adotado. Ele significa: **o código está dizendo ao modelo, durante todo o treino, que errar para
baixo é considerado 5,67 vezes mais grave do que errar para cima, no mesmo tamanho de erro.**

Essa não é uma propriedade "objetiva" dos dados de dengue — é uma **decisão de produto** embutida no
código, equivalente a decidir, antes de qualquer treino, que o custo de um alarme perdido (o modelo diz
"vai ficar tranquilo" e uma epidemia acontece) é maior do que o custo de um alarme falso (o modelo diz "vai
complicar" e a semana passa calma). A escolha de $\tau = 0,85$ e não, por exemplo, $\tau = 0,95$ (razão
19) ou $\tau = 0,65$ (razão 1,86), determina o quanto o modelo será, por construção, enviesado para cima.

---

## 9. A equivalência quantil ↔ probabilidade — o fundamento teórico de usar o modelo como alarme

Este é o ponto conceitual mais importante deste documento, porque é ele que sustenta, matematicamente, a
decisão central deste trabalho: usar a saída do modelo não como uma previsão pontual de "quantos casos vão
ter", e sim como um **alarme binário** de "vai ou não vai passar de um limiar de importância operacional".

### 9.1 A afirmação

**Prever o quantil $\tau$ de uma variável e checar se essa previsão ultrapassa um limiar fixo $T$ é
matematicamente equivalente a estimar se a probabilidade de a variável real ultrapassar $T$ é maior do que
$1 - \tau$.**

Para o caso deste projeto, com $\tau = 0,85$:

$$
\hat{q}_{0,85} > T \quad \Longleftrightarrow \quad P(y > T) > 0,15
$$

### 9.2 A derivação

Por definição (Seção 7.1), o quantil $\tau$ de uma variável aleatória $y$, chamado $q_\tau$, é o valor que
satisfaz:

$$
P(y \leq q_\tau) = \tau \qquad \Longleftrightarrow \qquad P(y > q_\tau) = 1 - \tau
$$

Agora, a pergunta operacional que interessa é: dado um limiar fixo de importância $T$ (por exemplo, o
Limite de Mobilização do plano municipal, 140 casos — ver Parte 3), **qual é a probabilidade de o valor
real ultrapassar $T$?**

A relação entre quantil e probabilidade de excedência é **monótona**: quanto maior o quantil que se
escolhe olhar, menor é a probabilidade de superá-lo (porque um quantil mais alto já "reservou" mais espaço
abaixo de si). Formalmente, se $q_\tau > T$ — ou seja, se o próprio quantil $\tau$-ésimo já está acima do
limiar $T$ — então, necessariamente:

$$
P(y > T) \geq P(y > q_\tau) = 1 - \tau
$$

Essa desigualdade vem diretamente da definição de quantil: se $T$ é menor que $q_\tau$, então todo cenário
em que $y$ supera $q_\tau$ também supera $T$ (superar o valor mais alto implica superar o mais baixo), mas
podem existir cenários adicionais em que $y$ fica entre $T$ e $q_\tau$, que também contam como "$y$ superou
$T$" mas não entram em "$y$ superou $q_\tau$". Logo $P(y > T)$ só pode ser **maior ou igual** a
$P(y > q_\tau)$, nunca menor.

Substituindo $\tau = 0,85$:

$$
\hat{q}_{0,85} > T \quad \Longrightarrow \quad P(y > T) \geq 1 - 0,85 = 0,15
$$

**Portanto: sempre que a previsão do quantil 0,85 do modelo ultrapassa um limiar $T$, isso é uma
declaração — sustentada pela própria definição matemática de quantil, não uma opinião do modelo — de que a
probabilidade estimada de a realidade ultrapassar $T$ é de pelo menos 15%.**

### 9.3 Por que isso é o fundamento de usar o modelo como alarme, e não como previsão de valor

A consequência prática dessa derivação é que **o número que o modelo produz não deveria ser lido, e nunca
é usado neste projeto, como "o modelo acha que vai ter exatamente X casos"**. A leitura correta, e a única
sustentada pela matemática acima, é binária: **"a probabilidade estimada de superar o limiar $T$ é maior
que 15%" — sim ou não**, dependendo de a previsão do quantil 0,85 estar acima ou abaixo de $T$.

Essa é exatamente a arquitetura de decisão descrita no artigo de referência sobre **Porto Rico** (Seção
"Literatura" da Parte 1, e detalhado na Parte 5 deste documento): ali, o limiar epidêmico oficial também é
definido como um quantil de uma distribuição ajustada aos dados históricos (o percentil 75 de uma regressão
ajustada a quase 40 anos de série), e o uso operacional do modelo é checar se a série atual ultrapassa esse
quantil — nunca usar a regressão para "prever o número exato de casos da semana que vem". A metodologia
deste projeto usa o mesmo princípio matemático, aplicado com os limiares (140, 421 e 702 casos) do Plano
Municipal de Contingência de Arboviroses de Porto Alegre em vez do limiar estatístico interno de Porto
Rico.

**HIPÓTESE (leitura teórica, não uma medição isolada — mas coerente com todos os resultados de alarme
medidos na Parte 4):** é essa equivalência que explica **por que o modelo funciona melhor como alarme do
que como estimativa de magnitude**. Como alarme, ele só precisa acertar de que lado do limiar $T$ a
realidade vai cair — uma pergunta binária, mais fácil. Como estimativa de magnitude, ele precisa acertar o
**tamanho exato** do desvio acima do limiar, que é onde a limitação estrutural de não-extrapolação da
árvore (Seção 4.4) e o viés medido de subestimação de picos (Seção 16) pesam mais.

---

## 10. Intervalo de previsão e cobertura

### 10.1 O que é um intervalo de previsão

Um **intervalo de previsão** de nível $c$ (por exemplo, $c = 90\%$) é um par de números — um limite
inferior e um limite superior — construído de tal forma que, **se o modelo estiver bem calibrado**, o
valor real deveria cair dentro desse intervalo em $c\%$ das semanas avaliadas.

Neste projeto, um intervalo de $90\%$ é construído a partir de dois quantis simétricos: o quantil 0,05 como
limite inferior e o quantil 0,95 como limite superior (deixando $5\% + 5\% = 10\%$ de fora, dos dois
lados). Um intervalo de $50\%$ usa os quantis 0,25 e 0,75.

### 10.2 O que é cobertura observada, e a diferença para a cobertura nominal

A **cobertura nominal** é o valor de $c$ que o intervalo promete, pela sua própria construção (90% ou 50%).
A **cobertura observada** é a fração de semanas, num conjunto real de avaliação, em que o valor que de
fato ocorreu caiu dentro do intervalo. Se o modelo estivesse perfeitamente calibrado, cobertura observada e
cobertura nominal deveriam coincidir. Na prática, quase nunca coincidem exatamente — a pergunta é o quão
longe ficam.

### 10.3 Exemplo com os números medidos deste projeto

**FATO (medido em 26/09/2026, `analises/2026-09-26_calibracao_por_faixa/`), cenário adotado:**

- Nas semanas de **calmaria** (0 a 20 casos reais, 814 semanas na amostra), o intervalo de $90\%$ nominal
  cobriu **90,5%** das semanas — muito próximo do prometido. O modelo está bem calibrado quando a situação
  é tranquila.
- Nas semanas de **Alerta ou mais** (acima de 421 casos reais, 163 semanas na amostra), o mesmo intervalo
  de $90\%$ nominal cobriu apenas **17,8%** das semanas — ou seja, em **82,2%** das semanas de epidemia
  forte, o valor real caiu **fora** do intervalo que deveria contê-lo com 90% de confiança.

Isso significa, concretamente: o modelo "sabe" o tamanho do seu próprio erro quando a cidade está calma,
mas subestima drasticamente esse erro (produz intervalos estreitos demais) exatamente nas semanas em que
saber o tamanho do erro mais importaria — durante uma epidemia. Este ponto é retomado com mais detalhe na
Seção 16 (viés contra variância).

---

## 11. Escore de intervalo ponderado (*weighted interval score*, WIS)

### 11.1 Por que existe uma métrica além do MAE

O MAE (Seção 5) avalia apenas **um número por semana** — a previsão pontual. Mas o cenário adotado produz,
na verdade, **sete números por semana** (as previsões dos quantis 0,05; 0,10; 0,25; 0,50; 0,75; 0,90 e
0,95), formando uma **distribuição inteira** de possibilidades, não um único palpite. O **escore de
intervalo ponderado**, em inglês *weighted interval score* (a partir daqui, WIS), proposto por **Bracher,
Ray, Gneiting e Reich (2021)**, é a métrica desenhada para avaliar essa distribuição inteira de uma só vez,
penalizando ao mesmo tempo: intervalos largos demais (imprecisão), intervalos estreitos demais que erram o
valor real (excesso de confiança) e o erro do valor central.

Essa é a razão de o WIS ser a **métrica oficial usada nos sprints brasileiros de previsão de dengue** (uma
competição anual, promovida por pesquisadores de saúde pública, em que diferentes equipes submetem
previsões semanais e são ranqueadas pelo WIS): ela recompensa não só "acertar o número", mas também "saber
o tamanho certo da própria incerteza".

### 11.2 A fórmula completa

Para uma única semana, com $K$ intervalos de previsão de níveis diferentes (por exemplo, $K = 2$: o
intervalo de 50% e o de 90%) mais a previsão da mediana:

$$
\text{WIS} = \frac{1}{K + 0,5} \left[ 0,5 \cdot |y - m| + \sum_{k=1}^{K} w_k \cdot \text{IS}_k \right]
$$

Onde:

- $y$ — o valor real observado.
- $m$ — a previsão da **mediana** (o quantil 0,50).
- $K$ — o número de intervalos usados (neste exemplo, 2: o de 50% e o de 90%).
- $w_k$ — o **peso** do intervalo $k$, igual a $\alpha_k / 2$, onde $\alpha_k$ é a fração deixada de fora
  pelo intervalo (para o intervalo de 50%, $\alpha = 0,5$ e $w = 0,25$; para o de 90%, $\alpha = 0,10$ e
  $w = 0,05$).
- $\text{IS}_k$ — o **escore de intervalo** (*interval score*) do nível $k$, calculado como:

$$
\text{IS}_k = (u_k - l_k) + \frac{2}{\alpha_k}(l_k - y) \cdot \mathbb{1}[y < l_k] + \frac{2}{\alpha_k}(y - u_k) \cdot \mathbb{1}[y > u_k]
$$

  Onde $l_k$ e $u_k$ são os limites inferior e superior do intervalo de nível $k$, e $\mathbb{1}[\cdot]$ é
  um indicador que vale 1 se a condição entre colchetes for verdadeira e 0 caso contrário: o segundo termo
  só entra em ação se o valor real ficou **abaixo** do limite inferior (o modelo pecou por excesso de
  confiança para cima), e o terceiro termo só entra em ação se o valor real ficou **acima** do limite
  superior (o modelo pecou por excesso de confiança para baixo).

Em palavras: o escore de intervalo de cada nível é, quando o valor real cai **dentro** do intervalo, apenas
a **largura** do intervalo — um intervalo mais largo já é penalizado, mesmo acertando, porque é menos
informativo. Quando o valor real cai **fora**, soma-se ainda uma penalidade proporcional à distância entre
o valor real e o limite mais próximo que ele rompeu, ampliada pelo fator $2/\alpha_k$ (quanto mais estreito
o intervalo que foi rompido, maior a amplificação da penalidade).

### 11.3 Exemplo numérico completo, com uma semana real deste projeto

Semana-alvo **18/02/2024**, horizonte $h = 4$, cenário adotado (fonte:
`analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`). O valor real foi
$y = 249$ casos. As previsões de quantil dessa semana:

| Quantil | Previsão |
|---|---|
| 0,05 | 3,02 |
| 0,25 | 46,08 |
| 0,50 (mediana, $m$) | 191,46 |
| 0,75 | 301,72 |
| 0,95 | 398,43 |

**Passo 1 — o termo da mediana:**

$$
0,5 \cdot |y - m| = 0,5 \cdot |249 - 191,46| = 0,5 \cdot 57,54 = 28,77
$$

**Passo 2 — o intervalo de 50%** ($\alpha = 0,5$, $w = 0,25$, $l = 46,08$, $u = 301,72$). O valor real
($y=249$) caiu **dentro** do intervalo ($46,08 \leq 249 \leq 301,72$), então nenhuma penalidade extra se
aplica:

$$
\text{IS}_{50\%} = u - l = 301,72 - 46,08 = 255,64
$$
$$
w_{50\%} \cdot \text{IS}_{50\%} = 0,25 \times 255,64 = 63,91
$$

**Passo 3 — o intervalo de 90%** ($\alpha = 0,10$, $w = 0,05$, $l = 3,02$, $u = 398,43$). O valor real
também caiu **dentro** desse intervalo mais largo:

$$
\text{IS}_{90\%} = u - l = 398,43 - 3,02 = 395,41
$$
$$
w_{90\%} \cdot \text{IS}_{90\%} = 0,05 \times 395,41 = 19,77
$$

**Passo 4 — somar tudo e dividir por $K + 0,5 = 2,5$:**

$$
\text{WIS} = \frac{28,77 + 63,91 + 19,77}{2,5} = \frac{112,45}{2,5} = 44,98
$$

**O escore de intervalo ponderado dessa semana foi 44,98.** Note que, mesmo o valor real tendo caído
**dentro** dos dois intervalos (não houve nenhuma penalidade de "furo"), o WIS ainda não é zero: ele
também penaliza a **largura** dos intervalos e o erro da mediana. Um modelo que acertasse a mediana
exatamente e tivesse intervalos infinitamente estreitos teria WIS zero; qualquer largura ou erro custa
pontos.

### 11.4 Por que o WIS avalia a distribuição inteira, e não só um número

O MAE, sozinho, não consegue distinguir dois modelos que erram igual no valor central mas têm níveis de
confiança completamente diferentes — um que diz "vai dar entre 40 e 460 casos" e outro que diz "vai dar
entre 190 e 195 casos", ambos com mediana 191, seriam indistinguíveis pelo MAE se o valor real fosse igual
à mediana dos dois. O WIS distingue: o segundo modelo, mais estreito, teria um IS menor **se acertasse**,
mas seria brutalmente penalizado **se errasse** — exatamente o comportamento que se quer medir quando o
que importa não é só "o número típico", mas também "o modelo sabe o tamanho do que não sabe".

---

## 12. Classificação binária e alarme

### 12.1 A matriz de confusão

Quando a saída do modelo é usada como **alarme** (Seção 9) — uma resposta sim/não sobre se um limiar $T$
será ultrapassado — o resultado de cada semana avaliada cai em um de quatro quadrantes, organizados na
chamada **matriz de confusão**:

| | Real: surto aconteceu | Real: surto não aconteceu |
|---|---|---|
| **Alarme disse: vai passar** | Verdadeiro positivo (VP) | Falso positivo (FP) |
| **Alarme disse: não vai passar** | Falso negativo (FN) | Verdadeiro negativo (VN) |

- **Verdadeiro positivo (VP):** o alarme soou, e de fato houve surto. O acerto que mais importa.
- **Falso positivo (FP):** o alarme soou, mas não houve surto. Um **alarme falso** — custa recursos
  mobilizados sem necessidade.
- **Falso negativo (FN):** o alarme não soou, mas houve surto. O **pior erro possível** em vigilância — a
  cidade foi pega de surpresa.
- **Verdadeiro negativo (VN):** o alarme não soou, e de fato não houve surto. O acerto "silencioso".

### 12.2 As métricas derivadas

- **Sensibilidade** (também chamada de recall, ou taxa de verdadeiros positivos): entre todas as semanas em
  que **de fato houve surto**, que fração o alarme conseguiu capturar.

$$
\text{Sensibilidade} = \frac{\text{VP}}{\text{VP} + \text{FN}}
$$

- **Especificidade**: entre todas as semanas em que **de fato não houve surto**, que fração o alarme
  corretamente deixou em silêncio.

$$
\text{Especificidade} = \frac{\text{VN}}{\text{VN} + \text{FP}}
$$

- **Precisão**: entre todas as vezes em que o alarme **soou**, que fração correspondeu a um surto real.

$$
\text{Precisão} = \frac{\text{VP}}{\text{VP} + \text{FP}}
$$

- **Alarmes falsos por ano**: uma tradução prática da precisão para a escala de "quantas vezes por ano a
  vigilância seria mobilizada à toa" — uma contagem, não uma fração.

- **Índice de Youden ($J$)**, proposto por William J. Youden em 1950, resume sensibilidade e
  especificidade num único número:

$$
J = \text{Sensibilidade} + \text{Especificidade} - 1
$$

  $J$ varia entre $-1$ e $1$: $J = 1$ significa um alarme perfeito (sensibilidade e especificidade ambas
  100%); $J = 0$ significa que o alarme não faz melhor do que um sorteio aleatório calibrado na mesma
  proporção de positivos da base; $J$ negativo significa que o alarme é **pior** que o acaso — ele erra
  sistematicamente mais do que acertaria por sorte.

### 12.3 Exemplo com os números medidos deste projeto, em $h = 4$

**FATO (avaliação 25/09/2026, evento "semana com mais de 100 casos confirmados", 2024 em diante, 102
semanas), cenário adotado, horizonte $h = 4$:** sensibilidade **97,1%**, precisão **94,3%**, **0,7**
alarmes falsos por ano, índice de Youden **0,94**.

Repare que a especificidade não é reportada diretamente na tabela do painel — mas pode ser **derivada**
diretamente da fórmula de Youden, já que $J = \text{Sensibilidade} + \text{Especificidade} - 1$ pode ser
reorganizada para:

$$
\text{Especificidade} = J - \text{Sensibilidade} + 1 = 0,94 - 0,971 + 1 = 0,969
$$

**Ou seja, em $h = 4$, o modelo tem sensibilidade de 97,1% (captura quase todo surto real de mais de 100
casos) e especificidade de 96,9% (raramente soa o alarme numa semana calma).** Isso é consistente com o
número absoluto de "0,7 alarmes falsos por ano" — menos de um por ano.

Para efeito de comparação, em $h = 12$ (três meses à frente), a mesma sensibilidade cai para **76,9%** e o
índice de Youden cai para **0,66** — o alarme de longo prazo é bem menos confiável do que o de curto prazo,
uma leitura consistente com a queda do R² e o aumento do MAE já vistos nas Seções 5 e 6.

---

## 13. Testes estatísticos

### 13.1 O que é uma hipótese nula

Um **teste estatístico** é um procedimento formal para responder à pergunta "a diferença que eu observei
entre dois grupos (por exemplo, o erro do modelo contra o erro de uma régua simples) é grande o bastante
para eu acreditar que é real, ou poderia ser só um acaso da amostra que eu tenho?".

Todo teste estatístico parte de uma **hipótese nula** ($H_0$): a afirmação conservadora, "de partida", de
que **não existe** diferença real entre os dois grupos comparados — qualquer diferença observada nos dados
seria puro efeito do acaso da amostragem. O teste tenta, então, acumular evidência **contra** essa
hipótese nula.

### 13.2 O que um p-valor é — e o que ele NÃO é

O **p-valor** é a probabilidade, **assumindo que a hipótese nula é verdadeira** (ou seja, assumindo que não
existe diferença real), de se observar uma diferença **tão grande quanto, ou maior do que**, a diferença
que de fato foi medida nos dados, só por efeito do acaso.

**O que o p-valor NÃO é, e este é um dos erros de interpretação mais comuns em ciência:** o p-valor **não
é** a probabilidade de a hipótese nula ser verdadeira. Um p-valor de 0,0001 não significa "há 0,01% de
chance de não haver diferença real" — significa "se não houvesse diferença real, seria muito raro (uma
chance em dez mil) observar, por acaso, uma diferença tão grande quanto a que apareceu nos dados". A
diferença entre essas duas frases é sutil, mas ela é exatamente o tipo de erro que este documento se
compromete a nunca cometer.

**Por que o $p < 0,0001$ citado neste documento faz sentido:** ele aparece na comparação, em $h = 4$, entre
o WIS do cenário adotado (e também do HistGB folha 20) contra o WIS da régua climatológica (2024-2025,
26/09/2026). Com $n = 96$ semanas pareadas e uma diferença consistente, semana após semana, a favor do
modelo (**215,4 contra 313,5** de WIS médio, uma diferença de quase 100 pontos), é esperado que o teste
retorne um p-valor extremamente pequeno — a diferença é grande e consistente o bastante para que "foi só
acaso" seja uma explicação improvável.

### 13.3 Teste pareado

Um **teste pareado** é aquele em que cada observação de um grupo tem uma correspondente exata no outro
grupo — neste projeto, cada semana avaliada gera **um par**: (erro do modelo naquela semana, erro da régua
naquela semana), sempre para a **mesma data-alvo**. Isso é diferente de comparar duas amostras
independentes (por exemplo, "os erros do modelo em 2024" contra "os erros da régua em 2025", sem
correspondência semana a semana) — comparar por pares controla o fato de que algumas semanas são
"inerentemente mais difíceis de prever" para qualquer método, isolando melhor a diferença atribuível ao
método em si. Esta é uma regra invariante do projeto (ver `CLAUDE.md` raiz): **comparação entre modelos é
sempre pareada por data-alvo, ou não vale.**

### 13.4 Teste de Wilcoxon para postos sinalizados

O **teste de Wilcoxon para postos sinalizados** (proposto por Frank Wilcoxon em 1945) é um teste pareado
que não assume que as diferenças entre os pares seguem uma distribuição específica (como a distribuição
normal) — ele funciona ordenando o **tamanho** das diferenças (ignorando o sinal) do menor para o maior,
atribuindo um **posto** (1º, 2º, 3º...) a cada diferença, e depois somando os postos separadamente para as
diferenças positivas e negativas. Se o modelo A é sistematicamente melhor que o modelo B, a maioria das
diferenças grandes deve ter o mesmo sinal, o que desequilibra a soma dos postos de um lado. É o teste usado
neste projeto para comparar o WIS do modelo contra o WIS da régua, par a par, semana a semana.

### 13.5 Teste de McNemar exato

O **teste de McNemar** (proposto por Quinn McNemar em 1947) é o teste usado quando a comparação é entre
dois métodos de **classificação binária** (Seção 12) — por exemplo, "o alarme do modelo soou ou não" contra
"o alarme da régua soou ou não" — pareados semana a semana.

**A ideia central, que precisa de ênfase: só os pares em que os dois métodos discordam entram no teste.**
Se, numa dada semana, tanto o modelo quanto a régua acertaram (ou ambos erraram) da mesma forma, essa
semana não carrega nenhuma informação sobre qual dos dois é melhor — ela é descartada do cálculo. O teste
de McNemar olha apenas para as semanas **discordantes**, divididas em duas categorias:

- $b$ = número de semanas em que o **modelo** acertou e a **régua** errou.
- $c$ = número de semanas em que a **régua** acertou e o **modelo** errou.

Sob a hipótese nula de que os dois métodos são igualmente bons, espera-se que, entre as semanas
discordantes, a divisão entre $b$ e $c$ seja próxima de 50/50 — se um dos dois métodos é de fato melhor,
a maioria das discordâncias deveria pender para ele.

A **versão exata** do teste (usada neste projeto, em vez de uma aproximação por qui-quadrado, porque o
número de discordâncias é pequeno demais para a aproximação ser confiável) calcula o p-valor diretamente
pela distribuição binomial, tratando cada discordância como um "lançamento de moeda" sob $H_0$:

$$
p = 2 \cdot \sum_{k=0}^{\min(b,c)} \binom{n}{k} \cdot 0,5^n \qquad \text{onde } n = b + c
$$

Onde $\binom{n}{k}$ (lido "$n$ escolhe $k$") é o número de combinações possíveis de $k$ elementos entre
$n$, e o fator 2 torna o teste **bicaudal** (considera desvios para qualquer um dos dois lados como
evidência contra $H_0$).

**Exemplo com os números medidos deste projeto — $h = 4$, cenário adotado contra a regra "hoje já passou de
100 casos"** (`mcnemar_holm.csv`, 25/09/2026): **15 semanas discordantes**, divididas **13 a 2** (13 vezes
o modelo acertou onde a régua errou; 2 vezes o oposto). Calculando o p-valor exato, com $n = 15$ e
$\min(b,c) = 2$:

$$
p = 2 \times \left[ \binom{15}{0} + \binom{15}{1} + \binom{15}{2} \right] \times 0,5^{15} = 2 \times \frac{1 + 15 + 105}{32.768} = 2 \times \frac{121}{32.768} \approx 0,00739
$$

Esse **0,00739** é o p-valor **bruto** (antes de qualquer correção — ver Seção 14). O painel oficial reporta
o p-valor **corrigido por Holm** para essa mesma comparação como **0,103**, que já leva em conta que essa
não é a única comparação feita (ver Seção 14.4 para a reconciliação exata desses dois números).

---

## 14. O problema das comparações múltiplas e a correção de Holm

### 14.1 Por que testar muitas hipóteses ao mesmo tempo produz falsos positivos esperados

Cada teste estatístico individual, feito a um limiar de significância de 5% (a convenção usual: "considero
uma diferença real se o p-valor for menor que 0,05"), tem, por construção, **5% de chance de acusar uma
diferença que não existe**, mesmo quando a hipótese nula é verdadeira — é a definição de p-valor da Seção
13.2 aplicada ao inverso.

Se, em vez de um teste, forem feitos **24 testes independentes** (o tamanho da família de testes do evento
de Alerta, 421 casos, citada na Parte 4 deste documento), e todos eles, na realidade, não tiverem diferença
nenhuma, a chance de **pelo menos um** desses 24 testes acusar, por puro acaso, um "p < 0,05" não é mais
5% — ela se aproxima de:

$$
1 - (1 - 0,05)^{24} \approx 1 - 0,292 = 0,708
$$

**Ou seja: com 24 testes, há cerca de 71% de chance de aparecer pelo menos um resultado "significativo" por
puro acaso, mesmo que nada de real esteja acontecendo.** Reportar esse resultado isolado, sem correção,
seria enganoso.

### 14.2 O procedimento de Holm, passo a passo

A **correção de Holm** (Sture Holm, 1979) é um método para ajustar os p-valores de uma família de $m$
testes, de forma a controlar a chance de **qualquer** falso positivo na família inteira, sendo menos
conservador (mais fácil de encontrar resultados reais) do que a correção mais simples de Bonferroni.

O procedimento:

1. Ordenar os $m$ p-valores **brutos** da família, do **menor** para o **maior**: $p_{(1)} \leq p_{(2)} \leq
   \dots \leq p_{(m)}$.
2. Multiplicar cada p-valor pelo número de testes que ainda "restam" a partir dele, contando de trás para
   frente: o menor p-valor é multiplicado por $m$, o segundo menor por $m - 1$, o terceiro por $m - 2$, e
   assim sucessivamente, até o maior, multiplicado por 1.
3. Impor que a sequência resultante seja **não decrescente** (se um p-valor ajustado ficar menor que o
   ajustado anterior na ordenação, ele é elevado até igualar o anterior) — isso garante que a ordem
   original dos p-valores brutos seja preservada nos p-valores ajustados.
4. Cortar em 1 qualquer valor que ultrapasse 1 (probabilidade não pode passar de 100%).

### 14.3 Exemplo simplificado, com cinco valores ilustrativos

Um exemplo didático, com números redondos e fictícios (não deste projeto, para isolar o mecanismo):
suponha uma família de 5 testes, com p-valores brutos $0,001$; $0,01$; $0,02$; $0,03$ e $0,20$.

| Posição (menor → maior) | p bruto | Multiplicador ($m$, $m{-}1$, ...) | p ajustado (bruto × mult.) | p de Holm final (impondo não decrescente) |
|---|---|---|---|---|
| 1º | 0,001 | 5 | 0,005 | 0,005 |
| 2º | 0,01 | 4 | 0,04 | 0,04 |
| 3º | 0,02 | 3 | 0,06 | 0,06 |
| 4º | 0,03 | 2 | 0,06 | 0,06 (empatado, pois 0,06 < 0,06 anterior não se aplica) |
| 5º | 0,20 | 1 | 0,20 | 0,20 |

Note como o menor p-valor (0,001) é multiplicado pelo tamanho inteiro da família (5), a penalidade mais
dura, enquanto o maior (0,20) não é multiplicado por nada (multiplicador 1) — o procedimento "gasta" a
correção mais pesada nos candidatos mais fortes primeiro.

### 14.4 Reconciliando o exemplo com os números reais do projeto

Usando as fórmulas das Seções 13.5, é possível **recalcular** os p-valores brutos das quatro comparações de
McNemar do evento "100 casos" citadas neste documento:

| Comparação | Discordantes | Divisão | p bruto (recalculado) | p de Holm (reportado no painel) |
|---|---|---|---|---|
| $h=12$ × "hoje já passou" | 37 | 31 a 6 | 0,0000413 | **0,00062** |
| $h=4$ × "hoje já passou" | 15 | 13 a 2 | 0,00739 | **0,103** |
| $h=12$ × "o ano passado" | 16 | 4 a 12 | 0,0768 | **0,845** |
| $h=4$ × "o ano passado" | 7 | 5 a 2 | 0,4531 | **1,000** |

Aplicando o procedimento da Seção 14.2 com o tamanho de família real usado nesse conjunto de testes
(**16 comparações**, feitas em 25/09/2026 — não apenas as 4 mostradas aqui), o menor p-valor bruto
recalculado, $0,0000413$, multiplicado por 16, dá $0,000661$ — **quase idêntico** ao $0,00062$ reportado
oficialmente (a pequena diferença vem de arredondamento na reconstrução manual acima). Isso confirma, por
reconstrução independente, que o painel oficial usa uma família de **16 testes**, não os 4 mostrados
isoladamente neste exemplo.

**Por que "p de Holm 0,103 em $h=4$" significa que não se pode afirmar vitória:** mesmo o modelo tendo
vencido 13 das 15 semanas discordantes contra a regra "hoje já passou de 100 casos" — um resultado que,
sozinho, pareceria forte —, depois de corrigir para o fato de que essa é uma entre 16 perguntas feitas
simultaneamente, a chance de esse resultado específico ter surgido por acaso deixa de ser desprezível
(**10,3%**). Como a convenção do projeto exige $p < 0,05$ para declarar significância, **o resultado não
sobrevive**, e o documento não pode afirmar que o alarme de 1 mês vence essa régua especificamente com
confiança estatística — mesmo reconhecendo que o desempenho bruto observado foi favorável ao modelo.

---

## 15. Correlação serial e reamostragem por blocos (*block bootstrap*)

### 15.1 Por que 39 semanas de surto não são 39 observações independentes

Muitos dos testes estatísticos apresentados nas Seções 13 e 14 assumem, na sua forma mais simples, que cada
observação (cada semana) é **independente** das outras — que saber o resultado de uma semana não ajuda a
prever o resultado da semana vizinha, a não ser pelo efeito que está sendo testado.

Essa suposição **não é verdadeira** para semanas de surto de dengue. **FATO (medido em 26/09/2026,
`analises/2026-09-26_...`):** ao limiar de 100 casos, as **39 semanas** identificadas como "semana de
surto" desde 2024 não estão espalhadas aleatoriamente — elas se concentram em apenas **2 blocos
contíguos** (sequências ininterruptas de semanas consecutivas acima do limiar), sendo o maior bloco de
**20 semanas seguidas**. Uma semana de surto quase sempre vem seguida de outra semana de surto — a série
tem **correlação serial** (dependência entre observações vizinhas no tempo).

Isso quebra a suposição de independência dos testes da Seção 13: se um teste trata essas 39 semanas como
39 "jogadas de moeda" independentes, ele está, na prática, contando o mesmo evento epidêmico várias vezes
como se fossem eventos diferentes — inflando artificialmente a confiança do resultado (deixando o p-valor
mais otimista do que deveria).

### 15.2 O que o *block bootstrap* faz

O **bootstrap** é uma técnica geral de reamostragem: em vez de calcular um p-valor por uma fórmula fechada
(como nas Seções 13.4 e 13.5), gera-se um grande número de amostras artificiais, sorteando **com reposição**
a partir dos dados observados, e observa-se a variação do resultado entre essas amostras artificiais para
estimar o quanto o resultado medido poderia variar só por acaso da amostragem.

O ***block bootstrap*** (bootstrap por blocos) adapta essa ideia para dados com correlação serial: em vez
de sortear **semanas individuais** com reposição (o que quebraria a dependência real entre semanas
vizinhas, fingindo que elas são independentes quando não são), sorteiam-se **blocos contíguos de várias
semanas seguidas** com reposição, preservando dentro de cada bloco sorteado a estrutura de dependência
real observada nos dados.

**FATO (medido em 26/09/2026):** este projeto testou blocos de **4, 8, 13 e 26 semanas**, com **2.000
reamostragens** por comprimento de bloco, usando uma semente aleatória fixa (**20260926**, um número
escolhido para permitir reprodução exata do mesmo sorteio por qualquer pessoa que rode o mesmo código).

### 15.3 O resultado: o quanto o p nominal fica otimista

O resultado é expresso como a **razão entre o p-valor obtido pelo bootstrap por blocos e o p-valor
nominal** (o p-valor calculado pela fórmula fechada, ignorando a correlação serial):

- Contra a régua "hoje já passou de 100 casos": a razão variou entre **0,0001 e 0,82** — o p-valor nominal
  já era, se algo, **conservador** (o bootstrap às vezes dá um p-valor até menor). Esse resultado é lido
  como **robusto**: a correlação serial não está inflando artificialmente a confiança nessa comparação
  específica.
- Contra a régua "o ano passado" (a régua sazonal): em $h=4$, a razão ficou entre **1,10 e 1,51**; em
  $h=12$, entre **2,11 e 3,44**. Isso significa que, ao contabilizar a correlação serial real da série, o
  p-valor verdadeiro poderia ser **até 3,44 vezes maior** do que o p-valor nominal calculado sem essa
  correção — um resultado lido como **otimista demais** quando reportado sem essa ressalva.

⚠️ **Uma pendência registrada com honestidade:** o teste de 13/09/2026 que apontou o único resultado do
projeto que sobrevive à correção de Holm (o vetor de captura de mosquito **piora** o alarme em $h=12$, p de
Holm 0,037) **não pôde ser re-testado** por bootstrap por blocos, porque as previsões semana a semana
daquela rodada específica não foram salvas em disco na época — só o resultado agregado. Isso significa que
esse resultado específico carrega uma incerteza adicional, não quantificada, sobre o quanto a correlação
serial poderia tê-lo inflado.

---

## 16. Viés contra variância

### 16.1 A distinção conceitual

**Viés** (em inglês *bias*) é um erro **sistemático e direcional** — o modelo erra consistentemente para o
mesmo lado, mesmo em média sobre muitas observações. **Variância**, neste contexto, é o erro que vem da
**instabilidade** do modelo — ele erra ora para um lado, ora para outro, sem um padrão de direção, mas com
tamanho imprevisível.

A distinção importa porque as duas coisas se **corrigem de formas diferentes**: variância se combate
aumentando os dados de treino, simplificando o modelo, ou — no contexto deste documento — alargando o
intervalo de previsão para acomodar a incerteza extra. Viés **não se corrige alargando o intervalo** — um
intervalo mais largo em torno de um centro sistematicamente errado continua sistematicamente errado, só
que com uma faixa maior ao redor do erro.

### 16.2 O exemplo medido: viés, não ruído

**FATO (medido em 26/09/2026, `analises/2026-09-26_...`, faixa "Alerta ou mais", acima de 421 casos reais,
163 semanas na amostra), cenário adotado:** o valor real **mediano** dessas semanas foi **917 casos**. O
**erro mediano** do modelo nessas mesmas semanas foi **539 casos** — e, como já discutido na Seção 16.3 do
raciocínio geral do documento (e no Item 5.3, sobre a natureza da subestimação estrutural do quantil
0,85 combinada com a não-extrapolação das árvores, Seção 4.4), esse erro é **sistematicamente para baixo**.

Isso significa que, numa semana típica dessa faixa, o modelo previu algo em torno de $917 - 539 = 378$
casos — **menos da metade** do que de fato ocorreu. Uma tradução concreta: é como uma secretaria de saúde
planejar recursos de resposta (leitos de observação, equipes de bloqueio, insumos de larvicida) para
receber **378 notificações** numa semana e, de fato, receber **917** — mais que o dobro do planejado.

**Por que isso é viés e não variância:** a largura do intervalo de 90% nessa mesma faixa foi de **592,7
casos** (Parte 4) — um intervalo já bastante largo. Se o problema fosse apenas variância (incerteza
simétrica e sem direção preferencial), um intervalo dessa largura, centrado corretamente, já cobriria a
maior parte dos desvios. O problema medido é outro: o **centro** do intervalo está deslocado
sistematicamente para baixo do valor real. **Alargar ainda mais o intervalo não resolve isso** — resolveria
apenas se o erro fosse aleatório e sem direção, o que não é o caso.

### 16.3 A consequência prática

Essa é a razão pela qual a correção conformal testada em 25/09/2026 (uma técnica que alarga
uniformemente os intervalos de previsão até atingir a cobertura nominal prometida) teve o efeito colateral
medido de aumentar os alarmes falsos de **15 para 124**: ao alargar o intervalo de forma **uniforme** para
compensar um problema que é, na faixa de epidemia, principalmente de **viés** (deslocamento do centro) e
não de variância (largura insuficiente ao redor de um centro correto), a correção "resolveu" a cobertura
numérica à custa de tornar o intervalo tão largo, em todas as faixas, que passou a incluir com frequência
o limiar de alarme mesmo em semanas calmas.

---

## 17. Hiperparâmetro contra parâmetro

### 17.1 A diferença

Um **parâmetro** é um número que o próprio algoritmo de treino **aprende automaticamente** a partir dos
dados — por exemplo, os valores de corte usados em cada nó de cada árvore, e os valores previstos em cada
folha, são parâmetros: eles emergem do processo de treino, olhando os dados.

Um **hiperparâmetro** é um número que precisa ser **decidido antes de começar o treino**, e que **controla
como o treino vai acontecer** — ele não é aprendido a partir dos dados, é uma escolha de configuração feita
por quem constrói o modelo. Os quatro números citados na Seção 4.3 (`max_iter`, `learning_rate`,
`max_leaf_nodes`, `min_samples_leaf`) são todos hiperparâmetros: nenhum deles é "descoberto" pelo
algoritmo — todos são escolhidos antes, e o algoritmo aprende os parâmetros (os cortes e valores de folha)
dentro das regras que esses hiperparâmetros impõem.

### 17.2 O que é busca aleatória de hiperparâmetros

Como não existe fórmula fechada que diga, de antemão, qual combinação de hiperparâmetros vai funcionar
melhor para um problema específico, uma forma de buscar uma boa combinação é a **busca aleatória**: sortear
um número grande de combinações diferentes de hiperparâmetros (dentro de faixas plausíveis definidas por
quem faz a busca), treinar um modelo completo para cada combinação sorteada, e comparar os resultados.

**FATO (medido em 25/09/2026, `analises/2026-09-25_busca_de_hiperparametros/`):** este projeto sorteou
**120 combinações** de hiperparâmetros — 60 para o `HistGradientBoostingRegressor` e 60 para um algoritmo
irmão chamado **LightGBM** (outra implementação de *gradient boosting*, de uma biblioteca diferente),
usando uma semente aleatória fixa (**20260925**) para reprodutibilidade, calibradas usando apenas o período
de 2022 a 2025 (para não "espiar" o período de avaliação oficial ao escolher a combinação vencedora).

**Nenhuma das 120 combinações sorteadas passou no critério de significância estatística** definido para a
busca (o menor p de Holm obtido, entre todas elas, foi **0,17** — acima do limiar de 0,05). Isso significa
que, mesmo testando um espaço amplo de configurações diferentes do mesmo tipo de algoritmo, nenhuma
conseguiu vencer as réguas de comparação com confiança estatística — um resultado negativo, mas informativo:
ele desloca a suspeita de "talvez os hiperparâmetros do cenário adotado sejam só uma escolha ruim" para
"o teto de desempenho desse tipo de algoritmo, com estes dados, parece estar perto de onde o cenário
adotado já está".
