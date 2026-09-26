# Certificação adversarial — Rodada B (quantis múltiplos e WIS)

> Certificador independente, 26/09/2026. Contexto: processos da rodada B **já haviam terminado**
> (log termina em "RODADA B CONCLUIDA", nenhum PID rodando) quando esta certificação começou.
> Uma certificação anterior, feita com resultados incompletos, **não vale** — esta refaz tudo do zero.

## Veredito: VÁLIDA

Reimplementei, com código próprio (não reusei nada de `rodar.py`), a trava, o WIS (Bracher et al. 2021),
a cobertura, a régua climatológica e o teste Wilcoxon+Holm. Script em
`/private/tmp/.../scratchpad/certificar_B.py`. Todos os números batem com os publicados em `saidas/`
com divergência ≤ `5,7e-14` (ruído de ponto flutuante, não erro).

## O que foi conferido

- **Trava:** retreinei do zero (via `harness`, sem copiar `rodar.py`) o cenário adotado no quantil 0,85,
  janela 2024-01-01→2026-02-01. `h=1` MAE **97,38** (esperado 97,4) · `h=12` MAE **279,96** (esperado
  280,0). Ambos dentro da tolerância 0,2. **Confirma** o que o executor reportou.
- **Vazamento na régua:** reimplementei `calcular_previsao_da_regua` com uma asserção que dispara se
  algum ano usado for `>= ano_alvo`. Rodei nas 269 datas-alvo com histórico suficiente — **nenhum disparo**.
  A régua é genuinamente "só passado".
- **WIS/cobertura:** recalculado por origem (fórmula de Bracher com mediana + 3 intervalos 50/80/90%) a
  partir de `previsoes_quantis.csv`. As 32 linhas de `wis_e_cobertura.csv` batem exatamente.
- **Wilcoxon + Holm:** recalculado por recorte (família de 4: 2 modelos × 2 horizontes, separada em
  2024-2025 / 2026 / tudo). As 12 linhas de `familia_b.csv` batem, inclusive o veredito `significativo`
  em todas.
- **Filtro do quantil 0,85:** confirmado que ele não vaza para o WIS — `previsoes_quantis.csv` só tem os
  7 quantis declarados.

## Números principais (WIS modelo × régua, e cobertura)

**2024-2025** (n=96-97): em **h=4** os dois modelos batem a régua com folga — cenário adotado 218,7 ×
regua 313,5 (p Holm 0,000010); folha 20, 200,6 × 313,5 (p Holm 0,000004). Em **h=12** o cenário adotado
não bate a régua de forma confiável (303,7 × 324,2, p Holm 0,111); a folha 20 bate (281,4 × 324,2, p Holm
0,0016).

**2026** (n=16, poder baixo): em **h=4** nenhum modelo difere da régua (p Holm 0,50 e 0,26). Em **h=12** os
dois modelos são **piores** que a régua — cenário adotado 141,7 × regua 64,4 (p Holm 0,000122); folha 20,
159,9 × 64,4 (p Holm 0,000122). É o ano atípico (poucos confirmados) favorecendo a climatologia.

**Cobertura nominal 50%/90%:** severamente subestimada em todos os modelos e recortes. Cenário adotado em
h=12/2024-2025: cobertura 50% real = **0,144** (nominal 0,50), cobertura 90% real = **0,536** (nominal
0,90). A régua também está mal calibrada no mesmo recorte (cobertura 50% = 0,177), mas por razão
distinta — a temporada 2024-2025 foi atípica frente ao histórico usado pela régua.

## Observações (não são defeitos, são achados a registrar)

- **76,7% das origens (1.846 de 2.406)** precisaram de rearranjo isotônico por cruzamento de quantis —
  esperado quando cada quantil é treinado como regressão independente, mas alto o bastante para valer
  registrar como limite de calibração do método.
- **WIS não repete o veredito de MAE em h=12** — o achado de 25/09 ("o modelo perde para a régua em MAE
  a 3 meses") não se repete de forma significativa no WIS em 2024-2025 (cenário adotado, p Holm 0,111) nem
  em "tudo" (p Holm 0,79 e 0,37). São métricas diferentes (mediana vs. distribuição inteira) — não é
  contradição, é nuance a explicitar ao relatar o resultado.
- Emendas de 26/09 01h20 (adicionar q0,85 só para a trava, filtrar antes do WIS) foram aplicadas
  corretamente — o efeito colateral (vazamento do 0,85 pro WIS) não ocorreu.

## Não verificado nesta certificação

- Conteúdo visual de `figura_intervalos_2026.png` (existe, 178 KB, não inspecionado pixel a pixel).
- Corretude de `harness.rodar_walk_forward` em si (já certificado em rodadas anteriores, 13/09 e 23/09;
  fora do escopo desta tarefa, que é só a seção B).
