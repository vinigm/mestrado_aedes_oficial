# PENDENCIAS — fila viva do projeto

> Leitura de 3 minutos. `@importado` em toda sessão: **tamanho é custo**, teto de ~100 linhas, item de 1 a
> 2 linhas. Retrato do sistema: [ESTADO.md](ESTADO.md) · Testes: [HISTORICO_DE_TESTES.md](HISTORICO_DE_TESTES.md)
> · Eixo fino: `git log`. Status: ✅ resolvido · ⏳ em aberto · 🚫 descartado (com data e quem decidiu).
> **Regra de 29/08/2026:** não existe "aguarda o orientador". Método é decisão nossa, pré-declarada.

---

## 🔴 SEMINÁRIO DE ANDAMENTO — prazo curto (reunião de 21/09/2026)

- ⏳ **Preencher título, resumo, palavras-chave e enquadramento** no sistema do PPGC. Banca provável: Mariana
  e Anderson. O PDF é opcional.
- ⏳ **Slides de até 10 min**, último slide de direcionamentos. **Escopo só dengue.** Não dizer "não teve
  correlação com mosquito ou clima".
- ⏳ Orientador mandar o link do site a Mariana e Mansilha · Vinicius mandar `brutos_secretarias_limpos/`
  (sem coordenada: não serve para análise espacial).
- 🧭 **Dois marcos, definidos pelo Vinicius em 25/09:** **pré-montagem** = site no ar, commit `710b411`,
  o que os professores viram · **pós-montagem** = de `22b70a6` em diante, só local. ⚠️ Os professores
  não sabem da folha 20 nem da régua sazonal.
- 📩 **Mansilha, 24/09:** textos com tom de "IA marqueteira", dupla negação, site que *"depõe contra quem
  nos forneceu os dados"*; propõe hipótese de subnotificação 2013-2021.
- **Depois do seminário a pesquisa CONGELA** e o foco vira o artigo (`../artigo_oficial/`, fora do git).

---

## ⏳ Destrava com o VINICIUS

- **Escolher o eixo da tese.** Candidatos em [ESTADO.md](ESTADO.md) §4.
- 🔴 **Ler da Silva et al. 2026, PLOS NTD** — mesma cidade e mesma armadilha, vetor com R² 0,46 contra
  −0,07 do clima. Muda o diferencial da tese. Ver `analises/2026-09-25_varredura_literatura/` §2.
- **Como apresentar a régua sazonal:** o modelo perde para "mesma semana do ano passado" em 2 e 3 meses.
  Entra no seminário? Ver `analises/2026-09-25_regua_regras_simples/`.
- **Automatizar a raspagem** — hoje manual; em 2026 é a única fonte, semana perdida é irrecuperável.
- **Folha 5 como controle** nas rodadas com folha 20 — recomendado, sem resposta.
- 🔴 **Métrica primária: MAE × perda quantílica 0,85.** Pelo MAE, a régua vence tudo em 3 meses; pela
  perda quantílica, o Chronos-2 vence o B0 por 47%. É definição de produto: quanto custa subestimar surto?

---

## ⏳ Decisões NOSSAS a pré-declarar

- **Recorte da tese** — depende do eixo. Pré-declaração formal antes de qualquer rodada nova.
- **Alvo:** vetor (letra do PEP) × casos (o código). O PEP também erra o horizonte: é **3 meses**
  (decisão do Vinicius, 23/09), não 1-4 semanas.
- **Residência × notificação** — o Estado usa residência; o projeto usa notificação, ~10% maior em POA.
- **Corte de maturidade** 12 semanas; medido em 2025: mediana 10,4 · p90 31,6. Só testável com dado vintage.

---

## ⏳ Rodadas candidatas

- **Confirmatória em 2026-2027** — o único juiz que resta. Pré-declarar antes da temporada:
  - vetor com folha 20 em 3 meses (exploratório: −12 a −16% de erro, carregado por 2024);
  - modelo contra a régua sazonal, por skill score;
  - o vetor piora o alarme (único resultado que sobrevive a Holm, 13/09).
- ⏳ **Métrica de alarme com folha 20** — nunca medida.
- ⏳ **Mistura modelo + régua** — a única direção consistente em 4 anos (+5,5%, sem significância).
- ⏳ **Pré-declarar teste pela perda quantílica** (Chronos-2 × B0) — pós-hoc hoje; e o **q0,85 do cenário
  adotado cobre só 35%** das semanas em h=12 (nominal 85%). Ver `analises/2026-09-25_sarima_lasso_ensemble/` §5.
- ⏳ **Vetor ajuda em 2024-2025 e atrapalha em 2022-2023** em três famílias de modelo (HistGB, LightGBM,
  Chronos-2). Explicar antes de 2026-2027. Chronos-2 com casos + vetor, sem clima, não rodou.
- ⏳ Janelas curtas parecem melhorar o **alarme** em h=12 (0,846 × 0,769) — exploratório.
- ⏳ **Canal endêmico em POA:** limite 0 em semanas fora da temporada (2018-2021 sem casos); não serve de régua
  de epidemia ainda. Considerar limiar fixo.
- 🔴 **2026 descolou:** o vetor de out/25-mar/26 igual ao de 2024-25 (média 0,71), mas só 11 confirmados (CEVS) —
  com 4.085 notificações e 3.832 inconclusivos. A temporada 2026 ficou FORA da avaliação (dados até fev/26).
- ⏳ **Defasagem vetor → casos nunca estimada no projeto.** da Silva 2026 mede τ 0,27 · 0,50 · 0,59 nos
  lags 0 · 4 · 8 semanas; replicar com os nossos dados.

---

## ⏳ Dívida técnica

- **Seleção das 6 colunas de clima fora do walk-forward** — treina nos 60% mais antigos (até 27/11/2022);
  contamina só a avaliação até 12/2022. Ranking instável.
- **`rodar_regressao_selecao_clima` não pareia M0 e M1.**
- **`bairro_surto` corrigido mas não re-rodado** — segue contaminado no painel.
- **`cidade_lift_vetor` não registrou run no MLflow** em 23/09 — causa não investigada.
- **Docstring de `acesso/fontes.py`** afirma 99,6% de confirmação em 2023; o medido é **69,3%**.
- **`testar_remedios.py`** usa hiperparâmetros diferentes do cenário 1 apesar do comentário.
- **`provar_sinal_da_ancora`** da bateria de 25/09 é tautológica — a garantia veio da revisão.
- **`../Contexto/` e `../artigo_oficial/` fora do git**, sem histórico.
- Miúdos: testes de bairro · `linha_do_tempo_dados()` morto · CSVs sem `data_origem` · deck de 19/06 antigo.

---

## Registro cronológico

### 25/09/2026 — a régua sazonal, a literatura e a bateria de formulação

- 🔴 **O modelo perde para "mesma semana do ano passado"** em h=8 e h=12 (MAE 217,8 × 243,8 a 278,8),
  inclusive na perda quantílica. Certificado por reimplementação. `analises/2026-09-25_regua_regras_simples/`
- ✅ **Varredura de literatura:** 40 achados, 32 confirmados na fonte, 0 refutados. Perder para régua em
  3 meses é comum. `analises/2026-09-25_varredura_literatura/`
- 🚫 **Seis formulações novas reprovadas** — log, âncora como atributo, resíduo, crescimento do vetor,
  linear, mistura. Nenhuma melhora nem bate a régua; resíduo e linear explodem.
  `analises/2026-09-25_bateria_formulacao_do_alvo/`
- 🚫 **Modelos de fundação zero-shot** (Chronos-Bolt, Chronos-2) não batem a régua em 3 meses; o vetor
  melhora o Chronos-2 (p Holm 0,007), só em 2024-2025. `analises/2026-09-25_modelos_de_fundacao/`
- ✅ **Alarme contra o canal endêmico:** em 1 mês o modelo vence; em 3 meses vence "esperar o surto" (p Holm
  0,0006) e empata com "o ano passado passou de 100". `analises/2026-09-25_alarme_contra_canal_endemico/`
- ✅ **Página "Comparações" no site, só local** (`NOVO_HTML/saida/comparacoes.html`), entre Cenário adotado e
  Próximos passos. ⚠️ Não publicada. ⏳ Unificar 278,7 (painel) × 278,8 (régua) do cenário adotado em 3 meses.
- ✅ **Comparação direta com a literatura:** acima dos estudos de pesquisa em POA e no Brasil; abaixo dos
  sistemas operacionais da Ásia em 3 meses. `analises/2026-09-25_comparacao_direta_literatura/`
- 🚫 **SARIMA e LASSO explodem** no começo da epidemia de 2024 (até 43 mil previstos); ensemble não bate a
  régua pelo MAE. 🔴 Pela perda quantílica, o quadro inverte. `analises/2026-09-25_sarima_lasso_ensemble/`
- ✅ **Catálogo de modelos prontos:** 34 itens, 26 confirmados. Em 27 capitais, POA ficou entre as piores (R² −0,21
  em 4 semanas); não há modelo preditivo publicado no RS. `analises/2026-09-25_catalogo_modelos_prontos/`
- ✅ **Novas fontes oficiais** (CEVS 2015-2026, TabNet, IBGE): 2015-2017 não trazem temporada epidêmica.
  `analises/2026-09-25_novas_fontes_oficiais/`
- ✅ **Notificações como alvo** (CEVS, até mai/2026): notificação como alvo ou entrada não ajuda; em 2026 o modelo
  de confirmados erra muito menos que "o ano passado". Página local. `analises/2026-09-25_notificacoes_como_alvo/`

### 24/09/2026 — bateria noturna

- 🔴 **Com folha mínima 20, o vetor reduz o erro de 3 meses** (p Holm 0,015 e 0,0001); com folha 5, não.
  Carregado por 2024. Não repetir "o vetor não melhora" sem "do HistGB com folha 5".
- 🚫 ENSO de agosto era vazamento. Lags de 5-12 e 52/104 semanas não ajudam. `analises/2026-09-23_bateria_noturna/`
- ✅ `cidade_referencia.py` corrigido para quantil **0,85** (commit `22b70a6`, 23/09).

### 23/09/2026 — site reconstruído e publicado (`710b411`)

- ✅ Painel novo por `NOVO_HTML/` e slides do seminário. 🔴 Só `cidade_regressao` rodou os 9 algoritmos.
  ✅ Treino certificado: começa em 18/02/2018; 2012-2017 não alimenta o cenário adotado.

### 21/09/2026 — reunião com o orientador

- 🔄 Eixo pós-seminário: casos a partir do vetor. ⚠️ Ele: o vetor não impactar *"indica que deve ter algum
  problema na metodologia"*. ✅ Dados da Secretaria limpos. ⚠️ Rótulos de quem fala trocados na transcrição.

### 13/09/2026 — o dia do vazamento

- 🔴 Treino cortado pela data da pergunta: +52% de MAE em h=12 ao corrigir. 🚫 Núcleo da tese refutado.
- 🔴 Único resultado que sobrevive a Holm: o vetor **piora** o alarme em h=12 (p 0,037).

### Antes: 30/08 grid de 120 execuções · 29/08 clima desde 2012 · 16/08 base certificada contra a Marília.
