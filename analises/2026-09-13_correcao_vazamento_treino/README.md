# Correção do vazamento temporal no corte de treino — 13/09/2026

> **Pergunta:** quanto do desempenho do modelo era vazamento temporal?
> **Resposta: muito, e concentrado exatamente nas duas escolhas que sustentam a configuração de referência.**
> Protocolo em [PRE_DECLARACAO.md](PRE_DECLARACAO.md), com a EMENDA 1 escrita antes de qualquer resultado.
> Ponto de retorno: tag git `antes-correcao-vazamento` (commit `6656598`).

**Status:** ✅ rodada concluída, 32/32 células, 0 falhas, 50,2 min · ⏳ grid de 120 precisa ser refeito.

---

## 1. O defeito e a correção

O walk-forward escolhia as linhas de treino pela data de **origem** (`iloc[:indice_corte]`). Como cada
linha carrega rótulo datado origem + horizonte, as **h−1** linhas mais recentes do treino tinham resposta
posterior à semana prevista.

Correção, em `rodar_corrigido.py`:

```python
linha_ja_respondida = validos["data"] + pd.Timedelta(weeks=horizonte) <= data_de_origem_do_teste
treino = validos.loc[linha_ja_respondida]
```

Filtro por **data**, não por posição: a série tem buracos (vetor NaN em ago/2022 e na enchente de 2024),
e recuar 12 posições não equivale a recuar 12 semanas. Verificação adversarial independente confirmou:
sem erro de fronteira, nenhuma linha posterior ao teste entra, descarte exatamente 0/3/7/11 fora dos
buracos e nunca acima de h−1.

**Tamanho da contaminação:** 5,1% do treino em h=12 na média dos cortes (10,6% no primeiro, 2,8% no
último). Pequeno em proporção, mas são as **11 semanas imediatamente anteriores** à previsão — os
últimos 2 meses e meio do treino, 100% contaminados, e as vizinhas mais próximas no espaço de features.

## 2. O controle passou

A pré-declaração fixou: h=1 tem 0 linhas contaminadas, logo o resultado corrigido tem de ser idêntico.

- 8 células de h=1, 2.384 pontos, **diferença máxima de previsão 0,0000000000**;
- 9.368 pontos pareados, **zero perda no pareamento**.

Toda diferença em h=4, h=8 e h=12 é o vazamento, não diferença de ambiente.

## 3. FATO — o custo do vazamento na configuração de referência

HistGradientBoosting · quantil 0,80 · **com vetor**, período de avaliação (2024+), n=102:

| h | MAE antes | MAE depois | var | R² antes | R² depois | captura do pico |
|---|---|---|---|---|---|---|
| 1 | 101,3 | 101,3 | 0,0% | 0,883 | 0,883 | 0,850 → 0,850 |
| 4 | 168,4 | 221,4 | **+31,5%** | 0,779 | 0,619 | 0,832 → **0,694** |
| 8 | 184,0 | 270,2 | **+46,8%** | 0,724 | 0,409 | 0,632 → **0,395** |
| 12 | 179,6 | 273,9 | **+52,5%** | **0,758** | **0,452** | 0,619 → **0,396** |

**H1 e H2 confirmadas, e com folga.** A piora cresce monotonicamente com o horizonte, exatamente como
previsto por escrito. O R² de 3 meses, que o ESTADO cita como 0,758, é **0,452** medido sem vazamento.

Sem vetor (M0), a piora é bem menor: +22,8% / +30,4% / +39,5% em h=4/8/12.

## 4. FATO — o vazamento não era neutro: favorecia a configuração escolhida

Piora do MAE de calibração com a correção, média dos 4 horizontes:

| Configuração | Antes | Depois | Piora |
|---|---|---|---|
| HistGB · quantil 0,80 · **M1** | 33,18 | 42,71 | **+28,7%** |
| HistGB · quantil 0,85 · M1 | 33,85 | 42,02 | +24,1% |
| GradientBoosting · quantil 0,70 · M1 | 34,53 | 42,83 | +24,0% |
| LightGBM · padrão · M1 | 38,66 | 47,00 | +21,6% |
| HistGB · **padrão** · M1 | 39,88 | 46,17 | **+15,8%** |
| HistGB · quantil 0,80 · **M0** | 38,19 | 42,52 | **+11,3%** |
| LightGBM · quantil 0,70 · M0 | 45,06 | 50,14 | +11,3% |
| LightGBM · quantil 0,90 · M1 | 53,65 | 58,45 | +9,0% |

Duas assimetrias limpas:

- **Com vetor foi punido cerca de 2× mais que sem vetor** (≈20,5% contra 11,3%). As colunas do vetor
  davam graus de liberdade a mais para explorar o rótulo vazado dos vizinhos. A hipótese de assimetria
  levantada na verificação está **confirmada**.
- **Perda quantílica foi punida quase 2× mais que a padrão**, no mesmo algoritmo e mesmo conjunto
  (+28,7% contra +15,8%). Plausível: prever o quantil 0,80 se apoia na cauda alta, e as linhas vazadas
  são justamente as dos picos.

**As duas escolhas que definem a configuração de referência são as duas mais infladas pelo vazamento.**

## 5. ❌ O ranking NÃO sobreviveu — o grid de 120 precisa ser refeito

Critério da EMENDA E1.2, fixado antes de rodar:

| Critério | Resultado | |
|---|---|---|
| 1º colocado mantido | HistGB q0,80 M1 caiu para **3º**; q0,85 M1 assumiu | ❌ |
| Ninguém se move mais de 2 posições | máximo 2 | ✅ |
| Vantagem quantílico × padrão ≥ 10 pp | **20,2 pp → 8,1 pp** | ❌ |

Spearman 0,857 entre as ordens. Duas das três condições falharam.

**Consequências, pelo critério pré-declarado:**

- ⏳ **O grid de 120 precisa ser refeito.** Faltam 22 configurações × 4 horizontes = **88 células, ~2h47**.
- 🚫 **"A perda importa mais que o algoritmo" sai do texto** até lá. O "+20,2%" é **+8,1%** sem vazamento.
- 🚫 **"A melhor entre as 30 testadas"** não pode ser afirmado: entre as 8 medidas, a vencedora mudou.
  A diferença para a nova 1ª é de só 1,6%, ou seja, segue empate técnico — mas o rótulo de vencedora não é mais dela.

## 6. ✅ O ganho do vetor em h=12 sobreviveu

A §5 da pré-declaração exige a comparação **pareada por `data_alvo`**. O primeiro script que escrevi
comparou M0 e M1 em semanas diferentes (109 × 102) e deu 64% de encolhimento. Erro meu, contra a
própria pré-declaração. Refeito pareado (n=102 nos dois lados):

| h | MAE M0 antes | MAE M1 antes | ganho antes | MAE M0 depois | MAE M1 depois | ganho depois |
|---|---|---|---|---|---|---|
| 1 | 94,6 | 101,3 | −6,6 | 94,6 | 101,3 | −6,6 |
| 4 | 187,7 | 168,4 | +19,3 | 225,5 | 221,4 | **+4,1** |
| 8 | 182,1 | 184,0 | −2,0 | 238,9 | 270,2 | **−31,2** |
| 12 | 214,3 | 179,6 | +34,7 | 300,3 | 274,0 | **+26,4** |

- **h=12: encolhimento de 24%**, abaixo do corte de 30% → pelo critério pré-declarado a alegação
  **sobrevive**, e continua **exploratória**. O teste focado de 60 execuções **não** precisa ser refeito.
- Pela EMENDA E1.5, encolhimento < 30% → as dispensas da **Rodada 1** e do **teste decisivo de alvos**
  **ficam de pé**.
- ⚠️ Mas o vetor fica ainda **mais concentrado em h=12**: em h=4 o ganho quase some (19,3 → 4,1) e em
  h=8 ele já prejudicava e passa a prejudicar muito mais (−2,0 → −31,2).

## 7. O que muda no ESTADO.md

| Afirmação hoje | Como fica |
|---|---|
| R² 0,758 em h=12 (3 meses) | **0,452** |
| R² 0,89 (h=1) a 0,63 (h=12) | h=1 confirmado; h=12 é 0,452 |
| "Confiável até 1 mês" | captura em h=4 cai de 0,832 para **0,694** — a frase precisa ser refeita |
| "A perda importa mais que o algoritmo (+20,2% × +16,5%)" | 🚫 suspensa; medido +8,1% |
| "Melhor entre as 30 testadas" | 🚫 suspensa até o grid ser refeito |
| Ganho do vetor em h=12 | ✅ mantido, exploratório, 34,7 → 26,4 de MAE |

## 8. Arquivos

- `rodar_corrigido.py` · `rodar_corrigido_padrao.py` — as duas bateladas.
- `comparar.py` — a comparação antes/depois (⚠️ o bloco H4 dele é o **não pareado**; o valor válido é
  o da §6 acima).
- `resumir.py` — reconstrói `grid_resumo.csv` e o ranking a partir das previsões brutas. Valida contra
  o original de 30/08 com diferença 0 em 240 linhas e as 30 posições idênticas. **Fecha a lacuna do
  script perdido.**
- `saidas/` — previsões das 32 células, logs e `comparacao_antes_depois.csv`.

---

# FASE 2 — a correção aplicada a todo o projeto

Protocolo em [PRE_DECLARACAO_FASE2.md](PRE_DECLARACAO_FASE2.md). Correção centralizada em
`modelagem_aedes/motor/corte_temporal.py`, aplicada em 5 pontos do código de produção e em 3 cópias
corrigidas das rodadas de 29/08. Suíte: 22/22.

## F2.1 — Controle

h=1 não tem linha contaminada, então tem de sair idêntico. Verificado em dois lugares:

- **Rodada 2**, 8 células de h=1: diferença máxima **0,0000000000**.
- **Grid**, 8 células de h=1 da fase 1: diferença máxima **0,0000000000**.

⚠️ Os experimentos de surto usam horizontes 4, 8 e 12 e **não têm controle de h=1**. Ressalva declarada.

## F2.2 — ❌ O núcleo proposto caiu: a equivalência clima × vetor não se sustenta

Duas coisas estavam erradas ao mesmo tempo no resultado de 29/08.

**(a) A margem.** A pré-declaração de 29/08 fixou o TOST em % do MAE da **persistência**; o código usou
% do MAE do **clima**. `tost_margem_predeclarada.py` refaz a estatística sobre as previsões salvas, sem
rodar modelo. Validação: sob a margem do clima ele reproduz os vereditos originais com diferença 10⁻¹⁴.

**(b) O alvo.** Os "4 de 8" são de **notificados**; o alvo decidido em 30/08 é **confirmados**.

Combinações que fecham equivalência a ±15%:

| Alvo | Margem do clima (código) | Margem da persistência (pré-declarada) |
|---|---|---|
| **Confirmados** (decidido) | 0 de 8 | **1 de 8** |
| Notificados | 4 de 8 | **0 de 8** |

**E não é superioridade disfarçada.** Testado: em h=1 o vetor puro ganha do clima puro por 23,0 de MAE
(confirmados, p bruto 0,049) e 12,3 (notificados, p 0,045), mas os IC por bootstrap **incluem zero** e,
com Holm sobre 8 comparações viram **0,388** (confirmados) e **0,363** (notificados). **O único IC que exclui zero é contra o vetor**: notificados,
`com_ar`, h=12, o clima ganha por **72,5** de MAE.

Padrão consistente: o vetor ajuda pouco em h=1 e atrapalha em h=8 e h=12.

**Consequência:** a virada de eixo de 29/08, que promovia a equivalência a núcleo, está **refutada**.
Não é falta de poder — são 576 a 587 semanas pareadas.

## F2.3 — ✅ Treinar desde 2012 continua vencendo (Emenda 1.3 resolvida)

Critério: vencer em 3 de 4 horizontes. MAE da densidade do vetor, menor é melhor.

| h | deslizante 6 anos | **expansível 2012** | expansível 2020 |
|---|---|---|---|
| 1 | 0,15 | **0,15** | 0,16 |
| 4 | 0,19 | **0,17** | 0,18 |
| 8 | 0,21 | **0,19** | 0,20 |
| 12 | 0,23 | **0,20** | 0,22 |

**3 de 4 antes e depois**, e a vantagem **cresceu** em horizonte longo. Confirma o que a Emenda 1.3
previu por escrito: os regimes de treino menor são proporcionalmente mais contaminados, então corrigir
pune mais eles. O item volta a ser citável.

## F2.4 — ✅ A Camada 2 ficou mais forte: a regra simples vence 8 de 8

Critério: a única célula k×h em que o modelo vencia a persistência sobrevive?

| | Modelo vence a persistência |
|---|---|
| Antes | 1 de 8 (k=8, h=8) |
| **Depois** | **0 de 8** |

O Spearman do modelo em k=8 h=8 caiu de **0,536 para 0,321**. A persistência não treina, então não muda
(0,893 · 0,821 · 0,607 · 0,500) — a queda é toda do modelo.

- **O sinal espacial continua real**: persistência 0,89 contra climatologia 0,46 em h=1, e nenhuma das
  duas tem vazamento.
- **O mapa de risco entomológico por regra simples é o resultado mais limpo do projeto**, e agora é
  8 de 8, não 7 de 8.

## F2.5 — O clima sozinho morre em horizonte longo; o vetor é o que segura

`comparacao_literatura` prevê casos com **só clima** contra **clima + vetor**, sem o núcleo
autorregressivo. Controle de h=1: diferença **0,0000000000** nas duas colunas.

| h | Só clima, antes | Só clima, **depois** | Clima + vetor, **depois** |
|---|---|---|---|
| 1 | 0,236 | 0,236 | 0,308 |
| 4 | 0,400 | 0,221 | 0,279 |
| 8 | 0,370 | **0,089** | 0,201 |
| 10 | 0,318 | **−0,045** | 0,128 |
| 12 | 0,210 | **−0,024** | 0,106 |

- **FATO — o clima sozinho não prevê casos em 10 a 12 semanas.** R² zero ou negativo. O que parecia
  0,21 a 0,32 era vazamento.
- **FATO — o vetor mantém R² de 0,11 a 0,13 exatamente onde o clima falha.** O ganho absoluto caiu pela
  metade (0,31 → 0,13 em h=12), mas passou de "ajuda um pouco" para "é a diferença entre ter e não ter
  sinal".
- Ganho do vetor positivo em **11 de 12** horizontes (era 12 de 12).

## F2.6 — 🚫 HIPÓTESE DE COMPLEMENTARIDADE: **retirada** após auditoria adversarial

**Versão anterior desta seção afirmava** que três medições corrigidas e *independentes* apontavam
para "o vetor é complementar ao clima, não substituto". **Auditoria independente derrubou a alegação
em 13/09/2026, e a checagem foi refeita pelo orquestrador.** O que estava errado:

- ❌ **"Independentes" é falso.** As três usam a mesma `tabela_final`, as mesmas semanas e o mesmo
  alvo. A interseção de datas entre a Rodada 2 e o grid em h=12 é de **284 de 284, ou seja, 100%**.
  Não são três evidências, são três recortes do mesmo dado.

- ❌ **"Grid pareado, 8 de 30 configs" era enganoso.** Das 8 configurações rodadas na fase 1, só
  **1 de 7** combinações de algoritmo + perda tem **M0 e M1 ao mesmo tempo**
  (`hist_gradient_boosting` · `quantil_0.80`). As outras 6 são só M0 **ou** só M1, em algoritmos e
  perdas diferentes, e não isolam o efeito do vetor. **O ganho de 26,4 de MAE em h=12 vem de UM par.**

- ❌ **Nada sobrevive a correção de múltiplas comparações.** Holm sobre as 16 comparações da Rodada 2
  (a única das três com p-valor): menor p bruto 0,0485, limiar 0,05/16 = 0,0031 → **0 rejeições**.
  A `comparacao_literatura` **não grava p, n, nem MAE** — só R² agregado. O ganho do grid não passou
  por teste nenhum.

- ⚠️ **A medição (i) mede outro eixo.** "Vetor no lugar do clima" é substituição, não complementaridade.
  Seu único IC que exclui zero favorece o **clima**. Isso é compatível com a hipótese, mas é ausência
  de contradição, não evidência a favor.

**Onde a hipótese fica:** ⏳ **indeterminada**, não confirmada e não refutada. Só o grid completo pode
decidir, porque lá existem **15 pares** de M0 × M1 no mesmo algoritmo e mesma perda, pareados por
`data_alvo`, com Diebold-Mariano e Holm sobre a família inteira.

**Lição registrada:** o orquestrador chamou de "triangulação" o que era um padrão num único conjunto
de dados. Foi a auditoria adversarial que pegou, não a leitura própria.

## F2.7 — Tempo real de execução (para calibrar estimativas futuras)

| Bloco | Estimado | Real |
|---|---|---|
| Rodada 2, dois alvos | ~6 min | **6 min** ✅ |
| Rodada 4 | ~2 min | **2 min** ✅ |
| Rodada 3 | ~2 min | **2 min** ✅ |
| `comparacao_literatura` | ~2 min | **30 min** ❌ |

A estimativa dos experimentos da pipeline foi calibrada pelas rodadas de 29/08, que são mais leves.
Erro de ~15×. Para a próxima: medir uma célula antes de estimar o bloco.

## F2.8 — O cenário 1 perde um terço do R² em horizonte longo

`cidade_regressao`, o experimento que sustenta a frase "R² de 0,89 (h=1) a 0,63 (h=12)" do ESTADO §3.
Controle de h=1: diferença **0,0000000000** nas 4 combinações (4ª confirmação independente do controle).

| Conjunto | h | MAE antes | MAE depois | var | R² antes | R² depois |
|---|---|---|---|---|---|---|
| M0 clima6 | 4 | 91,7 | 123,5 | +34,6% | 0,705 | **0,480** |
| M0 clima6 | 8 | 98,8 | 126,8 | +28,4% | 0,695 | **0,516** |
| M0 clima6 | 12 | 109,5 | 136,6 | +24,7% | **0,634** | **0,426** |
| M1 clima6 + vetor | 4 | 86,6 | 126,5 | +46,1% | 0,761 | **0,540** |
| M1 clima6 + vetor | 8 | 93,2 | 143,1 | +53,5% | 0,733 | **0,357** |
| M1 clima6 + vetor | 12 | 114,2 | 145,8 | +27,7% | 0,637 | **0,398** |

- **O "0,63 em h=12" do ESTADO é 0,43 sem vazamento.** Um terço do R² era artefato.
- **O vetor apanhou mais que o sem-vetor de novo**: +46,1% contra +34,6% em h=4, +53,5% contra +28,4%
  em h=8. Terceira vez que essa assimetria aparece.
- ⚠️ **A vantagem do vetor em h=4 e h=8 neste cenário INVERTE.** Antes: M1 86,6 × M0 91,7 (h=4) e
  93,2 × 98,8 (h=8), vetor ganhando. Depois: M1 126,5 × M0 123,5 e 143,1 × 126,8, **vetor perdendo**.
- ⚠️ **Ressalva importante:** `rodar_regressao_selecao_clima` **não pareia** M0 e M1 (dívida técnica já
  registrada). Esta comparação sofre do mesmo defeito do `grid_resumo` e não deve ser lida como o
  efeito do vetor. Quem responde isso é o grid, pareado por `data_alvo`.
- Tensão a resolver: aqui o cenário roda **LightGBM com perda padrão**; o grid mede o vetor com
  **HistGB quantílico**. O efeito do vetor pode depender do algoritmo e da perda — o grid completo
  tem 15 pares para dizer.

## F2.9 — Diebold-Mariano pareado: a vantagem do vetor quase some (LightGBM, perda padrão)

`cidade_diebold` usa `walk_forward_pareado`, que treina M0 e M1 **no mesmo corte e nas mesmas semanas**.
É a comparação do vetor **corretamente pareada** dentro da pipeline. Controle de h=1: diferença
**0,0000000000** nos dois conjuntos (5ª confirmação). `n` idêntico antes e depois em todos os horizontes.

`dMAE` positivo = o vetor erra menos.

| Conjunto | h | dMAE antes | dMAE depois | p antes | p depois |
|---|---|---|---|---|---|
| sem maturidade | 4 | −9,9 | **−26,0** | 0,796 | 0,900 |
| sem maturidade | 8 | +0,9 | **−24,2** | 0,473 | 0,836 |
| sem maturidade | 12 | −1,6 | **−9,3** | 0,542 | 0,756 |
| com maturidade | 4 | +1,7 | **−4,1** | 0,398 | 0,684 |
| com maturidade | 8 | +11,8 | **−4,1** | 0,101 | 0,610 |
| com maturidade | 12 | +7,2 | **+1,9** | 0,291 | 0,389 |

- **Com maturidade:** o vetor era melhor em **10 de 12** horizontes; agora é melhor em **4 de 12**.
- **Sem maturidade:** era melhor em 3 de 12; agora em **0 de 12**.
- Melhor p bruto: 0,0647 → **0,2700**. Estava longe de significância antes e ficou mais longe.

⚠️ **Tensão central do dia, agora nítida.** Duas comparações **pareadas** do vetor, corrigidas, discordam:

| Medição | Algoritmo e perda | Ganho do vetor em h=12 |
|---|---|---|
| Grid (§6) | HistGB · quantílico 0,80 | **+26,4** de MAE |
| Diebold (esta) | LightGBM · perda padrão | **+1,9** de MAE |

Ou o efeito do vetor **depende do algoritmo e da perda**, ou uma das duas é ruído. O grid completo tem
**15 pares** M0 × M1 nos 3 algoritmos e 5 perdas — é a única medição capaz de separar as duas leituras.

## F2.10 — 🔴 O ÚNICO resultado do projeto que já sobreviveu a Holm era vazamento

`cidade_deteccao_surto`, alvo confirmados. ⚠️ Sem controle de h=1: usa horizontes 4, 8 e 12 — ressalva
declarada na §4 da pré-declaração. Sanidade: o `n` é praticamente idêntico antes e depois
(287→288, 283→283, 279→278), então o desenho é o mesmo.

McNemar, clima só × clima + vetor:

| pctl | h | Antes (clima acerta × vetor acerta) | p antes | Depois | p depois |
|---|---|---|---|---|---|
| 90 | 4 | 9 × 9 | 1,000 | 12 × 10 | 0,832 |
| 90 | 8 | 5 × 10 | 0,302 | 8 × 11 | 0,648 |
| **90** | **12** | **4 × 24** | **0,00018** | **10 × 16** | **0,327** |
| 95 | 4 | 11 × 7 | 0,481 | 13 × 8 | 0,383 |
| 95 | 8 | 5 × 11 | 0,210 | 5 × 12 | 0,143 |
| **95** | **12** | **5 × 17** | **0,017** | **4 × 7** | **0,549** |

**O `confirmados · P90 · h=12` com p bruto 0,00018 e Holm 0,00108 era — e continua sendo — o único
resultado que o projeto inteiro já produziu capaz de sobreviver a correção de múltiplas comparações.
Sem vazamento ele vira 10 × 16, p = 0,327.**

O menor p do experimento inteiro vai de **0,00018 para 0,143**.

Isso fecha, por um segundo caminho independente, a cadeia que a auditoria de 13/09 tinha levantado:
o teste decisivo de 30/08 já havia derrubado esse resultado ao equalizar a janela (9×16, p=0,230).
Agora a correção do vazamento o derruba sozinha, na janela original. **Duas causas independentes,
mesma conclusão: o achado não existia.**

- O vetor continua favorecido em 4 de 6 comparações, igual a antes — mas isso é contagem descritiva,
  sem significância, e sempre foi.
- **Consequência para o texto:** a frase "nenhum resultado do projeto sobrevive a correção de múltiplas
  comparações" deixa de ter exceção. Antes havia uma, de 29/08, que agora está explicada.

## F2.11 — 🔵 ACHADO NOVO: sem vazamento, o vetor **piora** o alarme de surto, e isso sobrevive a Holm

`cidade_surto_notificados`, alvo notificados, n = 553 a 568 semanas. ⚠️ Sem controle de h=1 (horizontes
4, 8 e 12). O `n` é idêntico antes e depois em 5 de 6 linhas, então o desenho é o mesmo.

`clima acerta × vetor acerta` = pares discordantes do McNemar. Holm aplicado pelo próprio pipeline
sobre as 6 comparações.

| pctl | h | Antes | p Holm antes | Depois | p bruto | **p Holm depois** |
|---|---|---|---|---|---|---|
| 90 | 4 | 9 × 9 | 1,000 | 10 × 7 | 0,629 | 1,000 |
| 90 | 8 | 15 × 10 | 1,000 | **32 × 15** | 0,0196 | 0,098 |
| **90** | **12** | 14 × 10 | 1,000 | **23 × 7** | **0,0062** | **0,037** ✅ |
| 95 | 4 | 14 × 8 | 1,000 | 19 × 10 | 0,137 | 0,550 |
| 95 | 8 | 10 × 7 | 1,000 | 9 × 10 | 1,000 | 1,000 |
| 95 | 12 | 12 × 8 | 1,000 | 19 × 10 | 0,137 | 0,550 |

- **Antes: 0 de 6 sobreviviam a Holm, menor p bruto 0,286.**
- **Depois: 1 de 6 sobrevive, e o menor p bruto é 0,0062.**
- O sinal é **contra o vetor**: em `P90 · h=12`, o modelo só-clima acerta onde o clima+vetor erra em
  **23 semanas**, contra 7 no sentido oposto.

**Leitura.** Com o vazamento, as features do vetor tinham como "pagar" seu próprio custo de
complexidade espiando o rótulo dos vizinhos, e o resultado ficava nulo. Sem vazamento, elas aparecem
pelo que são em horizonte longo: **ruído que degrada o classificador**. Consistente com a assimetria
medida o dia todo — os conjuntos com vetor sempre apanharam ~2× mais na correção.

⚠️ **Como rotular.** A pré-declaração da fase 2 (§5, bloco E) previu por escrito que um negativo podia
se manter, e este se manteve **e ficou significativo**. Mas a hipótese específica "o vetor piora o
alarme" não foi pré-declarada com essa direção — nasceu da rodada corrigida. Rotular como **achado
robusto porém não pré-declarado**, e não como confirmatório.

**Consequência para o ESTADO:** o item "o vetor NÃO melhora o alarme de surto — 0 de 6 em Holm" fica
mais forte e muda de natureza. Não é mais ausência de efeito; é **efeito medido na direção contrária**,
sobrevivendo a correção de múltiplas comparações, com 553 semanas.

---

# F3 — O GRID COMPLETO, CORRIGIDO (120 de 120 células)

88 células novas em 1h51, zero falhas. **Controle: 30 células de h=1, 9.030 pontos, diferença
0,0000000000.** Definitivo.

## F3.1 — A nova configuração de referência

Pelo critério pré-declarado (menor MAE de calibração, média dos 4 horizontes), adotado sem discussão:

### **HistGradientBoosting · `loss="quantile"`, `quantile=0.85` · COM vetor**

Era a 2ª no grid contaminado. A antiga vencedora (`quantile=0.80`) caiu para 3º. Spearman entre as
ordens: **0,891**. Maior deslocamento: **13 posições** (HistGB q0,80 **sem** vetor subiu de 15º para 2º).

Métricas de avaliação (2024+), contra o que o ESTADO e o painel publicam hoje:

| h | MAE | **R² corrigido** | R² publicado | Captura do pico |
|---|---|---|---|---|
| 1 | 98,0 | **0,898** | 0,883 | 0,886 |
| 4 | 219,7 | **0,628** | 0,779 | 0,702 |
| 8 | 272,6 | **0,450** | 0,724 | 0,417 |
| 12 | 278,7 | **0,437** | 0,758 | 0,388 |

**O R² de 3 meses vai de 0,758 para 0,437.** A captura do pico em 1 mês, de 0,832 para 0,702.

## F3.2 — 🚫 "A perda importa mais que o algoritmo" está REFUTADO

| Trocar | Antes | **Depois** |
|---|---|---|
| O melhor algoritmo pelo melhor LightGBM | +16,5% | **+11,8%** |
| Quantílico por padrão (mesmo algoritmo e conjunto) | +20,2% | **+9,9%** |

A ordem **inverteu**: agora o algoritmo pesa mais que a perda, ainda que por pouco. E o efeito da perda
é **condicional ao algoritmo**:

| Algoritmo (M1) | Vantagem do quantílico |
|---|---|
| HistGradientBoosting | +9,9 pp |
| GradientBoosting | +8,0 pp |
| **LightGBM** | **−1,9 pp** (o quantílico é pior) |

A frase sai do texto. O que sobra, e é mais fraco: "a função de perda tem efeito comparável ao do
algoritmo, e depende de qual algoritmo".

## F3.3 — O vetor: 60 comparações pareadas, o teste decisivo

15 pares (mesmo algoritmo, mesma perda, só muda o vetor) × 4 horizontes, pareados por `data_alvo`,
Diebold-Mariano com HLN, Holm sobre os 60.

| | Original | **Corrigido** |
|---|---|---|
| O vetor erra menos em | 35 de 60 | **27 de 60** (minoria) |
| Sobrevivem a Holm | 0 | **0** |
| Menor p bruto | 0,0025 | 0,0144 |

Por horizonte, ganho médio de MAE:

| h | Original | **Corrigido** |
|---|---|---|
| 1 | 0/15 · −12,5 | 0/15 · −12,5 (controle) |
| 4 | 11/15 · +7,7 | **11/15 · +8,5** |
| 8 | 9/15 · +4,5 | **3/15 · −15,3** (inverteu) |
| 12 | 15/15 · +31,9 | **13/15 · +22,5** |

**⚠️ O achado que muda a leitura: em h=12 o ganho do vetor se concentra onde o algoritmo é PIOR.**
Os 5 maiores ganhos são as 5 configurações de **LightGBM** (+61,8 a +29,4); o HistGradientBoosting,
melhor algoritmo, fica entre **+8,9 e −11,2**. A configuração de referência tem ganho de só **+6,4**
(p=0,261).

Leitura honesta: o vetor **compensa parcialmente um algoritmo fraco**. O LightGBM sem vetor erra 286 a
329 em h=12; com vetor cai para 236 a 272, chegando perto do que o HistGB já faz **sem** vetor. Isso é
bem mais fraco do que "a armadilha melhora a previsão".

**Veredito:** o vetor não tem efeito demonstrável na previsão de casos. Nada sobrevive a Holm, ele
perde na maioria das 60 comparações, e onde ganha é substituindo qualidade de algoritmo.
