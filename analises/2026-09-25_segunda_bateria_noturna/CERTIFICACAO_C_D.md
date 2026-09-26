# Certificação adversarial — Rodadas C e D (segunda bateria noturna)

**Certificador independente, refeito do zero em 26/09/2026** (a certificação anterior, de 01h14, foi
descartada por instrução — resultados considerados incompletos naquele momento). Recálculo em
`cert_CD_v2.py` (scratchpad da sessão), sem reusar código de `rodar.py` de C ou D — só leitura das
previsões brutas (`previsoes_sementes.csv` de C, `previsoes_por_braco.csv` da rodada A, usado por D).

## Pré-condições conferidas

- **`vencedoras.json`** gravado às 23h49:55; a rodada C terminou às 00h15 — C rodou **depois** da busca,
  sem risco de corrida. `config_id` bate: `histgb_018` (HB_best) e `lightgbm_040` (LGB_best).
- **`previsoes_por_braco.csv`** (rodada A) gravado às 01h10:52, **completo**: 33.174 linhas, 9 braços,
  `data_alvo` até **19/04/2026** (bate o recorte 2026 da emenda de 25/09 23h50). A rodada D leu esse
  arquivo às 01h11:14 — depois da A terminar, arquivo já fechado.

## Rodada C — Estabilidade das vencedoras

**Veredito: CONFIRMADO, sem ressalvas.**

- **Trava do cenário adotado** (janela 2024-01-01 a 01/02/2026, tolerância 0,2): recalculado
  h=1 MAE **97,3764** (âncora 97,4, OK) · h=12 MAE **279,9583** (âncora 280,0, OK). h=4 e h=8
  registrados sem trava: 211,31 e 270,55 — batem o log.
- **HB_best é NÃO determinístico** (`max_features=0,5145 < 1`) — as 5 sementes rodaram de fato, como
  o script decidiu corretamente (não houve atalho de 1 semente só).
- **HB_best**: MAEs por semente (h=12, recorte 2026, n=16) = 552,5 / 470,7 / 578,0 / 492,6 / 504,7 →
  média 519,69, desvio 44,27, **CV 8,52%** (>5%) e sinais mistos contra o adotado (MAE 482,88) →
  **instável**, batendo exatamente `estabilidade.csv`.
- **LGB_best**: MAEs por semente = 526,8 / 548,5 / 536,8 / 549,6 / 528,9 → média 538,11, desvio 10,67,
  **CV 1,98%** (<5%), sinal consistente (pior que o adotado nas 5 sementes) → **estável**, batendo
  exatamente `estabilidade.csv`.

## Rodada D — Calibração conformal

**Veredito: CONFIRMADO, mecânica e números batem 100% com `previsoes_calibradas.csv`,
`metricas.csv` e `familia_d.csv`** (diferença máxima de ponto flutuante: 5×10⁻⁶ num único p_holm,
irrelevante ao veredito de significância).

- **Anti-vazamento**: reimplementação própria do pool por origem, testada em 30 linhas corrigidas
  sorteadas ao acaso — **0 violações** de `data_alvo_do_par > origem` e **0 violações** de
  `data_alvo_do_par < 2022-01-01`. Correção aplicada em **4.356 de 7.212 linhas** (60,4%), idêntico ao log.
- **Cobertura** (recorte "tudo") sobe em todos os braços/horizontes com a correção: ex. `HistGB_M1`
  h=12 vai de **0,502 → 0,780** (nominal seria 0,85 — ainda abaixo, mas muito mais perto).
- **Alarmes falsos disparam** com a correção: `HistGB_M1` h=12, limiar 100, vai de **15 → 124**.
- **Família D (Wilcoxon pareado + Holm sobre 4, por recorte)** — recorte "tudo":

  | Braço | h | Perda original | Perda corrigida | Δ% | p_holm | Significativo |
  |---|---|---|---|---|---|---|
  | HistGB_M1 | 4 | 65,61 | 71,41 | **piora 8,84%** | 1,04e-9 | **sim** |
  | HistGB_M1 | 12 | 108,18 | 98,98 | melhora 8,50% | 0,188 | não |
  | HistGB_folha20_M1 | 4 | 66,64 | 72,36 | **piora 8,59%** | 2,53e-7 | **sim** |
  | HistGB_folha20_M1 | 12 | 93,86 | 88,84 | melhora 5,35% | 0,058 | não |

  **Conclusão correta:** em h=4 a correção **piora** a perda quantílica de forma estatisticamente
  significativa nos dois braços; em h=12 ela melhora, mas **não sobrevive a Holm**. Qualquer redação que
  diga o oposto (ex. "reduz a perda em h=4" ou "melhora consistente em h=12") está invertida e não deve
  ser usada em slide ou decisão.
- Recortes "2024-2025" e "2026" conferidos linha a linha contra `familia_d.csv`: nenhuma outra
  divergência de cálculo.
