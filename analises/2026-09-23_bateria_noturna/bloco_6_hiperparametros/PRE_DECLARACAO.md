# Pré-declaração — Bloco 6: busca de hiperparâmetros do HistGB

**Escrita em 23/09/2026, antes de rodar.** Sugestão do Vinicius às ~20h50.

## Pergunta
Outra combinação de hiperparâmetros do HistGB, mantendo quantil 0,85 e as 20 colunas, reduz o erro?

## Por que
Nunca foram buscados. O grid de 30/08 variou algoritmo, perda e vetor; `max_iter=250`,
`learning_rate=0.05`, `max_leaf_nodes=15` e `min_samples_leaf=5` vieram fixos do cenário 1.

## ⚠️ O risco, e a trava
Cerca de 400 semanas. Varrer muitas configurações acha alguma "melhor" por sorte. Por isso a busca tem
**duas fases separadas**, e a segunda só recebe **uma** candidata.

## Grade — 18 configurações
- ritmo `learning_rate × max_iter`: (0,05 × 250) · (0,03 × 400) · (0,10 × 150)
- `max_leaf_nodes`: 15 · 7 · 31
- `min_samples_leaf`: 5 · 20

A referência (0,05 · 250 · 15 · 5) roda **primeiro**. Horizontes 1, 4, 8 e 12.

## Fase 1 — escolha, só na calibração
**Critério:** menor MAE médio dos quatro horizontes com `data_alvo < 2024-01-01`. É o mesmo critério do
grid de 30/08. A avaliação não participa.

## Fase 2 — um único teste na avaliação
A vencedora contra a referência, Wilcoxon pareado por `data_alvo`, 4 horizontes, Holm.
**Troca a referência** se reduzir o MAE em **h=8 E h=12** com **p de Holm < 0,05** nos dois.
Se a vencedora da calibração for a própria referência, não há teste e nada muda.

## Horário-limite
Nenhuma configuração nova começa depois das **05:00**. A escolha roda sobre o que tiver terminado. A
referência roda primeiro, então a validação e a comparação existem mesmo com a grade interrompida.

## Trava
A referência tem de reproduzir o painel nos 4 horizontes.

## Proibido
Olhar a avaliação para escolher. Ampliar a grade depois de ver o resultado.
