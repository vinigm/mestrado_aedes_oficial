# Certificação mecânica adversarial — bateria de formulação do alvo

> Certificador independente, tentando **reprovar** os dois braços com previsões explosivas.
> Código próprio em `cert_mecanica.py`, sem importar nada de `rodar.py` — só `harness.montar_features_do_braco`,
> `harness.construir_alvo_horizonte` e `corte_temporal.selecionar_treino_ja_respondido`. Formulação do alvo,
> classe da regressão linear e seleção de colunas para log1p foram **reimplementadas do zero**.

## Veredito resumido

| Braço | Previsão explosiva | Reproduzida? | Veredito |
|---|---|---|---|
| `V3_ancora_residuo` h=12, 2025-03-23 | 10.524 (real 1.801) | **10.524,2** — bate | **Comportamento real** da formulação |
| `V5_linear_log` h=8, 2024-04-21 | 27.258 (real 1.855) | **27.257,7** — bate | **Comportamento real** da formulação |
| `V2_ancora_atributo` (MAE 122,6 × 30,7 do B0) | — | confirmado | **Comportamento real**, risco pré-declarado |

**Nenhum bug de implementação encontrado.** As três explosões são consequência mecânica da formulação
declarada em `PRE_DECLARACAO.md`, não de um erro de código. Nenhuma linha do `rodar.py` precisa correção.

---

## 1. V3_ancora_residuo, h=12, 2025-03-23 (origem 2024-12-29)

**Reprodução:** ancora = **1.109** (casos em 2024-03-24, `data_alvo − 52 sem`, confirmado por data explícita).
Resíduo previsto pelo modelo = **2,2494**. Previsão = `expm1(2,2494 + log1p(1109))` = **10.524,2** — bate a trava.

**O mecanismo, não é bug:**

- A **âncora de teste (1.109) está ACIMA do máximo histórico de treino (879)** — é extrapolação genuína,
  não um valor comum na faixa de treino (295 linhas, treino até 06/10/2024).
- O **resíduo previsto (2,2494) NÃO é um outlier do modelo**: cai no percentil **83,4** da distribuição
  histórica de resíduos do treino (quantil 0,85 do treino = 2,39 — o modelo está fazendo exatamente o que
  o quantil 0,85 pede, nem mais nem menos).
- A explosão nasce da **interação entre os dois**: o treino tem muitas linhas com âncora ≈ 0 (temporada
  baixa do ano anterior) e resíduo grande (o log-salto para a epidemia seguinte) — os 8 maiores resíduos do
  treino são todos de linhas com âncora 0-12. O modelo aprende "multiplicar por ~9-10× é comum quando a
  epidemia decola". Em 2025-03-23, a âncora **já é um valor de pico** (1.109, maior que qualquer âncora
  vista em treino) — aplicar o mesmo fator multiplicativo aprendido em cima de uma âncora já alta explode
  o valor absoluto. Essa combinação (âncora extrema **e** resíduo alto simultâneos) está ausente do treino.
- **Isso é exatamente o risco que a seção 6 da pré-declaração já nomeava** ("risco herdado da âncora: se
  2026-2027 for menor que 2025-2026, o V2, V3 e V6 tendem a superestimar") — só que aqui a superestimação
  também ocorre **dentro** do período de avaliação, não só na temporada confirmatória futura, porque a
  formulação multiplicativa é sensível à magnitude da âncora, não só ao sinal.

**Conclusão:** formulação residual-sobre-âncora em log, com HistGB quantil 0,85 e âncora como *feature*
extrapolada, produz explosões multiplicativas quando a âncora do teste excede o alcance do treino. É
propriedade da formulação declarada — **não bug**.

---

## 2. V5_linear_log, h=8, 2024-04-21

**Reprodução:** previsão = **27.257,7** — bate a trava (esperado ~27.258). `QuantileRegressor(alpha=0)`
em 20 colunas (log1p em `casos*` e no grupo vetor), padronização ajustada só no treino (298 linhas).

**O mecanismo, não é bug:**

- Os **coeficientes maiores, em módulo, são todos das colunas de `casos`** (na escala padronizada):
  `casos_mm4` +12,07 · `casos_lag2` −3,45 · `casos` −2,43 · `casos_lag1` −2,78 · `casos_lag3` −2,91.
  Nenhum z-score individual da linha de teste é extremo (entre 1,3 e 2,7 desvios-padrão) — não é
  extrapolação de uma única variável.
- `casos`, `casos_lag1`...`casos_lag4` e `casos_mm4` são **quase colineares** (a mesma série, defasada e
  suavizada). Com `alpha=0` (regressão **sem nenhuma penalização**, exigência explícita da pré-declaração:
  "regressão quantílica linear, sem penalização"), o sistema linear fica mal-condicionado: os coeficientes
  ficam enormes e de sinais opostos, quase se cancelando no treino, mas amplificando qualquer pequeno
  desvio entre a combinação linear do teste e a do treino — clássica instabilidade numérica de OLS/quantil
  sem regularização sobre atributos colineares.
- Somando as contribuições (`z × coef`): `casos_mm4` sozinho contribui **+27,4** (em log1p!), parcialmente
  cancelado por `casos_lag2/lag1/casos` (−6,9/−6,3/−6,5). A soma final (10,21 em log1p) já é grande o
  bastante para o `expm1` explodir.

**Conclusão:** a explosão é a assinatura clássica de **regressão linear sem regularização sobre atributos
colineares** — exatamente o que `alpha=0` predeterminado na pré-declaração produz. É comportamento real
da formulação (uma decisão de desenho, arriscada, mas não um bug de código) — **não bug**.

---

## 3. Auditoria da âncora do V2 (MAE 122,6 × 30,7 do B0)

O gap de MAE está em **h=12, ano-alvo 2026** (n=5, início de temporada). As 5 linhas:

| data_alvo | real | previsto V2 | previsto B0 | data_âncora (−52 sem) | casos na âncora |
|---|---|---|---|---|---|
| 2026-01-04 | 2 | 54,6 | 10,8 | 2025-01-05 | 26 |
| 2026-01-11 | 1 | 129,5 | 9,8 | 2025-01-12 | 32 |
| 2026-01-18 | 1 | 152,9 | 36,4 | 2025-01-19 | 37 |
| 2026-01-25 | 1 | 129,2 | 32,4 | 2025-01-26 | 47 |
| 2026-02-01 | 1 | 152,9 | 70,3 | 2025-02-02 | 75 |

**Datas conferem exatamente** (`data_ancora = data_alvo − 52 semanas`, mesma regra provada em
`provar_sinal_da_ancora`). O V2 superestima porque a mesma semana de 2025 já tinha 26-75 casos (início da
temporada mais cedo/maior de 2025), enquanto 2026 começou quase zerado — o modelo pesa a âncora como
atributo forte e "puxa" a previsão para cima. **É exatamente o "risco herdado da âncora" da seção 6**,
confirmado empiricamente, não um erro de cálculo.

---

## Nota metodológica (não corrige nada, só registra)

- O V3 e o V5 ilustram dois modos DIFERENTES de instabilidade sob quantil 0,85: extrapolação de uma
  formulação multiplicativa (V3) e colinearidade sem regularização (V5). Nenhum dos dois é peculiar do
  código desta bateria — são pathologias conhecidas da literatura de regressão (ver `alpha=0` +
  atributos colineares; ver formulação residuo-multiplicativo + extrapolação de âncora).
- Ambos os braços já são reprovados pela família F1 (pioram o B0 com p Holm < 0,05 em h=8 e h=12) —
  esta certificação não muda a leitura estatística já feita, só confirma que os números extremos citados
  são genuínos, não artefato de bug.
