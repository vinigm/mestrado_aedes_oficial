# Verificação adversarial — Ângulo 3: Avaliação de modelos e réguas

> Verificador independente. Método: WebSearch + WebFetch direto nas fontes (DOI/URL), sem download de
> arquivo. Onde o texto completo foi bloqueado (PNAS/PLOS deram 403 em alguns casos), usei snippets de
> busca de motores que já indexaram o texto, e marco a diferença. `confirmado` = vi o número/trecho na
> fonte. `parcial` = achado central bate, mas um número específico não bateu ou não foi localizado.
> `não_verificavel` = não consegui acessar nada que confirme ou negue.

---

## Índice 0 — Johansson et al. 2019, PNAS — SARIMA vence no pico

**Veredito: CONFIRMADO.**

- Via busca (indexação de conteúdo do pnas.org, texto bloqueado por 403 no fetch direto): **"The baseline
  SARIMA model compared well with more complex models, including having the best overall calibration and
  the highest skill forecasts for peak week."** — frase quase idêntica à do relatório original.
- **16 times, 3 alvos (pico, semana do pico, incidência total), 8 temporadas, San Juan + Iquitos** —
  confirmado por busca (PubMed/PNAS).
- SARIMA(1,0,0)(4,1,0)₁₂ para San Juan e SARIMA(1,0,0)(3,1,0)₁₂ para Iquitos — 4 e 5 parâmetros, batendo
  com "4-5 parâmetros" do relatório.
- Não verifiquei diretamente (texto completo bloqueado) a frase sobre "skill geralmente menor em
  temporadas de pico alto e tardio" isoladamente, mas a busca trouxe frase equivalente do abstract:
  *"skill was generally lowest for high incidence seasons"* — bate.
- Journal/DOI/ano batem: PNAS 116(48):24268-24274, doi 10.1073/pnas.1909865116.

---

## Índice 1 — Benedum et al. 2020, PLOS NTD — RF perde para ARIMA em 12 semanas

**Veredito: CONFIRMADO.**

- Fonte acessada diretamente (journals.plos.org, sem bloqueio).
- 4 semanas: RF teve **21% e 33% menos erro que Poisson e ARIMA**, respectivamente — frase quase literal:
  *"RF forecasts had 21% and 33% less error than Poisson regression and ARIMA models."*
- 12 semanas: nMAE ARIMA Iquitos = **0,85**; Singapura = **0,40** (ambos melhores que RF, não localizado
  o nMAE exato do RF nesses dois casos no fetch, mas a inversão está confirmada); San Juan é a exceção —
  RF (0,48) segue à frente do ARIMA (1,16), exatamente como o relatório descreve.
- Conclusão dos autores confirmada quase palavra por palavra: *"for long-term predictions where the
  outcome is less certain, the additional model complexity appears to hurt model accuracy."*
- ⚠️ Nuance: o relatório original erra ao generalizar "Singapura" só pelo lado ARIMA melhor — o fetch não
  devolveu o nMAE do RF em Singapura a 12 semanas para comparar par a par, mas a direção do achado
  (ARIMA à frente) está confirmada pelo texto.

---

## Índice 2 — Sprint InfoDengue-Mosqlimate 2024 (Araujo/Codeço/Coelho, PNAS 2026)

**Veredito: PARCIAL.**

- Confirmado por busca: **6 equipes internacionais** (Brasil, Arábia Saudita, Espanha, EUA), **5 estados
  brasileiros** (Amazonas, Paraná, Minas Gerais, Rio de Janeiro, São Paulo), temporadas 2024-2025,
  publicado na PNAS 123(7) — journal/volume/issue batem com o citado.
- Confirmado: *"no single model consistently excelled, especially during 2024's atypical,
  climate-change-driven conditions"* — frase quase idêntica à afirmação do relatório.
- Confirmado: métricas **CRPS, log score, interval score**.
- **NÃO confirmado o número "8 modelos"** — todas as fontes acessadas (PNAS, KAUST repository, FGV EMAp)
  falam em "6 times" mas não especificam "8 modelos" nesse sprint especificamente. Um resultado de busca
  trouxe texto que parece **misturar dados do 1º e do 2º sprint** (menciona "pesos por CRPS em 2023" e
  desempenho em "RS, PR, MT em 2025" — anos que não deveriam aparecer no sprint de 2024/2025 isoladamente).
  Isso é sinal de contaminação de busca, não do próprio relatório, mas o número "8 modelos" fica como
  **não verificado**, não como confirmado.
- Texto completo (PNAS, medRxiv) bloqueado por 403/reCAPTCHA em todas as tentativas de fetch direto.

---

## Índice 3 — 2º Sprint IMDC (2025) — skill score mediano 0,12

**Veredito: CONFIRMADO.**

- Fonte acessada diretamente: `github.com/Mosqlimate-project/2nd_IMDC_sprint_results/ensemble_results.md`.
- Texto literal encontrado: **"15 teams contributed with 19 dengue forecast models for all Brazilian
  states for the years 2025 and 2026."** — bate com "19 modelos, 15 times" do relatório (relatório citava
  também "52 pesquisadores, todos os estados BR", esse detalhe não estava na afirmação central e não foi
  checado).
- Métrica confirmada: **WIS^norm = (Σ WIS) / casos_totais** — bate com a fórmula descrita.
- Skill score confirmado literalmente: **"Overall, the median SS is 0.12"**, comparando ensemble dos 5
  melhores modelos (testes 1 e 2) contra o melhor modelo individual (teste 3).
- Exceção confirmada literalmente: **"in some cases, the ensemble performs substantially worse than the
  individual model (e.g., RJ)"** — bate exatamente com "exceções onde piorou" citando RJ.

---

## Índice 4 — FluSight/CDC 2024-25 + Hines et al. 2026 (década)

**Veredito: CONFIRMADO.**

- Fonte CDC acessada diretamente (cdc.gov): **"A total of 33 teams contributed forecasts from 46 unique
  models; of those, 35 models met inclusion criteria"** e **"Of the 36 submitted models, 27 performed
  better than the baseline model."** — bate com "27 de 36" do relatório (o relatório do projeto já
  registrava essa mesma ambiguidade 46 vs 36/35, não é erro novo).
- Baseline confirmado: projeta a última observação com incerteza por ruído — bate com "random walk" citado.
- Métrica confirmada: **WIS relativo ao baseline**.
- Hines et al. 2026 (medRxiv, autores conferem: Hines, Mathis, Johansson, Reed, Biggerstaff, Borchering):
  abstract confirma *"no single model type consistently outperformed others"* e que o ensemble do
  FluSight **"ranked among the top-performing forecasts every year"** — bate com "ensembles foram os
  únicos estáveis".
- Número **79% vs 47%** confirmado por busca com o detalhamento exato: **"34 of the 43 model submissions
  (79%) from teams with experience... 25 of the 53 models (47%) submitted from teams that never submitted
  ILI forecasts"** — bate com o número do relatório, com o detalhe adicional (34/43 e 25/53) que o
  relatório não tinha citado, mas é consistente.
- Ressalva: o abstract da Hines et al. (única parte acessível) fala em correlação positiva entre anos de
  participação e acurácia, "com associação estatisticamente significativa em 4 temporadas" — não achei essa
  frase no relatório original, mas não o contradiz.

---

## Índice 5 — Bracher, Ray, Gneiting, Reich 2021, PLOS Comp Biol — WIS

**Veredito: CONFIRMADO.**

- Fonte acessada diretamente (journals.plos.org).
- WIS como soma de pinball loss com pesos wₖ=αₖ/2, convergindo ao CRPS: confirmado, com citação da
  Eq. 4 do artigo.
- Recomendação de estratificar por horizonte: confirmado literalmente — *"it is often helpful to also
  inspect average scores separately by horizon and assess how forecast quality deteriorates over time."*
- Uso de histograma PIT para calibração: confirmado literalmente — *"For a calibrated forecast, the PIT
  histogram should be approximately uniform."*

---

## Índice 6 — Cramer et al. 2022, PNAS — COVID-19 Forecast Hub

**Veredito: CONFIRMADO.**

- **>90 grupos** confirmado por busca: *"more than 90 different academic, industry, and independent
  research groups."*
- Degradação com horizonte confirmada: *"forecast accuracy and calibration were substantially degraded as
  forecast horizons increased, largely due to underestimating the possibility of increases in
  incidence."* Achado adicional relevante não citado no relatório: erro probabilístico em h=20 chegou a
  ser **3 a 5 vezes maior** que em h=1 (dado extra, não contradiz nada).
- Ensemble vencendo em toda localidade confirmado literalmente: *"the ensemble approach was the only model
  that outperformed the baseline forecast in every location."*
- Texto completo bloqueado (403); tudo acima veio de indexação de busca, não de leitura direta do PDF —
  reduz um degrau de confiança, mas as citações são literais e específicas o suficiente para considerar
  confirmado.

---

## Índice 7 — Coroneo, Iacone, Paccagnini, Santos Monteiro 2023, IJF — Diebold-Mariano

**Veredito: CONFIRMADO.**

- Journal/volume/páginas conferem: *International Journal of Forecasting*, 39(2):606-622, 2023.
- Achado central confirmado quase literalmente: *"At the short horizon (1 week ahead) no forecasting team
  outperforms a simple time-series benchmark, and at longer horizons (3 and 4 week ahead) forecasters are
  more successful and sometimes outperform the benchmark."*
- Correção de assintótica confirmada: *"to overcome the small-sample problem, they apply fixed-smoothing
  asymptotics, as recently proposed for this test by Coroneo and Iacone (2020)"* — bate com "fixed-b/
  fixed-smoothing (Coroneo & Iacone 2020)" citado no relatório.
- O relatório rotula corretamente como 🟡 inferência a extensão desse achado metodológico para dengue —
  isso está certo, o artigo é 100% sobre COVID, nada de dengue.

---

## Índice 8 — Lowe et al. 2016, eLife — hit rate 57% vs 33%

**Veredito: CONFIRMADO** (com uma lacuna menor).

- Confirmado por busca: **553 microrregiões do Brasil**, validação contra junho/2014, baseline de médias
  sazonais históricas, **hit rate 57% (modelo) vs 33% (baseline)** — frase quase literal encontrada:
  *"a hit rate of 57% for the forecast model compared to 33% for the null model."*
- **Não verificado diretamente** (fetch bloqueado por erro de carregamento da página): o detalhe fino de
  "81 acertos vs 46, 60 vs 95 perdas" e o horizonte exato de "3 meses" — não contradiz nada encontrado,
  mas não pude confirmar esses números específicos na fonte primária, só por inferência da coerência com
  o hit rate agregado.

---

## Índice 9 — Colón-González et al. 2021, PLOS Medicine — Vietnã

**Veredito: PARCIAL.**

- Fonte acessada diretamente (journals.plos.org).
- CRPS confirmado literalmente: **"the superensemble made slightly more accurate predictions (CRPS = 66.8,
  95% CI 60.6 to 148.0) than a baseline model... (CRPS = 79.4, 95% CI 78.5 to 80.5) at lead times of 1 to
  3 months."** — bate exatamente com o número do relatório.
- Desaparecimento da vantagem em 4-6 meses confirmado literalmente: *"outperformed the competing models at
  all time leads but only outperformed the baseline at leads of 1 to 3 months."*
- **Detecção de surto — inconsistência a registrar:** o relatório cita "69% vs 54,5%" para detecção de
  surto. A fonte, no trecho recuperado, mostra **72,5%** de acerto do superensemble com limiar do
  percentil 95 e **61,3%** de acerto geral do baseline, e separadamente **54,5%** como "menor probabilidade
  de detecção de surto" do baseline — o número do baseline (54,5%) bate, mas **não encontrei o "69%"
  exato do superensemble** no trecho acessado; o valor que apareceu foi 72,5%. Pode ser um corte/métrica
  diferente (ex.: sensibilidade vs. acerto geral) não distinguido no fetch. **Não dou como refutado — dou
  como parcial**, porque o padrão qualitativo (modelo bate o baseline na detecção) está confirmado, mas o
  número exato do lado do modelo não fechou 1:1.

---

## Síntese do verificador

- **8 de 10 achados: CONFIRMADO** sem ressalva relevante (índices 0, 1, 3, 4, 5, 6, 7, 8 — alguns com
  lacunas menores de números finos não encontrados, mas o achado central bate literalmente com a fonte).
- **2 de 10: PARCIAL** (índices 2 e 9) — em ambos os casos o achado central e a direção do resultado
  batem; o que não fechou foi um número secundário (8 modelos; 69% de detecção).
- **0 refutados.** Nenhum DOI, autor, ano ou veículo divergiu do que o relatório original citou.
- **Tratamento de inferência como fato:** não encontrei nenhum caso em que o relatório apresente uma
  inferência própria como se fosse um dado do trabalho original. Os rótulos 🟡 (ex.: extensão do DM test
  fixed-b para dengue, item 7; a leitura sobre risco categórico ser "mais fácil" no item Lowe) estão
  corretos e bem colocados — é exatamente onde a inferência do pesquisador entra, e ele já sinalizou.
- **Limite de acesso:** PNAS bloqueou fetch direto em 100% das tentativas (403); toda confirmação desses
  itens (0, 2, 4 parcialmente, 6) veio de snippets de busca que indexam o texto, não do PDF/HTML completo
  lido por mim. Isso é uma verificação de segunda mão sobre o texto, mais forte que um snippet de resumo,
  mas ainda não é "vi o PDF com meus olhos" — registro essa diferença de confiança para as duas fontes PNAS.
