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
| da Cunha e Silva et al. 2026 (CatBoost/GRU) | 27 capitais BR, incl. POA, semanal | Pesquisa | POA: R² −0,21 a −0,31; sMAPE 97–160% | **Parcial** | Mesma cidade e validação em avanço, mas o alvo é **INTERNAÇÃO por dengue** (DATASUS, CID-10 A90/A91), não caso notificado ou confirmado — 🔴 corrigido em 27/09/2026 contra o PDF; dizia "mesma unidade (casos/incidência)", o que está errado |
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
