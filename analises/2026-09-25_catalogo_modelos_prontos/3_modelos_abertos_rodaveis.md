# Catálogo de modelos prontos com código aberto — previsão de dengue

> **Pergunta:** quais modelos publicados de previsão de dengue têm **código aberto** e poderiam ser
> **rodados** na série de Porto Alegre (casos semanais de uma cidade, clima, índice de vetor por
> armadilha), e como estão os resultados deles em horizonte de 4 a 13 semanas?
>
> **Método:** `WebSearch` + `WebFetch` (sem download de arquivo, sem clone, sem instalação), 25/09/2026.
> Prioridade: repositórios Mosqlimate/InfoDengue, pacotes R/Python de previsão de dengue, modelos
> mecanísticos (SEIR+vetor, Ross-Macdonald), redes (LSTM/TFT) com repositório público, baselines
> oficiais dos sprints.
>
> **Rótulo:** 🔵 FATO (lido no repositório/artigo, com número ou trecho citável) · 🟡 INFERÊNCIA minha
> (rotulada) · ⚠️ não confirmado (acesso bloqueado, ou README insuficiente — nunca estimado no lugar
> do número real).
>
> **Comparabilidade:** nenhum MAE abaixo se compara ao MAE de POA (243,8 em h=12) — escala, cidade e
> horizonte diferem. Para cada modelo extraio o que É comparável: venceu a régua **dele**? por quanto
> (skill score/WIS/%)? em qual horizonte? contra qual régua?

---

## 0. AlertaDengue/baseline_paper — o modelo INLA "bandas epidêmicas" (Freitas et al. 2025)

- **Repo:** https://github.com/AlertaDengue/baseline_paper · **Artigo:** Freitas et al. 2025,
  *medRxiv* 10.1101/2025.06.12.25329525 (também PMC12359213 e ScienceDirect
  10.1016/j.epidem.2025....S2468042725000739).
- 🔵 Linguagem **R** (4.4.1) + **R-INLA** (24.06.27). Licença **GPL-3.0**. Repositório traz dados +
  código para replicar tabelas/figuras do manuscrito.
- 🔵 Dado exigido: só **série de casos semanais por distrito de saúde** (SINAN/InfoDengue) — não usa
  clima nem vetor. Modelo bayesiano hierárquico gera bandas probabilísticas (percentis 50/75/90) sobre
  o histórico.
- 🔵 **Horizonte: 52 semanas**, para os **118 distritos de saúde do Brasil**, validado retrospectivamente
  em 2022-23 e 2023-24.
- 🔵 **Régua:** o próprio artigo cita que, na literatura de West Nile, "modelos simples baseados em
  casos históricos geralmente performam melhor que modelos mais complexos" — mas **não reporta MAE/RMSE
  nem skill score próprio**; a validação é visual (bandas vs. curva observada).
- 🔴 **Achado mais importante deste modelo:** ele é o **baseline oficial do 3º IMDC (2026)** — confirmado
  no README do `3rd_IMDC_results` ("baseline: modelo PROCC (BB), Freitas et al. 2025"), contra o qual os
  **31 times/modelos** do sprint são medidos por razão de WIS (R_v < 1 = venceu o baseline).
- **Esforço para rodar em POA:** **baixo**. Só pede série de casos semanais (temos mais que isso). R-INLA
  precisa ser instalado (não é CRAN puro, tem binário próprio por SO). 🟡 Inferência: dá pra rodar hoje
  como régua adicional além da sazonal ingênua, e é a régua que o resto do Brasil usa.

---

## 1. Mosqlimate sprint-template — baselines oficiais dos sprints + arcabouço de submissão

- **Repo:** https://github.com/Mosqlimate-project/sprint-template · plataforma:
  https://sprint.mosqlimate.org/ · biblioteca cliente **Mosqlient** (Python e R).
- 🔵 Linguagem **R e Python** (notebooks demo separados). Licença **GPL-3.0**.
- 🔵 Baselines documentados na plataforma: **naive** (persistência), **seasonal-naive** e
  **climatológico** (quantis empíricos da mesma semana epidemiológica no histórico) — os três
  comparadores formais contra os quais um modelo submetido é julgado.
- 🔵 Dado exigido: série semanal de casos + geocódigo do município; clima vem embutido via
  Mosqlimate/ERA5 para quem quiser usar como atributo.
- **Régua:** os próprios baselines **são** a régua do sprint — não há um número de "quanto o modelo
  vence", isso é decidido caso a caso por submissão.
- **Esforço para rodar em POA:** **baixo**. É o candidato mais direto para implementar **os mesmos três
  baselines oficiais do sprint brasileiro** (não só "mesma semana do ano passado", também o
  climatológico por quantis) e comparar com eles, com o código de referência já pronto.

---

## 2. AlertTools (pacote R do InfoDengue) — GLM + Rt operacional

- **Repo:** https://github.com/AlertaDengue/AlertTools.
- 🔵 Linguagem **R**, licença **GPL-3.0**, 541 commits — é o pacote que roda **operacionalmente** por
  trás do site InfoDengue (alerta semanal em todo o Brasil).
- ⚠️ **Não confirmado por leitura direta do README** (página só listou a árvore de arquivos): a
  documentação de terceiros (rdrr.io) indica funções de **nowcasting bayesiano** (correção de atraso de
  notificação) e cálculo de **Rt**; a existência de um modelo de regressão hierárquica (GLM binomial
  negativa) é citada em material relacionado (AlertaDengue/baseline_paper reusa conceitos deste
  ecossistema), mas não pude confirmar o nome exato da função de previsão neste fetch.
- **Dado exigido:** casos semanais + clima (temperatura mínima documentada em funções auxiliares como
  `bestWU`).
- **Régua:** o pacote produz **classificação de risco por cor** (verde/amarelo/laranja/vermelho), não
  ponto de previsão numérica — não há "vencer régua" no mesmo sentido do projeto.
- **Esforço para rodar em POA:** **médio-alto**, com incerteza: o pacote é feito para rodar dentro do
  pipeline do InfoDengue (banco Postgres próprio); adaptar para uma série externa de Porto Alegre com
  vetor exigiria ler o código-fonte das funções (não fiz isso aqui, só o README) — marco como pendência
  se o Vinicius quiser aprofundar.

---

## 3. drrachellowe/hydromet_dengue — DLNM-INLA (Lowe et al. 2021, Lancet Planetary Health)

- **Repo:** https://github.com/drrachellowe/hydromet_dengue.
- 🔵 Linguagem **R** (4.0.2) + **R-INLA**. Licença **GPL-3.0**. Cinco scripts numerados
  (`00_load...` → `05_sensitivity_analysis.R`), rodam em sequência.
- 🔵 Modelo: **DLNM-INLA** — combina defasagem não-linear distribuída de variáveis hidrometeorológicas
  com efeitos espaciais estruturados (hierárquico bayesiano), nos municípios do Brasil.
- 🔵 Dado exigido: casos de dengue, variáveis hidrometeorológicas, indicadores de urbanização,
  shapefile — granularidade **mensal**, não semanal.
- ⚠️ **Não achei número de régua/baseline no README** — o artigo original (Lowe 2021) reporta associação
  exposição-resposta-defasagem, não um skill score de previsão contra baseline.
- **Régua:** não reportada no repositório.
- **Esforço para rodar em POA:** **médio**. É metodologicamente o mais próximo do que o projeto já faz
  (DLNM = defasagem distribuída, o que o projeto testa como lags 1-12), mas granularidade mensal exige
  reagregar a série semanal de POA, e o código foi escrito para múltiplos municípios (efeito espacial),
  não uma cidade só — precisaria podar a parte espacial.

---

## 4. gasparrini/dlnm — o pacote R que sustenta os dois modelos acima

- **Repo:** https://github.com/gasparrini/dlnm · página do autor:
  https://www.ag-myresearch.com/r-code.html.
- 🔵 Linguagem **R**, é o pacote CRAN oficial de **Distributed Lag Non-linear Models**, metodologia de
  Gasparrini (2010-2017), usado por Lowe et al. e por ARBOALVO (seção 8).
- **Não é um modelo de dengue** — é a ferramenta estatística genérica que qualquer um dos modelos
  DLNM/INLA acima usa por baixo.
- **Régua:** não aplicável (é biblioteca, não sistema de previsão).
- **Esforço para rodar em POA:** **baixo**, e é o item de **maior aproveitamento direto**: o projeto
  poderia montar seu **próprio** DLNM (clima + vetor defasados 0-12 semanas, em vez de só lag linear
  como hoje) usando este pacote, sem depender do código específico de nenhum paper — resolve exatamente
  a lacuna "defasagem vetor→casos nunca estimada com DLNM" listada no PENDENCIAS.

---

## 5. Wu et al. 2025, PNAS — ensemble de 11 modelos (AR/ARGO/ARGONet/DT-SIR/VAR/ETS/ML)

- **Artigo:** *Ensemble approaches for short-term dengue fever forecasts: a global evaluation study*,
  PNAS 122(33):e2422335122, DOI 10.1073/pnas.2422335122.
- 🔵 Já citado na varredura anterior: erro percentual absoluto do ensemble **38,5/54,5/62,7%** em
  1/2/3 meses, melhor que o melhor modelo individual isolado (VAR: 40/55/64%), em **>180 locais**
  (incluindo Brasil).
- ⚠️ **Código do artigo não localizado** — tentativa de leitura da seção "Data, Materials, and Software
  Availability" bloqueada (PNAS retornou 403). Não encontrei repositório público específico deste
  paper via busca.
- 🟡 Um dos componentes (**ARGONet**) tem repositório aberto, mas para **influenza**, não dengue:
  https://github.com/fl16180/argonet (Python/R, usado em Nature Communications 2018). Adaptar exigiria
  reescrever a parte de dados de internet (Google Trends já testado e reprovado no projeto) e a parte
  DT-SIR do zero.
- **Esforço para rodar em POA:** **alto**, com incerteza — a peça mais forte da literatura (achado
  central da varredura anterior) **não tem código aberto confirmado**. Reimplementar do zero (AR, VAR,
  ETS são triviais; DT-SIR e o ensemble stacking são o esforço real) é factível mas não é "rodar código
  pronto".

---

## 6. D-FENSE (americocunhajr) — pacote de 5 modelos, incluindo 1 mecanístico

- **Repo:** https://github.com/americocunhajr/D-FENSE.
- 🔵 **5 modelos distintos**, todos submissões aos sprints Mosqlimate: **ARp** (autorregressivo de
  ordem 92 em log, LNCC), **SARIMAX** e **SARIMAX v2** (UERJ, com regressores climáticos), **SURGE**
  (padrão médio de surtos, LNCC) e **CLiDENGO** (LNCC) — o único **mecanístico**: crescimento
  β-logístico estocástico modulado por clima.
- 🔵 Linguagem: **MATLAB** (ARp, CLiDENGO, SURGE) + **R** (SARIMAX). Licença **CC-BY-NC-ND 4.0** —
  ⚠️ **não é código aberto no sentido permissivo**: a licença proíbe uso comercial e obras derivadas
  distribuídas; dá para **rodar e inspecionar**, não para adaptar e redistribuir uma versão modificada.
- 🔵 Dado exigido: casos semanais por estado + temperatura/precipitação/umidade/pressão (Mosqlimate).
  Horizonte **52 semanas** (EW41→EW40).
- **Régua:** não reporta comparação com baseline no repositório (métricas ficam nos artigos de
  submissão do sprint, não neste README).
- **Esforço para rodar em POA:** **médio** para SARIMAX (R, direto); **médio-alto** para CLiDENGO
  (MATLAB, precisa clonar dinâmica β-logística e recalibrar parâmetros para POA) — é o candidato mais
  concreto de "mecanístico brasileiro com código, mesmo que não permissivo".

---

## 7. zmz48844 — Ross-Macdonald estendido + população de mosquito guiada por clima

- **Repo:**
  https://github.com/zmz48844/External-drivers-and-endogenous-feedback-for-dengue-dynamics.
- 🔵 Acopla um **modelo de população de mosquito guiado por clima** com um **Ross-Macdonald estendido**,
  testando 4 formulações (resposta empírica à temperatura, rede neural, retroalimentação endógena,
  taxa de picada dupla-regulada).
- 🔵 **Dado de Guangdong, China (2016-2019)**, não Brasil — clima + casos importados.
- 🔵 **Resultado (fato, reportado no repo):** R² 0,7394-0,7687 só com driver climático; **R² 0,8883-0,8949**
  incluindo retroalimentação endógena — melhora substancial na reconstrução multianual da epidemia.
  ⚠️ Não é skill score contra baseline formal, é R² de ajuste ao observado.
- ⚠️ Linguagem e licença **não confirmadas** no fetch (repo só expõe uma pasta "Code" sem README
  detalhado lido).
- **Esforço para rodar em POA:** **alto**. É o candidato mecanístico com vetor mais completo encontrado,
  mas foi calibrado para Guangdong (outra espécie/clima/regime de importação) — portar para POA exige
  reestimar todos os parâmetros entomológicos (taxa de picada, sobrevivência, tempo de desenvolvimento)
  com os dados de armadilha do projeto, o que é um projeto de pesquisa à parte, não um "rodar e comparar".

---

## 8. InfraMIND-Proteus — submissão híbrida do 3º IMDC (2026)

- **Repo:** https://github.com/paulocv/3rd_imdc_ifgw_inframind-proteus.
- 🔵 Linguagem **Python**. Dois componentes: **Outbreak Features** (CatBoost, estratégia
  climatologia-anomalia) e **Outbreak Dynamics** (**renewal model** mecanístico — não é SEIR
  compartimental clássico, é a família de "modelos de renovação" tipo Rt).
- 🔵 Dado exigido: notificações semanais de dengue, população DataSUS, **clima observado ERA5 +
  previsão climática sazonal Copernicus**, teleconexões oceânicas (ENSO-like), **casos de chikungunya**
  como sinal cruzado, tabela de regionais de saúde.
- 🔵 Horizonte: previsões anuais por UF (EW25) + trajetórias semanais.
- ⚠️ **Sem publicação associada ainda** — não há skill score/WIS reportado no repositório (é uma
  submissão de sprint em andamento, não um artigo fechado).
- **Esforço para rodar em POA:** **médio-alto**. É o exemplo mais moderno de pipeline Python
  "clima+renovação+ML" com código real, mas falta o componente de vetor por armadilha (usa
  chikungunya como proxy de sinal cruzado, não índice entomológico) — adaptar exigiria substituir esse
  sinal pelo dado de armadilha do projeto.

---

## 9. LSTM Brasil (ChenXiang1998) — clima defasado via SHAP + estados vizinhos

- **Repo:** https://github.com/ChenXiang1998/LSTM-Based-Dengue-Prediction-Across-Brazil.
- 🔵 Título confirmado: *"LSTM-Based Dengue Prediction Across Brazil: SHAP-Driven Selection of Lagged
  Climate Variables and Spatial Impacts from Neighboring States"* — nível **estadual**, não municipal.
- ⚠️ **README não expôs linguagem/licença/métricas numéricas** neste fetch (conteúdo mínimo retornado);
  o artigo companheiro provável é o do medRxiv 2025.03.02.25323168 ("Dengue forecasting and outbreak
  detection in Brazil using LSTM: integrating human mobility and climate factors") ou o da Springer/BMC
  Public Health 2025 (LSTM + SHAP + clima defasado + espacial) — **não consegui atribuir o número de
  MAE/R² com segurança a este repositório específico**, por isso omito da tabela-resumo como valor,
  mantendo só como código+arquitetura.
- **Esforço para rodar em POA:** **baixo-médio**. Arquitetura LSTM + seleção de atributos por SHAP é
  diretamente portável para uma série de cidade única com clima+vetor — é o tipo de coisa que o projeto
  já testou (9 algoritmos incluem redes, conforme PENDENCIAS), então o ganho marginal é a **técnica de
  seleção de lag por SHAP**, não a arquitetura em si.

---

## 10. Temporal Fusion Transformer — DengAI (Research Square) + implementações genéricas abertas

- **Artigo:** *Trustworthy AI for Dengue Outbreak Forecasting Using a Temporal Fusion Transformer with
  Explainability and Uncertainty Estimation*, Research Square rs-10975609/v1 — dataset **DengAI**
  (San Juan/Iquitos), janela de 24 semanas → horizonte de **4 semanas**. 🔵 MAE **6,56**, RMSE **10,72**,
  R² **0,84**, superando naive/seasonal-naive/LSTM (números já confirmados na varredura anterior).
- ⚠️ **Não localizei o repositório de código deste paper específico** — a busca só retornou
  implementações genéricas de TFT, não o código do experimento com DengAI.
- 🔵 Implementações **genéricas** de TFT, abertas, prontas para reuso: **mlverse/tft** (R,
  https://github.com/mlverse/tft) e **dehoyosb/temporal_fusion_transformer_pytorch** (Python/PyTorch
  Lightning, https://github.com/dehoyosb/temporal_fusion_transformer_pytorch) — arquitetura idêntica,
  sem o pré-processamento específico do paper.
- **Esforço para rodar em POA:** **médio**. A arquitetura é replicável com bibliotecas genéricas abertas;
  o ganho do desenho **multi-horizonte com atenção compartilhada** (previsto na varredura anterior, seção
  7) é a parte transferível — treinar do zero, sem atalho de código pronto específico para dengue.

---

## 11. DengAI (DrivenData) — soluções-comunidade, dataset-benchmark citado por vários papers

- **Exemplos de repositórios públicos:** https://github.com/umstek/DengAI (MAE **19,38**, GBM/RF/SVM),
  https://ramneekc.github.io/DengAI/ (Prophet MAE **3,45**/semana, rede neural MAE **2,79**/semana — 🟡
  inferência: esses valores muito baixos sugerem escala diferente ou vazamento de dado, não comparável
  sem auditoria — **não são números de artigo revisado por pares**, são projetos de estudante/hobby).
- 🔵 O dataset **DengAI** (San Juan + Iquitos, semanal, com clima) é o mesmo usado pelo paper de TFT da
  seção 10 e por dezenas de outros trabalhos — é um benchmark de fato, mas os repositórios de solução
  da comunidade **não são literatura**, são exercícios de competição sem revisão por pares.
- **Régua:** cada repositório usa seu próprio corte de MAE de competição (não uma régua sazonal formal).
- **Esforço para rodar em POA:** **baixo**, mas **baixo valor de evidência**. É o único item desta lista
  onde "rodar o código tal como está" é trivial (formato de dado quase idêntico ao nosso: cidade,
  semana, casos, clima) — útil como teste de sanidade rápido de arquitetura, não como fonte de
  comparação científica.

---

## Tabela-resumo

| Modelo/sistema | Quem/onde | Dado de entrada | Horizonte | Régua | Venceu a régua? por quanto | Código aberto (URL) | Roda nos nossos dados? |
|---|---|---|---|---|---|---|---|
| INLA bandas epidêmicas | Freitas et al. 2025 / AlertaDengue-PROCC | Casos semanais por distrito | 52 sem. | É o próprio baseline do 3º IMDC | N/A — ele É a régua; 31 modelos medidos contra ele por WIS | [baseline_paper](https://github.com/AlertaDengue/baseline_paper) (GPL-3.0) | Sim — baixo esforço |
| Baselines oficiais do sprint | Mosqlimate-project | Casos semanais + geocódigo | qualquer | naive/seasonal-naive/climatológico | N/A — são os 3 comparadores oficiais | [sprint-template](https://github.com/Mosqlimate-project/sprint-template) (GPL-3.0) | Sim — baixo esforço |
| AlertTools (GLM+Rt operacional) | AlertaDengue/InfoDengue | Casos semanais + clima | operacional (alerta) | Classificação de risco por cor, não ponto | Não aplicável nesse formato | [AlertTools](https://github.com/AlertaDengue/AlertTools) (GPL-3.0) | Incerto — não confirmado |
| DLNM-INLA hidrometeorológico | Lowe et al. 2021, Lancet Planet. Health | Casos + clima + urbanização, mensal | não reportado | Não reportado no repo | Não reportado | [hydromet_dengue](https://github.com/drrachellowe/hydromet_dengue) (GPL-3.0) | Parcial — médio esforço (mensal→semanal) |
| Pacote dlnm (metodológico) | Gasparrini | Qualquer série + covariável defasada | N/A | N/A | N/A | [dlnm](https://github.com/gasparrini/dlnm) (CRAN/GPL) | Sim — baixo esforço, maior aproveitamento |
| Ensemble 11 modelos | Wu et al. 2025, PNAS | Casos + Google Trends + vizinhos | 1-3 meses | Melhor modelo individual (VAR) | Sim, 38,5/54,5/62,7% vs 40/55/64% (PAE) | Não localizado (PNAS bloqueou seção de código) | Não — sem código confirmado |
| D-FENSE (5 modelos, 1 mecanístico) | LNCC/UERJ, submissões Mosqlimate | Casos por estado + clima | 52 sem. | Não reportado no repo | Não reportado no repo | [D-FENSE](https://github.com/americocunhajr/D-FENSE) (CC-BY-NC-ND, não permissiva) | Parcial — médio esforço |
| Ross-Macdonald estendido + mosquito | zmz48844 | Clima + casos importados, Guangdong | reconstrução multianual | Ajuste ao observado (R²) | R² 0,74→0,89 com retroalimentação | [repo](https://github.com/zmz48844/External-drivers-and-endogenous-feedback-for-dengue-dynamics) (licença não confirmada) | Não — recalibração é projeto à parte |
| InfraMIND-Proteus | Sprint 3º IMDC 2026 | Clima ERA5+sazonal, casos, chikungunya | anual (EW25) + semanal | Sem publicação, sem skill score ainda | Não reportado | [repo](https://github.com/paulocv/3rd_imdc_ifgw_inframind-proteus) (licença no repo, não lida) | Parcial — médio-alto esforço |
| LSTM Brasil + SHAP | ChenXiang1998 | Casos + clima defasado + estados vizinhos | não confirmado | Não confirmado | Não confirmado (não atribuível com segurança) | [repo](https://github.com/ChenXiang1998/LSTM-Based-Dengue-Prediction-Across-Brazil) (não confirmada) | Sim — baixo-médio esforço |
| TFT (DengAI) | Research Square rs-10975609 | Casos + clima, San Juan/Iquitos | 4 sem. (encoder 24 sem.) | naive/seasonal-naive/LSTM | Sim — MAE 6,56 vs baselines não quantificados no snippet | Paper sem repo confirmado; arquitetura genérica em [mlverse/tft](https://github.com/mlverse/tft) / [pytorch](https://github.com/dehoyosb/temporal_fusion_transformer_pytorch) | Parcial — reimplementar arquitetura |
| DengAI comunidade (benchmark) | Vários (DrivenData) | Casos + clima, San Juan/Iquitos | 1 sem. (competição) | Corte de MAE da competição | Variável, não peer-reviewed | [ex.: umstek/DengAI](https://github.com/umstek/DengAI) | Sim — baixo esforço, baixo valor de evidência |

---

## Lacunas identificadas

- **Nenhum modelo mecanístico SEIR/Ross-Macdonald com vetor calibrado para o Brasil e com código aberto
  permissivo foi encontrado.** O candidato mais completo (zmz48844) é para Guangdong; o único mecanístico
  brasileiro com código (CLiDENGO, dentro de D-FENSE) tem licença não-permissiva (CC-BY-NC-ND).
- **O achado mais forte da varredura de literatura anterior (ensemble de Wu et al. 2025) não tem código
  público confirmado** — é reimplementável (os componentes AR/VAR/ETS são triviais), mas não há atalho
  de "rodar o que o paper rodou".
- **O modelo que efetivamente é usado como régua nacional (INLA de Freitas et al. 2025) só usa casos
  históricos — não clima, não vetor.** Isso é compatível com o achado da varredura anterior de que
  baselines simples são difíceis de vencer: a régua oficial brasileira nem tenta usar mais atributos.
- **Nenhum repositório encontrado combina, ao mesmo tempo, (a) cidade única, (b) horizonte de 12 semanas,
  (c) clima E índice de vetor por armadilha como no projeto** — o mais próximo em desenho (ARBOALVO,
  Natal-RN, ovitrampa+clima+INLA/CAR) tem horizonte de só 4 semanas e não expõe URL de código.
