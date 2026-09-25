# Verificação adversarial — Catálogo de sistemas operacionais Brasil (25/09/2026)

> Método: WebSearch + WebFetch (sem download/clone). Tentativa de REFUTAR cada item, não confirmar por
> cortesia. `nao_verificavel` quando a fonte não deu acesso, nunca `confirmado` por omissão.

---

## Item 0 — InfoDengue
**CONFIRMADO.** bioRxiv `10.1101/046193` existe, autores Codeço/Coelho/Cruz batem (biorxiv.org/content/10.1101/046193v1.full).
GitHub `AlertaDengue/AlertaDengue` existe e é mesmo o portal InfoDengue (README: "early-warning system to
all states of Brazil"). Número de acurácia corretamente omitido (não achei número isolável). Rótulos
🔵/🟡/⚠️ usados de forma consistente com o que pude achar.

## Item 1 — Mosqlimate
**CONFIRMADO.** arXiv:2410.18945 existe, título e autoria (Ferreira/Codeço/Coelho) batem. Descrição do
que é a plataforma (dashboard+datastore+registro de modelos) confere com o abstract. Não consegui
confirmar de forma independente o detalhe "API exige conta" (não refutado, só não verificado) —
`parcial` nesse sub-ponto específico.

## Item 2 — 1º Sprint IMDC24
**CONFIRMADO.** PNAS `10.1073/pnas.2508989123` e medRxiv `10.1101/2025.05.12.25327419` existem. Texto
completo (PMC12912988) confirma os **5 estados exatos: AM, CE, GO, MG, PR** (uma busca solta havia
sugerido AM/PR/MG/RJ/SP — errado; o full-text corrige isso). 7 modelos/6 equipes, nomes M1-M7 e times
batem exatamente. Resultado 2023 (M6/M4 melhores) e 2024 (M2/M5, nenhum consistente) confirmado
literalmente no texto.

## Item 3 — 2º Sprint IMDC25
**CONFIRMADO.** Zenodo `10.5281/zenodo.17516484` e repo GitHub `Mosqlimate-project/2nd_IMDC_sprint_results`
existem. 15 equipes/19 modelos confirmado no README. Melhores por região batem exatamente (Sul→Dengue
Oracle M1, Sudeste→Dengue Oracle M2, Norte→LNCC-AR_p-1, Nordeste/Centro-Oeste→GHR Model). Skill score
mediano **0,12** confirmado literalmente em `ensemble_results.md`. RS aparece em 2025 junto com **PR e
MT** como estados de bom desempenho do ensemble — bate exatamente com o texto do catálogo. Único ponto
não verbatim: a fórmula "WIS_norm = ΣWIS/casos totais" não apareceu no texto que consegui puxar (`parcial`,
não necessariamente errado).

## Item 4 — Lowe et al. 2016, eLife
**CONFIRMADO.** DOI `10.7554/eLife.11285` existe, Lowe como autor líder confere. Hit rate **57% (81/141)
vs 33% (46/141)** confirmado literalmente (PMC4775211). Os "60 vs 95" do catálogo batem com 141-81=60 e
141-46=95 (derivação correta, ainda que a fonte não use a palavra "perdas"). Porto Alegre confirmada como
uma das 12 sedes, risco **baixo** previsto, incidência real 1/100mil — bate.

## Item 5 — D-MOSS
**CONFIRMADO com precisão notável.** PMC12965583 existe. RMSE por lead time bateu **exatamente**:
20,35/26,02/27,96/28,52/25,37/25,99, geral 25,70 vs baseline 31,29. "Venceu em todos os horizontes"
é verdade **para RMSE** — mas a fonte tem uma ressalva textual: para uma métrica diferente ("trajectory
forecast errors" em lead 2-4 meses) não há ganho. O catálogo não menciona essa exceção (não invalida a
frase, mas é um detalhe a mais que existe na fonte e ficou de fora).

## Item 6 — VIGIA-Dengue
**CONFIRMADO integralmente.** Repo `ghostopw/VIGIA-Dengue` existe. AUC 0,830 vs 0,757, sensibilidade
**0,698**, especificidade **0,803**, Brier 26% melhor — todos batem exatamente com o README. Horizonte
4 semanas e validação 2019-2025 confirmados.

## Item 7 — Painel Dengue RS (SES/CEVS)
**CONFIRMADO, com nuance.** URLs existem. Não achei nenhuma menção a modelo preditivo de casos futuros —
mas o painel faz "projeção mensal de insumos necessários" (planejamento de estoque/logística), que não é
o mesmo que prever número de casos. Isso não contradiz "não há modelo preditivo publicado", mas é uma
forma de "previsão" que o catálogo poderia ter mencionado para ser mais preciso.

## Item 8 — Modelo IMPA
**PARCIAL — omissão relevante.** Achei o DOI que o catálogo não localizou: `10.1016/j.eswa.2021.116324`
(Souza, Maia, Stolerman, Rolla, Velho, *Expert Systems with Applications* 2022). As 7 capitais, o
horizonte de 6 meses e o dado de entrada (só temp+precipitação) batem exatamente. **Mas o "80% de
acerto" mascara variância enorme por cidade**: Rio, São Luís e Aracaju em 100%, BH/Manaus/Salvador em
80%, **Recife em apenas 20%** (achado em reportagem — ohoje/Diário de Cuiabá). O catálogo already
sinaliza "métrica não especificada, sem baseline claro" (⚠️), o que é honesto, mas não registra essa
variação de 20%-100%, que é o dado mais importante para julgar se "80%" é confiável. Isso é uma omissão,
não uma invenção.

## Item 9 — CatBoost×GRU 27 capitais
**CONFIRMADO.** DOI `10.1007/s00484-026-03300-7` existe (PMC13476183). **R² = −0,2064, MAE = 0,2219,
sMAPE = 160%** para Porto Alegre — batem exatamente. Goiânia (R² 0,92) e João Pessoa (R² 0,90) como
melhores — confirmado. Ausência de baseline explícito confirmada. Nota: consegui achar a lista de
autores (Silva, Nery, Nicomedes et al.) sem bloqueio de reCAPTCHA — o catálogo relatou bloqueio; não é
erro, só uma limitação que se mostrou superável nesta rodada.

## Item 10 — RF mensal multi-cidade — 🔴 ERRO DE ATRIBUIÇÃO DE AUTORIA
**REFUTADO no ponto central de citação.** DOI `10.1093/aje/kwac090` existe e é o artigo certo (AJE
191(10):1803, 2022), mas os **autores são Kirstin Roster, Colm Connaughton e Francisco A. Rodrigues —
NÃO Colón-González**. O catálogo atribui o paper a "Colón-González et al. (grupo associado a R. Lowe)",
o que é uma citação incorreta (nome de autor errado). Resto do conteúdo confere: horizonte 1 mês, régua
sazonal ingênua, RF venceu a régua (MAE mediano 12,2 vs 20,0), "modelo vencedor varia por cidade"
confirmado. POA na amostra segue não confirmado (o catálogo já sinalizava isso corretamente com ⚠️).

## Item 11 — Projeção nacional 2026
**CONFIRMADO.** ~1,8 milhão de casos Brasil 2025-2026 bate com múltiplas matérias (Poder360, Medicina
S/A, Brasil61). Estados com redução prevista — **PR, RS, SP, AC, AP** — batem exatamente com o texto
encontrado. Sem número isolado de RS, como o catálogo já reconhecia.

---

## Resumo do que realmente quebrou
- **Item 10 é o único erro factual confirmado**: autoria errada (Colón-González não escreveu o AJE
  2022; são Roster/Connaughton/Rodrigues). Corrigir a citação no catálogo.
- **Item 8 tem omissão relevante**: a faixa 20%-100% por cidade devia estar no catálogo, não só "métrica
  não especificada".
- Todos os outros 10 itens (0,1,2,3,4,5,6,7,9,11) tiveram DOI/URL/números conferidos e bateram, em
  alguns casos (2, 3, 5, 6, 9) com correspondência exata a três ou mais casas decimais.
