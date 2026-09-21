# PENDENCIAS — fila viva do projeto

> Leitura de 3 minutos. Este arquivo é `@importado` em toda sessão, então **tamanho é custo**: teto de
> ~100 linhas, item de 1 a 2 linhas, zero detalhe de mecânica.
>
> Retrato do sistema: [ESTADO.md](ESTADO.md) · O que já foi testado e por quê:
> [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md) · Eixo fino: `git log`.
>
> Status: ✅ resolvido · ⏳ em aberto · 🚫 descartado (com data e quem decidiu).
> **Regra de 29/08/2026:** não existe item "aguarda o orientador". Método é decisão nossa,
> pré-declarada por escrito antes de rodar.

---

## 🔴 SEMINÁRIO DE ANDAMENTO — prazo curto

Definido na reunião de 21/09/2026 com o orientador.

- **Preencher título, resumo, palavras-chave e enquadramento** no sistema do PPGC, para ele agendar a
  banca (provável: Mariana e Anderson). ⚠️ O PDF do trabalho é **opcional** — ele disse para esquecer.
- **Slides de até 10 minutos**: problema, importância, metodologia, resultados, próximos passos. O
  **último slide é de direcionamentos**, com o que saiu da reunião. Ideal até o fim de semana.
- ⚠️ **Escopo do seminário é SÓ DENGUE.** As outras arboviroses ficam para depois. Instrução direta
  dele: não chegar na apresentação dizendo "não teve correlação com mosquito ou clima".
- **Dar push no site + criar uma página-roteiro** dizendo onde os professores clicam e o que veem. Ele
  vai mandar o link para **Mariana e Rodrigo Mansilha**, com o Vinicius em cópia.
- **Enviar os dados de mosquito** a ele, sem nome, telefone e endereço.
- **Enviar a lista de modelos** usados, para ele conferir sobreposição com o Bruno.

**Depois do seminário a pesquisa CONGELA** e o foco passa a ser o artigo para periódico.

---

## ⏳ Destrava com o VINICIUS

- **Escolher o eixo da tese.** A de 29/08 caiu em 13/09; o orientador propôs outra em 21/09. Candidatos
  e ressalvas medidas em [ESTADO.md](ESTADO.md) §4.

- **Automatizar a raspagem** — hoje 100% manual. Em 2026 a raspagem é a única fonte, então uma semana
  perdida é irrecuperável.

---

## ⏳ Decisões NOSSAS a pré-declarar

- **Recorte da tese** — depende do eixo acima. Redigir a pré-declaração formal (hipóteses, métricas,
  correção múltipla) **antes** de rodar qualquer coisa nova.

- **Alvo da predição**: abundância do vetor (letra do PEP) × casos (o que o código faz). Aberto desde
  jun/2026. ⚠️ O PEP declara o vetor; a direção atual prevê casos. É inversão do objeto, não ajuste.

- **Corte de maturidade**: hoje 12 semanas no config; medido real em 22.470 casos de 2025 =
  mediana 10,4 · p75 22,7 · p90 31,6.

---

## ⏳ Rodadas candidatas (nenhuma pré-declarada ainda)

- **Validar o ENSO dentro do grid** — passou isolado (+7% em h=8), nunca no protocolo completo.
- **Confirmar que o vetor piora o alarme** — só a temporada 2026-2027 torna o achado confirmatório.
- ⏳ Janelas curtas parecem melhorar o **alarme** em h=12 (sensib. 0,846 × 0,769) — exploratório, exige
  pré-declaração própria. Ablação de janela e métrica de alarme: feitas em 13/09.

---

## ⏳ Dívida técnica

- **`cidade_referencia.py` desatualizado** — aponta para quantil 0,80; a vencedora agora é 0,85.
- **Seleção das 6 colunas de clima fica fora do walk-forward** — vazamento remanescente, não corrigido
  em 13/09. E o ranking é instável: recortando em 2023, 4 das 6 colunas mudam.
- **`rodar_regressao_selecao_clima` não pareia M0 e M1** — a diferença mistura efeito do vetor com
  efeito de avaliar em semanas diferentes.
- **A pasta `../Contexto/` está fora do git**, sem histórico. Os 4 documentos vivos entraram no
  repositório em 13/09/2026.
- **`bairro_surto` recebeu a correção mas não foi re-rodado** — segue contaminado no painel.
- **Corrigir o docstring de `modelagem_aedes/acesso/fontes.py`**: ele afirma taxa de confirmação de
  99,6% em 2023, e o medido é **69,3%**. A direção da alegação se sustenta, o número não.
- **`testar_remedios.py` usa hiperparâmetros diferentes do cenário 1** (300/31/20 contra 250/15/5),
  apesar do comentário dizer que são iguais.
- Miúdos: testes das funções de bairro · `linha_do_tempo_dados()` é código morto · CSVs de previsão sem
  `data_origem`/`data_alvo` · deck de `../Apresentacao_andamento/2026-06-19/` conta a história antiga.

## Registro cronológico

### 21/09/2026 — reunião com o orientador, e a pesquisa ganha eixo novo

- 🔄 **Eixo novo, para depois do seminário:** prever a **proliferação do vetor** como antecedente causal
  do surto, e não o surto. Agregar as arboviroses de vetor único, quantificar a defasagem entre as duas
  curvas, incluir horizonte de 6 meses, janela 2022–2025. Detalhe e ressalvas em [ESTADO.md](ESTADO.md) §4.
- ⚠️ **A preocupação dele:** o vetor não impactar *"indica que deve ter algum problema na metodologia"*.
- ✅ Seminário destravado; banca provável com Mariana e Anderson. Pesquisa **congela** depois dele.
- 🎯 Desafio sem valer nota: prever a curva de mosquito 2026-2027 e comparar em julho/2027.
- Transcrição em `../Reunioes de andamento/2026-09-21 - Alinhamento com o professor...md`.
  ⚠️ **Rótulos de quem fala estão trocados** em vários trechos — atribuir pelo conteúdo.

### 13/09/2026 — o dia do vazamento

- 🔴 **Vazamento temporal descoberto e corrigido.** O treino era cortado pela data da pergunta, não pela
  da resposta. Custo medido: **+52% de MAE em h=12**, R² de 0,758 → **0,437**. 152 células re-rodadas,
  6 controles independentes com diferença zero.
- 🚫 **Núcleo da tese refutado** — a equivalência clima × vetor fecha 1 de 8, não 4 de 8.
- 🚫 **"A perda importa mais que o algoritmo" refutado** — a ordem inverteu.
- 🔴 **Único resultado do projeto que sobrevive a Holm:** o vetor **piora** o alarme de surto em h=12
  (p Holm 0,037, n=553). E o achado positivo de 29/08 que sobrevivia a Holm era vazamento.
- ✅ **Camada espacial ficou mais forte:** a regra simples vence o ML em **8 de 8**.
- ✅ Nova configuração de referência: HistGB · quantil **0,85** · com vetor.
- ✅ Script perdido do ranking do grid reconstruído e validado.
- Detalhe: `analises/2026-09-13_auditoria_mecanica_resultados/` e `.../2026-09-13_correcao_vazamento_treino/`.

### Antes de 13/09/2026

- **30/08** — grid de 120 execuções escolheu a configuração de referência; alvo decidido (confirmados);
  viés de pico tratado com perda quantílica. ⚠️ Quase tudo refeito em 13/09.
- **29/08** — clima recapturado desde 2012 (388 → 727 semanas); painel publicado; escopo podado
  (casos por bairro descartados por Comitê de Ética).
- **16/08** — base corrigida e certificada, validada contra a Marília com diferença zero.

> Detalhe de cada teste, com pergunta, método e conclusão: [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md).
