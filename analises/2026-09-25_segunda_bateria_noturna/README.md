# Segunda bateria noturna — os resultados do projeto na temporada de 2026

> **Rodada na noite de 25 para 26/09/2026**, com autorização do Vinicius. Protocolo em
> [PRE_DECLARACAO.md](PRE_DECLARACAO.md), com emendas datadas. **Cada rodada foi certificada por
> reimplementação independente:** [A](CERTIFICACAO_A.md) · [B](CERTIFICACAO_B.md) · [C e D](CERTIFICACAO_C_D.md).
> Base: tabela oficial atualizada com 2026, em [atualizacao_dados_2026](../2026-09-25_atualizacao_dados_2026/).
>
> **2026 não entrou em nenhuma decisão anterior.** Recorte 2026 = 01/01 a 19/04/2026, 16 semanas, nenhuma
> acima de 100 confirmados; o maior valor semanal foi 3.

---

> 🧭 **Leitura corrigida em 26/09/2026, pelo Vinicius:** 2026 está **fora do domínio** do modelo. Nenhuma série de
> temporadas crescentes permite prever um ano de 19 confirmados, então **o erro em 2026 não testa a metodologia**.
> A metodologia se testa acumulando temporadas, julgadas por tipo. Os números abaixo seguem sendo fatos medidos,
> mas as leituras de veredito (A1 "inverte", A2, D) passam a ser **descritivas**: mostram como o método se comporta
> num ano calmo. O que não depende de 2026 continua valendo: a seção B em 2024-2025.

---

## Em uma frase

**Em 2026, um ano calmo com o mosquito em nível crítico, o vetor empurrou a previsão para cima:** com vetor, o
modelo previu temporada; sem vetor, acertou a calmaria. É descritivo, porque 2026 está fora do domínio do modelo.

---

## A. Os resultados principais em 2026

MAE, casos por semana:

| Braço | 2024-2025, 1 mês | 2024-2025, 3 meses | **2026, 1 mês** | **2026, 3 meses** |
|---|---|---|---|---|
| HistGB folha 20, **com** vetor | **205,7** | **254,1** | 601,0 | 579,0 |
| HistGB folha 20, **sem** vetor | 225,3 | 270,4 | **41,8** | **315,1** |
| LightGBM, **com** vetor | 212,7 | 253,4 | 634,8 | 565,1 |
| LightGBM, **sem** vetor | 228,7 | 286,9 | **41,9** | **314,6** |
| Cenário adotado, com vetor | 221,3 | 293,3 | 223,8 | 482,9 |
| HistGB folha 5, sem vetor | 240,0 | 281,1 | **25,9** | 278,8 |
| Régua "o ano passado" | 212,0 | 212,0 | 902,9 | 902,9 |

### A1 — com folha 20, o vetor reduz o erro de 3 meses? 🚫 Não em 2026: inverte

- Em 2026, em 3 meses, **o vetor aumenta o erro**: 579 contra 315 no HistGB e 565 contra 315 no LightGBM.
  p Holm **0,0499** nos dois, **na direção contrária** à hipótese.
- Em 2024-2025 o vetor ajudava: 254 contra 270 e 253 contra 287.
- **Leitura:** o mosquito esteve em nível crítico em 2026 e não houve epidemia. O modelo aprendeu "mosquito
  alto = casos" com 2022-2025, e 2026 quebrou essa relação. É coerente com a hipótese de imunidade depois de
  2024-2025, mas imunidade não foi medida.

### A2 — o modelo erra menos que "o ano passado" num ano atípico? ✅ Sim

- Cenário adotado contra a régua em 2026: p Holm **0,0001** em 1 mês e **0,0039** em 3 meses. HistGB folha 20:
  **0,022** em 3 meses.
- ⚠️ **O modelo não foi preciso; a régua é que errou muito.** Ela repetiu o pico de 2025, 2.381 casos por semana.
  O modelo chegou a prever **1.117** numa semana com 3.

### A3 — alarmes falsos em 2026, somados nos 12 horizontes

| Limiar, casos por semana | Cenário adotado | HistGB folha 20 | Régua |
|---|---|---|---|
| 100, o do projeto | 107 | 121 | 132 |
| 140, Mobilização | 95 | 109 | 132 |
| 421, Alerta | 60 | 81 | 96 |
| 702, Epidemia | 39 | 63 | 84 |

- O modelo dispara **menos alarmes falsos que a régua em todos os limiares**. Mas continua disparando muitos: não
  houve nenhum surto real em 2026.

---

## B. Vários quantis e o WIS, a métrica oficial dos sprints

WIS, menor é melhor, contra a régua **climatológica**: os quantis da mesma semana nos anos anteriores.

| Recorte, horizonte | Cenário adotado | HistGB folha 20 | Régua climatológica |
|---|---|---|---|
| 2024-2025, 1 mês | **218,7** | **200,6** | 313,5 |
| 2024-2025, 3 meses | 303,7 | **281,4** | 324,2 |
| 2026, 3 meses | 141,7 | 159,9 | **64,4** |

- **Em 2024-2025, os modelos vencem a régua oficial dos sprints em 1 mês**, os dois com p Holm < 0,0001, e o folha 20
  vence também em 3 meses, p Holm 0,0016. **Pelo WIS, o modelo está à frente da régua do Brasil.**
- **Em 2026, em 3 meses, os dois perdem para a régua climatológica**, com p Holm 0,0001. A climatologia mistura os
  anos calmos e prevê pouco, o que em 2026 acertou.
- 🔴 **As faixas de previsão são estreitas demais:** o intervalo de 50% cobre só **14%** das semanas, e o de 90% só
  **54%**, no cenário adotado em 3 meses em 2024-2025. Em 77% das origens os quantis cruzaram e foram reordenados.

---

## C. Estabilidade das vencedoras da busca

| Vencedora | MAE em 3 meses em 2026, média de 5 sementes | Variação entre sementes | Veredito |
|---|---|---|---|
| LightGBM | 538,1 | 2,0% | **estável** |
| HistGB | 519,7 | 8,5%, com sinais mistos | **instável** |

Nas duas, a média fica **pior** que o cenário adotado, 482,9.

---

## D. Calibração conformal do quantil

- **A cobertura sobe**, de 50% para 78% no cenário adotado em 3 meses.
- **Mas os alarmes falsos explodem:** de 15 para 124, com o limiar de 100.
- **A perda quantílica piora em 1 mês,** −8,7% com p Holm < 0,001, e melhora em 3 meses sem significância.
- **Não serve como está.** Corrige a cobertura empurrando tudo para cima.

---

## O que muda

- ⚠️ **O achado do vetor com folha 20, de 24/09, segue exploratório:** carregado por 2024. 2026, fora do domínio,
  não o confirma nem o refuta. Continua fora do seminário como resultado, por ser exploratório.
- ✅ **O que se sustenta:** até 1 mês o modelo é bom. E, pelo WIS de 2024-2025, ele vence a régua oficial dos sprints
  brasileiros.
- 🔴 **O mosquito é necessário, mas não suficiente.** Em ano de epidemia ele ajuda a prever. Num ano com o
  mosquito alto e sem epidemia, ele empurra a previsão para cima. Para a tese, **a armadilha mede risco de
  transmissão, e não casos**.
- As faixas de previsão precisam de outra calibração. A conformal simples não resolve.

---

## Arquivos

| Pasta | Conteúdo |
|---|---|
| [`A_resultados_em_2026/`](A_resultados_em_2026/) | 8 braços × 12 horizontes, famílias A1 e A2, alarmes |
| [`B_quantis_e_wis/`](B_quantis_e_wis/) | 7 quantis, WIS, cobertura, régua climatológica |
| [`C_estabilidade/`](C_estabilidade/) | vencedoras da busca com 5 sementes |
| [`D_calibracao/`](D_calibracao/) | correção conformal |
