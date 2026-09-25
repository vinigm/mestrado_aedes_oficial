# Verificação adversarial — 4_vetor_como_preditor.md

> Método: WebFetch/WebSearch direto nas fontes (PMC, PLOS, Lancet, ScienceDirect), 25/09/2026.
> Sem download de arquivo. Rótulo por item: CONFIRMADO / PARCIAL / REFUTADO / NÃO VERIFICÁVEL.

---

## [0] da Silva et al. 2026, PLOS NTD — τ Kendall + R²/MAE vetor × clima

**Veredito: PARCIAL**

- Referência existe: PLOS NTD, DOI `10.1371/journal.pntd.0014201`, confirmada via PMC13537681.
  Estudo é mesmo POA/MosquiTRAP/SINAN 2018-2025.
- τ de Kendall **confirmado exato**: lag 0 = 0,2737 · lag 4 = 0,4953 · lag 8 = 0,5944 (Ae. aegypti).
- R²=0,46 do modelo com vetor **confirmado**, comparado a R²=−0,07 do modelo só-clima (Index P) —
  ambos prevendo o MESMO alvo (incidência de dengue log-transformada). Direção do achado está certa.
- 🔴 **MAE errado.** O texto da fonte diz literalmente: *"the dengue incidence model obtained an MAE
  of 0.79, a R² of 0.46"*. **MAE=0,19 pertence a outro modelo** — o que prevê a MFAI (infestação do
  vetor em si), não dengue. O pesquisador (e o próprio relatório-fonte, seção 1) colou o R² de um
  modelo com o MAE de outro modelo, ambos coincidentemente rotulados "vetor" mas com alvo diferente.
  **Corrigir para MAE=0,79** onde o achado for citado.

---

## [1] Ferreira, Freitas, Lowe et al. 2025, Lancet RHA — POA 2001→2010, 9 anos

**Veredito: CONFIRMADO**

- Referência existe: Lancet Regional Health – Americas, DOI `10.1016/j.lana.2025.101153` (PMC12226368).
- Autores batem (Ferreira DAC, Freitas LP, Lowe R, Souza GD, Fujiwara RT, Lana RM).
- Texto original: *"the Ae. aegypti mosquito was first detected in Porto Alegre in 2001"* e *"first
  autochthonous dengue cases were reported in May 2010"* — 2010−2001 = 9 anos, bate exato.
- Clusters de infestação em INVERNO também confirmados (2015 e 2018, bairro Vila Ipiranga).

---

## [2] Sedda et al. 2020, Acta Tropica — WAIC IGR × abundância × nulo

**Veredito: CONFIRMADO**

- DOI `10.1016/j.actatropica.2020.105519` (PMC7315132), Caratinga-MG confirmado.
- WAIC exatos batem com a Tabela 3 do artigo: **IGR=503,88 · abundância=505,34 · nulo=504,43**.
- Conclusão do próprio artigo é a mesma do achado: taxa de crescimento supera abundância bruta.

---

## [3] Chang et al. 2015 (Taiwan) + Aryaprema & Xue 2019 (Sri Lanka) — índices como alarme

**Veredito: CONFIRMADO** (com uma ressalva de precisão)

- Chang et al. 2015, PLOS NTD, DOI `10.1371/journal.pntd.0004043`: acurácias combinadas com
  meteorologia batem exatas — AI 83,8% · BI 87,8% · CI 88,3% · HI 88,4%. Lag de 2 semanas (AI) e
  1 mês (BI/CI/HI) confirmado.
- Aryaprema & Xue 2019, Acta Tropica 199:105155, DOI `10.1016/j.actatropica.2019.105155`: AUC>0,8
  confirmado; sensibilidade/especificidade batem para lag de 1 mês (>76%/>81%) e 2 meses (>71%/>56%).
- ⚠️ Ressalva: a especificidade de 70% citada no achado só vale para o lag de 1 mês — no lag de
  2 meses cai a 56%. O achado generaliza ">70%" sem separar por lag; não é erro grave, mas imprecisão.

---

## [4] Ribeiro et al. 2021, Cadernos de Saúde Pública — IIP × incidência, RJ

**Veredito: CONFIRMADO**

- DOI `10.1590/0102-311X00263320`. Autores batem (Ribeiro, Ferreira, Azevedo, dos Santos, Medronho).
- rs por ano batem exatos: 2011/12=0,479 (p<0,01, único significativo) · 2010/11=0,135 · 2012/13=−0,003
  · 2014/15=−0,060 · 2015/16=−0,035. 1 de 5 significativo, confirmado.
- ROC: sensibilidade 66,7% · especificidade 52,7% · acurácia 74%, limiar IIP=0,65% — todos exatos.

---

## [5] Sánchez et al. 2010, Trop Med Int Health — Breteau≥4 em Havana

**Veredito: CONFIRMADO**

- DOI `10.1111/j.1365-3156.2009.02437.x`. Local/ano batem (Havana, surto 2001).
- Sensibilidade 81,8% e especificidade 73,3% confirmados exatos, para quarteirão com BI≥4 no primeiro
  mês do surto. Escala de quarteirão (não cidade) corretamente sinalizada no achado.

---

## [6] Hamedin, Musa & Sulong 2026, Trop Med Health — LI × OI, Malásia

**Veredito: CONFIRMADO**

- DOI `10.1186/s41182-026-00974-y` (PMC13274206). 11 distritos-sentinela, Malásia peninsular.
- AUC exatos: LI=0,675 · OI=0,649 · combinado=0,667 — sem ganho ao combinar, confirmado.

---

## [7] Ong et al. 2023, Scientific Reports — Boruta remove container index, +6% AUC/F1

**Veredito: CONFIRMADO**

- DOI `10.1038/s41598-023-46342-2` (PMC10625978). Autores/ano/veículo batem.
- Texto original: *"CI was listed as the less important variable"* e *"removing this variable, the ML
  models improved their performance by at least 6% in AUC and F1 score"* — confirma exatamente
  "pelo menos 6%".

---

## [8] Córdoba 2009-2017 (Heliyon) — infestação sobe, dengue autóctone sem associação

**Veredito: CONFIRMADO**

- DOI `10.1016/j.heliyon.2020.e04858`. Infestação domiciliar 5,7%→15,4% confirmado exato.
- Confirmado: *"autochthonous dengue was not positively associated with vector or climate variables"*
  e pico autóctone (abril) seguindo pico de casos importados (março).

---

## [9] Estallo et al. 2024, Lancet RHA — Argentina 583.297 casos, Córdoba 127.483

**Veredito: CONFIRMADO**

- DOI `10.1016/j.lana.2024.100946` (PMC11613183). Autores batem (Estallo, López, Ludueña-Almeida,
  Madelón, Layún, Robert).
- Texto original: *"583,297 dengue cases were reported across the country... 4.18 times larger than
  in 2022-2023"* e *"127,483 in Córdoba"* — ambos exatos.
- O `url` do achado (PMID 32954035) é de OUTRO artigo (Heliyon 2020, item [8]) — mas o próprio achado
  já rotula isso como "contexto relacionado" e dá o DOI correto do estudo de 2024 à parte. Não é erro,
  é rótulo ambíguo mas explicitado.

---

## Achado geral sobre o relatório-fonte

- 9 de 10 achados batem exatos com a fonte primária.
- **1 erro real de mistura de números** (achado 0): MAE=0,19 é de um modelo diferente (previsão da
  MFAI/vetor), não do modelo de incidência de dengue citado (que tem MAE=0,79). R² e direção do
  achado permanecem corretos.
- Nenhum achado tratou inferência como fato sem rotular — o próprio relatório já separa "fato" de
  "inferência (minha, a confirmar)" na seção de lacunas.
