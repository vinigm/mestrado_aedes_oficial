# Certificação adversarial — rodadas A e B (segunda bateria noturna)

**Certificador independente, 25/09/2026 23h57.** Conferido do zero, sem reusar código das rodadas.

## Veredito: NADA A CERTIFICAR AINDA

Ambas as rodadas seguem **em execução**, não terminaram. Não existe nenhum CSV nem PNG de saída em
`A_resultados_em_2026/saidas/` nem em `B_quantis_e_wis/saidas/` (as duas pastas estão vazias — conferido
por `find`). Não há "previsões gravadas" para recalcular MAE, WIS, Wilcoxon/Holm ou alarmes: qualquer
número que eu calculasse agora seria sobre dado inexistente.

- **Processos confirmados rodando de fato** (`ps aux`, 23h56:
  - Rodada A: PID `64667`, ativo, 98,9% CPU. Log mostra só o braço 1/8 (`HistGB_M1`), h=4 de 12 concluído.
  - Rodada B: processo pai PID `64193` vivo; log em `execucao.log` avançou até a combinação 24/56
    (`cenario_adotado h=12 q=0.25`), consistente com o resumo recebido (~18-43% concluído).
- **Nenhum sinal de trava violada, vazamento ou crash** pôde ser checado, porque a trava só é avaliada
  pelo próprio `rodar.py` ao FINAL de cada rodada (conforme a pré-declaração: "Travas antes de ler
  resultado"). Ler os logs parciais não substitui a trava.
- **Recomputação independente (MAE, WIS, Holm, treino do zero) fica pendente** até existirem os CSVs
  em `saidas/`. Não faz sentido reimplementar métricas contra um vetor de previsões parcial e em
  progresso — o resultado mudaria a cada minuto e não é o que a pré-declaração define como unidade de
  certificação.

## Por que não forçar uma "certificação parcial"

- A pré-declaração (`PRE_DECLARACAO.md`) define a trava e as famílias A1/A2/A3 e B sobre a rodada
  **completa**; braço 1 de 8 (A) e 24 de 56 (B) não é a unidade certificável.
- Forçar conclusão sobre dado parcial violaria a regra do projeto de nunca fingir que uma verificação
  foi feita quando a evidência não sustenta — e um HistGB_M1 com só 4 dos 12 horizontes não permite
  nem repetir o teste de trava (exige h=1 e h=12 juntos).

## Próximo passo

- Reconferir quando `execucao.log` de cada rodada mostrar "CONCLUÍDA" (ou equivalente) e os CSVs
  aparecerem em `saidas/`. Estimativa por precedente (bloco 5, 23/09): rodada A ~2h-2h30 do início
  (23h48), rodada B mais rápida por paralelismo mas competindo por CPU com a A.
- Nesse momento, certificação real: recalcular MAE por braço/h/recorte, refazer A1/A2 (Wilcoxon+Holm)
  e A3 (alarmes) do zero para A; recalcular WIS/cobertura/régua climatológica e Holm do zero para B;
  re-treinar 3 origens de HistGB folha 20 h=12 para conferir contra o gravado; checar vazamento na
  régua climatológica (ano do alvo fora da amostra) e no recorte 2026 (corte em 19/04/2026 pelo
  corte de maturidade).
