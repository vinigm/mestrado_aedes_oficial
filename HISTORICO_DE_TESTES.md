# HISTÓRICO DE TESTES — o que já foi perguntado, medido e concluído

> **Para que serve este documento.** Cada teste que o projeto rodou está aqui: **por que** foi feito,
> **como** foi medido, **o que deu** e **o que se pode afirmar**. É o registro que sobrevive à memória.
> Leitura deliberada, não de toda sessão.
>
> Retrato do sistema hoje: [ESTADO.md](ESTADO.md) · Fila viva: [PENDENCIAS.md](PENDENCIAS.md)
> Detalhe de cada teste: pasta datada em `analises/`
>
> Atualizado em **13/09/2026**.

---

## Como ler

**Rótulos de evidência**, usados em todo o documento:

| Rótulo | Significa |
|---|---|
| ✅ **FATO** | Medido, com número, e sobrevive ao escrutínio que se aplicou. |
| ⚠️ **EXPLORATÓRIO** | A hipótese nasceu destes mesmos dados, ou faltou correção de múltiplas comparações. Não vira frase de tese sem novo dado. |
| 🔬 **HIPÓTESE** | Ainda não medido. |
| 🚫 **REFUTADO** | Foi medido e não se sustentou. Fica aqui com lápide, para não voltar como ideia-zumbi. |
| ⏳ **EM ABERTO** | Falta rodar ou falta decidir. |

**Três palavras de jargão** que aparecem o tempo todo:

- **Walk-forward** — treina só com o passado, prevê uma semana, avança, repete. É a simulação honesta de uso real.
- **Holm** — correção para múltiplas comparações. Se você testa 60 coisas, alguma dá "significativa" por sorte; Holm ajusta o limiar. **Regra do projeto: sem sobreviver a Holm, não se escreve "significativo".**
- **Pareado** — os dois modelos comparados previram exatamente as **mesmas semanas**. Sem isso, a diferença mistura efeito do modelo com efeito da amostra.

**Um aviso que vale para tudo antes de 13/09/2026:** um vazamento temporal inflava os resultados de horizonte longo. Ver [§6.1](#61-o-vazamento-temporal-no-corte-de-treino). Cada teste abaixo diz se foi refeito.

---

## Índice cronológico

| Data | Teste | Veredito de hoje |
|---|---|---|
| 16/08/2026 | Teste A — equivalência clima × vetor | 🚫 superado pela Rodada 2 |
| 16/08/2026 | Teste B — sinal espacial: bairro ou zona? | ✅ zona, não bairro |
| 16/08/2026 | Teste C — poder com notificados | 🚫 era projeção, refutada na prática |
| 29/08/2026 | Rodada 0 — recaptura do clima desde 2012 | ✅ 388 → 727 semanas |
| 29/08/2026 | Rodada 1 — vetor no alarme de surto | ✅ negativo, hoje reforçado |
| 29/08/2026 | Rodada 2 — equivalência na série longa | 🚫 refutado em 13/09 |
| 29/08/2026 | Rodada 3 — ranking espacial | ✅ regra simples vence o ML |
| 29/08/2026 | Rodada 4 — janela de treino | ✅ desde 2012 vence |
| 29/08/2026 | Regeneração oficial — confirmados × notificados | 🚫 o achado que sobrevivia a Holm era vazamento |
| 30/08/2026 | Decomposição do erro — por que o pico é subestimado | ✅ causa identificada |
| 30/08/2026 | Remédios do viés de pico | ✅ perda quantílica vence |
| 30/08/2026 | Calibração quantílica — qual alpha | ✅ superado pelo grid |
| 30/08/2026 | Vetor no modelo calibrado | ⚠️ 6 de 8, nada em Holm |
| 30/08/2026 | Grid completo — 120 execuções | 🚫 refeito em 13/09 |
| 30/08/2026 | Features de longo prazo | ⏳ só ENSO passou, não validado |
| 30/08/2026 | Alvo e features do InfoDengue | ✅ alvo = confirmados |
| 30/08/2026 | Teste decisivo de alvos | ✅ janela equalizada derruba o achado |
| 30/08/2026 | Teste focado em h=12 | ⚠️ 5 sementes, nada em Holm |
| 13/09/2026 | Auditoria da mecânica dos resultados | ✅ vazamento descoberto |
| 13/09/2026 | Correção do vazamento — 152 células | ✅ tudo remedido |

---

## 1. O modelo consegue prever casos de dengue em nível cidade?

### 1.1 A configuração de referência — grid de 120 execuções

**Por quê.** Até 30/08 o projeto usava LightGBM porque era o que estava à mão. Nunca se testou se era a
melhor escolha, nem se a função de perda importava.

**Como.** Grade completa: **3 algoritmos × 5 funções de perda × com/sem vetor = 30 configurações**, cada
uma nos horizontes 1, 4, 8 e 12 semanas. 120 execuções de walk-forward. Vencedor escolhido pelo menor
erro médio no período de **calibração** (até 31/12/2023); o período de **avaliação** (2024+) ficou
guardado como juiz. Refeito integralmente em 13/09 com o corte de treino corrigido.

**O que deu.**

✅ **FATO — a configuração de referência é HistGradientBoosting, perda quantílica em 0,85, com vetor.**

| Horizonte | MAE | R² | Captura do pico |
|---|---|---|---|
| 1 semana | 98,0 | **0,898** | 0,886 |
| 4 semanas | 219,7 | **0,628** | 0,702 |
| 8 semanas | 272,6 | **0,450** | 0,417 |
| 12 semanas | 278,7 | **0,437** | 0,388 |

- **O modelo é honesto até um mês.** Em quatro semanas ele explica 63% da variação. Em três meses, 44%.
- ⚠️ **A previsão quantílica não estima a média.** Ela estima um **patamar** ultrapassado em 15% das
  vezes. É enviesada para cima de propósito, porque subestimar surto custa mais caro. Qualquer texto
  que cite uma previsão precisa dizer isso.
- ⚠️ Escrever sempre **"a melhor entre as 30 testadas"**, nunca "a melhor possível".

### 1.2 O que faz o modelo piorar com o horizonte

✅ **FATO — a autocorrelação dos casos morre com o horizonte.** R² de prever `casos[t+h]` usando só
`casos[t]`, medido em 13/09/2026:

| h | 1 | 2 | 4 | 8 | 12 |
|---|---|---|---|---|---|
| R² | **0,915** | 0,804 | 0,527 | 0,080 | **0,000** |

A frase que circulava no projeto ("91% em h=1 e 0% em h=12") estava certa, mas **não tinha script**.
Agora tem: `analises/2026-09-13_metrica_de_alarme/`.

**Consequência:** em três meses o passado recente dos casos não informa nada. Não adianta trocar de
algoritmo nem acrescentar feature — o sinal não está lá.

### 1.3 O modelo subestimava sistematicamente os picos

**Por quê.** O erro nas semanas de epidemia era muito maior que a média, e sempre para baixo.

**O que deu.** ✅ **FATO — a causa foi identificada e a hipótese óbvia foi refutada.**

- 🚫 **Não é limite de extrapolação das árvores.** Testado: o teto do treino era 1.439 casos e o pico
  médio 829. Só 5 de 32 picos ficavam acima do teto.
- ✅ A causa é a **assimetria da série**: 61% das semanas têm 5 casos ou menos, o que puxa a previsão
  para o centro.
- ✅ O remédio validado é a **perda quantílica**, única entre quatro testadas que reduziu o viés nos
  quatro horizontes.

⚠️ A escolha do remédio foi leitura de tabela, sem pré-declaração nem teste formal.

---

## 2. A armadilha ajuda a prever o número de casos?

**Esta é a pergunta central da tese.** Foi atacada por quatro caminhos independentes de desenho.

### 2.1 O teste decisivo — 60 comparações pareadas

**Como.** No grid corrigido existem **15 pares**: mesmo algoritmo, mesma perda, mudando só a presença
das colunas do vetor. Cada par nos 4 horizontes = 60 comparações, todas **pareadas por data-alvo**,
com Diebold-Mariano e Holm sobre a família inteira.

**O que deu.**

| | Com vazamento | **Corrigido** |
|---|---|---|
| O vetor erra menos em | 35 de 60 | **27 de 60** |
| Sobrevivem a Holm | 0 | **0** |

Por horizonte, ganho médio de erro:

| h | Corrigido |
|---|---|
| 1 | 0 de 15 · **−12,5** |
| 4 | 11 de 15 · +8,5 |
| 8 | 3 de 15 · **−15,3** |
| 12 | 13 de 15 · +22,5 |

✅ **FATO — o vetor não tem efeito demonstrável na previsão de casos.** Perde na maioria das 60
comparações e nada sobrevive a Holm.

⚠️ **E onde ele ganha, ganha por um motivo desconfortável.** Em h=12 os cinco maiores ganhos são as
cinco configurações de **LightGBM**, o pior algoritmo (+61,8 a +29,4). O HistGradientBoosting, melhor
algoritmo, fica entre **+8,9 e −11,2**. O vetor **compensa algoritmo fraco**: LightGBM sem vetor erra
286 a 329 e com vetor cai para 236 a 272, chegando perto do que o HistGB já faz **sem** vetor.

### 2.2 Vetor no lugar do clima — a equivalência (Rodada 2)

**Por quê.** Se a armadilha empatasse com o clima, a tese teria um núcleo: a rede não é redundante.
Foi promovida a núcleo em 29/08 e **caiu em 13/09**.

**Como.** TOST, o teste de equivalência, sobre 4 conjuntos (clima puro, vetor puro, e os dois com
autorregressivo de casos) × 4 horizontes, nos dois alvos. 576 a 587 semanas pareadas.

🚫 **REFUTADO em 13/09/2026.** Dois erros somados:

- **A margem estava errada.** A pré-declaração de 29/08 fixou a margem em % do erro da **persistência**;
  o código usou % do erro do **clima**. Em uma semana isso é 6,8 contra 27,5 — régua quatro vezes maior.
- **O alvo estava errado.** Os "4 de 8" são de **notificados**; o alvo decidido é **confirmados**.

| Alvo | Margem do código | **Margem pré-declarada** |
|---|---|---|
| **Confirmados** (o decidido) | 0 de 8 | **1 de 8** |
| Notificados | 4 de 8 | **0 de 8** |

E não é superioridade disfarçada: em h=1 o vetor ganha por 23,0 de erro (p bruto 0,049), mas o
intervalo de confiança inclui zero e com Holm vira 0,388. **O único intervalo que exclui zero é contra
o vetor**: em três meses o clima ganha por 72,5.

### 2.3 Vetor além do clima, sem autorregressivo

⚠️ **EXPLORATÓRIO.** Prevendo casos só com clima contra clima mais vetor:

| h | Só clima | Clima + vetor |
|---|---|---|
| 8 | 0,089 | 0,201 |
| 10 | **−0,045** | 0,128 |
| 12 | **−0,024** | 0,106 |

✅ **FATO — o clima sozinho não prevê casos em 10 a 12 semanas.** R² zero ou negativo.
⚠️ O vetor segura R² em 0,11 a 0,13 ali. Mas este experimento **não grava p-valor nem MAE**, só R², e
usa a mesma tabela dos outros. Não é evidência independente.

### 2.4 Diebold-Mariano pareado na pipeline

Com LightGBM e perda padrão, o vetor era melhor em **10 de 12** horizontes e caiu para **4 de 12** após
a correção. Melhor p bruto: 0,065 → 0,270.

### 2.5 Síntese da pergunta 2

✅ **FATO — a armadilha não melhora a previsão de casos de dengue em nível cidade, de forma
demonstrável.** Quatro desenhos diferentes, nenhum sobrevive a Holm, e o único intervalo de confiança
que exclui zero aponta contra.

🔬 **Não confundir com "a armadilha é inútil".** O que foi medido é uma tarefa específica: prever
contagem de casos, em nível cidade, com esta série. Não se mediu utilidade operacional, nem valor para
o controle vetorial, nem previsão do próprio mosquito.

---

## 3. A armadilha ajuda a antecipar surtos?

**Por quê.** Prever o número exato é difícil; disparar um alarme é mais fácil e mais útil para a
vigilância. Talvez o vetor sirva aqui, ainda que não sirva na regressão.

**Como.** Classificador. Uma semana é "surto" se os casos de h semanas à frente ficarem acima de um
percentil calculado **só com o treino daquele passo** — sem espiar o futuro. Compara-se "só clima"
contra "clima + vetor" pelo teste de McNemar, que conta em quantas semanas um acerta e o outro erra.

### 3.1 🔴 O resultado mais forte do projeto, e ele é negativo

✅ **FATO — o vetor PIORA o alarme de surto em três meses, e isso sobrevive a Holm.**

Alvo notificados, percentil 90, h=12, n=553:

| | Antes da correção | **Corrigido** |
|---|---|---|
| Clima acerta × vetor acerta | 14 × 10 | **23 × 7** |
| p bruto | 0,541 | **0,0062** |
| p com Holm | 1,000 | **0,037** ✅ |

**É o único resultado que o projeto inteiro já produziu que sobrevive a correção de múltiplas
comparações.** Antes eram 0 de 6; agora é 1 de 6, e aponta contra a armadilha.

**Por que faz sentido.** Com o vazamento, as colunas do vetor conseguiam pagar seu próprio custo de
complexidade espiando o rótulo das semanas vizinhas, e o resultado ficava nulo. Sem vazamento elas
aparecem pelo que são em horizonte longo: **ruído que degrada o classificador**.

⚠️ **Rotular como robusto porém não pré-declarado.** A direção "o vetor piora" não estava escrita antes
de rodar. Vira confirmatório só com uma temporada nova.

### 3.2 🚫 O achado de 29/08 que parecia forte era vazamento

Em 29/08, com alvo confirmados, percentil 90, h=12, o resultado foi **4 × 24 a favor do vetor, p de
0,00018, Holm 0,00108**. Era o único resultado positivo que sobrevivia a Holm.

🚫 **Derrubado por dois caminhos independentes:**

1. **30/08, teste decisivo:** equalizando a janela (só denominador exato, ambas as séries presentes),
   virou 9 × 16, p = 0,230.
2. **13/09, correção do vazamento:** na janela original, virou **10 × 16, p = 0,327**.

O menor p do experimento inteiro foi de 0,00018 para 0,143.

### 3.3 Rodada 1 — o negativo bem-powered

✅ **FATO.** Com 565 semanas e 116 de surto, **0 de 6** comparações sobreviviam a Holm e o efeito
**inverteu de sinal** em relação a 16/08. A assimetria de 4 × 14 que animou o projeto era ruído
amostral.

---

### 3.4 A métrica de alarme que faltava

**Por quê.** A "captura do pico" é `média(previsto) ÷ média(real)` nas semanas acima de 100 casos —
razão de nível, não alarme. Não dizia quantos surtos seriam sinalizados nem com quanta antecedência.

**Como.** Re-agregação das previsões já salvas do grid corrigido, sem rodar nada. Sensibilidade,
precisão e falsos por ano, com o mesmo limiar de 100 casos. A antecedência é o próprio horizonte.

✅ **FATO — o modelo é um alarme melhor do que a métrica antiga sugeria.**

| h | Sensibilidade | Precisão | Falsos/ano | Captura do pico |
|---|---|---|---|---|
| 1 semana | 96,9% | 91,2% | 1,0 | 0,886 |
| 4 semanas | **97,1%** | **94,3%** | **0,7** | 0,702 |
| 8 semanas | 81,6% | 86,1% | 1,7 | 0,417 |
| 12 semanas | **76,9%** | 81,1% | 2,3 | 0,388 |

As duas métricas discordam porque medem coisas diferentes: a captura mede se o modelo acerta o
**tamanho** da epidemia (não acerta, subestima); o alarme só precisa cruzar o **limiar**.

⚠️ **EXPLORATÓRIO — no alarme, o vetor ajuda.** Pareado: em h=12 a sensibilidade sobe de 61,5% para
**76,9%**; em h=4 corta os alarmes falsos pela metade. Sem pré-declaração e sem teste.

🔴 **Ressalvas que precisam acompanhar qualquer citação:** só há **2 episódios** no período de
avaliação, então toda métrica por episódio é inútil; são 32 a 39 semanas de surto; e não há teste de
significância.

⚠️ **Tensão declarada com §3.1.** No experimento de surto o vetor **piora** o alarme (Holm 0,037);
aqui ele ajuda. Alvos diferentes (notificados × confirmados) e métodos diferentes (classificador com
percentil × regressor cortado em 100). Não se escolhe a leitura conveniente: as duas vão no texto.

## 4. Onde? A camada espacial

### 4.1 Bairro é ruído; zona sintética funciona

✅ **FATO (16/08).** O número semanal por bairro tem **31% de ruído de amostragem** (split-half 0,69).
Agrupando armadilhas em zonas por k-means sobre a posição geográfica, sobe para **0,92** com k=8.

🚫 **Bairro administrativo descartado** como granularidade em 16/08/2026.

### 4.2 O aprendizado de máquina perde para uma regra de uma linha

**Como.** Prever o ranking das zonas em t+h. Três competidores: o modelo (LightGBM), a **persistência**
("a ordem de hoje vale para daqui a h semanas") e a **climatologia** (a média histórica daquela época
do ano). Medida: correlação de Spearman entre ranking previsto e real.

✅ **FATO — a regra simples vence o modelo em 8 de 8 combinações.**

| | Modelo vence a persistência |
|---|---|
| Antes da correção | 1 de 8 |
| **Corrigido** | **0 de 8** |

A persistência e a climatologia **não treinam**, então não tinham vazamento. A queda foi toda do
modelo: em k=8 e h=8, de 0,536 para 0,321.

✅ **FATO — mas o sinal espacial é real.** Persistência 0,89 contra climatologia 0,46 em uma semana. O
ranking das zonas não é só a sazonalidade da cidade.

**Leitura para a tese.** Isto não é derrota, é entrega: um **protocolo de priorização de zonas
transparente, auditável e sem infraestrutura**, que bate o ML. Para vigilância isso é vantagem.

---

## 5. Que dados usar?

### 5.1 O alvo: casos confirmados

✅ **FATO (30/08).** Testados três candidatos na configuração vencedora. **Confirmados vencem**:
R² em h=12 de 0,758 contra 0,418 dos notificados (números da época, com vazamento; a direção se mantém).

🚫 **`casos_est`, o nowcasting do InfoDengue, é a MESMA série que os notificados** — idêntica em 99,1%
das semanas. A hipótese de que ele "desacharia" os picos históricos estava errada.

Fecha uma pendência aberta desde junho de 2026.

### 5.2 A janela de treino: desde 2012

**Por quê.** Mais dados ajudam ou atrapalham? Dados antigos podem ser de um regime diferente.

✅ **FATO — treinar desde 2012 vence em 3 de 4 horizontes**, e a vantagem cresce com o horizonte.
Medido corrigido em 13/09 (erro na densidade do vetor, menor é melhor):

| h | Deslizante 6 anos | **Expansível 2012** | Expansível 2020 |
|---|---|---|---|
| 4 | 0,19 | **0,17** | 0,18 |
| 8 | 0,21 | **0,19** | 0,20 |
| 12 | 0,23 | **0,20** | 0,22 |

Os 14 anos resgatados **melhoram a previsão**, não são só volume.

⏳ **Em aberto:** esta ablação usa como alvo a **densidade do vetor**. A mesma pergunta para o alvo
**casos** nunca foi testada. Nota: para casos, a série já começa em fev/2018 (428 semanas), então não
existem "14 anos de casos".

### 5.3 Features novas: quase todas reprovadas

🚫 **Quatro de cinco famílias reprovadas em 30/08/2026**: lags anuais (52 e 104 semanas), anomalia
climática, acúmulo de 8 a 12 semanas, e as features de transmissão do InfoDengue (`Rt`, `p_rt1`,
`notif_accum_year`).

⏳ **Só o ENSO passou** (~7% de MAE em h=8), e **nunca foi validado dentro do grid**. É candidato, não
parte da configuração.

### 5.4 O clima da série longa

✅ **FATO (29/08).** A captura de clima começava em 2018 por causa de um bloco de dados que já tinha
saído do fluxo. Corrigido para 2012: **388 → 727 semanas**. Certificação adversarial conferiu 365 das
388 semanas antigas idênticas; as 23 divergentes são reprocessamento normal da NASA. Vetor e casos
intocados.

---

## 6. Metodologia — o que aprendemos sobre medir

**Esta seção é candidata a contribuição própria da tese.** São erros que a literatura da área comete.

### 6.1 O vazamento temporal no corte de treino

**O defeito.** Cada linha da tabela tem **duas datas**: a da pergunta (origem, de onde vêm as features)
e a da resposta (origem + horizonte). O código selecionava o treino pela data da **pergunta**. Com isso,
as **h−1** linhas mais recentes do treino carregavam resposta datada **depois** da semana prevista.

**Exemplo concreto.** Ao prever 26/05/2024 a partir de 03/03/2024 com h=12, o treino incluía a linha de
18/02/2024, cujo rótulo é 12/05/2024 = **1.510 casos**, o pico da epidemia. Em 03/03 esse número não
existia.

**Quanto contamina:** 0 linhas em h=1, 3 em h=4, 7 em h=8, **11 em h=12**. São 5,1% do treino em média,
mas são as **11 semanas imediatamente anteriores** — os vizinhos mais próximos no espaço de features.

**A correção.** Filtrar por **data**, nunca por posição: só entra a linha cuja resposta já tinha
acontecido. Centralizada em `modelagem_aedes/motor/corte_temporal.py`.
Na literatura chama-se *purging*; o scikit-learn tem o parâmetro `gap` em `TimeSeriesSplit` para isso.

**O custo, medido:**

| h | MAE sobe | R² cai |
|---|---|---|
| 4 | +31,5% | 0,779 → 0,628 |
| 8 | +46,8% | 0,724 → 0,450 |
| 12 | +52,5% | 0,758 → 0,437 |

✅ **FATO — e o vazamento não era neutro entre configurações.** Punição na correção:

- conjuntos **com vetor** apanharam ~**2×** mais que os sem vetor (20,5% × 11,3%);
- perda **quantílica** apanhou ~**2×** mais que a padrão (28,7% × 15,8%).

**Vetor e perda quantílica eram exatamente os dois ingredientes da configuração escolhida.** O
vazamento estava sustentando as escolhas do projeto.

**O controle que valida tudo isso:** em h=1 nenhuma linha é contaminada, então o resultado corrigido
tem de ser idêntico. Verificado em **6 experimentos independentes**, com diferença **0,0000000000** em
mais de 12.000 pontos.

### 6.2 🚫 "A função de perda importa mais que o algoritmo" — refutado

Era a crítica metodológica mais forte do projeto. Não sobreviveu:

| Trocar | Antes | **Depois** |
|---|---|---|
| Melhor algoritmo pelo melhor LightGBM | +16,5% | **+11,8%** |
| Quantílico por padrão | +20,2% | **+9,9%** |

A ordem inverteu. E o efeito da perda **depende do algoritmo**: +9,9 pontos no HistGB, +8,0 no
GradientBoosting, **−1,9 no LightGBM**.

**O que sobra, mais fraco e ainda publicável:** a função de perda tem efeito **comparável** ao do
algoritmo e é condicional a ele — e a literatura compara algoritmos sem discutir perda.

### 6.3 Comparação não pareada

Comparar dois modelos avaliados em **semanas diferentes** mistura efeito do modelo com efeito da
amostra. No `grid_resumo` o conjunto com vetor perdia 7 origens de avaliação (109 → 102), incluindo as
**três semanas da enchente de maio/2024** (1.347, 911 e 1.510 casos), porque o vetor é NaN nelas.

Restringindo às mesmas semanas, o erro do M0 em h=1 **cai 18,5%** e a vantagem aparente do vetor
**inverte**.

⏳ **Dívida técnica aberta:** `rodar_regressao_selecao_clima` continua não pareando.

### 6.4 A margem de equivalência precisa ser pré-declarada em unidade fixa

A margem do TOST foi definida como % do erro **do próprio clima** medido naquele teste. Isso é
circular: **quanto pior o clima prevê, mais larga fica a régua que o aprova**. A pré-declaração mandava
usar a persistência, que é um referencial externo.

**Lição:** margem de equivalência se ancora em algo que não depende do resultado.

### 6.5 Rastreabilidade: script perdido

O ranking que escolheu a configuração de referência em 30/08 foi calculado por código que **não ficou
salvo**. Reconstruído em 13/09 (`resumir.py`), validado contra as tabelas originais com diferença
10⁻¹⁴ e as 30 posições idênticas.

**Lição:** a saída sem o script que a gerou não é auditável.

### 6.6 Um número que circula há meses e não se reproduz

🚫 **RESOLVIDO em 13/09/2026 — o número estava errado.** Medido dos próprios dados:

| Ano | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Taxa de confirmação | **73,2%** | **69,3%** | 60,1% | **38,3%** |

- A série **"99,6% em 2023 → 42,0% em 2025"**, em `PENDENCIAS` e em `modelagem_aedes/acesso/fontes.py`,
  usada como argumento para trocar o alvo: **não bate**. O real é 69,3% e 38,3%.
- A série **"73,2% em 2022 → 38,3% em 2025"**, da pré-declaração de `alvo_e_features_infodengue`:
  **bate exatamente**.

A direção da alegação (a taxa despencou) se sustenta; o valor de 2023 não. ⏳ Corrigir o docstring de
`fontes.py`.

**Lição:** número que entra em documento sem script que o gere sobrevive por meses e vira argumento.
A direção da alegação (a taxa caiu muito) se sustenta; o valor de 2023 não.

### 6.7 Seleção de variáveis fora do walk-forward

⏳ **Em aberto.** As 6 colunas de clima são escolhidas **uma vez**, sobre os 60% iniciais da série, e
reaproveitadas em todos os cortes. Cerca de 140 dos ~300 cortes preveem com colunas escolhidas usando
dado posterior à própria origem. **A correção de 13/09 não toca nisso.**

Além disso, o ranking é **instável**: recortando a série em 2023, **4 das 6 colunas mudam**. "Estas 6
variáveis de clima são as que importam" não é afirmação defensável.

---

## 7. Testes descartados, com lápide

Ideias medidas e enterradas. Ficam aqui para não voltarem.

| Ideia | Descartada em | Por quê |
|---|---|---|
| "As armadilhas são inúteis" como manchete | 16/08/2026 | O TOST não fecha nem em ±15%; não havia base para afirmar. |
| Bairro administrativo como granularidade | 16/08/2026 | 31% do número semanal é ruído de amostragem. |
| Regressão de casos em nível cidade como **eixo** | 16/08/2026 | Lift do vetor não significativo e concorrência densa. Permanece como benchmark. |
| Vetor no alarme de surto como **núcleo** | 29/08/2026 | 0 de 6 em Holm, e o efeito inverteu de sinal. |
| "ML prevê o mapa de risco" como diferencial | 29/08/2026 | O modelo vence a persistência em 1 de 8; hoje, 0 de 8. |
| Dependência do orientador para destravar método | 29/08/2026 | Decisão do Vinicius: método é decisão nossa, pré-declarada. |
| Casos por bairro (Comitê de Ética) | 29/08/2026 | Não fecha no prazo. Consequência: casos só em nível cidade. |
| Teto de extrapolação como causa do viés de pico | 30/08/2026 | Refutado: só 5 de 32 picos acima do teto do treino. |
| `casos_est` do nowcasting como alvo | 30/08/2026 | 99,1% idêntico aos notificados. |
| Trocar para LightGBM em horizonte longo | 30/08/2026 | Lidera na avaliação, é o pior na calibração. Trocar pelo juiz invalida o protocolo. |
| Rodar os 9 algoritmos como rotina | 30/08/2026 | Decisão do Vinicius: o foco passa a ser uma configuração. |
| **Equivalência clima × vetor como núcleo** | **13/09/2026** | Margem errada e alvo errado. Com a margem pré-declarada e o alvo decidido: 1 de 8. |
| **"A perda importa mais que o algoritmo"** | **13/09/2026** | Sem vazamento: perda +9,9% contra algoritmo +11,8%. A ordem inverteu. |

---

## 8. O que está em aberto

Ver [PENDENCIAS.md](PENDENCIAS.md) para a fila completa com donos. Em resumo:

- ⏳ **Ablação de janela de treino para o alvo casos** — nunca feita; só existe para o vetor.
- ⏳ **Validar o ENSO dentro do grid** — passou isolado, nunca no protocolo completo.
- ⏳ **Seleção de clima dentro do walk-forward** — o vazamento remanescente da §6.6.
- ⏳ **Pareamento por construção** em `rodar_regressao_selecao_clima`.
- ⏳ **Métrica de alarme de verdade** — sensibilidade e antecedência por episódio. A "captura do pico"
  atual é razão de níveis médios, não taxa de detecção.
- ⏳ **Confirmar o achado de que o vetor piora o alarme** com a temporada 2026-2027.
