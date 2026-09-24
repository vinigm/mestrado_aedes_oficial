#!/bin/bash
# Roda os quatro blocos em sequencia. Um bloco que falha nao impede os outros.
# Ordem por valor: o bloco 2 pode render o unico resultado positivo do projeto.
cd "$(dirname "$0")"
MESTRE=log_mestre.txt
echo "INICIO $(date '+%d/%m %H:%M:%S')" > "$MESTRE"
for bloco in bloco_2_features_longas bloco_3_importancia_por_bloco bloco_5_algoritmos bloco_4_lag_do_vetor; do
  echo "COMECOU $bloco $(date '+%H:%M:%S')" >> "$MESTRE"
  python3 -u "$bloco/rodar.py" > "$bloco/execucao.log" 2>&1
  echo "TERMINOU $bloco codigo=$? $(date '+%H:%M:%S')" >> "$MESTRE"
done
echo "FIM_DA_BATERIA $(date '+%d/%m %H:%M:%S')" >> "$MESTRE"
