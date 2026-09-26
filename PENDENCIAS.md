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
- 🧭 **Marcos (Vinicius, 25/09):** pré-montagem = site no ar, `710b411`, o que a banca viu · pós-montagem = de
  `22b70a6` em diante, só local. ⚠️ A banca não sabe da régua sazonal nem de 2026.
- 📩 **Mansilha, 24/09:** sem tom de "IA marqueteira", sem dupla negação, sem depor contra quem cedeu os dados.
- **Depois do seminário a pesquisa CONGELA**; foco no artigo (`../artigo_oficial/`, fora do git).

---

## ⏳ Destrava com o VINICIUS

- **Eixo da tese.** Candidatos em [ESTADO.md](ESTADO.md) §4.
- 🔴 **Ler da Silva et al. 2026, PLOS NTD** — mesma cidade e armadilha; já está em `Artigos de referencia/`.
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
- ⏳ **Defasagem vetor → casos nunca estimada.** da Silva 2026: τ 0,27 · 0,50 · 0,59 nos lags 0 · 4 · 8.
- 🚫 **Canal endêmico e MEM em POA** — 26/09: exigem histórico longo e anos calmos. Porto Rico usa **38,5 anos**;
  aqui o limite dá 0 e o corte do MEM sobe de 6 para 94. Limiar vem do plano municipal, não do nosso histórico.
- 🟢 **Aceleração de transmissão como régua de alarme:** média móvel 4 ÷ 26 semanas, alarme acima de **1,33**. Em 8
  países: sensibilidade 100% × 30% do canal, antecedência 6,9 × 1,6 semanas. Precisa de 26 semanas, não de anos.
  ⚠️ Regra importada pode não transferir: a da Malásia foi a pior aqui (Youden −0,05).
- ⏳ **Limiar de decisão do alarme nunca foi ajustado** — hoje dispara quando a previsão passa de 100, o mesmo número
  do evento. Varredura + semanas consecutivas + alarme composto com a régua: recálculo sobre previsões salvas.
- 🚫 **Vírus no mosquito como atributo** — descartado pelo Vinicius em 25/09: exigiria dado novo da Prefeitura.
- 🚫 **Notificações como alvo ou entrada** (25/09): pioram em 3 meses. 🚫 **SARIMA e LASSO** (25/09): explodem.

---

## ⏳ Dívida técnica

- **Seleção das 6 colunas de clima fora do walk-forward**, com ranking instável e dependente do alvo.
- **`bairro_surto` não re-rodado** · **`cidade_lift_vetor` sem run no MLflow** · `rodar_regressao_selecao_clima` sem pareamento.
- **Docstring de `acesso/fontes.py`:** 99,6% de confirmação em 2023; o medido é 69,3%.
- **Trava da busca de 25/09** com erro de janela no script, corrigido só por emenda · `provar_sinal_da_ancora` tautológica.
- 🔴 **Não rodar `consolidar_sinan` nem `montar.py`:** com a correção de 25/09 eles puxam o DENGBR26 novo e trazem 2026
  de volta. `preparar_dados.py` inteiro, nunca: rebaixa clima e ENSO.
- `../Contexto/` e `../artigo_oficial/` fora do git · `testar_remedios.py` com hiperparâmetros trocados · miúdos de bairro.

---

## Registro cronológico

### 26/09/2026 — 2026 sai da avaliação, e o limiar ganha base

- 🚫 **Premissa de Porto Rico derrubada:** eles usam **38,5 anos** de série (MMWR mm7405a1), não série curta. Limiar
  derivado de histórico exige anos calmos, que POA não tem. Reforça usar o plano municipal.
  🟢 Achado: **aceleração de transmissão** (4÷26 semanas, corte 1,33) como régua sem série longa.
  `analises/2026-09-26_limiar_para_serie_curta/`

- 🚫 **2026 não entra (Vinicius):** com séries crescentes é impossível prever um ano de 19 casos. A tabela oficial voltou à
  de antes (até SE 202617, avaliação até 01/02/2026); a versão com 2026 fica guardada em `atualizacao_dados_2026/`.
- ⚠️ A busca de 120 e a segunda bateria rodaram na tabela com 2026 e ficam só como registro. Em 2024-25: WIS melhor que a
  régua dos sprints em 1 mês; a melhor da busca perde para a régua em 3 meses (239,6 × 226,8). Refazer antes de citar.
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
