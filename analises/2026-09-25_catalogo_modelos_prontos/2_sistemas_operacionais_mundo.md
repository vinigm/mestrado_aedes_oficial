# Catálogo de modelos prontos — Ângulo 2: Sistemas operacionais de previsão/alerta de dengue no mundo

> **Pergunta:** quais sistemas operacionais e modelos prontos de previsão/alerta de dengue existem
> **fora do Brasil**, e como estão os resultados medidos?
>
> **Contexto do projeto (âncora, 25/09/2026):** previsão semanal de casos confirmados, Porto Alegre,
> horizonte-alvo 12 semanas (~3 meses), 2018-2026 (4 temporadas epidêmicas). Melhor modelo: HistGB
> quantílico 0,85 com vetor, MAE 243,8 casos/semana, contra 217,8 da regra "mesma semana do ano
> passado" (skill score −0,12, negativo = pior que a regra).
>
> **Método:** `WebSearch` + `WebFetch` (sem download de arquivo, sem git clone, sem instalação), 25/09/2026.
> Já coberto pela varredura de 25/09 (não repetido aqui): Johansson 2019, Benedum 2020, Colón-González 2021,
> Wu 2025, sprint InfoDengue-Mosqlimate 2024, Lowe 2016, da Silva 2026 (POA) — ver
> `analises/2026-09-25_varredura_literatura/2_modelos_e_alvo.md` e `3_avaliacao_e_reguas.md`.
>
> **Rótulo:** 🔵 FATO (reportado na fonte, com número) · 🟡 INFERÊNCIA minha (rotulada à parte) ·
> ⚠️ número obtido só por *snippet* de busca, não por leitura do texto completo — nunca usado no
> quadro-resumo sem essa marca.
>
> ⚠️ **Regra de comparabilidade:** nenhum MAE/erro abaixo é comparável em valor absoluto ao MAE de POA
> (243,8). Escala geográfica, população e unidade de contagem diferem. O que se extrai de cada um é
> **(a)** se venceu o baseline dele, **(b)** por quanto, **(c)** em qual horizonte, **(d)** contra qual régua.

---

## 1. EWARS-TDR (OMS/TDR) — o sistema de alarme mais replicado no mundo

**O que é:** ferramenta web (Shiny) de alarme de surto por distrito/cidade, desenvolvida pelo TDR-WHO com
parceiros, testada retrospectivamente em Brasil, México, Rep. Dominicana, Vietnã e Malásia, e
prospectivamente em Brasil, México e Malásia.

- 🔵 **Unidade:** série semanal por distrito/cidade — mesma granularidade do projeto (POA é uma cidade só).
  Fonte: Lowe et al. 2018, *PLOS ONE* 13(4):e0196811, DOI `10.1371/journal.pone.0196811`.
- 🔵 **Exige ao menos 3 anos de dados históricos** para montar o canal endêmico antes do teste
  prospectivo. Fonte: mesma referência.
- 🔵 **Horizonte do alarme varia por doença:** dengue 3-5 semanas, chikungunya 10-13 semanas, Zika 4-10
  semanas — **não é o horizonte de 12 semanas do projeto**, é alarme de curtíssimo prazo.
  Fonte: Lowe et al. 2022, *BMC Infectious Diseases* 22:224, DOI `10.1186/s12879-022-07197-6`.
- 🔵 **Régua:** canal endêmico (média móvel + desvio-padrão histórico), não regra sazonal única nem
  persistência.
- 🔵 **Resultados por país** (sensibilidade / VPP, alarme de surto, não erro pontual):
  - México (dengue): sensibilidade **100%**, VPP **83%**.
  - Colômbia/Cúcuta (dengue): sensibilidade **92%**, VPP **68%**.
  - Malásia (dengue): VPP **71-80%** (faixa, sem sensibilidade isolada no texto acessível).
  - México (Zika): sensibilidade **97%**, VPP **100%**. Colômbia (Zika): sensibilidade **100%**, VPP **54%**.
  - Colômbia (chikungunya): sensibilidade **93%**, VPP **92%**.
  Fonte: Lowe et al. 2022, BMC Infect Dis (acima).
- 🔵 **Código aberto:** demo pública em Shiny —
  [alramadona.shinyapps.io/Demo_Automated_Ewars](https://alramadona.shinyapps.io/Demo_Automated_Ewars/).
  Licenciamento do código-fonte completo não fica claro no texto acessível.
- **Roda nos nossos dados?** 🟡 Inferência: sim, tecnicamente — é feito para série semanal de uma
  cidade só, com só 3 anos de calibração. Mas resolve um problema **diferente** do projeto: alarme de
  surto de curto prazo (3-5 semanas), não previsão pontual de casos em 12 semanas. Não é comparável
  diretamente ao HistGB do projeto.

---

## 2. D-MOSS (Vietnã) — o superensemble de Colón-González em produção real

**O que é:** sistema operacional nacional, em produção desde **junho de 2019**, primeiro sistema
prospectivo e rotineiro de previsão de dengue baseado em dados de satélite. É o mesmo superensemble do
artigo Colón-González et al. 2021 (já coberto na varredura de 25/09), mas este é o **relatório de
desempenho em produção real**, não o estudo de validação retrospectiva.

- 🔵 **Fonte:** Lowe et al. 2026 (avaliação operacional), *PLOS Global Public Health*, DOI (via PMC)
  `10.1371/journal.pgph.0005867` — [pmc.ncbi.nlm.nih.gov/articles/PMC12965583](https://pmc.ncbi.nlm.nih.gov/articles/PMC12965583/).
- 🔵 **Dado de entrada:** 42 previsões climáticas sazonais do UK Met Office GloSea5 + covariáveis de
  satélite (temperatura, evapotranspiração, umidade do solo), nível **provincial** (63 províncias),
  não cidade única.
- 🔵 **Horizonte:** 1 a 6 meses. Nosso h=12 semanas ≈ 3 meses cai no meio da faixa testada.
- 🔵 **Régua:** dois baselines — amostragem aleatória da incidência histórica da província, e **média
  sazonal expansível** (o equivalente ao "sazonal ingênuo" do projeto, mas usando médias de vários anos).
- 🔵 **Venceu a régua, e por quanto:** RMSE **37,2% melhor** que o baseline aleatório e **17,8% melhor**
  que a média sazonal expansível, agregando todos os horizontes. Erro de tempo de pico: **2,5 meses**
  em média, contra 4+ meses dos baselines.
- 🔵 **Achado contraintuitivo relevante para POA:** a vantagem sobre a média sazonal **não decai**
  suavemente com o horizonte — o **maior ganho relativo sobre o baseline sazonal aparece em 4-6 meses**,
  não em 1 mês. 🟡 Inferência: isso sugere que "perder para o sazonal só em horizonte curto" não é
  universal — contradiz a leitura ingênua de que "quanto mais longe, pior contra o sazonal", que é o
  padrão observado em Benedum 2020 e Colón-González 2021 (já cobertos). Vale registrar como contraponto,
  não como regra.
- 🔵 **Código aberto:**
  [github.com/amymariecampbell/DMOSS_PerformanceEvaluation_Vietnam](https://github.com/amymariecampbell/DMOSS_PerformanceEvaluation_Vietnam).
  Dados **não** são abertos (restrição de segurança nacional vietnamita).
- **Roda nos nossos dados?** 🟡 Inferência: não diretamente — foi desenhado para previsão climática
  sazonal **de entrada** (GloSea5), que não existe pronta para o Brasil/POA nesse formato; adaptar
  exigiria trocar toda a camada de clima previsto por reanálise/observado, o que muda o método.

---

## 3. Puerto Rico — CDC Dengue Branch, limiares de alerta epidêmico (2024-2025)

**O que é:** sistema de alerta operacional do **CDC Dengue Branch** (com sede em San Juan), publicado
como "development and prospective application" — ou seja, já rodou de verdade na epidemia de
2024-2025 de Porto Rico.

- 🔵 **Fonte:** "Dengue epidemic alert thresholds for surveillance and decision-making in Puerto Rico:
  development and prospective application of an early warning system using routine surveillance data",
  2025-2026. PubMed ID `40998432`; preprint medRxiv
  [10.1101/2024.10.22.24315684](https://www.medrxiv.org/content/10.1101/2024.10.22.24315684v1.full).
- 🔵 **Método:** regressão binomial negativa intercepto-only sobre casos semanais históricos, gerando um
  **canal endêmico por percentil** (60º, 75º, 90º testados). O limiar de **75º percentil** foi o adotado
  operacionalmente, por equilibrar falso alarme e caso perdido. Duas ou mais semanas consecutivas acima
  do limiar = epidemia declarada.
- 🔵 **Régua/baseline:** o próprio canal histórico — não há comparação contra ML nem contra "mesma
  semana do ano passado" isolada; a métrica é sensibilidade/especificidade da classificação
  epidemia-vs-não-epidemia, não erro de magnitude.
- 🔵 **Uso real:** em **março de 2024**, o Departamento de Saúde de Porto Rico declarou emergência de
  saúde pública porque os casos superaram o limiar de alerta já em fevereiro — o sistema funcionou como
  gatilho de decisão real, não só exercício acadêmico.
- ⚠️ Números exatos de sensibilidade/especificidade do percentil 75 não confirmados por leitura direta
  (PubMed bloqueou por CAPTCHA); o texto indexado pela busca menciona a validação retrospectiva mas não
  isola o par sensibilidade/especificidade final — **omitido do quadro-resumo por essa razão**.
- 🔵 **Código aberto:** não localizado no material acessível.
- **Roda nos nossos dados?** 🟡 Inferência: sim, é o método **mais barato e replicável** de todo o
  catálogo — um canal endêmico por percentil sobre a série de casos de POA é trivial de calcular e já
  teria dado, na prática, o mesmo tipo de sinal que "mesma semana do ano passado" (que já vence o
  modelo). Não resolve previsão pontual em 12 semanas, resolve **alarme**.

---

## 4. Malásia — otimização de canal endêmico nacional (Ministério da Saúde, 2024-2025)

**O que é:** não é modelo de ML, é um **estudo de otimização de limiar** feito pelo próprio Ministério
da Saúde da Malásia, comparando duas variantes do canal endêmico clássico — inclui-se aqui porque é o
comparador metodológico mais direto ao "baseline sazonal" que o projeto já usa.

- 🔵 **Fonte:** "Optimizing Dengue Surveillance Thresholds in Malaysia: A Comparative Evaluation of
  Endemic Channel Approaches", PMC `13517397` (2025-2026).
- 🔵 **Dado:** série semanal **nacional agregada** (não cidade única), 2014-2024 (260 semanas
  epidemiológicas), excluindo 2020-2021 (distorção de COVID).
- 🔵 **Dois métodos comparados:** canal por desvio-padrão convencional vs. canal em **escala
  logarítmica** com regra de alerta reforçada (exige ultrapassar o limiar **e** crescer semana a semana).
- 🔵 **Resultado:** o canal em log venceu o convencional em sensibilidade (**0,60 vs 0,56**),
  especificidade (**0,82 vs 0,70**) e VPP (**0,35 vs 0,23**) — índice de Youden **0,43 vs 0,26**.
- 🔵 **Os próprios autores alertam:** o resultado é para dado **nacional agregado**, e pode não valer
  para uma cidade/subregião isolada — "análises subnacionais podem produzir limiares ótimos diferentes".
- 🔵 **Código aberto:** não — disponível "mediante solicitação razoável aos autores".
- **Roda nos nossos dados?** 🔵 Sim, diretamente — é um cálculo estatístico simples (canal endêmico em
  escala log) aplicável a qualquer série semanal de cidade única, incluindo POA, sem necessidade de
  ajuste. 🟡 Inferência: dado o alerta dos próprios autores sobre agregação nacional, o ganho de 0,60
  vs 0,56 pode não se repetir numa série de uma cidade só como POA — testar antes de assumir.

---

## 5. Singapura — NEA, modelo LASSO de Shi et al. 2016 (em produção desde 2016)

**O que é:** o sistema de previsão que a **National Environment Agency de Singapura** usa de fato,
desde 2016, para planejar controle vetorial. É citado no projeto CLAUDE.md como pendência de leitura.

- 🔵 **Fonte:** Shi Y, Liu X, Kok SY, Rajarethinam J, Liang S, Yap G, Chong CS, Lee KS, Tan SS, Chin CK,
  Lo A, Ferrières M, Ang LW, Ng LC (2016). "Three-Month Real-Time Dengue Forecast Models: An Early
  Warning System for Outbreak Alerts and Policy Decision Support in Singapore." *Environmental Health
  Perspectives* 124(9):1369-1375. DOI `10.1289/ehp.1509981`.
- 🔵 **Horizonte:** 3 meses (12 semanas) — **mesmo horizonte-alvo do projeto**.
- 🔵 **Régua:** SARIMA sazonal e regressão linear *step-down*.
- 🔵 **Dado de treino:** 2001-2010 (10 anos), validação 2011-2012, teste em surto real de 2013 —
  4 a 5× mais anos de série que os 8 anos utilizáveis do projeto.
- 🔵 **Venceu a régua, e por quanto:** em 1 semana os três métodos empatam (~17-18% MAPE); em **3 meses
  (12 semanas)**, LASSO **24% de MAPE** contra **29%** de SARIMA e **29%** de step-down — uma vantagem
  de **~5 pontos percentuais** de MAPE no mesmo horizonte que o projeto usa.
- 🔵 **Em produção real:** o artigo declara que a ferramenta "tornou-se parte integrante do programa de
  controle de dengue de Singapura", com previsões semanais enviadas ao Ministério da Saúde e à NEA.
- 🔵 **Código aberto:** não localizado — o método usa o pacote `glmnet` em R (disponível publicamente
  como biblioteca, mas o código específico do modelo não tem repositório citado).
- **Roda nos nossos dados?** 🔵 Sim, diretamente aplicável — LASSO sobre defasagens de clima e casos é
  reprodutível com os dados do projeto sem adaptação estrutural. 🟡 Inferência: é a comparação **mais
  favorável ao "vencer o sazonal em 12 semanas"** de todo o catálogo, mas roda sobre 10 anos de série,
  não 8 — a robustez do resultado com só 4 temporadas epidêmicas usáveis (o caso de POA) não está
  testada por este estudo.

---

## 6. Dengue Forecasting Project 2015 (CDC/NOAA) — o desafio-fundador

Já citado como Johansson et al. 2019 na varredura de 25/09 (não repetir os achados de lá). Aqui, o
recorte é **quem venceu e por quanto**, com foco na infraestrutura do desafio, não no achado de skill.

- 🔵 **Coordenação:** consórcio interagências dos EUA (HHS/CDC, DoD, NOAA, DHS), dados hospedados em
  [dengueforecasting.noaa.gov](https://dengueforecasting.noaa.gov/) e repositório
  [github.com/cdcepi/dengue-forecasting-project-2015](https://repository.library.noaa.gov/view/noaa/29196/noaa_29196_DS2.htm).
- 🔵 **16 equipes**, 3 alvos por temporada (pico, semana do pico, total da temporada), San Juan e
  Iquitos, 8 temporadas, avaliação fora da amostra.
- 🔵 **Régua:** modelo nulo + SARIMA (4-5 parâmetros) + ensemble simples de todos os times.
- 🔵 **Resultado central (já coberto):** SARIMA simples teve a melhor calibração geral e a maior skill
  no pico — nenhuma equipe individual bateu esse comparador de forma consistente.
- 🔵 **Código aberto:** sim — dados e templates de submissão no repositório GitHub do CDC-EPI acima.
- **Roda nos nossos dados?** 🔵 Sim, a infraestrutura (formato de submissão, réguas fixas) é replicável
  para uma cidade só com poucos anos — é literalmente o desenho mais parecido com o problema de POA
  (série curta, 2 cidades apenas, sem covariáveis externas obrigatórias).

## 6b. DengAI (DrivenData) — a versão "prática" do mesmo dado, sem revisão por pares

- 🔵 **O que é:** competição de aprendizado de máquina (não peer-reviewed) hospedada pela DrivenData,
  usando os **mesmos dados** de San Juan e Iquitos do Dengue Forecasting Project 2015, mas reformulada
  como regressão semanal de casos totais (não pico/semana-do-pico).
  [drivendata.org/competitions/44/dengai-predicting-disease-spread](https://www.drivendata.org/competitions/44/dengai-predicting-disease-spread/).
- 🔵 **Benchmark oficial da DrivenData:** regressão binomial negativa, ajustada por cidade separadamente
  (justificada por sobre-dispersão variância≫média). Fonte:
  [drivendata.co/blog/dengue-benchmark](https://drivendata.co/blog/dengue-benchmark).
- ⚠️ **MAE do vencedor da competição não confirmado por fonte única e verificável** — submissões
  públicas de participantes (não o resultado oficial revisado) mostram MAE na faixa de **25-27** para
  o conjunto combinado, mas nenhuma tem DOI ou publicação formal por trás. **Omitido do quadro-resumo**
  por não atender ao padrão de referência verificável exigido.
- **Roda nos nossos dados?** 🔵 Sim — é o mais parecido estruturalmente com o pipeline do projeto (uma
  série semanal por cidade, regressão direta de contagem de casos), mas **não é usado
  operacionalmente por nenhum órgão de saúde** — é material de treino/benchmark, não sistema de alerta.

---

## 7. Mosqlimate / InfoDengue (Brasil) — a infraestrutura por trás dos sprints já cobertos

Os *sprints* IMDC24/IMDC25 já foram cobertos na varredura de 25/09 (achados de skill/CRPS não
repetidos aqui). O que entra de novo é a **infraestrutura como sistema pronto**, reutilizável.

- 🔵 **Mosqlimate** é descrito como "plataforma para acesso automatizável a dados e modelos de previsão
  para doenças por arbovírus" — publica modelos submetidos pelas equipes participantes com código
  versionado. Fonte: "Mosqlimate: a platform to providing automatable access to data and forecasting
  models for arbovirus disease", arXiv:2410.18945.
- 🔵 **Código aberto do 2º sprint:**
  [github.com/Mosqlimate-project/2nd_IMDC_sprint_results](https://github.com/Mosqlimate-project/2nd_IMDC_sprint_results)
  (já citado na varredura de 25/09, referência mantida aqui por completude do catálogo de sistemas).
- 🔵 **InfoDengue** é o alerta operacional nacional desde 2015 (nível estado/município), que fornece o
  dado de entrada dos sprints — mas o alerta em si é o canal endêmico por incidência, não um modelo de
  ML publicado com métrica própria isolada no material acessível.
- **Roda nos nossos dados?** 🔵 Sim — é a plataforma mais próxima do formato do projeto (município
  brasileiro, série semanal, InfoDengue já é a fonte de referência oficial que o projeto usa para
  contexto). 🟡 Inferência: submeter o HistGB do projeto ao próximo sprint do Mosqlimate é a forma mais
  direta de obter uma certificação externa e comparável — mas exige série de município compatível com o
  formato deles (candidato de baixo custo, ver ideia 4).

---

## 8. Ensemble ML aberto Brasil+Peru (CatBoost+SVM+LSTM, ESA/UNICEF)

- 🔵 **Fonte:** "A reproducible ensemble machine learning approach to forecast dengue outbreaks",
  *Scientific Reports* 14, DOI (via Nature) `10.1038/s41598-024-52796-9`.
- 🔵 **Modelo:** três aprendizes de base (CatBoost, SVM, LSTM) combinados por um meta-aprendiz Random
  Forest — ensemble de *stacking*, não de médias simples.
- 🔵 **Dado:** Brasil (27 Unidades Federativas) 2001-2019 (19 anos) treino, 2017-2019 validação; Peru
  2010-2019, por departamento. **Muito mais anos de série que os 8 do projeto.**
- 🔵 **Horizonte:** 1 mês à frente (bem mais curto que os 3 meses do projeto).
- 🔵 **Régua:** "ensemble *dummy*" — só com casos de dengue defasados, sem variável ambiental.
- 🔵 **Resultado:** RMSE normalizado por estado entre **0,041 e 0,857**; o modelo completo supera a
  régua *dummy* de forma consistente, com menor incerteza (IC 95% mais estreito).
- 🔵 **Código aberto:**
  [github.com/ESA-PhiLab/ESA-UNICEF_DengueForecastProject](https://github.com/ESA-PhiLab/ESA-UNICEF_DengueForecastProject).
- **Roda nos nossos dados?** 🟡 Inferência: parcialmente — a arquitetura de *stacking* é aplicável a
  POA, mas o desenho original usa 19 anos de série e horizonte de 1 mês; aplicar a 8 anos e 3 meses
  exigiria reduzir a complexidade do ensemble (3 aprendizes de base para 4 temporadas epidêmicas é
  overfitting provável, risco não testado no artigo original).

---

## 9. Lacuna confirmada — América do Sul temperada/subtropical (Argentina, Paraguai, Uruguai)

- 🔵 **Nenhum sistema operacional de previsão/alerta de dengue com métrica de desempenho foi localizado**
  para Argentina, Paraguai ou Uruguai nas buscas realizadas.
- 🔵 O documento "EGI-Dengue Argentina" (OPAS/PAHO,
  [paho.org/sites/default/files/EGI%20ARGENTINA.pdf](https://www.paho.org/sites/default/files/EGI%20ARGENTINA.pdf))
  é um **protocolo de resposta e gestão de surto**, não um modelo preditivo — sem seção de método
  estatístico nem métrica de desempenho.
- 🔵 O material sobre Paraguai localizado é **avaliação de qualidade do sistema de vigilância**
  (conformidade com a lei de Benford em notificação, 2009-2011) e um estudo de **associação** clima-dengue
  em Assunção (GAM) — nenhum dos dois é um sistema de previsão com régua e horizonte declarados.
- **Relevância para POA:** 🟡 Inferência: isso é consistente com o achado já registrado na varredura de
  25/09 de que a dengue autóctone em Córdoba, Argentina (cidade temperada), **não se associou** ao
  vetor nem ao clima no período 2009-2017 — regiões temperadas do Cone Sul parecem ter dengue
  predominantemente importada/esporádica, o que reduz o incentivo a montar um sistema de previsão local
  dedicado. É análogo estrutural a Porto Alegre (também subtropical, também com surtos ainda recentes),
  mas **não achado, hipótese a registrar**, não fato publicado sobre POA.

---

## Tabela-resumo

| Sistema/modelo | Quem/onde | Dado de entrada | Horizonte | Régua | Venceu a régua? Por quanto | Código aberto | Roda nos nossos dados? |
|---|---|---|---|---|---|---|---|
| EWARS-TDR | OMS/TDR — México, Colômbia, Malásia, Brasil, Rep. Dominicana, Vietnã | Casos semanais por distrito/cidade, ≥3 anos | 3-5 sem. (dengue) | Canal endêmico histórico | Sim, alarme: sensib. 92-100%, VPP 54-100% conforme país | Demo Shiny público; fonte completa não confirmada | Sim, granularidade compatível — mas resolve alarme, não previsão pontual em 12 sem. |
| D-MOSS | Vietnã — Colón-González/Lowe, produção desde 2019 | Satélite + previsão climática sazonal GloSea5, nível provincial | 1-6 meses | Aleatório + média sazonal expansível | Sim: RMSE −37,2% (vs aleatório) / −17,8% (vs sazonal); ganho maior em 4-6 meses | Sim (GitHub, avaliação); dados fechados | Não diretamente — depende de previsão climática sazonal que não existe pronta para POA |
| Puerto Rico CDC (limiares 2024-25) | CDC Dengue Branch, San Juan | Casos semanais, canal por percentil (binomial negativa) | Alarme (sem horizonte fixo) | Canal histórico (percentil 75) | Usado em decisão real (emergência declarada mar/2024); sensib./espec. exatas não confirmadas | Não localizado | Sim — método barato e replicável para alarme, não para MAE em 12 sem. |
| Malásia (canal log, MOH) | Ministério da Saúde da Malásia, nacional | Casos semanais nacionais, 2014-2024 | Alarme (sem horizonte fixo) | Canal SD convencional | Sim: sensib. 0,60 vs 0,56; espec. 0,82 vs 0,70; Youden 0,43 vs 0,26 | Sob solicitação, não público | Sim, cálculo simples aplicável a cidade única — mas autores alertam que nacional ≠ subnacional |
| Singapura NEA (Shi et al. 2016) | NEA/Ministério da Saúde de Singapura, produção desde 2016 | Casos + clima defasado, LASSO, 10 anos de treino | 3 meses (12 sem.) — **mesmo horizonte de POA** | SARIMA sazonal + regressão step-down | Sim: MAPE 24% (LASSO) vs 29%/29% (SARIMA/step-down) em 12 sem. | `glmnet` (biblioteca pública); modelo específico não tem repo citado | Sim, diretamente replicável — mas com 10 anos de série, não 8 |
| Dengue Forecasting Project 2015 | CDC/NOAA/DHS, San Juan + Iquitos | Casos semanais, 2 cidades, 8 temporadas | Pico, semana do pico, total da temporada | Nulo + SARIMA + ensemble simples | SARIMA simples venceu métodos complexos no pico (já coberto na varredura anterior) | Sim, GitHub `cdcepi/dengue-forecasting-project-2015` | Sim — desenho mais parecido ao problema de POA (cidade única, série curta) |
| DengAI (DrivenData) | Competição prática, mesmos dados do item acima | Casos semanais + clima, regressão direta | Semanal, sem pico isolado | Binomial negativa (benchmark oficial) | Não confirmável com fonte única (números de vencedor sem DOI) — omitido | Sim, código de participantes no GitHub (não peer-reviewed) | Sim, estruturalmente — mas não é sistema operacional de saúde pública |
| Mosqlimate/InfoDengue | Brasil, plataforma nacional (sprints já cobertos) | Casos por município/estado, InfoDengue | Semanal (sprints 2024/2025) | Ensemble log-normal / WIS normalizado (já coberto) | Já coberto na varredura de 25/09 — não repetido | Sim, GitHub `Mosqlimate-project` | Sim — via submeter o HistGB do projeto ao próximo sprint |
| Ensemble CatBoost+SVM+LSTM (ESA/UNICEF) | Brasil (27 UFs) + Peru | Casos + clima, 19 anos (BR) / 10 anos (PE) | 1 mês | Ensemble *dummy* (só casos defasados) | Sim: RMSE normalizado 0,041-0,857, sempre melhor que dummy | Sim, GitHub `ESA-PhiLab` | Parcial — desenho para 19 anos, aplicar a 8 anos exige simplificar (risco de overfitting) |
| Argentina/Paraguai/Uruguai | — | — | — | — | **Nenhum sistema de previsão encontrado** — só protocolos de resposta e avaliação de vigilância | — | Lacuna confirmada, não modelo |

---

## Observação metodológica final

Nenhum DOI, número ou URL acima foi inventado. Onde o acesso ao texto completo foi bloqueado (PubMed/PMC
com CAPTCHA em 3 tentativas para Shi et al. via PubMed direto — contornado via cópia PMC — e para o
limiar de Porto Rico), isso está marcado com ⚠️ e o número correspondente foi omitido da tabela-resumo
ou rotulado como não confirmado, nunca estimado.
