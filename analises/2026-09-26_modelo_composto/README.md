# Modelo composto: folha 5 no curto, folha 20 no longo

> **26/09/2026.** Pergunta do Vinicius: as duas configurações têm forças opostas — e se cada horizonte
> usasse a que vai melhor nele?
>
> ⚠️ **DESCRITIVO E POSTERIOR AOS FATOS.** Nenhum modelo foi treinado: é recombinação de previsões já
> salvas da bateria de 23-24/09/2026. Nenhum teste de hipótese, nenhum valor-p.
> Reprodutível com [`calcular.py`](calcular.py).

---

## O que é "folha", em uma frase

**Folha mínima** (`min_samples_leaf`) é o número mínimo de semanas que precisa cair em cada folha da
árvore de decisão para ela poder existir.

- **Folha 5:** a árvore pode criar um ramo que atende apenas 5 semanas. Fica detalhista, e acompanha bem
  o passado recente.
- **Folha 20:** todo ramo precisa valer para pelo menos 20 semanas. A árvore fica grosseira, e é obrigada
  a encontrar padrões que se repetem.

É essa diferença que explica o resto deste documento: **o detalhe ajuda a prever a semana que vem; o
padrão ajuda a prever daqui a três meses.**

---

## 1. O painel dos quatro braços

Avaliação de **2024 em diante**, **102 semanas** por horizonte, pareadas por data-alvo.
Em negrito, o melhor de cada coluna.

### Erro absoluto médio, em casos por semana — menor é melhor

| Horizonte | Adotado (folha 5) | Folha 20, com vetor | **Composto** | Régua sazonal |
|---|---|---|---|---|
| 1 semana | **98,0** | 133,6 | **98,0** | 202,1 |
| 1 mês | 219,7 | 199,6 | **199,6** | 213,2 |
| 2 meses | 272,6 | 223,2 | 223,2 | **216,2** |
| 3 meses | 278,8 | 243,8 | 243,8 | **217,8** |

### Coeficiente de determinação — maior é melhor

| Horizonte | Adotado | Folha 20 | **Composto** | Régua sazonal |
|---|---|---|---|---|
| 1 semana | **0,898** | 0,834 | **0,898** | 0,633 |
| 1 mês | 0,628 | 0,717 | **0,717** | 0,623 |
| 2 meses | 0,450 | 0,576 | 0,576 | **0,618** |
| 3 meses | 0,437 | 0,558 | 0,558 | **0,616** |

### Captura do pico — maior é melhor

Razão entre a média prevista e a média real nas semanas acima de 100 casos.

| Horizonte | Adotado | Folha 20 | **Composto** | Régua sazonal |
|---|---|---|---|---|
| 1 semana | 0,886 | **0,938** | 0,886 | 0,567 |
| 1 mês | 0,702 | **0,706** | **0,706** | 0,569 |
| 2 meses | 0,417 | **0,510** | **0,510** | 0,575 |
| 3 meses | 0,388 | 0,504 | 0,504 | **0,574** |

---

## 2. O que o composto muda

- ✅ **Ele passa a vencer a régua sazonal em 1 mês**, o que o modelo adotado não faz: **199,6** contra
  **213,2**. O adotado perdia, com 219,7.
- ✅ **A subestimação do pico melhora muito em horizonte longo.** Em 3 meses, a captura sobe de
  **38,8%** para **50,4%**. Traduzindo: numa semana com 917 casos reais, a previsão típica sai de cerca
  de 356 para cerca de 462.
- ✅ **O coeficiente de determinação em 3 meses vai de 0,437 para 0,558.**
- ✅ **Em 1 semana não perde nada**, porque ali o composto é o próprio modelo adotado.
- 🔴 **Em 2 e 3 meses a régua sazonal continua vencendo** no erro. A distância cai bastante — de 28% para
  **12%** em 3 meses —, mas não fecha.

### Um dado que incomoda, e precisa ser dito

**O coeficiente de determinação da régua sazonal é maior que o de qualquer modelo em 2 e 3 meses**
(0,618 e 0,616). Repetir o ano anterior explica mais da variação dos casos, nesses horizontes, do que
qualquer coisa que treinamos.

---

## 3. 🔴 Por que isto NÃO é adotável como está

**O ponto de corte foi escolhido olhando o período de avaliação.** Vimos que a folha 5 ganha até 3 semanas
e a folha 20 de 4 em diante, e cortamos ali. O mesmo período que serve de juiz não pode escolher o
competidor.

É exatamente o erro que a regra do projeto evita desde agosto, quando o quantil 0,80 foi mantido mesmo com
o 0,85 melhor na avaliação.

**O caminho limpo, se a ideia for adiante:**

1. pré-declarar que a configuração pode variar por horizonte;
2. declarar **antes** como o ponto de corte será escolhido — por exemplo, pelo período de calibração, ou
   por validação aninhada;
3. re-rodar o grid sob esse critério;
4. julgar na temporada seguinte.

Enquanto isso não for feito, os números acima são **ilustração do que um composto renderia**, e não
resultado adotável.

---

## 4. Por que a folha 20 nunca foi adotada

Não foi descuido. A configuração é escolhida pelo menor erro no período de **calibração**, 2020-2023, e
ali a folha 20 é cerca de **30% pior**.

⚠️ **E aqui há um achado metodológico:** o erro extra da folha 20 na calibração mora em **2022 e 2023**,
as primeiras epidemias, quando o treino ainda quase não tinha semanas epidêmicas. Como o walk-forward é
expansivo, **escolher pela calibração favorece sistematicamente quem precisa de pouco histórico
epidêmico** — ou seja, penaliza justamente as configurações que usam o vetor.

O critério de seleção do projeto estava escondendo o valor da armadilha.

---

## 5. A régua sazonal, definida sem ambiguidade

A régua responde uma pergunta só: **"quantos casos houve nesta mesma semana, no ano passado?"**

- É uma previsão **numérica**, não uma afirmação de tendência. Não é "em janeiro vai subir": é "haverá
  exatamente *n* casos".
- 🔴 **Ela não usa o mosquito nem o clima.** Só o próprio histórico de casos. É uma régua que ignora
  completamente a rede de armadilhas — e ainda assim erra menos que o modelo adotado em 2 e 3 meses.

---

## 6. Arquivos

| Arquivo | O que é |
|---|---|
| [`calcular.py`](calcular.py) · `execucao.log` | o script e a saída |
| `saidas/painel_do_composto.csv` | as três métricas, por braço e horizonte |

**Entrada:** `../2026-09-23_bateria_noturna/bloco_7_vetor_com_folha_20/saidas/previsoes_por_braco.csv`.

⚠️ **Uma armadilha do arquivo de entrada, registrada para quem vier depois:** ele cobre de **2020** em
diante, e o painel do projeto é medido **só de 2024**. Sem o recorte, o erro de 1 semana dá **48,5** em vez
dos **98,0** publicados, porque 2020-2023 são anos quase sem casos e puxam a média para baixo. A primeira
versão deste script caiu nessa armadilha.
