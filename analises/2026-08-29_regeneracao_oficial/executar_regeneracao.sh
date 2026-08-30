#!/bin/bash
#
# Regeneracao oficial de 29/08/2026: roda todos os experimentos na tabela_final
# nova (clima recapturado desde 2012).
#
# Regras desta bateria:
#   - NAO para no primeiro erro. Numa rodada longa e sem ninguem olhando, um
#     experimento que quebra nao pode derrubar os outros 15. Cada falha e
#     registrada e a bateria segue.
#   - Cada experimento tem seu proprio log, para que a investigacao de uma
#     falha nao dependa de achar o trecho certo num log gigante.
#   - A ordem comeca pelos experimentos-nucleo da tese, para que o resultado
#     que importa apareca cedo mesmo se a bateria for interrompida.
#
# cidade_surto_notificados fica de fora: ja rodou hoje, na tabela nova.

set -u

PASTA_ANALISE="$(cd "$(dirname "$0")" && pwd)"
PASTA_PACOTE="$PASTA_ANALISE/../../modelagem_aedes"
PASTA_LOGS="$PASTA_ANALISE/saidas/logs_experimentos"
RESUMO="$PASTA_ANALISE/saidas/resumo_execucao.txt"

mkdir -p "$PASTA_LOGS"
cd "$PASTA_PACOTE" || exit 1

EXPERIMENTOS=(
  cidade_regressao
  cidade_lift_vetor
  cidade_diebold
  cidade_deteccao_surto
  cidade_regressao_sem_enso
  cidade_regressao_com_enso
  comparacao_literatura
  bairro_surto
  cidade_regressao_rf
  cidade_regressao_extra_trees
  cidade_regressao_hist_gradient_boosting
  cidade_regressao_gradient_boosting
  cidade_regressao_ridge
  cidade_regressao_elastic_net
  cidade_regressao_svr
  cidade_regressao_knn
)

echo "REGENERACAO OFICIAL — inicio: $(date '+%d/%m/%Y %H:%M:%S')" | tee "$RESUMO"
echo "total de experimentos: ${#EXPERIMENTOS[@]}" | tee -a "$RESUMO"
echo "" | tee -a "$RESUMO"

CONTADOR=0
FALHAS=0

for EXPERIMENTO in "${EXPERIMENTOS[@]}"; do
  CONTADOR=$((CONTADOR + 1))
  INICIO=$(date +%s)

  echo "[$CONTADOR/${#EXPERIMENTOS[@]}] $EXPERIMENTO — iniciado $(date '+%H:%M:%S')" | tee -a "$RESUMO"

  python3 -u main.py --experimento "$EXPERIMENTO" > "$PASTA_LOGS/$EXPERIMENTO.log" 2>&1
  CODIGO_SAIDA=$?

  DURACAO=$(( ($(date +%s) - INICIO) / 60 ))

  if [ $CODIGO_SAIDA -eq 0 ]; then
    echo "    OK    — ${DURACAO} min" | tee -a "$RESUMO"
  else
    FALHAS=$((FALHAS + 1))
    echo "    FALHA — codigo $CODIGO_SAIDA apos ${DURACAO} min (ver logs_experimentos/$EXPERIMENTO.log)" | tee -a "$RESUMO"
    tail -5 "$PASTA_LOGS/$EXPERIMENTO.log" | sed 's/^/           /' | tee -a "$RESUMO"
  fi
done

echo "" | tee -a "$RESUMO"
echo "REGENERACAO CONCLUIDA — fim: $(date '+%d/%m/%Y %H:%M:%S')" | tee -a "$RESUMO"
echo "sucesso: $((CONTADOR - FALHAS)) de $CONTADOR | falhas: $FALHAS" | tee -a "$RESUMO"
