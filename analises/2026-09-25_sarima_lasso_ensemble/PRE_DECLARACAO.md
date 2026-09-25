# Pré-declaração — SARIMA, LASSO quantílico e ensemble

> **Escrita em 25/09/2026, antes de rodar qualquer braço.** Autorizada pelo Vinicius em 25/09/2026
> ("pode fazer o a+b"), incluindo a instalação do `statsmodels` 0.15.0 no ambiente isolado
> `~/.venvs/aedes_modelos_fundacao/`. Mudança posterior vira **emenda datada** no fim.
>
> ⚠️ **Rodada exploratória.** A avaliação 2024+ já foi vista. O juiz confirmatório é **2026-2027**.

---

## 1. Pergunta e por quê

**Os dois modelos estatísticos que a literatura mostra vencendo em 12 semanas, e um ensemble de tudo o
que já temos, batem a regra "mesma semana do ano passado" em 3 meses?**

- **O que o dado mostra:** a régua sazonal erra **217,8** em h=12; o melhor modelo do projeto, o `B0`,
  **243,8**; o melhor modelo de fundação, **227,2**.
- **Base na literatura** ([catálogo de 25/09](../2026-09-25_catalogo_modelos_prontos/)):
  - SARIMA venceu 16 modelos no pico (Johansson 2019) e ARIMA venceu Random Forest em 12 semanas
    (Benedum 2020);
  - LASSO de Shi et al. 2016, em produção em Singapura, venceu SARIMA em 12 semanas: MAPE 24% × 29%;
  - ensembles venceram a régua em 1-3 meses (Colón-González 2021, Wu 2025).
- **Por que o LASSO pode não explodir:** a regressão linear em log de 25/09 explodiu porque os lags de
  casos são quase colineares e não havia penalização. O LASSO é a mesma família **com** penalização L1.

---

## 2. Os braços

Todos em **h = 1, 4, 8 e 12**, nos pares `(h, data_alvo)` do `HistGB_folha20_M1` do bloco 7. Origem =
`data_alvo − h` semanas. Previsão usada: o **quantil 0,85**.

| Braço | Modelo | Ambiente |
|---|---|---|
| `sarima_log` | SARIMA(2,0,0)(0,1,0)₅₂ **sem constante**, em `log1p(casos)` | venv isolado |
| `lasso` | regressão quantílica 0,85 com penalização L1, as 20 colunas do `B0` | Python do projeto |
| `lasso_M0` | o mesmo, sem as 6 colunas do vetor | Python do projeto |
| `ens_media` | média simples de 5 componentes | — |
| `ens_pesos` | média ponderada dos 5 componentes, pesos aprendidos no walk-forward | — |

### Regras de construção, fixadas antes

**`sarima_log`**

- Em palavras: **a regra sazonal mais uma correção autorregressiva curta.** A diferença sazonal faz o
  modelo partir de "o ano passado"; o AR(2) corrige com o desvio das semanas recentes. Sem constante, a
  correção some com o horizonte e a previsão converge para a régua.
- Ajustado em cada origem com a série de 18/02/2018 **até a origem**. Previsão de 12 passos.
- q0,85 = `expm1(média + 1,0364 × erro-padrão)` da previsão em log. Previsão negativa vira 0.
- Se o ajuste não convergir numa origem, a origem entra com a régua sazonal no lugar e é **contada e
  relatada**.

**`lasso` e `lasso_M0`**

- `QuantileRegressor(quantile=0.85, solver="highs")` do scikit-learn, alvo `log1p(y_h)`, `log1p` nas
  colunas de casos e de vetor, padronização ajustada **só no treino** de cada corte.
- Treino cortado pela data da **resposta**, como em todo walk-forward do projeto.
- **Penalização `alpha`** escolhida por horizonte, **uma vez só**, na grade `{0,001 · 0,01 · 0,1}`: a de
  menor perda quantílica 0,85 nos pares da **calibração epidêmica**, `2022-01-01 ≤ data_alvo < 2024-01-01`.
  Depois fica fixa na avaliação.
- Previsão = `max(0, expm1(·))`.

**Os 5 componentes do ensemble:** `B0` · `c2_casos`, o Chronos-2 só com casos, da rodada de 25/09 ·
`sarima_log` · `lasso` · régua sazonal.

**`ens_media`:** média simples dos 5.

**`ens_pesos`:**

- Em cada origem, pesos **não negativos que somam 1**, numa grade de passo **0,1**, com 1.001 combinações.
- Escolhidos pela menor perda quantílica 0,85 nos pares **já respondidos na origem**, do mesmo horizonte,
  com `data_alvo ≤ origem` e os 5 componentes disponíveis.
- Com menos de 26 pares respondidos, usa pesos iguais.
- Empate: vence a combinação de maior peso na régua, a mais simples.

---

## 3. Travas, antes de ler qualquer resultado

1. **Pareamento:** todos os braços com os pares do `B0`, 102 por horizonte na avaliação.
2. **Sem futuro:**
   - no SARIMA, a última data ajustada é a origem;
   - no LASSO, toda linha de treino tem `data + h ≤ origem`;
   - no ensemble, os pesos da origem usam só pares com `data_alvo ≤ origem`.
3. **Âncoras:**
   - `B0` 133,6 / 199,6 / 223,2 / 243,8;
   - régua 202,1 / 213,2 / 216,2 / 217,8;
   - `c2_casos` 193,6 / 255,8 / 256,1 / 227,2.
4. **Determinismo:** 5 origens repetidas dão resultado idêntico no SARIMA e no LASSO.
5. **Clima:** o `lasso` usa as mesmas 6 colunas de clima do `B0`.

Se uma trava falhar, nada é lido.

---

## 4. Métrica, teste e famílias

- **Métrica primária:** MAE do q0,85, pareado por `data_alvo`, avaliação `data_alvo ≥ 2024-01-01`.
- **Teste:** Wilcoxon bilateral do erro absoluto, pareado.
- **Família J1 — bate a régua?** `sarima_log`, `lasso`, `ens_media`, `ens_pesos` × h 4, 8, 12 =
  **12 comparações**, Holm sobre 12.
- **Família J2 — melhora o B0?** os mesmos 4 × h 1, 4, 8, 12 = **16 comparações**, Holm sobre 16.
- **Família J3 — o vetor vale no LASSO?** `lasso` × `lasso_M0` × h 1, 4, 8, 12 = **4 comparações**, Holm
  sobre 4.
- **Toda tabela de família traz MAE dos dois lados e a direção**, não só o p. Lição da rodada anterior.

### Leituras descritivas, sem teste

- Perda quantílica 0,85, cobertura do q0,85, MAE por ano, calibração epidêmica, faixas `real ≥ 100` e
  `< 100`.
- Os pesos médios do `ens_pesos` por horizonte na avaliação: **quem o ensemble escolhe**.
- Os `alpha` escolhidos e quantas colunas o LASSO zera por horizonte.

---

## 5. Critérios de decisão

- **Bate a régua** se, em **h=12**, o MAE for menor que o da régua com **p Holm J1 < 0,05**.
- **Melhora o modelo** se, em **h=12**, o MAE for menor que o do `B0` com **p Holm J2 < 0,05**.
- **O vetor vale no LASSO** se, em **h=12**, `lasso` tiver MAE menor que `lasso_M0` com **p Holm J3 < 0,05**.
- **Candidato a 2026-2027** se bater a régua **ou** melhorar o modelo, **e** não for pior que o `B0` em h=12
  na calibração epidêmica.
- Nada troca a referência nesta rodada.

---

## 6. Ameaças já conhecidas

- **Duas temporadas de avaliação**, as maiores da série.
- **O `sarima_log` converge para a régua** em horizonte longo, por desenho. Um empate com a régua em h=12 é
  o esperado; o teste interessante está em h=4 e h=8.
- **O ensemble contém a régua.** Se ele "bater a régua", parte do mérito é dela. Os pesos médios mostram
  quanto.
- **O `c2_casos` pode ter visto 2024-2025** no pré-treino, publicado em 30/10/2025.
- **Muitas rodadas no mesmo período:** é a quarta bateria em 25/09. Resultado positivo é hipótese para
  2026-2027.

---

## Emendas

Nenhuma até agora.
