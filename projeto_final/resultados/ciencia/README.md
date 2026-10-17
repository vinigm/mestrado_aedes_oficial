# A ciência do artigo (E1 a E5) — resultados certificados

> Rodada de 12/10/2026, conforme a pré-declaração aprovada pelo Vinicius em 12/10, com as emendas 1 a 3:
> `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md` (hash em `PRE_DECLARACAO.sha256`).
> Tudo foi rodado no pacote `projeto_final`, e cada etapa foi certificada por um agente independente
> (`certificacao/*/CERTIFICACAO.md`). A estatística foi reimplementada do zero e não apresentou nenhuma divergência numérica.
> O método dos testes foi fixado antes de rodar: `estatistica/METODO_ESTATISTICO.md`.

## Pergunta

Quanto o histórico de casos, o clima e a captura de mosquitos contribuem para prever casos confirmados de dengue em
Porto Alegre, de 1 a 12 semanas à frente?

## Método, em uma linha por etapa

- **E1:** quantil da perda escolhido só pela calibração (alvos até 31/12/2023).
- **Piso:** 5 perturbações de último bit no modelo completo (folhas 5 e 20).
- **E2:** 8 braços × 2 folhas × 12 h, walk-forward com corte pela resposta.
- **E3:** composto que, em cada semana, usa a folha de menor erro nas últimas 13 semanas já conhecidas.
- **E4:** o mesmo modelo, cortado pela data da entrada.
- **E5:** alarme no limiar 421 × r.
- **Testes:**
  - Diebold-Mariano com correção HLN, pareado por semana-alvo, com Holm dentro de cada família (F1 a F3 com 12 testes; F4 com 16);
  - IC 95% por bootstrap de blocos (8 semanas, 2.000 reamostragens);
  - o veredito exige p de Holm < 0,05 **e** |Δ| > 2 × piso.

## Âncoras

- **Referência reproduzida com diferença 0,0.** MAE do completo:
  - folha 5: 97,987 · 219,669 · 272,627 · 278,818 (h = 1, 4, 8, 12);
  - folha 20: 133,626 · 199,635 · 223,183 · 243,765.
- **Régua sazonal:** 202,108 · 213,176 · 216,167 · 217,784.
- **Pareamento:** 102 semanas-alvo por horizonte nos braços com vetor; 109 nos braços sem vetor.
- **Previsões:** 57.520 na E2; 9.660 no composto.

## Resultados

### E1 — quantil

- **O 0,85 continua.** É o melhor na calibração, com MAE médio de 42,02. O 0,80 fica 1,7% pior.
- ⚠️ Fora da amostra, na calibração, o caso real fica acima da previsão em **33% a 43%** das semanas, e não nos 15% nominais.

### Piso de ruído (2 × piso = limiar)

| | h = 1 | h = 4 | h = 8 | h = 12 |
|---|---|---|---|---|
| Folha 5 | 10,4 | 24,6 | 25,4 | 14,0 |
| Folha 20 | 2,7 | 4,4 | 27,1 | 20,4 |

- Ignorar o piso **não muda nenhum veredito**.

### Vereditos (52 testes: 5 "melhor", 0 "pior", 47 "sem evidência")

| Família | O que passa | Horizonte |
|---|---|---|
| F1 (folha 5): o que cada fonte acrescenta | **Casos**: Δ = +118,3 casos, +54,7% [22,3; 72,1], p de Holm 0,016 | só h = 1 |
| F2 (folha 5): fonte sozinha × calendário | **Casos sozinhos** (p de Holm 0,0004) e **vetor sozinho** (+20,5%, p de Holm 0,033) | só h = 1 |
| F3 (folha 20, exploratória) | nada | — |
| F4: modelo × régua | **Completo folha 5** (+51,5%, p de Holm 0,004) e **composto** (+49,4%, p de Holm 0,006) vencem a régua | só h = 1 |

- **Clima:** não há evidência de contribuição em nenhum horizonte. Descritivamente, **piora** o erro em 8 e 12 semanas: −27% na folha 5 e −30% na folha 20 em h = 12. O IC do bootstrap exclui zero, mas o p de Holm é 1,0.
- **Vetor:** com casos e clima no modelo, não há evidência de contribuição em nenhum horizonte nem em nenhuma folha.
  - Folha 5: Δ = −6,0 · −0,3 · −19,6 · +6,2.
  - Folha 20: Δ = +8,1% em h = 8 e +12,3% em h = 12; o p de Holm é 1,0.
- **Régua:** a partir de 4 semanas, nenhum modelo se distingue dela. Descritivamente, a régua erra menos em 8 e 12 semanas.
- **Composto × folha 5:** sem evidência. MAE do composto: 102,3 · 205,7 · 233,5 · 260,1. Ele usa a folha 20 em 31% a 67% das semanas.

### E4 — sensibilidade do corte (descritiva)

- **Com o corte pela entrada, o MAE parece 11% a 44% menor** (base: o corte pela resposta).
  - Em h = 12, −33,9%, e o R² fica 0,31 ponto maior.
  - A âncora de 13/09 (+52% sobre o corte ingênuo) foi reproduzida: +51,4%.
- **O corte pela entrada favorece o vetor.** Δ(V) na folha 5, pareado:

  | h | Corte pela resposta | Corte pela entrada |
  |---|---|---|
  | 4 | −0,3 | +11,9 |
  | 8 | −19,6 | +0,7 |
  | 12 | +6,2 | +14,9 |

  ✅ Conferida por recontagem independente em 15/10/2026 (diferença zero nos 8 valores).

### E5 — alarme (descritivo)

- **Razão e limiar:** r = 12.778 / 12.033 = **1,0619** (notificação ÷ residência, 2018 a 2023); **L = 447,07**.
- **Definição do evento:** a do código antigo (real > L e previsto > L, contado por semana). Falsos por ano = FP ÷ 1,96.

  | Modelo | Horizonte | Sensibilidade | Precisão | Falsos por ano |
  |---|---|---|---|---|
  | Folha 5 | h = 1 | 0,958 | 0,958 | 0,51 |
  | Folha 5 | h = 4 | 0,963 | 0,897 | 1,53 |
  | Folha 5 | h = 8 | 0,643 | 1,000 | 0 |
  | Folha 20 | h = 8 | 0,857 | 1,000 | 0 |
  | Composto | h = 8 | 0,821 | 1,000 | 0 |

- ⚠️ Há poucas semanas de surto na avaliação: 24, 27 e 28 em h = 1, 4 e 8.

## Hipóteses pré-declaradas

| Hipótese | Resultado |
|---|---|
| H1 — casos pesam no curto prazo | Confirmada em h = 1. Em h = 4, sem evidência. |
| H2 — clima acrescenta pouco | Coerente: sem evidência. Descritivamente, piora nos horizontes longos. |
| H3a — vetor, folha 5: sem contribuição | Coerente. |
| H3b — vetor, folha 20: contribui em h = 8 e 12 | **Não se sustenta**: sem evidência. |
| H4 — cada fonte sozinha tem sinal | Casos ✓ e vetor ✓ (só h = 1); clima ✗. |

## Ressalvas dos certificadores

- **O teste DM-HLN é anticonservador em h ≥ 4 com n = 102.** Sob a hipótese nula, ele rejeita 6,8% a 11,1% das vezes, em vez de 5%.
  - Isso torna os vereditos "sem evidência" ainda mais robustos.
  - Os 5 vereditos positivos estão em h = 1, onde o tamanho do teste é correto.
- **Bootstrap × DM em h = 12:** em alguns testes, o IC do bootstrap exclui zero e o DM-HLN, não.
  - Hipótese a investigar: blocos de 8 semanas são curtos para erros de 12 semanas à frente.
  - Vale o veredito pela regra pré-declarada.
- **Piso:** foi medido só no braço completo e aplicado aos demais.
- **Âncora do numerador da razão:** 12.778 contra 12.785 da tabela (−0,055%). A diferença está em 2023 (fronteira de ano).

## Arquivos

- `estatistica/familias.csv`: os 52 testes, linha a linha.
- `E3_composto/resumo.csv`
- `E5_alarme/alarme.csv`
- `E4_corte/comparacao.csv`
- `piso_de_ruido/piso.csv`
- `E1_quantil/decisao.json`
- `certificacao/{E1_piso, E2, E4_integridade, estatistica, E5}/CERTIFICACAO.md`
