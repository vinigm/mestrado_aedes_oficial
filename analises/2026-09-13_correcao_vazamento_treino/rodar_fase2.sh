#!/bin/zsh
# FASE 2 da correcao do vazamento temporal. Pre-declarada em PRE_DECLARACAO_FASE2.md.
# Baratos primeiro, grid por ultimo: erro de setup aparece em minutos, nao em horas.
set -u
PY=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
RAIZ="/Users/viniciusguerra/Library/CloudStorage/GoogleDrive-vinigm@gmail.com/Meu Drive/Mestrado/Pesquisa/Meu_Projeto"
ANALISE="$RAIZ/analises/2026-09-13_correcao_vazamento_treino"
LOG="$ANALISE/saidas/fase2.log"

executar() {
  echo "\n######## [$(date '+%H:%M:%S')] $1 ########" >> "$LOG"
  shift
  if "$@" >> "$LOG" 2>&1; then
    echo "[$(date '+%H:%M:%S')] OK" >> "$LOG"
  else
    echo "[$(date '+%H:%M:%S')] *** FALHOU (codigo $?) ***" >> "$LOG"
  fi
}

echo "FASE 2 iniciada em $(date '+%d/%m/%Y %H:%M:%S')" > "$LOG"

cd "$ANALISE"
executar "B1 rodada 2 - equivalencia, alvo CONFIRMADOS" $PY rodada_2_corrigida.py --alvo confirmados
executar "B2 rodada 2 - equivalencia, alvo NOTIFICADOS" $PY rodada_2_corrigida.py --alvo notificados
executar "C rodada 4 - janela de treino"                $PY rodada_4_corrigida.py
executar "D rodada 3 - ranking espacial"                $PY rodada_3_corrigida.py

cd "$RAIZ/modelagem_aedes"
executar "E1 comparacao_literatura"      $PY main.py --experimento comparacao_literatura
executar "E2 cidade_regressao"           $PY main.py --experimento cidade_regressao
executar "E3 cidade_diebold"             $PY main.py --experimento cidade_diebold
executar "E4 cidade_deteccao_surto"      $PY main.py --experimento cidade_deteccao_surto
executar "E5 cidade_surto_notificados"   $PY main.py --experimento cidade_surto_notificados

cd "$ANALISE"
executar "A grid - as 22 configuracoes restantes (88 celulas, ~2h)" $PY rodar_grid_restante.py

echo "\n######## FASE 2 CONCLUIDA em $(date '+%d/%m/%Y %H:%M:%S') ########" >> "$LOG"
grep -c "FALHOU" "$LOG" >> "$LOG"
