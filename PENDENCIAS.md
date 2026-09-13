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

## ⏳ Destrava com o VINICIUS

- **Escolher o eixo da tese.** A proposta de 29/08 (equivalência clima × vetor) foi **refutada** em
  13/09. Os quatro candidatos que sobreviveram estão em [ESTADO.md](ESTADO.md) §4.

- **Decidir o que fazer com o painel.** Ele publica 4 números hoje sabidamente errados, e regerar agora
  misturaria resultados corrigidos com não corrigidos. Nada foi publicado. [ESTADO.md](ESTADO.md) §5.

- **Commitar o dia 13/09** — correção em 5 motores + `modelagem_aedes/motor/corte_temporal.py` + 2 pastas de análise +
  os 20 resultados regerados. Ponto de retorno: tag `antes-correcao-vazamento`.

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

- **Ablação de janela de treino para o alvo CASOS** — só existe para o vetor. ~20 min. Pedida pelo
  Vinicius em 13/09.
- **Validar o ENSO dentro do grid** — passou isolado (+7% em h=8), nunca no protocolo completo.
- ✅ **Métrica de alarme — FEITA em 13/09/2026.** Sensibilidade 97,1% em h=4 e 76,9% em h=12.
  Ver `analises/2026-09-13_metrica_de_alarme/`. ⏳ Falta uma temporada com mais episódios: só há 2.
- **Confirmar que o vetor piora o alarme** — só a temporada 2026-2027 torna o achado confirmatório.

---

## ⏳ Dívida técnica

- **`cidade_referencia.py` desatualizado** — aponta para quantil 0,80; a vencedora agora é 0,85.
- **Seleção das 6 colunas de clima fica fora do walk-forward** — vazamento remanescente, não corrigido
  em 13/09. E o ranking é instável: recortando em 2023, 4 das 6 colunas mudam.
- **`rodar_regressao_selecao_clima` não pareia M0 e M1** — a diferença mistura efeito do vetor com
  efeito de avaliar em semanas diferentes.
- **Os 4 documentos vivos estão FORA do git** (vivem na raiz `Pesquisa/`; o repo é ``).
- **`bairro_surto` recebeu a correção mas não foi re-rodado** — segue contaminado no painel.
- **Corrigir o docstring de `modelagem_aedes/acesso/fontes.py`**: ele afirma taxa de confirmação de
  99,6% em 2023, e o medido é **69,3%**. A direção da alegação se sustenta, o número não.
- **`testar_remedios.py` usa hiperparâmetros diferentes do cenário 1** (300/31/20 contra 250/15/5),
  apesar do comentário dizer que são iguais.
- Miúdos: testes das funções de bairro · `linha_do_tempo_dados()` é código morto · CSVs de previsão sem
  `data_origem`/`data_alvo` · deck de `../Apresentacao_andamento/2026-06-19/` conta a história antiga.

## Registro cronológico

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

### 30/08/2026 — o modelo de casos ganhou dono

- ✅ Grid de 120 execuções escolheu a configuração de referência; alvo decidido por medição
  (**confirmados**); viés de pico diagnosticado e tratado com perda quantílica.
- 🚫 Descartados: 4 de 5 famílias de features novas · LightGBM em horizonte longo · os 9 algoritmos como rotina.
- ⚠️ Quase tudo deste dia foi **refeito em 13/09**.

### 29/08/2026 — clima longo, painel no ar, escopo podado

- ✅ Clima recapturado desde 2012 (388 → **727 semanas**), com certificação adversarial. Painel publicado.
- 🚫 Descartados pelo Vinicius: dependência do orientador · casos por bairro (Comitê de Ética) ·
  shapefile como bloqueio · dicionário das colunas de espécie.

### 16/08/2026 — o dia da virada

- ✅ Base corrigida e certificada (datas invertidas + 222 duplicatas), validada contra a Marília com
  **diferença zero**. Pipeline migrado para a série completa.
- 🚫 Descartados: "as armadilhas são inúteis" como manchete · regressão de casos como eixo ·
  bairro administrativo como granularidade.

> Antes de 16/08/2026 e o detalhe de cada teste: [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md).
