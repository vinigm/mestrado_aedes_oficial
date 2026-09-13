# Remédios para o viés de subestimação do pico — 30/08/2026

> **A pergunta:** dado que o modelo subestima sistematicamente os picos de dengue (e a subestimação
> cresce com o horizonte), qual das 4 variantes de LightGBM reduz esse viés sem quebrar o resto?
> **A resposta:** só a **regressão quantílica (alpha 0,8)** reduz o `|viés no pico|` nos 4 horizontes
> ao mesmo tempo; as outras 3 variantes só melhoram em h=1.
> Status: ⚠️ exploratório. Pré-declaração: não existe.

## 1. Por que este teste foi feito

- Diagnóstico anterior (30/08/2026, mesma rodada de trabalho): o modelo subestima o pico e o viés
  cresce com o horizonte — de **-89 em h=1** a **-429 em h=12** (números do diagnóstico, não deste script).
- Causa **testada e refutada**: limite de extrapolação das árvores (teto do treino 1.439 × pico médio
  829; só 5 de 32 picos ficavam acima do teto).
- Causa **assumida** aqui: assimetria da série — **61% das semanas têm até 5 casos** — puxa o objetivo
  padrão (erro quadrático) do LightGBM para o centro da distribuição.
- Três ideias vieram de um projeto anterior do Vinicius (previsão de demanda no varejo): mês-alvo
  categórico, objetivo tweedie, regressão quantílica. Este teste mede se elas funcionam aqui também.
- **Não há PRE_DECLARACAO.md nesta pasta** — confirmado por busca na pasta antes de escrever este README.

## 2. Como foi medido

- **Alvo:** `casos` da cidade, horizonte `h` (`construir_alvo_horizonte`), cenário de referência =
  `cidade_regressao` (mesmas colunas núcleo + 6 melhores colunas de clima por ganho).
- **Horizontes testados:** 1, 4, 8 e 12 semanas.
- **Walk-forward:** `mínimo_semanas_treino=104`, `passo=2` (retreina a cada 2 semanas) — vem de
  `config/experimentos/cidade_regressao.py`.
- **5 variantes**, todas clipadas em zero (previsão de casos não é negativa), hiperparâmetros-base
  iguais entre si (`n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20` —
  **não são os mesmos do `LGBM_REGRESSAO` em `cidade_regressao.py`**, que usa 250/15/5; o script
  declara isso como "iguais ao cenário 1", divergência não verificada neste README):
  - `atual` — objetivo padrão (erro quadrático), sem mês-alvo.
  - `A_mes_categorico` — acrescenta `mes_alvo` (1–12) como categoria.
  - `B_tweedie` — objetivo `tweedie`, potência 1,5.
  - `C_quantile_08` — objetivo `quantile`, alpha 0,8.
  - `D_mes_cat_+_tweedie` — A + B juntos.
- **Faixas de intensidade:** entressafra (`real ≤ 5`), intermediária, pico (`real > 100`).
- **Critério de decisão:** reduzir `pico_VIES` (média do erro nas semanas de pico) — **critério
  aplicado por leitura humana da tabela, sem função de decisão no script e sem pré-declaração.**
- **Execuções:** 5 variantes × 4 horizontes = 20 walk-forwards; **148 a 154 semanas** testadas por
  horizonte (cai com `h` porque o alvo desloca a última data usável). Tempo total: **16,2 min**
  (`saidas/remedios_log.txt`, linha final).

## 3. O que deu

| h | atual (viés) | A_mes_cat | B_tweedie | C_quantile_08 | D_mes+tweedie |
|---|---|---|---|---|---|
| 1 | -219,4 | -214,3 | -143,5 | **-114,7** | -141,4 |
| 4 | -288,5 | -301,5 | -297,8 | **-128,5** | -306,6 |
| 8 | -351,8 | -354,6 | -413,9 | **-268,2** | -400,7 |
| 12 | -466,5 | -467,0 | -521,6 | **-342,9** | -515,2 |

(`pico_VIES`, `saidas/remedios_resumo.csv`; n=32 semanas de pico em todos os horizontes.)

- **C_quantile_08 é a única variante que reduz `|viés|` nos 4 horizontes** frente a `atual` — as
  outras 3 (A, B, D) só melhoram em h=1 e pioram em h=4/8/12.
- O custo aparece em outro lugar: `MAE_global` em h=1 piora com C (**86,1 vs 80,4** do atual) e
  `entressafra_MAE` também piora em h=4 e h=12 (6,55 e 6,94 vs 5,27 e 6,06) — o quantil alto acerta
  menos as semanas de poucos casos.
- Em h=4/8/12, C melhora tanto `R2_global` (ex.: h=12: **0,716 vs 0,601**) quanto `MAE_global`
  (h=12: **100,2 vs 114,9**) — não é só troca de viés por variância, o ajuste geral também melhora.
- `pico_MAE` de C é o único caso onde a variante **piora ligeiramente em h=1** (351,7 vs 347,5 do
  atual) apesar do viés menor — indica que em h=1 o quantil corrige a direção do erro mas não o
  tamanho médio.

## 4. Conclusão

- **FATO:** dentro deste desenho (mesmos hiperparâmetros-base, mesma seleção de features, walk-forward
  de 148–154 semanas), `C_quantile_08` é a única das 4 variantes que reduz `|pico_VIES|` nos 4
  horizontes simultaneamente.
- **FATO:** essa vitória não veio de um critério pré-declarado nem de uma função de escolha no
  código — foi leitura humana da tabela impressa pelo script.
- **HIPÓTESE (não testada aqui):** o ganho de C se sustentaria com um alpha diferente de 0,8, ou é
  específico deste valor — o script não varreu alpha.
- **EXPLORATÓRIO:** a leitura de que "o quantil corrige mais em horizontes longos" nasce só desta
  tabela; não havia expectativa pré-declarada sobre a interação alpha × horizonte.

## 5. Ressalvas e o que ficou em aberto

- Sem pré-declaração — toda leitura acima é **post-hoc**.
- Sem correção de múltiplas comparações (5 variantes × 4 horizontes × várias métricas).
- Comparação **não pareada estatisticamente** — nenhum teste de significância, IC ou seed repetida;
  é uma única rodada de walk-forward por variante.
- `n_picos=32` por horizonte é pequeno para generalizar a estação seguinte.
- Hiperparâmetros-base do script **não conferidos** contra o cenário 1 real (ver §2) — se divergirem,
  a comparação com "o atual" de outras análises fica capenga.

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- **Este teste está na lista dos NÃO REFEITOS.** O corte de treino em `rodar_variante` usa
  `treino = validos.iloc[:indice_corte]`, isto é, corta pela posição da data de **origem**, não pela
  data-alvo (`origem + h` semanas) — exatamente o defeito descrito no vazamento de 13/09/2026.
- Para `h=1` o vazamento tende a ser mínimo (a última linha de treino quase não ultrapassa a
  data-alvo do teste). Para `h=4/8/12` várias linhas do fim do treino têm data-alvo posterior à
  data de origem testada — o modelo via, durante o treino, semanas de resultado que ainda não
  tinham acontecido no momento da previsão.
- **Direção provável do viés:** a correção documentada em outra análise custou **+52% de MAE em
  h=12** na configuração de referência — ou seja, vazamento **infla o desempenho aparente**, mais
  forte quanto maior o horizonte. Os números de `MAE_global` e `R2_global` deste teste em h=8/h=12
  são candidatos a estarem **otimistas demais**, para as 5 variantes igualmente.
- Como o vazamento afeta as 5 variantes do mesmo jeito (mesmo desenho de corte), o **ranking entre
  elas** (C vence no viés do pico) é mais robusto ao defeito do que os **valores absolutos** de MAE/R2
  — mas isso não foi testado; é leitura de plausibilidade, não medição.
- Não refeito até 13/09/2026. Corrigir e rodar de novo é pré-requisito antes de usar este resultado
  para decidir a função de perda definitiva do modelo de casos.

## 7. Arquivos

- `testar_remedios.py` — script gerador: monta as 5 variantes, roda o walk-forward por horizonte e
  imprime os pivots de viés/MAE/R2.
- `saidas/remedios_log.txt` — log da execução (16,2 min), com as 5 tabelas impressas pelo script.
- `saidas/remedios_previsoes.csv` — 3.020 linhas: `h`, `data`, `real`, `pred`, `variante` (uma linha
  por semana testada, por variante e horizonte).
- `saidas/remedios_resumo.csv` — 20 linhas: métricas agregadas (`MAE_global`, `R2_global`, `pico_VIES`,
  `pico_MAE`, `entressafra_MAE`) por variante × horizonte.
