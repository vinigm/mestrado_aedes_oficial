# Dossiê da bateria noturna — 23 para 24/09/2026

> Rodada sem supervisão, das **20h41 de 23/09** às **~03h de 24/09**, enquanto o Vinicius dormia.
> Pedido dele às 20h: *"fazer testagens de possibilidades que possam nos ajudar a chegar em melhores
> resultados dos modelos que já temos"*, sem mexer no site.
>
> Cada bloco tem pasta própria, com pré-declaração escrita **antes** de rodar, script, log, saídas e README.
> Este arquivo é o índice e a síntese.

---

## A noite em cinco achados

1. **O resultado "o vetor não melhora a previsão" depende do algoritmo.** No HistGB do cenário adotado ele
   se confirma. No **LightGBM**, o vetor reduz o erro de 3 meses em **15,5%**, com p de Holm **0,0001**,
   robusto a três testes diferentes e à retirada das semanas extremas. → [bloco 5](bloco_5_algoritmos/)

2. **A partir de 4 semanas à frente, o modelo depende mais do vetor do que do histórico de casos.**
   Trocar o vetor por valores de outra semana aumenta o erro entre 46% e 73% de h=4 a h=11. →
   [bloco 3](bloco_3_importancia_por_bloco/)

3. **O único sinal positivo que o projeto tinha era vazamento.** O ENSO, que derrubava o erro de h=8 em
   7,1% em agosto, não muda nada no protocolo limpo e piora h=12 em 11,6%. →
   [bloco 2](bloco_2_features_longas/)

4. **Dar mais memória ao modelo não resolve o horizonte longo** — nem memória anual, nem acúmulo de clima,
   nem lags mais longos do vetor. O que limita o HistGB não é quanto passado ele vê. →
   [blocos 2](bloco_2_features_longas/) e [4](bloco_4_lag_do_vetor/)

5. **Nada troca a referência.** O LightGBM é melhor em 2024-2025, mas é o **pior** dos três algoritmos no
   período que decide a escolha. Trocar agora seria escolher pelo juiz. → [bloco 5](bloco_5_algoritmos/)

---

## O fio que atravessou a noite

A tarde de 23/09 terminou com uma pergunta aberta. O orientador tinha dito, em 21/09, que o vetor não
impactar a previsão *"indica que deve ter algum problema na metodologia"*. O projeto tinha um resultado
negativo publicado sobre o vetor, e nenhuma forma de saber se ele era dos dados ou do modelo.

A noite atacou isso por três lados:

| Lado | Pergunta | Bloco | Resposta |
|---|---|---|---|
| O modelo **usa** o vetor? | Quanto ele depende de cada bloco? | 3 | **Sim**, mais que de tudo, a partir de 4 semanas |
| O modelo **precisa** de mais do vetor? | Mais memória do vetor ajuda? | 4 | **Não** |
| Outro modelo **aproveita** o vetor? | Tirar o vetor piora outro algoritmo? | 5 | **Sim**: o LightGBM, em 3 meses |

A leitura que junta os três: **o vetor carrega informação que antecipa os casos, e essa informação já
está nas quatro semanas mais recentes dele. O HistGB, com os hiperparâmetros atuais, não a aproveita. O
LightGBM aproveita.** O [bloco 6](bloco_6_hiperparametros/) testa se o que separa os dois é a
regularização.

---

## Os seis blocos

| Bloco | Pergunta | Tempo | Resultado |
|---|---|---|---|
| [1 · corte de maturidade](bloco_1_corte_de_maturidade_CANCELADO.md) | 12 semanas é o corte certo? | — | **cancelado antes de rodar**: o teste seria cego |
| [2 · features longas](bloco_2_features_longas/) | o teste de agosto sobrevive sem vazamento? | 1h19 | não; o ENSO de agosto era vazamento |
| [3 · importância por bloco](bloco_3_importancia_por_bloco/) | quanto o modelo depende de cada bloco? | 20 min | vetor domina de h=4 a h=11 |
| [4 · lag longo do vetor](bloco_4_lag_do_vetor/) | mais memória só para o vetor ajuda? | 57 min | não |
| [5 · algoritmos](bloco_5_algoritmos/) | outro algoritmo é melhor? o vetor ajuda algum? | 1h30 | LightGBM: vetor ajuda em 3 meses, p 0,0001 |
| [6 · hiperparâmetros](bloco_6_hiperparametros/) | outra configuração do HistGB é melhor? | ⏳ | ⏳ em execução |

### Bloco 1 — por que foi cancelado

O corte de maturidade apaga os casos das últimas N semanas, contadas da última semana com caso. Mas ele
age **uma vez, no fim da série**. Para qualquer previsão de 2024 ou da maior parte de 2025, o treino é
idêntico com corte de 8 ou de 32 semanas — o corte nem chega lá. O teste mostraria "sem diferença" sem
ter como enxergar a diferença, e uma conclusão falsa de "12 está bom" seria pior do que nenhuma. Testar de
verdade exige dados **vintage**, com a contagem de casos como ela estava em cada semana.

---

## O que muda para a tese

- **O resultado negativo do vetor precisa ser reformulado.** "O vetor não melhora a previsão" passa a ser
  "o vetor não melhora a previsão **do HistGB**". Com outro algoritmo, melhora, e no horizonte que a tese
  quer.
- **A tese ganha um argumento que não tinha.** O modelo adotado já se apoia no vetor mais do que em
  qualquer outra coisa a partir de 1 mês. É evidência medida, pelo procedimento publicado, contra a
  leitura "o mosquito não importa".
- **O eixo do orientador fica mais sustentável.** Prever casos a partir da proliferação do vetor deixa de
  ser uma aposta contra os dados e passa a ter um resultado a favor, ainda que exploratório.
- ⚠️ **Nada disso é confirmatório ainda.** O LightGBM não foi escolhido antes de olhar. A confirmação
  honesta é uma rodada pré-declarada com o LightGBM como hipótese — e, idealmente, a temporada 2026-2027,
  que ninguém viu.

---

## O que muda no `PENDENCIAS.md`

- 🚫 **"Validar o ENSO dentro do grid" perde a base.** O "+7% em h=8" que a sustentava era vazamento.
- ✅ **O teste de features longas de 30/08 foi refeito.** Sai da lista de não refeitos.
- ⏳ **Rodada nova candidata:** LightGBM como hipótese pré-declarada, com e sem vetor.
- ⏳ **Rodada nova candidata:** o corte de maturidade só é testável com dados vintage.

---

## O que se pode e o que não se pode dizer amanhã

**Pode:**
- no LightGBM, o vetor reduz o erro de 3 meses em 15,5%, p de Holm 0,0001, verificado por reimplementação
  independente;
- o modelo adotado depende mais do vetor que do histórico de casos de 1 a 3 meses à frente;
- o ganho do ENSO reportado em agosto não sobreviveu à correção do vazamento.

**Não pode:**
- que o vetor melhora a previsão, sem dizer "no LightGBM";
- que o LightGBM é melhor que o HistGB — ele é pior na calibração;
- que 12 semanas é o corte de maturidade certo, nem que não é.

---

## Método comum a todos os blocos

Todos usam o mesmo motor, [`harness.py`](harness.py): um walk-forward parametrizado, em vez de seis
scripts parecidos com seis chances de um erro sutil passar a noite despercebido.

- **Trava de validação.** Todo bloco roda a configuração de referência e confere se ela reproduz os oito
  números publicados no painel. Se não reproduzir, o bloco não reporta nada. **Passou nos cinco.**
- **Pareamento por `data_alvo`.** Braços diferentes perdem semanas diferentes — lags maiores comem o
  início da série, e a enchente de maio de 2024 deixou o vetor sem dado por 7 semanas. Só entram na
  comparação as semanas que os dois braços previram. Numa das tabelas do bloco 5, comparar sem parear
  chegou a produzir um número errado, detectado e corrigido antes de ser documentado.
- **Wilcoxon sobre o erro absoluto, Holm por família.** Cada bloco declarou a família antes de rodar.
- **Critério de decisão fixo:** uma variante só troca a referência se reduzir o erro em h=8 **e** h=12,
  os dois com p de Holm abaixo de 0,05. É o critério de agosto, mantido para os testes serem comparáveis.
- **Colunas reservadas.** Colunas novas entram por fora da seleção de clima, em todos os braços. Conferido
  em cada bloco: todos os braços escolheram as mesmas seis colunas de clima.

---

## Arquivos

| Arquivo | O que é |
|---|---|
| [`harness.py`](harness.py) | o motor comum |
| [`orquestrar.sh`](orquestrar.sh) | roda os blocos 2 a 5 em sequência |
| [`depois_da_bateria.sh`](depois_da_bateria.sh) | espera a bateria e roda o bloco 6 |
| `log_mestre.txt` | horário de início e fim de cada bloco |
| `bloco_*/` | uma pasta por bloco, cada uma com README próprio |
