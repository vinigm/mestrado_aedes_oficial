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
