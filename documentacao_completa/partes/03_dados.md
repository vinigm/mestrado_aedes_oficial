# Parte 3 — Os dados

## 3.1 A rede de armadilhas MI-Aedes

### 3.1.1 O que é uma armadilha MosquiTRAP

O projeto usa, como um dos seus dados de entrada, a contagem de mosquitos capturados por uma rede de
armadilhas espalhadas pela cidade de Porto Alegre. O modelo de armadilha usado por essa rede se chama
**MosquiTRAP**.

Uma MosquiTRAP é um recipiente plástico escuro, de formato cilíndrico, que funciona como uma **armadilha
de oviposição**: ela imita, para a fêmea do mosquito, um lugar ideal para pôr ovos (um recipiente com água
parada). Dentro dela existe um **atrativo químico** — uma substância sintética que reproduz o odor que a
fêmea grávida procura para escolher onde desovar — e uma superfície adesiva. A fêmea entra atraída pelo
atrativo, fica presa na superfície adesiva e é capturada viva. Depois, um técnico recolhe o conteúdo da
armadilha periodicamente e os insetos capturados são identificados em laboratório, por espécie (*Aedes
aegypti*, *Aedes albopictus*, *Culex sp.* e outras) e por sexo.

**Por que isso importa para os dados:** a armadilha captura principalmente **fêmeas adultas em busca de
local para desovar**. Machos não têm o mesmo comportamento de procurar sítio de oviposição e são raros
nas capturas — por isso a estatística oficial da rede (ver **3.1.2**) é construída sobre a contagem de
fêmeas, não sobre o total de mosquitos.

**FATO (registrado no código do projeto, `modelagem_aedes/`).** A tabela bruta da Secretaria Municipal de
Saúde de Porto Alegre (SMS-POA) guarda, para cada armadilha e cada semana, contagens separadas de fêmeas e
de machos de cada espécie (`aegypti_femea`, `aegypti_macho`, `aegypti_total`, e o mesmo para
*albopictus* e *Culex*). Isso confirma, nos próprios dados, que a distinção fêmea/macho é feita na
identificação em laboratório, e não estimada.

### 3.1.2 O índice de fêmeas por armadilha

A métrica oficial que resume, numa cidade ou num bairro, o quanto o mosquito está presente numa semana é
o **índice de fêmeas por armadilha (IFA)**: quantas fêmeas de *Aedes aegypti*, em média, cada armadilha
vistoriada capturou naquela semana. "Vistoriada" quer dizer que um técnico foi até a armadilha, recolheu
o conteúdo e o registro chegou ao sistema — uma armadilha instalada mas não visitada naquela semana não
entra no denominador.

**A fórmula:**

```
IFA = F / A
```

Onde:

- **IFA** — índice de fêmeas por armadilha, na semana e no recorte geográfico considerado (cidade,
  bairro, zona);
- **F** — número de fêmeas de *Aedes aegypti* capturadas naquele recorte, naquela semana;
- **A** — número de armadilhas efetivamente **vistoriadas** (com leitura registrada) nesse mesmo recorte
  e semana.

**Exemplo numérico, com dados reais do projeto — a semana epidemiológica 11 de 2025 (SE **`202511`**, que
começa em 09/03/2025):** nessa semana, a tabela do projeto registra **877 armadilhas vistoriadas** na
cidade inteira e um índice de **1,058153** fêmeas por armadilha. Isolando a fórmula para achar o número
de fêmeas:

```
F = IFA × A = 1,058153 × 877 ≈ 928 fêmeas de Aedes aegypti
```

Ou seja: naquela semana, em média, mais de uma fêmea de *Aedes aegypti* foi encontrada em cada armadilha
vistoriada na cidade — quase 928 fêmeas ao todo, espalhadas pelas 877 armadilhas.

Um segundo exemplo, agora usando o **agregado histórico inteiro** da base certificada (ver **3.2.4**):
**FATO (conferido célula a célula em 13/09/2026, registrado em `ESTADO.md` §1)** — a base tem
**636.587 inspeções de armadilha** e **236.166 fêmeas de *Aedes aegypti*** capturadas ao longo de
**718 semanas** (23/09/2012 a 09/08/2026). O índice médio de todo o período é:

```
IFA_histórico = 236.166 / 636.587 ≈ 0,371
```

Ou seja, em média histórica, cada armadilha vistoriada em Porto Alegre captura um pouco mais de um terço
de uma fêmea de *Aedes aegypti* por visita — um número bem mais baixo do que o **1,058** da semana de
epidemia usada no primeiro exemplo, o que já ilustra que o índice varia fortemente ao longo do tempo, com
picos sazonais.

⚠️ **Uma armadilha para não confundir:** o arquivo bruto da Secretaria também guarda a coluna
`aedes_aegypti` (ou, na tabela final do projeto, o mesmo nome), que soma **fêmeas e machos** capturados.
Ela **não é** o numerador do índice oficial. Um erro comum seria calcular "fêmeas por armadilha" dividindo
essa coluna pelo número de armadilhas: no exemplo acima, isso daria **937 ÷ 877 ≈ 1,068**, um número
próximo mas **diferente** do índice oficial de **1,058153**, porque a coluna de total inclui os poucos
machos capturados. O projeto preserva as duas colunas separadas exatamente para evitar essa confusão
(ver **3.9**).

### 3.1.3 Quem opera a rede, e com que frequência

**FATO.** A operação de campo — instalar as armadilhas, revisitá-las periodicamente e coletar o material
capturado — é feita pela vigilância em saúde da Secretaria Municipal de Saúde de Porto Alegre (SMS-POA):
é dela que o projeto recebe os arquivos brutos (pasta `arquivos_secretaria_saude_poa/`, ver **3.2.4**). A
frequência de vistoria é **semanal**: o portal público que expõe esses números para a cidade,
o **MI-Aedes** ("Monitoramento Inteligente do Aedes"), atualiza a leitura semana a semana, e é dele que
vem a segunda fonte de dados do projeto, a raspagem (ver **3.2.2**).

⚠️ **HIPÓTESE (não verificada por este projeto):** a tecnologia MosquiTRAP é comercializada pela empresa
Ecovec. Uma das autoras do artigo de referência da Silva et al. 2026 (ver Parte de literatura) tem vínculo
declarado com essa empresa, o que é consistente com a hipótese de que ela também é a fornecedora da
tecnologia usada em Porto Alegre — mas o projeto não teve acesso a um documento da Prefeitura que confirme
esse contrato, então isso fica registrado como hipótese, não como fato.

### 3.1.4 O índice oficial e suas faixas

O **Plano Municipal de Contingência de Arboviroses de 2026**, da SMS-POA, classifica a situação
entomológica (relativa aos insetos) da cidade em quatro faixas, usando o índice de fêmeas por armadilha
vistoriada (ver **3.1.2**):

| Faixa | Índice de fêmeas por armadilha (IFA) |
|---|---|
| Satisfatório | menor que **0,15** |
| Moderado | de **0,15** a **0,30** |
| Alerta | de **0,30** a **0,6** |
| **Crítico** | maior que **0,6** |

Comparando com os dois exemplos numéricos da seção 3.1.2: o índice médio histórico da cidade
(**≈ 0,371**) já cai na faixa **Alerta**, e o índice da semana epidemiológica 11 de 2025 (**1,058**) está
bem acima do limite de **Crítico**. Isso é coerente com o fato de 2025 ter sido um ano de epidemia forte
de dengue em Porto Alegre (ver Parte 1).

⚠️ Este índice mede **presença do mosquito**, não **casos de dengue**. Os dois são fenômenos diferentes
que o projeto tenta relacionar (ver Parte de resultados, §3.2 e §3.3 de `ESTADO.md`): ter mosquito não é o
mesmo que ter epidemia, e a relação entre os dois é justamente uma das perguntas que o projeto investiga.

---

## 3.2 As fontes de dados, uma a uma

O projeto combina **quatro fontes** de dados, cada uma com um período coberto, um volume, uma forma de
chegada até o repositório e uma fragilidade própria. As quatro entram juntas na "tabela final"
(ver **3.4**).

### 3.2.1 SINAN — o sistema nacional de notificação de agravos

O **Sistema de Informação de Agravos de Notificação (SINAN)** é o sistema do governo federal brasileiro
que registra, em todo o país, os casos de doenças de notificação obrigatória — doenças que, por lei,
todo profissional de saúde que as diagnostica é obrigado a comunicar às autoridades sanitárias. A dengue é
uma delas.

- **Como chega ao projeto:** o governo federal publica, no portal **OpenDataSUS**, um arquivo
  comprimido por ano (padrão de nome `DENGBR` + os dois últimos dígitos do ano, por exemplo
  `DENGBR26.csv.zip`), com uma linha por caso notificado de dengue **no Brasil inteiro**. O script
  `modelagem_aedes/preparo/consolidar_sinan.py` lê esses arquivos (eles são grandes demais para abrir de
  uma vez, então lê em pedaços de 300 mil linhas), filtra só os casos de Porto Alegre e só os
  **confirmados** (ver **3.3**), e gera um arquivo único, `casos_confirmados_poa.csv`, com um caso por
  linha.
- **Período coberto:** o projeto tem um arquivo `DENGBR` por ano, de 2018 a 2026. **FATO (registrado em
  `ESTADO.md` §1):** os casos só existem a partir de **18/02/2018** — não há 14 anos de série de casos como
  há de mosquito.
- **Volume:** cada arquivo anual nacional tem centenas de milhares a milhões de linhas (todo o Brasil);
  depois do filtro por Porto Alegre e por confirmação, sobram algumas centenas a poucos milhares de casos
  por ano (ver a tabela do Plano Municipal na Parte 1: de **5.144** casos confirmados em 2022 a
  **21.329** em 2025).
- **Fragilidade:** o governo às vezes **reexporta** o arquivo de um ano que o projeto já tinha, com uma
  versão mais completa (por exemplo, um arquivo com sufixo `_atualizado`). **FATO (corrigido em
  25/09/2026):** antes dessa data, o script juntava as duas versões do mesmo ano sem escolher uma, contando
  os casos em dobro — foi o que quase aconteceu com o arquivo de 2026 em 13/09/2026. Hoje o script escolhe
  **um único arquivo por ano**, com uma regra explícita (prioriza o nome com `_atualizado`; sem isso, o
  arquivo modificado mais recentemente no disco).

Cada caso, no arquivo do SINAN, carrega — entre outras — as colunas `SEM_PRI` (semana epidemiológica de
início dos sintomas), `SEM_NOT` (semana de notificação), `ID_MUNICIP` (município onde o caso foi
**notificado**), `ID_MN_RESI` (município de **residência** do paciente) e `CLASSI_FIN` (classificação
final do caso). Como essas quatro colunas moldam decisões centrais do projeto, elas voltam nas seções
**3.3** e **3.4**.

### 3.2.2 A raspagem semanal do portal MI-Aedes

O portal público **MI-Aedes**, da SMS-POA, expõe a contagem de mosquitos capturados pela rede de
armadilhas — mas **só a semana corrente**: não existe, nesse portal, um jeito de baixar o histórico
inteiro de uma vez. Por isso o projeto mantém uma **raspagem manual**: alguém (o próprio autor do
projeto) entra no portal a cada semana e baixa um arquivo com os números daquela semana.

- **Como chega:** arquivos `.xlsx`, um por coleta, salvos na pasta `Raspagem/Arquivos/`, com nome que
  já carrega a data da coleta, o número da semana e uma contagem aproximada de mosquitos (por exemplo,
  `dados_aedes_20250106_weekid02_137mosquitos.xlsx`). O script
  `modelagem_aedes/preparo/consolidar_raspagem.py` junta esses arquivos num histórico único. Quando a
  mesma semana foi raspada mais de uma vez (coletas em dias diferentes), fica só com o arquivo **mais
  completo** — o que tem mais mosquitos contados; em empate, o mais recente.
- **Período coberto:** hoje, só o pedaço de **2026** que a SMS-POA ainda não enviou oficialmente — de
  2012 a 2025 o projeto usa a série oficial da Secretaria (ver **3.2.4**), que é mais completa. A raspagem
  de **2025** foi mantida como conferência independente, mas não alimenta mais a tabela final.
- **Volume:** um arquivo por semana raspada, cada um com uma linha por armadilha vistoriada naquela
  semana (tipicamente algumas centenas de linhas).
- **Fragilidade — a mais grave do projeto para dados futuros:** essa raspagem é **manual, sem
  agendamento automático** (sem `cron`, sem `launchd`, os dois mecanismos comuns para automatizar tarefas
  recorrentes num computador). **FATO (registrado em `ESTADO.md` §1):** a semana de identificador
  **458** (05 a 11/10/2025) nunca foi raspada. Não houve prejuízo nesse caso porque a série oficial da
  Secretaria cobre 2025 inteiro — mas **daqui para frente**, uma semana que passe sem ser raspada em 2026
  em diante é uma semana **perdida para sempre**, porque o portal só mostra a semana corrente. Automatizar
  essa raspagem é um item em aberto do projeto (ver `PENDENCIAS.md`).

### 3.2.3 Os dados de clima

O clima entra no projeto como uma fonte totalmente diferente das duas anteriores: em vez de dados sobre
mosquitos ou pessoas, são medições meteorológicas diárias.

- **Como chega:** o script `modelagem_aedes/preparo/capturar_clima.py` baixa, pela internet, dados
  públicos do serviço **NASA POWER** (uma base de dados meteorológicos globais, de acesso público, mantida
  pela agência espacial norte-americana NASA, que não exige senha nem chave de acesso), para um ponto no
  centro de Porto Alegre (latitude −30,03, longitude −51,23). Os dados vêm dia a dia — chuva, temperatura,
  ponto de orvalho, umidade, pressão atmosférica, radiação solar e vento — e são agregados por semana, na
  mesma convenção de semana usada pelo resto do projeto (começando no domingo).
- **Período coberto:** desde **23/09/2012** — a mesma data em que abre a primeira semana com captura de
  mosquito na base certificada da Secretaria (ver **3.2.4**). Essa data foi escolhida deliberadamente:
  antes de 29/08/2026, o clima só cobria desde dezembro de 2018 (o início do bloco de dados chamado
  "Marília", hoje fora do fluxo — ver **3.2.4**), o que limitava a **interseção** entre clima e vetor a
  cerca de 379 semanas. Estendendo o clima para 2012, essa interseção passou para cerca de **718 semanas**,
  o que deu mais poder estatístico a testes que comparam clima e vetor como preditores.
- **Volume:** uma linha por semana, com cerca de vinte medidas de clima diferentes (ver a lista completa
  na **3.4.2**).
- **Fragilidade:** os dados **mais recentes** (as últimas semanas) podem mudar um pouco depois, porque a
  NASA ajusta suas próprias medições conforme recebe mais informação de satélite e de estações de
  superfície. Dados antigos, em compensação, são estáveis — não mudam mais depois de publicados.

### 3.2.4 A série da Secretaria Municipal de Saúde (a base do vetor)

Esta é a fonte de dados sobre mosquito que o projeto usa como principal, e a mais delicada em termos de
proteção de dados pessoais.

- **Como chega:** a SMS-POA entregou ao projeto **12 arquivos brutos** — um por ano, de 2012 a 2020 —, cada
  um num formato de planilha diferente ao longo do tempo (os anos de 2012 a 2018 usam nomes de coluna em
  código, como `QTD_AEDP_F`; os de 2019 e 2021 vêm em português, divididos em treze abas; o de 2020 usa um
  terceiro conjunto de nomes). O script
  `modelagem_aedes/preparo/limpar_arquivos_secretaria.py` traduz os três formatos para um vocabulário
  único, e `unificar_arquivos_secretaria.py` junta tudo num único arquivo (`.parquet`, um formato de
  arquivo tabular compacto e rápido de ler), com uma linha por **armadilha, numa semana** — o grão mais
  fino que existe, de onde dá para somar por bairro, por quadra ou pela cidade inteira.
- **Período coberto e volume: FATO (base certificada célula a célula em 13/09/2026, registrada em
  `ESTADO.md` §1)** — **636.587 inspeções**, **236.166 fêmeas de *Aedes aegypti*** capturadas, ao longo de
  **718 semanas** (23/09/2012 a 09/08/2026), cobrindo **81 bairros** e **2.742 armadilhas** diferentes ao
  longo do tempo. Faltam **7 semanas** em quatorze anos de série: quatro antigas, fora da temporada de
  mosquito, e **três da enchente de maio de 2024** (as semanas de 28/04, 05/05 e 12/05 daquele ano), quando
  as vistorias de campo foram interrompidas pela emergência climática.
- **Fragilidade — dado pessoal:** os arquivos **brutos** de 2012 a 2020 contêm **nome e telefone do
  morador** do endereço visitado. Por isso a pasta `arquivos_secretaria_saude_poa/brutos_secretaria/` é
  tratada como **datalake somente leitura**: nunca é editada, e está protegida de vazamento por estar
  listada na linha 55 do arquivo `.gitignore` do repositório (o que faz o sistema de controle de versão
  `git` **ignorar essa pasta inteira** — zero arquivos dela ficam rastreados ou enviados para qualquer
  lugar). O arquivo final que o projeto de fato usa (`secretaria_poa_armadilhas.parquet`) é gerado a partir
  da pasta `limpos_secretaria/`, que **não tem** os dados pessoais.
- **Duas fontes, sem vão:** de 2012 a 2025, quem cobre a série é a Secretaria; de 2026 em diante, é a
  raspagem própria do portal MI-Aedes (**3.2.2**), porque a Secretaria ainda não enviou o ano corrente.

**Bases legadas, preservadas mas fora do fluxo:** o projeto também guarda, sem nunca apagar, duas outras
séries de mosquito que serviram para **validar** a base certificada, mas que não alimentam mais a tabela
final:

- **Marília (2019–2023):** um conjunto de dados independente, usado como padrão-ouro de validação — foi
  comparando com ele que o projeto provou, em 16/08/2026, que a correção de datas da base certificada
  estava certa.
- **Raspagem própria de 2025:** feita antes de a Secretaria enviar o ano de 2025 oficialmente, serviu como
  conferência cruzada independente do mesmo período.

---

## 3.3 Caso confirmado, caso notificado e caso provável

Ao falar de "quantos casos de dengue" existiram numa semana, existem pelo menos três números diferentes
possíveis, e o projeto usa apenas um deles como alvo do modelo. É essencial defini-los sem ambiguidade.

### 3.3.1 As três definições

- **Caso notificado:** qualquer atendimento de saúde em que um profissional **suspeitou** de dengue e
  comunicou isso ao sistema (SINAN), abrindo um registro. Notificação não significa que a pessoa tinha
  dengue de fato — é só o primeiro degrau: alguém com sintomas compatíveis (febre, dor no corpo, entre
  outros) entrou no radar da vigilância em saúde.
- **Caso provável:** categoria usada pelo Plano Municipal de Contingência de Arboviroses da SMS-POA para
  os limiares de estágio epidemiológico (ver Parte 1). Reúne os casos notificados que, mesmo sem exame
  laboratorial concluído, têm quadro clínico e contexto epidemiológico compatíveis com dengue — uma
  categoria intermediária entre "notificado" e "confirmado".
- **Caso confirmado:** o caso notificado que, depois de investigado — por exame laboratorial (sorologia
  ou detecção do vírus) ou por critério clínico-epidemiológico, quando a situação da cidade permite
  dispensar o exame de cada paciente — recebeu uma classificação final que o sistema aceita como dengue de
  fato. No arquivo do SINAN, essa classificação vive na coluna `CLASSI_FIN` ("classificação final"), e o
  projeto usa **três códigos dessa coluna** (10, 11 e 12) para marcar um caso como confirmado — em
  contraste com os códigos que marcam um caso como descartado (não era dengue) ou ainda inconclusivo.

**O alvo do projeto é o caso CONFIRMADO**, não o notificado nem o provável. **FATO (decisão medida em
30/08/2026, registrada em `ESTADO.md` §3.6):** essa escolha foi testada e não é arbitrária — o projeto
mediu qual das três definições o modelo consegue prever melhor, e casos confirmados venceu.

⚠️ Essa escolha tem um custo, medido e documentado: a **confirmação está caindo ao longo dos anos**. A
**taxa de confirmação** de um ano é definida como:

```
taxa_confirmação = casos_confirmados / casos_notificados
```

**FATO (medido em 13/09/2026, ver `modelagem_aedes/acesso/fontes.py` e
`analises/2026-09-13_metrica_de_alarme/README.md` §6):** em Porto Alegre, essa taxa foi de **73,2%** em
2022, **69,3%** em 2023, **60,1%** em 2024 e **38,3%** em 2025. Isso quer dizer que, em 2025, de cada 100
notificações de dengue na cidade, cerca de **38** chegaram a virar um caso confirmado no sistema — não
porque a epidemia tenha sido pequena (2025 teve **21.329** casos confirmados, o maior número da série),
mas porque a política de quem é testado muda quando a epidemia cresce (ver **3.3.3** abaixo e a Parte 1,
onde o Plano Municipal descreve como a testagem encolhe justamente quando mais se precisaria dela), e
porque parte dos casos mais recentes ainda está em apuração no momento da consulta (ver **3.6**, sobre o
corte de maturidade).

### 3.3.2 Município de notificação × município de residência

Cada caso do SINAN carrega **duas** informações de localização diferentes, e escolher qual delas usar
muda o número final:

- **Município de notificação** (coluna `ID_MUNICIP` do SINAN): o município onde fica a unidade de saúde
  que **atendeu e notificou** o caso. É o que o script `consolidar_sinan.py` usa para filtrar "os casos de
  Porto Alegre" — a constante `CODIGO_MUNICIPIO_POA = 431490` (o código de Porto Alegre no cadastro
  nacional de municípios) é comparada contra essa coluna.
- **Município de residência** (coluna `ID_MN_RESI` do SINAN): o município onde o paciente **mora**.

Os dois podem divergir: um morador de uma cidade vizinha pode ser atendido (e notificado) num hospital de
Porto Alegre, e um morador de Porto Alegre pode ser atendido numa cidade vizinha. Também é assim que o
**Estado do Rio Grande do Sul** (na sua própria vigilância) e a **Prefeitura de Porto Alegre** podem
divulgar números diferentes para "os casos de Porto Alegre" sem que nenhum dos dois esteja errado — cada
um está respondendo uma pergunta ligeiramente diferente (uma sobre onde os pacientes foram atendidos,
outra sobre onde eles moram).

**FATO (decisão do autor do projeto em 25/09/2026, registrada em `PENDENCIAS.md`).** O projeto usa
**município de notificação**, para poder comparar seus números diretamente com as séries que a própria
SMS-POA divulga (o Plano Municipal, o portal MI-Aedes) — que também são organizadas por notificação, não
por residência. Município de residência fica registrado como um **cenário alternativo**, ainda não
explorado.

### 3.3.3 A confirmação encolhe quando a epidemia cresce

O Plano Municipal de Contingência de Arboviroses (ver Parte 1) documenta uma regra operacional que ajuda a
explicar a queda na taxa de confirmação: os grupos de pacientes que são **testados** por exame
laboratorial mudam conforme o estágio epidemiológico da cidade.

**FATO (Plano Municipal, Quadro 1, citado em `PENDENCIAS.md`):** nos estágios de menor gravidade
(Normalidade e Mobilização), a rede testa viajantes, pessoas com comorbidades, gestantes, crianças menores
de 5 anos, idosos acima de 60 anos, e outros dois grupos de risco. Já nos estágios mais graves (Alerta e
Epidemia), a testagem se restringe a **só três grupos**: viajantes, gestantes e idosos acima de 60 anos.

Isso significa que **quanto pior a epidemia, menos gente é testada em proporção**, e mais casos
notificados ficam sem confirmação laboratorial — o que é uma decisão de saúde pública deliberada (poupar
recursos de teste quando o quadro clínico já deixa pouca dúvida), mas que tem uma consequência direta para
quem tenta prever "casos confirmados": o próprio alvo que o modelo tenta acertar muda de significado
conforme a epidemia avança.

---

## 3.4 A tabela final: da tabela bruta aos 20 atributos do modelo

### 3.4.1 O que é a tabela final, e o que é cada linha

A **tabela final** (arquivo `modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv`) é o ponto
de encontro das quatro fontes de dados descritas em **3.2**: junta, semana a semana, o mosquito capturado
nas armadilhas, o clima, os casos de dengue confirmados e um indicador climático de larga escala chamado
El Niño – Oscilação Sul (ENSO, ver adiante).

**Cada linha da tabela final é uma semana epidemiológica.** Uma **semana epidemiológica** é a unidade de
tempo padrão usada pela vigilância em saúde brasileira: começa sempre num domingo e termina no sábado
seguinte, e a semana 1 de cada ano é definida como a primeira que tem pelo menos 4 dias dentro daquele
ano — o que equivale a dizer que é a semana que contém a primeira quarta-feira do ano. Essa é uma
convenção, não uma coincidência: ela garante que toda semana do calendário tenha um único número de
semana epidemiológica, sem ambiguidade nas viradas de ano.

**FATO (medido nesta sessão, 26/09/2026, reconferindo o arquivo).** A tabela final tem **725 linhas**
(725 semanas, de 23/09/2012 a 09/08/2026) e **36 colunas** na sua forma bruta — antes de qualquer coluna
derivada (defasagem, média móvel, seno/cosseno) ser calculada. A tabela é uma **grade semanal contínua**:
existe uma linha para **todo** domingo entre a primeira e a última semana com dado disponível, mesmo
quando não houve nenhuma vistoria de armadilha naquela semana. Quando isso acontece, as colunas do vetor
ficam com valor **vazio (NaN — "not a number", a forma padrão de representar "sem informação" numa
tabela)**, nunca com um zero inventado. O mesmo vale para os casos: fora do período coberto pelo SINAN
(antes de 18/02/2018, ou depois da última semana já divulgada), a coluna de casos fica vazia, não zero.

### 3.4.2 As 36 colunas da tabela bruta

As 36 colunas do arquivo, na ordem em que aparecem, são:

| Grupo | Colunas |
|---|---|
| Identificação da semana | `fonte`, `SE`, `data_inicio_semana_epidemi`, `ano`, `semana` |
| Mosquito (vetor) | `numero_de_armadilhas`, `aedes_aegypti`, `aedes_albopictus`, `culex_sp`, `aedes_aegypti_por_armadilha`, `denominador_aproximado` |
| Clima — chuva | `precip_total_mm`, `precip_max_dia_mm`, `precip_media_dia_mm`, `dias_de_chuva` |
| Clima — temperatura | `temp_media`, `temp_min`, `temp_max`, `temp_amplitude_media` |
| Clima — umidade do ar | `orvalho_min`, `orvalho_media`, `orvalho_max`, `umid_min`, `umid_media`, `umid_max` |
| Clima — pressão atmosférica | `pressao_min`, `pressao_media`, `pressao_max` |
| Clima — radiação solar | `radiacao_min`, `radiacao_media`, `radiacao_max` |
| Clima — vento | `vento_media`, `vento_max` |
| Casos de dengue | `casos_confirmados` |
| El Niño – Oscilação Sul | `nino34_anom`, `oni` |

`nino34_anom` e `oni` medem a temperatura anômala do oceano Pacífico tropical (o fenômeno El
Niño/La Niña, que influencia o clima em escala continental, inclusive no Sul do Brasil). Essas duas
colunas **entram na tabela bruta mas não entram no modelo** (ver `colunas_ignorar` na configuração do
experimento) — foram usadas em testes específicos sobre o efeito do clima de larga escala, não fazendo
parte do conjunto de atributos padrão (ver Parte de resultados / dívida técnica sobre ENSO).

### 3.4.3 Os grupos de atributos: núcleo, clima e vetor

O modelo **não usa as 36 colunas brutas diretamente**. Antes de treinar, o projeto calcula colunas
**derivadas** (defasagens, médias móveis, seno/cosseno da época do ano — ver **3.5**) e depois separa
**todas** as colunas candidatas (brutas + derivadas, exceto identificadores e ENSO) em **três grupos**,
pelo nome da coluna:

- **Núcleo:** o histórico da própria série de casos e a marcação da época do ano — a parte que existe
  sempre, mesmo sem clima nem mosquito;
- **Clima:** qualquer coluna cujo nome contenha um dos radicais `temp`, `precip`, `orvalho`, `umid`,
  `pressao`, `radiacao`, `vento` ou `dias_de_chuva`;
- **Vetor:** qualquer coluna cujo nome contenha `aedes`, `armadilha` ou `vetor`.

**FATO (calculado nesta sessão, 26/09/2026, reproduzindo o código real do projeto,
`dominio/selecao_features.py` e `dominio/features.py`, sobre a tabela final vigente):**

- O grupo **núcleo** tem exatamente **8 colunas**: `casos`, `casos_lag1`, `casos_lag2`, `casos_lag3`,
  `casos_lag4`, `casos_mm4` (média móvel de 4 semanas dos casos, ver **3.5**), `sem_sin` e `sem_cos`
  (a marcação circular da época do ano, ver **3.5**).
- O grupo **vetor** tem exatamente **6 colunas**: `aedes_aegypti_por_armadilha` (o índice da semana
  corrente, ver **3.1.2**), suas quatro defasagens (`aedes_aegypti_por_armadilha_lag1` a `_lag4`) e
  `vetor_mm4` (a média móvel de 4 semanas do índice).
- O grupo **clima** tem **42 colunas candidatas**, e a conta é esta:
  - **22 colunas brutas**, isto é, sem defasagem, que são as listadas em **3.4.2**: chuva (4) mais
    temperatura (4) mais umidade (6) mais pressão (3) mais radiação (3) mais vento (2);
  - mais **20 colunas defasadas**, que vêm de **cinco** dessas variáveis (`temp_media`,
    `precip_total_mm`, `orvalho_media`, `umid_media`, `pressao_media`), cada uma com defasagem de 1, 2, 3
    e 4 semanas: 5 × 4 = 20;
  - **22 + 20 = 42**.
  - As outras **17** colunas brutas, entre elas `temp_amplitude_media` e `dias_de_chuva`, entram **apenas
    sem atraso**, e não geram colunas defasadas.

Dessas **42 colunas de clima candidatas**, o **cenário adotado do projeto usa só as 6 que mais ajudaram** a
prever casos num teste específico (ver a seguir) — daí o **8 + 6 + 6 = 20 atributos** que o modelo
efetivamente recebe.

**Como as 6 colunas de clima são escolhidas.** O projeto usa um algoritmo de aprendizado de máquina
chamado **LightGBM** (um algoritmo de **boosting de gradiente** — uma família de métodos que treina muitas
árvores de decisão pequenas em sequência, cada uma corrigindo o erro que sobrou das anteriores) para medir
o **ganho** que cada coluna de clima trouxe para prever os casos, usando só uma fatia inicial dos dados
(60% mais antigos, para o próprio processo de escolha não "espiar" o futuro que o experimento principal
vai tentar prever depois). Isso é feito para três horizontes diferentes (1, 4 e 8 semanas à frente), e o
"ganho" de cada coluna nos três horizontes é somado. As seis colunas com maior ganho somado entram no
modelo; as outras 36 ficam de fora.

⚠️ **DÍVIDA TÉCNICA, registrada em `PENDENCIAS.md`.** Essa escolha de 6 colunas de clima acontece **fora
do walk-forward** (fora do teste que treina no passado e prevê o futuro repetidamente — ver Parte de
método) — ou seja, é feita **uma vez só**, olhando uma fatia fixa dos dados, e não refeita a cada rodada
do teste. Além disso, o próprio ranking de importância **muda dependendo de qual coluna se está tentando
prever** (casos confirmados, casos notificados, ou densidade do vetor): recortando a série em 2023, **4
das 6 colunas mudam** (FATO registrado em `ESTADO.md` §3.7). Isso quer dizer que a frase "estas 6 variáveis
de clima são as que importam" não pode ser tratada como um fato estável do fenômeno — é o resultado de uma
escolha de engenharia, sensível ao recorte de dados e ao alvo escolhido.

**Reproduzindo esse cálculo nesta sessão (26/09/2026), sobre a tabela final vigente, com a mesma
configuração do cenário adotado (corte de maturidade de 12 semanas, seleção pelo LightGBM, horizontes 1/4/8,
60% iniciais dos dados para a escolha)**, as seis colunas de clima escolhidas são:

1. `temp_media_lag4` — temperatura média do ar, com 4 semanas de atraso;
2. `umid_media` — umidade relativa média do ar, na própria semana;
3. `temp_media_lag3` — temperatura média do ar, com 3 semanas de atraso;
4. `temp_max` — temperatura máxima do ar, na própria semana;
5. `pressao_media_lag3` — pressão atmosférica média, com 3 semanas de atraso;
6. `pressao_media_lag4` — pressão atmosférica média, com 4 semanas de atraso.

Isso é consistente com o que se esperaria biologicamente: a temperatura de **3 a 4 semanas atrás** — o
tempo aproximado que o mosquito leva para se desenvolver do ovo ao adulto picador, mais o tempo de
incubação do vírus dentro dele — pesa mais do que a temperatura da própria semana. Ainda assim, por conta
da instabilidade documentada acima, este resultado específico é rotulado como **FATO (medido nesta sessão,
26/09/2026)**, não como uma verdade definitiva sobre quais variáveis de clima "realmente importam".

**A lista completa dos 20 atributos que o cenário adotado recebe, portanto, é:**

| # | Coluna | Grupo | O que é |
|---|---|---|---|
| 1 | `casos` | Núcleo | Casos confirmados na própria semana de origem |
| 2 | `casos_lag1` | Núcleo | Casos confirmados 1 semana antes |
| 3 | `casos_lag2` | Núcleo | Casos confirmados 2 semanas antes |
| 4 | `casos_lag3` | Núcleo | Casos confirmados 3 semanas antes |
| 5 | `casos_lag4` | Núcleo | Casos confirmados 4 semanas antes |
| 6 | `casos_mm4` | Núcleo | Média móvel de 4 semanas dos casos confirmados |
| 7 | `sem_sin` | Núcleo | Seno da posição da semana no ano (sazonalidade) |
| 8 | `sem_cos` | Núcleo | Cosseno da posição da semana no ano (sazonalidade) |
| 9 | `temp_media_lag4` | Clima | Temperatura média do ar, 4 semanas antes |
| 10 | `umid_media` | Clima | Umidade relativa média do ar, na semana |
| 11 | `temp_media_lag3` | Clima | Temperatura média do ar, 3 semanas antes |
| 12 | `temp_max` | Clima | Temperatura máxima do ar, na semana |
| 13 | `pressao_media_lag3` | Clima | Pressão atmosférica média, 3 semanas antes |
| 14 | `pressao_media_lag4` | Clima | Pressão atmosférica média, 4 semanas antes |
| 15 | `aedes_aegypti_por_armadilha` | Vetor | Índice de fêmeas por armadilha, na semana |
| 16 | `aedes_aegypti_por_armadilha_lag1` | Vetor | Índice de fêmeas por armadilha, 1 semana antes |
| 17 | `aedes_aegypti_por_armadilha_lag2` | Vetor | Índice de fêmeas por armadilha, 2 semanas antes |
| 18 | `aedes_aegypti_por_armadilha_lag3` | Vetor | Índice de fêmeas por armadilha, 3 semanas antes |
| 19 | `aedes_aegypti_por_armadilha_lag4` | Vetor | Índice de fêmeas por armadilha, 4 semanas antes |
| 20 | `vetor_mm4` | Vetor | Média móvel de 4 semanas do índice de fêmeas por armadilha |

### 3.4.4 Um exemplo numérico de uma linha real

Para tornar tudo isso concreto, eis uma linha real da tabela final — a semana epidemiológica **11 de
2025** (código **`SE 202511`**, que começa no domingo 09/03/2025), usada como exemplo ao longo desta seção
porque é justamente a semana com **917 casos confirmados** citada no painel de calibração do projeto (ver
Parte de resultados):

| Atributo | Valor nessa semana | De onde vem |
|---|---|---|
| `casos` (o alvo bruto daquela semana) | **917** | SINAN, confirmados, notificação em Porto Alegre |
| `casos_lag4` | **161** | Os casos confirmados de 4 semanas antes, SE 202507 (09/02/2025) |
| `casos_mm4` | (média das 4 semanas anteriores) | Calculado sobre a própria série |
| `sem_sin` / `sem_cos` | 0,971 / 0,239 | `semana = 11`, ver fórmula em **3.5** |
| `aedes_aegypti_por_armadilha` | **1,058153** | Base certificada da Secretaria |
| `temp_max` | **28,93 °C** | NASA POWER |
| `umid_media` | **74,52%** | NASA POWER |

Note que **917 casos confirmados numa única semana** é um número que precisa de tradução concreta: é
quase o dobro dos **161 casos** que a mesma cidade teve **4 semanas antes** — um salto que caracteriza a
fase de aceleração de uma epidemia, e é justamente o tipo de subida que o modelo tenta antecipar usando as
colunas de defasagem (ver **3.5** e a Parte de resultados sobre magnitude de erro em picos).

Para efeito de referência, a **semana de maior número de casos confirmados em toda a série** é a
seguinte: `SE 202514` (30/03/2025), com **2.381 casos confirmados** — três semanas depois da linha usada
como exemplo acima, mostrando como a subida continuou.

---

## 3.5 Defasagens (*lags*)

Uma **coluna defasada** (em inglês, *lag*, termo usado no código do projeto e mantido aqui por ser como
ele aparece nos nomes de coluna) é simplesmente **o valor de uma variável em uma semana passada, colocado
lado a lado com a semana atual**, para que o modelo possa "ver" o passado recente como se fosse mais uma
informação disponível na hora de prever.

**A fórmula, em palavras:** a coluna `X_lagN` de uma semana `t` guarda o valor de `X` na semana `t − N`.

```
X_lagN(t) = X(t − N semanas)
```

Onde:

- **X** — a variável original (por exemplo, `casos`, ou `aedes_aegypti_por_armadilha`);
- **N** — quantas semanas de atraso (o projeto usa **N = 1, 2, 3 e 4**);
- **t** — a semana de referência (a semana de "hoje", na qual o modelo está fazendo a previsão).

**Exemplo numérico, usando a linha da seção 3.4.4:** a semana de referência é `SE 202511`
(09/03/2025, com **917** casos confirmados). A coluna `casos_lag4` dessa linha deve guardar o número de
casos confirmados de **4 semanas antes**, ou seja, a semana `SE 202507` (09/02/2025). Olhando diretamente
a tabela final, `SE 202507` teve **161 casos confirmados** — e é exatamente esse o valor que aparece em
`casos_lag4` na linha de `SE 202511`. Confirma-se, com um exemplo real, que:

```
casos_lag4(09/03/2025) = casos(09/02/2025) = 161
```

**Por que a janela vai só de 1 a 4 semanas.** A escolha não é arbitrária: ela equilibra dois efeitos
opostos. Defasagens curtas (1 a 4 semanas) capturam o que há de mais recente e relevante no
**momentum** da epidemia — se os casos estão subindo ou descendo agora. Defasagens muito mais longas
esbarram em dois problemas medidos pelo próprio projeto (ver Parte de resultados, §3.1 de `ESTADO.md`):
primeiro, a força da relação entre "casos de uma semana" e "casos de semanas passadas" (a
**autocorrelação** — o quanto uma série se parece com ela mesma deslocada no tempo) já cai para
praticamente **zero em 12 semanas**; segundo, defasagens de 5 a 12 semanas e de 52/104 semanas (um ano ou
dois anos atrás) foram testadas e **não reduziram o erro** de previsão (23 e 24/09/2026). A janela de 1 a
4 semanas é, portanto, a que sobreviveu ao teste, não a única jamais cogitada.

⚠️ Uma coluna defasada **herda os vazios (NaN)** da coluna original: se a semana `t − N` não tinha
informação (por exemplo, por causa do corte de maturidade, ver **3.6**, ou de uma semana sem vistoria de
armadilha), a coluna defasada correspondente também fica vazia naquela linha. O código do projeto não
inventa nenhum valor para preencher esse vazio — ele se propaga naturalmente pelo cálculo (usando a função
`shift` da biblioteca de manipulação de tabelas `pandas`, que desloca uma coluna no tempo preservando os
vazios).

**A marcação de sazonalidade (`sem_sin` e `sem_cos`).** Embora não seja tecnicamente uma defasagem, essas
duas colunas do grupo núcleo (ver **3.4.3**) usam um mecanismo relacionado — transformar um número que se
repete em ciclo (a semana do ano, de 1 a 52) em algo que o modelo consegue interpretar sem ser enganado
pela quebra de ano. A fórmula é:

```
sem_sin = sen(2π × semana / 52)
sem_cos = cos(2π × semana / 52)
```

Onde **semana** é o número da semana epidemiológica dentro do ano (de 1 a 52), e **sen** e **cos** são as
funções trigonométricas seno e cosseno. A razão de usar as duas juntas, em vez de só o número da semana
puro: se o modelo recebesse diretamente "semana = 52" e "semana = 1" como dois números, ele os veria como
**distantes** (52 e 1 são numericamente afastados), quando na verdade são **semanas vizinhas** no
calendário (a última semana de um ano e a primeira do ano seguinte). Codificando a semana como um ponto
num círculo (usando seno e cosseno), a semana 52 e a semana 1 ficam **próximas** no espaço que o modelo
enxerga, exatamente como estão próximas no calendário.

**Exemplo numérico:** para a semana de referência do exemplo (`semana = 11`, dentro de `SE 202511`):

```
ângulo = 2π × 11 / 52 ≈ 1,329 radianos
sem_sin = sen(1,329) ≈ 0,971
sem_cos = cos(1,329) ≈ 0,239
```

Esses são exatamente os valores usados na tabela da seção 3.4.4.

---

## 3.6 O corte de maturidade de 12 semanas

### 3.6.1 O que é, e por que existe

Um caso de dengue não entra "pronto" no SINAN no momento em que a pessoa fica doente. Existe um atraso
entre a semana em que os sintomas começaram (o que o projeto usa para contar "quando" o caso aconteceu,
ver **3.2.1**, coluna `SEM_PRI`) e o momento em que esse caso é **investigado, classificado e confirmado**
no sistema — o que pode levar dias a semanas.

Isso cria um efeito enganoso: se alguém olhar a contagem de casos confirmados nas **últimas semanas**
antes de hoje, ela vai parecer **artificialmente baixa** — não porque a epidemia tenha diminuído, mas
porque boa parte dos casos daquelas semanas ainda **não terminou de ser confirmada**. Um modelo que
treinasse ingenuamente sobre esses números baixos, tratando-os como definitivos, aprenderia um padrão
errado (uma "queda" que não existe de verdade).

O **corte de maturidade** resolve isso: em vez de deixar os casos das últimas semanas com um número baixo
e enganoso, o projeto os marca como **"sem informação" (NaN)**, exatamente como se aquelas semanas nunca
tivessem sido divulgadas.

**A fórmula (implementada em `modelagem_aedes/dominio/surto.py`, função `aplicar_corte_maturidade`):**

```
casos_corrigidos(t) = casos(t)     se  t ≤ (t_máx − 12 semanas)
casos_corrigidos(t) = NaN          se  t > (t_máx − 12 semanas)
```

Onde:

- **t** — a data de início de uma semana qualquer da tabela;
- **t_máx** — a data da **última semana que tem um número de casos divulgado** (não a última linha da
  tabela — ver a ressalva abaixo);
- **12** — o número de semanas de corte, o parâmetro `semanas_corte_maturidade` da configuração do
  experimento.

**Exemplo numérico, com datas reais do projeto.** A última semana com casos confirmados divulgados na
tabela final vigente é **26/04/2026** (`t_máx`). Descontando 12 semanas:

```
t_máx − 12 semanas = 26/04/2026 − 84 dias = 01/02/2026
```

Ou seja: **toda semana depois de 01/02/2026 tem seus casos apagados (viram NaN)** para efeito de
treinamento e avaliação do modelo, mesmo que a tabela mostre um número (baixo, ainda em apuração) para
elas. Esse mesmo corte é a razão pela qual o painel de avaliação do cenário adotado (ver Parte de
resultados) descreve seu período como indo "até **~01/02/2026**" — a data não foi escolhida à mão: ela
**é** o resultado direto de aplicar a fórmula do corte de maturidade sobre a última semana disponível
quando a tabela foi gerada.

### 3.6.2 O que foi medido sobre o atraso real de confirmação

O valor "12 semanas" não é um chute: ele se baseia numa medição direta de quanto tempo os casos de 2025
efetivamente levaram entre o início dos sintomas e a confirmação no sistema.

**FATO (medido em 2025, registrado em `PENDENCIAS.md`):** a **mediana** desse atraso foi de **10,4
semanas**; o **percentil 75** (75% dos casos já confirmados até esse prazo) foi de **22,7 semanas**; o
**percentil 90** (90% dos casos já confirmados) foi de **31,6 semanas**.

Isso expõe uma tensão que o projeto reconhece explicitamente: o corte de **12 semanas** cobre a
**mediana** do atraso (metade dos casos já está confirmada nesse prazo) mas está **longe** de cobrir o
percentil 90 — quase **20 semanas** abaixo dele. Um corte de 12 semanas é, portanto, um meio-termo
deliberado: cortar mais (por exemplo, 32 semanas, cobrindo o percentil 90) preservaria mais confiabilidade
nos casos mantidos, mas descartaria quase **8 meses** de dados recentes a cada rodada — dados demais para
abrir mão, considerando que a epidemia mais recente é justamente a mais relevante para prever a próxima.

### 3.6.3 A limitação: o corte age uma vez só, no fim da série

**LIMITAÇÃO DE ARQUITETURA.** Olhando a fórmula da seção 3.6.1 com atenção: ela sempre ancora o corte na
**última semana com caso divulgado da tabela inteira** (`t_máx`), não na data em que uma previsão
específica está sendo feita dentro de um teste que simula o passado (o **walk-forward**, ver Parte de
método). Ou seja, o corte de maturidade **não simula**, para uma previsão feita em março de 2022, por
exemplo, "quais semanas de 2022 ainda estariam imaturas naquele momento" — ele sempre corta em relação ao
presente da tabela como um todo. Isso é adequado para gerar a tabela final que alimenta o modelo de
produção (que sempre prevê a partir de "agora"), mas significa que qualquer teste que **recrie o passado**
com a fórmula de corte de maturidade recebe uma versão "mais madura" das semanas antigas do que um
observador realmente teria visto naquela época — uma simplificação assumida, não escondida.

---

## 3.7 O período de treino e o período de avaliação

**Início do treino: 18/02/2018.** Essa data não é um filtro de calendário escolhido à mão — ela é uma
**consequência** de outra regra: o modelo só pode treinar em linhas que tenham um valor de casos
conhecido (sem isso, não há o que aprender). Como a série de casos confirmados só começa em **18/02/2018**
(ver **3.2.1**), toda linha anterior a essa data tem a coluna `casos` vazia (NaN) e é **removida** antes
do treino pelo próprio processo de descarte de linhas incompletas (`dropna`, "descartar não-disponível").
O efeito prático é o mesmo de um filtro por data, mas a causa é a remoção de linhas sem alvo, não uma
decisão de recorte temporal em si.

**Início da avaliação: 01/01/2024.** Esse é o corte que separa o período usado para **calibrar** decisões
de desenho do projeto (por exemplo, escolher quais colunas de clima entram — ver **3.4.3** — ou qual
algoritmo e função de perda usar) do período reservado para **julgar** o resultado final, sem que esse
julgamento tenha influenciado nenhuma escolha (ver Parte de método, sobre pré-declaração e o cuidado de
nunca deixar a avaliação "vazar" para dentro das decisões de desenho).

**Fim da avaliação: ~01/02/2026** — o mesmo limite que resulta do corte de maturidade de 12 semanas
aplicado à última semana com caso divulgado (ver **3.6.1**).

---

## 3.8 Por que 2026 foi excluído da avaliação

**FATO (decisão do autor do projeto em 26/09/2026, registrada em `PENDENCIAS.md` e `ESTADO.md` §3.2).** O
ano de **2026** foi **retirado** da tabela de avaliação oficial do projeto. A tabela oficial hoje vai só
até a semana epidemiológica 17 de 2026 (a última divulgada dentro do corte de maturidade), e qualquer
rodada que tenha incluído 2026 além desse ponto fica registrada só como material exploratório, guardado
à parte (pasta `atualizacao_dados_2026/`).

**O argumento é estatístico, não uma opinião:** **FATO (medido)**, o Plano Municipal registra
**19 casos confirmados** de dengue em Porto Alegre no início de 2026 divulgados até a data de corte —
um número extremamente baixo comparado aos **21.329** de 2025 e aos **17.686** de 2024. Um modelo cujo
histórico de treino é dominado por anos de epidemia crescente (2022 a 2025) não tem como "aprender", só
com dados, que um ano seguinte pode ser **calmo**: toda a tendência que ele viu até aqui aponta para cima.
Tentar avaliar a qualidade do modelo contra um ano de 19 casos, nessas condições, mediria principalmente o
quanto o modelo **não conseguiu prever uma coisa que a própria série histórica não dava pistas de que
aconteceria** — o que é diferente de medir se o modelo funciona bem no que ele foi desenhado para prever
(anos dentro do padrão observado até então).

⚠️ Isso não significa que 2026 seja irrelevante para sempre. **HIPÓTESE (levantada, não pré-declarada
como método permanente):** um protocolo específico para julgar anos calmos — com um critério de sucesso
diferente do erro absoluto usado para anos de epidemia — está em discussão (ver `PENDENCIAS.md`,
"Protocolo para testar a metodologia temporada a temporada"), mas ainda não foi formalizado nem aplicado.

---

## 3.9 Limitações conhecidas dos dados

Esta seção reúne, num só lugar, as fragilidades dos dados já mencionadas ao longo do texto, mais outras
que não caberiam nas seções anteriores sem interromper a explicação principal. Cada uma é uma
**limitação de arquitetura ou de dado disponível**, não uma falha de execução do projeto.

- **A seleção das 6 colunas de clima acontece fora do teste que simula o passado (o walk-forward), e o
  próprio ranking de importância é instável** — muda conforme o alvo escolhido e o recorte temporal (ver
  **3.4.3**). Isso significa que "estas são as variáveis de clima que importam" é uma afirmação sobre uma
  escolha de engenharia feita uma vez, não uma lei estável do fenômeno.

- **A raspagem do portal MI-Aedes é manual, sem automação.** Sem um mecanismo de agendamento automático
  (ver **3.2.2**), uma semana que passe sem ser raspada em 2026 em diante — quando a Secretaria ainda não
  publicou o ano corrente — é uma semana **permanentemente perdida**, porque o portal só expõe a semana
  corrente.

- **O portal MI-Aedes só expõe a semana corrente.** Não existe, nesse portal, uma forma de recuperar o
  histórico depois que uma semana "passa" — o que torna toda a captura de mosquito de 2026 em diante
  **insubstituível** assim que é coletada (ver invariantes do projeto em `CLAUDE.md`).

- **Não há sorotipo circulante entre os atributos do modelo.** O SINAN registra, por caso, uma coluna de
  sorotipo (`SOROTIPO`), mas essa informação **não entra** como atributo do modelo hoje. Como diferentes
  sorotipos encontram populações com diferentes níveis de imunidade prévia (ver Parte 1, sobre os quatro
  sorotipos da dengue), a ausência dessa informação é uma lacuna conceitual: o modelo não "sabe" se uma
  epidemia está sendo impulsionada por um sorotipo novo circulando numa população sem imunidade a ele.

- **Não há imunidade populacional entre os atributos do modelo.** Não existe, nos dados disponíveis ao
  projeto, uma estimativa de que fração da população de Porto Alegre já teve dengue (e portanto tem
  alguma imunidade). Esse é um fator conhecido na literatura de dengue como influente na dinâmica de
  epidemias futuras, e o projeto não tem como medi-lo com os dados que possui.

- **Não há mobilidade entre os atributos do modelo.** Deslocamento de pessoas dentro da cidade ou entre
  cidades vizinhas — relevante porque o mosquito tem baixo alcance de voo próprio, mas o vírus se espalha
  pelo deslocamento de pessoas infectadas — não está representado em nenhuma coluna do modelo.

- **A taxa de confirmação de casos caiu ao longo dos anos** (73,2% em 2022 para 38,3% em 2025, ver
  **3.3.1**), o que significa que o alvo do modelo (casos confirmados) está sendo medido com um "filtro"
  cada vez mais seletivo — uma mudança na própria definição operacional do número que se está tentando
  prever, não uma mudança na doença em si.

- **O corte de maturidade age uma vez só, ancorado no fim da tabela inteira** (ver **3.6.3**), e não
  simula o grau de maturidade que uma previsão feita no passado realmente teria enxergado naquele momento.

- **2,2% das linhas da base de armadilhas não têm coordenada geográfica registrada** (FATO, `ESTADO.md`
  §1), o que limita análises que dependam de localização exata (por exemplo, a associação de uma
  armadilha a um endereço específico).

- **O identificador de inspeção (`id_inspecao`) não é único** nos anos de 2012 a 2019 e em 2021, e a
  coluna de data do banco de dados (`data_banco`) tem cerca de 18% de valores invertidos nesses mesmos
  anos — duas fragilidades que impedem, por exemplo, deduplicar registros por identificador ou usar essa
  coluna de data para qualquer análise temporal fina nesses anos (FATO, `ESTADO.md` §1).

Estas limitações não invalidam os dados — cada uma delas foi medida, documentada e, sempre que possível,
contornada por uma decisão explícita de desenho (o corte de maturidade, a escolha de município de
notificação, o uso exclusivo do parquet certificado). Elas definem, isso sim, os limites do que pode ser
afirmado a partir destes dados — e é isso que as próximas partes deste documento levam em conta ao
descrever os modelos e os resultados.
