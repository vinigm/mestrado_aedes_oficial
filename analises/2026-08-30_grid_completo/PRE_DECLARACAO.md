# PRÉ-DECLARAÇÃO — grid completo (30/08/2026, noturno)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## Objetivo

Bater o martelo sobre a configuração de referência do projeto, testando os três eixos de uma vez em
vez de decidir por partes.

## O grid

| eixo | valores | qtd |
|---|---|---|
| algoritmo | `hist_gradient_boosting`, `gradient_boosting`, `lightgbm` | 3 |
| perda | padrão + quantil **0,70 · 0,80 · 0,85 · 0,90** | 5 |
| features | **M0** (sem vetor) · **M1** (com vetor) | 2 |
| horizonte | 1, 4, 8, 12 semanas | 4 |

**= 120 execuções de walk-forward**, `passo=1` (~300 pontos por horizonte).

**Só estes 3 algoritmos entram** porque são os únicos dos 9 do projeto que aceitam perda quantílica
(pinball). Os outros 6 não têm o método — e os 3 que entram são justamente os 3 melhores na perda
padrão (0,779 · 0,762 · 0,749).

## Protocolo de escolha

- **calibração:** semanas-alvo até **31/12/2023** — é onde a configuração vencedora é escolhida;
- **avaliação:** **2024 em diante** — não participa da escolha, só do veredito.

**Critério de escolha, fixado agora:** menor **MAE global médio** entre os 4 horizontes, no período
de **calibração**. Reporto também o viés no pico, mas o critério de escolha é o MAE — viés é o
problema que a calibração ataca, e usá-lo para escolher favoreceria alphas altos por construção.

## Teste do vetor

Para a configuração vencedora, comparo **M0 × M1** com **Diebold-Mariano** pareado e correção de
**Holm** sobre os 4 horizontes, no período de avaliação.

## ⚠️ Ressalva de comparações múltiplas — declarada antes

São **30 configurações** competindo (3 × 5 × 2). Escolher a melhor entre 30 garante que **parte da
vantagem do vencedor é sorte**. A separação calibração/avaliação reduz o problema mas não o elimina.

**Consequência para o texto:** a afirmação honesta é *"a melhor entre as 30 configurações
testadas"*, **nunca** *"a melhor configuração possível"*. E a diferença entre as primeiras colocadas
deve ser reportada — se for pequena, dizer explicitamente que são indistinguíveis.

## Regras de decisão

1. **HistGradientBoosting vence** → confirma a escolha atual; a configuração de referência fica
   fechada.
2. **Outro algoritmo vence por margem pequena** (< 5% de MAE) → declarar empate técnico e manter o
   HGB por continuidade, registrando a proximidade.
3. **Outro vence por margem grande** (≥ 5%) → trocar a referência do projeto, com a mudança
   registrada e datada.

**Proibido:** rodar de novo com outros valores depois de ver o resultado, para procurar melhora.
