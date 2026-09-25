# Comparação direta — Grupo 2 (4 artigos)

> **Pergunta:** para cada artigo, extrair da fonte (não da varredura anterior) a definição exata da
> métrica, a escala dos dados e o desenho de validação, para saber se um erro percentual é comparável
> ao do cenário adotado do projeto (HistGB, folha 5, com vetor — R² em casos: **0,898** em h=1,
> **0,628** em h=4, **0,450** em h=8, **0,437** em h=12 semanas; fonte:
> `metricas_do_projeto.csv` desta mesma pasta).
>
> Método: WebFetch direto na fonte (PMC/PLOS), uma consulta por artigo. Fato = extraído com citação
> literal. Inferência = marcada explicitamente. Nada suposto quando não encontrado.

---

## Artigo 1 — CatBoost × GRU em 27 capitais brasileiras

**Referência:** da Cunha e Silva et al., *Int J Biometeorology* 2026, DOI `10.1007/s00484-026-03300-7`
(PMC13476183).

### Para que foi usado
- **FATO:** pesquisa acadêmica (UNESP/Sorocaba + Universidade do Minho/Portugal), não sistema em produção.
- **FATO, citação:** o objetivo é "contribuir ao aprimoramento de sistemas preditivos para tomada de
  decisão em saúde pública" — os autores enquadram como ferramenta de apoio, não substituto da
  vigilância.

### Escala e volume
- **FATO:** 27 capitais brasileiras, série **semanal**, taxa de morbidade por 100 mil habitantes,
  período 1999-2021.
- ⚠️ **Não encontrado:** volume típico de casos/semana em Porto Alegre. O artigo só reporta, em geral,
  "zeros anuais" entre 10% e 59% dos registros e máximo anual de 60,55 casos/100 mil hab. — não dá para
  saber se o erro percentual é comparável sem esse número.

### Definição exata da métrica
- **sMAPE** (Equação 13 do artigo): $\frac{2}{n}\sum \frac{|y_t-\hat y_t|}{|y_t|+|\hat y_t|}\times 100\%$.
  Calculado **após reverter a transformação log1p**, ou seja, na escala original de taxa de morbidade.
- **R²** (Equação 12): coeficiente de determinação, podendo ser negativo. Calculado por horizonte
  (H1-H4) e agregado por capital.
- **FATO:** ambas calculadas dentro de validação walk-forward de **13 folds**, cada um prevendo 4
  semanas à frente.

### Valor para Porto Alegre
| Modelo | MAE | RMSE | R² | sMAPE |
|---|---|---|---|---|
| GRU | 0,2315 | 0,4764 | **−0,3085** | 97% |
| CatBoost | 0,2219 | 0,4575 | **−0,2064** | **160%** |

- Porto Alegre foi, segundo o catálogo prévio, o **pior resultado das 27 capitais**.
- Régua/baseline: **não há**. A comparação do artigo é só CatBoost × GRU entre si, nenhum dos dois
  contra persistência ou média histórica.

### Avaliação
- **FATO, citação:** "Validation was conducted using a walk-forward approach... window-based scaler
  during walk-forward para prevenir vazamento". Fora da amostra, sequencial, não é holdout único.

### Comparabilidade com o projeto
- **Comparável em desenho** (walk-forward, semanal) mas **não em escala**: o artigo usa taxa por 100 mil
  hab., o projeto usa casos absolutos da cidade. sMAPE de 160% e R² de −0,21 em Porto Alegre, contra R²
  0,628 do projeto em h=4 — mesma direção de leitura já registrada no catálogo, e aqui confirmada com a
  fórmula exata na fonte.

---

## Artigo 2 — da Silva, Ferreira, Lourenço & Freitas 2026 (PLOS NTD)

**Referência:** DOI `10.1371/journal.pntd.0014201` (PMC13537681). Autores: UFMG, Instituto René
Rachou/Fiocruz Minas, Universidade Católica Portuguesa, Ecovec. Financiado por FAPEMIG.

### Para que foi usado
- **FATO, citação:** os próprios autores dizem que a contribuição "does not lie in methodological
  innovation, but rather in its application to an emerging public health challenge in Brazil" —
  pesquisa acadêmica aplicada, não sistema operacional.

### Escala e volume
- **FATO:** Porto Alegre inteira (~50 distritos monitorados, 1.388.794 hab.), série **semanal**.
- **FATO:** 72.965 casos de dengue notificados entre 2019-2025 (51% confirmados, 93% autóctones);
  pico em 2025 nas semanas epidemiológicas 13-21.

### Definição exata da métrica — ⚠️ ponto crítico
- **FATO, citação:** "an MAE of 0.79, a R² of 0.46" — calculados sobre **log(incidência de dengue + 1)**
  por 100 mil hab., não em escala de casos.
- **FATO:** modelo só-clima (Index P): "predictive R² = −0.07; deviance ratio = 0.04".
- 🔴 **Achado que corrige o catálogo prévio:** o modelo **não tem horizonte de previsão à frente** no
  sentido de walk-forward do projeto. É um modelo de **regressão com variáveis defasadas (lag 0 a 8
  semanas)** explicando a incidência corrente — os próprios autores descrevem como "higher mosquito
  infestation was associated with increased dengue cases in the following eight weeks", uma correlação
  defasada, não uma previsão fora da amostra a N semanas fixas.
  - Há, sim, um componente prospectivo: "initial training window of 50 weeks... preserving a
    sufficiently long prospective evaluation period" e "out-of-sample residual distribution" — então É
    fora da amostra, mas o **horizonte exato em semanas não é declarado** no texto recuperado.
  - ⚠️ **Não encontrado:** o horizonte fixo (1, 4, 12 semanas etc.) do R²=0,46. Não supor que é
    comparável linha a linha com o h=4/h=12 do projeto.

### Avaliação
- **FATO:** walk-forward / rolling validation, out-of-sample, janela inicial de 50 semanas.

### Comparabilidade com o projeto
- Mesma cidade, mesma fonte de armadilha (MI-Aedes), o que o torna o comparável mais próximo em
  **desenho de dado**. Mas a métrica está em **log de incidência**, não em casos, e o **horizonte não
  está claro na fonte** — por isso R²=0,46 não pode ser lido como "equivalente" ao R² de casos do
  projeto sem mais essa peça. Fica como pendência de leitura completa do artigo, já registrada na
  varredura anterior.

---

## Artigo 3 — D-MOSS, Vietnã (Campbell, Colón-González, Brady et al. 2026)

**Referência:** *PLOS Global Public Health* (PMC12965583).

### Para que foi usado
- **FATO, citação:** "D-MOSS... was launched operationally in Vietnam in June 2019, providing near-real
  time dengue forecasts across all 63 provinces". **Sistema operacional real**, não protótipo.
- **FATO:** desenvolvido com o Ministério da Saúde do Vietnã, OMS regional, Institutos Pasteur (Nha
  Trang e Ho Chi Minh), NIHE e TIHE. Incluído nas diretrizes nacionais de controle de dengue desde
  novembro/2020.

### Escala e volume
- **FATO:** nível **provincial** (63 províncias), frequência **mensal**.
- **FATO:** no período operacional avaliado (jul/2019–set/2022), 692.617 casos totais no país; Ho Chi
  Minh sozinha teve 120.161 (17% do total) — ou seja, província típica varia em ordens de grandeza
  (razão ~1:100 entre extremos), o que já avisa que RMSE agregado mistura escalas muito diferentes.

### Definição exata da métrica
- **FATO, citação:** RMSE calculado sobre "incidência de dengue por 100.000 habitantes" (não casos
  brutos, não log). Fórmula-padrão de RMSE aplicada a essa unidade.
- **FATO:** média aritmética do RMSE sobre as 63 províncias e os meses do período operacional, **por
  horizonte de lead time**, depois média entre os 6 horizontes.

### Valor por horizonte
| Lead time | D-MOSS | Baseline sazonal |
|---|---|---|
| 1 mês | 20,35 | 23,93 |
| 6 meses | 25,99 | 35,38 |
| **Média 1-6 meses** | **25,70** | **31,29** |

- **Régua:** "seasonally expanding average baseline" — média cumulativa histórica por mês-calendário,
  usando dados desde agosto/2002.

### Avaliação
- **FATO, citação:** "Historical dengue forecasts generated by D-MOSS... during the operational period
  July 2019 to September 2022 were evaluated against observed monthly dengue incidence for the same
  operational period" — avaliação de **hindcast operacional real** (previsões geradas de fato no
  período, comparadas ao observado depois), não simulação retrospectiva pura nem prospectivo puro.

### Comparabilidade com o projeto
- Escala e unidade diferentes (país inteiro por província, mensal, incidência/100k) e o diferencial
  central do D-MOSS é usar **previsão climática sazonal do futuro** como insumo — algo que nenhum
  cenário do projeto usa. A vantagem de 18% em RMSE médio (25,70 × 31,29) não é comparável diretamente
  ao R²/MAPE do projeto; serve como referência de "quanto uma boa entrada climática futura ajuda", não
  como régua de desempenho equivalente.

---

## Artigo 4 — Superensemble, Vietnã (Colón-González et al. 2021)

**Referência:** *PLOS Medicine* 18(3): e1003542 (não 18(6) — **correção**: a citação correta do volume/
número é **18(3)**, DOI `10.1371/journal.pmed.1003542`, confirmada por busca direta no periódico).

### Para que foi usado
- **FATO:** ferramenta operacional de decisão baseada em dados de observação da Terra (satélite) +
  previsão climática sazonal, co-desenvolvida com OMS, Ministério da Saúde do Vietnã, Institutos
  Pasteur e NIHE/TIHE — é o **precursor direto do D-MOSS** (artigo 3).
- **FATO, citação:** no momento da publicação (2021) o sistema seria "prospectively evaluated" nos 2
  anos seguintes — ou seja, em 2021 ainda não era avaliação operacional real (isso só veio no artigo 3,
  de 2026).

### Escala e volume
- **FATO:** nível provincial (63 províncias), dados 2002-2020.
- **FATO:** subnotificação relevante — "only 95,000 cases have been reported annually to the Ministry of
  Health" nacionalmente, contra estimativa de ~2 milhões de infecções/ano; até 80% dos casos podem ser
  assintomáticos. Hanói ~8.700 casos/ano; províncias centro-sul, na casa dos milhares, com alta
  variabilidade interanual.

### Definição exata da métrica
- **FATO, citação:** CRPS (continuous ranked probability score) — "does not focus on a specific point
  of the probability distribution... but on their distribution as a whole", generaliza o MAE para
  previsões probabilísticas. Unidade: **número de casos de dengue** (não incidência normalizada, não
  log). Calculado via pacote `SpecsVerification` em R; artigo não traz a fórmula fechada no texto.

### Valor por horizonte
- **1-3 meses:** superensemble CRPS **66,8** (IC95% 60,6–148,0) × baseline **79,4** (IC95% 78,5–80,5).
- **4-6 meses:** baseline supera o superensemble (vantagem desaparece/inverte).
- **Régua:** "a baseline model which forecasts the same incidence rate every month" — a mesma média
  sazonal histórica por província, repetida todo mês.

### Avaliação
- **FATO, citação:** expanding window time-series cross-validation — treino inicial ago/2002-dez/2006,
  cada passo soma 1 mês ao treino, teste = 6 meses seguintes. Período de teste: **jan/2007-dez/2016**
  (114 meses). Fora da amostra por construção.

### Comparabilidade com o projeto
- Mesma limitação do artigo 3: unidade é contagem de casos por província (heterogênea), métrica é
  probabilística (CRPS), o projeto usa MAPE/R² pontuais. **Não dá para converter um no outro sem
  reimplementar a métrica nos dados do projeto.** Direção de leitura válida: mesmo um sistema com
  previsão climática futura só supera a régua sazonal em 1-3 meses, não em 4-6 — reforça que o
  horizonte de 3 meses do projeto já está na fronteira onde a literatura também vê a vantagem sumir.

---

## Síntese — o que muda com a leitura direta

- 🔴 **Artigo 2 (o "gêmeo" da tese) precisa de ressalva nova:** o R²=0,46 é sobre **log-incidência**,
  não casos, e o **horizonte exato não está declarado** no texto recuperado — não é seguro comparar
  como "modelo bate o nosso em X semanas". Fica pendência: ler o artigo completo (PDF) para achar o
  horizonte.
- **Artigos 3 e 4 (D-MOSS e seu precursor)** são a mesma linhagem de sistema, escala provincial/mensal,
  com a **previsão climática do futuro** como diferencial que nenhum cenário do projeto tem — a
  vantagem sobre a régua (17-18% em RMSE/CRPS) não é redutível a um número comparável ao MAPE do
  projeto, mas confirma o padrão: vantagem em 1-3/1-6 meses, sumindo depois.
- **Artigo 1** é o único com métrica (sMAPE) e desenho (walk-forward semanal) comparáveis em formato ao
  projeto — mas falta o volume de casos de Porto Alegre para julgar se 160% de sMAPE é "muito" ou
  "normal para série esparsa"; e não há régua/baseline no próprio artigo para calibrar.
- **Nenhum dos 4 artigos permite uma frase do tipo "nosso modelo tem X% de erro, o deles tem Y%"** sem
  qualificar unidade, horizonte e régua — a resposta honesta ao Vinicius é que a comparação direta em
  número único **não existe na literatura pronta**; existe comparação de **estrutura** (quem vence a
  régua, por quanto, com que vantagem de dado).
