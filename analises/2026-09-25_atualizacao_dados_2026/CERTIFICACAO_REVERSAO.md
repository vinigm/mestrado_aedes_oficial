# Certificação adversarial — reversão de 2026 (26/09/2026)

**Veredito: APROVADO.** As 6 âncoras bateram; nenhum número foi forçado.

Contexto: em 25/09 a tabela oficial ganhou o DENGBR26 de setembro (12→19 confirmados
em 2026). Em 26/09 o Vinicius decidiu não usar 2026 e reverteu copiando os backups
`*_ANTES.csv` por cima dos arquivos de entrada. Esta certificação mede do zero se a
reversão voltou exatamente ao estado anterior e se o cenário adotado reproduz o painel
publicado.

## As 6 âncoras

1. **Hash `tabela_final.csv`** — `6f34b854...f6f1f`, idêntico a `git show 544263a:...`. ✅
2. **Hash `casos_confirmados_poa.csv`** — `c71f2ddd...bebf3`, idêntico a `git show 7270056^:...`. ✅
3. **Última semana com dado**: restaurada = SE **202617** (26/04/2026); COM_2026 = SE **202628**
   (12/07/2026). Medido filtrando `ano==2026` e `casos_confirmados` não-nulo em ambas as tabelas. ✅
4. **Confirmados em 2026**: **12** (restaurada) e **19** (COM_2026), somando a coluna
   `casos_confirmados` de `tabela_final.csv` para `ano==2026`. Bate com o README da atualização. ✅
5. **Diff coluna a coluna** (pandas, merge por `SE`, 725 linhas nas duas): só `casos_confirmados`
   diverge, em 14 semanas — todas de 2026. As outras 35 colunas são idênticas em TODAS as 725
   linhas, incluindo 2018-2025. ✅, com um desvio a registrar: **não há linhas extras** — as duas
   tabelas têm o mesmo número de linhas (o calendário de armadilhas já se estende até SE 202632 nas
   duas; o que muda é só o preenchimento de `casos_confirmados`). A afirmação original ("linhas
   extras depois de SE 202617") não se sustenta ao pé da letra; a garantia de fundo (2018-2025
   intactos em tudo) está confirmada.
6. **Trava do harness** (`analises/2026-09-23_bateria_noturna/harness.py`, braço de referência
   HistGB quantil 0,85/250 it/lr 0,05/15 folhas/folha mín. 5, 20 colunas do modelo, k=6 de clima,
   `INICIO_DA_AVALIACAO = 2024-01-01`) rodado sobre a tabela restaurada:

   | h | MAE medido | MAE painel | R² medido | R² painel |
   |---|---|---|---|---|
   | 1 | 98,0 | 98,0 | 0,898 | 0,898 |
   | 4 | 219,7 | 219,7 | 0,628 | 0,628 |
   | 8 | 272,6 | 272,6 | 0,450 | 0,450 |
   | 12 | 278,8 | 278,7 | 0,437 | 0,437 |

   Os 8 números batem dentro da tolerância do próprio harness (MAE 0,2 · R² 0,003).
   **Veredito do harness: VALIDO.** ✅

## Comandos usados

```bash
shasum -a 256 modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv
git show 544263a:modelagem_aedes/dados/entradas/tabela_modelagem/tabela_final.csv | shasum -a 256
shasum -a 256 modelagem_aedes/dados/entradas/bases_governo/output/casos_confirmados_poa.csv
git show 7270056^:modelagem_aedes/dados/entradas/bases_governo/output/casos_confirmados_poa.csv | shasum -a 256
# diff coluna a coluna: reversao_certificacao/ (script python ad hoc, não gravado — só leitura)
python3 analises/2026-09-25_atualizacao_dados_2026/reversao_certificacao/rodar_trava.py
```

Script e log da trava: `reversao_certificacao/rodar_trava.py` e `reversao_certificacao/log_trava.txt`.

## Desvios encontrados

- Item 5 da âncora previa "linhas extras" na versão COM_2026; na prática as duas tabelas têm o
  mesmo número de linhas (725) porque o calendário de armadilhas (raspagem) já ia além de ambas as
  séries de casos. O que muda é só o preenchimento de `casos_confirmados` nas semanas de 2026.
  Não muda o veredito: a garantia relevante (2018-2025 intactos, diferença restrita a 2026) se
  confirma.
- Nenhum arquivo do pipeline foi editado; nenhum commit foi feito; `preparar_dados.py`,
  `consolidar_sinan` e `montar.py` não foram executados.
