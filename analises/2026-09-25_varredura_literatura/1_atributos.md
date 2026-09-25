# Varredura de literatura — Atributos e fontes de dados para previsão de dengue (1-3 meses)

> **Pergunta:** quais atributos e fontes de dados a literatura usa para prever dengue com 1 a 3 meses de
> antecedência, e quais mostraram ganho **medido fora da amostra** nesse horizonte?
>
> **Método:** busca via `WebSearch` + leitura de página/resumo via `WebFetch` em 25/09/2026. Fato ≠
> inferência, sempre rotulado. Toda afirmação numérica tem referência com DOI/URL verificável — números
> que não pude confirmar por bloqueio de acesso (reCAPTCHA/paywall) foram **omitidos**, não estimados.
>
> **Contexto do projeto (para comparar):** Porto Alegre, série 18/02/2018–2026, 4 temporadas epidêmicas
> (2022–2025), horizonte-alvo 12 semanas, HistGB quantil 0,85, 20 atributos. Referência atual em 12
> semanas: MAE 243,8–278,8 casos/semana, batida pela regra "mesma semana do ano passado" (MAE 217,8).

---

## 1. Clima defasado (temperatura, chuva, umidade, ponto de orvalho)

- **Faixa térmica ótima para transmissão por *Aedes aegypti*:** Mordecai et al. (2017), *PLOS NTD*,
  DOI [10.1371/journal.pntd.0005568](https://doi.org/10.1371/journal.pntd.0005568). Pico de transmissão
  em **29,1°C** (IC 95%: 28,4–29,8°C) num modelo mecanicista de R0 térmico.
  - **Fato medido fora da amostra:** o R0(T) previsto bateu contra incidência real de dengue nas
    Américas em 2014-2016 com **86-91% de acurácia** na probabilidade de transmissão autóctone, e
    **85-86%** na magnitude da incidência. Não há horizonte de antecedência explícito — é
    contemporâneo (o R0 térmico da semana atual explica a incidência da mesma janela), não um teste de
    previsão prospectiva a 1-3 meses.
  - **Contexto climático:** faixa validada nas Américas em geral (tropical/subtropical); POA tem
    inverno abaixo de 15°C, fora da faixa de transmissão ativa a maior parte do ano — **relevância
    direta é baixa fora do verão**.

- **Temperatura mínima e chuva por defasagem mensal (DLNM):** Polrob & La-up (2025), *BMC Public
  Health*, DOI [10.1186/s12889-025-25420-2](https://doi.org/10.1186/s12889-025-25420-2), Bangkok,
  Tailândia.
  - **Fato:** temperatura mínima tem risco relativo (**RR**) de pico **1,037** no lag de 5 meses;
    chuva tem RR de pico **1,046** no lag 0; umidade tem padrão bifásico (risco no lag 0, proteção
    entre lags 4-9 meses).
  - **Não há métrica preditiva fora da amostra** — é um estudo correlacional (DLNM clássico), sem
    walk-forward nem MAE/RMSE.
  - **Contexto:** Bangkok é tropical úmido, sem inverno — defasagens em **meses** (não semanas), o que
    dificulta comparação direta com o lag de 0-4 semanas do modelo de POA.

- **Ponto de orvalho e umidade em médias móveis de 10-15 dias:** Oliveira et al. (2025), *Anais
  ERAMIA-RS*, DOI [10.5753/eramiars.2025.16737](https://doi.org/10.5753/eramiars.2025.16737), **Porto
  Alegre**, 2020-2024.
  - **Fato:** XGBoost prevendo **aceleração** de casos (não a série contínua) atingiu **acurácia
    balanceada de 0,67**, o melhor entre Decision Tree/Random Forest/SVM/XGBoost. Os atributos mais
    importantes foram médias de **10-15 dias de ponto de orvalho e umidade**.
  - **Aplicabilidade a POA:** direta (mesma cidade), mas o alvo é diferente (classificação binária de
    aceleração, horizonte 10-15 dias — não 12 semanas de casos contínuos). Não dá para comparar
    magnitude de erro.

## 2. Estruturas de defasagem (DLNM, lag distribuído)

- Confirma-se na literatura (Polrob & La-up 2025 acima; e revisão geral em Shafqat et al. 2025,
  *GeoHealth*, DOI 10.1029/2025GH001608 — não lido em detalhe) que o **DLNM é a estrutura padrão** para
  modelar efeito não-linear e defasado do clima, mas **quase sempre em desenho correlacional** (RR por
  lag), não em previsão fora da amostra com métrica de erro comparável a MAE/RMSE.
- **Lacuna real:** não encontrei nenhum trabalho que reporte MAE/RMSE fora da amostra em 8-12 semanas
  comparando explicitamente uma estrutura de lag distribuído (DLNM) contra lags discretos simples
  (como os 0-4 semanas do projeto). O ganho do DLNM é sempre reportado em termos de RR/significância,
  não de erro de previsão.

## 3. Índices oceânicos (ENSO/ONI, IOD)

- **IOD (Índice do Dipolo do Oceano Índico) supera ENSO como preditor, horizonte de 6 meses:** Ma, Xu,
  Han et al. (2025), *PNAS Nexus*, DOI
  [10.1093/pnasnexus/pgaf350](https://doi.org/10.1093/pnasnexus/pgaf350), China (surtos importados).
  - **Fato:** XGBoost com IOD teve **R²=0,56**; sem IOD, **R²=0,44**; GAM, **R²=0,33**. O modelo
    projeta picos de surto com **6 meses de antecedência**. Poder explicativo do IOD (33,76%) superou
    o do ENSO (30,40%) com casos importados, e (20,36% vs 18,41%) sem eles.
  - **Contexto:** dengue **importada** na China (mobilidade humana + clima do Oceano Índico) — mecanismo
    distinto do de POA (transmissão local, sem componente de importação relevante documentado).
    **Aplicabilidade a POA é baixa** — o canal causal (chegada de viajantes de regiões com IOD alto) não
    existe da mesma forma.
- **ENSO no projeto já testado e reprovado:** o achado de ENSO piorando h=12 em 11,6% (registrado em
  PENDENCIAS) é consistente com a literatura mostrar ENSO como **mais fraco que IOD** e com efeito
  regional variável — em Bangladesh, a associação ENSO/IOD-dengue é fraca isoladamente e só aparece após
  ajuste por clima local (achado de busca, PMC4633589, não lido em texto completo — citado com cautela).

## 4. Imunidade e suscetíveis (incidência acumulada, troca de sorotipo)

- **Estabilidade do período inter-epidêmico como proxy do tamanho do pool de suscetíveis:** Rypdal &
  Sugihara (2019), *Nature Communications*, DOI
  [10.1038/s41467-019-10099-y](https://doi.org/10.1038/s41467-019-10099-y).
  - **Fato (qualitativo, confirmado por título/abstract):** os autores mostram que a estabilidade da
    série durante o período **entre** surtos prevê a magnitude do surto **seguinte**, e que essa
    métrica é computável só com dados de incidência (sem sorologia). **Não consegui confirmar o
    número exato de R²/correlação** — acesso bloqueado por paywall/redirect em duas tentativas; **omito
    o número** em vez de estimar.
  - **Relevância para POA:** conceito aplicável (a série de casos de POA tem exatamente esse padrão de
    inter-temporada "baixa" 2018-2021 seguida de picos crescentes 2022→2025) — mas precisa de reteste
    próprio, não há número da literatura para importar diretamente.

- **Sorotipo circulante como atributo, por horizonte:** Fuad, Milki & Al Aziz (2026), *PLOS ONE*, DOI
  [10.1371/journal.pone.0353069](https://doi.org/10.1371/journal.pone.0353069), Bangladesh.
  - **Fato:** em horizonte **curto (1 mês)**, o percentual do sorotipo DENV-1 defasado em 1 mês foi
    "crítico" e o SARIMAX (tático) atingiu precisão 0,886/recall 0,824 para alarme de surto. Em
    horizonte **médio (2-6 meses)**, o Prophet (estratégico) teve o menor RMSE agregado
    (**3.952,6–4.004,2**), superando SARIMAX (RMSE 6.501,1 no mesmo teste agregado). **Nenhum modelo
    venceu em todos os horizontes.**
  - **Contexto:** Bangladesh testa e reporta os 4 sorotipos separadamente (DENV-1 a 4). **POA não tem
    esse dado** — a Secretaria de Saúde não faz tipagem sorológica rotineira e sistemática, então esse
    atributo é **inviável de replicar** sem uma fonte de dado nova.

## 5. Sinais digitais (Google Trends, redes sociais)

- **Google Trends para nowcasting no Brasil (26 estados):** Xiao, Soares, Bastos, Izbicki & Moraga
  (2025), *PLOS NTD* 19(8), DOI
  [10.1371/journal.pntd.0012501](https://doi.org/10.1371/journal.pntd.0012501).
  - **Fato:** o modelo só-Google-Trends (GT) venceu o modelo só-dados-oficiais (DC) em RMSE em **12 de
    26 estados**, em RMSPE em **17 de 26**, e em logscore em **18 de 26**. Horizonte: **nowcasting**
    (semana corrente, não 1-3 meses à frente) — objetivo é preencher atraso de notificação (menos de
    50% dos casos chegam na 1ª semana), **não prever o futuro**.
  - **Aplicabilidade a POA:** baixa para o horizonte de 12 semanas do projeto — é uma ferramenta de
    "presente", não de "futuro".

- **Ganho de Google Trends é frágil/negativo fora da amostra:** estudo de Vietnám (2026), "Evaluating
  the incremental value of Google Trends for provincial dengue surveillance in Vietnam", PMID
  [42636653](https://pubmed.ncbi.nlm.nih.gov/42636653/) (DOI não confirmado — acesso bloqueado por
  reCAPTCHA; autores completos não confirmados).
  - **Fato (via resumo indexado):** o modelo AR + Google Trends bruto **piorou** o erro fora da amostra
    frente a AR puro — MAE 72,52 vs 63,70; RMSE 110,58 vs 92,25. Só em cenário de atraso de notificação
    simulado de 1 semana o Trends ajudou (MAE 74,33 vs 80,04); com atraso de 2 semanas o resultado foi
    misto.
  - **Leitura:** reforça que Google Trends **não é solução geral** — ganho depende de o sistema oficial
    estar atrasado, o que não é o caso do MI-Aedes/SINAN para POA (dados semanais correntes).

## 6. Sinais de crescimento (taxa de crescimento, Rt)

- Não encontrei nenhum trabalho, entre os lidos, que isolasse taxa de crescimento/Rt como atributo de
  entrada testado **especificamente** em horizonte de 8-12 semanas com número de ganho reportado. A
  busca (WebSearch) retornou apenas menções genéricas de "growth rate indicators (variação percentual,
  log-diferença)" sem paper com número específico e verificável.
  - **Marca como lacuna** — não incluir essa alegação como fato até achar a fonte primária.

## 7. Transformações (log, incidência por 100 mil)

- Achado de busca (não lido em texto completo, portanto **inferência de baixa confiança**): em um
  trabalho de forecasting fenomenológico com processos Gaussianos para dengue (Gaussian process, dengue
  case study — arXiv 1702.00261), a transformação **log** foi tentada e **piorou** o ajuste — "over
  corrige", achatando picos altos; **raiz quadrada funcionou melhor** nesse contexto específico. Não
  li o PDF completo, então não cito número de erro — só a direção qualitativa, com baixa confiança.
- Relevante para POA: o projeto já usa perda quantílica (0,85) em vez de transformar o alvo — a
  literatura sugere que a escolha entre log/raiz/quantílica é sensível ao formato da cauda de picos,
  reforçando (não provando) que testar sqrt como alternativa à perda quantílica pode valer, mas não há
  número de ganho fora da amostra confirmado para importar.

## 8. Atributos alinhados à semana-alvo (ex.: mesma semana do ano anterior)

- Nenhum dos trabalhos lidos testa explicitamente "casos na mesma semana-alvo do ano anterior" como
  **atributo de entrada** de um modelo de ML (o que é diferente de usá-la como **baseline** de
  comparação, que é exatamente o que o projeto já faz). A prática mais próxima encontrada é o uso de
  "codificação periódica" (seno/cosseno de semana/mês) — já presente no cenário adotado do projeto —
  em da Cunha e Silva et al. (2026, abaixo).
- **Comparação com regra sazonal ingênua:** nenhum dos 11 trabalhos lidos compara seu modelo de ML
  contra a regra "repetir a semana do ano anterior" com número explícito — isso é uma lacuna
  **relevante e específica** do projeto (o achado de que o modelo perde para essa regra em 8 e 12
  semanas não tem contraponto direto na literatura lida para validar se é comum ou incomum).

## 9. Referência adicional: comparação multi-modelo em capitais brasileiras

- da Cunha e Silva et al. (2026), *International Journal of Biometeorology*, DOI
  [10.1007/s00484-026-03300-7](https://doi.org/10.1007/s00484-026-03300-7). 27 capitais brasileiras,
  atributos: precipitação anual, umidade mínima, temperatura máxima, lags autorregressivos, janelas
  móveis de 4/8/12 semanas, PIB per capita, densidade, codificação periódica.
  - **Fato:** CatBoost (estratégia "Direct", um modelo por horizonte) supera GRU-MIMO; R² por capital
    variando de 0,87 a 0,92 nas melhores (Goiânia, João Pessoa, Fortaleza, Belo Horizonte). **Mas o
    horizonte testado vai só até 4 semanas** — não cobre 8-12 semanas, o intervalo de interesse do
    projeto.
  - **Ganho de clima/urbano vs. baseline não é isolado no resumo lido** — não há número de "quanto o
    clima contribui sozinho" que dê para comparar com POA.

- Chen & Moraga (2025), *BMC Public Health* 25:973, DOI
  [10.1186/s12889-025-22106-7](https://doi.org/10.1186/s12889-025-22106-7). LSTM+SHAP, 27 estados,
  climas defasados em 1-3 meses (para prever 1 mês) e 3 meses (para prever 3 meses/12 semanas).
  - **Fato:** o efeito espacial (dados de estados vizinhos) reduziu o MAE em Minas Gerais de 7.730,47
    para 5.088,71 (**-34%**), no horizonte de 1 mês. É a maior redução numérica isolada e verificável
    encontrada nesta varredura para um atributo específico.
  - **Contexto:** escala estadual (casos absolutos na casa dos milhares/semana), não municipal —
    números de MAE não são comparáveis diretamente aos de POA (~250 casos/semana em h=12), mas a
    **direção do achado** (vizinhança espacial ajuda) é transferível como hipótese, e é coerente com
    o eixo espacial do próprio projeto (regra simples por zona vence ML em 8 de 8, conforme
    HISTORICO_DE_TESTES).

- Freitas et al. (2025), *Infectious Disease Modelling*, DOI
  [10.1016/j.idm.2025.07.014](https://doi.org/10.1016/j.idm.2025.07.014). Bandas epidêmicas
  probabilísticas, 118 distritos de saúde do Brasil, horizonte de **52 semanas**.
  - **Fato:** o modelo usa a distribuição histórica de casos (2015 até a temporada anterior) para
    montar percentis (50/75/90%) e classifica a temporada seguinte como típica/atípica/muito atípica —
    é uma forma de usar "incidência acumulada de temporadas anteriores" como âncora, mas **sem
    reportar MAE/RMSE fora da amostra** — a validação é por classificação de banda (a temporada caiu
    dentro da banda certa ou não), não por erro numérico ponto a ponto.

---

## Tabela-resumo

| Trabalho | Dado/atributo/modelo | Horizonte | Métrica e número | Aplicável a POA? |
|---|---|---|---|---|
| Mordecai et al. 2017 (PLOS NTD, [10.1371/journal.pntd.0005568](https://doi.org/10.1371/journal.pntd.0005568)) | R0 térmico, ótimo 29,1°C | Contemporâneo (não é previsão prospectiva) | 86-91% acurácia de transmissão; 85-86% de magnitude | Baixa — POA tem inverno fora da faixa térmica ativa |
| Polrob & La-up 2025 (BMC Public Health, [10.1186/s12889-025-25420-2](https://doi.org/10.1186/s12889-025-25420-2)) | Temp. mín. e chuva por lag mensal (DLNM) | Correlacional, sem previsão | RR pico 1,037 (temp mín, lag 5m); RR 1,046 (chuva, lag 0) | Baixa — clima tropical úmido, sem out-of-sample |
| Oliveira et al. 2025 (ERAMIA-RS, [10.5753/eramiars.2025.16737](https://doi.org/10.5753/eramiars.2025.16737)) | Ponto de orvalho/umidade, médias 10-15 dias, XGBoost | 10-15 dias, alvo = aceleração (classificação) | Acurácia balanceada 0,67 | Alta (mesma cidade), mas alvo e horizonte diferentes |
| Ma et al. 2025 (PNAS Nexus, [10.1093/pnasnexus/pgaf350](https://doi.org/10.1093/pnasnexus/pgaf350)) | IOD vs ENSO, XGBoost | 6 meses | R² 0,56 (c/ IOD) vs 0,44 (s/ IOD) vs 0,33 (GAM) | Baixa — mecanismo é dengue importada por mobilidade |
| Rypdal & Sugihara 2019 (Nat. Commun., [10.1038/s41467-019-10099-y](https://doi.org/10.1038/s41467-019-10099-y)) | Estabilidade inter-epidêmica → magnitude do próximo surto | Entre-temporadas | Não confirmado (acesso bloqueado) | Média — conceito replicável, número não importável |
| Fuad, Milki & Al Aziz 2026 (PLOS ONE, [10.1371/journal.pone.0353069](https://doi.org/10.1371/journal.pone.0353069)) | Sorotipo DENV-1..4 + clima, SARIMAX vs Prophet | 1 mês (tático) vs 2-6 meses (estratégico) | RMSE agregado 3.952,6-4.004,2 (Prophet, 2-6m) vs 6.501,1 (SARIMAX) | Baixa — POA não tipa sorotipo rotineiramente |
| Xiao et al. 2025 (PLOS NTD, [10.1371/journal.pntd.0012501](https://doi.org/10.1371/journal.pntd.0012501)) | Google Trends para nowcasting, 26 estados | Semana corrente (nowcast) | GT venceu em 12/26 (RMSE), 18/26 (logscore) | Baixa — é ferramenta de atraso de notificação, POA não tem esse atraso |
| Vietnã 2026 (PubMed [42636653](https://pubmed.ncbi.nlm.nih.gov/42636653/)) | AR + Google Trends bruto | Semanal, provincial | RMSE piorou: 110,58 vs 92,25 (AR puro) | Baixa — reforça que GT não ajuda sistema não-atrasado |
| da Cunha e Silva et al. 2026 (Int J Biometeorol, [10.1007/s00484-026-03300-7](https://doi.org/10.1007/s00484-026-03300-7)) | CatBoost direct, 27 capitais | Só até 4 semanas | R² 0,87-0,92 nas melhores capitais | Baixa direta — não cobre 8-12 semanas |
| Chen & Moraga 2025 (BMC Public Health, [10.1186/s12889-025-22106-7](https://doi.org/10.1186/s12889-025-22106-7)) | LSTM+SHAP, efeito espacial de estados vizinhos | 4 e 12 semanas | MAE -34% com efeito espacial (MG: 7.730 → 5.089) | Média — direção transferível (vizinhança espacial), escala não comparável |
| Freitas et al. 2025 (Infect. Dis. Model., [10.1016/j.idm.2025.07.014](https://doi.org/10.1016/j.idm.2025.07.014)) | Percentis históricos como banda epidêmica | 52 semanas | Classificação de banda (sem MAE/RMSE) | Baixa para o método; média para o conceito de âncora histórica |

---

## Lacunas identificadas (nenhuma tem número de suporte na literatura lida)

- **DLNM com métrica de previsão fora da amostra em 8-12 semanas**: toda a literatura de DLNM lida é
  correlacional (risco relativo por lag), nunca reporta MAE/RMSE prospectivo comparável ao do projeto.
  Isso significa que "estrutura de lag distribuído" não tem, nesta varredura, nenhum número concreto de
  ganho preditivo a importar — só o padrão qualitativo de forma de resposta por lag.

- **Taxa de crescimento/Rt como atributo de entrada** (não como produto de saída): não achei paper que
  isole esse atributo com número de ganho verificável em 8-12 semanas. Buscas adicionais renderam só
  menções genéricas sem fonte primária navegável.

- **Comparação direta contra a regra "mesma semana do ano anterior"**: nenhum dos 11 trabalhos lidos
  usa esse baseline explicitamente — o achado do projeto (o modelo perde para essa regra em 8-12
  semanas) não tem contraponto na literatura para dizer se é um resultado incomum ou o padrão em
  cidades de porte médio com poucas temporadas de treino.

- **Transformação log vs. raiz quadrada vs. perda quantílica**: só achei uma pista qualitativa de baixa
  confiança (Gaussian process, não lido em texto completo) de que log "over-corrige" picos — não é
  fato robusto o bastante para orientar decisão.

- **Imunidade/suscetíveis com número de ganho preditivo**: o conceito existe (Rypdal & Sugihara 2019),
  mas o número de correlação/R² ficou bloqueado por paywall em duas tentativas — não posso afirmar a
  magnitude do ganho, só que o conceito é estabelecido na literatura de doenças sazonais.

- **Nenhum estudo Brasil-específico compara explicitamente vetor (armadilha de adultos) como atributo
  de entrada para prever casos** nesta varredura — os trabalhos brasileiros lidos (Chen & Moraga,
  Freitas, da Cunha e Silva, Oliveira) usam clima e/ou espaço, não densidade de vetor medida por
  armadilha. Isso é consistente com o projeto ser um dos poucos a ter esse dado — não achei
  contraponto direto na literatura internacional para o achado "vetor melhora h=12 com folha
  mínima 20" do projeto.
