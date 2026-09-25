# Verificação adversarial — grupo 2 (D-MOSS, superensemble, CatBoost/GRU, MFAI)

Método: WebFetch direto nas 4 fontes (PMC/PLOS), tentando reprovar cada campo. Sem download de arquivo.

---

## Item 0 — CatBoost/GRU, 27 capitais (da Cunha e Silva 2026)

**Status: CONFIRMADO**, com uma ressalva.

- R², sMAPE, equações (13/12), reversão de log1p, escala /100mil hab., 27 capitais, 1999-2021,
  horizonte 1-4 semanas / 13 folds, walk-forward com scaler por janela, ausência de régua/baseline,
  instituições (UNESP Sorocaba + Univ. Minho) — todos batem exatamente com o texto.
- Valores batem: CatBoost R² -0,2064 / sMAPE 160%; GRU R² -0,3085 / sMAPE 97%.
- ⚠️ **Ressalva:** o texto recuperado diz POA está "entre os piores desempenhos" (falhas na Região
  Sul), não confirma explicitamente que POA é **o pior das 27**. Correção: trocar "foi o pior
  resultado" por "um dos piores resultados", salvo confirmação adicional.
- Casos típicos (zeros 10-59%, máximo 60,55/100mil) não verificável no texto recuperado —
  não contradiz, apenas não foi encontrado no trecho.

## Item 1 — MFAI vs Index P, Porto Alegre (da Silva et al. 2026, PLOS NTD)

**Status: PARCIAL** — um campo conflita com a fonte.

- R²=0,46 / MAE=0,79 sobre log(incidência+1)/100mil, deviance ratio 0,04 do só-clima, afirmação
  "contribuição não é metodológica", 72.965 casos (51% confirmados, 93% autóctones), pico sem 13-21
  de 2025, lags 0-8 semanas, horizonte não declarado, janela inicial de 50 semanas — todos confirmados.
- 🔴 **Discrepância:** o item afirma "não há régua/baseline explícita" — mas o texto recuperado cita
  uma comparação **Linear Model (RMSE 1,003) vs LASSO (RMSE 1,13)**. Não fica claro se isso é uma
  régua de fato (tipo persistência) ou só seleção entre especificações de modelo, mas a afirmação
  categórica "não há régua" não se sustenta como está. **Correção:** rever se LM é a régua do artigo
  antes de repetir "sem baseline".

## Item 2 — D-MOSS operacional, Vietnã (Campbell/Colón-González 2026, PLOS GPH)

**Status: PARCIAL** — núcleo numérico confirmado, uma imprecisão de terminologia.

- Operacional desde jun/2019, diretrizes nacionais nov/2020, parceiros (MoH, OMS regional, Pasteur
  Nha Trang/HCMC, NIHE, Tay Nguyen=TIHE), 63 províncias, mensal, incidência/100mil, horizonte 1-6
  meses com refit mensal, RMSE por lead time e médias (20,35×23,93 em 1 mês; 25,99×35,38 em 6 meses;
  25,70×31,29 na média), régua = média sazonal expansiva desde ago/2002 — tudo confirmado.
- 692.617 casos totais confirmado. Não verificado no trecho recuperado: HCMC 120.161 (17%) e a
  variação ~1:100 entre províncias extremas — não contradiz, só não apareceu no texto extraído.
- ⚠️ **Correção de termo:** a fonte contrasta explicitamente "previsões operacionais prospectivas...
  e não hindcast retrospectivo". O item usa "hindcast operacional real" — termos que a própria fonte
  trata como opostos. Trocar para "previsão prospectiva operacional real".

## Item 3 — Superensemble precursor do D-MOSS (Colón-González et al. 2021, PLOS Medicine)

**Status: CONFIRMADO.**

- Número do artigo corrigido para **18(3):e1003542** — confirmado (não é 18(6)).
- Co-desenho com OMS/MoH Vietnã/Pasteur, "será avaliado prospectivamente" (ainda não operacional em
  2021), 63 províncias, dados até 2019/abr-2020, contagem de casos não normalizada, ~95 mil casos/ano
  nacional vs ~2 milhões de infecções estimadas (até 80% assintomáticas), Hanói ~8.700/ano, horizonte
  1-6 meses com vantagem só em 1-3 meses, CRPS via pacote SpecsVerification, valores exatos (66,8
  IC 60,6-148,0 × 79,4 IC 78,5-80,5 em 1-3 meses; baseline vence em 4-6 meses), régua = mesma
  incidência sazonal repetida, TSCV expansiva (treino ago/2002-dez/2006, teste jan/2007-dez/2016,
  114 meses) — tudo bate exatamente com o texto.
- Não verificado (não contradiz): detalhe "centro-sul na casa dos milhares com alta variância".

---

## Resumo para decisão

| Item | Status | Ação recomendada |
|---|---|---|
| 0 — CatBoost/GRU | Confirmado (1 ressalva) | trocar "o pior" por "um dos piores" |
| 1 — MFAI × Index P | Parcial | verificar se LM (RMSE 1,003) é a régua antes de dizer "sem baseline" |
| 2 — D-MOSS operacional | Parcial | trocar "hindcast" por "previsão prospectiva operacional" |
| 3 — Superensemble 2021 | Confirmado | nenhuma ação |
