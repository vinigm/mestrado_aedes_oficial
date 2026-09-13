# Vetor no modelo calibrado — 30/08/2026

> **A pergunta:** com o modelo bem calibrado (HistGradientBoosting, quantil 0,85), o vetor
> (armadilhas) ainda acrescenta informação sobre o que o clima já explica?
> **A resposta:** M1 (com vetor) tem MAE menor em 6 de 8 comparações, mas **nenhuma** sobrevive à
> correção de Holm (p_holm = 1,0 em todas as 8). Indício de direção, sem significância.
> Status: ⚠️ exploratório / indício sem significância. Pré-declaração: sim, `PRE_DECLARACAO.md` (30/08/2026).

## 1. Por que este teste foi feito

- Todos os testes anteriores de "o vetor ajuda a prever dengue?" rodaram com **perda padrão**
  (erro quadrático) — que já se sabia **enviesada para baixo nos picos**.
- Dúvida em aberto: se o modelo estava mal calibrado, os testes anteriores podem ter medido a
  **limitação do modelo**, não a informação real do vetor.
- Este teste roda o vetor contra o **modelo já calibrado** (quantil 0,85), validado em 30/08/2026
  fora do período de calibração, para isolar o efeito do vetor da qualidade da calibração.
- A **pré-declaração** (escrita antes de rodar) fixou 3 desfechos possíveis:
  1. M1 vence e sobrevive a Holm → vetor acrescenta informação, reabre o eixo entomológico da tese;
  2. M1 vence mas não sobrevive a Holm → indício, sem achado;
  3. M1 não vence → redundância vetor-clima fica mais forte, vira o achado mais sustentado.
  - A pré-declaração chamava o **desfecho 3** de "mais provável dado tudo que já medimos".

## 2. Como foi medido

- **Algoritmo:** `HistGradientBoostingRegressor` (`max_iter=250`, `learning_rate=0,05`,
  `max_leaf_nodes=15`, `min_samples_leaf=5`).
- **Perdas:** `padrao` (erro quadrático) e `quantil_0.85` (a perda estima o percentil 85 da
  distribuição condicional, não a média — reduz o viés de subestimar picos).
- **Dois conjuntos de features:**
  - **M0** (14 colunas) = núcleo + 6 variáveis de clima selecionadas por ganho, **sem vetor**;
  - **M1** (20 colunas) = M0 + 6 colunas do vetor (`aedes_aegypti_por_armadilha` + 4 defasagens +
    `vetor_mm4`, média móvel de 4 semanas).
- **Horizontes:** 1, 4, 8 e 12 semanas · **passo = 1** (walk-forward semana a semana).
- **16 execuções** = 2 perdas × 2 conjuntos × 4 horizontes.
- **Separação:** calibração até **31/12/2023** (3.044 linhas, só conferência) · avaliação **desde
  2024** (1.688 linhas, ~102 semanas pareadas por combinação) — o veredito usa só a avaliação.
- **Comparação pareada M0×M1** (mesmo `h`, `data_alvo`, `real`) via **Diebold-Mariano** (teste de
  diferença de erro entre previsões pareadas) + correção de **Holm** sobre as 8 comparações
  (2 perdas × 4 horizontes), α = 0,05.

## 3. O que deu

| perda | h | n | MAE sem vetor | MAE com vetor | ganho MAE | DM p (Holm-8) | significativo |
|---|---|---|---|---|---|---|---|
| padrão | 1 | 102 | 102,19 | 113,01 | −10,82 | 1,000 | Não |
| padrão | 4 | 102 | 182,63 | 170,49 | +12,13 | 1,000 | Não |
| padrão | 8 | 102 | 212,67 | 183,13 | +29,53 | 1,000 | Não |
| padrão | 12 | 102 | 205,30 | 203,41 | +1,89 | 1,000 | Não |
| quantil 0,85 | 1 | 102 | 91,98 | 97,99 | −6,00 | 1,000 | Não |
| quantil 0,85 | 4 | 102 | 180,57 | 168,71 | +11,86 | 1,000 | Não |
| quantil 0,85 | 8 | 102 | 179,01 | 178,35 | +0,66 | 1,000 | Não |
| quantil 0,85 | 12 | 102 | 199,03 | 184,20 | +14,84 | 1,000 | Não |

- Números conferidos direto nos CSVs (`vetor_comparacao.csv`, `vetor_previsoes.csv`, 4.732 linhas) —
  batem exatamente com o log e com o contexto passado.
- **M1 (com vetor) vence em 6 de 8** — perde só em h=1, nas duas perdas (h curto é dominado pela
  autocorrelação da própria série, o vetor não acrescenta).
- **0 de 8 sobrevivem a Holm**, p_holm = 1,0 em todas — a correção por múltiplas comparações zera
  qualquer leitura de significância.
- Viés de pico (`vies_pico_*`, só semanas com real > 100) segue **negativo em todas as células**
  (modelo subestima pico) tanto com quanto sem vetor — o vetor não resolve o viés de pico.

## 4. Conclusão

- **FATO:** M1 tem MAE menor em 6/8 combinações perda×horizonte no período de avaliação (2024+),
  mas nenhuma diferença sobrevive à correção de Holm (α=0,05, 8 comparações).
- **FATO:** o desfecho realizado foi o **2** da pré-declaração ("indício sem significância") — não
  o desfecho **3** ("vetor não vence"), que a pré-declaração classificava como mais provável.
- **HIPÓTESE, não FATO:** que o vetor tenha valor preditivo real em h=4/h=8/h=12 mesmo com modelo
  calibrado — a direção é favorável, mas o teste não tem poder estatístico para confirmar isso.
- **Não se pode afirmar:** que calibrar o modelo "reabre" o valor do vetor — o resultado é
  estatisticamente indistinguível de ruído, igual aos testes anteriores com perda padrão.

## 5. Ressalvas e o que ficou em aberto

- Amostra pequena para Diebold-Mariano (n=102 por célula) — poder estatístico baixo, compatível com
  "indício não detectável" mesmo que o efeito real exista.
- Sem repetição por seed — walk-forward determinístico (`random_state=42`), não há intervalo de
  confiança sobre o próprio ganho de MAE, só o teste pareado.
- `alpha=0,90` do quantil ficou fora deste teste (reservado para o grid noturno) — não se sabe se o
  padrão se mantém em outra calibração.
- Calibração (até 2023) entrou só como conferência, não é reportada aqui — não registrada nesta
  pasta além do que o script imprime internamente (o CSV de previsões contém as linhas, mas a
  comparação pareada com DM só foi calculada para a avaliação).

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- Este script **implementa seu próprio walk-forward** (`rodar_walk_forward`): ordena por `data`
  (origem) e corta por `iloc[:indice_corte]` — o mesmo padrão de corte por data de origem descrito
  no vazamento, sem excluir as `h-1` linhas de treino cujo rótulo (`y_h`, datado origem+horizonte)
  cai depois da `data_alvo` da semana testada.
- Este teste está **explicitamente na lista dos NÃO refeitos** em 13/09/2026.
- Direção provável do viés: MAE **subestimado** (otimista) em todas as células, mais forte em
  horizontes maiores — coerente com o **+52% de MAE em h=12** medido na correção da configuração de
  referência.
- Como o vazamento afeta M0 e M1 pela mesma mecânica de corte, **não está medido** se ele infla ou
  reduz especificamente o `ganho_MAE` (a vantagem do vetor) — só que os MAEs absolutos aqui relatados
  são otimistas. Refazer o teste com o corte corrigido é pré-requisito para qualquer uso destes
  números fora deste registro histórico.

## 7. Arquivos

- `PRE_DECLARACAO.md` — pré-declaração dos 3 desfechos, desenho e regras de decisão, escrita antes de rodar.
- `testar_vetor_calibrado.py` — script único: monta M0/M1, roda os 16 walk-forwards, calcula DM + Holm.
- `saidas/vetor_previsoes.csv` — 4.732 linhas, previsão semana a semana por perda/conjunto/horizonte.
- `saidas/vetor_comparacao.csv` — 8 linhas, a tabela da seção 3 (MAE, DM, Holm, significância).
- `saidas/vetor_log.txt` — saída de execução do script (tempos por etapa, 46,5 min no total).
