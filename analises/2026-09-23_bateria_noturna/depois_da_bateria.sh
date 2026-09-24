#!/bin/bash
# Espera a bateria principal terminar e so entao roda o bloco 6, para os dois
# nao disputarem CPU: o HistGB usa todos os nucleos.
cd "$(dirname "$0")"
until grep -q FIM_DA_BATERIA log_mestre.txt 2>/dev/null; do sleep 30; done
echo "COMECOU bloco_6_hiperparametros $(date '+%H:%M:%S')" >> log_mestre.txt
python3 -u bloco_6_hiperparametros/rodar.py > bloco_6_hiperparametros/execucao.log 2>&1
echo "TERMINOU bloco_6_hiperparametros codigo=$? $(date '+%H:%M:%S')" >> log_mestre.txt
echo "FIM_DO_BLOCO_6 $(date '+%d/%m %H:%M:%S')" >> log_mestre.txt
