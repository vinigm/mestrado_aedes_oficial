# Estender a janela de lag ajuda o horizonte longo?

**Rodado em 23/09/2026.** Protocolo fixado em [PRE_DECLARACAO.md](PRE_DECLARACAO.md) antes de rodar.

---

## 1. A pergunta

O modelo prevê até **12 semanas à frente** e olha no máximo **4 semanas para trás**. Cobrir o vão
de 5 a 12 semanas melhora a previsão longa?

⚠️ Não é o teste de 30/08/2026. Aquele adicionou memória **anual** (lag52, lag104) e reprovou.
Entre `lag4` e `lag52` havia um vão de 48 semanas que nunca tinha entrado em modelo nenhum.

## 2. Validação obrigatória — passou

O braço de referência reproduziu os oito números publicados no painel, com tolerância de 0,15 no
MAE e 0,002 no R²:

| h | MAE medido | MAE painel | R² medido | R² painel |
|---|---|---|---|---|
| 1 | 98,0 | 98,0 | 0,898 | 0,898 |
| 4 | 219,7 | 219,7 | 0,628 | 0,628 |
| 8 | 272,6 | 272,6 | 0,450 | 0,450 |
| 12 | 278,8 | 278,7 | 0,437 | 0,437 |

O arranjo está correto. Sem isso nada seria reportado.

## 3. O que deu

Comparação **pareada por `data_alvo`**, avaliação 2024+, Wilcoxon, Holm sobre 8 comparações.

| Braço | h | MAE ref | MAE variante | Redução | p Holm |
|---|---|---|---|---|---|
| B_lags_ate_8 | 1 | 100,7 | 100,0 | +0,76% | 1,000 |
| B_lags_ate_8 | 4 | 228,3 | 224,9 | +1,48% | 1,000 |
| B_lags_ate_8 | **8** | 283,4 | 282,4 | +0,37% | 1,000 |
| B_lags_ate_8 | **12** | 290,0 | 284,8 | +1,80% | 1,000 |
| C_lags_ate_12 | 1 | 104,9 | 98,2 | **+6,37%** | 1,000 |
| C_lags_ate_12 | 4 | 237,8 | 230,4 | +3,14% | 1,000 |
| C_lags_ate_12 | **8** | 295,4 | 302,1 | **−2,28%** | 1,000 |
| C_lags_ate_12 | **12** | 302,3 | 304,5 | **−0,74%** | 1,000 |

O MAE da referência muda de linha para linha porque o pareamento muda: braço com lag maior perde
semanas no início da série, e só entram as semanas que os dois previram (n=98 para B, n=94 para C).

## 4. Conclusão

- **FATO:** nenhuma variante cumpre o critério pré-declarado. Nenhum p sobrevive a Holm — todos
  ficam em **1,000**, ou seja, nem perto.
- **FATO:** estender até 8 semanas dá ganhos de **0,4% a 1,8%**, sempre positivos mas sempre
  irrelevantes estatisticamente.
- **FATO:** estender até 12 semanas **inverte o sinal** onde importa. Melhora h=1 em 6,4% e piora
  h=8 em 2,3%. É o contrário da hipótese.
- **Leitura:** a informação de 5 a 12 semanas atrás já está contida nos 4 lags curtos, na média
  móvel de 4 semanas e na sazonalidade. Acrescentar colunas correlacionadas em horizonte longo
  gasta capacidade do modelo sem trazer sinal novo.

## 5. Limitação declarada antes de rodar

A seleção de clima rodou igual nos três braços, mas o conjunto candidato cresce junto com os lags.
Os braços escolheram colunas parcialmente diferentes:

| Braço | Colunas de clima |
|---|---|
| A | temp_media_lag4, umid_media, temp_media_lag3, temp_max, pressao_media_lag3, **pressao_media_lag4** |
| B | temp_media_lag4, umid_media, **temp_media_lag6**, temp_max, temp_media_lag3, pressao_media_lag3 |
| C | temp_media_lag4, umid_media, temp_max, **temp_media_lag6**, pressao_media_lag3, temp_media_lag3 |

Cinco das seis coincidem nos três. A sexta troca `pressao_media_lag4` por `temp_media_lag6`.
Como o resultado é negativo, essa diferença não muda a conclusão: ela poderia inflar um ganho
falso, não produzir uma piora falsa.

## 6. O que isto NÃO responde

- Não testa lag **maior que 12**. O vão de 13 a 51 semanas segue sem teste.
- Não testa lag longo **só no vetor**, mantendo casos curto.
- Não testa outra **função de perda** junto com lag estendido.
- O teste de 30/08 sobre lags anuais **continua não refeito** no protocolo sem vazamento.
