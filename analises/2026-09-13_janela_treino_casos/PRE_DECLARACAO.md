# PRÉ-DECLARAÇÃO — janela de treino para o alvo CASOS

**Escrita em 13/09/2026, ANTES de rodar.** Proibido mudar hipótese, métrica ou critério depois de ver
resultado; qualquer mudança vira emenda datada ao final.

---

## 1. A pergunta

Vale a pena treinar com toda a história de casos, ou dados antigos atrapalham?

**De onde vem.** A Rodada 4 de 29/08 respondeu isso **para o alvo densidade do vetor**: treinar desde
2012 vence em 3 de 4 horizontes, e a vantagem cresce com o horizonte. Confirmado corrigido em 13/09.

**Mas para o alvo CASOS a pergunta nunca foi feita**, e não é a mesma coisa:

- os casos só existem desde **18/02/2018** (428 semanas, 8,2 anos) — não há 14 anos de casos;
- a epidemiologia mudou muito no período: 2020 e 2021 somam **109 casos**; 2024 e 2025 somam **43.827**;
- 61% das semanas têm 5 casos ou menos, e essa assimetria é a causa medida do viés de subestimação
  do pico. Cortar semanas calmas **poderia** reduzi-la.

## 2. Os quatro regimes, fixados agora

| Regime | Treino em cada corte |
|---|---|
| `expansivel_total` | tudo desde 18/02/2018 (o que o projeto faz hoje) |
| `expansivel_2020` | tudo desde 01/01/2020 |
| `deslizante_4anos` | só as últimas 208 semanas |
| `deslizante_2anos` | só as últimas 104 semanas |

**Não entra `expansivel_2022`**: sobrariam poucos pontos de teste comuns aos quatro, e o ganho de
informação não compensa a perda de comparabilidade.

## 3. Como será medido

- **Modelo:** a configuração de referência de 13/09 — HistGradientBoosting, `quantile=0.85`, conjunto
  M1 (com vetor). Idêntico para os quatro regimes; **só a janela de treino muda**.
- **Corte de treino:** o corrigido (`motor/corte_temporal.py`). Só entra a linha cuja resposta já
  tinha acontecido.
- **Horizontes:** 1, 4, 8 e 12. **Passo:** 1.
- **PAREAMENTO, e isto é inegociável:** os quatro regimes são avaliados **exatamente nas mesmas
  semanas**. Só entram os cortes em que **todos os quatro** têm pelo menos 104 linhas de treino. Sem
  isso a comparação mistura efeito da janela com efeito de avaliar em semanas diferentes — o erro que
  o projeto já cometeu duas vezes.
- **Métricas:** MAE, R² e, por horizonte, a sensibilidade de alarme (`real > 100` contra
  `previsto > 100`), porque é a métrica operacional definida hoje.

## 4. Controle

`expansivel_total` com o corte corrigido deve reproduzir, nas semanas comuns, o que o grid de 13/09 já
mediu para a mesma configuração. **Se divergir, há erro de implementação e nada é interpretado.**

## 5. Critérios de decisão, fixados agora

- **O regime vencedor é o de menor MAE médio na avaliação (2024+), contado por horizonte.** Vence
  quem levar mais horizontes; empate em número de horizontes é desempatado pelo MAE médio geral.
- **Se `expansivel_total` vencer em 3 ou 4 horizontes** → a prática atual está certa, o assunto fecha,
  e passa a valer para os dois alvos.
- **Se algum regime curto vencer em 3 ou 4 horizontes** → é achado relevante: significa que a
  epidemiologia mudou o bastante para que história antiga atrapalhe. Exige rodada de confirmação
  antes de virar decisão, porque a hipótese nasceu de uma conversa e não de teoria.
- **Se ficar dividido (2 × 2 ou pulverizado)** → resultado **indeterminado**, e a prática atual
  permanece por inércia, declarada como tal.
- **Sem teste de significância.** São 4 regimes × 4 horizontes; com o tamanho de amostra disponível,
  qualquer p seria frágil. Isto é uma **ablação descritiva** e será rotulada assim.

## 6. O que este teste NÃO responde

- Não mexe na seleção das colunas de clima, que continua fora do walk-forward.
- Não testa janela para o alvo vetor (já respondido em 29/08).
- Não é confirmatório: uma ablação de 4 regimes escolhida por conversa não substitui pré-registro.

---

## Emendas

*(nenhuma até agora)*
