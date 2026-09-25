# Revisão adversarial pré-rodada — SARIMA + LASSO + ensemble

> Escrita em 25/09/2026, revisão de `rodar_sarima.py`, `rodar_lasso.py` e `combinar_e_avaliar.py`
> contra `PRE_DECLARACAO.md`. **A bateria completa não rodou** — esta é uma revisão de código e de
> mecânica, com checagens provadas rodando trechos pequenos (não a bateria inteira).
>
> **Veredito: APROVADO PARA RODAR**, com dois achados não-bloqueantes (travas com furo de cobertura,
> não bugs que já causaram erro) e uma observação.

---

## 1. SARIMA (`rodar_sarima.py`)

- ✅ `trend='n'`, `seasonal_order=(0,1,0,52)`, `order=(2,0,0)` — batem a seção 2.
- ✅ `q085 = expm1(média + 1,0364 × erro-padrão)`, `q050 = expm1(média)` — `Z_DO_QUANTIL_085=1.0364`
  confere com `norm.ppf(0,85)`.
- ✅ **Contexto termina exatamente na origem.** Rodei `selecionar_contexto_ate_a_origem` direto contra
  `tabela_final.csv` em 6 pares (h=1 e h=12, 3 origens cada): em todos, `contexto['data'].max() == origem`.
  Série semanal sem buracos (`diff` sempre 7 dias) — não há risco de "vizinho mais próximo" silencioso.
- ✅ Fallback de não-convergência usa a régua sazonal e é contado (`usou_regua_de_fallback`).
- 🟡 **Achado 1 (não-bloqueante) — Trava 2 é tautológica.** O campo `ultima_data_ajuste` gravado em
  `montar_previsao_de_uma_origem` é `origem` **literal**, não `contexto['data'].max()`. A trava 2 do
  combinador (`ultima_data_ajuste == data_alvo - h`) compara o campo com a fórmula que o gerou —
  sempre verdadeiro por construção, nunca pega uma regressão futura em
  `selecionar_contexto_ate_a_origem`. Hoje não esconde erro (confirmei acima que o corte está certo),
  mas a trava não protege nada. Sugestão: gravar `contexto['data'].max()` em vez de `origem`.

## 2. LASSO (`rodar_lasso.py`)

- ✅ **Treino sem futuro.** Reusa `corte_temporal.selecionar_treino_ja_respondido` (já certificado em
  13/09), não reimplementa — `data + h ≤ origem` garantido.
- ✅ **StandardScaler só no treino.** Em `RegressaoQuantilicaLinearLog.fit`, `fit_transform` só no
  treino; `predict` usa `transform`. A subclasse com alpha não toca em `fit`/`predict`.
- ✅ **Alpha só na calibração 2022–2023, depois fixo.** `selecionar_alpha_e_previsoes` filtra
  `2022-01-01 ≤ data_alvo < 2024-01-01` antes de escolher; código correto (ainda não executado, é
  só da bateria completa).
- ✅ **Equivalência com V5 (alpha=0) re-rodada por mim agora**: 284 origens, 2,6s, últimas 20 origens
  de h=12 batem com `rtol=1e-8` contra `V5_linear_log`. Passou.
  - 🟡 Ressalva menor: só as últimas 20 de 284 são comparadas numericamente (custo). Como o `fit`/
    `predict` são literalmente herdados sem alteração, é evidência forte, não prova das 284 — aceitável.
- ✅ **Colunas de `lasso` × `lasso_M0` (20 × 14) e grade de datas.** Rodei os dois braços de verdade
  (h=1 e h=12): `lasso_M0` tem MAIS linhas válidas na avaliação (109 × 102), porque tirar o vetor
  remove menos linhas por NaN. Verifiquei que as 102 datas de `lasso` são um subconjunto exato das
  109 de `lasso_M0` — o merge da família J3 fecha em 102 pares, não menos. Também confirmei que a
  grade de `lasso` bate 100% com as 102 datas do B0 (mesmo conjunto exato, não só a mesma contagem).
- 🟡 **Achado 2 (não-bloqueante) — Trava 1 não cobre `lasso_M0`.** `conferir_trava_1_pareamento` só
  audita os braços que entram na tabela larga do ensemble (`b0, c2_casos, sarima_log, lasso, regua,
  ens_media, ens_pesos`); `lasso_M0` nunca é checado por N=102, embora a pré-declaração diga "todos
  os braços". Hoje fecha certo (comprovei acima), mas nada no código pegaria uma futura mudança que
  desalinhasse `lasso_M0`. Sugestão: acrescentar checagem explícita de N para `lasso_M0` (ou para a
  família J3 diretamente) antes de ler `familia_j3`.

## 3. Ensemble (`combinar_e_avaliar.py`)

- ✅ **Sem vazamento nos pesos.** `montar_previsoes_do_ens_pesos` usa só `data_alvo <= origem` do
  mesmo horizonte para escolher pesos — confirmado lendo o código, a filtragem é por linha e por `h`.
- ✅ **Grade de 1.001 combinações**, rodei e confirmei: 1.001 tuplas, todas não-negativas, todas somam
  1,0, sem duplicata.
- ✅ **Mínimo de 26 pares** e **empate por maior peso na régua** implementados como na seção 2.
- ✅ **Régua é `data_alvo - 52 semanas`, calculada direto da série** (não lida de nenhum braço de
  modelo) — o erro de sessão anterior não se repete, nem em `rodar_sarima.py` nem aqui.
- ✅ **Famílias J1 (12), J2 (16), J3 (4)** — contagem de comparações bate a seção 4. Toda tabela traz
  `mae_braco`, `mae_comparador` e `reducao_percentual` (direção).
- ✅ **Holm reimplementado e validado por mim** contra `statsmodels.stats.multitest(method='holm')`
  num vetor de 5 p-valores sintético — bate posição a posição.
- ✅ **Travas rodam antes das famílias** e a função retorna cedo (`if not valido: return`) sem gravar
  nem imprimir resultado.
- ✅ Padrão de código: sem `lambda`, sem `np.where` aninhado, sem comprehension com I/O, dataclasses
  para configuração, docstrings de negócio — varredura por grep não achou violação nos 3 scripts.

## 4. Observação (não é bug de código)

- No `--smoke` do combinador, `sarima_log` produz previsões bem instáveis em semanas de poucos casos
  reais (jan–fev/2026: real 1–2, previsto 32–272). Matemática confere com a seção 2 (AR(2) sem
  constante em log, quantil por z-score) — parece comportamento do modelo em contagem baixa, não erro
  de código. Vale olhar quando a bateria completa rodar, especialmente na perda quantílica.

---

## O que eu rodei para provar (custo real: ~15s de CPU)

- `selecionar_contexto_ate_a_origem` em 6 pares reais (venv SARIMA).
- `rodar_lasso.py --provar-equivalencia` (2,6s, 284 origens, passou).
- Walk-forward completo de `lasso` e `lasso_M0` em h=1 e h=12 (`python3` do sistema), comparando
  conjuntos de datas.
- `combinar_e_avaliar.py --smoke` (venv SARIMA).
- Contagem/soma/duplicata da grade de pesos e Holm contra `statsmodels`, isolados.

Nenhum script foi alterado. Nenhum `git` foi usado.
