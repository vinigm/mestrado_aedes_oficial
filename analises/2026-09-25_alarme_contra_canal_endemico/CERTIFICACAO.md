# Certificação adversarial — alarme contra o canal endêmico

> Certificador independente, 25/09/2026. Reimplementação escrita do zero (sem ler `rodar.py`
> antes de recalcular), a partir de `PRE_DECLARACAO.md`, do `README.md` de 13/09 e dos dados brutos
> (`previsoes_por_braco.csv` do bloco_7, `tabela_final.csv`). Script em
> `2c6301ae.../scratchpad/cert_alarme_canal.py`.

## Veredito: **APROVADO**

## 1. Trava — bate

| h | Sensibilidade | Precisão | Falsos/ano |
|---|---|---|---|
| 4 (meu / esperado) | 97,06% / 97,1% | 94,29% / 94,3% | 0,667 / 0,7 |
| 12 (meu / esperado) | 76,92% / 76,9% | 81,08% / 81,1% | 2,333 / 2,3 |

Reproduzi de forma independente (própria função de canal, própria montagem de regras), sem olhar
`rodar.py` antes. Diferença ≤0,04pp em sens/prec, 0,033 em falsos/ano — dentro da tolerância
declarada no próprio script (0,002 e 0,05) e explicada por arredondamento de "por ano" com só 3 anos
na avaliação.

## 2. Tabelas h=4/h=12, E_100 e E_canal(C_log) — batem

Recalculei os 3 canais (C_log, C_conv, C_p75) por semana epidemiológica, checando 10 valores contra
`canais_por_semana.csv`: **match exato**. As 5 regras nos 2 eventos × 2 horizontes batem com
`metricas_por_regra.csv` a **precisão de ponto flutuante** (diferença máxima 1e-16 em
sensibilidade/precisão) depois de eu replicar a regra de validade por linha do `rodar.py`: cada regra
exige o canal que ela própria usa (`M_adotado`/`M_folha20`/`R_ano_passado` só o canal do alvo;
`R_hoje`/`R_hoje_crescendo` também o da origem) — não um filtro único para as 5. Isso explica por que
o resumo textual do implementador arredondou para "n=101" em toda a tabela h=4/E_canal quando
`R_hoje` de fato usa n=100 (1 semana a menos, transparente na coluna `n_semanas` do CSV). Não é erro,
é simplificação de prosa; o CSV está certo.

## 3. McNemar + Holm — bate integralmente

Reimplementei o teste exato (via `binomtest`) e o Holm step-down do zero. As **16 comparações**
batem com `mcnemar_holm.csv` a **1e-16** de diferença, incluindo os 2 p_holm < 0,05 (M_adotado e
M_folha20 vs R_hoje, h=12, **E_100**) e o não-significativo do evento principal (M_adotado vs R_hoje,
h=12, **E_canal**: p_bruto 0,0336, p_holm 0,403).

## 4. Critério da seção 5 — corretamente não cumprido

h=12, E_canal(C_log): Youden M_adotado 0,259 > R_hoje 0,047 e > R_ano_passado 0,121 (vence as duas
descritivamente), mas p_holm=0,403 não passa em 0,05. `rodar.py` aplica exatamente essa lógica de
"E" entre Youden e significância — sem erro de sinal, sem trocar a regra de comparação.

## 5. Vazamento e alinhamento — não encontrei

- Canal usa só anos **estritamente anteriores** ao ano-alvo (`ano < ano_alvo`), nunca o próprio ano
  nem dado futuro — confirmado no código e na reprodução numérica.
- `R_hoje` usa `real` na **origem** (`data_alvo − h semanas`), não no alvo.
- `R_ano_passado` usa passo de exatos 52 semanas por data, comparado contra o canal do **alvo**
  (como a pré-declaração pede), não o canal da própria semana do ano passado.
- Denominadores de sensibilidade/precisão/especificidade não estão trocados.
- `falsos_por_ano` usa a mesma definição de 13/09 (falsos ÷ anos únicos de `data_alvo` no recorte).
- Holm rodou sobre a família certa: 16 comparações, só período de avaliação (2024+), sem misturar
  calibração.
- Semana 53/2025 (única com <3 anos de histórico) foi corretamente marcada inválida para E_canal e
  mantida válida para E_100, como o log declara.

## Divergências

Nenhuma que afete conclusão. Única nota: arredondamento de prosa do implementador ("n=101" universal
em h=4/E_canal) esconde que `R_hoje` usa n=100 nessa tabela — já corrigido no item 2, sem impacto no
veredito porque o CSV subjacente está correto e o McNemar (que é o que decide) já pareia
corretamente por linha.

Arquivo: `CERTIFICACAO.md` nesta pasta.
