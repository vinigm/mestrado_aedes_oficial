# Teste decisivo dos alvos — 30/08/2026

> Regras em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), escritas antes de rodar.

## A pergunta

Em 29/08 os dois alvos deram respostas opostas sobre o vetor ajudar a detectar surto. Mas os dois
experimentos diferiam em **duas** coisas, não uma: o alvo **e** a qualidade da medição do vetor
(45,8% das semanas do braço de notificados usam denominador aproximado, contra ~0% no de
confirmados). Não dava para atribuir a diferença ao alvo.

**Aqui os dois alvos rodam sobre exatamente as mesmas 379 semanas** (30/12/2018 a 26/04/2026),
todas com denominador exato. Sobra uma única diferença: o alvo.

## Resultado

| alvo | pctl | h | n | clima>vetor | vetor>clima | p bruto | Holm(6) | Holm(12) |
|---|---|---|---|---|---|---|---|---|
| confirmados | 90 | 4 | 251 | 7 | 9 | 0,804 | 1,000 | 1,000 |
| confirmados | 90 | 8 | 246 | 5 | **15** | **0,041** | 0,248 | 0,455 |
| confirmados | 90 | 12 | 242 | 9 | **16** | 0,230 | 1,000 | 1,000 |
| confirmados | 95 | 4 | 251 | 5 | 7 | 0,774 | 1,000 | 1,000 |
| confirmados | 95 | 8 | 246 | **11** | 9 | 0,824 | 1,000 | 1,000 |
| confirmados | 95 | 12 | 242 | 5 | **10** | 0,302 | 1,000 | 1,000 |
| notificados | 90 | 4 | 251 | **11** | 7 | 0,481 | 1,000 | 1,000 |
| notificados | 90 | 8 | 246 | **8** | 4 | 0,388 | 1,000 | 1,000 |
| notificados | 90 | 12 | 242 | 5 | **11** | 0,210 | 1,000 | 1,000 |
| notificados | 95 | 4 | 251 | 10 | **15** | 0,424 | 1,000 | 1,000 |
| notificados | 95 | 8 | 246 | 9 | **14** | 0,405 | 1,000 | 1,000 |
| notificados | 95 | 12 | 242 | 3 | **16** | **0,0044** | **0,027** ✅ | **0,053** ❌ |

## As quatro conclusões

### 1. ✅ O confundimento era real — e minha conclusão de 29/08 estava errada

Com a janela equalizada, **os dois braços passam a favorecer o vetor**:

- confirmados: **5 de 6** comparações;
- notificados: **4 de 6** — contra **1 de 6** quando a série incluía 2012–2018.

**O "o vetor não ajuda, e inverte" de 29/08 era artefato do meu erro de desenho**, não achado.
Alimentei o modelo com vetor degradado em quase metade da amostra e li o ruído como resultado.

### 2. ❌ Mas nada sobrevive à correção múltipla

O melhor caso é notificados P95 h=12: p bruto **0,0044**, Holm dentro do braço **0,027** (passaria),
mas Holm no conjunto de 12 dá **0,053** — perde por um fio.

Como a pergunta é a mesma nos dois braços, o conjunto de 12 é o correto. **Veredito: não significativo.**

### 3. 🚨 O resultado forte de 29/08 (p=0,00018) evaporou

Aquele P90 h=12 dos confirmados, que sobrevivia a Holm com 0,00108, era **9×16 (p=0,230)** aqui.

A diferença entre as duas execuções são só as **37 semanas de fev–dez/2018** que a recaptura do
clima liberou. Um resultado que sai de p=0,0002 para p=0,23 ao remover 37 de 279 semanas é
**frágil** — cai na regra de decisão 3 da pré-declaração.

### 4. 📌 Padrão descritivo, sem teste

O vetor é favorecido em **9 das 12** comparações, e a vantagem se concentra nos **horizontes longos**
(h=8 e h=12); em h=4 é mista. Coerente com a biologia: a densidade de mosquito é indicador
**antecedente** — larva → adulto → picada → infecção → sintoma → notificação leva semanas.

> ⚠️ **Isto é descrição, não inferência.** Não calculo p-valor para "9 de 12": não foi pré-declarado
> e as comparações compartilham dados. Serve para desenhar o **próximo** teste, não para concluir.

## Tensão honesta com a Rodada 2

Na Rodada 2 (equivalência, regressão do **número** de casos) o vetor era melhor em horizonte
**curto** e pior em longo. Aqui, na **detecção de surto**, é o contrário. São tarefas diferentes
— prever quantidade × detectar evento — e não vou forçá-las na mesma narrativa. **Fica registrado
como divergência em aberto.**
