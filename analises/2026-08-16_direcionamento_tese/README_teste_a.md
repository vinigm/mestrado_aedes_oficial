# TESTE A — Equivalência clima x vetor na previsão de casos (nível cidade)

> Esta pasta é compartilhada com outros testes (ver `README.md`, que documenta o
> Teste C). Este arquivo cobre **só o Teste A** para não sobrescrever o dos outros.

## O que este teste responde

Um modelo que usa **só clima** e um modelo que usa **só dados do vetor**
(armadilhas) são estatisticamente **equivalentes** para prever casos
confirmados de dengue em Porto Alegre, semana a semana? Rodado em duas
versões pré-declaradas:

- **puro** — sem nenhuma defasagem de `casos` nos dois lados, para isolar a
  fonte de informação (clima vs vetor) da autocorrelação da própria série.
- **com_ar** — os dois lados recebem os mesmos componentes autorregressivos
  de casos (`casos_lag1..4`, `casos_mm4`); é a versão operacionalmente
  realista (o que se rodaria em produção).

**Modelos NÃO foram re-rodados nem re-testados fora deste script.** Todo o
walk-forward (LightGBM, janela expansível, mínimo 104 semanas) foi rodado do
zero aqui, réplica das fórmulas de `motor/walk_forward_regressao.py`,
`dominio/features.py` e `config/experimentos/cidade_regressao.py` do projeto
— nenhum arquivo do projeto foi lido por import nem alterado; o script é
autocontido (só lê `tabela_final.csv`).

## Definição dos conjuntos de features

| Conjunto | Colunas | N features |
|---|---|---|
| `SO_CLIMA_PURO` | as 22 colunas com prefixo temp/precip/umid/orvalho/pressao/radiacao/vento/dias_de_chuva (valor contemporâneo, sem defasagem) + `sem_sin`/`sem_cos` | 24 |
| `SO_VETOR_PURO` | `aedes_aegypti_por_armadilha` + suas defasagens 1-4 + `vetor_mm4` + `sem_sin`/`sem_cos` | 8 |
| `SO_CLIMA_AR` | `SO_CLIMA_PURO` + `casos_lag1..4` + `casos_mm4` | 29 |
| `SO_VETOR_AR` | `SO_VETOR_PURO` + `casos_lag1..4` + `casos_mm4` | 13 |

Em todo conjunto, o motor de walk-forward soma ainda `alvo_sin`/`alvo_cos`
(sazonalidade da semana-alvo) — igual ao projeto, e igual para os dois lados
da comparação, então não favorece nenhum conjunto.

**Decisão de protocolo registrada:** "todas as colunas de clima" foi lido
como as 22 colunas de clima já existentes em `tabela_final.csv` (valor
contemporâneo). O projeto também gera defasagens de `temp_media`,
`precip_total_mm`, `orvalho_media`, `umid_media` e `pressao_media` em
`dominio/features.py`, mas o enunciado do Teste A não pediu isso — não
foram incluídas, para manter a definição de "clima" idêntica à lista de
prefixos dada no enunciado.

## Alinhamento pareado (por que N varia entre clima e vetor)

Clima só tem dado a partir de **2018-12-30** (as 337 primeiras semanas de
`tabela_final.csv` são NaN em todas as colunas de clima); o vetor tem 7
semanas NaN isoladas (2017-12/2018-01, 2022-08-21, 2024-04-28 a 05-12) que
se propagam até 4 semanas via defasagem. Isso faz cada conjunto ter um
número de semanas válidas ligeiramente diferente — os testes pareados (DM,
TOST, bootstrap) usam a **interseção de datas** entre clima e vetor, nunca a
união. Confirmado numericamente: a persistência (que não depende de clima
nem vetor) teve previsão válida em **100% das semanas pareadas** em todas
as 8 combinações versão×horizonte — não há semana pareada sem referência.

## Números-âncora (`resultados_testes_equivalencia.csv`)

| versão | h | n pareado | MAE clima | MAE vetor | MAE persistência | ΔMAE (vetor−clima) | IC95% boot | DM-HLN p |
|---|---|---|---|---|---|---|---|---|
| puro | 1 | 266 | 174,61 | 151,32 | **45,84** | −23,29 | [−71,6; 20,7] | 0,059 |
| puro | 4 | 263 | 165,79 | 160,93 | 150,13 | −4,86 | [−56,8; 42,4] | 0,863 |
| puro | 8 | 259 | 169,08 | 156,07 | 279,15 | −13,01 | [−90,7; 32,7] | 0,781 |
| puro | 12 | 255 | 172,08 | 178,52 | 364,79 | +6,44 | [−65,1; 42,7] | 0,881 |
| com_ar | 1 | 266 | 71,89 | 80,41 | **45,84** | +8,52 | [−3,2; 23,7] | 0,112 |
| com_ar | 4 | 263 | 104,17 | 119,25 | 150,13 | +15,08 | [−8,6; 41,1] | 0,287 |
| com_ar | 8 | 259 | 110,89 | 115,44 | 279,15 | +4,55 | [−17,9; 24,4] | 0,757 |
| com_ar | 12 | 255 | 144,51 | 131,49 | 364,79 | −13,02 | [−63,8; 24,0] | 0,676 |

**Nenhum DM-HLN é significativo a 5%** (todos p > 0,05) — não há evidência de
diferença de acurácia entre clima e vetor em nenhum horizonte, em nenhuma
das duas versões.

**TOST: equivalência NÃO declarada em nenhuma margem (5%, 10% ou 15% do MAE
do SO_CLIMA), em nenhum horizonte, em nenhuma versão** — ver colunas
`TOST_margem_{5,10,15}pct_p_valor` e `_equivalente_a_5pct` (todas `False`)
em `resultados_testes_equivalencia.csv`. Ou seja: com o N disponível
(255-266 semanas pareadas), o teste não tem poder para declarar equivalência
nem para declarar diferença — a diferença de fonte de dado é
estatisticamente **indeterminada**, não "igual" nem "diferente".

**Achado lateral que chama atenção (fato, não hipótese):** na versão
**puro**, h=1, a persistência ingênua (MAE 45,8) bate os dois modelos por
larga margem (clima 174,6; vetor 151,3) — sem nenhum componente
autorregressivo, LightGBM perde feio para "repetir o valor de ontem" no
horizonte mais curto. Na versão **com_ar**, h=1, a persistência (45,8) ainda
bate os dois modelos (clima 71,9; vetor 80,4), embora a diferença encolha
bastante. Isso é só um número relatado, não uma conclusão qualitativa sobre
utilidade do modelo (fora do escopo deste teste).

## Ressalvas metodológicas (decisões de implementação, registradas)

- ⏳ **Variância do TOST**: usa o mesmo estimador de variância de longo
  prazo do teste DM (autocovariância truncada em h-1 defasagens), mas SEM o
  fator de correção HLN — o fator HLN foi derivado para a hipótese nula
  ΔMAE=0 (teste DM), não para ΔMAE=±margem (TOST). Escolha documentada no
  código (`testar_tost_equivalencia`), não testada contra pacote de
  referência externo.
- ⏳ Bootstrap em blocos móveis (8 semanas, 2000 reamostras, semente fixa
  `20260816`) — não circular; blocos sorteados só entre posições iniciais
  que cabem inteiras na série.
- 🚫 `LGBMRegressor` rodou com `n_jobs=1` (script todo em ~1,7 min), não
  `n_jobs=-1` como o projeto: um teste de bancada mostrou que o overhead de
  criar pool de threads a cada re-treino (são ~2.070 re-treinos no total)
  multiplicava o tempo por ~12x (0,03s → 0,36s por fit) sem nenhum ganho,
  dado o tamanho pequeno de cada treino (100-420 linhas). Não muda a árvore
  construída nem o resultado do modelo (sem bagging/feature_fraction, o
  LightGBM é determinístico em 1 thread), só o tempo de parede.
- ⏳ CPU real do script: **1,7 min** (bem dentro do orçamento de 5-25 min);
  não houve necessidade de cortar escopo.

## Arquivos desta pasta (Teste A)

- `teste_a_equivalencia_clima_vetor.py` — script único, roda em ~1,7 min.
- `previsoes_{CONJUNTO}_h{H}.csv` (16 arquivos) — previsões semana a semana
  (`data`, `h`, `real`, `pred`) para os 4 conjuntos × 4 horizontes.
- `previsoes_persistencia_h{H}.csv` (4 arquivos) — previsão ingênua de
  referência (repete o valor atual), mesmas colunas.
- `resultados_testes_equivalencia.csv` — uma linha por versão×horizonte,
  com MAE, ΔMAE, IC95% bootstrap, DM-HLN e TOST (3 margens).
