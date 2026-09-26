# Verificação adversarial — limiar oficial de surto (25/09/2026)

**Método:** WebSearch/WebFetch nas 4 fontes citadas (sem download de arquivo) + reprodução independente
em `python3` (só leitura) do CSV `infodengue_poa_dengue.csv` (857 linhas, 2010-2026), sem usar o
código já existente do projeto.

---

## Veredito por critério

**[0] InfoDengue glossário (MEM) — ✅ CONFIRMADO.**
WebFetch em `lac.tghn.org/recursos/glossario-infodengue` traz literalmente: limiar epidêmico via
*"quartil superior... ou o desvio-padrão"*, MEM como *"régua inteligente"* sem números fixos.
Confirma: **não há valor numérico fixo**, é recalculado por histórico.

**[1] Guia MS 2024 (5 estágios, delegação ao estado/município) — ⏳ PARCIAL.**
`bvsms.saude.gov.br` retornou **HTTP 503** (site fora do ar no momento da checagem) — não dá para
confirmar a citação literal na própria fonte. Confirmação **indireta**: busca externa (planos de
POA/RS/BA/DF) mostra os mesmos 5 estágios (normalidade/mobilização/alerta/emergência/crise) e cada
um definindo seu próprio número — consistente com "delega ao estado/município", mas sem o texto
literal do MS na mão.

**[2] SES-RS/CEVS (LSE/LA) — ✅ CONFIRMADO.**
Busca externa traz a fórmula: **LSE = média móvel (5 semanas) da incidência de prováveis + 2 desvios-
padrão**, série de referência **2015-2021**; **LA = LSE − 45%**. Bate com o critério. Ambos dinâmicos,
recalculados por semana epidemiológica — não um número fixo.

**[3] SMS-POA Quadro 1 (10,00 / 30,0 / 50,0 por 100 mil) — ❓ NÃO_VERIFICÁVEL.**
O PDF (`prefeitura.poa.br/.../2026_Plano_Municipal...pdf`) é **imagem/binário não extraível por texto**
via WebFetch (confirmado 2x, inclusive no Boletim Epidemiológico 1/2026 que citaria os mesmos
critérios). Sem baixar o arquivo (vedado pela tarefa), não dá para confirmar os números literais do
Quadro 1 nem a população **1.404.269**. Confirmação **indireta**: busca externa acha o mesmo plano
com 5 estágios e menciona POA em "mobilização" na SE2/2026 por incidência de prováveis — estrutura
bate, números específicos não puderam ser lidos.

---

## Limiar deduzido pelo pesquisador — reprodução independente

Script próprio (`verificar_limiar.py`), sem reusar código do projeto:

- **Transição `nivel_inc` 0→1** (casos/semana): mínimo do nível 1 é **6** em todos os anos 2010-2020
  (máximo do nível 0 = 5 nesses anos) — ✅ confirmado. **2021 é exceção não observada**: não há
  semana com `casos` em 6-8 nesse ano no CSV, então o corte real de 2021 fica indeterminado entre
  6 e 9 (o pesquisador assumiu 6 por continuidade — **hipótese, não dado direto**). De 2022 em
  diante, mínimo do nível 1 sobe: **8** (2022) · **14** (2023) · **36** (2024) · **94** (2025) —
  ✅ bate exatamente com os números do pesquisador.

- **Transição `nivel_inc` 1→2:** mínimo do nível 2 fica em **21-25** em 2010-2019 (bate com
  "~20-23"), sobe para **48** (2022) · **49** (2023) · **55** (2024) · **105** (2025) — ✅ os
  extremos citados ("55-105 em 2024-2025") batem exatamente.

- **População:** `pop = 1.488.252` constante em **2010-2022**; muda para `1.404.269` a partir de
  **2023** (2023 tem os dois valores misturados, 2024+ só o novo) — ✅ confirmado.

- **`nivel_inc` é essencialmente monotônico em `casos` dentro do mesmo ano** (só 2025 quebra a
  monotonicidade estrita) — ✅ confirma que é um corte por ano, recalculado, não uma regra fixa.

- **`nivel` (cor do alerta) NÃO se reduz a corte de incidência:** testei sobreposição de faixas de
  `p_inc100k` entre níveis adjacentes, ano a ano — **houve sobreposição em TODOS os 17 anos**
  (2010-2026), nunca uma faixa limpa. ✅ confirma fortemente a conclusão do pesquisador: o alerta
  combina incidência com tendência (Rt), não é redutível a volume de casos.

- **Achado extra não citado pelo pesquisador:** `p_inc100k` bate exatamente com
  `casos_est/pop*100000` (0 discrepâncias de 857) mas **não** bate com `casos/pop*100000` (8
  discrepâncias) — a incidência oficial usa **casos estimados**, não confirmados. Vale registrar
  no ESTADO.md se for citar `p_inc100k` como proxy de "casos".

**Limiar deduzido, no geral: CONFIRMA.** Único ponto a suavizar no texto: o corte "5→6" para 2021
é inferido por continuidade, não observado diretamente nos dados (falta semana com 6-8 casos nesse
ano).
