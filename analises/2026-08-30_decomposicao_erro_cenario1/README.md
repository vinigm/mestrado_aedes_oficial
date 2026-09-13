# Decomposição do erro e viés de pico — cenário 1 (casos, POA) — 30/08/2026

> **A pergunta:** o R² alto do cenário 1 significa que o modelo enxerga o pico chegando, ou só acerta o
> "está calmo" numa série dominada por semanas de baixa contagem?
> **A resposta:** o modelo **subestima sistematicamente o pico** em todos os horizontes, e a causa **não**
> é o teto de extrapolação das árvores — a tentativa padrão de correção (log1p) piora o viés em vez de
> consertar.
> Status: ⚠️ exploratório. Pré-declaração: não existe arquivo dedicado — a hipótese e a previsão estão
> registradas no docstring de `diagnosticar_vies_pico.py`, escritas antes de rodar.

## 1. Por que este teste foi feito

- A série de casos de POA é extremamente desigual: **61% das semanas têm ≤5 casos** e algumas passam de
  2.000 — nesse regime o R² é dominado pelos poucos picos e pode ficar alto só por acertar o formato
  geral da curva.
- A pergunta que o R² não responde, e que importa para vigilância, é se o modelo **enxerga o pico
  chegando** ou só acerta as semanas calmas.
- `decompor_erro.py` quebra o erro (MAE e viés) por faixa de intensidade real (entressafra / intermediária
  / pico) e por horizonte, para os dois conjuntos do cenário 1 (`M0_clima6` e `M1_clima6_vetor`).
- `diagnosticar_vies_pico.py` testa **por que** o pico é subestimado, com duas hipóteses pré-registradas
  no próprio docstring:
  - **Teste A** — teto de extrapolação: árvore não extrapola além do máximo visto no treino; como cada
    epidemia de POA foi maior que a anterior (879 → 762 → 1.855 → 2.381), o modelo bateria num teto
    estrutural.
  - **Teste B** — remédio padrão (alvo em `log1p`, desfeito com `expm1`): previsão registrada **antes**
    de rodar — "se a causa for a não-extrapolação, o log não conserta o viés; se consertar, a hipótese
    está errada".

## 2. Como foi medido

- **Alvo:** `casos` (confirmados), cenário 1 = `cidade_regressao`.
- **Features:** núcleo + **6 melhores variáveis de clima** (`ranking_clima.head(6)`), com e sem as
  colunas do vetor (`M0_clima6` × `M1_clima6_vetor`); `diagnosticar_vies_pico.py` só roda o conjunto sem
  vetor (M0).
- **Modelo:** o mesmo do cenário 1 oficial (`config.modelo`), sazonalidade (`alvo_sin`/`alvo_cos`) sempre
  incluída.
- **Horizontes:** 1, 4, 8 e 12 semanas. **Passo:** o do config (`config.passo`), walk-forward expansível
  (o treino cresce a cada passo, nunca encolhe).
- **Faixas de intensidade** (fixadas antes de olhar o resultado): entressafra ≤5 casos · intermediária
  6–100 · pico >100.
- `decompor_erro.py` chama a função **do pacote** (`motor.walk_forward_regressao`); `diagnosticar_vies_pico.py`
  tem sua **própria** rotina de walk-forward, escrita à parte (achado da §6).
- Critério de decisão do Teste A: comparar o **teto do treino** (máximo de `y_h` já visto) com o valor
  real do pico e contar quantos picos ultrapassam esse teto. Critério do Teste B: o viés médio no pico
  piora ou melhora com `log1p`.

## 3. O que deu

**Teste A — teto de extrapolação (`diagnostico_picos.csv`, variante `original`, só picos >100):**

| h | n picos | real médio | previsto médio | viés médio | teto do treino médio | picos acima do teto |
|---|---|---|---|---|---|---|
| 1 | 32 | 858,7 | 769,4 | −89,2 | 1.384,6 | 7/32 |
| 4 | 32 | 829,5 | 623,6 | −205,9 | 1.439,3 | 5/32 |
| 8 | 32 | 829,5 | 506,3 | −323,1 | 1.439,3 | 5/32 |
| 12 | 32 | 829,5 | 400,1 | −429,3 | 1.439,3 | 5/32 |

- O **teto médio do treino (≈1.439) é quase o dobro do pico real médio (≈829)** — na maioria das semanas
  de pico (25 a 27 de 32, conforme h) o modelo **não estava travado em nenhum teto**: tinha espaço de
  sobra para prever mais alto e mesmo assim não previu.
- **Teste A refuta a hipótese do teto de extrapolação** como causa principal — o padrão numérico bate
  exatamente com o que o contexto do projeto atribui a esta fase (teto 1.439 / pico médio 829).

**Teste B — remédio padrão (`log1p` / `expm1`):**

| h | viés original | viés com log1p | melhorou? |
|---|---|---|---|
| 1 | −89,2 | −171,4 | não |
| 4 | −205,9 | −366,4 | não |
| 8 | −323,1 | −461,2 | não |
| 12 | −429,3 | −582,9 | não |

- Em **nenhum dos 4 horizontes** o `log1p` reduziu o viés — ele **piora** em todos, e a piora cresce com
  o horizonte (quase dobra em h=12).
- Pela previsão pré-registrada, isso é **consistente com a hipótese de não-extrapolação estar errada**
  (o log não conserta), mas também mostra que o remédio padrão **não é solução** por si só — o Teste A já
  havia mostrado que o teto não é o gargalo, então o log resolveria o problema errado.

**Decomposição por faixa (`decomposicao_erro_por_faixa.csv`):** o viés no pico já aparece negativo e
crescente com o horizonte nos dois conjuntos (M0 −89,2 em h=1 até −429,3 em h=12; M1 muito parecido:
−135,0 até −428,0). Nas faixas baixas (entressafra) o viés é **positivo** (o modelo superestima semanas
calmas) — o erro sistemático empurra a previsão para o centro da distribuição, subestimando extremos
altos e superestimando os baixos.

## 4. Conclusão

- **FATO** — o modelo subestima o pico em todos os horizontes testados (viés negativo, crescente de
  −89 a −429 de h=1 a h=12, conjunto M0).
- **FATO** — a maioria dos picos reais (25–27 de 32, conforme h) fica **abaixo** do teto de valores já
  vistos no treino; a hipótese do teto de extrapolação está refutada por este teste.
- **FATO** — o remédio padrão (`log1p`/`expm1`) piora o viés do pico em vez de corrigi-lo, nos 4
  horizontes testados.
- **EXPLORATÓRIO** — a causa real do viés (assimetria da distribuição da série, não o teto) é **hipótese
  levantada por este teste, não demonstrada aqui**: este script mede o sintoma e refuta uma causa
  candidata, mas não testa diretamente a assimetria como mecanismo.
- **⚠️ Divergência encontrada:** a frase "a autocorrelação dos casos explica 91% da variação em h=1 e 0%
  em h=12" (citada no PENDENCIAS/ESTADO para a rodada de 30/08) **não sai desta pasta** — nenhum dos dois
  scripts calcula autocorrelação ou R². Busca no projeto localiza esse número em
  `analises/2026-08-30_grid_completo/README.md` (linhas ~108-109). O contexto que originou esta tarefa
  atribuiu esse achado à fase errada.

## 5. Ressalvas e o que ficou em aberto

- **Sem `PRE_DECLARACAO.md` dedicado** — a única pré-declaração é o docstring do próprio script, o que é
  mais fraco que um arquivo versionado à parte (não impede o autor de ajustar a leitura depois de ver o
  resultado, mesmo que aqui a previsão bateu).
- **Sem correção de múltiplas comparações** — 4 horizontes × 2 testes × 2 conjuntos, nenhum p-valor
  calculado; as tabelas são descritivas (MAE, viés médio), não testes de hipótese.
- **Amostra pequena no pico**: 28 a 33 semanas por célula — qualquer leitura fina (ex.: diferença entre
  M0 e M1 no viés do pico) é frágil.
- **Comparação M0 × M1 não é o foco desta análise** (é o foco de `cidade_regressao`/F2.8 do README de
  vazamento) — aqui o conjunto com vetor aparece só para contexto, não para decidir sobre o vetor.
- **`diagnosticar_vies_pico.py` não usa o alvo confirmado por padrão do pacote** — ele chama
  `fontes.carregar_tabela_final()` e `config.coluna_alvo`, então herda o que estiver configurado em
  `CIDADE_REGRESSAO` no momento da execução; não há garantia neste README de qual alvo estava ativo em
  30/08/2026 além do que a `PRE_DECLARACAO` de outras pastas descreve (assumido: confirmados, decisão de
  30/08/2026).

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- **Sim, os dois scripts rodaram com o corte de treino defeituoso, e isso é verificável nesta própria
  pasta:**
  - `diagnosticar_vies_pico.py` tem sua **própria** rotina de walk-forward (não usa
    `motor.corte_temporal`) e corta o treino por **posição** (`treino = validos.iloc[:indice_corte]`) —
    exatamente o padrão defeituoso descrito na correção de 13/09/2026. Esse script, se rodado hoje **sem
    edição**, ainda produziria o mesmo vazamento — a correção central do pacote não o alcança.
  - `decompor_erro.py` chama `motor.walk_forward_regressao` (função do pacote, hoje corrigida); mas os
    CSVs salvos em `saidas/` são de 30/08/2026, **antes** da correção de 13/09/2026 — foram gerados
    com a versão antiga da função.
- **Confirmação numérica cruzada:** o MAE ponderado por faixa desta pasta reproduz, dígito a dígito, a
  coluna "antes" da §F2.8 do README de 13/09/2026 (mesmo experimento `cidade_regressao`, mesmas colunas
  clima6): M0 h=4/8/12 = 91,7 / 98,8 / 109,5; M1 h=4/8/12 = 86,6 / 93,2 / 114,2 — todos batem com a
  reconstrução feita a partir de `decomposicao_erro_por_faixa.csv` nesta sessão.
- **Direção da inflação, pela §F2.8 daquele README:** o MAE "antes" (== os números desta pasta) está
  **subestimado** em +24,7% a +53,5% conforme h e conjunto — ou seja, o erro real do modelo é **maior**
  do que o mostrado aqui, e o viés do pico provavelmente é **ainda mais negativo** sem vazamento (mais
  erro concentrado justamente nas semanas de pico, que são as mais recentes e mais contaminadas).
- **Este teste NÃO foi refeito** — consta explicitamente na lista de pendências ("decomposição do erro" e
  "remédios do viés de pico" seguem não refeitos em 13/09/2026). A conclusão qualitativa (modelo
  subestima o pico; teto de extrapolação não é a causa; log1p não conserta) tem boa chance de sobreviver,
  porque o vazamento tende a **reduzir** o erro medido, não a criá-lo — mas as magnitudes exatas de viés
  e MAE aqui **não devem ser citadas** como número final sem reexecução com `motor.corte_temporal`.

## 7. Arquivos

- `decompor_erro.py` — decompõe MAE e viés por faixa de intensidade (entressafra/intermediária/pico), h
  e conjunto (M0/M1); usa a função de walk-forward do pacote.
- `diagnosticar_vies_pico.py` — testa a hipótese do teto de extrapolação e o remédio `log1p`; walk-forward
  próprio, com corte por posição (vazamento confirmado, ver §6).
- `saidas/previsoes_por_semana.csv` — 1.184 previsões semana a semana de `decompor_erro.py` (h, conjunto,
  real, previsto).
- `saidas/decomposicao_erro_por_faixa.csv` — 24 linhas: MAE/viés agregados por conjunto × h × faixa.
- `saidas/diagnostico_previsoes.csv` — 1.208 previsões semana a semana de `diagnosticar_vies_pico.py`
  (variantes `original` e `log1p`), com o teto do treino a cada passo.
- `saidas/diagnostico_picos.csv` — 8 linhas: resumo dos testes A e B só nas semanas de pico (>100 casos).
