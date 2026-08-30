# PRÉ-DECLARAÇÃO — alvo nowcasting e features do InfoDengue (30/08/2026)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## Contexto

O arquivo `infodengue_poa_dengue.csv` já baixado tem **31 colunas, 100% preenchidas desde 2010**, e
o projeto usa **uma** (`casos`). Este teste avalia duas dessas colunas esquecidas.

## TESTE A — qual alvo?

**Problema:** a taxa de confirmação caiu de 73,2% (2022) para 38,3% (2025) — quanto maior a
epidemia, menor a fração confirmada. A série de confirmados **achata os anos grandes**, e parte do
"viés de subestimação do pico" que perseguimos hoje pode ser do **alvo**, não do modelo.

**Três alvos, mesma configuração vencedora** (HistGB · quantil 0,80 · M1):

| alvo | o que é |
|---|---|
| `casos_confirmados` | SINAN — o alvo atual |
| `casos` (InfoDengue) | notificados |
| **`casos_est`** | **notificados corrigidos por nowcasting** (corrige atraso de notificação) |

⚠️ **Alvos diferentes têm escalas diferentes** — MAE bruto não é comparável entre eles. A métrica de
comparação é a **captura do pico** (previsto ÷ real nas semanas de pico) e o **R²**, que são
adimensionais.

**Regra de decisão:** se `casos_est` capturar o pico melhor que `casos_confirmados`, parte do viés
era do alvo, e isso muda a leitura de tudo que medimos hoje.

## TESTE B — features de transmissão

Cinco colunas nunca usadas, todas contemporâneas (disponíveis em t):

`Rt` · `p_rt1` · `notif_accum_year` · `receptivo` · `transmissao`

**Justificativa:** `Rt` é o parâmetro de transmissão — resume num número o efeito de imunidade,
sorotipo e controle. `notif_accum_year` é proxy de imunidade acumulada na temporada. São o tipo de
variável cuja ausência foi apontada como limitação estrutural — inclusive pela própria Fiocruz no
Relatório Técnico 02/2026.

**Verificação de vazamento feita ANTES (30/08):** `Rt(t)` correlaciona **+0,118** com casos passados
(t−4) e **−0,106** com futuros (t+4). Vazamento produziria o padrão inverso. **Aprovado.**
Ressalva: sozinho o `Rt` carrega pouco sinal (|r| < 0,12 em todos os horizontes).

**Regra de decisão:** entra na referência se melhorar **h=8 e h=12** na avaliação — os horizontes
onde a limitação está.

## Protocolo (igual aos anteriores)

Calibração até **31/12/2023** escolhe · avaliação **2024+** julga · `passo=1` · horizontes 1, 4, 8, 12.
