# Certificacao adversarial da E2 (ablacao) - 12/10/2026

**Veredito: APROVADO.** Nao consegui reprovar. Nenhuma divergencia material; 3 observacoes menores no fim.
Certificador independente (Sonnet), codigo proprio em `minha_receita.py` (nao importa `aedes/` nem `experimentos/`).
O unico script que importa `aedes.bracos` e `v05_comparador_pacote.py`, e so para extrair as matrizes do pacote (objeto sob teste).
Ambiente: `python3` 3.14.4, scikit-learn 1.8.0, `OMP_NUM_THREADS=1`, `-B`. Maximo de 3 processos python simultaneos. Sem git.

## Resultados por item

1. **Vazamento de bloco: nenhum.** (`v05`, `v05_resultado.json`)
   - Colunas de cada braco do pacote = definicao pre-declarada: 22, 16, 16, 16, 10, 10, 10, 4 (completo, sem_casos, sem_clima, sem_vetor, so_casos, so_clima, so_vetor, so_calendario).
   - so_clima e so_vetor: 0 colunas `casos*`; sem_vetor: 0 colunas `aedes_*`/`vetor_mm4`; calendario (4) em todos os 8.
   - Prova empirica: a replica independente com exatamente essas colunas reproduz as previsoes salvas bit a bit (item 2). Controle negativo: so_vetor h=12 folha 5 com uma coluna `casos` extra muda a previsao em 39,6 casos.
2. **Matrizes e retreino: identicos.**
   - 96 matrizes (8 bracos x 12 h): pacote x minha receita, colunas, ordem, datas e valores iguais bit a bit (`v05`). Tabela cortada identica (hash conferido).
   - Retreino de 2 origens de so_vetor, sem_casos e so_calendario (h=1 e 12, folhas 5 e 20): `v02`. Diferenca <= 3,6e-15 (artefato do `read_csv` rapido, ver obs. 1).
   - **Muito alem do pedido:** replica COMPLETA do walk-forward (todas as origens) de 8 bracos x 2 folhas x h in {1,4,8,12} = 64 celulas, 19.188 previsoes, lidas com `float_precision=round_trip`: **dif max 0,0; 0 bits diferentes** (`v04_agregado.log`).
3. **Travas recomputadas dos arquivos (`v03`):** completo f5 x `referencia` (3474 linhas) e completo f20 x `HistGB_folha20_M1` (3474): dif max 0,0. sem_vetor f20 x `HistGB_folha20_M0` (3618, casando por h e data_alvo): dif max 0,0. Mesmos conjuntos de datas (0 orfas). Tambem iguais ao gabarito antigo `referencia` e `HistGB_folha20_M1`.
4. **MAE e contagens (`v03`):** `mae_descritivo.csv` recomputado das previsoes: 192 linhas, dif max 2,8e-14, n da janela igual em todas. n da janela: 102 (completo, sem_casos, sem_clima, so_vetor), 109 (sem_vetor, so_casos, so_clima, so_calendario). Pares em comum: completo x sem_X = 102; so_casos e so_clima x so_calendario = 109; so_vetor x so_calendario = 102. Ancoras: MAE janela completo f5 = 97,987/219,669/272,627/278,818, f20 = 133,626/199,635/223,183/243,765; calibracao f5 n = 193/190/186/182, MAE 22,337/45,786/48,167/51,799; gabarito M0 janela n=109, MAE 138,678/214,741/231,119/261,180. Todas batem.
5. **Parciais e corte:** 192 parciais presentes, nenhum arquivo extra; 0 duplicatas de (braco, folha, h, data_alvo) e de (..., data_origem); 0 NaN; `data_alvo - data_origem = h` semanas em todas; `real` = casos da tabela cortada na data_alvo, e identico entre bracos; linhas, datas e `real` de cada um dos 192 parciais = minha matriz (origens a partir da 105a linha). Linhas por braco-folha: 3474/3544/3474/3618/3744/3618/3744/3544 (como o executor relatou). data_alvo de 16/02/2020 a 01/02/2026 (2026 fora da avaliacao). **Corte pela resposta:** minha replica (treino = `data_alvo <= t`) reproduz as previsoes salvas; controle negativo, corte ingenuo (`data_origem < t`) em so_vetor h=12 f5 muda a previsao em 582,6 casos.
6. **Suite:** 669 passed (86 s) em copia identica (diff -r sem diferencas). Mutantes em copia no scratchpad:
   - M1 so_vetor ganha o bloco casos: **pego** (2 falhas, `test_bracos.py`).
   - M2 dropna nas 22 variaveis em vez das do braco: **pego** (5 falhas, incl. a trava 2 com modelo).
   - M3 bloco clima com 5 colunas: **pego** (>= 8 falhas).
   - M4 folhas 5 e 20 trocadas em `e2_ablacao.MODELOS_POR_FOLHA`: **NAO pego** (669 passed). Ver obs. 2.

## Observacoes menores (nao reprovam)

1. `previsoes.csv` != concatenacao exata dos parciais: 12.010 de 57.520 previsoes diferem por ate 4,5e-13. Causa: o `read_csv` padrao do pandas nao e exato no ultimo bit, e `previsoes.csv` foi escrito a partir dos parciais lidos assim. Sem efeito pratico (trava 1e-9, MAE ~1e-13), mas `previsoes.csv` nao e a fonte bit-exata; os parciais sao. Para as proximas etapas, ler com `float_precision="round_trip"` ou aceitar 1e-12.
2. Lacuna de teste: nenhum teste unitario protege o mapa folha -> modelo do `e2_ablacao.py` (M4). Hoje so a trava 1 na rodada real pega (e passou).
3. Pacote cresceu: suite tem 669 testes, nao 479. 2.763 previsoes negativas (quantilico sem truncar), igual a referencia; nao e defeito.

Nota de desenho (consequencia da trava 2, nao defeito): bracos sem vetor treinam com mais linhas (semanas da enchente); por isso n da janela difere (109 x 102) e os pares usam so datas em comum.

## Arquivos (todos nesta pasta)
`minha_receita.py`, `v02_*.py/json/log`, `v03_travas_mae_parciais.py`, `v03_resultado.json`, `v03b_roundtrip.py`, `v04_replica_walk_forward.py`, `v04_resultado.json`, `v04_agregado.log`, `replica/` (64 CSVs), `v05_comparador_pacote.py`, `v05_resultado.json`. Logs do pytest e mutantes: `.../scratchpad/cert_e2/pytest_*.log`.
Nenhum arquivo certificado foi alterado; nenhum `__pycache__` criado.
