# Alvo e features do InfoDengue — 30/08/2026

> **A pergunta:** o alvo (confirmados/notificados/nowcasting) e as features de transmissão do
> InfoDengue (`Rt`, `p_rt1`...) melhoram a captura do pico e a previsão em h=8/h=12?
> **A resposta:** alvo continua **confirmados**; nowcasting é 99,1% idêntico a notificados;
> features de transmissão pioram o pico em quase todos os horizontes — descartadas.
> Status: ✅ concluído (com ressalva grave na seção 6). Pré-declaração: sim, `PRE_DECLARACAO.md`
> nesta pasta.

## 1. Por que este teste foi feito

- O projeto usava só a coluna `casos` (confirmados/SINAN) do InfoDengue, que tem **31 colunas**
  preenchidas desde 2010, com duas frentes nunca exploradas.
- **Teste A:** suspeita de que o "viés de subestimação do pico" fosse parcialmente do **alvo**, não
  do modelo — a taxa de confirmação cai justamente nos anos de epidemia grande.
- **Teste B:** cinco colunas de transmissão (`Rt`, `p_rt1`, `notif_accum_year`, `receptivo`,
  `transmissao`) nunca testadas, contemporâneas (disponíveis em t, não vazam ao prever t+h).
- Pré-declaração prometeu, **antes de rodar**: comparar captura do pico e R² (adimensionais, únicas
  métricas comparáveis entre alvos de escalas diferentes) e decidir Teste B só se melhorasse
  **h=8 e h=12**, os horizontes onde a limitação estrutural foi apontada.

## 2. Como foi medido

- **Alvo (Teste A):** três variantes — `casos_confirmados` (SINAN), `casos_notificados`
  (InfoDengue) e `casos_nowcast` (`casos_est`, notificado corrigido por atraso de notificação).
- **Features (Teste B):** referência (confirmados) + as 5 colunas de transmissão, rodada só sobre
  o alvo confirmados.
- **Algoritmo:** HistGradientBoosting, config de referência do grid de 30/08 — `quantile 0,80`,
  `max_iter=250`, `learning_rate=0,05`, `max_leaf_nodes=15`.
- **Horizontes:** 1, 4, 8, 12 semanas. **Passo:** 1 (walk-forward semana a semana).
- **Calibração** até 31/12/2023 · **avaliação** 2024 em diante.
- **Corte de treino:** por posição de linha ordenada por `data` (data de **origem**, não de alvo)
  — ver seção 6.
- **Métrica de decisão:** captura do pico = previsto ÷ real nas semanas de pico (percentil 85 de
  cada alvo, já que as escalas diferem) e R², ambos só na avaliação.
- **Execuções:** 4 variantes de Teste A × 4 horizontes + 1 variante de Teste B × 4 horizontes =
  20 walk-forwards completos, **57,2 min** de tempo total (log).

## 3. O que deu

**Captura do pico na avaliação** (previsto/real; 1,0 = perfeito):

| h | A1 confirmados | A2 notificados | A3 nowcast | B confirmados+transmissão |
|---|---|---|---|---|
| 1 | 0,800 | 0,859 | 0,859 | 0,786 |
| 4 | 0,664 | 0,684 | 0,684 | 0,645 |
| 8 | 0,570 | **0,463** | **0,463** | 0,566 |
| 12 | 0,598 | **0,480** | **0,480** | 0,604 |

- **A2 e A3 são numericamente idênticos** em todo horizonte (MAE, R², captura). Confirmado à parte:
  `casos` e `casos_est` no InfoDengue são iguais em **99,1%** das 857 semanas (verificado nesta
  auditoria, correlação 0,99999997) — o nowcasting só ajusta as últimas semanas, que saem da
  amostra de teste.
- Notificados (A2/A3) capturam melhor o pico em h=1/h=4, mas **pioram** em h=8/h=12 — o oposto do
  que a hipótese de "achatamento do alvo confirmado" previa.
- Teste B (transmissão) **piora** a captura do pico em h=1, h=4 e h=8; só melhora minimamente em
  h=12 (0,604 × 0,598). A regra de decisão exigia ganho em **h=8 e h=12** simultaneamente — não
  ocorreu.
- **Escala de cada alvo** (pico médio real): confirmados ≈ 1.882–1.900 casos/semana · notificados e
  nowcast ≈ 4.107 — por isso o MAE bruto de A2/A3 (267 a 695) não é comparável ao de A1/B (101 a
  187): escalas diferentes, métrica de decisão é a captura do pico, não o MAE.

## 4. Conclusão

- **FATO:** nesta rodada (com o defeito da seção 6), `casos_est` e `casos_notificados` produzem
  previsões estatisticamente indistinguíveis — a base de dados não permite testar "nowcasting"
  como alvo diferente de "notificado" nesta pergunta.
- **FATO:** as features de transmissão do InfoDengue não cumpriram a regra de decisão
  pré-declarada (melhorar h=8 e h=12 juntos) — descartadas por medição, não por intuição.
- **HIPÓTESE (não confirmada aqui):** a suspeita original — de que parte do viés de pico viria do
  alvo confirmado — não se sustenta nestes números; alvo confirmado captura pico **melhor** que
  notificado em h=8/h=12, mesmo antes de qualquer correção de vazamento.
- **EXPLORATÓRIO:** a vantagem de notificados em h=1/h=4 não estava na regra de decisão do Teste A
  (que comparava pico global, não por horizonte) — não vira recomendação de trocar alvo por
  horizonte curto sem uma pré-declaração própria.

## 5. Ressalvas e o que ficou em aberto

- Sem correção de múltiplas comparações — 4 variantes × 4 horizontes × 2 métricas nunca passaram
  por Holm ou equivalente.
- Uma única execução por combinação (sem sementes múltiplas); não há intervalo de confiança em
  nenhum número desta tabela.
- Comparação entre alvos não é pareada nas mesmas semanas exatas: A1/B têm **n=102** na avaliação
  contra **n=107** de A2/A3 (confirmados tem menos histórico coberto que notificados no InfoDengue).
- **Divergência de dado encontrada e não resolvida** (ver missão): a taxa de confirmação citada
  nesta pasta (`PRE_DECLARACAO.md`) é **73,2% em 2022 → 38,3% em 2025** — reproduzi esse número
  nesta auditoria a partir de `casos_confirmados` (tabela_final) ÷ `casos` (InfoDengue) por ano:
  2022 = 73,2% · 2023 = 69,3% · 2024 = 60,1% · 2025 = 38,3%. **Bate exatamente** com o texto desta
  pasta (73,2/38,3).
  - O `PENDENCIAS.md` do projeto e o docstring de `fontes.py`
    (`carregar_tabela_final_com_casos_notificados`) citam **99,6% (2023) → 42,0% (2025)** — número
    diferente, sem script encontrado no repositório que o gere. Com a mesma conta (confirmados ÷
    notificados por ano), 2023 dá **69,3%**, não 99,6%. **Não registrado**: de onde vem o 99,6/42,0
    — pode ser outra base, outro corte de datas ou erro de transcrição num relato anterior. Fica
    como pendência a investigar, não resolvida por esta auditoria.

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- **Sim, esta análise usa o corte de treino defeituoso.** A função `rodar()` em
  `testar_alvo_e_features.py` corta `treino = validos.iloc[:corte]` / `teste = validos.iloc[corte:corte+1]`
  sobre a tabela ordenada por `data` (data de **origem**), não por `data_alvo` (origem + h semanas)
  — exatamente o padrão descrito no vazamento de 13/09/2026.
- Está na lista **"NÃO REFEITO"** informada na missão — nenhuma das 4 variantes (A1, A2, A3, B) foi
  re-rodada com o corte corrigido.
- **Direção provável do viés:** os números de captura de pico e R² desta pasta estão
  **otimistas/inflados**, na mesma direção do achado de 13/09/2026 (+52% de MAE em h=12 na
  configuração de referência quando corrigido). O efeito cresce com o horizonte — h=8 e h=12,
  justamente os horizontes que decidiram o Teste B, são os mais expostos.
  - Consequência prática: a rejeição das features de transmissão em h=8/h=12 **precisa ser
    revalidada** após a correção — não dá para descartar em definitivo enquanto o corte que gerou
    o "não passou na regra" ainda carrega o vazamento.
- Nenhum re-teste com o corte corrigido foi feito para este par (alvo × features) até o momento
  desta auditoria (13/09/2026).

## 7. Arquivos

- `PRE_DECLARACAO.md` — desenho e regras de decisão de Teste A e Teste B, escrita antes de rodar.
- `testar_alvo_e_features.py` — script único que roda os dois testes em sequência (~57 min).
- `saidas/alvo_features_previsoes.csv` — previsão × real linha a linha, 6.876 linhas, 4 variantes.
- `saidas/alvo_features_resumo.csv` — MAE, R², captura de pico por variante × horizonte × período.
- `saidas/alvo_features_log.txt` — log de execução completo (57,2 min, 20 walk-forwards).
