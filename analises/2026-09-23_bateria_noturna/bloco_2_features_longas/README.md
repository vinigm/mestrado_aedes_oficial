# Bloco 2 — Features de longo prazo, refeito sem vazamento

> **Rodado em 23/09/2026, das 20h41 às 22h00** (1h19). Parte da [bateria noturna](../README.md).
> Protocolo fixado antes em [PRE_DECLARACAO.md](PRE_DECLARACAO.md).

---

## Em uma frase

**O único sinal positivo do projeto era artefato do vazamento.** O ENSO, que derrubava o erro de h=8 em
7,1% no teste de agosto, agora não muda nada em h=8 (o erro sobe 0,06%) e **aumenta o erro de h=12 em
11,6%**. Nenhum grupo de feature longa entra na referência.

---

## 1. De onde veio este teste

### A pergunta original, de agosto

Em 30/08/2026 o projeto perguntou: *o modelo se degrada tanto em horizonte longo por falta de
informação de longo prazo?* O conjunto de referência só enxerga 4 semanas para trás. Nada nele carrega
o ciclo anual, a anomalia climática da estação, a chuva acumulada de meses, nem a fase do El Niño.

O teste de agosto ([`analises/2026-08-30_features_longo_prazo/`](../../2026-08-30_features_longo_prazo/))
adicionou quatro grupos de colunas ao conjunto de referência e mediu o MAE em h=8 e h=12.

### O que agosto concluiu

- Nenhum grupo passou no critério de melhorar h=8 **e** h=12 juntos.
- **Exceção parcial: o ENSO melhorou h=8 em −7,1% de MAE.** Não passou no critério porque não melhorou
  h=12, mas virou o único resultado positivo do projeto. Aparece no `PENDENCIAS.md` como rodada
  candidata: *"Validar o ENSO dentro do grid — passou isolado (+7% em h=8)"*.

### Por que precisava ser refeito

Em 13/09/2026 descobriu-se um vazamento temporal: o treino era cortado pela **posição** da linha, e não
pela **data da resposta**. Uma linha de treino podia carregar um alvo que, naquela data, ainda não
tinha acontecido. O teste de agosto tinha esse defeito — está no script:
`treino = validos.iloc[:indice_corte]`.

Além disso, o quantil de referência mudou de 0,80 para 0,85 depois da correção.

O teste estava na lista explícita de **não refeitos**. O número do ENSO nunca tinha sido conferido no
protocolo limpo.

---

## 2. O que foi feito

### Os cinco braços, idênticos aos de agosto

| Braço | O que acrescenta | Colunas |
|---|---|---|
| **A_referencia** | nada, é o cenário adotado | 20 |
| **A+B_lags_anuais** | `casos_lag52`, `casos_lag104`, `vetor_lag52` — memória de 1 e 2 anos | 23 |
| **A+C+D_clima_longo** | anomalia de temperatura, chuva e umidade contra a norma daquela semana do ano; chuva e temperatura acumuladas em 8 e 12 semanas | 27 |
| **A+E_enso** | `nino34_anom`, `oni` — a fase do El Niño e da La Niña | 22 |
| **A+TUDO** | os quatro grupos juntos | 32 |

### Os dois consertos em relação a agosto

- **Corte de treino pela data da resposta**, via `motor/corte_temporal.selecionar_treino_ja_respondido`.
- **Quantil 0,85**, a referência atual.

### Um cuidado de desenho

As colunas extras entram **por fora** da seleção de clima, em todos os braços. Sem isso, as colunas de
anomalia e acúmulo cairiam no grupo de clima pelo nome e disputariam as seis vagas — e cada braço teria
um clima diferente, misturando dois efeitos.

**Conferido:** os cinco braços escolheram exatamente as mesmas seis colunas de clima:
`temp_media_lag4`, `umid_media`, `temp_media_lag3`, `temp_max`, `pressao_media_lag3`, `pressao_media_lag4`.
A única diferença entre eles é o grupo testado.

### A norma histórica não vaza

A anomalia compara a semana com a média **das ocorrências anteriores** da mesma semana do ano:
`expanding().mean().shift(1)`. Usar a média da série inteira faria a feature enxergar o futuro. Isso já
estava certo em agosto e foi copiado literalmente.

---

## 3. Trava de validação — passou

A referência reproduziu os oito números publicados no painel antes de qualquer resultado novo ser lido:

| h | MAE medido | MAE painel | R² medido | R² painel |
|---|---|---|---|---|
| 1 | 98,0 | 98,0 | 0,898 | 0,898 |
| 4 | 219,7 | 219,7 | 0,628 | 0,628 |
| 8 | 272,6 | 272,6 | 0,450 | 0,450 |
| 12 | 278,8 | 278,7 | 0,437 | 0,437 |

---

## 4. Resultado

Comparação pareada por `data_alvo`, período de avaliação (2024+), Wilcoxon, Holm sobre 16 comparações.
Redução positiva = melhorou; negativa = piorou.

| Braço | h=1 | h=4 | **h=8** | **h=12** |
|---|---|---|---|---|
| A+B lags anuais | +7,4% | +5,7% | +0,1% | −3,3% |
| A+C+D clima longo | −0,9% | +6,0% | −8,2% | −4,9% |
| **A+E ENSO** | −1,9% | +1,0% | **−0,1%** | **−11,6%** |
| A+TUDO | +0,9% | −1,5% | **−13,9%** \* | −13,0% |

\* único resultado que sobrevive a Holm: p = **0,030**. É uma **piora** significativa.

Das outras 15 comparações, 14 ficam com p de Holm igual a **1,000**; a restante é o A+TUDO em h=12,
com 0,418. Nenhuma chega perto de 0,05.

### Veredito pelo critério pré-declarado

**Nenhum dos quatro grupos entra na referência.**

---

## 5. O que isso quer dizer

### O ENSO

Variação do **erro** (MAE) ao acrescentar o ENSO. Negativo é bom.

| | Agosto, contaminado | Setembro, limpo |
|---|---|---|
| h=8 | erro caiu **7,1%** | erro subiu 0,1% |
| h=12 | erro caiu 0,2% | erro subiu **11,6%** |

O ganho de agosto em h=8 **desapareceu**. E em h=12 o ENSO passou a **piorar** o modelo.

- **FATO:** o sinal positivo do ENSO não sobrevive à correção do vazamento.
- **Hipótese, não medida:** o vazamento inflava justamente as features que variam devagar. O ENSO muda de mês em mês.
  Com o treino cortado pela posição, o modelo via alvos futuros junto com um ENSO que já apontava para
  eles — e aprendia uma relação que, sem o vazamento, não existe na forma em que foi medida.
- ⚠️ **Consequência para o `PENDENCIAS.md`:** a rodada candidata *"Validar o ENSO dentro do grid"* perde
  a base. O "+7% em h=8" que a sustentava era vazamento.

### Juntar tudo é o pior

O A+TUDO piora h=8 em **13,9%** com significância estatística. Acrescentar 12 colunas a um modelo que
treina com ~300 semanas dá ao algoritmo mais formas de se ajustar ao ruído do que sinal novo para
aprender. É o mesmo padrão que agosto já tinha visto — lá o A+TUDO também era o pior em h=8 e h=12.

### Os lags anuais ajudam no curto prazo

A+B melhora h=1 em **7,4%** e h=4 em **5,7%**, mas nenhum dos dois sobrevive a Holm, e o critério
decidia em h=8 e h=12. **Exploratório**, não achado.

### O que agosto dizia que continua valendo

A conclusão de agosto se mantém — **nenhuma feature longa resolve o horizonte longo** — e agora com
números limpos. A degradação com o horizonte segue parecendo **limite do dado**, não falta de feature.

---

## 6. Limitações

- **Um único arranjo de colunas por grupo.** Não se testou, por exemplo, o ENSO defasado alguns meses,
  que é como a literatura costuma usá-lo — o efeito do El Niño no clima local chega com atraso.
- **Hiperparâmetros fixos.** Com 32 colunas, um modelo mais regularizado poderia aproveitar melhor o
  A+TUDO. O [bloco 6](../bloco_6_hiperparametros/) busca hiperparâmetros, mas só no conjunto de 20.
- **Avaliação em ~100 semanas**, quase todas de duas temporadas. O poder estatístico é baixo: um ganho
  real pequeno pode não aparecer.

---

## 7. Arquivos

| Arquivo | O que é |
|---|---|
| [`PRE_DECLARACAO.md`](PRE_DECLARACAO.md) | protocolo, escrito antes de rodar |
| [`rodar.py`](rodar.py) | o script, usando o motor [`../harness.py`](../harness.py) |
| `execucao.log` | a saída completa da execução |
| `saidas/previsoes_por_braco.csv` | uma previsão por linha, com `data_alvo`, para qualquer reanálise |
| `saidas/comparacoes.csv` | a tabela do §4, com p bruto e p de Holm |
| `saidas/resumo_dos_bracos.csv` | colunas e clima escolhido por braço |
