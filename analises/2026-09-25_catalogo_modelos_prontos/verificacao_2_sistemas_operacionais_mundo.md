# Verificação adversarial — Catálogo "2_sistemas_operacionais_mundo.md"

> Método: WebSearch + WebFetch, 25/09/2026. Sem download de arquivo, sem git clone. Índice = posição no JSON, a partir de 0.

---

## [0] EWARS-TDR (OMS/TDR) — PARCIAL

- **Referência ERRADA em ambas as partes.**
  - PLOS ONE 2018: primeiro autor real é **Hussain-Alkhateeb** (Kroeger, Olliaro, Rocklöv, Sewe, Tejeda, Benitez, Gill, Hakim, Carvalho, Bowman, Petzold) — **não "Lowe et al."**. Nome de Lowe não aparece na lista de autores. Volume/issue real: **13(5)**, não 13(4). DOI confere.
  - BMC Infect Dis 2022: primeiro autor real é **Cardenas** (Hussain-Alkhateek, Benitez-Valladares, Sánchez-Tejeda, Kroeger) — **não "Lowe et al."**. Número real do artigo: **22:235**, não 22:224. DOI `10.1186/s12879-022-07197-6` confere e aponta para este artigo (confirmado via texto).
- **Números batem exatamente** com o texto do artigo BMC 2022: México dengue sens 100%/VPP 83%; Colômbia dengue sens 92%/VPP 68%; Colômbia chikungunya sens 93%/VPP 92%; México Zika sens 97%/VPP 100%; Colômbia Zika sens 100%/VPP 54%. Horizontes (dengue 3-5 sem., chikungunya 10-13 sem., Zika 4-10 sem.) também conferem.
- ⚠️ **Malásia VPP 71-80%**: não localizado no texto do BMC 2022 (que cobre só México e Colômbia) — **não verificável** com o material acessado.
- URL da demo Shiny (`alramadona.shinyapps.io/Demo_Automated_Ewars`) carrega só uma tela "Please Wait" (app React/Shiny não renderiza em fetch estático) — **não verificável** se está de fato ativa.

## [1] D-MOSS (Vietnã) — PARCIAL

- **Referência ERRADA:** o artigo (DOI `10.1371/journal.pgph.0005867`, PMC12965583, PLOS Global Public Health, mar/2026) é de **Campbell, Colón-González [...] Brady (autor sênior)** — **"Lowe" não é autor deste artigo**. DOI e achado de conteúdo conferem, só a atribuição de autoria está errada.
- **Números CONFIRMADOS** por leitura do texto: RMSE −37,2% vs aleatório, −17,8% vs sazonal expansível; erro de pico 2,55 meses (D-MOSS) vs 4,52 (aleatório) e 4,09 (sazonal) — bate com "2,5 meses vs 4+". Maior ganho relativo em 4-6 meses confirmado literalmente no texto.
- Código GitHub `amymariecampbell/DMOSS_PerformanceEvaluation_Vietnam` **confirmado**: repositório real, 4 scripts R de pré-processamento/métricas/utilidade/figuras, casa com o estudo.

## [2] Puerto Rico — CDC Dengue Branch — PARCIAL

- Referência (PubMed 40998432, medRxiv 10.1101/2024.10.22.24315684) **confirmada existente**.
- Método confirmado: binomial negativa intercepto-only, percentis 60/75/90, **75º adotado**.
- 🔴 **Número errado:** o relatório diz que os casos superaram o limiar "já em fevereiro". A fonte primária (CDC MMWR 74(5), mm7405a1) diz explicitamente: *"In January 2024, the number of dengue cases in Puerto Rico surpassed the epidemic threshold [...] declare a public health emergency in March 2024."* — é **janeiro**, não fevereiro.
- Sensibilidade/especificidade exatas do percentil 75: confirmado que não estão acessíveis (PubMed bloqueou também para mim) — rotulagem de incerteza do catálogo está correta aqui.

## [3] Malásia — canal endêmico log (MOH) — CONFIRMADO

- PMC 13517397 confirmado, título exato.
- Todos os números batem literalmente com o texto: convencional sens 0,56 / espec. 0,70 / VPP 0,23 / Youden 0,26; log-escala sens 0,60 / espec. 0,82 / VPP 0,35 / Youden 0,43.
- Frase dos autores sobre dado nacional vs subnacional confirmada quase literalmente.
- Código "mediante solicitação" confirmado por citação direta (e-mail dos autores no texto).

## [4] Singapura NEA — LASSO Shi et al. 2016 — CONFIRMADO

- EHP 124(9):1369-1375, DOI `10.1289/ehp.1509981` confirmado via PMC5010413.
- Treino 2001-2010, validação 2011-2012, teste 2013 — confirmado.
- MAPE 1 semana ≈17% (todos os métodos); MAPE 12 semanas: **LASSO 24%, SARIMA 29%, step-down 29%** — confirmado exatamente.
- Frase sobre uso operacional (previsões semanais ao MOH e à NEA) confirmada quase literalmente no texto.

## [5] Dengue Forecasting Project 2015 (CDC/NOAA) — CONFIRMADO

- Johansson et al. 2019, PNAS 116(48), DOI `10.1073/pnas.1909865116` confirmado (16 equipes, 3 alvos, 8 temporadas, San Juan/Iquitos, SARIMA simples com melhor calibração e skill no pico).
- GitHub `cdcepi/dengue-forecasting-project-2015` confirmado como repositório oficial do CDC.

## [6] DengAI (DrivenData) — CONFIRMADO

- Página da competição e do blog de benchmark confirmadas: mesmos dados de San Juan/Iquitos, regressão semanal, benchmark = binomial negativa por cidade separadamente (citação direta confirmada).
- Catálogo já rotula o MAE do vencedor como não confirmável — **confirmado que o blog oficial não traz esse número**, coerente com a omissão correta no quadro-resumo.

## [7] Mosqlimate / InfoDengue — CONFIRMADO

- arXiv:2410.18945 confirmado: descrição "web-based platform [...] automatable access [...] forecasting models for arbovirus" bate com o catálogo.
- GitHub `Mosqlimate-project/2nd_IMDC_sprint_results` confirmado como repositório oficial do 2º sprint IMDC.

## [8] Ensemble CatBoost+SVM+LSTM (ESA/UNICEF) — PARCIAL

- DOI `10.1038/s41598-024-52796-9` confirmado (Scientific Reports, fev/2024); arquitetura (CatBoost+SVM+LSTM combinados por meta-aprendiz Random Forest) confirmada; horizonte 1 mês confirmado; GitHub `ESA-PhiLab/ESA-UNICEF_DengueForecastProject` confirmado (arquivado, mas existente e correspondente).
- 🔴 **Número errado:** RMSE normalizado relatado no catálogo como "0,041-0,857". O texto completo (PMC10869339) dá **0,041 a 1,021** para o Brasil (pior caso: RS, faixa 0-19 anos) e **0,117 a 0,327** para o Peru. O limite superior de 0,857 não corresponde ao valor real (1,021).
- Anos exatos de treino/validação (2001-2019 BR / 2010-2019 PE) **não verificáveis** com o material acessado (resumos não deram essa granularidade).

## [9] Lacuna — Argentina/Paraguai/Uruguai — CONFIRMADO (achado central) / NÃO VERIFICÁVEL (Paraguai)

- PDF do EGI-Dengue Argentina confirmado como documento de protocolo/estratégia (não permitiu extração de texto por ser majoritariamente imagem, mas buscas externas descrevem-no como estratégia de gestão integrada com anexos clínicos/epidemiológicos — sem seção de modelo estatístico), consistente com a caracterização do catálogo.
- Material sobre Paraguai (lei de Benford, GAM Assunção): **não verificado independentemente** — não localizei essas fontes especificamente nesta rodada.
- Inferência sobre Córdoba/Cone Sul corretamente rotulada como hipótese, não fato.

---

## Resumo dos erros confirmados

1. **[0] e [1]:** atribuição de autoria "Lowe et al." está errada em 3 das 3 referências centrais do item [0] e na única referência do item [1] — os autores reais são Hussain-Alkhateeb (2018), Cardenas (2022) e Campbell/Brady (2026). Lowe não é autor de nenhum dos três.
2. **[0]:** número do artigo BMC errado (22:224 → real 22:235); issue do PLOS ONE errado (13(4) → real 13(5)).
3. **[2]:** mês errado — limiar superado em **janeiro** de 2024, não fevereiro.
4. **[8]:** faixa de RMSE normalizado errada — real é 0,041–**1,021**, não 0,041–0,857.

Nenhum caso de fabricação total de referência ou de URL de código inexistente foi encontrado. Os erros são de **atribuição de autoria e de dígitos** (número de artigo, mês, limite de faixa), não de invenção de fonte.
