# Transformação de escala do alvo — 26/09/2026

Pré-declaração: [`PRE_DECLARACAO.md`](PRE_DECLARACAO.md). Script: [`rodar.py`](rodar.py). Log: [`execucao.log`](execucao.log).

## Trava

B0 (q0,85) contra o painel publicado, tolerância 0,2:

| h | MAE certificado | Painel publicado | Status |
|---|---|---|---|
| 1 | 97,99 | 98,0 | ok |
| 4 | 219,67 | 219,7 | ok |
| 8 | 272,63 | 272,6 | ok |
| 12 | 278,82 | 278,7 | ok |

**VÁLIDA.** Os números do B0 vêm do log já certificado de
`../2026-09-26_wis_na_tabela_restaurada/execucao.log` — o quantil 0,85 do B0 nunca foi salvo em CSV
(descartado pelo próprio script de origem antes de gravar `previsoes_quantis.csv`), e o B0 não foi
re-rodado aqui. Ver `rodar.py`, desvio 1, para o detalhe.

## Veredito — critério duplo (seção 5)

| Braço | Cobertura ic90% Alerta (>421) | Critério 1 (≥50%) | MAE h=12 | Critério 2 (≤306,7) | **Veredito** |
|---|---|---|---|---|---|
| B0 (referência) | 17,8% | — | 278,8 | — | controle |
| **T_raiz** | 15,9% | ❌ | 289,2 | ✅ | **NEGATIVO** |
| **T_log** | 13,5% | ❌ | 299,0 | ✅ | **NEGATIVO** |

- **T_raiz**: piora o erro pontual em até 10% (dentro do teto), mas a cobertura no Alerta **piorou** frente
  ao B0 (15,9% < 17,8%), em vez de melhorar — falha o critério 1, veredito **NEGATIVO**.
- **T_log**: mesmo padrão, com queda maior de cobertura (13,5%) e erro pontual pior em h=12 (+7,3%) — falha
  o critério 1, veredito **NEGATIVO**.
- Como a regra da seção 5 é clara — "se só (1) valer, o resultado é NEGATIVO" —, aqui nem (1) vale: **nenhum
  dos dois braços melhora a cobertura no Alerta**, então o veredito é negativo por não sobrar nenhum
  critério a favor, não por um trade-off.

## MAE por horizonte (q0,85), janela 2024-01-01 a 2026-02-01, n=102

| Braço | h=1 | h=4 | h=8 | h=12 |
|---|---|---|---|---|
| B0 | 98,0 | 219,7 | 272,6 | 278,8 |
| T_raiz | 103,2 (+5,3%) | 205,0 (−6,7%) | 278,0 (+2,0%) | 289,2 (+3,7%) |
| T_log | 114,5 (+16,8%) | 212,9 (−3,1%) | 284,6 (+4,4%) | 299,0 (+7,3%) |

Os dois braços melhoram o MAE em h=4 e pioram nos demais horizontes — h=1 é o mais afetado, especialmente
o T_log (+16,8%, fora do teto de 10% se a regra fosse aplicada a esse horizonte, mas o critério
pré-declarado só olha h=12).

## Cobertura por faixa — os 7 quantis do WIS, série completa (2020-2026), 4 horizontes agrupados

Mesma metodologia de `../2026-09-26_calibracao_por_faixa/diagnosticar.py` (ver desvio 3 em `rodar.py`).

| Braço | Faixa | Semanas | Cobertura IC50 | Cobertura IC90 |
|---|---|---|---|---|
| B0 | 1. calmaria (0-20) | 814 | 59,2% | 90,5% |
| T_raiz | 1. calmaria (0-20) | 814 | 51,6% | 84,2% |
| T_log | 1. calmaria (0-20) | 814 | 51,2% | 80,5% |
| B0 | 2. subida (21-140) | 110 | 18,2% | 63,6% |
| T_raiz | 2. subida (21-140) | 110 | 14,5% | 55,5% |
| T_log | 2. subida (21-140) | 110 | 16,4% | 48,2% |
| B0 | 3. Mobilização (141-421) | 72 | 27,8% | 47,2% |
| T_raiz | 3. Mobilização (141-421) | 72 | 15,3% | 43,1% |
| T_log | 3. Mobilização (141-421) | 72 | 15,3% | 33,3% |
| B0 | 4. Alerta ou mais (>421) | 163 | 8,0% | 17,8% |
| T_raiz | 4. Alerta ou mais (>421) | 163 | 6,7% | 15,9% |
| T_log | 4. Alerta ou mais (>421) | 163 | 3,7% | 13,5% |

**Achado principal, mais forte que o risco pré-declarado**: a ameaça listada na seção 8 era que "a raiz
pode piorar a calmaria" — o que se confirmou, mas para os **dois** braços, e a cobertura piorou em **TODAS
as 4 faixas, para os dois braços**, sem exceção. A hipótese central da rodada (variância que cresce com o
nível, corrigida pela transformação, devolveria faixa proporcional ao nível) **não se sustentou em nenhum
recorte** — nem sequer na faixa de epidemia, onde deveria ajudar mais.

## Captura do pico (semana de 2025-03-30, 2.381 casos — o maior valor da série)

| Braço | h | IC 90% previsto | Cobriu? |
|---|---|---|---|
| T_raiz | 1 | [256, 1.433] | Não |
| T_raiz | 4 | [467, 1.080] | Não |
| T_raiz | 8 | [0, 891] | Não |
| T_raiz | 12 | [0, 1.176] | Não |
| T_log | 1 | [685, 1.358] | Não |
| T_log | 4 | [531, 1.275] | Não |
| T_log | 8 | [0, 855] | Não |
| T_log | 12 | [0, 965] | Não |

**Nenhuma das 8 combinações cobriu o pico** — o limite superior do intervalo de 90% fica sempre bem abaixo
dos 2.381 casos reais, em todos os horizontes e nos dois braços.

## Cruzamento de quantis (seção 3 da pré-declaração)

- **Cruzamento bruto** (na escala transformada, antes do rearranjo): 1.796 de 2.318 origens (77,5%) —
  mesma magnitude do B0 original (67-79% por horizonte, medido em 26/09 na rodada do WIS).
- **Cruzamento restante em casos**, depois do rearranjo isotônico + volta monótona: **0 de 2.318** —
  confirma que a volta (quadrado com corte em 0, ou expm1 com corte em 0) preserva a ordem, como esperado
  pela seção 3. Conferido também por spot-check manual numa origem individual.

## Desvios da pré-declaração/brief (reportados, não decididos em silêncio)

Ver o cabeçalho de `rodar.py` para o texto completo. Resumo:

1. A trava do B0 não pôde ser lida de `previsoes_quantis.csv` (o quantil 0,85 nunca foi salvo ali) — usada
   a evidência já certificada do log da rodada de origem, com checagem automática de que o log citado
   realmente contém essas linhas.
2. O MAE do B0 **por faixa** (calmaria/subida/Mobilização/Alerta) não pôde ser calculado — exigiria
   re-rodar o B0 no quantil 0,85, proibido nesta tarefa. Reportado como indisponível, não aproximado.
3. A cobertura por faixa usa a série completa de origens (2020-2026), não a janela 2024-2026, para
   reproduzir exatamente os números-âncora do B0 (163 semanas, 17,8%, 8,0%).
4. O MAE (critério e "no total") usa a janela 2024-01-01 a 2026-02-01 — a mesma da trava —, diferente da
   janela usada na cobertura por faixa (item 3). Cada âncora dada no brief foi reproduzida na janela em
   que originalmente foi medida.

## Pendência

Esta rodada ainda não passou por **certificação adversarial** por agente independente (regra do projeto
para mudança de pipeline/dado). O spot-check de monotonicidade feito aqui é do próprio autor da rodada, não
substitui essa certificação.

## Arquivos em `saidas/`

- `previsoes_completas.csv` — as 64 células, previsão bruta (transformada e em casos) por origem.
- `previsoes_quantis_finais.csv` — os 7 quantis do WIS, já rearranjados e revertidos para casos.
- `diagnostico_cruzamento.csv`, `mae_por_h.csv`, `mae_por_faixa.csv`, `cobertura_por_faixa.csv`,
  `wis_por_h.csv`, `wis_por_faixa.csv`, `captura_do_pico.csv`, `veredito.csv`.

---

## Adendo do orquestrador, 26/09/2026 — por que falhou

A pré-declaração apostava num mecanismo: *"dado de contagem tem variância que cresce com o nível; em escala
transformada, uma faixa de largura constante volta como faixa proporcional"*. **A aposta estava errada, e o
motivo é mensurável.**

Medido no `B0`, cenário adotado, mesma base:

| Faixa | Semanas | Real mediano | Largura do IC90 | Erro mediano | Largura necessária | Quanto falta |
|---|---|---|---|---|---|---|
| Calmaria | 814 | 1 | 8,5 | 1,3 | 4 | **0,5×** — larga demais |
| Subida | 110 | 47 | 101,1 | 29,6 | 97 | 1,0× — certa |
| Mobilização | 72 | 247 | 195,6 | 157,8 | 519 | 2,7× |
| **Alerta ou mais** | 163 | 917 | **592,7** | **539,0** | 1.773 | **3,0×** |

### O erro da minha hipótese

- **A faixa JÁ cresce com o nível**, e muito: de 8,5 para 592,7, um fator de **70×**.
- **Mas o erro cresce mais rápido:** de 1,3 para 539,0, um fator de **415×**.
- Ou seja, o problema nunca foi faixa de largura constante. Era faixa que **cresce menos que o erro**.
- **Raiz e log comprimem valores altos**, então fazem a faixa crescer ainda **mais devagar**. Foram na
  direção contrária do necessário. Isso explica por que a cobertura piorou em **todas** as faixas.

### O que o número realmente diz

- **Na calmaria o modelo é tímido demais:** a faixa é **o dobro** do necessário. Ele sabe menos do que
  demonstra saber.
- **Em epidemia ele é confiante demais**, por um fator de 3.
- 🔴 **E isso não é problema de variância, é de viés.** O erro mediano acima de 421 é **539 casos** sobre
  um valor real mediano de **917** — 59% do nível. Erro sistemático dessa magnitude é o modelo prevendo
  baixo demais, não ruído em torno do valor certo. Bate com a captura do pico de **0,388** de 13/09.
- **Alargar a faixa não conserta viés.** Uma faixa de 1.773 casos de largura cobriria 90%, mas iria de
  ~100 a ~1.900 e não informaria nada a ninguém.

### A consequência honesta

O caminho 1 da lista de 26/09 (`../2026-09-26_calibracao_por_faixa/` §6) está **descartado, com medição**.
Os caminhos 2, 3 e 4 daquela lista atacam a forma da distribuição, e o problema medido aqui é de **nível**:
o modelo não consegue prever o tamanho da epidemia, e a raiz do limite é ter **2 epidemias** na série.

**Nenhuma transformação de escala resolve falta de epidemia no treino.**
