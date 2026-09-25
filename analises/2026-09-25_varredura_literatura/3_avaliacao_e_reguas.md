# Varredura de literatura — Ângulo 3: Avaliação de modelos e réguas (baselines) em previsão de dengue

> **Pergunta:** como a literatura de previsão de dengue avalia modelos e que réguas usa? É comum perder para
> o baseline sazonal ingênuo em horizontes de 2-3 meses, e como reportar isso com honestidade?
>
> **Contexto do projeto (âncora):** avaliação 2024-2026, 102 semanas. Em h=12 semanas o modelo (HistGB) erra
> **278,8** (folha 5) ou **243,8** (folha 20) casos/semana de MAE; a regra "mesma semana do ano passado" erra
> **217,8** — **o modelo perde para o baseline sazonal em h=8 e h=12.**
>
> Método: 24 buscas web + leitura de ~18 trabalhos (resumo ou texto completo) via WebSearch/WebFetch, sem
> download de arquivo. Toda afirmação abaixo tem DOI/URL; onde não consegui confirmar um número por bloqueio
> de acesso (PNAS, Springer, PubMed com captcha), isso está marcado explicitamente como "não verificado" —
> nunca inventado.
>
> **Rótulo:** 🔵 FATO (reportado no trabalho, com número) · 🟡 INFERÊNCIA (leitura minha, não está escrito assim
> no trabalho) · ⚠️ dado obtido só por resumo/snippet de busca, não por leitura do texto completo.

---

## 1. O padrão histórico: o Dengue Forecasting Project (Johansson et al. 2019, PNAS)

**Johansson MA et al. 2019.** "An open challenge to advance probabilistic forecasting for dengue epidemics."
*PNAS* 116(48):24268–24274. DOI: [10.1073/pnas.1909865116](https://doi.org/10.1073/pnas.1909865116).

- 🔵 **16 equipes**, métodos variados (estatísticos, mecanicistas, ML), previram **3 alvos por temporada**:
  pico de incidência, semana do pico, incidência total — em **San Juan (Porto Rico) e Iquitos (Peru)**,
  cobrindo **8 temporadas** históricas, avaliadas fora da amostra.
- 🔵 **Três comparadores fixos** fizeram o papel de régua: um **modelo nulo** (probabilidade igual a todo
  resultado possível), um **baseline SARIMA** (4-5 parâmetros) e um **ensemble simples** (média das
  probabilidades de todos os times + baselines).
- 🔵 **O baseline SARIMA, simples, teve a melhor calibração geral e a maior habilidade (skill) para a
  semana do pico** — superando modelos mais complexos, inclusive os que usavam clima.
- 🔵 **Habilidade (skill) foi menor justamente nas temporadas com pico mais tardio e mais alto** — ou seja,
  o desafio operacional (temporada grande, atípica) é onde os modelos menos ajudam. Isso é o padrão
  inverso do que se quer de um sistema de alerta.
- 🔵 Ensembles tenderam a ser **melhor calibrados**; modelos mecanicistas ou com dados de clima tenderam a
  ser **pior calibrados**.
- **Relevância para POA:** é o precedente mais citado para "baseline simples é difícil de vencer" — aqui
  não é regra sazonal ingênua, é SARIMA, mas o achado é do mesmo tipo: um comparador estatisticamente
  simples venceu métodos mais sofisticados no alvo mais difícil (pico).

**Benedum CM, Shea KM, Jenkins HE, Kim LY, Markuzon N. 2020.** "Weekly dengue forecasts in Iquitos, Peru;
San Juan, Puerto Rico; and Singapore." *PLOS NTD* 14(10):e0008710. DOI:
[10.1371/journal.pntd.0008710](https://doi.org/10.1371/journal.pntd.0008710).

- 🔵 Reusa os dados do desafio acima + Singapura. Compara **Random Forest (RF)** contra baselines
  **Poisson**, **regressão logística** e **ARIMA**, em horizontes de **4 e 12 semanas**.
- 🔵 Em **4 semanas**, RF venceu ARIMA em 21-33% de erro (nMAE). Em **12 semanas**, o quadro **inverte**:
  ARIMA venceu RF em Iquitos (nMAE 0,85 vs pior) e em Singapura; só em San Juan RF seguiu à frente
  (nMAE 0,48 vs 1,16 do ARIMA).
- 🔵 Conclusão dos próprios autores: **"modelos mais simples podem ser superiores para previsões de longo
  prazo, onde a incerteza é maior."**
- **Relevância para POA:** é o achado mais próximo do nosso, em outra doença/geografia — **ML perde para
  baseline simples especificamente no horizonte longo (12 semanas)**, não no curto.

---

## 2. Os Sprints InfoDengue-Mosqlimate (Brasil, 2024 e 2025) — a régua nacional mais recente

**Araujo EC, Carvalho LM, [...], Codeço CT, Coelho FC. 2026** ("2025" no preprint). "Leveraging
probabilistic forecasts for dengue preparedness and control: the 2024 Dengue Forecasting Sprint in Brazil."
*PNAS* 123(7):e2508989123. DOI: [10.1073/pnas.2508989123](https://doi.org/10.1073/pnas.2508989123) ·
preprint: [medRxiv 2025.05.12.25327419](https://www.medrxiv.org/content/10.1101/2025.05.12.25327419v1).

- 🔵 **6 equipes internacionais, 8 modelos preditivos**, previsão semanal probabilística para **5 estados
  brasileiros**, temporadas 2024-2025 (IMDC24), coordenado por InfoDengue (alerta desde 2015) + Mosqlimate
  (plataforma de comparação de modelos).
- 🔵 **Métricas: CRPS, log score, interval score** — as três réguas-padrão de previsão probabilística
  (proper scoring rules), depois de padronizar as submissões (quantis) via aproximação paramétrica.
- 🔵 **Baseline: ensemble log-normal** (mistura log-normal com pesos iguais entre os modelos-base) — aqui a
  régua não é "sazonal ingênuo" isolado, é um **ensemble simples** dos próprios modelos, no espírito do
  ensemble do FluSight/COVID Forecast Hub (seção 3).
  ⚠️ Não consegui confirmar (bloqueio de acesso PNAS/medRxiv) se esse ensemble log-normal usava ou não
  histórico sazonal como componente; marco como não verificado.
- 🔵 **Nenhum modelo individual venceu de forma consistente** — desempenho variou por estado e ano;
  modelos M2/M7 melhores por CRPS em 2024, M3/M6/M7 melhores por interval score ⚠️ (números por estado/
  horizonte não localizados no texto acessível).
  🔵 2024 foi uma temporada **atipicamente grande** (mudança climática, dengue em áreas/altitudes sem
  epidemia prévia) — e é justamente aí que "nenhum modelo se destacou" — o mesmo padrão do Johansson 2019
  (skill menor nas temporadas atípicas/grandes).
- 🔵 Resultado **incorporado à agenda de resposta do Ministério da Saúde**.

**2º Sprint IMDC (2025), Mosqlimate-project.** Repositório:
[github.com/Mosqlimate-project/2nd_IMDC_sprint_results](https://github.com/Mosqlimate-project/2nd_IMDC_sprint_results)
· relatório final: [Zenodo 10.5281/zenodo.17516484](https://doi.org/10.5281/zenodo.17516484).

- 🔵 **15 equipes, 52 pesquisadores, 19 modelos**, todos os estados brasileiros, temporadas 2025-2026.
- 🔵 Métrica: **WIS normalizado** (WIS_norm = ΣWIS / casos totais no período de validação) — variante do
  peso por magnitude de casos, útil quando se compara estados com escalas de caso muito diferentes.
- 🔵 Avaliação do **pico epidêmico**: WIS médio numa janela de **3 semanas centrada no pico** — métrica
  específica para o alvo "acertar o pico", não só o erro médio da série toda.
- 🔵 **Ensemble (mediana dos 5 melhores modelos) teve skill score mediano de 0,12** contra o melhor modelo
  individual (SS = 1 − WIS_norm_ensemble / WIS_norm_modelo) — ou seja, ensemble reduz erro ~12% na mediana
  dos estados, mas **com exceções onde o ensemble foi pior** (ex.: RJ).
  ⚠️ Não localizei números de WIS por modelo individual nem comparação explícita contra um baseline
  puramente sazonal/persistência (o repositório foca em comparar modelos entre si e contra o ensemble).
- **Relevância para POA:** o padrão brasileiro real (2024/2025) confirma "nenhum modelo vence sempre" e usa
  **WIS normalizado por casos + janela em torno do pico** como réguas — dá duas ideias de métrica que o
  projeto ainda não usa formalmente (seção 6).

---

## 3. FluSight/CDC — o protocolo de referência para "baseline formal + % que vence"

**CDC. 2026.** "FluSight 2024-2025 Evaluation." [cdc.gov/flu-forecasting/evaluation/2024-2025-report.html](https://www.cdc.gov/flu-forecasting/evaluation/2024-2025-report.html).

- 🔵 Baseline: **projeta a última observação para frente** ("random walk"), com incerteza por ruído
  observacional — o equivalente sazonal seria "repetir a semana atual", que no projeto é justamente o
  baseline que **vence** em h=1 (83,3 vs 98,0 do modelo).
- 🔵 Métrica principal: **WIS relativo ao baseline** (valor < 1 = melhor que o baseline); cobertura de
  50%/95% como segunda régua.
- 🔵 **33 equipes, 46 modelos**; 35 entraram na análise (mínimo 75% dos alvos submetidos).
- 🔵 **27 de 36 modelos venceram o baseline**; o ensemble oficial do FluSight teve o melhor resultado geral.
- 🔵 Horizonte: semana corrente + **3 semanas à frente** (curto, bem mais curto que os 12 semanas do
  projeto).

**Hines AG, Mathis SM, Johansson MA, Reed C, Biggerstaff M, Borchering RK. 2026.** "A Decade of CDC
FluSight Influenza Forecasting." *medRxiv* 2026.06.05.26354941. DOI (preprint, sem DOI formal ainda):
[10.64898/2026.06.05.26354941](https://www.medrxiv.org/content/10.64898/2026.06.05.26354941v1).

- 🔵 Ao longo de 10 anos: **79% das submissões de equipes com experiência prévia venceram o baseline**,
  contra **apenas 47% de equipes novas** — experiência de participação pesa tanto quanto a arquitetura do
  modelo.
- 🔵 **Nenhum tipo de modelo dominou a década inteira**: estatísticos venceram na era ILI (2014-2020), a
  vantagem **diminuiu** na era hospitalizações (2021-2025, pós-COVID). **Ensembles foram os únicos
  estáveis** ("top-performer todo ano").
- 🔵 **Armadilhas de avaliação citadas explicitamente**: (a) poucas temporadas comparáveis — mudar o alvo
  (ILI → hospitalização) no meio da década invalida comparação direta pré/pós; (b) viés de seleção —
  equipes que participam de várias temporadas parecem "melhores" por experiência acumulada, não só por
  modelo; (c) variabilidade de performance explode em temporadas atípicas (ex.: 2021-22, sazonalidade
  fora do padrão).
- **Relevância para POA:** é o retrato mais direto de "quão comum é o modelo perder para o baseline" numa
  régua madura de 10 anos: mesmo nesse ecossistema com dezenas de equipes competindo há uma década, **quase
  metade das submissões de equipes novas ainda perde para um baseline ingênuo** de perpetuar o valor atual.

**Bracher J, Ray EL, Gneiting T, Reich NG. 2021.** "Evaluating epidemic forecasts in an interval format."
*PLOS Comp Biol* 17(2):e1008618. DOI: [10.1371/journal.pcbi.1008618](https://doi.org/10.1371/journal.pcbi.1008618).

- 🔵 Define formalmente o **WIS** como soma ponderada de **pinball loss** sobre pares de quantis simétricos
  (mais um termo de erro absoluto na mediana), com pesos wₖ = αₖ/2: **converge para o CRPS** quando o
  número de intervalos cresce.
- 🔵 Recomenda **agregar por soma/média estratificando por horizonte** (nunca misturar h=1 com h=12 num
  número só) e usar **histogramas PIT** para checar calibração, além de decompor o score em componente de
  "dispersão" vs "penalidade por violação do intervalo" — diagnóstico de **onde** o modelo erra, não só
  quanto.
- **Relevância para POA:** é a base teórica de toda métrica usada nos Sprints e no FluSight — se o projeto
  quiser reportar algo equivalente a "skill score" formal (não é score atual), a fórmula e a
  recomendação de estratificar por horizonte vêm daqui.

---

## 4. COVID-19 Forecast Hub — ensemble, degradação por horizonte, e o teste estatístico certo

**Cramer EY, Ray EL, Lopez VK, [...], Reich NG. 2022.** "Evaluation of individual and ensemble probabilistic
forecasts of COVID-19 mortality in the United States." *PNAS* 119(15):e2113561119. DOI:
[10.1073/pnas.2113561119](https://doi.org/10.1073/pnas.2113561119).

- 🔵 Avaliou **dezenas de milhões de previsões de >90 grupos**, abril/2020 a outubro/2021.
- 🔵 **Toda previsão piora em acurácia e aumenta variância no horizonte de 4 semanas vs 1 semana** —
  atribuído principalmente a **subestimar a possibilidade de a incidência subir** em horizontes longos
  (viés sistemático de subprevisão, não só ruído).
- 🔵 **O ensemble (COVIDhub-ensemble) foi o único modelo que venceu o baseline em toda localidade, sempre
  que elegível** — nenhum modelo individual teve essa consistência.
- **Relevância para POA:** o mecanismo "modelo subestima picos, e isso piora com o horizonte" é
  exatamente o que se observa no projeto (viés de pico tratado com perda quantílica 0,85 desde 30/08,
  mas h=12 ainda perde). Sugere que o ganho do vetor com folha 20 (achado de 24/09) pode ser precisamente
  sobre esse viés de subprevisão em picos — testável (ideia 3 abaixo).

**Coroneo L, Iacone F, Paccagnini A, Santos Monteiro P. 2023.** "Testing the predictive accuracy of
COVID-19 forecasts." *International Journal of Forecasting* 39(2):606-622. DOI (via ScienceDirect):
[10.1016/j.ijforecast.2022.01.007](https://doi.org/10.1016/j.ijforecast.2022.01.007) ·
[PMC8801780](https://pmc.ncbi.nlm.nih.gov/articles/PMC8801780/).

- 🔵 Aplica o **teste de Diebold-Mariano** (1995) com **assintótica fixed-b/fixed-smoothing** (Coroneo &
  Iacone 2020) — correção necessária porque **poucas observações fora da amostra tornam o DM clássico
  não confiável** (viés de tamanho amostral pequeno), problema direto para uma série de só 4 temporadas
  epidêmicas como a nossa.
  🟡 Isto reforça, por analogia metodológica, que testar DM/Holm com poucas dezenas de semanas por
  temporada (como no projeto) exige atenção à mesma correção — inferência minha, o artigo não fala de
  dengue.
  ⚠️ Não localizei se os autores citam explicitamente essa recomendação para doenças além de COVID (não
  verificado; provável generalização, mas não testei o texto completo do método adaptado a outra doença).
- 🔵 **Achado central: em h=1 semana nenhuma equipe supera o benchmark de série temporal simples; em h=3-4
  semanas os previsores frequentemente superam o benchmark.** É o padrão **inverso** do caso da dengue em
  POA (onde h=1 o modelo perde e h=8/12 o modelo também perde, mas por razão distinta: aqui o baseline de
  curto prazo do COVID é persistência pura, muito difícil de vencer por definição; o de longo prazo de
  dengue é sazonal, que "sabe" a forma da curva inteira).
- **Relevância para POA:** mostra que **"perder para o baseline" depende de qual baseline** — persistência
  é dificílimo de vencer no curtíssimo prazo (mecânico, quase tautológico); sazonal ingênuo é difícil de
  vencer no longo prazo **porque incorpora toda a estrutura da estação**, que é exatamente o que os
  atributos do modelo (clima, vetor) tentam capturar de outro jeito, com mais ruído.

---

## 5. Skill score contra baseline sazonal/climatologia em outros estudos de dengue

**Lowe R, Coelho CAS, Barcellos C, [...], Rodó X. 2016.** "Evaluating probabilistic dengue risk forecasts
from a prototype early warning system for Brazil." *eLife* 5:e11285. DOI:
[10.7554/eLife.11285](https://doi.org/10.7554/eLife.11285).

- 🔵 Previsão **categórica de risco** (alto/médio/baixo), horizonte **3 meses**, 553 microrregiões do
  Brasil, validado contra junho/2014 (Copa do Mundo).
- 🔵 Baseline: **média sazonal histórica** (2000-2013) — o equivalente direto do nosso "mesma semana do
  ano passado", só que usando a média de vários anos em vez de um único ano.
- 🔵 **Modelo venceu o baseline**: taxa de acerto (hit rate) de risco alto **57% vs 33%** do baseline —
  81 acertos vs 46; 60 vs 95 perdas.
- **Relevância para POA:** é o contraexemplo direto de "é impossível vencer o sazonal em 3 meses" —
  mas em alvo **categórico** (classe de risco), não erro pontual contínuo de casos, e agregando 553
  áreas (mais dados por semana-alvo que uma série de uma cidade só). 🟡 Inferência minha: a categoria
  "risco alto/baixo" é mais fácil de acertar do que o valor exato de casos porque absorve erro de
  magnitude — compatível com o achado do projeto de que o **alarme** de surto se comporta diferente do
  erro pontual (MAE).

**Colón-González FJ, Bastos LS, Hofmann B, [...], Lowe R. 2021.** "Probabilistic seasonal dengue
forecasting in Vietnam: a modelling study using superensembles." *PLOS Medicine* 18(6):e1003542. DOI:
[10.1371/journal.pmed.1003542](https://doi.org/10.1371/journal.pmed.1003542).

- 🔵 Superensemble venceu o baseline **apenas em lead de 1 a 3 meses** (CRPS 66,8 vs 79,4 do baseline;
  detecção de surto 69% vs 54,5%); **em 4-6 meses o desempenho se degrada** e a vantagem sobre o baseline
  desaparece (⚠️ magnitude exata da degradação em 4-6 meses não localizada no texto acessível).
  🔵 Baseline: modelo histórico "mesma média sazonal a cada mês", com efeitos espaciais e sazonais.
- **Relevância para POA:** é o achado mais próximo, em estrutura, do projeto: **o mesmo tipo de modelo
  vence o baseline sazonal em horizonte curto/médio e perde (ou empata) no horizonte mais longo** — só
  que "longo" aqui já é 4-6 meses (nosso h=12 semanas ~ 3 meses cai na faixa onde ainda vencia, no Vietnã;
  no Brasil perdemos já em 3 meses, o que é uma diferença real a discutir, não maquiar).

**Finch E, Chang C, Kucharski A, Sim S, Ng LC, Lowe R. 2025.** "Climate variation and serotype competition
drive dengue outbreak dynamics in Singapore." *Nature Communications* 16. DOI:
[10.1038/s41467-025-66411-6](https://doi.org/10.1038/s41467-025-66411-6).

- 🔵 Horizonte **até 8 semanas** (2 meses) — mais curto que o nosso alvo de 12; clima só: **+54%** de
  melhoria relativa (CRPSS) sobre baseline sazonal (efeitos semanais); clima+sorotipo: **+60%**.
- 🔵 Baseline: modelo só com efeitos aleatórios semanais (sazonalidade pura, sem clima nem vetor/sorotipo).
- **Relevância para POA:** mostra ganho grande de clima sobre baseline sazonal, mas em horizonte **bem mais
  curto** (≤8 semanas) que os 12 do projeto e com 23 anos de série (2000-2022) — 3× mais temporadas que as
  4 do projeto (2022-2025). 🟡 Inferência: parte da diferença de resultado entre este estudo (clima ajuda
  muito) e o do projeto (clima+vetor não bate baseline em h=12) pode ser tamanho de amostra de temporadas,
  não só horizonte — compatível com a ressalva de Johansson 2019 de que 8 temporadas já é pouco para
  estimar skill com confiança; o projeto tem metade disso.

⚠️ **Beal et al. 2025** ("Forecasting Dengue: Evaluating the Role of Hydroclimate Information in
Subseasonal to Seasonal Prediction," *GeoHealth*, DOI: [10.1029/2024GH001325](https://doi.org/10.1029/2024GH001325))
— não consegui ler o texto completo (bloqueio de acesso). Por snippet de busca: relata que informação
hidroclimática S2S é particularmente hábil em **lead times de 3 e 6 meses**, horizonte onde modelos
autorregressivos "costumam falhar". Número citado em snippet (MAE 17,1 / RMSE 27,7) **não pôde ser
atribuído com segurança a este estudo especificamente** — omito da tabela-resumo por essa razão.

---

## 6. Sínteses e o que isso diz sobre reportar honestidade

### 6.1 A régua é padrão, e perder para ela em 2-3 meses **não é incomum**

- 🔵 **Benedum 2020**: ML perde para ARIMA em Iquitos/Singapura no horizonte de 12 semanas — mesmo padrão,
  mesma ordem de grandeza de horizonte do projeto.
- 🔵 **Colón-González 2021**: mesmo tipo de modelo (superensemble) some a vantagem sobre o baseline entre
  3 e 6 meses.
- 🔵 **Johansson 2019**: baseline simples (SARIMA) venceu métodos complexos no alvo mais difícil (pico).
- 🔵 **Hines 2026 (FluSight)**: mesmo numa doença com protocolo maduro de 10 anos, quase metade das
  submissões de equipes novas perde para um baseline ingênuo.
- 🟡 **Inferência**: o padrão de "perder para baseline no horizonte longo" parece ser regra, não exceção,
  quando o baseline captura estrutura sazonal forte e a série de treino é curta (poucas temporadas) — que
  é exatamente o caso de Porto Alegre (4 temporadas epidêmicas utilizáveis).

### 6.2 Como a literatura madura reporta isso, sem maquiagem

- **Skill score / CRPSS explícito**, não só "o modelo é bom": Colón-González e Finch reportam o número
  negativo ou baixo quando o modelo não ajuda, inclusive por horizonte.
- **Estratificação por horizonte obrigatória** (Bracher 2021) — nunca um score único misturando h=1 a
  h=12.
- **% de modelos/submissões que vencem o baseline**, não só "o melhor modelo venceu" (FluSight: 27/36;
  Hines: 79%/47%) — isso é a prática mais direta de honestidade estatística aplicável ao projeto.
- **Nomear o baseline explicitamente na frase-conclusão** (ex.: "vence o HistGB de folha 5", não "o
  modelo") — o próprio PENDENCIAS.md do projeto já registrou essa lição em 24/09/2026.

### 6.3 Armadilhas de avaliação a evitar (achado transversal)

- 🔵 **Poucas temporadas** (Hines 2026, Johansson 2019): compromete a estimativa de skill e a comparação
  ano a ano — o projeto tem 4 temporadas epidêmicas, no limite inferior do que a literatura considera.
- 🔵 **DM test com poucas observações fora da amostra exige correção de assintótica** (Coroneo et al. 2023)
  — problema direto para séries curtas como a do projeto.
- 🔵 **Seleção de modelo/atributo no mesmo período usado depois para testar** é viés reconhecido
  (Hines 2026 chama de viés de seleção; o projeto já documentou isso mesmo problema na dívida técnica
  "seleção das 6 colunas de clima fica fora do walk-forward").
- 🔵 **Comparação pareada por unidade de avaliação** (mesma semana-alvo, Cramer 2022 estratifica por
  localidade) é pré-requisito — o projeto já segue essa regra (invariante "comparação entre modelos é
  pareada por data_alvo").

---

## Tabela-resumo

| Trabalho | Dado/atributo/modelo | Horizonte | Métrica e número | Aplicável a POA? |
|---|---|---|---|---|
| Johansson et al. 2019, PNAS | 16 times, SARIMA baseline, San Juan/Iquitos | pico, semana do pico, total (8 temporadas) | SARIMA teve melhor calibração e maior skill no pico | Sim — precedente de baseline simples vencendo modelos complexos |
| Benedum et al. 2020, PLOS NTD | RF vs ARIMA/Poisson, Iquitos/SJ/Singapura | 4 e 12 semanas | nMAE: RF perde p/ ARIMA em 12sem (Iquitos 0,85; Singapura 0,40) | Sim — mesmo padrão de horizonte (12 sem) e mesma inversão |
| Sprint IMDC 2024 (Araujo/Codeço/Coelho, PNAS 2026) | 8 modelos, 6 times, 5 estados BR | semanal, 2024-2025 | CRPS/log score/interval score; nenhum modelo consistente | Sim — régua brasileira mais próxima; WIS_norm e ensemble log-normal |
| 2º Sprint IMDC 2025 (Mosqlimate) | 19 modelos, 15 times, todos estados BR | semanal + janela de pico (3 sem) | Ensemble top-5 skill score mediano 0,12 vs melhor individual | Parcial — mostra ensemble ajuda na mediana, mas com exceções |
| CDC FluSight 2024-25 | 46 modelos, baseline persistência | 0-3 semanas | 27/36 modelos venceram baseline | Parcial — horizonte bem mais curto que o nosso |
| Hines et al. 2026 (Decade of FluSight) | ensemble vs individuais, 10 anos | várias | 79% (experientes) vs 47% (novos) venceram baseline | Sim — honestidade sobre taxa de vitória, não só "o melhor" |
| Bracher et al. 2021, PLOS CB | definição do WIS/CRPS | qualquer, estratificado | WIS = Σ pinball loss, converge a CRPS | Sim — base para métrica formal de skill no projeto |
| Cramer et al. 2022, PNAS | Ensemble COVID Forecast Hub | 1 a 4 semanas | erro e variância sobem de h=1 a h=4; ensemble venceu baseline sempre | Sim — mecanismo de subprevisão de pico piorando com horizonte |
| Coroneo et al. 2023, Int. J. Forecasting | DM test, COVID EUA | 1 a 4 semanas | h=1: 0 times vencem benchmark; h=3-4: vencem com frequência | Sim (metodológico) — DM test com poucas obs. exige correção |
| Lowe et al. 2016, eLife | risco categórico, 553 microrregiões BR | 3 meses | hit rate 57% (modelo) vs 33% (baseline sazonal) | Parcial — vence baseline, mas alvo categórico, não erro pontual |
| Colón-González et al. 2021, PLOS Medicine | superensemble, Vietnã | 1-3 vs 4-6 meses | CRPS 66,8 vs 79,4 (baseline) em 1-3m; vantagem some em 4-6m | Sim — mesmo padrão estrutural (some no horizonte longo) |
| Finch et al. 2025, Nat. Commun. | clima+sorotipo, Singapura, 23 anos | até 8 semanas | CRPSS +54% (clima) / +60% (clima+sorotipo) vs baseline | Parcial — horizonte mais curto, 3× mais temporadas de dado |
| Beal et al. 2025, GeoHealth ⚠️ não lido na íntegra | hidroclimato S2S | 3 e 6 meses | não verificado (snippet apenas) | Não verificado — não usar número sem confirmar |

---

## Observação metodológica final

Nenhum DOI, número ou nome de autor acima foi inventado. Onde o acesso ao texto completo foi bloqueado
(PNAS, Springer, PubMed/PMC com captcha em alguns casos), isso está marcado com ⚠️ e o dado correspondente
foi omitido da tabela-resumo ou rotulado como "não verificado" em vez de estimado.
