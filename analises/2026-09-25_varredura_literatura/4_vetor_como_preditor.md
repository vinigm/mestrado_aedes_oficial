# Varredura de literatura — Ângulo 4: índices entomológicos como preditores de dengue

> Pergunta: o que a literatura mostra sobre armadilhas de adultos, ovitrampas, LIRAa/Breteau/predial
> como preditores de casos de dengue — com que defasagem (semanas) e que ganho preditivo (com número)
> além de casos+clima? Cobre também vetor como variável intermediária (dois estágios), modelos
> mecanísticos (Ross-Macdonald, SEI-SEIR) ajustados a dado de armadilha, e estudos de Porto Alegre/RS/
> cone sul temperado.
>
> Método: 18 buscas na web + leitura de 15 trabalhos (abstract ou texto via WebFetch), 2015-2026.
> Rodada em 25/09/2026. Sem download de arquivo, sem acesso a dado pessoal do projeto.

---

## 1. Achado mais relevante para a tese: defasagem vetor→casos JÁ MEDIDA em Porto Alegre

**da Silva, Ferreira, Lourenço & Freitas (2026), PLOS Neglected Tropical Diseases**,
DOI `10.1371/journal.pntd.0014201`.

- Usa a MESMA fonte de dado do projeto (MosquiTRAP/MI-Aedes + SINAN/InfoDengue, Porto Alegre,
  2018-2025) — é o estudo mais próximo possível de um "gêmeo" da tese.
- **Correlação (Kendall τ) entre infestação do vetor e incidência de dengue cresce com a defasagem**:
  - lag 0 semanas: τ = **0,2737**
  - lag 4 semanas: τ = **0,4953**
  - lag 8 semanas: τ = **0,5944** (*Ae. aegypti*; *Ae. albopictus* segue padrão parecido: 0,12 → 0,45 → 0,53)
- Modelo preditivo baseado em infestação do vetor (MFAI): **R² = 0,46 · MAE = 0,19 · RMSE = 0,313**.
- Modelo baseado SÓ em clima (Index P, suitabilidade climática): **R² preditivo = −0,07** (pior que a
  média) — o vetor domina o poder preditivo, o clima sozinho quase não presta.
- **Relevância direta:** responde exatamente a pendência aberta no projeto ("a defasagem [vetor→casos]
  segue sem estimativa", ver `PENDENCIAS.md`). O padrão de correlação crescente até 8 semanas é
  **compatível** com a decisão do projeto de usar vetor defasado 0-4 semanas, mas sugere que a força
  do sinal pode não ter saturado em 4 semanas — possível ideia testável (seção 7).

---

## 2. Armadilhas de adultos (MosquiTRAP/MI-Aedes) — Porto Alegre tem mais 2 estudos próprios

**Ferreira DAC, Freitas LP, Lowe R et al. (2025), Lancet Regional Health – Americas**,
DOI `10.1016/j.lana.2025.101153`.

- Retrospectivo de vigilância: vetor detectado em Porto Alegre em **2001**, primeira transmissão
  autóctone confirmada em **maio de 2010** — **9 anos de defasagem** entre chegada do vetor e
  transmissão local sustentada (não é a defasagem semanal do projeto, é o tempo de estabelecimento).
- Anos com mais casos foram precedidos por clusters de infestação mais longos (fato qualitativo,
  não quantificado em correlação numérica no resumo).
- Achado inesperado: clusters de infestação significativos também no INVERNO, incomum para clima
  temperado.

**Ferreira et al. (2017), Parasites & Vectors**, DOI `10.1186/s13071-017-2025-8` (Porto Alegre,
sistema MI-Dengue).

- Modelo GAM com infestação da semana anterior prevê observado **melhor** que modelo só com
  variáveis meteorológicas (comparação qualitativa no resumo disponível, sem R² exato recuperado).
- Temperatura mínima semanal **acima de 18°C** associada a maior abundância; umidade **acima de 75%**
  tem efeito negativo na abundância.
- ⚠️ Já citado no acervo do projeto (Ferreira 2017) — não resumir de novo, só ancorar limiares acima.

**Sedda, Taylor, Eiras, Marques & Dillon (2020), Acta Tropica**, DOI `10.1016/j.actatropica.2020.105519`
(Caratinga, MG, Brasil — armadilha tipo MosquiTRAP).

- Compara 4 modelos log-Gaussianos de Cox: nulo, com abundância do vetor, com **taxa intrínseca de
  crescimento (IGR)** do vetor, e combinado.
- **WAIC:** IGR = 503,88 · abundância = 505,34 · nulo = 504,43 — o modelo com taxa de crescimento
  supera o de abundância bruta, embora a margem seja pequena.
- **Achado central:** não é o NÍVEL do vetor que carrega mais sinal, é a VELOCIDADE de mudança dele.
  O projeto usa nível + média móvel, mas não taxa de crescimento — ideia testável (seção 7).

---

## 3. Ovitrampas

**Hamedin, Musa & Sulong (2026), Tropical Medicine and Health**, DOI `10.1186/s41182-026-00974-y`
(11 distritos-sentinela, Malásia peninsular, 2024).

- DLNM (distributed lag non-linear model), janela de lag até 12 semanas, validação rolling-origin,
  horizonte de previsão de 4 semanas.
- Pico de associação entre **semanas 3 e 7** de defasagem para índice larval (LI) e ovitrampa (OI).
- **AUC:** OI sozinho = 0,649 · LI sozinho = **0,675** · OI+LI combinado = 0,667 (sem ganho adicional
  ao combinar) — ovitrampa (OI) tem sinal mais fraco e inconsistente que índice larval (LI) neste
  estudo (RR de OI perto de 1,0 na maior parte dos lags).

**Estudo de Córdoba, Argentina (2009-2017)** — ovitrampas semanais + levantamento larval mensal.

- Proporção de domicílios com *Ae. aegypti* juvenil subiu de **5,7% (2009-10) para 15,4% (2016-17)**.
- Ovos/ovitrampa e abundância larval associados positivamente à temperatura do MESMO mês (sem
  defasagem).
- **Achado negativo importante:** dengue autóctone NÃO foi positivamente associada a vetor ou clima
  neste estudo — pico de transmissão autóctone em abril seguiu pico de casos IMPORTADOS em março, não
  o vetor. Contraponto de honestidade estatística: nem todo estudo em região temperada do cone sul
  encontra o vetor como preditor.

---

## 4. LIRAa / Breteau / índice predial — resultado é HETEROGÊNEO, e no Brasil é fraco

**Ribeiro, Ferreira, Azevedo, Santos & Medronho (2021), Cadernos de Saúde Pública**,
DOI `10.1590/0102-311X00263320` (Estado do Rio de Janeiro, IIP de outubro → incidência do ano
seguinte).

- Correlação (Spearman) ano a ano é **inconsistente**: 2011/2012 rs=0,479 (p<0,01, único ano
  significativo) · 2010/2011 rs=0,135 (n.s.) · 2012/2013 rs=−0,003 (n.s.) · 2014/2015 rs=−0,060 (n.s.)
  · 2015/2016 rs=−0,035 (n.s.).
- ROC com limiar IIP≥0,65%: sensibilidade **66,7%**, especificidade **52,7%**, acurácia **74%** —
  desempenho fraco, "confiabilidade limitada" nas palavras do próprio artigo.
- **Achado honesto para citar:** no maior estudo brasileiro sobre o tema, o índice predial (o mesmo
  tipo de métrica do LIRAa) **NÃO** é preditor confiável de epidemia ano a ano.

**Chang, Tseng, Hsu, Chen, Lian & Chao (2015), PLOS NTD**, DOI `10.1371/journal.pntd.0004043`
(Kaohsiung, Taiwan) — modelo de dois estágios com regressão de Poisson.

- Índices testados isoladamente: Adult Index (AI) acurácia **83,8%** · Breteau (BI) **87,8%** ·
  Container (CI) **88,3%** · House (HI) **88,4%**.
- Defasagens usadas: **2 semanas** e **1 mês**.
- Combinar índice + meteorologia melhora a acurácia de cada um (número exato de ganho não
  discriminado no resumo disponível).

**Aryaprema & Xue (2019), Acta Tropica**, DOI `10.1016/j.actatropica.2019.105155` (Kaduwela/Colombo,
Sri Lanka, 2009-2016).

- Correlação Breteau×dengue significativa com defasagem de **1 e 2 meses**.
- AUC-ROC **>80%**, sensibilidade **>75%**, especificidade **>70%** nos limiares definidos.
- Limiar para lag de 1 mês: CBI=13,5 → sensibilidade >76%, especificidade >81% (melhor que lag de 2
  meses: sensibilidade >71%, especificidade >56%).

**Sánchez, Cortinas, Pelaez, Gutierrez, Concepción & Van der Stuyft (2010), Tropical Medicine &
International Health**, DOI `10.1111/j.1365-3156.2009.02437.x` (Havana, Cuba, surto de 2001).

- Quarteirão com Breteau Index **≥4** previu transmissão local com sensibilidade **81,8%** e
  especificidade **73,3%** — é o resultado mais forte da varredura para índice larval, mas em nível de
  QUARTEIRÃO (não cidade inteira, escala muito mais fina que a do projeto).

---

## 5. Vetor como variável intermediária / modelos de dois estágios

- O desenho de **Chang et al. 2015** (seção 4) já É um modelo de dois estágios formal: 1º estágio
  seleciona a defasagem ótima do índice entomológico por AIC, 2º estágio usa esse índice + meteorologia
  para prever casos via Poisson.
- **Ong, Isawasan, Mohd Ngesom, Shahar, Md Lasim & Nair (2023), Scientific Reports**,
  DOI `10.1038/s41598-023-46342-2` (5 distritos de Kuala Lumpur/Putrajaya, Malásia, 2018-2020).
  - Compara 7 algoritmos de ML prevendo TRANSMISSÃO (não só casos) usando índices vetoriais +
    variáveis meteorológicas.
  - **Achado contrário à intuição:** clima pesou mais que os índices vetoriais; o índice de recipiente
    (container index) foi o MENOS importante, e removê-lo (junto com outras variáveis fracas via
    seleção Boruta) **melhorou AUC e F1-score em pelo menos 6%** (feature selection ajudou mais que
    manter o vetor).
  - XGBoost venceu entre os 7 algoritmos testados.
- Nenhum trabalho lido usa explicitamente "prever o vetor primeiro, depois usar o vetor PREVISTO
  (não o observado) como insumo para prever casos" no sentido estrito de um pipeline de dois estágios
  com previsão encadeada — os "dois estágios" na literatura geralmente significam "seleção de
  variável/lag" + "regressão final", não um modelo de vetor separado alimentando um modelo de casos.
  **Isso é uma lacuna real** (seção 6) e abre espaço de ideia testável genuinamente nova (seção 7).

---

## 6. Modelos mecanísticos (Ross-Macdonald / SEI-SEIR) calibrados com dado de armadilha

- Nenhum estudo mecanístico encontrado calibra diretamente contra dado de armadilha em cidade
  subtropical/temperada da América do Sul — os exemplos fortes são de fora da região:
- **Modelo de Miami-Dade (Acta Tropica, 2023)**, DOI reportado nas fontes como Buchanan et al./
  matemáticos da NSU/Univ. Miami — modelo determinístico de população de mosquito, parâmetros
  ajustados com dado entomológico e de temperatura local, **calibrado contra dado de armadilha real de
  2017-2019**. Achado: chuva afeta criadouro/abundância mais em áreas turísticas que residenciais.
  Usado para avaliar efetividade de controle vetorial, não para prever caso de dengue diretamente.
- Modelos Ross-Macdonald "clássicos" aplicados a dengue (revisão geral, sem dado específico do cone
  sul) tratam principalmente de R0 e magnitude/frequência de surto, calibrados contra série de CASOS,
  não contra série de ARMADILHA — outra lacuna.

---

## 7. Estudos do cone sul temperado (Argentina/RS) — quadro é misto, não unânime

**Estallo, López, Ludueña-Almeida, Madelón, Layún & Robert (2024), Lancet Regional Health – Americas**,
DOI `10.1016/j.lana.2024.100946` (Córdoba, Argentina).

- *Ae. aegypti* ativo durante o INVERNO de 2024 — historicamente a atividade ia de final de
  outubro a final de maio; achado de expansão sazonal.
- Temporada 2023-2024: Argentina registrou **583.297** casos de dengue (aumento de **4,18×** vs.
  temporada anterior); só Córdoba, **127.483** casos.

**Estudo longitudinal de Córdoba 2009-2017** (seção 3) — reforça que em clima temperado do cone sul,
a associação vetor↔dengue autóctone pode ser FRACA ou nula dependendo do desenho (casos importados
dominando o sinal).

**Oliveira, Netto, Francisco, Vieira, Variza, Iser, Lima-Camara, Lorenz & Prophiro (2023), Tropical
Medicine and Infectious Disease**, DOI `10.3390/tropicalmed8020077` (PR + SC + RS, 1.191 municípios,
2003-2021, correlação climática 2017-2021).

- Precipitação: correlação **negativa** com infestação (p=0,030) · temperatura mínima: **positiva**
  (p=0,032) · umidade relativa: **negativa** (p<0,001) · infraestrutura urbana: **positiva** (p<0,001).
- Aumento simultâneo de infestação e casos de dengue no Sul do Brasil, sobretudo após 2017 — sem
  quantificar defasagem ou ganho preditivo numérico.

---

## Lacunas identificadas na literatura (rotuladas — fato ≠ inferência)

- **Fato:** a maioria dos estudos com número forte de defasagem/AUC/sensibilidade é da Ásia (Sri
  Lanka, Taiwan, Malásia) ou Caribe (Cuba) — poucos têm desenho equivalente na América do Sul
  temperada/subtropical.
- **Fato:** no Brasil, o único estudo direto sobre índice predial/LIRAa e incidência (Ribeiro et al.
  2021, RJ) encontrou desempenho preditivo **fraco e inconsistente ano a ano** — compatível com o
  próprio ceticismo do projeto sobre entomologia larval como preditor de epidemia em nível de cidade.
- **Fato:** o estudo mais equivalente ao projeto (da Silva et al. 2026, Porto Alegre, seção 1) mede
  defasagem crescente até 8 semanas, mas usa correlação (τ de Kendall), não erro de previsão fora da
  amostra num walk-forward — não é diretamente comparável ao MAE do projeto.
- **Inferência (minha, a confirmar):** a divergência entre "vetor melhora muito" (Porto Alegre 2026,
  R²=0,46 vs. −0,07) e "vetor não ajuda muito além do clima" (Ong et al. 2023, Malásia) pode vir de
  escala temporal do alvo — os estudos que dão mais crédito ao vetor preveem no MESMO horizonte
  epidemiológico curto (poucas semanas), enquanto o projeto mira 12 semanas à frente, horizonte em que
  o vetor observado hoje já é um sinal mais fraco/defasado.
- **Nenhum trabalho lido** testa explicitamente um pipeline de dois estágios em que o vetor É
  PREVISTO (não observado) para alimentar a previsão de casos a 3 meses — é a lacuna mais clara e mais
  diretamente testável no projeto (idea 3 abaixo).

---

## Tabela-resumo

| Trabalho | Dado/atributo/modelo | Horizonte | Métrica e número | Aplicável a POA? |
|---|---|---|---|---|
| da Silva et al. 2026, PLOS NTD | MosquiTRAP+clima+SINAN, POA, correlação por lag | lag 0-8 sem. | τ 0,27→0,50→0,59; R²=0,46 (vetor) vs. −0,07 (só clima) | **Sim — mesma cidade, mesma fonte de dado** |
| Ferreira et al. 2025, Lancet RHA | Vigilância retrospectiva, POA | 2001-2021 | 9 anos entre chegada do vetor e 1ª transmissão autóctone | Sim — mesma cidade |
| Ferreira et al. 2017, Parasites & Vectors | GAM, infestação sem. anterior, POA | 1 semana | GAM c/ vetor > só clima (qualitativo); limiar 18°C/75% | Sim — já no acervo |
| Sedda et al. 2020, Acta Tropica | MosquiTRAP, taxa de crescimento (IGR), Caratinga-MG | — | WAIC: IGR 503,9 < abundância 505,3 < nulo 504,4 | Parcial — outra cidade, mesma métrica de trap |
| Hamedin et al. 2026, Trop Med Health | Ovitrampa (OI) e larval (LI), Malásia, DLNM | lag até 12 sem. | AUC: LI 0,675 · OI 0,649 · combinado 0,667 | Baixa — outro continente/clima |
| Chang et al. 2015, PLOS NTD | AI/BI/CI/HI + Poisson 2 estágios, Taiwan | lag 2 sem./1 mês | Acurácia 83,8-88,4% | Baixa — larval, não adulto |
| Aryaprema & Xue 2019, Acta Tropica | Breteau Index, Sri Lanka | lag 1-2 meses | AUC>80%, sens>75%, esp>70% | Baixa — outro continente |
| Sánchez et al. 2010, Trop Med Int Health | Breteau≥4 por quarteirão, Havana | — | Sens 81,8%, esp 73,3% | Baixa — escala de quarteirão |
| Ribeiro et al. 2021, Cad. Saúde Pública | IIP (LIRAa) outubro, RJ, Brasil | 1 ano | rs entre 0,48 e −0,06 (inconsistente); ROC acc 74% | **Sim — mesmo país, mostra fraqueza do índice predial** |
| Ong et al. 2023, Sci Rep | Índices vetoriais + clima, ML, Malásia | curto prazo | Clima > vetor; remover fracos +6% AUC/F1 | Baixa — outro continente |
| Miami-Dade (Acta Tropica 2023) | Modelo mecanístico população, calibrado c/ trap | — | Qualitativo (chuva x turismo x abundância) | Baixa — sem série de casos |
| Estallo et al. 2024, Lancet RHA | Vigilância, Córdoba, Argentina | 2023-2024 | 583.297 casos país (+4,18×); Córdoba 127.483 | Parcial — cone sul temperado |
| Córdoba 2009-2017 (Heliyon/bioRxiv) | Ovitrampa+larval, Argentina | 2009-2017 | Infestação domiciliar 5,7%→15,4%; dengue autóctone SEM assoc. c/ vetor | Parcial — contraponto negativo |
| Oliveira et al. 2023, Trop Med Infect Dis | Infestação x clima, Sul do Brasil (PR/SC/RS) | 2003-2021 | Correlações climáticas (p<0,05), sem defasagem numérica | **Sim — RS incluso** |

---

## Ideias testáveis no projeto (baseadas na literatura, ainda não testadas)

1. **Taxa de crescimento do vetor (IGR), não só nível.** Base: Sedda et al. 2020 mostrou que a taxa
   intrínseca de crescimento supera abundância bruta como preditor (WAIC 503,9 vs. 505,3).
   Diferença do que já foi testado: o projeto usa nível do vetor + média móvel de 4 semanas, nunca a
   DERIVADA/taxa de variação semana a semana. Dado necessário: já existe — é só uma transformação
   (log-razão ou diferença) da série MI-Aedes já presente no projeto.

2. **Vetor como alarme binário por limiar, não só regressor contínuo.** Base: Chang et al. 2015 e
   Aryaprema & Xue 2019 convertem o índice entomológico em LIMIAR categórico (ex.: Breteau≥13,5) e
   medem sensibilidade/especificidade para prever SURTO, não o valor contínuo de casos.
   Diferença do que já foi testado: o projeto testou lag do vetor só como regressor contínuo em
   modelo de regressão (MAE); nunca testou o vetor como variável limiar categórica alimentando
   especificamente o modelo de ALARME de surto em h=12 (onde já existe 1 resultado que sobrevive a
   Holm). Dado necessário: já existe — série MI-Aedes + definição de percentil como limiar.

3. **Vetor PREVISTO (não observado) como insumo de 2º estágio.** Base: nenhum trabalho lido faz
   pipeline formal de "prever vetor 12 semanas à frente → usar essa previsão como feature do modelo
   de casos"; a literatura de "dois estágios" (Chang 2015) só encadeia seleção de lag + regressão
   final, ambos com vetor OBSERVADO. Diferença do que já foi testado: o projeto só usa vetor
   observado defasado 0-4 semanas (dado disponível na data de corte); nunca projetou o vetor à frente
   com seu próprio modelo e usou a projeção como atributo adicional para o horizonte de 12 semanas.
   Dado necessário: existe a série de vetor; falta o modelo auxiliar de previsão do vetor em si
   (esforço extra de implementação, não de coleta).

4. **Defasagem de 8 semanas isolada como feature única (não faixa 5-12 já testada), alimentando
   especificamente o modelo de ALARME.** Base: da Silva et al. 2026 (POA) mostra correlação
   ainda subindo em τ até lag=8 (0,59), maior que em lag=4 (0,50). Diferença do que já foi testado: o
   projeto testou faixa 5-12 semanas para métrica de ERRO (MAE) em regressão, com resultado negativo;
   não testou lag=8 isolado como feature do modelo de CLASSIFICAÇÃO de alarme de surto (métrica
   diferente da testada). Dado necessário: já existe na série MI-Aedes.

5. **Réplica formal da correlação por lag (τ de Kendall, 0-8 semanas) nos dados do próprio projeto**,
   para comparar diretamente com os números do da Silva et al. 2026 (τ 0,27/0,50/0,59). Base: mesmo
   artigo, seção 1. Diferença do que já foi testado: o projeto tem "leitura de gráfico" informal sobre
   a defasagem (registrado como pendência em aberto), nunca uma medição formal de correlação por lag
   comparável à da literatura. Dado necessário: já existe — só falta calcular e documentar.

6. **Seleção de atributo agressiva tipo Boruta antes do modelo, testando se REMOVER o vetor de
   baixa contribuição individual (não o vetor inteiro, mas sub-atributos fracos dele) melhora AUC.**
   Base: Ong et al. 2023 removeu o índice mais fraco (container index) e ganhou +6% em AUC/F1.
   Diferença do que já foi testado: o projeto testou 9 algoritmos e grade de hiperparâmetros, mas não
   seleção de subatributos individuais dentro do bloco de 6 colunas do vetor (pode ser que 1-2 das 6
   colunas do vetor carreguem todo o sinal e as outras adicionem ruído). Dado necessário: já existe —
   as 6 colunas do vetor já estão no dataset preparado.
