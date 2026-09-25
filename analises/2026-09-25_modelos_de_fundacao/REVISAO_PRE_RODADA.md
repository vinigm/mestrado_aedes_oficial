# Revisão adversarial pré-rodada — modelos de fundação

> Revisor independente, 25/09/2026. Alvo: `rodar.py` contra `PRE_DECLARACAO.md` e `AMBIENTE.md`.
> Nenhum arquivo alterado. `--rodar` **não foi executado** por este revisor (rodaria a bateria cara);
> só código pequeno via `/Users/viniciusguerra/.venvs/aedes_modelos_fundacao/bin/python`.

## Veredito: 🔴 REPROVADO — achado bloqueante confirmado empiricamente

---

## 🔴 Achado bloqueante: a "régua sazonal" não é a régua sazonal

- `rodar.py` lê o comparador régua do braço `"referencia"` dentro do CSV do **bloco 7**
  (`CAMINHO_PREVISOES_B0`). Mas esse braço `"referencia"` é o **modelo `CIDADE_REFERENCIA`**
  (HistGB, quantil 0,85, hiperparâmetros padrão do projeto) — não a regra "mesma semana do ano
  passado".
- **Prova:** recalculei o MAE do braço `"referencia"` do bloco 7 na avaliação (`data_alvo≥2024`):
  **97,99 / 219,67 / 272,63 / 278,82** (h=1/4/8/12). Isso bate com o painel `PAINEL_PUBLICADO` do
  `harness.py` da bateria noturna (98,0/219,7/272,6/278,7) — é o modelo de referência, não a régua.
- A régua sazonal de verdade (casos em `data_alvo−52` semanas) está em
  `analises/2026-09-25_regua_regras_simples/saidas/conferencia_ancoras_numericas.csv`, rotulada
  `sazonal`: MAE **202,1/213,2/216,2/217,8** — exatamente as âncoras que `rodar.py` tem hardcoded
  em `MAE_ANCORA_REGUA_POR_HORIZONTE`. Ou seja: **a âncora está certa, a fonte de dado está errada.**
- **Consequência ao rodar:** executei `carregar_pares_de_avaliacao` + `verificar_trava_ancoras` de
  verdade. A **Trava 5 falha** com mensagem clara (`MAE régua medido 97.99 != âncora 202.10`, etc.
  nos 4 horizontes) — então `--rodar` vai **abortar antes de qualquer leitura**, o que é o
  comportamento desenhado (a trava está fazendo o trabalho dela). Mas isso significa que **a
  bateria completa não roda hoje**: precisa trocar a fonte do braço régua para o CSV/coluna certo
  de `analises/2026-09-25_regua_regras_simples/` (pareado por `data_alvo`), não para o `"referencia"`
  do bloco 7.
- Família **H1** (bate a régua) ficaria inteiramente inválida se a trava 5 fosse afrouxada sem
  corrigir a fonte — comparar contra o modelo de referência em vez da régua muda a pergunta.

---

## Checagens 1-7 (as que rodaram)

1. **Futuro no contexto:** OK. 3 pares em h=12 conferidos: contexto de casos e as 5 covariáveis
   terminam exatamente na origem (`origem = data_alvo − 12sem`), mesmo `.loc` slice, mesmo `len`.
2. **Passo certo:** OK. `predict_quantiles` do Chronos-2 só reordena o eixo de quantis
   (`rearrange "... q h -> ... h q"`), não o eixo temporal — índice `h-1` é o passo `h` após a
   origem, que é `data_alvo`. Confirmado lendo o source da biblioteca.
3. **Pareamento (h, data_alvo):** OK mecanicamente — `chave_b0 == chave_regua` não lançou erro,
   1159 pares carregados (295+292+288+284 = 1159, bate o log do smoke). Mas os pares vêm do B0 e do
   braço `"referencia"` errado (ver achado bloqueante) — o pareamento em si está certo, o conteúdo não.
4. **Quantis:** OK. Chronos-2 tem 0,85 nativo (`training_quantile_levels` inclui 0.85 exato, sem
   interpolação). Bolt não tem — confirmei que a biblioteca usa `interpolate_quantiles`, interpolação
   linear real entre 0,8 e 0,9, não é média nem nearest.
5. **Famílias H1(12)/H2(16)/H3(4):** contagens corretas no código (H1 só h∈{4,8,12}; H2 todos os h;
   H3 uma comparação por h). **Régua NÃO usa `data_alvo−52` semanas** na prática — usa o modelo
   errado (achado bloqueante acima).
6. **Travas antes das comparações:** Travas 1 e 5 rodam logo após carregar os dados, antes de
   carregar modelo ou comparar. Travas 2 e 4 rodam dentro do loop de previsão, também antes das
   famílias. **Trava 3 (determinismo) não é chamada em `executar_bateria_completa`** — só no
   smoke test. Não bloqueante (é propriedade do ambiente, já confirmada no smoke com os 4 braços),
   mas vale nota: a rigor a pré-declaração pede a trava "antes de ler qualquer resultado" na rodada.
7. **Padrão de código:** sem `lambda`; comprehensions são só extração/filtro de campo, sem regra de
   negócio nem I/O. Type hints e docstrings presentes em toda função pública. Nada bloqueante.

---

## Não bloqueantes / observações

- Tolerância da trava 5 (±0,15 MAE absoluto) é decisão do agente, não da pré-declaração — razoável,
  mas registrar como emenda formal se a rodada seguir adiante.
- `testar_aceitacao_de_nan_em_past_covariates`: comportamento e mensagem batem com o relatado
  (Chronos-2 aceitou NaN, 4 NaN no contexto testado).
- Datas de publicação dos modelos no Hub conferem com a seção 6 da pré-declaração (Chronos-2
  30/10/2025, Bolt 25/11/2024) — sem divergência.

---

## O que destrava o `--rodar`

Trocar, em `carregar_pares_de_avaliacao`, a fonte do `previsto_regua`: não é o braço `"referencia"`
de `CAMINHO_PREVISOES_B0` (bloco 7). `analises/2026-09-25_regua_regras_simples/calcular_regua.py`
(`calcular_regra_sazonal`) mostra que a régua é só `casos_confirmados[data_alvo − 52 semanas]` —
não existe um CSV per-par com esse valor pronto lá, então o mais simples é **recalcular direto**
em `rodar.py` com essa mesma fórmula (uma linha, usando `tabela_final.csv` já carregado), em vez de
puxar de outro braço. Confirmei que essa fórmula reproduz as âncoras 202,1/213,2/216,2/217,8.
