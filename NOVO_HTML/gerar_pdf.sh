#!/bin/bash
# Atalho para o gerador de PDF da apresentação. O trabalho está em
# `gerar_pdf.py`; este arquivo existe só para quem já tinha o comando na mão.
#
# 🔴 Este script MUDOU em 27/09/2026. Antes ele chamava o `--print-to-pdf` do
# Chrome direto na página inteira, e o PDF saía com o título em cima da barra de
# andamento e com o slide encolhido no alto da folha. A causa e a correção estão
# documentadas no cabeçalho do `gerar_pdf.py`.
#
# ⚠️ Rodar com `python3`, e não com o `.venv`: o projeto tem dois Pythons com
# bibliotecas diferentes (ver PENDENCIAS.md, Dívida técnica).
#
# Uso:
#   ./gerar_pdf.sh                      → gera o seminário (cópia 2)
#   ./gerar_pdf.sh seminario.html       → gera outra página do site
set -euo pipefail

PASTA_DESTE_ARQUIVO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$PASTA_DESTE_ARQUIVO/gerar_pdf.py" "$@"
