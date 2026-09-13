# Auditoria da mecânica dos resultados — 13/09/2026

> **Pergunta desta pasta:** o que o CÓDIGO faz é o que o pesquisador tem na cabeça? Reconstrução da
> mecânica de cada resultado a partir do código (não dos READMEs), com verificação adversarial.
> Nada foi rodado de novo, exceto re-agregações baratas sobre CSVs já existentes.
> Relatórios brutos dos agentes: [relatorios_agentes.md](relatorios_agentes.md).

**Status:** ✅ leitura concluída · ⏳ nenhuma decisão tomada · nada foi alterado no código ou nos dados.

---

## 1. Como foi feito

- **10 agentes Sonnet em paralelo**: 7 leitores (dados → tabela · motor/grid · métricas/testes · calibração/pico ·
  surto/McNemar · equivalência/janela · espacial) e 3 verificadores adversariais (seleção de clima · vazamento
  em features/surto · pareamento M0×M1).
- **Orquestrador confirmou com os próprios olhos** os cinco achados de maior peso (§3.1 a §3.5), lendo as linhas citadas.
- ~1,19 M tokens de subagente, 165 chamadas de ferramenta, 5,6 minutos.

---

## 2. O que o código faz — as afirmações que importam

Tudo abaixo é **LIDO_NO_CODIGO**, com arquivo:linha.

### Dados → `tabela_final`
- Semana = domingo a sábado, regra da semana epidemiológica (`dominio/montagem_tabela.py:48-78`).
- **Densidade** `aedes_aegypti_por_armadilha` = **fêmeas** ÷ armadilhas inspecionadas; a **contagem** `aedes_aegypti` = fêmeas + machos (`montagem_tabela.py:126,136-137,167-169`). Numeradores diferentes.
- Semana sem inspeção = NaN em todas as colunas do vetor, via `reindex` na grade contínua (`montagem_tabela.py:142-147`).
- `casos_confirmados` vem do SINAN agrupado por SE e casado **por SE, não por data** (`montagem_tabela.py:206-214`); dentro do intervalo coberto, semana sem registro = 0; fora = NaN.
- **Corte de maturidade fica FORA da tabela**: é decisão de experimento, 12 semanas (ou 0), ancorado na **última semana com caso**, não no fim da tabela (`dominio/surto.py:38-49`).
- ENSO mensal replicado em todas as semanas do mês (`montagem_tabela.py:240-246`).

### Motor de previsão de casos (config de referência e grid)
- Origem = semana *t*; alvo `y_h` = casos em *t+h* (`dominio/features.py:151`). Lags 1–4 e média móvel de 4 (que **inclui** a semana *t*) para casos, vetor e 5 variáveis de clima (`features.py:19-38,96-109`).
- **A versão crua (lag 0) de casos, vetor e clima também é feature** — `colunas_ignorar` não a remove (`config/experimentos/cidade_regressao.py:143-147`). O modelo vê "histórico + último valor conhecido".
- `alvo_sin/alvo_cos` = calendário da semana **alvo** (legítimo, é só data) (`features.py:152-155`).
- Walk-forward **expansível**, 1 previsão por corte, mínimo 104 semanas de treino, passo em linhas válidas pós-`dropna` (`motor/walk_forward_regressao.py:63-82`).
- Seleção das 6 colunas de clima: **uma vez só**, com os primeiros 60% das linhas válidas (mar/2018 → nov/2022), usando `y_h` como resposta e LightGBM (`dominio/selecao_features.py:100-118`; `rodar_grid.py:88-96`).
- Perda quantílica 0,80 ⇒ a previsão é o **quantil 0,80** da distribuição condicional, não a média (`cidade_referencia.py:55-66`).
- M0 e M1 fazem **`dropna` separados** ⇒ semanas de teste diferentes (`rodar_grid.py:133-137`; `walk_forward_regressao.py:65-66`). Só `walk_forward_pareado.py` e os testes de 30/08 pareiam por `data_alvo`.

### Métricas
- **"Captura do pico" = média(pred) ÷ média(real) nas semanas com real > 100** (`2026-08-30_features_longo_prazo/testar_features_longas.py:218`; `…_alvo_e_features_infodengue/testar_alvo_e_features.py:145`). É uma **razão de viés agregado**, não uma taxa de detecção de picos.
- `vies_pico` = média(pred − real) nas mesmas semanas.
- Diebold-Mariano: perda absoluta, correção HLN, **unilateral** ("M1 erra menos") (`avaliacao/diebold_mariano.py:94-97`).
- Holm: a família é decidida pelo script chamador — 6, 8 ou 12 conforme a rodada (`avaliacao/correcao_multipla.py:22`). No teste h=12, o Holm roda sobre a **mediana** do p entre 5 sementes (`testar_h12_focado.py:241-243`).

### Alarme de surto
- Surto = `casos_h` ≥ percentil calculado **só com o treino de cada passo** (expansível, sem olhar o futuro) (`motor/walk_forward.py:96-100`). ✅ Sem vazamento aqui.
- Classificador LightGBM `class_weight="balanced"`, limiar fixo 0,5 (`walk_forward.py:131`).
- McNemar sobre pares discordantes (clima acerta e clima+vetor erra, ou o oposto) na mesma semana pós-merge (`avaliacao/mcnemar.py:59-84`).
- Confirmados: Holm aplicado **depois**, por script à parte; notificados: Holm **dentro** do pipeline (`pipeline.py:203-235` vs `~663-668`).

### Equivalência clima × vetor (Rodada 2, 29/08)
- Braço **clima** = 22 colunas de clima **contemporâneas, sem lag**; braço **vetor** = vetor + lag1–4 + mm4 (`rodada_2_teste_a_serie_longa.py:190-232,267-281`).
- Versão `com_ar` acrescenta `casos_lag1..4 + casos_mm4` aos dois lados — **sem** casos lag 0.
- Margem TOST = 5/10/15% do **MAE do SO_CLIMA** (`rodada_2:102,645-646`).
- Pareamento por interseção de datas (n = 587/584/580/576).

### Camada espacial
- Zonas = k-means sobre a posição média de cada armadilha (só geografia), k = 8 e 16, fixas no tempo (`rodada_3_ranking_zonas.py:121-129`).
- Alvo = densidade suavizada (mm4) da zona em *t+h*; ranking = Spearman transversal por semana, mediana (`rodada_3:252-267,320-323`).
- Persistência = valor de hoje repetido; climatologia = média histórica ±1 semana (`rodada_3:270-291,352`).

---

## 3. Achados que mudam a leitura dos resultados

### 3.1 ⚠️ Vazamento de rótulo pelo horizonte no walk-forward (FATO no código; efeito NÃO medido)

- **O que o código faz:** para prever a semana *t+h* a partir da origem *t*, o treino usa **todas as linhas anteriores por posição** (`treino = dados_validos.iloc[:indice_corte]`), e cada linha de treino *j* carrega o rótulo `y_h` = casos em *j+h*. As linhas *j* ∈ [*t−h+1*, *t−1*] têm rótulos em datas **depois de *t*** — que na prática ainda não existiam na origem.
  - `motor/walk_forward_regressao.py:70-72` · `motor/walk_forward.py:96-98` · `motor/walk_forward_pareado.py:70-72` · `analises/2026-08-30_grid_completo/rodar_grid.py:141-143`.
- **Tamanho:** h=1 → 0 linhas; h=4 → 3; h=8 → 7; **h=12 → 11 linhas** de treino com rótulo futuro, a cada corte.
- **Exemplo real:** origem 03/03/2024, h=12, alvo 26/05/2024. O treino inclui a linha de 18/02/2024 cujo rótulo é 12/05/2024 = **1.510 casos** (o pico). O modelo aprende "features de fevereiro → 1.500" e prevê a partir de features de março. Em tempo real, em 03/03 ninguém sabia o valor de 12/05.
- **Consequência (hipótese a medir):** as métricas de h ≥ 4 são otimistas em relação a uma operação real, e o efeito é maior exatamente onde a "captura do pico" é medida. Pode explicar parte do "vetor ganha em h=12": qualquer feature autocorrelacionada se beneficia.
- **Correção padrão:** treinar só com linhas *j* ≤ *t−h* (origem do teste posterior a todos os rótulos de treino).
- **Custo de medir:** re-rodar a config de referência (HGB quantil 0,80, M0 e M1, h=1/4/8/12, passo=1) com o corte corrigido: **~10–15 min de CPU**. Exige pré-declaração.

### 3.2 ⚠️ O núcleo proposto (equivalência a ±15%) tem três problemas de desenho

- **(a) Margem ≠ pré-declaração.** `PRE_DECLARACAO.md:123` fixa a margem em % do **MAE da persistência**, "exatamente como em 16/08". O código (de 16/08 **e** de 29/08) usa % do **MAE do clima**. O texto errou sobre 16/08, mas a pré-declaração escrita é a que vale.
  - Notificados, h=1 puro: margem usada **27,5** × pré-declarada **6,8**; com_ar h=1: **10,9** × **6,8**; puro h=4: 28,5 × 21,6; com_ar h=8: 25,7 × 38,0.
  - Pela leitura dos ICs, com a base pré-declarada fechariam **~1 de 8** (com_ar h=8), não 4 de 8. **Estimativa; recomputar** (barato: as previsões pareadas estão salvas).
- **(b) O alvo é o errado.** Os "4 de 8" são da versão **notificados** (n≈587). Na versão **confirmados** — o alvo decidido em 30/08 — fecham **0 de 8** a ±15% (`saidas/rodada_2_confirmados_resultados_equivalencia.csv`). O núcleo e a decisão de alvo são inconsistentes.
- **(c) Assimetria de memória.** Clima sem lag algum vs vetor com 4 lags + média móvel. Em h=8 e h=12 puro, o vetor sozinho é **pior** que o clima sozinho (+14 e +25 de MAE), com IC superior em +46 e +73 — longe de equivalência.
- **(d) A persistência joga com uma carta a mais.** `construir_previsao_persistencia` (`rodada_2:365`) repete `casos` da **semana atual**; o bloco `com_ar` dá aos modelos só `casos_lag1..4` e `casos_mm4`, **sem o lag 0**. Em h=1 a persistência faz MAE **45,1** contra 72,6 e 74,4 dos modelos com AR — mas com informação que eles não receberam. A comparação com a persistência nesta rodada é **desfavorável aos modelos por desenho**; não conclua "o modelo perde para copiar a semana passada". (Na pipeline principal e no grid o `casos` cru **entra** como feature — lá a comparação é justa.)
- **Leitura honesta hoje:** "vetor sozinho ≈ clima sozinho em horizonte curto, ambos muito piores que persistência; em horizonte longo o vetor sozinho é pior". Isso é diferente de "a armadilha empata com o clima".

### 3.3 ⚠️ "Captura do pico" não mede alarme

- É `média(pred)/média(real)` nas semanas com > 100 casos. **92% em h=4** significa: o patamar médio previsto nas semanas de pico é 92% do real médio. Não diz quantos picos foram sinalizados nem quando.
- A perda quantílica 0,80 **eleva a previsão por construção** — logo eleva essa razão mecanicamente. O "remédio" e a métrica que o julga apontam na mesma direção. O ganho é real como redução de viés, mas a frase "serve para alarme" precisa de outra métrica (sensibilidade/antecedência por episódio).

### 3.4 ⚠️ M0 × M1 no `grid_resumo` não é pareado — e em h=1 inverte o sinal (FATO, medido)

- M1 perde 7 origens de avaliação (109 → 102): 28/04, 05/05, 12/05/2024 (enchente, vetor NaN) + 4 de propagação dos lags. Alvos excluídos em h=4: 26/05 a 07/07/2024, reais 520/199/263/277/194/89/22.
- Restringindo M0 às mesmas `data_alvo` de M1:

| h | MAE M0 próprio | MAE M0 interseção | MAE M1 | leitura |
|---|---|---|---|---|
| 1 | 116,1 | **94,6** (−18,5%) | 101,3 | não pareado: M1 "vence" 13%; pareado: **M0 vence 7%** |
| 4 | 188,6 | 187,7 | 168,4 | M1 vence nos dois |
| 8 | 175,5 | 182,1 | 184,0 | empate |
| 12 | 202,3 | **214,3** (+5,9%) | 179,7 | vantagem do vetor **cresce** pareado |

- O `grid_vetor_pareado.csv` e o teste h=12 já pareavam (✅ o "0/15 em h=1" e o "15/15 em h=12" estão certos). O problema é qualquer leitura feita a partir do `grid_resumo.csv` e da pipeline de produção (`rodar_regressao_selecao_clima`).
- Saída: HistGradientBoosting aceita NaN nativamente; o `dropna` do vetor é escolha. Sem ele, M0 e M1 ficam pareados por construção.

### 3.5 ⚠️ Números-manchete sem script salvo

- `rodar_grid.py` só grava previsões. **Nenhum arquivo do repositório gera** `grid_resumo.csv`, `grid_ranking_completo.csv` nem `grid_vetor_pareado.csv` — o ranking que escolheu a configuração de referência não é reproduzível a partir do código versionado (`LIMITE_PICO` e `FIM_DA_CALIBRACAO` definidos e nunca usados).
- Idem para "captura 78% → 92%", "65% → 83% / 46% → 62%", a decomposição +15,1/−9,9/+13,3 pp e "autocorrelação 91% → 0%": não estão em nenhum dos scripts das pastas de 30/08.
- V3 reproduziu o MAE de avaliação do `grid_resumo` assumindo `periodo = avaliação se data_alvo > 31/12/2023` — bateu ao centavo, então a convenção é essa. Mas é inferência.

### 3.6 Seleção de clima: sem vazamento hoje, mas instável e sem trava

- O corte dos 60% cai em nov/2022 — antes de 2024, ✅ não contamina a avaliação. Mas é **fração de linhas, não data**: quando a série crescer, avança sem aviso.
- O período de calibração (critério do ranking do grid) **se sobrepõe** à janela de seleção. Efeito comum a todas as 30 configurações → ranking pouco afetado; mas não é limpo.
- **Instável:** cortando a série em 2023 antes dos 60%, **4 das 6 colunas mudam**. "Estas 6 variáveis de clima são as que importam" não é um fato defensável.

---

## 4. Escolhas de implementação que você precisa saber (não são erros)

- Previsão quantílica = **patamar** superado em 20% das vezes. Comparar seu R²/MAE com o modelo de média não é entre iguais.
- Calibração escolheu **alpha 0,85** (menor |viés no pico|, guarda MAE ≤ +20%, que 3 dos 4 alphas passavam); o grid escolheu **0,80** (menor MAE de calibração). A referência usa 0,80. Dois critérios, dois vencedores.
- Vetor no modelo calibrado: M1 venceu em 6/8 sem sobreviver a Holm = **desfecho 2** pré-declarado ("indício"), não o desfecho 3 ("não vence") que a pré-declaração chamava de mais provável.
- Diebold-Mariano só testa "M1 melhor"; nunca sinaliza "M1 pior".
- `casos_mm4` inclui a semana da origem.
- Diagnóstico do viés de pico: a refutação do "teto de extrapolação" repousa no Teste A (5 de 32 picos acima do teto); o Teste B (log1p) piorou o viés e não discrimina hipóteses.
- Corte de maturidade ancorado na última semana **com** caso: se a fonte atrasar, o corte anda para trás.
- Docstring de `config/experimentos/cidade_surto_notificados.py:8-10,37-41` ainda diz "só o alvo muda" — premissa refutada em 30/08.
- Espacial: zona entra no LightGBM como **código ordinal** (0..k−1); persistência é ingênua por desenho; Spearman semanal sem ajuste de autocorrelação (descritivo, não teste).

---

## 5. O que está sólido

- Base certificada e `tabela_final`: todas as âncoras batem ao número.
- Lags só olham para trás; `alvo_sin/cos` é só calendário; não há `casos_est`/nowcasting em nenhum código.
- Limiar de surto é expansível e local ao treino: ✅ sem vazamento.
- Os testes de 30/08 que importam (h=12 focado, vetor calibrado, grid pareado) pareiam por `data_alvo`.
- Rodada 4 (treinar desde 2012 vence) avalia os 3 regimes nas **mesmas** semanas.
- Zonas k-means usam só geografia — não vazam o alvo.

---

## 6. Perguntas para o pesquisador (é isso que estava na sua cabeça?)

1. Você esperava que o modelo, ao prever *t+12*, tivesse sido treinado com rótulos de até *t+11*?
2. "Captura do pico" para você era **taxa de picos detectados** ou **razão de níveis**?
3. O núcleo da tese deveria ser medido em **confirmados** (alvo decidido) ou em **notificados** (onde os 4/8 aparecem)?
4. A margem do TOST deveria ser % do MAE do clima (código) ou da persistência (pré-declaração)?
5. Esperava clima **sem lag** contra vetor **com 4 lags** na equivalência?
6. Sabia que casos/vetor/clima da **própria semana de origem** entram como feature, além dos lags?
7. Esperava que M0 e M1 fossem avaliados em semanas **diferentes** no grid e na pipeline?
8. Onde estão os scripts que geraram o ranking do grid, a captura do pico e a decomposição do ganho?

---

## 7. Próximos passos propostos (nenhum executado; todos exigem pré-declaração)

- ⏳ **A. Medir o vazamento pelo horizonte** — re-rodar a referência com `treino = linhas j ≤ t−h`, M0/M1 × 4 horizontes, passo=1 (~10–15 min CPU). Hipótese pré-declarada: MAE/R²/captura pioram em h ≥ 4; se a captura em h=4 cair abaixo de X, a frase "confiável até 1 mês" precisa ser refeita.
- ⏳ **B. Recomputar o TOST com a base pré-declarada** (persistência), nas duas versões e nos dois alvos, a partir das previsões pareadas já salvas (< 1 min). Emenda datada na pasta da Rodada 2.
- ⏳ **C. Salvar os scripts faltantes**: resumo do grid (a partir de `grid_previsoes_parciais.csv`), captura do pico, decomposição do ganho. Sem isso a configuração de referência não é auditável.
- ⏳ **D. Decidir o alvo do núcleo** (confirmados × notificados) antes de qualquer texto.
- ⏳ **E. Pareamento por construção**: remover o `dropna` das colunas de vetor para HGB/LightGBM (aceitam NaN), ou avaliar sempre na interseção.
- ⏳ **F. Métrica de alarme de verdade** para acompanhar a captura: sensibilidade e antecedência por episódio de pico.
