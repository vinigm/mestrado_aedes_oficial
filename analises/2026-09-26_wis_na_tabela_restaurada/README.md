> ⚠️ **Nota do orquestrador, 26/09/2026:** o brief desta rodada apontava, por erro meu, para a
> pré-declaração de `2026-09-26_varredura_limiar_de_decisao/`, que trata de outro assunto. A
> pré-declaração que governa esta rodada é a **seção B** de
> `../2026-09-25_segunda_bateria_noturna/PRE_DECLARACAO.md`, com a emenda de 26/09 01h20 que
> acrescentou o quantil 0,85 para a trava. O certificador reportou a troca em vez de decidir sozinho.

# WIS e quantis múltiplos — refeito na tabela restaurada (sem 2026)

> Refaz a Rodada B da segunda bateria noturna (`analises/2026-09-25_segunda_bateria_noturna/B_quantis_e_wis/`,
> que rodou às 01h23 de 26/09 **sobre a tabela contaminada com 2026**) agora sobre a
> **tabela restaurada** (`tabela_final.csv`, sha256 `6f34b854…`, 725 linhas, até SE 202632,
> `casos_confirmados` parando em SE 202617 — confirmado por hash antes de rodar).
>
> Script: [`rodar.py`](rodar.py), cópia de `B_quantis_e_wis/rodar.py` com 2 desvios reportados
> abaixo (nenhuma outra lógica mudou). Log completo: [`execucao.log`](execucao.log).

---

## Trava — VÁLIDA (com desvio reportado)

| h | MAE medido | MAE esperado (painel publicado) | Veredito |
|---|---|---|---|
| 1 | 98,0 | 98,0 | ok |
| 4 | 219,7 | 219,7 | ok |
| 8 | 272,6 | 272,6 | ok |
| 12 | 278,8 | 278,7 | ok |

Tolerância 0,2. Janela 2024-01-01 a 2026-02-01, n=102.

### ⚠️ Desvio 1 — anchor da trava corrigido (reportado, não decidido em silêncio)

O `rodar.py` original de 25/09 tinha `TRAVA_ESPERADA_MAE = {1: 97.4, 12: 280.0}` — calibrado para a
tabela **contaminada** com 2026. Rodando essa cópia sem mudar nada além dos caminhos, a trava
**DIVERGIU** (h=1 medido 97,99 contra 97,4 · h=12 278,82 contra 280,0, ambos fora da tolerância 0,2).
A investigação embutida do próprio `harness.py` (`conferir_trava_de_validacao`, chamada automaticamente
na falha) rodou o mesmo cenário adotado contra `harness.PAINEL_PUBLICADO` — o painel publicado original
(98,0/219,7/272,6/278,7), **o mesmo anchor desta tarefa** — e bateu nos 4 horizontes. Troquei
`TRAVA_ESPERADA_MAE` para esse anchor (ver comentário datado no código) e refiz a rodada; a segunda
rodada passou. Nenhuma outra lógica foi alterada.

### ⚠️ Desvio 2 — caminhos relativos ajustados (permitido pela tarefa)

Esta pasta fica 1 nível mais rasa que `B_quantis_e_wis/` original, então `PASTA_DA_BATERIA_ANTERIOR` e
`PASTA_DO_PIPELINE` tiveram o número de `.parent` reduzido em 1 para apontar para os mesmos diretórios
absolutos (`analises/2026-09-23_bateria_noturna` e `modelagem_aedes/`). Só caminho.

---

## WIS médio, por modelo/horizonte, recorte 2024-2025 (n=96-97)

| Modelo | h | WIS restaurada | WIS contaminada (25/09) | Δ% | Cobertura 50% | Cobertura 90% |
|---|---|---|---|---|---|---|
| Cenário adotado | 1 | **101,9** | 104,8 | **−2,7%** ⚠️ | 41,2% | 77,3% |
| Cenário adotado | 4 | 215,4 | 216,5 | −0,5% | 25,8% | 69,1% |
| Cenário adotado | 8 | 288,6 | 289,7 | −0,4% | 24,7% | 54,6% |
| Cenário adotado | 12 | 300,7 | 300,6 | +0,0% | 19,6% | 51,5% |
| HistGB folha 20 | 1 | 121,3 | 120,8 | +0,4% | 34,0% | 84,5% |
| HistGB folha 20 | 4 | 199,0 | 198,5 | +0,2% | 32,0% | 68,0% |
| HistGB folha 20 | 8 | 259,0 | 258,7 | +0,1% | 19,6% | 57,7% |
| HistGB folha 20 | 12 | 278,6 | 278,5 | +0,0% | 26,8% | 56,7% |
| Régua climatológica | 1–12 | 292,7 / 313,5 / 322,2 / 324,2 | idênticos | 0,0% | 17,7–17,8% | 35,4–39,6% |

Comparação feita linha a linha contra `analises/2026-09-25_segunda_bateria_noturna/B_quantis_e_wis/saidas/wis_e_cobertura.csv`
(mesmo n em cada célula, 97 ou 96). A régua bateu **exatamente idêntica** nas 4 casas decimais — esperado,
pois ela só usa anos anteriores e não depende de feature de modelo.

### 🔴 Divergência acima de 1%: h=1, cenário adotado (2024-2025)

**−2,75%** (101,89 contra 104,77), a única célula fora do limite de 1% declarado na tarefa. Todas as
outras 7 células de modelo ficam ≤0,53%. Causa mais provável, já registrada como dívida técnica do
projeto: `selecionar_clima_por_ganho` escolhe as 6 colunas de clima usando os **60% mais antigos** da
série; a tabela restaurada tem menos linhas totais que a contaminada, o que desloca o corte de 60% e pode
trocar quais colunas entram. Não investiguei a fundo qual coluna mudou (custo/benefício, dado que a trava
bateu e o efeito é isolado a uma célula) — **reportando para o orquestrador decidir se vale aprofundar**
antes de citar o número de h=1 do cenário adotado.

---

## WIS modelo × régua climatológica, Wilcoxon pareado, Holm por recorte (família de 4 por recorte)

| Recorte | Modelo | h | WIS modelo | WIS régua | p Holm | Significativo |
|---|---|---|---|---|---|---|
| 2024-2025 | Cenário adotado | 4 | 217,6 | 313,5 | 0,000035 | **Sim** |
| 2024-2025 | Cenário adotado | 12 | 303,8 | 324,2 | 0,0956 | Não |
| 2024-2025 | HistGB folha 20 | 4 | 201,0 | 313,5 | 0,000002 | **Sim** |
| 2024-2025 | HistGB folha 20 | 12 | 281,5 | 324,2 | 0,0020 | **Sim** |
| 2026 (n=5, poder baixíssimo) | Cenário adotado | 4 e 12 | — | — | 0,25 | Não |
| 2026 (n=5) | HistGB folha 20 | 4 e 12 | — | — | 0,25 | Não |
| tudo | Cenário adotado | 4 | 207,0 | 298,1 | 0,000091 | **Sim** |
| tudo | Cenário adotado | 12 | 289,1 | 308,2 | 0,217 | Não |
| tudo | HistGB folha 20 | 4 | 191,3 | 298,1 | 0,000007 | **Sim** |
| tudo | HistGB folha 20 | 12 | 267,9 | 308,2 | 0,0086 | **Sim** |

**Conclusão qualitativa idêntica à rodada contaminada:** em 2024-2025 e em "tudo", pelo WIS, os dois
modelos vencem a régua climatológica em 1 mês (h=4), com folga; em 3 meses (h=12) só o HistGB folha 20
vence de forma confiável, o cenário adotado não. O recorte 2026 caiu de n=16 para **n=5** (menos semanas
confirmadas na tabela restaurada) e continua sem poder estatístico — nenhum teste significativo, como
antes.

---

## Cobertura dos intervalos — segue mal calibrada

Cenário adotado, h=12, 2024-2025: cobertura 50% = **19,6%** (nominal 50%), cobertura 90% = **51,5%**
(nominal 90%). Pior que a régua não é o caso aqui — a régua tem cobertura ainda mais baixa (17,7%/37,5%)
no mesmo recorte, mas por razão distinta (2024-2025 foi atípico frente à climatologia de anos calmos).
Achado já registrado no projeto (`PENDENCIAS.md`); os números da tabela restaurada confirmam a mesma
ordem de grandeza da rodada contaminada, sem melhora.

77,0% das origens (1.784 de 2.318) precisaram de rearranjo isotônico por cruzamento de quantis —
consistente com os 76,7% da rodada contaminada.

---

## Arquivos

- [`saidas/wis_e_cobertura.csv`](saidas/wis_e_cobertura.csv) — WIS médio e cobertura por modelo/h/recorte.
- [`saidas/familia_b.csv`](saidas/familia_b.csv) — Wilcoxon pareado + Holm, modelo × régua.
- [`saidas/previsoes_quantis.csv`](saidas/previsoes_quantis.csv) — previsões dos 7 quantis, já reordenadas.
- [`saidas/figura_intervalos_2026.png`](saidas/figura_intervalos_2026.png) — intervalos em 2026 (n baixo, ver acima).
- [`execucao.log`](execucao.log) — log da rodada validada (a primeira tentativa, com o anchor antigo, não
  foi mantida; só o log final está aqui).
