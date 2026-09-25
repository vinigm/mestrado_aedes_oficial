# Régua de regras simples — os modelos batem previsão sem aprendizado de máquina?

**Data:** 25/09/2026 · **Script:** `calcular_regua.py` · **Saídas:** `saidas/`

> ⚠️ **Isto é uma medição DESCRITIVA, feita DEPOIS de os números de avaliação já
> terem sido vistos** (a bateria noturna de 23/09/2026 e o painel público já
> existiam antes deste teste). **Não é um teste pré-declarado.** Serve para
> decidir a régua oficial das próximas rodadas, não para reivindicar
> significância confirmatória sobre o resultado já visto.

---

## Pergunta

Os modelos de previsão de casos de dengue do projeto (9 configurações já
rodadas na bateria noturna de 23/09/2026) batem três regras simples de
previsão, sem nenhum aprendizado de máquina?

Nenhum modelo foi treinado neste teste — só se leram previsões já gravadas em
disco e a tabela semanal de casos.

## Método

- **Fonte dos modelos:** `previsoes_por_braco.csv` dos blocos 5 e 7 da bateria
  noturna (`analises/2026-09-23_bateria_noturna/`). 9 bracos distintos:
  `referencia`, `HistGB_folha20_M1`, `HistGB_folha20_M0` (bloco 7) e
  `HistGB_M1`, `HistGB_M0`, `LightGBM_M1`, `LightGBM_M0`, `GradBoost_M1`,
  `GradBoost_M0` (bloco 5).
- **Fonte da série de casos:** `tabela_final.csv`, 725 semanas contínuas
  (7 em 7 dias, sem buraco nem duplicata — validado antes de qualquer
  cálculo) de 2012-09-23 a 2026-08-09, com 297 semanas sem
  `casos_confirmados` (282 antes de 2018-02-18, 15 nas mais recentes).
- **Períodos:** `calibracao` (`data_alvo < 2024-01-01`),
  `calibracao_epidemica` (`2022-01-01 <= data_alvo < 2024-01-01`) e `avaliacao` (`data_alvo >= 2024-01-01`,
  102 semanas por horizonte). `calibracao_epidemica` é **subconjunto** de
  `calibracao`, não uma fatia à parte.
- **Métricas:** MAE, perda quantílica no quantil 0,85 (a mesma perda que
  treina o cenário adotado), R² e n — por horizonte (h=1..12), por período e
  por ano do alvo.

## As três regras simples

| Regra | Definição | Observação |
|---|---|---|
| **Persistência** | `casos_confirmados` na semana de origem (`data_alvo - h` semanas) | É o mesmo número que o modelo recebe como atributo (lag h) — comparação usa a mesma informação |
| **Sazonal** | `casos_confirmados` em `data_alvo - 52` semanas | Como h ≤ 12, esse número tem ≥ 40 semanas de idade na origem: já era maduro |
| **Climatologia** | Média de `casos_confirmados` em `data_alvo - 52k` semanas, k=1,2,3,..., só com semanas não vazias | Passo fixo de 52 semanas ignora anos de 53 semanas — simplificação deliberada, igual à da regra sazonal |

Nenhuma linha ficou vazia em nenhuma das três regras (0 de 3.474 pares
h×data_alvo, ver `saidas/linhas_vazias_por_regra.csv`) — o histórico de casos
já é longo o bastante para nunca faltar origem.

## Âncoras numéricas — reproduzidas integralmente

As 53 âncoras dadas pelo orquestrador (MAE e perda quantílica em h=1,4,8,12
na avaliação; MAE em h=12 por ano; teto histórico e maior previsão por ano)
**batem todas, sem exceção**, depois da correção de desenho descrita abaixo.
Ver `saidas/conferencia_ancoras_numericas.csv`.

| h | referencia (MAE) | folha20_M1 (MAE) | persistência (MAE) | sazonal (MAE) |
|---|---|---|---|---|
| 1 | 98,0 | 133,6 | 83,3 | 202,1 |
| 4 | 219,7 | 199,6 | 279,0 | 213,2 |
| 8 | 272,6 | 223,2 | 531,0 | 216,2 |
| 12 | 278,8 | 243,8 | 697,5 | 217,8 |

## Divergência encontrada e investigada (não forçada)

Na primeira rodada, a métrica "solta" das regras (sem parear com um braço
específico) usava a **união** dos pares (h, data_alvo) dos 9 bracos como
grade de cálculo. Isso divergia das âncoras (ex.: MAE da persistência em h=1
saía 100,2 em vez de 83,3).

**Causa raiz, investigada:** os 4 bracos **M0** (sem vetor) cobrem **7
semanas a mais** que os bracos **M1**/`referencia` em alguns horizontes (ex.:
maio–junho/2024 em h=1) — um buraco nas colunas do vetor derruba essas
semanas do `dropna` dos modelos que usam vetor, mas não afeta quem não usa.
Isso é um **FATO medido**, não hipótese: confirmado comparando os conjuntos
exatos de `data_alvo` por braço (`referencia` e todos os M1 têm datas
idênticas entre si; os M0 têm as mesmas datas **mais** um bloco extra).

**Decisão de desenho:** a grade de (h, data_alvo) usada para a métrica
"solta" das 3 regras passou a ser a do braço `referencia` — não a união dos
9. As comparações pareadas (Wilcoxon) não foram afetadas por essa escolha,
porque já pareiam por `data_alvo` via *merge* — a interseção naturalmente
restringe ao conjunto do braço mais estreito em cada comparação.

## Consistência dos dados

- **`real` (previsões) vs `casos_confirmados` (tabela final): 0 divergências**
  em 31.842 linhas — confirmado, não hipótese.
- **HistGB_M1 (bloco 5) é duplicata exata de `referencia` (bloco 7):**
  3.474 linhas em comum, diferença máxima 0,0 em previsto e em real.
  Confirmado, não hipótese.

## Skill score — avaliação (2024+)

`skill = 1 - MAE_modelo / MAE_melhor_regra`. Negativo = a melhor regra bate o
modelo.

| h | referencia | folha20_M1 | LightGBM_M1 | melhor regra |
|---|---|---|---|---|
| 1 | -0,176 | -0,604 | -0,595 | persistência |
| 4 | -0,030 | 0,064 | 0,047 | sazonal |
| 8 | -0,261 | -0,032 | -0,073 | sazonal |
| 12 | -0,280 | -0,119 | -0,135 | sazonal |

**Leitura, separando fato de framing:**
- **FATO:** contra a **persistência**, os modelos ganham forte e de forma
  estatisticamente significativa em h=8 e h=12 (Holm p < 0,0001, reduções de
  48% a 65% no MAE) — mas em h=1 é a **persistência que bate os modelos**
  (LightGBM_M1 perde para ela de forma significativa, p Holm = 0,021).
- **FATO:** contra a **sazonal**, o quadro é oposto: em h=1 os modelos ganham
  significativamente (reduções de 42% a 54%), mas em h=4, 8 e 12 o placar é
  **negativo ou perto de zero e nunca significativo** — a sazonal empata ou
  supera os modelos no horizonte que mais importa para vigilância (3 meses).
- **HIPÓTESE a investigar**, testada na
  [bateria de formulação do alvo](../2026-09-25_bateria_formulacao_do_alvo/): o modelo recebe o lag
  de 52 semanas contado da **origem**, e a régua usa a semana **alvo** do ano anterior. Em h=12 são
  números a 12 semanas de distância. A informação sazonal existe, mas não chega ao modelo alinhada.
  - 🚫 **Refutada no mesmo dia.** Com a semana-alvo do ano anterior como atributo, o erro de h=12 subiu
    de 243,8 para 300,9.
  - ⚠️ A explicação "os modelos puxam para a média" não se sustenta: a perda quantílica 0,85 puxa a
    previsão **para cima** da mediana, não para a média.

## Skill score — calibração epidêmica (2022–2023)

| h | referencia | folha20_M1 | melhor regra |
|---|---|---|---|
| 1 | -0,157 | -1,267 | persistência |
| 4 | 0,138 | -0,128 | sazonal |
| 8 | 0,143 | -0,128 | sazonal |
| 12 | 0,074 | 0,056 | sazonal |

`referencia` (folha mínima 5, o cenário adotado) supera a melhor regra em
quase todos os horizontes de médio/longo prazo neste período mais curto,
enquanto `folha20_M1` fica sistematicamente atrás — reforça a escolha de
folha 5 como referência, mas com amostra menor (2022–2023, sem os picos
extremos de 2024–2025).

## Teto (maior previsão do ano vs. maior caso já visto antes dele)

| Ano | Teto histórico | referencia (h=12) | folha20_M1 (h=12) |
|---|---|---|---|
| 2024 | 879 | 364 (não ultrapassa) | 525 (não ultrapassa) |
| 2025 | 1.855 | 1.399 (não ultrapassa) | 1.614 (não ultrapassa) |

**FATO:** nenhum dos dois modelos jamais previu, em h=12, um valor acima do
maior caso histórico já visto até aquele ano — mesmo em 2024 e 2025, anos de
pico inédito. A regra `persistência` "ultrapassa" o teto em ambos os anos,
mas isso não é mérito: ela só ecoa o valor real de poucas semanas atrás, que
naturalmente já está subindo durante o próprio surto.

⚠️ **O teto não é o que prende o modelo em 2024.** A maior previsão de 3 meses em 2024 foi **364**, bem
abaixo do teto de **879**. O modelo não chegou nem ao que já tinha visto. Isso é coerente com a lápide de
30/08/2026 no [HISTORICO_DE_TESTES.md](../../HISTORICO_DE_TESTES.md) §1.3: o limite de extrapolação
das árvores não explica o viés de pico.

## Comparação de Holm — resumo

Família de 72 comparações (9 bracos × 2 regras de controle × 4 horizontes),
avaliação, Wilcoxon pareado por `data_alvo`. Ver
`saidas/comparacoes_pareadas_holm.csv` para a tabela completa.

- **27 de 72 comparações sobrevivem a Holm (p < 0,05).**
  - ⚠️ **Corrigido em 25/09/2026 pela certificação:** o rascunho dizia 18. O CSV sempre teve 27.
  - ⚠️ A família de 72 inclui `HistGB_M1`, que é duplicata exata de `referencia`. Sem a duplicata,
    são **64 comparações distintas e 24 significativas**. A família maior só torna o Holm mais
    conservador; nenhuma conclusão muda.
- **Contra a persistência:** os modelos ganham em h=8 e h=12, todos os 9 bracos. Em h=1 a persistência
  ganha do `LightGBM_M1`.
- **Contra a sazonal em h=1:** os modelos ganham em 5 bracos.
- **Contra a sazonal em h=12, os 3 bracos SEM vetor perdem com significância:**

  | Braço | Queda do erro contra a sazonal | p Holm |
  |---|---|---|
  | `HistGB_M0` (folha 5) | −30,9% | 0,018 |
  | `HistGB_folha20_M0` | −27,7% | 0,001 |
  | `LightGBM_M0` | −34,3% | 0,003 |

  Os bracos **com** vetor também perdem em h=12, mas **sem significância**: `referencia` −28,0%
  (p Holm 0,17), `HistGB_folha20_M1` −11,9% e `LightGBM_M1` −13,5% (p Holm 1,0).
  - **Leitura, não teste:** o vetor aproxima o modelo da régua sazonal em 3 meses, mas não o faz
    passar dela.
- **Nenhuma comparação contra `sazonal` em h=4 ou h=8 é significativa** —
  não dá para afirmar que os modelos batem a sazonal nesses horizontes.

## Fato vs. Hipótese

| Rótulo | Afirmação |
|---|---|
| FATO | Os 9 bracos batem a persistência com folga e significância em h=8 e h=12 |
| FATO | Nenhum braço bate a sazonal com significância em h=4 ou h=8 |
| FATO | Em h=1, a persistência é competitiva e chega a bater `LightGBM_M1` com significância |
| FATO | Nenhum modelo já previu acima do teto histórico em h=12, em nenhum ano |
| FATO | O buraco de 7 semanas nos bracos M1 (maio–jun/2024) vem de dropna em colunas do vetor |
| FATO já conhecido | O buraco coincide com a enchente de maio e junho de 2024, semanas sem registro do vetor. O mesmo buraco apareceu no bloco 5 da bateria noturna |
| FATO | Na calibração epidêmica 2022-2023, a `referencia` bate a melhor regra em h=4, 8 e 12; na avaliação 2024+, perde. O mesmo modelo muda de lado conforme a temporada |
| HIPÓTESE | Por que os modelos perdem para a sazonal em horizontes longos — não testado formalmente aqui |

## Desvios e decisões tomadas

1. **Grade das regras simples = pares (h, data_alvo) do braço `referencia`**,
   não a união dos 9 bracos — decisão registrada e justificada acima, tomada
   após investigar a divergência contra as âncoras.
2. **R² não definido quando n < 2** (não ocorreu em nenhuma célula real deste
   teste, mas a função trata o caso para não quebrar em recortes futuros
   menores).
3. **`previsao_ultrapassa_teto` retorna `False`** quando `maior_previsao_do_ano`
   ou `teto_historico_antes_do_ano` são NaN (não ocorreu neste teste, já que
   climatologia/persistência/sazonal nunca ficaram vazias na avaliação).
