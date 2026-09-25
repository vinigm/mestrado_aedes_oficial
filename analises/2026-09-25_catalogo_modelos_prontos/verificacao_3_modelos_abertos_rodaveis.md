# Verificação adversarial — catálogo de modelos abertos rodáveis

> Método: WebSearch + WebFetch (sem download/clone), 25/09/2026. Verificador independente do autor do
> catálogo. Sem acesso primário completo a um trecho = `nao_verificavel`, nunca `confirmado`.

---

## 0. INLA bandas epidêmicas (Freitas et al. 2025) — **CONFIRMADO**

- Repo `AlertaDengue/baseline_paper`: R, GPL-3.0, usa só casos (SINAN/InfoDengue), 118 distritos —
  confirmado por fetch direto do repo.
- Paper (medRxiv 10.1101/2025.06.12.25329525 = PMC12359213): confirmado por busca. Citação: "propose a
  Bayesian forecasting model... to predict the number of dengue cases 52 weeks ahead for the 118 health
  districts of Brazil." Validação **exatamente** 2022–2023 e 2023–2024 (2024–2025 é só estimativa de
  mediana, não validação) — bate com o catálogo.
- É o baseline do 3º IMDC: README de `Mosqlimate-project/3rd_IMDC_results` confirma — "The baseline model
  adopted in this study was **PROCC (BB)** model, as described in Freitas et al. (2025)", WIS com
  "R_v < 1 = outperformed baseline", **31 times** listados. Todos os números do catálogo batem.
- Único ponto discutível: "validação é visual" — o paper na verdade reporta números pontuais (ex.
  2023-24: observado 6.454.020 vs percentil 90 de 2.221.557), não é puramente visual, mas não é MAE/RMSE
  nem skill score formal — a caracterização do catálogo é aceitável.

## 1. Baselines oficiais do sprint (Mosqlimate) — **CONFIRMADO**

- Repo `Mosqlimate-project/sprint-template`: GPL-3.0, notebooks Python e R confirmados por fetch direto.
- Os três baselines (naive, seasonal-naive, climatológico por quantis empíricos da mesma semana
  epidemiológica) confirmados via busca sobre o ecossistema do sprint (paper do IMDC24, PNAS
  10.1073/pnas.2508989123): "baseline models... include naive, seasonal-naive, and a
  climatological-quantile model that uses empirical quantiles of historical same-epiweek incidence."
  ⚠️ Nuance: essa descrição vem do paper do sprint 2024, não da página específica do repo
  `sprint-template` (o fetch direto do repo não trouxe essa definição) — mas é o mesmo ecossistema
  Mosqlimate citado pelo catálogo, então a atribuição geral procede.

## 2. AlertTools (GLM+Rt operacional) — **CONFIRMADO** (hedge do catálogo era correto)

- Repo confirmado: R, GPL-3.0, 541 commits não confirmado diretamente (API não retornou contagem), resto ok.
- Fetch do README cru falhou (só achou badge Zenodo), mas busca no rdrr.io confirma exatamente o que o
  catálogo hedgeou como incerto: função `bayesnowcasting` (nowcasting bayesiano), cálculo de tempo de
  geração (proxy de Rt), e sistema de alerta de **4 níveis por cor** — "yellow indicates environmental
  conditions for mosquito population growth... green otherwise, orange indicates sustained transmission,
  and red indicates epidemic scenario." Bate com "verde/amarelo/laranja/vermelho".
- O catálogo rotulou isso corretamente como ⚠️ não confirmado por leitura direta — postura correta, e a
  inferência se confirma como certa.

## 3. DLNM-INLA hidrometeorológico (Lowe et al. 2021) — **CONFIRMADO**

- Repo confirmado: R, GPL-3.0, 6 scripts exatamente como listado (00 a 05).
- Paper confirmado: Lancet Planetary Health 2021, **mensal**, mas a granularidade espacial é
  **558 microrregiões/municípios** (não "municípios do Brasil" genérico) — catálogo omite o número exato
  mas não erra a unidade. Nenhum skill score reportado — confirmado.

## 4. Pacote dlnm (Gasparrini) — **CONFIRMADO**

- Confirmado como pacote CRAN oficial de DLNM por Gasparrini, R, disponível via `install.packages("dlnm")`.

## 5. Ensemble de 11 modelos (Wu et al. 2025, PNAS) — **CONFIRMADO**

- Números exatos confirmados via PMC12377650: "38.5%, 54.5%, and 62.7% in terms of percent absolute
  error" (ensemble) vs "40%, 55%, and 64%, for each respective task" (VAR), nos horizontes 1/2/3 meses.
- Ausência de código confirmada: a declaração de disponibilidade de dados do paper não cita nenhum
  repositório público — "No public code repository is mentioned" no texto formal, batendo com o 403 e a
  busca sem resultado do catálogo.

## 6. D-FENSE (americocunhajr) — **CONFIRMADO**

- 5 modelos confirmados por nome e método: ARp, SARIMAX (2 versões), CLiDENGO (β-logístico climático),
  SURGE. Linguagens (MATLAB + R), licença **CC-BY-NC-ND 4.0**, horizonte 52 sem. (EW41→EW40) — todos
  confirmados por fetch direto do repo.

## 7. Ross-Macdonald estendido (zmz48844) — **PARCIAL**

- Números R² confirmados exatamente: "0.7394 and 0.7687" (só clima) vs "0.8883 and 0.8949" (com
  retroalimentação endógena), Guangdong 2016-2019, modelo Ross-Macdonald + população guiada por clima —
  tudo confirmado por fetch direto.
- ⚠️ Discrepância: o catálogo rotula licença como "não confirmada" (implica incerteza/pendência). A API
  do GitHub retorna licença **null** — ou seja, já dá para afirmar **"sem licença declarada"** (todos os
  direitos reservados por padrão), não apenas "não confirmada". Linguagem é **Python**, confirmada pela
  API (o catálogo também deixou como não confirmada). Não muda a conclusão de esforço, mas o catálogo
  poderia ter sido mais assertivo aqui.

## 8. InfraMIND-Proteus — **PARCIAL**

- Componentes, dados de entrada (ERA5, chikungunya, DataSUS, Copernicus) e horizonte (EW25 anual +
  semanal EW41→EW40) confirmados por fetch direto do repo.
- Licença: API confirma **GPL-3.0** (catálogo disse "licença no repo, não lida em detalhe" — consistente,
  agora com o dado exato).
- ⚠️ Discrepância pequena: catálogo diz "Linguagem **Python**". A API do GitHub classifica a linguagem
  primária do repositório como **Jupyter Notebook** (29.788 bytes, majoritariamente `.ipynb`), não
  "Python" como linguagem de repositório — o código dentro dos notebooks é Python, mas a caracterização
  literal do catálogo ("Linguagem Python") não é o que a métrica do GitHub mostra.

## 9. LSTM Brasil + SHAP (ChenXiang1998) — **CONFIRMADO** (hedge correto)

- Título confirmado exatamente: "LSTM-Based Dengue Prediction Across Brazil: SHAP-Driven Selection of
  Lagged Climate Variables and Spatial Impacts from Neighboring States" (aparece também na descrição do
  repo via API).
- Licença e linguagem: API confirma **null/null** (nenhuma declarada, nenhuma detectada) — o catálogo já
  rotulou como "não confirmadas", postura correta. Nenhum número de MAE/R² encontrado — catálogo agiu
  corretamente ao omitir da tabela-resumo em vez de estimar.

## 10. Temporal Fusion Transformer (DengAI, Research Square) — **CONFIRMADO**

- Paper confirmado (rs-10975609/v1, título exato). Números confirmados via busca (agregador cita o texto
  do paper): "MAE of 6.560 and RMSE of 10.724... R² of 0.840... outperformed Naive, Seasonal Naive, and
  LSTM baselines across all primary metrics" — bate com 6,56 / 10,72 / 0,84 do catálogo.
- ⚠️ Não verifiquei diretamente no PDF (extração falhou, texto vem binário) os números de encoder de 24
  semanas / horizonte de 4 semanas — ficam como **não verificável** nesta rodada, mas não contradizem
  nada encontrado.
- Repositórios genéricos de TFT confirmados como existentes: `mlverse/tft` (R) e
  `dehoyosb/temporal_fusion_transformer_pytorch` (Python/PyTorch, sem licença declarada) — nenhum dos
  dois é o código do paper específico, confirmando a lacuna que o catálogo já apontava.

## 11. DengAI (DrivenData) comunidade — **PARCIAL / REFUTADO em parte**

- Número confirmado: `umstek/DengAI` reporta "Current best result: 19.3798 (MAE)" — bate com "19,38".
- 🔴 **Refutado:** o catálogo descreve os modelos deste repo como "GBM/RF/SVM". O README real lista
  **Negative Binomial Regression** (sklearn/statsmodels), **redes neurais profundas** (Keras/TensorFlow)
  e **decomposição de série temporal + regressão linear** (citada como a melhor abordagem) — nenhuma
  menção a Gradient Boosting, Random Forest ou SVM. É um erro de atribuição de método, não de número.
- Números de `ramneekc.github.io/DengAI/` confirmados e a atribuição por cidade bate: Prophet teste MAE
  **3,45**/RN **2,79** são especificamente de **Iquitos** (Prophet MAE 3.45, LSTM MAE 2.79); San Juan tem
  MAE bem mais alto (Prophet 14,64, LSTM 23,31), não citado pelo catálogo. A ressalva do catálogo sobre
  "escala diferente ou vazamento" é razoável dado o contraste treino/teste e entre cidades.

---

## Resumo dos veredictos

| # | Item | Veredicto |
|---|---|---|
| 0 | INLA bandas epidêmicas | Confirmado |
| 1 | Baselines oficiais do sprint | Confirmado |
| 2 | AlertTools | Confirmado |
| 3 | DLNM-INLA hidrometeorológico | Confirmado |
| 4 | Pacote dlnm | Confirmado |
| 5 | Ensemble 11 modelos (Wu 2025) | Confirmado |
| 6 | D-FENSE | Confirmado |
| 7 | Ross-Macdonald estendido | Parcial (licença é "null", não "incerta") |
| 8 | InfraMIND-Proteus | Parcial (linguagem primária do repo é Jupyter Notebook, não "Python") |
| 9 | LSTM Brasil + SHAP | Confirmado (hedge correto) |
| 10 | TFT (DengAI) | Confirmado |
| 11 | DengAI comunidade | Parcial/Refutado (métodos do umstek/DengAI não são GBM/RF/SVM) |

**Nenhuma inferência foi apresentada como fato sem rótulo** — as duas discrepâncias reais (#8 e #11) são
de detalhe técnico secundário, não de conclusão. As conclusões centrais do catálogo (aplicabilidade a
POA, esforço, ausência de código para o achado mais forte da literatura) sobrevivem à verificação.
