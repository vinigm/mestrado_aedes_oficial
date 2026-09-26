# A calibração das faixas, separada por nível de casos

> **26/09/2026.** Pergunta do Vinicius: os números agregados de cobertura e de cruzamento de quantis
> preocupam — dá para medir isso melhor? Resposta: dá, e desagregar muda o diagnóstico.
>
> **Descritivo.** Nenhum modelo treinado, nenhum teste de hipótese, nenhum p-valor. É recálculo sobre as
> previsões certificadas de `../2026-09-26_wis_na_tabela_restaurada/`. Por não testar hipótese, não abre
> família de correção múltipla. Reprodutível com [`diagnosticar.py`](diagnosticar.py).

---

## Em uma frase

🔴 **O modelo é bem calibrado quando está calmo e péssimo quando importa.** Nas semanas acima de 421
casos, o intervalo de 50% cobre **8%** e o de 90% cobre **18%**.

---

## 1. A cobertura, por faixa — cenário adotado

O esperado, se as faixas fossem honestas, é **50%** e **90%**.

| Faixa de casos reais | Semanas | Intervalo de 50% | Intervalo de 90% |
|---|---|---|---|
| **Calmaria, 0 a 20** | 814 | **59,2%** | **90,5%** |
| Subida, 21 a 140 | 110 | 18,2% | 63,6% |
| Mobilização, 141 a 421 | 72 | 27,8% | 47,2% |
| 🔴 **Alerta ou mais, acima de 421** | 163 | **8,0%** | **17,8%** |

No HistGB folha 20 o padrão é o mesmo: **63,8% / 93,4%** na calmaria contra **6,1% / 27,0%** no Alerta.

- **Na calmaria a calibração é quase perfeita.** O intervalo de 90% cobrindo 90,5% é o que se espera de um
  modelo bem ajustado.
- **A degradação é monotônica com o nível de casos.** Quanto maior a epidemia, mais estreita fica a faixa
  em relação ao erro real.
- ⚠️ **O número agregado escondia isso.** As "20% a 41%" eram uma média entre 814 semanas calmas, bem
  calibradas, e 163 semanas de epidemia, em que a faixa não vale nada.

## 2. O cruzamento de quantis, por faixa

| Faixa | Origens | Cruzaram | Correção mediana | Correção p90 | Casos reais medianos |
|---|---|---|---|---|---|
| Calmaria, 0 a 20 | 1.628 | 79% | **1,0 caso** | 10,6 | 2 |
| Subida, 21 a 140 | 220 | 77% | 10,0 | 64,2 | 39 |
| Mobilização | 144 | 71% | 27,6 | 111,6 | 245 |
| Alerta ou mais | 326 | 67% | **61,3 casos** | 231,3 | 1.109 |

- **A taxa de cruzamento é parecida em todas as faixas**, entre 67% e 79%. O "77%" agregado não estava
  concentrado em lugar nenhum.
- **Mas o tamanho da correção muda por duas ordens de grandeza:** 1 caso na calmaria e 61 no Alerta.
- **Na calmaria o cruzamento é ruído puro.** Os 7 quantis ficam todos amontoados perto de zero e a ordem
  deles se inverte por acaso. Corrigir muda 1 caso numa semana que tem 2. É irrelevante.
- **Em epidemia o cruzamento é sintoma real**, com correção mediana de 61 casos.

## 3. O que causa isso

**Fato estrutural, não hipótese:** os 7 quantis são **7 modelos independentes**, cada um treinado com sua
própria perda quantílica. Nada no treino obriga o q0,25 a ficar abaixo do q0,75. Quando os dados são
poucos e a variância é alta, eles se cruzam.

- A correção que aplicamos hoje é **reordenar** os quantis. Isso é a solução clássica de Chernozhukov,
  Fernández-Val e Galichon (2010), e é comprovadamente não-pior que o original. **Já estamos usando a
  correção barata.**
- **Ela não resolve a faixa estreita.** Reordenar conserta a ordem, não a largura.

## 4. 🔴 A leitura que junta com o resto do projeto

Três medições independentes apontam para a mesma coisa:

| Medição | Data | O que diz |
|---|---|---|
| Captura do pico **0,388** em 3 meses | 13/09 | o modelo subestima o tamanho da epidemia |
| Melhor limiar de decisão fica **abaixo** de 421 em h=4, 8 e 12 | 26/09 | o modelo prevê baixo demais em horizonte longo |
| Cobertura de **8%** acima de 421 | 26/09 | e ele está **confiante** ao prever baixo demais |

**A frase que resume, e que é honesta:** *o modelo sabe dizer quando a cidade está calma, não sabe dizer o
tamanho da epidemia, e — o que é pior — não sabe que não sabe.*

## 5. O que isso muda na prática

- ✅ **Para alarme em limiar baixo, a calibração não atrapalha.** O que o alarme precisa é cruzar o
  limiar, e nas semanas calmas o modelo é confiável.
- 🚫 **Para estimar o tamanho da epidemia, a faixa não deve ser publicada como está.** Dizer "entre X e Y
  casos" com o intervalo de 90% seria enganoso: ele acerta 18% das vezes quando a coisa é grande.
- ⏳ **Isso explica por que a conformal de 25/09 não funcionou:** ela aplica uma correção **única** para
  todos os níveis. O problema é dependente do nível, então uma correção constante empurra tudo para cima
  e estoura os alarmes falsos, que foi exatamente o medido (de 15 para 124).

## 6. Caminhos, do mais barato ao mais caro

Nenhum foi testado. Ordem de custo crescente:

1. **Modelar em escala transformada** (raiz ou log) e voltar. A variância cresce com o nível, que é o
   padrão de contagem; em escala transformada, faixa constante vira faixa proporcional. É o caminho mais
   barato e o mais provável de funcionar.
2. **Distribuição empírica dos resíduos por faixa**, em vez de 7 modelos independentes. Coerente por
   construção, e impossível de cruzar.
3. **Um modelo só que emita a distribuição inteira** — floresta de regressão quantílica, em que a
   distribuição sai da folha. Elimina o cruzamento por construção.
4. **Conformal condicionada ao nível previsto**, em vez da constante que falhou.

## 7. Arquivos

| Arquivo | O que é |
|---|---|
| [`diagnosticar.py`](diagnosticar.py) · `execucao.log` | o script e a saída |
| `saidas/cobertura_por_faixa.csv` | cobertura dos intervalos de 50% e 90%, por modelo e faixa |
| `saidas/cruzamento_por_faixa.csv` | taxa de cruzamento e tamanho da correção, por faixa |
