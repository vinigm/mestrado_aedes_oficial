# Grid completo — 30 configurações · 30/08/2026

> Regras em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), escritas antes de rodar.

**Execução:** 120 walk-forwards (3 algoritmos × 5 perdas × 2 conjuntos × 4 horizontes),
`passo=1`, ~300 pontos por horizonte. **120 de 120 com sucesso, zero falhas, 2h36.**

**Escolha:** menor MAE médio no período de **calibração** (semanas-alvo até 31/12/2023).
**Veredito:** período de **avaliação** (2024+), que não participou da escolha.

---

## 🏆 Configuração de referência do projeto

**HistGradientBoosting · quantil 0,80 · COM vetor**

```python
HistGradientBoostingRegressor(
    max_iter=250, learning_rate=0.05, max_leaf_nodes=15,
    min_samples_leaf=5, random_state=42,
    loss="quantile", quantile=0.80,
)
```
Conjunto **M1**: núcleo + 6 variáveis de clima + 6 do vetor (`aedes_aegypti_por_armadilha`,
defasagens 1–4 e `vetor_mm4`).

---

## O ranking completo das 30

`MAE cal` = critério de escolha · `MAE aval`, `R² aval`, `viés pico` = período de avaliação.

| # | algoritmo | perda | vetor | MAE cal | dif. | MAE aval | R² aval | viés pico |
|---|---|---|---|---|---|---|---|---|
| 1 | HistGB | q 0.80 | ✅ | 33.18 | +0.0% | 158.3 | 0.786 | −305 |
| 2 | HistGB | q 0.85 | ✅ | 33.85 | +2.0% | 157.3 | 0.793 | −268 |
| 3 | HistGB | q 0.70 | ✅ | 34.36 | +3.6% | 163.0 | 0.773 | −326 |
| 4 | GradBoost | q 0.70 | ✅ | 34.53 | +4.0% | 171.4 | 0.758 | −359 |
| 5 | GradBoost | q 0.85 | ✅ | 34.99 | +5.4% | 162.8 | 0.793 | −251 |
| 6 | GradBoost | q 0.80 | ✅ | 35.85 | +8.0% | 163.8 | 0.785 | −308 |
| 7 | HistGB | q 0.90 | ✅ | 36.77 | +10.8% | 168.5 | 0.766 | −259 |
| 8 | GradBoost | q 0.90 | ✅ | 37.16 | +12.0% | 166.6 | 0.774 | −242 |
| 9 | GradBoost | q 0.85 | — | 37.50 | +13.0% | 175.9 | 0.759 | −191 |
| 10 | GradBoost | padrão | — | 37.76 | +13.8% | 182.0 | 0.713 | −334 |
| 11 | GradBoost | q 0.70 | — | 37.78 | +13.9% | 172.5 | 0.737 | −314 |
| 12 | HistGB | q 0.85 | — | 37.99 | +14.5% | 166.6 | 0.780 | −213 |
| 13 | GradBoost | padrão | ✅ | 38.02 | +14.6% | 173.4 | 0.732 | −391 |
| 14 | HistGB | q 0.70 | — | 38.06 | +14.7% | 167.9 | 0.756 | −289 |
| 15 | HistGB | q 0.80 | — | 38.19 | +15.1% | 170.6 | 0.755 | −255 |
| 16 | GradBoost | q 0.80 | — | 38.24 | +15.2% | 173.0 | 0.748 | −271 |
| 17 | HistGB | padrão | — | 38.53 | +16.1% | 177.1 | 0.714 | −317 |
| 18 | LightGBM | padrão | ✅ | 38.66 | +16.5% | 199.5 | 0.679 | −464 |
| 19 | GradBoost | q 0.90 | — | 39.53 | +19.1% | 180.5 | 0.742 | −147 |
| 20 | HistGB | padrão | ✅ | 39.88 | +20.2% | 167.5 | 0.747 | −362 |
| 21 | HistGB | q 0.90 | — | 40.09 | +20.8% | 176.0 | 0.754 | −174 |
| 22 | LightGBM | q 0.70 | ✅ | 42.11 | +26.9% | 187.4 | 0.710 | −414 |
| 23 | LightGBM | padrão | — | 42.53 | +28.2% | 203.3 | 0.651 | −433 |
| 24 | LightGBM | q 0.80 | ✅ | 44.36 | +33.7% | 168.0 | 0.780 | −295 |
| 25 | LightGBM | q 0.80 | — | 44.54 | +34.2% | 176.0 | 0.753 | −277 |
| 26 | LightGBM | q 0.70 | — | 45.06 | +35.8% | 192.6 | 0.689 | −404 |
| 27 | LightGBM | q 0.85 | — | 47.28 | +42.5% | 175.0 | 0.765 | −202 |
| 28 | LightGBM | q 0.90 | — | 49.66 | +49.7% | 178.2 | 0.757 | −142 |
| 29 | LightGBM | q 0.85 | ✅ | 49.68 | +49.7% | 156.9 | 0.810 | −228 |
| 30 | LightGBM | q 0.90 | ✅ | 53.65 | +61.7% | 162.3 | 0.792 | −173 |

## Os 6 algoritmos que ficaram de fora

Dos 9 do projeto, só 3 entraram: **regressão quantílica exige perda pinball**, e `extra_trees`,
`random_forest`, `ridge`, `elastic_net`, `knn` e `svr` não a implementam. Não é limitação de
configuração — é do método. Os 3 que entraram já eram os 3 melhores na perda padrão
(R² 0,779 · 0,762 · 0,749).

---

## Os três achados

### 1. A função de perda importa mais que o algoritmo

| troca | custo em MAE |
|---|---|
| melhor algoritmo → pior (dos 3) | **+16,5%** |
| quantílico → padrão (mesmo algoritmo) | **+20,2%** |

**As 6 configurações de perda padrão ocupam as posições 10 a 23 de 30.** Nenhuma entra no top 9.

E a ironia: o **HistGB com vetor e perda padrão fica em 20º** — a mesma combinação que, trocando só
a perda, **vence o grid**.

**Consequência para a tese:** meses comparando 9 algoritmos, e o ganho maior estava numa linha de
configuração que nunca foi mexida. É crítica metodológica legítima à literatura da área, que
compara algoritmos e mantém a perda padrão sem discutir.

### 2. O vetor domina o topo — mas não é comprovável

- **8 das 10 melhores** configurações usam vetor;
- posição média: **12,8** (com vetor) contra **18,2** (sem);
- pareado nas mesmas semanas: M1 vence em **35 de 60**, ganho médio de MAE **+7,88**.

**FATO — quebra por horizonte** (o padrão mais forte do dia):

| horizonte | vetor vence | ganho médio |
|---|---|---|
| 1 semana | **0 de 15** ❌ | −12,5 |
| 1 mês | 11 de 15 | +7,7 |
| 2 meses | 9 de 15 | +4,5 |
| **3 meses** | **15 de 15** ✅ | **+31,9** |

Em 12 semanas o vetor vence em **100%** das combinações de algoritmo e perda; em 1 semana perde em
**100%**. Bate com a correlação medida: o vetor segura r=0,47–0,62 enquanto a autocorrelação dos
casos vai a zero.

⚠️ **Nenhuma das 60 comparações sobrevive a Holm** (melhor p bruto 0,0025 → Holm 0,150). O padrão é
consistente, não comprovado.

⚠️ **Não calculei p-valor para "15 de 15"** — escolher esse teste depois de ver o padrão seria pesca.
O caminho honesto é pré-declarar um teste focado em h=12 e rodá-lo.

### 3. As três primeiras são indistinguíveis

Pódio: HistGB com vetor, variando só o alpha (0,80 · 0,85 · 0,70), a **2,0%** e **3,6%** entre si —
dentro do limite de empate técnico declarado. O melhor GradientBoosting fica em 4º, a **+4,0%**,
também dentro da faixa.

**Na avaliação o alpha 0,85 fica à frente** (MAE 157,3 × 158,3; viés −268 × −305). **A escolha não
foi trocada:** a avaliação existe para julgar, não para escolher. Trocar por ela invalidaria a
independência do número. Fica registrado como candidato para um teste próprio, pré-declarado.

---

## Ressalva obrigatória no texto

São **30 configurações competindo**. Escolher a melhor entre 30 garante que **parte da vantagem do
vencedor é sorte** — a separação calibração/avaliação reduz, não elimina.

A afirmação honesta é *"a melhor entre as 30 testadas, com as três primeiras estatisticamente
indistinguíveis"*, **nunca** *"a melhor configuração possível"*.
