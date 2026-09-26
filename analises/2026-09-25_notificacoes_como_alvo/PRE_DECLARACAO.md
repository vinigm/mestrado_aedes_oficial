# Pré-declaração — notificações como alvo

> **Escrita em 25/09/2026, antes de montar a tabela ou rodar qualquer braço.** Autorizada pelo Vinicius em
> 25/09/2026. Mudança posterior vira **emenda datada** no fim.
>
> ⚠️ **Exploratória.** 2024-2025 já foram vistos. 2026 é o primeiro ano **atípico** avaliado.

---

## 1. Pergunta

**Com as notificações, o modelo acompanha a queda real de 2026? E as notificações ajudam a prever os
confirmados?**

- **O que o dado mostra:**
  - vetor de out/2025 a mar/2026 igual ao de 2024-2025, média 0,71;
  - CEVS 2026, até a semana 37: **4.085 notificações**, **11 confirmados**, **3.832 inconclusivos**;
  - CEVS 2025: 57.167 notificações e 22.504 confirmados.
- **A avaliação atual para em fev/2026.** A temporada de 2026 nunca foi avaliada.

---

## 2. Dados

- **Fonte única dos dois alvos:** a série semanal do CEVS para Porto Alegre,
  `analises/2026-09-25_novas_fontes_oficiais/dados/cevs_poa_dengue_semanal_por_medida.csv`, baixada em
  25/09/2026. Medidas `Notificações` e `Confirmados`.
- **Critério:** município de **residência**, o do CEVS. O pipeline usa notificação, cerca de 10% maior.
  Adaptação declarada.
- **Tabela da rodada:** `tabela_final.csv` com vetor e clima até 09/08/2026, e a coluna de casos trocada
  pela série do CEVS. A junção é por `(ano, semana)` epidemiológicos. Fica na pasta desta análise.
  - **O pipeline oficial não é tocado.** `preparar_dados.py` não roda, por causa do DENGBR26 duplicado.
- **Corte de maturidade:** o do pipeline, 12 semanas. A avaliação vai então até ~maio de 2026 e cobre o
  pico da temporada.

---

## 3. Braços

Todos com o **HistGB folha mínima 20** do bloco 7: 20 colunas, quantil 0,85. Horizontes **1, 4, 8 e 12**.

| Braço | Alvo | Entrada extra |
|---|---|---|
| `T0` | confirmados da tabela oficial | — trava |
| `C0` | confirmados do CEVS | — base dos confirmados |
| `N1` | **notificações** do CEVS | — |
| `C2a` | confirmados do CEVS | notificações da origem e lags 1 a 4 |
| `C2b` | confirmados do CEVS | taxa de confirmação das últimas 8 semanas |

- **Taxa de confirmação:** confirmados ÷ notificações nas 8 semanas até a origem. Com zero notificações,
  repete a última taxa válida, o que só usa o passado.
- Colunas extras entram como reservadas: o clima escolhido é o mesmo em todos os braços.
- **Régua de cada alvo:** a mesma semana do ano passado, na própria série.

---

## 4. Travas

1. **`T0` reproduz o `HistGB_folha20_M1` do bloco 7:** MAE 133,6 / 199,6 / 223,2 / 243,8 na avaliação até
   fev/2026. Prova que o caminho do código é o certo antes de trocar a fonte.
2. **Junção do CEVS:** os confirmados anuais batem com o painel: 2022 **5.142** · 2023 **6.318** · 2024
   **16.764** · 2025 **22.504** · 2026 **11**. As notificações: **7.263 · 9.759 · 31.101 · 57.167 · 4.085**.
   Semanas sem registro no CEVS entram como 0 e são contadas.
3. **Clima idêntico** em todos os braços.

---

## 5. Métricas e testes

- **Avaliação:** `data_alvo ≥ 2024-01-01`, até onde houver alvo, com três recortes: **2024-2025**,
  **2026** e **tudo**.
- **Por alvo:** MAE, skill score contra a régua do próprio alvo e, em 2026, a maior previsão contra o
  maior real.
- **Família K1 — as notificações ajudam os confirmados?** `C2a` e `C2b` contra `C0`, em h 1, 4, 8, 12, no
  recorte "tudo" = **8 comparações**. Wilcoxon pareado, Holm sobre 8.
- **Família K2 — o modelo bate a régua do próprio alvo?** `C0` e `N1` contra a régua de cada um, em h 4, 8,
  12, no recorte "tudo" = **6 comparações**, Holm sobre 6.
- **Leitura principal de 2026, descritiva:** o erro relativo ao total de cada braço em 2026. Pergunta: quem
  acompanha a queda?

---

## 6. Critérios

- **As notificações ajudam os confirmados** se `C2a` ou `C2b` tiver MAE menor que `C0` em h=12 com p Holm
  K1 < 0,05.
- **O modelo acompanha a transmissão** se, em 2026, o erro relativo de `N1` for menor que o de `C0` e
  menor que o da régua de notificações. Descritivo, porque 2026 é uma temporada só.

---

## 7. Ameaças

- **Uma temporada atípica só.** Nada sobre 2026 generaliza.
- **Notificação inclui casos que não são dengue.**
- **Os confirmados de 2026 podem ainda ser reclassificados:** há 33 em investigação e 3.832 inconclusivos.

---

## Emendas

Nenhuma até agora.
