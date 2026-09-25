# Catálogo de sistemas e modelos prontos para dengue no Brasil

> **Pergunta:** quais sistemas/modelos prontos existem no Brasil para prever dengue, e como estão os
> resultados? Complementa `../2026-09-25_varredura_literatura/` (que cobriu a literatura acadêmica
> internacional) com o ângulo **operacional/nacional**.
>
> **Contexto do projeto (âncora, 25/09/2026):** previsão semanal de casos confirmados, cidade inteira,
> Porto Alegre, horizonte-alvo **12 semanas**. Melhor modelo: HistGB quantílico 0,85 com vetor, MAE
> **243,8** casos/semana (2024-2026). Régua "mesma semana do ano passado" erra **217,8** — o modelo
> **perde** para ela (skill score −0,12).
>
> Método: `WebSearch` + `WebFetch` (sem download de arquivo, sem clone), 25/09/2026. 🔵 FATO (reportado na
> fonte, com número) · 🟡 INFERÊNCIA minha (rotulada) · ⚠️ obtido só por snippet/resumo, não leitura
> completa (fetch bloqueado por reCAPTCHA/paywall).
>
> **Regra de comparabilidade:** nenhum MAE abaixo se compara em valor absoluto com o MAE 243,8 de POA —
> escalas, cidades, transformações de alvo e horizontes diferem. O que se extrai de cada modelo é: (a)
> venceu a régua dele? por quanto? (b) em qual horizonte? (c) contra qual régua?

---

## 0. InfoDengue (Fiocruz/FGV) — o sistema de vigilância, não de previsão

**Coordenação:** Cláudia T. Codeço (Fiocruz/PROCC), Flávio C. Coelho (FGV/EMAp), Oswaldo G. Cruz.
Operacional desde jan/2015 (Rio de Janeiro), hoje nacional, todos os municípios.

- 🔵 **O que ele de fato entrega:** nowcasting (correção de atraso de notificação) + **nível de alerta**
  em 4 cores (verde/amarelo/laranja/vermelho) baseado no **número reprodutivo efetivo Rt** + limiar
  epidêmico histórico. Fonte: Codeço, Coelho, Cruz et al., *InfoDengue: a nowcasting system for the
  surveillance of dengue fever transmission*, bioRxiv 2016, `10.1101/046193`.
- 🔴 **Não é um sistema de previsão (forecasting) de casos futuros** — é diagnóstico da semana corrente
  e recente (a diferença entre "nowcasting" e "forecasting" é central: o alerta diz "onde estamos agora,
  corrigido pelo atraso", não "quanto teremos daqui a 12 semanas"). 🟡 Inferência: isso explica por que o
  projeto nunca encontrou uma previsão InfoDengue de 3 meses para comparar diretamente.
- ⚠️ **Avaliação de desempenho publicada:** achei menção de "boa confiança e acurácia" no artigo original
  (RJ, 2011-2014 histórico + 2015 prospectivo) e "informação precisa" no primeiro ano no Paraná — **sem
  número de erro/acurácia isolável no texto acessível**. Não incluo número no quadro-resumo por isso.
- 🔵 **Código aberto:** organização GitHub `AlertaDengue`, repositório principal
  [`github.com/AlertaDengue/AlertaDengue`](https://github.com/AlertaDengue/AlertaDengue) (portal de dados)
  + `infodengue-bucardo`, app mobile. Dados exportáveis via API em JSON/CSV.
- **Aplicável a POA?** Como **insumo de dado** (casos nowcasted), sim — o projeto já usa dado do
  InfoDengue/SINAN indiretamente. Como **modelo comparável em horizonte de 3 meses**, não — ele não
  produz esse tipo de previsão.

---

## 1. Mosqlimate — a plataforma de registro e comparação de modelos

**Fiocruz + FGV/EMAp**, financiado Wellcome Trust. Paper: Ferreira, Codeço, Coelho et al., *Mosqlimate:
a platform to providing automatable access to data and forecasting models for arbovirus disease*,
arXiv:2410.18945 (2024).

- 🔵 **O que é:** dashboard + datastore + registro de modelos + registro de previsões, para comparação
  pública de desempenho entre modelos de arbovirose no Brasil, por escores probabilísticos.
- 🔵 **Dados no datastore:** casos (via InfoDengue), clima (temperatura/precipitação semanal),
  abundância de mosquito, vegetação, indicadores sociodemográficos — nível **municipal**, Brasil inteiro.
- 🔵 **API pública existe** (`api.mosqlimate.org/docs/pt/`), mas **exige conta e autenticação** para
  puxar dado — não é acesso anônimo direto. Biblioteca Python `mosqlient` para consumo interativo.
- ⚠️ **Previsões para RS/POA especificamente:** a API dá dado por município (permite filtrar RS/POA),
  mas não confirmei se algum modelo registrado publica previsão semanal de 12 semanas para POA
  especificamente — os sprints (itens 2 e 3) cobriram estados, não a granularidade de cidade única.
- **Aplicável a POA?** Sim, como fonte de dado adicional (clima, sociodemografia) e como vitrine para
  eventualmente **registrar o próprio modelo do projeto** e comparar contra os demais publicamente.

---

## 2. 1º Sprint InfoDengue-Mosqlimate (IMDC24, 2024) — a régua nacional mais recente

Araujo, Carvalho [...], Codeço, Coelho, *Leveraging probabilistic forecasts for dengue preparedness and
control: the 2024 Dengue Forecasting Sprint in Brazil*, **PNAS** 123(7):e2508989123 (2026); preprint
medRxiv `10.1101/2025.05.12.25327419`.

- 🔵 **5 estados avaliados: Amazonas, Ceará, Goiás, Minas Gerais, Paraná** — escolhidos para cobrir
  gradiente latitudinal equador→subtropical. **Rio Grande do Sul NÃO participou** desta 1ª edição.
- 🔵 **7 modelos, 6 equipes:** Dobby Data (LSTM), Global Health Resilience/GHR (bayesiano
  espaço-temporal), GeoHealth (LSTM+Prophet), Ki-Dengu Peppa (decomposição de série, 2 variantes),
  BB-M (bayesiano só-histórico, baseline), DS_OKSTATE (CNN-LSTM).
- 🔵 **Baseline:** dois ensembles-referência — **E1** (pooling linear, pesos iguais) e **E2** (pooling
  logarítmico, pesos otimizados por CRPS na temporada anterior).
- 🔵 **Métrica:** CRPS, log score, interval score (proper scoring rules), previsão semanal para o **ano
  epidemiológico inteiro** (~52 semanas à frente, dado liberado em junho para prever a partir de outubro).
- 🔵 **Resultado:** 2023 — M6 e M4 melhores; 2024 (fora da amostra, ano atípico) — M2 e M5 com "melhor
  desempenho", mas **nenhum modelo se destacou de forma consistente** entre estados/anos. O ensemble E2
  superou a maioria em 2023, resultado **misto** em 2024.
- **Código aberto:** repositórios por equipe (não centralizados; ver item 3 para os do 2º sprint, mesma
  organização GitHub `Mosqlimate-project`).
- **Aplicável a POA?** Parcial — é o precedente nacional mais próximo, mas em nível **estadual**, não
  municipal, e não incluiu RS. O achado "nenhum modelo consistente no ano atípico" é diretamente análogo
  ao que POA viveu em 2024-2025 (já registrado na varredura de literatura, item 9).

---

## 3. 2º Sprint InfoDengue-Mosqlimate (IMDC25, 2025) — agora com RS

Repositório: [`github.com/Mosqlimate-project/2nd_IMDC_sprint_results`](https://github.com/Mosqlimate-project/2nd_IMDC_sprint_results).
Relatório: Zenodo `10.5281/zenodo.17516484`.

- 🔵 **15 equipes, 19 modelos, todos os estados brasileiros**, temporadas 2025-2026. **RS incluído.**
- 🔵 **Métrica: WIS normalizado** (WIS_norm = ΣWIS / casos totais no período) — pensada para comparar
  estados de escala de caso muito diferente, mais uma métrica de **pico** (WIS médio numa janela de 3
  semanas centrada no pico).
- 🔵 **Melhor modelo por região (ranking WIS):** Sul → **Dengue Oracle M1**; Sudeste → Dengue Oracle M2;
  Norte → LNCC-AR_p-1; Nordeste e Centro-Oeste → GHR Model.
- 🔵 **Ensemble top-5 (mediana dos 5 melhores modelos por estado) teve skill score mediano de 0,12**
  contra o melhor modelo individual (redução de erro ~12% na mediana dos estados) — **com exceções onde
  o ensemble foi pior** (ex.: RJ). RS aparece entre os estados onde o ensemble teve bom desempenho em
  2025, junto com PR e MT ⚠️ (número específico de RS não localizado em texto, só em gráfico).
- ⚠️ Não localizei o número de WIS_norm do modelo vencedor no Sul (Dengue Oracle M1) isolado para RS —
  o relatório é majoritariamente gráfico (PNG), não tabular.
- **Código aberto:** parcial — links de repositórios por equipe no relatório (IMPA-Tech/Preditores da
  Picada, LaCiD/UFRN, D-FENSE LNCC/UERJ, Imperial College London, ISI Foundation); "Dengue Oracle" e
  "GHR", os vencedores, **não tiveram repositório isolado localizado** nesta varredura.
- **Roda nos nossos dados?** Não diretamente — os modelos são treinados/avaliados na infraestrutura do
  Mosqlimate, sem instalação local documentada e acessível nesta varredura.
- **Aplicável a POA?** Sim, é a **régua nacional mais atual em nível estadual incluindo RS** — mas ainda
  não em granularidade de município.

---

## 4. Lowe et al. 2014/2016 — sistema bayesiano de alerta precoce (precursor)

Lowe R, Coelho CAS, Barcellos C, Carvalho MS, Catão RC, Coelho GE, Ramalho WM, Bailey TC, Stephenson DB,
Rodó X. *Evaluating probabilistic dengue risk forecasts from a prototype early warning system for
Brazil*. **eLife** 5:e11285 (2016). DOI `10.7554/eLife.11285`. Precursor: Lowe et al. 2013, *Lancet
Infect Dis*, DOI (via PubMed 24841859), previsão para a Copa do Mundo 2014.

- 🔵 **Modelagem:** hierárquico bayesiano espaço-temporal (INLA), clima sazonal previsto (GloSea)
  + vigilância precoce como insumo, para **553 microrregiões do Brasil**, incluindo **Porto Alegre**
  como uma das 12 cidades-sede avaliadas para a Copa (previu risco **baixo** para POA em jun/2014).
- 🔵 **Horizonte: 3 meses** — mesmo horizonte-alvo do projeto.
- 🔵 **Alvo:** categórico (risco alto/médio/baixo), não erro pontual de casos.
- 🔵 **Régua:** média sazonal histórica 2000-2013 (equivalente a "clima do lugar", não "ano passado
  específico").
- 🔵 **Resultado: venceu a régua** — taxa de acerto (hit rate) de risco alto **57% (81 acertos) contra
  33% (46 acertos) do baseline** — 60 vs 95 perdas.
- **Código aberto:** não localizado (2013-2016, pré-era de repositórios públicos como prática padrão
  em epidemiologia computacional brasileira).
- **Aplicável a POA?** Sim, como **precedente direto brasileiro, mesmo horizonte de 3 meses, mesma
  cidade avaliada** (POA) — mas alvo categórico absorve erro de magnitude, o que facilita vencer a régua
  comparado ao alvo contínuo do projeto (já registrado na varredura de literatura, item 5).

---

## 5. D-MOSS — sucessor operacional da linha Lowe, avaliado formalmente (não Brasil)

Campbell AM, Colón-González F, Do Kien Quoc, Nguyen Hai Tuan et al. *Performance evaluation of an
operational dengue forecasting system (D-MOSS) in Vietnam*, **PLOS Global Public Health** (2026),
via PMC `PMC12965583`. Consórcio HR Wallingford + UK Space Agency, com participação de R. Lowe.

- 🔵 **Operacional no Vietnã desde jun/2019**, todas as 63 províncias, usando dado de satélite
  (precipitação, temperatura, água disponível) + previsão climática sazonal GloSea5 do UK Met Office.
- 🔵 **Horizonte: 1 a 6 meses**, com **duas réguas explícitas**: (1) amostragem aleatória da incidência
  observada; (2) **"seasonal expanding average"** — média sazonal histórica crescente, equivalente
  conceitual ao "mesma época do ano" do projeto, só que médio, não do ano anterior específico.
- 🔵 **Resultado por antecedência (RMSE, casos/100 mil hab.):** lead 1 → **20,35**; lead 2 → 26,02;
  lead 3 → 27,96; lead 4 → 28,52; lead 5 → 25,37; lead 6 → 25,99. **Geral: 25,70 contra 31,29 da régua
  sazonal — o modelo venceu a régua em todos os horizontes testados**, com a maior acurácia relativa no
  lead 1 (mas sem queda linear acentuada até o lead 6).
- **Código aberto:** não confirmado nesta varredura (documentação em `d-moss.org`, sem repositório
  público localizado).
- **Aplicável a POA?** Não roda nos dados de POA (Brasil não é um dos países-piloto: Vietnã, e depois
  expandido para outros países asiáticos) — mas é o **contraexemplo mais forte** encontrado de um
  sistema de previsão contínua de 3-6 meses que **vence** consistentemente uma régua sazonal, com
  avaliação operacional real (não só retrospectiva acadêmica). 🟡 Inferência: a diferença central para
  POA é a **régua** — "seasonal expanding average" (média de vários anos) tende a ser mais fácil de
  vencer que "ano passado específico" (mais ruidoso, mas também mais "atualizado").

---

## 6. VIGIA-Dengue — sistema aberto para o Distrito Federal, mesma lógica de POA

Repositório: [`github.com/ghostopw/VIGIA-Dengue`](https://github.com/ghostopw/VIGIA-Dengue).

- 🔵 **Cobertura:** Distrito Federal + RIDE-DF (34 municípios: DF, 29 de Goiás, 4 de Minas Gerais).
- 🔵 **Dado de entrada:** casos semanais por município via **InfoDengue** (nowcasting-corrigido), clima,
  população, indicadores censitários de vulnerabilidade socioambiental.
- 🔵 **Alvo:** classificação de risco alto/muito alto, horizonte de **4 semanas** (mais curto que o
  alvo de 12 semanas do projeto).
- 🔵 **Régua: persistência** (repetir o nível atual). **Resultado:** LightGBM AUC **0,830**, sensibilidade
  0,698, especificidade 0,803 — **venceu a régua de persistência (AUC 0,757)**. Brier score 26% melhor
  que o modelo de referência. Validação temporal por janela expansiva, 2019-2025.
- 🔵 **Código aberto e reproduzível**, com testes automatizados documentados.
- **Aplicável a POA?** Estruturalmente é o **precedente mais próximo em desenho** do projeto — mesma
  fonte de dado (InfoDengue), mesma ideia de régua de persistência/baseline simples, arquitetura
  LightGBM/HistGB-adjacente. Diferença chave: alvo é **classificação de risco**, não regressão contínua
  de casos, e horizonte é **4 semanas**, não 12. 🟡 Inferência: reforça, de novo, que alvo categórico com
  régua de persistência é mais fácil de vencer que regressão contínua com régua sazonal específica.

---

## 7. Painel Dengue RS (SES/CEVS) — vigilância, não previsão

[`dengue.saude.rs.gov.br`](https://dengue.saude.rs.gov.br/) e
[`ti.saude.rs.gov.br/dengue/painel_de_casos.html`](https://ti.saude.rs.gov.br/dengue/painel_de_casos.html).

- 🔵 **O que existe:** painel de **monitoramento** (casos confirmados, óbitos, hospitalizações,
  atualização diária) e **nível de alerta municipal** (3 níveis) para apoio à gestão — insumos, ações
  de controle. Fonte: material institucional CEVS/SES-RS, Plano de Contingência Dengue 2024-2025.
- 🔴 **Não há modelo preditivo publicado** — nenhuma menção, em nenhuma fonte consultada, a um modelo
  estatístico ou de ML que gere **previsão numérica de casos futuros** para o RS ou seus municípios.
  O painel é descritivo (o que aconteceu / está acontecendo), não prognóstico (o que vai acontecer).
- **Código aberto:** não há — é ferramenta institucional interna (Power BI / painel proprietário).
- **Aplicável a POA?** **Achado negativo relevante para a tese:** não existe, hoje, um sistema estadual
  ou municipal de previsão de dengue em produção no RS que o projeto precise "vencer" ou comparar — o
  projeto de POA preencheria uma lacuna real de ferramenta, não estaria competindo com algo já existente
  no próprio estado.

---

## 8. Modelo do IMPA (Instituto de Matemática Pura e Aplicada) — 7 capitais, sem POA

Publicado em *Expert Systems with Applications* (Elsevier). Fonte: divulgação institucional IMPA,
[impa.br/notices/modelo-do-impa-preve-surtos-de-dengue-com-80-de-acerto](https://impa.br/notices/modelo-do-impa-preve-surtos-de-dengue-com-80-de-acerto/)
— DOI do artigo não localizado nesta varredura (só a nota institucional foi lida).

- 🔵 **Dado de entrada:** só temperatura e precipitação (índice climático), sem dado de vetor nem clima
  detalhado — deliberadamente simples ("qualquer pessoa com Python básico roda").
- 🔵 **Horizonte:** até **6 meses** à frente.
- 🔵 **Cobertura: 7 capitais — Aracaju, Recife, São Luís, Belo Horizonte, Salvador, Manaus, Rio de
  Janeiro.** ⚠️ **Porto Alegre e RS não estão entre as cidades testadas** — capitais do Sul, com clima
  subtropical e sazonalidade de dengue diferente das capitais tropicais/equatoriais testadas, ficaram de
  fora.
- 🔵 **Métrica: "80% de acerto"** (subiu de 72% após ajuste) — ⚠️ **não especificado** se é acerto de
  surto sim/não, categoria de risco ou magnitude; sem baseline de comparação citado na nota institucional.
- 🔵 **Código aberto**, mencionado como disponível, mas sem URL de repositório localizada nesta varredura.
- **Aplicável a POA?** Baixa — não testado em clima subtropical, métrica de "acerto" mal especificada, e
  sem regra de comparação (régua) explícita para julgar se 80% é bom ou trivial.

---

## 9. Comparativo CatBoost × GRU em 27 capitais — Porto Alegre testado e **falhou**

**Título completo não identificado com autores nesta varredura** (acesso à ficha de autoria bloqueado por
reCAPTCHA do PubMed). *Comparative evaluation of machine learning strategies for short-term dengue
forecasting in Brazilian capital municipalities*, **International Journal of Biometeorology** (2026),
DOI `10.1007/s00484-026-03300-7`.

- 🔵 **Cobertura: as 27 capitais brasileiras (26 estaduais + Brasília) — inclui Porto Alegre e
  Florianópolis.**
- 🔵 **Modelos:** GRU (rede neural recorrente, arquitetura multi-entrada/multi-saída) vs. **CatBoost**
  (gradient boosting, estratégia "Direct": um modelo por horizonte — mesmo desenho que o "um modelo por
  horizonte" que o projeto usa hoje).
- 🔵 **Horizonte: até 4 semanas** (H1-H4) — mais curto que os 12 do projeto. **Validação walk-forward.**
- ⚠️ **Sem régua/baseline explícito** localizado — a comparação reportada é só entre os dois modelos
  propostos, não contra persistência ou sazonal.
- 🔴 **Resultado para Porto Alegre: R² = −0,2064, MAE = 0,2219, sMAPE = 160%** (CatBoost) — **desempenho
  pior que prever a média**, o pior ou entre os piores resultados do estudo entre as 27 capitais.
  Contraste: Goiânia (R² 0,92) e João Pessoa (R² 0,90) tiveram os melhores resultados.
  ⚠️ Escala do alvo (MAE 0,22) sugere taxa de morbidade normalizada, não caso bruto — **não comparável**
  em unidade ao MAE 243,8 de POA, mas o **R² negativo é comparável em direção**: o próprio artigo mostra
  que um modelo genérico de ML nacional **não generaliza para Porto Alegre**, mesmo em horizonte curto
  (4 semanas) — o projeto perde a régua em 12 semanas, este estudo mostra o modelo perdendo até para a
  própria média em 4 semanas, na mesma cidade.
- **Código aberto:** não mencionado; dados "mediante solicitação ao autor correspondente".
- **Aplicável a POA?** **Achado o mais diretamente relevante desta varredura**: é evidência **externa e
  independente**, na própria cidade do projeto, de que modelos de ML treinados de forma padrão
  falham especificamente em Porto Alegre — reforça a hipótese de que o problema de POA não é
  peculiaridade do pipeline do projeto, é uma característica da série da cidade (curta, com poucos
  picos, sazonalidade atípica no Sul).

---

## 10. Random Forest mensal, múltiplas cidades — vence a régua sazonal em 1 mês

Colón-González et al. (grupo associado a R. Lowe), *Machine-learning–based forecasting of dengue fever
in Brazilian cities using epidemiologic and meteorological variables*, **American Journal of
Epidemiology** 191(10):1803-1812 (2022). DOI `10.1093/aje/kwac090`.

- 🔵 **Dado:** casos + variáveis climáticas/epidemiológicas mensais, **2007-2019**, múltiplas cidades
  brasileiras (⚠️ lista exata de cidades e se inclui POA não confirmada nesta varredura — fetch não
  aprofundado no texto completo).
- 🔵 **Horizonte: 1 mês** (bem mais curto que os 12 semanas/3 meses do projeto).
- 🔵 **Régua: sazonal ingênuo** ("seasonal naive baseline").
- 🔵 **Resultado: Random Forest venceu a régua sazonal**, com erro menor que gradient boosting, rede
  neural feed-forward e regressão de vetores de suporte — mas **"modelos diferentes venceram em cidades
  diferentes"** (não há um único modelo vencedor universal).
- **Código aberto:** não localizado nesta varredura.
- **Aplicável a POA?** Parcial — confirma que **vencer a régua sazonal é possível em horizonte de 1
  mês**, mas o próprio achado de "modelo vencedor varia por cidade" é consistente com o achado do item 9
  (modelo genérico falha em POA especificamente) — o horizonte de 1 mês é bem mais curto que o alvo de
  12 semanas do projeto, então não é comparação direta de dificuldade.

---

## 11. Sprint como fonte de projeção nacional 2026 — não é previsão de POA

Fiocruz/FGV, divulgação institucional (Portal FGV), *Modelo preditivo antecipa dinâmica da dengue no
Brasil*, projeção para a temporada 2025-2026 usando o **ensemble dos 5 melhores modelos por estado** do
2º sprint (item 3).

- 🔵 **Projeção divulgada: ~1,8 milhão de casos no Brasil em 2025-2026**, com **redução prevista para
  RS**, junto com PR, SP, AC e AP (🟡 inferência: "redução" é qualitativo na divulgação pública, não vi
  número específico de RS na nota institucional).
- 🔴 **Não há previsão numérica semanal publicamente disponível para Porto Alegre** — a divulgação é em
  nível de manchete/estado, não a série completa por município que o projeto precisaria para comparação
  pareada por `data_alvo`.
- **Aplicável a POA?** Não diretamente utilizável como comparação quantitativa — é evidência de que a
  **infraestrutura existe** (item 1, Mosqlimate) para eventualmente extrair essa previsão via API, mas
  a varredura não confirmou que o dado granular por município/RS esteja disponível sem contato direto
  com os autores ou solicitação de acesso à API autenticada.

---

## Tabela-resumo

| # | Modelo/sistema | Quem/onde | Dado de entrada | Horizonte | Régua | Venceu a régua? Por quanto | Código aberto | Roda nos nossos dados? |
|---|---|---|---|---|---|---|---|---|
| 0 | InfoDengue | Fiocruz/FGV, nacional | Casos SINAN nowcasted | Corrente (nowcasting) | — (não é forecast) | N/A — não faz previsão de 3 meses | [AlertaDengue/AlertaDengue](https://github.com/AlertaDengue/AlertaDengue) | Como insumo de dado, sim |
| 1 | Mosqlimate | Fiocruz/FGV, plataforma | Casos, clima, vetor, sociodemografia | Depende do modelo registrado | — (plataforma, não modelo) | N/A | Parcial (API autenticada) | Sim, como fonte de dado/API |
| 2 | 1º Sprint IMDC24 | 6 equipes, 5 estados (AM/CE/GO/MG/PR) | Casos+clima harmonizados | Semanal, ano epidemiológico | Ensemble E1/E2 | Nenhum modelo consistente 2024 | Por equipe, parcial | Não (nível estadual, sem RS) |
| 3 | 2º Sprint IMDC25 | 15 equipes/19 modelos, todos estados | idem + vetor | Semanal + janela de pico | Ensemble top-5 | SS mediano 0,12 do ensemble | Parcial, por equipe | Não (nível estadual) |
| 4 | Lowe et al. 2016, eLife | 553 microrregiões BR (POA incluída) | Clima sazonal previsto | 3 meses | Média sazonal histórica | **Sim** — 57% vs 33% hit rate | Não localizado | Não (alvo categórico) |
| 5 | D-MOSS | Vietnã, HR Wallingford/UK Space Agency | Satélite + clima sazonal GloSea5 | 1-6 meses | Seasonal expanding average | **Sim**, todos os horizontes — RMSE 25,70 vs 31,29 | Não confirmado | Não (país diferente) |
| 6 | VIGIA-Dengue | DF + RIDE-DF, open source | InfoDengue + clima + censo | 4 semanas | Persistência | **Sim** — AUC 0,830 vs 0,757 | [ghostopw/VIGIA-Dengue](https://github.com/ghostopw/VIGIA-Dengue) | Não direto, mas desenho replicável |
| 7 | Painel Dengue RS (SES/CEVS) | RS, institucional | Vigilância corrente | — | — (não prevê) | N/A — não é modelo preditivo | Não (proprietário) | Não existe para comparar |
| 8 | Modelo IMPA | 7 capitais (sem POA/RS) | Só temperatura+precipitação | 6 meses | Não citado | "80% de acerto" (métrica não especificada) | Mencionado, URL não achada | Não testado no Sul |
| 9 | CatBoost×GRU 27 capitais | Int. J. Biometeorology 2026, POA incluída | Casos+clima por capital | 4 semanas | Nenhum explícito | **Modelo falhou em POA**: R² −0,21, sMAPE 160% | Não | Evidência de que POA é difícil, não roda |
| 10 | RF mensal multi-cidade | AJE 2022, Colón-González | Casos+clima mensal 2007-2019 | 1 mês | Sazonal ingênuo | **Sim**, mas vencedor varia por cidade | Não localizado | Não (POA não confirmado na amostra) |
| 11 | Projeção nacional 2026 | Fiocruz/FGV, divulgação | Ensemble do 2º sprint | Temporada (anual) | — | Redução qualitativa prevista p/ RS | Via Mosqlimate (item 1) | Não (sem série numérica pública p/ POA) |

---

## Síntese para o projeto

- **Não existe, hoje, um sistema operacional brasileiro (estadual, municipal ou nacional) que preveja
  casos de dengue especificamente para Porto Alegre em horizonte de 3 meses** — nem para comparar, nem
  para competir. O painel do RS (item 7) é vigilância, não previsão.
- **O achado mais forte para a tese é o item 9**: um modelo de ML genérico, nacional, treinado nas 27
  capitais, **falha especificamente em Porto Alegre** (R² negativo), mesmo em horizonte de 4 semanas —
  evidência externa e independente, na própria cidade, de que o problema não é do pipeline do projeto.
- **Os sprints nacionais (itens 2 e 3) só chegaram a incluir RS na 2ª edição (2025)**, em nível
  **estadual**, nunca municipal — não há como baixar uma série de previsão comparável a POA hoje.
- **D-MOSS (item 5) é o contraponto mais forte** de um sistema que vence a régua sazonal de forma
  consistente em 1-6 meses — mas usa dado de satélite + previsão climática sazonal formal (GloSea5), que
  o projeto não tem acesso equivalente para o Brasil.
