# VERIFICAÇÃO ADVERSARIAL — Teste A (equivalência clima x vetor)

> Pasta compartilhada — ver `README.md` (Teste C) e `README_teste_a.md`
> (relatório original do Teste A). Este arquivo cobre só a auditoria
> independente do Teste A.

## O que este teste responde

Confere, de forma **independente** (sem ler nem importar o código do
Teste A), se os números que o Teste A reportou em
`resultados_testes_equivalencia.csv` estão corretos — reimplementando do
zero, só a partir dos CSVs de previsões já salvos, o MAE pareado, o teste
DM-HLN (4 células à mão), o TOST (3 margens) e o bootstrap (semente
diferente), e checando rastreabilidade de vazamento temporal.

**Script:** `verificacao_teste_a.py` (roda em ~1,2s de CPU — bem dentro do
orçamento). **Só leitura** dos CSVs do Teste A e de `tabela_final.csv`
(projeto); nada foi alterado.

## Números-âncora recalculados (`verificacao_teste_a_resultados.csv`)

| versão | h | MAE clima (meu) | MAE clima (original) | DM-HLN p (meu, 4 células) | DM-HLN p (original) |
|---|---|---|---|---|---|
| puro | 1 | 174,6077 | 174,6077 | 0,059040 | 0,059040 |
| puro | 12 | 172,0836 | 172,0836 | 0,881423 | 0,881423 |
| com_ar | 1 | 71,8943 | 71,8943 | 0,112135 | 0,112135 |
| com_ar | 12 | 144,5141 | 144,5141 | 0,675876 | 0,675876 |

Todos os 8 MAEs (clima e vetor, puro e com_ar, h=1/4/8/12) batem com
`resultados_testes_equivalencia.csv` do Teste A até a 4ª casa decimal
(0 discrepâncias de `real` no pareamento clima×vetor, nas 8 combinações).

As 4 células de DM-HLN recalculadas à mão batem exatamente com o original
(estatística e p-valor). Os p-valores do TOST (3 margens × 8 combinações)
também batem, e todos os 24 vereditos `equivalente_a_5pct` reproduzidos são
`False`, igual ao original.

**Bootstrap com semente diferente** (777001, no lugar de 20260816):
o IC 95% de ΔMAE mudou no máximo **6,7%** de largura (puro h4: 99,2 →
92,5) entre as 8 combinações — abaixo do limiar de 10% pedido — os
intervalos são estáveis, não é artefato da semente escolhida.

## Vazamento temporal / rastreabilidade — REPROVADO no critério estrito

Os CSVs de previsões (`data,h,real,pred`) têm **só uma coluna de data**,
não duas (origem e alvo). Reconstruí a semântica por engenharia reversa
contra `tabela_final.csv` (não é possível saber pela leitura do CSV
sozinho): em 70/70 linhas testadas (amostra de 7 combinações
conjunto×horizonte, 10 linhas cada), `data` = semana de **origem** e
`real` = casos em `data + h` semanas (o alvo), sem nenhuma divergência.
Isso confirma que **mecanicamente não há vazamento** (a previsão de
`data+h` usa só informação disponível em `data`, e o walk-forward treina
só com linhas estritamente anteriores ao corte).

Mas o critério de auditoria pedido era explícito: "datas de origem e alvo
devem estar gravadas; se não estiverem, REPROVE por rastreabilidade". Elas
não estão — só uma data existe na coluna, e sua semântica (origem, não
alvo) não é auto-evidente sem esse cruzamento externo que fiz aqui. Um
terceiro auditor, sem acesso a `tabela_final.csv` ou sem saber ler o
código-fonte do Teste A, não conseguiria confirmar a ausência de
vazamento só com os CSVs publicados.

**Recomendação:** Teste A deveria adicionar uma coluna `data_alvo` (ou
`data_origem` + `data_alvo` explícitas) aos 20 CSVs de previsões, para que
a rastreabilidade não dependa de reconstrução externa.

## Arquivos desta verificação

- `verificacao_teste_a.py` — script único de auditoria independente.
- `verificacao_teste_a_resultados.csv` — MAE, ΔMAE, DM-HLN (4 células),
  TOST (3 margens) e IC bootstrap (semente nova) recalculados por
  versão×horizonte.
- `verificacao_teste_a_rastreabilidade.csv` — resultado da checagem de
  rastreabilidade (colunas dos CSVs de previsão, se há data de origem e
  alvo separadas).
