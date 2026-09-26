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
