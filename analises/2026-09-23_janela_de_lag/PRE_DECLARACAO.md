# Pré-declaração — estender a janela de lag

**Escrita em 23/09/2026, ANTES de rodar.** Nada aqui pode ser alterado depois de ver o resultado;
mudança posterior vira emenda datada no fim deste arquivo.

---

## 1. A pergunta

O modelo prevê até **12 semanas à frente** e olha no máximo **4 semanas para trás**
(`LAGS_SEMANAS = [1, 2, 3, 4]`). Estender a janela curta melhora o horizonte longo?

**Origem:** pergunta do Vinicius em 23/09/2026. O `[1,2,3,4]` nunca foi escolhido — veio hardcoded
do código pré-refatoração (único commit: `355795a`, migração byte a byte) e provavelmente é resíduo
do horizonte de 1 a 4 semanas declarado no PEP, que o Vinicius declarou **errado** em 23/09: o
horizonte é de 3 meses.

⚠️ **Não é o teste de 30/08/2026.** Aquele ADICIONOU `casos_lag52`, `casos_lag104` e `vetor_lag52`,
ou seja, memória anual, e reprovou. Entre `lag4` e `lag52` existe um vão de 48 semanas que nunca
entrou em nenhum modelo. É esse vão que este teste cobre.

## 2. Hipótese

**H1:** prevendo a 8 e a 12 semanas, o modelo se beneficia de ver o mês 2 e o mês 3 para trás.
**H0:** não se beneficia — a informação de 5 a 12 semanas atrás já está contida nos 4 lags curtos,
na média móvel de 4 semanas e nos termos de sazonalidade.

## 3. Os braços

Todos com a configuração de referência: **HistGradientBoosting · quantil 0,85 · com vetor**,
passo 1, mínimo de 104 semanas de treino, corte de treino pela data da RESPOSTA.

| Braço | `LAGS_SEMANAS` | Features esperadas |
|---|---|---|
| **A_referencia** | `[1, 2, 3, 4]` | 20 |
| **B_lags_ate_8** | `[1, 2, 3, 4, 6, 8]` | 24 |
| **C_lags_ate_12** | `[1, 2, 3, 4, 6, 8, 10, 12]` | 28 |

A seleção de clima (top-6 por ganho) roda **igual nos três**, com o mesmo procedimento. Como o
conjunto candidato cresce junto com os lags, os braços podem escolher colunas de clima diferentes.
**Isso é declarado como limitação**, não corrigido: congelar o clima do braço A seria artificial,
já que na prática mudar `LAGS_SEMANAS` muda o pool. As colunas escolhidas por braço vão no relatório.

## 4. Métrica e teste

- **Métrica primária:** MAE no período de avaliação (`data_alvo >= 2024-01-01`), por horizonte.
- **Métrica secundária, descritiva:** R² no mesmo período.
- **Teste:** Wilcoxon pareado por `data_alvo`, sobre o erro absoluto da variante contra a
  referência. Pareado, conforme a regra do projeto — comparação não pareada não vale.
- **Família de correção múltipla:** 2 variantes × 4 horizontes (1, 4, 8, 12) = **8 comparações**,
  correção de **Holm**.

## 5. Critério de decisão, fixado agora

Uma variante **entra na referência** se, e só se:

1. reduzir o MAE em **h=8 E h=12** na avaliação; **e**
2. o p de Holm ficar **< 0,05 nos dois horizontes**.

Melhora em um horizonte só, ou melhora sem sobreviver a Holm, é **resultado exploratório** e não
troca a referência. Mesmo critério de h=8 e h=12 do teste de 30/08, de propósito, para os dois
serem comparáveis.

## 6. Validação obrigatória antes de aceitar qualquer conclusão

O braço **A_referencia** tem que reproduzir os números já publicados no painel:

| h | MAE | R² |
|---|---|---|
| 1 | 98,0 | 0,898 |
| 4 | 219,7 | 0,628 |
| 8 | 272,6 | 0,450 |
| 12 | 278,7 | 0,437 |

Se não reproduzir, **o teste é inválido** e nada dele é reportado até a divergência ser explicada.

## 7. Proibido

- Rodar com outros valores de lag depois de ver o resultado, para procurar melhora.
- Trocar a métrica, o critério ou a família depois de ver o resultado.
- Reportar melhora em h=1 ou h=4 como se cumprisse o critério: eles entram na família de correção,
  mas a decisão é em h=8 e h=12.

## 8. Custo medido antes de rodar

Cronometrado em 23/09/2026, medindo o início e o fim do walk-forward, não por analogia:

- **~214 ms** por corte no começo, **~377 ms** no fim, porque a janela de treino cresce.
- **~284 cortes** por horizonte, 12 horizontes.
- **~16 min por braço**, **~50 min no total**.
