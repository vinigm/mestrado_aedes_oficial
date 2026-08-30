#!/bin/bash
# Roda as duas variantes do Teste A em sequencia, sobre a serie longa de clima.
# notificados primeiro (708 semanas, a variante que justifica a rodada),
# confirmados depois (424 semanas, para comparar com o resultado de 16/08).
set -u
cd "$(dirname "$0")"

echo "############ VARIANTE 1: alvo NOTIFICADOS ############"
python3 rodada_2_teste_a_serie_longa.py --alvo notificados

echo ""
echo "############ VARIANTE 2: alvo CONFIRMADOS ############"
python3 rodada_2_teste_a_serie_longa.py --alvo confirmados

echo ""
echo "############ RODADA 2 CONCLUIDA ############"
