# Método estatístico — E3, famílias F1 a F4 e E5

> Escrito em 12/10/2026 pelo orquestrador (especificação fixada ANTES de qualquer teste) e copiado aqui pelo executor
> ANTES de rodar qualquer coisa. Pré-declaração aprovada: `analises/2026-10-12_pre_declaracao_ciencia/PRE_DECLARACAO.md`
> (com as emendas 1 a 3). Este arquivo só detalha a mecânica; nenhuma decisão de ciência nasce aqui.

## Dados

- Previsões da E2: `resultados/ciencia/E2_ablacao/parciais/` (192 arquivos), reunidas em `E2_ablacao/previsoes.csv`
  (colunas `braco, folha, h, data_origem, data_alvo, real, previsto`). Piso de ruído: `piso_de_ruido/piso.csv`.
- Janela de avaliação: `data_alvo` de 2024-01-07 a 2026-02-01 (inclusive).
- Régua sazonal: `yhat` = casos 52 semanas antes da semana-alvo, da tabela cortada (`aedes.metricas`).

## E3 — composto (pré-declaração §5)

- Em cada horizonte `h` e semana-alvo, origem `t = data_alvo - h semanas`.
- Para cada folha (completo folha 5 e completo folha 20): MAE nas últimas `N` semanas-alvo com `data_alvo <= t` em que
  AS DUAS folhas têm previsão naquele `h` (pares disponíveis; buracos de calendário ignorados).
- Usa a previsão da folha de menor MAE; empate exato: folha 5. `N = 13` primário; `N = 8` e `N = 26` só descritivos.
- Saídas: `E3_composto/previsoes.csv` (N, h, data_origem, data_alvo, real, previsto, folha_escolhida) e `resumo.csv`
  (N, h, n, mae, fracao_folha20). Âncora: 102 semanas por `h` na janela.

## Comparação A × B (A = candidato, B = comparador), sempre PAREADA por `data_alvo` comum no `h`

- `n` = semanas em comum; `MAE_A`, `MAE_B`; `Delta = MAE_B - MAE_A` (positivo = A erra menos);
  `ganho_pct = Delta / MAE_B * 100`.
- **Diebold-Mariano com correção HLN.** `d_t = |e_B,t| - |e_A,t|` na série pareada ordenada por `data_alvo` (buracos de
  calendário omitidos); `dbar` = média; `gamma_k = (1/n) * soma_{t>k} (d_t - dbar)(d_{t-k} - dbar)`, `k = 0..h-1`;
  `V = (gamma_0 + 2 * soma_{k=1}^{h-1} gamma_k) / n`; `DM = dbar / sqrt(V)`;
  `DM_HLN = DM * sqrt((n + 1 - 2h + h(h-1)/n) / n)`; `p` bilateral pela t de Student com `n-1` graus de liberdade.
  Se `V <= 0`: pesos de Bartlett `(1 - k/h)` nos mesmos lags e coluna `variancia_fallback = true`.
- **Bootstrap de blocos móveis.** Blocos de 8 posições consecutivas da série pareada, início sorteado uniforme em
  `0..n-8`, concatenar até `>= n` e truncar em `n`; 2.000 reamostragens; gerador novo por comparação
  (`np.random.default_rng(42)`); estatística = `ganho_pct` recalculado na reamostra; IC 95% pelos percentis 2,5 e 97,5.
- **Holm** dentro de cada família.
- **Piso (Emenda 1):** `limiar = 2 x piso[folha, h]`. Comparações de folha 5 usam o piso da folha 5; de folha 20, o da
  folha 20; envolvendo o composto, o MAIOR dos dois pisos no `h`; a régua não tem ruído.
- **Veredito:** `p_Holm < 0,05` E `|Delta| > limiar`: se `Delta > 0`, "A melhor"; se `Delta < 0`, "A pior"; senão,
  "sem evidência".

## Famílias (h em {1, 4, 8, 12})

- **F1** (folha 5, 12 testes): A = completo, B = sem_X, X em {casos, clima, vetor}.
- **F2** (folha 5, 12 testes): A = so_X, B = so_calendario.
- **F3** (folha 20, 12 testes): A = completo, B = sem_X.
- **F4** (16 testes, Emenda 1): A = completo folha 5, completo folha 20 e composto N=13, cada um contra a régua
  sazonal; e A = composto N=13 contra completo folha 5.

## E5 — alarme (pré-declaração §7, descritivo)

- `r` = (confirmados de Porto Alegre por município de NOTIFICAÇÃO) / (por município de RESIDÊNCIA), somando fichas com
  `DT_SIN_PRI` em 2018 a 2023; confirmados = `CLASSI_FIN` em 10, 11 ou 12; Porto Alegre = código 431490 em `ID_MUNICIP`
  (notificação) e `ID_MN_RESI` (residência). Zips DENGBR18 a DENGBR24 (principal); `r` também só com DENGBR18 a 23.
- Âncora: soma de `casos_confirmados` de `dados/tabela_final.csv` nas semanas iniciadas em 2018 a 2023 = 12.785; o
  numerador deve ficar a ~1%; senão, investigar antes de seguir.
- `L = 421 x r`. Alerta real = `real` acima de `L`; alerta previsto = `previsto` acima de `L`. A definição de evento
  (estrito `>` ou `>=`, semanas ou eventos) segue a do código antigo `analises/2026-09-26_modelo_composto/calcular_alarme.py`.
- Métricas por braço x folha (8 x 2) e composto N=13, `h` em {1, 4, 8}, nas 102 semanas-alvo do completo em cada `h`:
  VP, FN, FP, sensibilidade = VP/(VP+FN), precisão = VP/(VP+FP), alarmes falsos por ano = FP / 1,96.
  Repetido com `L = 421` sem conversão.

## Escolhas não previstas na especificação (registradas ANTES de rodar)

1. **Operador do alarme.** O código antigo usa `real > limiar` e `previsto > limiar` (estrito) e conta SEMANAS, não eventos.
   O texto da especificação dizia `>=`; seguimos o código antigo (regra da própria especificação) e registramos o desvio.
2. **Sensibilidade e precisão sem denominador.** Como no código antigo: NaN quando não há alerta real (VP+FN = 0) ou
   previsto (VP+FP = 0).
3. **Composto com histórico curto.** Só gera previsão numa origem se houver ao menos `N` pares disponíveis com
   `data_alvo <= t` (nunca usa menos de `N`). Na janela de avaliação isso nunca restringe (há anos de histórico).
4. **E3 em todos os 12 horizontes** (a especificação pede 1, 4, 8, 12 nos testes e as curvas usam os 12); o resumo traz os 12.
5. **DM indefinido.** Se `V <= 0` mesmo com Bartlett (por exemplo, `d_t` constante), `dm_hln` fica NaN, `p_bruto = 1,0` e
   `variancia_fallback = true`. Não depende de resultado: é regra de borda.
6. **Régua.** A grade `(h, data_alvo)` é a do `completo` folha 5 na janela (como na referência certificada); o `real` da
   régua tem de coincidir com o `real` da E2 (conferido).
7. **`alarmes falsos por ano`** divide por 1,96 (constante da especificação), não por `n/52`.
8. **Leitura das previsões** com `float_precision="round_trip"`.
9. Esta rodada não altera nenhum arquivo certificado; só acrescenta `aedes/estatistica.py`, `aedes/composto.py`,
   `aedes/alarme.py`, `aedes/familias.py`, `experimentos/e3_composto.py`, `experimentos/testes_familias.py`,
   `experimentos/e5_alarme.py`, testes novos e as pastas de resultado.
