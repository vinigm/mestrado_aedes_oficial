# Janela de treino para o alvo CASOS — 13/09/2026

> **A pergunta:** vale treinar com toda a história de casos, ou dados antigos atrapalham?
> **A resposta: INDETERMINADO pelo critério pré-declarado — e a escolha da janela quase não importa.**
> Os quatro regimes ficam num intervalo de **3,8%** de MAE médio.
> Status: ✅ concluído · Pré-declaração: [PRE_DECLARACAO.md](PRE_DECLARACAO.md) · 15,8 min de CPU.

## 1. Por que este teste foi feito

- A Rodada 4 de 29/08 respondeu isso **para o alvo densidade do vetor**: treinar desde 2012 vence em
  3 de 4 horizontes. Confirmado corrigido em 13/09.
- **Para o alvo CASOS a pergunta nunca tinha sido feita**, e não é a mesma: os casos só existem desde
  18/02/2018, e a epidemiologia mudou demais no período. 2020 e 2021 somam **109 casos**; 2024 e 2025
  somam **43.827**.
- Levantada pelo Vinicius em 13/09: se 61% das semanas têm 5 casos ou menos e essa assimetria é a
  causa medida do viés de pico, talvez cortar história calma ajude.

## 2. Como foi medido

Quatro regimes, **mesmo modelo** (a configuração de referência: HistGradientBoosting, quantil 0,85,
com vetor) e **mesmas semanas de teste**. Só a janela de treino muda.

| Regime | Treino em cada corte | Mediana de linhas |
|---|---|---|
| `expansivel_total` | tudo desde 18/02/2018 | 326 a 348 |
| `expansivel_2020` | tudo desde 01/01/2020 | 232 a 254 |
| `deslizante_4anos` | as últimas 208 linhas utilizáveis | 208 |
| `deslizante_2anos` | as últimas 104 linhas utilizáveis | 104 |

**Pareamento:** só entraram os cortes em que **os quatro** têm pelo menos 104 linhas de treino. Isso
empurrou o início da avaliação para **janeiro de 2022** e deixou 179 a 201 cortes por horizonte, dos
quais **102 caem no período de avaliação** (2024+). É o preço de comparar regimes nas mesmas semanas.

⚠️ **Ajuste de desenho registrado:** a primeira versão definia a janela deslizante como "as últimas N
semanas antes da origem" e dava **zero cortes válidos** — o corte temporal corrigido já remove as h−1
semanas mais recentes, então uma janela de 104 semanas entregava 93 linhas. Passou a contar as últimas
N linhas **utilizáveis**, que é o que a intenção pedia.

## 3. Os controles passaram

- Os quatro regimes usam **exatamente as mesmas semanas** nos quatro horizontes.
- `expansivel_total` reproduz o grid de 13/09 nas 762 semanas em comum, com diferença
  **0,0000000000**. Confirma que este é o mesmo protocolo, só começando mais tarde.

## 4. O que deu

MAE na avaliação (2024+), n=102 em todos. Menor é melhor; **negrito** é o vencedor do horizonte.

| h | expansivel_total | expansivel_2020 | deslizante_4anos | deslizante_2anos |
|---|---|---|---|---|
| 1 | **98,0** | 104,3 | 109,7 | 107,5 |
| 4 | 219,7 | **209,3** | 209,4 | 247,1 |
| 8 | 272,6 | 283,8 | 284,6 | **263,1** |
| 12 | **278,7** | 286,1 | 287,1 | 284,0 |
| **média** | **217,2** | 220,9 | 222,7 | 225,4 |

**Vitórias:** `expansivel_total` 2 de 4 · `expansivel_2020` 1 · `deslizante_2anos` 1.

## 5. Conclusão

- ✅ **VEREDITO PRÉ-DECLARADO: INDETERMINADO.** O critério exigia 3 ou 4 horizontes para fechar. Deu
  2 × 1 × 1, que a §5 classificou de antemão como pulverizado. **A prática atual permanece por inércia,
  e isso fica declarado como tal.**

- ✅ **FATO — a janela de treino não é uma alavanca importante.** Quatro regimes muito diferentes, de
  104 a 348 linhas de treino, cabem num intervalo de **3,8%** de MAE médio. Trocar a janela rende menos
  que qualquer outra decisão já medida no projeto: a função de perda rende 9,9% e o algoritmo 11,8%.

- ⚠️ **A hipótese do Vinicius não se confirma como regra geral, e também não se refuta.** Em h=1 mais
  dados vencem com folga (98,0 contra 104 a 110). Em h=4 e h=8 as janelas curtas levam vantagem
  pequena. Em h=12 o expansível volta a vencer. É um empate com sinais trocados por horizonte.

- ⚠️ **EXPLORATÓRIO, e não era o critério: no ALARME as janelas curtas vão melhor em horizonte longo.**
  Sensibilidade em h=12: `deslizante_2anos` **0,846** contra `expansivel_total` 0,769. Em h=8:
  `deslizante_4anos` 0,895 contra 0,816.
  - **Não se troca o critério depois de ver o resultado.** O MAE foi o que se pré-declarou, e por ele o
    veredito é indeterminado. Isto fica como **hipótese para outra rodada**, com pré-declaração própria.
  - Base pequena: 39 semanas de surto.

## 6. Ressalvas

- **Ablação descritiva, sem teste de significância**, como a §5 já declarava. Com 102 pontos e 4
  regimes, qualquer p seria frágil.
- O pareamento custou o período 2018–2021: a avaliação começa em 2022.
- O `deslizante_2anos` treina com exatamente 104 linhas, que é o mínimo do projeto. É o limite inferior
  do que faz sentido, não um regime confortável.
- Testado num único modelo. Outro algoritmo pode responder diferente.

## 7. Arquivos

- `rodar_janelas.py` — os quatro regimes, com o corte temporal corrigido.
- `analisar.py` — aplica os critérios da pré-declaração, incluindo os dois controles.
- `saidas/janelas_previsoes.csv` · `saidas/janelas_resumo.csv` · `saidas/analise.txt` · `saidas/janelas.log`
