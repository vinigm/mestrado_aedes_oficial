# Pré-declaração — Bloco 5: três algoritmos com quantil, com e sem vetor

**Escrita em 23/09/2026, antes de rodar.**

## Perguntas — duas famílias independentes
1. **Outro algoritmo bate o HistGB?** A escolha do HistGB vem do grid de 30/08, que rodou contaminado.
2. **O resultado negativo do vetor depende do algoritmo?** Se os três concordam, o achado é robusto.

Só HistGB, GradientBoosting e LightGBM implementam perda quantílica — os outros 6 algoritmos do projeto
não podem rodar o cenário adotado.

## Braços — hiperparâmetros idênticos aos do grid de 30/08, quantil 0,85
HistGB, GradBoost e LightGBM, cada um em M1 (com vetor) e M0 (sem vetor). Seis braços. A seleção de clima
não olha o vetor, então M0 e M1 de um mesmo algoritmo recebem o mesmo clima.

## Família 1 — algoritmo
GradBoost_M1 e LightGBM_M1 contra HistGB_M1, 4 horizontes = **8 comparações**, Holm.
**Critério:** um algoritmo substitui o HistGB se reduzir o MAE em **h=8 E h=12** com p de Holm < 0,05.

## Família 2 — vetor
M0 contra M1 dentro de cada algoritmo, 4 horizontes = **12 comparações**, Holm.
**Leitura:** para cada algoritmo, se tirar o vetor muda o erro de forma significativa, e para que lado.
É descritivo da robustez; não troca a referência.

## Trava
HistGB_M1 tem de reproduzir o painel.
