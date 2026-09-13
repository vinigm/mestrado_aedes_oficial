# Calibração quantílica do HistGradientBoosting — 30/08/2026

> **A pergunta:** o melhor algoritmo do projeto (HistGradientBoosting), calibrado por regressão
> quantílica, corrige o viés de subestimação do pico de casos?
> **A resposta:** sim no critério pré-declarado — alpha **0,85** reduz o viés do pico na avaliação
> em todos os horizontes (h=1: -111,8 → -21,6), mas **não elimina** o viés, que continua negativo e
> cresce forte em h=8/h=12.
> Status: ⚠️ exploratório (ver §6 — vazamento temporal não corrigido). Pré-declaração: sim,
> `PRE_DECLARACAO.md` nesta pasta.

## 1. Por que este teste foi feito

- Um teste anterior (30/08/2026, mesmo dia) já tinha apontado a regressão quantílica como remédio
  para a subestimação do pico, mas rodou em **LightGBM** — só o 3º melhor algoritmo do projeto
  (R² médio 0,749).
- Faltava confirmar o remédio no algoritmo que a tese de fato usa: **HistGradientBoosting**
  (R² médio 0,779).
- A pré-declaração prometeu, **antes de rodar**: separar o alpha (0,70/0,80/0,85/0,90) por menor
  `|viés no pico|` medido só até 31/12/2023 (calibração), com guarda de não piorar o MAE global em
  mais de 20% — e só depois olhar 2024+ (avaliação), nunca usado na escolha.

## 2. Como foi medido

- **Alvo:** `y_h` — casos notificados na cidade, horizonte `h` semanas à frente (`cidade_regressao`).
- **Algoritmo:** `HistGradientBoostingRegressor`, hiperparâmetros fixos do projeto
  (`max_iter=250`, `learning_rate=0,05`, `max_leaf_nodes=15`, `min_samples_leaf=5`).
- **Variantes:** `padrao` (perda `squared_error`) + `quantil_0.70/0.80/0.85/0.90`.
- **Horizontes:** 1, 4, 8, 12 semanas. **Passo=1** — toda semana, não uma a cada duas.
- **Janela:** walk-forward com **mínimo de 104 semanas de treino** antes do primeiro teste
  (`minimo_semanas_treino=104`), corte de maturidade de 12 semanas.
- **Separação calibração × avaliação:** pela data da **semana-alvo** — até 31/12/2023 é calibração,
  01/01/2024 em diante é avaliação.
- **Pico:** semanas com `real > 100` casos.
- **Execuções:** 5 variantes × 4 horizontes = 20 walk-forwards completos, **1.507 semanas testadas**
  no total (307+304+300+296 por variante). Tempo total: **52,5 min** (`calibracao_log.txt`).
- **Critério de escolha do alpha:** menor `|viés no pico|` médio nos 4 horizontes, **só na
  calibração**, com guarda de o MAE global não piorar mais de 20% contra o padrão.

## 3. O que deu

| variante | \|viés pico\| calibração | Δ MAE vs. padrão | aprovado |
|---|---|---|---|
| quantil_0,85 | **103,3** | -1,4% | ✅ escolhido |
| quantil_0,90 | 107,8 | +4,1% | ✅ |
| quantil_0,80 | 130,4 | -0,9% | ✅ |
| quantil_0,70 | 149,0 | -1,2% | ✅ |

- O critério pré-declarado escolheu **alpha 0,85** — menor viés absoluto e dentro da guarda de MAE.

| h | viés pico padrão (avaliação) | viés pico quantil_0,85 (avaliação) | R² padrão | R² quantil_0,85 |
|---|---|---|---|---|
| 1 | -111,8 | **-21,6** | 0,833 | 0,874 |
| 4 | -222,2 | -86,0 | 0,711 | 0,739 |
| 8 | -441,6 | -325,6 | 0,636 | 0,779 |
| 12 | -494,3 | -420,6 | 0,675 | 0,728 |

- Em **todos os 4 horizontes** o quantil_0,85 reduz o viés do pico na avaliação — a maior redução
  relativa é em h=1 (-80,7% do viés) e a menor em h=12 (-14,9%).
- O viés continua **negativo em todos os horizontes** (o modelo ainda subestima o pico, só que
  menos) — não é correção completa.
- R² melhora em todos os horizontes com quantil_0,85; MAE global também melhora em h=1, h=8 e h=12
  — só piora em h=4 (185,8 contra 183,0 do padrão, +1,5%).
- `n` por período: 109 semanas de avaliação e entre 187 e 198 de calibração (cai com o horizonte,
  como esperado — janela mais curta em h maior); **39 picos** na avaliação e **25** na calibração,
  em todos os horizontes (mesmas semanas-alvo, o que muda é a base de treino).

## 4. Conclusão

- **FATO:** com o critério pré-declarado e medido só na calibração, alpha 0,85 venceu
  (`|viés|`=103,3, guarda de MAE em -1,4%) — números em `calibracao_resumo.csv` e
  `calibracao_log.txt`, conferidos por leitura direta do CSV.
- **FATO:** na avaliação (nunca usada na escolha), o viés do pico caiu em todos os 4 horizontes com
  quantil_0,85, incluindo o salto citado externamente de -111,8 para -21,6 em h=1.
- **HIPÓTESE:** a calibração quantílica é adequada como "contribuição metodológica" da dissertação —
  isso é uma leitura do resultado (regra de decisão nº1 da pré-declaração), não um número medido.
- **NÃO SE PODE AFIRMAR:** que o viés do pico foi eliminado — ele permanece grande e negativo em
  h=8 (-325,6) e h=12 (-420,6). O remédio atenua, não resolve, e atenua menos quanto maior o
  horizonte.

## 5. Ressalvas e o que ficou em aberto

- **Sem correção de múltiplas comparações**: 5 variantes × 4 horizontes × 2 períodos são muitas
  comparações; nenhuma passou por Holm ou equivalente.
- **A previsão quantílica não estima a média** — um modelo em alpha 0,85 mira um patamar
  ultrapassado só em 15% das vezes, enviesado para cima de propósito (ressalva já na
  `PRE_DECLARACAO.md`). Comparar seu R²/MAE com o do modelo padrão não é competição entre iguais.
  Isso **infla a leitura de "melhora"**: parte do ganho de viés é o preço, esperado, de mirar acima
  da média.
- **Amostra pequena de picos**: só 25 (calibração) e 39 (avaliação) semanas acima de 100 casos —
  médias de viés no pico são sensíveis a poucas semanas extremas.
- **Não há reexecução independente** (nem certificação adversarial) desta rodada especificamente —
  só a leitura direta dos CSVs feita aqui.

## 6. ⚠️ Efeito do vazamento temporal descoberto em 13/09/2026

- Esta análise **RODOU com o corte de treino defeituoso** e **NÃO foi refeita** — está na lista
  explícita dos "não refeitos" pós-correção.
- O código (`rodar_walk_forward`, linha 121) corta `treino = validos.iloc[:indice_corte]` — ou seja,
  corta pelo **índice de origem** ordenado por `data`, não pela data-alvo. Como cada linha carrega
  `y_h` datado `data_alvo = data_origem + h`, as últimas `h-1` linhas do treino têm alvo posterior à
  semana que está sendo prevista — o mesmo vazamento documentado em
  `2026-09-13_correcao_vazamento_treino/README.md`.
- **Direção provável da inflação:** o vazamento favorece horizontes maiores (mais linhas
  contaminadas por corte), então os números de h=8 e h=12 desta análise — inclusive a "melhora" de
  R² de 0,636 para 0,779 em h=8 — estão **provavelmente inflados para cima** (otimistas) em ambas as
  variantes, padrão e quantil_0,85, na mesma direção. Como o vazamento afeta as duas, a comparação
  *relativa* entre padrão e quantil_0,85 é mais robusta que qualquer número absoluto isolado — mas
  isso é **hipótese**, não medido aqui.
- Consequência prática: os números desta pasta **não devem ser citados como resultado final** da
  dissertação sem re-rodar com o corte corrigido; servem hoje como evidência de que a calibração
  quantílica *tem sinal*, não como valor definitivo do ganho.

## 7. Arquivos

- `PRE_DECLARACAO.md` — desenho e critério de escolha do alpha, escritos antes de rodar.
- `calibrar_quantilico.py` — script único: monta dados, roda os 20 walk-forwards, escolhe o alpha,
  imprime as tabelas de viés/R²/MAE.
- `saidas/calibracao_previsoes.csv` — uma linha por semana testada (variante, h, data de origem,
  data-alvo, real, previsto).
- `saidas/calibracao_resumo.csv` — uma linha por (variante, h, período) com n, n_picos, MAE, R²,
  viés no pico.
- `saidas/calibracao_log.txt` — saída completa da execução, com as tabelas citadas neste README.
