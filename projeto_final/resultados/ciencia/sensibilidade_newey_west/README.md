# Sensibilidade de Newey-West nos 13 testes de h = 1

Gerado por `experimentos/sensibilidade_newey_west.py` (não editar à mão; refazer pelo script).

## O que é

- **Sensibilidade, não pré-declarada**, escrita pela **Emenda 5** da pré-declaração
  (`analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, 17/10/2026, Vinicius, depois de ver os resultados).
- **Por que existe:** em h = 1 o DM-HLN usa h − 1 = 0 autocovariâncias, mas a diferença semanal de perda tem autocorrelação de
  defasagem 1 (ACF1 ≈ 0,44 em composto × régua). Um revisor da V1 apontou isso.
- **Uso:** só no material suplementar (S3). Os vereditos **pré-declarados continuam sendo os do DM-HLN** (`familias.csv`) e
  não mudam no artigo.
- Nenhum modelo foi treinado; nenhum módulo ou resultado existente foi alterado.

## Método (Emenda 5)

- **Mesma diferença de perda pareada** de `testes_familias.py`: `d_t = |e_B,t| − |e_A,t|`, pareada por `data_alvo`
  (`parear_por_data_alvo`); positivo = A erra menos.
- **Variância da média de Newey-West** com pesos de Bartlett e **L = 4** (regra floor(4·(n/100)^(2/9)) com n ≈ 102):
  V = [γ₀ + 2 Σₖ₌₁⁴ (1 − k/5) γₖ] / n, com γₖ = Σₜ (dₜ − d̄)(dₜ₊ₖ − d̄) / n.
- **Estatística** d̄ / √V comparada à **t de Student com n − 1 g.l., bilateral**, **sem** a correção HLN.
- **Holm** reaplicado dentro de cada família (F1 a F4 inteiras, 12 ou 16 testes): p de Newey-West nos testes de h = 1 e o p bruto
  do DM-HLN (de `familias.csv`) nos de h = 4, 8 e 12.
- **Critério do piso mantido:** |Δ| > `limiar_piso` de `familias.csv` (2 × piso de ruído) e p de Holm < 0,05.
  Veredito: "A melhor", "B melhor" (aqui, "A pior") ou "sem evidencia".
- **ACF1** = γ₁ / γ₀ (mesma divisão por n do DM-HLN).

## Números-âncora

- **Reprodução do DM-HLN:** estatística e p bruto dos 13 testes de h = 1 recalculados reproduzem `familias.csv` com diferença
  < 1e-12 (trava (a); o script para se falhar). n e Δ também conferidos.
- **Holm do CSV:** reaplicar Holm ao `p_bruto` de `familias.csv` reproduz o `p_holm` (diferença máxima 0.0e+00).
- **Âncora exploratória (composto N=13 × régua sazonal, h = 1):** ACF1 ≈ 0,44 e p bruto Newey-West ≈ 0,021.
  Obtido: **ACF1 = 0.4350** e **p Newey-West = 0.0215**.

## Os 13 testes de h = 1

| Família | A × B | ACF1 da diferença | p bruto: DM-HLN → Newey-West | p de Holm: pré-declarado → sensibilidade | Veredito: antes → depois |
|---|---|---|---|---|---|
| F1 | completo@f5 x sem_casos@f5 | 0,631 | 0,0013 → 0,0654 | 0,0157 → 0,7845 | A melhor → sem evidencia |
| F1 | completo@f5 x sem_clima@f5 | 0,197 | 0,6164 → 0,6086 | 1,0000 → 1,0000 | sem evidencia → sem evidencia |
| F1 | completo@f5 x sem_vetor@f5 | 0,251 | 0,5288 → 0,6260 | 1,0000 → 1,0000 | sem evidencia → sem evidencia |
| F3 | completo@f20 x sem_casos@f20 | 0,653 | 0,0212 → 0,1205 | 0,2550 → 1,0000 | sem evidencia → sem evidencia |
| F3 | completo@f20 x sem_clima@f20 | 0,124 | 0,9145 → 0,9272 | 1,0000 → 1,0000 | sem evidencia → sem evidencia |
| F3 | completo@f20 x sem_vetor@f20 | -0,054 | 0,0829 → 0,0655 | 0,9114 → 0,7862 | sem evidencia → sem evidencia |
| F2 | so_casos@f5 x so_calendario@f5 | 0,669 | <0,0001 → 0,0208 | 0,0004 → 0,2498 | A melhor → sem evidencia |
| F2 | so_clima@f5 x so_calendario@f5 | 0,111 | 0,1564 → 0,2065 | 0,7822 → 1,0000 | sem evidencia → sem evidencia |
| F2 | so_vetor@f5 x so_calendario@f5 | 0,639 | 0,0030 → 0,0789 | 0,0334 → 0,7888 | A melhor → sem evidencia |
| F4 | completo@f5 x regua_sazonal | 0,471 | 0,0003 → 0,0202 | 0,0040 → 0,3234 | A melhor → sem evidencia |
| F4 | completo@f20 x regua_sazonal | 0,482 | 0,0195 → 0,1038 | 0,2724 → 1,0000 | sem evidencia → sem evidencia |
| F4 | composto_N13 x regua_sazonal | 0,435 | 0,0004 → 0,0215 | 0,0064 → 0,3234 | A melhor → sem evidencia |
| F4 | composto_N13 x completo@f5 | 0,164 | 0,3522 → 0,3321 | 1,0000 → 1,0000 | sem evidencia → sem evidencia |

Valores completos (precisão total) em `sensibilidade.csv`.

## Quais vereditos mudam

**5 de 13 vereditos mudam** (sensibilidade; o pré-declarado não muda):

- **F1 completo@f5 x sem_casos@f5**: A melhor → sem evidencia.
- **F2 so_casos@f5 x so_calendario@f5**: A melhor → sem evidencia.
- **F2 so_vetor@f5 x so_calendario@f5**: A melhor → sem evidencia.
- **F4 completo@f5 x regua_sazonal**: A melhor → sem evidencia.
- **F4 composto_N13 x regua_sazonal**: A melhor → sem evidencia.

## Limites

- **Fato:** o p de Newey-West com L = 4 é um estimador entre vários; o revisor obteve ≈ 0,10 com outro estimador no teste de
  composto × régua (conta exploratória, antes da emenda). O método fixado aqui é UM, relatado como sensibilidade.
- **Fato:** o ACF1 e o p dependem de n ≈ 102 semanas; L fixo em 4 para todos os testes (inclusive n = 109 em F2).
- A leitura do artigo continua sendo a pré-declarada; esta tabela só mostra quanto ela depende de ignorar a autocorrelação em h = 1.

## Conferências (17/10/2026)

- Suíte do pacote: **919 passed** antes e **919 passed** depois (`python3 -B -m pytest -q -p no:cacheprovider`).
- Reimplementação independente do Newey-West (numpy, sem importar o código novo) reproduz `p_newey_west` e `acf1` dos 13 testes, diferença máxima 2,8e-16.
- Certificação adversarial por agente independente: pendente.
