# Certificação adversarial — busca de hiperparâmetros

Certificador independente, 26/09/2026, madrugada. **Refeita do zero** — a versão anterior
(25/09/2026 23h41) certificou a rodada com o processo ainda em execução (28/120 configs, nenhuma
saída final existia) e **não vale**. Nesta rodada os processos já tinham terminado e todas as
saídas existem em disco. Todo item abaixo foi reproduzido por código próprio, não por reler o
`rodar.py`.

## ✅ 1. Sorteio (semente `20260925`) — reproduzido do zero

Reimplementei `sortear_configuracoes_histgb` + `sortear_configuracoes_lightgbm` num script à
parte, com `np.random.default_rng(20260925)` e a mesma ordem (HistGB primeiro, LightGBM depois).
Comparando as 120 linhas × 14 colunas numéricas + `config_id` + `familia` contra
`saidas/configuracoes_sorteadas.csv`: **0 divergências** (`np.isclose` com `equal_nan=True` em
cada coluna, incluindo `max_depth`, que tem `None`/`NaN`). `configuracoes_sorteadas.csv` está correto.

## ✅ 2. Vencedoras e nota — reproduzidas do zero

- Recalculei a nota (`média do MAE em h=4 e h=12, 2022-01-01 a 2025-12-31`) direto de
  `saidas/previsoes_vencedoras_e_controles.csv` para `HB_best` e `LGB_best`: **161,738** e
  **160,954**, batendo exatamente com `vencedoras.json` (`161,73799...` e `160,95368...`).
  `max(data_alvo)` usada = **2025-12-28** em ambos — 2026 não entra na nota.
- Recalculei a nota das 120 configs a partir de `saidas/notas_2022_2025.csv`, agrupando por
  família (prefixo do `config_id`): a menor nota do HistGB é `histgb_018` (161,738) e do
  LightGBM é `lightgbm_040` (160,954) — **idênticas** às gravadas em `vencedoras.json` como
  `HB_best`/`LGB_best`. Critério de menor nota confirmado.

## ✅ 3. Trava do cenário adotado — reproduzida do zero, VÁLIDA

Recalculei o MAE de `cenario_adotado` na janela `[2024-01-01, 2026-02-01]` (**inclusive nas duas
pontas** — é essa a leitura que bate) a partir de `previsoes_vencedoras_e_controles.csv`:

| h | meu recálculo | emenda 01h20 | alvo pré-declarado | tolerância |
|---|---|---|---|---|
| 1 | 97,38 | 97,38 | 97,4 | ✅ dentro de 0,2 |
| 4 | 211,31 | 211,31 | (sem alvo, só registro) | — |
| 8 | 270,55 | 270,55 | (sem alvo, só registro) | — |
| 12 | 279,96 | 279,96 | 280,0 | ✅ dentro de 0,2 |

Bate exatamente com os quatro números da emenda de 26/09 01h20. **Trava válida**, confirmado
por reimplementação independente. ⚠️ `saidas/trava_cenario_adotado.json` ainda registra
`"valido": false` com MAE 48,6/133,3 (h=1/h=12) — é o bug do limite inferior da janela que a
própria emenda documenta e que **o script não corrigiu** (só o registro manual corrigiu). O
arquivo `.json` em disco está desatualizado por desenho; a validade real é a da tabela acima.

## ✅ 4. Retreino do zero, HB_best, h=12, 5 origens de 2026

Em vez do walk-forward completo (custoso), treinei só as 5 primeiras origens de 2026
(alvos 04/01, 11/01, 18/01, 25/01 e 01/02/2026), chamando o harness da bateria noturna
(`montar_features_do_braco`, mesmas 20 colunas) e `corte_temporal.selecionar_treino_ja_respondido`
igual ao `rodar_walk_forward`, com os hiperparâmetros de `histgb_018` e `random_state=42`.

Resultado: as 5 previsões batem com `previsoes_vencedoras_e_controles.csv` com diferença máxima
de **1,8×10⁻¹⁵** (epsilon de ponto flutuante — ou seja, exatamente iguais). Confirma que o
retreino é determinístico e que as 20 colunas do modelo batem com as declaradas em `vencedoras.json`
(`MONO.colunas_do_modelo`).

## ✅ 5. `julgamento_2026.csv` e `holm_2026.csv` — reproduzidos do zero

Recalculei diretamente de `previsoes_vencedoras_e_controles.csv`, recorte 01/01 a 19/04/2026
(n=16 por entidade/h): MAE, alarmes falsos (limiar 100), maior previsto e maior real — **bate
exatamente** com `julgamento_2026.csv` para as 6 entidades × 4 horizontes.

Recalculei Wilcoxon pareado (braço × `cenario_adotado`, por `data_alvo`) + Holm sobre as
**6 comparações que existem** (`HB_best`, `LGB_best`, `LGB_linear` × h=4/h=12 — `MONO` é
impossível, então são 6 e não 8, ver item 6) — bate exatamente com `holm_2026.csv`
(MAE, redução %, `n_pareado=16`, `p_bruto` e `p_holm` idênticos). **Nenhum braço é significativo
a 5% após Holm** (menor `p_holm` = 0,1732, `HB_best` h=4).

## ✅ 6. `LGB_linear` e `MONO` — confirmado empiricamente, não só por log

- **`MONO`: impossível**, confirmado rodando eu mesmo um `LGBMRegressor(objective="quantile",
  monotone_constraints=[...])` isolado — LightGBM 4.6.0 recusa com
  `Cannot use monotone_constraints in quantile objective`. Bate com `vencedoras.json`
  (`"impossivel": true`) e com o log.
- **`LGB_linear`: rodou normalmente** — testei `linear_tree=True` com `objective="quantile"`
  isolado e não deu erro, confirmando que a hipótese pré-declarada ("LightGBM não aceitar
  linear_tree com perda quantílica") **não se confirmou**: o braço rodou. Só que rodou mal — a
  vencedora (`lambda=0,1`) tem nota **297,25**, quase o dobro da HB_best/LGB_best (~161). O
  `linear_tree` piorou o ajuste em 2022-2025, não ajudou.

## Números principais (2026, recorte 01/01–19/04, n=16 por célula)

**Hiperparâmetros das vencedoras:**
- `HB_best` (histgb_018): `learning_rate=0,1972 · max_iter=239 · max_leaf_nodes=55 ·
  min_samples_leaf=15 · l2=0,0 · max_features=0,514 · max_depth=8`
- `LGB_best` (lightgbm_040): `learning_rate=0,0224 · n_estimators=177 · num_leaves=49 ·
  min_child_samples=10 · reg_lambda=0,0033 · colsample_bytree=0,917 · subsample=0,808 ·
  extra_trees=True`
- `LGB_linear`: igual à `LGB_best` + `linear_tree=True, linear_lambda=0,1`

**MAE em 2026, h=4 / h=12:**

| Entidade | h=4 | h=12 |
|---|---|---|
| `cenario_adotado` (controle) | 223,76 | 482,88 |
| `HistGB_folha20` (controle) | 600,98 | 578,97 |
| `regua_sazonal` (controle) | 902,88 | 902,88 |
| `HB_best` | 350,06 | 439,67 |
| `LGB_best` | 233,99 | 540,90 |
| `LGB_linear` | 94,20 | 201,63 |

`LGB_linear` reduz o MAE do adotado em 58% em h=12 (p Holm 0,193 — não significativo, n=16,
poder baixo) e 58% em h=4 (p Holm 0,35). Nenhum braço bate o critério de decisão da
seção 6 da pré-declaração (MAE menor **e** menos alarmes falsos **e** p Holm < 0,05):
`LGB_linear` tem MAE bem menor mas **16 de 16 alarmes falsos** em h=8 e h=12 (limiar 100),
contra 9-11 do adotado — supersensibiliza o alarme. **Nada troca a referência.**

## Nenhuma correção aplicada

Todos os itens reproduziram o protocolo pré-declarado (com as emendas de 25/09 23h50 e 26/09
01h20) exatamente. O único ponto de atenção é o `trava_cenario_adotado.json` desatualizado em
disco (item 3), que é um registro do bug já documentado nas emendas, não um erro novo.
