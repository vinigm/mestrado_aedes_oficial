# Bloco 1 — corte de maturidade: CANCELADO antes de rodar

**Decisão de 23/09/2026, antes de gastar CPU.**

## O que se queria testar
O config usa `semanas_corte_maturidade=12`. O medido em 22.470 casos de 2025 é mediana 10,4, p75 22,7,
p90 31,6 semanas. Ninguém testou se 12 é o número certo. A ideia era rodar 8, 12, 16, 22 e 32.

## Por que o teste seria cego
`dominio/surto.py:aplicar_corte_maturidade` age **uma única vez, no fim da série**: apaga os casos das
últimas N semanas contando da última semana com caso (26/04/2026). Com N=32, apaga a partir de ~set/2025.

Para qualquer previsão de 2024 e da maior parte de 2025, o treino é **idêntico** em todos os braços — o
corte nem chega lá. O teste mostraria "sem diferença" não porque 12 seja certo, mas porque não consegue
enxergar a diferença. E uma conclusão falsa de "12 está bom" seria pior que nenhuma.

## O que seria preciso para testar de verdade
Dados **vintage**: como a contagem de casos estava em cada semana, antes de amadurecer. O walk-forward usa a
contagem final revisada para todo o passado, então nunca vê o problema que o corte existe para resolver.

## Consequência para a banca
Se perguntarem "por que 12?", a resposta honesta é: foi herdado, e não é ajustável sem dados vintage — o
walk-forward disponível não tem poder para decidir entre 8 e 32.
