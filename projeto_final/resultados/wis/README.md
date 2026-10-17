# E7 — WIS, a métrica secundária (12/10/2026)

> Pré-declaração aprovada pelo Vinicius em 12/10/2026: `analises/2026-10-12_pre_declaracao_reproducao_e_wis/PRE_DECLARACAO.md`, §5.
> Certificada e reimplementada do zero por agente independente (`certificacao/RELATORIO_CERTIFICACAO_E7.md`, APROVADO,
> sem nenhuma divergência numérica).

## Método

- **Quantis:** 7 (0,05 a 0,95), um HistGB por quantil, nas folhas 5 e 20, em h = 1 a 12; quantis ordenados quando se
  cruzam.
- **WIS:** fórmula de Bracher (2021), com K = 3.
- **Régua:** climatológica.
- **Composto:** usa os quantis da folha que a E3 escolheu.
- **Testes:** família F5, com 12 testes DM-HLN e Holm, sem piso de ruído.

## Reprodução de 26/09

As **16.226 previsões** dos 7 quantis são iguais às antigas (diferença 0,0), e o WIS na janela antiga bate as âncoras.

## Resultado na janela padrão (07/01/2024 a 01/02/2026)

| h | Folha 5 | Folha 20 | Composto | Régua climatológica |
|---|---|---|---|---|
| 1 | 97,0 | 115,5 | 106,2 | 278,3 |
| 4 | 205,0 | 189,5 | 188,5 | 298,1 |
| 8 | 275,0 | 246,9 | 248,0 | 306,3 |
| 12 | 286,3 | 265,3 | 279,5 | 308,2 |

- **Família F5 (12 testes, n = 101):**
  - **só h = 1 passa**: folha 5, folha 20 e composto vencem a régua climatológica, com WIS 58% a 65% menor e p de Holm < 0,001;
  - em h = 4, 8 e 12, sem evidência, embora os três modelos tenham WIS 6% a 36% menor (p de Holm de 0,18 a 0,98).
- **Cobertura abaixo do nominal nos três modelos** (janela padrão, h = 1 a 12): intervalos de 50% cobrem de 12% a 42% das
  semanas, os de 80% de 36% a 74% e os de 90% de 49% a 85%. Os intervalos são estreitos demais. A régua climatológica
  cobre ainda menos: 20% a 21%, 34% a 37% e 39% a 43%.

## Ressalvas

- **A régua tem n = 101:** 28/12/2025 é semana 53, e só 2020 teve semana 53 desde 2018, o que dá menos de 3 anos de
  histórico.
- **Cruzamentos de quantis em 65% a 89% das origens.** Sem ordenar, o WIS subiria de 0,7% a 3,9%. A ordenação está no
  Método.
- **O quantil 0,05 é negativo em até 8,8% das origens**, porque não há truncamento em 0, como no antigo.
- ⚠️ **Mudança em relação a 26/09:** com Wilcoxon, o antigo dizia que em h = 4 os modelos venciam a régua
  climatológica (p de Holm 0,000035). Com o DM-HLN, que considera a autocorrelação, a vantagem de 31% a 36% em h = 4
  **não se confirma** (p de Holm 0,18 a 0,29).

## Arquivos

- `wis_resumo.csv` (h = 1 a 12, com cobertura)
- `familia_F5.csv`
- `previsoes_quantis*.csv`
- `regua_climatologica.csv`
- `cruzamentos.csv`
