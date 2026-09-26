# Pré-declaração — busca aleatória de hiperparâmetros, julgada em 2026

> **Escrita em 25/09/2026, antes de rodar qualquer configuração.** Autorizada pelo Vinicius em 25/09/2026
> ("pode rodar, vamos ver o que aparece"). Mudança posterior vira **emenda datada** no fim.
>
> **2026 nunca foi usado para escolher nada.** É o primeiro teste fora da amostra de escolha desde 13/09.

---

## 1. Pergunta

**Com hiperparâmetros escolhidos de forma sistemática em 2022-2025, algum modelo erra menos que o cenário
adotado e que a régua na temporada de 2026, que ninguém usou para escolher?**

- Até hoje só foram buscados 3 hiperparâmetros do HistGB, em 18 combinações. A folha mínima mudou tudo.
- Hipóteses com motivo:
  - `linear_tree` deixa a árvore extrapolar, o problema de 2024;
  - a restrição monotônica põe o domínio no modelo: mais vetor e mais casos hoje nunca preveem menos.

---

## 2. Dados

- A tabela oficial, **atualizada com o DENGBR26 de setembro/2026**, depois de resolvida a leitura dupla
  do arquivo de 2026 e certificado que **2018-2025 não mudaram**.
- Município de **notificação**, decisão do Vinicius em 25/09/2026.
- Corte de maturidade do pipeline, 12 semanas.

---

## 3. Espaços de busca

Semente do sorteio: **20260925**. Todas as configurações usam quantil 0,85, as 20 colunas do cenário
adotado, `random_state=42` e 1 thread.

**HistGB — 60 sorteios**

| Hiperparâmetro | Faixa |
|---|---|
| `learning_rate` | log-uniforme, 0,01 a 0,2 |
| `max_iter` | inteiro, 100 a 600 |
| `max_leaf_nodes` | inteiro, 4 a 63 |
| `min_samples_leaf` | inteiro, 5 a 60 |
| `l2_regularization` | 0 com probabilidade 0,2; senão log-uniforme, 0,001 a 10 |
| `max_features` | uniforme, 0,4 a 1,0 |
| `max_depth` | um de {nenhum, 3, 4, 6, 8} |

**LightGBM — 60 sorteios**

| Hiperparâmetro | Faixa |
|---|---|
| `learning_rate` | log-uniforme, 0,01 a 0,2 |
| `n_estimators` | inteiro, 100 a 600 |
| `num_leaves` | inteiro, 4 a 63 |
| `min_child_samples` | inteiro, 5 a 60 |
| `reg_lambda` | 0 com probabilidade 0,2; senão log-uniforme, 0,001 a 10 |
| `colsample_bytree` | uniforme, 0,4 a 1,0 |
| `subsample` | uniforme, 0,5 a 1,0, com `subsample_freq=1` |
| `extra_trees` | falso ou verdadeiro |

**Braços com motivo, montados sobre as vencedoras:**

- **`LGB_linear`:** a vencedora do LightGBM com `linear_tree=True` e `linear_lambda` em {0,1 · 1 · 10}. O
  lambda é escolhido pelo mesmo critério da seção 4. Se o LightGBM não aceitar `linear_tree` com perda
  quantílica, o braço é registrado como **impossível**, sem trocar a perda.
- **`MONO`:** a vencedora geral, HistGB ou LightGBM, com restrição monotônica **crescente** nas colunas de
  casos e de vetor e sem restrição no resto.

---

## 4. Critério de escolha, só com 2022-2025

- **Nota de cada configuração:** a média do MAE em **1 mês e 3 meses**, nos pares com
  `2022-01-01 ≤ data_alvo ≤ 2025-12-31`.
- A de menor nota vence em cada família.
- Empate até a primeira casa decimal: vence a de menos árvores.

---

## 5. Julgamento em 2026

**Braços julgados:** `HB_best`, `LGB_best`, `LGB_linear`, `MONO`. **Controles:** cenário adotado, HistGB folha
20 e régua sazonal.

- **Recorte principal:** 2026, de janeiro até o último alvo maduro, em h 1, 4, 8, 12.
- **Métricas:**
  - MAE;
  - alarmes falsos com o limiar de 100 casos: nenhuma semana de 2026 passou de 100 até agora;
  - maior previsão contra maior real.
- **Teste:** Wilcoxon pareado de cada braço contra o cenário adotado, em 2026, h 4 e h 12 = **8
  comparações**, Holm sobre 8. ⚠️ São ~20 semanas por horizonte: o poder é baixo, e a leitura principal é
  descritiva.
- **Descritivo:** 2024-2025, sabendo que já entrou na escolha; perda quantílica; cobertura do q0,85.

## 6. Critério de decisão

- **Um braço melhora em 2026** se tiver MAE menor que o cenário adotado em 3 meses **e** menos alarmes falsos em
  3 meses. Com p Holm < 0,05, vira evidência; sem, é hipótese para 2027.
- Nada troca a referência nesta rodada.

## 7. Ameaças

- **2026 é uma temporada só, e atípica.**
- A escolha em 2022-2025 favorece configurações que acertam epidemias crescentes.
- 120 configurações num período curto: a vencedora pode ter ganhado por sorte na escolha. **O teste em 2026
  existe para isso.**

---

## Emendas

- **25/09/2026, 23h50, antes de rodar:** a trava do cenário adotado passa a usar **âncoras recalculadas na tabela
  atualizada**, e não os números publicados. Até fev/2026, o adotado dá h=1 **97,4** e h=12 **280,0**, contra 98,0 e
  278,7 publicados. A diferença vem da revisão dos casos de jan/2026 e da ordem das colunas de clima; ver o adendo
  em `analises/2026-09-25_atualizacao_dados_2026/CERTIFICACAO.md`. A trava exige reproduzir esses valores com
  tolerância de 0,2. Os de h=4 e h=8 são calculados e registrados pelo próprio script. Com a série maior, o
  recorte 2026 vai até **19/04/2026**, a última semana válida depois do corte de maturidade.
