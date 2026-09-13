# PRÉ-DECLARAÇÃO — correção do vazamento temporal no corte de treino

**Escrita em 13/09/2026, ANTES de rodar.** Ponto de retorno no git: tag `antes-correcao-vazamento`
(commit `6656598`). Proibido alterar hipótese, métrica ou critério depois de ver o resultado; qualquer
mudança vira **EMENDA datada** ao final deste arquivo.

---

## 1. O defeito

O walk-forward seleciona as linhas de treino pela data de **origem** (`iloc[:indice_corte]`), quando
deveria selecionar pela data da **resposta** (origem + horizonte). A cada corte, **h−1** linhas de
treino carregam rótulo datado depois da semana que está sendo prevista.

| h | linhas contaminadas | % no 1º corte (104 linhas) | % no último corte (~500) |
|---|---|---|---|
| 1 | 0 | 0,0% | 0,0% |
| 4 | 3 | 2,9% | 0,6% |
| 8 | 7 | 6,7% | 1,4% |
| 12 | 11 | 10,6% | 2,2% |

Exemplo: origem 03/03/2024, h=12, alvo 26/05/2024. O treino inclui a linha de 18/02/2024, cujo rótulo
é 12/05/2024 = **1.510 casos**. Documentação completa em
[`../2026-09-13_auditoria_mecanica_resultados/README.md`](../2026-09-13_auditoria_mecanica_resultados/README.md) §3.1.

**A correção:** `treino = validos[validos["data"] + horizonte_em_semanas <= data_de_origem_do_teste]`.
Filtro por **data**, não por posição: depois do `dropna` a tabela tem buracos (semanas da enchente
saem do M1), e contar posições não equivale a contar semanas.

## 2. O que será rodado

Réplica exata de `2026-08-30_grid_completo/rodar_grid.py` com **uma única alteração**, o corte de treino.
Mesma tabela, mesmos hiperparâmetros, mesmas colunas de clima, `passo=1`.

- **Bloco A — a configuração de referência:** HistGradientBoosting · `quantile=0.80` · M0 e M1 · h=1/4/8/12.
- **Bloco B — robustez do ranking:** as posições **1, 2, 4, 15, 26 e 30** do ranking de 30/08, nos 4
  horizontes. Escolhidas antes de rodar, cobrindo topo, meio e fundo, e incluindo o par M0/M1 do vencedor.

Total: **24 células** (8 de A, 16 novas em B; as posições 1 e 15 são as próprias células de A).
Estimativa: **~30 min** de CPU, com `nohup` e log.

**Os pontos de teste são idênticos aos de 30/08**: o laço de teste não muda, só o fatiamento do treino.
Nos primeiros cortes o treino fica com menos de 104 linhas (93 em h=12). Isso é aceito e é parte do
custo da correção; **não** vamos deslocar o início do laço, porque isso quebraria a comparabilidade.

## 3. Hipóteses

- **H1 (principal):** o MAE de avaliação **piora** com a correção, e a piora **cresce com o horizonte**.
- **H2:** a captura do pico (média(pred)/média(real) nas semanas com real > 100) **cai**, mais em h longo.
- **H3:** o **ranking** das 6 configurações se preserva, porque o viés é de modo comum.
- **H4:** a vantagem do M1 sobre o M0 em h=12 **encolhe**, porque h=12 é o horizonte mais contaminado.

## 4. Controle interno (falseável)

**h=1 tem 0 linhas contaminadas, logo o resultado corrigido tem de ser IDÊNTICO ao de 30/08.**

- Critério: `|MAE_corrigido − MAE_original| < 0,01` em h=1, nas 4 células de h=1 do Bloco A e B.
- **Se h=1 divergir, a rodada está errada.** Aborta, investiga e não se interpreta nada do resto.

## 5. Critérios de decisão, fixados agora

**Ranking (decide se o grid de 120 precisa ser refeito):**

- Spearman entre a ordem das 6 antes e depois **≥ 0,90** *e* o 1º colocado mantido
  → **ranking declarado robusto**, o grid de 120 **não** é refeito, e isso fica registrado como a
  justificativa de não refazê-lo.
- Spearman < 0,90 **ou** troca do 1º colocado → **o grid de 120 precisa ser refeito**; nenhuma frase
  sobre "a melhor das 30" pode ser usada até lá.

**Métricas absolutas:**

- Toda métrica que mudar mais de **5%** passa a valer pelo **valor corrigido**, e o valor antigo é
  marcado como superado no ESTADO.md, com a data.
- Vale para: R² por horizonte, MAE, captura do pico e a frase "confiável até 1 mês".

**Vantagem do vetor em h=12 (M1 − M0, em MAE de avaliação, pareado por `data_alvo`):**

- Se o ganho corrigido ficar **≥ 70%** do ganho original → a alegação sobrevive, continua
  **exploratória**, e o teste focado de 60 execuções **não** precisa ser refeito.
- Se ficar **entre 30% e 70%** → o teste focado precisa ser refeito antes de qualquer menção.
- Se ficar **abaixo de 30%**, ou inverter de sinal → a alegação "o vetor ajuda em h=12" está
  **refutada** e sai do texto.

## 6. O que NÃO será rodado, e por quê

A correção só **tira** informação do treino, então só pode **piorar** o modelo. Resultados em que o
modelo já perdia ficam mais fortes, não mais fracos. Portanto **não** serão refeitos:

- **Rodada 3, ranking espacial** — o modelo já perde da persistência, e a persistência **não treina**,
  logo não tem vazamento. Corrigir aumenta a derrota.
- **Rodada 1, vetor no alarme de surto** — negativo, os dois braços com o mesmo viés.
- **Teste decisivo de alvos** — idem.
- **Rodada 4, janela de treino** — os três regimes têm o mesmo viés; é comparação relativa.
- **Grid completo de 120** — condicionado ao critério de ranking da §5.

**Ressalva declarada:** estes resultados passam a carregar a nota "medido com o corte de treino
antigo; a correção só reforçaria a conclusão". Não é o mesmo que "medido corretamente".

## 7. O que este teste NÃO responde

- Não corrige a margem do TOST na equivalência clima × vetor (outro problema, outra rodada).
- Não mede alarme de verdade (sensibilidade e antecedência por episódio); a captura do pico segue
  sendo razão de nível.
- Não revalida o ENSO nem refaz a seleção das 6 colunas de clima.

---

## Emendas

### EMENDA 1 — 13/09/2026, escrita com a rodada na célula 2 de 24 e ANTES de olhar qualquer resultado

Motivo: verificação adversarial independente **REPROVOU** a §6 e apontou uma falha de desenho na §2.
Nenhum número da rodada corrigida foi lido até aqui. O log só foi consultado para tempo de execução.

**E1.1 — A amostra do ranking não tinha nenhuma perda padrão (falha minha).**

As 6 configurações escolhidas (posições 1, 2, 4, 15, 26, 30) são **todas quantílicas**. A alegação mais
forte do projeto, "a perda importa mais que o algoritmo", compara justamente quantílico contra padrão,
e com essa amostra ela **não poderia ser testada**.

Acrescentadas 2 configurações, escolhidas agora e antes de ver resultado:

- **posição 20** — HistGradientBoosting · padrão · M1. É o par exato da vencedora: mesmo algoritmo,
  mesmo conjunto, só a perda muda. A diferença de 33,18 para 39,88 de MAE de calibração **é** o
  "+20,2%" citado no ESTADO.
- **posição 18** — LightGBM · padrão · M1. É a melhor configuração do LightGBM e sustenta o "+16,5%".

Passa a 8 configurações e 32 células. Custo adicional ~16 min, em segunda batelada.

**E1.2 — O critério de ranking da §5 era fraco demais para n=6.**

Com 6 pontos, o valor crítico do Spearman fica perto de 0,886, então exigir ≥ 0,90 é quase o acaso.
Critério substituído, agora com 8 configurações:

- O teste passa a ser **necessário, não suficiente**. Se **falhar**, o grid de 120 tem de ser refeito.
  Se **passar**, escreve-se "compatível com ranking robusto", nunca "ranking comprovado".
- Passa se, simultaneamente: o **1º colocado se mantém**; **nenhuma** configuração se move mais de
  **2 posições**; e a vantagem da perda quantílica sobre a padrão no par 1 × 20 permanece **≥ 10
  pontos percentuais** (era 20,2).
- Se a vantagem do par 1 × 20 cair abaixo de 10 pp, a frase "a perda importa mais que o algoritmo"
  sai do texto até o grid ser refeito.

**E1.3 — A dispensa da Rodada 4 está REFUTADA.**

A §6 alegava viés de modo comum nos três regimes de janela. Falso: as linhas contaminadas são as
mesmas h−1 em número, mas o treino mediano difere de **584 (expansível 2012) × 216 (expansível 2020)
× 299 (deslizante 6 anos)**. A **proporção** de contaminação é 2 a 3 vezes maior nos regimes menores,
e proporção é o que pesa num modelo de árvores.

- A Rodada 4 passa a **⏳ pendente de re-rodada** (12 células, ~25 min). **Não** roda agora.
- Até lá, proibido citar "treinar desde 2012 vence" como resultado fechado.
- Registro de uma expectativa, que é argumento e **não** medição: como os regimes menores são os mais
  contaminados, corrigir deveria puni-los mais e **reforçar** a vitória do expansível 2012. Se a
  re-rodada mostrar o contrário, isso é um achado maior, não um ajuste.

**E1.4 — Rodada 3: o modelo também vaza, não só a persistência estava em questão.**

A dispensa justificava apenas a persistência, que de fato não treina. Mas o LightGBM do ranking
espacial tem **o mesmo defeito de corte**.

- As **7 de 8** combinações em que o modelo já perde: conclusão **reforçada**, dispensa mantida.
- A **1 de 8** em que o modelo vence: **proibida de ser citada** sem re-rodada. É a célula com maior
  chance de ser artefato do vazamento.
- A frase "o sinal espacial é real" continua válida, porque ela se apoia em persistência contra
  climatologia (0,89 × 0,46), e **nenhuma das duas treina**.

**E1.5 — Rodada 1 e teste decisivo: risco de assimetria admitido, e agora medido de lado.**

Os dois braços sofrem o mesmo vazamento de rótulo, mas o braço com vetor tem **mais colunas**, logo
mais graus de liberdade para explorar as linhas com rótulo vazado. A dispensa tratava isso como
simétrico, sem prova.

Decisão, fixada agora: a **H4 desta rodada** (o ganho do M1 sobre o M0 em h=12) é um teste direto
dessa hipótese no caso da regressão. Portanto:

- Se o ganho do M1 encolher **menos de 30%** com a correção, a assimetria é fraca e as dispensas da
  Rodada 1 e do teste decisivo **ficam de pé**.
- Se encolher **30% ou mais**, a assimetria é real, e Rodada 1 e teste decisivo **entram na fila de
  re-rodada** antes de qualquer citação.

**E1.6 — Registro do que a correção NÃO resolve.**

Confirmado pela verificação: a escolha das 6 colunas de clima continua sendo feita **uma vez, por
posição, sobre os 60% iniciais da série**, e é reaproveitada em todos os cortes. Cerca de 140 dos
~300 cortes preveem com colunas escolhidas usando dado posterior à própria data de origem. Esta
rodada **não** corrige isso, por decisão de escopo. Fica como ⏳ próprio.

Confirmado também: nos **2 buracos reais** da série do M1 (vetor NaN em ago/2022 e na enchente de
2024), o filtro descarta **menos** de h−1 linhas, nunca mais. É o comportamento correto de um filtro
por data, e é a razão de não se poder usar a forma por posição.
