# Certificação adversarial — atualização dos dados de 2026 (25/09/2026)

**Veredito:** o CONSERTO do pipeline (`consolidar_sinan.py`) e a integridade dos dados **passam**.
O check de regressão do modelo (item 5 da tarefa) **reprova**, mas por um motivo que parece ser
**anterior a esta atualização**, não causado por ela — ver seção final.

## 1) Nenhuma célula mudou antes de 2026-01-01

Comparação célula a célula, própria (script `cert_dados_2026.py`), 725 datas comuns, `NaN=NaN`:
**0 divergências** antes de 2026-01-01. Única coluna que mudou: `casos_confirmados`, em 14 semanas
(11/01 a 12/07/2026). Confirma o relatado.

## 2) Recontagem independente do DENGBR26_atualizado_set26.csv.zip

Reimplementação própria (sem importar `consolidar_sinan`), filtro POA (`ID_MUNICIP=431490`) +
confirmado (`CLASSI_FIN∈{10,11,12}`), agrupado por `SEM_PRI` (mesmo campo que
`dominio/montagem_tabela.py:207` usa como `SE`): **19 casos em 2026**, semana a semana **idêntico**
à coluna `casos_confirmados` da `tabela_final.csv` nova, nas 16 semanas com caso — **0 divergências**.
Nenhuma semana em dobro.

Bônus: recontei também o `DENGBR26.csv.zip` (antigo) isolado = **12** — bate com o "antes". Se a
lógica antiga concatenasse os dois arquivos sem seleção, o total seria **31**, não 19 — confirma
empiricamente o risco que o conserto elimina.

## 3) Teste novo falha na lógica antiga, passa na corrigida

`pytest tests -q` → **24 passed**. Reproduzi a lógica antiga por monkeypatch (glob sem seleção): dá
**5** casos no cenário sintético (esperado pelo teste novo: **3**) — o teste novo falharia contra ela,
confirmado por execução direta, não só por leitura do código.

## 4) Nenhum DENGBR apagado ou movido

Os 10 arquivos `DENGBR*.csv.zip` (2018-2025 + as duas versões de 2026) seguem em
`bases_governo/`. `git status` mostra só os 3 arquivos esperados modificados
(`consolidar_sinan.py`, `casos_confirmados_poa.csv`, `tabela_final.csv`) + arquivos novos
(teste, pasta de análise). `.gitignore` linha 55 intacta.

## 5) ⚠️ REPROVADO — braço "referência" do harness não reproduz o painel publicado

Rodei `harness.py` (bloco 2026-09-23, brincadeira `referencia`) contra a `tabela_final.csv` **já
atualizada**:

| h | MAE medido | MAE painel | R² medido | R² painel | veredito |
|---|---|---|---|---|---|
| 1 | 91,6 | 98,0 | 0,900 | 0,898 | diverge (-6,5%) |
| 4 | 221,7 | 219,7 | 0,627 | 0,628 | diverge (+0,9%) |
| 8 | 298,1 | 272,6 | 0,368 | 0,450 | **diverge (+9,4%)** |
| 12 | 320,2 | 278,7 | 0,319 | 0,437 | **diverge (+14,9%)** |

**Isto NÃO parece ser efeito da atualização do SINAN.** Motivos:

- A janela de avaliação alcançada (`data_alvo` máximo = 2026-04-19, igual nos 4 horizontes) é
  limitada por disponibilidade de **clima**, não de casos — e não muda com este update.
- Das 14 semanas que mudaram, só 3 caem dentro dessa janela (11/01, 05/04, 19/04/2026) — poucas
  células, com deltas pequenos (ex. 1→0), não deveriam mover o MAE agregado em 9-15%.
- **Achado separado, mais provável:** `LGBM_REGRESSAO` (usado só para escolher as 6 colunas de
  clima, `config/experimentos/cidade_regressao.py:27-38`) **não tem `random_state`** — é
  não-determinístico entre execuções, mesmo com dado idêntico. Isso já está registrado como dívida
  técnica no `PENDENCIAS.md` ("ranking instável: recortando em 2023, 4 das 6 mudam"). Não confirmei
  isso rodando duas vezes (custaria +28 min cada rodada) — é hipótese forte, não certeza.

**Reportando o desvio, não decidindo em silêncio:** não dá para afirmar que o painel publicado
continua válido, nem que a atualização o invalidou. Recomendo ao Vinicius: rodar a trava duas vezes
sobre o MESMO dado (já atualizado) para separar não-determinismo de efeito real; se variar entre
as duas rodadas, o painel publicado é não-reprodutível por motivo alheio a este update, e a
correção fica em fixar `random_state` no `LGBM_REGRESSAO`.

## Scripts usados

- `/private/tmp/claude-501/.../scratchpad/cert_dados_2026.py` — checks 1 e 2.
- `/private/tmp/claude-501/.../scratchpad/cert_extra_old_logic.py` — bônus do check 2.
- `/private/tmp/claude-501/.../scratchpad/cert_check5_harness.py` — check 5.

Nada além da leitura foi alterado neste projeto.

---

## Adendo do orquestrador, 25/09/2026, 23h50 — a reprovação do check 5 foi explicada

- **Causa:** o check comparou conjuntos de semanas diferentes. Com a série estendida até jul/2026, o corte de
  maturidade de 12 semanas passa a deixar **fev a abr/2026** na avaliação. A última semana válida foi de
  01/02/2026 para 19/04/2026: 11 semanas a mais, quase sem casos, em que o modelo previa temporada.
- **Medido nas mesmas semanas de antes**, até 01/02/2026, com a tabela nova, braço `referencia`:

  | h | Publicado | Tabela nova até fev/2026 | Com fev-abr/2026 |
  |---|---|---|---|
  | 1 | 98,0 · R² 0,898 | **97,4** · R² 0,897 | 91,6 |
  | 12 | 278,7 · R² 0,437 | **280,0** · R² 0,429 | 320,2 |

- **A diferença residual, até 0,5%, tem duas causas legítimas:**
  - os confirmados de jan/2026 foram revisados pelo DENGBR26 de setembro;
  - a seleção de clima escolheu **as mesmas 6 colunas**, mas em outra ordem, porque os 60% de treino da seleção
    ficaram maiores.
- **Veredito do orquestrador:** a atualização vale. 2018-2025 intactos, 2026 recontado sem duplicação, painel
  reproduzido a 0,5% nas mesmas semanas. As rodadas seguintes usam âncoras recalculadas na tabela nova, por
  emenda datada.
