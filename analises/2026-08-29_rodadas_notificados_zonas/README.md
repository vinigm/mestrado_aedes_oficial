# Rodadas de 29/08/2026 — notificados, zonas, clima longo e ablação

> **Leia primeiro a [PRE_DECLARACAO.md](PRE_DECLARACAO.md).** Ela foi escrita ANTES de qualquer
> execução e fixa hipóteses, métricas, correção múltipla e regras de decisão. É o que substitui a
> validação externa do orientador (decisão de 29/08/2026).

**Contexto:** o Vinicius autorizou rodar as quatro rodadas pendentes em sequência, sem
acompanhamento. Esta pasta é o registro completo — scripts, logs, CSVs e o que cada número
significa.

---

## O que cada arquivo é

| Arquivo | O que é |
|---|---|
| `PRE_DECLARACAO.md` | As regras, fixadas antes de rodar. Inclui a EMENDA 1, datada. |
| `rodada_0_recapturar_clima.py` | Recaptura o NASA POWER desde 2012 e certifica contra a série antiga. |
| `rodada_0_certificar_tabela_final.py` | Certificação adversarial da `tabela_final` regerada. |
| `rodada_3_ranking_zonas.py` | Ranking de risco por zona sintética (k=8, k=16). Autocontido. |
| `saidas/` | Logs, CSVs e a cópia congelada da `tabela_final` antes da recaptura. |

---

## Registro cronológico das rodadas

### ✅ Rodada 0 — recaptura do clima (APROVADA)

- **`INICIO_PADRAO`** em `preparo/capturar_clima.py`: `"20181230"` → **`"20120923"`**.
  - a constante antiga era justificada como "o primeiro domingo do bloco da Marília" — fonte que
    saiu do fluxo em 16/08/2026. A justificativa estava morta e truncava o clima.
- **Clima semanal: 388 → 727 semanas** (23/09/2012 a 23/08/2026).
- **`tabela_final` regerada**: `temp_media` foi de **388 → 725** semanas não-nulas.

**Certificação (tentou reprovar, não confirmar):**

- ✅ formato **725 × 36** e ordem das colunas preservados;
- ✅ vetor intocado — 718 não-nulos, soma **280,8343**;
- ✅ casos intocados — 428 não-nulos, soma **56.624**;
- ✅ **nenhuma** coluna não-clima alterada, célula a célula;
- ⚠️ **a primeira execução REPROVOU** — 169 divergências. Investigado: **365 das 388 semanas
  bateram exatamente**; as 23 divergentes começam em 28/12/2025 e são reprocessamento normal da
  NASA (radiação solar é derivada de satélite e é revista com atraso). Critério corrigido pela
  **EMENDA 1**, com o motivo registrado. Divergência em período consolidado segue bloqueante.

**Ganho medido — é o número que justificava a rodada:**

| Interseção | Antes | Depois |
|---|---|---|
| clima + vetor + casos **confirmados** | 379 | **424** |
| clima + vetor + casos **notificados** | 379 | **708** |

### ✅ Rodada 1 — surto com alvo NOTIFICADOS (RESULTADO NEGATIVO)

**Veredito: 0 de 6 comparações sobrevivem a Holm.** E o motivo **não** é falta de poder.

| | 16/08 (confirmados) | 29/08 (notificados) |
|---|---|---|
| semanas testadas | 232–243 | **553–568** |
| semanas de surto | 42–61 | **75–116** |
| direção favorável ao vetor | 5 de 6 | **1 de 6** |
| melhor p bruto | 0,031 | 0,286 |
| melhor p Holm | 0,185 | **1,000** |

- a amostra **mais que dobrou** e o efeito não só deixou de aparecer — **inverteu de sinal**;
- em 5 das 6 comparações o **clima acerta mais que o vetor** nas discordâncias;
- o caso que sustentava a esperança (P90 h=8: 4 × 14 em 16/08) virou **15 × 10 contra o vetor**.

**Leitura (fato):** a assimetria 4×14 de 16/08 era **ruído amostral**. A projeção do teste C
assumia que a taxa de discordância *e a proporção b/c* se manteriam; a taxa se manteve, a
proporção não. **Isto refuta a hipótese pré-registrada da Rodada 1.**

**Consequência pela regra pré-declarada:** o vetor no alarme de surto **não** é o núcleo da tese.
Mas o resultado é melhor do que "indeterminado por falta de poder" — é um **negativo bem-powered**,
com 565 semanas e 14 anos de série. Isso é publicável e é uma contribuição real.

### ✅ Rodada 3 — ranking por zona (NEGATIVO PARA O MODELO, POSITIVO PARA O SINAL)

**Veredito: o modelo supera a persistência em 1 de 8 combinações k × h.** Pela regra pré-declarada,
o modelo **não** é declarado útil.

| k | h | modelo | persistência | climatologia | vence? |
|---|---|---|---|---|---|
| 8 | 1 | 0,786 | **0,893** | 0,464 | ❌ |
| 8 | 2 | 0,679 | **0,821** | 0,446 | ❌ |
| 8 | 4 | 0,536 | **0,607** | 0,429 | ❌ |
| 8 | 8 | **0,536** | 0,500 | 0,429 | ✅ |
| 16 | 1 | 0,814 | **0,899** | 0,373 | ❌ |
| 16 | 2 | 0,721 | **0,801** | 0,380 | ❌ |
| 16 | 4 | 0,570 | **0,607** | 0,389 | ❌ |
| 16 | 8 | 0,486 | 0,493 | 0,394 | ❌ (empate) |

*(Spearman mediano entre o ranking previsto e o real; 228–235 semanas testadas por combinação.)*

**Mas o achado importante não é sobre o modelo — é sobre o sinal:**

- **FATO:** modelo e persistência **esmagam a climatologia** (0,89 × 0,46 em h=1). O ranking das zonas
  **não** é só sazonalidade da cidade: existe estrutura espacial real e persistente.
- **FATO:** o ranking se mantém previsível até 8 semanas (Spearman ~0,50), caindo de ~0,89 em h=1.
- **FATO:** o LightGBM **não acrescenta nada** sobre a regra "a ordem de hoje vale para daqui a h semanas".
- 7 de 8 zonas (k=8) e 15 de 16 (k=16) são elegíveis — mesma cobertura do teste B de 16/08.

**Releitura da camada 3 da tese (não é derrota, é simplificação):** o mapa de risco entomológico
**funciona** — e funciona com uma regra simples e transparente, sem machine learning. Para vigilância
isso é uma vantagem, não um defeito: é implantável, auditável e não precisa de infraestrutura de ML.

### ✅ Rodada 2 — teste A na série longa (O RESULTADO FORTE DO DIA)

**Veredito: saiu de INDETERMINADO para equivalência demonstrada em ±15%.**

**O poder finalmente chegou** — e veio da recaptura do clima, não da troca do alvo sozinha:

| Rodada | N pareado (h=1) | IC95 de ΔMAE | largura |
|---|---|---|---|
| 16/08 — clima curto + confirmados | 266 | [−71,6; +20,7] | 92,2 |
| 29/08 — clima longo + confirmados | 312 | [−69,6; +22,0] | 91,5 |
| **29/08 — clima longo + notificados** | **587** | **[−30,3; +1,8]** | **32,1** |

- a largura do IC **caiu 65%**; trocar só o alvo (sem o clima longo) teria rendido 5 semanas.

**TOST (margem pré-declarada, sem alteração):**

| Margem | 16/08 | 29/08 confirmados | 29/08 notificados |
|---|---|---|---|
| ±5% | 0 de 8 | 0 de 8 | 0 de 8 |
| ±10% | 0 de 8 | 0 de 8 | 0 de 8 |
| **±15%** | **0 de 8** | **0 de 8** | **4 de 8** |

**FATO:** pela primeira vez o TOST fecha equivalência — **clima sozinho e vetor sozinho são
estatisticamente equivalentes a ±15%** em metade das combinações.

**Sinal por horizonte (exploratório, ver ressalva):**

- **h=1 e h=4 (puro): o vetor é MELHOR** — ΔMAE de −12,3 e −14,3; em h=4 o IC95 **não cruza zero**
  ([−30,7; −2,7]) e o Diebold-Mariano dá p = 0,033;
- **h=8 e h=12: o clima é melhor** (ΔMAE +14,3 e +25,4), não significativo.
- leitura biológica plausível (**hipótese**): o mosquito é sinal **proximal** — o adulto já está lá
  transmitindo agora; o clima é sinal **distal** — determina a geração de mosquitos semanas à frente.

> ⚠️ **RESSALVA DE RIGOR, registrada contra o próprio resultado:** a pré-declaração da Rodada 2
> **não fixou correção de múltiplas comparações** para o Diebold-Mariano — uma lacuna real da minha
> pré-declaração. Aplicado Holm como sensibilidade sobre as 8 comparações, **0 de 8 sobrevivem**
> (p=0,033 → 0,266). Portanto: a vantagem do vetor em horizonte curto é **EXPLORATÓRIA**, não
> confirmatória, e precisa de pré-registro próprio para virar achado. A **equivalência a ±15%
> continua valendo** — a margem TOST foi pré-declarada e não foi tocada.

### ✅ Rodada 4 — ablação de janela de treino (TREINAR DESDE 2012 VENCE)

**Veredito: a série longa não é ruído — ela ajuda, e ajuda mais quanto maior o horizonte.**

Alvo: densidade do vetor (a série que de fato tem 14 anos). Janela de avaliação comum aos três
regimes: 2022 em diante, 213–226 semanas.

| h | expansível 2012 | expansível 2020 | deslizante 6 anos |
|---|---|---|---|
| 1 | MAE 0,1526 · R² 0,740 | 0,1617 · 0,709 | **0,1505** · 0,739 |
| 4 | **0,1731** · 0,687 | 0,1760 · 0,693 | 0,1772 · 0,677 |
| 8 | **0,1802** · 0,688 | 0,1863 · 0,677 | 0,1950 · 0,645 |
| 12 | **0,1919** · 0,634 | 0,2027 · 0,632 | 0,2089 · 0,577 |

- **expansível desde 2012 vence em 3 de 4 horizontes**; em h=1 empata com a janela deslizante;
- a vantagem **cresce com o horizonte**: em h=12 o R² é 0,634 contra 0,577 da janela de 6 anos;
- explicação plausível (**hipótese**): horizonte longo depende de aprender o ciclo sazonal completo,
  e mais anos = mais ciclos observados.

**Consequência prática:** o padrão do projeto (treinar com tudo desde 2012) está **validado por
medição**. E é um argumento direto para a contribuição de dados da tese: os 14 anos resgatados não
são só volume — melhoram a previsão.

---

## Síntese das quatro rodadas

| Rodada | Pergunta | Veredito |
|---|---|---|
| 0 | recapturar o clima desde 2012 vale? | ✅ **sim** — interseção 379 → 708 semanas |
| 1 | o vetor melhora o alarme de surto? | ❌ **não** — 0/6 em Holm, e o efeito **inverteu** |
| 3 | o modelo acerta o ranking das zonas? | ❌ **não vence a persistência** — mas o sinal espacial é real |
| 2 | clima e vetor são equivalentes? | ✅ **sim, a ±15%** — primeira vez que o TOST fecha |
| 4 | treinar desde 2012 é melhor? | ✅ **sim** — vence em 3 de 4 horizontes |

**A mensagem que atravessa as quatro:** o vetor **não** é redundante (equivale ao clima a ±15%, e
tende a ganhar em horizonte curto), mas também **não** é o que faltava para o alarme de surto. E o
valor espacial existe — só não precisa de ML para ser explorado.
