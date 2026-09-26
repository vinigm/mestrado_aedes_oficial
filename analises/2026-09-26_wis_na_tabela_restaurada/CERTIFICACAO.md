# Certificação adversarial — WIS na tabela restaurada

> Agente independente, tentando REPROVAR. Todo número abaixo foi recalculado do zero, com código
> próprio (não copiado de `rodar.py`), a partir de `saidas/previsoes_quantis.csv`, do CSV bruto ou
> por retreino direto via `harness`.

## 🔴 Divergência a reportar ao orquestrador (não decidida aqui)

**A pré-declaração citada na tarefa (`analises/2026-09-26_varredura_limiar_de_decisao/PRE_DECLARACAO.md`,
emenda 1) NÃO governa esta análise.** Ela trata de outro assunto — limiar de decisão do alarme, evento
`E_421`, Youden, McNemar com block-bootstrap. Nada nela menciona WIS, quantis ou a trava de MAE.
A pré-declaração que de fato especifica esta Rodada B é
`analises/2026-09-25_segunda_bateria_noturna/PRE_DECLARACAO.md`, seção B (com emendas 25/09 23h30,
23h50 e 26/09 01h20) — foi essa que usei como referência para checar método, trava e famílias de Holm.
Sinalizo o descompasso para o orquestrador corrigir a citação; não alterei nenhuma pré-declaração.

## Veredito por item

1. **Hash da tabela** — CONFIRMADO. `sha256` = `6f34b8549009c01b39b8080b904ef69af5d209ebbcbdba9357a708fd044f6f1f`
   (bate `6f34b854…`), **725 linhas**, até `SE 202632`. `casos_confirmados` para em `SE 202617`: somei
   manualmente as 17 semanas de 2026 confirmadas = **12** casos, e as 15 semanas seguintes (`202618`–`202632`)
   estão vazias. É o estado correto — não é reintrodução de 2026.

2. **Trava (MAE q0,85)** — VÁLIDA, com **retreino independente** (script próprio, mesmos hiperparâmetros,
   chamando `harness` direto, sem reusar `rodar.py`): h=1 **97,99** · h=4 **219,67** · h=8 **272,63** ·
   h=12 **278,82**, contra o anchor 98,0/219,7/272,6/278,7 — as 4 diferenças ficam dentro da tolerância 0,2
   (máxima: 0,12 em h=12). Praticamente idêntico ao medido pelo executor (98,0/219,7/272,6/278,8).
   - Troca de anchor (desvio 1) é justificada: conferi `harness.py` linha 46 — `PAINEL_PUBLICADO` é
     exatamente `{1:98.0, 4:219.7, 8:272.6, 12:278.7}`, tolerância 0,2. É o mesmo anchor desta tarefa,
     não um número inventado pelo executor.

3. **WIS reimplementado do zero** (fórmula de Bracher et al. 2021, código independente, a partir dos
   7 quantis salvos) — bate a saída salva em todas as 16 células de modelo × h × recorte, às 6 casas
   decimais (ex.: cenário adotado h=1 2024-2025 = 101,892961 nas duas contas).

4. **Régua climatológica reimplementada do zero** (sem reusar `montar_previsoes_da_regua`), lendo a
   tabela bruta direto — bate os 4 valores salvos (292,684/313,480/322,174/324,153) e o `n=96`.

5. **Cobertura 50%/90%** recalculada junto com o WIS do item 3 — bate exatamente os percentuais do
   README (ex.: adotado h=12 2024-2025: 19,6%/51,5%).

6. **Quantis cruzados** — contagem direta da coluna `cruzamento_corrigido`: **1.784 de 2.318 origens**
   (77,0%), idêntico ao reportado.

7. **Família B (Wilcoxon pareado + Holm)** — reimplementada do zero (função Holm própria, merge próprio
   modelo×régua) — todos os 12 `p_bruto` e `p_holm` batem à saída salva, inclusive os 4 significativos.

8. **Comparação restaurada × contaminada** — diff direto dos dois CSVs: **só** cenário adotado h=1
   passa de 1% (**-2,75%**, confere com o -2,7% do README); as outras 7 células ficam ≤0,53%. O executor
   reportou a causa provável (corte de 60% em `selecionar_clima_por_ganho`, que confirmei existir em
   `dominio/selecao_features.py`) sem aprofundar — decisão correta de não decidir sozinho, mas o
   diagnóstico continua não confirmado; fica para o orquestrador decidir se vale investigar qual coluna
   de clima mudou antes de citar o número de h=1 do cenário adotado.

9. **Arquivo órfão** `trava_h4_h8.csv` — confirmado ausente na pasta. Reportado corretamente.

## Nenhuma tentativa de reprovação teve sucesso

Todos os 9 pontos auditáveis sobreviveram à reimplementação independente. O único item aberto é de
julgamento (vale aprofundar o h=1?), já corretamente escalado pelo executor, e a citação errada da
pré-declaração na tarefa, que não é erro do executor.
