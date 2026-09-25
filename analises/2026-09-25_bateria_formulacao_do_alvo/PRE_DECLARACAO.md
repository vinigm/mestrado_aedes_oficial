# Pré-declaração — bateria de formulação do alvo

> **Escrita em 25/09/2026, antes de rodar qualquer braço.** Autorizada pelo Vinicius em 25/09/2026
> ("pode rodar todas em sequência"). Mudança posterior vira **emenda datada** no fim deste arquivo.
>
> ⚠️ **Rodada exploratória.** O período de avaliação (2024+) já foi visto: foi ele que mostrou o modelo
> perdendo para a regra sazonal ([régua das regras simples](../2026-09-25_regua_regras_simples/)).
> Nada aqui troca a referência. O juiz confirmatório é a temporada **2026-2027**.

---

## 1. Por que esta rodada existe

**O que o dado mostra** (medido em 25/09/2026, avaliação 2024+, 102 semanas por horizonte):

| h | HistGB folha 20 com vetor | mesma semana do ano passado |
|---|---|---|
| 8 | 223,2 | **216,2** |
| 12 | 243,8 | **217,8** |

MAE em casos por semana. A régua sazonal vence também na perda quantílica 0,85, que é a perda que o
modelo otimiza: **191,2 × 170,6** em h=12.

**O que já se sabe e não se repete:** lags de 5 a 12 semanas, lag de 52 e 104 semanas contado da semana
de origem, anomalias, acúmulos de 8 a 12 semanas, ENSO, atributos do InfoDengue, 9 algoritmos, 5 perdas
e a grade de hiperparâmetros. Todos reprovados.

**Hipótese de trabalho:** a informação sazonal está nos dados, mas a forma como o modelo recebe o alvo e
os atributos impede que ele a use. O lag 52 testado era contado da **origem**; a regra que vence usa a
semana **alvo** do ano anterior. São números diferentes: em h=12, distam 12 semanas.

**Base na literatura** ([varredura de 25/09](../2026-09-25_varredura_literatura/)):

- Perder para régua estatística simples em 12 semanas é achado recorrente: SARIMA venceu 16 modelos no
  pico (Johansson et al. 2019) e ARIMA venceu Random Forest em 12 semanas (Benedum et al. 2020).
- Ensembles com componentes heterogêneos venceram a régua em 1-3 meses (Colón-González et al. 2021;
  Wu et al. 2025).
- Taxa de crescimento do vetor superou a abundância bruta como preditor (Sedda et al. 2020).
- Nenhum trabalho localizado usa o resíduo sobre o ano anterior como alvo. É lacuna, não resultado.

---

## 2. Os braços

Todos em **h = 1, 4, 8 e 12**. Quantil 0,85 em todos. As 20 colunas do cenário adotado são a base; o
clima escolhido tem de ser **o mesmo em todos os braços**: `temp_media_lag4 · umid_media ·
temp_media_lag3 · temp_max · pressao_media_lag3 · pressao_media_lag4`.

| Braço | O que muda em relação ao B0 | Hipótese que testa |
|---|---|---|
| `referencia` | HistGB folha mínima 5, o cenário adotado | trava 1 |
| **`B0`** | HistGB folha mínima 20, com vetor. **Base de todas as comparações** | trava 2 |
| `V1_alvo_log` | treina em `log1p(casos)`, devolve `expm1` | erro relativo em vez de absoluto |
| `V2_ancora_atributo` | + coluna `ancora` = casos da semana-alvo, 52 semanas antes | o modelo usa a régua se a receber alinhada |
| `V3_ancora_residuo` | + `ancora`; alvo = `log1p(casos) − log1p(ancora)`; previsão = `expm1(resíduo + log1p(ancora))` | o modelo aprende o desvio da temporada em relação à anterior |
| `V4_crescimento_vetor` | + 2 colunas: `log1p(vetor_t) − log1p(vetor_t−1)` e `log1p(vetor_t) − log1p(vetor_t−4)` | a velocidade do vetor informa mais que o nível |
| `V5_linear_log` | regressão quantílica **linear** 0,85 em log, sem penalização, mesmas 20 colunas | um modelo que extrapola, na linha dos ARIMA que vencem em 12 semanas |
| `V6_mistura` | média simples, peso fixo 0,5, entre o B0 e a régua sazonal. Sem treino | ensemble heterogêneo |
| `V3_ancora_residuo_M0` | o V3 sem as 6 colunas do vetor | quanto o vetor vale dentro do V3 |

### Regras de construção, fixadas antes

- `ancora` na linha de origem `t` = casos em `t + h − 52` semanas. Como `h ≤ 12`, o valor tem ao menos
  **40 semanas** na origem.
- Nos braços em log, previsão negativa vira **0**. No B0 e na referência nada muda.
- `V5`: `log1p` nas colunas de casos e de vetor, padronização ajustada **só no treino** de cada corte,
  `QuantileRegressor(quantile=0.85, alpha=0, solver="highs")`.
- `V6`: `0,5 × previsão do B0 + 0,5 × casos na data_alvo − 52 semanas`. O peso **não** é ajustado.
- As colunas novas não disputam vaga de clima: entram como reservadas (`colunas_reservadas` do harness).
- Braços com `ancora` perdem as primeiras ~52 semanas de treino, porque o casos começa em 18/02/2018.
  A avaliação não muda; o pareamento por `data_alvo` absorve a diferença.

---

## 3. Travas, antes de ler qualquer resultado

1. `referencia` reproduz o painel: MAE **98,0 / 219,7 / 272,6 / 278,7** e R² **0,898 / 0,628 / 0,450 /
   0,437**, tolerância do harness.
2. `B0` reproduz o `HistGB_folha20_M1` do bloco 7 **exatamente**, em MAE e n: **133,6 / 199,6 / 223,2 /
   243,8**, 102 semanas por horizonte.
3. O clima escolhido é idêntico em todos os braços.

Se uma trava falhar, a rodada é **inválida** e nada é lido.

---

## 4. Métrica, teste e famílias

- **Métrica primária:** MAE pareado por `data_alvo`, avaliação `data_alvo ≥ 2024-01-01`.
- **Teste:** Wilcoxon bilateral do erro absoluto, pareado.
- **Família F1 — a variante melhora o B0?** V1 a V6 × h 1, 4, 8, 12 = **24 comparações**, Holm sobre 24.
- **Família F2 — a variante bate a régua sazonal?** B0 e V1 a V6 × h 4, 8, 12 = **21 comparações**, Holm
  sobre 21. Em h 4, 8 e 12 a régua sazonal é a melhor das três regras simples na avaliação.
- **Família F3 — o vetor vale dentro do V3?** `V3_ancora_residuo_M0` × `V3_ancora_residuo` × h 1, 4, 8,
  12 = **4 comparações**, Holm sobre 4.

### Leituras descritivas, sem teste

- Perda quantílica 0,85 e skill score contra a melhor regra simples, por braço e horizonte.
- MAE na **calibração epidêmica**, `2022-01-01 ≤ data_alvo < 2024-01-01`.
- MAE por ano do alvo.
- MAE separado em semanas com `real ≥ 100` casos e `real < 100`.

---

## 5. Critérios de decisão

- **A variante melhora o modelo** se, em **h=12**, o MAE for menor que o do B0 com **p Holm F1 < 0,05**.
- **A variante bate a régua** se, em **h=12**, o MAE for menor que o da régua sazonal com
  **p Holm F2 < 0,05**.
- **Candidata à rodada confirmatória 2026-2027** só se melhorar o modelo **e** não piorar o MAE do B0 em
  h=12 na calibração epidêmica 2022-2023.
- **Réplica condicional:** cada candidata é refeita com **LightGBM folha 20**, contra o `LightGBM_M1` do
  bloco 5, em h=12. Um teste por candidata, Holm sobre o número de candidatas. É réplica, não decisão.
- **O vetor vale dentro do V3** se, em h=12, tirar o vetor aumentar o MAE com **p Holm F3 < 0,05**.

---

## 6. Ameaças já conhecidas

- **Duas temporadas de avaliação.** 2024 e 2025 foram as maiores da série. A régua sazonal e as variantes
  ancoradas nela se beneficiam de anos grandes seguidos.
- **Risco herdado da âncora:** se 2026-2027 for menor que 2025-2026, o V2, o V3 e o V6 tendem a
  superestimar. A temporada confirmatória testa exatamente isso.
- **O corte de maturidade age só no fim da série.** No walk-forward, os casos das 12 semanas anteriores à
  origem aparecem maduros. Vale igual para todos os braços.
- **Nove braços medidos no mesmo período:** um resultado positivo aqui é hipótese para 2026-2027, não
  conclusão.

---

## Emendas

Nenhuma até agora.
