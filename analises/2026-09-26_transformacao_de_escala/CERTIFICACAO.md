# Certificação adversarial — transformação de escala (26/09/2026)

Agente independente, medindo do zero, código próprio (não reusa `rodar.py`). Objetivo: **reprovar**.
Veredito: **relatório do executor SOBREVIVE integralmente.** Nenhuma reprovação encontrada.

---

## 1. Hash da tabela

`shasum -a 256` em `tabela_final.csv`: **`6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f`** —
bate com `6f34b854…` declarado. 726 linhas (725 dados + header) — consistente com "725 linhas" do brief.

## 2. Trava do B0

Lido direto de `../2026-09-26_wis_na_tabela_restaurada/execucao.log`, linhas 69-72:
`h=1 MAE 97.99`, `h=4 219.67`, `h=8 272.63`, `h=12 278.82` — bate exatamente com o que o executor cita, e
dentro da tolerância 0,2 do painel publicado. **VÁLIDA.** O desvio 1 (não re-rodar B0, usar log já
certificado) é razoável: o quantil 0,85 nunca foi salvo em CSV na rodada de origem.

## 3. Volta da transformação (spot-check em 4 células, não só 2)

Recalculado `max(0,transformado)**2` (T_raiz) e `max(0,expm1(transformado))` (T_log) em 2 linhas de cada
braço, direto de `previsoes_completas.csv`, contra a coluna `previsto`: as 4 batem exatamente (diferença
< 1e-6). Exemplo: T_raiz h=8, 2025-03-30, transformado=31,4145 → recalculado 986,87 = arquivo 986,87.

## 4. Cobertura acima de 421, recalculada do zero

A partir de `previsoes_quantis_finais.csv` (7 quantis do WIS), `pivot_table` reimplementado por mim,
faixa classificada pela coluna **`real`** (confirmado, não pelo previsto). Resultado idêntico ao README:

| Braço | Faixa | Semanas | IC50 | IC90 |
|---|---|---|---|---|
| B0 (âncora, `calibracao_por_faixa`) | Alerta (>421) | 163 | 8,0% | 17,8% |
| T_raiz | Alerta (>421) | 163 | 6,7% | 15,9% |
| T_log | Alerta (>421) | 163 | 3,7% | 13,5% |

Também recalculei o B0 direto de `../2026-09-26_calibracao_por_faixa/saidas/cobertura_por_faixa.csv`
(linha `cenario_adotado`): 163 sem., ic50 7,975%, ic90 17,79% — bate a âncora da pré-declaração.

## 5. MAE h=12, recalculado

Direto de `previsoes_completas.csv`, quantil 0,85, janela 2024-01-01 a 2026-02-01: **T_raiz 289,21 · T_log
299,04** — bate exatamente. Teto (B0×1,10) = 306,68 → ambos passam o critério 2.

## 6. Critério duplo aplicado como escrito?

Reimplementei a regra da seção 5 literalmente (crit1 = cobertura ≥ 0,50; crit2 = MAE ≤ 306,7; veredito só
POSITIVO se os dois). Resultado: **T_raiz NEGATIVO, T_log NEGATIVO** — idêntico ao relatado. Não houve
suavização: nos dois braços falha o critério 1 (cobertura caiu, não subiu), e a regra é aplicada de forma
literal ("se só (1) valer, NEGATIVO" — aqui nem (1) vale).

## 7. Cruzamento de quantis

Reimplementado sobre os 7 quantis brutos (excluindo 0,85) de `previsoes_completas.csv`: **1.796/2.318
(77,5%)** cruzados na escala transformada — bate. Sobre `previsoes_quantis_finais.csv` (pós-rearranjo):
**0 origens fora de ordem** nos dois braços — bate. Consistente com a construção monotônica.

## 8. Calmaria (0-20)

Medido e **não omitido**: B0 90,5%/59,2% (ic90/ic50) → T_raiz 84,2%/51,6% → T_log 80,5%/51,2%. **Piorou
nos dois braços**, como a ameaça da seção 8 cogitava — e o README relata isso como achado mais forte que o
esperado (piorou em todas as 4 faixas, não só na calmaria).

## Achados

Nenhum. Os 8 itens do brief foram checados por reimplementação independente e todos batem com o relatório
do executor, dentro de tolerância numérica desprezível (<1e-6 nos casos determinísticos). O critério duplo
foi aplicado sem suavização, os desvios foram reportados (não decididos em silêncio) e a hash confirma a
tabela restaurada. **Certificação: APROVADA. Veredito NEGATIVO do executor se sustenta.**
