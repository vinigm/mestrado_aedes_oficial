# Pré-declaração — limiar de decisão, estágios oficiais e a inflação do p

> **Escrita em 26/09/2026, antes de qualquer número novo ser calculado.** Autorizada pelo Vinicius em
> 26/09/2026 ("pode rodar alguma coisa se precisar"). Mudança posterior vira **emenda datada** no fim.
>
> Nenhum modelo é treinado. Tudo é recálculo sobre **previsões já salvas** da bateria de 23/09
> (`previsoes_por_braco.csv`), que rodou na tabela **sem 2026** — a mesma que está oficial hoje.

---

## 0. ⚠️ Escolha que o Vinicius fixa ANTES de rodar

O evento principal está declarado como **E_140** (piso de Mobilização do plano municipal). Se ele preferir
**E_421** (piso de Alerta), isto muda **antes** da execução e vira emenda. Depois de rodar, não muda.

- **Por que E_140 como principal:** difere de E_100 em **1 semana de 121**, então preserva a comparação com
  tudo que já foi medido, e ganha dono institucional.
- **Por que E_421 seria defensável:** "Alerta" é semanticamente mais próximo de surto, e o evento é mais raro
  (28 contra 38 semanas), o que o torna mais informativo.

---

## 1. O achado que motiva a rodada

No `rodar.py` de 25/09, linha 565, o alarme do modelo é:

```python
alarme_m_adotado = tabela["previsto_M_adotado"] > definicao_evento.limite_alvo
```

- **O limiar de DECISÃO está colado no limiar do EVENTO.** São coisas diferentes:
  - **evento** = a semana real passou de T casos. É definição do problema.
  - **decisão** = a previsão passou de D. É um parâmetro livre, e nunca foi ajustado.
- A previsão é o **quantil 0,85**. Vale a equivalência exata: alarmar quando `q̂₀,₈₅ > D` é o mesmo que alarmar
  quando `P̂(casos > D) > 15%`. O alarme atual **já é** um classificador probabilístico com corte implícito de
  15%, herdado do q0,85 sem que ninguém tenha decidido isso.

---

## 2. As quatro partes

### A. Varredura do limiar de decisão — **DESCRITIVA**

- Para cada modelo (`M_adotado`, `M_folha20`) e cada horizonte **h ∈ {1, 4, 8, 12}**, varrer
  **D ∈ {25, 50, 75, 100, 140, 200, 300, 421, 600, 702, 900, 1200}**, com o evento fixo em T.
- Saída: sensibilidade, especificidade, precisão, falsos por ano e Youden, por (modelo, h, D). Mais a figura
  da curva sensibilidade × falsos por ano.
- **Previsão declarada, que pode falhar:** como o q0,85 superestima por desenho, o **D de melhor Youden deve
  ficar ACIMA de T**. Se ficar abaixo, a leitura de que o modelo superestima está errada em algum ponto.
- 🚫 **Não é permitido** escolher o melhor D e apresentá-lo como resultado. A varredura produz **curva**, não
  vencedor. Um D escolhido aqui só pode virar resultado em rodada confirmatória futura, em temporada nova.

### B. Os estágios oficiais como evento

- Acrescentar `E_140`, `E_421` e `E_702` à estrutura existente, **sem abrir família nova de Holm**.
- **`E_140`: confirmatório**, somado à família já aberta em 25/09 — McNemar pareado, h=4 e h=12,
  `M_adotado` e `M_folha20` contra `R_hoje` e `R_ano_passado`. **8 testes novos.**
- **`E_421` e `E_702`: descritivos**, sempre, sem p-valor de veredito. Motivo: são o mesmo corte deslizante
  sobre os mesmos **2 blocos** (ver C), e o aninhamento é aritmético.
- **Critério de decisão para `E_140`:** o modelo só conta como ganho se vencer **`R_ano_passado`** em Youden
  com p Holm < 0,05. Vencer só o `R_hoje` não conta — isso já foi mostrado em 25/09.
- **Compromisso declarado:** o resultado é publicado mesmo se repetir a derrota de 3 meses para a régua
  sazonal (Youden 0,81 dela contra 0,66 do adotado em `E_100`).

### C. A inflação do p — **o item que precede os outros dois**

**Fato medido em 26/09:** as semanas acima de qualquer limiar formam **exatamente 2 blocos contíguos**, um em
2024 e outro em 2025.

| Limiar | Semanas | Blocos | Maior bloco |
|---|---|---|---|
| 100 | 39 | **2** | 20 |
| 140 | 38 | **2** | 20 |
| 421 | 28 | **2** | 14 |
| 702 | 23 | **2** | 12 |

- **O problema:** o McNemar trata cada semana como par independente. Semanas dentro do mesmo bloco são
  fortemente correlacionadas, então o p nominal é **otimista**.
- **A medição:** *moving block bootstrap* sobre os pares discordantes, com comprimento de bloco
  **L ∈ {4, 8, 13, 26}** semanas, **2.000 reamostragens**, semente **20260926**.
- **Saída:** a razão `p_bootstrap / p_nominal` para cada teste, incluindo **o p Holm 0,037 de 13/09**, que é o
  único resultado do projeto que sobrevive a Holm.
- **Como será reportado:** a razão é **descritiva**, uma ordem de grandeza da inflação, não um p novo
  oficial. Se a razão for maior que 3 em qualquer teste-chave, isso vira aviso obrigatório em toda citação.

### D. Trava de validação — roda ANTES de qualquer resultado ser lido

O `M_adotado` em `E_100`, avaliação 2024+, tem de reproduzir os números de 25/09:

| h | Sensibilidade | Precisão | Falsos/ano |
|---|---|---|---|
| 4 | 0,971 | 0,943 | 0,7 |
| 12 | 0,769 | 0,811 | 2,3 |

Tolerância **0,002** nas proporções e **0,05** em falsos por ano. Se não bater, a rodada para e a diferença é
explicada antes de seguir.

---

## 3. O que é confirmatório e o que é descritivo

| Parte | Estatuto |
|---|---|
| B, `E_140` contra `R_ano_passado` e `R_hoje` | **confirmatório**, 8 testes, Holm sobre a família de 25/09 |
| A, varredura de D | descritiva |
| B, `E_421` e `E_702` | descritivas |
| C, inflação do p | descritiva, mas **condiciona a leitura de tudo** |

---

## 4. Ameaças, sem suavizar

- 🔴 **N efetivo é 2, não 121.** Só há 2 episódios epidêmicos. Toda métrica de alarme descreve 2 curvas.
- 🔴 **Risco de pesca:** varrer D e escolher o melhor seria p-hacking. A defesa é o estatuto descritivo da
  parte A, declarado aqui, antes de rodar.
- ⚠️ **O evento de 140 ocorre em 31% das semanas.** Isso é regime sazonal, não anomalia. Youden alto pode ser
  o modelo aprendendo o calendário, e não detectando surto.
- ⚠️ **Aninhamento é aritmético:** toda semana acima de 702 está acima de 421 e de 140. Os estágios não são
  eventos independentes.
- ⚠️ **140, 421 e 702 são só a metade fixa do critério do plano.** O Quadro 1 liga cada um por **E** ao
  Limite de Alerta ou ao Limite Superior Endêmico, que são curvas do RS sobre casos prováveis, e que não
  temos. Mais óbito e sorotipo novo, que o modelo não prevê. **Toda citação diz "simplificação declarada"**,
  nunca "critério oficial".
- ⚠️ **As previsões vêm do q0,85**, que não é calibrado: o intervalo de 50% cobre 14% das semanas. Por isso a
  leitura probabilística da seção 1 é **estrutural**, e não autoriza dizer "há X% de chance de surto".

---

## 5. Custo

Recálculo sobre CSV já salvo, sem treinar modelo. Estimativa: **minutos**. O *bootstrap* de 2.000
reamostragens sobre pares discordantes é a parte mais cara, e ainda assim é segundos por teste.

---

## 6. Certificação

Reimplementação independente por agente que tente **reprovar**, medindo do zero: a contagem de blocos, a
trava, pelo menos uma célula da varredura e pelo menos um p de *bootstrap*.

---

## Emendas

- *(nenhuma até agora)*
