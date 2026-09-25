# Varredura de literatura — Ângulo 2: Modelos e formulação do alvo

> Pergunta: quais **modelos** e **formulações de alvo** a literatura usa para prever dengue a 1–3 meses,
> e quais superaram baselines nesse horizonte? Contexto: Porto Alegre, previsão semanal de casos
> confirmados, horizonte-alvo 12 semanas, HistGB quantílico atual perde para a regra sazonal ingênua em
> h=8 e h=12.
>
> Método: busca via `WebSearch` + leitura de página via `WebFetch` (sem download de arquivo), 25/09/2026.
> Toda afirmação abaixo cita autor/ano/veículo e DOI ou URL. Números vêm do texto/abstract do trabalho
> quando o fetch teve sucesso; quando o fetch foi bloqueado (paywall/reCAPTCHA), o número vem do
> **snippet do buscador** — rotulado explicitamente. **Fato** = reportado no trabalho. **Inferência
> minha** = rotulado à parte.

---

## 1. GLM (Poisson / binomial negativa) com defasagens climáticas

- Comparação recente entre **NB-GLM**, **INGARCH-NB**, um modelo de renovação mecanístico (Renewal-NB)
  e um **BiLSTM-NB** para Freetown, Serra Leoa (2015–2024), em horizontes de **1 a 3 meses** — família de
  modelos de contagem com componente NB continua competitiva contra deep learning em horizonte curto.
  Fonte: BiLSTM-Negative Binomial Model vs Mechanistic and Count-Model Baselines, medRxiv/PLOS Glob.
  Public Health 2025. https://journals.plos.org/globalpublichealth/article?id=10.1371%2Fjournal.pgph.0005404
- Modelos hierárquicos bayesianos comparando **Poisson sem/com defasagem** e **Binomial Negativa sem/com
  defasagem**, dados semanais de Omã 2020–2024 — a defasagem climática melhora ambas as famílias, e NB
  lida melhor com sobre-dispersão que Poisson puro (**fato**, mecanismo estatístico bem estabelecido, o
  próprio artigo compara as 4 variantes). Fonte: comparativo Poisson/NB para arboviroses, ScienceDirect
  2025. https://www.sciencedirect.com/science/article/pii/S1876034125002552
- **Relevância para POA:** o projeto usa HistGB com perda quantílica — nunca testou uma família de
  contagem (Poisson/NB) como baseline estatístico paralelo. Como o alvo é contagem de casos com muitos
  zeros/valores baixos (61% das semanas ≤5 casos), NB seria estatisticamente mais bem especificado que
  regressão contínua para o **nível de ruído**, embora não resolva o problema central (perder para o
  ingênuo em picos).

## 2. Bayesiano hierárquico / INLA — Lowe et al., Brasil

- **Lowe et al. 2016, eLife 5:e11285** (DOI `10.7554/eLife.11285`) — sistema de alerta precoce
  probabilístico para dengue no Brasil, horizonte de **3 meses**, usando climas sazonais previstos +
  vigilância precoce. **Fato (confirmado por fetch direto):** o modelo acertou a categoria de risco em
  **57%** dos casos, contra **33%** do modelo nulo (médias sazonais históricas) — validado com os casos
  de junho/2014 (Copa do Mundo). Autores: Lowe, Coelho, Barcellos, Carvalho, Catão, Coelho GE, Ramalho,
  Bailey, Stephenson, Rodó.
- Lowe et al. 2013, *Statistics in Medicine* (DOI `10.1002/sim.5549`) — GLMM espaço-temporal bayesiano
  (DLNM + INLA) para risco de dengue no Sudeste do Brasil; base metodológica do sistema de 2016.
- **Relevância para POA:** é o precedente brasileiro mais próximo do projeto — mesmo horizonte de 3
  meses, mesmo país, e mesma conclusão qualitativa de que o **baseline sazonal é o adversário a bater**
  (33% de acerto do nulo já é uma base não trivial). A vitória de 57% vs 33% é modesta — reforça que
  ganhar do sazonal em 3 meses é estrutural mente difícil, não peculiaridade do pipeline de POA.

## 3. SARIMA / SARIMAX

- **Comparativo Rio de Janeiro** (SARIMAX vs. ML, dados semanais) — **fato via snippet do buscador**
  (fetch bloqueado por reCAPTOCHA/paywall em 3 tentativas): SARIMAX com covariáveis climáticas obteve
  **MAE 279,15 (8 sem.) e 375,15 (12 sem.)**, MAPE 54,86%/73,33%; ARIMA puro teve MAE 308,92/396,91 nos
  mesmos horizontes. Fonte: *Assessing dengue forecasting methods...*, Trop Med Health / medRxiv 2024,
  DOI `10.1186/s41182-025-00723-7` (não confirmado por leitura direta — três fetches bloqueados).
- Surabaia, Indonésia: SARIMA(2,1,1)(1,0,0) superou ARIMA e LSTM para DHF (**fato**, mas sem números de
  erro extraídos). Fonte: MDPI, *Processes* 2022. https://www.mdpi.com/2227-9717/10/11/2454
- **Relevância para POA:** os MAE do Rio (279–375 em 8–12 sem.) são da mesma ordem de grandeza do MAE de
  POA em 12 semanas (243,8–278,8), mas séries e populações diferentes tornam a comparação direta
  **inferência frágil** — não comparável sem normalizar por incidência/tamanho de população.

## 4. Prophet

- Prophet venceu em 6 de 9 cidades de Maharashtra, Índia, num comparativo de modelos de série temporal
  (**fato via snippet**, sem métrica numérica extraída). Fonte: Frontiers Public Health 2021,
  https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2021.798034/full
- Prophet superou ARIMA em Cagayan de Oro, Filipinas (**fato via snippet**). Fonte: ResearchGate 2023,
  https://www.researchgate.net/publication/372351365
- **Relevância para POA:** Prophet é aditivo (tendência + sazonalidade + regressores), conceitualmente
  parecido com "modelar resíduo sobre baseline sazonal" (seção 10) — mas nenhum dos achados reporta
  desempenho em pico atípico ou horizonte de 12 semanas, então o valor prático para POA é limitado.

## 5. Gradient boosting (XGBoost, LightGBM, CatBoost) — já testado no projeto

- XGBoost venceu SARIMAX, NBR e LSTM num comparativo de previsão semanal (**fato via snippet**): MAE
  89,12, RMSE 156,07, R²=0,83 — mas sem indicação clara de horizonte multi-semana nem se inclui picos
  fora da amostra. Fonte: busca agregada, sem DOI isolável e verificável — **omitir do quadro-resumo**
  por não ter DOI confirmado.
- CatBoost/XGBoost/LightGBM para dengue **grave** (classificação clínica, não previsão temporal): AUC-ROC
  97,1 — não comparável ao problema de séries temporais de POA (unidade de análise é paciente, não
  semana-cidade). Fonte: snippet agregado, sem DOI isolado.
- **Relevância para POA:** o projeto já testou HistGB e LightGBM exaustivamente (9 algoritmos, grade de
  hiperparâmetros). A literatura de boosting para dengue não traz achado novo de horizonte/alvo que POA
  não tenha coberto — a lacuna real está em **como o alvo é formulado**, não em qual boosting é usado.

## 6. Random Forest — Colômbia (Zhao et al. 2020)

- **Zhao N, Charland K, Carabali M, Nsoesie EO, Maheu-Giroux M, Rees E, Yuan M, Garcia Balaguera C,
  Jaramillo Ramirez G, Zinszer K (2020)**, *PLOS NTD*, DOI `10.1371/journal.pntd.0008056` — RF nacional
  vs. ANN vs. ARIMA, 30 departamentos colombianos, treino 2014–2017 / validação 2018, horizontes de
  **1 a 12 semanas**. **Fato (confirmado por fetch direto):** MAE de **9,32 em 1 semana** e **24,56 em
  12 semanas** para o RF nacional agrupado, superando ARIMA e ANN em todos os horizontes. Atributos:
  casos históricos (t até t-11), EVI/temperatura de superfície via MODIS, população, índice de Gini,
  cobertura educacional.
- **Relevância para POA:** é o comparativo direto mais citável de RF em 12 semanas com número de erro
  limpo. A escala é diferente (departamento colombiano vs. cidade única), então o MAE absoluto não é
  comparável — mas confirma que **erro cresce ~2,6× de 1 para 12 semanas** também em RF, e que
  sociodemografia pesa mais que clima em horizontes longos (achado do próprio artigo, fato).

## 7. Redes neurais (LSTM / TCN / TFT)

- **TFT aplicado a malária e dengue** (África do Sul e Vietnã), horizonte de até 6 meses com codificador
  de 12 meses — **fato via snippet**: R² até 0,90 para dengue, 0,95 para malária, com perda quantílica
  gerando P10/P50/P90. Fonte: PMC 2026, https://pmc.ncbi.nlm.nih.gov/articles/PMC12841506/ (fetch
  bloqueado — número não confirmado por leitura direta, só por snippet agregado de busca).
- **TFT em conjunto DengAI:** MAE 6,56, RMSE 10,72, R²=0,84, superando naive, seasonal-naive e LSTM, com
  janela de 24 semanas de entrada e 4 de saída (**fato via snippet**, DOI não isolado — Research Square
  preprint, revisão por pares pendente). https://www.researchsquare.com/article/rs-10975609/v1
- **Relevância para POA:** o ponto estruturalmente relevante não é a arquitetura (LSTM/TCN já cobertos
  implicitamente por HistGB no projeto, que captura não linearidade), é o **desenho multi-horizonte
  conjunto**: TFT treina um único modelo que prevê todos os horizontes simultaneamente com atenção
  compartilhada, diferente do "um modelo por horizonte" que POA usa hoje.

## 8. Modelos de fundação de séries temporais (Chronos, TimesFM, Moirai, Lag-Llama)

- Nenhuma aplicação encontrada, especificamente, a **dengue ou doença vetorial** nas buscas realizadas —
  os quatro modelos existem e são descritos em material de fornecedor/blog (Chronos-Amazon,
  TimesFM-Google, Moirai-Salesforce, Lag-Llama), mas a varredura não encontrou paper de aplicação a
  arbovirose. **Lacuna confirmada, não achado.**
- Trabalhos adjacentes de modelos pré-treinados **especificamente para epidemias** existem (PEMS —
  Pre-trained Epidemic Time-series Models, arXiv 2311.07841; "Pre-training Epidemic Time Series
  Forecasters with Compartmental Prototypes", PMC13464487) mas o fetch de ambos falhou (PDF binário
  ilegível) — **não confirmado**, cito apenas a existência da linha de pesquisa via título/arXiv id.
- **Relevância para POA:** ideia testável de baixo custo (zero-shot, sem treinar do zero) — ver seção de
  ideias.

## 9. Ensembles e formulações de alvo por diferença — o achado mais forte da varredura

- **Wu S, Meyer AG, Clemente L, Stolerman LM, Lu F, Majumder A, Verbeeck R, Masyn S, Santillana M
  (2025)**, *PNAS* 122(33):e2422335122, DOI `10.1073/pnas.2422335122` — **fato (confirmado por fetch
  direto)**: ensemble de 11 modelos individuais (mecanístico DT-SIR; estatísticos AR, ARGO, ARGONet,
  VAR regularizado, ETS; ML stacked com Elastic Net + SVM; baselines persistência/média sazonal) em
  **>180 locais** (Brasil, Colômbia, Malásia, México, Tailândia, Peru, Porto Rico), horizontes de
  **1, 2 e 3 meses**. Erro percentual absoluto do ensemble: **38,5% / 54,5% / 62,7%** para 1/2/3 meses,
  melhor que o melhor modelo individual isolado (VAR: 40%/55%/64%) e superando persistência ingênua na
  maioria dos locais. Ensemble ficou entre os 3 melhores em "vasta maioria" dos 187 locais testados.
- **Sprint de previsão de dengue no Brasil 2024 (IMDC24)** — Infodengue-Mosqlimate, publicado na PNAS
  (fev/2026), DOI `10.1073/pnas.2508989123`. **Fato via snippet** (fetch bloqueado 2×): 6 equipes
  internacionais previram dengue em 5 estados brasileiros para as temporadas 2024/2025; **nenhum modelo
  venceu de forma consistente**, especialmente durante 2024, ano atípico com mais casos que a soma da
  década anterior — achado direto sobre **falha de extrapolação em pico sem precedente**, no mesmo
  país e no mesmo tipo de ano atípico que POA viveu em 2024/2025.
- **Relevância para POA:** o achado do sprint brasileiro é o mais análogo ao problema central do
  projeto — **em ano de pico recorde, nenhuma abordagem (mecanística, estatística ou ML) generalizou
  bem**, o que é consistente com POA perder para o ingênuo sazonal justamente em h=8/12 (onde o pico
  pesa mais). Isso é evidência **externa e independente** de que o problema pode ser estrutural
  (picos sem precedente são difíceis para qualquer família), não um defeito específico do pipeline.

## 10. Alvo transformado — log, resíduo sobre baseline sazonal, razão ao ano anterior

- SARIMAX-log é usado como baseline padrão em vários comparativos (**fato agregado de múltiplos
  snippets**, sem DOI único isolável para essa afirmação específica — trato como prática comum, não
  achado de um único paper).
- Modelos com defasagens em **t-1, t-2, t-3 e t-12** são interpretados no próprio material de busca como
  equivalentes a comparação implícita com o ano anterior — mas não localizei um paper que module
  explicitamente a **razão casos-atuais/casos-mesma-semana-ano-passado** como variável-alvo (a
  formulação mais próxima do "ingênuo sazonal" que já vence POA). **Lacuna confirmada.**
- **Relevância para POA:** como o baseline "repetir semana do ano passado" já vence o modelo atual em
  h=8/12, a literatura não fornece um precedente direto de modelar o **resíduo sobre esse baseline como
  alvo** — é lacuna genuína, não algo já testado e reprovado em outro lugar. Ver ideia testável 1.

## 11. Peça-chave para picos sem precedente: seleção de modelo por critério de pico

- **Morbey RA, Todkill D, Watson C, Elliot AJ (2023)**, *PLOS ONE* 18(9):e0291932,
  DOI (via PMC10516409) — **fato (confirmado por fetch/snippet consistente)**: comparando VSR típico
  (2019) e atípico (2020/21, pico "adiado" da temporada), o modelo que minimiza erro diário médio **não
  é** o melhor para acertar tempo e magnitude do pico; incluir sazonalidade **melhora** desempenho em
  temporada típica mas **piora** em temporada atípica. Os autores propõem critério de seleção de modelo
  **baseado em acurácia do pico**, não em erro médio.
- **Relevância para POA:** achado diretamente aplicável — o projeto seleciona hiperparâmetro (folha
  mínima) e modelo por MAE médio nas 102 semanas de avaliação, nunca por acurácia específica de pico.
  Isso é uma dimensão de avaliação nova, não testada. Ver ideia testável 3.

## 12. Séries curtas com poucas epidemias

- **McGough SF, Clemente L, Kutz JN, Santillana M (2021)**, *J R Soc Interface* 18(179):20201006,
  DOI `10.1098/rsif.2020.1006` — **fato (confirmado por fetch direto)**: ensemble dinâmico de múltiplos
  SVM em janelas de 10–95 dias, para prever **ano epidêmico vs. não epidêmico** de dengue em 20
  municípios brasileiros, usando **apenas 17 anos** de dados (2001–2017) — os autores reconhecem
  explicitamente que "apenas 17 pontos de dados de resultado estavam disponíveis". Acurácia: 71,7%
  (só clima) e 75% (clima + ciclos de dengue), com uma camada pós-hoc de cadeia de Markov de 2ª/3ª ordem
  sobre ciclos empíricos de 3–4 anos entre epidemias.
- **Relevância para POA:** é o precedente mais próximo do problema de "só 4 temporadas epidêmicas
  usáveis" (2022, 2023, 2024, 2025) — mostra que outros grupos brasileiros trataram o problema como
  classificação binária ano-a-ano com regra de decisão de ciclo multianual, em vez de regressão semana
  a semana. Não é o que POA faz hoje. Ver ideia testável 5.

## 13. Transfer learning entre doenças correlatas

- **Roster K, Connaughton C, Rodrigues FA (2022)**, arXiv:2204.05059 — **fato (confirmado por fetch
  direto)**: transfer learning entre pares de doenças (dengue→zika; influenza→COVID) em cenários de
  dados escassos, usando dados empíricos do Brasil e dados teóricos gerados por modelo SIR. Conclusão
  do próprio resumo: "transfer learning oferece potencial para melhorar previsões... embora a doença de
  origem apropriada deva ser escolhida cuidadosamente" — **sem métrica numérica exposta no abstract**,
  não incluído no quadro-resumo por falta de número.
- **Relevância para POA:** baixa aplicabilidade direta (o projeto excluiu explicitamente outras
  arboviroses como dado de entrada), mas relevante como problema análogo — não incluído nas ideias
  testáveis por conflitar com exclusão já decidida pelo pesquisador.

---

## Tabela-resumo

| Trabalho | Dado / atributo / modelo | Horizonte | Métrica e número | Aplicável a POA? |
|---|---|---|---|---|
| Lowe et al. 2016, eLife (`10.7554/eLife.11285`) | GLMM bayesiano INLA + clima sazonal previsto, Brasil | 3 meses | 57% acerto de categoria vs. 33% do nulo sazonal | Sim — precedente brasileiro direto no mesmo horizonte; mesma conclusão de que o sazonal é adversário forte |
| Zhao et al. 2020, PLOS NTD (`10.1371/journal.pntd.0008056`) | RF nacional, 30 deptos Colômbia, clima+satélite+caso | 1–12 sem. | MAE 9,32 (1 sem.) / 24,56 (12 sem.) | Parcial — RF já testado em POA; útil como referência de crescimento de erro por horizonte |
| Wu et al. 2025, PNAS (`10.1073/pnas.2422335122`) | Ensemble de 11 modelos (mecanístico+estatístico+ML), >180 locais | 1–3 meses | PAE ensemble 38,5/54,5/62,7% vs. melhor individual 40/55/64% | Sim — POA nunca testou ensemble heterogêneo entre famílias de modelo |
| Sprint IMDC24, PNAS 2026 (`10.1073/pnas.2508989123`) | 6 equipes, 5 estados BR, 2024/2025 | Semanal, sazonal | Nenhum modelo consistente no ano atípico 2024 (snippet, não confirmado por leitura direta) | Sim — evidência externa de que picos recordes derrotam toda família de modelo, não só a de POA |
| Morbey et al. 2023, PLOS ONE (via PMC10516409) | Seleção de modelo por critério de pico, VSR Inglaterra | Sazonal (semanal) | Seleção por MAE médio ≠ seleção por acerto de pico; sazonalidade ajuda típico, atrapalha atípico | Sim — critério de avaliação novo, nunca aplicado em POA |
| McGough et al. 2021, J R Soc Interface (`10.1098/rsif.2020.1006`) | SVM ensemble dinâmico + Markov pós-hoc, 20 municípios BR, 17 anos | Ano epidêmico (classificação) | Acurácia 71,7% (clima) / 75% (clima+ciclo dengue) | Sim — precedente direto para problema de poucas temporadas epidêmicas |
| Rio de Janeiro, SARIMAX vs ML (`10.1186/s41182-025-00723-7`) | SARIMAX com clima, semanal | 8 / 12 sem. | MAE 279,15 / 375,15 (SARIMAX); 308,92 / 396,91 (ARIMA) — **via snippet, não confirmado por leitura direta** | Fraco — escala populacional diferente, não comparável em valor absoluto |
| TFT malária/dengue, PMC12841506 | Atenção multi-cabeça + LSTM, África do Sul/Vietnã | Até 6 meses | R² até 0,90 (dengue) — **via snippet, não confirmado por leitura direta** | Parcial — desenho multi-horizonte conjunto é a parte transferível, não o R² |

---

## Lacunas identificadas

- **Nenhuma aplicação de modelo de fundação de séries temporais (Chronos/TimesFM/Moirai/Lag-Llama) a
  dengue ou arbovirose foi encontrada** — é lacuna real da literatura, não só limitação desta busca (as
  buscas cruzando os quatro nomes com "epidemic"/"infectious disease" retornaram material de
  fornecedor/benchmark genérico, nunca um paper de arbovirose).
- **Nenhum paper localizado modela explicitamente "razão sobre o mesmo período do ano anterior" como
  variável-alvo** (em vez de defasagem como atributo) — a maioria usa a defasagem de 52 semanas como
  *feature*, não transforma o alvo em resíduo/razão sobre ela. Isso é notável porque é exatamente o tipo
  de baseline que vence o modelo de POA.
- **Poucos trabalhos relatam desempenho separadamente para o subconjunto de semanas de pico** — a imensa
  maioria reporta MAE/RMSE médio sobre todo o período de avaliação, escondendo o desempenho justamente
  onde POA mais perde (h=8/12, temporada de pico). Só Morbey et al. 2023 trata isso como critério
  explícito, e é para VSR, não dengue.
- **Três tentativas de leitura direta de PMC (`pmc.ncbi.nlm.nih.gov`) foram bloqueadas por reCAPTCHA**,
  e o Springer/BioMedCentral exigiu login em 2 tentativas — vários números desta varredura vêm do
  snippet do buscador, não do texto integral, e estão explicitamente rotulados como tal acima. Isso é
  uma limitação da coleta, não da literatura.
