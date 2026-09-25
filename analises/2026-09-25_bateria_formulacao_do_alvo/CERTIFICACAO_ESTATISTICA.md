# Certificação estatística adversarial — bateria de formulação do alvo (25/09/2026)

Certificador independente. Reimplementação do zero, sem ler as funções de comparação de `rodar.py`,
a partir de `previsoes_por_braco.csv` e `tabela_final.csv`. Código:
`/private/tmp/claude-501/.../scratchpad/cert_estatistica.py`.

## Veredito: **APROVADO**. Nenhuma divergência encontrada.

## O que foi conferido e bateu

- **Travas 1 e 2:** `referencia` MAE 98,0/219,7/272,6/278,8; `B0` MAE 133,6/199,6/223,2/243,8; n=102 em
  todos os h. Exato.
- **MAE de avaliação (h=12) para os 9 braços + régua sazonal:** todos os 9 valores batem com a âncora,
  na casa decimal informada (ex.: V3_ancora_residuo 823,96 → 824,0; V3_M0 858,77 → 858,8).
- **Duplicatas de (braço, h, data_alvo):** nenhuma. B0 não entrou duas vezes.
- **V6_mistura reconstruído** (`0,5×B0 + 0,5×régua`) bate com o CSV, diferença máxima ~1e-13 (erro de
  ponto flutuante, não divergência).
- **F1 (24 comparações, Holm sobre 24):** só V3 h=1 (0,0054), V3 h=8 (0,0017), V3 h=12 (0,0097), V5 h=8
  (0,0263) com p Holm < 0,05 — todas as 4 batem exatamente com a âncora, e todas são pioras (mae_variante
  > mae_B0), confirmando o sinal.
- **F2 (21, Holm sobre 21):** só V2 h=12 (0,0006), V3 h=8 (0,0033), V3 h=12 (0,0032), V5 h=8 (0,0073)
  significativos — batem exatamente, e todos são pioras contra a régua.
- **F3 (4, Holm sobre 4):** p Holm 0,1890 / 0,0001 / 0,0624 / 0,0132 (h=1,4,8,12) — bate exatamente.
- **Tamanho das famílias:** F1 = 6 variantes × 4 h = 24; F2 = 7 braços (B0+6) × 3 h = 21; F3 = 4. Corretos.
- **Previsões extremas** (V3 h=12, 2025-03-23, previsto 10.524/real 1.801; V5 h=8, 2024-04-21, previsto
  27.258/real 1.855): ambas conferidas linha a linha no CSV, batem.
- **Critério de decisão (seção 5):** nenhum braço satisfaz "melhora + p Holm F1 <0,05 em h=12" (os únicos
  significativos em h=12 pioram); portanto nenhum candidato à rodada confirmatória — coerente com o
  relatório.

## Discrepâncias

Nenhuma. Todas as âncoras numéricas do orquestrador e os três CSVs de família (`familia_f1...`,
`familia_f2...`, `familia_f3...`) foram reproduzidos de forma independente sem qualquer divergência de
sinal, magnitude ou composição de família.
