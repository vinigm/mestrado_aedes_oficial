# PRÉ-DECLARAÇÃO — features de longo prazo (30/08/2026)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## A pergunta

A configuração de referência (**HistGradientBoosting · quantil 0,80 · M1 com vetor**) degrada em
horizonte longo: captura **98%** do pico em 1 semana e só **62%** em 12 semanas.

**Causa medida em 30/08:** a autocorrelação dos casos explica 91% da variação em h=1 e cai a **0%**
em h=12. O modelo perde a muleta principal e sobra clima recente (r≈0,40).

**Hipótese:** as features do projeto são todas de curto prazo — defasagens de 1 a 4 semanas e média
móvel de 4. Não existe nada que capture ciclo anual ou acúmulo de estação, que é justamente o tipo
de sinal que poderia sustentar horizonte longo.

## Os quatro grupos de features novas

Escolhidos por **medição feita antes**, não por intuição (correlação da anomalia, tirando sazonalidade):

| grupo | features | justificativa medida |
|---|---|---|
| **B — lags anuais** | `casos_lag52`, `casos_lag104`, `vetor_lag52` | anomalia dos casos: r=**0,711** (lag52) e **0,342** (lag104) |
| **C — anomalia climática** | temp/precip/umidade menos a norma histórica daquela semana do ano | mede "este ano é atípico", que o nível bruto não mede |
| **D — acúmulo longo** | chuva e calor somados em 8 e 12 semanas | criadouro se forma ao longo de meses, não de 4 semanas |
| **E — ENSO** | `nino34_anom`, `oni` | único candidato a ciclo plurianual; hoje **explicitamente descartado** no config |

**Não entram lags anuais de clima:** a anomalia climática tem r = **−0,013** em lag52. É ruído
meteorológico e foi medido antes de decidir.

## Proteção contra vazamento

Toda feature nova usa **só passado**:

- lags: `shift(52)` e `shift(104)`;
- acúmulo: `rolling(8).sum()` e `rolling(12).sum()` — janelas para trás;
- **norma histórica:** média expansível das ocorrências ANTERIORES daquela semana do ano
  (`expanding().mean().shift(1)`). Nunca a média da série inteira, que veria o futuro.

## Variantes

`A` (referência) · `A+B` · `A+C+D` (clima longo) · `A+E` · `A+B+C+D+E` (tudo) — **5 variantes ×
4 horizontes = 20 execuções**, `passo=1`.

Rodar os grupos separados permite saber **qual** ajuda, e não só se o conjunto ajuda.

## Critério e regras de decisão

Mesma separação: **calibração** até 31/12/2023 escolhe, **avaliação** 2024+ julga.
Métrica primária: **MAE em h=8 e h=12** — é onde a limitação está. Reporto todos os horizontes.

1. **Alguma variante melhora h=8 e h=12 na avaliação** → entra na configuração de referência.
2. **Melhora só na calibração** → sobreajuste; a referência permanece.
3. **Nenhuma melhora** → a degradação em horizonte longo é limite do dado, não falta de feature.
   Vira limitação declarada da dissertação.

**Proibido:** inventar features novas depois de ver o resultado e rodar de novo no mesmo protocolo.
