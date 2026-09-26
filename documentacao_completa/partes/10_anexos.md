# Anexos

## Anexo A — Glossário e onde cada conceito é definido

Este índice existe para consulta pontual. A definição completa, com fórmula e exemplo numérico, está na
parte indicada.

### Termos de epidemiologia

| Termo | Em uma linha | Definido em |
|---|---|---|
| **Vetor** | O organismo que transporta o agente infeccioso entre hospedeiros — aqui, o mosquito *Aedes aegypti* | Parte 1.1 |
| **Sorotipo** | Uma das quatro variantes do vírus da dengue; a imunidade a uma não protege contra as outras | Parte 1.1 |
| **Endêmico** | Doença que circula de forma contínua e esperada numa população | Parte 1.2 |
| **Caso notificado** | Caso suspeito registrado no sistema, antes de qualquer confirmação laboratorial | Parte 3.3 |
| **Caso provável** | Caso suspeito que atende à definição clínica, sem descarte laboratorial | Parte 3.3 |
| **Caso confirmado** | Caso com confirmação laboratorial ou por critério clínico-epidemiológico | Parte 3.3 |
| **Município de notificação × de residência** | Onde o caso foi registrado × onde a pessoa mora; o projeto usa notificação | Parte 3.3 |
| **Semana epidemiológica** | Unidade padronizada de tempo da vigilância, que não coincide com a semana do calendário | Parte 2.1 |
| **Incidência** | Casos novos por unidade de população, em geral por 100 mil habitantes | Parte 7.2 |
| **Canal endêmico** | Faixa do que se considera normal, construída a partir do histórico de anos anteriores | Parte 7.4 |
| **Índice de fêmeas por armadilha** | Média de fêmeas de *Aedes aegypti* capturadas por armadilha vistoriada | Parte 3.1 |

### Termos de modelagem e estatística

| Termo | Em uma linha | Definido em |
|---|---|---|
| **Série temporal** | Sequência de observações ordenadas no tempo | Parte 2.1 |
| **Horizonte** | Quantas semanas à frente a previsão é feita | Parte 2.2 |
| **Data de origem × data-alvo** | Quando a previsão é feita × a semana que ela descreve | Parte 2.2 |
| **Janela deslizante** (*walk-forward*) | Simular o uso real: prever, receber o valor verdadeiro, avançar | Parte 2.3 |
| **Vazamento temporal** | Usar no treino informação que não existiria na data da previsão | Parte 2.3 |
| **Árvore de regressão** | Modelo que divide os dados em grupos e prevê um valor constante por grupo | Parte 2.4 |
| ***Boosting*** | Conjunto de árvores em que cada uma corrige o erro das anteriores | Parte 2.4 |
| **Extrapolação** | Prever fora do intervalo de valores visto no treino; árvores não fazem | Parte 2.4 |
| **Erro absoluto médio** | Média do tamanho dos erros, sem considerar o sinal | Parte 2.5 |
| **Coeficiente de determinação** | Quanto da variação dos dados o modelo explica | Parte 2.6 |
| **Quantil** | O valor abaixo do qual cai uma dada fração das observações | Parte 2.7 |
| **Perda quantílica** | Função de custo que penaliza assimetricamente subestimar e superestimar | Parte 2.8 |
| **Intervalo de previsão** | Faixa dentro da qual o valor real deveria cair com dada frequência | Parte 2.10 |
| **Cobertura** | Quantas vezes o valor real de fato caiu dentro do intervalo | Parte 2.10 |
| **Escore de intervalo ponderado** | Métrica que avalia a distribuição prevista inteira, não só um número | Parte 2.11 |
| **Matriz de confusão** | Tabela dos quatro resultados possíveis de uma classificação binária | Parte 2.12 |
| **Sensibilidade** | Fração dos eventos reais que o alarme pegou | Parte 2.12 |
| **Precisão** | Fração dos alarmes disparados que eram eventos reais | Parte 2.12 |
| **Índice de Youden** | Sensibilidade mais especificidade menos um; resume o desempenho num número | Parte 2.12 |
| **Hipótese nula** | A afirmação de que não há diferença, que o teste tenta refutar | Parte 2.13 |
| **Valor-p** | A chance de observar um resultado tão extremo se a hipótese nula fosse verdadeira | Parte 2.13 |
| **Teste pareado** | Comparação feita observação a observação, na mesma data | Parte 2.13 |
| **Teste de McNemar** | Teste para classificação binária pareada; usa só os casos em que as regras discordam | Parte 2.13 |
| **Correção de Holm** | Procedimento que ajusta os valores-p quando vários testes são feitos juntos | Parte 2.14 |
| **Correlação serial** | Quando observações próximas no tempo se parecem, violando independência | Parte 2.15 |
| **Reamostragem por blocos** | Bootstrap que sorteia trechos contíguos, preservando a correlação serial | Parte 2.15 |
| **Viés × variância** | Erro sistemático numa direção × dispersão em torno do valor certo | Parte 2.16 |
| **Hiperparâmetro** | Ajuste escolhido antes do treino, que o modelo não aprende sozinho | Parte 2.17 |
| **Busca aleatória** | Sortear combinações de hiperparâmetros em vez de testar todas | Parte 2.17 |
| **Régua** (linha de base) | Regra simples, sem aprendizado, usada como padrão de comparação | Parte 4.15 |

---

## Anexo B — Índice das análises do repositório

Cada pasta está em `analises/` e contém, quando aplicável, pré-declaração, código, registro de execução,
certificação independente e emendas datadas.

### As análises que sustentam os números centrais deste documento

| Pasta | O que produziu |
|---|---|
| `2026-09-13_correcao_vazamento_treino` | A correção do vazamento temporal e o custo de **+52%** de erro |
| `2026-09-13_metrica_de_alarme` | As métricas de alarme por horizonte |
| `2026-09-25_regua_regras_simples` | As réguas e a constatação de que a sazonal vence em 2 e 3 meses |
| `2026-09-25_alarme_contra_canal_endemico` | O alarme contra as regras e contra o canal, com McNemar e Holm |
| `2026-09-25_limiar_oficial_de_surto` | Os quatro estágios do Plano Municipal e o adendo do Quadro 1 |
| `2026-09-25_busca_de_hiperparametros` | As 120 configurações |
| `2026-09-26_calibracao_por_faixa` | A cobertura por faixa e a largura do intervalo contra o erro |
| `2026-09-26_wis_na_tabela_restaurada` | O escore de intervalo ponderado na tabela oficial |
| `2026-09-26_varredura_limiar_de_decisao` | O limiar de decisão, o estágio Alerta e o bloco-bootstrap |
| `2026-09-26_transformacao_de_escala` | O resultado negativo de raiz e logaritmo |
| `2026-09-26_banca_adversarial` | A crítica aos três argumentos |
| `2026-09-26_ficha_da_silva_2026` | A ficha do estudo da mesma cidade |
| `2026-09-26_limiar_para_serie_curta` | Porto Rico, série curta e a aceleração de transmissão |

### Demais análises, em ordem cronológica

`2026-08-16_direcionamento_tese` · `2026-08-29_regeneracao_oficial` ·
`2026-08-29_rodadas_notificados_zonas` · `2026-08-30_alvo_e_features_infodengue` ·
`2026-08-30_calibracao_quantilica` · `2026-08-30_decomposicao_erro_cenario1` ·
`2026-08-30_features_longo_prazo` · `2026-08-30_grid_completo` · `2026-08-30_remedios_vies_pico` ·
`2026-08-30_teste_decisivo_alvos` · `2026-08-30_teste_focado_h12` ·
`2026-08-30_vetor_no_modelo_calibrado` · `2026-09-13_auditoria_mecanica_resultados` ·
`2026-09-13_janela_treino_casos` · `2026-09-21_limpeza_dados_para_envio` ·
`2026-09-23_bateria_noturna` · `2026-09-23_janela_de_lag` · `2026-09-25_atualizacao_dados_2026` ·
`2026-09-25_bateria_formulacao_do_alvo` · `2026-09-25_catalogo_modelos_prontos` ·
`2026-09-25_comparacao_direta_literatura` · `2026-09-25_modelos_de_fundacao` ·
`2026-09-25_notificacoes_como_alvo` · `2026-09-25_novas_fontes_oficiais` ·
`2026-09-25_sarima_lasso_ensemble` · `2026-09-25_segunda_bateria_noturna` ·
`2026-09-25_varredura_literatura`

### Documentos vivos do repositório

| Documento | O que responde |
|---|---|
| `CLAUDE.md` | Onde fica o quê, e o que nunca se faz |
| `PENDENCIAS.md` | O que está em aberto e quem destrava |
| `ESTADO.md` | O que o sistema é hoje |
| `HISTORICO_DE_TESTES.md` | O que já foi perguntado, medido e concluído |

---

## Anexo C — Referências

### Artigos e documentos usados

1. **da Silva, A. A.; Ferreira, Á. G. A.; Lourenço, J.; Cupertino de Freitas, A.** (2026). *Climate-driven
   spatiotemporal dynamics of Aedes infestation and dengue transmission in Porto Alegre.* Preprint no
   medRxiv, 02/04/2026. DOI 10.64898/2026.03.31.26349860.
   ⚠️ **Não revisado por pares.** Estudo da mesma cidade e da mesma rede de armadilhas.
2. **Centers for Disease Control and Prevention** (2025). *Dengue Outbreak and Response — Puerto Rico,
   2024.* Morbidity and Mortality Weekly Report, mm7405a1, 20/02/2025. Lido via PMC12370255.
3. **Dengue epidemic alert thresholds, a tool for surveillance and epidemic detection.* Preprint no
   medRxiv, DOI 10.1101/2024.10.22.24315684.
   ⚠️ **Texto completo não lido** — acesso bloqueado (erro 403). Usado apenas pelo que o item 2 relata.
4. **Bracher, J.; Ray, E. L.; Gneiting, T.; Reich, N. G.** (2021). *Evaluating epidemic forecasts in an
   interval format.* Origem do escore de intervalo ponderado usado neste trabalho.
5. **Chernozhukov, V.; Fernández-Val, I.; Galichon, A.** (2010). *Quantile and probability curves without
   crossing.* Origem do reordenamento de quantis cruzados.
6. **Bergstra, J.; Bengio, Y.** (2012). *Random search for hyper-parameter optimization.* Origem da regra
   de 60 sorteios usada na busca de hiperparâmetros.
7. Artigo sobre **aceleração de transmissão**, lido na íntegra via PMC13228775. Regra da razão entre média
   móvel de 4 e de 26 semanas.
8. **Nature Communications** (2024), s41467-024-48465-0. Limiares fixos de incidência em área de invasão
   da dengue.
9. **Chen, Y. et al.** (2020), lido via PMC7318238. Previsão de dengue em Singapura.
10. **Secretaria Municipal de Saúde de Porto Alegre** (dezembro de 2025). *Plano Municipal de Contingência
    de Arboviroses 2026.* Quadro 1, página 15.

### ⚠️ Afirmações que NÃO devem ser citadas como fato

Estas apareceram em buscas mas **não** foram confirmadas em fonte primária legível, e por isso não
sustentam afirmação neste documento nem fora dele:

- O limiar oficial de epidemia do Ministério da Saúde (as buscas retornaram 100 e 300 por 100 mil
  habitantes, sem documento primário acessível).
- A janela histórica exata que o InfoDengue usa em produção (as fontes divergiram entre 10, 14 e "de 3 a
  16 anos").
- O texto completo do preprint do método de Porto Rico.

---

## Anexo D — Índice das fórmulas

| Fórmula | Para que serve | Parte |
|---|---|---|
| Erro absoluto médio | Medir o tamanho típico do erro | 2.5 |
| Coeficiente de determinação | Medir quanto da variação foi explicada | 2.6 |
| Perda quantílica | Treinar o modelo com penalidade assimétrica | 2.8 |
| Razão de penalidade τ/(1−τ) | Traduzir o quantil em custo relativo dos dois erros | 2.8 |
| Equivalência quantil ↔ probabilidade | Fundamentar o uso da previsão como alarme | 2.9 |
| Cobertura de intervalo | Verificar se a incerteza declarada é honesta | 2.10 |
| Escore de intervalo | Avaliar um nível de intervalo | 2.11 |
| Escore de intervalo ponderado | Avaliar a distribuição prevista inteira | 2.11 |
| Sensibilidade, especificidade, precisão | Avaliar o alarme | 2.12 |
| Índice de Youden | Resumir o alarme num número | 2.12 |
| Teste de McNemar exato | Comparar duas regras de alarme pareadas | 2.13 |
| Correção de Holm | Ajustar os valores-p de vários testes | 2.14 |
| Reamostragem por blocos móveis | Corrigir o valor-p sob correlação serial | 2.15 |
| Índice de fêmeas por armadilha | Medir a presença do vetor | 3.1 |
| Conversão de incidência em casos por semana | Traduzir os estágios do plano municipal | 7.2 |
| Captura do pico | Medir a subestimação da magnitude das epidemias | 8.3 |

---

## Anexo E — Estado do documento

**Escrito em 26/09/2026.** Reflete o repositório até o commit daquela data.

**Como foi produzido:** a arquitetura, os números canônicos e as Partes 0, 1 e os Anexos foram escritos
pelo orquestrador; as Partes 2 a 9 foram escritas em paralelo por oito autores independentes, cada um
recebendo o mesmo conjunto de números verificados e a instrução de reportar divergência em vez de
corrigir sozinho. Em seguida o documento passou por uma conferência número a número contra os arquivos de
origem.

**Divergências encontradas durante a produção e corrigidas:**

1. 🔴 **Erro nos números canônicos fornecidos aos autores.** O informe dizia que a variante de alvo em
   logaritmo perdia **23,0%** para o controle em horizonte de 12 semanas. O número correto é **9,9%**
   contra o controle; os 23,0% são a diferença contra a **régua sazonal**, que é outro comparador. O autor
   da Parte 4 detectou, reportou e usou o número correto. Corrigido em todo o documento.
2. **Diferença de 0,1 no erro em 12 semanas** entre o painel publicado (278,7) e o recálculo (278,8).
   Ambos aparecem, com a origem de cada um.
3. **O tamanho da família de correção múltipla** no evento de 100 casos foi reconstruído numericamente
   por um dos autores, e confere: são **16** testes.

⚠️ **O que este documento não cobre:** a camada espacial por bairros, a previsão do próprio vetor como
alvo e os resultados anteriores a 16/08/2026, que foram em grande parte refeitos após a correção do
vazamento temporal de 13/09/2026.
