# Catálogo de modelos prontos de previsão de dengue

> **Montado em 25/09/2026**, a pedido do Vinicius: *"na literatura o que temos de modelos prontos feitos e
> como estão os resultados dele?"*. Três pesquisadores independentes, um por ângulo, cada um com um
> verificador adversarial. Complementa a [varredura de literatura](../2026-09-25_varredura_literatura/) do
> mesmo dia, sem repetir o que já estava lá.

---

## Em uma frase

**Quem vence a régua em 3 meses faz isso com pouca margem, com mais dados ou com previsão climática do
futuro — e o único estudo multicapitais que incluiu Porto Alegre teve na cidade um dos piores resultados, já em 4 semanas.**

---

## 1. Método

| Ângulo | Arquivo | Verificação |
|---|---|---|
| 1. Sistemas e modelos no Brasil | [`1_sistemas_operacionais_brasil.md`](1_sistemas_operacionais_brasil.md) | [`verificacao_1_...`](verificacao_1_sistemas_operacionais_brasil.md) |
| 2. Sistemas operacionais no mundo | [`2_sistemas_operacionais_mundo.md`](2_sistemas_operacionais_mundo.md) | [`verificacao_2_...`](verificacao_2_sistemas_operacionais_mundo.md) |
| 3. Modelos com código aberto que rodam nos nossos dados | [`3_modelos_abertos_rodaveis.md`](3_modelos_abertos_rodaveis.md) | [`verificacao_3_...`](verificacao_3_modelos_abertos_rodaveis.md) |

- **34 itens verificados:** 26 confirmados · 7 parciais · **1 refutado**.
- Os parciais e o refutado são quase todos de **autoria atribuída errado**, nunca de fonte inventada:
  - o artigo do AJE 2022 sobre Random Forest mensal é de **Roster, Connaughton e Rodrigues**, não de
    Colón-González;
  - os artigos do EWARS são de **Hussain-Alkhateeb 2018** e **Cardenas 2022**, e o do D-MOSS é de
    **Campbell e Brady**. Nenhum dos três é de Lowe.
- ⚠️ **Comparabilidade:** MAE de outro estudo não se compara com o nosso, porque escala, cidade e horizonte
  mudam. O catálogo registra só o que é comparável: **venceu a régua dele? por quanto? em que horizonte?**

---

## 2. 🔴 Porto Alegre já foi testada, e o ML falhou nela

**Int. J. Biometeorology 2026**, DOI `10.1007/s00484-026-03300-7`: CatBoost e GRU em 27 capitais,
até 4 semanas.

- **FATO:** Porto Alegre ficou **entre os piores resultados das 27 capitais**: R² **−0,21**, sMAPE 160%, em até 4 semanas.
  ⚠️ Corrigido em 25/09/2026: a primeira versão dizia "o pior"; a fonte diz "entre os piores".
- **FATO:** as melhores capitais tiveram R² 0,87 a 0,92.
- **Comparação, com cautela:** o nosso cenário adotado tem R² **0,63** em 4 semanas. O desenho é diferente, e
  isso não é teste, mas é a única referência publicada na mesma cidade.
- **Por que importa:** é evidência externa de que Porto Alegre é difícil para ML genérico. O resultado do
  projeto em 1 mês deixa de parecer modesto quando comparado com isso.

---

## 3. Quem vence a régua em 3 meses

| Sistema | Onde | Horizonte | Régua | Vantagem | O que ele tem que nós não temos |
|---|---|---|---|---|---|
| **LASSO de Shi et al. 2016**, em produção | Singapura | **12 semanas** | SARIMA | MAPE **24% × 29%** | 10 anos de treino |
| **D-MOSS** | Vietnã, província | 1-6 meses | média sazonal expansiva | RMSE **−17,8%** | previsão climática **sazonal do futuro** |
| Superensemble, Colón-González 2021 | Vietnã | 1-3 meses | sazonal | CRPS 66,8 × 79,4 | ensemble de muitos modelos |
| Ensemble de 11 modelos, Wu 2025 | +180 locais | 1-3 meses | melhor modelo isolado | 62,7% × 64% em 3 meses | heterogeneidade de modelos |
| Lowe et al. 2016 | Brasil, 553 microrregiões | 3 meses | média histórica | acerto **57% × 33%** | alvo **categórico**, não número |

- **FATO:** o **LASSO de Singapura** é o único sistema do catálogo que vence uma régua **exatamente em 12
  semanas, numa cidade só**. Vence por 5 pontos percentuais de MAPE, e contra SARIMA, não contra a regra
  "mesma semana do ano passado".
- **FATO:** o D-MOSS usa **previsão climática sazonal**, o clima previsto para os próximos meses. É a única
  entrada que carrega informação sobre o futuro, e nenhum modelo do projeto a usou.

### Quem não venceu

- **Sprint InfoDengue-Mosqlimate 2024:** nenhum dos 7 modelos se destacou de forma consistente no ano
  atípico de 2024.
- **2º sprint, 2025:** o ensemble dos 5 melhores teve skill score mediano de apenas **0,12** sobre o melhor
  modelo isolado, e piorou em alguns estados.
- **Dengue Forecasting Project 2015:** um SARIMA simples venceu os modelos complexos na semana do pico.

---

## 4. O que existe no Brasil, e o que existe para Porto Alegre

- **InfoDengue:** faz **nowcasting**, a estimativa da semana corrente corrigida pelo atraso, e níveis de
  alerta. **Não prevê 3 meses.**
- **Mosqlimate:** plataforma nacional de registro e comparação de modelos, com sprints anuais. O RS entrou
  no sprint de 2025, mas só em nível **estadual**. Não há série municipal de Porto Alegre para comparar.
- **Réguas oficiais dos sprints:** persistência, sazonal e **climatológica por quantis**. No 3º sprint, a
  régua é o modelo INLA de bandas epidêmicas de Freitas et al. 2025, contra o qual 31 equipes foram medidas.
- **RS:** o Painel Dengue da SES/CEVS é **descritivo**. **Não existe modelo preditivo publicado para o RS.**

---

## 5. Código aberto que roda nos nossos dados

| Código | O que é | Esforço | Exige |
|---|---|---|---|
| `Mosqlimate-project/sprint-template` | as 3 réguas oficiais | baixo | Python ou R |
| `AlertaDengue/baseline_paper` | INLA de bandas epidêmicas, a régua do 3º sprint | baixo | **R + INLA**, só casos |
| pacote `dlnm` (Gasparrini) | defasagem distribuída não linear | médio | R |
| D-FENSE | SARIMAX, AR e um mecanístico climático | médio | R e MATLAB; licença CC-BY-NC-ND |
| `cdcepi/dengue-forecasting-project-2015` | dados e protocolo do projeto de 2015 | baixo | — |
| ESA-UNICEF | ensemble CatBoost + SVM + LSTM + RF | médio | desenhado para 19 anos de série |

---

## 6. Limitações

- Leitura por resumo e texto aberto. PNAS e parte do PMC bloquearam a leitura direta.
- Os números do DengAI vêm de repositórios de participantes, não de artigo revisado.
- O catálogo não é revisão sistemática.
