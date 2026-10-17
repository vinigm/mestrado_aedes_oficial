# Experimentos da reprodução da seleção (E6a, E6b, E6c) e do WIS (E7) — construídos em 12/10/2026, NÃO rodados

Pré-declaração aprovada e congelada: `../../analises/2026-10-12_pre_declaracao_reproducao_e_wis/PRE_DECLARACAO.md`.
Tudo de dentro de `projeto_final/`, sempre `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.<script>`
(sem `OMP_NUM_THREADS=1` cada célula leva ~5x mais; o resultado é o mesmo). Nunca o `.venv`.

**Regra do Vinicius (12/10):** o modelo de referência do artigo NÃO muda, aconteça o que acontecer. Se a reprodução escolher outra
configuração ou outro clima, a rodada termina e a divergência é documentada.

| Script | Etapa | Células | Saída |
|---|---|---|---|
| `e6a_clima` | E6a | 3 variantes (segundos) | `resultados/reproducao_selecao/E6a_clima/` (`ganho_<variante>.csv`, `resumo.json`) |
| `e6b_grade30` | E6b | 120 = 30 configurações x h {1,4,8,12}, matriz inteira, previsão truncada em 0 | `E6b_grade30/` (previsoes, resumo, ranking, comparacao_com_gabarito, ancoras, trava) |
| `e6c_grade18` | E6c | fase 1: 72 = 18 x 4 h (matriz cortada na calibração); fase 2: 8 (vencedora e referência, matriz inteira) | `E6c_grade18/` (ranking, trava, ancoras, decisao, fase2) |
| `e7_wis` | E7 | 176 = 168 (2 folhas x 7 quantis x 12 h) + 8 da trava (q0,85, 2 folhas, h {1,4,8,12}) | `resultados/wis/` |

Cada script (menos a E6a): fatias por argumento, parciais em `parciais/` com escrita atômica (parcial existente é pulado;
`--refazer` força), log `<etapa>.log`, junção automática quando todos os parciais existem, `--so-juntar`, `--so-trava`.

## Trava (antes de ler qualquer resultado)

Se reprovar, a etapa PARA (código de saída 1), grava só o diagnóstico e nenhum resultado. A tolerância é a da pré-declaração, 1e-9.

- **E6b:** HistGB q0,85 M1 (h 1, 4, 8, 12) = `resultados/referencia/previsoes.csv` (braço `referencia`) TRUNCADA em 0 também.
- **E6c:** a referência da grade na calibração = referência certificada; na fase 2, em todas as origens.
- **E7:** o q0,85 das duas folhas = `referencia` e `HistGB_folha20_M1`.

Os diferenciais com modelo dos testes (`test_reproducao_diferencial.py`) usam 1e-12: a referência certificada **não** é
reproduzida bit a bit nem pelo `executar_walk_forward` de hoje (diferença de 4e-16 a 2e-13, igual com 1, 2 ou todas as threads).
A igualdade EXATA entre o laço do pacote e o das etapas está em `test_grade.py` (diferença 0,0).

## Como rodar

    # E6a, segundos:
    ... python3 -B -m experimentos.e6a_clima

    # E6b, uma fatia por processo (algoritmo x perda x conjunto x h); a trava primeiro:
    ... nohup python3 -B -m experimentos.e6b_grade30 --algoritmos hist_gradient_boosting --perdas quantil_0.85 --conjuntos M1_com_vetor > /dev/null 2>&1 &
    ... python3 -B -m experimentos.e6b_grade30 --so-trava
    ... python3 -B -m experimentos.e6b_grade30 --so-juntar

    # E6c, fase 1 por configuração; depois --so-juntar; depois a fase 2:
    ... nohup python3 -B -m experimentos.e6c_grade18 --configuracoes lr0.05_it250_folhas15_min5 lr0.03_it400_folhas15_min5 > /dev/null 2>&1 &
    ... python3 -B -m experimentos.e6c_grade18 --so-juntar
    ... python3 -B -m experimentos.e6c_grade18 --fase2 --horizontes 1 4      # e depois 8 12 em outro processo

    # E7, a trava primeiro (8 células), depois o WIS:
    ... nohup python3 -B -m experimentos.e7_wis --quantis 0.85 > /dev/null 2>&1 &
    ... python3 -B -m experimentos.e7_wis --so-trava
    ... nohup python3 -B -m experimentos.e7_wis --folhas 5 --quantis 0.05 0.1 > /dev/null 2>&1 &
    ... python3 -B -m experimentos.e7_wis --so-juntar

## Tempos medidos em 12/10/2026 (1 célula, 6 processos em paralelo numa máquina de 10 núcleos)

| Célula | Tempo |
|---|---|
| HistGB q0,85 M1 h=4 (E6b) | ~39 s |
| GradientBoosting q0,85 M1 h=4 (E6b) | ~59 s |
| LightGBM q0,85 M1 h=4 (E6b) | ~88 s |
| E6c fase 1, referência (matriz cortada), h=4 | ~29 s |
| E6c fase 1, 0,03 x 400, h=4 | ~43 s |
| E6c fase 2, referência (matriz inteira), h=4 | ~46 s |
| E7 folha 5, h=4 | ~47 s |
| E7 folha 20, h=4 | ~30 s |

Estimativa de CPU: E6a segundos · E6b ~130 min · E6c ~42 min · E7 ~111 min · **total ~4,8 h de CPU** (a pré-declaração
estimava 3,5 a 4 h); com 8 processos, ~40 a 45 min de relógio.

## Código novo

`aedes/`: `selecao_clima.py` (E6a), `grade.py` (E6b), `hiperparametros.py` (E6c), `quantis.py` e `wis.py` (E7). Testes:
`test_selecao_clima.py`, `test_grade.py`, `test_hiperparametros.py`, `test_quantis_wis.py`, `test_experimentos_reproducao.py`,
`test_reproducao_diferencial.py`. Gabaritos copiados do código antigo (só leitura, sha256 em `testes/referencia_antiga/MANIFESTO_E6_E7.csv`):
`e6b_*`, `e6c_*` e `e7_*` em `testes/referencia_antiga/`.
