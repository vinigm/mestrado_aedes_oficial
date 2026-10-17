# Experimentos da ciencia (E1, piso de ruido, E2, E4) - construidos em 12/10/2026, NAO rodados

Pre-declaracao aprovada e congelada: `../../analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`.
Tudo de dentro de `projeto_final/`, sempre `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 python3 -B -m experimentos.<script>`
(sem `OMP_NUM_THREADS=1` cada celula leva ~5x mais; o resultado e o mesmo). Nunca o `.venv`.

| Script | Etapa | Celulas | Saida em `resultados/ciencia/` |
|---|---|---|---|
| `e1_quantil` | E1 (secao 3) | 20 = 5 quantis x h {1,4,8,12}; so calibracao (`data_alvo <= 2023-12-31`), folha 5 | `E1_quantil/` (previsoes, metricas, decisao.json com a trava 3) |
| `piso_de_ruido` | secao 8b | 40 = 5 perturbacoes (csv, s1..s4) x folhas 5 e 20 x h {1,4,8,12} | `piso_de_ruido/` (previsoes, mae_por_perturbacao, piso); `--zeros manter` grava em `piso_de_ruido_zeros_mantidos/` |
| `e2_ablacao` | E2 (secao 4) | 192 = 8 bracos x folhas 5 e 20 x 12 h | `E2_ablacao/` (previsoes, mae_descritivo, travas.json) |
| `e4_corte` | E4 (secao 6) | 24 = bracos completo e sem_vetor x 12 h, folha 5, corte pela pergunta; EXIGE a E2 pronta e com travas aprovadas | `E4_corte/` (previsoes, comparacao) |

Cada script: `--refazer`, `--so-juntar`, fatias por argumento (`--bracos`, `--folhas`, `--horizontes`, `--quantis`,
`--perturbacoes`); parciais em `parciais/` com escrita atomica (parcial existente e pulado); log `<etapa>.log`; a juncao
roda sozinha quando todos os parciais existem. `e2_ablacao --so-travas` confere as travas 1 e 2 assim que `completo`
(folhas 5 e 20) e `sem_vetor` (folha 20) tiverem os 12 horizontes: rodar esses primeiros. Trava reprovada: a etapa para,
nenhum arquivo descritivo e gerado e o codigo de saida e 1.

Codigo novo em `aedes/`: `bracos.py` (8 bracos e a matriz de cada um), `walk_forward_com_corte.py` (regra de corte
resposta/pergunta e recorte da calibracao), `perturbacao.py` (ultimo bit), `comparacoes.py` (travas, regra de 2%, cobertura,
comparacao de cortes, piso). Nenhum teste estatistico (DM, Holm, bootstrap) aqui: so MAE, R2 e cobertura descritivos.
