# Pré-declaração — importância por bloco na configuração de folha mínima 20

> Escrita em **26/09/2026**, **antes** de rodar. Pedido do Vinicius na mesma data.
> Emenda posterior, se houver, entra datada no fim deste arquivo — nunca por edição silenciosa.

---

## 1. A pergunta

**O modelo de folha mínima 20 se apoia mais no vetor do que o de folha mínima 5?**

O [bloco 3 de 23/09/2026](../2026-09-23_bateria_noturna/bloco_3_importancia_por_bloco/) mediu quanto o
modelo **adotado** depende de cada bloco de colunas. O vetor domina de h=4 a h=11, entre **45,7%** e
**73,1%** de aumento do erro quando as colunas do mosquito são trocadas.

Essa medição existe numa configuração só. A configuração de **folha mínima 20** é a única das duas em que
o vetor **reduz** o erro na ablação (+12,3% em 3 meses, p de Holm 0,0151, bloco 7). Falta saber se essa
diferença aparece também na dependência medida por permutação.

---

## 2. Estatuto: DESCRITIVO

Declarado antes, para não ser reinterpretado depois:

- 🚫 **Não testa hipótese.** Nenhum valor-p será calculado.
- 🚫 **Não abre família de correção múltipla.** Nada aqui entra em Holm.
- 🚫 **Não adota configuração.** Nenhum resultado deste bloco autoriza trocar o cenário de referência.
- ✅ **Descreve a forma da dependência** de um modelo já treinado, e nada além disso.

É o mesmo estatuto do bloco 3, e pela mesma razão: a troca de colunas cria combinações que não existem no
mundo (uma semana de verão pode receber o vetor de uma semana de inverno), o que tende a **inflar** a
importância de blocos que interagem com os outros.

---

## 3. A métrica

Para cada bloco de colunas, em cada horizonte:

$$\text{importância}_{\text{bloco},h} = 100 \times \frac{\overline{|y - \hat{y}_{\text{trocado}}|} - \text{MAE}_{h}}{\text{MAE}_{h}}$$

Onde:

- $y$ é o número real de casos da semana-alvo;
- $\hat{y}_{\text{trocado}}$ é a previsão feita com as colunas daquele bloco substituídas pelas de uma
  semana sorteada **do próprio treino**, repetido **20 vezes** por corte;
- $\text{MAE}_{h}$ é o erro absoluto médio da previsão **sem troca** naquele horizonte;
- a média é tomada sobre as **102 semanas** do período de avaliação (a partir de 01/01/2024).

**Positivo = o modelo piora quando perde o bloco, ou seja, ele se apoia nesse bloco.**

Os três blocos são os mesmos do bloco 3:

| Bloco | Colunas |
|---|---|
| **Núcleo** | `casos`, `casos_lag1` a `lag4`, `casos_mm4`, `sem_sin`, `sem_cos` |
| **Clima** | as 6 escolhidas pelo ranking de ganho |
| **Vetor** | `aedes_aegypti_por_armadilha`, seus lags 1 a 4, `vetor_mm4` |

---

## 4. O que muda em relação ao bloco 3

**Exatamente um parâmetro:** `min_samples_leaf`, de **5** para **20**.

Permanecem idênticos: a tabela, o corte de maturidade, as defasagens, a seleção de clima, o alvo, os
horizontes, o walk-forward, o corte de treino pela data da resposta, o número de trocas (20) e a semente
(42).

⚠️ **Consequência deliberada:** como a semente é a mesma e a sequência de consumo do gerador é a mesma
(mesmos horizontes, mesmos cortes, mesmos tamanhos de treino, mesma ordem dos blocos), **as semanas
sorteadas são as mesmas** das do bloco 3. As duas medições são pareadas no sorteio, não só no período.

---

## 5. A trava de validação

A trava do bloco 3 confere a referência de folha 5 contra o painel publicado. Aqui ela **reprovaria por
construção**, porque o modelo é outro. Ela é substituída por:

**A previsão sem troca, na folha 20, tem de reproduzir o braço `HistGB_folha20_M1` do
[bloco 7](../2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/), no período de avaliação:**

| h | MAE esperado | R² esperado |
|---|---|---|
| 1 | 133,6259 | 0,8335 |
| 4 | 199,6352 | 0,7167 |
| 8 | 223,1827 | 0,5761 |
| 12 | 243,7645 | 0,5577 |

Tolerâncias: **0,2** no MAE e **0,003** no R², as mesmas do harness. O n de cada célula tem de dar **102**.

**A trava prova três coisas de uma vez:**

1. o modelo instanciado é mesmo o de folha 20;
2. o laço de walk-forward deste script reproduz o do harness;
3. 🔴 **a tabela de dados é a mesma de 23/09/2026** — isto é, a reversão de 2026 feita em 26/09 devolveu a
   base ao estado anterior. Sem isso, comparar com o bloco 3 seria inválido.

**Se a trava reprovar, nenhum número novo é lido.** O script para e reporta.

---

## 6. A leitura, declarada antes de ver o resultado

**Direção esperada:** que a importância do vetor na folha 20 seja **maior ou igual** à da folha 5 nos
horizontes longos, porque a folha 20 é a configuração que extrai ganho do vetor na ablação.

🔴 **O resultado contrário é possível e será reportado como veio.** A folha 20 obriga cada folha da árvore
a ter no mínimo 20 semanas, o que produz um modelo mais grosso; um modelo mais grosso pode se apoiar
**menos** em qualquer coluna específica, inclusive no vetor. Se a importância do vetor **cair**, a leitura
é que ablação e permutação medem coisas diferentes — e isso vai para o README com essa letra.

**Nenhuma das duas direções muda a configuração adotada.** O bloco é descritivo.

---

## 7. Limitações conhecidas, herdadas do bloco 3

- **A troca cria combinações inexistentes** e tende a inflar a importância de blocos que interagem.
- **Sem intervalo de confiança.** Uma semente, sem repetição. Os números mostram a forma da dependência,
  não a precisão dela.
- **Duas temporadas.** As 102 semanas de avaliação cobrem 2024 e 2025, duas epidemias.
- ⚠️ **Escalas diferentes:** o MAE base da folha 20 não é o da folha 5 (133,6 contra 98,0 em h=1). O
  percentual é relativo ao próprio MAE de cada configuração, então comparar os percentuais compara
  **dependência relativa**, não erro absoluto. Dizer isso em qualquer slide que use os dois.

---

## 8. Custo estimado

**12 a 14 minutos.** O bloco 3 levou 20 minutos na folha 5; a folha 20 treina em torno de 0,6× o tempo
(medido no bloco 6: 7,1 contra 4,0 minutos; e no bloco 7: 19,5 contra 11,8).
