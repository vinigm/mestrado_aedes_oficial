# Relatórios dos agentes — auditoria de 13/09/2026

> Saída bruta dos 10 agentes Sonnet (7 leitores de código + 3 verificadores adversariais). Cada afirmação traz arquivo:linha e grau: LIDO_NO_CODIGO / INFERIDO / NAO_ENCONTRADO.
> Síntese e crítica do orquestrador: [README.md](README.md).

## R1 — Dos dados brutos até a tabela_final

### Afirmações

- **[LIDO_NO_CODIGO]** Semana = domingo a sabado, regra da semana epidemiologica brasileira (semana 1 = a que contem a quarta-feira do dia 1/1). Calculada a partir da quarta-feira de cada domingo.  
  `dominio/montagem_tabela.py:48-78 calcular_semana_epidemiologica`
- **[LIDO_NO_CODIGO]** aedes_aegypti (contagem) = soma de FEMEAS+MACHOS de todas as inspecoes da semana. Ja aedes_aegypti_por_armadilha usa so FEMEAS no numerador (femeas_aegypti) dividido pelo numero_de_armadilhas.  
  `dominio/montagem_tabela.py:126,136-137,167-169`
- **[LIDO_NO_CODIGO]** numero_de_armadilhas: quando existe inspecao_realizada na semana, e a contagem de armadilhas com inspecao_realizada=True; quando TODA a semana tem inspecao_realizada vazio (2012-2018), vira a contagem de QUALQUER registro na semana (aproximacao) e denominador_aproximado=1.  
  `dominio/montagem_tabela.py:83-84,129-165`
- **[LIDO_NO_CODIGO]** Semana sem NENHUMA inspecao: todas as colunas do vetor (armadilhas, contagens, densidade) ficam NaN, via reindex na grade continua semanal; nao ha interpolacao.  
  `dominio/montagem_tabela.py:142-147`
- **[LIDO_NO_CODIGO]** Grade semanal vai de 2012-09-23 ate 2026-08-09, contigua por construcao (pd.date_range freq=W-SUN entre o min e o max de data com inspecao no parquet); tabela_final.csv tem 725 linhas de dado (726 com cabecalho).  
  `dominio/montagem_tabela.py:142 + dados/entradas/tabela_modelagem/tabela_final.csv (contagem direta)`
- **[LIDO_NO_CODIGO]** casos_confirmados vem do SINAN (df_casos), agrupado por SE (coluna SEM_PRI convertida p/ numero) e casado na tabela por SE (merge on='SE'), NAO pela data.  
  `dominio/montagem_tabela.py:206-214`
- **[LIDO_NO_CODIGO]** Dentro do intervalo [primeira SE, ultima SE] que o arquivo de casos cobre, semana sem registro vira 0 de verdade; antes da primeira SE ou depois da ultima SE fica NaN (nunca 0).  
  `dominio/montagem_tabela.py:216-238`
- **[LIDO_NO_CODIGO]** O corte de maturidade NAO e aplicado na montagem da tabela_final; e aplicado depois, por experimento, via aplicar_corte_maturidade(dados, semanas_corte) chamado em pipeline.py, com semanas_corte_maturidade variando por config (12 em tres experimentos, 0 em outros tres).  
  `dominio/surto.py:12-50; pipeline.py:219,271,322,593; config/experimentos/*.py`
- **[LIDO_NO_CODIGO]** O corte de maturidade zera (NaN) os casos das semanas mais recentes contando a partir da ULTIMA semana que tem caso nao-nulo (nao da ultima linha da tabela).  
  `dominio/surto.py:38-49`
- **[LIDO_NO_CODIGO]** Comentario em montagem_tabela.py cita uma constante 'JANELA_MATURACAO_CASOS_SEMANAS' como se existisse no arquivo; ela NAO EXISTE em lugar nenhum do codigo (grep vazio). Referencia esta desatualizada/errada.  
  `dominio/montagem_tabela.py:198 (comentario); busca em todo o pacote nao encontrou a constante`
- **[LIDO_NO_CODIGO]** ENSO (nino34_anom, oni) e mensal e casado por (ano do calendario, mes do calendario) do domingo que abre a semana: todo domingo do mesmo mes recebe o MESMO valor de ENSO, mesmo que a semana atravesse dois meses.  
  `dominio/montagem_tabela.py:240-246`
- **[INFERIDO]** Clima (CAMINHO_CLIMA_SEMANAL) e casado por data_inicio_semana_epidemi (merge left); as colunas (precip_total_mm, temp_media, etc.) sugerem soma/media/max diarios agregados por semana, mas a formula exata esta em preparo/capturar_clima.py, nao lido nesta tarefa.  
  `dominio/montagem_tabela.py:212-213; cabecalho de tabela_final.csv`
- **[NAO_ENCONTRADO]** As '7 semanas sem inspecao' (virada 2017/2018 + 3 semanas da enchente de maio/2024) sao afirmadas no README e nos comentarios do codigo, mas nao foram contadas diretamente por esta reconstrucao (nao abri o parquet da Secretaria).  
  `README.md:162-165; dominio/montagem_tabela.py:109-114 (comentario)`

### Escolhas que um pesquisador talvez não espere

- **Densidade e contagem tem numeradores diferentes**: `aedes_aegypti` soma macho+femea; `aedes_aegypti_por_armadilha` usa SO femea. Facil supor erradamente que uma e a outra dividida pelo denominador.

- **Denominador pre-2019 e aproximado sem aviso no valor**: `denominador_aproximado=1` mistura "qualquer registro" com inspecao real. Se um experimento nao filtrar por essa flag, 2012-2018 entra com qualidade diferente do resto sem sinal visivel no numero.

- **Corte de maturidade fica FORA da tabela_final, por experimento**: duas configs usando o MESMO CSV podem ter valores diferentes de `casos` nas ultimas ~12 semanas (12 vs 0), dependendo de `semanas_corte_maturidade`. Nao e bug — mas exige checar a config antes de comparar dois experimentos.

- **ENSO repete o mesmo numero mensal em varias semanas do mes** (casado por ano/mes do domingo, nao por semana real de divulgacao) — injeta correlacao serial artificial dentro do mes.

- **casos_confirmados casa por SE, nao por data** — se o calculo de SE do SINAN divergir do calculo do vetor em alguma borda de ano, o caso vai pra semana errada sem erro nenhum.

### Riscos de validade

- **Comentario aponta constante inexistente** (`JANELA_MATURACAO_CASOS_SEMANAS`, montagem_tabela.py:198): sugere doc interna desatualizada sobre o mecanismo de maturidade real (que hoje e `ultima_se_divulgada` na montagem + `aplicar_corte_maturidade` a parte). Risco de reconstruir a logica errado de memoria.

- **Vazamento por SE mal alinhado (hipotese)**: merge de casos por SE (linha 214), nao por data. Se `SEM_PRI` do SINAN divergir da SE recalculada pelo vetor numa virada de ano, caso vai pra semana adjacente sem erro. So vi confirmacao de alinhamento (715 semanas, 0 divergencia) para o par InfoDengue x tabela_final (fontes.py:183), nao para o par SINAN x vetor.

- **ENSO mensal replicado por semana** pode virar "sinal" espurio pra um modelo com lags curtos, sendo na verdade o mesmo numero repetido.

- **Formula de agregacao do clima nao verificada** (preparo/capturar_clima.py fora do escopo lido) — nomes de coluna sao INFERIDOS, nao confirmados linha a linha.

### Divergências código × README

README confirma que Marilia/raspagem saem do fluxo da tabela_final e o codigo bate (montar.py so chama carregar_secretaria_armadilhas). Unica divergencia achada e INTERNA ao codigo, nao README x codigo: comentario em montagem_tabela.py:198 cita constante `JANELA_MATURACAO_CASOS_SEMANAS` que nao existe no pacote (grep vazio). README nao menciona essa constante, entao nao ha contradicao README x codigo — so comentario desatualizado dentro do proprio arquivo.

### Perguntas para o pesquisador

- Voce esperava que a densidade use SO femeas no numerador, enquanto a contagem bruta soma macho+femea?

- Voce sabia que o corte de maturidade (12 semanas) fica fora da tabela_final e e decidido por experimento — dois experimentos podem ver `casos` diferente nas ultimas 12 semanas com o MESMO CSV?

- Quer que eu confirme se o SE do SINAN bate com o SE do vetor em todas as viradas de ano (merge de casos e por SE, nao por data)?

- A flag `denominador_aproximado` (2012-2018) e usada como peso/filtro em algum experimento hoje?

### Arquivos lidos

dominio/montagem_tabela.py (integral), preparar_dados.py (integral), montar.py (integral), acesso/fontes.py (integral), dominio/surto.py (integral), config/settings.py (integral), README.md (secoes via grep+sed), tabela_final.csv (cabecalho+3 linhas+contagem). Nao lido: preparo/capturar_clima.py, preparo/capturar_enso.py, preparo/unificar_arquivos_secretaria.py, parquet da Secretaria.

## R2 — Motor de previsão, features, seleção de clima e grid

### Afirmações

- **[LIDO_NO_CODIGO]** y_h (alvo) = coluna_alvo deslocada -horizonte linhas: na linha da ORIGEM (semana i), y_h = casos da semana i+h. Lags olham pra tras a partir da origem.  
  `dominio/features.py:151`
- **[LIDO_NO_CODIGO]** alvo_sin/alvo_cos usam o calendario da semana ALVO (semana.shift(-horizonte)); sem_sin/sem_cos e que sao da origem.  
  `dominio/features.py:111-113 vs 152-155`
- **[LIDO_NO_CODIGO]** So existem lags 1,2,3,4 semanas na lista oficial, para casos, vetor e 5 variaveis de clima.  
  `dominio/features.py:19-28`
- **[LIDO_NO_CODIGO]** MAS a versao CRUA (contemporanea a origem) de casos, do vetor e de varias colunas de clima tambem vira feature, porque colunas_ignorar nao remove esses nomes crus.  
  `config/experimentos/cidade_regressao.py:143-147 + dominio/selecao_features.py:40-46`
- **[LIDO_NO_CODIGO]** Confirmado no cabecalho de tabela_final.csv: 'aedes_aegypti_por_armadilha' e 'temp_media' crus existem e nao estao em colunas_ignorar - M1 fica com 6 colunas de vetor (1 crua+4 lags+mm4), batendo com o README.  
  `dados/entradas/tabela_modelagem/tabela_final.csv (cabecalho)`
- **[LIDO_NO_CODIGO]** casos_mm4 = rolling(4).mean(), janela padrao do pandas inclui a propria semana de origem + 3 anteriores.  
  `dominio/features.py:32-38,105`
- **[LIDO_NO_CODIGO]** Walk-forward: janela de treino EXPANSIVEL, 1 previsao por corte; passo pula 'passo' linhas VALIDAS (pos-dropna), nao necessariamente 'passo' semanas de calendario se houver buracos.  
  `motor/walk_forward_regressao.py:63-82`
- **[LIDO_NO_CODIGO]** minimo_semanas_treino=104 fixo nas duas configs; passo=2 na config padrao, passo=1 na de referencia (dobra pontos testados).  
  `config/experimentos/cidade_regressao.py:132-138; cidade_referencia.py:79`
- **[LIDO_NO_CODIGO]** Selecao das k colunas de clima e feita UMA UNICA VEZ (fora do loop de k e do walk-forward), usando so a fatia inicial cronologica (60%) de TODAS as linhas com clima completo.  
  `dominio/selecao_features.py:100-118; pipeline.py:277-280`
- **[LIDO_NO_CODIGO]** O mesmo ranking de clima e reaproveitado por todos os valores de k e todos os cortes do walk-forward subsequentes dentro do mesmo script.  
  `pipeline.py:277-297`
- **[LIDO_NO_CODIGO]** M0 e M1 NAO usam as mesmas semanas de teste no motor de regressao simples nem no grid: cada um faz seu proprio dropna.  
  `motor/walk_forward_regressao.py:65-66; rodar_grid.py:133-137`
- **[LIDO_NO_CODIGO]** Confirmado no checkpoint do grid: em h=1, M0 tem 307 pontos de teste por combinacao algoritmo x perda, M1 tem 295 - diferentes conjuntos de semanas.  
  `saidas/grid_previsoes_parciais.csv`
- **[LIDO_NO_CODIGO]** So o motor walk_forward_pareado forca as MESMAS semanas p/ M0 e M1 (dropna usa o conjunto maior, features_m1); usado no Diebold-Mariano, nao no ranking MAE do grid.  
  `motor/walk_forward_pareado.py:59-66`
- **[NAO_ENCONTRADO]** No grid, FIM_DA_CALIBRACAO e LIMITE_PICO sao definidos mas NAO usados dentro de rodar_grid.py; o split calibracao/avaliacao que gerou grid_resumo.csv nao esta salvo como script na pasta.  
  `rodar_grid.py:44 (nao referenciado)`
- **[LIDO_NO_CODIGO]** Previsao com perda quantilica (quantile=0.80) e o quantil 0,80 da distribuicao condicional, NAO a media - enviesada pra cima por construcao.  
  `config/experimentos/cidade_referencia.py:27-32,55-66`
- **[LIDO_NO_CODIGO]** Selecao de clima na config de referencia usa sempre o LightGBM (modelo_selecao_clima), mesmo o modelo final sendo HistGradientBoosting - deliberado, p/ nao mudar o ranking do grid.  
  `config/experimentos/cidade_referencia.py:69-77`

### Escolhas que um pesquisador talvez não espere

**1) Feature contemporânea (lag 0) escondida.** `LAGS_SEMANAS` so tem 1-4, mas `colunas_ignorar` nao remove as versoes CRUAS de `casos`, do vetor e do clima. Alem de `casos_lag1..4`/`casos_mm4`, o modelo recebe `casos` da PROPRIA semana de origem (idem vetor/clima). Correto (nao e vazamento do alvo), mas muda a leitura de "so historico" para "historico + ultimo valor conhecido".

**2) casos_mm4 inclui a semana atual** (`rolling(4).mean()` do pandas nao e so passado estrito).

**3) Selecao de clima e uma unica foto, nao por dobra.** O top-6 de clima e escolhido uma vez com 60% inicial da serie inteira e reaproveitado em TODOS os cortes do walk-forward, inclusive nos primeiros (logo apos a semana 104) - informacao mais "larga" do que a disponivel nesses pontos.

**4) M0 x M1 nao pareados no grid.** Confirmei nos dados: em h=1, M0 tem 307 pontos e M1 tem 295 - o MAE de cada um vem de conjuntos de semanas diferentes, exceto no teste Diebold-Mariano (que forca pareamento).

**5) Perda quantilica muda o significado do numero** (patamar 80%, nao valor esperado) - o README ja avisa isso.

### Riscos de validade

**Comparacao M0 x M1 nao pareada** no grid e no `rodar_regressao_selecao_clima` (confirmado: 307 vs 295 pontos em h=1) - a diferenca de MAE mistura efeito do vetor com efeito de testar em semanas diferentes. So `walk_forward_pareado` corrige isso.

**Selecao de clima fora do walk-forward**, com corte cronologico unico (60%) sobre toda a serie - risco de otimismo leve nos primeiros pontos do walk-forward, que "herdam" um ranking calculado com mais informacao do que teriam disponivel se recalculado a cada dobra.

**Multiplas comparacoes (30 configs no grid)** - ja reconhecido no README/PRE_DECLARACAO: nenhuma das 60 comparacoes M0xM1 sobrevive a Holm.

**Passo do walk-forward e em linhas validas pos-dropna**, nao em semanas de calendario - se ha buracos de NaN, o espacamento real entre testes pode variar sem aparecer no "n" reportado.

**Script que decide o vencedor do grid** (split calibracao/avaliacao, MAE/R2/vies) nao esta nos arquivos fornecidos - so os outputs existem, entao nao pude auditar essa etapa a partir do codigo.

### Divergências código × README

Nenhuma divergencia factual entre README/PRE_DECLARACAO e o `rodar_grid.py` (hiperparametros, eixos do grid, passo=1, clip em zero). Lacuna de rastreabilidade: o script que aplica `FIM_DA_CALIBRACAO` e gera `grid_resumo.csv` (a peca que decide o vencedor) nao esta salvo na pasta, so os outputs dele.

### Perguntas para o pesquisador

- Voce sabia que o modelo usa a versao CRUA (sem defasagem) de casos/vetor/clima da propria semana de origem, alem dos lags 1-4?

- Voce esperava que a selecao das 6 colunas de clima fosse refeita a cada corte do walk-forward, ou sabia que e uma unica vez (60% inicial da serie)?

- Voce tinha ciencia de que M0 e M1 sao avaliados em semanas DIFERENTES no grid e no rodar_regressao_selecao_clima (so o Diebold-Mariano e pareado)?

- O script que gera grid_resumo.csv (split calibracao/avaliacao) existe em algum notebook/historico? Vale salva-lo na pasta.

### Arquivos lidos

pipeline.py; motor/walk_forward_regressao.py; motor/walk_forward_pareado.py; dominio/features.py; dominio/selecao_features.py; dominio/surto.py; config/experimentos/cidade_regressao.py e cidade_referencia.py; config/modelo.py; config/settings.py; analises/2026-08-30_grid_completo/rodar_grid.py, PRE_DECLARACAO.md, README.md; saidas/*.csv (cabecalhos/contagens); tabela_final.csv (so cabecalho).

## R3 — Métricas e testes estatísticos

### Afirmações

- **[LIDO_NO_CODIGO]** 'Pico' NAO tem definicao unica: maioria usa limiar FIXO real>100 casos/semana (LIMITE_PICO=100); testar_alvo_e_features.py usa limiar RELATIVO (percentil 85 da propria serie de cada alvo).  
  `rodar_grid.py:43 (nao usado); decompor_erro.py:43-45; testar_alvo_e_features.py:139`
- **[LIDO_NO_CODIGO]** 'captura_pico' = razao entre MEDIAS, nao taxa de deteccao ponto-a-ponto: picos['pred'].mean()/picos['real'].mean(), so nas semanas classificadas como pico.  
  `testar_features_longas.py:218; testar_alvo_e_features.py:145`
- **[LIDO_NO_CODIGO]** 'vies_pico' = media do erro (pred-real) restrita as semanas de pico; sinal importa (negativo=subestima). Em testar_vetor_calibrado.py: vies_pico_sem/com_vetor = mean(pred-real) nos picos pareados.  
  `testar_features_longas.py:217; decompor_erro.py; testar_vetor_calibrado.py:199-200`
- **[LIDO_NO_CODIGO]** rodar_grid.py (script apontado na tarefa) NAO contem nenhuma funcao de MAE/R2/vies_pico/captura_pico: so roda walk-forward e grava previsoes brutas (h,data_alvo,real,pred). As metricas de grid_resumo.csv/grid_ranking_completo.csv vieram de outro processo, sem .py na pasta.  
  `rodar_grid.py (216 linhas, integro)`
- **[LIDO_NO_CODIGO]** R2 oficial (metricas_regressao.py) usa sklearn.r2_score(real,pred) agrupado por h, sem filtro de periodo dentro da funcao - quem filtra calibracao/avaliacao e o script chamador antes.  
  `metricas_regressao.py:33-41`
- **[LIDO_NO_CODIGO]** Nas analises de 30/08 o R2 e reimplementado na mao como 1 - soma(erro^2)/soma((real-media)^2) (formula equivalente a sklearn, mas nao chama metricas_regressao.py).  
  `testar_features_longas.py:213-216; calibrar_quantilico.py:161-166`
- **[LIDO_NO_CODIGO]** Diebold-Mariano aceita 'quadratico' (default) ou 'absoluto'; todos os usos vistos em 30/08 chamam explicitamente com 'absoluto', nunca o default quadratico.  
  `diebold_mariano.py:52,76-79; testar_h12_focado.py:216; testar_vetor_calibrado.py:184-186`
- **[LIDO_NO_CODIGO]** DM usa correcao HLN (fator sqrt((n+1-2h+h(h-1)/n)/n), piso 1e-9) e p-valor de UM LADO SO via stats.t.cdf(-estatistica, df=n-1) - testa so 'M1 erra menos', nunca o sentido contrario.  
  `diebold_mariano.py:94-97`
- **[LIDO_NO_CODIGO]** A serie de diferencas do DM vem de um merge/pareamento explicito por data_alvo (e 'real') entre M0 e M1 - e pareada por semana-alvo, nao por indice de linha.  
  `testar_h12_focado.py:210; testar_vetor_calibrado.py:181-183`
- **[LIDO_NO_CODIGO]** McNemar oficial (pipeline.py) compara acerto binario (pred==real) de surto entre so-clima e clima+vetor; usa binomial exato se discordancias<25, senao qui-quadrado com correcao de continuidade -1.  
  `mcnemar.py:69-84; pipeline.py:643-648`
- **[LIDO_NO_CODIGO]** corrigir_holm() nao decide a familia - so recebe o array que o chamador montou. Tamanho muda por script: 6 (oficial e h12), 8 (vetor calibrado), 12 (investigar_contradicao_alvos).  
  `correcao_multipla.py:22; pipeline.py:677; testar_h12_focado.py:243; testar_vetor_calibrado.py:207`
- **[LIDO_NO_CODIGO]** Bootstrap em blocos (h12): bloco de 8 semanas, 2000 reamostras com reposicao, concatenadas/truncadas ao tamanho original; IC95=percentil 2.5/97.5 da media da diferenca de erros absolutos.  
  `testar_h12_focado.py:134-164`
- **[LIDO_NO_CODIGO]** Em testar_h12_focado.py o Holm(6) roda sobre a MEDIANA do p de DM entre 5 sementes por (algoritmo,h) - nao um p recomputado com dados agrupados nem combinacao formal (Fisher/Stouffer).  
  `testar_h12_focado.py:241,243`

### Escolhas que um pesquisador talvez não espere

- 'Captura do pico' nao e taxa de deteccao (%-de-picos-sinalizados); e razao entre media das previsoes e media dos reais so nas semanas de pico. 92% pode conviver com erro grande em picos individuais, se os erros se compensarem na media - a metrica nao penaliza variancia dentro do grupo, so vies agregado.

- O limiar de "pico" muda entre scripts: maioria fixa 100 casos/semana; testar_alvo_e_features.py usa percentil 85 RELATIVO a cada alvo. Comparar captura_pico entre esses dois scripts sem notar a troca compara coisas diferentes.

- rodar_grid.py (indicado na tarefa) nao calcula nenhuma metrica - so gera previsoes brutas. Os numeros oficiais do grid (base da escolha HGB quantil 0.80) vieram de processo sem .py salvo na pasta - a formula exata nao e auditavel hoje a partir do codigo.

- DM sempre unilateral ("M1 erra menos"); se o vetor piorar em algum horizonte, o teste como escrito nunca sinaliza isso como significativo no sentido oposto.

- Holm em h12 roda sobre a MEDIANA de 5 p-valores (sementes), nao uma combinacao formal (Fisher/Stouffer) - resumo pratico, nao procedimento padrao de meta-analise.

### Riscos de validade

- Selecao de hiperparametro com dado do futuro (suspeita, nao confirmada): calibrar_quantilico.py escolhe alpha SO com calibracao (correto, visivel no codigo). Mas o "vencedor" do grid completo (config de referencia) foi escolhido olhando um ranking cujo script gerador nao existe na pasta - nao da pra confirmar se avaliacao (2024+) entrou no criterio de escolha do alpha/algoritmo. PRECISA achar esse script.

- Familias de Holm inconsistentes (6, 8, 12) entre rodadas: comparar "sobreviveu a Holm" entre rodadas diferentes sem citar o tamanho da familia sugere rigor igual quando nao e.

- DM pareado via merge (inner join) por data_alvo: se M0/M1 tiverem semanas validas diferentes (NaN em feature), o merge reduz silenciosamente a amostra a interseccao - nao vi checagem/log de quantas linhas foram descartadas.

- McNemar com poucos positivos (percentil 95) tem poder baixo - risco conhecido, ja documentado no proprio codigo/README, nao e bug oculto.

### Divergências código × README

Nao foi feita comparacao linha-a-linha contra README/PRE_DECLARACAO de cada pasta (escopo focou nos .py de metrica). Unica divergencia encontrada foi INTERNA ao codigo: rodar_grid.py define LIMITE_PICO=100 mas nunca usa - residuo de algo removido ou nunca implementado.

### Perguntas para o pesquisador

- Voce sabia que 'captura do pico' e razao de medias agregadas, nao taxa de acerto ponto-a-ponto?

- Voce sabia que o limiar de pico e FIXO (100) na maioria e RELATIVO (percentil 85) em testar_alvo_e_features.py?

- Sabe quem/o que gerou grid_resumo.csv e grid_ranking_completo.csv, ja que rodar_grid.py so grava previsoes brutas? Preciso desse script pra auditar a config de referencia.

- Esperava que o DM fosse sempre unilateral (so testa "vetor ajuda")?

- Esperava que o Holm em h12 usasse a MEDIANA de p entre sementes, em vez de combinacao formal?

### Arquivos lidos

avaliacao/{metricas_regressao,metricas,diebold_mariano,mcnemar,correcao_multipla}.py; grid_completo/rodar_grid.py; teste_focado_h12/testar_h12_focado.py; vetor_no_modelo_calibrado/testar_vetor_calibrado.py; trechos de features_longo_prazo, decomposicao_erro_cenario1, calibracao_quantilica, alvo_e_features_infodengue, remedios_vies_pico; pipeline.py (~590-690); config/experimentos (grep); grep "pico"/"corrigir_holm" no projeto.

## R4 — Calibração quantílica, viés de pico, remédios, decomposição

### Afirmações

- **[LIDO_NO_CODIGO]** TESTE A mede, a cada corte, o máximo de casos visto no treino (maximo_visto_no_treino) e conta picos reais (>100) acima desse teto (picos_ACIMA_do_teto). Resultado: teto médio ~1439; só 5 de 32 picos (7 em h1) ficam acima — maioria dos picos está dentro do já visto, mas o modelo ainda subestima muito.  
  `diagnosticar_vies_pico.py:100-146; diagnostico_picos.csv`
- **[LIDO_NO_CODIGO]** TESTE B (log1p) não confirma nem refuta de forma limpa a hipótese do teto: previsão registrada era 'se causa=teto, log não conserta'; na prática o viés PIOROU com log1p em todos horizontes — não bate com nenhuma das duas previsões binárias do docstring.  
  `diagnosticar_vies_pico.py:16-23,186-188; diagnostico_picos.csv`
- **[NAO_ENCONTRADO]** O '61% das semanas com <=5 casos' citado como causa do viés é uma frase de comentário/docstring; nenhuma linha executável destes 6 arquivos calcula esse percentual — é citação repassada de análise anterior, não recomputada aqui.  
  `testar_remedios.py:9-11 (comentário)`
- **[LIDO_NO_CODIGO]** testar_remedios.py compara 4 remédios contra o baseline 'atual' (LightGBM squared_error, mesmos hiperparâmetros): A=mês-alvo categórico, B=objetivo tweedie (potência 1,5), C=quantílico alpha 0,8, D=A+B combinados.  
  `testar_remedios.py:76-83`
- **[INFERIDO]** Não existe função de escolha de vencedor no código — só imprime tabelas. A vitória do quantílico (C) é leitura humana: é o único que reduz |viés no pico| nos 4 horizontes simultaneamente; tweedie/D melhoram h=1 mas PIORAM o viés em h=8/h=12 vs baseline.  
  `remedios_resumo.csv; ausência de função 'escolher_*' em testar_remedios.py`
- **[LIDO_NO_CODIGO]** Calibração do alpha: métrica = média de |viés no pico| nos 4 horizontes, só com semanas cujo data_alvo <= 31/12/2023; guarda = MAE global não pode piorar mais que 20% vs padrão nesse recorte; vence o menor viés que passa na guarda.  
  `calibrar_quantilico.py:183-218,43,58`
- **[LIDO_NO_CODIGO]** Resultado real: alpha 0,85 escolhido (|viés| calibração=103,3; guarda -1,4% de MAE, aprovado). Na avaliação (2024+, nunca usada na escolha) o viés no pico também caiu: -111,8→-21,6 (h1) e -494,3→-420,6 (h12).  
  `calibracao_log.txt (bloco 'escolha do alpha'); calibracao_resumo.csv`
- **[NAO_ENCONTRADO]** Os números 'captura do pico 78%→92%(h4)', '65%→83%/46%→62%' e a decomposição +15,1/-9,9/+13,3 pp NÃO aparecem em nenhum dos 6 scripts nem seus CSVs — nenhum calcula 'captura do pico' (%); só viés absoluto, MAE e R².  
  `busca integral nos 6 scripts + 4 pastas 'saidas/'`
- **[NAO_ENCONTRADO]** 'Autocorrelação explica 91% em h1 e 0% em h12' também não está nos 6 arquivos-alvo. A única referência a autocorrelação no projeto fica em 2026-08-30_grid_completo/README.md e num CSV de 16/08/2026, fora do escopo desta reconstrução.  
  `grep em analises/ (fora dos 6 arquivos designados)`
- **[LIDO_NO_CODIGO]** testar_vetor_calibrado.py compara M0 (núcleo+clima) x M1 (M0+vetor) com merge EXPLÍCITO pareado em [h, data_alvo, real], seguido de Diebold-Mariano (erro absoluto) + Holm sobre 8 comparações (2 perdas x 4 horiz.), α=0,05, só na avaliação (2024+).  
  `testar_vetor_calibrado.py:167-208`
- **[LIDO_NO_CODIGO]** Resultado real: M1 (com vetor) tem MAE menor em 6 de 8 comparações (perde só em h=1); NENHUMA sobrevive a Holm (p_holm=1,0 em todas). É o desfecho 2 pré-declarado ('indício, não achado'), não o desfecho 3 ('M1 não vence M0') chamado de mais provável.  
  `vetor_comparacao.csv; PRE_DECLARACAO.md (vetor) linhas 41-49`
- **[LIDO_NO_CODIGO]** decompor_erro.py roda o protocolo oficial do cenário 1 chamando motor.walk_forward_regressao do próprio pacote (não uma cópia); usa a perda OFICIAL (squared_error), isto é, mede o viés ANTES de qualquer remédio de calibração.  
  `decompor_erro.py:11-16,94-97`
- **[LIDO_NO_CODIGO]** Nem testar_remedios.py nem decomposicao_erro_cenario1/ têm PRE_DECLARACAO.md ou README — só calibrar_quantilico.py e testar_vetor_calibrado.py têm pré-declaração escrita antes de rodar.  
  `listagem de arquivos das 4 pastas de análise`
- **[LIDO_NO_CODIGO]** 'Picos' (critério do alpha e comparação do vetor) são semanas com real>100 — limiar FIXO, não conjunto fixo de eventos; n de picos varia por variante/horizonte (25 na calibração, 39 na avaliação) pois o dropna de cada horizonte corta linhas diferentes.  
  `calibrar_quantilico.py:165,42; calibracao_resumo.csv (n_picos)`

### Escolhas que um pesquisador talvez não espere

- O corte calibração/avaliação usa a DATA-ALVO da previsão, não a data em que a previsão foi feita: uma previsão gerada em 2023 para uma semana de 2024 conta como "avaliação". Deliberado e documentado, mas muda a composição das duas amostras de um jeito não óbvio de cabeça.

- A previsão quantílica (alpha 0,80/0,85) não estima a média — estima um patamar viesado para cima "de propósito" (ressalva na própria PRE_DECLARACAO). Comparar seu R²/MAE lado a lado com o modelo padrão não é comparação entre iguais, mesmo que as tabelas mostrem os dois juntos.

- A guarda de MAE no critério do alpha (não pode piorar >20%) é frouxa: 3 dos 4 alphas testados (0,70/0,80/0,90) TAMBÉM passariam nela. O alpha 0,85 venceu só por ter o menor |viés|, não por ser o único aprovado — a guarda quase não filtrou nada nesta rodada.

- calibrar_quantilico.py e testar_remedios.py comparam variantes SEM merge explícito por data_alvo (diferente de testar_vetor_calibrado.py, que faz merge pareado). Dependem de que o walk-forward gere as mesmas semanas em cada variante — plausível pelo desenho, mas não verificado por assert/merge no código.

- decompor_erro.py mede o viés usando a perda OFICIAL (squared_error) do config — retrata o cenário ANTES de qualquer remédio. Se lido fora de ordem cronológica, pode ser confundido com medição pós-calibração.

### Riscos de validade

- Nenhuma correção de múltiplas comparações na escolha do alpha (calibrar_quantilico.py) nem do remédio (testar_remedios.py) — só o teste do vetor usa Holm. Nos outros dois, "vencedor" é leitura visual de tabela entre 4-5 variantes x 4 horizontes, sem teste estatístico formal.

- Teste B do diagnóstico (log1p) não tem critério de sucesso robusto: o viés PIOROU com log, compatível com qualquer causa (não confirma nem refuta a hipótese do teto isoladamente). A refutação do teto descansa quase toda no Teste A.

- Os números "captura do pico %" e a decomposição em pp citados no PENDENCIAS.md NÃO são reproduzíveis a partir destes 6 arquivos. Se a dissertação atribuir essas cifras a "calibracao_quantilica" ou "decomposicao_erro_cenario1", é atribuição de fonte incorreta.

- O resultado do vetor calibrado (6/8 vitórias de MAE, 0/8 sobrevivendo a Holm) é o desfecho 2 pré-declarado ("indício sem significância"), não o 3 ("M1 não vence M0", chamado "mais provável" na pré-declaração). Se o registro do projeto resumiu como "redundância reforçada" (desfecho 3), supervaloriza a evidência contra o vetor.

- calibrar_quantilico.py e testar_remedios.py não fazem merge pareado por data_alvo entre variantes — assumem, sem verificação explícita, que cada variante rodou sobre as mesmas semanas.

### Divergências código × README

As PRE_DECLARACAO.md de calibracao_quantilica e vetor_no_modelo_calibrado batem com o código — nenhuma divergência relevante nesses dois.

remedios_vies_pico e decomposicao_erro_cenario1 NÃO têm PRE_DECLARACAO.md nem README — não há "o que foi dito" para comparar com "o que foi feito" nessas pastas.

A PRE_DECLARACAO.md do vetor calibrado chama o desfecho 3 ("M1 não vence M0") de "mais provável". O resultado real bateu no desfecho 2 ("M1 vence M0 mas não sobrevive a Holm") — diverge da expectativa registrada, não do código em si.

### Perguntas para o pesquisador

1. Os números "captura 78%→92%" e a decomposição +15,1/-9,9/+13,3 pp vêm de outro script fora destes 6 — sabe qual arquivo os gera e se usa o mesmo desenho pareado por data_alvo?

2. Esperava que o vetor calibrado desse o desfecho 2 (indício sem significância), e não o desfecho 3 (redundância reforçada) que a pré-declaração chamava de "mais provável"?

3. Sabia que testar_remedios.py não tem pré-declaração nem critério automático — o "quantílico venceu" foi leitura sua da tabela, não regra travada antes de rodar?

4. Concorda que o Teste B (log1p piorou) não confirma nem refuta sozinho o teto de extrapolação, e a refutação depende do Teste A?

5. Qual arquivo produz "autocorrelação 91%→0%"? Não está nos 6 que analisei.

### Arquivos lidos

analises/2026-08-30_calibracao_quantilica/*; analises/2026-08-30_remedios_vies_pico/*; analises/2026-08-30_decomposicao_erro_cenario1/*; analises/2026-08-30_vetor_no_modelo_calibrado/*; grep de checagem (não integral) em 2026-08-30_grid_completo/README.md

## R5 — Cadeia do alarme de surto (McNemar)

### Afirmações

- **[LIDO_NO_CODIGO]** Surto = casos_h (casos deslocados -horizonte) >= percentil calculado a CADA passo do walk-forward usando SÓ o treino daquele passo (janela expansiva, sem olhar futuro); não há separação por temporada.  
  `motor/walk_forward.py:96-100`
- **[LIDO_NO_CODIGO]** Treino = TODAS as linhas anteriores ao corte (expansivo, cresce a cada passo, nunca janela fixa); mínimo 104 semanas antes do 1º teste (settings.MINIMO_SEMANAS_TREINO); passo=1 por padrão (testa toda semana).  
  `motor/walk_forward.py:31,96-98; config/settings.py:88`
- **[LIDO_NO_CODIGO]** Classificador é IDÊNTICO nos dois alvos: LGBMClassifier, n_estimators=250, lr=0.05, num_leaves=15, min_child_samples=5, class_weight='balanced'; limiar de decisão FIXO em 0,5 (não calibrado).  
  `config/experimentos/cidade_deteccao_surto.py:58-70; cidade_surto_notificados.py:69-81; motor/walk_forward.py:23,131`
- **[LIDO_NO_CODIGO]** Dois braços de features no Experimento B/notificados: 'so-clima' (autorregressivo+clima+sem_sin/cos) e 'clima+vetor' (idem + vetor); o motor também injeta alvo_sin/alvo_cos (estação da semana-ALVO, não da semana atual) nos dois braços.  
  `pipeline.py:120-131; motor/walk_forward.py:79-84`
- **[LIDO_NO_CODIGO]** 'comparacao' na tabela = merge de resultado_clima × resultado_vetor por (h,data,real), um walk-forward completo por (percentil,horizonte); McNemar roda sobre esse merge.  
  `pipeline.py:145-147,187-192`
- **[LIDO_NO_CODIGO]** Discordante McNemar = so-clima acerta E clima+vetor erra (ou o oposto) NA MESMA semana pós-merge; usa qui-quadrado com correção de continuidade se discordâncias>=25, senão binomial exato.  
  `avaliacao/mcnemar.py:59-84`
- **[LIDO_NO_CODIGO]** O pipeline de CONFIRMADOS (rodar_cidade_deteccao_surto) NÃO aplica Holm internamente — só grava p bruto arredondado a 3 casas; o Holm que sobreviveu em 29/08 (p=0,00108) foi calculado DEPOIS, do zero, por um script à parte.  
  `pipeline.py:203-235 (sem chamada a correcao_multipla); investigar_contradicao_alvos.py:44-63,109-125`
- **[LIDO_NO_CODIGO]** O pipeline de NOTIFICADOS (rodar_cidade_surto_notificados) aplica Holm internamente sobre as 6 comparações (percentil x horizonte) daquele experimento, com p bruto em precisão cheia (não arredondado).  
  `pipeline.py:558-698, chamada a correcao_multipla ~l.663-668`
- **[LIDO_NO_CODIGO]** Corte de maturidade (12 semanas, igual nos 3 scripts) conta a partir da ÚLTIMA semana com caso NÃO-nulo, não do fim físico da tabela — se a fonte atrasar, o corte se desloca para trás.  
  `dominio/surto.py:38-49; cidade_deteccao_surto.py:71; cidade_surto_notificados.py:82; teste_decisivo_alvos.py:47`
- **[LIDO_NO_CODIGO]** Mudança 29/08→30/08 no P90 h=12 confirmados (4x24,p=0,00018 → 9x16,p=0,230): teste_decisivo restringiu a janela a denominador_aproximado==0 E às duas séries de casos presentes na mesma semana, removendo 37 semanas fev-dez/2018 (n 279→242). Só a janela mudou.  
  `teste_decisivo_alvos.py:104-116; saidas/teste_decisivo_mcnemar.csv`
- **[LIDO_NO_CODIGO]** O script investigativo de 29/08 usa uma reimplementação PRÓPRIA e mais simples de 'surto' (percentil expansível, mínimo 52 semanas) só para medir concordância/Jaccard entre as duas séries — não é o classificador testado nem usa o motor de produção.  
  `investigar_contradicao_alvos.py:79-101`
- **[INFERIDO]** Para linhas de treino próximas do corte, o alvo (casos h semanas à frente) pode ter DATA posterior à semana de teste sendo prevista quando h>1 — o treino inclui todas as linhas anteriores por POSIÇÃO, sem filtrar por 'data_alvo <= data_do_teste'.  
  `motor/walk_forward.py:96-99`
- **[INFERIDO]** Cada braço (so-clima, clima+vetor) faz seu próprio dropna nas colunas obrigatórias ANTES do merge; se o vetor tiver NaN numa semana que o clima não tem, essa semana some do braço clima+vetor e é descartada da comparação pareada pelo merge.  
  `motor/walk_forward.py:88-93; pipeline.py:145-147`
- **[LIDO_NO_CODIGO]** teste_decisivo_alvos.py aplica Holm 2x: dentro de cada braço (6 comparações) e sobre os 2 braços juntos (12); o veredito declarado usa o de 12 — nenhuma comparação sobrevive (melhor caso Holm-12=0,053).  
  `teste_decisivo_alvos.py:210-215; PRE_DECLARACAO.md seção 'Correção múltipla'`
- **[LIDO_NO_CODIGO]** O docstring de cidade_surto_notificados.py ainda afirma que a única diferença p/ confirmados é o alvo — mas o próprio projeto já provou (29-30/08) que a janela também mudava a qualidade de medição do vetor.  
  `config/experimentos/cidade_surto_notificados.py:8-10,37-41`

### Escolhas que um pesquisador talvez não espere

- Limiar de decisão FIXO em 0,5 (não calibrado), mesmo com class_weight='balanced' compensando o desbalanceamento no treino.
- Janela de treino EXPANSIVA (usa tudo desde o início), não deslizante — cada passo re-treina do zero com mais dados (daí o custo alto de CPU).
- Modelo recebe a estação do ANO-ALVO (alvo_sin/alvo_cos), não só a atual — sabe em que época cai a semana prevista; legítimo (horizonte é fixo), mas não aparece na lista de features do config.
- Holm tratado DIFERENTE nos dois experimentos oficiais: confirmados só recebe Holm depois, num script à parte; notificados recebe Holm dentro do próprio pipeline. Quem só olha os CSVs pode achar que os dois foram tratados igual.
- teste_decisivo (30/08) roda sobre um SUBCONJUNTO de semanas (denominador exato + duas séries presentes) — os números de "confirmados" em 29/08 e 30/08 não são diretamente comparáveis sem essa ressalva.
- "vetor favorece 9 de 12" no teste decisivo é descritivo, sem p-valor — fácil de ler como evidência de efeito.

### Riscos de validade

- VAZAMENTO TEMPORAL POTENCIAL (walk_forward.py:96-99): treino usa todas as linhas anteriores por POSIÇÃO, sem exigir que a data-alvo (casos_h) de cada linha de treino seja <= à data de teste. Com h=12, ~11 linhas de treino perto do corte têm alvo datado DEPOIS da semana testada — o modelo pode "ver" casos reais de semanas posteriores ao ponto simulado, inflando o resultado mais em h longos.
- DROPNA ASSIMÉTRICO (inferido): so-clima e clima+vetor fazem dropna independente antes do merge; datas sem vetor (comum pré-2018) somem só do braço vetor, afetando a amostra pareada do McNemar.
- MÚLTIPLAS COMPARAÇÕES INCONSISTENTES entre experimentos: confirmados só recebeu Holm post-hoc; notificados recebe Holm no próprio pipeline — um resultado forte circulou sem correção embutida no artefato de produção.
- FRAGILIDADE JÁ CONFIRMADA PELO PROJETO: remover 37 de 279 semanas (13%) fez p sair de 0,00018 para 0,230 (README 30/08) — achado sensível à janela, não efeito estável.
- "9 de 12 favorece vetor" é padrão descritivo (comparações não-independentes, sem pré-declaração) — risco de virar frase de tese sem ser teste.

### Divergências código × README

Nenhuma divergência ESCONDIDA — os READMEs de 29/08 e 30/08 documentam os próprios erros (seção "ERRO DE DESENHO MEU" já assume que a Rodada 1 estava errada).

Divergência RESIDUAL não corrigida: o docstring de config/experimentos/cidade_surto_notificados.py (l.8-10,37-41) ainda diz "todo o resto é idêntico" ao experimento de confirmados, garantindo atribuir a diferença só ao alvo — premissa que o projeto refutou em 29-30/08 (a janela mudava a qualidade do vetor). O README foi corrigido; o docstring da config de produção, não.

### Perguntas para o pesquisador

1. Sabia que o experimento CONFIRMADOS nunca aplica Holm dentro do pipeline — o p corrigido de 29/08 (0,00108) veio de script separado, feito depois?
2. Esperava que o corte de maturidade conte a partir da última semana COM dado (não do fim da tabela)?
3. Quer atualizar o docstring de cidade_surto_notificados.py, que ainda diz "só o alvo muda" após a correção de 30/08?
4. Concorda que "vetor favorece 9 de 12" deve ficar só como hipótese, não virar frase de tese?
5. Quer que eu aprofunde a possível sobreposição treino/alvo em h=12 no walk-forward?

### Arquivos lidos

pipeline.py (l.1-260,540-698); motor/walk_forward.py; dominio/surto.py; config/experimentos/cidade_deteccao_surto.py; cidade_surto_notificados.py; avaliacao/mcnemar.py; correcao_multipla.py; config/settings.py; acesso/fontes.py (l.1-240); 2026-08-29_regeneracao_oficial/investigar_contradicao_alvos.py+README.md; 2026-08-30_teste_decisivo_alvos/teste_decisivo_alvos.py+PRE_DECLARACAO.md+README.md+saidas/teste_decisivo_mcnemar.csv

## R6a — Equivalência clima × vetor (Rodada 2) e janela de treino (Rodada 4)

### Afirmações

- **[LIDO_NO_CODIGO]** SO_CLIMA_PURO/AR usa só as 22 colunas de clima contemporâneas (temp,precip,umid,orvalho,pressao,radiacao,vento,dias_de_chuva) — nenhuma defasagem de clima é criada neste script.  
  `rodada_2_teste_a_serie_longa.py:105-108,267-271`
- **[LIDO_NO_CODIGO]** SO_VETOR_PURO/AR usa vetor contemporâneo + vetor_lag1..4 + vetor_mm4 (5 colunas de memória), assimétrico em relação ao clima que não tem lag algum.  
  `rodada_2_teste_a_serie_longa.py:214-227,272-274`
- **[LIDO_NO_CODIGO]** Na versão 'com_ar' os DOIS lados recebem o mesmo bloco casos_lag1..4+casos_mm4; a diferença fica reduzida ao que sobra depois desse AR forte (MAE cai de ~183 p/ ~72 em h=1).  
  `rodada_2_teste_a_serie_longa.py:275,280-281; CSV linhas 0 e 4`
- **[LIDO_NO_CODIGO]** A margem TOST é 5/10/15% do MAE_SO_CLIMA (não da persistência), calculada do erro observado no próprio teste, não de um valor absoluto fixado antes.  
  `rodada_2_teste_a_serie_longa.py:37,645-646; razão margem/MAE_clima=0,15 exata no CSV`
- **[LIDO_NO_CODIGO]** IC de ΔMAE por bootstrap em blocos de 8 semanas, 2000 reamostras, seed 20260816 — estatística separada do TOST, só para relatar largura do intervalo.  
  `rodada_2_teste_a_serie_longa.py:99-101,520-560`
- **[LIDO_NO_CODIGO]** TOST usa a MESMA variância de longo prazo do DM (gama0 + autocovariâncias até lag h-1), SEM a correção HLN, pois ela só vale p/ H0: diferença=0.  
  `rodada_2_teste_a_serie_longa.py:479-486,498-501`
- **[LIDO_NO_CODIGO]** As '8 combinações' = 2 versões (puro, com_ar) × 4 horizontes; as 4 que fecham ±15% são: puro h1, puro h4, com_ar h1, com_ar h8.  
  `saidas/rodada_2_notificados_resultados_equivalencia.csv, col TOST_margem_15pct_equivalente_a_5pct`
- **[LIDO_NO_CODIGO]** N pareado 587 (h=1) é o tamanho da interseção de datas entre previsões clima e vetor após merge por (data,h,real); cai p/ 584/580/576 em h=4/8/12.  
  `rodada_2_teste_a_serie_longa.py:600-602; CSV col n_semanas_pareadas`
- **[LIDO_NO_CODIGO]** Vantagem do vetor em h=4 (puro): DM-HLN p=0,0332 bruto; com Holm sobre as 8 comparações sobe p/ 0,2657 — nenhuma sobrevive.  
  `rodada_2_teste_a_serie_longa.py:425-457; CSV rodada_2_notificados_resultados_com_holm.csv`
- **[LIDO_NO_CODIGO]** Rodada 4 tem 3 regimes: expansivel_2012, expansivel_2020, deslizante_6anos — todos avaliados nas MESMAS semanas via dropna conjunto sobre as 3 colunas de previsão.  
  `rodada_4_ablacao_janela_treino.py:194-204,207,276-278`
- **[LIDO_NO_CODIGO]** Janela de avaliação começa em 2022-01-02; semanas avaliadas por horizonte: 226(h1)/221(h4)/217(h8)/213(h12).  
  `rodada_4_ablacao_janela_treino.py:58; saidas/rodada_4_ablacao_resumo.csv`
- **[LIDO_NO_CODIGO]** n_treino_mediano em h=1: expansivel_2012=584, expansivel_2020=216, deslizante_6anos=299 semanas — tamanhos de treino bem diferentes, mesma semana de teste.  
  `saidas/rodada_4_ablacao_resumo.csv linha h=1`
- **[LIDO_NO_CODIGO]** rodada_2 NÃO importa motor/walk_forward_pareado.py; monta pareamento por merge próprio pois clima/vetor não são aninhados, diferente do motor do projeto (M0⊆M1).  
  `rodada_2_teste_a_serie_longa.py:15-17; walk_forward_pareado.py:38-41,62-63`
- **[LIDO_NO_CODIGO]** PRE_DECLARACAO.md diz margem TOST = '% do MAE da persistência'; o código usa % do MAE_SO_CLIMA — bases diferentes.  
  `PRE_DECLARACAO.md:123 vs rodada_2_teste_a_serie_longa.py:37,646`
- **[LIDO_NO_CODIGO]** Hiperparâmetros LightGBM e MINIMO_SEMANAS_TREINO=104 da rodada_2 batem exatamente com config do projeto.  
  `rodada_2:84-97,80 vs cidade_regressao.py:31-34, settings.py:88`

### Escolhas que um pesquisador talvez não espere

- **Assimetria de memória:** clima entra só contemporâneo (sem lag); vetor entra com atual+4 lags+média móvel. A "equivalência" não compara estruturas temporais iguais — o vetor tem mais memória por construção, o que pode inflar sua vantagem em h curto.

- **'com_ar' fica quase blindado pelo AR de casos:** casos_lag1-4+mm4 idênticos nos 2 lados fazem MAE cair de ~183 p/ ~72 (h=1). 2 das 4 combinações que "fecham equivalência" são 'com_ar' — a leitura pretendida é clima=vetor SEM ajuda de casos ou COM casos no meio?

- **Margem TOST é relativa e pós-hoc:** é % do próprio MAE_SO_CLIMA medido naquele teste, não um número absoluto fixado antes — um clima pior "compra" margem maior mecanicamente.

- **Rodada 4 tem 3 regimes, não 2** — "expansivel_2020" fica no meio, não citado na pergunta original.

- **Motor próprio, não reuso do projeto:** rodada_2 não usa walk_forward_pareado.py (que assume M0⊆M1); refaz pareamento via merge por interseção pois clima/vetor são conjuntos disjuntos.

- **n_jobs=1 no LightGBM** é só desempenho (documentado), não afeta o resultado.

### Riscos de validade

- **Margem não é fixa em casos absolutos:** é 5/10/15% do MAE_SO_CLIMA medido no PRÓPRIO teste. Clima com desempenho pior naquele horizonte alarga a régua que decide "equivalência" — não é vazamento clássico, mas há circularidade: a fórmula foi pré-declarada, o VALOR não.

- **8 DMs sem correção múltipla planejada** — já mitigado e declarado no README (Holm à parte, 0/8 sobrevivem); não é achado novo, só confirma que "vetor ganha em h curto" é exploratório mesmo.

- **Assimetria estrutural de lags** (clima sem defasagem, vetor com) pode favorecer o vetor em h curto por desenho, não por biologia.

- **Rodada 4 sem teste de significância** (declarado como robustez) — "expansível 2012 vence 3 de 4" é ranking pontual de MAE, sem incerteza quantificada.

- **Nenhum vazamento temporal encontrado:** walk-forward sempre treina com data<corte; sazonalidade-alvo vem do calendário, não do valor futuro.

### Divergências código × README

PRE_DECLARACAO.md:123 diz margem TOST = "% do MAE da persistência". O código (linha 37 do docstring e linha 646, margem=fração*mae_clima) usa % do MAE_SO_CLIMA — confirmado nos CSVs (razão margem/MAE_clima=0,15 exata). README não repete a frase da PRE_DECLARACAO, só diz "margem pré-declarada, sem alteração", dando a entender (incorretamente) que bateu. Fora isso, N, MAE, TOST e Holm citados no README batem com os CSVs gerados pelo código lido.

### Perguntas para o pesquisador

- Você esperava clima SEM lag algum vs vetor com 4 semanas de memória? Isso pode inflar a vantagem do vetor em h curto por desenho.

- Nas 4 combinações "equivalentes", 2 são 'com_ar' (onde o AR de casos já domina o erro) — essa é a leitura que você quer para a tese?

- Você sabia que a margem TOST é % do MAE do clima NAQUELE teste, não um valor fixo entre horizontes?

- Já sabia do 3º regime "expansível 2020" na Rodada 4 (pior dos três quase sempre)?

- A troca margem-da-persistência → margem-do-clima foi decisão consciente ou passou despercebida? Merece uma EMENDA datada, como a Rodada 0 fez.

### Arquivos lidos

rodada_2_teste_a_serie_longa.py (íntegro); rodada_4_ablacao_janela_treino.py (íntegro); PRE_DECLARACAO.md (íntegro); README.md (íntegro); motor/walk_forward_pareado.py (íntegro); config/experimentos/cidade_regressao.py e config/settings.py (grep); saidas/rodada_2_notificados_resultados_equivalencia.csv, rodada_2_notificados_resultados_com_holm.csv, rodada_4_ablacao_resumo.csv (lidos via pandas).

## R6b — Camada espacial (zonas sintéticas, ranking)

### Afirmações

- **[LIDO_NO_CODIGO]** Zonas sintéticas vêm de K-Means sobre a posição média (latitude/longitude) de cada armadilha — não usa a série temporal de mosquito nem casos. k=8 e k=16, semente 42, mesma construção nos dois scripts.  
  `teste_b_sinal_espacial.py:351-355; rodada_3_ranking_zonas.py:121-129`
- **[LIDO_NO_CODIGO]** O 'alvo suavizado' é a média móvel de 4 semanas (mm4/'dens') da densidade (fêmeas/armadilhas inspecionadas) por zona, com mínimo de 2 semanas não-nulas na janela.  
  `teste_b:112-114; rodada_3:222-226`
- **[LIDO_NO_CODIGO]** O que o modelo (LightGBM) prevê no ranking é a densidade suavizada da MESMA zona h semanas à frente (shift(-horizonte)) — não é casos, surto nem valor bruto.  
  `rodada_3_ranking_zonas.py:320-323`
- **[LIDO_NO_CODIGO]** Ranking = Spearman entre o vetor de previsões e o vetor de valores reais de todas as zonas elegíveis na mesma semana-alvo (comparação transversal, não ranking explícito calculado à parte).  
  `rodada_3_ranking_zonas.py:252-267, 359-369`
- **[LIDO_NO_CODIGO]** Baseline 'persistência' = a densidade suavizada de HOJE (semana de origem) repetida como previsão para t+h, sem nenhum decaimento ou ajuste de tendência.  
  `rodada_3_ranking_zonas.py:352`
- **[LIDO_NO_CODIGO]** Baseline 'climatologia' = média histórica de densidade da zona em semanas dentro de ±1 semana (circular) da semana-alvo; se <3 zonas tiverem dado nessa janela, cai para a média geral da zona.  
  `rodada_3_ranking_zonas.py:270-291`
- **[LIDO_NO_CODIGO]** No Teste B, o Spearman de persistência espacial é entre o ranking de mm4 na semana t e em t+lag (lag=4 ou 8), mediana sobre semanas com ≥5 grupos válidos nos dois momentos.  
  `teste_b_sinal_espacial.py:145-170`
- **[LIDO_NO_CODIGO]** Split-half: para cada grupo-semana com ≥8 armadilhas, divide as armadilhas aleatoriamente em 2 metades e correlaciona (Pearson) a densidade das metades, bruta e suavizada (mm4); 50 sorteios, mediana reportada.  
  `teste_b_sinal_espacial.py:173-243`
- **[LIDO_NO_CODIGO]** Elegibilidade de zona/bairro exige ≥10 armadilhas em ≥50% das semanas da GRADE COMPLETA (denominador é o total de semanas do período, não só as semanas em que o grupo aparece).  
  `teste_b:84-99; rodada_3:161-190`
- **[LIDO_NO_CODIGO]** O modelo é um único LightGBM treinado com TODAS as zonas-semana agrupadas (pooled); a zona entra como feature numérica ordinal (índice de enumeração 0..k-1), não one-hot.  
  `rodada_3_ranking_zonas.py:80-89, 246-247, 347-349`
- **[LIDO_NO_CODIGO]** Walk-forward usa janela expansiva (treina com tudo antes da semana de origem), com mínimo de 104 semanas (2 anos) de histórico antes do primeiro teste, passo de 1 semana.  
  `rodada_3_ranking_zonas.py:56-58, 338-341`
- **[LIDO_NO_CODIGO]** A posição média de cada armadilha usada no K-Means é calculada sobre TODO o período 2019-2026 de uma vez só — não é recalculada dentro de cada corte temporal do walk-forward.  
  `rodada_3_ranking_zonas.py:121-126; teste_b:351-353`
- **[LIDO_NO_CODIGO]** A decomposição de variância do Teste B roda só no subconjunto de semanas 100% completas (todo grupo elegível com mm4 não-nulo simultaneamente), reduzindo a amostra de semanas nessa métrica específica.  
  `teste_b_sinal_espacial.py:255-262`
- **[INFERIDO]** features_bairro.py é um caminho paralelo (granularidade bairro administrativo, com vizinhança via NearestNeighbors) não usado pelos dois scripts de zona sintética — serve só para contextualizar a diferença bairro × zona.  
  `features_bairro.py:1-20, 293-326`

### Escolhas que um pesquisador talvez não espere

- **Zona é puramente geográfica e fixa no tempo**: k-means usa só a posição média histórica da armadilha, nunca a densidade de mosquito. Zonas não se adaptam se uma armadilha mudar de local ao longo dos anos.

- **"Ranking previsto" não é um ranking explícito**: o script compara VALORES de densidade previstos entre zonas na mesma semana via Spearman — o modelo nunca "sabe" que compete em ordem.

- **Persistência é ingênua por design**: copia o valor de hoje. É proposital (o que a vigilância já faz de graça), mas favorece persistência em horizontes curtos por captar bem a autocorrelação.

- **Zona entra no LightGBM como número ordinal** (0,1,2...): árvores lidam bem tecnicamente, mas o código não tem significado de distância — zona 3 não é "mais parecida" com zona 4 do que com zona 15.

- **Denominador aproximado de 2012-2018** (em features_bairro.py) não afeta a camada espacial: teste B e Rodada 3 filtram `inspecao_realizada==True`, restringindo tudo a 2019+.

### Riscos de validade

- **Coordenada da armadilha usa todo o período de uma vez**: o k-means roda sobre a posição média calculada com dados de 2019-2026 inteiros, antes de qualquer corte do walk-forward. Como a posição física não muda, não vaza o ALVO, mas usa dado de todo o período (inclusive futuro) para fixar a estrutura de zonas usada em previsões de anos anteriores. Risco baixo, não testado no código.

- **Múltiplas comparações não corrigidas na Rodada 3**: 8 combinações k×h comparadas contra persistência sem correção formal — mas a regra é binária/pré-declarada por combinação (mediana modelo > mediana persistência), não teste de hipótese com p-valor, então o risco é menor que nas Rodadas 1/2 (que usam Holm).

- **Autocorrelação temporal das ~228-235 semanas testadas**: Spearman é calculado semana a semana e resumido em mediana; as semanas não são independentes (mm4 tem memória de 4 semanas, há sazonalidade). Válido como descritivo, mas não sustentaria teste de hipótese formal sem ajuste — o código não faz esse ajuste, e nem reporta p-valor aqui.

- **Poucas zonas em k=8**: com 7-8 zonas elegíveis, Spearman é sensível a poucas trocas de posição — explica a queda rápida de h=1 para h=8.

### Divergências código × README

Nenhuma divergência de fundo entre o README da Rodada 3 e o código lido. Uma nuance que o README não deixa explícita: `codigo_zona` no LightGBM é um índice ordinal (0..k-1) da enumeração das zonas, não one-hot — o README só diz "a zona entra como número", sem detalhar a forma.

### Perguntas para o pesquisador

- A zona entra como código ordinal (0..k-1), não one-hot — isso pode sugerir "distância" entre zonas que não existe fisicamente. Era o esperado?

- As zonas (k-means) usam só a posição geográfica média de TODO o período 2019-2026, nunca a densidade de mosquito, e são fixas (não recalculadas por corte temporal). Sabia disso?

- Persistência = "densidade de hoje vale para t+h", sem ajuste de tendência. Corresponde ao que você tinha em mente?

- O critério é a ORDEM relativa (Spearman), não o erro absoluto de densidade. Você também esperava ver MAE como critério secundário?

### Arquivos lidos

teste_b_sinal_espacial.py (integral, 404 linhas); rodada_3_ranking_zonas.py (integral, 492 linhas); README.md da pasta 2026-08-29 (integral, seção Rodada 3 e contexto geral); features_bairro.py (integral, 404 linhas, só para contraste bairro×zona).

## V1 — Verificação: vazamento na seleção de clima

**Veredito: PARCIAL** — O código não tem trava por data (usa fração de linhas, não corte temporal) — mas HOJE, por coincidência do tamanho da série, o corte cai em nov/2022, antes de 2024+, então não há vazamento no ranking atual; o risco é estrutural, não realizado.

### Evidência

(a) selecao_features.py:100-118, chamada por pipeline.py:270-279 e rodar_grid.py:88-95: não existe filtro de data. É `n_treino = int(len(dados_validos) * fracao_treino)` sobre a série ordenada por data inteira (LIDO_NO_CODIGO). fracao_treino_selecao=0.60 fixo em cidade_regressao.py:136 (e nos outros 3 configs). (b) Calculado 1x só — em rodar_grid.py, dentro de montar_dados_e_conjuntos(), chamada uma única vez em main() antes do loop das 120 células (linha 164); o corte calibração/avaliação do PRE_DECLARACAO.md (2023-12-31) NÃO é aplicado aqui, só depois, na escolha da config vencedora. O PRE_DECLARACAO.md não menciona esta etapa nem o risco. (c) Sim — features.py:150-152 cria y_h=casos.shift(-horizonte) (o alvo futuro), e selecao_features.py:113 faz `modelo.fit(treino[features], treino['y_h'])`. (d) 42 candidatas, 6 escolhidas (config.valores_k tem 6 e 8, mas rodar_grid.py:96 fixa `.head(6)`). (e) Rodei a função original (script scratchpad): treino real vai de 2018-03-18 até 2022-11-13/27 conforme h — ANTES de 2024, sem tocar no período de avaliação. Rodei também restringindo a tabela a <=31/12/2023 antes da mesma fração: top-6 muda bastante (só 2 de 6 colunas repetem: temp_media_lag4 e ~umid_media_lag1). Isso mostra que o ranking é sensível/instável ao recorte, não que hoje há vazamento de futuro.

### Números

tabela_final: 725 linhas, 2012-09-23 a 2026-08-09. Clima válido (sem NaN) só a partir de 2018-03-18 (411 linhas) — contradiz o registro de 29/08 de "727 semanas" de clima; parece que o config cidade_regressao ainda não reflete a recaptura. n_treino=246/244/242 (h=1/4/8), terminando em 2022-11-13~27. Top-6 original: temp_media_lag4, umid_media, temp_media_lag3, temp_max, pressao_media_lag3, pressao_media_lag4 (bate 100% com o citado no prompt). Top-6 com corte <=2023-12-31: radiacao_max, pressao_min, orvalho_media_lag4, orvalho_media_lag1, temp_media_lag4, umid_media_lag1.

### Impacto provável nos resultados

Nas métricas atuais (grid de 30/08), o vazamento de 2024+ NÃO aconteceu — o corte real ficou em 2022, longe da janela de avaliação. O risco é de projeto, não de resultado publicado: como o corte é por fração (não por data), à medida que a série cresce, esse ponto avança e um dia ultrapassa 2024-01-01 sem alarme no código. Achado mais forte que o hipotetizado: o ranking de clima é instável — recortar a série em 2023 muda 4 das 6 colunas escolhidas, enfraquecendo a alegação de que "estas 6 são as que mais importam" como fato estável.

### O que faltou verificar

Não confirmei por que clima só fica sem NaN a partir de 2018-03 no tabela_final atual (PENDENCIAS de 29/08 diz recaptura até 2012) — pode ser tabela desatualizada ou lag comendo linhas iniciais. Não testei os outros 3 configs (com_enso, sem_enso, diebold) nem refiz o grid completo com as 6 colunas alternativas.

## V2 — Verificação: vazamento em features e definição de surto

**Veredito: PARCIAL** — H1 refutada nos mecanismos citados mas achei um vazamento novo na seleção de clima; H2 refutada (limiar de surto é sempre local ao treino); H3 confirmada como descrito (é rótulo, não vazamento).

### Evidência

H1 REFUTADA nos mecanismos citados: lags só shift(+1..+4) passado (features.py:96-102); alvo_sin/cos só calendário da semana alvo, sem dado real (features.py:151-155); casos_est/nowcasting não aparece em nenhum lugar do código (grep vazio) — fontes.py:39-40,167-207 sempre usam 'casos' bruto. ACHADO NOVO (não citado na hipótese, mas achado inspecionando selecao_features.py): a seleção das colunas de clima roda 1 VEZ usando os primeiros 60% da série inteira (selecao_features.py:100-117, fracao_treino=0.60) e essa MESMA lista é reusada em TODO o walk-forward (rodar_grid.py:80-102; pipeline.py:272-278 e ~370-380). O walk-forward testa a partir da semana 104, mas a seleção usa dado até ~semana 425/708 — os testes iniciais usam colunas escolhidas com dado que, naquele ponto, ainda era futuro. É vazamento na ETAPA DE SELEÇÃO de colunas, não no valor de cada feature.

H2 REFUTADA: limiar de surto = np.percentile(treino['casos_h'], percentil), calculado só com o treino de CADA passo, janela expansiva (walk_forward.py:99). surto.py não tem nenhuma função de percentil. Confirmado nos 4 pontos de chamada.

H3 CONFIRMADA (é rótulo, não vazamento): aplicar_corte_maturidade (surto.py:36-49) usa como referência a última semana COM caso (não a última linha da tabela) e apaga 'casos' das semanas acima de referência−12.

### Números

semanas_corte_maturidade=12 (cidade_regressao.py:132; teste_decisivo_alvos.py:49). fracao_treino_selecao=0.60 (cidade_regressao.py:136). minimo_semanas_treino=104 (cidade_regressao.py:137). Série total ~708 semanas (PENDENCIAS 30/08) → fatia de seleção ≈425 semanas; walk-forward testa da semana 104 até 708, passo=2 → cerca de 320 dos ~604 passos testados (≈53%) caem antes da semana 425, logo dentro da janela "contaminada" pela seleção. LAGS_SEMANAS=[1,2,3,4] (features.py:28). horizontes_selecao_clima=(1,4,8) (cidade_regressao.py:134). valores_k=(6,8) (cidade_regressao.py:135); grid usa head(6) (rodar_grid.py:96).

### Impacto provável nos resultados

REGRESSÃO (grid 30/08): MAE/R2 podem estar levemente otimistas nos primeiros ~40-50% dos passos de teste, pois parte das colunas de clima foi escolhida com semanas ainda futuras naquele ponto — efeito indireto (só afeta QUAIS colunas entram, não os valores), tende a ser pequeno, não explica o padrão geral por horizonte.

SURTO (McNemar/Holm/deteccao_surto/surto_notificados): nenhum viés encontrado — limiar e treino são sempre expansivos e locais ao passo. Achados de 29-30/08 (equivalência clima×vetor, calibração) não são explicados por vazamento aqui.

### O que faltou verificar

Não medi o tamanho do efeito da seleção-de-clima antecipada (rodar sem essa etapa e comparar por posição do teste). Não abri por completo walk_forward_regressao.py/walk_forward_pareado.py p/ confirmar o mesmo padrão. Não conferi se as 23 semanas reprocessadas da NASA caem na fatia de seleção.

## V3 — Verificação: viés de pareamento M0 × M1 no grid

**Veredito: PROBLEMA_CONFIRMADO** — Confirmado: comparar o MAE "próprio" de M0 (109 semanas) com o de M1 (102 semanas) não é justo — só restringir M0 às mesmas data_alvo de M1 já muda o MAE em -18,5% no h=1 e +5,9% no h=12, passando o limiar de 5% pedido.

### Evidência

rodar_grid.py:44 define FIM_DA_CALIBRACAO=2023-12-31, mas NUNCA é usado no arquivo (grep confirma) — quem gera a coluna "periodo" de grid_resumo.csv não é rodar_grid.py. Reproduzi com a mesma constante e a convenção usada em analises/2026-08-30_vetor_no_modelo_calibrado/testar_vetor_calibrado.py:161-163 (INFERIDO, não do arquivo pedido): periodo="avaliacao" quando data_alvo > FIM_DA_CALIBRACAO. Âncora bateu: hist_gradient_boosting|quantil_0.80|M0|h=1 MAE=116,0821 n=109 e lightgbm|padrao|M1|h=12 MAE=196,7599 n=102, idênticos ao grid_resumo.csv.
Captura do pico (passo 3): NAO_ENCONTRADO — rodar_grid.py:43 define LIMITE_PICO=100 mas 0 ocorrências da string "pico" no corpo; pulei conforme instrução.
7 data_alvo só em M0 (h=4): 26/05, 02/06, 09/06 (=origens 28/04,05/05,12/05/2024 +28d, a enchente) e mais 06/16, 06/23, 06/30, 07/07/2024 (propagação de lag), reais = 520/199/263/277/194/89/22 casos.

### Números

h=1: MAE_M0 116,08→94,64 (Δ-18,47%) | MAE_M1=101,27 | R²_M0 0,8728→0,9075 | R²_M1=0,8830
h=4: MAE_M0 188,62→187,72 (Δ-0,48%) | MAE_M1=168,40 | R²_M0 0,7211→0,7345 | R²_M1=0,7790
h=8: MAE_M0 175,53→182,05 (Δ+3,72%) | MAE_M1=184,04 | R²_M0 0,7468→0,7435 | R²_M1=0,7236
h=12: MAE_M0 202,28→214,32 (Δ+5,95%) | MAE_M1=179,65 | R²_M0 0,6809→0,6740 | R²_M1=0,7579
(Δ = MAE_M0_intersecao vs MAE_M0_próprio; n_próprio=109, n_interseção=n_M1=102 em todos os h)

### Impacto provável nos resultados

O viés muda de sinal por horizonte: em h=1 excluir as semanas da enchente MELHORA M0 (-18,5%), sugerindo que parte da vantagem aparente do vetor em curto prazo é artefato da amostra desemparelhada, não do vetor. Em h=8 e h=12 o efeito é pequeno/moderado e no sentido oposto (M0 piora um pouco na interseção), então a comparação nesses horizontes é mais confiável. Recomendação: qualquer conclusão "M1 vence M0" deve ser recalculada na interseção de data_alvo, especialmente perto da enchente de 2024.

### O que faltou verificar

Não encontrei no projeto o script que gera grid_resumo.csv/grid_ranking_completo.csv (grep por "grid_resumo" e "grid_previsoes_parciais" só retorna rodar_grid.py e o log) — a definição de "periodo" foi inferida de script irmão, não confirmada linha-a-linha no gerador real. Captura de pico não verificável (ausente em rodar_grid.py).
