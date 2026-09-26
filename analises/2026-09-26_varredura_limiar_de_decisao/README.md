# Varredura do limiar de decisão e estágios oficiais — 26/09/2026

> Pré-declaração: `PRE_DECLARACAO.md` (com a emenda 1), nesta mesma pasta. Script: `rodar.py`,
> cópia estendida de `analises/2026-09-25_alarme_contra_canal_endemico/rodar.py` (original intacto).
> Log completo: `execucao.log`. Saídas: `saidas/`.

## Trava (Parte D) — ✅ OK

`M_adotado`, evento `E_100`, avaliação 2024+:

| h | Sensibilidade | Precisão | Falsos/ano |
|---|---|---|---|
| 4 | 0,9706 (esperado 0,971) | 0,9429 (esperado 0,943) | 0,667 (esperado 0,7) |
| 12 | 0,7692 (esperado 0,769) | 0,8108 (esperado 0,811) | 2,333 (esperado 2,3) |

Todas as diferenças dentro da tolerância (0,002 nas proporções, 0,05 em falsos/ano). A rodada
prosseguiu.

## Veredito em uma frase

**O modelo (`M_adotado` e `M_folha20`) NÃO passa no critério de `E_421`**: em nenhuma das 4
combinações (2 modelos × h=4/h=12) ele vence `R_ano_passado` em Youden com p de Holm < 0,05 — perde
ou empata em Youden em 3 das 4, e na única em que vence (h=4) o p de Holm fica em 1,0.

---

## Parte A — varredura do limiar de decisão (descritiva)

`saidas/varredura_limiar_decisao.csv` · `saidas/verificacao_previsao_youden.csv` ·
`saidas/figura_varredura_sensibilidade_falsos.png`.

**Previsão declarada (D de melhor Youden deve ficar ACIMA de 421): confirma só em h=1, falha em
h=4/8/12.**

| Modelo | h | D de melhor Youden | Confirmou D>421? |
|---|---|---|---|
| M_adotado | 1 | 600 | ✅ sim |
| M_adotado | 4 | 421 | 🔴 não (empata no próprio 421) |
| M_adotado | 8 | 200 | 🔴 não |
| M_adotado | 12 | 50 | 🔴 não |
| M_folha20 | 1 | 600 | ✅ sim |
| M_folha20 | 4 | 300 | 🔴 não |
| M_folha20 | 8 | 300 | 🔴 não |
| M_folha20 | 12 | 100 | 🔴 não |

Sem suavizar: a hipótese de que o q0,85 superestima e por isso pede um D de decisão mais alto que o
evento **só se sustenta em h=1**. Em h=4/8/12 o melhor Youden aparece em D **abaixo** de 421 — nesses
horizontes o modelo não está superestimando o bastante para justificar um decisão mais exigente; ao
contrário, um D mais baixo já captura mais surto sem custar tantos falsos positivos. Isso não vira
resultado (a pré-declaração proíbe apresentar o melhor D como vencedor) — é só o registro de que a
previsão, como escrita, falhou na maioria dos horizontes.

A figura confirma visualmente: o círculo vazado (D=421, a regra de hoje) fica em pontos da curva que
NÃO são o "joelho" (melhor sensibilidade por falso) em h=4/8/12 — haveria ganho de sensibilidade
disponível a poucos falsos a mais de distância, movendo D para baixo.

## Parte B — os estágios oficiais como evento

`saidas/metricas_estagios_oficiais.csv` (E_100, E_140, E_421 confirmatório, E_702; com
`n_surto_periodo_total` e `n_blocos_contiguos_periodo` ao lado de `n_surto`, calculados sobre as 121
semanas reais do período — **bate a âncora**: 100→39/2 blocos · 140→38/2 · 421→28/2 blocos, maior 14 ·
702→23/2).

`saidas/mcnemar_holm_familia_combinada_24_testes.csv`: família de Holm com **24 comparações** (16 já
abertas em 25/09 + 8 novas de `E_421`). **4 sobrevivem a Holm** — as 4 já eram esperadas: os 2 modelos
perdendo para `R_hoje` em h=12 (p_holm 0,00014 e 0,00008), mesmo padrão de 25/09. Nenhuma das 4
comparações contra `R_ano_passado` sobrevive.

`saidas/criterio_de_ganho_e421.csv` — critério da pré-declaração (vencer `R_ano_passado` em Youden
com p_holm<0,05):

| Modelo | h | Youden modelo | Youden R_ano_passado | Vence Youden? | p_holm | Conta como ganho? |
|---|---|---|---|---|---|---|
| M_adotado | 4 | 0,960 | 0,727 | sim | 1,000 | 🔴 não |
| M_folha20 | 4 | 0,920 | 0,727 | sim | 1,000 | 🔴 não |
| M_adotado | 12 | 0,393 | 0,736 | não | 0,204 | 🔴 não |
| M_folha20 | 12 | 0,473 | 0,736 | não | 0,148 | 🔴 não |

Em h=4 os modelos vencem em Youden bruto, mas o McNemar contra `R_ano_passado` não é nem perto de
significativo (p_holm=1,0) — a amostra de discordantes é pequena (9 e 12 pares). Em h=12 os modelos
perdem em Youden. **Compromisso cumprido**: o resultado negativo é reportado como tal, igual à derrota
de 3 meses contra a régua sazonal já registrada em 25/09.

## Parte C — bloco-bootstrap da inflação do p

`saidas/bootstrap_inflacao_p.csv`. Método: reamostragem por bloco móvel circular da série semanal
INTEIRA de sinais (+1/-1/0, ordenada por `data_alvo`), L ∈ {4,8,13,26} semanas, 2.000 reamostragens,
semente 20260926; erro padrão bootstrap da proporção de sinais positivos substitui o erro padrão
binomial iid; p bootstrap via aproximação normal em torno de 0,5. Descritivo, não substitui o p oficial.

⚠️ **Parágrafo corrigido pelo orquestrador em 26/09/2026.** A redação original dizia que a inflação
aparecia "só" num teste, e o descrevia como "o mais equilibrado (7 contra 4)". Estava **errado nos dois
pontos**, achado pela certificação e conferido no CSV. O texto abaixo é o correto.

**A inflação aparece exatamente onde importa: nas comparações contra `R_ano_passado`.**

| Teste | Discordantes | Razão `p_bootstrap/p_nominal` |
|---|---|---|
| h=4, `M_adotado` × `R_ano_passado` | 9 (7 × 2) | **1,10 a 1,51** — acima de 1 nos 4 comprimentos |
| h=12, `M_adotado` × `R_ano_passado` | 11 (1 × 10) | **2,11 a 3,44** em 3 dos 4 comprimentos |
| h=4 e h=12 × `R_hoje` | 11 a 35 | 0,0001 a 0,82 — **abaixo de 1** |
| h=12, `M_folha20` × `R_ano_passado` | 8 | não calculável, erro padrão zero |

- **São 2 testes com inflação, não 1.**
- **O teste de h=12 não é o mais equilibrado; é o mais desequilibrado** dos dois, com divisão 1 contra 10.
  A explicação mecanicista da redação original, de que a inflação viria do equilíbrio entre os lados, **não
  se sustenta** nesses dados.
- **A leitura que os números sustentam:** onde o modelo vence com folga, contra `R_hoje`, o resultado é
  robusto ao bloco. Onde a disputa é apertada, contra `R_ano_passado`, o p nominal é otimista em até
  **3,4×** — e como o veredito contra `R_ano_passado` já é negativo, a inflação o torna **ainda mais**
  negativo, nunca o contrário. 4 células (`M_folha20 vs R_ano_passado, h=12`, todos os L) ficam com erro padrão
bootstrap = 0 (série quase constante nos poucos pares discordantes) — p bootstrap não calculável,
registrado como tal, sem forçar um número.

🔴 **Desvio a reportar — teste de 13/09 NÃO localizado.** A pré-declaração pedia bootstrap também do
teste que sobrevive a Holm em 13/09 (alvo notificados, P90, h=12, n=553, p_holm 0,037). Localizado o
resultado agregado (`modelagem_aedes/dados/saidas/resultados/surto_notificados_mcnemar.csv`: n=553,
discordantes=30, p_bruto=0,00617, p_holm=0,0370) — mas **as previsões por semana (acerto/erro por
`data_alvo`) nunca foram salvas em disco**: `rodar_cidade_surto_notificados` (`modelagem_aedes/pipeline.py`)
calcula a tabela `comparacao` em memória e descarta após agregar. Sem a ordem temporal dos pares
discordantes, o bloco-bootstrap não pode ser calculado sem re-treinar os 2 classificadores
walk-forward — proibido pela pré-declaração ("nenhum modelo é treinado"). Registrado como linha própria
em `bootstrap_inflacao_p.csv` (p_bootstrap=NaN, motivo explícito), não decidido em silêncio.

## Arquivos gerados

`saidas/`: `metricas_por_regra_e100_ecanal.csv` (trava), `varredura_limiar_decisao.csv`,
`verificacao_previsao_youden.csv`, `figura_varredura_sensibilidade_falsos.png`,
`metricas_estagios_oficiais.csv`, `mcnemar_holm_familia_combinada_24_testes.csv`,
`criterio_de_ganho_e421.csv`, `bootstrap_inflacao_p.csv`. Log: `execucao.log`.
