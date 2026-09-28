# PENDENCIAS — fila viva do projeto

> Leitura de 3 minutos. `@importado` em toda sessão: **tamanho é custo**, teto de ~100 linhas, item de 1 a
> 2 linhas. Retrato do sistema: [ESTADO.md](ESTADO.md) · Testes: [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md)
> · Eixo fino: `git log`. Status: ✅ resolvido · ⏳ em aberto · 🚫 descartado (com data e quem decidiu).
> **Regra de 29/08/2026:** não existe "aguarda o orientador". Método é decisão nossa, pré-declarada.

---

## 🔴 SEMINÁRIO DE ANDAMENTO — prazo curto (reunião de 21/09/2026)

- ⏳ **Título, resumo, palavras-chave e enquadramento** no sistema do PPGC. Banca provável: Mariana e Anderson.
- ⏳ **Slides de até 10 min**, último de direcionamentos. **Só dengue.** Não dizer "não teve correlação com mosquito".
- ⏳ Orientador mandar o link a Mariana e Mansilha · Vinicius mandar `brutos_secretarias_limpos/`.
- ✅ **PUBLICADO em 28/09/2026: `6c6b1a2`.** As **10 páginas** foram ao ar (eram 6) — o menu do deck linka para
  todas, e publicar um subconjunto daria 404 dentro do site. A **cópia 2** é a apresentação atual, 21 slides.
  ⚠️ **A banca agora VÊ a régua sazonal e 2026** — o marco de 25/09 (pós-montagem só local) foi revogado aqui.
  ⚠️ Os alarmes falsos subiram **como estavam, 2,3/ano**: decisão do Vinicius em 28/09, por o número já estar
  no ar desde 23/09. Ver Dívida técnica — o correto é ~3,57/ano.
- 🧭 Marcos antigos (Vinicius, 25/09): pré-montagem = `710b411`, o que a banca via até 27/09.
- 📩 **Mansilha, 24/09:** sem tom de "IA marqueteira", sem dupla negação, sem depor contra quem cedeu os dados.
- **Depois do seminário a pesquisa CONGELA**; foco no artigo (`../artigo_oficial/`, fora do git).

---

## ⏳ Destrava com o VINICIUS

- **Eixo da tese.** Candidatos em [ESTADO.md](ESTADO.md) §4.
- ✅ **da Silva et al. 2026 lido** (26/09): é **preprint medRxiv**, não PLOS NTD, e **não é revisado por pares**.
  Mesma cidade e armadilha, mas alvo, validação e horizonte são outros — não comparável direto.
  `analises/2026-09-26_ficha_da_silva_2026/`
- 🔴 **Métrica primária: MAE × perda quantílica/WIS.** Pelo MAE, a régua vence em 3 meses (2024-25); pelo WIS, o modelo
  vence a régua dos sprints em 1 mês (a refazer na tabela oficial). Definição de produto: quanto custa subestimar surto?
- **O que levar ao seminário** da régua sazonal. Ver `analises/2026-09-25_regua_regras_simples/`.
- **Automatizar a raspagem** — hoje manual; semana perdida é irrecuperável.

---

## ⏳ Decisões NOSSAS a pré-declarar

- **Recorte da tese** — depende do eixo.
- ⏳ **Protocolo para testar a METODOLOGIA temporada a temporada** (Vinicius, 26/09): temporadas futuras julgadas
  por tipo, com o critério de sucesso de cada tipo escrito antes; ano calmo não se julga pelo erro absoluto.
- **Alvo:** vetor (letra do PEP) × casos (o código). O PEP também erra o horizonte: é **3 meses** (Vinicius, 23/09).
- ✅ **Município de notificação mantido** (Vinicius, 25/09), para comparar; residência fica como cenário alternativo.
- **Limiar de surto:** 100 casos/semana é convenção; o plano municipal usa 140 · 421 · 702, e é o instrumento certo
  para série curta (26/09). ⚠️ O limiar do MS (100 ou 300 por 100 mil) **não tem fonte primária lida** — não citar.
- **Corte de maturidade** 12 semanas; medido em 2025: mediana 10,4 · p90 31,6.

---

## ⏳ Rodadas candidatas

- ⏳ **Vetor com folha 20 reduz o erro de 3 meses em 12-16%** (24/09, exploratório, carregado por 2024). No Chronos-2:
  ajuda em 2024-25, atrapalha em 2022-23.
- **Confirmatória em 2027**, pré-declarar antes da temporada: modelo × régua por skill; o vetor piora o alarme (13/09).
- ⏳ **Faixas de previsão estreitas demais:** o intervalo de 50% cobre 14%; a conformal piora os alarmes. Medido na tabela com 2026.
- ⏳ **Positividade das armadilhas e bairros em nível crítico** como atributos, com dado próprio de 2012 a 2026.
- ⏳ **Defasagem vetor → casos nunca estimada por nós.** da Silva 2026 mediu τ de Kendall **0,274 no lag 0** e
  **0,495 no lag 4**; a tabela dele **para no lag 4**. ⚠️ O "τ 0,59 no lag 8" que estava aqui **não existe no
  artigo** — erro meu, corrigido em 26/09.
- 🚫 **Canal endêmico e MEM em POA** — 26/09: exigem histórico longo e anos calmos. Porto Rico usa **38,5 anos**;
  aqui o limite dá 0 e o corte do MEM sobe de 6 para 94. Limiar vem do plano municipal, não do nosso histórico.
- 🟢 **Aceleração de transmissão como régua de alarme:** média móvel 4 ÷ 26 semanas, alarme acima de **1,33**. Em 8
  países: sensibilidade 100% × 30% do canal, antecedência 6,9 × 1,6 semanas. Precisa de 26 semanas, não de anos.
  ⚠️ Regra importada pode não transferir: a da Malásia foi a pior aqui (Youden −0,05).
- ✅ **Inflação do p medida** (26/09): contra `R_hoje`, o resultado é robusto ao bloco; contra `R_ano_passado`, o p
  nominal é otimista em até **3,4×**. Como o veredito contra a régua já é negativo, a inflação o reforça.
  ⏳ **O p Holm 0,037 de 13/09 segue sem medir** — as previsões por semana nunca foram salvas em disco; só dá para
  refazer retreinando o classificador. Citar com a ressalva até lá.
- 🚫 **Alarme no estágio Alerta (421): o modelo NÃO vence a régua sazonal** — 0 de 4 combinações, 26/09,
  pré-declarado. Vence `R_hoje` em 3 meses com folga (p Holm ≤ 0,00014).
- ⏳ **Limiar de decisão: separar decisão de evento só ajuda em 1 semana.** Em h=4, 8 e 12 o melhor corte fica
  ABAIXO de 421, contra a previsão declarada. Descritivo; nenhum D foi adotado. — hoje dispara quando a previsão passa de 100, o mesmo número
  do evento. Varredura + semanas consecutivas + alarme composto com a régua: recálculo sobre previsões salvas.
- 🚫 **Vírus no mosquito como atributo** — descartado pelo Vinicius em 25/09: exigiria dado novo da Prefeitura.
- 🚫 **Notificações como alvo ou entrada** (25/09): pioram em 3 meses. 🚫 **SARIMA e LASSO** (25/09): explodem.

---

## ⏳ Dívida técnica

- 🔴 **A taxa de alarmes falsos por ano está subestimada em ~53% no site publicado e no deck original.** A
  medição de 13/09 dividiu por **3 anos civis** (2024, 2025, 2026), mas a avaliação cobre **1,96 ano**: 2024
  entra com 45 semanas e 2026 com 5. Em 3 meses são **3,57/ano**, não 2,33. Achado em 26/09 pela trava de
  `analises/2026-09-26_modelo_composto/calcular_alarme.py`. ⏳ Corrigir exige decisão do Vinicius, porque o
  número está no ar.

- 🔴 **Dois Pythons no projeto, com resultados diferentes.** `python3` tem scikit-learn **1.8.0** (é o que o
  `orquestrar.sh` e toda a bateria usaram); `.venv/bin/python` tem **1.9.0**. Mesmo dado e mesmo código dão
  números diferentes **em silêncio** — descoberto em 26/09 pela trava, que reprovou. **Rodar sempre com
  `python3`.** Detalhe em `analises/2026-09-26_importancia_na_folha_20/` §4.

- **Seleção das 6 colunas de clima fora do walk-forward**, com ranking instável e dependente do alvo.
- **`bairro_surto` não re-rodado** · **`cidade_lift_vetor` sem run no MLflow** · `rodar_regressao_selecao_clima` sem pareamento.
- **Docstring de `acesso/fontes.py`:** 99,6% de confirmação em 2023; o medido é 69,3%.
- **Trava da busca de 25/09** com erro de janela no script, corrigido só por emenda · `provar_sinal_da_ancora` tautológica.
- 🔴 **Não rodar `consolidar_sinan` nem `montar.py`:** com a correção de 25/09 eles puxam o DENGBR26 novo e trazem 2026
  de volta. `preparar_dados.py` inteiro, nunca: rebaixa clima e ENSO.
- `../Contexto/` e `../artigo_oficial/` fora do git · `testar_remedios.py` com hiperparâmetros trocados · miúdos de bairro.

---

## Registro cronológico

### 27/09/2026 — o alarme falso de 2026, e os dois anos separados

- ✅ **PDF do seminário refeito, e agora sai certo** (27/09). O caminho antigo imprimia os 21 slides de uma
  vez com `transform:scale(.88)` e quebra de página, e o Chrome não reproduz isso: o título caía **na mesma
  faixa** dos nomes da barra (48,1–69,8pt contra 49,3–54,6pt, medido na p.2). O novo `NOVO_HTML/gerar_pdf.py`
  imprime **um slide por vez** via DevTools Protocol, com a barra de verdade do palco no topo, e junta as
  páginas. Slide a **89,8%** numa página de 1280x720. Certificado: 21/21 slides com o texto da tela íntegro
  no PDF, todas as páginas no tamanho certo, zero colisão. ⚠️ Nenhum conteúdo de slide foi tocado.
  ⏳ O botão **"Salvar em PDF"** da própria página segue no caminho antigo (`@media print` do `deck.py`) e
  continua produzindo a colisão — quem usar o botão, e não o script, vai ver o PDF velho.
- ✅ **A mancha cinza do slide 3 era a sombra do tema** (27/09, apontada pelo Vinicius). A segunda camada de
  `--sombra` tem **spread negativo** (`0 8px 24px -16px`), e o Chrome não escreve isso em vetor: no PDF vira
  um retângulo chapado a 22% do tamanho do cartão — 8 blocos, o maior com **18.637pt²**. Já estava no PDF
  antigo. O modo PDF agora usa só a 1ª camada (5%), e há trava que reprova a mancha se ela voltar.

- 🔴 **Em março de 2026 o modelo previu 1.808 casos para uma semana de ZERO.** Em 3 meses disparou Alerta em
  **10 das 17 semanas** do ano, 8 delas em Emergência — num ano de **12 casos**. A régua dispara 9. Em 1 semana,
  nenhum. Ele aprendeu o calendário e a tendência de alta; falta-lhe entrada para **imunidade e sorotipo**.
  ⚠️ Minha direção pré-declarada estava errada. `analises/2026-09-27_alarme_falso_em_2026/`
- 🟢 **2024 e 2025 são regimes diferentes.** Em 3 meses o alarme vai de **1/14** para **13/14** e o R² de
  **0,054** para **0,792**. Ao prever o pico de 2024 o modelo só conhecia **879** casos, precisava acertar
  **1.855** e previu **363**; em 2025, conhecia 1.855 e previu 1.321 para 2.381. Descritivo e pós-fato;
  confirmar em 2027. ✅ Certificado adversarialmente em 27/09: **9 de 9 afirmações confirmadas**.
  🔴 **Correção de 27/09:** o "precisava acertar 1.601" era erro meu — 1.601 é a semana de 17/03/2024, e o
  pico da avaliação é 1.855 (21/04). O "previu 1.614" era o maior previsto de 2025 inteiro, não o do pico.
- ✅ **Seção nova no deck da cópia 2, "Os dois anos"**, entre Resultados e Limitações, com 2 slides: a régua
  histórica e a tabela com os 3 gráficos. 21 slides. ⚠️ `seminario.py` e `seminario_v2.py` seguem intactos.
  🔴 **A 1ª versão da régua mentia** (pergunta do Vinicius, 27/09): pintava uma faixa de avaliação por ano e
  fazia parecer **dois experimentos com treino em bloco**. A avaliação é **UMA só e contínua** — 102 semanas,
  07/01/2024 a 01/02/2026 — e o treino **cresce a cada semana**. Refeita: as duas réguas são duas fotografias
  do mesmo experimento, cortadas em **nov/2023** e **out/2024**. Cada uma vem com a tabela das **5 maiores
  semanas** do ano (semana · real · previsto · diferença), critério declarado no rótulo.
- 🔴 **A melhora de 2025 NÃO é do modelo, é do ano** — medido em 27/09 contra a pergunta do Vinicius "por que
  não adotar o cenário de 2025?". Em 3 meses, a **régua sazonal** melhora igual: R² **0,243 → 0,788**, contra
  **0,054 → 0,792** do modelo. E no MAE o modelo **perde para a régua nos DOIS anos**: −14,7% em 2024 e −9,0%
  em 2025. 2025 foi mais previsível porque repetiu 2024, e a régua não aprende nada.
  ⚠️ **Não existem "dois cenários de treino"**: é um walk-forward só, que retreina a cada semana. Os números de
  2025 JÁ SÃO "treinado com 2018-2024". Reportar só 2025 seria escolher a janela depois de ver o resultado.

- 🟢 **Nenhuma previsão passou do teto do treino: 0 de 97** (27/09). Zero de 45 em 2024 (teto 879) e zero de 52
  em 2025 (teto 1.855); o real passou dele em **11** e **8** semanas. É a regra da árvore de decisão medida.
  Nas 5 maiores semanas o erro vai de **−76% a −87%** em 2024 e de **−26% a −45%** em 2025 — e as 4 primeiras
  caem na mesma época nos dois anos (31/03·07/04·14/04·21/04 × 30/03·06/04·13/04·20/04), então são comparáveis.
- ✅ **A avaliação NÃO é contínua semana a semana, e agora se sabe por quê** (27/09): faltam **7 semanas** das
  109 do calendário. A **enchente de maio/2024** parou as vistorias das armadilhas de **28/04 a 09/06/2024**, e
  o `dropna` levou as semanas-alvo que dependiam delas. Como a feature vem de `alvo − h`, o buraco **desloca
  com o horizonte** (h=1: 05/05–16/06; h=12: 21/07–01/09). Total avaliado: **102 em todo h**.
  ⚠️ O braço **sem vetor tem 109**, não 102 — não depende de armadilha. As comparações com ele **são pareadas**
  (`comparacoes.csv` registra `semanas_pareadas=102` em todo h), então nada está contaminado.
- 🔴 **Slide da literatura: certificado e REPROVADO** (27/09, leitura dos PDFs em disco). Três achados:
  1. O **R² 0,46 do da Silva NÃO EXISTE** no artigo — o PDF traz `RMSE 1,003/1,006` e **razão de deviance 0,61**
     em log(incidência). É **preprint medRxiv**, não PLOS NTD. A "confirmação" de 25/09 veio de **WebFetch**, não
     do arquivo; o item está emendado em `analises/2026-09-25_comparacao_direta_literatura/verificacao_grupo_2.md`.
  2. O **CatBoost é da Cunha e Silva 2026** (Int J Biometeorol, ≠ da Silva) e prevê **INTERNAÇÃO** (CID-10
     A90/A91), não caso. R² POA −0,2064 em H1-H4. ✅ `06_literatura.md` L680 corrigido — dizia "mesma unidade".
  3. ✅ **Shi et al. 2016 confere** literalmente (17% em 1 sem, 24% em 3 meses; SARIMA 29%).
  🔴 **E o R² não compara nada:** o MESMO modelo nosso dá **−18,02 em 2021**, −0,22 em 2022, 0,33 em 2023 e
  **0,717 em 2024-25** — é refém da variância da janela. Na nossa janela, **repetir o ano passado dá 0,623**.
  ✅ **Decidido e reescrito (Vinicius, 27/09):** o slide deixou de ser placar e virou **panorama** — 6 estudos
  com `estudo · onde e série · O QUE PREVÊ · resultado`, sem o nosso na tabela. A coluna do alvo é o argumento:
  caso notificado, internação, incidência em log, categoria de risco e probabilístico — o campo não convergiu
  nem sobre o que medir. **Só 2 dos 6 rodam em produção** (Shi/Singapura e D-MOSS/Vietnã).
  Todos os campos conferidos contra o PDF. ⚠️ Duas correções contra a doc: Shi usa **12** anos (2001-2012),
  não 13; e o "skill mediano 0,12" é do **2º sprint Mosqlimate, que não tem PDF em disco** — fora do slide.
- 🟢 **A única coisa comparável entre estudos: cada um bate a própria referência?** Medido nos PDFs em 27/09.
  **3 dos 6 batem** — Shi (24% × 29% do SARIMA), D-MOSS (−17,8% × média sazonal) e Lowe (57% × 33% do nulo);
  os três têm **12 a 20 anos** de série. **Não batem:** da Silva (empata com regressão linear, RMSE 1,006 ×
  1,003), da Cunha e Silva (R² negativo em POA) e o **sprint nacional** (baseline bayesiano empata com os
  modelos complexos). **O nosso bate até 1 mês (+6,4%) e perde de 2 meses (−3,2%) e 3 meses (−11,9%).**
  ⚠️ A janela de POA no da Cunha e Silva é **1999-2021** — não alcança 2024-25, então o R² negativo dele não
  se compara ao nosso. 🔴 **Não dizer "o nosso é melhor que a literatura"**: não é sustentável.
- 🟢 **As quatro arboviroses: o dado EXISTE, o problema é outro** (27/09). Temos zika e chikungunya em
  `modelagem_aedes/dados/entradas/infodengue_poa/`. De 2010 a 2026: **125.868** casos de dengue, **528** de
  chikungunya e **364** de zika — dengue é **99,3%**. Chik fica em zero em **70%** das semanas e zika em
  **81%**; maior semana de cada uma: 14 e 16, contra 6.260 da dengue. O alvo seria quase sempre zero — o mesmo
  problema de 2026. ⚠️ A série de zika do InfoDengue **para em fev/2024**.
- 🟢 **A série do VETOR tem quase o dobro da de casos:** 13,9 anos (set/2012 a ago/2026) contra 8,2 (fev/2018 a
  abr/2026). Em casos estamos abaixo dos 12-20 anos dos estudos que batem a própria referência; **no vetor,
  dentro da faixa**. Argumento a favor de adotar o vetor como alvo, não contra.
- 🟢 **E os três que batem tinham vantagem de partida** (coluna "em que condições", 27/09): Shi tem **12 anos**
  e compara com **SARIMA**, não com régua sazonal; D-MOSS tem **20+ anos** e agrega província e mês; Lowe prevê
  **categoria** de risco, não o número. **Nenhum dos três venceu nas nossas condições** — 8 anos, cidade com
  epidemia só desde 2022, alvo é o número semanal.
- ⏳ `documentacao_completa/partes/06_literatura.md` L680 diz "mesma unidade (casos/incidência)" sobre o CatBoost.
  **Está errado** — é internação por 100 mil. Corrigir antes da banca.

### 26/09/2026 — a folha 20 se apoia MUITO mais no vetor

- ✅ **Permutação medida na folha 20**, pré-declarada, descritiva: o vetor pesa mais nos **12 de 12**
  horizontes. Em 1 mês, trocar as colunas do mosquito **dobra** o erro (**+108,3%** contra +62,2% na folha 5).
  Maior também em casos absolutos, então não é artefato de denominador.
- 🟢 **As duas medidas apontam junto:** a folha 20 **ganha** mais com o vetor (ablação) e **se apoia** mais
  nele (permutação). É o argumento mais forte que o projeto tem sobre a armadilha.
- 🚫 **Continua sem sustentar "indispensável":** na configuração adotada, tirar o vetor não piora
  (p Holm 1,00). Permutação e ablação respondem perguntas diferentes.
- 🔴 A primeira rodada **reprovou na trava** — causa era o Python, não o dado (ver Dívida técnica).
  `analises/2026-09-26_importancia_na_folha_20/`

### 26/09/2026 — documentação técnica completa

- ✅ **`documentacao_completa/DOCUMENTACAO_COMPLETA.md`**: 11 partes, ~95 mil palavras, tudo conceituado do
  zero, com fórmula e exemplo numérico. Escrita por 8 autores em paralelo sobre números canônicos comuns.
- ✅ **Conferida número a número** por 5 verificadores independentes: 12 achados, 6 graves, **todos os
  graves e médios corrigidos**. Lista em `documentacao_completa/CORRECOES_PENDENTES.md`.
- 🔴 **Três erros eram meus, nos números canônicos:** o n avaliado é **102** e não 295/292/288/284; o
  `V1_alvo_log` perde **9,9%** para o controle e 23,0% para a régua; o Youden da régua em h=12 é **0,80**
  e não 0,81. Corrigidos no documento e aqui.

### 26/09/2026 — 2026 sai da avaliação, e o limiar ganha base

- 🚫 **Premissa de Porto Rico derrubada:** eles usam **38,5 anos** de série (MMWR mm7405a1), não série curta. Limiar
  derivado de histórico exige anos calmos, que POA não tem. Reforça usar o plano municipal.
  🟢 Achado: **aceleração de transmissão** (4÷26 semanas, corte 1,33) como régua sem série longa.
  `analises/2026-09-26_limiar_para_serie_curta/`

- 🚫 **2026 não entra (Vinicius):** com séries crescentes é impossível prever um ano de 19 casos. A tabela oficial voltou à
  de antes (até SE 202617, avaliação até 01/02/2026); a versão com 2026 fica guardada em `atualizacao_dados_2026/`.
- ⚠️ A busca de 120 e a segunda bateria rodaram na tabela com 2026 e ficam só como registro; a melhor da busca perde
  para a régua em 3 meses (239,6 × 226,8).
- ✅ **WIS refeito na tabela oficial** (26/09): em 1 mês os dois modelos vencem a régua climatológica (p Holm < 0,0001);
  em 3 meses só o **folha 20** vence (p Holm 0,0020) — o adotado **não** (p Holm 0,096).
  🔴 **Cobertura: boa na calmaria, péssima onde importa** (26/09). Acima de 421 casos o intervalo de 90% cobre
  **18%**; na calmaria, 91%. 🚫 **Transformação de escala não resolve** — raiz e log pioraram a cobertura em
  todas as faixas. A causa medida é **viés, não variância**: o erro mediano acima de 421 é **539 casos sobre
  917 reais**, e a faixa já cresce 69× enquanto o erro cresce **425×**. Alargar não conserta viés.
  ⚠️ O "415×" que estava aqui era erro meu, corrigido em 27/09 remedindo do CSV de quantis.
  `analises/2026-09-26_calibracao_por_faixa/` · `analises/2026-09-26_transformacao_de_escala/`
  ⚠️ Dívida: h=1 do adotado diverge **−2,75%** da rodada anterior, acima do teto de 1%; causa provável é a seleção de
  clima nos 60% mais antigos, não confirmada. `analises/2026-09-26_wis_na_tabela_restaurada/`
  `analises/2026-09-25_segunda_bateria_noturna/` · `analises/2026-09-25_busca_de_hiperparametros/`

### 25/09/2026 — régua, literatura e novas tentativas

- 🔴 **O modelo perde para "a mesma semana do ano passado"** em 2 e 3 meses (2024-25). `analises/2026-09-25_regua_regras_simples/`
- ✅ Literatura, catálogo e comparação direta: perder para régua em 3 meses é comum; em POA, o projeto está acima dos
  estudos publicados. 🚫 Formulações novas, modelos de fundação, SARIMA, LASSO e notificações: nenhum bate a régua.
- ✅ Alarme: em 1 mês o modelo vence as regras simples. ✅ Plano municipal: limiares oficiais e testagem por estágio.
- ✅ Páginas locais **Comparações** e **Notificações como alvo**, não publicadas.

### 24/09/2026 — bateria noturna

- 🔴 Com folha mínima 20, o vetor reduzia o erro de 3 meses em 2024-25; **em 2026 inverteu**. 🚫 ENSO era vazamento.

### Antes

- **23/09** site reconstruído e publicado (`710b411`) · **21/09** reunião: eixo pós-seminário, casos a partir do vetor.
- **13/09** vazamento corrigido (+52% de MAE em 3 meses); único resultado em Holm: o vetor piora o alarme (p 0,037).
- **30/08** grid de 120 execuções · **29/08** clima desde 2012 · **16/08** base certificada contra a Marília.
