# PRÉ-DECLARAÇÃO — calibração quantílica (30/08/2026)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## Pergunta

O melhor algoritmo do projeto (**HistGradientBoosting**, R² médio 0,779 contra 0,749 do LightGBM),
calibrado por regressão quantílica, corrige o viés de subestimação do pico?

**Por que refazer:** o teste de 30/08 que apontou o quantílico como remédio rodou em **LightGBM**,
que é apenas o 3º melhor algoritmo. O resultado precisa ser confirmado no algoritmo que a tese vai
de fato usar.

## Desenho

- **Algoritmo:** `HistGradientBoostingRegressor`, hiperparâmetros idênticos aos do projeto
  (`max_iter=250`, `learning_rate=0.05`, `max_leaf_nodes=15`, `min_samples_leaf=5`).
- **Variantes:** padrão (`squared_error`) + quantílico em **alpha 0,70 · 0,80 · 0,85 · 0,90**.
- **Horizontes:** 1, 4, 8, 12 semanas.
- **`passo=1`** — avalia toda semana, e não a cada duas. Dobra a base de avaliação de ~152 para
  ~304 pontos por horizonte.
- Previsão clipada em zero em **todas** as variantes, inclusive a referência.

## Separação honesta para escolher o alpha

O alpha **não pode** ser escolhido olhando o resultado final — isso seria sobreajuste.

- **Período de calibração:** previsões com semana-alvo **até 31/12/2023**;
- **Período de avaliação:** **01/01/2024 em diante** — nunca olhado na escolha.

**Critério de escolha, fixado agora:** o alpha cujo **viés no pico** (semanas com mais de 100 casos)
ficar **mais próximo de zero no período de calibração**. O MAE global entra como guarda: se o alpha
escolhido piorar o MAE global em mais de 20% contra o padrão, ele é rejeitado e o segundo colocado
assume.

Reporto **todos** os alphas nos dois períodos, para transparência — mas o alpha "escolhido" é o que
o critério acima seleciona usando **só** a calibração.

## Regras de decisão

1. **Se o alpha escolhido reduzir o viés do pico na avaliação** → a calibração quantílica entra como
   contribuição metodológica da dissertação, com o protocolo acima descrito.
2. **Se reduzir na calibração mas não na avaliação** → o ganho era sobreajuste ao período. Registrado
   como negativo e o modelo padrão permanece.
3. **Se não reduzir em nenhum** → o achado de 30/08 no LightGBM não se transfere ao HGB, e fica
   registrado como específico daquele algoritmo.

## Ressalva declarada antes

A previsão quantílica **não é previsão da média**. Um modelo em alpha 0,8 estima *"um patamar que
só será ultrapassado em 20% das vezes"* — ele é enviesado para cima **de propósito**. Isso é
adequado para alarme epidemiológico (subestimar custa mais que superestimar), mas **muda a pergunta
respondida** e precisa ser declarado assim em qualquer texto. Comparar seu R² com o de um modelo de
média é informativo, não é uma competição justa entre iguais.
