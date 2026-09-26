# Resumo — Plano Municipal de Contingência de Arboviroses 2026 (SMS Porto Alegre)

> Fonte: `Artigos de referencia/2026_Plano_Municipal_de_Contingencia_Arboviroses.docx_0.pdf` (45 páginas,
> dez/2025, PDF não modificado). Extração via `pdftotext -layout` + render de páginas com tabela/figura
> (`pdftoppm`) onde o texto saiu ilegível. Paginação citada = numeração impressa no rodapé do documento
> (a partir de "1. Apresentação"), não a página física do PDF.
>
> Rótulo em cada item: **[FATO]** = o documento diz isso, com citação; **[INFERÊNCIA]** = leitura minha,
> não está escrito assim no texto.

---

## 1. Critério de confirmação de caso

- **[FATO]** O plano **não contém uma seção de "definição de caso"** com os termos
  "laboratorial" × "clínico-epidemiológico" × "inconclusivo". Busquei literalmente a palavra
  **"inconclusivo"** no texto extraído das 45 páginas: **zero ocorrências**. Isso é um achado
  relevante para o projeto — o plano municipal não formaliza essa categoria, que deve vir de norma
  estadual/federal (SINAN) não reproduzida aqui.

- **[FATO] Critério clínico de suspeita** (p.9): *"febre aferida ou referida, e duas ou mais das
  seguintes manifestações: náusea, vômitos; exantema; mialgia, artralgia; cefaleia, dor
  retro-orbital; petéquias; prova do laço positiva e leucopenia"*. Também é caso suspeito toda
  criança com "quadro febril agudo, usualmente entre dois e sete dias de duração, e sem foco de
  infecção aparente" (p.9).

- **[FATO] Exames e janelas de uso** (p.10, Anexo E p.32-33), por dia de início da febre:
  - NS1 dengue: até o **5º dia**.
  - RT-PCR: dengue e zika até o **5º dia**; chikungunya até o **8º dia**.
  - Sorologia IgM: dengue e zika do **6º ao 30º dia**; chikungunya do **9º ao 30º dia**
    (Anexo E usa "7º ao 30º", ver observação abaixo).

- **[FATO] Regra de confirmação usada no Anexo E** (repetida nos 4 estágios, p.32-33):
  **"SE NS1 POSITIVO → Dengue confirmada"**. **"SE NS1 NEGATIVO → Não descartar Dengue, seguir
  manejo clínico"**. Não há um terceiro ramo escrito para "inconclusivo" — um NS1 negativo não
  confirma nem descarta, o caso permanece em acompanhamento clínico.
  - ⚠️ **[FATO] Divergência interna do próprio documento**: o corpo do texto (p.10) diz IgM "do 6º
    ao 30° dia", mas o Anexo E (p.32) diz **"IgM (do 7° ao 30° dia)"** para todos os 4 estágios.
    Não é erro meu de leitura — os dois números aparecem literalmente em lugares diferentes do
    mesmo PDF.

- **[FATO] Quando cada critério "vale" mais** (Anexo E, p.32-33): a lista de grupos testados
  **encolhe conforme o estágio avança**. Em Normalidade/Mobilização: viajantes, comorbidades,
  gestantes, <5 anos, >60 anos, Grupo B, Grupo C. Em Alerta/Epidemia: **só viajantes, gestantes e
  >60 anos**. Isso é evidência direta de **redução de captação de exame** justamente quando o
  volume de casos é maior — em epidemia, a maioria dos casos é confirmada só pelo NS1 de quem
  ainda cabe nesses 3 grupos, e o restante segue clínico sem confirmação laboratorial sistemática.
  **[INFERÊNCIA]**: essa é provavelmente uma explicação estrutural (não hipótese do documento) para
  a taxa de confirmação baixa em cenário de epidemia — quanto mais alto o estágio, menos gente é
  testada.

- **[FATO] Vigilância de sorotipo** (independente da confirmação clínica, p.11): amostras de
  gestantes e viajantes sempre vão ao Lacen, mais **"10 amostras semanais aleatórias"** entre
  NS1-reagentes e outras 10 entre NS1-não-reagentes (Anexo E confirma esse desenho nos 2 primeiros
  estágios; cai fora do texto do Anexo E nos estágios Alerta/Epidemia, que só menciona "10 amostras
  por semana de adultos com 60 anos ou mais" — leitura de tabela, não frase explícita separada).

---

## 2. Estágios operacionais e limiares (Quadro 1, p.14-15)

- **[FATO] 4 estágios**: Normalidade → Mobilização → Alerta → Epidemia (p.13), seguindo o Plano de
  Contingência Nacional do Ministério da Saúde (BRASIL, 2025).

- **[FATO] Os números 10 / 30 / 50 EXISTEM e são de taxa de incidência de casos CONFIRMADOS**,
  citação literal do Quadro 1 (p.15):
  - Normalidade: *"Taxa de incidência de casos confirmados, em todas as últimas 4SE, abaixo do
    Limite Alerta (LA)... OU... abaixo de 10,00 em todas as últimas 4SE"*.
  - Alerta: *"...taxa de incidência de casos confirmados acima de 30,0 e até 50, em pelo menos 1
    das 4SE"* / *"...acima de 30,0 em uma das últimas 4SE"*.
  - Epidemia: *"...taxa de incidência de casos confirmados acima de 50,0 em pelo menos uma das
    4SE"*.
  - Mobilização usa **casos prováveis** (não confirmados) acima de 10,00 como um dos gatilhos
    alternativos — mistura os dois tipos de caso na mesma régua.

- ⚠️ **[FATO] A unidade population-base NÃO é declarada no texto.** Busquei "100 mil", "100.000",
  "habitantes" no documento inteiro: **nenhuma ocorrência associada aos números 10/30/50**. O plano
  não escreve "por 100 mil habitantes" nem diz qual população usa (residente? Distrito Sanitário?
  cidade toda?). **[INFERÊNCIA]**: por convenção nacional (LIRAa/SINAN, PCN do MS citado como fonte,
  BRASIL 2025), esses limiares costumam ser taxa de incidência **por 100 mil habitantes por semana
  epidemiológica**, mas isso **não está escrito neste PDF** — é lacuna documental, não confirmação.

- **[FATO] Definições de LA e LSE, citação literal (rodapé do Quadro 1, p.15)**:
  - *"SE (Semana Epidemiológica): semana epidemiológica do início dos primeiros sintomas."*
  - *"LSE (Limite Superior Endêmico): média móvel da incidência de casos prováveis somada a dois
    desvios padrões para todas as semanas epidemiológicas (taxa de incidências no RS)."* — note que
    o LSE é calculado sobre **casos prováveis**, com base estadual ("no RS"), não municipal.
  - *"LA (Limite de Alerta): curva de incidência de casos prováveis 45% abaixo do LSE."*

- **[FATO] Gatilhos adicionais fora de taxa de incidência** (estágio Alerta, p.15): *"Detecção da
  introdução/reintrodução de novo sorotipo no período sazonal atual"* OU *"Um óbito confirmado por
  dengue nas últimas 4SE e/ou óbito(s) em investigação"*. Epidemia: *"Mais de 1 óbito(s) confirmado
  por dengue nas últimas 4SE"*.

- **[FATO]** Além do Quadro 1, *"poderão ser utilizados indicadores assistenciais para definição de
  mudança de estágio operacional, conforme análise de cenário da Secretaria Municipal de Saúde"*
  (p.14) — ou seja, a régua numérica não é a única porta de entrada; há margem de decisão da SMS.

---

## 3. Vetor e armadilhas

- **[FATO] MI-Aedes / Mosquitrap** (p.6-7): em uso há **13 anos** na cidade, instaladas em **46
  bairros**. Captura fêmeas adultas e identifica sorotipos de Dengue (1-4), Zika e Chikungunya em
  todos os mosquitos capturados. Indicadores gerados: **IMFA**, **IPM** (Índice de Positividade da
  Mosquitrap) e **IMFAP** (IMFA Ponderado).

- **[FATO] Novidade 2026 — ovitrampas** (p.6): entram em uso em 2026, escalonadas em **9 bairros**,
  distância de **~300 metros** entre si, coleta **semanal ou quinzenal**. Junto com o Mosquitrap,
  ampliam a cobertura de monitoramento para **73% da população** (p.7).

- **[FATO] Fórmulas dos índices (Anexo A, p.27-28)**:
  - IMFA = nº de fêmeas coletadas / nº de armadilhas vistoriadas.
  - IPM = nº de armadilhas positivas / nº total de armadilhas vistoriadas na semana.
  - IMFAP = média ponderada do IMFA de 4 semanas, com peso maior na semana mais recente.

- **[FATO] Limiares entomológicos oficiais, citação literal (Anexo A, p.27-28)**:
  - **IMFA**: Satisfatório 0 a <0,15 (verde) · Moderado >0,15 a <0,30 (amarelo) · Alerta >0,30 a
    <0,6 (laranja) · Crítico >0,6 (vermelho).
  - **IMFAP**: Mínimo 0,00 (verde) · Baixo 0,01-0,49 (amarelo) · Médio 0,50-0,99 (laranja) · Alto
    ≥1,00 (vermelho).
  - Essas cores são exatamente as faixas de fundo (verde/amarelo/laranja/vermelho) da Figura 1 —
    confirma que a figura usa a escala do IMFA, não uma escala de casos.

- **[FATO] Como a Prefeitura usa esses dados para agir (Anexo A, p.28)**: a decisão de aplicar
  UBV ("fumacê") depende do IMFA médio do município:
  - Se IMFA médio em **Alerta ou Crítico**: UBV em todos os imóveis num raio de **150 m** do local
    provável de infecção, **mesmo sem exigir contagem mínima de mosquitos**.
  - Se IMFA médio em **Satisfatório ou Moderado**: só aplica UBV se alguma armadilha no raio de
    150 m capturar **mais de 1 mosquito** (sinalização laranja ou vermelha).
  - Ou seja, existe um **limiar entomológico operacional explícito e binário** (IMFA municipal
    alerta/crítico vs. satisfatório/moderado) que muda a regra de decisão do bloqueio quimico —
    dado direto e utilizável para modelagem de política, não só de vigilância.

- **[FATO] EDL (Estações Disseminadoras de Larvicida)** — novidade de controle químico 2026 (p.7-8,
  Anexo A p.28): implantação inicial em 4 bairros (Passo das Pedras, Bom Jesus, Vila João Pessoa,
  Vila São José); distância entre estações de **5 a 10 imóveis (até 100 m)**; formato "espinha de
  peixe" ao longo de vias principais.

- **[FATO] Priorização de bloqueio químico** (p.8, critério em ordem): 1º área com maior
  concentração de casos; 2º área com início mais recente de transmissão; 3º área com maior
  vulnerabilidade social.

---

## 4. Sorotipos circulantes e leitura sobre 2025/2026

- **[FATO]** Sorotipo predominante histórico: **DENV1**. **[FATO]** DENV2 circula **desde 2023**.
  **[FATO]** Em 2025, **2 casos importados de DENV3** identificados (p.4-5).
  **[FATO]** *"circulação de mais de um sorotipo do vírus na cidade"* confirmada nos últimos anos
  (p.3).

- **[FATO] O documento NÃO discute explicitamente por que os casos caíram em 2026** nem fala de
  imunidade de rebanho ou reintrodução — o PDF é de **dezembro/2025** e a "Análise Situacional"
  (seção 3) só cobre dados **até SE 46/2025**. Não há projeção nem explicação para 2026. Isso é uma
  lacuna relevante para o projeto: **o plano não sustenta nem contesta a hipótese de subnotificação
  em 2026** citada no contexto da tarefa — simplesmente não fala do ano.

- **[FATO]** Circulação de múltiplos sorotipos é tratada como fator de risco, não de proteção:
  *"A circulação de diferentes subtipos virais aumenta a vulnerabilidade a ocorrências de epidemias
  e predispõe a população a maior risco de formas graves e consequente aumento da letalidade"*
  (p.4-5).

- **[FATO]** Chikungunya: **3 casos importados em 2025** (dado de 20/11/2025, sujeito a revisão,
  p.5). Zika: **nenhum caso desde o surto de 2016** (28 casos, 14 autóctones, p.5).

---

## 5. Séries e números históricos

- **[FATO] Casos confirmados de dengue por ano** (corpo do texto, p.3, e Tabela 1, p.4 — os dois
  batem): **2022 = 5.144** (texto arredonda "5,1 mil") · **2023 = 6.461** ("6,4 mil") ·
  **2024 = 17.686** ("17 mil") · **2025 = 21.329**, parcial ("mais de 22 mil").

- **[FATO] Óbitos por dengue por ano** (Tabela 1, p.4): **2022 = 4** · **2023 = 3** ·
  **2024 = 11** · **2025 = 24** (texto do corpo diz *"recorde de 25 mortes em 2025"* — 1 óbito de
  diferença entre corpo do texto e a Tabela 1; ambos são **dados parciais**, nota de rodapé da
  tabela).

- **[FATO] Tabela 1 completa por Distrito Sanitário de residência** (p.4, confirmados/óbitos,
  2022→2025): destaques — **Eixo Baltazar** salta de 162 casos (2022) para **4.587** (2025, 8
  óbitos); **Leste** é o maior distrito em quase todos os anos (2167→2807); **Noroeste** cresce
  forte (271→2.659); **Não identificado** chega a 1.232 casos em 2023 (maior valor da coluna
  "óbitos=0" daquele ano, mas mostra problema de geocodificação/endereço em parte da base).

- **[FATO] Série histórica pré-2022** (p.4-5): *"Na década de 2010... a 2020, o maior número de
  casos foi registrado em 2019, quando 1,2 mil pessoas foram diagnosticadas... Havia apenas um
  subtipo viral em circulação, sem registro de óbitos."* E: *"em 15 anos de registros de casos
  autóctones... pouco mais de 50 mil casos da doença foram confirmados"* (isto é, 15 anos somam
  menos que só 2024+2025 quase somam sozinhos: 17.686+21.329 ≈ 39 mil).

- **[FATO] Fonte oficial dos números**: "BI das arboviroses" / "BI Arboviroses SMS POA" e Sistema
  MI Aedes/NVRV/DVS/SMS. Tabela 1: *"Dados sujeitos à revisão, atualizados em 20/11/2025"*.
  Figura 1: *"Acesso em: 25/11/2025"*.

---

## 6. Outras informações úteis para a modelagem

- **[FATO] Fluxo de notificação e sistemas** (p.9-10): notificação **compulsória** a partir da
  **suspeita clínica**, "preferencialmente durante o atendimento". Sistema oficial: **Sentinela**
  (`sentinela.procempa.com.br`) — online ou por telefone (EVDT, plantão 24h) para casos que exigem
  contato direto (viagem para área de outro sorotipo, outras arboviroses, óbitos). Exames vão para
  o **GAL** (`gal.saude.rs.gov.br`), sistema estadual — ou seja, há **dois sistemas distintos**
  (Sentinela para notificação clínica, GAL para laboratório), que precisam ser cruzados/pareados.

- **[FATO] Atraso estrutural embutido no desenho do plano**: casos com sinais de alarme devem ser
  notificados no Sentinela **mesmo se já notificados em outro local** — sugere retrabalho e
  potencial duplicidade/atraso na consolidação, mas o plano não quantifica esse atraso em nenhum
  lugar do texto.

- **[FATO] Distritos/bairros prioritários**: não há uma lista fixa de "bairros prioritários" —
  a priorização é **dinâmica**, por indicador (IMFA por bairro monitorado, concentração de casos,
  vulnerabilidade social — critérios de bloqueio químico da seção 3 acima). A Tabela 1 é o recorte
  fixo mais próximo de um ranking territorial.

- **[FATO] Critérios de encerramento**: o documento **não usa esse termo**. O mais próximo é o
  conceito de reclassificação contínua do Fluxograma de Manejo Clínico (Anexo B): paciente migra
  entre Grupos A/B/C/D conforme reavaliação, com **Cartão de Acompanhamento** (Anexo C) obrigatório
  desde a primeira consulta.

- **[FATO] Vacina da dengue**: mencionada apenas como ação de gestão (*"monitorar os dados e
  elaborar estratégias de aumento da cobertura vacinal... dos públicos-alvo definidos pelo
  Ministério da Saúde"*, p.17) — não há dado de cobertura vacinal no documento, e ela **não entra**
  em nenhum critério numérico de estágio operacional (Quadro 1).

- **[FATO] Referência ao Morés et al. (2020)** usada pelo próprio plano (p.8) para justificar que
  o controle mecânico é mais eficaz "entre o outono e o inverno" em Porto Alegre — relevante como
  possível variável sazonal a comparar com a pré-declaração de janela de maturidade do projeto.

---

## Notas de extração

- Tabela 1 (p.4) e Figura 1 (p.3) saíram como imagem no `pdftotext` (células/gráfico em branco);
  foram lidas via render de página (`pdftoppm -r 150`) e leitura visual — números conferidos e
  batem com o resumo do corpo do texto.
- Figura 2 (incidência por bairro, p.5) não foi extraída em detalhe numérico — é mapa coroplético
  sem tabela de valores associada no texto; não essencial para os 6 pontos pedidos.
- PDF não foi alterado (somente leitura).
