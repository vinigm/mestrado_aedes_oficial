# CERTIFICAÇÃO ADVERSARIAL — régua de regras simples

**Certificador:** agente independente (Sonnet 5), 25/09/2026. Reimplementação do zero, sem olhar
`calcular_regua.py` antes de recalcular. Código em
`/private/tmp/claude-501/.../scratchpad/regua_independente/reimplementacao.py`.

## Veredito

🔴 **NÃO APROVADO** — não por erro de método ou de números, mas por um **erro de contagem no
relatório** (README_RASCUNHO.md) que não bate com a própria tabela que o script gerou.

## O que recalculei e bateu 100%

- **Todas as 53 âncoras numéricas do brief batem exatamente** (MAE, perda quantílica 0,85 e n dos 3
  bracos e das 3 regras em h=1,4,8,12; MAE por ano em h=12 para 2022-2026; teto de previsão).
- **Skill score** (1 − MAE_modelo/MAE_melhor_regra) e **Wilcoxon pareado vs sazonal em h=12**
  (referencia p=0,004159; folha20_M1 p=0,3577; LightGBM_M1 p=0,1654; n=102) batem com as saídas do
  outro agente até a casa decimal.
- **real == casos_confirmados**: 0 divergências, nos 3 bracos, em todas as 3.474 linhas (não só na
  janela de avaliação).
- **Grade de (h, data_alvo):** confirmei que `referencia`, `HistGB_folha20_M1` e `LightGBM_M1` têm
  exatamente as mesmas 102 datas-alvo por h em 2024+; usar só o braço `referencia` como grade (decisão
  do outro agente) é neutro, não inflaciona nem filtra nada.
- **Nenhuma regra simples perdeu linha por NaN** na janela de avaliação (2024+, h=1..12).
- Reimplementei a correção de Holm do zero (cummax dos p-ajustados) e o resultado bate com a coluna
  `p_holm` do CSV deles a 1e-15 — a implementação de Holm está **correta**.

## O erro que achei

`saidas/comparacoes_pareadas_holm.csv` (família de 72 = 9 bracos × 2 regras × 4 h) tem **27
comparações com `significativo_5pct=True`**, não 18. Recalculei Holm independentemente e bati com a
coluna deles — o CSV está certo. O erro está no **texto**:

- `README_RASCUNHO.md` linha 156: **"18 de 72 comparações sobrevivem a Holm"** — deveria ser **27**.
- A mesma contagem errada (18/72) foi repassada no resumo que me chegou como "o que o outro agente já
  concluiu".
- Sub-contagens também erram por braço: "sazonal em h=1, 4 bracos significativos" → são **5**
  (falta `HistGB_M0`); "2 bracos M0 perdem para sazonal em h=12" → são **3** (falta `HistGB_M0`,
  que também perde para sazonal em h=12).
- Busquei em `execucao.log`: o script só imprime "Família de Holm: 72 comparações", nunca o número
  18 — ou seja, o "18" foi escrito à mão no README, não gerado pelo código. Não é bug de método;
  é erro de transcrição do relatório.

**Por que importa:** a conclusão qualitativa central (persistência perde em h=8/12, sazonal não é
batida com significância em h=4/h=8) continua de pé. Mas o relatório subestima a evidência real —
há mais vitórias/derrotas significativas do que o texto admite, e quem ler só o resumo (como eu recebi)
tira uma foto errada do quanto sobrevive a Holm.

## Recomendação

Corrigir a contagem e as duas sub-listas em `README_RASCUNHO.md` (18→27, 4→5, 2→3, citando
`HistGB_M0`) antes de qualquer uso do documento na tese. Não mexi no README nem no CSV — só
constatei a divergência.
