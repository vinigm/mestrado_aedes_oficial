# Certificação adversarial — varredura do limiar de decisão (26/09/2026)

> Agente independente, cético, objetivo é REPROVAR. Reimplementação do zero, sem reaproveitar
> `rodar.py` do executor. Script próprio em Python (pandas/scipy), lendo os mesmos CSVs de entrada
> (`previsoes_por_braco.csv` da bateria de 23/09, `tabela_final.csv`, `mcnemar_holm.csv` de 25/09).

---

## Veredito

✅ **APROVADO COM RESSALVA.**

Todos os números centrais (trava, blocos contíguos, varredura, McNemar, família de Holm, proibição
de apresentar "melhor D") reproduziram **exatamente** na reimplementação independente. Um problema
real foi encontrado na **narrativa descritiva da Parte C** (bootstrap) — não nos números salvos em
CSV, mas na frase do README que caracteriza qual teste "infla" e por quê. Não afeta a conclusão
confirmatória de `E_421` (que se mantém: 0 de 4 combinações passam no critério).

---

## O que reproduziu exatamente

1. **Trava (E_100, M_adotado, 2024+):** recalculado do zero a partir de `previsoes_por_braco.csv` +
   `tabela_final.csv` (hash conferido, `6f34b854…`, 725 linhas). h=4: sens **0,9706**, prec **0,9429**,
   falsos/ano **0,6667**. h=12: sens **0,7692**, prec **0,8108**, falsos/ano **2,3333**. Bate o
   relatado e a âncora de 25/09 dentro da tolerância.

2. **Blocos contíguos** (real > limiar, período 2024+, 121 semanas com dado): `100→39/2 blocos (maior 20)`,
   `140→38/2 (maior 20)`, **`421→28/2 (maior 14)`**, `702→23/2 (maior 12)`. Bate a âncora da
   pré-declaração linha a linha.

3. **3 células da varredura** escolhidas por mim (não as do executor): `M_adotado h=4 D=421` →
   sens 1,000/esp 0,960/youden 0,960; `M_adotado h=12 D=100` → sens 0,929/esp 0,851/youden 0,780;
   `M_folha20 h=8 D=300` → sens 1,000/esp 1,000/youden 1,000. As 3 batem exatamente
   `saidas/varredura_limiar_decisao.csv`.

4. **McNemar refeito do zero**, todos os 8 testes de `E_421` (não só os 2 pedidos), reimplementando
   `binomtest` exato: discordantes e p_bruto batem **em todas as 8 linhas** de
   `mcnemar_holm_familia_combinada_24_testes.csv` (ex.: `M_adotado h=12 vs R_ano_passado`:
   disc=11, p=0,011719 — igual).

5. **Holm sobre a família de 24:** confirmado que a família tem **16 (25/09) + 8 (novas)** e que a
   correção foi recalculada **sobre o total de 24**, não isolada nos 8 novos — reimplementação
   própria do Holm step-down bate a coluna `p_valor_holm` salva com diferença de arredondamento
   (~1e-16) em todas as 24 linhas, incluindo as 16 antigas. **4 significativos**, mesmos 4 do
   relatado (os 2 modelos perdendo para `R_hoje` em h=12).

6. **Critério de ganho `E_421`:** as 4 combinações (2 modelos × h=4/h=12) meu recálculo bate
   `criterio_de_ganho_e421.csv` linha a linha — **0 de 4 passam** (h=4 vence Youden mas p_holm=1,0;
   h=12 perde Youden). Veredito confirmatório do executor está correto.

7. **Bootstrap, 1 p refeito com a mesma semente** (`M_adotado vs R_ano_passado, h=12, L=13,
   semente 20260926`): meu `p_bootstrap≈0,040` contra o salvo `0,0403` — dentro do ruído esperado de
   Monte Carlo (a ordem de consumo do gerador difere porque testei só essa célula isolada, não a
   sequência completa dos 32 testes). Confirma o método e a ordem de grandeza.

8. **Pergunta crítica (item 7 do brief): o executor apresentou algum "melhor D" como resultado?**
   **NÃO.** Conferido em `README.md` e em `rodar.py`
   (`verificar_previsao_youden_acima_do_evento`): a função existe só para checar a previsão declarada
   (D>421), o resultado é logado como "CONFIRMOU/FALHOU" e o texto do README diz explicitamente
   "Isso não vira resultado (a pré-declaração proíbe apresentar o melhor D como vencedor)". A
   pré-declaração foi respeitada neste ponto crítico.

---

## 🔴 Achado — Parte C: caracterização do teste "mais equilibrado" está errada

**O que o README/relatório diz:** *"dos 8 testes de `E_421`, a razão `p_bootstrap/p_nominal` fica
acima de 1 (inflação) **só** em `M_adotado vs R_ano_passado, h=12` (razão entre 2,1 e 3,4) — **o
teste com discordantes mais equilibrados (7 contra 4)**."*

**O que os dados salvos em `bootstrap_inflacao_p.csv` mostram** (reconferido linha a linha):

| Teste | Discordantes (modelo acerta / base acerta) | Razão p_boot/p_nominal (L=4,8,13,26) |
|---|---|---|
| `M_adotado h=4 vs R_ano_passado` | **7 / 2** | **1,10 · 1,44 · 1,45 · 1,51** — todas > 1 |
| `M_adotado h=12 vs R_ano_passado` | **1 / 10** | 0,24 · 2,45 · 3,44 · 2,11 — 3 de 4 > 1 |

Duas divergências factuais, não uma questão de estilo:

- **A contagem "7 contra 4" não existe em nenhuma das 8 linhas da tabela.** O par mais próximo é
  `7 / 2` (h=4) — que é justamente o teste que o relatório **não menciona** como fonte de inflação,
  apesar de ter razão > 1 em todos os 4 comprimentos de bloco.
- **O teste que o relatório chama de "mais equilibrado" (h=12, `1/10`) é, na verdade, o MAIS
  desequilibrado dos dois candidatos** (razão 10:1, contra 3,5:1 em h=4). A mecânica que o próprio
  relatório propõe para explicar a inflação — "só quando os discordantes são equilibrados" — é
  contrariada pelos seus próprios números: o teste mais equilibrado (h=4, 7:2) é que teria, por essa
  lógica, mais razão de inflar, e de fato infla (ainda que sem cruzar o gatilho de aviso obrigatório,
  já que fica abaixo de 3).

**Consequência prática:** a Parte C é descritiva por pré-declaração, e o critério de "aviso
obrigatório" (razão > 3) só é cruzado por `M_adotado h=12 vs R_ano_passado` em L=13 (3,44) — nisso o
relatório está certo, e o aviso foi de fato incluído. Mas a frase "só em h=12" está **incompleta**:
são **2 dos 8 testes** (h=4 e h=12, ambos contra `R_ano_passado`) que mostram razão > 1 na maioria
dos comprimentos de bloco, não 1. Isso não muda o veredito confirmatório de `E_421` (que depende do
p de Holm nominal, não do bootstrap, e já é negativo nos 4), mas é uma imprecisão que deve ser
corrigida antes de qualquer citação da Parte C — inclusive porque a leitura errada ("só o mais
equilibrado infla") é o tipo de generalização não sustentada que a pré-declaração pede para evitar.

---

## Itens do brief não cobertos por esta certificação (por desenho, não por omissão)

- Não recontei os outros 6 testes McNemar de `E_421` fora dos 2 pedidos — mas o item 5 acima já
  reconferiu **os 8**, então o requisito mínimo (2) foi excedido.
- Não recalculei os 32 pontos do bootstrap (4 L × 8 testes) — só 1, conforme pedido; os demais foram
  auditados por leitura cruzada do CSV salvo contra a narrativa do README (é assim que o achado acima
  foi encontrado).
- O desvio do teste de 13/09 (não localizado para bootstrap) foi conferido apenas por leitura: o
  arquivo `modelagem_aedes/dados/saidas/resultados/surto_notificados_mcnemar.csv` existe e tem
  `n=553, discordantes=30, p_holm=0,0370` como alegado; não fui atrás do código-fonte de
  `rodar_cidade_surto_notificados` para confirmar que as previsões por semana realmente não foram
  persistidas — aceito a alegação do executor como plausível e não contraditada pelo que vi.

---

## Recomendação

Corrigir a frase da Parte C do README (e, se citada em slide/documento, em qualquer lugar que
repita "só em h=12") para: **"a razão p_bootstrap/p_nominal supera 1 em 2 dos 8 testes — ambos
contra `R_ano_passado` (h=4 e h=12) — e cruza o gatilho de aviso obrigatório (razão>3) só em h=12,
L=13"**. Fora isso, a rodada pode ser considerada certificada: trava, contagem de blocos, McNemar,
Holm sobre a família de 24 e a proibição de apresentar "melhor D" como resultado — todos batem a
reimplementação independente.
