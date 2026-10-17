# Reimplementação independente — sensibilidade Newey-West (Emenda 5)

> 17/10/2026. Reimplementado do zero (pandas/numpy/scipy) a partir de `E2_ablacao/previsoes.csv`, `E3_composto/previsoes.csv` (N=13, 102 linhas em h=1) e da régua sazonal (casos em `data_alvo` − 52 semanas de `dados/tabela_final.csv`; `real` da régua conferido contra o da E2). Janela 07/01/2024–01/02/2026, pareamento por `data_alvo`, perda = erro absoluto, `d` = |erro B| − |erro A|. Nenhum módulo `aedes/` e nenhum código do colega importado. Script: scratchpad da sessão (não versionado).

## Resultado: APROVADO

- Diferença máxima por coluna contra `sensibilidade.csv` (13 linhas): `n` 0 · `delta` 5,1e-14 (ruído de soma) · `acf1` 1,1e-16 · `p_dm_hln` 1,1e-16 · `p_newey_west` 1,1e-16 · `p_holm_dm_hln` 1,1e-16 · `p_holm_sensibilidade` 5,6e-17.
- `p_dm_hln` h=1 e Holm pré-declarado também batem com `familias.csv` (dif. máx. 1,1e-16).
- Vereditos pré-declarados e de sensibilidade: **0 divergências** em 13. Mudam 5 de 13 (F1 casos, F2 casos, F2 vetor, F4 compl f5 × régua, F4 composto × régua), todos "A melhor" → "sem evidência".

## Método usado

- DM-HLN h=1: `V = γ0/n`, `DM = d̄/√V`, fator `√((n−1)/n)`, p bilateral t(n−1).
- Newey-West: `V = (γ0 + 2 Σ_{k=1..4} (1−k/5) γk)/n`, `γk = (1/n) Σ (d_t−d̄)(d_{t−k}−d̄)`; t(n−1) bilateral; sem fator HLN.
- Holm por família com os p de h=4, 8, 12 lidos de `familias.csv` (DM-HLN); veredito = p_Holm<0,05 e |Δ|>`limiar_piso` (de `familias.csv`).

## Tabela (reimplementação)

| Família | A × B | n | Δ | ACF1 | p DM-HLN | p NW | Holm pré → sens. | Veredito pré → sens. |
|---|---|---|---|---|---|---|---|---|
| F1 | completo@f5 × sem_casos@f5 | 102 | 118.35 | 0.631 | 0.001305 | 0.06538 | 0.01566 → 0.7845 | A melhor → sem evidencia |
| F1 | completo@f5 × sem_clima@f5 | 102 | -2.80 | 0.197 | 0.6164 | 0.6086 | 1 → 1 | sem evidencia → sem evidencia |
| F1 | completo@f5 × sem_vetor@f5 | 102 | -6.00 | 0.251 | 0.5288 | 0.626 | 1 → 1 | sem evidencia → sem evidencia |
| F2 | so_casos@f5 × so_calendario@f5 | 109 | 156.38 | 0.669 | 3.529e-05 | 0.02082 | 0.0004235 → 0.2498 | A melhor → sem evidencia |
| F2 | so_clima@f5 × so_calendario@f5 | 109 | 17.45 | 0.111 | 0.1564 | 0.2065 | 0.7822 → 1 | sem evidencia → sem evidencia |
| F2 | so_vetor@f5 × so_calendario@f5 | 102 | 54.59 | 0.639 | 0.003033 | 0.07888 | 0.03336 → 0.7888 | A melhor → sem evidencia |
| F3 | completo@f20 × sem_casos@f20 | 102 | 75.54 | 0.653 | 0.02125 | 0.1205 | 0.255 → 1 | sem evidencia → sem evidencia |
| F3 | completo@f20 × sem_clima@f20 | 102 | -0.48 | 0.124 | 0.9145 | 0.9272 | 1 → 1 | sem evidencia → sem evidencia |
| F3 | completo@f20 × sem_vetor@f20 | 102 | -18.13 | -0.054 | 0.08285 | 0.06551 | 0.9114 → 0.7862 | sem evidencia → sem evidencia |
| F4 | completo@f5 × regua_sazonal | 102 | 104.12 | 0.471 | 0.0002515 | 0.02021 | 0.004024 → 0.3234 | A melhor → sem evidencia |
| F4 | completo@f20 × regua_sazonal | 102 | 68.48 | 0.482 | 0.01946 | 0.1038 | 0.2724 → 1 | sem evidencia → sem evidencia |
| F4 | composto_N13 × regua_sazonal | 102 | 99.78 | 0.435 | 0.0004238 | 0.02146 | 0.006357 → 0.3234 | A melhor → sem evidencia |
| F4 | composto_N13 × completo@f5 | 102 | -4.35 | 0.164 | 0.3522 | 0.3321 | 1 → 1 | sem evidencia → sem evidencia |

## Origem provável do p ≈ 0,10 (composto × régua, h=1; n=102, Δ=99,78, ACF1..4 = 0,435; 0,457; 0,209; 0,119)

Variantes testadas sobre a MESMA série `d` (p bilateral, t com n−1 g.l.):

| Estimador | p |
|---|---|
| DM-HLN h=1 (γ0 apenas) | 0,0004 |
| Newey-West Bartlett L=4 (Emenda 5) | 0,0215 |
| Bartlett L=8 / 12 / 26 | 0,043 / 0,054 / 0,040 |
| Uniforme (sem Bartlett) L=3 / 4 / 6 | 0,043 / 0,051 / 0,071 |
| Uniforme L=8 / 10 / 12 | 0,084 / 0,082 / 0,069 |
| **DM-HLN com h=8 (autocovariâncias 0..7 sem pesos, + fator HLN)** | **0,1017** |
| DM-HLN h=12 / h=13 sem pesos | 0,120 / 0,110 |
| Parzen L=20 · Tukey-Hanning L=20 | 0,062 · 0,062 |
| Pré-branqueamento AR(1) L=0 / 4 / 8 | 0,024 / 0,034 / 0,054 |
| Bootstrap de blocos (4 / 8 / 13 / 26) | 0,012 / 0,036 / 0,056 / 0,013 |
| Perda quadrática, NW L=4 | 0,034 |

- **Candidato mais provável: variância de longo prazo SEM pesos de Bartlett com ~8 autocovariâncias.** A fórmula do DM-HLN do projeto aplicada com `h=8` à série de h=1 (lags 0..7 somados com peso 1, mais correção HLN) dá **p = 0,1017**; sem HLN, uniforme L=7/8 dá 0,084–0,09. Seria o estimador "DM com h grande" do revisor.
- Sem pesos o estimador pode ficar não-positivo ou instável e é sensível ao L: p vai de 0,051 (L=4) a 0,12 (h=12), cruzando 0,10 só em torno de L≈8–12.
- **Não explicam 0,10:** L maior COM Bartlett (p fica 0,04–0,054), g.l. diferentes (normal vs t muda ≤0,002), pré-branqueamento, bootstrap.
- Leitura: o p ≈ 0,10 é um estimador mais conservador (sem pesos, ~8 lags), não discrepância de dado. Cuidado ao relatar: o p de composto × régua em h=1 varia de 0,0004 a ~0,10 conforme o estimador; em NENHUM Bartlett razoável passa de 0,055.

## Conferências

- Reprodução do colega exata no nível de ponto flutuante; sem divergência de veredito. A hipótese sobre 0,10 é inferência (revisor não informou o código): rotular como hipótese.
