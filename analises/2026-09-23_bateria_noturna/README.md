# Dossiê da bateria noturna — 23 para 24/09/2026

> Rodada sem supervisão, das **20h41 de 23/09** às **03h08 de 24/09**, enquanto o Vinicius dormia.
> Pedido dele às 20h: *"fazer testagens de possibilidades que possam nos ajudar a chegar em melhores
> resultados dos modelos que já temos"*, sem mexer no site. Às ~20h50 ele acrescentou: *"aproveita pra
> botar um tunning de hiperparâmetros"*.
>
> Sete blocos planejados, seis rodados, um cancelado antes de rodar. Cada um tem pasta própria, com
> pré-declaração escrita **antes**, script, log, saídas e README. Este arquivo é o índice e a síntese.

---

## A noite em uma frase

**O resultado de que o vetor não melhora a previsão de casos era, com boa chance, efeito de um
hiperparâmetro herdado e nunca buscado.** Com a folha mínima da árvore em 20 em vez de 5, o vetor passa a
reduzir o erro de 3 meses em dois algoritmos diferentes, com significância — **mas quase todo o efeito vem
da temporada de 2024**, e duas temporadas não bastam para fechar a questão.

![Com folha mínima 20, o vetor passa a ajudar](bloco_7_vetor_com_folha_20/saidas/vetor_com_folha_20.png)

---

## Os achados, do mais importante ao menos

### 1. Com folha mínima 20, o vetor ajuda a prever 3 meses à frente

| Modelo | Queda do erro de h=12 com o vetor | p de Holm |
|---|---|---|
| HistGB, folha 5 — **cenário adotado** | +2,2% | não significativo |
| HistGB, folha 20 | **+12,3%** | **0,015** |
| LightGBM, folha 20 | **+15,5%** | **0,0001** |

Os dois modelos com folha 20 seguem praticamente a mesma curva nos 12 horizontes: o vetor atrapalha até
2 semanas e ajuda de 7 a 12. O modelo adotado fica abaixo de zero de 6 a 11. Conferido por
reimplementação estatística independente, duas vezes. → [blocos 5](bloco_5_algoritmos/) e
[7](bloco_7_vetor_com_folha_20/)

### 2. ⚠️ Esse efeito é carregado pela temporada de 2024

Separando a avaliação por ano, o vetor ajuda com p < 0,01 em **todos** os horizontes longos em 2024. Em
2025, só se repete com significância no LightGBM em 11 e 12 semanas; em 8 semanas, inverte nos dois
modelos. **O horizonte de 3 meses é o mais robusto**: mantém a direção nas duas temporadas.

**Hipótese:** 2024 foi a primeira epidemia gigante da série. Nada no histórico de casos a anunciava; a
densidade do vetor, sim. Em 2025 o modelo já tinha 2024 no treino. Se isso estiver certo, o vetor vale mais
quando a temporada foge do que já se viu — que é quando a vigilância mais precisa dele.

### 3. A partir de 1 mês, o modelo adotado já depende mais do vetor que do histórico de casos

Trocar as colunas do vetor por valores de outra semana aumenta o erro entre 46% e 73% de h=4 a h=11. Trocar
o histórico de casos, entre 20% e 47%. O modelo **usa** o vetor — só não consegue tirar dele um ganho sobre
o modelo sem vetor. → [bloco 3](bloco_3_importancia_por_bloco/)

### 4. O critério de escolha do projeto penaliza as configurações que usam o vetor

Todas as 9 configurações com folha 20 ficam ~30% piores na **calibração** (2020-2023) e ~11-17% melhores em
2 e 3 meses na **avaliação** (2024+). O erro extra da calibração mora em 2022 e 2023, as primeiras
epidemias, quando o treino quase não tinha semanas epidêmicas. Como o walk-forward é expansivo, escolher
pela calibração favorece sistematicamente quem precisa de pouco histórico epidêmico. → [bloco 6](bloco_6_hiperparametros/)

### 5. O único sinal positivo que o projeto tinha era vazamento

O ENSO, que derrubava o erro de h=8 em 7,1% em agosto, não muda nada no protocolo limpo e piora h=12 em
11,6%. → [bloco 2](bloco_2_features_longas/)

### 6. Mais memória não resolve o horizonte longo

Nem lags anuais, nem acúmulo de clima, nem lags mais longos do vetor. A informação que antecipa os casos já
está nas quatro semanas mais recentes do vetor. → [blocos 2](bloco_2_features_longas/) e
[4](bloco_4_lag_do_vetor/)

### 7. A referência não muda

Nenhuma variante passou no critério pré-declarado de troca. A busca de hiperparâmetros achou uma vencedora
só 0,9% melhor na calibração, que empata com a referência na avaliação. O LightGBM e o HistGB com folha 20
são **piores** no período que decide a escolha. Trocar por eles agora seria escolher pelo juiz.

---

## Como a noite chegou lá

A tarde de 23/09 terminou com uma pergunta aberta. O orientador tinha dito em 21/09 que o vetor não
impactar a previsão *"indica que deve ter algum problema na metodologia"*. O projeto tinha um resultado
negativo publicado sobre o vetor e nenhuma forma de saber se ele era dos dados ou do modelo.

| Hora | Bloco | Pergunta | Resposta | Levou a |
|---|---|---|---|---|
| 20h41 | 2 | O teste de agosto sobrevive sem vazamento? | Não; o ENSO era vazamento | — |
| 22h00 | 3 | O modelo **usa** o vetor? | Sim, mais que tudo, a partir de 1 mês | por que ele não ganha com isso? |
| 22h21 | 5 | Outro algoritmo **aproveita** o vetor? | O LightGBM, em 3 meses | é o algoritmo ou a folha 20 dele? |
| 23h51 | 4 | Mais memória do vetor ajuda? | Não | o gargalo não é a janela |
| 00h48 | 6 | Outros hiperparâmetros ajudam? | Não pelo teste; mas a folha 20 imita o LightGBM | a folha é o mecanismo? |
| 02h25 | 7 | Com folha 20, o vetor ajuda o HistGB? | **Sim**, em 2 e 3 meses | separar por ano: é 2024 |

O bloco 7 **não estava no plano original**. Foi pré-declarado às 02h30, depois de ler os blocos 5 e 6,
para separar algoritmo de hiperparâmetro — a confusão que o bloco 5 tinha deixado. Por ter nascido de
resultados já vistos, está marcado como exploratório.

---

## Os sete blocos

| Bloco | Pergunta | Tempo | Resultado |
|---|---|---|---|
| [1 · corte de maturidade](bloco_1_corte_de_maturidade_CANCELADO.md) | 12 semanas é o corte certo? | — | **cancelado**: o teste seria cego |
| [2 · features longas](bloco_2_features_longas/) | o teste de agosto sobrevive sem vazamento? | 1h19 | não; o ENSO era vazamento |
| [3 · importância por bloco](bloco_3_importancia_por_bloco/) | quanto o modelo depende de cada bloco? | 20 min | vetor domina de h=4 a h=11 |
| [4 · lag longo do vetor](bloco_4_lag_do_vetor/) | mais memória só para o vetor ajuda? | 57 min | não |
| [5 · algoritmos](bloco_5_algoritmos/) | outro algoritmo é melhor? o vetor ajuda algum? | 1h30 | LightGBM: vetor ajuda em 3 meses |
| [6 · hiperparâmetros](bloco_6_hiperparametros/) | outra configuração do HistGB é melhor? | 1h35 | não; a folha mínima divide tudo |
| [7 · vetor com folha 20](bloco_7_vetor_com_folha_20/) | com folha 20, o vetor ajuda o HistGB? | 43 min | sim, em 2 e 3 meses; carregado por 2024 |

### Por que o bloco 1 foi cancelado

O corte de maturidade apaga os casos das últimas N semanas, mas age **uma vez, no fim da série**. Para
qualquer previsão de 2024 ou da maior parte de 2025, o treino é idêntico com corte de 8 ou de 32 semanas. O
teste mostraria "sem diferença" sem ter como enxergar a diferença. Testar de verdade exige dados
**vintage**, com a contagem de casos como estava em cada semana antes de amadurecer.

---

## O que muda para a tese

- **O resultado negativo do vetor precisa ser reformulado.** Não é "o vetor não melhora a previsão". É "o
  vetor não melhora a previsão **do HistGB com folha mínima 5**", uma configuração herdada e nunca buscada.
- **A pergunta do orientador ganha uma candidata a resposta.** O "problema na metodologia" pode ser a folha
  mínima, somada a um critério de escolha que a favorece. Candidata forte, não diagnóstico fechado.
- **O eixo novo ganha sustentação.** Prever casos a partir do vetor deixa de ser aposta contra os dados. Há
  resultado a favor, exploratório, em 3 meses.
- **O valor do vetor pode estar nas temporadas atípicas.** Se a hipótese do achado 2 se confirmar, isso é um
  argumento de vigilância muito mais forte do que "melhora o erro médio".

---

## O que se pode e o que não se pode dizer amanhã

**Pode:**
- com folha mínima 20, em dois algoritmos, o vetor reduz o erro de 3 meses com significância após Holm,
  conferida por reimplementação independente;
- o efeito é dominado pela temporada de 2024;
- o modelo adotado depende mais do vetor que do histórico de casos de 1 a 3 meses à frente;
- o ganho do ENSO reportado em agosto não sobreviveu à correção do vazamento.

**Não pode:**
- que o vetor melhora a previsão, sem dizer "com folha mínima 20" e "sobretudo em 2024";
- que o LightGBM ou a folha 20 são melhores que o cenário adotado — são piores na calibração e em 1 semana;
- que é resultado confirmatório — os blocos 5, 6 e 7 foram lidos em sequência, na mesma avaliação;
- que 12 semanas é o corte de maturidade certo, nem que não é.

---

## O que fazer depois — propostas, não decisões

**Parar de olhar a avaliação 2024-2025.** Os blocos 5, 6 e 7 leram o mesmo período em sequência, e cada
leitura informou a seguinte. Mais uma busca ali seria procurar resultado no juiz.

**Próxima rodada confirmatória, a pré-declarar com calma:**
- hipótese: com folha mínima 20, o vetor reduz o erro de 3 meses;
- dado novo: a temporada **2026-2027**, que ninguém viu;
- desenho que evite o viés da calibração: um modelo por faixa de horizonte — folha 5 até 3 semanas, folha
  20 a partir de 4 — ou escolha numa janela posterior a 2022.

**Já atualizado nesta madrugada:** o `PENDENCIAS.md` — a rodada "validar o ENSO" ganhou lápide, o teste de
features longas saiu da lista de não refeitos, e entraram a rodada confirmatória acima e a necessidade de
dados vintage para o corte de maturidade.

**Depende do Vinicius:**
- Site e slides: **nada foi mexido**. A frase sobre o vetor no painel e no slide "O vetor" é a que precisa
  de reformulação, quando ele decidir.

---

## Método comum a todos os blocos

Todos usam o mesmo motor, [`harness.py`](harness.py): um walk-forward parametrizado, em vez de sete scripts
parecidos com sete chances de um erro sutil passar a noite despercebido.

- **Trava de validação.** Todo bloco roda a configuração de referência e confere se ela reproduz os oito
  números publicados no painel. Se não reproduzir, o bloco não reporta nada. **Passou nos seis.** O bloco 7
  teve uma segunda trava: reproduzir exatamente uma configuração já rodada no bloco 6. Passou.
- **Pareamento por `data_alvo`.** Braços diferentes perdem semanas diferentes — lags maiores comem o início
  da série, e a enchente de maio de 2024 deixou o vetor sem dado por 7 semanas. Só entram na comparação as
  semanas que os dois braços previram. No bloco 5, uma tabela sem pareamento chegou a produzir um número
  errado, detectado e corrigido antes de ser documentado.
- **Wilcoxon sobre o erro absoluto, Holm por família.** Cada bloco declarou a família antes de rodar.
- **Critério de troca fixo:** reduzir o erro em h=8 **e** h=12, os dois com p de Holm abaixo de 0,05.
- **Colunas reservadas.** Colunas novas entram por fora da seleção de clima. Conferido em cada bloco: todos
  os braços escolheram as mesmas seis colunas de clima.
- **Estatística conferida por reimplementação independente** nos dois blocos com resultado significativo,
  5 e 7, por um agente que não leu o código original. Os dois também passaram por teste t, teste de sinal e
  retirada das semanas extremas. A separação por temporada veio da segunda verificação.

---

## Arquivos

| Arquivo | O que é |
|---|---|
| [`harness.py`](harness.py) | o motor comum |
| [`orquestrar.sh`](orquestrar.sh) | roda os blocos 2 a 5 em sequência |
| [`depois_da_bateria.sh`](depois_da_bateria.sh) | espera a bateria e roda o bloco 6 |
| `log_mestre.txt` | horário de início e fim de cada bloco |
| `bloco_*/` | uma pasta por bloco, cada uma com README próprio |
