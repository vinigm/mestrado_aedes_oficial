# Pré-declaração — Bloco 7: o vetor no HistGB com folha mínima 20

**Escrita em 24/09/2026 às ~02h30, antes de rodar.** Bloco acrescentado durante a noite, depois de ler os
blocos 5 e 6. Mudança posterior vira emenda datada no fim.

## ⚠️ Natureza deste bloco: exploratório

A hipótese nasceu de resultados já vistos. O bloco 6 mostrou, de forma **descritiva**, que o HistGB com
`min_samples_leaf=20` se comporta como o LightGBM do bloco 5 — pior na calibração, melhor em h=8 e h=12
na avaliação. A avaliação 2024+ do HistGB com folha 20 **com vetor** já foi vista. O que **não** foi visto é
o mesmo modelo **sem vetor**.

Por isso este bloco testa um **mecanismo**, e não a hipótese da tese. Um resultado positivo aqui não
confirma que o vetor melhora a previsão: indica onde vale uma pré-declaração confirmatória de verdade.

## Pergunta
No bloco 5, o vetor reduziu o erro de 3 meses do LightGBM em 15,5% (p Holm 0,0001) e não mudou nada no
HistGB. O bloco 6 sugere que a diferença entre os dois é a folha mínima, 20 no LightGBM e 5 no HistGB.
**Se a folha mínima é o mecanismo, o vetor deve ajudar o HistGB com folha mínima 20.**

## Braços — 12 horizontes
| Braço | Modelo | Vetor |
|---|---|---|
| referencia | HistGB, folha mínima 5 — o cenário adotado | com |
| HistGB_folha20_M1 | HistGB, `min_samples_leaf=20`, demais iguais à referência | com |
| HistGB_folha20_M0 | idem | sem |

## Teste
M0 contra M1 do HistGB com folha 20, pareado por `data_alvo`, Wilcoxon, horizontes 1, 4, 8 e 12,
**Holm sobre 4 comparações**. Leitura descritiva nos 12 horizontes.

## Critério de leitura
O mecanismo é **apoiado** se tirar o vetor aumentar o erro em h=12 com p de Holm < 0,05. É **contrariado**
se não aumentar. Nenhum resultado aqui troca a referência.

## Trava
A referência tem de reproduzir o painel. E o HistGB_folha20_M1 tem de reproduzir, em h=1, 4, 8 e 12, os
números da mesma configuração no bloco 6 (`lr0.05_it250_folhas15_min20`), já que o modelo é determinístico.
