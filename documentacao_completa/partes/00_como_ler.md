# Parte 0 — Como ler este documento

## 0.1 Para quem este documento foi escrito

Para alguém que **não conhece este projeto** e que pode **não trabalhar com aprendizado de máquina nem com
epidemiologia**. Nenhum conceito é dado como sabido. Todo termo técnico é definido na primeira vez que
aparece, antes de ser usado, e toda sigla é apresentada por extenso antes de ser abreviada.

Se em algum ponto o texto usar um conceito sem tê-lo definido antes, isso é um defeito do documento, não
uma falha do leitor.

## 0.2 O que este documento é, e o que não é

**É** o registro completo do que foi construído, testado, medido e concluído na pesquisa de mestrado sobre
previsão de casos de dengue em Porto Alegre a partir da rede de armadilhas de mosquito, até **26/09/2026**.

**Não é** um artigo, uma proposta nem uma peça de convencimento. Resultados negativos aparecem com o mesmo
destaque que os positivos, e em alguns casos com mais, porque são a maioria do que foi encontrado.

## 0.3 A convenção de fato e hipótese

Esta é a convenção mais importante do documento, e ela é seguida sem exceção.

- **FATO** — algo que foi medido, com o número e a data da medição. Se está marcado como fato, existe um
  arquivo no repositório que o produziu e, na maioria dos casos, uma certificação independente que o
  conferiu.
- **HIPÓTESE** — uma explicação plausível que **não** foi testada. Pode estar certa. Não foi verificada.
- **⚠️ RESSALVA** — uma limitação que precisa acompanhar a afirmação sempre que ela for citada, inclusive
  fora deste documento.
- **🚫 DESCARTADO** — algo que foi deliberadamente abandonado, com a data e quem decidiu. Existe para que
  a ideia não volte meses depois sem que ninguém lembre por que caiu.

Quando a evidência não sustenta uma afirmação, o documento diz isso. Não há afirmação sem o número que a
sustenta.

## 0.4 Três avisos que mudam a leitura de tudo

Estes três pontos aparecem repetidamente ao longo do texto. Vale conhecê-los antes de começar.

### Aviso 1 — a série tem apenas duas epidemias

**FATO (medido em 26/09/2026).** No período avaliado, as semanas com número alto de casos formam
**exatamente dois blocos contíguos**: um em 2024 e outro em 2025. Isso vale para qualquer limiar testado.

A consequência é severa e atravessa o documento inteiro: quando se lê "39 semanas de surto", o número de
**eventos independentes** não é 39, é **2**. Dois blocos de cerca de vinte semanas cada. Todo teste
estatístico deste projeto que trate semana como observação independente produz um valor otimista, e isso
está quantificado na Parte 2 e na Parte 8.

### Aviso 2 — a régua mais difícil de bater é trivial

Ao longo do documento, os modelos são comparados contra **réguas**: regras simples, sem aprendizado,
usadas como linha de base. A mais importante é a **régua sazonal**, que responde apenas *"quantos casos
houve nesta mesma semana do ano passado?"*.

**FATO.** Em horizonte de dois e três meses, essa régua **vence** o modelo. Isso não é uma falha de
implementação: é o que acontece quando a sazonalidade carrega quase toda a informação disponível. A
Parte 6 mostra que o mesmo padrão aparece na literatura internacional.

### Aviso 3 — não existe pergunta de tese fechada

A pesquisa está em **fase exploratória**, assumidamente. Em 26/09/2026 o pesquisador registrou que não há
uma pergunta de tese definida e que muitas frentes estão sendo testadas para descobrir onde há resultado.

Isso muda como os resultados devem ser lidos: cada rodada responde ao **instrumento que ela testou** —
previsão do número de casos, alarme de surto, medida de risco, priorização espacial — e **não** funciona
como veredito sobre a pesquisa inteira. Um resultado negativo na previsão do número de casos não é "a tese
caindo".

## 0.5 Como o documento está organizado

| Parte | O que responde | Leia se você quer |
|---|---|---|
| **1** | Qual é o problema, e por que Porto Alegre é um caso diferente | entender o contexto |
| **2** | O que significa cada conceito, fórmula e métrica usados | **começar por aqui, se os termos forem novos** |
| **3** | De onde vêm os dados, o que eles têm e o que lhes falta | avaliar a base empírica |
| **4** | Todos os modelos e abordagens testados, um a um | saber o que já foi tentado |
| **5** | Todas as hipóteses, com veredito, e o método de trabalho | avaliar o rigor |
| **6** | O que a literatura obteve, e como nos comparamos | situar o resultado |
| **7** | Os limiares oficiais e por que usar o modelo como alarme | entender a escolha central |
| **8** | Os resultados, com tradução do que cada número significa | ver as evidências |
| **9** | Os argumentos defensáveis, as limitações e o que vem depois | preparar a discussão |
| **Anexos** | Glossário, índice de análises e todas as fórmulas | consultar pontualmente |

**A Parte 2 é pré-requisito das Partes 6 a 9.** Quem pular os conceitos vai encontrar números sem saber o
que eles medem — e alguns deles, em particular o valor-p e a cobertura de intervalo, são exatamente os que
mais se prestam a interpretação errada.

## 0.6 Onde cada número deste documento foi produzido

Cada resultado citado vem de uma pasta datada no repositório, no formato
`analises/AAAA-MM-DD_descricao/`, e cada uma contém:

- uma **pré-declaração** escrita **antes** da execução, com a hipótese, a métrica, o critério de decisão e
  a família de correção estatística;
- o **código** que produziu o resultado e o registro da execução;
- uma **certificação** feita por um avaliador independente, cuja tarefa era tentar reprovar o resultado
  medindo do zero;
- as **emendas** datadas, quando algo mudou depois da pré-declaração.

O índice completo dessas pastas está no Anexo B. Esse método é, ele próprio, parte do que a pesquisa tem a
mostrar, e está descrito na Parte 5.

## 0.7 Uma nota sobre a linguagem

O documento evita adjetivos de propaganda. Não há "resultado robusto", "modelo poderoso" nem "abordagem
inovadora". Onde um resultado é forte, o número é apresentado e o leitor julga. Onde é fraco, o texto diz
que é fraco.

Também são evitadas **duplas negações** e construções que exigem reler para entender de que lado está a
afirmação. Quando o assunto é a ausência de um efeito, o texto diz diretamente o que foi medido e o que
não foi demonstrado.
