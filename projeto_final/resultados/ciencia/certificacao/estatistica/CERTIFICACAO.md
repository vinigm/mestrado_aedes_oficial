# Certificação adversarial — estatística (E3 composto, famílias F1 a F4)

> 12/10/2026. Reimplementação independente, do zero (`reimpl.py`: só numpy, pandas, scipy; nada de `aedes/`; a régua foi
> refeita a partir de `dados/tabela_final.csv` com o corte de maturidade de 12 semanas). Rodado com `python3 -B`,
> `OMP_NUM_THREADS=1`. Nenhum arquivo certificado foi alterado. Escopo: verificações 1 a 5; **E5 (alarme) não foi reimplementada**.

## Veredito: APROVADO COM RESSALVAS (nenhuma reprovação)

Todo número determinístico do executor foi reproduzido com diferença ≤ 6e-14. As ressalvas são de método e de formato, não de cálculo.

## 1. Composto (N = 8, 13, 26)

- **9.660 linhas** (3.312 / 3.252 / 3.096) idênticas em `N, h, data_alvo, data_origem, folha_escolhida, real`; 0 linhas só de um lado.
- `previsto`: diferença máx. **2,3e-13** (relativa ≤ 9e-14), em 1.817 linhas. Causa: o `previsoes.csv` do executor foi gravado com
  16 dígitos significativos, sem ida-e-volta exata. Abaixo da tolerância de 1e-9; não afeta nenhuma escolha de folha.
- `resumo.csv` (36 linhas): `n` igual (102 em todas as janelas), MAE diff 5,7e-14, fração da folha 20 diff 0.
- **Sem vazamento:** no meu código, a maior `data_alvo` usada em qualquer escolha é ≤ `data_origem` em **0 violações**.
  Como o executor reproduz a minha escolha em 100% das linhas, a dele também respeita a regra.
  Teste de mutação: deixando entrar pares até t+1 ou t+4 semanas, **118 e 282 de 1.086** escolhas (N=13, h=1/4/8/12) mudam, então o teste enxerga vazamento.
- Empates exatos de MAE entre folhas: **0** em 9.894 decisões (a regra "empate → folha 5" nunca é acionada).
- Em N = 13 o `previsto` é sempre a previsão da folha escolhida (0 divergências).

## 2. As 52 comparações (F1 12, F2 12, F3 12, F4 16)

Comparadas linha a linha com `estatistica/familias.csv`:

| Campo | diff máx. |
|---|---|
| `n` | 0 |
| `mae_A`, `mae_B`, `delta` | 5,7e-14 |
| `ganho_pct` | 2,8e-14 |
| `dm_hln` | 1,6e-15 |
| `p_bruto` | 1,2e-15 |
| `p_holm` | 6,7e-16 |
| `limiar_piso` | 0 |
| `variancia_fallback` | 0 divergências (nenhum fallback) |
| **veredito** | **0 divergências** (47 "sem evidência", 5 "A melhor", 0 "A pior") |

- Régua: o `real` refeito da tabela cortada é idêntico ao `real` da E2 em todas as semanas da grade (asserção no código).
- Checagens cruzadas (`v5`): em h = 1 o DM-HLN é algebricamente o teste t de uma amostra (|dif| de p = 4e-16); em h = 4, 8, 12 o DM por
  outro caminho (autocovariâncias via `np.correlate`) bate em 4e-16. Holm: meu exemplo manual confere; `statsmodels` não está instalado.

## 3. Bootstrap

- Com o esquema especificado (blocos de 8, início uniforme em 0..n-8, `ceil(n/8)` blocos truncados em n, 2.000 reamostragens,
  `default_rng(42)` novo por comparação, percentis 2,5 e 97,5): **IC idêntico ao do executor, diff ≤ 2,5e-14, nos 52 testes.**
- Ordem dos sorteios: as 3 formas (matriz `size=(B,nb)`, um `size=nb` por reamostra, escalar por bloco) dão as **mesmas** sequências.
  Não há ambiguidade de implementação aqui.
- **Variação de Monte Carlo** (sementes 42, 1, 7, 123; `variacao_monte_carlo_ic.csv`): amplitude entre sementes do limite inferior do IC
  mediana 1,14 pp, máx. 7,15 pp (F2 so_casos × so_calendario h=4); do superior, mediana 0,73 pp, máx. 2,51 pp. p, delta e vereditos não
  dependem da semente (idênticos nas 4).
- O único teste cujo "IC exclui zero" muda com a semente: **F4 composto × completo@f5, h=12** (IC [0,03; 11,99] com 42; inclui zero com 1, 7 e 123).
  O veredito não muda (Holm). Quem for escrever "IC exclui zero" para esse par deve saber que é fronteira.

## 4. Especificação × pré-declaração

- Contagens 12 / 12 / 12 / 16 e a Emenda 1 (F4 = 12 + composto × folha 5): conferem.
- Direção: F1/F3 `completo` × `sem_X` com Δ = MAE(sem_X) − MAE(completo) (Eq. 4); F2 `so_X` × `so_calendario`; F4 candidato × régua e composto × folha 5.
- Piso: folha 5 → piso da 5; folha 20 → piso da 20; composto → o maior dos dois (o `limiar_piso` do executor é igual ao meu nos 52).
- DM com defasagem h−1, HLN, bilateral, t(n−1); Holm por família; bootstrap 8/2.000/42: como pré-declarado.
- **Se o piso for ignorado, nenhum veredito muda** (5 "A melhor" e 47 "sem evidência" nos dois casos). Os 5 passam folgados: |Δ| ≥ 54,6 contra
  limiar 10,4; nenhum teste tem p_Holm entre 0,05 e 0,10. Descritivo.

## 5. Sanidade do DM-HLN (n = 102, 20.000 simulações, nível nominal 5%; `v4_piso_e_sanidade.log`)

| h | d iid normal | d MA(h−1) |
|---|---|---|
| 1 | 4,81% | 4,72% |
| 4 | **6,78%** | 6,17% |
| 8 | **9,68%** | 8,30% |
| 12 | **11,07%** | 9,79% |

- O estimador **não está calibrado a 5% para h ≥ 4 com n = 102**: o núcleo retangular de h−1 defasagens e n pequeno inflam a
  rejeição (conhecido na literatura do DM). Não é erro de implementação (h = 1 e a checagem cruzada acima confirmam). É o método pré-declarado.
- Fallback de Bartlett (V ≤ 0): 0,04% em h = 4, 1,2% em h = 8, 4,3% em h = 12 sob H0 iid; nos 52 testes reais, 0.
- Poder (efeito 0,4 d.p., n = 102): 97,5% (h = 4) e 96,5% (h = 12).
- **Consequência para as conclusões:** o viés é anticonservador, mas os 5 "A melhor" estão **todos em h = 1**, onde o tamanho é correto (4,8%).
  Em h = 4, 8, 12 nada passou; p mais honestos só reduziriam rejeições. As conclusões positivas não são ameaçadas.

## Ressalvas (para o texto do artigo e do executor)

1. **Tamanho do DM-HLN em h ≥ 4** (acima): declarar na Seção 3.5 como limitação; não afirmar "nível 5%" para h = 8 e 12.
2. **Serie pareada com buraco de calendário:** 1 salto de 56 dias nas 102 semanas (7 semanas faltantes seguidas); o DM e o bootstrap tratam as semanas vizinhas
   ao buraco como adjacentes (como especificado). Efeito esperado desprezível.
3. **Piso medido só no `completo`** (§8b) e aplicado a `sem_X`, `so_X` e ao composto por extensão (Emenda 1). Não verificável aqui; vale como suposição declarada.
4. **IC fronteira** em F4 composto × folha 5, h = 12 (ver 3).
5. **Formato:** `E3_composto/previsoes.csv` com 16 dígitos (não ida-e-volta exata); diferença ≤ 2,3e-13 nas previsões.
6. **Fora do escopo desta certificação:** E5 (alarme: r, L = 421 × r, VP/FN/FP) não foi reimplementada.

## Arquivos

`reimpl.py` (reimplementação) · `v1_e3.py` · `v2_familias.py` + `v2_comparar.py` · `v3_bootstrap.py` · `v4_piso_e_sanidade.py` · `v5_checagens_cruzadas.py` · `v6_empates.log`
· logs `*.log` · saídas `minhas_familias.csv`, `meu_e3_previsoes.csv`, `fam_seed*.csv`, `variacao_monte_carlo_ic.csv`.
