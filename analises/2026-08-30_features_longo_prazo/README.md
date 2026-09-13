# Features de longo prazo para horizonte alto — 30/08/2026

> **A pergunta:** features de sazonalidade anual, anomalia/acúmulo climático ou ENSO reduzem o MAE
> do modelo de referência em h=8 e h=12, onde ele mais degrada?
> **A resposta:** nenhum grupo cumpre o critério pré-declarado (melhorar h=8 **e** h=12 juntos). Só
> o **ENSO** melhora isoladamente em h=8 (**-7,1%** de MAE); em h=12 o ganho é **+0,17%**, dentro do
> ruído. A degradação em horizonte longo permanece, pela regra 3 da pré-declaração, um limite do dado.
> Status: 🚫 descartado como upgrade da referência · ⚠️ sinal do ENSO em h=8 fica exploratório.
> Pré-declaração: sim, `PRE_DECLARACAO.md` (30/08/2026, autorizada pelo Vinicius).

## 1. Por que este teste foi feito

- A configuração de referência (HistGradientBoosting · quantil 0,80 · com vetor) capturava **98%**
  do pico em h=1 e só **62%** em h=12 (medido em 30/08/2026, mesmo dia).
- Causa já medida antes de rodar: a autocorrelação dos casos explica **91%** da variação em h=1 e
  cai a **0%** em h=12 — a "muleta" autorregressiva desaparece em horizonte longo.
- Hipótese pré-declarada: todas as features do projeto são de curto prazo (defasagem de 1 a 4
  semanas); não existe nada que capture ciclo anual ou acúmulo de estação.
- A pré-declaração prometeu testar **4 grupos de features novas**, cada um com justificativa medida
  (não intuição) e construção **só com passado** (`shift`, `rolling`, `expanding().mean().shift(1)`).
- Critério fixado antes de rodar: só entra na referência se melhorar **MAE em h=8 e h=12 na
  avaliação (2024+)**; melhora só na calibração é sobreajuste; sem melhora nenhuma é limitação
  declarada da dissertação — não licença para inventar features depois de ver o resultado.

## 2. Como foi medido

- **Alvo:** `casos` (cidade), deslocado `horizonte` semanas à frente (`construir_alvo_horizonte`).
- **Algoritmo:** `HistGradientBoostingRegressor`, parâmetros fixos da referência (perda quantílica,
  `quantile=0,80`, `max_iter=250`, `learning_rate=0,05`).
- **Variantes** (conjunto A = referência, 20 colunas, já com o vetor):
  - `A_referencia` — só a referência;
  - `A+B_lags_anuais` — `casos_lag52`, `casos_lag104`, `vetor_lag52`;
  - `A+C+D_clima_longo` — anomalia (temp/precip/umidade menos a norma histórica daquela semana do
    ano) + acúmulo de chuva/calor em 8 e 12 semanas;
  - `A+E_enso` — `nino34_anom`, `oni` (hoje descartados no config padrão);
  - `A+TUDO` — os quatro grupos juntos.
- **Horizontes:** 1, 4, 8 e 12 semanas · **passo** = 1 (reprevê toda semana) · **mínimo de treino**
  = 104 semanas (`CIDADE_REGRESSAO.minimo_semanas_treino`).
- **Corte calibração/avaliação:** calibração até 31/12/2023 escolhe; avaliação (2024+) julga —
  102 semanas de avaliação para A/C+D/E, **99** para B/TUDO (o lag de 104 semanas encurta a série
  utilizável).
- **Walk-forward:** treino = tudo antes do corte, teste = 1 semana, avança 1 corte por vez — **20
  execuções** (5 variantes × 4 horizontes), refeito um `HistGradientBoostingRegressor` a cada corte.

## 3. O que deu (MAE, período de avaliação — 2024+)

| h | A_referencia | A+B_lags_anuais | A+C+D_clima_longo | A+E_enso | A+TUDO |
|---|---|---|---|---|---|
| 1 | 101,3 | 95,6 | 97,3 | 98,0 | 95,2 |
| 4 | 168,4 | 143,2 | 165,0 | 167,0 | 152,1 |
| 8 | 184,0 | 189,7 | 184,2 | **171,1** | 208,4 |
| 12 | 179,7 | 190,1 | 190,0 | 179,3 | 190,8 |

- **ENSO é o único grupo que melhora h=8:** 184,0 → 171,1 MAE = **-7,06%** (bate com o "+7%" já
  citado em outros documentos). Em h=12 o ganho é **179,7 → 179,3 = -0,17%**, irrelevante.
- **Lags anuais (B) e clima longo (C+D) pioram h=8 e h=12** — ambos ficam acima da referência nos
  dois horizontes-alvo do teste.
- **A+TUDO é o pior em h=8 e h=12** entre todas as variantes — combinar os grupos não soma os
  ganhos, o ruído dos grupos fracos domina.
- Em h=1 e h=4 (fora do alvo do teste) várias variantes batem a referência, mas o critério
  pré-declarado nunca avaliou esses horizontes como decisão — são só contexto.
- Captura de pico em h=12 (avaliação) fica entre **0,61 e 0,64** em todas as variantes — nenhum
  grupo resolve o problema original de subestimação do pico em horizonte longo.

## 4. Conclusão

- **FATO:** nenhuma variante cumpre o critério pré-declarado de melhorar h=8 **e** h=12 juntos na
  avaliação — pela regra 3 da própria pré-declaração, isso classifica a degradação em horizonte
  longo como **limite do dado**, não falta de feature.
- **FATO:** o grupo ENSO melhora h=8 isoladamente (**-7,1%** de MAE) mas não h=12 — resultado
  parcial, não atinge o critério de entrada na referência tal como pré-declarado.
- **EXPLORATÓRIO:** o sinal do ENSO em h=8 nasceu do dado (medição pré-declarada, mas o critério de
  decisão não previa "aceitar por horizonte isolado") — não pode ser lido como "ENSO valida" sem
  revisitar a regra de decisão ou rodar um teste focado nele.
- **Nada aqui autoriza** promover ENSO, lags anuais, clima longo ou a combinação para a
  configuração de referência do projeto — o `config/experimentos/` correto continua sendo a
  referência sem essas features.

## 5. Ressalvas e o que ficou em aberto

- **Comparação não pareada por bootstrap/IC:** os deltas de MAE (ex.: -7,06% do ENSO) não têm
  intervalo de confiança nem teste estatístico — não se sabe se o ganho sobrevive a uma métrica de
  incerteza, muito menos a correção de múltiplas comparações (5 variantes × 4 horizontes = 20
  comparações, nenhuma corrigida).
- **Amostra pequena:** 99–102 semanas de avaliação por variante — poucas para separar sinal de
  ruído em uma métrica de cauda como MAE em h=8/h=12.
- **B e TUDO têm avaliação com 3 semanas a menos** (99 vs 102) por causa do `lag104` — a comparação
  entre essas duas e as demais três não é estritamente sobre a mesma janela.
- **ENSO nunca entrou no grid completo** de 30/08/2026 (`analises/2026-08-30_grid_completo/`) — o
  "+7% em h=8" é isolado deste script, não confirmado junto com as 30 configurações do grid.

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- **Este teste rodou com o corte de treino defeituoso.** Em `rodar()`, `validos` é ordenado por
  `data` (data de ORIGEM da linha) e o corte usa `validos.iloc[:indice_corte]` — mas o alvo `y_h` é
  a coluna `casos` deslocada `horizonte` semanas à frente (rótulo datado origem+horizonte). Isso é
  exatamente o padrão do vazamento: para cada corte, as últimas `horizonte-1` linhas do treino têm
  rótulo posterior à semana que está sendo prevista.
- **"Features de longo prazo" está na lista explícita dos testes NÃO REFEITOS** após a correção de
  13/09/2026 — não foi rodado de novo com o corte correto.
- **Direção provável da distorção:** o vazamento cresce com o horizonte (mais linhas de treino
  contaminadas quanto maior `h`). Na configuração de referência, a correção elevou o MAE em h=12 em
  **+52%** — logo os números de h=8 e h=12 desta tabela (para todas as 5 variantes, incluindo o
  -7,1% do ENSO) estão **provavelmente otimistas/subestimados**. O ranking relativo entre variantes
  pode não sobreviver — não dá para afirmar que ENSO continuaria melhor que a referência em h=8
  depois da correção.
- **Consequência prática:** a conclusão de "degradação em horizonte longo é limite do dado" (item 4)
  tende a se manter ou piorar após a correção — o vazamento infla a qualidade aparente, não o
  problema. Já o resultado do ENSO precisa ser refeito antes de qualquer uso.

## 7. Arquivos

- `PRE_DECLARACAO.md` — pré-declaração completa, escrita e autorizada em 30/08/2026 antes de rodar.
- `testar_features_longas.py` — script que gera os 4 grupos de features e roda o walk-forward das
  5 variantes × 4 horizontes.
- `saidas/features_log.txt` — log da execução (30/08/2026), com as tabelas de MAE e captura de pico
  impressas ao final.
- `saidas/features_longas_previsoes.csv` — previsão linha a linha (4.963 linhas: 5 variantes × 4
  horizontes × semanas de teste), com `real`, `pred`, `erro`, `periodo`.
- `saidas/features_longas_resumo.csv` — MAE, R², viés de pico e captura de pico agregados por
  variante × horizonte × período (40 linhas).
