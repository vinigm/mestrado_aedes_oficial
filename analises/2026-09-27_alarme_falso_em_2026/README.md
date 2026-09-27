# O modelo teria gritado surto na temporada de 2026 — e gritou

> **Rodado em 27/09/2026**, 5,9 min. Protocolo em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), escrito antes.
> **Bloco descritivo**, pergunta binária: o alarme tocou ou não tocou.

---

## Em uma frase

**Em março de 2026 o modelo previu 1.808 casos para uma semana que teve ZERO.** Em 3 meses de
antecedência ele disparou alarme de Alerta em **10 das 17 semanas** do ano, e oito delas no patamar de
**Emergência** — num ano em que Porto Alegre teve **12 casos no total**.

🔴 **A direção declarada na pré-declaração estava ERRADA.** Eu escrevi que esperava poucos ou nenhum
alarme, com base nas 5 semanas de janeiro que já estavam na avaliação, onde o máximo previsto foi 173. A
pré-declaração previa essa possibilidade e mandava reportar como veio — é o que este documento faz.

---

## 1. O ano de 2026, para escala

| | |
|---|---|
| Semanas divulgadas | 17 (até 26/04/2026) |
| Casos no ano inteiro | **12** |
| Maior semana | **2 casos** |

Para comparar: 2025 teve **24.793** casos e um pico semanal de **2.381**.

---

## 2. Quantas semanas o alarme tocou

Limiar de **Alerta = 421** casos por semana, o piso do estágio Alerta do Plano Municipal.

| Horizonte | Semanas | Maior previsto | Mobilização (140) | **Alerta (421)** | Emergência (702) |
|---|---|---|---|---|---|
| **1 semana** | 6 | 64 | 0 | **0** ✅ | 0 |
| **1 mês** | 9 | 555 | 4 | **3** | 0 |
| **2 meses** | 13 | **1.808** | 7 | **4** | 4 |
| **3 meses** | 17 | 1.298 | 11 | **10** 🔴 | 8 |

E a régua sazonal, que repete 2025:

| Horizonte | Maior previsto | Alerta |
|---|---|---|
| 1 semana | 161 | 0 |
| 1 mês | 494 | 1 |
| 2 meses | 2.381 | 5 |
| 3 meses | 2.381 | 9 |

**Os dois falham, e em ordem parecida.** Em 3 meses o modelo dispara 10 contra 9 da régua — ou seja, ele
é **um pouco pior** que repetir o ano anterior.

---

## 3. Semana a semana, em 2 meses — o trecho que importa

| Semana-alvo | Real | Previsto | |
|---|---|---|---|
| 01/02/2026 | 1 | 173 | |
| 15/02/2026 | 1 | 146 | |
| 01/03/2026 | 1 | 298 | |
| **08/03/2026** | **0** | **822** | 🔴 ALARME |
| **15/03/2026** | **0** | **964** | 🔴 ALARME |
| **22/03/2026** | **0** | **1.808** | 🔴 ALARME |
| **29/03/2026** | **0** | **1.350** | 🔴 ALARME |

Em 3 meses o alarme fica **ligado de 22/02 a 26/04 sem interrupção** — dez semanas seguidas, com
previsões entre 667 e 1.298, contra um real que nunca passou de 2.

---

## 4. O que isso quer dizer

### O modelo aprendeu a sazonalidade, e ela não falhou — a epidemia é que não veio

As previsões sobem exatamente quando deveriam: fevereiro e março são o pico da temporada em Porto Alegre.
O modelo aprendeu o **calendário** e a **tendência de alta** da série (5.583 casos em 2022, 6.600 em 2023,
19.034 em 2024, 24.793 em 2025) e projetou a continuação.

**O que ele não tinha como saber é que a transmissão não ia acontecer.** As armadilhas continuaram
pegando mosquito em 2026; o que mudou foi algo que não está em nenhuma coluna do modelo — provavelmente
imunidade de população depois de duas epidemias grandes, ou ausência de sorotipo circulante.

### O erro cresce com o horizonte, e isso é coerente

- **1 semana: zero alarme falso.** Ali o histórico recente de casos manda, e ele dizia "quase nada".
- **2 e 3 meses: desastre.** Ali o modelo depende do calendário e do vetor, e os dois diziam "vai ter
  temporada".

É a mesma dependência medida em `analises/2026-09-26_importancia_na_folha_20/`: o vetor domina de h=3 a
h=11. Em 2026 essa dependência custou caro.

---

## 5. ⚠️ O que este bloco NÃO diz

- **Não mede erro, R² ou captura em 2026**, e nenhum desses números entra em slide ou documento. Prever
  12 casos a partir de uma série crescente é impossível, e o Vinicius tirou 2026 da avaliação em
  26/09/2026 por esse motivo. A pergunta aqui é outra: o alarme tocou?
- **Não diz que o método está errado.** Diz que ele não tem entrada para imunidade populacional nem para
  sorotipo circulante, e que sem isso ele projeta a continuação da tendência.
- **Não diz que a régua salvaria.** Ela dispara 9 vezes contra as 10 do modelo.

---

## 6. Limitações

- **Um ano.** 2026 é uma temporada, e é atípica por definição.
- **A contagem pode crescer.** Confirmações atrasadas do SINAN ainda podem subir os 12 casos. Com 0 a 2
  por semana, nenhuma revisão plausível chega perto de 421, então a conclusão binária não muda.
- **O corte de maturidade foi contornado**, como declarado no §4 da pré-declaração: ele continua valendo
  para features e treino, e só o gabarito vem da tabela crua.

---

## 7. Arquivos

| Arquivo | O que é |
|---|---|
| [`PRE_DECLARACAO.md`](PRE_DECLARACAO.md) | o protocolo, escrito antes |
| [`rodar.py`](rodar.py) | o script |
| `execucao.log` | a saída completa, semana a semana |
| `saidas/previsoes_de_2026.csv` | todas as previsões, modelo e régua |
| `saidas/alarmes_de_2026.csv` | a contagem do §2 |
