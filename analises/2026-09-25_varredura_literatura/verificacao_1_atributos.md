# Verificação adversarial — 1_atributos.md

> Método: WebSearch + WebFetch em 25/09/2026, direto na fonte (PLOS, PNAS Nexus, Springer, PubMed/PMC).
> Nenhum arquivo baixado ao disco. Índice = posição na lista original (começa em 0).

---

## 0 — Mordecai et al. 2017, PLOS NTD — R0 térmico 29,1°C

✅ **CONFIRMADO.** Autores corretos (Mordecai, Cohen, Evans et al.), 29,1°C (IC 28,4–29,8°C) bate
exato. **86-91% de acurácia** confirmado no próprio texto (out-of-sample, transmissão autóctone,
Américas 2014-2016). Confirmado que é **validação retrospectiva/contemporânea**, não previsão
prospectiva — o pesquisador rotulou isso corretamente. Não consegui confirmar de forma independente
o sub-número "85-86% na magnitude" (fonte secundária só citou o de 86-91%), mas não achei nada que o
contradiga.

## 1 — Ma, Xu, Han et al. 2025, PNAS Nexus — IOD vs ENSO, "horizonte de 6 meses"

⚠️ **PARCIAL.** R² **confirmados exatos**: 0,56 (c/ IOD) vs 0,44 (s/ IOD) vs 0,33 (GAM). Poder
explicativo IOD 33,76% vs ENSO 30,40% também bate.
- 🔴 **"Horizonte de 6 meses" não se sustenta.** Três buscas independentes (PubMed, PNAS Nexus,
  ScienceDaily) mostram: (a) o desenho é histórico 2013-2021 + **projeção 2022-2028** (multi-anual,
  não um horizonte fixo de 6 meses); (b) a correlação IOD-dengue reportada é em **lag de 0 meses**
  (efeito quase imediato), não 6 meses. O pesquisador tratou uma inferência não encontrada na fonte
  como fato — não achei a frase "6 meses" em nenhum resumo/abstract acessado.
- Aplicabilidade a POA (baixa, dengue importada/mobilidade) segue válida como julgamento qualitativo.

## 2 — Xiao, Soares, Bastos, Izbicki & Moraga 2025, PLOS NTD — Google Trends nowcasting Brasil

✅ **CONFIRMADO exato.** Autores batem. GT venceu em **12/26** (RMSE), **17/26** (RMSPE), **18/26**
(logscore) — os três números batem dígito a dígito com o resumo obtido direto do PLOS. Objetivo
(nowcasting, preencher atraso de notificação <50% na 1ª semana) também confirmado.

## 3 — Estudo Vietnã 2026 (PMID 42636653) — Google Trends piorou AR

✅ **CONFIRMADO exato.** Título "Evaluating the incremental value of Google Trends for provincial
dengue surveillance in Vietnam" confirmado via PubMed. RMSE **110,58 vs 92,25** e MAE **72,52 vs
63,70** batem exatos com o texto do resumo indexado. Contexto de atraso simulado (1 semana ajuda,
2 semanas misto) também bate.

## 4 — Chen & Moraga 2025, BMC Public Health — LSTM+SHAP, efeito espacial

✅ **CONFIRMADO exato.** MAE em Minas Gerais **7.730,47 → 5.088,71** (LSTM-clima-espacial vs
LSTM-clima) bate exato, no horizonte de 1 mês. Redução de ~34% confirmada.

## 5 — Fuad, Milki & Al Aziz 2026, PLOS ONE — sorotipo, tático vs estratégico

⚠️ **PARCIAL.** Confirmados: autores (Fuad MM, Milki MS, Aziz RA), RMSE Prophet 2-6m
**3.952,6–4.004,2**, SARIMAX 1 mês (h=1) RMSE 3.716,9, precisão/recall do alarme SARIMAX
**0,886/0,824** (1-step).
- 🔴 **A comparação "Prophet 3.952,6-4.004,2 (2-6m) vs SARIMAX 6.501,1 no mesmo teste agregado" é
  questionável.** O valor 6.501,1 aparece rotulado como RMSE "overall" do SARIMAX — não confirmei que
  seja especificamente o agregado 2-6m (excluindo h=1, onde o SARIMAX é o melhor modelo, RMSE 3.716,9,
  MELHOR que o Prophet). Se 6.501,1 incluir todos os horizontes 1-6, a comparação mistura duas bases
  diferentes e infla a vantagem do Prophet. Não consegui acessar a tabela completa para resolver.

## 6 — Oliveira, Santos, Bruhn, Bohm & Santana 2025, ERAMIA-RS — Porto Alegre

✅ **CONFIRMADO.** Autores batem (UFPel, 2025). Acurácia balanceada XGBoost **0,67** confirmada.
Atributos mais importantes = médias 10-15 dias de ponto de orvalho e umidade, confirmado. Alvo =
classificação de **aceleração** de casos (não série contínua), confirmado — o pesquisador rotulou
essa diferença corretamente.

## 7 — da Cunha e Silva et al. 2026, Int J Biometeorology — CatBoost vs GRU

✅ **CONFIRMADO exato.** R² das melhores capitais: Goiânia 0,9199, João Pessoa 0,9024, Fortaleza
0,8728, Belo Horizonte 0,8733 — faixa 0,87-0,92 bate. Horizonte confirmado como **só até 4 semanas
(H1-H4)**, sem cobertura de 8-12 semanas — a ressalva do pesquisador está correta.

## 8 — Polrob & La-up 2025, BMC Public Health — DLNM Bangkok

✅ **CONFIRMADO exato.** RR **1,037** (IC 95% 1,028–1,046) para temp. mínima em lag 5 meses, e RR
**1,046** (IC 95% 1,029–1,063) para chuva em lag 0 — batem literalmente com o texto do artigo. Estudo
é **puramente correlacional**, os próprios autores afirmam isso ("inherently correlational, does not
imply causality"), sem MAE/RMSE — confirmado.

## 9 — Rypdal & Sugihara 2019, Nature Communications — estabilidade inter-epidêmica

✅ **CONFIRMADO como conceito, e a omissão do número foi a decisão certa.** O achado central (período
entre-surtos estável → surto seguinte menor; instável → surto maior) bate. O único número de horizonte
encontrado nas buscas é qualitativo ("previsões até 3-4 meses antes do surto", caso San Juan) — nenhuma
fonte acessada trouxe R²/correlação explícito, então o pesquisador agiu corretamente ao **omitir o
número** em vez de estimar.

---

## Resumo

| Índice | Veredicto |
|---|---|
| 0 (Mordecai) | ✅ Confirmado |
| 1 (Ma/IOD) | ⚠️ Parcial — R² certos, "horizonte 6 meses" não encontrado na fonte |
| 2 (Xiao/GT Brasil) | ✅ Confirmado |
| 3 (Vietnã GT) | ✅ Confirmado |
| 4 (Chen & Moraga) | ✅ Confirmado |
| 5 (Fuad serotipo) | ⚠️ Parcial — comparação de RMSE pode misturar bases diferentes |
| 6 (Oliveira POA) | ✅ Confirmado |
| 7 (da Cunha e Silva) | ✅ Confirmado |
| 8 (Polrob DLNM) | ✅ Confirmado |
| 9 (Rypdal & Sugihara) | ✅ Confirmado (conceito; número corretamente omitido) |

**8 de 10 achados batem exatos na fonte.** 2 são parciais — 1 tem uma alegação (horizonte de 6 meses
do IOD) sem lastro na fonte, tratada como fato sem ser; o outro mistura duas bases de RMSE possivelmente
diferentes. Nenhum achado teve referência inexistente ou número fabricado do zero.
