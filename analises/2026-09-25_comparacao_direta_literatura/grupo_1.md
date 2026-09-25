# Comparação direta — Grupo 1 (4 artigos)

> Extração feita direto na fonte (WebFetch/WebSearch) em 25/09/2026. Números dos 4 artigos já vinham
> verificados do [catálogo](../2026-09-25_catalogo_modelos_prontos/README.md) e da
> [varredura de literatura](../2026-09-25_varredura_literatura/README.md); esta rodada só extraiu as
> **definições exatas de métrica** e o contexto de uso/escala, que ainda faltavam.
>
> ⚠️ **Nenhum destes 4 modelos é comparável ao nosso por diferença de métrica ou de escala** — ver a
> ressalva em cada item. Isto não é ainda a comparação numérica pedida ("nosso X% × modelo Y Z%"); é o
> material bruto para montá-la com honestidade.

---

## 1. Shi et al. 2016 — LASSO, Singapura (EHP, DOI 10.1289/ehp.1509981)

- **Para que foi usado:** **operacional**, não só pesquisa. Citação literal: *"The forecasting tool
  described in this paper has become an integral part of Singapore's dengue control program."* Rodado
  pela **National Environment Agency (NEA)**, com previsões enviadas ao Ministério da Saúde e ao
  Environmental Public Health Operations Department; usado no surto de 2013 para gestão de leitos
  hospitalares e ações preventivas de controle de foco.
- **Onde e escala:** Singapura **inteira** (não subdividido por área), granularidade **semanal**.
- **Casos típicos por período:** surto de 2013 teve 22.170 casos no ano, com pico de **~842 casos/semana**
  (semana 25). É uma cidade-estado de ~5,5 milhões de habitantes — patamar de casos/semana muito acima do
  de Porto Alegre.
- **Horizonte:** 1 a 12 semanas (rotulado no artigo como "1 a 3 meses").
- **Definição exata da métrica:** MAPE = **média** do erro percentual absoluto sobre o conjunto de
  validação, por janela de previsão w. Fórmula explícita no artigo (soma de |erro|/valor real sobre o
  conjunto V, dividido por |V|).
- **Valor por horizonte:** LASSO — 1 semana: **17%** (IC95% 16–19%); 12 semanas (3 meses): **24%**
  (IC95% 22–26%).
- **Régua e valor da régua:** **SARIMA**, 12 semanas: **29%** (IC95% 26–32%). O LASSO venceu em quase
  todas as janelas, exceto a de 2 semanas.
- **Avaliação fora da amostra:** **sim**. Treino 2001–2010, validação 2011–2012 (define hiperparâmetros
  via 10-fold CV), teste final aplicado a 2013 — ano não usado em nenhuma etapa de ajuste.
- ⚠️ **Comparabilidade:** MAPE de Singapura (cidade toda, semanal, dezenas a centenas de casos/semana em
  surto) não se compara diretamente ao MAE/erro do nosso modelo (Porto Alegre, semanal, escala de casos
  bem menor) sem reprocessar na mesma métrica.

---

## 2. Wu et al. 2025 — Ensemble de 11 modelos, PNAS 122(33):e2422335122

- **Para que foi usado:** **duplo uso**. Retrospectivamente, avaliação em mais de 180 locais; e
  **prospectivamente como plataforma operacional em tempo real** — citação: *"real-time dengue activity
  forecasting platform implemented as a prospective tool to identify when and where an upcoming dengue
  outbreak"* —, usada para orientar alocação de recursos de ensaios clínicos em **Brasil, Colômbia,
  Malásia, México e Tailândia (2022–2023)**.
- **Onde e escala:** **187 localidades**, nível **estado/província** (Brasil: 27 estados; Tailândia: 77
  províncias; também Iquitos-Peru e San Juan-Porto Rico), granularidade **mensal**.
- **Casos típicos por período:** não especificado explicitamente no texto principal; varia muito por
  localidade e temporada (agregação estadual, não municipal — patamar de casos tende a ser bem maior que
  o de uma cidade só).
- **Horizonte:** 1, 2 e 3 meses.
- **Definição exata da métrica:** citada no artigo como **"percent absolute error" (PAE)**, derivada do
  MAE — *"deriving PAE from mean absolute error (MAE)"*. **A fórmula explícita não está no corpo
  principal**, é remetida ao SI Appendix (não acessado nesta rodada). **Não encontrada a definição
  completa (média vs. mediana, denominador exato).**
- **Valor por horizonte:** ensemble — **38,5% / 54,5% / 62,7%** em 1/2/3 meses (Figura 3, painéis A–C).
- **Régua e valor da régua:** **melhor modelo isolado** (não a régua sazonal): modelos VAR seguintes
  tiveram **40% / 55% / 64%**. O ensemble venceu o melhor modelo isolado, por margem pequena.
- **Avaliação fora da amostra:** **sim** — citação: *"out-of-sample forecasts utilizing the designated
  test period"* e *"out-of-sample accuracy for each forecast horizon"*.
- ⚠️ **Comparabilidade:** escala estadual/provincial mensal com heterogeneidade de locais não é comparável
  a uma série semanal de uma cidade só; e a métrica PAE não tem denominador confirmado nesta rodada.

---

## 3. Aleixo et al. 2022 — CatBoost, Rio de Janeiro (AI4Health, best paper)

- **Para que foi usado:** **pesquisa acadêmica** (não há evidência de uso operacional). Objetivo
  declarado: *"assist public health epidemiological policies"* — é uma proposta de ferramenta, código e
  dados publicados em GitLab, sem relato de adoção por órgão de saúde.
- **Onde e escala:** cidade do **Rio de Janeiro**, **160 distritos** individuais (modelo único para todos
  os distritos, mas previsão é por distrito), granularidade **mensal**, dados jan/2011–out/2020 (SINAN).
- **Casos típicos por período:** distribuição de casos por distrito-mês (2016–2020): **percentil 95 = 24
  casos**, **percentil 99 = 77 casos** (Figura 1 do artigo). É uma escala de casos por distrito-mês bem
  mais baixa que a cidade inteira de Porto Alegre por semana.
- **Horizonte:** 1, 2 e 3 meses (multistep recursivo).
- **Definição exata da métrica:** **R² usando a variância do respectivo conjunto de teste** — citação
  literal: *"For the R², we used the variance of the respective test set."* É calculado **por mês
  civil, agregando todos os distritos naquele mês** (não é um R² único do modelo inteiro); o valor
  reportado no catálogo é a **mediana** dessa distribuição de R² mensais (Figura 3: tabela de percentis).
  O próprio artigo alerta que R² mensal pode ficar **negativo** em meses de início/fim de temporada
  (fevereiro, junho, julho), porque o denominador é a variância de casos daquele mês específico.
- **Valor por horizonte:** mediana do R² mensal — **1 mês: 0,47** (25º percentil 0,31); **3 meses: 0,38**
  (25º percentil 0,08).
- **Régua e valor da régua:** **SARIMA** por distrito. Mediana do R² — 1 mês: **0,11**; 3 meses:
  **−0,16**. O CatBoost venceu com folga nesta métrica, mas o próprio artigo pondera que **MAPE e R²
  mensal são pouco confiáveis** por dependerem da escala de casos de cada mês, e recomenda métricas de
  classificação de surto em vez de regressão pura.
- **Avaliação fora da amostra:** **sim**, mas desenho é validação cruzada de 5 anos (2016–2020), 1 ano de
  teste e os outros 4 (não necessariamente anteriores) como treino — não é um corte temporal
  estritamente prospectivo ano a ano (ex.: para prever 2017 usa 2016+2018+2019+2020 como treino, incluindo
  anos **futuros** ao ano previsto). ⚠️ Isso é diferente de walk-forward puro.
- ⚠️ **Comparabilidade:** R² mensal por distrito-mês não é comparável a um MAE/MAPE semanal cidade-inteira
  sem reagregar; e o desenho de treino inclui anos futuros ao alvo, o que o nosso protocolo (corte pela
  data da resposta) proíbe.

---

## 4. Zhao et al. 2020 — Random Forest, Colômbia (PLOS NTD, DOI 10.1371/journal.pntd.0008056)

- **Para que foi usado:** **pesquisa acadêmica** — comparação de metodologias de ML (ARIMA, RF, ANN)
  publicada em periódico revisado por pares, sem relato de implementação operacional.
- **Onde e escala:** **nível nacional** (agregado) e **departamental** (30 departamentos colombianos),
  granularidade **semanal**.
- **Casos típicos por período:** série nacional teve **mais de 2.500 casos/semana** no pico de fim de
  2015 — escala nacional de um país inteiro, não de uma cidade.
- **Horizonte:** 1 a 12 semanas.
- **Definição exata da métrica:** MAE calculado sobre as **52 semanas de 2018** (conjunto de teste),
  comparando casos previstos × observados semana a semana — citação literal: *"The MAEs of the ARIMA,
  RF, and ANN models were calculated for the 52 weeks in 2018 by the actual and the predicted numbers of
  dengue cases."*
- **Valor por horizonte:** Random Forest — **1 semana: MAE 9,32**; **12 semanas: MAE 24,56**.
- **Régua e valor da régua:** **ARIMA** como linha de base (valores exatos por horizonte não extraídos
  nesta rodada — não encontrados no texto consultado); há também comparação com um modelo ANN nacional.
- **Avaliação fora da amostra:** **sim** — treino 2014–2017, teste reservado em 2018; também rodou
  "leave-one-season-out cross-validation" com iterações de 5 anos.
- ⚠️ **Comparabilidade:** MAE em unidades de casos absolutos só é comparável entre séries de magnitude
  semelhante. Escala nacional colombiana (milhares de casos/semana) é muito maior que Porto Alegre — MAE
  de 9,32 a 24,56 casos aqui não diz nada sobre erro relativo nessa escala maior.

---

## 5. O que ficou pendente

- **Wu et al. 2025:** fórmula exata de PAE está no SI Appendix, não acessado nesta rodada (paywall/bloqueio
  de leitura direta do PNAS).
- **Zhao et al. 2020:** valor exato do MAE do ARIMA (régua) por horizonte não foi localizado no texto
  consultado (site PLOS não abriu o artigo completo diretamente; extração via busca).
- Nenhum destes 4 é comparável **numericamente** ao cenário adotado do projeto sem reagregar por escala
  de casos e por definição de métrica — a comparação "nosso X% × modelo Y Z%" ainda não pode ser feita com
  honestidade estatística a partir só destes 4 artigos.
