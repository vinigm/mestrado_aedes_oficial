# Comparação direta com modelos publicados

> **Montada em 25/09/2026**, a pedido do Vinicius: *"nosso modelo tem x% de erro, o modelo y tem z% de erro e
> foi usado para isso e aquilo"*. As definições das métricas de cada artigo foram extraídas e verificadas na
> fonte ([`grupo_1.md`](grupo_1.md), [`grupo_2.md`](grupo_2.md) e as verificações). As nossas foram calculadas
> nas mesmas unidades por [`metricas_do_projeto.py`](metricas_do_projeto.py).

---

## Em uma frase

**Contra os estudos de pesquisa em Porto Alegre e no Brasil, o nosso modelo tem números iguais ou melhores.
Contra os sistemas operacionais da Ásia, ele é pior em 3 meses: eles vencem a régua sazonal, e nós não.**

---

## ⚠️ Por que não dá para comparar o erro em casos

- Singapura tem centenas de casos por semana; Porto Alegre tem semanas com zero. Um erro de 50 casos é
  pequeno lá e enorme aqui.
- Por isso a comparação usa só métricas **relativas**, e em cada linha a definição do artigo foi conferida.
- O nosso modelo prevê o **quantil 0,85**, de propósito acima do valor mais provável. Isso **infla** os
  nossos erros percentuais contra modelos que preveem a média.

Nossa avaliação: **2024 a fev/2026, 102 semanas por horizonte**, com as duas maiores temporadas da série.

---

## 1. Erro percentual (MAPE)

| Modelo | Uso | Erro em 1 semana | Erro em 3 meses |
|---|---|---|---|
| **LASSO, Shi et al. 2016** | **operacional**: agência ambiental de Singapura, gestão de leitos e controle de foco no surto de 2013 | 17% | **24%** |
| SARIMA, a régua do mesmo artigo | — | — | 29% |
| **Nós, cenário adotado** | pesquisa | **27%** | **65%** |
| **Nós, HistGB folha 20** | pesquisa | 49% | **58%** |

- Singapura: o país inteiro, pico de 842 casos por semana, **todas as semanas com caso**, 10 anos de treino.
- O nosso MAPE conta só as semanas com **100 casos ou mais**, o recorte comparável. Nas semanas com poucos
  casos, o MAPE explode por divisão por um número pequeno.
- **Leitura:** em 3 meses, Singapura erra menos da metade do nosso.

---

## 2. Erro relativo ao total

| Modelo | Uso | Erro em 1 mês | Erro em 3 meses |
|---|---|---|---|
| **Ensemble, Wu et al. 2025** | **operacional**: alocação de ensaios clínicos no Brasil, Colômbia, Malásia, México e Tailândia | 38,5% | **62,7%** |
| **Nós, cenário adotado** | pesquisa | 53% | **65%** |
| **Nós, HistGB folha 20** | pesquisa | 48% | **57%** |

- Wu: 187 estados e províncias, **mensal**. A métrica deles é derivada do MAE; a fórmula exata está num
  apêndice que não foi acessado.
- A nossa é a soma dos erros dividida pela soma dos casos.
- **Leitura:** em 3 meses estamos no mesmo patamar. Em 1 mês erramos mais, mas eles agregam por mês e por
  estado, o que suaviza a série.

---

## 3. R²

| Modelo | Onde | Uso | R² em 1 mês | R² em 3 meses |
|---|---|---|---|---|
| CatBoost, Aleixo et al. 2022 | Rio, distrito e mês | pesquisa | 0,47 | **0,38** |
| CatBoost, 27 capitais, 2026 | **Porto Alegre** | pesquisa | **−0,21**, até 4 semanas | — |
| Vetor + clima, da Silva et al. 2026 | **Porto Alegre** | pesquisa | 0,46 em log, horizonte não declarado | — |
| **Nós, cenário adotado** | Porto Alegre | pesquisa | **0,63** | **0,44** |
| **Nós, HistGB folha 20** | Porto Alegre | pesquisa | **0,72** | **0,56** |

- **Leitura:** estamos acima dos três.
- ⚠️ **Três ressalvas:**
  - a nossa avaliação tem as duas maiores epidemias da série, e muita variação ajuda o R²;
  - o estudo das 27 capitais usa 1999-2021, quando Porto Alegre tinha pouquíssima dengue;
  - o R² do da Silva é em log e não é previsão a horizonte fixo.
- O Aleixo usa anos futuros no treino da validação cruzada, o que facilita. O nosso walk-forward nunca faz isso.

---

## 4. Vantagem sobre a régua sazonal — a comparação mais justa

| Sistema | Uso | Em 1 mês | Em 3 meses |
|---|---|---|---|
| **D-MOSS** | **operacional** no Vietnã desde 2019, nas diretrizes nacionais desde 2020 | **+15%** | **+27%** em 6 meses |
| Superensemble, Colón-González et al. 2021 | precursor do D-MOSS | **+16%** em 1-3 meses | some em 4-6 meses |
| **Nós, HistGB folha 20** | pesquisa | **+13%** | **−7%** |
| **Nós, cenário adotado** | pesquisa | +1% | **−21%** |

- Positivo = erra menos que "a mesma época do ano passado". Métrica: RMSE no D-MOSS e na nossa linha; CRPS no
  superensemble.
- **Leitura:**
  - em 1 mês estamos na mesma faixa dos sistemas operacionais;
  - em 3 meses eles vencem a régua e nós perdemos.
- **O que eles têm:**
  - séries de 2002 em diante, com dengue endêmica;
  - no D-MOSS, a **previsão do clima dos próximos meses** como entrada.

---

## 5. O que não coube

- **Zhao et al. 2020, Colômbia:** MAE 24,56 em 12 semanas, em casos por departamento. Sem o volume típico de
  cada departamento, não dá para converter.
- **Lowe et al. 2016:** prevê categoria de risco, com acerto de 57% contra 33%. Não é erro numérico.

---

## 6. Correções que esta verificação trouxe

- O estudo das 27 capitais põe Porto Alegre **entre as piores**, e não explicitamente como "a pior". O
  catálogo e o PENDENCIAS foram corrigidos.
- O R² 0,46 do da Silva é sobre **log da incidência**, e o artigo não declara horizonte fixo.
- O artigo de Colón-González 2021 é **PLOS Medicine 18(3)**, não 18(6).

---

## Arquivos

| Arquivo | O que é |
|---|---|
| [`metricas_do_projeto.py`](metricas_do_projeto.py) · `metricas_do_projeto.csv` | as nossas métricas relativas por modelo e horizonte |
| [`grupo_1.md`](grupo_1.md) · [`grupo_2.md`](grupo_2.md) | definições extraídas de 8 artigos |
| `verificacao_grupo_1.md` · `verificacao_grupo_2.md` | a verificação adversarial na fonte |
