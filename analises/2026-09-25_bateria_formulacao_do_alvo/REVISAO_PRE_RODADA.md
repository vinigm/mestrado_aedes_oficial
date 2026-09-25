# Revisão adversarial pré-rodada — 25/09/2026

Revisor: agente independente. Alvo: `rodar.py` contra `PRE_DECLARACAO.md`, `harness.py` (23/09) e
`motor/corte_temporal.py`. Método: leitura linha a linha + reexecução de código pequeno (smoke test,
`--provar-ancora`, `--provar-equivalencia`, 1 célula completa de B0 h=12, e um script isolado
comparando a coluna `ancora` contra busca por data). Nada em `rodar.py` foi alterado.

## Veredito

**APROVADO PARA RODAR A BATERIA.** Nenhum problema bloqueante encontrado nas 9 checagens pedidas.

## As 9 checagens

1. **Sinal da âncora / vazamento** — CONFIRMADO CORRETO, por reexecução independente (não só pela
   função `provar_sinal_da_ancora` do próprio script, que é fraca — ver achado não bloqueante).
   Validei que `tabela["data"]` é uma grade semanal 100% contínua (725 linhas, `diff()` = 7 dias
   sempre), então o `shift(52-h)` posicional em `tabela_do_horizonte` (linha 463, antes do dropna)
   equivale exatamente a recuar `52-h` semanas em data. Testei 10 linhas amostradas comparando o valor
   da coluna `ancora` contra uma busca por data independente: bateu 10/10. Crescimento do vetor
   (`shift(1)`, `shift(4)`) usa a mesma grade contínua — correto. `StandardScaler` do V5 é instanciado
   novo a cada corte e só recebe `.fit_transform` no treino (`RegressaoQuantilicaLinearLog.fit`,
   linha 260-266); teste só usa `.transform`. A transformação do alvo (`preparar_alvo_residuo_sobre_ancora`)
   usa a coluna `ancora` da própria linha de treino — correto.

2. **Corte pela data da resposta em todos os braços, inclusive V5** — CONFIRMADO. `rodar_walk_forward_customizado`
   chama `harness.corte_temporal.selecionar_treino_ja_respondido` uma única vez (linha 490), fora de
   qualquer `if` por braço — V5 passa pelo mesmo laço, só troca a fábrica do modelo.

3. **B0 == HISTGB_FOLHA_20 do bloco 7** — CONFIRMADO por diff de parâmetros (`max_iter=250,
   learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20, random_state=42, loss=quantile,
   quantile=0.85` — idêntico nos dois arquivos). Reexecutei a célula completa de B0 h=12 (109s): MAE
   243,76 (âncora 243,8) com **n=102** — bate a trave 2 dentro da tolerância.

4. **Colunas novas reservadas / clima idêntico** — CONFIRMADO. Reexecutei o smoke test: os 8 braços
   treinados escolhem exatamente `temp_media_lag4, umid_media, temp_media_lag3, temp_max,
   pressao_media_lag3, pressao_media_lag4`. Núcleo (8) + clima (6) + vetor (6) = 20, conferido também
   via `montar_features_para_braco` no V5 (colunas impressas).

5. **Inversas das transformações** — CONFIRMADO. `expm1(previsao + log1p(ancora))` no V3/V3_M0;
   `expm1` simples no V1; clipe em 0 só nos 4 braços em log (V1, V3, V3_M0, V5) — B0, referência, V2 e
   V4 não clipam, como a pré-declaração exige.

6. **V6 pareado por `data_alvo`** — CONFIRMADO. `calcular_previsoes_do_v6_mistura` itera as linhas do
   B0 e busca a régua sazonal pela mesma `data_alvo - 52 semanas`; linha sem régua sai da mistura (não
   vira 0 nem NaN silencioso).

7. **Tamanho das famílias** — CONFIRMADO por contagem: F1 = 6 variantes × 4 h = **24**; F2 = 7
   entidades × 3 h = **21**; F3 = 1 par × 4 h = **4**. Holm é recalculado por família
   (`_comparacoes_para_dataframe` chama `harness.corrigir_por_holm` uma vez por família).

8. **Travas antes das comparações** — CONFIRMADO. `consolidar_e_analisar` chama `conferir_travas` e dá
   `return` antes de montar qualquer família se `valido` for falso.

9. **Padrão de código** — sem `lambda`, sem comprehension com regra de negócio, `np.where` só de um
   nível, type hints e docstrings presentes. Achado não bloqueante: `PAINEL_REFERENCIA` (linha 103) e
   `NIVEL_DE_SIGNIFICANCIA` (linha 87) são atribuídos e nunca lidos — código morto inofensivo.

## Achados não bloqueantes (não invalidam a rodada, mas valem registro)

- **`provar_sinal_da_ancora` é tautológica.** Ela recalcula os dois lados da igualdade só por
  aritmética de datas (`data_origem - semanas_de_recuo` vs `data_alvo - 52`), sem nunca chamar
  `.shift()` nem usar a tabela do walk-forward real. Ela sempre passa, mesmo que o `.shift()` de
  produção estivesse errado. A garantia real veio da minha reexecução independente (item 1), não desta
  função. Sugestão: reescrever o teste para ler a coluna `ancora` de fato calculada e comparar contra
  um `dict` `data -> casos`, como fiz na verificação.
- **Seção 5 (candidata à confirmatória, réplica condicional em LightGBM) não tem código.**
  `consolidar_e_analisar` grava os CSVs de F1/F2/F3 e as leituras descritivas, mas a decisão final
  (MAE vs B0 na calibração 2022-2023, e a réplica condicional) depende de leitura manual dos CSVs. É
  compatível com "réplica condicional" ser posterior, mas registrar para não esperar veredito
  automático do script.
- **Risco operacional em `--consolidar`:** `previsoes_parcial__*.csv` duplicados (braço reexecutado sob
  um agrupamento `--bracos` diferente) são resolvidos por `drop_duplicates(subset=["braco","h","data_alvo"])`,
  que fica com a primeira ocorrência na ordem alfabética dos arquivos — não necessariamente a mais
  recente. Recomendo limpar `saidas/previsoes_parcial__*.csv` antes da rodada real.

## O que foi reexecutado (evidência, não só leitura)

- `python3 rodar.py --smoke` — 8 braços + V6, sem erro, todas as previsões finitas.
- `python3 rodar.py --provar-ancora` — passou (mas ver achado sobre ser tautológica).
- `python3 rodar.py --provar-equivalencia` — walk-forward próprio == `harness.rodar_walk_forward`
  nas últimas 20 origens de B0 h=12, `rtol=1e-10` (158s de CPU).
- Célula completa de B0 h=12 (109s): MAE 243,76, n=102, contra âncora 243,8 — bate.
- Script isolado comparando a coluna `ancora` (V3) contra busca por data em 10 linhas amostradas —
  10/10 bateram.
