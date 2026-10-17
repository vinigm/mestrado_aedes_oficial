# Certificacao independente das contagens de notificacoes (15/10/2026)

**Veredito: APROVADO COM RESSALVAS.** Contagens do contador reproduzidas com diferenca zero; 1 explicacao do relato esta errada e 1 premissa vale so em parte.

Metodo: codigo proprio (`recontar_independente.py`, sem importar `aedes/` nem `experimentos/`), pandas, zips publicos DENGBR18-26 em pedacos de 250 mil linhas, 6 colunas, so contagens. Diferencas deliberadas: ano por fatiamento de texto de `DT_SIN_PRI`; codigo por `to_numeric`; `ID_MUNICIP` casado numericamente e por prefixo; contagem extra por `SEM_PRI`. Rodou em 20 s, 1 processo, `python3 -B`.

## 1. Recontagem (diferenca zero)
- `contagens_por_arquivo.csv`: 10 linhas x 5 colunas (total, confirmadas, inconclusivas, em aberto, outros) = **soma das diferencas absolutas 0**. Codigos por arquivo tambem iguais.
- `contagens_por_ano_de_sintomas.csv`: 10 anos (2017-2026) x 5 colunas = **0**. Total 2026 = 3.929 (19 conf., 3.843 incl., 67 em aberto).
- Municipio: so existe o formato de 6 digitos `431490` (nenhuma variante de 7 digitos); nenhuma ficha escapou do filtro por formato.

## 2. Descartados
- DENGBR22 a 26: **nenhum** codigo de descartado (so 10, 11, 12, 8 e vazio). Premissa vale a partir de 2022.
- DENGBR18 a 21: **codigo 5 presente** (213, 798, 140, 82 fichas), confirmando o desvio 1 do contador. Nao ha codigo 2 nem 13 em nenhum arquivo.
- Efeito: o "% confirmado" de 2018-2021 nao e comparavel ao de 2022+ (denominador inclui descartados).

## 3. Versao do DENGBR26
- `DENGBR26.csv.zip` (jun): maior `DT_ENCERRA` 08/06/2026, arquivo de 14/06/2026, 3.835 fichas, 12 confirmadas, 976 em aberto.
- `DENGBR26_atualizado_set26.csv.zip`: maior `DT_ENCERRA` 02/09/2026, arquivo de 13/09/2026, 3.861 fichas, 19 confirmadas, 1 em aberto. E a que entra na soma por ano (correto, sem dupla contagem).

## 4. tabela_final.csv x contagem
- Tabela: 428 semanas com caso, soma **56.624**; por ano 2018 3 · 2019 489 · 2020 38 · 2021 72 · 2022 5.583 · 2023 6.591 · 2024 19.024 · 2025 24.812 · 2026 **12**.
- Recontagem por `SEM_PRI` com a versao **jun** do DENGBR26: soma 56.624, **0 semanas diferentes** da tabela (semana a semana, 428 de 428). Logo a tabela usa a exportacao de **jun**, confirmado.
- Com a versao **set**: soma 56.631 (+7): 2026 vira 19 confirmadas. Diferencas: SE 202602 (-1, reclassificada), SE 202614 (0 -> 1), SE 202616 (2 -> 3) e 6 semanas novas depois de 26/04 (SE 202618, 19, 20, 23, 24, 28; 1 caso cada). 12 - 1 + 1 + 1 + 6 = 19.
- A tabela termina a serie na SE 202617 (26/04/2026) por regra (ultima semana com caso na versao jun); depois ha 15 semanas vazias em 2026 (de 32).

## 5. Divergencias e ressalvas
- **Explicacao errada no relato:** "48 das 67 em aberto de 2026 vem do DENGBR25". Medido: DENGBR25 tem **68** fichas com sintomas em 2026 (**66 em aberto**, 2 inconclusivas); 67 = 66 + 1 do DENGBR26 set. O numero 67 esta certo; a decomposicao, nao.
- **Possivel dupla contagem entre arquivos:** as 68 fichas de 2026 do DENGBR25 podem ser as mesmas do DENGBR26 (anos diferentes de extracao). Sem ID individual nao foi testado; o total 3.929 de 2026 pode estar inflado em ate 68. As 19 confirmadas nao sao afetadas (nenhuma ficha confirmada de 2026 esta no DENGBR25).
- Ano por `DT_SIN_PRI` (calendario) difere do ano de `SEM_PRI` (epidemiologico) em 82 fichas (76 no DENGBR25): borda de ano, sem efeito nas semanas.
- 11 fichas com sintomas em 2017 (DENGBR18, codigo 5) e 2018-2021 sao em maioria descartadas: nao usar esses anos para fracao de confirmadas.

Arquivos: `recontar_independente.py/.log`, `comparar.py/.log`, `decompor_2026.py/.log`, `recontagem_*.csv`.
