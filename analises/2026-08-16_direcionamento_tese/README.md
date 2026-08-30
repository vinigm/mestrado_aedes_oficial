# TESTE C — Poder estatístico com casos notificados

## O que este teste responde

Migrar o alvo de detecção de surto de **confirmados** (SINAN, `tabela_final.csv`, só
2018-2026) para **notificados** (InfoDengue, 2010-2026) aumenta o número de semanas
de surto disponíveis — e isso, mantida a mesma taxa de discordância por semana de
surto observada ontem, bastaria para o McNemar ganhar poder (sobreviver à correção
de Holm com 6 comparações)?

**Importante: isto é projeção binomial, não um modelo re-rodado.** Nenhum modelo foi
treinado. O script só (1) conta semanas de surto nas duas séries e (2) escala o
número de discordantes de ontem pela razão entre semanas de surto das duas séries,
assumindo que a taxa de discordância por semana de surto se mantém constante.

## Dados e método

- **Notificados:** `infodengue_poa_dengue.csv`, coluna `casos` (não é `casos_est`,
  que é estimado por nowcasting) — 857 semanas, **2010-01-03 a 2026-05-31**.
- **Confirmados:** `tabela_final.csv`, coluna `casos_confirmados` — janela com dado
  não-nulo: **2018-02-18 a 2026-04-26** (428 semanas não-nulas dentro de 725 linhas
  totais 2012-2026).
- **Limiar de surto:** percentil expansível (P90 e P95), calculado semana a semana
  usando só o passado, com mínimo de 52 semanas de histórico antes de classificar —
  replica a lógica que o projeto já usa (nada de vazamento de futuro).

## Números-âncora

### Semanas de surto por série (P90 / P95)

| Série | Percentil | Semanas classificáveis | Semanas de surto | Taxa de surto |
|---|---|---|---|---|
| Notificados (InfoDengue) | P90 | 805 | **193** | 23,98% |
| Confirmados (SINAN) | P90 | 376 | **89** | 23,67% |
| Notificados (InfoDengue) | P95 | 805 | **112** | 13,91% |
| Confirmados (SINAN) | P95 | 376 | **62** | 16,49% |

A taxa de surto (% de semanas classificadas como surto) é **praticamente igual**
entre as duas séries — a diferença real está no **número absoluto** de semanas
classificáveis: notificados oferece **805** vs **376** de confirmados (mais que o
dobro), porque cobre 2010-2026 em vez de só 2018+.

### Poder projetado do McNemar (P90, base de discordância = confirmados)

| Cenário | Semanas de surto (base) | b | c | Discordantes | p bruto | p Holm (teto, 6 comp.) |
|---|---|---|---|---|---|---|
| Ontem (confirmados, observado) | 89 | 4 | 14 | 18 | 0,0309 | 0,1853 |
| Projeção (notificados, mesma taxa) | 193 | 9 | 30 | **39** | **0,0011** | **0,0064** |

Taxa de discordância mantida constante: **0,2022 discordantes por semana de surto**
(18/89), aplicada às 193 semanas de surto de notificados → **≈39 discordantes**
projetados (b≈9, c≈30, mantendo a proporção b/c de ontem).

**Conclusão numérica:** com 39 discordantes em vez de 18, o p bruto projetado cai de
0,031 para **≈0,001**, e o teto Holm (6 comparações) cai de 0,185 para **≈0,006** —
ou seja, a migração para notificados, **se a taxa de discordância se mantiver**,
seria suficiente para o teste sobreviver à correção múltipla.

### Bônus — bandas/percentis prontos no InfoDengue

O CSV do InfoDengue já traz colunas de classificação de alerta prontas — úteis para
comparar com Freitas 2025 sem precisar recalcular percentil:

- `nivel` — nível de alerta INCIDÊNCIA (1 a 4, escala tipo verde/amarelo/laranja/vermelho).
- `nivel_inc` — nível de incidência (0, 1, 2).
- `p_rt1` — probabilidade de Rt > 1.
- `Rt` — número de reprodução estimado.
- `receptivo` / `transmissao` — indicadores binários de condição climática/transmissão.

Nenhuma dessas colunas é um percentil expansível "só passado" — são calculadas pelo
próprio modelo do InfoDengue (metodologia própria, não documentada aqui em detalhe),
então **não substituem** o cálculo P90/P95 expansível feito neste teste, mas servem
de checagem cruzada.

## Ressalvas (hipótese, não fato)

- ⏳ **A projeção de poder é aritmética, não um McNemar real rodado com o alvo
  notificados.** Ela assume que a taxa de discordância por semana de surto (b, c)
  observada com confirmados se repete identicamente com notificados — isso é uma
  hipótese a confirmar re-rodando o modelo real com notificados como alvo.
- ⏳ O denominador usado para "taxa de discordância" (89 semanas de surto de
  confirmados) é uma aproximação: o correto seria o número de semanas classificadas
  como surto por **pelo menos um** dos dois métodos comparados no McNemar de ontem,
  que não estava disponível aqui — só o resumo b=4, c=14.
- ⏳ Notificados (InfoDengue) tem componente de nowcasting/atualização retroativa
  (coluna `casos_est` existe para isso); usamos a coluna `casos` (contagem
  reportada), que ainda pode ser revisada para trás nas semanas mais recentes —
  checar estabilidade da série antes de fixá-la como alvo definitivo.
- ⏳ Notificação ≠ confirmação clínica/laboratorial: mudar o alvo muda a
  **definição de produto/pergunta de pesquisa** (prever notificação vs prever
  confirmação), não é só uma escolha técnica de poder estatístico — decisão de
  produto a validar com o orientador.

## Arquivos desta pasta

- `teste_c_poder_notificados.py` — script único, roda em <1s.
- `semanas_surto_por_serie.csv` — contagens P90/P95 nas duas séries.
- `poder_projetado_mcnemar.csv` — projeção de b/c/p bruto/p Holm.
- `bandas_infodengue_colunas.csv` — inventário das colunas de banda prontas do InfoDengue.
