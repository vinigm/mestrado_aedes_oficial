# Importância por bloco na folha mínima 20 — o quanto cada modelo se apoia no mosquito

> **Rodado em 26/09/2026**, 15,6 min. Pedido do Vinicius na mesma data.
> Protocolo em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), escrito **antes** de rodar.
> **Bloco descritivo:** não testa hipótese, não calcula valor-p, não entra em correção múltipla e não
> autoriza trocar a configuração adotada.

---

## Em uma frase

**A configuração de folha 20 se apoia mais no vetor do que a adotada, nos 12 horizontes, sem exceção.**
Em 1 mês à frente, trocar as colunas do mosquito **mais que dobra** o erro da folha 20 (+108,3%), contra
+62,2% na folha 5. A direção tinha sido declarada antes de rodar, e se confirmou.

---

## 1. Por que este bloco existe

O [bloco 3 de 23/09/2026](../2026-09-23_bateria_noturna/bloco_3_importancia_por_bloco/) mediu quanto o
modelo **adotado** (folha mínima 5) se apoia em cada bloco de colunas. Existia numa configuração só.

A configuração de **folha 20** é a única das duas em que o vetor **reduz** o erro quando se treina um
modelo sem ele (+12,3% em 3 meses, p de Holm 0,0151,
[bloco 7](../2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/)). Faltava saber se essa diferença
aparece também na **dependência**, que é outra medida.

**As duas medidas respondem perguntas diferentes, e isso não pode ser confundido:**

| Medida | Pergunta | Como se mede |
|---|---|---|
| **Permutação** (este bloco) | o modelo **se apoia** no vetor? | embaralhar as colunas de um modelo **já treinado** |
| **Ablação** (bloco 5 e 7) | um modelo **sem** o vetor prevê pior? | treinar **do zero** sem as colunas |

---

## 2. O que muda em relação ao bloco 3

**Exatamente um parâmetro:** `min_samples_leaf`, de **5** para **20**.

Permanecem idênticos a tabela, o corte de maturidade, as defasagens, a seleção de clima (as mesmas 6
colunas, na mesma ordem), o alvo, os horizontes, o walk-forward, o corte de treino pela data da resposta,
o número de trocas (20) e a semente (42).

⚠️ **As semanas sorteadas são as mesmas do bloco 3.** A semente é a mesma, a ordem de consumo do gerador é
a mesma e os tamanhos de treino não dependem do modelo. As duas medições estão pareadas no sorteio, não só
no período.

---

## 3. Trava de validação — passou

A previsão sem troca reproduziu o braço `HistGB_folha20_M1` do bloco 7, no período de avaliação:

| h | MAE medido | MAE do bloco 7 | R² medido | R² do bloco 7 |
|---|---|---|---|---|
| 1 | 133,626 | 133,626 | 0,834 | 0,834 |
| 4 | 199,635 | 199,635 | 0,717 | 0,717 |
| 8 | 223,183 | 223,183 | 0,576 | 0,576 |
| 12 | 243,765 | 243,764 | 0,558 | 0,558 |

n = **102** em todos. A trava prova três coisas: o modelo é mesmo o de folha 20, o laço reproduz o do
harness, e **a tabela continua a de 23/09/2026** — isto é, a reversão de 2026 feita em 26/09 devolveu a
base ao estado anterior.

---

## 4. 🔴 O incidente do Python — a primeira rodada reprovou

A primeira execução, com `./.venv/bin/python`, **reprovou na trava**: MAE 132,25 / 191,46 / 226,80 /
245,91 contra 133,63 / 199,64 / 223,18 / 243,76.

A investigação descartou, com evidência, todas as causas de dado e de código:

- a tabela é **bit a bit idêntica** à de 30/08 (`git diff 544263a 40d49c9` volta vazio);
- o alvo real bate nas 295 semanas, diferença máxima **0,000000**;
- as 6 colunas de clima e as 20 colunas do modelo são as mesmas;
- os cortes são os mesmos (295, 294, … 284);
- duas passagens no mesmo processo dão resultado **idêntico** (292/292 previsões).

**A causa é o interpretador.** O projeto tem dois Pythons com versões diferentes da biblioteca:

| Como se roda | scikit-learn | numpy |
|---|---|---|
| `python3` — o que o `orquestrar.sh` da bateria usa | **1.8.0** | 2.4.4 |
| `./.venv/bin/python` | **1.9.0** | 2.4.6 |

A 1.9.0 constrói as árvores de forma diferente: ~55% das previsões batiam bit a bit e as demais divergiam.
Re-rodado com `python3`, a trava passou com reprodução exata.

⚠️ **Consequência para o projeto:** qualquer análise antiga re-rodada pelo venv produz números diferentes
**em silêncio**. O log da rodada reprovada está preservado em `execucao_com_venv_REPROVADA.log`.

---

## 5. Resultado

Aumento do erro (MAE) ao trocar cada bloco, período de avaliação (102 semanas, 2024+):

| h | MAE real | R² | Núcleo | Clima | **Vetor** |
|---|---|---|---|---|---|
| 1 | 133,6 | 0,834 | **198,0%** | 2,7% | 23,6% |
| 2 | 191,6 | 0,692 | **72,2%** | 4,0% | 54,4% |
| 3 | 203,3 | 0,660 | 32,4% | 6,5% | **93,6%** |
| 4 | 199,6 | 0,717 | 25,0% | 7,2% | **108,3%** |
| 5 | 225,4 | 0,636 | 15,2% | 12,3% | **89,7%** |
| 6 | 221,5 | 0,609 | 25,4% | 12,4% | **90,7%** |
| 7 | 232,4 | 0,531 | 30,0% | 11,4% | **91,7%** |
| 8 | 223,2 | 0,576 | 45,0% | 16,8% | **98,7%** |
| 9 | 234,8 | 0,545 | 47,8% | 6,7% | **87,0%** |
| 10 | 236,8 | 0,559 | 52,6% | 4,5% | **82,3%** |
| 11 | 241,6 | 0,570 | 54,6% | 5,8% | **68,4%** |
| 12 | 243,8 | 0,558 | **56,7%** | 3,5% | 51,1% |

### O vetor nas duas configurações

| h | folha 5 (adotado) | folha 20 | diferença | em casos |
|---|---|---|---|---|
| 1 | 20,0% | 23,6% | +3,6 pp | +11,9 |
| 2 | 40,4% | 54,4% | +14,0 pp | +38,8 |
| 3 | 70,5% | 93,6% | +23,0 pp | +59,6 |
| 4 | 62,2% | **108,3%** | **+46,1 pp** | +79,5 |
| 5 | 73,1% | 89,7% | +16,7 pp | +43,2 |
| 6 | 56,9% | 90,7% | +33,7 pp | +51,3 |
| 7 | 60,8% | 91,7% | +30,9 pp | +61,2 |
| 8 | 52,8% | **98,7%** | **+45,9 pp** | +76,3 |
| 9 | 48,7% | 87,0% | +38,3 pp | +65,7 |
| 10 | 54,7% | 82,3% | +27,5 pp | +41,2 |
| 11 | 45,7% | 68,4% | +22,7 pp | +31,8 |
| 12 | 38,6% | 51,1% | +12,4 pp | +16,8 |

⚠️ **Não é artefato de denominador.** A folha 20 tem MAE menor de h=4 em diante, o que sozinho inflaria o
percentual. A última coluna mostra o aumento em **casos**, e a folha 20 é maior nos 12 horizontes também
em valor absoluto.

---

## 6. O que isso quer dizer

### A virada acontece mais cedo e é mais funda

- Na folha 5 o vetor passa o histórico de casos em **h=4**; na folha 20, em **h=3**.
- Na folha 20 o vetor fica acima do núcleo de **h=3 a h=11**, nove horizontes seguidos, e por margem
  muito maior: em h=4 são 108,3% contra 25,0%.
- Em **h=12 o núcleo retoma** nas duas configurações (56,7% contra 51,1% na folha 20).

### As duas medidas apontam junto

A folha 20 **ganha mais** com o vetor (ablação: +8,1% em 2 meses, +12,3% em 3 meses, p de Holm 0,0056 e
0,0151) **e se apoia mais** nele (permutação: +45,9 pp e +12,4 pp). Convergência entre medidas
independentes é o argumento mais forte que o projeto tem hoje sobre o valor da armadilha.

### O clima cresce no meio e some nas pontas

Na folha 20 o clima chega a 16,8% em h=8, contra 14% na folha 5, mas volta a 3,5% em h=12. A hipótese de
23/09 continua de pé e continua **não medida**: o que o clima informa chega por outro caminho, o vetor.

---

## 7. ⚠️ O que este resultado NÃO diz

**Não diz que as armadilhas são indispensáveis.** Permutação e ablação respondem perguntas diferentes:

- um modelo **treinado com** o vetor constrói as árvores em torno dele e quebra quando ele é trocado;
- um modelo **treinado sem** o vetor reaprende pelo histórico de casos, que é correlacionado com ele.

Na configuração **adotada**, tirar o vetor não piora de forma significativa (p de Holm **1,00** nos quatro
horizontes do bloco 5). Na folha 20 piora, em 2 e 3 meses. **"Indispensável" é a palavra que a ablação da
folha 5 proíbe.**

**Não autoriza adotar a folha 20 nem o composto.** O critério de escolha do projeto olha a calibração de
2020-2023, e ali a folha 20 é ~30% pior. E o ponto de corte do composto foi escolhido olhando o período de
avaliação.

---

## 8. Limitações, herdadas do bloco 3

- **A troca cria combinações que não existem.** Uma semana de verão pode receber o vetor de uma semana de
  inverno sorteada do treino. Isso tende a **inflar** a importância de blocos que interagem com os outros.
- **Descritivo, sem intervalo.** Uma semente, sem repetição, sem teste estatístico.
- **Duas temporadas.** As 102 semanas cobrem 2024 e 2025, duas epidemias.
- **Escalas diferentes.** O MAE base das duas configurações não é o mesmo; o percentual é relativo ao erro
  de cada uma. Por isso a tabela traz também o aumento em casos.

---

## 9. Arquivos

| Arquivo | O que é |
|---|---|
| [`PRE_DECLARACAO.md`](PRE_DECLARACAO.md) | o protocolo, escrito antes |
| [`rodar.py`](rodar.py) | o script |
| `execucao.log` | a saída da rodada válida |
| `execucao_com_venv_REPROVADA.log` | a rodada que reprovou na trava, preservada |
| `saidas/importancia_por_corte.csv` | um corte por linha |
| `saidas/importancia_por_horizonte.csv` | a tabela do §5 |
| `saidas/folha_5_contra_folha_20.csv` | a comparação entre as duas configurações |
