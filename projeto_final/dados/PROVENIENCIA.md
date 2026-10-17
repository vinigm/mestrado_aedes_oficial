# Proveniência de `tabela_final.csv`

Escrito em 12/10/2026. Fonte: `../PREPROCESSAMENTO_mapa_2026-10-10.md` (mapa do pré-processamento) e
`../mapa_do_codigo_antigo_2026-10-09.md`. **Rótulos:** ✅ medido ou lido no código em 10-12/10/2026 · 📄 consta só em documento
do projeto, não re-medido (depende de dado de acesso restrito) · ⚠️ ponto frágil.

## 1. O que é este arquivo

- **`tabela_final.csv`:** uma linha por **semana epidemiológica** (domingo a sábado), 23/09/2012 a 09/08/2026.
  - ✅ **725 linhas × 36 colunas**, grade contínua de passo 7 dias, todas as datas são domingos.
  - ✅ Hash **sha256**: `6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f` (arquivo `tabela_final.sha256`).
  - ✅ **Snapshot certificado em 26/09/2026** (certificação adversarial da reversão da base de 2026). Hash anterior à recaptura
    de clima de 29/08/2026: `96b21b84…` (📄).
- **É o único dado de entrada do pacote.** É agregado semanal da cidade inteira: **não tem dado pessoal**.

## 2. De onde vem cada bloco de colunas

| Colunas | Origem | Como entra |
|---|---|---|
| `fonte`, `SE`, `data_inicio_semana_epidemi`, `ano`, `semana` | Grade semanal (domingo a sábado) | Semana epidemiológica pela regra da quarta-feira: a semana pertence ao ano da sua quarta-feira ✅ |
| `numero_de_armadilhas`, `aedes_aegypti`, `aedes_albopictus`, `culex_sp`, `aedes_aegypti_por_armadilha`, `denominador_aproximado` | **Vetor:** MI-Aedes / SMS-POA (Prefeitura de Porto Alegre), armadilhas **MosquiTRAP** | Soma por semana na cidade; ver 2.1 |
| 22 colunas `precip_*`, `dias_de_chuva`, `temp_*`, `orvalho_*`, `umid_*`, `pressao_*`, `radiacao_*`, `vento_*` | **Clima:** NASA POWER, ponto único (−30,03; −51,23) | Diário agregado em semanas domingo a sábado; ver 2.3 |
| `casos_confirmados` | **Casos:** Sinan / DENGBR (OpenDataSUS), dengue em Porto Alegre | Contagem por semana de início dos sintomas; ver 2.2 |
| `nino34_anom`, `oni` | **ENSO:** NOAA CPC (Niño 3.4 e ONI, 1 valor por mês) | Presentes na tabela, **fora do modelo** (ver 2.4) |

### 2.1 Vetor (armadilhas)

- **Fonte:** série de captura do programa MI-Aedes da Secretaria Municipal de Saúde de Porto Alegre (SMS-POA). Armadilha
  **MosquiTRAP**; a contagem usada no modelo é de **fêmeas de *Aedes aegypti*** por vistoria. 📄
- **Cobertura:** 12 arquivos de 2012 a 2025 entregues pela Secretaria (5 formatos de exportação) mais a **raspagem própria**
  do portal MI-Aedes para 2026. 📄 Linhas da tabela por origem: ✅ **686** `secretaria` · **32** `raspagem` (04/01 a 09/08/2026) ·
  **7** sem dado (`fonte` vazia).
- **7 semanas sem vistoria** (vetor vazio, nunca 0 nem interpolado) ✅: 24/12/2017, 31/12/2017, 07/01/2018, 21/08/2022 e as
  três da enchente de 28/04, 05/05 e 12/05/2024.
- **`aedes_aegypti_por_armadilha`** = fêmeas de *Ae. aegypti* ÷ `numero_de_armadilhas`. ✅ Soma da coluna = 280,8343.
  - ⚠️ **`numero_de_armadilhas` conta inspeções (linhas), não armadilhas distintas.** O texto não pode chamá-la de "por armadilha
    distinta" nem afirmar equivalência com o IMFA oficial sem essa ressalva.
  - ⚠️ `aedes_aegypti` (contagem) é fêmeas + machos; a densidade usa só fêmeas. Não são comparáveis sem aviso.
  - **`denominador_aproximado` = 1** em ✅ 324 semanas (23/09/2012 a 23/12/2018), em que o campo de inspeção realizada não existe
    e o denominador é o número de registros. Nenhuma semana da janela de avaliação é aproximada ✅.
- ⚠️ **Raspagem 2026:** é a única parte da série sem conferência independente; a última semana raspada é sempre parcial; 4 das 102
  origens avaliadas em h = 1 usam vetor da raspagem ✅.

### 2.2 Casos

- **Fonte:** microdados nacionais do Sinan (arquivos DENGBR18 a DENGBR26, OpenDataSUS), filtrados para Porto Alegre. 📄
- **Filtro:** município de **notificação** `ID_MUNICIP == 431490` e `CLASSI_FIN` ∈ {10, 11, 12} (dengue confirmada). Total ✅
  **56.624 casos**: 55.017 (10) + 1.429 (11) + 178 (12).
  - ⚠️ É município de **notificação**, não de residência (o Estado usa residência); o alvo difere do oficial (hipótese: cerca de 10% maior).
    ✅ Decisão do Vinicius (10/10/2026): o alvo continua por município de notificação; na leitura de alarme, o limiar do plano
    municipal (definido sobre residentes) é convertido para a escala da notificação.
  - ⚠️ `CLASSI_FIN = 1` (confirmado genérico) fica de fora; **não foi medido** quantos há.
  - ⚠️ Sem deduplicação.
- **Semana:** **início dos sintomas** (`SEM_PRI`), não notificação nem confirmação. ✅ 56.624 de 56.624 casos casam com uma semana da grade.
- **Início da série:** primeira semana com caso confirmado, **18/02/2018** (SE 201808); dentro da série, semana sem caso = 0
  (✅ 428 semanas com série, 158 zeros). As 282 semanas anteriores ficam vazias ("sem série"). ⚠️ O início é definido pelo dado, não
  por cobertura do Sinan.
- **Fim da série:** última semana com caso **26/04/2026**; depois disso a coluna fica vazia (nunca 0).
- ⚠️ Cada ano do Sinan foi extraído em **data diferente** (data de modificação dos arquivos, de 24/08/2025 a 14/06/2026; o `DENGBR26_atualizado_set26`, de 13/09/2026, não entrou na tabela), então a
  maturidade da classificação final é heterogênea entre os anos. A data de extração oficial não foi registrada.
- ✅ Por ano de calendário do domingo: 2018 = 4 · 2019 = 489 · 2020 = 37 · 2021 = 72 · 2022 = 5.583 · 2023 = 6.600 · 2024 = 19.034 ·
  2025 = 24.793 · 2026 = 12. O treino inicial (2018 a 2020) vem de um regime de quase nenhum caso.

### 2.3 Clima

- **Fonte:** NASA POWER, comunidade AG, ponto único em Porto Alegre. Nove medidas diárias (precipitação, ponto de orvalho,
  temperatura média/mínima/máxima, umidade relativa, pressão em kPa, radiação, vento a 10 m); `-999` vira ausente. ✅ (código)
- **Agregação:** semanas domingo a sábado; mínimo, média e máximo; chuva em soma e em nº de dias com ≥ 1 mm. Só semanas com 7 dias.
- ✅ 727 semanas × 22 colunas, 23/09/2012 a 23/08/2026, **0 ausentes** na tabela.
- **Recaptura de 29/08/2026:** o clima passou a começar em 2012. ✅ 365 semanas (30/12/2018 a 21/12/2025) idênticas à captura antiga
  (`rtol = 1e-9`); 23 semanas (de 28/12/2025 em diante) foram reprocessadas pela NASA.
- ⚠️ A NASA **reprocessa semanas recentes**. As 6 colunas de clima do modelo não divergem em nenhuma linha usada na avaliação ✅.
- **Validação externa (não é etapa do pipeline):** NASA POWER × estação INMET A801, 689 semanas pareadas, Spearman: `temp_media`
  0,988 · `temp_max` 0,918 · `pressao_media` 0,980 · `umid_media` **0,793** (abaixo do critério pré-declarado de 0,90). 📄

### 2.4 ENSO

- `nino34_anom` e `oni`: um valor **mensal** copiado para cada semana do mês (✅ 439 semanas não vazias em `nino34_anom` e 434 em `oni`, a partir de 07/01/2018).
- **Estão na tabela e fora do modelo.** Decisão de 24/09/2026: o uso de ENSO se mostrou vazamento. O modelo de referência **não**
  usa El Niño; deve ficar explícito no texto.

## 3. Quais scripts do projeto antigo geraram a tabela (nomes; nenhum código foi copiado)

| Etapa | Script / função do projeto antigo | Observação |
|---|---|---|
| Casos Sinan → 1 linha por caso | `preparo/consolidar_sinan.py` | Gera arquivo individual de casos, **não distribuído** |
| Clima | `preparo/capturar_clima.py` (API NASA POWER) | Resposta diária **não é arquivada** |
| ENSO | `preparo/capturar_enso.py` (API NOAA) | — |
| Limpeza e unificação dos arquivos da Secretaria, e parquet de inspeções | Scripts privados, **fora do pacote e do repositório público** | Tratam dado de acesso restrito (decisão de 09/10/2026) |
| Agregação semanal do vetor e grade contínua | `dominio/montagem_tabela.py:agregar_vetor_semanal` | Semana sem inspeção = vazio |
| Junção de vetor, clima, casos e ENSO e gravação | `dominio/montagem_tabela.py` via `montar.py` | Gera `tabela_final.csv` |

⚠️ **Não rodar** `consolidar_sinan` nem `montar.py` hoje: trazem 2026 de volta e novas semanas de raspagem, e não reproduzem o hash.

## 4. Decisões que valem para o pacote

- **2026 fora da avaliação** (Vinicius, 26/09/2026). A tabela vai até 09/08/2026, mas o corte de maturidade de 12 semanas
  apaga `casos` a partir de **08/02/2026** (a última semana com caso é 26/04/2026; 01/02/2026 é mantida). A última semana-alvo
  avaliada é **01/02/2026**; a avaliação cobre de 07/01/2024 a 01/02/2026 (✅ 102 semanas por horizonte, após as 7 perdidas
  pela enchente).
- **A base de armadilhas da Marília não entra** no artigo nem na modelagem (Vinicius, 10/10/2026). Nenhuma etapa do caminho das 22
  variáveis a lê (✅ no código). O lastro da conferência da base de armadilhas, que usava a Marília como padrão de comparação,
  precisa ser reescrito sem ela (provas independentes: 0 vistorias em domingo depois da correção das datas; a enchente de 2024
  reaparece como semanas sem inspeção; revisitas 18.628 → 489) 📄.
- **Correção das datas invertidas pelo Excel** num dos arquivos da Secretaria (2022 a jul/2025): 📄 regra determinística;
  ⚠️ as contagens (60.539 células trocadas de volta, só 55.895 com dia ≠ mês) saíam só no terminal e **nenhum registro foi localizado**.

## 5. O que NÃO é reproduzível a partir do dado bruto

O que **se reproduz**: tudo da `tabela_final.csv` em diante, conferido por sha256. O que vem antes é **descrito, não reexecutável**:

- ⚠️ **Clima por API ao vivo, sem arquivo diário guardado.** A resposta diária de 2012 a 2018 não está arquivada; a NASA reprocessa
  semanas recentes (23 mudaram em 29/08/2026). Refazer a captura hoje pode dar valores diferentes.
- ⚠️ **Sinan: arquivos com datas de extração diferentes**, e o script de consolidação hoje escolheria o arquivo `DENGBR26_atualizado`
  (19 casos) em vez do usado na tabela (12 casos). Não reproduz o snapshot.
- ⚠️ **Raspagem do portal MI-Aedes:** feita à mão, semanal; o portal só expõe a semana corrente (semana perdida é irrecuperável) e
  o acervo cresce, então remontar traria semanas novas. Raspagem de 2026 sem conferência independente.
- ⚠️ **Dados brutos da Secretaria:** acesso restrito, sob guarda da Secretaria; ficam **fora** do pacote. Sem eles não se
  regenera o vetor. As contagens do tratamento bruto (636.587 inspeções, 2.742 armadilhas, 81 bairros, 236.166 fêmeas de
  *Ae. aegypti*) constam só em documento 📄: o arquivo de origem não foi aberto nesta construção.
- ⚠️ **Seleção das 6 colunas de clima:** feita com LightGBM (`n_jobs=-1`, **sem semente**), fora do walk-forward. A lista foi
  tomada do log certificado, **não recalculada**: `temp_media_lag4`, `umid_media`, `temp_media_lag3`, `temp_max`,
  `pressao_media_lag3`, `pressao_media_lag4`. No pacote, ela fica **congelada** na configuração (decisão de 09/10/2026).
- ⚠️ **Avaliação sobre dado consolidado, não vintage:** o corte de maturidade age uma vez, no fim da série; não simula o dado
  disponível à época de cada previsão. Entra como limitação no artigo.
