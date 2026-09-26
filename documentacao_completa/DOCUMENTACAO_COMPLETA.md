# Previsão de casos de dengue em Porto Alegre a partir da rede de armadilhas de mosquito

## Documentação técnica completa

**Pesquisa de mestrado — Programa de Pós-Graduação em Computação, Universidade Federal do Rio Grande do Sul**
Orientador: Prof. Weverton Cordeiro · Início: setembro de 2025

**Versão de 26/09/2026**, após conferência número a número contra os arquivos de origem.

> Este documento foi escrito para ser lido por quem **não conhece o projeto** e pode **não trabalhar com
> aprendizado de máquina nem com epidemiologia**. Todo conceito é definido antes de ser usado, toda sigla
> é apresentada por extenso, e toda fórmula vem acompanhada de um exemplo numérico com dados reais desta
> pesquisa.

---

## Sumário

- **Parte 0 — Como ler este documento**
- **Parte 1 — O problema**
- **Parte 2 — Conceitos fundamentais**
- **Parte 3 — Os dados**
- **Parte 4 — Todos os modelos e abordagens testados**
- **Parte 5 — As hipóteses testadas e seus vereditos**
- **Parte 6 — A literatura e a comparação com o nosso resultado**
- **Parte 7 — Limiares oficiais e a justificativa de usar o modelo como alarme**
- **Parte 8 — Os resultados, com tradução concreta**
- **Parte 9 — Os três argumentos, limitações e próximos passos**
- **Anexos**

---

# Parte 0 — Como ler este documento

## 0.1 Para quem este documento foi escrito

Para alguém que **não conhece este projeto** e que pode **não trabalhar com aprendizado de máquina nem com
epidemiologia**. Nenhum conceito é dado como sabido. Todo termo técnico é definido na primeira vez que
aparece, antes de ser usado, e toda sigla é apresentada por extenso antes de ser abreviada.

Se em algum ponto o texto usar um conceito sem tê-lo definido antes, isso é um defeito do documento, não
uma falha do leitor.

## 0.2 O que este documento é, e o que não é

**É** o registro completo do que foi construído, testado, medido e concluído na pesquisa de mestrado sobre
previsão de casos de dengue em Porto Alegre a partir da rede de armadilhas de mosquito, até **26/09/2026**.

**Não é** um artigo, uma proposta nem uma peça de convencimento. Resultados negativos aparecem com o mesmo
destaque que os positivos, e em alguns casos com mais, porque são a maioria do que foi encontrado.

## 0.3 A convenção de fato e hipótese

Esta é a convenção mais importante do documento, e ela é seguida sem exceção.

- **FATO** — algo que foi medido, com o número e a data da medição. Se está marcado como fato, existe um
  arquivo no repositório que o produziu e, na maioria dos casos, uma certificação independente que o
  conferiu.
- **HIPÓTESE** — uma explicação plausível que **não** foi testada. Pode estar certa. Não foi verificada.
- **⚠️ RESSALVA** — uma limitação que precisa acompanhar a afirmação sempre que ela for citada, inclusive
  fora deste documento.
- **🚫 DESCARTADO** — algo que foi deliberadamente abandonado, com a data e quem decidiu. Existe para que
  a ideia não volte meses depois sem que ninguém lembre por que caiu.

Quando a evidência não sustenta uma afirmação, o documento diz isso. Não há afirmação sem o número que a
sustenta.

## 0.4 Três avisos que mudam a leitura de tudo

Estes três pontos aparecem repetidamente ao longo do texto. Vale conhecê-los antes de começar.

### Aviso 1 — a série tem apenas duas epidemias

**FATO (medido em 26/09/2026).** No período avaliado, as semanas com número alto de casos formam
**exatamente dois blocos contíguos**: um em 2024 e outro em 2025. Isso vale para qualquer limiar testado.

A consequência é severa e atravessa o documento inteiro: quando se lê "39 semanas de surto", o número de
**eventos independentes** não é 39, é **2**. Dois blocos de cerca de vinte semanas cada. Todo teste
estatístico deste projeto que trate semana como observação independente produz um valor otimista, e isso
está quantificado na Parte 2 e na Parte 8.

### Aviso 2 — a régua mais difícil de bater é trivial

Ao longo do documento, os modelos são comparados contra **réguas**: regras simples, sem aprendizado,
usadas como linha de base. A mais importante é a **régua sazonal**, que responde apenas *"quantos casos
houve nesta mesma semana do ano passado?"*.

**FATO.** Em horizonte de dois e três meses, essa régua **vence** o modelo. Isso não é uma falha de
implementação: é o que acontece quando a sazonalidade carrega quase toda a informação disponível. A
Parte 6 mostra que o mesmo padrão aparece na literatura internacional.

### Aviso 3 — não existe pergunta de tese fechada

A pesquisa está em **fase exploratória**, assumidamente. Em 26/09/2026 o pesquisador registrou que não há
uma pergunta de tese definida e que muitas frentes estão sendo testadas para descobrir onde há resultado.

Isso muda como os resultados devem ser lidos: cada rodada responde ao **instrumento que ela testou** —
previsão do número de casos, alarme de surto, medida de risco, priorização espacial — e **não** funciona
como veredito sobre a pesquisa inteira. Um resultado negativo na previsão do número de casos não é "a tese
caindo".

## 0.5 Como o documento está organizado

| Parte | O que responde | Leia se você quer |
|---|---|---|
| **1** | Qual é o problema, e por que Porto Alegre é um caso diferente | entender o contexto |
| **2** | O que significa cada conceito, fórmula e métrica usados | **começar por aqui, se os termos forem novos** |
| **3** | De onde vêm os dados, o que eles têm e o que lhes falta | avaliar a base empírica |
| **4** | Todos os modelos e abordagens testados, um a um | saber o que já foi tentado |
| **5** | Todas as hipóteses, com veredito, e o método de trabalho | avaliar o rigor |
| **6** | O que a literatura obteve, e como nos comparamos | situar o resultado |
| **7** | Os limiares oficiais e por que usar o modelo como alarme | entender a escolha central |
| **8** | Os resultados, com tradução do que cada número significa | ver as evidências |
| **9** | Os argumentos defensáveis, as limitações e o que vem depois | preparar a discussão |
| **Anexos** | Glossário, índice de análises e todas as fórmulas | consultar pontualmente |

**A Parte 2 é pré-requisito das Partes 6 a 9.** Quem pular os conceitos vai encontrar números sem saber o
que eles medem — e alguns deles, em particular o valor-p e a cobertura de intervalo, são exatamente os que
mais se prestam a interpretação errada.

## 0.6 Onde cada número deste documento foi produzido

Cada resultado citado vem de uma pasta datada no repositório, no formato
`analises/AAAA-MM-DD_descricao/`, e cada uma contém:

- uma **pré-declaração** escrita **antes** da execução, com a hipótese, a métrica, o critério de decisão e
  a família de correção estatística;
- o **código** que produziu o resultado e o registro da execução;
- uma **certificação** feita por um avaliador independente, cuja tarefa era tentar reprovar o resultado
  medindo do zero;
- as **emendas** datadas, quando algo mudou depois da pré-declaração.

O índice completo dessas pastas está no Anexo B. Esse método é, ele próprio, parte do que a pesquisa tem a
mostrar, e está descrito na Parte 5.

## 0.7 Uma nota sobre a linguagem

O documento evita adjetivos de propaganda. Não há "resultado robusto", "modelo poderoso" nem "abordagem
inovadora". Onde um resultado é forte, o número é apresentado e o leitor julga. Onde é fraco, o texto diz
que é fraco.

Também são evitadas **duplas negações** e construções que exigem reler para entender de que lado está a
afirmação. Quando o assunto é a ausência de um efeito, o texto diz diretamente o que foi medido e o que
não foi demonstrado.

---

# Parte 1 — O problema

## 1.1 A dengue, em uma página

A **dengue** é uma doença viral transmitida pela picada de fêmeas infectadas do mosquito *Aedes aegypti*.
O vírus não passa de pessoa para pessoa diretamente: ele precisa do mosquito como intermediário. Esse
intermediário é o que se chama de **vetor** — o organismo que carrega o agente infeccioso de um
hospedeiro a outro. Ao longo deste documento, "vetor" significa sempre o mosquito.

Quatro pontos dessa biologia explicam por que prever casos de dengue é difícil:

1. **O ciclo tem atrasos encadeados.** Um mosquito precisa picar alguém infectado, o vírus precisa se
   multiplicar dentro dele, ele precisa sobreviver e picar outra pessoa, e essa pessoa leva dias até
   apresentar sintomas. Entre a condição que favoreceu o mosquito e o caso registrado, passam semanas.
2. **Existem quatro sorotipos.** Um **sorotipo** é uma variante do vírus. Quem se infecta por um fica
   imune àquele para o resto da vida, mas continua suscetível aos outros três. Uma população pode estar
   coberta contra o sorotipo que circulou no ano passado e completamente exposta a um novo.
3. **A transmissão é fortemente sazonal.** No Sul do Brasil, calor e chuva do verão criam as condições
   para o mosquito; o inverno as interrompe. A curva de casos sobe e desce todo ano, de forma previsível
   no calendário e imprevisível na magnitude.
4. **Nem todo caso suspeito vira caso confirmado.** A confirmação depende de exame laboratorial, e a
   política de quem é testado muda conforme a situação epidemiológica. Isso significa que o próprio
   número que se tenta prever é produto de uma decisão administrativa, e não apenas da biologia.

## 1.2 Por que Porto Alegre é um caso diferente

A maior parte da literatura de previsão de dengue vem de lugares onde a doença é **endêmica** há décadas —
ou seja, circula de forma contínua e esperada na população. Singapura, Porto Rico, o Sudeste asiático e o
Nordeste brasileiro têm séries históricas de vinte, trinta ou quarenta anos.

**Porto Alegre não.** A cidade está na **fronteira de expansão** da dengue no Brasil: é uma capital
subtropical, no extremo sul do país, onde a doença passou a circular de forma relevante há poucos anos.

**FATO.** Entre 2018 e 2021 a cidade praticamente não teve casos. As epidemias começam em 2022 e ganham
escala em 2024 e 2025. Segundo o Plano Municipal de Contingência de Arboviroses de 2026 da Secretaria
Municipal de Saúde, os casos confirmados foram:

| Ano | Casos confirmados |
|---|---|
| 2022 | **5.144** |
| 2023 | **6.461** |
| 2024 | **17.686** |
| 2025 | **21.329** (parcial, até 20/11/2025) |

Essa trajetória cria uma situação específica, e ela é a raiz de quase todas as dificuldades relatadas
neste documento:

- **Há poucos exemplos do que se quer prever.** As epidemias grandes são duas.
- **A série é curta e, ao mesmo tempo, não é estacionária.** Uma série **estacionária** é aquela cujo
  comportamento estatístico não muda com o tempo. Aqui ele muda: a mesma cidade tinha quase nenhum caso em
  2019 e mais de vinte mil em 2025.
- **Os métodos padrão da vigilância pressupõem história que não existe aqui.** A Parte 7 mostra, com
  números medidos, o que acontece quando se aplica o instrumento clássico — o canal endêmico — a uma
  cidade nessa situação: ele produz limiares de zero fora da temporada, e o limiar sobe junto com a
  epidemia, normalizando exatamente o que deveria sinalizar.

## 1.3 A rede de armadilhas, e o que ela oferece

Porto Alegre opera uma rede de armadilhas de captura de mosquitos, do programa conhecido como MI-Aedes. As
armadilhas atraem e capturam fêmeas adultas do *Aedes aegypti*, que são contadas periodicamente. O
resultado é uma medida direta da presença do vetor na cidade, semana a semana.

Isso é incomum. A maioria dos estudos de previsão de dengue trabalha só com casos e com clima, porque
medir mosquito de forma sistemática é caro e trabalhoso. Porto Alegre tem essa medição desde **2012**, o
que dá uma série de captura de mais de uma década.

**A pergunta prática que motiva a pesquisa é:** essa medição direta do vetor melhora a capacidade de
antecipar o que vai acontecer com os casos de dengue na cidade?

⚠️ **Ressalva importante sobre o escopo.** Esta pergunta admite vários instrumentos de resposta — prever o
número de casos, disparar um alarme de surto, medir risco de transmissão, priorizar bairros, prever a
própria curva do mosquito. Este documento cobre principalmente os dois primeiros. Um resultado negativo em
um instrumento não responde pelos outros.

## 1.4 O que exatamente se tenta prever

**O alvo é o número de casos confirmados de dengue por semana em Porto Alegre**, contados pelo município
de **notificação** — isto é, o município onde o caso foi registrado, que pode diferir do município onde a
pessoa mora. Essa escolha foi decidida em 25/09/2026, para manter a comparabilidade com todos os
resultados anteriores do projeto.

A previsão é feita para **horizontes** de 1 a 12 semanas à frente. Um horizonte de 12 semanas corresponde
a aproximadamente **três meses**, que é o prazo de interesse declarado: é o tempo que a vigilância
precisaria para mobilizar ações antes de uma epidemia se instalar.

**FATO.** O horizonte de três meses foi fixado por decisão de 23/09/2026. O documento de projeto original
declarava de 1 a 4 semanas, e está sendo corrigido.

## 1.5 Por que três meses é o problema difícil

Existe uma assimetria que vale entender desde o começo, porque ela explica a forma de quase todos os
resultados deste documento.

- **Em uma semana à frente**, prever casos de dengue é relativamente fácil: o número da semana que vem se
  parece muito com o da semana atual. O modelo tem um erro absoluto médio de **98,0 casos**.
- **Em três meses à frente**, a informação recente perde quase todo o valor. A autocorrelação — o quanto o
  valor de hoje informa sobre o valor futuro — cai a praticamente zero nesse intervalo. Sobra a
  sazonalidade: saber em que mês do ano se está. O erro sobe para **278,8 casos**.

E é exatamente aí que aparece a dificuldade central do trabalho: **se em três meses só a sazonalidade
informa, então uma régua que só olha o calendário é um adversário muito forte.** A régua sazonal, que
apenas repete o que aconteceu na mesma semana do ano anterior, erra **217,8 casos** — menos que o modelo.

Esse fato, medido em 25/09/2026 e reproduzido desde então em várias rodadas independentes, é o eixo em
torno do qual o restante do documento se organiza.

## 1.6 O que este documento vai mostrar

Antecipando, em cinco linhas, para que o leitor saiba onde a argumentação chega:

1. **Em horizonte curto, de até um mês, o modelo funciona bem** e é bem calibrado sobre a própria
   incerteza em períodos de calmaria.
2. **Em horizonte de três meses, o modelo não supera a régua sazonal** no erro do número previsto.
3. **O modelo subestima sistematicamente a magnitude dos picos** — captura, em média, cerca de 39% do
   tamanho real das semanas de surto —, e é excessivamente confiante ao fazê-lo.
4. **Isso não vem de defeito de implementação nem de ajuste de configuração.** Foram testadas 120
   configurações, nove algoritmos, modelos de fundação, seis formulações do alvo, transformações de escala
   e modelos estatísticos clássicos. Nenhum superou a régua sazonal em horizonte longo.
5. **A explicação mais provável é limitação de dados** — duas epidemias na série, e ausência de variáveis
   que a literatura aponta como determinantes, como sorotipo circulante, imunidade populacional e
   mobilidade.

Cada uma dessas cinco afirmações é sustentada por números nas Partes 4, 5, 6 e 8, e cada uma é submetida a
crítica adversarial na Parte 9.

---

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
\text{Especificidade} = J - \text{Sensibilidade} + 1 = 0{,}9412 - 0{,}9706 + 1 = 0{,}9706
$$

**Ou seja, em $h = 4$, o modelo tem sensibilidade de 97,1% (captura quase todo surto real de mais de 100
casos) e especificidade de 97,1% (raramente soa o alarme numa semana calma).** Isso é consistente com o
número absoluto de "0,7 alarmes falsos por ano" — menos de um por ano.

⚠️ **Uma armadilha de arredondamento, que vale para o documento inteiro.** A conta acima só fecha com os
valores cheios. Se alguém arredondar **antes** de subtrair — 0,94 menos 0,971 mais 1 — o resultado dá
**0,969**, um número que não existe em lugar nenhum. A especificidade medida, disponível direto no arquivo
`metricas_por_regra.csv`, é **0,9706**. Arredondar depois da conta, nunca antes.

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

🔴 **Atenção ao limiar, porque ele muda entre os dois números abaixo.** A contagem de blocos apresentada na
Seção 15.1 refere-se ao evento **"semana com mais de 100 casos"**. Já as razões de p-valor desta seção
foram calculadas sobre o evento **"semana com mais de 421 casos"**, que é o piso do estágio Alerta do
Plano Municipal de Contingência. São **limiares diferentes**, de análises diferentes. **Não existe, no
repositório, nenhum bootstrap por blocos rodado especificamente para o limiar de 100 casos** — a
reamostragem só foi feita na rodada de 26/09/2026, que adotou 421 como evento principal.

A lição sobre correlação serial vale para os dois limiares, porque a estrutura de blocos é a mesma: em
qualquer limiar testado, as semanas de surto formam **exatamente dois blocos contíguos**. Mas os números
específicos abaixo pertencem ao limiar de 421, e é assim que devem ser citados.

O resultado é expresso como a **razão entre o p-valor obtido pelo bootstrap por blocos e o p-valor
nominal** (o p-valor calculado pela fórmula fechada, ignorando a correlação serial). Todos os valores
abaixo são do evento de **421 casos**:

- Contra a régua "hoje já passou do limiar": a razão variou entre **0,0001 e 0,82** — o p-valor nominal
  já era, se algo, **conservador** (o bootstrap às vezes dá um p-valor até menor). Esse resultado é lido
  como **robusto**: a correlação serial não está inflando artificialmente a confiança nessa comparação
  específica.
- Contra a régua "o ano passado passou do limiar" (a régua sazonal): em $h=4$, a razão ficou entre
  **1,10 e 1,51**; em
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

---

# Parte 3 — Os dados

## 3.1 A rede de armadilhas MI-Aedes

### 3.1.1 O que é uma armadilha MosquiTRAP

O projeto usa, como um dos seus dados de entrada, a contagem de mosquitos capturados por uma rede de
armadilhas espalhadas pela cidade de Porto Alegre. O modelo de armadilha usado por essa rede se chama
**MosquiTRAP**.

Uma MosquiTRAP é um recipiente plástico escuro, de formato cilíndrico, que funciona como uma **armadilha
de oviposição**: ela imita, para a fêmea do mosquito, um lugar ideal para pôr ovos (um recipiente com água
parada). Dentro dela existe um **atrativo químico** — uma substância sintética que reproduz o odor que a
fêmea grávida procura para escolher onde desovar — e uma superfície adesiva. A fêmea entra atraída pelo
atrativo, fica presa na superfície adesiva e é capturada viva. Depois, um técnico recolhe o conteúdo da
armadilha periodicamente e os insetos capturados são identificados em laboratório, por espécie (*Aedes
aegypti*, *Aedes albopictus*, *Culex sp.* e outras) e por sexo.

**Por que isso importa para os dados:** a armadilha captura principalmente **fêmeas adultas em busca de
local para desovar**. Machos não têm o mesmo comportamento de procurar sítio de oviposição e são raros
nas capturas — por isso a estatística oficial da rede (ver **3.1.2**) é construída sobre a contagem de
fêmeas, não sobre o total de mosquitos.

**FATO (registrado no código do projeto, `modelagem_aedes/`).** A tabela bruta da Secretaria Municipal de
Saúde de Porto Alegre (SMS-POA) guarda, para cada armadilha e cada semana, contagens separadas de fêmeas e
de machos de cada espécie (`aegypti_femea`, `aegypti_macho`, `aegypti_total`, e o mesmo para
*albopictus* e *Culex*). Isso confirma, nos próprios dados, que a distinção fêmea/macho é feita na
identificação em laboratório, e não estimada.

### 3.1.2 O índice de fêmeas por armadilha

A métrica oficial que resume, numa cidade ou num bairro, o quanto o mosquito está presente numa semana é
o **índice de fêmeas por armadilha (IFA)**: quantas fêmeas de *Aedes aegypti*, em média, cada armadilha
vistoriada capturou naquela semana. "Vistoriada" quer dizer que um técnico foi até a armadilha, recolheu
o conteúdo e o registro chegou ao sistema — uma armadilha instalada mas não visitada naquela semana não
entra no denominador.

**A fórmula:**

```
IFA = F / A
```

Onde:

- **IFA** — índice de fêmeas por armadilha, na semana e no recorte geográfico considerado (cidade,
  bairro, zona);
- **F** — número de fêmeas de *Aedes aegypti* capturadas naquele recorte, naquela semana;
- **A** — número de armadilhas efetivamente **vistoriadas** (com leitura registrada) nesse mesmo recorte
  e semana.

**Exemplo numérico, com dados reais do projeto — a semana epidemiológica 11 de 2025 (SE **`202511`**, que
começa em 09/03/2025):** nessa semana, a tabela do projeto registra **877 armadilhas vistoriadas** na
cidade inteira e um índice de **1,058153** fêmeas por armadilha. Isolando a fórmula para achar o número
de fêmeas:

```
F = IFA × A = 1,058153 × 877 ≈ 928 fêmeas de Aedes aegypti
```

Ou seja: naquela semana, em média, mais de uma fêmea de *Aedes aegypti* foi encontrada em cada armadilha
vistoriada na cidade — quase 928 fêmeas ao todo, espalhadas pelas 877 armadilhas.

Um segundo exemplo, agora usando o **agregado histórico inteiro** da base certificada (ver **3.2.4**):
**FATO (conferido célula a célula em 13/09/2026, registrado em `ESTADO.md` §1)** — a base tem
**636.587 inspeções de armadilha** e **236.166 fêmeas de *Aedes aegypti*** capturadas ao longo de
**718 semanas** (23/09/2012 a 09/08/2026). O índice médio de todo o período é:

```
IFA_histórico = 236.166 / 636.587 ≈ 0,371
```

Ou seja, em média histórica, cada armadilha vistoriada em Porto Alegre captura um pouco mais de um terço
de uma fêmea de *Aedes aegypti* por visita — um número bem mais baixo do que o **1,058** da semana de
epidemia usada no primeiro exemplo, o que já ilustra que o índice varia fortemente ao longo do tempo, com
picos sazonais.

⚠️ **Uma armadilha para não confundir:** o arquivo bruto da Secretaria também guarda a coluna
`aedes_aegypti` (ou, na tabela final do projeto, o mesmo nome), que soma **fêmeas e machos** capturados.
Ela **não é** o numerador do índice oficial. Um erro comum seria calcular "fêmeas por armadilha" dividindo
essa coluna pelo número de armadilhas: no exemplo acima, isso daria **937 ÷ 877 ≈ 1,068**, um número
próximo mas **diferente** do índice oficial de **1,058153**, porque a coluna de total inclui os poucos
machos capturados. O projeto preserva as duas colunas separadas exatamente para evitar essa confusão
(ver **3.9**).

### 3.1.3 Quem opera a rede, e com que frequência

**FATO.** A operação de campo — instalar as armadilhas, revisitá-las periodicamente e coletar o material
capturado — é feita pela vigilância em saúde da Secretaria Municipal de Saúde de Porto Alegre (SMS-POA):
é dela que o projeto recebe os arquivos brutos (pasta `arquivos_secretaria_saude_poa/`, ver **3.2.4**). A
frequência de vistoria é **semanal**: o portal público que expõe esses números para a cidade,
o **MI-Aedes** ("Monitoramento Inteligente do Aedes"), atualiza a leitura semana a semana, e é dele que
vem a segunda fonte de dados do projeto, a raspagem (ver **3.2.2**).

⚠️ **HIPÓTESE (não verificada por este projeto):** a tecnologia MosquiTRAP é comercializada pela empresa
Ecovec. Uma das autoras do artigo de referência da Silva et al. 2026 (ver Parte de literatura) tem vínculo
declarado com essa empresa, o que é consistente com a hipótese de que ela também é a fornecedora da
tecnologia usada em Porto Alegre — mas o projeto não teve acesso a um documento da Prefeitura que confirme
esse contrato, então isso fica registrado como hipótese, não como fato.

### 3.1.4 O índice oficial e suas faixas

O **Plano Municipal de Contingência de Arboviroses de 2026**, da SMS-POA, classifica a situação
entomológica (relativa aos insetos) da cidade em quatro faixas, usando o índice de fêmeas por armadilha
vistoriada (ver **3.1.2**):

| Faixa | Índice de fêmeas por armadilha (IFA) |
|---|---|
| Satisfatório | menor que **0,15** |
| Moderado | de **0,15** a **0,30** |
| Alerta | de **0,30** a **0,6** |
| **Crítico** | maior que **0,6** |

Comparando com os dois exemplos numéricos da seção 3.1.2: o índice médio histórico da cidade
(**≈ 0,371**) já cai na faixa **Alerta**, e o índice da semana epidemiológica 11 de 2025 (**1,058**) está
bem acima do limite de **Crítico**. Isso é coerente com o fato de 2025 ter sido um ano de epidemia forte
de dengue em Porto Alegre (ver Parte 1).

⚠️ Este índice mede **presença do mosquito**, não **casos de dengue**. Os dois são fenômenos diferentes
que o projeto tenta relacionar (ver Parte de resultados, §3.2 e §3.3 de `ESTADO.md`): ter mosquito não é o
mesmo que ter epidemia, e a relação entre os dois é justamente uma das perguntas que o projeto investiga.

---

## 3.2 As fontes de dados, uma a uma

O projeto combina **quatro fontes** de dados, cada uma com um período coberto, um volume, uma forma de
chegada até o repositório e uma fragilidade própria. As quatro entram juntas na "tabela final"
(ver **3.4**).

### 3.2.1 SINAN — o sistema nacional de notificação de agravos

O **Sistema de Informação de Agravos de Notificação (SINAN)** é o sistema do governo federal brasileiro
que registra, em todo o país, os casos de doenças de notificação obrigatória — doenças que, por lei,
todo profissional de saúde que as diagnostica é obrigado a comunicar às autoridades sanitárias. A dengue é
uma delas.

- **Como chega ao projeto:** o governo federal publica, no portal **OpenDataSUS**, um arquivo
  comprimido por ano (padrão de nome `DENGBR` + os dois últimos dígitos do ano, por exemplo
  `DENGBR26.csv.zip`), com uma linha por caso notificado de dengue **no Brasil inteiro**. O script
  `modelagem_aedes/preparo/consolidar_sinan.py` lê esses arquivos (eles são grandes demais para abrir de
  uma vez, então lê em pedaços de 300 mil linhas), filtra só os casos de Porto Alegre e só os
  **confirmados** (ver **3.3**), e gera um arquivo único, `casos_confirmados_poa.csv`, com um caso por
  linha.
- **Período coberto:** o projeto tem um arquivo `DENGBR` por ano, de 2018 a 2026. **FATO (registrado em
  `ESTADO.md` §1):** os casos só existem a partir de **18/02/2018** — não há 14 anos de série de casos como
  há de mosquito.
- **Volume:** cada arquivo anual nacional tem centenas de milhares a milhões de linhas (todo o Brasil);
  depois do filtro por Porto Alegre e por confirmação, sobram algumas centenas a poucos milhares de casos
  por ano (ver a tabela do Plano Municipal na Parte 1: de **5.144** casos confirmados em 2022 a
  **21.329** em 2025).
- **Fragilidade:** o governo às vezes **reexporta** o arquivo de um ano que o projeto já tinha, com uma
  versão mais completa (por exemplo, um arquivo com sufixo `_atualizado`). **FATO (corrigido em
  25/09/2026):** antes dessa data, o script juntava as duas versões do mesmo ano sem escolher uma, contando
  os casos em dobro — foi o que quase aconteceu com o arquivo de 2026 em 13/09/2026. Hoje o script escolhe
  **um único arquivo por ano**, com uma regra explícita (prioriza o nome com `_atualizado`; sem isso, o
  arquivo modificado mais recentemente no disco).

Cada caso, no arquivo do SINAN, carrega — entre outras — as colunas `SEM_PRI` (semana epidemiológica de
início dos sintomas), `SEM_NOT` (semana de notificação), `ID_MUNICIP` (município onde o caso foi
**notificado**), `ID_MN_RESI` (município de **residência** do paciente) e `CLASSI_FIN` (classificação
final do caso). Como essas quatro colunas moldam decisões centrais do projeto, elas voltam nas seções
**3.3** e **3.4**.

### 3.2.2 A raspagem semanal do portal MI-Aedes

O portal público **MI-Aedes**, da SMS-POA, expõe a contagem de mosquitos capturados pela rede de
armadilhas — mas **só a semana corrente**: não existe, nesse portal, um jeito de baixar o histórico
inteiro de uma vez. Por isso o projeto mantém uma **raspagem manual**: alguém (o próprio autor do
projeto) entra no portal a cada semana e baixa um arquivo com os números daquela semana.

- **Como chega:** arquivos `.xlsx`, um por coleta, salvos na pasta `Raspagem/Arquivos/`, com nome que
  já carrega a data da coleta, o número da semana e uma contagem aproximada de mosquitos (por exemplo,
  `dados_aedes_20250106_weekid02_137mosquitos.xlsx`). O script
  `modelagem_aedes/preparo/consolidar_raspagem.py` junta esses arquivos num histórico único. Quando a
  mesma semana foi raspada mais de uma vez (coletas em dias diferentes), fica só com o arquivo **mais
  completo** — o que tem mais mosquitos contados; em empate, o mais recente.
- **Período coberto:** hoje, só o pedaço de **2026** que a SMS-POA ainda não enviou oficialmente — de
  2012 a 2025 o projeto usa a série oficial da Secretaria (ver **3.2.4**), que é mais completa. A raspagem
  de **2025** foi mantida como conferência independente, mas não alimenta mais a tabela final.
- **Volume:** um arquivo por semana raspada, cada um com uma linha por armadilha vistoriada naquela
  semana (tipicamente algumas centenas de linhas).
- **Fragilidade — a mais grave do projeto para dados futuros:** essa raspagem é **manual, sem
  agendamento automático** (sem `cron`, sem `launchd`, os dois mecanismos comuns para automatizar tarefas
  recorrentes num computador). **FATO (registrado em `ESTADO.md` §1):** a semana de identificador
  **458** (05 a 11/10/2025) nunca foi raspada. Não houve prejuízo nesse caso porque a série oficial da
  Secretaria cobre 2025 inteiro — mas **daqui para frente**, uma semana que passe sem ser raspada em 2026
  em diante é uma semana **perdida para sempre**, porque o portal só mostra a semana corrente. Automatizar
  essa raspagem é um item em aberto do projeto (ver `PENDENCIAS.md`).

### 3.2.3 Os dados de clima

O clima entra no projeto como uma fonte totalmente diferente das duas anteriores: em vez de dados sobre
mosquitos ou pessoas, são medições meteorológicas diárias.

- **Como chega:** o script `modelagem_aedes/preparo/capturar_clima.py` baixa, pela internet, dados
  públicos do serviço **NASA POWER** (uma base de dados meteorológicos globais, de acesso público, mantida
  pela agência espacial norte-americana NASA, que não exige senha nem chave de acesso), para um ponto no
  centro de Porto Alegre (latitude −30,03, longitude −51,23). Os dados vêm dia a dia — chuva, temperatura,
  ponto de orvalho, umidade, pressão atmosférica, radiação solar e vento — e são agregados por semana, na
  mesma convenção de semana usada pelo resto do projeto (começando no domingo).
- **Período coberto:** desde **23/09/2012** — a mesma data em que abre a primeira semana com captura de
  mosquito na base certificada da Secretaria (ver **3.2.4**). Essa data foi escolhida deliberadamente:
  antes de 29/08/2026, o clima só cobria desde dezembro de 2018 (o início do bloco de dados chamado
  "Marília", hoje fora do fluxo — ver **3.2.4**), o que limitava a **interseção** entre clima e vetor a
  cerca de 379 semanas. Estendendo o clima para 2012, essa interseção passou para cerca de **718 semanas**,
  o que deu mais poder estatístico a testes que comparam clima e vetor como preditores.
- **Volume:** uma linha por semana, com cerca de vinte medidas de clima diferentes (ver a lista completa
  na **3.4.2**).
- **Fragilidade:** os dados **mais recentes** (as últimas semanas) podem mudar um pouco depois, porque a
  NASA ajusta suas próprias medições conforme recebe mais informação de satélite e de estações de
  superfície. Dados antigos, em compensação, são estáveis — não mudam mais depois de publicados.

### 3.2.4 A série da Secretaria Municipal de Saúde (a base do vetor)

Esta é a fonte de dados sobre mosquito que o projeto usa como principal, e a mais delicada em termos de
proteção de dados pessoais.

- **Como chega:** a SMS-POA entregou ao projeto **12 arquivos brutos** — um por ano, de 2012 a 2020 —, cada
  um num formato de planilha diferente ao longo do tempo (os anos de 2012 a 2018 usam nomes de coluna em
  código, como `QTD_AEDP_F`; os de 2019 e 2021 vêm em português, divididos em treze abas; o de 2020 usa um
  terceiro conjunto de nomes). O script
  `modelagem_aedes/preparo/limpar_arquivos_secretaria.py` traduz os três formatos para um vocabulário
  único, e `unificar_arquivos_secretaria.py` junta tudo num único arquivo (`.parquet`, um formato de
  arquivo tabular compacto e rápido de ler), com uma linha por **armadilha, numa semana** — o grão mais
  fino que existe, de onde dá para somar por bairro, por quadra ou pela cidade inteira.
- **Período coberto e volume: FATO (base certificada célula a célula em 13/09/2026, registrada em
  `ESTADO.md` §1)** — **636.587 inspeções**, **236.166 fêmeas de *Aedes aegypti*** capturadas, ao longo de
  **718 semanas** (23/09/2012 a 09/08/2026), cobrindo **81 bairros** e **2.742 armadilhas** diferentes ao
  longo do tempo. Faltam **7 semanas** em quatorze anos de série: quatro antigas, fora da temporada de
  mosquito, e **três da enchente de maio de 2024** (as semanas de 28/04, 05/05 e 12/05 daquele ano), quando
  as vistorias de campo foram interrompidas pela emergência climática.
- **Fragilidade — dado pessoal:** os arquivos **brutos** de 2012 a 2020 contêm **nome e telefone do
  morador** do endereço visitado. Por isso a pasta `arquivos_secretaria_saude_poa/brutos_secretaria/` é
  tratada como **datalake somente leitura**: nunca é editada, e está protegida de vazamento por estar
  listada na linha 55 do arquivo `.gitignore` do repositório (o que faz o sistema de controle de versão
  `git` **ignorar essa pasta inteira** — zero arquivos dela ficam rastreados ou enviados para qualquer
  lugar). O arquivo final que o projeto de fato usa (`secretaria_poa_armadilhas.parquet`) é gerado a partir
  da pasta `limpos_secretaria/`, que **não tem** os dados pessoais.
- **Duas fontes, sem vão:** de 2012 a 2025, quem cobre a série é a Secretaria; de 2026 em diante, é a
  raspagem própria do portal MI-Aedes (**3.2.2**), porque a Secretaria ainda não enviou o ano corrente.

**Bases legadas, preservadas mas fora do fluxo:** o projeto também guarda, sem nunca apagar, duas outras
séries de mosquito que serviram para **validar** a base certificada, mas que não alimentam mais a tabela
final:

- **Marília (2019–2023):** um conjunto de dados independente, usado como padrão-ouro de validação — foi
  comparando com ele que o projeto provou, em 16/08/2026, que a correção de datas da base certificada
  estava certa.
- **Raspagem própria de 2025:** feita antes de a Secretaria enviar o ano de 2025 oficialmente, serviu como
  conferência cruzada independente do mesmo período.

---

## 3.3 Caso confirmado, caso notificado e caso provável

Ao falar de "quantos casos de dengue" existiram numa semana, existem pelo menos três números diferentes
possíveis, e o projeto usa apenas um deles como alvo do modelo. É essencial defini-los sem ambiguidade.

### 3.3.1 As três definições

- **Caso notificado:** qualquer atendimento de saúde em que um profissional **suspeitou** de dengue e
  comunicou isso ao sistema (SINAN), abrindo um registro. Notificação não significa que a pessoa tinha
  dengue de fato — é só o primeiro degrau: alguém com sintomas compatíveis (febre, dor no corpo, entre
  outros) entrou no radar da vigilância em saúde.
- **Caso provável:** categoria usada pelo Plano Municipal de Contingência de Arboviroses da SMS-POA para
  os limiares de estágio epidemiológico (ver Parte 1). Reúne os casos notificados que, mesmo sem exame
  laboratorial concluído, têm quadro clínico e contexto epidemiológico compatíveis com dengue — uma
  categoria intermediária entre "notificado" e "confirmado".
- **Caso confirmado:** o caso notificado que, depois de investigado — por exame laboratorial (sorologia
  ou detecção do vírus) ou por critério clínico-epidemiológico, quando a situação da cidade permite
  dispensar o exame de cada paciente — recebeu uma classificação final que o sistema aceita como dengue de
  fato. No arquivo do SINAN, essa classificação vive na coluna `CLASSI_FIN` ("classificação final"), e o
  projeto usa **três códigos dessa coluna** (10, 11 e 12) para marcar um caso como confirmado — em
  contraste com os códigos que marcam um caso como descartado (não era dengue) ou ainda inconclusivo.

**O alvo do projeto é o caso CONFIRMADO**, não o notificado nem o provável. **FATO (decisão medida em
30/08/2026, registrada em `ESTADO.md` §3.6):** essa escolha foi testada e não é arbitrária — o projeto
mediu qual das três definições o modelo consegue prever melhor, e casos confirmados venceu.

⚠️ Essa escolha tem um custo, medido e documentado: a **confirmação está caindo ao longo dos anos**. A
**taxa de confirmação** de um ano é definida como:

```
taxa_confirmação = casos_confirmados / casos_notificados
```

**FATO (medido em 13/09/2026, ver `modelagem_aedes/acesso/fontes.py` e
`analises/2026-09-13_metrica_de_alarme/README.md` §6):** em Porto Alegre, essa taxa foi de **73,2%** em
2022, **69,3%** em 2023, **60,1%** em 2024 e **38,3%** em 2025. Isso quer dizer que, em 2025, de cada 100
notificações de dengue na cidade, cerca de **38** chegaram a virar um caso confirmado no sistema — não
porque a epidemia tenha sido pequena (2025 teve **21.329** casos confirmados, o maior número da série),
mas porque a política de quem é testado muda quando a epidemia cresce (ver **3.3.3** abaixo e a Parte 1,
onde o Plano Municipal descreve como a testagem encolhe justamente quando mais se precisaria dela), e
porque parte dos casos mais recentes ainda está em apuração no momento da consulta (ver **3.6**, sobre o
corte de maturidade).

### 3.3.2 Município de notificação × município de residência

Cada caso do SINAN carrega **duas** informações de localização diferentes, e escolher qual delas usar
muda o número final:

- **Município de notificação** (coluna `ID_MUNICIP` do SINAN): o município onde fica a unidade de saúde
  que **atendeu e notificou** o caso. É o que o script `consolidar_sinan.py` usa para filtrar "os casos de
  Porto Alegre" — a constante `CODIGO_MUNICIPIO_POA = 431490` (o código de Porto Alegre no cadastro
  nacional de municípios) é comparada contra essa coluna.
- **Município de residência** (coluna `ID_MN_RESI` do SINAN): o município onde o paciente **mora**.

Os dois podem divergir: um morador de uma cidade vizinha pode ser atendido (e notificado) num hospital de
Porto Alegre, e um morador de Porto Alegre pode ser atendido numa cidade vizinha. Também é assim que o
**Estado do Rio Grande do Sul** (na sua própria vigilância) e a **Prefeitura de Porto Alegre** podem
divulgar números diferentes para "os casos de Porto Alegre" sem que nenhum dos dois esteja errado — cada
um está respondendo uma pergunta ligeiramente diferente (uma sobre onde os pacientes foram atendidos,
outra sobre onde eles moram).

**FATO (decisão do autor do projeto em 25/09/2026, registrada em `PENDENCIAS.md`).** O projeto usa
**município de notificação**, para poder comparar seus números diretamente com as séries que a própria
SMS-POA divulga (o Plano Municipal, o portal MI-Aedes) — que também são organizadas por notificação, não
por residência. Município de residência fica registrado como um **cenário alternativo**, ainda não
explorado.

### 3.3.3 A confirmação encolhe quando a epidemia cresce

O Plano Municipal de Contingência de Arboviroses (ver Parte 1) documenta uma regra operacional que ajuda a
explicar a queda na taxa de confirmação: os grupos de pacientes que são **testados** por exame
laboratorial mudam conforme o estágio epidemiológico da cidade.

**FATO (Plano Municipal, Quadro 1, citado em `PENDENCIAS.md`):** nos estágios de menor gravidade
(Normalidade e Mobilização), a rede testa viajantes, pessoas com comorbidades, gestantes, crianças menores
de 5 anos, idosos acima de 60 anos, e outros dois grupos de risco. Já nos estágios mais graves (Alerta e
Epidemia), a testagem se restringe a **só três grupos**: viajantes, gestantes e idosos acima de 60 anos.

Isso significa que **quanto pior a epidemia, menos gente é testada em proporção**, e mais casos
notificados ficam sem confirmação laboratorial — o que é uma decisão de saúde pública deliberada (poupar
recursos de teste quando o quadro clínico já deixa pouca dúvida), mas que tem uma consequência direta para
quem tenta prever "casos confirmados": o próprio alvo que o modelo tenta acertar muda de significado
conforme a epidemia avança.

---

## 3.4 A tabela final: da tabela bruta aos 20 atributos do modelo

### 3.4.1 O que é a tabela final, e o que é cada linha

A **tabela final** (arquivo `modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv`) é o ponto
de encontro das quatro fontes de dados descritas em **3.2**: junta, semana a semana, o mosquito capturado
nas armadilhas, o clima, os casos de dengue confirmados e um indicador climático de larga escala chamado
El Niño – Oscilação Sul (ENSO, ver adiante).

**Cada linha da tabela final é uma semana epidemiológica.** Uma **semana epidemiológica** é a unidade de
tempo padrão usada pela vigilância em saúde brasileira: começa sempre num domingo e termina no sábado
seguinte, e a semana 1 de cada ano é definida como a primeira que tem pelo menos 4 dias dentro daquele
ano — o que equivale a dizer que é a semana que contém a primeira quarta-feira do ano. Essa é uma
convenção, não uma coincidência: ela garante que toda semana do calendário tenha um único número de
semana epidemiológica, sem ambiguidade nas viradas de ano.

**FATO (medido nesta sessão, 26/09/2026, reconferindo o arquivo).** A tabela final tem **725 linhas**
(725 semanas, de 23/09/2012 a 09/08/2026) e **36 colunas** na sua forma bruta — antes de qualquer coluna
derivada (defasagem, média móvel, seno/cosseno) ser calculada. A tabela é uma **grade semanal contínua**:
existe uma linha para **todo** domingo entre a primeira e a última semana com dado disponível, mesmo
quando não houve nenhuma vistoria de armadilha naquela semana. Quando isso acontece, as colunas do vetor
ficam com valor **vazio (NaN — "not a number", a forma padrão de representar "sem informação" numa
tabela)**, nunca com um zero inventado. O mesmo vale para os casos: fora do período coberto pelo SINAN
(antes de 18/02/2018, ou depois da última semana já divulgada), a coluna de casos fica vazia, não zero.

### 3.4.2 As 36 colunas da tabela bruta

As 36 colunas do arquivo, na ordem em que aparecem, são:

| Grupo | Colunas |
|---|---|
| Identificação da semana | `fonte`, `SE`, `data_inicio_semana_epidemi`, `ano`, `semana` |
| Mosquito (vetor) | `numero_de_armadilhas`, `aedes_aegypti`, `aedes_albopictus`, `culex_sp`, `aedes_aegypti_por_armadilha`, `denominador_aproximado` |
| Clima — chuva | `precip_total_mm`, `precip_max_dia_mm`, `precip_media_dia_mm`, `dias_de_chuva` |
| Clima — temperatura | `temp_media`, `temp_min`, `temp_max`, `temp_amplitude_media` |
| Clima — umidade do ar | `orvalho_min`, `orvalho_media`, `orvalho_max`, `umid_min`, `umid_media`, `umid_max` |
| Clima — pressão atmosférica | `pressao_min`, `pressao_media`, `pressao_max` |
| Clima — radiação solar | `radiacao_min`, `radiacao_media`, `radiacao_max` |
| Clima — vento | `vento_media`, `vento_max` |
| Casos de dengue | `casos_confirmados` |
| El Niño – Oscilação Sul | `nino34_anom`, `oni` |

`nino34_anom` e `oni` medem a temperatura anômala do oceano Pacífico tropical (o fenômeno El
Niño/La Niña, que influencia o clima em escala continental, inclusive no Sul do Brasil). Essas duas
colunas **entram na tabela bruta mas não entram no modelo** (ver `colunas_ignorar` na configuração do
experimento) — foram usadas em testes específicos sobre o efeito do clima de larga escala, não fazendo
parte do conjunto de atributos padrão (ver Parte de resultados / dívida técnica sobre ENSO).

### 3.4.3 Os grupos de atributos: núcleo, clima e vetor

O modelo **não usa as 36 colunas brutas diretamente**. Antes de treinar, o projeto calcula colunas
**derivadas** (defasagens, médias móveis, seno/cosseno da época do ano — ver **3.5**) e depois separa
**todas** as colunas candidatas (brutas + derivadas, exceto identificadores e ENSO) em **três grupos**,
pelo nome da coluna:

- **Núcleo:** o histórico da própria série de casos e a marcação da época do ano — a parte que existe
  sempre, mesmo sem clima nem mosquito;
- **Clima:** qualquer coluna cujo nome contenha um dos radicais `temp`, `precip`, `orvalho`, `umid`,
  `pressao`, `radiacao`, `vento` ou `dias_de_chuva`;
- **Vetor:** qualquer coluna cujo nome contenha `aedes`, `armadilha` ou `vetor`.

**FATO (calculado nesta sessão, 26/09/2026, reproduzindo o código real do projeto,
`dominio/selecao_features.py` e `dominio/features.py`, sobre a tabela final vigente):**

- O grupo **núcleo** tem exatamente **8 colunas**: `casos`, `casos_lag1`, `casos_lag2`, `casos_lag3`,
  `casos_lag4`, `casos_mm4` (média móvel de 4 semanas dos casos, ver **3.5**), `sem_sin` e `sem_cos`
  (a marcação circular da época do ano, ver **3.5**).
- O grupo **vetor** tem exatamente **6 colunas**: `aedes_aegypti_por_armadilha` (o índice da semana
  corrente, ver **3.1.2**), suas quatro defasagens (`aedes_aegypti_por_armadilha_lag1` a `_lag4`) e
  `vetor_mm4` (a média móvel de 4 semanas do índice).
- O grupo **clima** tem **42 colunas candidatas**, e a conta é esta:
  - **22 colunas brutas**, isto é, sem defasagem, que são as listadas em **3.4.2**: chuva (4) mais
    temperatura (4) mais umidade (6) mais pressão (3) mais radiação (3) mais vento (2);
  - mais **20 colunas defasadas**, que vêm de **cinco** dessas variáveis (`temp_media`,
    `precip_total_mm`, `orvalho_media`, `umid_media`, `pressao_media`), cada uma com defasagem de 1, 2, 3
    e 4 semanas: 5 × 4 = 20;
  - **22 + 20 = 42**.
  - As outras **17** colunas brutas, entre elas `temp_amplitude_media` e `dias_de_chuva`, entram **apenas
    sem atraso**, e não geram colunas defasadas.

Dessas **42 colunas de clima candidatas**, o **cenário adotado do projeto usa só as 6 que mais ajudaram** a
prever casos num teste específico (ver a seguir) — daí o **8 + 6 + 6 = 20 atributos** que o modelo
efetivamente recebe.

**Como as 6 colunas de clima são escolhidas.** O projeto usa um algoritmo de aprendizado de máquina
chamado **LightGBM** (um algoritmo de **boosting de gradiente** — uma família de métodos que treina muitas
árvores de decisão pequenas em sequência, cada uma corrigindo o erro que sobrou das anteriores) para medir
o **ganho** que cada coluna de clima trouxe para prever os casos, usando só uma fatia inicial dos dados
(60% mais antigos, para o próprio processo de escolha não "espiar" o futuro que o experimento principal
vai tentar prever depois). Isso é feito para três horizontes diferentes (1, 4 e 8 semanas à frente), e o
"ganho" de cada coluna nos três horizontes é somado. As seis colunas com maior ganho somado entram no
modelo; as outras 36 ficam de fora.

⚠️ **DÍVIDA TÉCNICA, registrada em `PENDENCIAS.md`.** Essa escolha de 6 colunas de clima acontece **fora
do walk-forward** (fora do teste que treina no passado e prevê o futuro repetidamente — ver Parte de
método) — ou seja, é feita **uma vez só**, olhando uma fatia fixa dos dados, e não refeita a cada rodada
do teste. Além disso, o próprio ranking de importância **muda dependendo de qual coluna se está tentando
prever** (casos confirmados, casos notificados, ou densidade do vetor): recortando a série em 2023, **4
das 6 colunas mudam** (FATO registrado em `ESTADO.md` §3.7). Isso quer dizer que a frase "estas 6 variáveis
de clima são as que importam" não pode ser tratada como um fato estável do fenômeno — é o resultado de uma
escolha de engenharia, sensível ao recorte de dados e ao alvo escolhido.

**Reproduzindo esse cálculo nesta sessão (26/09/2026), sobre a tabela final vigente, com a mesma
configuração do cenário adotado (corte de maturidade de 12 semanas, seleção pelo LightGBM, horizontes 1/4/8,
60% iniciais dos dados para a escolha)**, as seis colunas de clima escolhidas são:

1. `temp_media_lag4` — temperatura média do ar, com 4 semanas de atraso;
2. `umid_media` — umidade relativa média do ar, na própria semana;
3. `temp_media_lag3` — temperatura média do ar, com 3 semanas de atraso;
4. `temp_max` — temperatura máxima do ar, na própria semana;
5. `pressao_media_lag3` — pressão atmosférica média, com 3 semanas de atraso;
6. `pressao_media_lag4` — pressão atmosférica média, com 4 semanas de atraso.

Isso é consistente com o que se esperaria biologicamente: a temperatura de **3 a 4 semanas atrás** — o
tempo aproximado que o mosquito leva para se desenvolver do ovo ao adulto picador, mais o tempo de
incubação do vírus dentro dele — pesa mais do que a temperatura da própria semana. Ainda assim, por conta
da instabilidade documentada acima, este resultado específico é rotulado como **FATO (medido nesta sessão,
26/09/2026)**, não como uma verdade definitiva sobre quais variáveis de clima "realmente importam".

**A lista completa dos 20 atributos que o cenário adotado recebe, portanto, é:**

| # | Coluna | Grupo | O que é |
|---|---|---|---|
| 1 | `casos` | Núcleo | Casos confirmados na própria semana de origem |
| 2 | `casos_lag1` | Núcleo | Casos confirmados 1 semana antes |
| 3 | `casos_lag2` | Núcleo | Casos confirmados 2 semanas antes |
| 4 | `casos_lag3` | Núcleo | Casos confirmados 3 semanas antes |
| 5 | `casos_lag4` | Núcleo | Casos confirmados 4 semanas antes |
| 6 | `casos_mm4` | Núcleo | Média móvel de 4 semanas dos casos confirmados |
| 7 | `sem_sin` | Núcleo | Seno da posição da semana no ano (sazonalidade) |
| 8 | `sem_cos` | Núcleo | Cosseno da posição da semana no ano (sazonalidade) |
| 9 | `temp_media_lag4` | Clima | Temperatura média do ar, 4 semanas antes |
| 10 | `umid_media` | Clima | Umidade relativa média do ar, na semana |
| 11 | `temp_media_lag3` | Clima | Temperatura média do ar, 3 semanas antes |
| 12 | `temp_max` | Clima | Temperatura máxima do ar, na semana |
| 13 | `pressao_media_lag3` | Clima | Pressão atmosférica média, 3 semanas antes |
| 14 | `pressao_media_lag4` | Clima | Pressão atmosférica média, 4 semanas antes |
| 15 | `aedes_aegypti_por_armadilha` | Vetor | Índice de fêmeas por armadilha, na semana |
| 16 | `aedes_aegypti_por_armadilha_lag1` | Vetor | Índice de fêmeas por armadilha, 1 semana antes |
| 17 | `aedes_aegypti_por_armadilha_lag2` | Vetor | Índice de fêmeas por armadilha, 2 semanas antes |
| 18 | `aedes_aegypti_por_armadilha_lag3` | Vetor | Índice de fêmeas por armadilha, 3 semanas antes |
| 19 | `aedes_aegypti_por_armadilha_lag4` | Vetor | Índice de fêmeas por armadilha, 4 semanas antes |
| 20 | `vetor_mm4` | Vetor | Média móvel de 4 semanas do índice de fêmeas por armadilha |

### 3.4.4 Um exemplo numérico de uma linha real

Para tornar tudo isso concreto, eis uma linha real da tabela final — a semana epidemiológica **11 de
2025** (código **`SE 202511`**, que começa no domingo 09/03/2025), usada como exemplo ao longo desta seção
porque é justamente a semana com **917 casos confirmados** citada no painel de calibração do projeto (ver
Parte de resultados):

| Atributo | Valor nessa semana | De onde vem |
|---|---|---|
| `casos` (o alvo bruto daquela semana) | **917** | SINAN, confirmados, notificação em Porto Alegre |
| `casos_lag4` | **161** | Os casos confirmados de 4 semanas antes, SE 202507 (09/02/2025) |
| `casos_mm4` | (média das 4 semanas anteriores) | Calculado sobre a própria série |
| `sem_sin` / `sem_cos` | 0,971 / 0,239 | `semana = 11`, ver fórmula em **3.5** |
| `aedes_aegypti_por_armadilha` | **1,058153** | Base certificada da Secretaria |
| `temp_max` | **28,93 °C** | NASA POWER |
| `umid_media` | **74,52%** | NASA POWER |

Note que **917 casos confirmados numa única semana** é um número que precisa de tradução concreta: é
quase o dobro dos **161 casos** que a mesma cidade teve **4 semanas antes** — um salto que caracteriza a
fase de aceleração de uma epidemia, e é justamente o tipo de subida que o modelo tenta antecipar usando as
colunas de defasagem (ver **3.5** e a Parte de resultados sobre magnitude de erro em picos).

Para efeito de referência, a **semana de maior número de casos confirmados em toda a série** é a
seguinte: `SE 202514` (30/03/2025), com **2.381 casos confirmados** — três semanas depois da linha usada
como exemplo acima, mostrando como a subida continuou.

---

## 3.5 Defasagens (*lags*)

Uma **coluna defasada** (em inglês, *lag*, termo usado no código do projeto e mantido aqui por ser como
ele aparece nos nomes de coluna) é simplesmente **o valor de uma variável em uma semana passada, colocado
lado a lado com a semana atual**, para que o modelo possa "ver" o passado recente como se fosse mais uma
informação disponível na hora de prever.

**A fórmula, em palavras:** a coluna `X_lagN` de uma semana `t` guarda o valor de `X` na semana `t − N`.

```
X_lagN(t) = X(t − N semanas)
```

Onde:

- **X** — a variável original (por exemplo, `casos`, ou `aedes_aegypti_por_armadilha`);
- **N** — quantas semanas de atraso (o projeto usa **N = 1, 2, 3 e 4**);
- **t** — a semana de referência (a semana de "hoje", na qual o modelo está fazendo a previsão).

**Exemplo numérico, usando a linha da seção 3.4.4:** a semana de referência é `SE 202511`
(09/03/2025, com **917** casos confirmados). A coluna `casos_lag4` dessa linha deve guardar o número de
casos confirmados de **4 semanas antes**, ou seja, a semana `SE 202507` (09/02/2025). Olhando diretamente
a tabela final, `SE 202507` teve **161 casos confirmados** — e é exatamente esse o valor que aparece em
`casos_lag4` na linha de `SE 202511`. Confirma-se, com um exemplo real, que:

```
casos_lag4(09/03/2025) = casos(09/02/2025) = 161
```

**Por que a janela vai só de 1 a 4 semanas.** A escolha não é arbitrária: ela equilibra dois efeitos
opostos. Defasagens curtas (1 a 4 semanas) capturam o que há de mais recente e relevante no
**momentum** da epidemia — se os casos estão subindo ou descendo agora. Defasagens muito mais longas
esbarram em dois problemas medidos pelo próprio projeto (ver Parte de resultados, §3.1 de `ESTADO.md`):
primeiro, a força da relação entre "casos de uma semana" e "casos de semanas passadas" (a
**autocorrelação** — o quanto uma série se parece com ela mesma deslocada no tempo) já cai para
praticamente **zero em 12 semanas**; segundo, defasagens de 5 a 12 semanas e de 52/104 semanas (um ano ou
dois anos atrás) foram testadas e **não reduziram o erro** de previsão (23 e 24/09/2026). A janela de 1 a
4 semanas é, portanto, a que sobreviveu ao teste, não a única jamais cogitada.

⚠️ Uma coluna defasada **herda os vazios (NaN)** da coluna original: se a semana `t − N` não tinha
informação (por exemplo, por causa do corte de maturidade, ver **3.6**, ou de uma semana sem vistoria de
armadilha), a coluna defasada correspondente também fica vazia naquela linha. O código do projeto não
inventa nenhum valor para preencher esse vazio — ele se propaga naturalmente pelo cálculo (usando a função
`shift` da biblioteca de manipulação de tabelas `pandas`, que desloca uma coluna no tempo preservando os
vazios).

**A marcação de sazonalidade (`sem_sin` e `sem_cos`).** Embora não seja tecnicamente uma defasagem, essas
duas colunas do grupo núcleo (ver **3.4.3**) usam um mecanismo relacionado — transformar um número que se
repete em ciclo (a semana do ano, de 1 a 52) em algo que o modelo consegue interpretar sem ser enganado
pela quebra de ano. A fórmula é:

```
sem_sin = sen(2π × semana / 52)
sem_cos = cos(2π × semana / 52)
```

Onde **semana** é o número da semana epidemiológica dentro do ano (de 1 a 52), e **sen** e **cos** são as
funções trigonométricas seno e cosseno. A razão de usar as duas juntas, em vez de só o número da semana
puro: se o modelo recebesse diretamente "semana = 52" e "semana = 1" como dois números, ele os veria como
**distantes** (52 e 1 são numericamente afastados), quando na verdade são **semanas vizinhas** no
calendário (a última semana de um ano e a primeira do ano seguinte). Codificando a semana como um ponto
num círculo (usando seno e cosseno), a semana 52 e a semana 1 ficam **próximas** no espaço que o modelo
enxerga, exatamente como estão próximas no calendário.

**Exemplo numérico:** para a semana de referência do exemplo (`semana = 11`, dentro de `SE 202511`):

```
ângulo = 2π × 11 / 52 ≈ 1,329 radianos
sem_sin = sen(1,329) ≈ 0,971
sem_cos = cos(1,329) ≈ 0,239
```

Esses são exatamente os valores usados na tabela da seção 3.4.4.

---

## 3.6 O corte de maturidade de 12 semanas

### 3.6.1 O que é, e por que existe

Um caso de dengue não entra "pronto" no SINAN no momento em que a pessoa fica doente. Existe um atraso
entre a semana em que os sintomas começaram (o que o projeto usa para contar "quando" o caso aconteceu,
ver **3.2.1**, coluna `SEM_PRI`) e o momento em que esse caso é **investigado, classificado e confirmado**
no sistema — o que pode levar dias a semanas.

Isso cria um efeito enganoso: se alguém olhar a contagem de casos confirmados nas **últimas semanas**
antes de hoje, ela vai parecer **artificialmente baixa** — não porque a epidemia tenha diminuído, mas
porque boa parte dos casos daquelas semanas ainda **não terminou de ser confirmada**. Um modelo que
treinasse ingenuamente sobre esses números baixos, tratando-os como definitivos, aprenderia um padrão
errado (uma "queda" que não existe de verdade).

O **corte de maturidade** resolve isso: em vez de deixar os casos das últimas semanas com um número baixo
e enganoso, o projeto os marca como **"sem informação" (NaN)**, exatamente como se aquelas semanas nunca
tivessem sido divulgadas.

**A fórmula (implementada em `modelagem_aedes/dominio/surto.py`, função `aplicar_corte_maturidade`):**

```
casos_corrigidos(t) = casos(t)     se  t ≤ (t_máx − 12 semanas)
casos_corrigidos(t) = NaN          se  t > (t_máx − 12 semanas)
```

Onde:

- **t** — a data de início de uma semana qualquer da tabela;
- **t_máx** — a data da **última semana que tem um número de casos divulgado** (não a última linha da
  tabela — ver a ressalva abaixo);
- **12** — o número de semanas de corte, o parâmetro `semanas_corte_maturidade` da configuração do
  experimento.

**Exemplo numérico, com datas reais do projeto.** A última semana com casos confirmados divulgados na
tabela final vigente é **26/04/2026** (`t_máx`). Descontando 12 semanas:

```
t_máx − 12 semanas = 26/04/2026 − 84 dias = 01/02/2026
```

Ou seja: **toda semana depois de 01/02/2026 tem seus casos apagados (viram NaN)** para efeito de
treinamento e avaliação do modelo, mesmo que a tabela mostre um número (baixo, ainda em apuração) para
elas. Esse mesmo corte é a razão pela qual o painel de avaliação do cenário adotado (ver Parte de
resultados) descreve seu período como indo "até **~01/02/2026**" — a data não foi escolhida à mão: ela
**é** o resultado direto de aplicar a fórmula do corte de maturidade sobre a última semana disponível
quando a tabela foi gerada.

### 3.6.2 O que foi medido sobre o atraso real de confirmação

O valor "12 semanas" não é um chute: ele se baseia numa medição direta de quanto tempo os casos de 2025
efetivamente levaram entre o início dos sintomas e a confirmação no sistema.

**FATO (medido em 2025, registrado em `PENDENCIAS.md`):** a **mediana** desse atraso foi de **10,4
semanas**; o **percentil 75** (75% dos casos já confirmados até esse prazo) foi de **22,7 semanas**; o
**percentil 90** (90% dos casos já confirmados) foi de **31,6 semanas**.

Isso expõe uma tensão que o projeto reconhece explicitamente: o corte de **12 semanas** cobre a
**mediana** do atraso (metade dos casos já está confirmada nesse prazo) mas está **longe** de cobrir o
percentil 90 — quase **20 semanas** abaixo dele. Um corte de 12 semanas é, portanto, um meio-termo
deliberado: cortar mais (por exemplo, 32 semanas, cobrindo o percentil 90) preservaria mais confiabilidade
nos casos mantidos, mas descartaria quase **8 meses** de dados recentes a cada rodada — dados demais para
abrir mão, considerando que a epidemia mais recente é justamente a mais relevante para prever a próxima.

### 3.6.3 A limitação: o corte age uma vez só, no fim da série

**LIMITAÇÃO DE ARQUITETURA.** Olhando a fórmula da seção 3.6.1 com atenção: ela sempre ancora o corte na
**última semana com caso divulgado da tabela inteira** (`t_máx`), não na data em que uma previsão
específica está sendo feita dentro de um teste que simula o passado (o **walk-forward**, ver Parte de
método). Ou seja, o corte de maturidade **não simula**, para uma previsão feita em março de 2022, por
exemplo, "quais semanas de 2022 ainda estariam imaturas naquele momento" — ele sempre corta em relação ao
presente da tabela como um todo. Isso é adequado para gerar a tabela final que alimenta o modelo de
produção (que sempre prevê a partir de "agora"), mas significa que qualquer teste que **recrie o passado**
com a fórmula de corte de maturidade recebe uma versão "mais madura" das semanas antigas do que um
observador realmente teria visto naquela época — uma simplificação assumida, não escondida.

---

## 3.7 O período de treino e o período de avaliação

**Início do treino: 18/02/2018.** Essa data não é um filtro de calendário escolhido à mão — ela é uma
**consequência** de outra regra: o modelo só pode treinar em linhas que tenham um valor de casos
conhecido (sem isso, não há o que aprender). Como a série de casos confirmados só começa em **18/02/2018**
(ver **3.2.1**), toda linha anterior a essa data tem a coluna `casos` vazia (NaN) e é **removida** antes
do treino pelo próprio processo de descarte de linhas incompletas (`dropna`, "descartar não-disponível").
O efeito prático é o mesmo de um filtro por data, mas a causa é a remoção de linhas sem alvo, não uma
decisão de recorte temporal em si.

**Início da avaliação: 01/01/2024.** Esse é o corte que separa o período usado para **calibrar** decisões
de desenho do projeto (por exemplo, escolher quais colunas de clima entram — ver **3.4.3** — ou qual
algoritmo e função de perda usar) do período reservado para **julgar** o resultado final, sem que esse
julgamento tenha influenciado nenhuma escolha (ver Parte de método, sobre pré-declaração e o cuidado de
nunca deixar a avaliação "vazar" para dentro das decisões de desenho).

**Fim da avaliação: ~01/02/2026** — o mesmo limite que resulta do corte de maturidade de 12 semanas
aplicado à última semana com caso divulgado (ver **3.6.1**).

---

## 3.8 Por que 2026 foi excluído da avaliação

**FATO (decisão do autor do projeto em 26/09/2026, registrada em `PENDENCIAS.md` e `ESTADO.md` §3.2).** O
ano de **2026** foi **retirado** da tabela de avaliação oficial do projeto. A tabela oficial hoje vai só
até a semana epidemiológica 17 de 2026 (a última divulgada dentro do corte de maturidade), e qualquer
rodada que tenha incluído 2026 além desse ponto fica registrada só como material exploratório, guardado
à parte (pasta `atualizacao_dados_2026/`).

**O argumento é estatístico, não uma opinião:** **FATO (medido)**, o Plano Municipal registra
**19 casos confirmados** de dengue em Porto Alegre no início de 2026 divulgados até a data de corte —
um número extremamente baixo comparado aos **21.329** de 2025 e aos **17.686** de 2024. Um modelo cujo
histórico de treino é dominado por anos de epidemia crescente (2022 a 2025) não tem como "aprender", só
com dados, que um ano seguinte pode ser **calmo**: toda a tendência que ele viu até aqui aponta para cima.
Tentar avaliar a qualidade do modelo contra um ano de 19 casos, nessas condições, mediria principalmente o
quanto o modelo **não conseguiu prever uma coisa que a própria série histórica não dava pistas de que
aconteceria** — o que é diferente de medir se o modelo funciona bem no que ele foi desenhado para prever
(anos dentro do padrão observado até então).

⚠️ Isso não significa que 2026 seja irrelevante para sempre. **HIPÓTESE (levantada, não pré-declarada
como método permanente):** um protocolo específico para julgar anos calmos — com um critério de sucesso
diferente do erro absoluto usado para anos de epidemia — está em discussão (ver `PENDENCIAS.md`,
"Protocolo para testar a metodologia temporada a temporada"), mas ainda não foi formalizado nem aplicado.

---

## 3.9 Limitações conhecidas dos dados

Esta seção reúne, num só lugar, as fragilidades dos dados já mencionadas ao longo do texto, mais outras
que não caberiam nas seções anteriores sem interromper a explicação principal. Cada uma é uma
**limitação de arquitetura ou de dado disponível**, não uma falha de execução do projeto.

- **A seleção das 6 colunas de clima acontece fora do teste que simula o passado (o walk-forward), e o
  próprio ranking de importância é instável** — muda conforme o alvo escolhido e o recorte temporal (ver
  **3.4.3**). Isso significa que "estas são as variáveis de clima que importam" é uma afirmação sobre uma
  escolha de engenharia feita uma vez, não uma lei estável do fenômeno.

- **A raspagem do portal MI-Aedes é manual, sem automação.** Sem um mecanismo de agendamento automático
  (ver **3.2.2**), uma semana que passe sem ser raspada em 2026 em diante — quando a Secretaria ainda não
  publicou o ano corrente — é uma semana **permanentemente perdida**, porque o portal só expõe a semana
  corrente.

- **O portal MI-Aedes só expõe a semana corrente.** Não existe, nesse portal, uma forma de recuperar o
  histórico depois que uma semana "passa" — o que torna toda a captura de mosquito de 2026 em diante
  **insubstituível** assim que é coletada (ver invariantes do projeto em `CLAUDE.md`).

- **Não há sorotipo circulante entre os atributos do modelo.** O SINAN registra, por caso, uma coluna de
  sorotipo (`SOROTIPO`), mas essa informação **não entra** como atributo do modelo hoje. Como diferentes
  sorotipos encontram populações com diferentes níveis de imunidade prévia (ver Parte 1, sobre os quatro
  sorotipos da dengue), a ausência dessa informação é uma lacuna conceitual: o modelo não "sabe" se uma
  epidemia está sendo impulsionada por um sorotipo novo circulando numa população sem imunidade a ele.

- **Não há imunidade populacional entre os atributos do modelo.** Não existe, nos dados disponíveis ao
  projeto, uma estimativa de que fração da população de Porto Alegre já teve dengue (e portanto tem
  alguma imunidade). Esse é um fator conhecido na literatura de dengue como influente na dinâmica de
  epidemias futuras, e o projeto não tem como medi-lo com os dados que possui.

- **Não há mobilidade entre os atributos do modelo.** Deslocamento de pessoas dentro da cidade ou entre
  cidades vizinhas — relevante porque o mosquito tem baixo alcance de voo próprio, mas o vírus se espalha
  pelo deslocamento de pessoas infectadas — não está representado em nenhuma coluna do modelo.

- **A taxa de confirmação de casos caiu ao longo dos anos** (73,2% em 2022 para 38,3% em 2025, ver
  **3.3.1**), o que significa que o alvo do modelo (casos confirmados) está sendo medido com um "filtro"
  cada vez mais seletivo — uma mudança na própria definição operacional do número que se está tentando
  prever, não uma mudança na doença em si.

- **O corte de maturidade age uma vez só, ancorado no fim da tabela inteira** (ver **3.6.3**), e não
  simula o grau de maturidade que uma previsão feita no passado realmente teria enxergado naquele momento.

- **2,2% das linhas da base de armadilhas não têm coordenada geográfica registrada** (FATO, `ESTADO.md`
  §1), o que limita análises que dependam de localização exata (por exemplo, a associação de uma
  armadilha a um endereço específico).

- **O identificador de inspeção (`id_inspecao`) não é único** nos anos de 2012 a 2019 e em 2021, e a
  coluna de data do banco de dados (`data_banco`) tem cerca de 18% de valores invertidos nesses mesmos
  anos — duas fragilidades que impedem, por exemplo, deduplicar registros por identificador ou usar essa
  coluna de data para qualquer análise temporal fina nesses anos (FATO, `ESTADO.md` §1).

Estas limitações não invalidam os dados — cada uma delas foi medida, documentada e, sempre que possível,
contornada por uma decisão explícita de desenho (o corte de maturidade, a escolha de município de
notificação, o uso exclusivo do parquet certificado). Elas definem, isso sim, os limites do que pode ser
afirmado a partir destes dados — e é isso que as próximas partes deste documento levam em conta ao
descrever os modelos e os resultados.

---

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

---

# Parte 5 — As hipóteses testadas e seus vereditos

## 5.1 O método de trabalho: por que cada regra existe

Esta seção explica a **engenharia de verificação** do projeto — não os resultados em si, mas o
protocolo que decide quando um resultado pode virar frase de tese. Isso é parte da contribuição do
trabalho, porque a literatura da área frequentemente não segue nada disso (ver Parte sobre
metodologia e vazamento temporal, item 6 abaixo).

Antes de explicar as regras, quatro termos que vão aparecer o tempo todo:

- **Série temporal**: uma sequência de números medidos em instantes de tempo sucessivos e ordenados
  — aqui, o número de casos de dengue ou a contagem de mosquitos em cada semana epidemiológica. A
  diferença para uma tabela comum é que a **ordem importa**: embaralhar as linhas destrói a
  informação.
- **Hiperparâmetro**: um ajuste do algoritmo de aprendizado de máquina que **não é aprendido a partir
  dos dados** — é escolhido por quem constrói o modelo, antes do treino. Por exemplo, quantas
  "perguntas" (divisões) uma árvore de decisão pode fazer antes de parar. Errar a escolha de
  hiperparâmetro é uma causa comum de resultado que parece bom só por acaso (sobreajuste).
- **Viés**: um erro sistemático, que aponta sempre para o mesmo lado. Diferente de erro aleatório
  (que às vezes erra para cima, às vezes para baixo, e se cancela na média), o viés não se cancela:
  a previsão do modelo, por exemplo, é sistematicamente **menor** que o real durante picos de
  epidemia (ver §5.1.6 e §5.3.7).
- **Walk-forward**: o protocolo de avaliação usado em quase todo teste deste documento. Em vez de
  separar os dados em "treino" e "teste" de uma vez só (como se faz em problemas sem tempo), o
  modelo é treinado só com o passado disponível até uma certa semana, faz uma previsão para `h`
  semanas à frente, depois a data de corte avança uma semana, o modelo é retreinado com mais uma
  semana de dado, e o processo se repete. É a simulação mais honesta de como o modelo seria usado na
  prática: nunca se deixa o modelo "ver" dado que na vida real ainda não teria acontecido.

### 5.1.1 O problema que todas as regras abaixo resolvem

Um projeto de modelagem preditiva testa dezenas de hipóteses ao longo de meses. Se cada hipótese for
julgada isoladamente, sem memória do que já foi tentado, dois problemas destroem a credibilidade do
resultado final:

1. **Buscar até achar (data dredging).** Testando hipóteses suficientes, alguma vai "dar certo" só
   por acaso, mesmo que não exista efeito real. É estatística básica: se o limiar de significância é
   5%, e você testa 20 hipóteses independentes sem nenhum efeito real, o número esperado de "achados
   positivos" por puro acaso é `20 × 0,05 = 1`.
2. **Mover o alvo depois de ver o resultado.** Se o critério de sucesso só é definido depois de olhar
   o número, é sempre possível redesenhar o critério para que o resultado pareça bom.

As quatro práticas abaixo existem para fechar essas duas portas.

### 5.1.2 Pré-declaração escrita, antes de rodar

**O que é.** Antes de qualquer rodada nova, o projeto escreve, em um documento datado dentro de
`analises/AAAA-MM-DD_descricao/`, quatro coisas:

- a **hipótese** em uma frase (o que se espera encontrar);
- a **métrica** que vai decidir (por exemplo, erro absoluto médio, ou sensibilidade de um alarme);
- o **critério de decisão** (que número, ou que combinação de números, conta como "confirmado");
- a **família de correção de múltiplas comparações** (quantos testes serão feitos junto, para saber
  quanto o limiar de significância precisa ser apertado — ver Holm, §5.1.6).

**Por que existe.** Sem isso, qualquer resultado pode ser "explicado" depois de vê-lo. Um exemplo real
do próprio projeto, onde a ausência de pré-declaração custou caro: a escolha da perda quantílica como
remédio para o viés de pico (30/08/2026, ver §5.3.7) foi feita **lendo uma tabela depois do fato**,
sem teste formal. O documento `HISTORICO_DE_TESTES.md` sinaliza isso com uma advertência explícita:
"a escolha do remédio foi leitura de tabela, sem pré-declaração nem teste formal". O achado pode até
estar certo, mas carrega uma etiqueta de honestidade menor — é rotulado como **exploratório**, não
**confirmatório**, e essa diferença é o assunto da próxima seção.

**Qual erro isso previne.** Escolher, depois de ver os números, exatamente o corte que faz o resultado
parecer bom — o que estatísticos chamam de "p-hacking".

### 5.1.3 Emenda datada, nunca edição silenciosa

**O que é.** Quando uma pré-declaração precisa mudar — porque um erro foi encontrado, ou porque o
plano original não fazia sentido —, a mudança é registrada como um evento novo, com data e
justificativa, e o texto antigo **não é apagado nem reescrito por cima**.

**Exemplo real do projeto.** Em `PENDENCIAS.md`, a entrada de defasagem entre vetor e casos registra:
"o 'τ 0,59 no lag 8' que estava aqui **não existe no artigo** — erro meu, corrigido em 26/09/2026".
O erro antigo não foi apagado silenciosamente: ficou visível que existiu, quando foi corrigido, e qual
o valor correto (τ de Kendall de 0,274 no atraso 0 e 0,495 no atraso 4, do artigo de da Silva et al.
2026 — ver §5.5).

**Qual erro isso previne.** Reescrever a história do projeto de um jeito que o esconda de si mesmo —
um número errado que "desaparece" sem deixar rastro pode reaparecer meses depois, porque ninguém
lembra que já foi checado e estava errado.

### 5.1.4 Certificação adversarial por agente independente

**O que é.** Toda vez que um dado ou um trecho de código do pipeline de previsão muda, uma segunda
pessoa (ou um segundo agente de inteligência artificial, com instruções separadas) tenta **reprovar**
o resultado, refazendo a medição do zero — nunca lendo o código já escrito e concordando com ele.
"O teste passou" (rodar o código e não dar erro) **não é a mesma coisa** que "o teste foi certificado"
(uma segunda parte tentou ativamente encontrar o defeito e não encontrou).

**Exemplo real do projeto, com números.** A correção do vazamento temporal em 13/09/2026 (§6 abaixo)
reprocessou 152 células de uma grade de testes. Para provar que a correção não introduziu um erro
novo, o projeto usou uma trava lógica: em previsões de **1 semana à frente** (`h=1`), nenhuma linha do
treino deveria ter sido afetada pela correção (porque o vazamento só contamina linhas de horizonte
maior — ver §6.1). Se o resultado em `h=1` mudasse mesmo assim, a correção teria um bug. Foi
verificado em **6 experimentos independentes**, com diferença de **0,0000000000** entre o resultado
antigo e o novo, em mais de 12.000 pontos comparados. Diferença zero, ao invés de "quase zero", é a
evidência de que a trava estava correta — se a correção tivesse mexido em algo que não devia, ainda
que por um erro pequeno de arredondamento, a diferença não seria exatamente zero.

Outro exemplo: a recuperação do clima desde 2012 (29/08/2026, §5.4) foi conferida linha a linha por um
agente independente, que confirmou que **365 das 388 semanas antigas** ficaram idênticas ao dado
anterior; as 23 semanas diferentes foram checadas individualmente e explicadas por reprocessamento de
rotina da fonte de dados (NASA), não por erro do projeto.

**Qual erro isso previne.** Um autor tende a testar o próprio código de um jeito que confirma o que já
espera encontrar — não por má-fé, mas porque quem escreveu o código sabe onde ele "deveria" funcionar
e tende a testar ali. Uma segunda parte, sem esse conhecimento prévio, testa onde o autor não pensou.

### 5.1.5 Âncoras numéricas e travas de validação

**O que é.** Antes de aceitar qualquer resultado novo, certos números **têm que bater** com um valor
já conhecido e auditado. Se não baterem, o agente que está rodando o teste **investiga a causa**, e
**nunca ajusta o código só para o número bater**.

**Exemplo real e recente, incluindo uma divergência ainda em aberto.** Em 26/09/2026, ao refazer o
escore de erro por intervalo (WIS — ver definição em §5.1.6) na tabela de dados oficial, o resultado em
`h=1` do cenário adotado divergiu **−2,75%** da rodada anterior — acima do teto de tolerância de 1% que
o projeto usa como sinal de alerta. A causa provável apontada foi a seleção das colunas de clima ser
feita sobre os 60% mais antigos da série (uma dívida técnica documentada em §6.7), mas essa causa
**não foi confirmada**. O documento registra a divergência como pendência aberta, rotulada
"⚠️ Dívida", em vez de aceitar o número novo sem explicação ou de forçar o antigo.

⚠️ **Divergência que este documento também encontrou, e reporta em vez de corrigir sozinho:** o painel
de erro do cenário adotado cita **278,8** para o erro absoluto médio em `h=12`, mas o mesmo documento
anota entre parênteses que "o painel publicado" (o que está no site da banca) registra **278,7**. A
diferença é de **0,1 caso**, bem abaixo do teto de 1% usado como gatilho de investigação em outros
pontos do projeto — mas, seguindo a própria regra do projeto de nunca corrigir uma divergência em
silêncio, ela fica registrada aqui como está, sem decidir qual dos dois números é o certo.

**Qual erro isso previne.** Um pipeline de dados que muda ao longo de meses (novas semanas de dado
chegam, código é refatorado) pode introduzir um erro silencioso que não quebra nada, só produz um
número levemente diferente. Sem uma âncora para comparar, esse tipo de erro é invisível.

---

## 5.2 Caixa de ferramentas estatísticas usadas neste documento

Esta seção define, uma única vez, com fórmula e exemplo numérico, cada instrumento estatístico que
reaparece nas seções seguintes. As seções de detalhamento (§5.3) aplicam essas definições aos números
de cada hipótese, sem repetir a dedução completa.

### 5.2.1 Erro absoluto médio (MAE)

**O que mede.** Em média, "de quanto" o modelo erra, em número de casos, sem diferenciar se errou para
mais ou para menos.

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$

- $n$ — número de semanas comparadas (os "pares" avaliados);
- $y_i$ — o número real de casos confirmados na semana $i$;
- $\hat{y}_i$ — o número que o modelo previu para a semana $i$;
- $|\cdot|$ — valor absoluto (ignora o sinal do erro).

**Exemplo numérico com dado do projeto.** Na faixa que o projeto chama de "Alerta ou mais" (mais de 421
casos confirmados na semana, medido em 26/09/2026), o número real **mediano** foi **917 casos** e o
erro **mediano** do cenário adotado foi **539 casos**. Isso quer dizer que, numa semana típica dessa
faixa, o modelo previu por volta de `917 − 539 = 378` casos onde a cidade teve 917. **Tradução
concreta**: é como um hospital planejar leitos para 378 pacientes e receber 917 — mais que o dobro do
planejado. Para três semanas hipotéticas com esse padrão (917 reais / 378 previstos, erro 539; 46
reais / 44 previstos, erro 2; 12 reais / 10 previstos, erro 2), o MAE dessas três semanas seria
$(539+2+2)/3 = 181{,}0$ — um número puxado para cima pela única semana de pico, o que é exatamente o
motivo de o MAE do painel oficial (278,8 em `h=12`, sobre 284 semanas) ser maior que o erro típico em
semana de calmaria.

### 5.2.2 Coeficiente de determinação (R²)

**O que mede.** Que fração da variação do número real de casos o modelo consegue explicar, numa escala
de 0 (o modelo não explica nada, equivale a sempre prever a média) a 1 (o modelo explica tudo).
R² pode ficar **negativo** quando o modelo é pior do que simplesmente prever a média todo o tempo.

$$R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}$$

- $\bar{y}$ — a média de todos os valores reais no período avaliado;
- o numerador é a soma dos erros ao quadrado do modelo; o denominador é a soma dos erros ao quadrado
  de um "modelo" que sempre prevê a média.

**Exemplo numérico com dado do projeto.** Em `h=1`, o R² do cenário adotado é **0,898**: o modelo
explica cerca de **90%** da variação semana a semana dos casos. Em `h=12`, cai para **0,437**: o
modelo explica menos de **44%**, e mais da metade da variação fica sem explicação. Isso é consistente
com o próprio teste de autocorrelação do projeto (§5.3.6): o R² de prever `casos` de uma semana usando
só o `casos` de 12 semanas atrás é **0,000** — ou seja, em três meses, o passado recente por si só não
carrega quase nenhuma informação, e o pouco de R² que o modelo mantém (0,437) vem de outras variáveis
(clima e vetor), não da simples continuidade da série.

### 5.2.3 p-valor

**O que mede.** A probabilidade de observar uma diferença **tão grande quanto** a medida (ou maior),
**se a hipótese nula fosse verdadeira** — ou seja, se, na realidade, não existisse o efeito que se
está testando e a diferença observada fosse só sorte de amostragem. Não é a probabilidade de a
hipótese ser verdadeira; é a probabilidade dos **dados**, supondo que o efeito não existe.

**Como interpretar um p pequeno.** Um p-valor de **0,0001** (citado no bloco-bootstrap, §5.3.11) quer
dizer: se realmente não houvesse diferença nenhuma entre o modelo e a regra de comparação, a chance de
um estudo deste tamanho produzir, por puro acaso de amostragem, uma diferença tão grande quanto a
observada seria de **1 em 10 mil**. É um evento raro o bastante para que a explicação "foi sorte" fique
pouco convincente — mas note a distinção do parágrafo seguinte: p pequeno não significa efeito grande
nem importante, só significa que o efeito medido dificilmente é ruído puro.

**O limiar convencional.** Por convenção da estatística aplicada (não uma lei da natureza), costuma-se
chamar de "estatisticamente significativo" um resultado com p abaixo de **0,05** — 5% de chance de ser
só sorte. Este projeto usa esse mesmo corte, mas só depois de aplicar a correção de Holm (§5.2.4),
porque testar muitas hipóteses infla a chance de algum p pequeno aparecer por acaso.

### 5.2.4 Correção de Holm para múltiplas comparações

**O problema que resolve.** Se um projeto testa **60 comparações** independentes ao acaso, e nenhuma
tiver efeito real, o número esperado de p-valores abaixo de 0,05 só por sorte é `60 × 0,05 = 3`. Sem
correção, o projeto acabaria "descobrindo" três efeitos falsos.

**O procedimento (passo a passo).**

1. Ordene os $m$ p-valores da família de testes do menor para o maior: $p_{(1)} \le p_{(2)} \le \dots
   \le p_{(m)}$.
2. Para o menor p-valor, o limiar de comparação é $\alpha / m$.
3. Para o segundo menor, o limiar é $\alpha / (m-1)$; para o terceiro, $\alpha/(m-2)$; e assim até o
   maior, cujo limiar volta a ser $\alpha$ (o mesmo de um teste único).
4. Um resultado só é considerado significativo se ele **e todos os que vieram antes dele na fila**
   (com p menor) também passaram no respectivo limiar. Isso torna o procedimento **monótono**: o
   p-valor ajustado nunca pode ser menor que o do teste anterior na fila.

Em notação equivalente e mais usada na prática (o "p ajustado" que aparece nas tabelas do projeto):

$$p^{\text{Holm}}_{(i)} = \max_{j \le i} \Big[ (m - j + 1) \cdot p_{(j)} \Big], \quad \text{limitado a no máximo } 1$$

- $m$ — o tamanho da família de testes rodados juntos (o número que precisa ser declarado **antes**
  de rodar, por isso pré-declaração e Holm andam juntos);
- $p_{(j)}$ — o $j$-ésimo menor p-valor bruto da família;
- $p^{\text{Holm}}_{(i)}$ — o p-valor corrigido do $i$-ésimo teste, na mesma ordem.

**Exemplo numérico didático (números inventados só para ensinar o mecanismo, não são do projeto).**
Suponha uma família de $m=4$ testes com p-valores brutos $0{,}001$; $0{,}02$; $0{,}03$; $0{,}20$.
Multiplicadores, na ordem: $4, 3, 2, 1$. Resultado: $0{,}004$; $0{,}06$; $0{,}06$ (o segundo produto
seria $0{,}03 \times 2 = 0{,}06$, mas como não pode ser menor que o anterior ajustado de $0{,}06$,
fica $0{,}06$); $0{,}20$. Só o primeiro teste (p bruto 0,001) sobrevive ao corte de 0,05.

**Aplicação real do projeto.** Na família de testes de McNemar sobre o alarme de 100 casos por semana
(analisada em §5.3.9), o resultado mais forte tem discordância de **37 semanas**, dividida **31 a 6**
a favor de uma das regras — o p **bruto** dessa comparação (calculado pelo teste de McNemar, §5.2.6) é
pequeno o bastante para que, mesmo depois de multiplicado pelo tamanho da família e comparado com os
demais na fila de Holm, o resultado corrigido publicado seja **p = 0,00062**, ainda muito abaixo de
0,05. Já a comparação do cenário adotado contra "a mesma semana do ano passado" em `h=12`, com
discordância **16**, dividida **4 a 12**, não sobrevive: **p de Holm = 0,845**.

**Regra inegociável do projeto, e por quê.** "Sem sobreviver a Holm, não se escreve 'significativo'."
Isso existe porque, ao longo dos meses, o projeto já testou **dezenas** de comparações (o grid de
120 execuções, a busca de 120 configurações de hiperparâmetro, as 60 comparações pareadas de vetor, os
24 testes de McNemar do estágio Alerta). Sem Holm, a chance de algum "achado" ser só ruído amostral
acumulado seria alta demais para qualquer afirmação ser confiável.

### 5.2.5 Pareamento por data-alvo

**O que é.** Comparar dois modelos (ou um modelo contra uma regra simples) **só** nas semanas em que
os dois têm previsão disponível para a **mesma data de resposta** (`data_alvo`).

**Por que é obrigatório, com exemplo real.** No relatório interno `grid_resumo`, o conjunto de
variáveis **com** vetor perdia sete semanas de avaliação (109 → 102) em relação ao conjunto **sem**
vetor, porque a densidade de mosquitos ficava ausente (`NaN`) nessas semanas — e essas sete semanas
incluíam as **três semanas da enchente de maio de 2024** (1.347, 911 e 1.510 casos confirmados),
justamente as mais difíceis de prever. Ao restringir a comparação às mesmas semanas para os dois
lados, o erro do modelo sem vetor em `h=1` **caiu 18,5%**, e a vantagem que antes parecia existir a
favor do modelo com vetor **se inverteu**. A conclusão inteira do teste mudava de sinal só por causa
do pareamento — por isso "comparação entre modelos é pareada, ou não vale" é regra sem exceção do
projeto.

### 5.2.6 Teste de McNemar

**Para que serve.** Compara dois classificadores binários (por exemplo, dois alarmes de surto: "sim,
vai passar de 100 casos" ou "não") olhando só para as semanas em que os dois **discordam**. Semanas em
que os dois acertam, ou em que os dois erram, não carregam informação sobre qual é melhor — são
descartadas do cálculo.

$$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$$

- $b$ — número de semanas em que o classificador A acerta e o B erra;
- $c$ — número de semanas em que o B acerta e o A erra;
- o $-1$ dentro do parênteses é a **correção de continuidade**, usada porque uma contagem discreta
  (número inteiro de semanas) está sendo aproximada por uma distribuição contínua (qui-quadrado);
- o resultado, sob a hipótese nula de que os dois classificadores são igualmente bons, segue
  aproximadamente uma distribuição qui-quadrado com 1 grau de liberdade.

**Exemplo numérico com dado real do projeto.** Na comparação do cenário adotado contra a regra "hoje
já passou de 100 casos", em `h=12`, o total de semanas discordantes foi **37**, divididas **31 a 6**
(o modelo acerta e a regra erra em 31 semanas; a regra acerta e o modelo erra em 6). Calculando:

$$\chi^2 = \frac{(|31-6|-1)^2}{31+6} = \frac{(25-1)^2}{37} = \frac{576}{37} \approx 15{,}57$$

Um valor de qui-quadrado de 15,57 com 1 grau de liberdade corresponde a um p bruto da ordem de
**0,00008** — um evento extremamente raro sob a hipótese de empate. Depois de passar pela correção de
Holm (§5.2.4) dentro da família de comparações do estágio de 100 casos, o valor publicado do projeto é
**p = 0,00062** (ainda muito abaixo de 0,05): a correção de Holm torna o critério mais rigoroso, mas
não apaga um efeito deste tamanho.

### 5.2.7 Teste de equivalência (TOST)

**Em que difere de um teste comum.** Um teste de hipótese comum (como o de McNemar ou o
Diebold-Mariano, §5.2.9) tenta provar que existe **diferença**. O TOST ("two one-sided tests", dois
testes unilaterais) tenta provar o oposto: que a diferença entre dois métodos é **pequena o
suficiente para ser considerada equivalente na prática** — não que é exatamente zero, mas que fica
dentro de uma **margem de indiferença** decidida antes do teste.

**Mecanismo.** Define-se uma margem $\Delta$ (a maior diferença que ainda seria considerada "sem
importância prática"). O TOST testa, ao mesmo tempo, se a diferença é **significativamente maior que**
$-\Delta$ e **significativamente menor que** $+\Delta$. Só se as duas coisas forem verdadeiras a
equivalência é declarada.

**Por que a margem tem que vir de fora do próprio teste.** Este é um dos erros metodológicos mais
importantes já corrigidos no projeto (§5.3.1 e §5.1.2): a margem original do teste de equivalência
clima-vetor foi definida como uma **porcentagem do próprio erro do clima**, medido no mesmo teste. Isso
é circular — quanto pior o clima prevê, mais larga fica a régua que aprova a equivalência, tornando
praticamente impossível reprovar a hipótese. A correção foi ancorar a margem em algo **externo**: uma
porcentagem do erro de um modelo de referência que não depende do resultado (a persistência, que é só
repetir o valor de hoje).

### 5.2.8 Bootstrap por blocos e inflação do p-valor

**O que é bootstrap.** Uma técnica que estima a incerteza de uma medida **reamostrando os próprios
dados**, em vez de assumir uma fórmula matemática pronta para a variância. Em vez de calcular a
distribuição teórica de um p-valor, o computador gera milhares de conjuntos de dados artificiais,
parecidos com o original, e observa quão variável o resultado seria só por causa da amostragem.

**Por que "por blocos", e não sorteando semana a semana.** Séries temporais têm **autocorrelação**:
uma semana de epidemia tende a ser seguida por outra semana de epidemia. Se o bootstrap sorteasse
semanas isoladas, destruiria essa dependência e subestimaria a incerteza real. Por isso o projeto
sorteia **blocos contíguos** de semanas (testados com comprimento de 4, 8, 13 e 26 semanas), preservando
pedaços da estrutura temporal.

**O que o teste de 26/09/2026 mediu.** A razão entre o p-valor obtido pelo bootstrap e o p-valor
nominal (calculado pela fórmula teórica). Contra a regra "hoje já passou de 100 casos", essa razão
ficou entre **0,0001 e 0,82** — ou seja, o p nominal era, na pior leitura, ligeiramente **otimista
demais** por um fator de até `1/0,82 ≈ 1,22`, mas na maior parte das reamostragens o p nominal era, se
algo, **conservador demais** (razão bem abaixo de 1). Contra a regra "a mesma semana do ano passado",
a razão ficou entre **1,10 e 1,51** em `h=4` e entre **2,11 e 3,44** em `h=12`: aqui o p nominal é
**otimista** — o bootstrap diz que a incerteza real é de 2 a 3,4 vezes maior que a fórmula assumia.
Como o veredito do projeto contra essa régua **já era negativo** (o modelo não vence com significância
— §5.3.9), essa inflação **reforça** a conclusão, em vez de contradizê-la: mesmo que o p nominal
estivesse "generoso demais" com o modelo, corrigir isso só torna o resultado ainda menos favorável ao
modelo.

### 5.2.9 Teste de Diebold-Mariano

**Para que serve.** Compara o erro de previsão de dois modelos, semana a semana, e testa se a
diferença média de erro é maior do que se esperaria só por variação amostral — a versão do teste de
McNemar (§5.2.6) para erros **contínuos** (como o MAE) em vez de acerto/erro binário.

$$d_t = L(e_{1,t}) - L(e_{2,t}), \qquad DM = \frac{\bar{d}}{\widehat{SE}(\bar{d})}$$

- $L(\cdot)$ — uma função de perda aplicada ao erro de cada modelo na semana $t$ (por exemplo, o erro
  absoluto);
- $\bar{d}$ — a média das diferenças de perda ao longo de todas as semanas pareadas;
- $\widehat{SE}(\bar{d})$ — o **erro-padrão** (em inglês *standard error*, abreviado **SE**) dessa
  média, isto é, uma medida de quão precisamente a média amostral $\bar d$ estima a diferença real,
  ajustada para a autocorrelação da série de diferenças;
- sob a hipótese nula de igual capacidade preditiva, $DM$ segue aproximadamente uma distribuição
  normal padrão.

**Exemplo com dado do projeto.** Na comparação pareada de 15 pares de configurações com e sem vetor
(§5.3.2), em `h=12` o vetor "ganhava" em 13 dos 15 pares, com uma redução média de erro de **22,5**
casos — um número que soa favorável. Mas ao rodar o Diebold-Mariano sobre a família inteira de 60
comparações e aplicar Holm, **nenhuma das 60** sobrevive: a diferença de 22,5 casos, medida sobre um
número limitado de semanas de avaliação, não é grande o bastante, frente à variabilidade amostral,
para ser distinguida de zero com confiança.

### 5.2.10 Escore de intervalo ponderado (WIS)

**Contexto: por que não basta prever um número só.** Um alarme de vigilância não decide só "quantos
casos teremos", decide **até onde estar preparado**. Por isso, em vez de uma única previsão, o
cenário adotado usa **perda quantílica** (definida a seguir) para produzir um **intervalo de
confiança (IC)**: uma faixa de valores dentro da qual se espera que o número real caia, com uma certa
probabilidade declarada (por exemplo, um IC de 90% deveria conter o valor real em 90% das semanas, se
a calibração estiver correta).

**O que é a perda quantílica.** Um **quantil** é o valor abaixo do qual cai uma certa fração dos
dados — o quantil 0,85, por exemplo, é o valor que **85%** das observações não ultrapassam. A perda
quantílica pune de forma **assimétrica** o erro de um modelo que tenta acertar um quantil específico:

$$L_\tau(y, \hat{y}) = \begin{cases} \tau \cdot (y - \hat{y}) & \text{se } y \ge \hat{y} \\ (1-\tau) \cdot (\hat{y} - y) & \text{se } y < \hat{y} \end{cases}$$

- $\tau$ — o quantil-alvo (o projeto usa $\tau = 0{,}85$);
- se o modelo **subestima** ($y \ge \hat y$), a perda é multiplicada por $\tau = 0{,}85$;
- se o modelo **superestima** ($y < \hat y$), a perda é multiplicada por $(1-\tau) = 0{,}15$.

Isso faz o modelo aprender a **errar mais vezes para cima** do que para baixo — de propósito, porque
o projeto decidiu que subestimar um surto de dengue custa mais caro para a vigilância do que
superestimar (mais leitos hospitalares reservados à toa custam menos que hospitais lotados sem aviso).

**A fórmula do escore de intervalo (WIS), passo a passo.** O escore de intervalo ponderado (em inglês
*weighted interval score*, abreviado **WIS**) combina vários intervalos de confiança, de diferentes
níveis, numa única nota de qualidade — quanto **menor**, melhor.

Primeiro, o escore de um único intervalo com nível de cobertura $(1-\alpha)$, limite inferior $l$ e
limite superior $u$:

$$IS_\alpha(l, u; y) = (u - l) + \frac{2}{\alpha}(l - y)\cdot \mathbb{1}\{y < l\} + \frac{2}{\alpha}(y - u)\cdot \mathbb{1}\{y > u\}$$

- $(u-l)$ — a **largura** do intervalo: quanto mais largo, pior (menos informativo);
- o segundo termo só é diferente de zero se o valor real $y$ ficou **abaixo** do limite inferior —
  penaliza a falta de cobertura por baixo, com peso $2/\alpha$;
- o terceiro termo só é diferente de zero se $y$ ficou **acima** do limite superior — penaliza por
  cima, mesmo peso;
- $\mathbb{1}\{\cdot\}$ — função indicadora: vale 1 se a condição é verdadeira, 0 caso contrário.

O WIS combina vários desses intervalos (o projeto usa os pares de quantis que formam os IC de 50% e de
90%) com a mediana $m$:

$$WIS = \frac{1}{K + 0{,}5}\left[ \frac{1}{2}|y - m| + \sum_{k=1}^{K} \frac{\alpha_k}{2} IS_{\alpha_k}(l_k, u_k; y) \right]$$

- $K$ — número de intervalos usados (aqui, 2: o de 50% e o de 90%);
- cada intervalo $k$ tem seu próprio $\alpha_k$ ($\alpha=0{,}5$ para o IC de 50%; $\alpha=0{,}1$ para
  o de 90%).

**Exemplo numérico ilustrativo, construído a partir de números reais do projeto.** Na faixa "Alerta ou
mais" (mais de 421 casos), o real mediano medido foi **917** e a largura medida do IC de 90% foi
**592,7** casos. Supondo, para fins de exemplo, um intervalo aproximadamente centrado no valor
previsto (mediana $m \approx 378$, coerente com o erro mediano de 539 já discutido em §5.2.1), os
limites do IC de 90% ficariam por volta de $l \approx 82$ e $u \approx 674$. Como o real (917) fica
**acima** do limite superior (674):

$$IS_{0{,}1}(82, 674; 917) = (674-82) + 0 + \frac{2}{0{,}1}(917-674) = 592 + 4.860 = 5.452$$

Um número alto, dominado quase inteiramente pelo termo de penalização por falta de cobertura — o
exato comportamento que o projeto mede de forma agregada na tabela de calibração por faixa (§5.3.7):
nas semanas de "Alerta ou mais", o IC de 90% cobre o valor real em só **17,8%** das vezes, quando o
esperado seria 90%.

**Por que o projeto usa WIS como métrica de erro, ao lado do MAE.** O MAE julga só a previsão central
(a mediana); o WIS julga a **faixa inteira**, incluindo se ela é larga demais ou estreita demais e se
cobre o valor real. Um modelo pode ter bom MAE e mau WIS (faixas mal calibradas), ou vice-versa — por
isso o projeto trata a escolha de qual métrica é a "principal" como uma decisão de produto, não uma
questão puramente técnica (ver §5.1, pendência aberta com o Vinicius sobre MAE × WIS).

### 5.2.11 Sensibilidade, precisão e índice de Youden

Para avaliar um **alarme** (uma decisão binária: "vai passar de X casos, sim ou não"), quatro
contagens organizam tudo: verdadeiro-positivo (VP, o alarme dispara e o surto acontece),
falso-positivo (FP, dispara e não acontece), falso-negativo (FN, não dispara e acontece) e
verdadeiro-negativo (VN, não dispara e não acontece).

$$\text{Sensibilidade} = \frac{VP}{VP + FN} \qquad \text{Precisão} = \frac{VP}{VP + FP} \qquad \text{Especificidade} = \frac{VN}{VN+FP}$$

$$J_{\text{Youden}} = \text{Sensibilidade} + \text{Especificidade} - 1$$

- **Sensibilidade** — de todos os surtos que de fato aconteceram, que fração o alarme conseguiu
  capturar;
- **Precisão** — de todas as vezes que o alarme disparou, que fração era surto de verdade (o
  complemento é a taxa de falso alarme);
- **Índice de Youden** — varia de −1 a 1; mede a qualidade do alarme somando o quão bem ele acerta os
  positivos e os negativos, com **zero** significando desempenho igual ao acaso.

**Exemplo com dado real do projeto.** Em `h=4`, o cenário adotado tem sensibilidade **97,1%** e
precisão **94,3%**, com **0,7 falsos alarmes por ano** — de cada 100 surtos reais de mais de 100
casos por semana, o modelo avisa 97; de cada 100 avisos, 94 eram surtos de verdade; e, num ano típico,
o modelo dá menos de um alarme falso. O índice de Youden desse cenário é **0,94** — muito próximo do
máximo teórico de 1. Em `h=12`, a sensibilidade cai para **76,9%**, a precisão para **81,1%**, os
falsos por ano sobem para **2,3**, e o Youden cai para **0,66**: o alarme de três meses é
sensivelmente pior que o de um mês, mas ainda longe do acaso (Youden 0).

---

## 5.3 Tabela mestra de todas as hipóteses testadas

| Data | Hipótese (uma frase) | Como foi testada | Resultado numérico | Veredito | Estatuto |
|---|---|---|---|---|---|
| 16/08/2026 | Clima e densidade de vetor são informacionalmente equivalentes para prever casos | TOST inicial, margem de ±15% | Não fechou dentro da margem | Inconclusiva (superada em 29/08) | Exploratório |
| 16/08/2026 | Bairro administrativo é granularidade espacial válida | Confiabilidade split-half do número semanal por bairro | 31% de ruído de amostragem (0,69) | Refutada | Confirmatório |
| 16/08/2026 | Zonas sintéticas (k-means) reduzem o ruído espacial | Split-half em zonas com k=8 | Confiabilidade sobe a 0,92 | Confirmada | Confirmatório |
| 16/08/2026 | Notificados dão mais poder estatístico que confirmados | Projeção teórica de tamanho de amostra | — | Refutada na prática (30/08) | Exploratório |
| 29/08/2026 | O clima estava truncado desde 2018 por artefato de captura | Auditoria da fonte de dados | 388 → 727 semanas recuperadas | Confirmada (correção de dado) | Confirmatório |
| 29/08/2026 | O vetor melhora o alarme de surto (percentil 90, alvo confirmados) | McNemar, h=12 | 4×24 a favor do vetor, p Holm 0,00108 | 🚫 Era vazamento (ver 13/09) | Refeito |
| 29/08/2026 | Clima e vetor são equivalentes na série longa (Rodada 2) | TOST, 4 conjuntos × 4 horizontes × 2 alvos | Margem indevida + alvo trocado | Refutada em 13/09 | Confirmatório |
| 29/08/2026 | Aprendizado de máquina supera regra simples no ranking espacial | Spearman entre ranking previsto e real, k=8 | Persistência vence em 8 de 8 (pós-correção) | Refutada (para o modelo) | Confirmatório |
| 29/08/2026 | Janela de treino desde 2012 supera janelas mais curtas (alvo vetor) | Ablação: deslizante 6a × expansível 2012 × expansível 2020 | Expansível 2012 vence em 3 de 4 horizontes | Confirmada | Confirmatório |
| 29/08/2026 | O vetor sozinho tem poder estatístico com alvo notificados | Regeneração oficial | Achado dependia de vazamento | Refutada em 13/09 | Refeito |
| 30/08/2026 | O viés de pico vem de limite de extrapolação das árvores | Comparação teto do treino × picos reais | Só 5 de 32 picos acima do teto | Refutada | Confirmatório |
| 30/08/2026 | A perda quantílica corrige o viés de subestimação de pico | 4 remédios comparados | Única que reduz o viés nos 4 horizontes | Confirmada (sem pré-declaração) | Exploratório |
| 30/08/2026 | Existe um alpha de calibração ótimo único | Varredura de alpha | Superado pelo grid de 120 execuções | Sem veredito próprio | Exploratório |
| 30/08/2026 | O vetor ajuda no modelo já calibrado | 8 comparações | 6 de 8 a favor, nada sobrevive a Holm | Inconclusiva | Exploratório |
| 30/08/2026 | HistGB + perda quantílica + vetor é a melhor configuração entre 30 | Grid de 120 execuções, juiz = avaliação 2024+ | Refeito em 13/09 (vazamento) | Refeita | Confirmatório |
| 30/08/2026 | Lags anuais, anomalia climática, acúmulo 8-12 semanas e Rt/p_rt1 ajudam | 5 famílias de features testadas | 4 de 5 reprovadas; só ENSO passou isolado | Refutada (4/5) | Confirmatório |
| 30/08/2026 | Confirmados é melhor alvo que notificados ou casos_est | 3 candidatos na config. vencedora | R² 0,758 × 0,418 (com vazamento, direção mantida) | Confirmada | Confirmatório |
| 30/08/2026 | O ganho de notificados sobre confirmados é real | Janela equalizada (mesmas semanas) | Achado derrubado ao parear | Refutada | Confirmatório |
| 30/08/2026 | Vetor ajuda especificamente em h=12 | 5 sementes aleatórias | Nada sobrevive a Holm | Inconclusiva | Exploratório |
| 13/09/2026 | O corte de treino contamina o resultado (vazamento temporal) | Auditoria da mecânica do walk-forward | Vazamento confirmado, corte pela pergunta não pela resposta | Confirmada | Confirmatório |
| 13/09/2026 | A correção do vazamento muda os resultados anteriores | Reprocessamento de 152 células, certificado | MAE sobe até 52,5% em h=12; R² cai de 0,758 a 0,437 | Confirmada | Confirmatório |
| 13/09/2026 | A perda quantílica importa mais que o algoritmo escolhido | Comparação de efeito relativo, antes/depois da correção | Ordem se inverte: perda 9,9% × algoritmo 11,8% | Refutada | Confirmatório |
| 13/09/2026 | O modelo é um bom alarme de surto de 100 casos | Reagregação das previsões já salvas | 97,1% sensibilidade em h=4; 76,9% em h=12 | Confirmada | Confirmatório |
| 13/09/2026 | O vetor piora o alarme de surto em 3 meses | McNemar, alvo notificados, percentil 90, h=12 | 23×7, p Holm 0,037 | Confirmada — único resultado do projeto que sobrevive a Holm | Confirmatório |
| 13/09/2026 | A janela de treino ideal para o alvo casos é uma janela específica | 4 regimes, mesmas semanas pareadas | Indeterminado (2×1×1); janela pesa 3,8% contra 9,9% da perda | Inconclusiva (por desenho) | Confirmatório |
| 23-24/09/2026 | Lags de 5 a 12 semanas, e de 52/104 semanas, melhoram a previsão | Testados isoladamente e em combinação | Não reduzem o erro em nenhuma coluna | Refutada | Confirmatório |
| 24/09/2026 | O ENSO (El Niño/La Niña) melhora a previsão | Validação limpa, sem vazamento de agosto | Piora h=12 em 11,6% | Refutada | Confirmatório |
| 24/09/2026 | Com folha mínima 20, o vetor reduz o erro em 3 meses | Bateria noturna, blocos 2-7 | Reduz 12-16% em 2024-25, mas carregado por 2024 | Exploratória, depois invertida em 2026 | Exploratório |
| 25/09/2026 | O modelo bate uma regra sazonal simples (MAE) | Comparação com 3 regras, 9 configurações | Régua sazonal vence em h=8 e h=12 | Refutada (para o modelo, nestes horizontes) | Confirmatório |
| 25/09/2026 | Perder para régua em 3 meses é incomum na literatura | Varredura e catálogo de artigos publicados | É comum; POA está acima da média publicada | Confirmada (leitura descritiva) | Exploratório |
| 25/09/2026 | Mudar a formulação do alvo melhora o modelo | 6 variantes pré-declaradas, Holm por família | Nenhuma bate a régua; 2 explodem numericamente | Refutada | Confirmatório |
| 25/09/2026 | Modelos de fundação pré-treinados batem a régua | Chronos-Bolt e Chronos-2, zero-shot | Nenhum bate; melhor erra 227,2 × 217,8 da régua | Refutada | Confirmatório |
| 25/09/2026 | SARIMA e LASSO servem para esta série | Ajuste direto, pré-declarado | Ambos explodem no início de epidemia | Refutada | Confirmatório |
| 25/09/2026 | Pela perda quantílica, um modelo de fundação vence o cenário adotado | Leitura descritiva pós-hoc | Chronos-2: 100,9 × 191,2 (47% menor) | Achado descritivo, não confirmatório | Exploratório |
| 25/09/2026 | O modelo vence o canal endêmico como alarme | Classificador, evento = acima do canal | 1 mês: vence; 3 meses: empata com "ano passado" | Parcialmente confirmada | Confirmatório |
| 26/09/2026 | Uma busca ampla de hiperparâmetros supera a configuração adotada | 120 configurações sorteadas (60+60), julgadas em 2024-25 | Nenhuma passa no critério pré-declarado; menor p Holm 0,17 | Refutada | Confirmatório |
| 26/09/2026 | O desempenho de 2026 (ano atípico) muda o veredito sobre o vetor | 16 semanas de 2026, pré-declarado e certificado | Vetor inverte de sinal; p Holm 0,0499 contra | Confirmada, mas 2026 excluído da avaliação oficial | Confirmatório |
| 26/09/2026 | O modelo é melhor alarme que a régua no estágio Alerta (421 casos) | McNemar, 24 testes, evento pré-declarado | 0 de 4 vence "ano passado"; vence "hoje" em h=12 | Refutada (contra régua sazonal) | Confirmatório |
| 26/09/2026 | Transformar a escala (raiz, log) melhora a calibração dos intervalos | 3 braços, pré-declarado, certificação adversarial | Cobertura piora em todas as faixas | Refutada | Confirmatório |
| 26/09/2026 | O p-valor do teste de vetor-no-alarme é inflado por autocorrelação | Bloco-bootstrap, 4 comprimentos, 2.000 reamostragens | Robusto contra "hoje"; otimista até 3,4× contra "ano passado" | Confirmada (reforça o veredito negativo) | Confirmatório |
| 26/09/2026 | O limiar de Porto Rico (percentil 75 sobre histórico) se aplica a Porto Alegre | Leitura do MMWR original | Porto Rico usa 38,5 anos de série; POA não tem histórico calmo equivalente | Refutada (premissa não se transfere) | Confirmatório |
| 26/09/2026 | O artigo de da Silva et al. 2026 é comparável direto ao projeto | Leitura integral do preprint | Preprint não revisado por pares; alvo, validação e horizonte diferentes | Não comparável diretamente | Confirmatório |

---

## 5.4 Detalhamento das hipóteses centrais

### 5.4.1 A equivalência entre clima e vetor (refutada em 13/09/2026)

**A hipótese, e por que importava.** Se a densidade de mosquitos capturada pelas armadilhas
carregasse a **mesma informação** que as variáveis climáticas para prever casos de dengue, isso
sustentaria um argumento forte a favor da rede de armadilhas: ela não seria redundante com uma fonte
de dado mais barata (estações meteorológicas). Essa hipótese foi promovida a acento central do projeto
em 29/08/2026.

**Como foi testada.** Teste de equivalência TOST (§5.2.7) sobre 4 conjuntos de variáveis (clima puro,
vetor puro, e os dois combinados com o histórico autorregressivo de casos), em 4 horizontes, para 2
alvos possíveis (casos confirmados e casos notificados) — 576 a 587 semanas pareadas por comparação.

**O que decidiu o veredito: dois erros de execução encontrados em auditoria.**

1. **A margem estava errada.** A pré-declaração de 29/08 mandava fixar a margem de equivalência como
   uma porcentagem do erro da **persistência** (repetir o valor de hoje) — um referencial externo, que
   não depende do resultado do próprio teste (ver §5.2.7). O código efetivamente rodado usou, em vez
   disso, uma porcentagem do erro do **próprio clima**. Na prática, isso torna a régua de aprovação
   **cerca de quatro vezes mais larga** do que deveria: no exemplo medido, a margem correta seria
   **6,8** casos de erro, e a margem usada foi **27,5**.
2. **O alvo estava errado.** Os resultados otimistas ("4 de 8" combinações equivalentes) foram
   medidos usando **casos notificados** como alvo; a decisão vigente do projeto é usar **casos
   confirmados**.

**O número que decidiu.** Corrigindo os dois erros:

| Alvo | Margem do código (errada) | Margem pré-declarada (correta) |
|---|---|---|
| Confirmados (o alvo decidido) | 0 de 8 combinações equivalentes | **1 de 8** |
| Notificados | 4 de 8 | **0 de 8** |

E mais: em `h=1`, o vetor parecia ganhar por 23,0 casos de erro (p bruto 0,049) — mas o intervalo de
confiança dessa diferença **inclui zero**, e com Holm o p sobe para 0,388. O **único** intervalo de
confiança que exclui zero na família inteira aponta **contra** o vetor: em três meses, o clima sozinho
ganha por 72,5 casos de erro.

**Veredito: refutada como núcleo da tese, com data e responsável.** Descartada como acento central em
13/09/2026, por decisão registrada no próprio histórico do projeto (a lápide em §5.6 abaixo cita "margem
errada e alvo errado" como causa).

### 5.4.2 "A função de perda importa mais que o algoritmo" (refutada)

**A hipótese.** Era a crítica metodológica mais forte que o projeto tinha construído até 30/08/2026:
a escolha de **como punir o erro** (a função de perda) importaria mais para o resultado final do que
a escolha de **qual algoritmo de aprendizado de máquina** usar — um argumento que, se sustentado,
seria uma contribuição metodológica própria, porque a literatura da área costuma comparar algoritmos
sem discutir a função de perda.

**Como foi testada.** Comparação do efeito relativo de trocar o algoritmo pelo melhor concorrente
(LightGBM) contra o efeito de trocar a função de perda (de padrão para quantílica), medida antes e
depois da correção do vazamento temporal de 13/09.

**O número que decidiu.**

| Troca | Efeito antes da correção | Efeito depois da correção |
|---|---|---|
| Melhor algoritmo pelo LightGBM | +16,5% de erro | **+11,8%** |
| Perda padrão pela quantílica | +20,2% de erro | **+9,9%** |

A ordem das duas barras **se inverteu**: com o dado corrigido, o algoritmo pesa mais (11,8%) que a
perda (9,9%) — o oposto do que a hipótese original afirmava. Além disso, o efeito da perda **depende**
de qual algoritmo está sendo usado: +9,9 pontos percentuais no HistGradientBoosting (o algoritmo do
cenário adotado), +8,0 no GradientBoosting comum, e **−1,9** no LightGBM (ou seja, no LightGBM a perda
quantílica **piora** o resultado, na direção contrária às outras famílias de algoritmo).

**Veredito: refutada, mas com um achado mais fraco e ainda defensável.** A frase forte ("a perda
importa mais que o algoritmo") não se sustenta. Uma versão mais modesta sobrevive: a função de perda
tem um efeito **comparável em magnitude** ao do algoritmo, e esse efeito é **condicional** ao
algoritmo escolhido — e a prática comum na literatura de comparar algoritmos sem discutir a função de
perda é, por essa evidência, incompleta.

### 5.4.3 O vetor no alarme de surto — o único resultado que sobrevive a Holm, e é negativo

**A hipótese.** Mesmo que o vetor não ajude a prever o **número exato** de casos (§5.4.1), ele poderia
ajudar a antecipar **se** vai haver surto — uma tarefa mais fácil, e mais próxima do uso real de um
sistema de vigilância.

**Como foi testada.** Um classificador binário: uma semana é "surto" se os casos, `h` semanas à
frente, ficarem acima de um percentil calculado **só com o passado disponível até aquele ponto** (sem
espiar o futuro — a mesma disciplina do walk-forward, §5.1). Compara-se "só clima" contra "clima +
vetor" pelo teste de McNemar (§5.2.6). Alvo: casos notificados, percentil 90, horizonte de 12 semanas,
**n = 553** semanas.

**O número que decidiu, e como a correção do vazamento mudou tudo.**

| | Antes da correção do vazamento | Depois (dado corrigido) |
|---|---|---|
| Clima acerta e vetor erra × vetor acerta e clima erra | 14 × 10 | **23 × 7** |
| p bruto (McNemar) | 0,541 | **0,0062** |
| p de Holm | 1,000 | **0,037** |

**Por que faz sentido, tecnicamente.** Com o vazamento, as colunas do vetor conseguiam "pagar" seu
próprio custo de complexidade espiando informação de semanas vizinhas que, na prática real, ainda não
estaria disponível — e o resultado ficava nulo, sem direção clara. Removido o vazamento, o vetor
aparece pelo que estatisticamente é, num horizonte de três meses: uma fonte de ruído adicional que
**degrada** um classificador que, sem ela, seria mais estável.

**Veredito: confirmada, e é o resultado mais robusto do projeto contra correção de múltiplas
comparações — mas ainda exploratória quanto à direção.** É o único resultado, entre todos os testados
até 26/09/2026, que sobrevive à correção de Holm. Ainda assim, a direção específica ("o vetor piora")
não estava escrita na pré-declaração antes de rodar — ela só vira **confirmatória** de fato com uma
segunda temporada de dados (2026-2027), testada com a mesma direção pré-anunciada. O bloco-bootstrap
de 26/09/2026 (§5.2.8) mostrou que esse p-valor é, se algo, **conservador** (a incerteza real medida
por reamostragem foi menor que a nominal contra a regra "hoje"), o que reforça a confiança no
resultado.

### 5.4.4 O ganho do vetor com folha mínima 20 (exploratório, carregado por 2024)

**A hipótese.** Um hiperparâmetro específico do HistGradientBoosting — o número mínimo de semanas de
treino que cada "folha" final da árvore de decisão precisa ter antes de parar de se dividir — poderia
mudar a conclusão sobre o vetor. Com uma folha mínima maior (20, contra o 5 do cenário adotado), a
árvore fica mais simples e menos propensa a se ajustar a ruído.

**O que deu, e a mudança de direção entre 2024-25 e 2026.**

- Em 24/09/2026 (bateria noturna): com folha mínima 20, em três meses, o vetor **reduzia** o erro em
  2024-2025.
- Em 26/09/2026, testando especificamente a temporada de 2026: o vetor **inverteu** — passou a
  **piorar** a previsão. Com folha 20, o erro em 3 meses foi **579 casos com vetor** contra **315 sem
  vetor**; com LightGBM, **565 com vetor** contra **315 sem**. A diferença sobrevive à correção de
  Holm: **p = 0,0499** — dentro do limiar convencional de 0,05, mas por uma margem muito estreita.

**Por que "exploratório, carregado por 2024" é o rótulo certo.** O ganho de 2024-2025 vem de **duas
temporadas**, e uma delas (2024) teve uma epidemia severa que domina a média — não há garantia de que
o padrão se repita em anos comuns. Já o resultado de 2026 mostra o oposto, num ano atípico (mosquito em
nível crítico, só 19 casos confirmados). O padrão de "ajuda em ano de epidemia, atrapalha em ano
calmo" também apareceu de forma independente no modelo de fundação Chronos-2 (§5.4.6), o que é um
indício (não uma prova) de que o efeito é real e não um acidente de um único algoritmo.

**Veredito: nem confirmada nem refutada — pendência explícita para 2027.** A `PENDENCIAS.md` já regista
uma rodada confirmatória planejada para a temporada de 2027, pré-declarada antes de a temporada
começar, especificamente para decidir esta hipótese com um dado que ainda não influenciou a escolha do
hiperparâmetro.

### 5.4.5 O ENSO (El Niño – Oscilação Sul) como variável de entrada

**Contexto: o que é o ENSO.** El Niño–Oscilação Sul é um padrão climático de larga escala, ligado à
temperatura da superfície do Oceano Pacífico, que influencia o regime de chuvas e temperatura em boa
parte da América do Sul, incluindo o Rio Grande do Sul — e, por extensão, o ambiente propício à
reprodução do mosquito *Aedes aegypti*.

**A hipótese.** Incluir um índice numérico do ENSO como variável de entrada do modelo melhoraria a
previsão de casos, ao capturar variação climática de ciclo mais longo que a temperatura e chuva locais
não capturam.

**O que deu.** Em 30/08/2026, testado isoladamente, o ENSO parecia melhorar o erro em `h=8` por cerca
de **7%**. Mas essa medição nunca foi validada dentro do protocolo completo do grid (walk-forward com
corte correto de treino). Em 24/09/2026, ao revalidar dentro do protocolo — depois da correção do
vazamento temporal de 13/09 — ficou claro que o ganho de agosto **era, ele mesmo, um vazamento**:
uma vez removido, o ENSO **piora** a previsão em `h=12` em **11,6%**.

**Veredito: refutada, com data e causa identificada.** Descartado como atributo em 24/09/2026. A
lição geral (registrada em §5.6 do documento de metodologia) é que qualquer ganho isolado, fora do
protocolo de validação completo, deve ser tratado como candidato, nunca como parte confirmada da
configuração — exatamente o mesmo padrão de erro do vazamento temporal original (§6.1).

### 5.4.6 Janelas de defasagem longas (lags)

**O que é um lag, em uma frase.** Um "lag" (defasagem) de `k` semanas é o valor de uma variável medido
`k` semanas **antes** da semana que se está tentando prever — por exemplo, "a densidade de mosquitos
de 8 semanas atrás" como atributo de entrada para prever os casos de hoje.

**A hipótese.** Se existe uma defasagem biológica entre a picada infectante do mosquito, a incubação
do vírus da dengue (em inglês *dengue virus*, abreviado **DENV**) no organismo humano, e a
notificação do caso, os lags mais informativos poderiam estar mais distantes do que os poucos usados
no cenário adotado — por exemplo, 8 ou 12 semanas em vez de 4.

**O que foi testado no projeto.** Entre 23 e 24/09/2026: lags de 5 a 12 semanas e lags anuais (52 e
104 semanas, i.e., "o mesmo período do ano passado" e "de dois anos atrás") como atributos adicionais,
testados isoladamente e em combinação. **Nenhum reduz o erro**, nem em todas as colunas nem
restringindo só às colunas do vetor.

**O que a literatura mede, e o que o projeto ainda não estimou por conta própria.** O preprint de da
Silva et al. (2026, ver §5.5) mediu a correlação de posto de Kendall (uma medida de associação entre
duas variáveis ordenadas, que varia de −1 a 1) entre o índice de mosquitos e os casos de dengue, em
diferentes defasagens: **τ = 0,274** na defasagem 0 (mesma semana) e **τ = 0,495** na defasagem de 4
semanas — a tabela do próprio artigo **para na defasagem 4**, não testando mais longe. 🔬 **HIPÓTESE,
não testada por este projeto:** se a defasagem ótima entre vetor e casos, medida com os dados e o
protocolo deste projeto (walk-forward, sem vazamento), seguiria o mesmo padrão crescente até a
defasagem 4 encontrado por da Silva et al. Isso nunca foi estimado aqui — é uma pendência explícita,
registrada em `PENDENCIAS.md`.

**Veredito: refutada para a faixa testada (5 a 12 semanas, e lags anuais); em aberto para a faixa de 0
a 4 semanas.**

### 5.4.7 O horizonte de 3 meses: o modelo é confiável, mas só até 1 mês

Esta seção reúne três medidas diferentes para responder a uma pergunta que motivou boa parte da
discussão do projeto: **até que ponto se pode confiar na previsão?** A resposta muda dependendo de se
a pergunta é sobre o **número exato** (MAE) ou sobre um **alarme binário** (McNemar) — e depende
fortemente do horizonte.

**Pelo erro absoluto médio (MAE), o modelo perde para a regra sazonal em 2 e 3 meses.** A régua
"a mesma semana do ano passado" tem erro **202,1 · 213,2 · 216,2 · 217,8** nos horizontes 1, 4, 8 e 12
semanas (avaliação completa, 01/01/2024 a ~01/02/2026); o cenário adotado tem **98,0 · 219,7 · 272,6 ·
278,8** — o modelo vence claramente em `h=1`, empata aproximadamente em `h=4`, e perde em `h=8` e
`h=12`. ⚠️ **A régua sazonal muda de valor conforme a janela de avaliação**: na janela mais estreita de
2024-2025 (n=97), ela dá **210,4 · 222,0 · 225,1 · 226,8** — sempre é preciso dizer qual janela está
sendo citada.

**Pelo escore de intervalo ponderado (WIS), o quadro se inverte em parte: o modelo vence em 1 mês.**
Medido na tabela de dados oficial (26/09/2026), em `h=4` tanto o cenário adotado (WIS 215,4) quanto a
variante de folha mínima 20 (WIS 199,0) vencem a régua climatológica (WIS 313,5), com **p de Holm <
0,0001** — um resultado forte e claramente significativo. Em `h=12`, só a variante de folha 20 (WIS
278,6) vence a régua (WIS 324,2, p Holm 0,0020); o cenário **adotado** (WIS 300,7) **não** vence (p
Holm 0,096).

**Pelo alarme de McNemar contra as regras simples (o quadro mais importante deste documento).**
Comparando o alarme do cenário adotado (dispara quando a previsão ultrapassa 100 casos) contra dois
alarmes sem aprendizado de máquina — "hoje já passou de 100" e "o ano passado passou de 100" —, no
evento "mais de 100 casos confirmados por semana":

| Horizonte | Comparação | Semanas discordantes | Divisão a favor/contra | p de Holm | Significativo? |
|---|---|---|---|---|---|
| 4 semanas | adotado × "hoje já passou" | 15 | 13 a 2 | **0,103** | Não |
| 4 semanas | adotado × "o ano passado" | 7 | 5 a 2 | **1,000** | Não |
| 12 semanas | adotado × "hoje já passou" | 37 | 31 a 6 | **0,00062** | **Sim** |
| 12 semanas | adotado × "o ano passado" | 16 | 4 a 12 | **0,845** | Não |

**O que esta tabela diz, com todas as letras.** Em `h=4` (um mês), o modelo é claramente melhor que
"hoje já passou" (vence 13 vezes contra 2), mas essa diferença **não sobrevive** à correção de Holm
(p=0,103) — o tamanho da amostra ainda é pequeno demais para provar isso com confiança estatística,
mesmo que a direção pareça favorável. Contra "o ano passado" em `h=4`, o placar é quase empatado (5 a
2) e também não significativo. Em `h=12` (três meses), o modelo vence "hoje já passou" com folga e
**com significância estatística** (p=0,00062) — mas isso não é uma vitória sobre a régua mais forte:
contra "o ano passado", o modelo **perde** o placar (4 a 12) e a diferença também não é significativa.

**A frase resumo que este documento sustenta, e a razão para ela.** "O modelo é confiável para um mês"
é uma afirmação que a tabela acima **sustenta apenas parcialmente**: em 1 mês (`h=4`), a direção
observada é favorável ao modelo contra as duas regras, mesmo sem sobreviver a Holm com a amostra atual
(um problema de tamanho de amostra, não necessariamente de ausência de efeito real — o próprio
bloco-bootstrap, §5.2.8, mostra que a incerteza contra "o ano passado" tende a ser subestimada pela
fórmula nominal, o que pede cautela adicional). Em 3 meses (`h=12`), o modelo bate uma regra fraca
("hoje já passou") com sobra, mas **não** bate a regra mais forte disponível ("a mesma semana do ano
passado"). **Não se pode escrever "o modelo vence a régua sazonal em 3 meses"** — isso seria falso
frente a este quadro.

### 5.4.8 As seis formulações alternativas do alvo

**A hipótese.** Talvez o problema não seja o modelo em si, mas **como o alvo é apresentado** a ele —
talvez a informação sazonal (a época do ano) chegue "desalinhada", e reformular matematicamente o alvo
ajude o modelo a capturá-la melhor.

**As seis variantes, pré-declaradas, testadas sobre o HistGradientBoosting com folha mínima 20 e
vetor, com correção de Holm por família (25/09/2026):**

1. **`V1_alvo_log`** — o modelo aprende a prever o **logaritmo** do número de casos (mais 1, para
   evitar logaritmo de zero), em vez do número bruto. Erro, nos 4 horizontes: **174,4 · 205,8 · 251,0
   · 267,9**. Em `h=12`, o erro **piora 9,90%** frente ao controle (o próprio HistGB folha 20 sem essa
   transformação, que erra 243,8) e **piora 23,01%** frente à régua sazonal (217,8). São dois
   comparadores diferentes: contra o controle a perda é de 9,90%; contra a régua, de 23,01%.
2. **Semana-alvo do ano anterior como atributo de entrada** — em vez de só usar o valor absoluto,
   adiciona explicitamente "quantos casos houve nesta mesma semana, no ano anterior" como uma coluna
   extra de entrada. Resultado: **piora** o erro em `h=12`, de 243,8 para **300,9** — o oposto do que
   a hipótese previa.
3. **`V3` — resíduo sobre o ano anterior** — o modelo aprende a prever a **diferença** entre o valor
   de hoje e o mesmo período do ano passado, em vez do valor absoluto. **Explode**: em uma semana cujo
   máximo histórico do treino era 879 casos, esta formulação previu **10.524**. A causa é **extrapolação
   para fora da faixa treinada**: a âncora usada valia **1.109** casos (semana de 23/03/2025), ou seja,
   **acima** do maior valor visto no treino (879), e a diferença aprendida multiplicou esse valor já
   extrapolado por um crescimento de 9,5 vezes. Não é "estar perto do teto"; é estar fora dele.
4. **`V5` — regressão quantílica linear sobre o logaritmo** — troca o algoritmo de árvores por um
   modelo linear simples, ainda com perda quantílica, sobre o logaritmo do alvo. **Explode ainda
   mais**: previu **27.258** casos numa semana em que o real foi **1.855**. A causa é a colinearidade
   entre os múltiplos lags de casos usados como entrada — um modelo linear sem penalização adequada
   amplifica esse tipo de correlação em vez de neutralizá-la.
5. **A taxa de crescimento do vetor como atributo** (em vez da densidade absoluta) — piora a previsão
   em **0,7%** em `h=12`: os lags absolutos já usados já carregam essencialmente a mesma informação.
6. **Mistura 50/50 entre a previsão do modelo e a régua sazonal** — a única direção que se mostrou
   consistentemente positiva nos 4 anos avaliados: ganho médio de **+5,5%**, mas **sem significância
   estatística** (rotulado exploratório).

**Veredito: nenhuma das seis bate a régua sazonal em `h=12`, e nenhuma passa no critério
pré-declarado.** Refutada como conjunto. A mistura 50/50 fica registrada como candidata exploratória
para rodada futura.

### 5.4.9 Modelos de fundação (Chronos-Bolt e Chronos-2)

**O que é um modelo de fundação, em uma frase.** Um modelo de aprendizado profundo treinado
previamente em milhões de séries temporais de domínios variados (vendas, tráfego, energia, clima),
capaz de fazer previsões em uma série nova **sem ser retreinado especificamente** nela (a técnica
chamada *zero-shot*, "sem exemplo prévio" naquele domínio específico).

**A hipótese.** Se o limite do projeto for a **quantidade** de dado disponível (poucas temporadas de
dengue em Porto Alegre), um modelo que já viu padrões parecidos em outras séries do mundo poderia
generalizar melhor do que um modelo treinado do zero com poucos anos de dado local.

**Como foi testado (25/09/2026).** Chronos-Bolt e Chronos-2, sem qualquer treino nos dados do
projeto, usando como contexto de entrada tudo disponível até a data de origem de cada previsão, com
protocolo pré-declarado.

**O que deu.**

- **Nenhum bate a régua sazonal nem melhora o cenário base (B0) em `h=12`, pelo critério
  pré-declarado (MAE).** O melhor, Chronos-2 usando só a série de casos (sem clima nem vetor), erra
  **227,2**, contra **217,8** da régua sazonal — uma diferença pequena, na direção errada.
- ⚠️ **Exploratório: o vetor melhora o Chronos-2 quando combinado com clima**, em `h=4`, `h=8` e
  `h=12`, com p de Holm ≤ 0,007 — um resultado estatisticamente forte, à primeira vista. Mas o mesmo
  padrão já visto na folha mínima 20 (§5.4.4) se repete aqui: o vetor **atrapalha em 2022-2023** e
  **ajuda em 2024-2025** — o ganho depende de qual período domina a média, não é uniforme no tempo.
- A mediana do Chronos-2 (sem vetor) bate as duas regras simples em `h=1` e `h=4`, numa leitura
  descritiva pós-hoc (não confirmatória): erro de **67,0** e **136,7**.

**Veredito: refutada como caminho para bater a régua em 3 meses.** Confirma, por um caminho
independente (arquitetura de rede neural pré-treinada, em vez de árvores de decisão), a mesma conclusão
de §5.4.7: o limite em 3 meses parece ser do **dado disponível**, não do algoritmo escolhido.

### 5.4.10 A busca de hiperparâmetros (25/09/2026)

**O que é uma busca de hiperparâmetros, em uma frase.** Em vez de escolher manualmente os
hiperparâmetros de um algoritmo (§5.1: ajustes que não são aprendidos dos dados), sorteia-se um grande
número de combinações e testa-se cada uma, na esperança de encontrar uma combinação melhor do que a
escolhida manualmente.

**A hipótese.** A configuração adotada (HistGradientBoosting, `max_iter=250`, taxa de aprendizado
0,05, 15 folhas máximas por árvore, folha mínima de 5 semanas) foi escolhida por um grid relativamente
pequeno (120 execuções, cobrindo combinações discretas). Uma busca mais ampla e aleatória poderia
encontrar algo melhor.

**Como foi testado.** **120 configurações** sorteadas aleatoriamente — 60 de HistGradientBoosting e 60
de LightGBM —, com semente aleatória fixa **20260925** (um número usado para tornar o sorteio
reprodutível: rodar o mesmo código com a mesma semente sempre sorteia as mesmas 120 combinações),
escolhidas usando **só o período de 2022 a 2025** (nunca 2026, que já estava excluído nesta fase).

**O que deu.**

- 🚫 **Nenhuma das 120 passa no critério pré-declarado.** O menor p de Holm encontrado foi **0,17** —
  ainda acima do limiar de 0,05.
- A configuração vencedora dentro do LightGBM usa: taxa de aprendizado **0,022**, **177 árvores**, 49
  folhas por árvore, folha mínima de 10 semanas, usando 92% das colunas disponíveis e 81% das
  semanas de treino em cada árvore (uma técnica chamada *subsampling*, que injeta aleatoriedade
  controlada para reduzir sobreajuste), com a variante `extra_trees` (que sorteia os pontos de corte
  das árvores em vez de otimizá-los, trocando um pouco de precisão por mais estabilidade). Nota do
  critério de seleção: **160,95**.
- A vencedora dentro do HistGradientBoosting usa: taxa **0,197**, 239 iterações, 55 folhas, folha
  mínima de 15 semanas, 51% das colunas, profundidade máxima de árvore de 8 níveis. Nota: **161,74**.
- Testando a vencedora do LightGBM na janela 2024-2025, em `h=12`: erro de **239,6**, contra **226,8**
  da régua sazonal (nesta mesma janela) — ainda perde. Para comparação, o cenário adotado erra
  **293,3** e a variante de folha 20 erra **254,1** na mesma janela.
- ⚠️ **Um resultado à parte, fora do critério oficial:** a variante `linear_tree` (uma opção do
  LightGBM em que cada folha da árvore ajusta uma reta, em vez de prever um valor constante) teve erro
  muito menor (**201,6** em `h=12`, medido em 2026) — mas disparou o alarme de surto em **16 de 16**
  semanas testadas, ou seja, alarme sempre ligado, o que na prática o torna inútil como sistema de
  aviso (um alarme que sempre soa não distingue nada).
- 🚫 **Restrição monotônica testada e impossível de aplicar.** Uma "restrição monotônica" força o
  modelo a nunca diminuir a previsão quando uma variável de entrada aumenta (por exemplo, garantir que
  mais mosquitos nunca reduza a previsão de casos). O LightGBM na versão 4.6 usada pelo projeto
  **recusa** essa restrição quando combinada com perda quantílica — uma limitação da biblioteca, não
  do método.

**Advertência que acompanha todo este teste.** ⚠️ A busca rodou sobre uma tabela de dados que **ainda
incluía 2026**, posteriormente excluído da avaliação oficial (§5.5). Os números acima devem ser
citados com essa ressalva, e uma repetição na tabela restaurada (sem 2026) é pendência aberta.

**Veredito: refutada como caminho de melhoria — a busca ampla não supera a configuração manual.**

### 5.4.11 As transformações de escala (raiz quadrada e logaritmo)

**A hipótese, pré-declarada.** A distribuição do número de casos por semana é assimétrica: a maioria
das semanas tem poucos casos, e um pico eleva a escala inteira (61% das semanas têm 5 casos ou menos —
§1.3 do histórico de testes). Transformar o alvo para uma escala que comprima essa assimetria (raiz
quadrada, ou logaritmo) poderia melhorar a **calibração** dos intervalos de confiança — isto é,
aproximar a cobertura real da cobertura nominal declarada (por exemplo, um IC de 90% realmente conter
o valor real em 90% das semanas).

**Como foi testado.** Três braços comparados: sem transformação (o cenário adotado), com raiz
quadrada, e com logaritmo — todos pré-declarados e submetidos a certificação adversarial, que
**aprovou** a execução (26/09/2026).

**O que deu — o oposto do esperado.**

| Braço | Cobertura do IC 90% acima de 421 casos | Cobertura do IC 50% | Erro absoluto médio em h=12 |
|---|---|---|---|
| Sem transformação | 17,8% | 8,0% | 278,8 |
| Raiz quadrada | **15,9%** | 6,7% | 289,2 |
| Logaritmo | **13,5%** | 3,7% | 299,0 |

A cobertura **piorou** em todas as faixas com as transformações — inclusive na faixa de calmaria, onde
a cobertura do IC de 90% caiu de 90,5% (sem transformação) para 84,2% (raiz) e 80,5% (log). O erro
absoluto médio também piorou em quase todos os horizontes (por exemplo, em `h=1`: 98,0 → 103,2 com
raiz, um aumento de 5,3%; → 114,5 com log, aumento de 16,8%) — a única exceção parcial é `h=4`, onde a
raiz quadrada reduziu o erro em 6,7% (219,7 → 205,0).

**Por que o resultado é o oposto do esperado — a causa é viés, não variância.** O documento
`PENDENCIAS.md` (26/09/2026) identifica a causa: o erro nas semanas de mais de 421 casos é
**sistemático** (viés), não aleatório (variância). O erro mediano nessa faixa é de **539 casos** sobre
um real mediano de **917**, enquanto a **faixa** de previsão (a largura do intervalo) já cresce **70
vezes** entre a faixa de calmaria e a de Alerta ou mais, contra um crescimento do **erro** de **415
vezes** no mesmo intervalo — a faixa não consegue crescer na mesma proporção do erro. Uma
transformação de escala redistribui a variância, mas **não corrige viés sistemático**: é como tentar
consertar uma trena que sempre mede curto demais apertando ou afrouxando sua fita — o defeito está na
marcação, não na tensão.

**Um efeito colateral positivo, sem compensar o resto.** As transformações eliminam o "cruzamento de
quantis" (quando o quantil mais alto previsto acidentalmente fica **abaixo** do quantil mais baixo,
uma inconsistência lógica): de 77,5% das origens antes, para **zero** depois — porque a transformação
por raiz ou log é **monotônica** (preserva a ordem dos valores), o que garante matematicamente que a
ordem dos quantis também se preserve. Mas isso não compensa a piora de cobertura e de erro.

**Veredito: refutada.** Transformar a escala do alvo não resolve o problema de calibração, porque o
problema é viés sistemático de subestimação de pico, não assimetria de variância.

### 5.4.12 O alarme no estágio Alerta (mais de 421 casos por semana)

**Contexto: de onde vem o número 421.** O Plano Municipal de Contingência de Arboviroses 2026, da
Secretaria Municipal de Saúde de Porto Alegre, define quatro estágios de resposta, cada um por um
critério numérico **combinado** — nunca o corte numérico sozinho — com o Limite de Alerta ou o Limite
Superior Endêmico (medidas calculadas sobre a série de casos **prováveis** do Rio Grande do Sul
inteiro, não só de Porto Alegre). Usando a população de Porto Alegre declarada no plano
(**1.404.269** habitantes) e os cortes de incidência do plano (10, 30 e 50 casos confirmados por
100 mil habitantes), os limiares em número absoluto de casos por semana são: Normalidade abaixo de
**140**; Mobilização acima de **140**; Alerta acima de **421**; Epidemia acima de **702**.

**A hipótese, pré-declarada em 26/09/2026.** Se o modelo funciona como alarme para o limiar de 100
casos (§5.4.7), deveria também funcionar — talvez melhor, por ser um evento mais raro e mais decisivo
operacionalmente — para o limiar oficial de Alerta (421 casos).

**Como foi testado.** McNemar, mesma lógica de §5.2.6 e §5.4.7, agora com o evento "mais de 421 casos
confirmados por semana", dentro de uma família de **24 testes** (os 16 já existentes de 25/09/2026,
mais 8 novos), com correção de Holm sobre a família inteira.

**O número que decidiu.** **0 de 4** combinações relevantes vencem a régua "a mesma semana do ano
passado" com significância (p de Holm abaixo de 0,05). O modelo **vence** a regra mais fraca ("hoje já
passou de 421") em `h=12`, com folga: **p de Holm = 0,00014** para o cenário adotado, e **p = 0,00008**
para a variante de folha mínima 20.

**Veredito: refutada contra a régua forte; confirmada contra a régua fraca.** O mesmo padrão de §5.4.7
se repete no estágio Alerta: o modelo bate uma regra ingênua com facilidade, mas não bate a régua
sazonal, que já incorpora a informação de que a dengue tem estação.

---

## 5.5 Hipóteses abandonadas — decisão explícita de não seguir, com data e responsável

Estas não são hipóteses **refutadas por teste** — são hipóteses cuja continuação foi **decidida
contra** por quem tem autoridade sobre o escopo do projeto (o Vinicius, mestrando responsável), antes
mesmo de um teste completo, geralmente por inviabilidade prática ou por conflito com uma decisão de
escopo já tomada.

- 🚫 **Vírus no mosquito como atributo de entrada** — descartado pelo Vinicius em **25/09/2026**.
  Exigiria solicitar um dado novo à Prefeitura de Porto Alegre (qual sorotipo específico do vírus da
  dengue, **DENV**, foi encontrado em cada armadilha), o que o projeto já decidiu, por norma
  permanente, **não fazer** (ver PENDENCIAS: "não contar com dado novo da Prefeitura"). Existem 242
  detecções do vírus registradas entre 2022 e 2025 (sendo 237 do sorotipo DENV-1), com a primeira
  detecção do ano ocorrendo mais cedo justamente nos anos de epidemia maior — mas o zero de detecções
  em 2026 é, ele mesmo, um limite da raspagem de dados (o processo manual de coleta semanal do
  portal), não uma medida real da ausência do vírus.

- 🚫 **Notificações (em vez de casos confirmados) como alvo, ou como variável de entrada** —
  descartado em **25/09/2026**. Testado dentro da bateria de formulações do alvo (§5.4.8): piora a
  previsão em três meses. A decisão de abandonar soma-se à decisão anterior, de 30/08/2026, de que
  **confirmados** é o alvo correto (§5.4.1).

- 🚫 **Avaliar o modelo com os dados de 2026** — descartado pelo Vinicius em **26/09/2026**. A
  justificativa registrada, nas palavras do próprio Vinicius, é que "com séries crescentes é
  impossível prever um ano de 19 casos" — 2026 teve o índice de mosquitos em nível crítico e apenas
  19 casos confirmados até a data de corte, um regime tão fora do padrão histórico que qualquer
  veredito baseado nele seria pouco informativo sobre o desempenho esperado em anos comuns. A tabela
  de dados oficial do projeto **voltou a excluir 2026**, e a avaliação segue indo até
  aproximadamente **01/02/2026**. Os testes que já haviam rodado sobre a tabela com 2026 incluído
  (a busca de hiperparâmetros, §5.4.10, e a segunda bateria noturna) ficam registrados **só como
  memória histórica**, com a ressalva explícita de que precisam ser refeitos na tabela restaurada
  antes de qualquer citação em texto final.

- 🚫 **Canal endêmico e Modelo de Envelope Móvel (MEM) para Porto Alegre, calculados com histórico
  próprio** — descartado em **26/09/2026**, depois de uma premissa central se revelar incorreta: o
  projeto havia assumido que o método usado por Porto Rico para calcular seu limiar epidêmico
  (percentil 75 de uma regressão binomial negativa) poderia ser replicado com o histórico de Porto
  Alegre. A leitura completa do artigo original (MMWR, "Dengue Outbreak and Response — Puerto Rico,
  2024", lido em 26/09/2026) mostrou que Porto Rico ajusta esse modelo sobre **86.282 casos ao longo
  de cerca de 38,5 anos** de vigilância contínua (desde 1986), **sem excluir os anos de epidemia** da
  série usada para calibrar o limiar — uma extensão de histórico que Porto Alegre não tem (o dado de
  casos confirmados do projeto começa efetivamente em fevereiro de 2018, cerca de 8 anos). Sem esse
  histórico longo e com anos calmos suficientes, o canal endêmico calculado localmente produz um
  limite de **zero** em muitas semanas fora da temporada (por exemplo, a semana epidemiológica 39 de
  2024, com 7 casos reais, teve limite calculado de zero) — um defeito estrutural, não um erro de
  implementação. Em vez disso, o projeto passou a usar os limiares **oficiais do plano municipal**
  (140, 421, 702 casos) como referência, e registrou como achado alternativo a regra de
  "aceleração de transmissão" (razão entre a média móvel de 4 semanas e a de 26 semanas, com alarme
  acima de 1,33), que não depende de histórico longo — mas com a ressalva de que essa regra, importada
  de um estudo com 8 países, teve desempenho pior em Porto Alegre (índice de Youden −0,05 usando o
  corte da Malásia) do que em sua validação original, um lembrete de que uma regra de alarme
  desenvolvida para outro contexto **pode não transferir** diretamente.

- 🚫 **Casos de dengue por bairro como unidade espacial** — descartado no início do projeto
  (29/08/2026, reafirmado em decisões posteriores) por depender de dado que exigiria aprovação de um
  Comitê de Ética em Pesquisa, fora do alcance de prazo do mestrado. Consequência: a análise espacial
  do projeto (§4 do histórico de testes) usa **zonas sintéticas**, agrupamentos geográficos de
  armadilhas por k-means, não a divisão administrativa oficial de bairros.

---

## 5.6 O que nunca foi testado, e por que

Estas são lacunas explícitas de escopo — não erros, e não necessariamente prioridades perdidas, mas
caminhos que o projeto conscientemente não percorreu, por razões de tempo, de dado disponível ou de
adequação ao problema.

- 🔬 **Teoria de valores extremos** (em inglês *extreme value theory*; a distribuição usada nessa
  teoria para o valor máximo de um conjunto de observações se chama distribuição **generalizada de
  valores extremos**, abreviada **GEV**). É um ramo da estatística dedicado especificamente a modelar
  a **cauda** de uma distribuição — os eventos raros e extremos — em vez da distribuição inteira. Como
  o defeito mais persistente e mais custoso do modelo é justamente a subestimação sistemática dos
  picos de epidemia (§5.2.1, §5.4.11), uma abordagem desenhada especificamente para modelar caudas
  poderia, em princípio, tratar esse defeito de um jeito mais direto do que ajustar o quantil de um
  modelo de árvores de decisão. **Por que não foi testada:** exigiria uma reformulação metodológica
  inteira (não é um hiperparâmetro a mais no HistGradientBoosting, é uma família de modelo diferente),
  e o tempo disponível até o momento priorizou entender e corrigir o vazamento temporal (§6.1) e
  varrer alternativas mais diretas (formulações do alvo, transformação de escala, modelos de
  fundação) — todas já refutadas ou inconclusivas (§5.4.8, §5.4.9, §5.4.11).

- 🔬 **Modelos mecanicistas do tipo compartimental** (por exemplo, da família **SIR** —
  Suscetível-Infectado-Recuperado — ou suas variantes específicas para doenças transmitidas por
  vetor, com compartimentos adicionais para a população de mosquitos e o período de incubação do
  vírus). Diferente dos modelos de aprendizado de máquina usados neste projeto, que aprendem padrões
  estatísticos diretamente dos dados sem impor uma estrutura biológica, um modelo compartimental
  **impõe** equações que representam explicitamente como a doença se espalha de pessoa a pessoa e de
  mosquito a pessoa, com parâmetros que têm significado epidemiológico direto (taxa de transmissão,
  período infeccioso). **Por que não foi testado:** exige estimar parâmetros biológicos (taxa de
  picada, taxa de transmissão vetorial, período de incubação extrínseca) que este projeto não tem
  medidos localmente, e caiu fora do escopo de uma dissertação centrada em avaliação de valor
  preditivo de uma fonte de dado (a rede de armadilhas), não em construção de um modelo epidemiológico
  mecanicista novo.

- 🔬 **Transferência de aprendizado (em inglês *transfer learning*) a partir de outras cidades.**
  Consiste em treinar (ou pré-treinar) um modelo com dados de dengue de outras cidades — por exemplo,
  outras capitais brasileiras ou cidades com clima e regime de dengue parecidos — e depois ajustá-lo
  com o pouco dado de Porto Alegre, na esperança de que padrões aprendidos alhures se transfiram.
  **Por que não foi testado:** o caminho mais próximo disso que o projeto tentou foi o uso de modelos
  de fundação pré-treinados em séries temporais de domínios genéricos, não especificamente em outras
  séries de dengue (§5.4.9) — e mesmo esse caminho não bateu a régua sazonal. Uma transferência
  específica de dengue-para-dengue exigiria localizar, limpar e harmonizar dados de vigilância de
  outras cidades (frequências de notificação diferentes, definições de caso diferentes, coberturas de
  armadilha ausentes na maioria delas), um trabalho de preparação de dados que não coube no tempo do
  projeto até 26/09/2026.

- 🔬 **Modelos hierárquicos bayesianos.** Uma classe de modelos estatísticos que permite compartilhar
  informação entre unidades relacionadas (por exemplo, entre zonas da cidade, ou entre anos), estimando
  ao mesmo tempo um padrão "geral" e desvios específicos de cada unidade, com incerteza propagada
  formalmente por meio de distribuições de probabilidade (em vez de intervalos calculados
  empiricamente a partir de quantis, como o cenário adotado faz). Este tipo de modelo é particularmente
  adequado quando há **poucos dados por unidade** — exatamente a situação das zonas espaciais deste
  projeto (§4 do histórico de testes) e dos poucos anos de série de casos disponíveis. **Por que não
  foi testado:** exige uma escolha de estrutura de distribuições a priori (as suposições estatísticas
  de partida do modelo) e ferramental de amostragem (por exemplo, Monte Carlo via Cadeias de Markov)
  que está fora do ferramental usado até aqui pelo projeto, centrado em bibliotecas de aprendizado de
  máquina supervisionado (`scikit-learn`, `LightGBM`). É um candidato natural para uma extensão futura,
  especialmente para a camada espacial (§4), onde a regra simples de persistência já venceu o
  aprendizado de máquina (§5.3, tabela mestra) — um cenário em que compartilhar informação entre zonas
  de forma hierárquica poderia, em princípio, superar tanto a regra simples quanto o modelo atual.

---

# Parte 6 — A literatura e a comparação com o nosso resultado

## 6.1 Por que comparar com a literatura é difícil

Antes de qualquer tabela com números lado a lado, é preciso entender por que esse tipo de tabela engana
com facilidade. A comparação entre o nosso resultado e o de outro estudo publicado não é uma comparação
de **ranking** — não é como comparar dois corredores na mesma pista, com a mesma distância, correndo ao
mesmo tempo. É uma comparação de **contexto**: cada estudo correu uma pista diferente, com uma distância
diferente, em condições diferentes, e o cronômetro de cada um mede uma coisa ligeiramente distinta.

Quatro eixos tornam a maioria das comparações diretas impossíveis sem qualificação:

- **O alvo (o que está sendo previsto) muda de estudo para estudo.** Alguns preveem o número absoluto de
  casos numa cidade (é o que este projeto faz). Outros preveem a **incidência**, que é o número de casos
  dividido pela população e multiplicado por um fator fixo — em geral **100 mil habitantes** — para poder
  comparar lugares de tamanhos diferentes. Outros ainda preveem o **logaritmo** da incidência, isto é,
  aplicam a função matemática $\log(x+1)$ sobre o valor de incidência antes de rodar o modelo. Essa
  transformação comprime a escala: a diferença entre 10 e 100 casos deixa de ser "90 casos a mais" e passa
  a ser "log(101) − log(11) ≈ 2,22", um número muito menor e muito menos sensível a picos extremos. Um erro
  de previsão medido em casos absolutos e um erro medido em log de incidência **não são o mesmo tipo de
  número**, e transformar um no outro exige reconstruir o cálculo do zero, coisa que este documento evita
  fazer sem necessidade, por regra do projeto (nunca converter escala ou unidade só para viabilizar uma
  comparação).
- **O período de dados e o número de temporadas variam por uma ordem de grandeza.** Singapura tem série
  contínua desde 2001 (mais de duas décadas até os artigos mais recentes); o sistema do Vietnã (D-MOSS,
  detalhado na seção 6.4) usa dados desde agosto de 2002; Porto Rico, desde 1986. Porto Alegre, na série
  usada neste projeto, tem **4 temporadas de epidemia utilizáveis** (2022 a 2025) — um décimo do que os
  estudos mais maduros usam. Quanto menos temporadas, menos o modelo (e a régua de comparação) têm o que
  aprender sobre o que é "normal" e o que é "surto".
- **A população e a escala de casos mudam a leitura de qualquer erro relativo.** Singapura chegou a
  **842 casos numa única semana** no surto de 2013. Porto Alegre, na série usada aqui, tem semanas com
  **zero casos confirmados** fora da temporada. Um erro absoluto de 50 casos é pequeno diante de 842 e é
  enorme diante de zero ou de poucas dezenas — por isso um erro percentual (que divide o erro pelo valor
  real) explode matematicamente quando o valor real é pequeno, mesmo que o modelo tenha acertado bem em
  termos absolutos.
- **A forma de validar o modelo muda o que o número final significa.** A seção 6.3 detalha o caso mais
  importante disto no nosso contexto: um modelo validado por **validação cruzada em partes embaralhadas
  no tempo** (explicada logo abaixo) tende a produzir um erro medido menor do que um modelo validado por
  **validação em avanço** (do inglês *walk-forward*, o método deste projeto), porque o primeiro permite
  que o modelo "veja", durante o ajuste, um pedaço de informação que só existiria no futuro em relação ao
  que está sendo previsto.

Dois conceitos de validação, portanto, precisam estar definidos antes de qualquer tabela:

- **Validação em avanço (*walk-forward*):** o método usado neste projeto. Para prever a semana X, o
  modelo só pode ser treinado com dados de semanas anteriores à **data em que o resultado da semana X já
  seria conhecido**. Nunca se usa, no treino de uma previsão, um dado que só existiria depois. A regra
  exata (cortar pela data da **resposta**, não da **pergunta**) vive no código do projeto, em
  `modelagem_aedes/motor/corte_temporal.py`, e seu efeito prático foi medido em 13/09/2026 (detalhe na
  seção 6.6).
- **Validação cruzada em partes embaralhadas no tempo (*k-fold cross-validation*):** um método diferente,
  comum em estudos que não têm como objetivo central fazer previsão prospectiva operacional. Os dados são
  divididos em, por exemplo, **10 partes (*folds*)** de tamanho parecido, sorteadas **sem respeitar a
  ordem cronológica**. O modelo treina em 9 partes e testa na parte restante, repetindo o processo 10
  vezes até que cada parte tenha servido de teste uma vez. O problema, para uma série temporal, é que uma
  das 9 partes de treino pode conter semanas **posteriores** à semana que está sendo testada — o modelo
  aprende com o futuro para prever o passado. Isso não é um erro de quem projetou o método: é adequado
  quando o objetivo é entender **associação** entre variáveis (por exemplo, "será que a infestação do
  mosquito se relaciona com os casos de dengue, olhando todos os dados de uma vez?"), mas não mede
  **capacidade de previsão prospectiva**, que é uma pergunta diferente. A seção 6.3 mostra o caso concreto
  deste problema no estudo mais próximo do nosso.

Com essas definições em mãos, as seções seguintes tratam cada estudo em detalhe, sempre indicando, ao
final, se a comparação numérica é ou não segura.

---

## 6.2 Singapura, em detalhe — o teto do que é possível com série longa

### 6.2.1 ⚠️ Uma divergência a registrar antes de prosseguir

O material de referência fornecido para compor esta seção cita como fonte principal de Singapura
"**Chen et al. 2020, PMC7318238**". Essa referência **não foi localizada** em nenhuma das pastas de
análise lidas para escrever esta seção (`analises/2026-09-25_varredura_literatura/`,
`analises/2026-09-25_comparacao_direta_literatura/`), nem em nenhuma outra pasta datada do projeto
consultada. Não sendo possível verificar o conteúdo dessa citação, ela **não é usada como fonte de
números** neste documento — apenas registrada aqui como uma pendência de verificação.

Em lugar dela, esta seção usa dois estudos sobre Singapura que **foram lidos e verificados
adversarialmente** por um segundo agente contra a fonte primária (PMC/EHP), com status **CONFIRMADO**:

- **Shi et al. 2016**, *Environmental Health Perspectives* (EHP), DOI `10.1289/ehp.1509981` (PMC5010413).
- **Finch, Chang, Kucharski, Sim, Ng & Lowe, 2025**, *Nature Communications* 16, DOI
  `10.1038/s41467-025-66411-6`.

### 6.2.2 Shi et al. 2016 — o sistema que virou política pública

**O que é.** Um modelo de regressão chamado **LASSO** — sigla em inglês para *Least Absolute Shrinkage
and Selection Operator*, uma técnica de regressão linear que, além de ajustar uma reta (ou hiperplano) aos
dados, **penaliza** o uso de variáveis de entrada pouco úteis, empurrando o coeficiente delas para exatamente
zero. Na prática, isso funciona como uma seleção automática de quais variáveis climáticas e epidemiológicas
realmente ajudam a prever, descartando as que só adicionam ruído.

**A série usada.** Dados semanais de Singapura, de **2001 a 2013**, ou seja, **13 anos contínuos**. O
modelo foi:

- **treinado** com os dados de 2001 a 2010 (10 anos);
- **ajustado** (escolha de hiperparâmetros — valores de configuração do modelo que não são aprendidos
  automaticamente pelos dados, mas escolhidos por quem constrói o modelo, como a intensidade da
  penalização do LASSO) usando 2011 e 2012;
- **testado**, de fato, só em **2013**, um ano inteiro que o modelo nunca tinha visto em nenhuma etapa
  anterior.

Esse desenho é uma validação fora da amostra genuína e prospectiva, no mesmo espírito da validação em
avanço deste projeto, embora com um único corte fixo (treino → ajuste → teste), e não um corte que avança
semana a semana como o nosso.

**A escala do problema.** Singapura é um país-cidade de cerca de 5,5 milhões de habitantes. O surto de
2013 — o ano de teste — somou **22.170 casos no ano**, com um pico de **cerca de 842 casos numa única
semana** (semana epidemiológica 25). Compare: a maior semana da série de Porto Alegre usada neste projeto
teve **2.381 casos** (seção 6.6), então, em termos absolutos, Porto Alegre chega a ter picos semanais
maiores — mas Singapura tinha **13 anos de histórico**, incluindo vários anos sem epidemia grande, para
calibrar o que era "normal".

**A métrica: erro percentual absoluto médio (MAPE).**

O MAPE — em inglês *Mean Absolute Percentage Error* — mede o erro do modelo como uma fração do valor
real, e não em unidades absolutas. A fórmula, para uma janela de previsão $w$ (por exemplo, "uma semana à
frente" ou "doze semanas à frente"):

```
MAPE(w) = (1/|V|) × Σ_{t ∈ V} |y_t − ŷ_t(w)| / y_t
```

Onde:

- **$V$** é o conjunto de semanas usadas para validar aquela janela $w$ (o conjunto de teste);
- **$|V|$** é o número de semanas nesse conjunto;
- **$y_t$** é o número real de casos na semana $t$;
- **$ŷ_t(w)$** é o número previsto pelo modelo para a semana $t$, feita com $w$ semanas de antecedência;
- **$Σ$** (a letra grega sigma maiúscula) é o símbolo de somatório: soma o termo que vem depois dela para
  cada semana $t$ do conjunto $V$.

**Exemplo numérico, com números do próprio artigo.** Suponha uma semana de teste em que Singapura teve
**$y_t = 500$ casos reais**, e o modelo LASSO previu **$ŷ_t = 415$ casos**. O erro percentual absoluto
dessa única semana seria:

```
|500 − 415| / 500 = 85/500 = 0,17 → 17%
```

Esse número — **17% de erro médio em previsões de 1 semana** — é exatamente o valor relatado no artigo
para o horizonte mais curto (intervalo de confiança de 95%: 16% a 19%). No horizonte de **12 semanas (3
meses)**, o MAPE do LASSO sobe para **24%** (IC95%: 22% a 26%).

**A régua de comparação: SARIMA.** SARIMA é a sigla, em inglês, para *Seasonal Autoregressive Integrated
Moving Average* — um modelo estatístico clássico de série temporal que prevê o futuro olhando para a
autocorrelação da própria série (o valor de hoje explicado pelos valores de semanas anteriores) e para um
padrão sazonal repetido a cada ano, sem usar nenhuma variável externa (como clima). No artigo de Shi et
al., o SARIMA teve MAPE de **29%** (IC95%: 26% a 32%) em 12 semanas — o LASSO venceu essa régua em quase
todas as janelas de previsão testadas, com a única exceção sendo a janela de 2 semanas.

**Uso operacional, não só pesquisa.** O artigo declara, em citação literal traduzida: *"a ferramenta de
previsão aqui descrita tornou-se parte integral do programa de controle de dengue de Singapura"*. As
previsões eram enviadas ao Ministério da Saúde e ao departamento de operações de saúde ambiental de
Singapura, e ajudaram a **gerir leitos hospitalares** e a **priorizar ações preventivas de controle de
foco (eliminação de criadouros)** durante o próprio surto de 2013.

**Por que eles conseguem o que nós não conseguimos.** Três razões, todas mensuráveis:

1. **Volume de dados histórico:** 10 anos de treino contra os cerca de 4 anos úteis de Porto Alegre — mais
   que o dobro de temporadas para o modelo aprender o padrão sazonal e para o LASSO escolher bem quais
   variáveis manter.
2. **Escala de casos:** picos de centenas de casos por semana tornam o erro percentual naturalmente menor,
   porque o denominador da fração ($y_t$) raramente é pequeno. Em Porto Alegre, semanas de baixa
   temporada com poucos casos (às vezes 1 ou 2) fazem o mesmo tipo de métrica percentual explodir mesmo
   quando o erro absoluto é pequeno.
3. **Maturidade da epidemia:** Singapura tem dengue endêmica havia décadas quando o artigo foi escrito —
   ou seja, o comportamento da doença já é bem compreendido estatisticamente. Porto Alegre está, como a
   seção 6.7 detalha, na **fronteira de expansão** da doença, sem esse acúmulo de história.

### 6.2.3 Finch et al. 2025 — clima e sorotipo, série de 23 anos

**O que é.** Um modelo que usa variação climática e **competição de sorotipo** (a dengue tem quatro
sorotipos — variações genéticas do vírus — e a proporção de cada um circulando muda com o tempo, afetando
quantas pessoas ainda são suscetíveis a cada um) para prever surtos em Singapura.

**A série usada.** **23 anos de dados**, de 2000 a 2022 — quase **seis vezes** as 4 temporadas utilizáveis
de Porto Alegre.

**O horizonte.** Até **8 semanas (2 meses)** — mais curto que o horizonte de 12 semanas (3 meses) usado
neste projeto como o mais longo avaliado.

**A régua de comparação.** Um modelo que usa apenas **efeitos aleatórios semanais**: um termo estatístico
que captura a sazonalidade média de cada semana do calendário, sem nenhuma variável de clima ou de vetor —
o equivalente conceitual, embora não idêntico em implementação, da régua sazonal deste projeto ("quantos
casos houve na mesma semana do ano passado").

**A métrica: pontuação de habilidade probabilística (CRPSS).** O CRPSS (a definição de CRPS está na seção
6.4.5, sobre os *sprints* nacionais) é a versão relativa do CRPS: mostra o **quanto melhor** um modelo é
em relação a uma régua, em percentual. Um CRPSS de +54% significa que o erro probabilístico do modelo é
54% menor do que o da régua.

**O resultado.** Usando só clima: **CRPSS de +54%** sobre a régua sazonal. Usando clima **e** sorotipo:
**+60%**.

**Por que eles conseguem o que nós não conseguimos.** Além dos 23 anos de série (quase 6 vezes mais
temporadas que Porto Alegre), o horizonte testado é mais curto (8 semanas contra os 12 do projeto), e o
modelo tem acesso a uma variável — a proporção de cada sorotipo circulando — que exige vigilância
laboratorial contínua e específica, um tipo de dado que este projeto não tem disponível para Porto Alegre.

---

## 6.3 da Silva et al. 2026 — o estudo gêmeo, mesma cidade e mesma rede de armadilhas

### 6.3.1 Uma correção de classificação, feita em público

Esta subseção começa com uma correção, porque ela é ela mesma um exemplo do tipo de verificação que este
documento defende como padrão de honestidade metodológica (ver seção 6.1 e a Parte 0, §0.3).

Em **25/09/2026**, uma rodada de extração de literatura (pasta `analises/2026-09-25_comparacao_direta_literatura/`)
identificou este artigo como publicado na revista **PLOS Neglected Tropical Diseases** (PLOS NTD), sob o
DOI `10.1371/journal.pntd.0014201`, com resultados de **R² = 0,46** e **erro absoluto médio (MAE) = 0,79**,
medidos sobre o logaritmo da incidência de dengue. Uma segunda rodada de verificação adversarial, no mesmo
dia, tentou reproduzir esse achado buscando a fonte de novo e **confirmou** os mesmos números.

Em **26/09/2026**, uma ficha de leitura dedicada (pasta `analises/2026-09-26_ficha_da_silva_2026/`) leu o
**arquivo PDF completo, 41 páginas**, do artigo realmente salvo na pasta de referências do projeto
(`Artigos de referencia/Climate-driven spatiotemporal dynamics of Aedes infestation and dengue.pdf`). Esse
PDF traz, em **todas as 41 páginas**, o cabeçalho: *"medRxiv preprint... esta versão postada em 2 de abril
de 2026... (which was not certified by peer review)"* — ou seja, é um **preprint** (um manuscrito
disponibilizado publicamente **antes** de passar pela revisão por pares, o processo pelo qual outros
cientistas da mesma área avaliam criticamente um trabalho antes de ele ser aceito como publicação
científica) no repositório **medRxiv**, sob o DOI `10.64898/2026.03.31.26349860`, **sem revisão por
pares**. Não há, no arquivo lido, nenhuma menção a "R²=0,46" nem a "MAE=0,79" — os números medidos e
relatados nesse PDF são outros, detalhados abaixo.

**O que isso significa, com honestidade:** existem duas leituras internas deste projeto sobre o mesmo
artigo, com números diferentes e com uma diferença de classificação editorial (revista com revisão por
pares × preprint sem revisão). A leitura de 26/09/2026, feita diretamente no arquivo PDF completo salvo no
projeto, é tratada aqui como a versão correta, porque foi obtida por leitura direta da fonte primária, e
porque o registro de pendências do projeto (`PENDENCIAS.md`) já a marcou como ✅ resolvida em 26/09/2026,
substituindo a classificação anterior. Não foi possível determinar, dentro do escopo desta seção, se a
extração de 25/09/2026 capturou um artigo diferente por engano, se citou uma versão revisada que não está
salva no projeto, ou se produziu uma citação incorreta. Todos os números usados daqui em diante nesta
seção vêm da leitura direta de 26/09/2026.

### 6.3.2 Identificação

- **Título:** "Climate-driven spatiotemporal dynamics of *Aedes* infestation and dengue transmission in
  Porto Alegre, Southern Brazil".
- **Autores:** Adryan Aparecido da Silva (Faculdade de Farmácia, UFMG), Álvaro Gil Araujo Ferreira
  (Instituto René Rachou–Fiocruz Minas), José Lourenço (Universidade Católica Portuguesa) e Amanda
  Cupertino de Freitas (Instituto René Rachou–Fiocruz Minas **e Ecovec**, autora correspondente).
- **Data e status editorial:** postado no medRxiv em **02/04/2026**; é um **preprint**, **não revisado por
  pares** até a data de leitura (26/09/2026).
- **Vínculo institucional a registrar sem tom acusatório:** a autora correspondente tem afiliação
  declarada com a **Ecovec**, a empresa fabricante da armadilha MI-Aedes usada tanto neste projeto quanto
  no artigo. Isso é um fato relevante para o leitor avaliar de forma independente, e não motivo, por si
  só, para desqualificar os achados do estudo — a Ecovec é citada no artigo, junto com a Prefeitura de
  Porto Alegre e a empresa Rentokil, como fonte de dados e apoio, e o financiamento declarado é da
  Fapemig, sem menção a financiamento da Ecovec.

### 6.3.3 O que fizeram

O estudo usa **três alvos diferentes**, não um só:

1. **MFAI** — sigla em inglês para *Mean Female Aedes Index*, o índice médio de fêmeas do mosquito
   *Aedes* capturadas por armadilha por semana, calculado separadamente para as duas espécies monitoradas
   (*Aedes aegypti* e *Aedes albopictus*), **sem transformação logarítmica**.
2. **Índice de positividade para DENV** — a sigla DENV se refere ao vírus da dengue (*dengue virus*); o
   índice mede a **porcentagem de armadilhas** que testaram positivo para o vírus por uma técnica
   laboratorial chamada RT-PCR (reação em cadeia da polimerase com transcrição reversa, um método de
   detecção genética do vírus).
3. **Incidência de dengue**, transformada como $\log(\text{incidência por 100 mil habitantes} + 1)$,
   agregada **semanalmente para a cidade toda** (não por bairro), usada no modelo final de regressão.

**O período dos dados:** entomológico (relativo aos insetos) e climático, **de 2018 a 2025** (8 anos);
casos autóctones (contraídos localmente, não importados de viagem) de dengue de **2019 a 2025**, somando
**72.965 casos notificados**, dos quais 51% foram confirmados e, destes, 93% autóctones.

**O horizonte de previsão declarado no texto: não existe um horizonte formal como o deste projeto.** O
estudo trabalha com **defasagens (*lags*) de 0 a 4 semanas** em correlação estatística (ver 6.3.5) e numa
regressão — é uma associação contemporânea ou levemente defasada entre variáveis medidas no mesmo período
histórico, e **não** uma previsão testada fora da amostra em horizontes fixos como 1, 4, 8 ou 12 semanas à
frente, do jeito que este projeto testa.

**Os algoritmos usados**, listados individualmente:

- **Índice de Moran (Moran's I) e LISA** (*Local Indicators of Spatial Association*) — técnicas
  estatísticas de **autocorrelação espacial**: medem se um valor alto (por exemplo, muita infestação do
  mosquito) num bairro tende a aparecer perto de outros bairros também com valor alto, mais do que se
  fosse por acaso. Calculadas por bairro e por ano.
- **Correlação de Kendall (τ)** — detalhada com exemplo numérico na seção 6.3.5, por bairro e por semana,
  com defasagens de 0 a 4 semanas.
- **Regressão polinomial** (de 1ª a 4ª ordem, escolhida pelo critério estatístico AIC — *Akaike
  Information Criterion*, uma medida que penaliza modelos com mais parâmetros para evitar escolher um
  modelo que apenas decora os dados) para relacionar frequência de chuva à MFAI.
- **LASSO** (a mesma técnica descrita na seção 6.2.2), rodado três vezes — uma para cada um dos três
  alvos — e comparado, em cada caso, a uma **regressão linear simples (LM)**.

**As variáveis de entrada:** precipitação acumulada, temperatura média e umidade relativa (todas com
defasagens de 0 a 4 semanas); o **Index P**, um índice de adequação climática para a transmissão
vetor-vírus calculado pelo pacote de software MVSE; e o **VFII** (*Vector-Fitness Infestation Index*, um
índice próprio dos autores, calculado como MFAI multiplicado pelo Index P).

**A validação: validação cruzada de 10 partes (10-fold), não validação em avanço.** O LASSO foi ajustado
com **validação cruzada de 10 partes**, embaralhadas — o método definido na seção 6.1, que **não** corta
pela ordem cronológica. O próprio texto do artigo, ao descrever essa etapa, não menciona nenhum corte
temporal ou proteção contra vazamento de futuro para o passado.

**A unidade espacial** muda conforme a análise: o índice de Moran e a correlação de Kendall por bairro
usam cerca de **50 distritos/bairros** de Porto Alegre; já o modelo LASSO final de incidência de dengue
usa a **série semanal agregada para o município inteiro**.

### 6.3.4 Resultados relatados no PDF

- **MFAI, *Aedes aegypti*:** raiz do erro quadrático médio de **0,2866** para o modelo linear simples e
  **0,2864** para o LASSO; razão de deviance de **0,5225**.
  - A **raiz do erro quadrático médio** (em inglês *root mean squared error*, abreviado RMSE) é a raiz
    quadrada da média dos erros elevados ao quadrado: $\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}
    (y_i - \hat{y}_i)^2}$, em que $y_i$ é o valor real, $\hat{y}_i$ é o previsto e $n$ é o número de
    observações. Diferença em relação ao erro absoluto médio: elevar ao quadrado antes de somar faz com
    que **erros grandes pesem desproporcionalmente mais**. Um erro de 10 pesa cem vezes um erro de 1,
    enquanto no erro absoluto médio pesaria dez vezes.
    ⚠️ **Estes valores não são comparáveis aos nossos**, porque estão numa escala diferente: eles medem o
    erro sobre o índice de fêmeas por armadilha, um número que fica entre 0 e cerca de 1, e não sobre
    contagem de casos.
  - A "razão de deviance" (*deviance ratio*) é uma medida análoga ao R² (definido com exemplo na seção
    6.4.2), usada quando o modelo estatístico não é uma regressão linear comum, mas sim um modelo da
    família de regressões generalizadas (como o LASSO usado aqui). Ela também varia entre 0 e 1 (quanto
    mais perto de 1, melhor o modelo explica a variação dos dados), mas seu cálculo interno usa a
    "deviance" — uma medida de discrepância entre o modelo ajustado e o modelo perfeito — em vez da soma
    de quadrados dos resíduos usada no R² clássico.
- **MFAI, *Aedes albopictus*:** RMSE de 0,00977 (LM) e 0,00975 (LASSO); razão de deviance de **0,4933**.
- **Log(incidência de dengue + 1):** RMSE de **1,003** (LM) e **1,006** (LASSO); razão de deviance de
  **0,61**. Não há, em nenhum lugar do artigo, um valor de erro absoluto médio (MAE), de erro percentual
  (MAPE) ou de coeficiente de determinação (R²) clássico para este alvo — apenas RMSE em escala log e a
  razão de deviance.
- **Modelo só com clima (sem vetor), para o mesmo alvo de incidência:** predictive R² de **−0,07**;
  razão de deviance de **0,04** — um ajuste bem mais fraco do que o modelo com o vetor (MFAI) incluído.
- **Correlação de Kendall, clima × MFAI (temperatura), defasagem 0 a 4 semanas:** τ sobe de **0,419**
  (defasagem 0) a **0,581** (defasagem 4) para *Aedes aegypti*; a correlação com umidade é negativa, de
  −0,216 a −0,293; com precipitação, fraca e negativa, de −0,09 a −0,125.
- **Correlação de Kendall, MFAI defasado × casos autóctones (o número que interessa mais de perto ao
  projeto):** para *Aedes aegypti*, τ = **0,2737** na defasagem 0, subindo para **0,3376** (defasagem 1),
  **0,3911** (2), **0,4470** (3) e **0,4953** na defasagem 4 — todos com valor-p menor que 0,001 (o
  valor-p é definido com exemplo na seção **6.6.5**). Para *Aedes albopictus*, o padrão é semelhante, de
  0,1206 a 0,4479. **A tabela do artigo para exatamente na defasagem 4** — não há um ponto de defasagem 8
  medido neste estudo. Isso corrige um número que havia sido registrado anteriormente em `PENDENCIAS.md`
  ("τ 0,59 no lag 8"), que não existe no texto — a correção já foi feita no próprio `PENDENCIAS.md` em
  26/09/2026.
- **Índice de Moran anual:** pico em 2023 para ambas as espécies (*Aedes aegypti*: 0,6235; *Aedes
  albopictus*: 0,4377; ambos com p < 0,001).
- **Positividade das armadilhas para o vírus DENV:** subiu de 0,01% em 2018 para 0,98% em 2025.

### 6.3.5 O que é a correlação de Kendall (τ), com exemplo numérico

A correlação de Kendall, representada pela letra grega τ (tau), mede se duas variáveis tendem a **subir e
descer juntas**, sem assumir que a relação entre elas seja uma linha reta (diferente da correlação de
Pearson, mais comum, que assume linearidade). Ela é calculada contando **pares concordantes** e **pares
discordantes** entre todas as combinações possíveis de duas observações.

A fórmula, ignorando a possibilidade de empates (valores iguais):

```
τ = (C − D) / [n(n−1)/2]
```

Onde:

- **$C$** é o número de **pares concordantes**: pares de semanas em que, se uma variável é maior numa
  semana do que na outra, a segunda variável também é maior na mesma semana;
- **$D$** é o número de **pares discordantes**: pares em que uma variável é maior mas a outra é menor;
- **$n$** é o número total de observações (semanas), e $n(n-1)/2$ é o número total de pares possíveis
  entre elas.

**Exemplo numérico trabalhado, com números fictícios simples para ilustrar o mecanismo** (o artigo não
publica os pares brutos, só o τ final): suponha 4 semanas, com um índice de mosquito defasado (variável
X) e casos de dengue na semana seguinte (variável Y):

| Semana | Índice do mosquito (X) | Casos de dengue (Y) |
|---|---|---|
| 1 | 0,10 | 5 |
| 2 | 0,15 | 12 |
| 3 | 0,12 | 8 |
| 4 | 0,20 | 20 |

Há **6 pares possíveis** ($4×3/2$): (1,2), (1,3), (1,4), (2,3), (2,4), (3,4).

- (1,2): X sobe (0,10→0,15) e Y sobe (5→12) → **concordante**.
- (1,3): X sobe (0,10→0,12) e Y sobe (5→8) → **concordante**.
- (1,4): X sobe e Y sobe → **concordante**.
- (2,3): X desce (0,15→0,12) e Y desce (12→8) → **concordante**.
- (2,4): X sobe (0,15→0,20) e Y sobe (12→20) → **concordante**.
- (3,4): X sobe (0,12→0,20) e Y sobe (8→20) → **concordante**.

Neste exemplo fictício, todos os 6 pares são concordantes: $C=6$, $D=0$, e $τ = (6-0)/6 = 1,0$ — uma
correlação perfeita, porque os dados foram construídos para isso. O valor real medido por da Silva et al.
para *Aedes aegypti* na defasagem 4 foi **τ = 0,4953**: isso significa que, entre todos os pares de
semanas comparadas na série real deles, havia bem mais pares concordantes do que discordantes, mas
longe de ser perfeito — há bastante ruído na relação entre infestação do vetor e casos futuros de dengue.

### 6.3.6 Comparabilidade item a item com este projeto

| Item | Este projeto | da Silva et al. 2026 | Comparável? |
|---|---|---|---|
| Alvo | Casos confirmados semanais, contagem bruta, por município de notificação | (i) MFAI bruto; (ii) % de armadilhas positivas; (iii) log(incidência/100 mil hab. + 1) | **Não.** O alvo (iii) é o mais próximo em espírito, mas está em log e em incidência normalizada por população, não em casos brutos. |
| Horizonte | 1 a 12 semanas, testado fora da amostra, com corte pela data da resposta | 0 a 4 semanas, usado como defasagem de correlação/regressão **dentro** da amostra histórica | **Não.** Não há um horizonte de previsão prospectivo declarado; é ajuste histórico com variável defasada. |
| Validação | Validação em avanço (*walk-forward*), corte pela data da resposta | Validação cruzada de 10 partes embaralhadas, sem corte temporal | **Não.** O embaralhamento permite que o treino "veja" semanas posteriores à semana de teste — o mesmo mecanismo do vazamento que este projeto corrigiu em 13/09/2026 (seção 6.6). |
| Unidade espacial | Cidade inteira | Cidade inteira (modelo de incidência) + por bairro (MFAI, índice de Moran) | Parcialmente comparável, só no agregado municipal. |
| Métrica | Erro absoluto médio (MAE) em casos, coeficiente de determinação (R²) em casos, por horizonte | RMSE em log(incidência+1); razão de deviance | **Não comparável diretamente** — escalas diferentes (log × bruto) e RMSE em log não equivale a MAE em casos. A razão de deviance é o único ponto de contato conceitual com o R² deste projeto, mas mede ajuste **dentro** da amostra histórica, não previsão fora da amostra. |
| Papel do vetor como preditor | O vetor **piora** o alarme de surto em validação em avanço pareada (valor-p de Holm entre 0,037 e 0,0499, seção 6.6) | O MFAI defasado **correlaciona-se positivamente e de forma crescente com a defasagem** com casos futuros (τ de 0,27 a 0,50) — interpretado no texto como "relação de antecedência" (*lead relationship*) | **Achados na direção aparentemente oposta, mas metodologias diferentes** — ver 6.3.7. |

### 6.3.7 Por que a validação cruzada embaralhada é um problema em série temporal — a conexão com o vazamento de 13/09/2026

A validação cruzada de 10 partes embaralhadas, descrita na seção 6.3.3, tem o mesmo mecanismo estrutural
de um problema que este projeto **encontrou nos próprios dados** e corrigiu em **13/09/2026**: um
**vazamento temporal** (*data leakage*), que é quando o modelo, durante o treino, tem acesso, direta ou
indiretamente, a informação que só existiria no futuro em relação ao momento que está sendo previsto.

**O que foi medido aqui, no vazamento próprio:** antes da correção, o corte de treino usado neste projeto
respeitava a data da **pergunta** (a data-alvo da previsão), e não a data em que a **resposta** (o valor
real de casos daquela semana) estaria de fato disponível. Como o número de casos de uma semana demora a
ser consolidado no sistema de notificação, isso permitia que o treino "enxergasse", por um atalho técnico,
uma versão dos dados mais completa do que estaria realmente disponível no momento da previsão. O custo
medido dessa falha foi um aumento de **52% no erro absoluto médio (MAE)** no horizonte de 12 semanas, e
uma queda no coeficiente de determinação de **0,758 para 0,437** no mesmo horizonte — **152 células de
resultado** (combinações de configuração e período) tiveram que ser re-executadas depois da correção.

**A conexão com da Silva et al.:** quando o LASSO deles treina com uma parte dos dados escolhida por
sorteio, sem respeitar a ordem cronológica, uma das 9 partes de treino pode facilmente conter semanas
posteriores à semana de teste — o modelo aprende, sem perceber, um pedaço do padrão que só existiria no
futuro daquela semana específica. Isso não invalida o artigo deles como estudo de **associação espacial e
temporal** (que é o objetivo declarado do trabalho, e para esse objetivo o desenho é adequado), mas
significa que a razão de deviance de 0,61 relatada para o modelo de incidência **não pode ser lida como
"capacidade de previsão prospectiva"** no mesmo sentido que o R² deste projeto é lido — é uma medida de
quão bem o modelo se ajusta ao conjunto histórico completo, olhando os dados todos de uma vez.

**Isto não é uma crítica ao desenho do artigo deles**, e vale repetir isso com clareza: o objetivo do
trabalho de da Silva et al. é entender a dinâmica espaço-temporal da infestação e da transmissão — uma
pergunta de associação, não de previsão operacional. É uma diferença de **desenho para um objetivo
diferente**, não um erro de execução.

### 6.3.8 A pergunta que eles responderam e nós não — e o que isso significa para a banca

Da Silva et al. **mediram e quantificaram** a defasagem entre a infestação do vetor e os casos de dengue
(seção 6.3.4 e 6.3.5: τ de 0,27 na defasagem 0 até 0,50 na defasagem 4). Este projeto, até 26/09/2026,
**não estimou** essa defasagem de forma direta — o motivo, registrado como pendência em aberto no projeto,
é que o desenho deste trabalho testa uma pergunta diferente: não "o vetor se move junto com os casos
futuros?" (uma pergunta de correlação, respondida pelo τ de Kendall), mas **"o vetor ajuda a prever casos
futuros além do que já sabemos apenas pela época do ano?"** — uma pergunta de **contribuição
incremental**, testada controlando pelo que a régua sazonal (definida na seção 6.6) já captura sozinha.

São perguntas diferentes, e por isso os dois achados **não se contradizem tecnicamente**, mesmo
parecendo apontar em direções opostas à primeira vista:

- **"O vetor se move junto com a dengue?"** — sim, nos dois estudos, no fundo: ambos, vetor e casos,
  sobem com calor e umidade, então uma correlação bruta entre os dois tende a aparecer mesmo sem relação
  causal direta.
- **"O vetor ajuda a PREVER além do que a época do ano já entrega?"** — no teste deste projeto, controlado
  contra a régua sazonal em validação em avanço pareada, a resposta medida foi **não**: o vetor **piora**
  o alarme de surto no horizonte de 12 semanas, com significância estatística (seção 6.6).

Para a banca, a resposta a "se o artigo gêmeo de Porto Alegre encontrou o vetor útil, por que o de vocês
não encontrou o mesmo?" precisa ser **metodológica, não um desmentido do achado deles**: os dois estudos
medem coisas diferentes com desenhos diferentes, e ambos podem estar certos dentro do que cada um se
propôs a medir.

---

## 6.4 Os estudos brasileiros de previsão de dengue

Esta seção cobre, um a um, todos os estudos brasileiros de previsão de dengue lidos para compor este
documento. Nenhum é resumido a "entre outros" — cada um aparece com o que é, como funciona e que resultado
obteve.

### 6.4.1 Aleixo et al. 2022 — CatBoost, Rio de Janeiro

**O que é.** Um modelo chamado **CatBoost** — uma variante de *gradient boosting* (a mesma família de
técnica usada no cenário adotado deste projeto, o `HistGradientBoostingRegressor`, com a explicação
completa de *boosting* na Parte 2 e retomada resumidamente aqui: um método que constrói muitas árvores de
decisão pequenas em sequência, onde cada árvore nova tenta corrigir os erros deixados pelas árvores
anteriores) especializada em lidar bem com variáveis categóricas (como o nome do bairro) sem exigir
pré-processamento manual complexo.

**Escala:** cidade do Rio de Janeiro, **160 distritos individuais**, previsão mensal, dados de janeiro de
2011 a outubro de 2020 (fonte: sistema nacional de notificação SINAN — sigla para Sistema de Informação de
Agravos de Notificação). O volume típico de casos por distrito-mês, entre 2016 e 2020, tinha o percentil
95 em **24 casos** e o percentil 99 em **77 casos** — uma escala de caso por distrito-mês bem mais baixa do
que a cidade inteira de Porto Alegre por semana.

**Horizonte:** 1, 2 e 3 meses, com previsão recursiva de múltiplos passos (o modelo prevê 1 mês, usa essa
previsão como parte da entrada para prever o mês seguinte, e assim por diante).

**A métrica: R² usando a variância do próprio conjunto de teste, agregado por mês civil.** Diferente do R²
"clássico" (definido na seção 6.4.2), este é calculado juntando as previsões dos 160 distritos **daquele
mês específico**, e o denominador da fórmula (a variância total, contra a qual o erro do modelo é
comparado) muda a cada mês. Isso significa que o número de R² de um mês não é diretamente comparável ao de
outro mês — e o próprio artigo alerta que essa métrica pode ficar **negativa** em meses de transição de
temporada (fevereiro, junho e julho), porque a variância real de casos naqueles meses é muito pequena.

**Resultado (mediana do R² mensal, com o 25º percentil entre parênteses):** em 1 mês, **0,47** (0,31); em
3 meses, **0,38** (0,08). A régua de comparação foi o **SARIMA** por distrito, com mediana de R² de
**0,11** em 1 mês e **−0,16** em 3 meses — o CatBoost venceu essa régua com folga.

**⚠️ Uma limitação de desenho a registrar.** A validação usada foi validação cruzada de 5 anos (2016 a
2020), com 1 ano como teste e os outros 4 como treino — **incluindo anos futuros ao ano previsto**. Por
exemplo, para prever 2017, o treino usou 2016, 2018, 2019 e 2020, ou seja, **2018, 2019 e 2020 são
futuro** em relação a 2017. Isso é o mesmo tipo de desenho que a seção 6.3.7 discute para o LASSO de da
Silva et al., e o protocolo deste projeto (corte pela data da resposta) **proíbe** esse tipo de desenho.

### 6.4.2 da Cunha e Silva et al. 2026 — CatBoost × GRU, 27 capitais brasileiras

**O que é.** Uma comparação entre **CatBoost** (descrito acima) e **GRU** — sigla em inglês para *Gated
Recurrent Unit*, um tipo de rede neural artificial desenhada especificamente para dados sequenciais (como
séries temporais), que mantém uma "memória" interna resumida das observações anteriores para ajudar a
prever a próxima.

**Escala:** as **27 capitais brasileiras**, série semanal, taxa de morbidade por 100 mil habitantes,
período de **1999 a 2021**. Horizonte de 1 a 4 semanas, validado com **13 partes (folds) em validação em
avanço** — ou seja, ao contrário do LASSO de da Silva et al., este estudo **usa** o método correto de
corte temporal, com um normalizador de escala (*scaler*) recalculado a cada janela para evitar vazamento.

**O resultado específico para Porto Alegre — a comparação mais direta e mais desfavorável ao nosso
resultado, e é preciso dizer isso sem meio-termo:**

| Modelo | Erro absoluto médio | RMSE | Coeficiente de determinação (R²) | sMAPE |
|---|---|---|---|---|
| GRU | 0,2315 | 0,4764 | **−0,3085** | 97% |
| CatBoost | 0,2219 | 0,4575 | **−0,2064** | **160%** |

Segundo a verificação adversarial feita em 25/09/2026, Porto Alegre está **entre os piores desempenhos**
das 27 capitais — não foi possível confirmar, na leitura recuperada, se é **o** pior isolado, então esta é
a formulação correta a usar, e não "o pior".

**O que é o R² negativo.** O coeficiente de determinação (R²) mede a fração da variação dos dados reais
que o modelo consegue explicar, e sua fórmula é:

```
R² = 1 − (Σ(y_i − ŷ_i)²) / (Σ(y_i − ȳ)²)
```

Onde:

- **$y_i$** é o valor real da observação $i$;
- **$ŷ_i$** é o valor previsto pelo modelo para a observação $i$;
- **$ȳ$** (y com uma barra em cima) é a **média** de todos os valores reais no conjunto;
- **$Σ(y_i − ŷ_i)²$** é a soma dos quadrados dos erros do modelo — quanto menor, melhor o modelo;
- **$Σ(y_i − ȳ)²$** é a soma dos quadrados da diferença entre cada valor real e a média — a variação total
  que existe nos dados, sem nenhum modelo.

**Exemplo numérico, com os números do cenário adotado deste projeto no horizonte de 1 semana** (R² =
0,898, conforme o painel de erro do cenário adotado): um R² de 0,898 significa que o modelo explica
**89,8%** da variação real dos casos semana a semana, deixando 10,2% como erro não explicado. Um R²
**negativo**, como o −0,2064 do CatBoost em Porto Alegre no estudo de 27 capitais, significa que o modelo
é **pior do que simplesmente prever, toda semana, a média histórica de casos** — o modelo erra mais do que
erraria alguém que nem olhasse para os dados de entrada e só respondesse "a média de sempre".

**A definição exata da métrica sMAPE usada neste estudo, com fórmula e exemplo:**

O sMAPE (*symmetric Mean Absolute Percentage Error*, erro percentual absoluto médio simétrico) é uma
variação do MAPE (definido na seção 6.2.2) que evita alguns problemas matemáticos do MAPE clássico quando
o valor real é próximo de zero, ao dividir pela **soma** dos valores absolutos previsto e real, em vez de
só pelo valor real:

```
sMAPE = (2/n) × Σ |y_i − ŷ_i| / (|y_i| + |ŷ_i|) × 100%
```

Onde $n$ é o número de observações, e os demais símbolos são os mesmos definidos acima.

**Exemplo numérico com números do cenário adotado deste projeto**, horizonte de 12 semanas (sMAPE medido:
**108,16%**, conforme a certificação de 25/09/2026): tome uma única semana em que o valor real foi
$y=100$ e o modelo previu $ŷ=250$ (um erro de superestimação, para ilustrar como o sMAPE lida com esse
caso):

```
2 × |100 − 250| / (100 + 250) × 100% = 2 × 150/350 × 100% ≈ 85,7%
```

Repare que, se a fórmula fosse o MAPE clássico (dividindo só por $y=100$), o erro dessa mesma semana
seria $150/100 = 150\%$ — bem mais alto. O sMAPE "suaviza" esse tipo de caso porque também usa o valor
previsto no denominador, o que o torna uma métrica mais estável quando há tanto sub quanto
superestimação forte, mas ainda assim sensível a valores reais pequenos.

**Importante: o estudo de 27 capitais não tem régua de comparação.** É uma comparação CatBoost × GRU entre
si, sem nenhum dos dois testado contra persistência ou média histórica — o que impede saber, só com esse
artigo, se um sMAPE de 160% é "ruim para o problema" ou "esperado para uma série com muitas semanas de
poucos casos".

### 6.4.3 Chen & Moraga 2025 — efeito espacial entre estados vizinhos

**O que é.** Um modelo de rede neural do tipo **LSTM** (*Long Short-Term Memory*, uma variante de rede
neural recorrente parecida em espírito com a GRU descrita acima, mas com uma estrutura de memória interna
mais complexa) combinado com **SHAP** (*SHapley Additive exPlanations*, uma técnica que atribui, a cada
variável de entrada, uma contribuição numérica para a previsão final, permitindo entender o "porquê" de
uma previsão específica, e não só o número final).

**O achado central:** incluir o **efeito espacial de estados vizinhos** — isto é, usar como entrada
também os casos de dengue dos estados que fazem fronteira com o estado que está sendo previsto — reduziu
o erro absoluto médio em **34%** no estado de Minas Gerais, de **7.730 para 5.089 casos** (números
absolutos do próprio estudo).

**Comparabilidade:** a escala (nível estadual, todo o Brasil) é muito maior do que uma cidade só, e o
próprio estudo é sobre **direção do efeito** (vizinhança espacial ajuda), não sobre um número que se
transponha diretamente para Porto Alegre. É relevante para este projeto como uma **hipótese não testada
aqui**: Porto Alegre não tem "cidades vizinhas" no mesmo sentido de estados fazendo fronteira, mas o
princípio (informação de fora da própria série ajuda a prever) é o mesmo que motiva o uso de variáveis
climáticas e de vetor neste projeto.

### 6.4.4 Lowe et al. 2016 — risco categórico, 553 microrregiões

**O que é.** Um sistema de alerta prototípico para o Brasil que não prevê o número exato de casos, mas
sim uma **categoria de risco** (alto, médio ou baixo), com horizonte de **3 meses**, cobrindo **553
microrregiões brasileiras**, validado contra os meses da Copa do Mundo de 2014 (junho de 2014).

**A régua de comparação:** a **média sazonal histórica** de 2000 a 2013 — o equivalente conceitual, com
mais anos de histórico agregados, do "quantos casos houve na mesma semana do ano passado" deste projeto.

**O resultado:** o modelo acertou a categoria de risco alto em **57%** das vezes em que o risco alto
realmente ocorreu (81 acertos contra 60 erros), contra **33%** de acerto da régua sazonal (46 acertos
contra 95 erros).

**Por que este resultado não se aplica diretamente à comparação deste projeto:** o alvo é **categórico**
(uma classe de risco), não um valor contínuo de número de casos. Prever a categoria certa é, em geral,
mais fácil do que acertar o valor exato, porque a categoria absorve parte do erro de magnitude — um
modelo pode errar o número exato de casos por uma margem considerável e ainda assim acertar a categoria de
risco. Isso é compatível com o que este projeto já observa: o desempenho do **alarme de surto** (que
também é uma decisão categórica, "vai passar de X casos ou não") se comporta de forma diferente do erro
pontual medido pelo MAE (detalhe na Parte 8).

### 6.4.5 Os *sprints* nacionais InfoDengue-Mosqlimate (2024 e 2025) — a régua brasileira mais recente

**O que é.** Uma competição coordenada nacionalmente entre equipes de pesquisa, usando dados do
**InfoDengue** (sistema de alerta de dengue em operação desde 2015) e da plataforma **Mosqlimate** (que
compara modelos entre si de forma padronizada).

**Primeiro sprint (2024):** **6 equipes internacionais, 8 modelos preditivos**, previsão semanal
probabilística para **5 estados brasileiros**, avaliando as temporadas de 2024 e 2025. Coordenado por
Araujo, Carvalho, Codeço e Coelho, publicado em 2026 na revista PNAS.

**Segundo sprint (2025):** **15 equipes, 52 pesquisadores, 19 modelos**, cobrindo **todos os estados
brasileiros**, temporadas de 2025 e 2026.

**As métricas usadas — todas próprias de previsão probabilística, e não de previsão de um único número:**

- **CRPS** (*Continuous Ranked Probability Score*, pontuação de probabilidade classificada contínua) —
  explicada na seção **6.4.5**, sobre os *sprints* nacionais. ⚠️ O escore de probabilidade classificada
  contínua (CRPS) não recebe fórmula formal neste documento: aparece só na forma relativa, como escore de
  habilidade, que é a forma em que os estudos citados o reportam.
- **Log score** — o logaritmo negativo da probabilidade que o modelo atribuiu ao valor que de fato
  ocorreu. Quanto mais o modelo "confiava" (atribuía alta probabilidade) no valor que realmente aconteceu,
  menor (melhor) o log score.
- **Escore de intervalo (*interval score*) e sua versão ponderada, o WIS** — a métrica de erro usada neste
  projeto para medir a qualidade da faixa de incerteza da previsão, com fórmula e exemplo numérico
  completos na seção **6.6.4**, que traz a fórmula e o exemplo numérico do escore de intervalo
  ponderado.
- **WIS normalizado** (WIS_norm), calculado no segundo sprint como a soma do WIS dividida pelo total de
  casos no período de validação — uma forma de comparar estados com escalas de caso muito diferentes
  entre si.

**O resultado central: nenhum modelo individual venceu de forma consistente.** No primeiro sprint, o
desempenho variou por estado e por ano. No segundo sprint, um **ensemble** (a combinação da mediana dos 5
melhores modelos individuais) teve um **skill score mediano de 0,12** contra o melhor modelo individual —
ou seja, o ensemble reduziu o erro em cerca de 12% na mediana dos estados, mas **com exceções em que o
próprio ensemble foi pior** que modelos individuais (por exemplo, no Rio de Janeiro).

**Relevância para Porto Alegre:** este é o padrão nacional mais recente e mais próximo, em espírito, do
tipo de avaliação que este projeto faz — e ele confirma, numa escala nacional com dezenas de
pesquisadores competindo, o mesmo padrão encontrado neste projeto isoladamente: **nenhum modelo é
consistentemente o melhor em todas as condições**, e a métrica correta para reportar isso é o percentual
de vitórias contra uma régua, não apenas "o melhor modelo venceu".

---

## 6.5 A tabela comparativa final

A tabela abaixo reúne todos os estudos citados nesta seção, com uma coluna explícita de comparabilidade e
a razão de cada veredito. **"Sim"** significa que a métrica, a escala e o desenho permitem uma leitura
direta lado a lado; **"Parcial"** significa que a direção do achado é informativa, mas o número exato não
deve ser lido como equivalente; **"Não"** significa que comparar os números diretamente induziria a erro.

| Estudo | Onde / escala | Uso | Métrica e valor | Comparável? | Razão |
|---|---|---|---|---|---|
| Shi et al. 2016 (LASSO) | Singapura inteira, semanal, 13 anos | **Operacional** (NEA) | MAPE 17% (1 sem.) / 24% (12 sem.) | Parcial | Mesma família de métrica percentual, mas escala de casos (até 842/semana) muito maior que POA |
| Finch et al. 2025 | Singapura, semanal, 23 anos | Pesquisa | CRPSS +54% (clima) / +60% (clima+sorotipo) | Não | Métrica de habilidade relativa (CRPSS), não erro absoluto; horizonte mais curto (8 sem.) |
| da Silva et al. 2026 (preprint medRxiv) | Porto Alegre, semanal, 8 anos entomológicos | Pesquisa | RMSE 1,003–1,006 em log(incidência+1); razão de deviance 0,61 | Não | Alvo em log-incidência, não casos brutos; validação cruzada embaralhada, não em avanço; sem horizonte fixo declarado |
| Aleixo et al. 2022 (CatBoost) | Rio de Janeiro, 160 distritos, mensal | Pesquisa | R² mediano 0,47 (1 mês) / 0,38 (3 meses) | Não | R² mensal por distrito-mês, escala e agregação diferentes; treino usa anos futuros ao alvo |
| da Cunha e Silva et al. 2026 (CatBoost/GRU) | 27 capitais BR, incl. POA, semanal | Pesquisa | POA: R² −0,21 a −0,31; sMAPE 97–160% | **Sim, para POA** | Mesma cidade, mesma unidade (casos/incidência), validação em avanço — é a comparação mais direta e mais desfavorável ao nosso resultado |
| Chen & Moraga 2025 | Todos os estados BR, mensal | Pesquisa | MAE −34% com efeito espacial (MG: 7.730→5.089) | Não | Escala estadual; achado é de direção (vizinhança ajuda), não de magnitude transponível |
| Lowe et al. 2016 | 553 microrregiões BR, 3 meses | Pesquisa | Acerto de categoria: 57% × 33% (régua) | Não | Alvo categórico (risco), não erro pontual contínuo |
| Sprints IMDC 2024/2025 | Estados brasileiros, semanal | Pesquisa (com uso na resposta do Ministério da Saúde) | Nenhum modelo consistente; ensemble skill mediano 0,12 | Parcial | Mesmo país, métricas de habilidade probabilística (CRPS/WIS), não redutível a um número único comparável |
| Wu et al. 2025 (ensemble) | 187 locais, 5 países incl. Brasil, mensal | **Operacional** (alocação de ensaios clínicos) | PAE 38,5% / 54,5% / 62,7% (1/2/3 meses) | Não | Escala estadual/provincial mensal; fórmula exata da métrica não publicada no corpo do artigo |
| D-MOSS (Vietnã) | 63 províncias, mensal, 20+ anos | **Operacional** desde 2019 | RMSE (incidência/100mil): 20,35 (1 mês) / 25,99 (6 meses); régua 23,93 / 35,38 | Não | Unidade de incidência normalizada, usa previsão climática futura como entrada — recurso que nenhum cenário deste projeto usa |
| Superensemble Vietnã 2021 | 63 províncias, mensal | Precursor do D-MOSS | CRPS 66,8 × 79,4 (régua) em 1-3 meses; vantagem some em 4-6 meses | Não | Métrica probabilística (CRPS) em contagem de casos por província, heterogênea |
| Johansson et al. 2019 | San Juan/Iquitos, 8 temporadas | Desafio de pesquisa (16 equipes) | SARIMA simples venceu métodos complexos no alvo do pico | Parcial | Não numérico direto, mas achado estrutural relevante: régua simples é difícil de vencer no alvo mais difícil |
| Benedum et al. 2020 | Iquitos/San Juan/Singapura | Pesquisa | RF perde para ARIMA em 12 semanas (nMAE pior) | Parcial | Mesmo padrão de horizonte (12 semanas) e mesma inversão observada neste projeto |
| Zhao et al. 2020 (RF) | Colômbia, nacional/departamental, semanal | Pesquisa | MAE 9,32 (1 sem.) / 24,56 (12 sem.) | Não | Escala nacional colombiana (milhares de casos/semana), muito maior que POA |

---

## 6.6 Por que os nossos resultados são o que são

Esta seção junta os números deste projeto (repetidos aqui para não obrigar o leitor a voltar a outra
parte do documento) com o que a literatura mostra, para explicar — nos dois sentidos, quando favorável e
quando desfavorável — por que o resultado obtido é o que é.

### 6.6.1 Onde estamos **acima** da literatura comparável

- **Contra o estudo mais diretamente comparável (27 capitais, incluindo Porto Alegre):** nosso R² no
  cenário adotado é **0,898** (1 semana), **0,628** (4 semanas), **0,450** (8 semanas) e **0,437** (12
  semanas). O mesmo tipo de modelo (gradient boosting), rodado especificamente para Porto Alegre no estudo
  de 27 capitais, teve R² **negativo** (−0,21 a −0,31). A diferença é grande o suficiente para não
  depender de nenhuma nuance de definição de métrica: um R² positivo de 0,437 contra um R² negativo
  significa que o nosso modelo, no mínimo, **é melhor do que prever a média histórica toda semana**,
  enquanto o modelo do outro estudo, para a mesma cidade, **não é**.
- **Contra Aleixo et al. 2022 (Rio de Janeiro):** nosso R² em 3 meses (0,437) é comparável em ordem de
  grandeza ao R² mediano deles em 3 meses (0,38), mesmo com a ressalva de que o desenho deles usa anos
  futuros no treino (o que tende a inflar o resultado deles, e não o nosso).

### 6.6.2 Onde estamos **abaixo** da literatura comparável — sem maquiagem

- **Contra a régua sazonal, no horizonte de 3 meses, na janela oficial de 2024 a 2026:** o erro absoluto
  médio do cenário adotado é **278,8 casos**; a régua sazonal erra **217,8 casos** na mesma janela — a
  régua **vence**. Pelo escore de intervalo ponderado (WIS, com fórmula e exemplo na seção 6.6.4), na
  janela 2024–2025, o cenário adotado tem **300,7** contra **324,2** da régua climatológica: aqui o
  cenário adotado vence, mas **sem significância estatística** (o valor-p ajustado de Holm é 0,096 — a
  seção 6.6.4 explica o que esse número quer dizer). Já a variante com folha mínima 20 vence com
  significância (valor-p de Holm 0,0020).
- **Contra o D-MOSS (Vietnã) e o superensemble precursor:** ambos vencem a régua sazonal deles em
  horizontes de 1 a 3 meses (D-MOSS: RMSE 25,70 contra 31,29 da régua, uma vantagem de cerca de 18%;
  superensemble: CRPS 66,8 contra 79,4). Nosso cenário adotado, no mesmo tipo de comparação, **perde** para
  a régua sazonal em 3 meses.
- **Contra Benedum et al. 2020 (Iquitos/San Juan/Singapura):** o achado deles — modelos de aprendizado de
  máquina perdem para réguas estatísticas simples especificamente no horizonte de 12 semanas — é
  **exatamente o mesmo padrão** encontrado neste projeto.

### 6.6.3 Por que isso acontece — as três razões medidas, não hipotéticas

1. **Poucas temporadas de treino.** Este projeto tem **4 temporadas de epidemia utilizáveis** (2022 a
   2025). Singapura (Shi et al.) usou 10 anos só de treino; o D-MOSS usa dados desde 2002; Porto Rico
   (seção 6.7) usa 38,5 anos. Menos temporadas significa menos exemplos de "como uma epidemia cresce e
   diminui" para o modelo aprender — e menos exemplos também para a **régua sazonal** aprender, mas a
   régua sazonal precisa de muito menos dado para funcionar (ela só olha para a mesma semana do ano
   anterior), então a desvantagem de série curta pesa mais sobre o modelo do que sobre a régua.
2. **Viés sistemático de subestimação de picos.** "Viés", aqui, é o erro que se repete sempre na mesma
   direção — não um erro aleatório que às vezes é para cima e às vezes para baixo, mas um erro que
   consistentemente aponta para o mesmo lado. **FATO (medido em 26/09/2026):** na faixa de casos reais
   mais alta (a faixa chamada "Alerta ou mais", com mais de 421 casos reais na semana, seguindo o limiar
   do Plano Municipal de Contingência — detalhado na Parte 7), o **real mediano** dessas semanas foi **917
   casos**, e o **erro mediano** do modelo nessas mesmas semanas foi **539 casos**. Isso significa que a
   previsão típica nessas semanas ficou em torno de $917 - 539 = 378$ casos — o modelo previu menos da
   metade do que de fato aconteceu. **Tradução concreta deste número:** é como um hospital planejar leitos
   para receber 378 pacientes numa semana de pico e, na prática, chegarem 917 — **quase duas vezes e meia a
   mais do que o planejado**. Esse mesmo mecanismo — modelos de previsão de epidemia subestimando picos, e o
   viés piorando com o horizonte — é documentado de forma independente no estudo de Cramer et al. 2022
   sobre previsões de COVID-19 nos Estados Unidos, com dezenas de milhões de previsões avaliadas: "toda
   previsão piora em acurácia e aumenta variância no horizonte de 4 semanas contra 1 semana", atribuído
   principalmente a subestimar a possibilidade de a incidência subir.
3. **A calibração da faixa de incerteza é boa exatamente onde importa menos, e ruim exatamente onde
   importa mais.** **FATO (medido em 26/09/2026, avaliação por faixa).** A previsão deste projeto não
   entrega só um número — entrega também uma faixa de incerteza (um **intervalo de confiança**, por
   exemplo "entre 200 e 400 casos, com 90% de confiança de que o valor real cairá nessa faixa"). Na faixa
   de "calmaria" (0 a 20 casos reais na semana), o intervalo de 90% cobriu o valor real em **90,5%** das
   semanas — próximo do esperado. Na faixa "Alerta ou mais" (mais de 421 casos reais), esse mesmo
   intervalo de 90% cobriu o valor real em apenas **17,8%** das semanas — ou seja, em mais de 4 a cada 5
   semanas de pico, o valor real caiu **fora** da faixa que o modelo declarou como "90% de confiança".
   Tentativas de consertar isso alargando a escala da previsão (aplicando raiz quadrada ou logaritmo antes
   de prever) **pioraram** a cobertura em vez de melhorar (seção 6.6.4 detalha por quê), porque a causa
   raiz é **viés** (o modelo aponta sistematicamente para um valor baixo demais), e alargar o intervalo em
   torno de um centro errado não resolve um problema de centro errado.

### 6.6.4 O que é o WIS (escore de intervalo ponderado), com fórmula e exemplo — e o que o valor-p de Holm significa aqui

**A definição.** O WIS (*Weighted Interval Score*, escore de intervalo ponderado) é a métrica usada nos
sprints nacionais de dengue (seção 6.4.5), no FluSight do CDC (o sistema de previsão de gripe dos Estados
Unidos) e no COVID Forecast Hub, e é a métrica usada neste projeto para avaliar a qualidade da faixa de
incerteza da previsão, não só o valor central previsto. A formulação de referência, de Bracher et al.
2021, para um único nível de intervalo de confiança (por exemplo, 90%):

```
IS_α(l, u, y) = (u − l) + (2/α)(l − y) × 1{y < l} + (2/α)(y − u) × 1{y > u}
```

Onde:

- **$l$** e **$u$** são o limite inferior e o limite superior do intervalo de previsão (por exemplo, "entre
  200 e 400 casos");
- **$y$** é o valor real observado;
- **$α$** (a letra grega alfa) é o complemento do nível de confiança — para um intervalo de 90%, $α=0,10$;
  para um intervalo de 50%, $α=0,50$;
- **$1\{y<l\}$** e **$1\{y>u\}$** são "indicadores": valem **1** se a condição entre chaves for verdadeira,
  e **0** caso contrário — ou seja, esses termos só entram na conta quando o valor real ficou **fora** do
  intervalo (abaixo do limite inferior ou acima do limite superior).

O WIS completo combina vários desses escores de intervalo, calculados em vários níveis de confiança
(tipicamente 50% e 90%, entre outros), mais um termo de erro absoluto na mediana, todos ponderados e
somados. Quanto **mais níveis de intervalo** forem usados, mais o WIS se aproxima matematicamente do CRPS
(a métrica contínua descrita a seguir).

**Exemplo numérico ilustrativo, com números do projeto** (este exemplo simplifica o cálculo para mostrar o
mecanismo — o valor final não reproduz o número exato reportado na tabela oficial do projeto, que usa mais
níveis de intervalo e é calculado por código, não à mão):

Tome a faixa "Alerta ou mais" descrita acima: valor real $y = 917$; suponha, para este exemplo, um
intervalo de 90% de $l=650$ e $u=1.243$ (uma largura de 593, compatível com a largura mediana medida de
592,7 casos nessa faixa, centrada aproximadamente no ponto de previsão de 378 mais o deslocamento típico
da distribuição de quantis do modelo). Como $y=917$ está **dentro** de $[650, 1.243]$ neste exemplo
específico, os termos de penalidade (o segundo e o terceiro termo da fórmula) seriam zero, e o escore de
intervalo seria simplesmente a largura: $IS_{0,10} = 1.243 − 650 = 593$. Se, em vez disso, o intervalo
superior estivesse em $u=850$ (mais estreito, e sem cobrir o valor real de 917, o que é o que **de fato**
acontece na maioria das semanas dessa faixa, dado que a cobertura medida foi de apenas 17,8%):

```
IS_{0,10} = (850 − 650) + (2/0,10) × (917 − 850) × 1
          = 200 + 20 × 67
          = 200 + 1.340 = 1.540
```

Este número mostra o mecanismo central do WIS: **errar para fora do intervalo custa muito mais caro do
que a simples largura do intervalo** — o fator $2/α$ (aqui, 20) multiplica a distância do valor real até o
limite mais próximo, punindo pesadamente os casos em que o modelo declarou confiança e errou. É por isso
que a cobertura baixa medida (17,8% na faixa de Alerta) é tão custosa para o WIS quanto para qualquer
leitor que precise confiar na faixa declarada pelo modelo.

### 6.6.5 O que é o valor-p, com o exemplo do próprio projeto (p de Holm < 0,0001)

O **valor-p** responde a uma pergunta específica: **se, na realidade, não existisse diferença nenhuma**
entre dois modelos sendo comparados (a chamada "hipótese nula" — a suposição, feita só para fins do
teste, de que a diferença observada é pura coincidência de amostragem), **qual seria a probabilidade de
observar, por puro acaso, uma diferença tão grande ou maior do que a que foi medida?**

Um valor-p pequeno significa que essa coincidência seria muito improvável — e por isso a diferença
observada é lida como um sinal real, não ruído.

**A correção de Holm.** Quando várias comparações são feitas ao mesmo tempo (por exemplo, comparar o
modelo contra a régua em 4 horizontes diferentes, ou contra várias réguas diferentes), a chance de que
**pelo menos uma** dessas comparações dê um resultado "significativo" só por acaso **aumenta** com o
número de comparações — é o mesmo princípio de jogar uma moeda várias vezes: quanto mais vezes se joga,
maior a chance de, em algum lance, sair uma sequência que pareceria "suspeita" mesmo com uma moeda
honesta. A correção de Holm ajusta o limiar de significância de cada teste individual para compensar esse
efeito, mantendo sob controle a taxa de falsos positivos **para o conjunto inteiro** de comparações feitas
na mesma rodada (a "família" de testes).

**Exemplo com os números do projeto.** Na comparação do escore de intervalo ponderado (WIS) entre o
cenário adotado e a régua climatológica, no horizonte de 4 semanas, o resultado medido foi **215,4**
(cenário adotado) contra **313,5** (régua climatológica) — uma diferença de cerca de 32% a favor do
modelo. O valor-p de Holm para essa comparação foi **menor que 0,0001**. Isso significa: **se, na
realidade, o modelo e a régua tivessem o mesmo desempenho esperado**, a chance de observar, por puro
acaso de amostragem, uma vantagem tão grande quanto 32% a favor do modelo seria **menor do que 1 em 10
mil** — mesmo depois de ajustar essa probabilidade para o fato de que essa comparação fazia parte de uma
família maior de testes simultâneos. É, na prática, uma evidência estatística forte de que a vantagem do
modelo sobre a régua climatológica em 4 semanas é real, e não coincidência da amostra avaliada.

Contraste isso com o horizonte de 12 semanas, onde o cenário adotado teve WIS de **300,7** contra **324,2**
da régua — uma vantagem numérica menor (cerca de 7%) — e o valor-p de Holm foi **0,096**. Como 0,096 é
maior que o limiar convencional de 0,05, a conclusão honesta é: **não há evidência estatística suficiente
para dizer que essa vantagem de 7% é real e não apenas ruído de amostragem** — mesmo que o número pareça,
à primeira vista, favorável ao modelo.

---

## 6.7 A lacuna que este trabalho ocupa

A literatura revisada nas seções anteriores — Singapura, Vietnã, Porto Rico (detalhado abaixo), os
*sprints* nacionais — tem um traço em comum que separa esses estudos do problema de Porto Alegre: todos
eles **pressupõem uma área endêmica com décadas de série histórica**, incluindo anos sem epidemia grande,
para calibrar o que é "normal" antes de alertar sobre o que é "anormal".

**Porto Rico é o exemplo mais direto deste ponto**, e vale detalhar porque uma hipótese levantada
inicialmente neste projeto — de que o método de Porto Rico serviria de modelo justamente por ter sido
criado **sem** série histórica longa — foi **testada e refutada** em 26/09/2026:

- **FATO (verificado em 26/09/2026, fonte MMWR mm7405a1, lido via PMC12370255):** Porto Rico tem
  vigilância contínua de dengue desde **1986**, através do *Dengue Branch* do CDC (Centro de Controle e
  Prevenção de Doenças dos Estados Unidos) em San Juan. O limiar epidêmico oficial deles é definido como o
  **percentil 75 de uma regressão binomial negativa** — um tipo de modelo estatístico usado para contar
  eventos raros, adequado quando a variância dos dados é maior do que a média, o que é comum em contagem
  de casos de doença — **ajustada sobre 86.282 casos, cobrindo cerca de 38,5 anos** de história (1986 a
  2024), **sem excluir os anos de epidemia grande** do cálculo do limiar.
- **A hipótese original não se sustenta**: Porto Rico não criou um método para série curta; criou um
  método que **exige** uma série ainda mais longa do que a de Singapura (38,5 anos contra pouco mais de
  20). O método deles é, estruturalmente, o mesmo tipo de método usado pelo canal endêmico clássico e pelo
  chamado **MEM** (*Método de Encoder Móvel*, sigla usada pelo sistema brasileiro InfoDengue para calcular
  limiares de alerta) — um percentil calculado sobre o histórico da própria série.
- **O motivo pelo qual esse tipo de método falha em Porto Alegre já foi medido, e não é hipotético:** o
  canal endêmico, aplicado à série de Porto Alegre, dá um limite de **zero** em muitas semanas fora da
  temporada de dengue, porque os anos de 2018 a 2021 tiveram pouquíssimos casos. Um exemplo concreto: na
  semana epidemiológica 39 de 2024, com **7 casos** confirmados, o limite calculado pelo canal endêmico
  para aquela semana era **zero** — ou seja, qualquer caso, por menor que fosse, já teria disparado um
  alarme de "acima do canal", tornando o alarme inútil por excesso de sensibilidade.
- **O limiar do próprio InfoDengue está subindo junto com o crescimento da epidemia, ano após ano**: o
  corte usado pelo método MEM para classificar uma semana como "baixa incidência" era de **6 casos** por
  semana entre 2010 e 2021, e subiu para **94 casos** por semana em 2025 — um aumento de mais de 15 vezes
  em poucos anos, porque o método recalcula o "normal" usando o histórico recente, e o histórico recente
  de Porto Alegre está mudando rápido demais para esse tipo de método estabilizar.

**A alternativa que a literatura oferece para séries curtas, e que não depende de décadas de história:**

- **Limiares fixos por incidência populacional**, já usados em outras áreas de invasão recente da dengue:
  México usa um corte de **2 casos por 100 mil habitantes por ano**; o Brasil, como país, usa **20 por 100
  mil**. É a mesma lógica dos limiares de **140, 421 e 702 casos por semana** do Plano Municipal de
  Contingência de Arboviroses 2026 da Secretaria Municipal de Saúde de Porto Alegre — que não depende do
  histórico da própria série de Porto Alegre para ser calculado, e por isso não sofre do mesmo problema
  medido acima.
- **HIPÓTESE, não testada neste projeto:** a regra de **aceleração de transmissão** — a razão entre a
  média móvel de 4 semanas e a média móvel de 26 semanas dos casos, com alarme quando essa razão ultrapassa
  **1,33** — testada em 8 países (incluindo Singapura) na literatura, com sensibilidade de **100%** contra
  **30%** do canal endêmico clássico, e antecedência média de **6,9 semanas** contra **1,6 semanas** do
  canal endêmico. Essa regra **não depende de anos de histórico**, só de 26 semanas contínuas — dentro do
  alcance de qualquer série corrente de Porto Alegre. **Ela ainda não foi medida com os dados de Porto
  Alegre**, e há um precedente de cautela direto: uma regra parecida, importada da Malásia ("acima do
  canal endêmico e crescendo"), foi testada em 25/09/2026 e foi a **pior** de todas as réguas testadas em
  Porto Alegre (índice de Youden de −0,05, pior do que uma moeda jogada ao acaso), o que mostra que uma
  regra que funciona em outro país **pode não se transferir** sem verificação local.

**A conclusão desta seção, e a lacuna que este trabalho de fato ocupa:** a literatura internacional madura
resolveu o problema de alertar sobre surtos assumindo décadas de série histórica com anos calmos
suficientes para calibrar o que é "normal". Porto Alegre é uma cidade onde a dengue está se tornando
endêmica **agora**, com apenas 4 temporadas de epidemia utilizáveis e nenhum ano recente sem epidemia
grande o bastante para servir de calibração. Este trabalho não corrige essa limitação — ela é uma
característica dos dados disponíveis, não um defeito de método — mas **mede exatamente o que acontece
quando se tenta aplicar, mesmo assim, os métodos padrão a essa realidade**, e propõe, como alternativa
testável (e ainda não testada em profundidade), instrumentos que a própria literatura já descreve como
adequados para esse cenário de série curta: limiares fixos de incidência e a régua de aceleração de
transmissão.

---

# Parte 7 — Limiares oficiais e a justificativa de usar o modelo como alarme

## 7.1 O que esta seção sustenta

Esta seção sustenta a escolha central deste trabalho: usar a previsão do modelo não como um número a ser
lido diretamente ("na semana X vão ocorrer Y casos"), mas como a entrada de um **classificador de alarme**
— uma regra que responde apenas SIM ou NÃO à pergunta "esta semana vai passar de um certo número de
casos?". Essa é uma escolha de desenho, não um detalhe técnico, e precisa ser justificada com o mesmo rigor
que qualquer outra decisão de método deste projeto.

A justificativa se apoia em quatro pilares, cada um desenvolvido em uma seção adiante:

- **um precedente na literatura de vigilância** (Porto Rico), que mostra que transformar uma série
  temporal em um sistema de limiares de alerta é uma prática estabelecida — mas cujo **método de cálculo**
  não pode ser copiado para Porto Alegre, pelos motivos explicados no item 7.2;
- **uma fonte oficial e local** para os números de corte — o Plano Municipal de Contingência de
  Arboviroses da Secretaria Municipal de Saúde de Porto Alegre (item 7.3), usada de forma **parcial e
  declarada** (item 7.4);
- **uma razão matemática de fundo** — a relação entre o quantil que o modelo aprende a prever e uma leitura
  probabilística do alarme (item 7.6);
- **um conjunto de medições próprias**, feitas em 25 e 26 de setembro de 2026, que testam essa escolha
  contra a alternativa mais simples possível — repetir o que aconteceu no mesmo período do ano anterior —
  e que, sem suavização, não a confirmam de forma estatisticamente conclusiva (itens 7.7 e 7.8).

O compromisso desta seção, e de todo o documento, é relatar os quatro pilares com o mesmo peso, inclusive
quando o quarto contradiz a intuição que motivou o primeiro e o terceiro.

---

## 7.2 O argumento de Porto Rico: separando o conceito do método

### 7.2.1 O que Porto Rico fez

Porto Rico é um território dos Estados Unidos no Caribe que mantém **vigilância epidemiológica contínua**
da dengue — ou seja, a contagem sistemática e ininterrupta de casos, semana a semana, sem lacunas — desde
**1986**, conduzida pelo CDC Dengue Branch ("Dengue Branch" é a divisão do CDC, o Centro de Controle e
Prevenção de Doenças dos Estados Unidos, dedicada a esta doença) sediado em San Juan.

**FATO (fonte: MMWR mm7405a1, *"Dengue Outbreak and Response — Puerto Rico, 2024"*, publicado em
20/02/2025, lido via o repositório público PMC12370255).** O artigo relata que, em janeiro de 2024, o
número semanal de casos ultrapassou o **limiar epidêmico** oficial do território, e uma emergência de
saúde pública foi declarada em março de 2024. O ano fechou com **6.291 casos confirmados e 11 óbitos**.

Um **limiar epidêmico**, aqui, é um valor de referência: quando o número de casos observados numa semana
ultrapassa esse valor, considera-se que a doença está circulando acima do que se espera para aquele
período do ano, e uma resposta de saúde pública é acionada (reforço de vigilância, comunicação, controle de
vetor, alocação de leitos).

### 7.2.2 Como esse limiar é calculado — e por que o cálculo não serve para Porto Alegre

**FATO.** O método de Porto Rico ajusta uma **regressão binomial negativa** sobre **86.282 casos** de
dengue registrados entre 1986 e 2024 — um período de aproximadamente **38,5 anos** — e usa o **percentil
75** dessa distribuição ajustada como limiar epidêmico.

Dois termos técnicos precisam ser definidos aqui, porque sustentam o argumento inteiro desta subseção:

- **Regressão binomial negativa.** É um modelo estatístico usado para dados de contagem (números inteiros
  não negativos, como "casos por semana") quando a variância dos dados é maior do que a média — fenômeno
  chamado de **sobredispersão**. A regressão de Poisson, o modelo padrão para contagens, assume que
  variância e média são iguais; quando isso não é verdade — como costuma acontecer em séries
  epidemiológicas, que alternam longos períodos calmos com picos explosivos —, a binomial negativa descreve
  os dados com mais fidelidade, porque tem um parâmetro extra que absorve esse excesso de variância.
- **Percentil.** O percentil 75 de uma distribuição é o valor abaixo do qual estão 75% das observações. Se
  o percentil 75 do número semanal de casos em Porto Rico, segundo o modelo ajustado, é um certo valor V,
  isso significa que, historicamente, 75% das semanas tiveram menos casos que V, e apenas 25% tiveram mais.
  Um limiar no percentil 75 é, portanto, um corte estatístico sobre o comportamento **histórico completo**
  da doença naquele lugar — não um número escolhido a priori.

**Aqui está o ponto que precisa ficar cristalino.** Esse cálculo depende de duas condições que Porto Rico
tem e Porto Alegre não tem:

1. **Uma série longa** — quase quatro décadas, contra os poucos anos de série epidemiologicamente
   relevante que Porto Alegre possui (ver item 7.2.3, abaixo).
2. **Anos sem epidemia dentro dessa série**, que servem de referência para o que é "normal". O texto do
   artigo é explícito quanto a isso: a regressão binomial negativa é ajustada sobre a série **inteira**,
   *sem excluir os anos epidêmicos* — o que só é estatisticamente razoável porque, numa série de 38,5 anos,
   os anos epidêmicos são uma minoria que não domina o ajuste. Numa série curta e majoritariamente
   epidêmica, o mesmo procedimento produziria um "percentil 75" inflado pelas próprias epidemias que ele
   deveria detectar — um problema que é medido diretamente no item 7.5, adiante.

⚠️ **Ressalva de leitura.** O artigo-preprint que descreve o método em detalhe (medRxiv
10.1101/2024.10.22.24315684) não pôde ser lido: o acesso ao texto completo devolveu erro HTTP 403
(bloqueio de acesso) em 25/09/2026. A descrição do método usada aqui vem do resumo do próprio artigo do
MMWR, que é a fonte principal, revisada por especialistas do CDC antes da publicação — mas o detalhe fino
do ajuste estatístico não foi verificado na fonte primária do método.

### 7.2.3 A conclusão que se sustenta: adotar o conceito, não o método

**HIPÓTESE, tratada aqui como decisão de desenho, não como fato estatístico.** O que este projeto adota do
exemplo de Porto Rico é o **conceito operacional**: transformar uma previsão contínua (quantos casos vão
ocorrer) em um instrumento de decisão binário (soar o alarme ou não), ancorado em limiares que disparam
ação concreta de vigilância. Isso é transferível — é uma prática de saúde pública, não uma fórmula
estatística amarrada à história epidemiológica de um lugar específico.

O que **não** é adotado é o **método de cálculo do limiar** — a regressão binomial negativa sobre a série
histórica. Ele exige exatamente o que Porto Alegre não tem: décadas de série com anos calmos que sirvam de
referência. A seção 7.5 mostra, com números, o que acontece quando um método dessa família (o "canal
endêmico" clássico, aparentado ao de Porto Rico) é aplicado mesmo assim aos dados da cidade.

Em vez do método de Porto Rico, os limiares numéricos usados neste projeto vêm de uma fonte diferente,
explicada a seguir: um plano de contingência municipal, que já converteu a decisão de "o que é normal e o
que é alerta" em números fixos, sem exigir do projeto o cálculo desse ajuste histórico.

---

## 7.3 De onde vêm os nossos limiares: o Plano Municipal de Contingência de Arboviroses 2026

### 7.3.1 A fonte

Os quatro patamares usados neste trabalho vêm do **Plano Municipal de Contingência de Arboviroses 2026**,
documento da **Secretaria Municipal de Saúde de Porto Alegre (SMS-POA)**, publicado em **dezembro de
2025**. O critério está no **Quadro 1, página 15** do documento (arquivo local:
`Artigos de referencia/2026_Plano_Municipal_de_Contingencia_Arboviroses.docx_0.pdf`).

"Arbovirose" é o termo geral para doenças transmitidas por vírus que se replicam em artrópodes (insetos,
carrapatos) e são transmitidos por eles a humanos — a dengue é uma arbovirose, assim como a zika e a
chikungunya, todas transmitidas pelo mosquito *Aedes aegypti* em Porto Alegre.

### 7.3.2 Os quatro estágios

O plano define quatro estágios de resposta, cada um com um critério numérico sobre a **incidência**
semanal de casos **confirmados**. Incidência, aqui, é o número de casos dividido pelo tamanho da
população e multiplicado por 100 mil — a unidade padrão em epidemiologia para tornar comparáveis
lugares com populações diferentes, chamada de **"casos por 100 mil habitantes"**.

| Estágio | Critério de incidência (confirmados) | Em casos por semana* |
|---|---|---|
| **Normalidade** | abaixo de 10,0 por 100 mil, em todas as últimas 4 semanas | abaixo de **140** |
| **Mobilização** | acima de 10,0 por 100 mil, em pelo menos 1 das últimas 4 semanas | acima de **140** |
| **Alerta** | acima de 30,0 por 100 mil, em pelo menos 1 das últimas 4 semanas | acima de **421** |
| **Epidemia** | acima de 50,0 por 100 mil, em pelo menos 1 das últimas 4 semanas | acima de **702** |

*\*Conversão explicada no item 7.3.3, abaixo. ⚠️ Ver a ressalva do item 7.4 — a coluna da direita é uma
simplificação declarada do critério real do plano, que também exige uma segunda condição.*

Cada estágio dispara uma resposta diferente da Secretaria. O documento mostra, por exemplo, que a
**testagem laboratorial encolhe conforme a situação piora**:

- em **Normalidade** e **Mobilização**, são testados viajantes, pessoas com comorbidades, gestantes,
  crianças menores de 5 anos, idosos acima de 60 anos, além dos grupos de sintomas B e C do protocolo
  clínico;
- em **Alerta** e **Epidemia**, a testagem se restringe a viajantes, gestantes e idosos acima de 60 anos.

**HIPÓTESE (não testada neste documento).** Essa mudança de protocolo de testagem pode ajudar a explicar
por que a taxa de confirmação de casos suspeitos cai durante epidemias grandes — menos gente é testada
justamente quando mais gente está doente — mas essa relação não foi medida diretamente na base de dados
deste projeto.

Os estágios **Alerta** e **Epidemia** também podem ser disparados, independentemente da incidência, por
**um óbito confirmado** por dengue nas últimas 4 semanas, ou pela circulação de um **sorotipo novo do
vírus** (a dengue tem quatro sorotipos — DENV-1 a DENV-4 — e a chegada de um sorotipo que não circulava
antes numa região é, por si, um sinal de risco, porque a população não tem imunidade prévia a ele). Nenhum
desses dois gatilhos é previsto pelo modelo deste projeto, que trabalha apenas com o número de casos.

### 7.3.3 A conversão de incidência para casos por semana — a conta completa

O plano expressa seus critérios em casos por 100 mil habitantes; este projeto trabalha com o número
absoluto de casos por semana, porque é isso que o modelo prevê. A conversão exige a população da
cidade usada como referência.

**A fórmula:**

```
casos_limiar = (taxa_por_100_mil / 100.000) × população
```

Onde:

- `casos_limiar` é o número absoluto de casos confirmados por semana que equivale ao patamar do plano;
- `taxa_por_100_mil` é o corte de incidência do plano (10,0 · 30,0 · 50,0);
- `população` é a população de referência de Porto Alegre usada pelo InfoDengue e pelo plano, **1.404.269**
  habitantes.

**O exemplo numérico, para os três cortes fixos do plano:**

- Normalidade/Mobilização, 10,0 por 100 mil:
  `(10,0 / 100.000) × 1.404.269 = 0,0001 × 1.404.269 = 140,4269` → arredondado, **140 casos/semana**.
- Alerta, 30,0 por 100 mil:
  `(30,0 / 100.000) × 1.404.269 = 0,0003 × 1.404.269 = 421,2807` → arredondado, **421 casos/semana**.
- Epidemia, 50,0 por 100 mil:
  `(50,0 / 100.000) × 1.404.269 = 0,0005 × 1.404.269 = 702,1345` → arredondado, **702 casos/semana**.

⚠️ **Ressalva declarada no próprio plano.** O documento **nunca escreve explicitamente** que a base da
taxa é "por 100 mil habitantes" — essa é a convenção nacional para indicadores de incidência de doenças, e
foi assumida por inferência, não lida literalmente no texto. Se a base fosse outra, os três números de
casos por semana mudariam proporcionalmente.

Para comparação, a convenção usada até aqui neste projeto — **100 casos/semana** como limiar de "surto" —
fica **abaixo até do teto do estágio Normalidade** (140). Ou seja: o critério de 100 casos, sem
correspondência oficial, é **mais sensível** (dispara mais cedo, com menos casos) do que qualquer patamar
do plano municipal.

---

## 7.4 A simplificação declarada: o que fica de fora ao usar só o número fixo

### 7.4.1 O critério oficial completo não é um número sozinho

🔴 **Este é o ponto mais importante desta seção, e precisa ser dito sem meias-palavras: o número fixo do
Quadro 1 nunca aparece isolado no plano municipal.** Em todo estágio, o corte numérico vem ligado por um
**E** lógico a uma segunda condição, baseada em duas curvas que o plano chama de **Limite de Alerta (LA)**
e **Limite Superior Endêmico (LSE)**.

O texto literal do critério de Epidemia, copiado do documento, mostra a estrutura:

> *"acima do LSE nas últimas 4SE **E** taxa de incidência de casos confirmados acima de 50,0 em pelo menos
> uma das 4SE"*

("4SE" abrevia "4 semanas epidemiológicas" — a semana epidemiológica é a unidade de tempo padrão da
vigilância em saúde, que numera as semanas do ano de forma consistente entre países e permite comparar
o mesmo período em anos diferentes.)

O critério de Alerta segue a mesma estrutura de duas condições combinadas: incidência entre o LA e o LSE
em pelo menos 3 das últimas 4 semanas **E** incidência acima de 30,0 por 100 mil em pelo menos 1 delas —
ou, alternativamente, óbito confirmado ou sorotipo novo.

### 7.4.2 O que são o Limite de Alerta e o Limite Superior Endêmico

- **Limite Superior Endêmico (LSE):** definido no plano como a **média móvel da incidência de casos
  prováveis, somada a dois desvios-padrão**, calculada sobre a série do **Rio Grande do Sul inteiro** — o
  Estado, não o município. Uma "média móvel" é a média calculada sobre uma janela de tempo que desliza
  junto com o calendário (por exemplo, a média das últimas 12 semanas, recalculada a cada semana nova); um
  "desvio-padrão" é uma medida de o quanto os valores tipicamente se afastam dessa média. Somar dois
  desvios-padrão à média é uma forma comum de definir "acima do que normalmente se observa".
- **Limite de Alerta (LA):** definido como uma curva **45% abaixo** do LSE.
- **Casos prováveis** ≠ **casos confirmados.** O plano usa duas definições de caso diferentes dentro do
  mesmo Quadro 1: os cortes fixos de 10,0 · 30,0 · 50,0 são sobre casos **confirmados** (com exame
  laboratorial ou critério clínico-epidemiológico fechado); o LA e o LSE são sobre casos **prováveis**
  (notificações que ainda não passaram por essa confirmação). Isso significa que o critério oficial mistura
  duas fontes de contagem com volumes tipicamente diferentes — prováveis costumam superar confirmados.

### 7.4.3 O que este projeto usa, e o viés que isso introduz

Este projeto **não possui** as séries de casos prováveis do Rio Grande do Sul necessárias para calcular o
LA e o LSE. Por isso, a simplificação adotada aqui usa **apenas a metade fixa do critério** — o corte de
incidência sobre confirmados (140 · 421 · 702) — e **descarta** a segunda condição (posição frente ao
LA/LSE), assim como os gatilhos por óbito e por sorotipo novo.

**Isso precisa ser dito com todas as letras: nossa versão do critério é mais fraca do que a oficial, e o
viés tem direção conhecida.** O raciocínio é puramente lógico, e não depende de nenhum dado: quando uma
condição definida por "A **E** B" é substituída por apenas "A", a nova condição é satisfeita em **todo**
caso em que a condição completa também é satisfeita, mais em qualquer caso adicional em que A é
verdadeiro mas B não é. Uma condição com uma exigência a menos nunca é mais rígida que a original — ela é
igual ou mais permissiva.

**Consequência prática: a versão usada aqui dispara "Alerta" ou "Epidemia" em pelo menos tantas semanas
quanto o critério oficial completo dispararia — e possivelmante em mais.** Não é possível quantificar
exatamente quantas semanas a mais, porque os dados de casos prováveis do Estado não estão disponíveis a
este projeto — mas a direção do viés é uma consequência da lógica proposicional, não uma suposição.

---

## 7.5 Por que o canal endêmico clássico não serve em Porto Alegre

### 7.5.1 O que é um canal endêmico

Um **canal endêmico** é um método clássico de vigilância epidemiológica: usa-se o histórico de anos
anteriores de uma doença para definir uma faixa de "normalidade" — tipicamente a média histórica mais ou
menos um múltiplo do desvio-padrão, calculada semana a semana do calendário. Quando a contagem da semana
corrente ultrapassa o teto dessa faixa, considera-se que há um sinal de alerta ou epidemia. É a mesma
lógica de fundo do método de Porto Rico (item 7.2) e do **MEM** ("Moving Epidemic Method", Método da
Epidemia Móvel), usado pela plataforma brasileira **InfoDengue** (uma parceria entre a Fiocruz e outras
instituições que publica boletins semanais de risco de dengue por município).

**O mecanismo central, e por que ele falha numa cidade onde a doença é nova:** qualquer canal endêmico
calculado por média e desvio-padrão depende de ter, na sua janela de referência, anos **sem** epidemia —
são eles que ancoram o que é "normal". Numa cidade onde a dengue está em expansão, e onde os anos
recentes já são epidemicamente ativos, essa suposição falha de duas formas diferentes, medidas abaixo.

### 7.5.2 Falha 1 — o canal fica em zero quando o histórico é quase todo zero

**FATO (medido em 25/09/2026, análise `2026-09-25_alarme_contra_canal_endemico`).** Entre 2018 e 2021,
Porto Alegre teve poucos casos de dengue na maior parte do ano — um período fora de temporada em que a
contagem semanal ficava perto de zero. Um canal endêmico calculado sobre esses anos produz, por
consequência aritmética, um **limite superior igual a zero** em muitas semanas do calendário.

O caso concreto: **na semana epidemiológica 39 de 2024, com 7 casos confirmados, o limite do canal
endêmico (calculado sobre 2018-2021) era 0.** Como qualquer contagem positiva ultrapassa zero, **qualquer
semana com pelo menos 1 caso** seria classificada como "acima do canal" — o método perde a capacidade de
distinguir uma semana normal de uma semana de alerta, porque a própria definição de "normal" (histórico
quase sem casos) já não corresponde à realidade da cidade.

### 7.5.3 Falha 2 — o corte sobe junto com as próprias epidemias que deveria detectar

**FATO (medido em 25/09/2026, análise `2026-09-25_limiar_oficial_de_surto`, a partir dos dados públicos
do InfoDengue para Porto Alegre, 857 semanas entre 2010 e 2026).** O InfoDengue classifica cada semana em
três faixas de incidência — baixa, média e alta — usando o método MEM, recalculado sobre o histórico
recente. O corte entre "baixa" e "média" incidência, medido em **número de casos por semana**, mudou assim
ao longo dos anos:

| Período | Corte "baixa → média" (casos/semana) |
|---|---|
| 2010–2021 (típico) | **6** |
| 2022 | 8 |
| 2023 | 14 |
| 2024 | 36 a 47 |
| 2025 | **94** |

O corte que separa "baixa" de "alta" incidência subiu de **6 para 94 casos por semana entre 2010-2021 e
2025** — um aumento de mais de 15 vezes.

**O mecanismo, por trás dos dois números:** o MEM (e qualquer canal endêmico recalculado sobre uma janela
móvel) redefine "normal" usando os anos mais recentes da própria janela. Quando esses anos recentes
incluem epidemias grandes (2022 a 2025), a média histórica sobe, e o que antes seria classificado como
"alto" passa a ser classificado como "normal" apenas porque já ocorreu antes, recentemente. **O método
normaliza a epidemia quando a doença é nova na cidade**: no começo, ele é permissivo demais (falha 1,
porque não há histórico de epidemia); depois de alguns anos de epidemia, ele volta a ser permissivo demais
(falha 2, porque a epidemia virou parte do próprio histórico de referência). Em nenhum momento intermediário
o método produz um corte estável e interpretável para uma cidade em expansão epidemiológica recente.

**Conclusão desta subseção.** É por essa falha, medida em dois pontos distintos da série (não uma
suposição teórica), que este projeto não usa o canal endêmico clássico — nem o InfoDengue/MEM, nem uma
reprodução do método de Porto Rico — como fonte do limiar de alarme, e prefere o corte fixo do plano
municipal (item 7.3), apesar da simplificação declarada no item 7.4.

---

## 7.6 A fundamentação matemática de usar a previsão como alarme

### 7.6.1 O que o modelo prevê, exatamente

O cenário adotado deste projeto usa o algoritmo `HistGradientBoostingRegressor`, da biblioteca
`scikit-learn`, treinado com **perda quantílica** no **quantil 0,85**. Dois conceitos precisam ser
definidos aqui, e ambos são retomados com mais profundidade na Parte 2 deste documento — a definição
abaixo é a necessária para entender o argumento desta seção.

- **Quantil.** Dado um número entre 0 e 1 — chamado de τ (letra grega tau) —, o quantil τ de uma
  distribição de probabilidade, escrito q_τ, é o valor que satisfaz `P(X ≤ q_τ) = τ`: a probabilidade de
  a variável aleatória X (aqui, o número de casos de dengue numa semana futura) ser menor ou igual a q_τ
  é exatamente τ. Por definição, também vale que `P(X > q_τ) = 1 − τ` — a probabilidade de superar o
  quantil é o complemento de τ.
- **Perda quantílica.** É a função que o algoritmo de aprendizado de máquina minimiza durante o
  treinamento para aprender a prever um quantil específico, em vez da média (que é o que a maioria dos
  modelos de regressão prevê por padrão). Treinar com perda quantílica em τ = 0,85 significa pedir ao
  modelo que aprenda a estimar, para cada semana, o valor **q̂₀,₈₅** — sua melhor estimativa do quantil
  85% da distribuição de casos futuros, dadas as variáveis de entrada daquela semana (o acento circunflexo,
  "^", indica que é uma estimativa produzida pelo modelo, não o valor verdadeiro e desconhecido).

Por construção, se o modelo estivesse perfeitamente calibrado, apenas 15% das semanas reais teriam um
número de casos **acima** de q̂₀,₈₅ — o modelo é desenhado para, propositalmente, "errar para cima" com
mais frequência do que "errar para baixo", 85% contra 15% das vezes.

### 7.6.2 A regra de alarme, e onde ela mistura dois parâmetros que deveriam ser distintos

O alarme atual do projeto compara a previsão do modelo — que já é q̂₀,₈₅, o quantil 85 — contra o mesmo
número que define o **evento de interesse** (por exemplo, 100 casos, ou 421 casos no estágio Alerta). Isso
está escrito, literalmente, na linha **564** do script `rodar.py` da análise `2026-09-25_alarme_contra_canal_endemico`
(a pré-declaração da análise de 26/09/2026 cita esta mesma linha como 565; a diferença de uma linha, entre
o número citado na pré-declaração e o que este documento conferiu diretamente no arquivo, é registrada
aqui como uma pequena divergência de citação, sem consequência sobre o argumento):

```python
alarme_m_adotado = tabela["previsto_M_adotado"] > definicao_evento.limite_alvo
```

Isto é: o alarme dispara quando a previsão (`previsto_M_adotado`, que é q̂₀,₈₅) ultrapassa `limite_alvo` —
o mesmo número, por exemplo 421, que define o próprio evento de interesse ("a semana teve mais de 421
casos reais").

**Aqui estão dois parâmetros que a literatura de classificação binária trata como distintos, e que este
projeto, sem que ninguém tivesse decidido isso explicitamente, colou um no outro:**

- o **limiar do evento** (T): o que conta como "verdade" — quantos casos reais precisam ocorrer para a
  semana ser rotulada como surto. É uma definição do problema, e vem do plano municipal (item 7.3).
- o **limiar de decisão** (D): o valor que a previsão do modelo precisa ultrapassar para o alarme soar. É
  um parâmetro do classificador, livre para ser ajustado — pode ser mais alto, mais baixo, ou igual ao
  limiar do evento.

Hoje, **D = T** por construção do código, não por uma escolha deliberada e justificada. A seção 7.7 mostra
o que acontece quando essa igualdade é testada.

### 7.6.3 A leitura probabilística: o que "D = T" significa, e o que ele não significa

Como q̂₀,₈₅ é definido por `P(X ≤ q̂₀,₈₅) = 0,85`, e a função de distribuição acumulada (a função F(x) que
dá a probabilidade de X ser menor ou igual a x) é crescente, vale a seguinte cadeia de implicações sempre
que a previsão ultrapassa o limiar D:

```
q̂₀,₈₅ > D
  ⟹  F(D) < F(q̂₀,₈₅) = 0,85          (F é crescente, e D é menor que q̂₀,₈₅)
  ⟹  P(X > D) = 1 − F(D) > 1 − 0,85 = 0,15
```

Em palavras: **sempre que o alarme dispara, o modelo, implicitamente, está afirmando que a chance de a
semana real ultrapassar D é maior que 15%** — não exatamente 15%, apenas maior que 15%. O valor 15% não
foi escolhido por ninguém como "o corte de risco que dispara o alarme"; ele é uma consequência aritmética
de ter escolhido treinar no quantil 0,85, uma decisão tomada por outro motivo (superestimar picos com mais
frequência do que subestimá-los, ver Parte 4).

**Um exemplo numérico completo.** Suponha que, numa certa semana, o modelo produza a previsão
`q̂₀,₈₅ = 550` casos para um horizonte de 12 semanas à frente, e o limiar do evento Alerta seja
`D = 421`. Como `550 > 421`, o alarme dispara. Pela cadeia lógica acima, isso equivale a dizer que o
modelo estima que há **mais de 15% de chance** de a semana real, quando chegar, ter mais de 421 casos.
Se, em vez disso, o modelo tivesse previsto `q̂₀,₈₅ = 300` para a mesma semana, `300 < 421`, o alarme não
dispararia — o que equivale a dizer que o modelo estima uma chance **igual ou menor que 15%** de
ultrapassar 421 casos.

⚠️ **A ressalva que precisa acompanhar esta leitura sempre que ela for citada.** O "mais de 15%" acima é
**nominal** — é o que a matemática do quantil 0,85 implica **se o modelo estiver calibrado**, isto é, se
suas estimativas de quantil realmente correspondessem às proporções reais observadas. A calibração do
cenário adotado foi medida em 26/09/2026 (análise `2026-09-26_calibracao_por_faixa`), e o resultado, na
faixa de casos que mais importa para este alarme, é o oposto de calibrado: nas semanas em que o número
real de casos ficou **acima de 421** (o próprio estágio Alerta), o intervalo de 90% de confiança do
modelo — que deveria conter o valor real em 90% das semanas, se estivesse bem calibrado — conteve o valor
real em apenas **17,8%** delas. Isso significa que a chance real de superar um limiar, nas semanas de
maior risco, tende a ser **muito maior** do que os "15% nominais" sugerem — o modelo subestima a
magnitude dos picos nessa faixa, um viés sistemático medido e discutido na Parte 8, não um erro aleatório
que se cancela em média.

### 7.6.4 Por que isso importa para o resto da seção

A distinção entre limiar de decisão e limiar de evento, e a constatação de que o modelo tende a
**subestimar** (não superestimar) a magnitude dos picos mais extremos, preparam o terreno para o resultado
da subseção seguinte: quando o limiar de decisão é afastado do limiar de evento e testado livremente, ele
não se comporta como a intuição do quantil 0,85 sugeriria.

---

## 7.7 A varredura do limiar de decisão de 26/09/2026

### 7.7.1 O desenho da rodada

Em 26/09/2026, com autorização do Vinicius ("pode rodar alguma coisa se precisar"), foi feita uma
**varredura** — um teste sistemático de vários valores candidatos — do limiar de decisão D, mantendo fixo
o limiar do evento (T = 421, o piso do estágio Alerta). Para cada um dos dois modelos avaliados
(`M_adotado`, o cenário descrito no item 7.6.1, e `M_folha20`, uma variação de hiperparâmetro com folha
mínima 20) e cada um dos quatro horizontes de previsão (1, 4, 8 e 12 semanas à frente), o valor de D foi
testado em uma grade de doze candidatos: 25, 50, 75, 100, 140, 200, 300, 421, 600, 702, 900 e 1.200 casos.

Para cada combinação de (modelo, horizonte, D), foram calculadas cinco métricas — sensibilidade,
especificidade, precisão, falsos alarmes por ano e o índice de Youden — cujas definições e um exemplo
numérico completo aparecem no item 7.8.2, adiante, porque é ali que os números ficam mais fáceis de
seguir com um caso concreto.

A pré-declaração escrita **antes** da rodada continha uma previsão testável, derivada diretamente do
raciocínio do item 7.6: **como o quantil 0,85 é desenhado para superestimar** (prever acima do valor real
em 85% das vezes, por construção), **o melhor valor de D — aquele que maximiza o índice de Youden — deveria
ficar ACIMA de T = 421**, porque a previsão, tendendo a vir alta, precisaria de um bar mais alto antes de
disparar o alarme com confiança.

### 7.7.2 O resultado: a previsão se confirma só no horizonte mais curto

| Modelo | Horizonte | D de melhor Youden | A previsão (D > 421) se confirma? |
|---|---|---|---|
| `M_adotado` | 1 semana | 600 | ✅ sim |
| `M_adotado` | 4 semanas | 421 | 🔴 não (empata no próprio 421, não fica acima) |
| `M_adotado` | 8 semanas | 200 | 🔴 não |
| `M_adotado` | 12 semanas | 50 | 🔴 não |
| `M_folha20` | 1 semana | 600 | ✅ sim |
| `M_folha20` | 4 semanas | 300 | 🔴 não |
| `M_folha20` | 8 semanas | 300 | 🔴 não |
| `M_folha20` | 12 semanas | 100 | 🔴 não |

**FATO (medido e certificado de forma independente em 26/09/2026, análise
`2026-09-26_varredura_limiar_de_decisao`; a certificação reproduziu, célula a célula, três pontos
escolhidos pelo próprio certificador, com resultado idêntico ao do executor).**

A previsão declarada se confirma **apenas no horizonte de 1 semana**. Em 4, 8 e 12 semanas, o melhor
valor de D fica **abaixo** de 421 — em alguns casos, muito abaixo (50 casos, para o `M_adotado` em 12
semanas, contra um evento definido em 421).

### 7.7.3 O que isso revela: o modelo subestima, não superestima, nos horizontes longos

Sem suavizar: a leitura de que "o modelo tende a prever para cima, então o alarme deveria exigir uma
previsão bem alta antes de disparar" **só se sustenta na semana seguinte**. A partir de um mês de
antecedência, o padrão medido é o oposto — um limiar de decisão **mais baixo** que o evento captura mais
semanas de surto real sem custar tantos falsos positivos a mais. Isso é consistente com o viés de
subestimação de picos já apontado no item 7.6.3 (cobertura de apenas 17,8% acima de 421 casos): se o
modelo tende a prever abaixo do que realmente acontece nas semanas de pico, esperar que ele ultrapasse o
próprio limiar do evento antes de alarmar é pedir um sinal que, nesses horizontes, ele frequentemente não
chega a dar — mesmo em semanas que de fato serão de surto.

### 7.7.4 Por que nenhum valor de D foi adotado

🚫 **Nenhum corte de decisão foi adotado a partir desta varredura, por proibição explícita da
pré-declaração.** O motivo é um risco estatístico chamado de **garimpagem de hipóteses** (em inglês,
*data dredging* ou *p-hacking*): quando se testam muitos valores candidatos e se escolhe, depois, o
melhor resultado entre eles para apresentar como "o achado", o valor que parece melhor pode ser apenas o
que teve mais sorte na amostra específica testada — sem correção estatística para o número de candidatos
avaliados, esse melhor resultado tende a parecer mais forte do que realmente é.

A pré-declaração de 26/09/2026 registrou este risco antes de calcular qualquer número, e determinou que a
Parte A da rodada (a varredura) é **descritiva**: produz uma curva de sensibilidade contra falsos
alarmes, não um vencedor. Um valor de D só pode virar resultado confirmatório numa rodada futura, sobre
uma temporada nova de dados — nunca escolhido a posteriori sobre os mesmos dados em que foi testado.

---

## 7.8 O resultado do alarme no estágio Alerta

### 7.8.1 O desenho do teste confirmatório

Diferente da varredura (descritiva), o teste do alarme no evento **E_421** (definido como: a semana real
teve mais de 421 casos confirmados — o piso do estágio Alerta do plano municipal) foi **pré-declarado como
confirmatório** em 26/09/2026, antes de qualquer número ser calculado. O critério de sucesso, escrito
antes da rodada, foi: **o modelo só conta como ganho se vencer a régua "o ano passado passou de 421" em
índice de Youden, com significância estatística após correção de múltiplas comparações (p de Holm menor
que 0,05).** Vencer apenas a régua mais fraca ("hoje já passou de 421") não conta como ganho — esse
resultado mais fraco já havia sido mostrado em 25/09/2026, e por si só não justifica o alarme como
instrumento.

Os testes estatísticos usados — o teste de McNemar e a correção de Holm — são definidos com exemplo
numérico completo no item 7.8.2. O índice de Youden é definido, também com exemplo numérico, no item
7.8.3.

### 7.8.2 O teste de McNemar e a correção de Holm, definidos com um exemplo

**Teste de McNemar.** É um teste estatístico para comparar **duas regras binárias avaliadas sobre os
mesmos pares de observação** — aqui, duas regras de alarme (por exemplo, o modelo contra a régua "o ano
passado") avaliadas nas mesmas semanas. O teste ignora as semanas em que as duas regras concordam (ambas
alarmam, ou nenhuma alarma) e olha só para as semanas **discordantes** — onde uma regra alarma e a outra
não. Se as duas regras fossem igualmente boas, a discordância deveria se dividir, em média, meio a meio
entre "regra A acerta e B erra" e "regra B acerta e A erra". O teste calcula a probabilidade (o
**p-valor**) de observar uma divisão tão desigual quanto a observada, ou mais desigual, **se as duas
regras fossem de fato igualmente boas** (essa suposição de igualdade é chamada de **hipótese nula**). Um
p-valor pequeno é evidência de que a divisão observada dificilmente aconteceria só por acaso, e portanto
uma das regras é realmente melhor que a outra.

**Exemplo numérico completo, com dados reais deste projeto (comparação de 25/09/2026, evento de 100
casos, horizonte de 4 semanas, `M_adotado` contra "hoje já passou de 100"):** houve **15 semanas
discordantes**, divididas **13 a 2** (em 13 delas o modelo acertou e a régua errou; em 2, o inverso). Sob a
hipótese nula de que as duas regras são igualmente boas, o número de vezes que "o modelo acerta e a régua
erra" segue uma distribuição binomial com 15 tentativas e probabilidade 0,5 em cada uma. A probabilidade
de uma divisão tão desigual quanto 13 a 2 (ou mais desigual ainda) **para qualquer um dos dois lados** é:

```
P(K ≤ 2 | n=15, p=0,5) = [C(15,0) + C(15,1) + C(15,2)] / 2^15
                       = (1 + 15 + 105) / 32.768
                       = 121 / 32.768 ≈ 0,003693

p (bruto, teste de duas caudas) = 2 × 0,003693 ≈ 0,0074
```

("C(n,k)" é o número de combinações de n itens tomados k a k — de quantas formas diferentes se pode
escolher k semanas discordantes entre as 15, sem importar a ordem.)

Este é o **p-valor bruto**, calculado como se esta fosse a única comparação feita no projeto. Mas este
projeto fez **muitas** comparações — 24, ao todo, somando as 16 abertas em 25/09/2026 às 8 novas do evento
E_421 em 26/09/2026 — e cada comparação adicional aumenta a chance de que **pelo menos uma** pareça
significativa só por acaso, mesmo que nenhuma seja real. É esse problema que a correção de Holm resolve.

**Correção de Holm.** Diante de uma família de m testes, ordenam-se todos os p-valores brutos do menor
para o maior: p₍₁₎ ≤ p₍₂₎ ≤ ... ≤ p₍ₘ₎. Compara-se p₍₁₎ contra α/m (onde α, tipicamente 0,05, é o nível de
significância desejado para a família inteira); se passar, compara-se p₍₂₎ contra α/(m−1); e assim por
diante, cada vez com um divisor menor, até que um teste **não** passe — a partir daí, nenhum dos testes
seguintes (com p-valores ainda maiores) é considerado significativo, mesmo que algum, isoladamente,
parecesse pequeno.

**Exemplo didático da mecânica, com números simplificados (não são os do projeto — servem só para mostrar
o procedimento):** numa família de 4 testes com p-valores brutos 0,01, 0,02, 0,03 e 0,04, ordenados, e
α = 0,05: o primeiro é comparado contra 0,05/4 = 0,0125 (passa, 0,01 < 0,0125); o segundo contra 0,05/3 ≈
0,0167 (passa, 0,02 < 0,0167); o terceiro contra 0,05/2 = 0,025 (**não passa**, 0,03 > 0,025) — a partir
daqui, o terceiro e o quarto teste são considerados não significativos, mesmo que 0,04 (o quarto) seja um
p-valor que, sozinho, muitas pessoas considerariam "quase significativo".

**De volta ao número real do projeto:** o p-valor bruto de ≈0,0074 calculado acima, depois de passar pela
correção de Holm dentro da família de 24 testes, tornou-se **p de Holm = 0,103** — um fator de
multiplicação de aproximadamente 14 vezes sobre o valor bruto, compatível com este teste ocupar uma
posição intermediária na fila ordenada dos 24 p-valores da família. **0,103 é maior que 0,05: esta
comparação específica não é considerada estatisticamente significativa**, mesmo o resultado bruto
parecendo forte (13 vitórias contra 2 derrotas) antes da correção.

### 7.8.3 O índice de Youden, definido com um exemplo numérico

O **índice de Youden** resume, num único número entre −1 e 1, a qualidade de um classificador binário
(como o alarme), combinando duas taxas:

- **sensibilidade** = (semanas de surto real corretamente alarmadas) / (total de semanas de surto real).
  Mede a capacidade de **não deixar passar** um surto verdadeiro.
- **especificidade** = (semanas sem surto corretamente não alarmadas) / (total de semanas sem surto).
  Mede a capacidade de **não alarmar à toa**.

```
Youden = sensibilidade + especificidade − 1
```

Um Youden de 1 é um classificador perfeito; um Youden de 0 significa desempenho equivalente a jogar uma
moeda; um Youden negativo significa desempenho **pior** que o acaso.

**Exemplo numérico completo, com dados reais deste projeto** (varredura de 26/09/2026, `M_adotado`,
horizonte de 4 semanas, exatamente no ponto D = 421, que é a regra de hoje): sensibilidade = **1,000**
(o modelo alarmou em 100% das semanas que de fato tiveram mais de 421 casos), especificidade = **0,960**
(o modelo corretamente não alarmou em 96,0% das semanas que ficaram abaixo de 421 casos). Logo:

```
Youden = 1,000 + 0,960 − 1 = 0,960
```

Um Youden de 0,960, isoladamente, é um número alto — mas, como mostra a subseção seguinte, um Youden alto
não é, sozinho, suficiente para declarar vitória sobre a régua de comparação, porque a régua também tem
Youden alto neste mesmo evento, e a diferença entre os dois precisa passar pelo teste estatístico do item
7.8.2 para ser considerada real.

### 7.8.4 O resultado, sem suavizar: 0 de 4 combinações vencem a régua sazonal

| Modelo | Horizonte | Youden do modelo | Youden de "o ano passado" | Vence em Youden bruto? | p de Holm | Conta como ganho pré-declarado? |
|---|---|---|---|---|---|---|
| `M_adotado` | 4 semanas | 0,960 | 0,727 | sim | 1,000 | 🔴 **não** |
| `M_folha20` | 4 semanas | 0,920 | 0,727 | sim | 1,000 | 🔴 **não** |
| `M_adotado` | 12 semanas | 0,393 | 0,736 | **não** | 0,204 | 🔴 **não** |
| `M_folha20` | 12 semanas | 0,473 | 0,736 | **não** | 0,148 | 🔴 **não** |

**FATO (medido e certificado de forma independente em 26/09/2026; a certificação refez, do zero, os 8
testes de McNemar e a correção de Holm sobre a família combinada de 24 testes, reproduzindo cada uma das
24 linhas com diferença de arredondamento da ordem de 10⁻¹⁶).**

**Nenhuma das quatro combinações relevantes vence a régua "o ano passado passou de 421" com significância
estatística — 0 de 4.** Em 4 semanas de antecedência, os dois modelos até superam a régua no Youden bruto
(0,960 e 0,920 contra 0,727), mas o teste de McNemar não encontra evidência estatística de que essa
diferença seja real: o p de Holm fica em **1,000**, o valor máximo possível, o que significa que a
amostra de semanas discordantes entre modelo e régua é pequena demais (9 e 12 pares, respectivamente) para
que qualquer diferença, por maior que pareça, seja distinguível do acaso depois da correção para múltiplas
comparações. Em 12 semanas de antecedência, a situação se inverte: os modelos **perdem** em Youden bruto
para a régua (0,393 e 0,473 contra 0,736).

**A causa de fundo, que atravessa todo o documento (Aviso 1 da Parte 0): o período avaliado contém apenas
dois episódios de surto genuinamente independentes — um em 2024, um em 2025.** Qualquer teste pareado
sobre esse período tem poder estatístico limitado, porque o número de eventos verdadeiramente
independentes é muito menor do que o número de semanas na tabela. Um Youden bruto alto pode refletir um
efeito real, mas também pode refletir o modelo aprendendo o calendário de duas temporadas específicas — a
diferença só fica clara quando o teste estatístico, com a correção adequada, é aplicado, e é exatamente
isso que os p de Holm acima mostram.

**Este resultado é reportado exatamente como saiu, sem abrandamento, por decisão pré-declarada em
26/09/2026: mesmo que o alarme repetisse a derrota de 3 meses já registrada contra a régua sazonal em
25/09/2026, o resultado seria publicado.** É o que aconteceu.

---

## 7.9 A alternativa que a literatura oferece, e que ainda não foi testada aqui

### 7.9.1 A regra de aceleração de transmissão

**HIPÓTESE (fonte na literatura, não testada com os dados deste projeto).** Um artigo lido na íntegra em
26/09/2026 (repositório público PMC13228775) descreve e testa, em oito países diferentes (incluindo
Singapura), uma regra de alarme diferente do canal endêmico clássico, chamada aqui de **aceleração de
transmissão**. A regra:

```
razão = (média móvel das últimas 4 semanas) / (média móvel das últimas 26 semanas)
alarme dispara quando razão > 1,33
```

Uma **média móvel** de 4 semanas, numa certa semana, é a média do número de casos daquela semana e das 3
anteriores; a de 26 semanas é a média das 26 semanas mais recentes (aproximadamente meio ano). A razão
entre as duas mede **aceleração**, não nível absoluto: ela sobe quando o número de casos recente está
crescendo mais depressa do que a média de mais longo prazo sugeriria, independentemente de o número
absoluto de casos ser alto ou baixo. Essa é a diferença central frente ao canal endêmico (item 7.5), que
mede nível contra um histórico de referência, e por isso herda os problemas de precisar de anos calmos.

**FATO (do artigo, medido nos 8 países testados).** Contra o canal endêmico clássico, a regra de
aceleração teve:

| Métrica | Aceleração de transmissão | Canal endêmico clássico |
|---|---|---|
| Sensibilidade | **100%** | 30% |
| Antecedência média (semanas antes do pico) | **6,9** | 1,6 |

"Antecedência", aqui, é quantas semanas **antes** do pico epidêmico a regra já estava sinalizando alarme —
quanto maior, mais tempo de reação a saúde pública tem disponível.

### 7.9.2 Por que essa regra é candidata, e por que ainda não é resultado

**A razão de interesse para Porto Alegre:** a regra de aceleração precisa de apenas **26 semanas** de
histórico — cerca de 6 meses — para ser calculada, não de anos. Isso a livra, em princípio, do mesmo
problema que invalidou o canal endêmico e o método de Porto Rico na cidade (item 7.5): não depende de
anos calmos de referência, porque não compara nível contra história — compara a série contra ela mesma, em
duas janelas de tempo diferentes.

**Um exemplo numérico, calculado agora diretamente sobre a tabela de dados deste projeto**, apenas para
ilustrar o mecanismo da fórmula — **este cálculo é exploratório, feito para esta seção, e não é um
resultado certificado do projeto**, que continua exigindo pré-declaração escrita antes de qualquer teste
formal desta regra:

| Semana (início) | Casos confirmados | Média móvel 4 semanas | Média móvel 26 semanas | Razão |
|---|---|---|---|---|
| 07/01/2024 | 11 | 8,25 | 8,19 | 1,01 |
| 14/01/2024 | 12 | 10,50 | 7,42 | **1,41** |
| 21/01/2024 | 30 | 15,50 | 7,62 | 2,04 |
| 28/01/2024 | 39 | 23,00 | 8,54 | 2,69 |
| 04/02/2024 | 80 | 40,25 | 10,92 | 3,68 |

Na semana de **14/01/2024**, a razão (1,41) já ultrapassava o corte de 1,33 — cerca de **3 semanas antes**
de a série atingir 80 casos/semana (04/02/2024) e mais de 4 semanas antes do pico da epidemia de 2024. Este
único exemplo é consistente, na direção, com a antecedência de 6,9 semanas medida nos 8 países do artigo,
mas **um único episódio não constitui medição**: é exatamente o tipo de observação de amostra pequena que
as diretrizes deste projeto proíbem transformar em conclusão documentada.

### 7.9.3 O precedente que exige cautela: uma regra importada já falhou aqui

⚠️ **Ressalva que precisa acompanhar qualquer menção futura à regra de aceleração.** Este projeto já
testou, em 25/09/2026, uma outra regra de alarme importada da literatura internacional — a da Malásia,
"a série está acima do canal endêmico E crescendo" — e ela foi, de todas as regras testadas naquela
rodada, **a pior**: índice de Youden de **−0,05** em 3 meses de antecedência, pior que jogar uma moeda. Os
próprios autores da regra da Malásia já alertavam, no artigo original, que ela poderia não se transferir
para outros contextos epidemiológicos.

**A consequência lógica para a regra de aceleração de transmissão:** o fato de ela ter funcionado bem em
8 países, incluindo Singapura, **não é garantia** de que funcione em Porto Alegre — o precedente da
Malásia é evidência direta, medida neste próprio projeto, de que regras importadas de vigilância podem não
transferir para a epidemiologia local da cidade. A regra de aceleração de transmissão entra neste
documento como **régua candidata a testar em rodada futura, com pré-declaração própria**, nunca como
método já adotado por citação da literatura.

---

## 7.10 Síntese da seção

- O projeto adota de Porto Rico o **conceito** de limiar de alerta operacional, não o **método** de
  cálculo (regressão binomial negativa sobre 38,5 anos de história) — Porto Rico tem década de série
  histórica calma que Porto Alegre não tem.
- Os números 140, 421 e 702 casos/semana vêm do **Plano Municipal de Contingência de Arboviroses 2026** da
  SMS-POA, convertidos da incidência oficial (10 · 30 · 50 por 100 mil habitantes) usando a população de
  **1.404.269**.
- 🔴 Essa conversão usa **apenas metade** do critério oficial: o corte fixo, sem a condição adicional
  sobre o Limite de Alerta e o Limite Superior Endêmico (curvas do Rio Grande do Sul), nem os gatilhos por
  óbito ou sorotipo novo. Logicamente, isso torna a versão usada aqui **igual ou mais permissiva** que o
  critério oficial completo — nunca mais restritiva.
- O canal endêmico clássico (e, por extensão, o método de Porto Rico) falha, medido em dois pontos
  diferentes: dá limite **zero** fora de temporada nos anos calmos (2018-2021) e sobe de **6 para 94
  casos/semana** entre 2010-2021 e 2025 conforme os próprios anos epidêmicos entram na janela de
  referência.
- A justificativa matemática de usar a previsão como alarme repousa na equivalência entre o quantil 0,85
  e uma leitura probabilística (`P(X>D) > 15%` sempre que o alarme dispara) — mas essa leitura é
  **nominal**, não calibrada: a cobertura real medida acima de 421 casos é de **17,8%**, não 90%, e o
  modelo tende a subestimar, não superestimar, nas semanas de pico.
- A varredura do limiar de decisão de 26/09/2026 confirmou a intuição do quantil 0,85 apenas em **1
  semana** de antecedência; em 4, 8 e 12 semanas, o melhor corte ficou **abaixo** do limiar do evento — e
  **nenhum** valor foi adotado, por proibição pré-declarada contra apresentar o "melhor" candidato de uma
  varredura como resultado.
- 🔴 No estágio Alerta (evento de 421 casos), **0 de 4 combinações** (2 modelos × 2 horizontes) vencem a
  régua "o ano passado" com significância estatística após a correção de Holm.
- A regra de **aceleração de transmissão** (razão entre médias móveis de 4 e 26 semanas, corte 1,33) é a
  alternativa mais promissora ainda não testada — não exige anos de histórico —, mas entra como candidata a
  pré-declarar, não como método adotado, porque uma regra importada já falhou em Porto Alegre antes (a da
  Malásia, Youden −0,05).

---

# Parte 8 — Os resultados, com tradução concreta

Esta seção mostra o que o modelo previsto acertou e errou, na avaliação feita entre **01/01/2024** e
aproximadamente **01/02/2026**, e — ponto central pedido pelo Vinicius — traduz cada número em uma
consequência prática. Um erro de "278,8 casos" ou uma "captura de pico de 0,388" não significam nada por
si só; a seção existe para explicar o que esses números fazem no mundo real, numa cidade de vigilância
epidemiológica.

Toda tabela citada aqui vem de uma pasta datada dentro de `analises/`, cada uma com seu próprio `README.md`
e, quando aplicável, sua pré-declaração e certificação adversarial (processo em que um segundo agente, sem
ver o resultado esperado, tenta reproduzir a medição do zero e apontar erros, em vez de só rodar o mesmo
código de novo). Os caminhos exatos aparecem ao lado de cada tabela.

---

## 8.1 O cenário adotado — o que está sendo medido, em uma frase

Antes de olhar números, é preciso saber o que é "o cenário adotado", porque todas as tabelas desta seção o
usam como referência principal.

- O algoritmo é o **`HistGradientBoostingRegressor`** da biblioteca `scikit-learn`, abreviado neste
  documento como **HistGB**. É um método de **boosting**: em vez de treinar uma única árvore de decisão
  para prever o número de casos, ele treina uma sequência de árvores pequenas, cada uma corrigindo o erro
  que a soma das árvores anteriores ainda comete. O resultado final é a soma das previsões de todas as
  árvores da sequência.
- A árvore não é treinada para acertar a **média** do número de casos, e sim um **quantil**. Um quantil é
  o valor abaixo do qual uma certa fração das observações cai — por exemplo, o quantil 0,85 é o valor que,
  numa distribuição de possibilidades, deixa 85% das observações abaixo dele e 15% acima. Treinar para o
  quantil 0,85 (em vez da média, quantil equivalente a 0,50) é uma escolha deliberada de ser **cauteloso
  para cima**: o modelo tenta ficar acima do valor real com mais frequência do que ficaria se mirasse a
  média, porque, para um sistema de alarme de saúde pública, errar por excesso de cautela (prever demais)
  é operacionalmente menos perigoso do que errar por escassez (prever de menos, subestimar uma epidemia).
  Uma parte importante desta seção (§8.4 e §8.5) mostra que, na prática, essa cautela **não é suficiente**
  para evitar subestimação sistemática nos picos.
- Os hiperparâmetros são as configurações do algoritmo que não são aprendidas dos dados, e sim escolhidas
  antes do treino. No cenário adotado: `max_iter` **250** (o número de árvores da sequência de boosting),
  `learning_rate` **0,05** (o quanto cada árvore nova corrige o erro da soma anterior — um valor baixo
  significa correções pequenas e uma sequência mais longa, o que costuma generalizar melhor para dados
  novos), `max_leaf_nodes` **15** (o número máximo de folhas — de decisões finais — que cada árvore
  individual pode ter, limitando a complexidade de cada árvore) e `min_samples_leaf` **5** (o número mínimo
  de semanas de treino que precisam cair numa folha para ela ser aceita, evitando que o modelo memorize
  casos isolados).
- A entrada tem **20 colunas**: 8 de núcleo (o histórico da própria série de casos e variáveis de
  sazonalidade, como a semana do ano), 6 de clima (temperatura, precipitação e variáveis correlatas obtidas
  via satélite) e 6 do vetor (a série de captura de mosquitos *Aedes aegypti* nas armadilhas do MI-Aedes em
  Porto Alegre).
- O alvo (a variável que o modelo tenta prever) é o número de **casos confirmados** de dengue por semana
  epidemiológica em Porto Alegre, contados pelo município de **notificação** (onde o caso foi registrado no
  sistema de saúde), não pelo município de **residência** do paciente — a diferença entre os dois é uma
  decisão de produto, não um detalhe técnico, e está registrada como tal em outra seção deste documento.
- **Horizonte de previsão**, abreviado **h** nas tabelas, é quanto tempo de antecedência a previsão tem: h=1
  é uma previsão feita 1 semana antes da semana que ela tenta prever, h=4 é feita 4 semanas antes (por
  isso tratado neste documento como "1 mês"), h=8 como "2 meses" e h=12 como "3 meses".

Com isso definido, os números das próximas seções passam a fazer sentido.

---

## 8.2 O erro pontual por horizonte

### 8.2.1 O que é o erro absoluto médio (MAE)

O **erro absoluto médio**, em inglês *mean absolute error*, abreviado **MAE**, mede o tamanho médio do erro
de previsão, sem se importar se o modelo errou para cima ou para baixo — ele usa o **valor absoluto** do
erro, que é a distância entre o previsto e o real, sempre positiva.

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|
$$

Onde:

- **$n$** é o número de semanas (pares real-previsto) avaliadas.
- **$y_i$** é o número real de casos confirmados na semana $i$.
- **$\hat{y}_i$** é o número de casos que o modelo previu para a semana $i$.
- **$|\cdot|$** é o valor absoluto: transforma qualquer número negativo em positivo, então um erro de "−50
  casos" (previu menos que o real) e um erro de "+50 casos" (previu mais que o real) contam igual, os dois
  como 50.

**Exemplo numérico, do começo ao fim** (didático — números redondos, só para mostrar o mecanismo; a
tradução com os números reais do painel vem logo depois): imagine 4 semanas com real e previsto assim —
semana A: real 11, previsto 34; semana B: real 32, previsto 8; semana C: real 194, previsto 40; semana D:
real 494, previsto 384. Os erros absolutos são $|11-34|=23$, $|32-8|=24$, $|194-40|=154$ e $|494-384|=110$.
A soma é $23+24+154+110=311$, e o MAE é $311 \div 4 = 77{,}75$. Este exemplo, aliás, não é inventado: é uma
amostra real de 4 semanas certificadas do projeto (h=12, mediana prevista, período 2024-2025), calculada
por [`analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`](../../analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv)
— só que ali usa-se a previsão da mediana (quantil 0,50), não do quantil 0,85 do cenário adotado, por isso
o valor (77,75) não deve ser confundido com o **278,8** do painel oficial abaixo, que usa 284 semanas e o
quantil 0,85.

### 8.2.2 O que é o coeficiente de determinação (R²)

O **coeficiente de determinação**, chamado de **R²**, mede que fração da variação do número real de casos
o modelo consegue explicar, comparado com o erro que se teria só "chutando a média" da série toda para
todas as semanas.

$$
R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}
$$

Onde:

- **$\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$** é a soma dos erros do modelo, ao quadrado (essa soma tem nome
  próprio, soma dos quadrados dos resíduos).
- **$\sum_{i=1}^{n}(y_i - \bar{y})^2$** é a soma da distância de cada semana real até a média de todas as
  semanas reais ($\bar{y}$), ao quadrado (soma dos quadrados totais) — é o erro de um modelo ingênuo que
  sempre prevê a média.
- $R^2 = 1$ significa acerto perfeito; $R^2 = 0$ significa que o modelo é tão bom quanto prever sempre a
  média da série; **$R^2$ negativo** significa que o modelo é **pior** do que simplesmente prever a média
  — acontece quando o modelo erra sistematicamente numa direção com mais força do que a própria variação
  natural dos dados.

**Exemplo numérico, com os mesmos 4 pontos de cima:** a média dos 4 valores reais é
$\bar{y} = (11+32+194+494)/4 = 182{,}75$. A soma dos quadrados totais é
$(11-182{,}75)^2+(32-182{,}75)^2+(194-182{,}75)^2+(494-182{,}75)^2 = 29.498{,}1+22.725{,}6+126{,}6+96.876{,}6
= 149.226{,}75$. A soma dos quadrados dos erros do modelo é
$23{,}44^2+24{,}08^2+154{,}14^2+110{,}35^2 = 549{,}4+579{,}8+23.759{,}1+12.177{,}1 = 37.066{,}1$. O R² é
$1 - 37.066{,}1/149.226{,}75 = 1 - 0{,}2484 = 0{,}7516$. Nesta pequena amostra de 4 semanas, o modelo
explicaria **75,2%** da variação — bem acima do 0,437 medido no painel oficial completo (§8.2.3), porque
uma amostra de 4 semanas escolhidas ao acaso tende a produzir números instáveis; é exatamente por isso
que o painel oficial usa **284 a 295 pares**, não 4.

### 8.2.3 O painel de erro do cenário adotado

Avaliação de **01/01/2024** a aproximadamente **01/02/2026**:

| Horizonte | Pares avaliados ($n$) | Erro absoluto médio (MAE) | Coeficiente de determinação (R²) |
|---|---|---|---|
| 1 semana | **102** | **98,0** | **0,898** |
| 4 semanas (1 mês) | **102** | **219,7** | **0,628** |
| 8 semanas (2 meses) | **102** | **272,6** | **0,450** |
| 12 semanas (3 meses) | **102** | **278,8** (painel publicado: 278,7) | **0,437** |

Um "par" é uma semana em que existe tanto um valor real de casos confirmados quanto uma previsão feita
$h$ semanas antes para aquela mesma semana — o número de pares cai de 295 para 284 conforme $h$ cresce
porque a janela de avaliação é fixa em datas de calendário, e previsões de horizonte mais longo "cabem"
menos vezes dentro da mesma janela nas pontas.

### 8.2.4 Tradução: o que um erro de 98 a 278,8 casos significa numa semana real

Um MAE de **278,8** na avaliação de 3 meses não diz, sozinho, se isso é grave. A gravidade depende do
tamanho típico das semanas que estão sendo previstas — e aqui a série tem semanas de calmaria (poucos
casos) e semanas de epidemia (centenas de casos) misturadas.

- **Em 1 semana de antecedência (h=1), o erro de 98,0 casos é pequeno frente às semanas de epidemia** —
  nas semanas com mais de 421 casos (estágio Alerta do plano municipal, ver §8.6), o valor real mediano é
  **917** (medido em `analises/2026-09-26_transformacao_de_escala/README.md`); um erro de 98 nessa faixa
  seria de cerca de **10,7%** do valor real. Mas na calmaria (semanas com poucos casos), um erro de 98
  pode ser maior do que o próprio valor real — é um erro relativamente grande quando a cidade está calma.
- **Em 1 mês (h=4), o erro sobe para 219,7.** Numa semana de epidemia moderada (a faixa "Mobilização" do
  plano municipal, 141 a 421 casos), esse erro já é comparável ao próprio tamanho da faixa inteira: é como
  errar por uma margem do tamanho da diferença entre "início de epidemia" e "epidemia grave".
- **Em 3 meses (h=12), o erro de 278,8 numa semana de epidemia grande (917 casos reais medianos nessa
  faixa) significa prever, tipicamente, bem menos da metade do que vai acontecer.** Isso é aprofundado com
  todo o detalhe em §8.4 e §8.5, porque **278,8 é a média de TODOS os horizontes de erro em 3 meses,
  incluindo as semanas calmas** — nas semanas de epidemia especificamente, o erro típico é ainda maior
  (mediana de **539**, ver §8.5), porque a média de 278,8 é puxada para baixo pelas muitas semanas calmas
  em que o modelo acerta quase exatamente.
- **O coeficiente de determinação cai de 0,898 (h=1) para 0,437 (h=12).** Em português simples: a 1 semana
  de antecedência, o modelo explica quase 90% de por que uma semana tem mais ou menos casos que outra; a
  3 meses, explica menos de 44% — mais da metade da variação entre semanas fica sem explicação do modelo
  nesse horizonte.

---

## 8.3 A comparação com as réguas simples

### 8.3.1 O que é uma "régua" nesta avaliação

Uma **régua** (em inglês, *baseline*) é uma regra de previsão deliberadamente simples, sem nenhum
aprendizado estatístico, usada como piso de comparação: se o modelo treinado não bate uma régua ingênua,
ele não está agregando valor sobre o óbvio. Duas réguas aparecem aqui:

- **Régua sazonal**: prevê que o número de casos de uma semana futura será igual ao número de casos da
  mesma semana epidemiológica, **52 semanas antes** (isto é, "o que aconteceu nessa mesma época do ano
  passado").
- **Persistência**: prevê que o número de casos da semana futura será igual ao número de casos **de hoje**
  (a última semana com dado disponível no momento da previsão).

### 8.3.2 A tabela, na janela oficial (2024 até fev/2026)

Erro absoluto médio (MAE), por horizonte:

| Regra / modelo | h=1 | h=4 | h=8 | h=12 |
|---|---|---|---|---|
| **Cenário adotado (HistGB, quantil 0,85)** | **98,0** | **219,7** | **272,6** | **278,8** |
| Régua sazonal (mesma semana, ano anterior) | 202,1 | 213,2 | 216,2 | 217,8 |
| Persistência (repete o valor de hoje) | 83,3 | 279,0 | 531,0 | 697,5 |
| HistGB, variante folha mínima 20 | 133,6 | 199,6 | 223,2 | 243,8 |

Fonte: `analises/2026-09-25_regua_regras_simples/`.

⚠️ **Cuidado ao citar isto em outro contexto:** numa janela mais estreita, só 2024-2025 (**n=97**), a régua
sazonal muda para **210,4 · 222,0 · 225,1 · 226,8** — números diferentes, porque a janela de avaliação é
diferente. Toda citação desta tabela precisa vir com a janela declarada ao lado.

### 8.3.3 A leitura honesta

- **Em 1 semana de antecedência (h=1), o modelo vence com folga.** 98,0 contra 202,1 da régua sazonal e
  83,3 da persistência — o modelo é o único que bate os dois pisos simultaneamente nesse horizonte.
- **Em 2 e 3 meses (h=8 e h=12), a régua sazonal vence o cenário adotado.** 216,2 contra 272,6 em h=8; e
  217,8 contra 278,8 em h=12. A régua sazonal — que não usa clima, não usa mosquito, não usa nenhum dado
  do ano corrente além do calendário — erra **menos** que o modelo treinado, nesses dois horizontes.
- **Por que isso acontece:** dengue em Porto Alegre segue um ciclo forte de sazonalidade — os casos sobem
  no verão e outono e caem no inverno, ano após ano, de forma consistente. Quando a pergunta é "quantos
  casos em 3 meses", quase toda a informação útil para responder já está contida na própria época do ano:
  saber que estamos em março já entrega grande parte da resposta, porque março historicamente tem mais
  casos que julho. As variáveis que o modelo usa além disso — clima recente e mosquito recente — carregam
  informação sobre o **presente**, não sobre o que vai acontecer daqui a 3 meses; conforme o horizonte
  cresce, a vantagem de informação recente decai e a sazonalidade (que a régua já captura de graça, sem
  treinar nada) passa a valer mais que o resto.
- Isso não é uma falha de implementação. É uma **limitação estrutural do horizonte longo**: para vencer a
  régua sazonal em 3 meses, o modelo precisaria de sinal preditivo que ainda não decaiu depois de 12
  semanas — e a busca de hiperparâmetros (25/09/2026, 120 configurações) e as outras 9 famílias de modelo
  testadas (§8.9 e demais seções deste documento) não encontraram esse sinal.

---

## 8.4 A captura do pico, traduzida

### 8.4.1 A fórmula

A **captura do pico** é a métrica histórica do projeto (calculada pela primeira vez em 13/09/2026) para
medir se o modelo acerta o **tamanho** de uma epidemia, olhando só para as semanas em que já se sabe que
há surto:

$$
\text{Captura do pico} = \frac{\overline{\hat{y}}_{\text{surto}}}{\overline{y}_{\text{surto}}}
$$

Onde:

- **$\overline{y}_{\text{surto}}$** é a média do número real de casos, contando só as semanas em que o
  real passou de **100 casos** (o corte de "semana de surto" usado por esta métrica).
- **$\overline{\hat{y}}_{\text{surto}}$** é a média do número **previsto** de casos pelo modelo, nas
  mesmas semanas.
- Um valor de **1,0** significa acerto perfeito no tamanho médio da epidemia; um valor abaixo de 1
  significa que o modelo, em média, prevê menos do que a epidemia real; acima de 1 significaria previsão
  em excesso.

### 8.4.2 O valor medido e o exemplo numérico

Em 3 meses (h=12), avaliação 2024+: **captura do pico = 0,388** (fonte:
`analises/2026-09-13_metrica_de_alarme/README.md`, reconfirmado em 26/09/2026 na rodada de calibração por
faixa).

Para traduzir isso em um exemplo concreto: a mesma medição de 26/09/2026 (fonte:
`analises/2026-09-26_transformacao_de_escala/README.md`, tabela de largura do intervalo por faixa) mostra
que, na faixa de gravidade "Alerta ou mais" (semanas com mais de **421** casos reais, o estágio de alerta
epidemiológico do plano municipal — ver §8.6), o **valor real mediano** dessas 163 semanas é **917**
casos, e o **erro mediano** do modelo nessa mesma faixa é **539** casos, sempre para menos (ver §8.5 sobre
por que é "sempre para menos" e não um erro que às vezes é para mais). Isso implica uma previsão mediana
de aproximadamente $917 - 539 = 378$ casos numa semana desse porte — uma proporção de $378/917 \approx
41\%$, no mesmo patamar da captura do pico agregada de 0,388 (a pequena diferença entre 41% e 38,8% vem
de usar mediana num caso e média no outro).

### 8.4.3 A consequência prática

- Se um gestor de saúde dimensionar **leitos, equipes e insumos** com base na previsão do modelo para uma
  semana que vai chegar a 917 casos reais, ele planejaria para cerca de **378** casos. Quando a semana
  real chegar, a demanda real será **cerca de 2,4 vezes** maior do que o planejado.
- Esse fator de 2,4 não é um exagero pontual: é consistente com a captura do pico de 0,388 medida sobre
  **todas** as semanas de surto da avaliação, não um caso isolado.
- **Por que subestimação sistemática é mais perigosa do que um erro aleatório do mesmo tamanho:**
  - Um erro **aleatório** (ruído) tem a mesma chance de superestimar quanto de subestimar. Um gestor que
    planeja repetidamente com um modelo desse tipo, ao longo de muitas semanas, vai por vezes ter folga de
    recursos e por vezes ter falta — em média, o sistema absorve o erro, porque os excessos de umas
    semanas compensam as faltas de outras (supondo que os recursos "sobrando" numa semana calma possam,
    na prática, ser realocados ou não custem muito a mais).
  - Um erro **sistemático** (viés) empurra sempre na mesma direção. Um gestor que planeja repetidamente
    com este modelo em semanas de epidemia grande vai **sempre** ter falta de recursos, nunca sobra — não
    há semana de "compensação". O erro se acumula na mesma direção a cada nova epidemia, em vez de se
    cancelar estatisticamente.
  - Em termos de saúde pública: um sistema de leitos dimensionado sistematicamente para 40% da demanda
    real de picos vai colapsar **toda vez** que uma epidemia grande chegar, não só ocasionalmente.

---

## 8.5 O erro mediano de 539 casos sobre 917 reais — por que é viés, não ruído

### 8.5.1 Mediana: a definição

A **mediana** de um conjunto de números é o valor do meio quando eles são colocados em ordem — metade dos
valores fica abaixo dela, metade acima. Ao contrário da **média** (soma dividida pela quantidade), a
mediana não é puxada por valores extremos isolados; por isso costuma ser preferida para descrever "o caso
típico" quando a distribuição tem valores muito distantes da maioria (como acontece com casos de dengue,
que variam de 0 a mais de 2.000 numa mesma série).

### 8.5.2 O número e a tradução

Nas 163 semanas da faixa "Alerta ou mais" (real acima de 421 casos, avaliação certificada em
26/09/2026), o valor real mediano é **917** casos e o erro mediano do modelo é **539** casos — ou seja, na
semana típica dessa faixa, o modelo erra por **539 casos**, o equivalente a **59%** do valor real
($539/917 \approx 0{,}588$).

### 8.5.3 Por que isso é viés e não ruído

Três medições independentes, feitas em datas diferentes, com métodos diferentes, apontam todas na mesma
direção:

| Medição | Data | Direção do erro |
|---|---|---|
| Captura do pico **0,388** (h=12) | 13/09/2026 | previsão sistematicamente **abaixo** do real |
| Melhor limiar de decisão do alarme cai **abaixo** de 421 em h=4/8/12 (§8.9) | 26/09/2026 | o modelo já subestima o bastante para que baixar o limiar de decisão capture mais surtos |
| Cobertura do intervalo de 90% cai para **17,8%** acima de 421 casos (§8.6) | 26/09/2026 | o modelo erra sempre para o mesmo lado — errar em direções aleatórias não derrubaria a cobertura assim |

Se o erro de 539 fosse **ruído** (aleatório), a distribuição dos erros nessa faixa teria aproximadamente
metade das semanas com previsão acima do real e metade abaixo — o que faria a cobertura do intervalo de
90% ficar próxima de 90% (a faixa cobriria o real na maioria das vezes) e a captura do pico ficar próxima
de 1,0 (superestimações e subestimações se cancelariam na média). Nenhuma das duas coisas acontece: a
cobertura despenca e a captura fica em 0,388. **Isso é a assinatura de um viés sistemático — o modelo não
está "errando por acaso perto do valor certo", está prevendo consistentemente abaixo dele.**

---

## 8.6 A calibração por faixa — o modelo é honesto quando está calmo, e não quando importa

### 8.6.1 O que é um intervalo de previsão, cobertura e calibração

O cenário adotado, além do quantil 0,85 usado como estimativa pontual (§8.1), também é treinado
separadamente em outros **6 quantis** (0,05 · 0,10 · 0,25 · 0,50 · 0,75 · 0,90 · 0,95, mais o próprio
0,85), formando **7 modelos independentes**, cada um mirando um quantil diferente da distribuição de
casos possível para aquela semana. Combinando pares desses quantis, forma-se um **intervalo de previsão**:
por exemplo, o intervalo entre o quantil 0,05 e o quantil 0,95 deveria conter o valor real em
aproximadamente **90%** das semanas, **se o modelo estiver bem calibrado** — por isso ele é chamado, nas
tabelas deste projeto, de "IC 90%" (o intervalo entre os quantis 0,25 e 0,75 é chamado "IC 50%").

⚠️ **Nota de rigor:** este "IC" (abreviação de intervalo de confiança, sigla amplamente usada em
estatística) não é tecnicamente um intervalo de confiança clássico no sentido em que a estatística
inferencial usa o termo — um intervalo de confiança clássico descreve a incerteza sobre um **parâmetro**
de uma população (por exemplo, a média verdadeira), assumindo repetição do processo de amostragem. Aqui
trata-se de um **intervalo de previsão** (ou intervalo preditivo): a incerteza sobre uma **observação
futura específica** (o número de casos de uma semana), obtida diretamente dos quantis previstos pelo
modelo. O projeto usa "IC" como atalho de notação nas tabelas; este documento mantém essa notação por
consistência, mas o conceito correto é "intervalo de previsão calibrado por quantis".

**Cobertura** é a fração de semanas em que o valor real caiu de fato dentro do intervalo previsto.
**Calibração** é o quanto a cobertura medida bate com a cobertura nominal esperada (50% ou 90%) — um
modelo bem calibrado erra a cobertura por pouco; um modelo mal calibrado erra por muito, para mais ou
para menos confiança do que deveria ter.

### 8.6.2 A tabela, por faixa de gravidade (cenário adotado, 26/09/2026)

O esperado, se o modelo fosse honesto sobre sua própria incerteza, é **50%** e **90%** de cobertura:

| Faixa de casos reais | Semanas | Cobertura IC 50% | Cobertura IC 90% |
|---|---|---|---|
| Calmaria, 0 a 20 casos | 814 | **59,2%** | **90,5%** |
| Subida, 21 a 140 casos | 110 | 18,2% | 63,6% |
| Mobilização, 141 a 421 casos | 72 | 27,8% | 47,2% |
| **Alerta ou mais, acima de 421 casos** | 163 | **8,0%** | **17,8%** |

Fonte: `analises/2026-09-26_calibracao_por_faixa/`.

### 8.6.3 A tradução

- **Na calmaria, o intervalo de 90% cobre 90,5% das 814 semanas** — isso é quase exatamente o esperado. O
  modelo, quando a cidade está com poucos casos, sabe descrever corretamente sua própria incerteza: quando
  ele diz "tenho 90% de certeza de que o valor vai cair neste intervalo", ele acerta 9 em cada 10 vezes,
  como prometido.
- **Acima de 421 casos, o mesmo intervalo de 90% cobre só 17,8%** — o modelo diz "tenho 90% de certeza",
  mas na prática acerta **menos de 1 em cada 5 vezes**. A degradação é **monotônica**: quanto maior o
  nível de casos da semana, pior a calibração — não é um problema isolado de uma faixa, é uma tendência
  contínua.
- **O que um gestor faria de errado, confiando nisso:** se um gestor de saúde lesse "o modelo estima entre
  X e Y casos, com 90% de confiança" numa semana de epidemia grande, e tomasse decisões de alocação de
  recursos como se essa confiança fosse real, ele estaria, na verdade, operando com uma confiança real de
  apenas **17,8%** — quase 5 vezes menor do que a suposta. Na prática, isso significa que a faixa
  "acabaria de fora" o valor real em mais de 4 entre 5 semanas de epidemia grave, e o gestor descobriria
  isso tarde demais, quando a demanda real já tivesse estourado a faixa que ele havia planejado.
- Um exemplo concreto e real, da própria série de dados certificada (26/09/2026): numa semana com **917**
  casos reais (h=12, cenário adotado), o intervalo de 90% previsto foi de **0 a 839,93** casos — o limite
  **superior** do intervalo, o mais otimista possível, já ficou abaixo do valor real. O modelo não apenas
  errou o centro da previsão: ele errou a ponto de o valor real cair **fora até do extremo superior da sua
  própria margem de incerteza declarada**.

---

## 8.7 A largura do intervalo contra o erro real — por que "alargar a régua" não resolve

### 8.7.1 A tabela

Cenário adotado, comparando o tamanho do intervalo de 90% (o quanto de margem o modelo declara) com o
erro que ele de fato comete (26/09/2026):

| Faixa | Real mediano | Largura do IC 90% | Erro mediano | Largura que seria necessária | Quanto falta |
|---|---|---|---|---|---|
| Calmaria | 1 | 8,5 | 1,3 | 4 | **0,5×** (o intervalo já é largo demais) |
| Subida | 47 | 101,1 | 29,6 | 97 | 1,0× (aproximadamente correto) |
| Mobilização | 247 | 195,6 | 157,8 | 519 | 2,7× |
| **Alerta ou mais** | **917** | **592,7** | **539,0** | **1.773** | **3,0×** |

"Largura que seria necessária" é o tamanho de intervalo que teria feito o valor real caber dentro da
margem de erro típica daquela faixa; "quanto falta" é a razão entre essa largura necessária e a largura
que o modelo de fato declarou.

### 8.7.2 Por que a transformação de escala (raiz quadrada, logaritmo) não resolveu isso

A hipótese natural, testada e pré-declarada em 26/09/2026
(`analises/2026-09-26_transformacao_de_escala/`), era que dados de contagem (como número de casos) têm
**variância crescente com o nível** — quanto maior o número esperado de casos, maior a dispersão em torno
dele — e que reescrever o alvo em raiz quadrada ou logaritmo antes de treinar corrigiria isso, porque
essas transformações "comprimem" valores altos, o que deveria fazer o intervalo de largura constante na
escala transformada virar um intervalo de largura **proporcional ao nível** depois de voltar para a escala
de casos.

**A hipótese estava errada, e o motivo é mensurável:**

- A largura do intervalo **já cresce** com o nível de casos: de **8,5** (calmaria) para **592,7** (Alerta
  ou mais), um fator de aproximadamente **70 vezes**.
- Mas o erro cresce **mais rápido ainda**: de **1,3** para **539,0**, um fator de aproximadamente **415
  vezes**.
- Ou seja, o problema nunca foi "intervalo de largura constante" — o intervalo já não é constante. O
  problema é um intervalo que cresce **mais devagar do que o erro real cresce**.
- Raiz quadrada e logaritmo **comprimem** valores altos ainda mais do que a escala original — então, ao
  aplicá-las, o intervalo (depois de voltar para casos) cresce **ainda mais devagar** do que sem
  transformação nenhuma, o oposto da direção necessária. Foi exatamente isso que a rodada de 26/09/2026
  mediu: a cobertura acima de 421 casos, que já era 17,8% sem transformação, caiu para **15,9%** com raiz
  quadrada e **13,5%** com logaritmo — piorou nas duas variantes, sem exceção, em todas as 4 faixas de
  gravidade, inclusive na calmaria (que era bem calibrada e passou a subcalibrada: de 90,5% para 84,2% e
  80,5%).
- **FATO (medido em 26/09/2026, certificação adversarial aprovada):** o problema de calibração nos picos
  é de **viés de nível**, não de forma da variância — e nenhuma transformação de escala corrige viés, só
  redistribui a forma da incerteza. Alargar o intervalo até os **1.773** casos de largura necessários
  cobriria os 90% prometidos, mas produziria uma faixa de aproximadamente 100 a 1.900 casos — larga
  demais para informar qualquer decisão prática de dimensionamento.

---

## 8.8 O escore de intervalo ponderado (WIS)

### 8.8.1 A fórmula

O **escore de intervalo ponderado**, em inglês *weighted interval score*, abreviado **WIS**, é a métrica
usada neste projeto para avaliar a qualidade de uma previsão **probabilística** — uma previsão que não dá
só um número, mas uma distribuição inteira de possibilidades (aqui, os 7 quantis do cenário adotado). Ela
penaliza ao mesmo tempo (a) intervalos largos demais e (b) o valor real cair fora do intervalo declarado,
de forma proporcional a quão longe ele caiu. A formulação usada é a de Bracher, Heyder e colegas (2021)
para desafios de previsão epidemiológica.

Primeiro, o **escore de intervalo** de um único par de quantis (por exemplo, os quantis 0,25 e 0,75, que
formam o intervalo de 50%):

$$
IS_\alpha(l, u, y) = (u - l) + \frac{2}{\alpha}(l - y)\cdot\mathbb{1}[y<l] + \frac{2}{\alpha}(y - u)\cdot\mathbb{1}[y>u]
$$

Onde:

- **$l$** e **$u$** são os limites inferior e superior do intervalo (os dois quantis previstos que o
  formam).
- **$y$** é o valor real observado.
- **$\alpha$** é 1 menos a cobertura nominal do intervalo (0,50 no intervalo de 50%; 0,20 no intervalo de
  80%; 0,10 no intervalo de 90%).
- **$\mathbb{1}[y<l]$** é um indicador que vale 1 se o valor real caiu **abaixo** do limite inferior (e 0
  caso contrário) — junto com o termo que o multiplica, é a penalidade por o modelo ter sido otimista
  demais para baixo.
- **$\mathbb{1}[y>u]$** é o indicador equivalente para o valor real ter caído **acima** do limite superior
  — a penalidade por subestimação, que é o problema medido nesta seção.
- Sem nenhuma penalidade (valor real dentro do intervalo), o escore é simplesmente a largura $(u-l)$ — um
  intervalo mais estreito já é melhor, mesmo acertando.

Depois, o WIS de uma origem (uma previsão específica) combina o erro da mediana com os escores de vários
intervalos, com pesos:

$$
\text{WIS} = \frac{\frac{1}{2}|y - m| + \sum_{k=1}^{K} \frac{\alpha_k}{2}\, IS_{\alpha_k}(l_k, u_k, y)}{K + \frac{1}{2}}
$$

Onde:

- **$m$** é a mediana prevista (quantil 0,50).
- **$K$** é o número de intervalos usados — neste projeto, **$K=3$**: o intervalo de 50% (quantis 0,25 e
  0,75), o de 80% (quantis 0,10 e 0,90) e o de 90% (quantis 0,05 e 0,95).
- Quanto **menor** o WIS, melhor a previsão — ele soma 0 só numa previsão perfeita (todos os quantis
  exatamente iguais ao valor real).

### 8.8.2 Exemplo numérico, do começo ao fim, com um dado real do projeto

Semana-alvo **09/03/2025**, horizonte de 3 meses (h=12), cenário adotado, valor real $y = 917$ casos
(fonte: `analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`, mesma configuração
certificada do painel oficial). Os 7 quantis previstos para essa origem foram:

| Quantil | Valor previsto |
|---|---|
| 0,05 | 0,00 |
| 0,10 | 0,00 |
| 0,25 | 99,68 |
| 0,50 (mediana) | 553,14 |
| 0,75 | 607,10 |
| 0,90 | 751,92 |
| 0,95 | 839,93 |

**Passo 1 — o termo da mediana:** $\frac{1}{2}|917 - 553{,}14| = \frac{1}{2}\times 363{,}86 = 181{,}93$.

**Passo 2 — o intervalo de 50%** ($l=99{,}68$, $u=607{,}10$, $\alpha=0{,}50$): como $y=917 > u=607{,}10$,
$IS_{0{,}50} = (607{,}10-99{,}68) + \frac{2}{0{,}50}(917-607{,}10) = 507{,}42 + 1.239{,}60 = 1.747{,}02$.
Ponderado por $\alpha/2 = 0{,}25$: contribuição de $436{,}76$.

**Passo 3 — o intervalo de 80%** ($l=0$, $u=751{,}92$, $\alpha=0{,}20$): $y=917>u$, então
$IS_{0{,}20} = 751{,}92 + \frac{2}{0{,}20}(917-751{,}92) = 751{,}92 + 1.650{,}80 = 2.402{,}72$. Ponderado
por $0{,}10$: contribuição de $240{,}27$.

**Passo 4 — o intervalo de 90%** ($l=0$, $u=839{,}93$, $\alpha=0{,}10$): $y=917>u$, então
$IS_{0{,}10} = 839{,}93 + \frac{2}{0{,}10}(917-839{,}93) = 839{,}93 + 1.541{,}40 = 2.381{,}33$. Ponderado
por $0{,}05$: contribuição de $119{,}07$.

**Passo 5 — soma tudo e divide por $K+0{,}5=3{,}5$:**
$$
\text{WIS} = \frac{181{,}93 + 436{,}76 + 240{,}27 + 119{,}07}{3{,}5} = \frac{978{,}03}{3{,}5} \approx 279{,}4
$$

Este valor único (279,4) é da mesma ordem de grandeza que a média de WIS reportada para h=12 no cenário
adotado (288,6 na série completa, 300,7 em 2024-2025 — §8.8.3) — o que é esperado, já que essa é uma
semana de epidemia grande, exatamente o tipo de semana em que o modelo tende a errar mais (§8.4 e §8.5).

### 8.8.3 A tabela oficial e a leitura estatística

Escore de intervalo ponderado (WIS) médio, recorte 2024-2025 (fonte:
`analises/2026-09-26_wis_na_tabela_restaurada/`):

| Horizonte | Cenário adotado | HistGB folha 20 | Régua climatológica |
|---|---|---|---|
| 1 semana | 101,9 | 121,3 | 292,7 |
| 4 semanas (1 mês) | **215,4** | **199,0** | 313,5 |
| 8 semanas | 288,6 | 259,0 | 322,2 |
| 12 semanas (3 meses) | 300,7 | **278,6** | 324,2 |

A **régua climatológica**, diferente da régua sazonal de §8.3 (que olha só o ano anterior), prevê usando
os **quantis da mesma semana epidemiológica em todos os anos anteriores disponíveis** — é a régua
probabilística de referência usada oficialmente pelos sprints de previsão de dengue no Brasil, e o WIS é
a métrica oficial desses mesmos sprints.

Comparando modelo contra essa régua, com o **teste de Wilcoxon pareado** (um teste que verifica se as
diferenças pareadas, semana a semana, entre dois métodos, tendem consistentemente para um lado, sem
assumir que os erros seguem uma distribuição normal) e correção de Holm (explicada em detalhe em §8.9.4):

- **Em 1 mês (h=4), os dois modelos vencem a régua climatológica com p de Holm menor que 0,0001.**
- **Em 3 meses (h=12), só o HistGB folha 20 vence** (p de Holm **0,0020**); **o cenário adotado não vence**
  (p de Holm **0,096** — acima do limiar convencional de 0,05).

**O que um "p menor que 0,0001" significa, e o que não significa:** um p-valor é a probabilidade de se
observar uma diferença tão grande quanto a medida (ou maior), **assumindo que a hipótese nula fosse
verdadeira** — aqui, a hipótese nula é "o modelo e a régua têm o mesmo desempenho esperado, e a diferença
observada é só flutuação aleatória de amostra". Um p menor que 0,0001 significa que, **se** modelo e régua
fossem igualmente bons, seria extremamente improvável (menos de 1 em 10 mil) observar uma vantagem do
modelo tão grande e consistente quanto a medida — por isso rejeita-se a hipótese de empate. **O que isso
NÃO significa:** não significa que a vantagem é "grande" em termos práticos (um p pequeno pode acompanhar
uma diferença pequena, se a amostra for grande o bastante para detectá-la com precisão), não significa que
o modelo está correto em valor absoluto (só que é mais preciso que a régua) e não significa que o resultado
se generaliza para outros horizontes ou para outra janela de anos — cada célula desta tabela é um teste
independente, com seu próprio p.

Também vale notar, como achado descritivo (não é teste de hipótese, não abre família de correção
múltipla): **77,0%** das origens (1.784 de 2.318) precisaram de correção por **cruzamento de quantis** —
quando um quantil mais alto (por exemplo, 0,75) sai, por acaso do treino independente de cada quantil, com
valor previsto **menor** que um quantil mais baixo (por exemplo, 0,25), o que é logicamente impossível
numa distribuição real e precisa ser corrigido reordenando os valores (método de Chernozhukov, Fernández-Val
e Galichon, 2010). Isso acontece porque os 7 quantis do WIS são 7 modelos **treinados de forma
independente**, cada um com sua própria perda quantílica — nada no treino impõe que a saída do quantil
0,25 fique sempre abaixo da saída do quantil 0,75.

---

## 8.9 O alarme e o quadro de McNemar

### 8.9.1 O que é "o alarme" nesta avaliação

Em vez de perguntar "o modelo acertou o número exato de casos", esta seção pergunta uma coisa mais
simples e operacional: **"o modelo soube dizer, com antecedência, que uma semana ia virar surto?"** Para
isso, define-se um evento binário (sim/não): uma semana é "de surto" se o número real de casos passar de
um limiar (100, 140, 421 ou 702, dependendo do estágio — ver o Plano Municipal de Contingência de
Arboviroses, citado em outra seção deste documento); e o modelo "dispara o alarme" se sua previsão para
aquela semana também passar do mesmo limiar.

- **Sensibilidade**: das semanas que de fato foram surto, quantas o modelo sinalizou com alarme.
- **Precisão**: dos alarmes que o modelo disparou, quantos eram surto de verdade (e não falso alarme).
- **Falsos por ano**: quantos alarmes o modelo disparou fora de qualquer episódio real de surto, contados
  por ano de avaliação.
- **Índice de Youden**, chamado de **J**: $J = \text{sensibilidade} + \text{especificidade} - 1$, onde
  especificidade é "das semanas que NÃO foram surto, quantas o modelo corretamente não alarmou". $J=1$ é
  o alarme perfeito (acerta toda semana de surto e nunca alarma à toa); $J=0$ é o desempenho de um alarme
  que decide ao acaso, sem nenhuma informação real.

**Exemplo numérico de Youden**, com os números reais do evento "mais de 100 casos", h=4, cenário adotado
(fonte: `analises/2026-09-25_alarme_contra_canal_endemico/README.md`): sensibilidade 97,1% e precisão
94,3% são dados na tabela; a especificidade (não listada diretamente na tabela, mas usada no cálculo de J
publicado) resulta em $J = 0{,}94$, o valor mais alto entre todas as regras testadas nesse horizonte —
ou seja, o alarme do cenário adotado, em 1 mês, é o mais equilibrado entre acertar surtos e não alarmar à
toa, entre as opções comparadas.

### 8.9.2 A tabela completa — evento "mais de 100 casos na semana", avaliação 2024+, 102 semanas

| Horizonte | Sensibilidade | Precisão | Falsos por ano | Youden (J) | Captura do pico (métrica de §8.4) |
|---|---|---|---|---|---|
| 1 semana | 96,9% | 91,2% | 1,0 | — | 0,886 |
| 4 semanas (1 mês) | **97,1%** | **94,3%** | **0,7** | **0,94** | 0,702 |
| 8 semanas (2 meses) | 81,6% | 86,1% | 1,7 | — | 0,417 |
| 12 semanas (3 meses) | 76,9% | 81,1% | 2,3 | 0,66 | **0,388** |

Para comparação, na variante HistGB folha 20: Youden **0,90** em h=4 e **0,78** em h=12; a régua "o ano
passado passou de 100" tem Youden **0,84** em h=4 e **0,80** em h=12; e a régua "hoje já passou de 100" tem
Youden **0,68** em h=4 e **0,11** em h=12.

⚠️ Os valores medidos em `metricas_por_regra.csv` são **0,8046** e **0,1148**, que arredondam para
**0,80** e **0,11**. A correção não muda nenhuma conclusão: a régua do ano passado continua acima do
cenário adotado em 3 meses, 0,80 contra 0,66.

### 8.9.3 🔴 O quadro dos testes de McNemar com correção de Holm — o mais importante desta seção

**O que é o teste de McNemar:** quando se comparam dois classificadores binários (aqui, "o alarme do
modelo" contra "o alarme da régua") **nas mesmas semanas**, cada semana cai em uma de quatro categorias:
os dois acertam, os dois erram, só o modelo acerta, ou só a régua acerta. O teste de McNemar ignora as
semanas em que os dois concordam (acertam juntos ou erram juntos) e olha **só** para as semanas em que
**discordam** — chamadas de **pares discordantes** — perguntando: entre as vezes em que só um dos dois
acertou, o modelo acertou mais vezes do que a régua, mais do que se poderia esperar só por acaso (50-50)?

A versão exata do teste (usada nesta rodada, dada a quantidade pequena de pares discordantes) é um teste
binomial sobre esse conjunto:

$$
p = 2 \times P(X \le \min(b, c) \mid X \sim \text{Binomial}(n = b+c, \, p=0{,}5))
$$

Onde:

- **$b$** é o número de pares discordantes em que o modelo acertou e a régua errou.
- **$c$** é o número de pares discordantes em que a régua acertou e o modelo errou.
- **$X \sim \text{Binomial}(n=b+c, p=0{,}5)$** representa a distribuição de resultados que se esperaria
  **se** modelo e régua tivessem exatamente a mesma chance de acertar em cada par discordante (a hipótese
  nula: não há vantagem real de nenhum dos dois).
- O fator **2×** torna o teste **bilateral**: conta tanto a possibilidade de o modelo vencer por muito
  quanto a de a régua vencer por muito.

**Exemplo numérico, do começo ao fim, com o dado real mais citado desta seção** (h=12, cenário adotado
contra "hoje já passou de 100 casos"; fonte:
`analises/2026-09-25_alarme_contra_canal_endemico/saidas/mcnemar_holm.csv`): $n=102$ pares totais, dos
quais **37** são discordantes, sendo $b=31$ (modelo acerta, régua erra) e $c=6$ (régua acerta, modelo
erra). $\min(b,c)=6$. O p-valor bruto é $2 \times P(X\le 6 \mid \text{Binomial}(37, 0{,}5)) =
0{,}0000412576$ — batendo exatamente com o valor certificado no arquivo (`4,12575900554657e-05`).

**Correção de Holm** — por que é necessária: quando se roda **vários** testes de hipótese na mesma
rodada (aqui, a família tem **16 testes**: 2 modelos × 2 horizontes × 2 réguas × 2 eventos), a chance de
pelo menos um deles dar "significativo" só por acaso, mesmo que nenhuma diferença real exista em lugar
nenhum, cresce com o número de testes. A correção de Holm controla essa chance, tornando cada p-valor
individual mais rigoroso, na proporção da posição do teste quando todos os p-valores brutos da família
são ordenados do menor para o maior:

$$
p^{\text{Holm}}_{(i)} = \max_{j \le i} \left[ (m - j + 1) \times p_{(j)} \right]
$$

Onde:

- **$m$** é o número total de testes na família (aqui, **16**).
- **$p_{(j)}$** é o $j$-ésimo menor p-valor bruto, depois de ordenar todos os 16 do menor para o maior.
- **$\max_{j \le i}$** garante que o p-valor corrigido nunca diminua conforme a posição $i$ aumenta (uma
  correção monótona) — e o resultado é sempre limitado no máximo a 1,0.

**Continuando o exemplo:** dentro da família de 16 testes de 25/09/2026, o par (h=12, cenário adotado ×
"hoje já passou") tem o **segundo menor** p-valor bruto de toda a família ($i=2$; o menor de todos é o do
HistGB folha 20 no mesmo confronto). O multiplicador de Holm nessa posição é $m - i + 1 = 16 - 2 + 1 = 15$.
$p^{\text{Holm}} = 15 \times 0{,}0000412576 = 0{,}00061886$ — batendo, com precisão de 5 casas decimais,
com o valor certificado no arquivo (**0,0006188638508319855**, arredondado para **0,00062** nas tabelas
deste documento).

### 8.9.4 A tabela completa de McNemar (evento "mais de 100 casos")

| Horizonte | Comparação | Pares discordantes | Divisão (modelo × régua) | p de Holm | Significativo a 5%? |
|---|---|---|---|---|---|
| 4 (1 mês) | adotado × "hoje já passou" | 15 | 13 a 2 | **0,103** | **NÃO** |
| 4 (1 mês) | adotado × "o ano passado" | 7 | 5 a 2 | **1,000** | **NÃO** |
| 12 (3 meses) | adotado × "hoje já passou" | 37 | 31 a 6 | **0,00062** | **SIM** |
| 12 (3 meses) | adotado × "o ano passado" | 16 | 4 a 12 | **0,845** | **NÃO** |

### 8.9.5 Por que "97,1% de sensibilidade com p de Holm 0,103" é "número alto, vitória não demonstrada"

Em h=4 (1 mês), o cenário adotado tem sensibilidade de 97,1% contra a régua "hoje já passou de 100 casos"
— um número que, isolado, parece uma vitória clara. Mas o teste de McNemar sobre os **15 pares
discordantes** desse confronto não fecha com significância (p de Holm **0,103**, acima do limiar
convencional de 0,05).

- **A causa mais provável é falta de poder estatístico, não ausência de efeito real.** Poder estatístico
  é a capacidade de um teste de detectar uma diferença real, quando ela de fato existe, com o tamanho de
  amostra disponível. Com apenas **15** pares discordantes, mesmo uma vantagem real e consistente do
  modelo (aqui, o modelo venceu em **13** dos 15, contra 2 da régua — uma proporção de 87% a favor) pode
  não passar do limiar de significância, porque o teste binomial exige uma assimetria ainda maior, ou uma
  amostra maior de discordâncias, para descartar com confiança a hipótese de que essa proporção surgiu só
  por acaso de uma moeda honesta.
- Em termos concretos: com 15 lançamentos de uma "moeda" que decide qual dos dois vence, sair 13 contra 2
  já é bastante incomum sob a hipótese de moeda honesta (50-50), mas não incomum o bastante para vencer o
  padrão de rigor de uma família de 16 testes simultâneos (que já exige, por Holm, um p bruto ainda menor
  para ser aceito).
- **A direção do efeito aponta a favor do modelo (13 de 15).** O resultado correto de se comunicar é: "o
  modelo parece melhor neste confronto, mas a amostra de discordâncias ainda é pequena demais para provar
  isso com o rigor estatístico exigido" — não "o modelo vence" e não "não há diferença nenhuma". É uma
  terceira categoria, tratada explicitamente na tabela de síntese (§8.11).
- Já em h=12 (3 meses) contra a mesma régua fraca ("hoje já passou"), a amostra de discordâncias é maior
  (**37** pares) e a assimetria também (31 a 6) — aí sim o teste fecha com p de Holm **0,00062**. É o
  mesmo fenômeno, poder estatístico, na direção oposta: mais discordâncias, mais capacidade de detectar
  a diferença real que já existia.
- Contra a régua mais forte ("o ano passado passou de 100"), o resultado é diferente de natureza: em
  h=12, a divisão dos 16 pares discordantes é **4 a 12** — a favor da **régua**, não do modelo (Youden
  0,66 do modelo contra 0,81 da régua) — e mesmo assim não significativo (p de Holm 0,845). Aqui a leitura
  correta não é "falta de poder"; é **empate estatístico com direção levemente desfavorável ao modelo**.

---

## 8.10 Os blocos contíguos de semanas de surto — e o que isso faz com os p-valores acima

### 8.10.1 O que é um "bloco contíguo" e por que ele importa para os testes acima

Um **bloco contíguo** de semanas de surto é uma sequência de semanas consecutivas, todas acima de um
limiar, sem interrupção. Contar "quantas semanas de surto" não é o mesmo que contar "quantos eventos de
surto independentes" — se 20 semanas seguidas estão todas acima de 100 casos, isso é **um único** episódio
de epidemia, não 20 observações independentes de "surto acontecendo".

Medido em 26/09/2026, sobre as 121 semanas avaliadas desde 2024 (maior semana individual: **2.381**
casos):

| Limiar | Semanas acima | Blocos contíguos | Maior bloco | Em 2024 | Em 2025 |
|---|---|---|---|---|---|
| 100 casos | 39 | **2** | 20 semanas | 20 | 19 |
| 140 casos | 38 | **2** | 20 semanas | 20 | 18 |
| 421 casos | 28 | **2** | 14 semanas | 14 | 14 |
| 702 casos | 23 | **2** | 12 semanas | 11 | 12 |

Fonte: `analises/2026-09-26_varredura_limiar_de_decisao/`.

### 8.10.2 O que isso muda nos testes de McNemar e Holm de §8.9

Os testes de McNemar tratam cada semana como uma observação. Mas se 39 "semanas de surto" vêm de apenas
**2 blocos contíguos** (essencialmente, as epidemias de 2024 e de 2025, cada uma vista semana a semana),
essas 39 observações **não são estatisticamente independentes** entre si — semanas vizinhas de uma mesma
epidemia tendem a se parecer (se o modelo acerta uma semana de um bloco, é mais provável que acerte a
seguinte, porque a dinâmica da epidemia muda devagar de uma semana para a próxima). Tratar semanas
correlacionadas como se fossem independentes tende a fazer os testes parecerem **mais confiantes do que
deveriam ser** — o chamado problema de graus de liberdade efetivos menores do que o número bruto de
observações.

Para medir esse efeito diretamente, o projeto rodou, em 26/09/2026, um **bloco-bootstrap**: em vez de
reamostrar semana a semana, reamostra-se em **blocos móveis** de tamanho fixo (4, 8, 13 e 26 semanas
testadas), preservando a correlação temporal dentro de cada bloco, com **2.000** reamostragens e semente
aleatória fixa (**20260926**, para reprodutibilidade). Compara-se o p-valor assim obtido com o p-valor
nominal (o do teste padrão que assume independência):

- **Nas comparações contra "hoje já passou de 100" (a régua mais fraca), a razão p-bootstrap/p-nominal
  ficou entre 0,0001 e 0,82** — ou seja, o bloco-bootstrap confirma que esses resultados são **robustos**
  à correlação temporal; corrigir por ela não enfraquece a conclusão, e em vários comprimentos de bloco
  até a reforça.
- **Nas comparações contra "o ano passado passou de 100" (a régua mais forte, onde o resultado já era
  não-significativo), a razão subiu para 1,10–1,51 em h=4 e para 2,11–3,44 em h=12** — isto é, o p-valor
  nominal já reportado como não-significativo estava, na verdade, **otimista demais**: contabilizando a
  correlação temporal real dos dados, o verdadeiro p-valor é ainda **maior** (menos significativo) do que
  o já reportado.
- **A consequência prática:** o bloco-bootstrap nunca inverte nenhuma conclusão desta seção — ele torna o
  resultado já positivo (contra a régua fraca) ainda mais confiável, e o resultado já negativo (contra a
  régua forte) **ainda mais claramente negativo**. Não há nenhum caso em que a correção de blocos
  transformaria um "não significativo" em "significativo".
- ⚠️ **Pendência declarada:** o resultado histórico de 13/09/2026 que sobrevivia à correção de Holm antes
  desta rodada (o vetor piora o alarme em h=12, p de Holm **0,037**, alvo notificados, quantil 90) **não
  pôde ser submetido a este mesmo bloco-bootstrap** — as previsões semana a semana daquela rodada foram
  calculadas em memória e descartadas antes de serem salvas em disco, e reconstruí-las exigiria retreinar
  os classificadores originais, proibido pela pré-declaração desta rodada ("nenhum modelo é treinado").
  Isso é registrado como uma lacuna de verificação, não como um resultado invalidado — apenas não
  confirmado quanto à robustez quando se leva em conta a correlação temporal.

---

## 8.11 Tabela final de síntese

| Categoria | Achado |
|---|---|
| **FATO, demonstrado com significância estatística** | WIS em 1 mês (h=4): cenário adotado **e** HistGB folha 20 vencem a régua climatológica, p de Holm **< 0,0001**, robusto ao bloco-bootstrap. |
| | Alarme (evento >100 casos), h=12: modelo vence a régua fraca "hoje já passou de 100", p de Holm **0,00062** (adotado) e **< 0,0001** (folha 20), robusto ao bloco-bootstrap. |
| | Alarme (evento >421 casos, estágio Alerta), h=12: modelo vence a mesma régua fraca, p de Holm **0,00014** (adotado) e **0,00008** (folha 20). |
| | Vazamento temporal de treino (achado histórico, 13/09/2026): corrigir o corte pela data da resposta (em vez da pergunta) aumentou o erro em h=12 em **+52%** e derrubou o R² de 0,758 para 0,437. |
| | Transformação de escala (raiz e log) **piora** a calibração nas 4 faixas de gravidade, sem exceção — critério pré-declarado, certificação adversarial aprovada em 26/09/2026 (não é teste de hipótese com p-valor, é medição direta contra critério fixado antes). |
| **FATO, medido, mas SEM significância estatística demonstrada** | Alarme, h=4, evento >100: modelo com sensibilidade 97,1% e Youden 0,94, mas McNemar não fecha contra nenhuma das duas réguas (p de Holm **0,103** e **1,000**) — direção a favor (13 de 15 e 5 de 7 pares discordantes), amostra pequena, provável falta de poder estatístico. |
| | Alarme, h=12, evento >100, contra "o ano passado": empate estatístico (Youden 0,66 do modelo contra 0,81 da régua), p de Holm **0,845** — divisão de pares discordantes (4 a 12) favorece a régua, mas sem significância. |
| | Alarme, evento >421 (Alerta): **0 de 4** combinações vencem "o ano passado" com p de Holm < 0,05. |
| | WIS em 3 meses (h=12): HistGB folha 20 vence a régua climatológica (p de Holm **0,0020**); o cenário adotado **não vence** (p de Holm **0,096**, perto do limiar convencional mas fora dele). |
| | Alarme contra o canal endêmico clássico (regra do tipo Singapura): modelo vence em Youden, mas sem significância (p bruto 0,034, p de Holm **0,40**). |
| | Bloco-bootstrap: comparações contra a régua forte ("o ano passado") ficam **ainda mais** longe da significância quando se corrige pela correlação temporal (razão p-bootstrap/p-nominal de até 3,44×) — reforça, não enfraquece, a categoria "sem significância". |
| **HIPÓTESE, não testada nesta rodada** | Que uma distribuição empírica dos resíduos por faixa de gravidade (em vez de 7 quantis treinados de forma independente) resolveria o cruzamento de quantis e a má calibração nos picos sem alargar demais o intervalo. |
| | Que um modelo único de regressão quantílica por floresta (onde a distribuição sai de uma vez, coerente por construção) eliminaria o cruzamento de quantis por desenho, em vez de precisar de correção posterior. |
| | Que uma conformal condicionada ao nível previsto (em vez da correção constante já testada e reprovada, que fez os falsos alarmes saltarem de 15 para 124) melhoraria a calibração nos picos sem esse efeito colateral. |
| | Que a causa raiz da subestimação nos picos seja **só** a escassez de exemplos de epidemia grande na série (2 epidemias documentadas) e não, adicionalmente, a ausência de variáveis-chave não medidas (sorotipo circulante do vírus, nível de imunidade da população, mobilidade urbana) — as duas causas são plausíveis e não mutuamente exclusivas, e nenhum teste feito até 26/09/2026 isola uma da outra. |

---

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

---

# Anexos

## Anexo A — Glossário e onde cada conceito é definido

Este índice existe para consulta pontual. A definição completa, com fórmula e exemplo numérico, está na
parte indicada.

### Termos de epidemiologia

| Termo | Em uma linha | Definido em |
|---|---|---|
| **Vetor** | O organismo que transporta o agente infeccioso entre hospedeiros — aqui, o mosquito *Aedes aegypti* | Parte 1.1 |
| **Sorotipo** | Uma das quatro variantes do vírus da dengue; a imunidade a uma não protege contra as outras | Parte 1.1 |
| **Endêmico** | Doença que circula de forma contínua e esperada numa população | Parte 1.2 |
| **Caso notificado** | Caso suspeito registrado no sistema, antes de qualquer confirmação laboratorial | Parte 3.3 |
| **Caso provável** | Caso suspeito que atende à definição clínica, sem descarte laboratorial | Parte 3.3 |
| **Caso confirmado** | Caso com confirmação laboratorial ou por critério clínico-epidemiológico | Parte 3.3 |
| **Município de notificação × de residência** | Onde o caso foi registrado × onde a pessoa mora; o projeto usa notificação | Parte 3.3 |
| **Semana epidemiológica** | Unidade padronizada de tempo da vigilância, que não coincide com a semana do calendário | Parte 2.1 |
| **Incidência** | Casos novos por unidade de população, em geral por 100 mil habitantes | Parte 4.15, retomada em 6.1 e 7.2 |
| **Canal endêmico** | Faixa do que se considera normal, construída a partir do histórico de anos anteriores | Parte 7.4 |
| **Índice de fêmeas por armadilha** | Média de fêmeas de *Aedes aegypti* capturadas por armadilha vistoriada | Parte 3.1 |

### Termos de modelagem e estatística

| Termo | Em uma linha | Definido em |
|---|---|---|
| **Série temporal** | Sequência de observações ordenadas no tempo | Parte 2.1 |
| **Horizonte** | Quantas semanas à frente a previsão é feita | Parte 2.2 |
| **Data de origem × data-alvo** | Quando a previsão é feita × a semana que ela descreve | Parte 2.2 |
| **Janela deslizante** (*walk-forward*) | Simular o uso real: prever, receber o valor verdadeiro, avançar | Parte 2.3 |
| **Vazamento temporal** | Usar no treino informação que não existiria na data da previsão | Parte 2.3 |
| **Árvore de regressão** | Modelo que divide os dados em grupos e prevê um valor constante por grupo | Parte 2.4 |
| ***Boosting*** | Conjunto de árvores em que cada uma corrige o erro das anteriores | Parte 2.4 |
| **Extrapolação** | Prever fora do intervalo de valores visto no treino; árvores não fazem | Parte 2.4 |
| **Erro absoluto médio** | Média do tamanho dos erros, sem considerar o sinal | Parte 2.5 |
| **Coeficiente de determinação** | Quanto da variação dos dados o modelo explica | Parte 2.6 |
| **Quantil** | O valor abaixo do qual cai uma dada fração das observações | Parte 2.7 |
| **Perda quantílica** | Função de custo que penaliza assimetricamente subestimar e superestimar | Parte 2.8 |
| **Intervalo de previsão** | Faixa dentro da qual o valor real deveria cair com dada frequência | Parte 2.10 |
| **Cobertura** | Quantas vezes o valor real de fato caiu dentro do intervalo | Parte 2.10 |
| **Escore de intervalo ponderado** | Métrica que avalia a distribuição prevista inteira, não só um número | Parte 2.11 |
| **Matriz de confusão** | Tabela dos quatro resultados possíveis de uma classificação binária | Parte 2.12 |
| **Sensibilidade** | Fração dos eventos reais que o alarme pegou | Parte 2.12 |
| **Precisão** | Fração dos alarmes disparados que eram eventos reais | Parte 2.12 |
| **Índice de Youden** | Sensibilidade mais especificidade menos um; resume o desempenho num número | Parte 2.12 |
| **Hipótese nula** | A afirmação de que não há diferença, que o teste tenta refutar | Parte 2.13 |
| **Valor-p** | A chance de observar um resultado tão extremo se a hipótese nula fosse verdadeira | Parte 2.13 |
| **Teste pareado** | Comparação feita observação a observação, na mesma data | Parte 2.13 |
| **Teste de McNemar** | Teste para classificação binária pareada; usa só os casos em que as regras discordam | Parte 2.13 |
| **Correção de Holm** | Procedimento que ajusta os valores-p quando vários testes são feitos juntos | Parte 2.14 |
| **Correlação serial** | Quando observações próximas no tempo se parecem, violando independência | Parte 2.15 |
| **Reamostragem por blocos** | Bootstrap que sorteia trechos contíguos, preservando a correlação serial | Parte 2.15 |
| **Viés × variância** | Erro sistemático numa direção × dispersão em torno do valor certo | Parte 2.16 |
| **Hiperparâmetro** | Ajuste escolhido antes do treino, que o modelo não aprende sozinho | Parte 2.17 |
| **Busca aleatória** | Sortear combinações de hiperparâmetros em vez de testar todas | Parte 2.17 |
| **Régua** (linha de base) | Regra simples, sem aprendizado, usada como padrão de comparação | Parte 4.15 |

---

## Anexo B — Índice das análises do repositório

Cada pasta está em `analises/` e contém, quando aplicável, pré-declaração, código, registro de execução,
certificação independente e emendas datadas.

### As análises que sustentam os números centrais deste documento

| Pasta | O que produziu |
|---|---|
| `2026-09-13_correcao_vazamento_treino` | A correção do vazamento temporal e o custo de **+52%** de erro |
| `2026-09-13_metrica_de_alarme` | As métricas de alarme por horizonte |
| `2026-09-25_regua_regras_simples` | As réguas e a constatação de que a sazonal vence em 2 e 3 meses |
| `2026-09-25_alarme_contra_canal_endemico` | O alarme contra as regras e contra o canal, com McNemar e Holm |
| `2026-09-25_limiar_oficial_de_surto` | Os quatro estágios do Plano Municipal e o adendo do Quadro 1 |
| `2026-09-25_busca_de_hiperparametros` | As 120 configurações |
| `2026-09-26_calibracao_por_faixa` | A cobertura por faixa e a largura do intervalo contra o erro |
| `2026-09-26_wis_na_tabela_restaurada` | O escore de intervalo ponderado na tabela oficial |
| `2026-09-26_varredura_limiar_de_decisao` | O limiar de decisão, o estágio Alerta e o bloco-bootstrap |
| `2026-09-26_transformacao_de_escala` | O resultado negativo de raiz e logaritmo |
| `2026-09-26_banca_adversarial` | A crítica aos três argumentos |
| `2026-09-26_ficha_da_silva_2026` | A ficha do estudo da mesma cidade |
| `2026-09-26_limiar_para_serie_curta` | Porto Rico, série curta e a aceleração de transmissão |

### Demais análises, em ordem cronológica

`2026-08-16_direcionamento_tese` · `2026-08-29_regeneracao_oficial` ·
`2026-08-29_rodadas_notificados_zonas` · `2026-08-30_alvo_e_features_infodengue` ·
`2026-08-30_calibracao_quantilica` · `2026-08-30_decomposicao_erro_cenario1` ·
`2026-08-30_features_longo_prazo` · `2026-08-30_grid_completo` · `2026-08-30_remedios_vies_pico` ·
`2026-08-30_teste_decisivo_alvos` · `2026-08-30_teste_focado_h12` ·
`2026-08-30_vetor_no_modelo_calibrado` · `2026-09-13_auditoria_mecanica_resultados` ·
`2026-09-13_janela_treino_casos` · `2026-09-21_limpeza_dados_para_envio` ·
`2026-09-23_bateria_noturna` · `2026-09-23_janela_de_lag` · `2026-09-25_atualizacao_dados_2026` ·
`2026-09-25_bateria_formulacao_do_alvo` · `2026-09-25_catalogo_modelos_prontos` ·
`2026-09-25_comparacao_direta_literatura` · `2026-09-25_modelos_de_fundacao` ·
`2026-09-25_notificacoes_como_alvo` · `2026-09-25_novas_fontes_oficiais` ·
`2026-09-25_sarima_lasso_ensemble` · `2026-09-25_segunda_bateria_noturna` ·
`2026-09-25_varredura_literatura`

### Documentos vivos do repositório

| Documento | O que responde |
|---|---|
| `CLAUDE.md` | Onde fica o quê, e o que nunca se faz |
| `PENDENCIAS.md` | O que está em aberto e quem destrava |
| `ESTADO.md` | O que o sistema é hoje |
| `HISTORICO_DE_TESTES.md` | O que já foi perguntado, medido e concluído |

---

## Anexo C — Referências

### Artigos e documentos usados

1. **da Silva, A. A.; Ferreira, Á. G. A.; Lourenço, J.; Cupertino de Freitas, A.** (2026). *Climate-driven
   spatiotemporal dynamics of Aedes infestation and dengue transmission in Porto Alegre.* Preprint no
   medRxiv, 02/04/2026. DOI 10.64898/2026.03.31.26349860.
   ⚠️ **Não revisado por pares.** Estudo da mesma cidade e da mesma rede de armadilhas.
2. **Centers for Disease Control and Prevention** (2025). *Dengue Outbreak and Response — Puerto Rico,
   2024.* Morbidity and Mortality Weekly Report, mm7405a1, 20/02/2025. Lido via PMC12370255.
3. **Dengue epidemic alert thresholds, a tool for surveillance and epidemic detection.* Preprint no
   medRxiv, DOI 10.1101/2024.10.22.24315684.
   ⚠️ **Texto completo não lido** — acesso bloqueado (erro 403). Usado apenas pelo que o item 2 relata.
4. **Bracher, J.; Ray, E. L.; Gneiting, T.; Reich, N. G.** (2021). *Evaluating epidemic forecasts in an
   interval format.* Origem do escore de intervalo ponderado usado neste trabalho.
5. **Chernozhukov, V.; Fernández-Val, I.; Galichon, A.** (2010). *Quantile and probability curves without
   crossing.* Origem do reordenamento de quantis cruzados.
6. **Bergstra, J.; Bengio, Y.** (2012). *Random search for hyper-parameter optimization.* Origem da regra
   de 60 sorteios usada na busca de hiperparâmetros.
7. Artigo sobre **aceleração de transmissão**, lido na íntegra via PMC13228775. Regra da razão entre média
   móvel de 4 e de 26 semanas.
8. **Nature Communications** (2024), s41467-024-48465-0. Limiares fixos de incidência em área de invasão
   da dengue.
9. **Chen, Y. et al.** (2020), lido via PMC7318238. Previsão de dengue em Singapura.
10. **Secretaria Municipal de Saúde de Porto Alegre** (dezembro de 2025). *Plano Municipal de Contingência
    de Arboviroses 2026.* Quadro 1, página 15.

### ⚠️ Afirmações que NÃO devem ser citadas como fato

Estas apareceram em buscas mas **não** foram confirmadas em fonte primária legível, e por isso não
sustentam afirmação neste documento nem fora dele:

- O limiar oficial de epidemia do Ministério da Saúde (as buscas retornaram 100 e 300 por 100 mil
  habitantes, sem documento primário acessível).
- A janela histórica exata que o InfoDengue usa em produção (as fontes divergiram entre 10, 14 e "de 3 a
  16 anos").
- O texto completo do preprint do método de Porto Rico.

---

## Anexo D — Índice das fórmulas

| Fórmula | Para que serve | Parte |
|---|---|---|
| Erro absoluto médio | Medir o tamanho típico do erro | 2.5 |
| Coeficiente de determinação | Medir quanto da variação foi explicada | 2.6 |
| Perda quantílica | Treinar o modelo com penalidade assimétrica | 2.8 |
| Razão de penalidade τ/(1−τ) | Traduzir o quantil em custo relativo dos dois erros | 2.8 |
| Equivalência quantil ↔ probabilidade | Fundamentar o uso da previsão como alarme | 2.9 |
| Cobertura de intervalo | Verificar se a incerteza declarada é honesta | 2.10 |
| Escore de intervalo | Avaliar um nível de intervalo | 2.11 |
| Escore de intervalo ponderado | Avaliar a distribuição prevista inteira | 2.11 |
| Sensibilidade, especificidade, precisão | Avaliar o alarme | 2.12 |
| Índice de Youden | Resumir o alarme num número | 2.12 |
| Teste de McNemar exato | Comparar duas regras de alarme pareadas | 2.13 |
| Correção de Holm | Ajustar os valores-p de vários testes | 2.14 |
| Reamostragem por blocos móveis | Corrigir o valor-p sob correlação serial | 2.15 |
| Índice de fêmeas por armadilha | Medir a presença do vetor | 3.1 |
| Conversão de incidência em casos por semana | Traduzir os estágios do plano municipal | 7.2 |
| Captura do pico | Medir a subestimação da magnitude das epidemias | 8.3 |

---

## Anexo E — Estado do documento

**Escrito em 26/09/2026.** Reflete o repositório até o commit daquela data.

**Como foi produzido:** a arquitetura, os números canônicos e as Partes 0, 1 e os Anexos foram escritos
pelo orquestrador; as Partes 2 a 9 foram escritas em paralelo por oito autores independentes, cada um
recebendo o mesmo conjunto de números verificados e a instrução de reportar divergência em vez de
corrigir sozinho. Em seguida o documento passou por uma conferência número a número contra os arquivos de
origem.

### Conferência número a número

Depois da primeira montagem, cinco verificadores independentes conferiram o documento contra os arquivos
de origem, um deles dedicado apenas a incoerências entre partes. Encontraram **12 problemas**: 6 graves,
4 médios e 2 leves. **Todos os 6 graves e os 4 médios foram corrigidos**; a lista completa, com o trecho
original e a fonte que decidiu cada caso, está em `CORRECOES_PENDENTES.md`, mantida como registro.

**As correções graves aplicadas:**

1. 🔴 **Contradição interna sobre significância** (Parte 4). O texto afirmava que o modelo vence as réguas
   em 1 mês "com significância estatística", enquanto a mesma parte, 150 linhas antes, reportava os
   valores-p de Holm de **0,103** e **1,000** como não significativos. Reescrito para separar o que tem
   significância (o escore de intervalo ponderado contra a régua climatológica) do que não tem (o alarme).
2. 🔴 **Número de pares avaliados** (Partes 4 e 8). A tabela do painel dizia 295, 292, 288 e 284. O valor
   correto é **102** nos quatro horizontes — é o que reproduz os erros e os coeficientes citados na mesma
   tabela. Erro originado nos números canônicos fornecidos aos autores.
3. 🔴 **A variante de alvo em logaritmo** (Parte 5). O texto dizia "redução de 23,0% frente ao controle".
   Na verdade o erro **piora 9,90%** contra o controle e **23,01%** contra a régua sazonal — dois
   comparadores diferentes. Erro originado nos números canônicos.
4. 🔴 **Atribuição do bootstrap por blocos** (Parte 2). As razões de inflação do valor-p foram apresentadas
   junto da contagem de blocos do evento de 100 casos, mas pertencem ao evento de **421 casos**. Não
   existe no repositório bootstrap rodado para o limiar de 100.
5. 🔴 **Especificidade** (Partes 2 e 9). O valor 0,969 vinha de arredondar antes de subtrair; o valor
   medido é **0,9706**. Corrigido nos dois lugares, com uma nota sobre a armadilha de arredondamento.
6. 🔴 **Colunas brutas de clima** (Parte 3). Eram 22, não 20. O total de 42 estava certo, mas a conta
   apresentada escondia duas colunas.

**As correções médias aplicadas:** arredondamento do índice de Youden em 3 meses (0,80 e 0,11, não 0,81 e
0,12); a âncora da formulação de resíduo está **acima** do teto do treino, e não próxima dele, o que muda
a causa explicada da explosão; cinco referências cruzadas quebradas na Parte 6, com a definição da raiz do
erro quadrático médio acrescentada onde faltava; e a entrada de "incidência" no glossário, que apontava
para a Parte 7 ignorando que o termo aparece antes.

⚠️ **Um problema leve permanece, declarado:** dentro da Parte 2, os termos "hiperparâmetro" e "quantil"
são mencionados algumas páginas antes de sua definição formal, ainda que ambas cheguem antes do fim da
parte. Corrigir exigiria reordenar a seção inteira, e o custo não se justifica.

### Divergências encontradas já durante a escrita

1. 🔴 **Erro nos números canônicos fornecidos aos autores.** O informe dizia que a variante de alvo em
   logaritmo perdia **23,0%** para o controle em horizonte de 12 semanas. O número correto é **9,9%**
   contra o controle; os 23,0% são a diferença contra a **régua sazonal**, que é outro comparador. O autor
   da Parte 4 detectou, reportou e usou o número correto. Corrigido em todo o documento.
2. **Diferença de 0,1 no erro em 12 semanas** entre o painel publicado (278,7) e o recálculo (278,8).
   Ambos aparecem, com a origem de cada um.
3. **O tamanho da família de correção múltipla** no evento de 100 casos foi reconstruído numericamente
   por um dos autores, e confere: são **16** testes.

⚠️ **O que este documento não cobre:** a camada espacial por bairros, a previsão do próprio vetor como
alvo e os resultados anteriores a 16/08/2026, que foram em grande parte refeitos após a correção do
vazamento temporal de 13/09/2026.
