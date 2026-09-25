# Verificação adversarial — grupo 1 (4 modelos da literatura)

Método: fonte primária lida via WebFetch/WebSearch (PMC, PNAS, PLOS NTD, PDF do artigo). Sem download de arquivo, só leitura remota.

## Índice 0 — LASSO, Shi et al. 2016 (EHP)

**Status: CONFIRMADO** — todos os campos batem com o texto (PMC5010413).

- MAPE definido por janela de previsão sobre o conjunto de validação — fórmula bate.
- LASSO: 17% (IC95% 16-19%) em 1 semana; 24% (IC95% 22-26%) em 12 semanas — literal.
- SARIMA: 29% (IC95% 26-32%) em 12 semanas — literal ("29% at 3 months ahead").
- Treino 2001-2010, validação 2011-2012, teste 2013 — confirmado.
- Uso operacional confirmado, citação literal: *"our forecasts helped guide hospital bed management and public health interventions, including preemptive source reduction measures..."*
- Surto 2013: 22.170 casos/ano, pico 842 casos/semana (sem. 25) — literal.
- Horizonte "1 to 12 weeks", rotulado "3-month time horizon" — bate.

## Índice 1 — Ensemble de 11 modelos, Wu et al. 2025 (PNAS)

**Status: CONFIRMADO**, com uma nuance a registrar.

- PAE ensemble: 38,5% / 54,5% / 62,7% em 1/2/3 meses — literal (Fig. 3).
- Melhor modelo isolado é VAR regularizado: 40% / 55% / 64% — bate.
- PAE só é nomeado no corpo principal; fórmula fica no SI Appendix (não acessado) — confirmado.
- Escala: 187 localidades, Brasil 27 estados, Tailândia 77 províncias, mensal — literal.
- Out-of-sample confirmado no texto.
- Uso prospectivo 2022-2023 para alocar recursos de ensaios clínicos em BR/CO/MY/MX/TH — confirmado quase literal.
- ⚠️ **Nuance (não é erro, é imprecisão de nomenclatura):** os "11 modelos" são os componentes candidatos (AR, ARGO, NetModel, VAR-reg, VAR-clust-reg, ARGONet, DT-SIR, ETS, Stacked ML, Naive, Seasonal); o "ensemble" final combina **subconjuntos otimizados** desses 11, não a soma fixa dos 11. Chamar o modelo de "Ensemble de 11 modelos" é aceitável como atalho, mas tecnicamente são "2 ensembles construídos a partir de 11 componentes".

## Índice 2 — CatBoost, Aleixo et al. 2022 (AI4Health)

**Status: CONFIRMADO** — todos os campos batem com o PDF do artigo.

- Escala: 160 distritos do Rio de Janeiro, mensal, jan/2011-out/2020 — literal.
- R²: *"For the R2, we used the variance of the respective test set"* — citação literal confirmada. Agregação é **por mês civil, juntando as previsões dos 160 distritos daquele mês**: *"For each error measurement, we consider the predictions for all districts in a single month"* — confirma o mecanismo descrito no item.
- CatBoost: mediana R² = 0,47 (p25=0,31) em 1 mês; 0,38 (p25=0,08) em 3 meses — literal (Fig. 3).
- SARIMA: mediana R² = 0,11 (1 mês) e -0,16 (3 meses) — literal.
- CV: 5-fold, 1 ano teste / 4 anos treino, incluindo anos **futuros** (ex.: para prever 2017 treina com 2016+2018+2019+2020) — confirmado literalmente, não é walk-forward estrito.
- Casos por distrito-mês (2016-2020): p95=24, p99=77 — literal.
- Uso: só pesquisa, sem relato de adoção operacional; mencionam ferramenta de visualização web como trabalho futuro — confirmado.
- R² negativo em transição de temporada (fev/jun/jul) — citação literal confirmada.

## Índice 3 — Random Forest, Zhao et al. 2020 (PLOS NTD)

**Status: CONFIRMADO**

- Escala: 30 departamentos colombianos + nível nacional, semanal — confirmado.
- MAE definido e calculado sobre as 52 semanas de 2018 (teste) — citação literal: *"The MAEs... were calculated for the 52 weeks in 2018..."*
- Random Forest: MAE 9,32 (1 semana) e 24,56 (12 semanas) — modelo nacional agrupado, confirmado.
- ARIMA: valores absolutos por horizonte **não estão tabulados** no artigo (só RMAE relativo) — bate com o "não localizado" do item; não é falha da extração, é o artigo mesmo que omite.
- Treino 2014-2017, teste 2018, mais leave-one-season-out CV em 5 iterações (cada ano como teste, 4 como treino) — confirmado, bate com "janelas de 5 anos".
- Pico de casos: mais de 2.500/semana no fim de 2015 — citação literal.
- Uso: só pesquisa acadêmica, sem relato operacional — confirmado.

## Resumo

4 de 4 itens **confirmados** contra a fonte primária. Única ressalva: rotular o modelo de Wu et al. 2025 como "Ensemble de 11 modelos" é uma simplificação aceitável — tecnicamente são 2 ensembles finais construídos a partir de 11 componentes candidatos, não a soma fixa dos 11.
