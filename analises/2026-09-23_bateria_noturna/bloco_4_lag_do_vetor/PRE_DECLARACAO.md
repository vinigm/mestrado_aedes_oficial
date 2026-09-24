# Pré-declaração — Bloco 4: janela de lag longa só no vetor

**Escrita em 23/09/2026, antes de rodar.**

## Pergunta
Estender a janela de lag **só do vetor**, mantendo casos e clima em 1-4 semanas, melhora o horizonte longo?

## Por que
O teste de 23/09 (`analises/2026-09-23_janela_de_lag/`) estendeu **todas** as colunas juntas e não achou
ganho: até 8 semanas, +0,4% a +1,8%; até 12, −2,3% em h=8. Mas a importância por bloco do mesmo dia mostrou
o vetor crescendo com o horizonte (derruba 0,642 de R² em h=12). Se o sinal longo mora no vetor, estender
tudo junto dilui com lags correlacionados de casos e clima.

## Braços
| Braço | Vetor | Casos e clima |
|---|---|---|
| A_referencia | lags 1-4 | lags 1-4 |
| B_vetor_ate_8 | + lags 6, 8 | lags 1-4 |
| C_vetor_ate_12 | + lags 6, 8, 10, 12 | lags 1-4 |

## Métrica, teste, família
MAE na avaliação, Wilcoxon pareado por `data_alvo`. Família: 2 × 4 horizontes = **8 comparações**, Holm.

## Critério
Entra na referência se reduzir o MAE em **h=8 E h=12** com **p de Holm < 0,05** nos dois.

## Trava
A_referencia tem de reproduzir o painel.
