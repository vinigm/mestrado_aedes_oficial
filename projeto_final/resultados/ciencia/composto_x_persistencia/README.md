# Composto × persistência (exploratório)

Gerado por `experimentos/composto_x_persistencia.py` (não editar à mão; refazer pelo script).

## O que é

- **Comparação exploratória, não pré-declarada**, registrada como **Emenda 6** da pré-declaração
  (`analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`, 17/10/2026, Vinicius), depois de medida.
- **Persistência:** a previsão da semana-alvo é o número de casos confirmados da semana de origem (`data_origem`).
- **Uso:** só no material suplementar (S3), tabela `tabelaS_persistencia.tex`. Nenhum veredito pré-declarado muda.
- Nenhum modelo foi treinado; nenhum módulo ou resultado existente foi alterado.

## Método

- **Composto:** E3, N = 13 (`resultados/ciencia/E3_composto/previsoes.csv`); persistência a partir de
  `dados/tabela_final.csv` (sha256 conferido), coluna `casos_confirmados`.
- **Janela:** semanas-alvo de 07/01/2024 a 01/02/2026, 102 por horizonte; h = 1, 2, 3, 4, 8 e 12.
- **Diferença de perda:** d = |real − persistência| − |real − composto|; positivo = o composto erra menos.
- **DM-HLN:** o método pré-declarado (`aedes/estatistica.py`), bilateral. **Newey-West:** Bartlett, L = 4, sem HLN, t com
  n − 1 g.l. (leitura extra, sem correção de multiplicidade).
- **Holm:** sobre os p do DM-HLN de h = 1, 4, 8 e 12 (a família fixada na Emenda 6); h = 2 e 3 ficam sem correção.

## Âncora

- **Reprodução:** o resultado bate com o CSV medido em 17/10/2026
  (`analises/2026-10-17_persistencia_exploratorio/composto_x_persistencia.csv`) com diferença máxima
  **0.0e+00** em todas as colunas (limite do script: 1e-12). Aquele CSV foi confirmado por uma
  reimplementação independente, sem o código do projeto, com diferença máxima de 8,9e-16.

## Resultado

| h | MAE do composto | MAE da persistência | Ganho do composto | p DM-HLN | p Newey-West | p de Holm (h = 1, 4, 8, 12) |
|---|---|---|---|---|---|---|
| 1 | 102,3 | 83,3 | −22,9% | 0,127 | 0,252 | 0,253 |
| 2 | 185,7 | 153,5 | −21,0% | 0,349 | 0,363 | — |
| 3 | 198,4 | 214,6 | +7,5% | 0,703 | 0,663 | — |
| 4 | 205,7 | 279,0 | +26,3% | 0,222 | 0,150 | 0,253 |
| 8 | 233,5 | 531,0 | +56,0% | 0,045 | 0,007 | 0,155 |
| 12 | 260,1 | 697,5 | +62,7% | 0,039 | 0,001 | 0,155 |

Ganho = (MAE da persistência − MAE do composto) ÷ MAE da persistência; negativo quando a persistência erra menos.
Valores completos (precisão total) em `composto_x_persistencia.csv`.

## Limites

- **Fato:** o menor p de Holm é 0,155; nenhum passa de 0,05.
- **Fato:** a comparação inteira, inclusive a família de Holm (4 testes) e o Newey-West, não foi pré-declarada; a leitura
  é exploratória.
- **Fato:** a persistência usa o dado consolidado, como o resto da avaliação (sem dados da época).
