# Regeneração oficial — 29–30/08/2026

**Motivo:** a recaptura do clima (Rodada 0 de 29/08) mudou a `tabela_final`. Todo resultado
oficial de 16/08 tinha sido calculado com o clima truncado em 2018 — os números publicados no
painel e citados nos documentos **não reproduziam mais**.

**Execução:** 16 experimentos em sequência, 29/08 14:45:56 → 30/08 00:18:04 (**9h32**).
**16 de 16 com sucesso, zero falhas.** Gargalo: `hist_gradient_boosting`, **188 min** sozinho.

---

## O que mudou (`comparacao_antes_depois.csv`)

**17 dos 20 arquivos mudaram de valor.** Os 3 idênticos são legitimamente idênticos:

- `bairro_vetor_r2_resultados.csv` — lê o **parquet**, não a `tabela_final`. Não podia mudar com o
  clima, e não mudou. **É a checagem de sanidade da regeneração inteira.**
- `surto_notificados_*` — já haviam rodado na tabela nova; não entraram nesta bateria.

Maiores mudanças: `diebold_mariano` (979%), `deteccao_surto_mcnemar` (874%),
`comparacao_casos` (312%), regressão-núcleo (40%).

---

## O achado principal: o vetor é SUBSTITUTO do clima, não complemento

**FATO — somar o vetor ao clima piora** (`lift_limpo_resultados.csv`, R²):

| h | só clima | clima+vetor | só vetor |
|---|---|---|---|
| 1 | 0,813 | **0,822** | 0,804 |
| 4 | **0,769** | 0,688 | 0,685 |
| 7 | **0,714** | 0,568 | 0,676 |
| 9 | 0,606 | 0,650 | **0,773** |
| 12 | 0,595 | 0,560 | **0,671** |

- juntar as duas fontes **piora em 11 dos 12 horizontes**; o único ganho (h=1, +0,009) é ruído;
- **mas o vetor sozinho frequentemente vence o clima sozinho** — em h=9, 0,773 contra 0,606.

**FATO — o Diebold-Mariano concorda:** com corte de maturidade o vetor ajuda em h=6–12
(dMAE **+7,5 a +18,3**), mas o melhor p é **0,065** e são 24 comparações. Nada sobrevive.

**Leitura:** as duas fontes carregam informação sobreposta. Somadas, dobram a dimensionalidade sem
trazer sinal novo. Isso explica por que a equivalência fecha (Rodada 2) e por que o lift nunca fecha.

---

## O problema em aberto: os dois alvos se contradizem

`investigar_contradicao_alvos.py` mediu três coisas.

### 1. O resultado dos confirmados SOBREVIVE à correção múltipla

| alvo | pctl | h | n | clima>vetor | vetor>clima | p exato | Holm (6) | Holm (12) |
|---|---|---|---|---|---|---|---|---|
| confirmados | 90 | 12 | 279 | 4 | **24** | **0,00018** | **0,00108** ✅ | **0,00216** ✅ |
| confirmados | 95 | 12 | 279 | 5 | 17 | 0,0169 | 0,0845 | 0,186 |
| notificados | 90 | 12 | 553 | 14 | 10 | 0,541 | — | 1,000 |

**É o primeiro resultado do projeto que sobrevive a Holm**, inclusive contando as 12 comparações
do dia inteiro.

### 2. ⚠️ CORREÇÃO — eu disse que o sinal era instável. Estava errado.

Afirmei em 29/08 que "o significativo pulou de h=8 para h=12, e efeito real não faz isso".
Conferindo execução contra execução no **mesmo alvo**:

| pctl | h | 16/08 | 30/08 | leitura |
|---|---|---|---|---|
| 90 | 12 | 9×20, p=0,061 | 4×24, **p=0,00018** | mesma direção, **mais forte** |
| 95 | 12 | 7×9, p=0,80 | 5×17, **p=0,017** | mesma direção, **mais forte** |
| 90 | 8 | 4×14, p=0,031 | 5×10, p=0,30 | enfraqueceu |

O h=12 **já estava presente e favorável em 16/08** e ficou mais forte com 18% mais dados — que é a
assinatura de efeito **real**, não de ruído. O que era ruído era o h=8. Minha leitura anterior
inverteu o diagnóstico.

### 3. As duas séries não medem o mesmo evento

- concordância geral: 88,0%, mas **sobreposição (Jaccard) das semanas de surto: só 64,0%**;
- 34 semanas são surto só para notificados; 11 só para confirmados.

### 4. 🚨 ERRO DE DESENHO MEU NA RODADA 1

A pré-declaração dizia *"idêntico ao `cidade_deteccao_surto`, mudando SÓ o alvo"*. **Isso era falso.**

| | confirmados | notificados |
|---|---|---|
| janela | 2018-02 em diante | 2012-09 em diante |
| semanas com **denominador aproximado** | ~0% | **45,8%** |

Estender a série para trás não mudou só o alvo — **mudou a qualidade da medição do próprio vetor**.
De 2012 a 2018 a Secretaria não registrava se a vistoria acontecia (`inspecao_realizada` nula em
324 semanas), então a densidade dali é aproximada.

**O experimento de notificados alimentou o modelo com um vetor degradado em quase metade da
amostra.** A conclusão "o vetor não ajuda no alarme de surto" está **confundida**: pode ser o alvo,
pode ser o ruído de medição.

**Teste decisivo pendente:** rodar o McNemar de notificados **restrito a 2019+** (denominador
exato). Aí a única diferença para o experimento de confirmados passa a ser o alvo. ~35 min de CPU.
**Não rodado — aguarda autorização.**
