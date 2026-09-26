# Parte 8 — Os resultados, com tradução concreta

Esta seção mostra o que o modelo previsto acertou e errou, na avaliação feita entre **01/01/2024** e
aproximadamente **01/02/2026**, e — ponto central pedido pelo Vinicius — traduz cada número em uma
consequência prática. Um erro de "278,8 casos" ou uma "captura de pico de 0,388" não significam nada por
si só; a seção existe para explicar o que esses números fazem no mundo real, numa cidade de vigilância
epidemiológica.

Toda tabela citada aqui vem de uma pasta datada dentro de `analises/`, cada uma com seu próprio `README.md`
e, quando aplicável, sua pré-declaração e certificação adversarial (processo em que um segundo agente, sem
ver o resultado esperado, tenta reproduzir a medição do zero e apontar erros, em vez de só rodar o mesmo
código de novo). Os caminhos exatos aparecem ao lado de cada tabela.

---

## 8.1 O cenário adotado — o que está sendo medido, em uma frase

Antes de olhar números, é preciso saber o que é "o cenário adotado", porque todas as tabelas desta seção o
usam como referência principal.

- O algoritmo é o **`HistGradientBoostingRegressor`** da biblioteca `scikit-learn`, abreviado neste
  documento como **HistGB**. É um método de **boosting**: em vez de treinar uma única árvore de decisão
  para prever o número de casos, ele treina uma sequência de árvores pequenas, cada uma corrigindo o erro
  que a soma das árvores anteriores ainda comete. O resultado final é a soma das previsões de todas as
  árvores da sequência.
- A árvore não é treinada para acertar a **média** do número de casos, e sim um **quantil**. Um quantil é
  o valor abaixo do qual uma certa fração das observações cai — por exemplo, o quantil 0,85 é o valor que,
  numa distribuição de possibilidades, deixa 85% das observações abaixo dele e 15% acima. Treinar para o
  quantil 0,85 (em vez da média, quantil equivalente a 0,50) é uma escolha deliberada de ser **cauteloso
  para cima**: o modelo tenta ficar acima do valor real com mais frequência do que ficaria se mirasse a
  média, porque, para um sistema de alarme de saúde pública, errar por excesso de cautela (prever demais)
  é operacionalmente menos perigoso do que errar por escassez (prever de menos, subestimar uma epidemia).
  Uma parte importante desta seção (§8.4 e §8.5) mostra que, na prática, essa cautela **não é suficiente**
  para evitar subestimação sistemática nos picos.
- Os hiperparâmetros são as configurações do algoritmo que não são aprendidas dos dados, e sim escolhidas
  antes do treino. No cenário adotado: `max_iter` **250** (o número de árvores da sequência de boosting),
  `learning_rate` **0,05** (o quanto cada árvore nova corrige o erro da soma anterior — um valor baixo
  significa correções pequenas e uma sequência mais longa, o que costuma generalizar melhor para dados
  novos), `max_leaf_nodes` **15** (o número máximo de folhas — de decisões finais — que cada árvore
  individual pode ter, limitando a complexidade de cada árvore) e `min_samples_leaf` **5** (o número mínimo
  de semanas de treino que precisam cair numa folha para ela ser aceita, evitando que o modelo memorize
  casos isolados).
- A entrada tem **20 colunas**: 8 de núcleo (o histórico da própria série de casos e variáveis de
  sazonalidade, como a semana do ano), 6 de clima (temperatura, precipitação e variáveis correlatas obtidas
  via satélite) e 6 do vetor (a série de captura de mosquitos *Aedes aegypti* nas armadilhas do MI-Aedes em
  Porto Alegre).
- O alvo (a variável que o modelo tenta prever) é o número de **casos confirmados** de dengue por semana
  epidemiológica em Porto Alegre, contados pelo município de **notificação** (onde o caso foi registrado no
  sistema de saúde), não pelo município de **residência** do paciente — a diferença entre os dois é uma
  decisão de produto, não um detalhe técnico, e está registrada como tal em outra seção deste documento.
- **Horizonte de previsão**, abreviado **h** nas tabelas, é quanto tempo de antecedência a previsão tem: h=1
  é uma previsão feita 1 semana antes da semana que ela tenta prever, h=4 é feita 4 semanas antes (por
  isso tratado neste documento como "1 mês"), h=8 como "2 meses" e h=12 como "3 meses".

Com isso definido, os números das próximas seções passam a fazer sentido.

---

## 8.2 O erro pontual por horizonte

### 8.2.1 O que é o erro absoluto médio (MAE)

O **erro absoluto médio**, em inglês *mean absolute error*, abreviado **MAE**, mede o tamanho médio do erro
de previsão, sem se importar se o modelo errou para cima ou para baixo — ele usa o **valor absoluto** do
erro, que é a distância entre o previsto e o real, sempre positiva.

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|
$$

Onde:

- **$n$** é o número de semanas (pares real-previsto) avaliadas.
- **$y_i$** é o número real de casos confirmados na semana $i$.
- **$\hat{y}_i$** é o número de casos que o modelo previu para a semana $i$.
- **$|\cdot|$** é o valor absoluto: transforma qualquer número negativo em positivo, então um erro de "−50
  casos" (previu menos que o real) e um erro de "+50 casos" (previu mais que o real) contam igual, os dois
  como 50.

**Exemplo numérico, do começo ao fim** (didático — números redondos, só para mostrar o mecanismo; a
tradução com os números reais do painel vem logo depois): imagine 4 semanas com real e previsto assim —
semana A: real 11, previsto 34; semana B: real 32, previsto 8; semana C: real 194, previsto 40; semana D:
real 494, previsto 384. Os erros absolutos são $|11-34|=23$, $|32-8|=24$, $|194-40|=154$ e $|494-384|=110$.
A soma é $23+24+154+110=311$, e o MAE é $311 \div 4 = 77{,}75$. Este exemplo, aliás, não é inventado: é uma
amostra real de 4 semanas certificadas do projeto (h=12, mediana prevista, período 2024-2025), calculada
por [`analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`](../../analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv)
— só que ali usa-se a previsão da mediana (quantil 0,50), não do quantil 0,85 do cenário adotado, por isso
o valor (77,75) não deve ser confundido com o **278,8** do painel oficial abaixo, que usa 284 semanas e o
quantil 0,85.

### 8.2.2 O que é o coeficiente de determinação (R²)

O **coeficiente de determinação**, chamado de **R²**, mede que fração da variação do número real de casos
o modelo consegue explicar, comparado com o erro que se teria só "chutando a média" da série toda para
todas as semanas.

$$
R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}
$$

Onde:

- **$\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$** é a soma dos erros do modelo, ao quadrado (essa soma tem nome
  próprio, soma dos quadrados dos resíduos).
- **$\sum_{i=1}^{n}(y_i - \bar{y})^2$** é a soma da distância de cada semana real até a média de todas as
  semanas reais ($\bar{y}$), ao quadrado (soma dos quadrados totais) — é o erro de um modelo ingênuo que
  sempre prevê a média.
- $R^2 = 1$ significa acerto perfeito; $R^2 = 0$ significa que o modelo é tão bom quanto prever sempre a
  média da série; **$R^2$ negativo** significa que o modelo é **pior** do que simplesmente prever a média
  — acontece quando o modelo erra sistematicamente numa direção com mais força do que a própria variação
  natural dos dados.

**Exemplo numérico, com os mesmos 4 pontos de cima:** a média dos 4 valores reais é
$\bar{y} = (11+32+194+494)/4 = 182{,}75$. A soma dos quadrados totais é
$(11-182{,}75)^2+(32-182{,}75)^2+(194-182{,}75)^2+(494-182{,}75)^2 = 29.498{,}1+22.725{,}6+126{,}6+96.876{,}6
= 149.226{,}75$. A soma dos quadrados dos erros do modelo é
$23{,}44^2+24{,}08^2+154{,}14^2+110{,}35^2 = 549{,}4+579{,}8+23.759{,}1+12.177{,}1 = 37.066{,}1$. O R² é
$1 - 37.066{,}1/149.226{,}75 = 1 - 0{,}2484 = 0{,}7516$. Nesta pequena amostra de 4 semanas, o modelo
explicaria **75,2%** da variação — bem acima do 0,437 medido no painel oficial completo (§8.2.3), porque
uma amostra de 4 semanas escolhidas ao acaso tende a produzir números instáveis; é exatamente por isso
que o painel oficial usa **284 a 295 pares**, não 4.

### 8.2.3 O painel de erro do cenário adotado

Avaliação de **01/01/2024** a aproximadamente **01/02/2026**:

| Horizonte | Pares avaliados ($n$) | Erro absoluto médio (MAE) | Coeficiente de determinação (R²) |
|---|---|---|---|
| 1 semana | **102** | **98,0** | **0,898** |
| 4 semanas (1 mês) | **102** | **219,7** | **0,628** |
| 8 semanas (2 meses) | **102** | **272,6** | **0,450** |
| 12 semanas (3 meses) | **102** | **278,8** (painel publicado: 278,7) | **0,437** |

Um "par" é uma semana em que existe tanto um valor real de casos confirmados quanto uma previsão feita
$h$ semanas antes para aquela mesma semana — o número de pares cai de 295 para 284 conforme $h$ cresce
porque a janela de avaliação é fixa em datas de calendário, e previsões de horizonte mais longo "cabem"
menos vezes dentro da mesma janela nas pontas.

### 8.2.4 Tradução: o que um erro de 98 a 278,8 casos significa numa semana real

Um MAE de **278,8** na avaliação de 3 meses não diz, sozinho, se isso é grave. A gravidade depende do
tamanho típico das semanas que estão sendo previstas — e aqui a série tem semanas de calmaria (poucos
casos) e semanas de epidemia (centenas de casos) misturadas.

- **Em 1 semana de antecedência (h=1), o erro de 98,0 casos é pequeno frente às semanas de epidemia** —
  nas semanas com mais de 421 casos (estágio Alerta do plano municipal, ver §8.6), o valor real mediano é
  **917** (medido em `analises/2026-09-26_transformacao_de_escala/README.md`); um erro de 98 nessa faixa
  seria de cerca de **10,7%** do valor real. Mas na calmaria (semanas com poucos casos), um erro de 98
  pode ser maior do que o próprio valor real — é um erro relativamente grande quando a cidade está calma.
- **Em 1 mês (h=4), o erro sobe para 219,7.** Numa semana de epidemia moderada (a faixa "Mobilização" do
  plano municipal, 141 a 421 casos), esse erro já é comparável ao próprio tamanho da faixa inteira: é como
  errar por uma margem do tamanho da diferença entre "início de epidemia" e "epidemia grave".
- **Em 3 meses (h=12), o erro de 278,8 numa semana de epidemia grande (917 casos reais medianos nessa
  faixa) significa prever, tipicamente, bem menos da metade do que vai acontecer.** Isso é aprofundado com
  todo o detalhe em §8.4 e §8.5, porque **278,8 é a média de TODOS os horizontes de erro em 3 meses,
  incluindo as semanas calmas** — nas semanas de epidemia especificamente, o erro típico é ainda maior
  (mediana de **539**, ver §8.5), porque a média de 278,8 é puxada para baixo pelas muitas semanas calmas
  em que o modelo acerta quase exatamente.
- **O coeficiente de determinação cai de 0,898 (h=1) para 0,437 (h=12).** Em português simples: a 1 semana
  de antecedência, o modelo explica quase 90% de por que uma semana tem mais ou menos casos que outra; a
  3 meses, explica menos de 44% — mais da metade da variação entre semanas fica sem explicação do modelo
  nesse horizonte.

---

## 8.3 A comparação com as réguas simples

### 8.3.1 O que é uma "régua" nesta avaliação

Uma **régua** (em inglês, *baseline*) é uma regra de previsão deliberadamente simples, sem nenhum
aprendizado estatístico, usada como piso de comparação: se o modelo treinado não bate uma régua ingênua,
ele não está agregando valor sobre o óbvio. Duas réguas aparecem aqui:

- **Régua sazonal**: prevê que o número de casos de uma semana futura será igual ao número de casos da
  mesma semana epidemiológica, **52 semanas antes** (isto é, "o que aconteceu nessa mesma época do ano
  passado").
- **Persistência**: prevê que o número de casos da semana futura será igual ao número de casos **de hoje**
  (a última semana com dado disponível no momento da previsão).

### 8.3.2 A tabela, na janela oficial (2024 até fev/2026)

Erro absoluto médio (MAE), por horizonte:

| Regra / modelo | h=1 | h=4 | h=8 | h=12 |
|---|---|---|---|---|
| **Cenário adotado (HistGB, quantil 0,85)** | **98,0** | **219,7** | **272,6** | **278,8** |
| Régua sazonal (mesma semana, ano anterior) | 202,1 | 213,2 | 216,2 | 217,8 |
| Persistência (repete o valor de hoje) | 83,3 | 279,0 | 531,0 | 697,5 |
| HistGB, variante folha mínima 20 | 133,6 | 199,6 | 223,2 | 243,8 |

Fonte: `analises/2026-09-25_regua_regras_simples/`.

⚠️ **Cuidado ao citar isto em outro contexto:** numa janela mais estreita, só 2024-2025 (**n=97**), a régua
sazonal muda para **210,4 · 222,0 · 225,1 · 226,8** — números diferentes, porque a janela de avaliação é
diferente. Toda citação desta tabela precisa vir com a janela declarada ao lado.

### 8.3.3 A leitura honesta

- **Em 1 semana de antecedência (h=1), o modelo vence com folga.** 98,0 contra 202,1 da régua sazonal e
  83,3 da persistência — o modelo é o único que bate os dois pisos simultaneamente nesse horizonte.
- **Em 2 e 3 meses (h=8 e h=12), a régua sazonal vence o cenário adotado.** 216,2 contra 272,6 em h=8; e
  217,8 contra 278,8 em h=12. A régua sazonal — que não usa clima, não usa mosquito, não usa nenhum dado
  do ano corrente além do calendário — erra **menos** que o modelo treinado, nesses dois horizontes.
- **Por que isso acontece:** dengue em Porto Alegre segue um ciclo forte de sazonalidade — os casos sobem
  no verão e outono e caem no inverno, ano após ano, de forma consistente. Quando a pergunta é "quantos
  casos em 3 meses", quase toda a informação útil para responder já está contida na própria época do ano:
  saber que estamos em março já entrega grande parte da resposta, porque março historicamente tem mais
  casos que julho. As variáveis que o modelo usa além disso — clima recente e mosquito recente — carregam
  informação sobre o **presente**, não sobre o que vai acontecer daqui a 3 meses; conforme o horizonte
  cresce, a vantagem de informação recente decai e a sazonalidade (que a régua já captura de graça, sem
  treinar nada) passa a valer mais que o resto.
- Isso não é uma falha de implementação. É uma **limitação estrutural do horizonte longo**: para vencer a
  régua sazonal em 3 meses, o modelo precisaria de sinal preditivo que ainda não decaiu depois de 12
  semanas — e a busca de hiperparâmetros (25/09/2026, 120 configurações) e as outras 9 famílias de modelo
  testadas (§8.9 e demais seções deste documento) não encontraram esse sinal.

---

## 8.4 A captura do pico, traduzida

### 8.4.1 A fórmula

A **captura do pico** é a métrica histórica do projeto (calculada pela primeira vez em 13/09/2026) para
medir se o modelo acerta o **tamanho** de uma epidemia, olhando só para as semanas em que já se sabe que
há surto:

$$
\text{Captura do pico} = \frac{\overline{\hat{y}}_{\text{surto}}}{\overline{y}_{\text{surto}}}
$$

Onde:

- **$\overline{y}_{\text{surto}}$** é a média do número real de casos, contando só as semanas em que o
  real passou de **100 casos** (o corte de "semana de surto" usado por esta métrica).
- **$\overline{\hat{y}}_{\text{surto}}$** é a média do número **previsto** de casos pelo modelo, nas
  mesmas semanas.
- Um valor de **1,0** significa acerto perfeito no tamanho médio da epidemia; um valor abaixo de 1
  significa que o modelo, em média, prevê menos do que a epidemia real; acima de 1 significaria previsão
  em excesso.

### 8.4.2 O valor medido e o exemplo numérico

Em 3 meses (h=12), avaliação 2024+: **captura do pico = 0,388** (fonte:
`analises/2026-09-13_metrica_de_alarme/README.md`, reconfirmado em 26/09/2026 na rodada de calibração por
faixa).

Para traduzir isso em um exemplo concreto: a mesma medição de 26/09/2026 (fonte:
`analises/2026-09-26_transformacao_de_escala/README.md`, tabela de largura do intervalo por faixa) mostra
que, na faixa de gravidade "Alerta ou mais" (semanas com mais de **421** casos reais, o estágio de alerta
epidemiológico do plano municipal — ver §8.6), o **valor real mediano** dessas 163 semanas é **917**
casos, e o **erro mediano** do modelo nessa mesma faixa é **539** casos, sempre para menos (ver §8.5 sobre
por que é "sempre para menos" e não um erro que às vezes é para mais). Isso implica uma previsão mediana
de aproximadamente $917 - 539 = 378$ casos numa semana desse porte — uma proporção de $378/917 \approx
41\%$, no mesmo patamar da captura do pico agregada de 0,388 (a pequena diferença entre 41% e 38,8% vem
de usar mediana num caso e média no outro).

### 8.4.3 A consequência prática

- Se um gestor de saúde dimensionar **leitos, equipes e insumos** com base na previsão do modelo para uma
  semana que vai chegar a 917 casos reais, ele planejaria para cerca de **378** casos. Quando a semana
  real chegar, a demanda real será **cerca de 2,4 vezes** maior do que o planejado.
- Esse fator de 2,4 não é um exagero pontual: é consistente com a captura do pico de 0,388 medida sobre
  **todas** as semanas de surto da avaliação, não um caso isolado.
- **Por que subestimação sistemática é mais perigosa do que um erro aleatório do mesmo tamanho:**
  - Um erro **aleatório** (ruído) tem a mesma chance de superestimar quanto de subestimar. Um gestor que
    planeja repetidamente com um modelo desse tipo, ao longo de muitas semanas, vai por vezes ter folga de
    recursos e por vezes ter falta — em média, o sistema absorve o erro, porque os excessos de umas
    semanas compensam as faltas de outras (supondo que os recursos "sobrando" numa semana calma possam,
    na prática, ser realocados ou não custem muito a mais).
  - Um erro **sistemático** (viés) empurra sempre na mesma direção. Um gestor que planeja repetidamente
    com este modelo em semanas de epidemia grande vai **sempre** ter falta de recursos, nunca sobra — não
    há semana de "compensação". O erro se acumula na mesma direção a cada nova epidemia, em vez de se
    cancelar estatisticamente.
  - Em termos de saúde pública: um sistema de leitos dimensionado sistematicamente para 40% da demanda
    real de picos vai colapsar **toda vez** que uma epidemia grande chegar, não só ocasionalmente.

---

## 8.5 O erro mediano de 539 casos sobre 917 reais — por que é viés, não ruído

### 8.5.1 Mediana: a definição

A **mediana** de um conjunto de números é o valor do meio quando eles são colocados em ordem — metade dos
valores fica abaixo dela, metade acima. Ao contrário da **média** (soma dividida pela quantidade), a
mediana não é puxada por valores extremos isolados; por isso costuma ser preferida para descrever "o caso
típico" quando a distribuição tem valores muito distantes da maioria (como acontece com casos de dengue,
que variam de 0 a mais de 2.000 numa mesma série).

### 8.5.2 O número e a tradução

Nas 163 semanas da faixa "Alerta ou mais" (real acima de 421 casos, avaliação certificada em
26/09/2026), o valor real mediano é **917** casos e o erro mediano do modelo é **539** casos — ou seja, na
semana típica dessa faixa, o modelo erra por **539 casos**, o equivalente a **59%** do valor real
($539/917 \approx 0{,}588$).

### 8.5.3 Por que isso é viés e não ruído

Três medições independentes, feitas em datas diferentes, com métodos diferentes, apontam todas na mesma
direção:

| Medição | Data | Direção do erro |
|---|---|---|
| Captura do pico **0,388** (h=12) | 13/09/2026 | previsão sistematicamente **abaixo** do real |
| Melhor limiar de decisão do alarme cai **abaixo** de 421 em h=4/8/12 (§8.9) | 26/09/2026 | o modelo já subestima o bastante para que baixar o limiar de decisão capture mais surtos |
| Cobertura do intervalo de 90% cai para **17,8%** acima de 421 casos (§8.6) | 26/09/2026 | o modelo erra sempre para o mesmo lado — errar em direções aleatórias não derrubaria a cobertura assim |

Se o erro de 539 fosse **ruído** (aleatório), a distribuição dos erros nessa faixa teria aproximadamente
metade das semanas com previsão acima do real e metade abaixo — o que faria a cobertura do intervalo de
90% ficar próxima de 90% (a faixa cobriria o real na maioria das vezes) e a captura do pico ficar próxima
de 1,0 (superestimações e subestimações se cancelariam na média). Nenhuma das duas coisas acontece: a
cobertura despenca e a captura fica em 0,388. **Isso é a assinatura de um viés sistemático — o modelo não
está "errando por acaso perto do valor certo", está prevendo consistentemente abaixo dele.**

---

## 8.6 A calibração por faixa — o modelo é honesto quando está calmo, e não quando importa

### 8.6.1 O que é um intervalo de previsão, cobertura e calibração

O cenário adotado, além do quantil 0,85 usado como estimativa pontual (§8.1), também é treinado
separadamente em outros **6 quantis** (0,05 · 0,10 · 0,25 · 0,50 · 0,75 · 0,90 · 0,95, mais o próprio
0,85), formando **7 modelos independentes**, cada um mirando um quantil diferente da distribuição de
casos possível para aquela semana. Combinando pares desses quantis, forma-se um **intervalo de previsão**:
por exemplo, o intervalo entre o quantil 0,05 e o quantil 0,95 deveria conter o valor real em
aproximadamente **90%** das semanas, **se o modelo estiver bem calibrado** — por isso ele é chamado, nas
tabelas deste projeto, de "IC 90%" (o intervalo entre os quantis 0,25 e 0,75 é chamado "IC 50%").

⚠️ **Nota de rigor:** este "IC" (abreviação de intervalo de confiança, sigla amplamente usada em
estatística) não é tecnicamente um intervalo de confiança clássico no sentido em que a estatística
inferencial usa o termo — um intervalo de confiança clássico descreve a incerteza sobre um **parâmetro**
de uma população (por exemplo, a média verdadeira), assumindo repetição do processo de amostragem. Aqui
trata-se de um **intervalo de previsão** (ou intervalo preditivo): a incerteza sobre uma **observação
futura específica** (o número de casos de uma semana), obtida diretamente dos quantis previstos pelo
modelo. O projeto usa "IC" como atalho de notação nas tabelas; este documento mantém essa notação por
consistência, mas o conceito correto é "intervalo de previsão calibrado por quantis".

**Cobertura** é a fração de semanas em que o valor real caiu de fato dentro do intervalo previsto.
**Calibração** é o quanto a cobertura medida bate com a cobertura nominal esperada (50% ou 90%) — um
modelo bem calibrado erra a cobertura por pouco; um modelo mal calibrado erra por muito, para mais ou
para menos confiança do que deveria ter.

### 8.6.2 A tabela, por faixa de gravidade (cenário adotado, 26/09/2026)

O esperado, se o modelo fosse honesto sobre sua própria incerteza, é **50%** e **90%** de cobertura:

| Faixa de casos reais | Semanas | Cobertura IC 50% | Cobertura IC 90% |
|---|---|---|---|
| Calmaria, 0 a 20 casos | 814 | **59,2%** | **90,5%** |
| Subida, 21 a 140 casos | 110 | 18,2% | 63,6% |
| Mobilização, 141 a 421 casos | 72 | 27,8% | 47,2% |
| **Alerta ou mais, acima de 421 casos** | 163 | **8,0%** | **17,8%** |

Fonte: `analises/2026-09-26_calibracao_por_faixa/`.

### 8.6.3 A tradução

- **Na calmaria, o intervalo de 90% cobre 90,5% das 814 semanas** — isso é quase exatamente o esperado. O
  modelo, quando a cidade está com poucos casos, sabe descrever corretamente sua própria incerteza: quando
  ele diz "tenho 90% de certeza de que o valor vai cair neste intervalo", ele acerta 9 em cada 10 vezes,
  como prometido.
- **Acima de 421 casos, o mesmo intervalo de 90% cobre só 17,8%** — o modelo diz "tenho 90% de certeza",
  mas na prática acerta **menos de 1 em cada 5 vezes**. A degradação é **monotônica**: quanto maior o
  nível de casos da semana, pior a calibração — não é um problema isolado de uma faixa, é uma tendência
  contínua.
- **O que um gestor faria de errado, confiando nisso:** se um gestor de saúde lesse "o modelo estima entre
  X e Y casos, com 90% de confiança" numa semana de epidemia grande, e tomasse decisões de alocação de
  recursos como se essa confiança fosse real, ele estaria, na verdade, operando com uma confiança real de
  apenas **17,8%** — quase 5 vezes menor do que a suposta. Na prática, isso significa que a faixa
  "acabaria de fora" o valor real em mais de 4 entre 5 semanas de epidemia grave, e o gestor descobriria
  isso tarde demais, quando a demanda real já tivesse estourado a faixa que ele havia planejado.
- Um exemplo concreto e real, da própria série de dados certificada (26/09/2026): numa semana com **917**
  casos reais (h=12, cenário adotado), o intervalo de 90% previsto foi de **0 a 839,93** casos — o limite
  **superior** do intervalo, o mais otimista possível, já ficou abaixo do valor real. O modelo não apenas
  errou o centro da previsão: ele errou a ponto de o valor real cair **fora até do extremo superior da sua
  própria margem de incerteza declarada**.

---

## 8.7 A largura do intervalo contra o erro real — por que "alargar a régua" não resolve

### 8.7.1 A tabela

Cenário adotado, comparando o tamanho do intervalo de 90% (o quanto de margem o modelo declara) com o
erro que ele de fato comete (26/09/2026):

| Faixa | Real mediano | Largura do IC 90% | Erro mediano | Largura que seria necessária | Quanto falta |
|---|---|---|---|---|---|
| Calmaria | 1 | 8,5 | 1,3 | 4 | **0,5×** (o intervalo já é largo demais) |
| Subida | 47 | 101,1 | 29,6 | 97 | 1,0× (aproximadamente correto) |
| Mobilização | 247 | 195,6 | 157,8 | 519 | 2,7× |
| **Alerta ou mais** | **917** | **592,7** | **539,0** | **1.773** | **3,0×** |

"Largura que seria necessária" é o tamanho de intervalo que teria feito o valor real caber dentro da
margem de erro típica daquela faixa; "quanto falta" é a razão entre essa largura necessária e a largura
que o modelo de fato declarou.

### 8.7.2 Por que a transformação de escala (raiz quadrada, logaritmo) não resolveu isso

A hipótese natural, testada e pré-declarada em 26/09/2026
(`analises/2026-09-26_transformacao_de_escala/`), era que dados de contagem (como número de casos) têm
**variância crescente com o nível** — quanto maior o número esperado de casos, maior a dispersão em torno
dele — e que reescrever o alvo em raiz quadrada ou logaritmo antes de treinar corrigiria isso, porque
essas transformações "comprimem" valores altos, o que deveria fazer o intervalo de largura constante na
escala transformada virar um intervalo de largura **proporcional ao nível** depois de voltar para a escala
de casos.

**A hipótese estava errada, e o motivo é mensurável:**

- A largura do intervalo **já cresce** com o nível de casos: de **8,5** (calmaria) para **592,7** (Alerta
  ou mais), um fator de aproximadamente **70 vezes**.
- Mas o erro cresce **mais rápido ainda**: de **1,3** para **539,0**, um fator de aproximadamente **415
  vezes**.
- Ou seja, o problema nunca foi "intervalo de largura constante" — o intervalo já não é constante. O
  problema é um intervalo que cresce **mais devagar do que o erro real cresce**.
- Raiz quadrada e logaritmo **comprimem** valores altos ainda mais do que a escala original — então, ao
  aplicá-las, o intervalo (depois de voltar para casos) cresce **ainda mais devagar** do que sem
  transformação nenhuma, o oposto da direção necessária. Foi exatamente isso que a rodada de 26/09/2026
  mediu: a cobertura acima de 421 casos, que já era 17,8% sem transformação, caiu para **15,9%** com raiz
  quadrada e **13,5%** com logaritmo — piorou nas duas variantes, sem exceção, em todas as 4 faixas de
  gravidade, inclusive na calmaria (que era bem calibrada e passou a subcalibrada: de 90,5% para 84,2% e
  80,5%).
- **FATO (medido em 26/09/2026, certificação adversarial aprovada):** o problema de calibração nos picos
  é de **viés de nível**, não de forma da variância — e nenhuma transformação de escala corrige viés, só
  redistribui a forma da incerteza. Alargar o intervalo até os **1.773** casos de largura necessários
  cobriria os 90% prometidos, mas produziria uma faixa de aproximadamente 100 a 1.900 casos — larga
  demais para informar qualquer decisão prática de dimensionamento.

---

## 8.8 O escore de intervalo ponderado (WIS)

### 8.8.1 A fórmula

O **escore de intervalo ponderado**, em inglês *weighted interval score*, abreviado **WIS**, é a métrica
usada neste projeto para avaliar a qualidade de uma previsão **probabilística** — uma previsão que não dá
só um número, mas uma distribuição inteira de possibilidades (aqui, os 7 quantis do cenário adotado). Ela
penaliza ao mesmo tempo (a) intervalos largos demais e (b) o valor real cair fora do intervalo declarado,
de forma proporcional a quão longe ele caiu. A formulação usada é a de Bracher, Heyder e colegas (2021)
para desafios de previsão epidemiológica.

Primeiro, o **escore de intervalo** de um único par de quantis (por exemplo, os quantis 0,25 e 0,75, que
formam o intervalo de 50%):

$$
IS_\alpha(l, u, y) = (u - l) + \frac{2}{\alpha}(l - y)\cdot\mathbb{1}[y<l] + \frac{2}{\alpha}(y - u)\cdot\mathbb{1}[y>u]
$$

Onde:

- **$l$** e **$u$** são os limites inferior e superior do intervalo (os dois quantis previstos que o
  formam).
- **$y$** é o valor real observado.
- **$\alpha$** é 1 menos a cobertura nominal do intervalo (0,50 no intervalo de 50%; 0,20 no intervalo de
  80%; 0,10 no intervalo de 90%).
- **$\mathbb{1}[y<l]$** é um indicador que vale 1 se o valor real caiu **abaixo** do limite inferior (e 0
  caso contrário) — junto com o termo que o multiplica, é a penalidade por o modelo ter sido otimista
  demais para baixo.
- **$\mathbb{1}[y>u]$** é o indicador equivalente para o valor real ter caído **acima** do limite superior
  — a penalidade por subestimação, que é o problema medido nesta seção.
- Sem nenhuma penalidade (valor real dentro do intervalo), o escore é simplesmente a largura $(u-l)$ — um
  intervalo mais estreito já é melhor, mesmo acertando.

Depois, o WIS de uma origem (uma previsão específica) combina o erro da mediana com os escores de vários
intervalos, com pesos:

$$
\text{WIS} = \frac{\frac{1}{2}|y - m| + \sum_{k=1}^{K} \frac{\alpha_k}{2}\, IS_{\alpha_k}(l_k, u_k, y)}{K + \frac{1}{2}}
$$

Onde:

- **$m$** é a mediana prevista (quantil 0,50).
- **$K$** é o número de intervalos usados — neste projeto, **$K=3$**: o intervalo de 50% (quantis 0,25 e
  0,75), o de 80% (quantis 0,10 e 0,90) e o de 90% (quantis 0,05 e 0,95).
- Quanto **menor** o WIS, melhor a previsão — ele soma 0 só numa previsão perfeita (todos os quantis
  exatamente iguais ao valor real).

### 8.8.2 Exemplo numérico, do começo ao fim, com um dado real do projeto

Semana-alvo **09/03/2025**, horizonte de 3 meses (h=12), cenário adotado, valor real $y = 917$ casos
(fonte: `analises/2026-09-26_wis_na_tabela_restaurada/saidas/previsoes_quantis.csv`, mesma configuração
certificada do painel oficial). Os 7 quantis previstos para essa origem foram:

| Quantil | Valor previsto |
|---|---|
| 0,05 | 0,00 |
| 0,10 | 0,00 |
| 0,25 | 99,68 |
| 0,50 (mediana) | 553,14 |
| 0,75 | 607,10 |
| 0,90 | 751,92 |
| 0,95 | 839,93 |

**Passo 1 — o termo da mediana:** $\frac{1}{2}|917 - 553{,}14| = \frac{1}{2}\times 363{,}86 = 181{,}93$.

**Passo 2 — o intervalo de 50%** ($l=99{,}68$, $u=607{,}10$, $\alpha=0{,}50$): como $y=917 > u=607{,}10$,
$IS_{0{,}50} = (607{,}10-99{,}68) + \frac{2}{0{,}50}(917-607{,}10) = 507{,}42 + 1.239{,}60 = 1.747{,}02$.
Ponderado por $\alpha/2 = 0{,}25$: contribuição de $436{,}76$.

**Passo 3 — o intervalo de 80%** ($l=0$, $u=751{,}92$, $\alpha=0{,}20$): $y=917>u$, então
$IS_{0{,}20} = 751{,}92 + \frac{2}{0{,}20}(917-751{,}92) = 751{,}92 + 1.650{,}80 = 2.402{,}72$. Ponderado
por $0{,}10$: contribuição de $240{,}27$.

**Passo 4 — o intervalo de 90%** ($l=0$, $u=839{,}93$, $\alpha=0{,}10$): $y=917>u$, então
$IS_{0{,}10} = 839{,}93 + \frac{2}{0{,}10}(917-839{,}93) = 839{,}93 + 1.541{,}40 = 2.381{,}33$. Ponderado
por $0{,}05$: contribuição de $119{,}07$.

**Passo 5 — soma tudo e divide por $K+0{,}5=3{,}5$:**
$$
\text{WIS} = \frac{181{,}93 + 436{,}76 + 240{,}27 + 119{,}07}{3{,}5} = \frac{978{,}03}{3{,}5} \approx 279{,}4
$$

Este valor único (279,4) é da mesma ordem de grandeza que a média de WIS reportada para h=12 no cenário
adotado (288,6 na série completa, 300,7 em 2024-2025 — §8.8.3) — o que é esperado, já que essa é uma
semana de epidemia grande, exatamente o tipo de semana em que o modelo tende a errar mais (§8.4 e §8.5).

### 8.8.3 A tabela oficial e a leitura estatística

Escore de intervalo ponderado (WIS) médio, recorte 2024-2025 (fonte:
`analises/2026-09-26_wis_na_tabela_restaurada/`):

| Horizonte | Cenário adotado | HistGB folha 20 | Régua climatológica |
|---|---|---|---|
| 1 semana | 101,9 | 121,3 | 292,7 |
| 4 semanas (1 mês) | **215,4** | **199,0** | 313,5 |
| 8 semanas | 288,6 | 259,0 | 322,2 |
| 12 semanas (3 meses) | 300,7 | **278,6** | 324,2 |

A **régua climatológica**, diferente da régua sazonal de §8.3 (que olha só o ano anterior), prevê usando
os **quantis da mesma semana epidemiológica em todos os anos anteriores disponíveis** — é a régua
probabilística de referência usada oficialmente pelos sprints de previsão de dengue no Brasil, e o WIS é
a métrica oficial desses mesmos sprints.

Comparando modelo contra essa régua, com o **teste de Wilcoxon pareado** (um teste que verifica se as
diferenças pareadas, semana a semana, entre dois métodos, tendem consistentemente para um lado, sem
assumir que os erros seguem uma distribuição normal) e correção de Holm (explicada em detalhe em §8.9.4):

- **Em 1 mês (h=4), os dois modelos vencem a régua climatológica com p de Holm menor que 0,0001.**
- **Em 3 meses (h=12), só o HistGB folha 20 vence** (p de Holm **0,0020**); **o cenário adotado não vence**
  (p de Holm **0,096** — acima do limiar convencional de 0,05).

**O que um "p menor que 0,0001" significa, e o que não significa:** um p-valor é a probabilidade de se
observar uma diferença tão grande quanto a medida (ou maior), **assumindo que a hipótese nula fosse
verdadeira** — aqui, a hipótese nula é "o modelo e a régua têm o mesmo desempenho esperado, e a diferença
observada é só flutuação aleatória de amostra". Um p menor que 0,0001 significa que, **se** modelo e régua
fossem igualmente bons, seria extremamente improvável (menos de 1 em 10 mil) observar uma vantagem do
modelo tão grande e consistente quanto a medida — por isso rejeita-se a hipótese de empate. **O que isso
NÃO significa:** não significa que a vantagem é "grande" em termos práticos (um p pequeno pode acompanhar
uma diferença pequena, se a amostra for grande o bastante para detectá-la com precisão), não significa que
o modelo está correto em valor absoluto (só que é mais preciso que a régua) e não significa que o resultado
se generaliza para outros horizontes ou para outra janela de anos — cada célula desta tabela é um teste
independente, com seu próprio p.

Também vale notar, como achado descritivo (não é teste de hipótese, não abre família de correção
múltipla): **77,0%** das origens (1.784 de 2.318) precisaram de correção por **cruzamento de quantis** —
quando um quantil mais alto (por exemplo, 0,75) sai, por acaso do treino independente de cada quantil, com
valor previsto **menor** que um quantil mais baixo (por exemplo, 0,25), o que é logicamente impossível
numa distribuição real e precisa ser corrigido reordenando os valores (método de Chernozhukov, Fernández-Val
e Galichon, 2010). Isso acontece porque os 7 quantis do WIS são 7 modelos **treinados de forma
independente**, cada um com sua própria perda quantílica — nada no treino impõe que a saída do quantil
0,25 fique sempre abaixo da saída do quantil 0,75.

---

## 8.9 O alarme e o quadro de McNemar

### 8.9.1 O que é "o alarme" nesta avaliação

Em vez de perguntar "o modelo acertou o número exato de casos", esta seção pergunta uma coisa mais
simples e operacional: **"o modelo soube dizer, com antecedência, que uma semana ia virar surto?"** Para
isso, define-se um evento binário (sim/não): uma semana é "de surto" se o número real de casos passar de
um limiar (100, 140, 421 ou 702, dependendo do estágio — ver o Plano Municipal de Contingência de
Arboviroses, citado em outra seção deste documento); e o modelo "dispara o alarme" se sua previsão para
aquela semana também passar do mesmo limiar.

- **Sensibilidade**: das semanas que de fato foram surto, quantas o modelo sinalizou com alarme.
- **Precisão**: dos alarmes que o modelo disparou, quantos eram surto de verdade (e não falso alarme).
- **Falsos por ano**: quantos alarmes o modelo disparou fora de qualquer episódio real de surto, contados
  por ano de avaliação.
- **Índice de Youden**, chamado de **J**: $J = \text{sensibilidade} + \text{especificidade} - 1$, onde
  especificidade é "das semanas que NÃO foram surto, quantas o modelo corretamente não alarmou". $J=1$ é
  o alarme perfeito (acerta toda semana de surto e nunca alarma à toa); $J=0$ é o desempenho de um alarme
  que decide ao acaso, sem nenhuma informação real.

**Exemplo numérico de Youden**, com os números reais do evento "mais de 100 casos", h=4, cenário adotado
(fonte: `analises/2026-09-25_alarme_contra_canal_endemico/README.md`): sensibilidade 97,1% e precisão
94,3% são dados na tabela; a especificidade (não listada diretamente na tabela, mas usada no cálculo de J
publicado) resulta em $J = 0{,}94$, o valor mais alto entre todas as regras testadas nesse horizonte —
ou seja, o alarme do cenário adotado, em 1 mês, é o mais equilibrado entre acertar surtos e não alarmar à
toa, entre as opções comparadas.

### 8.9.2 A tabela completa — evento "mais de 100 casos na semana", avaliação 2024+, 102 semanas

| Horizonte | Sensibilidade | Precisão | Falsos por ano | Youden (J) | Captura do pico (métrica de §8.4) |
|---|---|---|---|---|---|
| 1 semana | 96,9% | 91,2% | 1,0 | — | 0,886 |
| 4 semanas (1 mês) | **97,1%** | **94,3%** | **0,7** | **0,94** | 0,702 |
| 8 semanas (2 meses) | 81,6% | 86,1% | 1,7 | — | 0,417 |
| 12 semanas (3 meses) | 76,9% | 81,1% | 2,3 | 0,66 | **0,388** |

Para comparação, na variante HistGB folha 20: Youden **0,90** em h=4 e **0,78** em h=12; a régua "o ano
passado passou de 100" tem Youden **0,84** em h=4 e **0,80** em h=12; e a régua "hoje já passou de 100" tem
Youden **0,68** em h=4 e **0,11** em h=12.

⚠️ Os valores medidos em `metricas_por_regra.csv` são **0,8046** e **0,1148**, que arredondam para
**0,80** e **0,11**. A correção não muda nenhuma conclusão: a régua do ano passado continua acima do
cenário adotado em 3 meses, 0,80 contra 0,66.

### 8.9.3 🔴 O quadro dos testes de McNemar com correção de Holm — o mais importante desta seção

**O que é o teste de McNemar:** quando se comparam dois classificadores binários (aqui, "o alarme do
modelo" contra "o alarme da régua") **nas mesmas semanas**, cada semana cai em uma de quatro categorias:
os dois acertam, os dois erram, só o modelo acerta, ou só a régua acerta. O teste de McNemar ignora as
semanas em que os dois concordam (acertam juntos ou erram juntos) e olha **só** para as semanas em que
**discordam** — chamadas de **pares discordantes** — perguntando: entre as vezes em que só um dos dois
acertou, o modelo acertou mais vezes do que a régua, mais do que se poderia esperar só por acaso (50-50)?

A versão exata do teste (usada nesta rodada, dada a quantidade pequena de pares discordantes) é um teste
binomial sobre esse conjunto:

$$
p = 2 \times P(X \le \min(b, c) \mid X \sim \text{Binomial}(n = b+c, \, p=0{,}5))
$$

Onde:

- **$b$** é o número de pares discordantes em que o modelo acertou e a régua errou.
- **$c$** é o número de pares discordantes em que a régua acertou e o modelo errou.
- **$X \sim \text{Binomial}(n=b+c, p=0{,}5)$** representa a distribuição de resultados que se esperaria
  **se** modelo e régua tivessem exatamente a mesma chance de acertar em cada par discordante (a hipótese
  nula: não há vantagem real de nenhum dos dois).
- O fator **2×** torna o teste **bilateral**: conta tanto a possibilidade de o modelo vencer por muito
  quanto a de a régua vencer por muito.

**Exemplo numérico, do começo ao fim, com o dado real mais citado desta seção** (h=12, cenário adotado
contra "hoje já passou de 100 casos"; fonte:
`analises/2026-09-25_alarme_contra_canal_endemico/saidas/mcnemar_holm.csv`): $n=102$ pares totais, dos
quais **37** são discordantes, sendo $b=31$ (modelo acerta, régua erra) e $c=6$ (régua acerta, modelo
erra). $\min(b,c)=6$. O p-valor bruto é $2 \times P(X\le 6 \mid \text{Binomial}(37, 0{,}5)) =
0{,}0000412576$ — batendo exatamente com o valor certificado no arquivo (`4,12575900554657e-05`).

**Correção de Holm** — por que é necessária: quando se roda **vários** testes de hipótese na mesma
rodada (aqui, a família tem **16 testes**: 2 modelos × 2 horizontes × 2 réguas × 2 eventos), a chance de
pelo menos um deles dar "significativo" só por acaso, mesmo que nenhuma diferença real exista em lugar
nenhum, cresce com o número de testes. A correção de Holm controla essa chance, tornando cada p-valor
individual mais rigoroso, na proporção da posição do teste quando todos os p-valores brutos da família
são ordenados do menor para o maior:

$$
p^{\text{Holm}}_{(i)} = \max_{j \le i} \left[ (m - j + 1) \times p_{(j)} \right]
$$

Onde:

- **$m$** é o número total de testes na família (aqui, **16**).
- **$p_{(j)}$** é o $j$-ésimo menor p-valor bruto, depois de ordenar todos os 16 do menor para o maior.
- **$\max_{j \le i}$** garante que o p-valor corrigido nunca diminua conforme a posição $i$ aumenta (uma
  correção monótona) — e o resultado é sempre limitado no máximo a 1,0.

**Continuando o exemplo:** dentro da família de 16 testes de 25/09/2026, o par (h=12, cenário adotado ×
"hoje já passou") tem o **segundo menor** p-valor bruto de toda a família ($i=2$; o menor de todos é o do
HistGB folha 20 no mesmo confronto). O multiplicador de Holm nessa posição é $m - i + 1 = 16 - 2 + 1 = 15$.
$p^{\text{Holm}} = 15 \times 0{,}0000412576 = 0{,}00061886$ — batendo, com precisão de 5 casas decimais,
com o valor certificado no arquivo (**0,0006188638508319855**, arredondado para **0,00062** nas tabelas
deste documento).

### 8.9.4 A tabela completa de McNemar (evento "mais de 100 casos")

| Horizonte | Comparação | Pares discordantes | Divisão (modelo × régua) | p de Holm | Significativo a 5%? |
|---|---|---|---|---|---|
| 4 (1 mês) | adotado × "hoje já passou" | 15 | 13 a 2 | **0,103** | **NÃO** |
| 4 (1 mês) | adotado × "o ano passado" | 7 | 5 a 2 | **1,000** | **NÃO** |
| 12 (3 meses) | adotado × "hoje já passou" | 37 | 31 a 6 | **0,00062** | **SIM** |
| 12 (3 meses) | adotado × "o ano passado" | 16 | 4 a 12 | **0,845** | **NÃO** |

### 8.9.5 Por que "97,1% de sensibilidade com p de Holm 0,103" é "número alto, vitória não demonstrada"

Em h=4 (1 mês), o cenário adotado tem sensibilidade de 97,1% contra a régua "hoje já passou de 100 casos"
— um número que, isolado, parece uma vitória clara. Mas o teste de McNemar sobre os **15 pares
discordantes** desse confronto não fecha com significância (p de Holm **0,103**, acima do limiar
convencional de 0,05).

- **A causa mais provável é falta de poder estatístico, não ausência de efeito real.** Poder estatístico
  é a capacidade de um teste de detectar uma diferença real, quando ela de fato existe, com o tamanho de
  amostra disponível. Com apenas **15** pares discordantes, mesmo uma vantagem real e consistente do
  modelo (aqui, o modelo venceu em **13** dos 15, contra 2 da régua — uma proporção de 87% a favor) pode
  não passar do limiar de significância, porque o teste binomial exige uma assimetria ainda maior, ou uma
  amostra maior de discordâncias, para descartar com confiança a hipótese de que essa proporção surgiu só
  por acaso de uma moeda honesta.
- Em termos concretos: com 15 lançamentos de uma "moeda" que decide qual dos dois vence, sair 13 contra 2
  já é bastante incomum sob a hipótese de moeda honesta (50-50), mas não incomum o bastante para vencer o
  padrão de rigor de uma família de 16 testes simultâneos (que já exige, por Holm, um p bruto ainda menor
  para ser aceito).
- **A direção do efeito aponta a favor do modelo (13 de 15).** O resultado correto de se comunicar é: "o
  modelo parece melhor neste confronto, mas a amostra de discordâncias ainda é pequena demais para provar
  isso com o rigor estatístico exigido" — não "o modelo vence" e não "não há diferença nenhuma". É uma
  terceira categoria, tratada explicitamente na tabela de síntese (§8.11).
- Já em h=12 (3 meses) contra a mesma régua fraca ("hoje já passou"), a amostra de discordâncias é maior
  (**37** pares) e a assimetria também (31 a 6) — aí sim o teste fecha com p de Holm **0,00062**. É o
  mesmo fenômeno, poder estatístico, na direção oposta: mais discordâncias, mais capacidade de detectar
  a diferença real que já existia.
- Contra a régua mais forte ("o ano passado passou de 100"), o resultado é diferente de natureza: em
  h=12, a divisão dos 16 pares discordantes é **4 a 12** — a favor da **régua**, não do modelo (Youden
  0,66 do modelo contra 0,81 da régua) — e mesmo assim não significativo (p de Holm 0,845). Aqui a leitura
  correta não é "falta de poder"; é **empate estatístico com direção levemente desfavorável ao modelo**.

---

## 8.10 Os blocos contíguos de semanas de surto — e o que isso faz com os p-valores acima

### 8.10.1 O que é um "bloco contíguo" e por que ele importa para os testes acima

Um **bloco contíguo** de semanas de surto é uma sequência de semanas consecutivas, todas acima de um
limiar, sem interrupção. Contar "quantas semanas de surto" não é o mesmo que contar "quantos eventos de
surto independentes" — se 20 semanas seguidas estão todas acima de 100 casos, isso é **um único** episódio
de epidemia, não 20 observações independentes de "surto acontecendo".

Medido em 26/09/2026, sobre as 121 semanas avaliadas desde 2024 (maior semana individual: **2.381**
casos):

| Limiar | Semanas acima | Blocos contíguos | Maior bloco | Em 2024 | Em 2025 |
|---|---|---|---|---|---|
| 100 casos | 39 | **2** | 20 semanas | 20 | 19 |
| 140 casos | 38 | **2** | 20 semanas | 20 | 18 |
| 421 casos | 28 | **2** | 14 semanas | 14 | 14 |
| 702 casos | 23 | **2** | 12 semanas | 11 | 12 |

Fonte: `analises/2026-09-26_varredura_limiar_de_decisao/`.

### 8.10.2 O que isso muda nos testes de McNemar e Holm de §8.9

Os testes de McNemar tratam cada semana como uma observação. Mas se 39 "semanas de surto" vêm de apenas
**2 blocos contíguos** (essencialmente, as epidemias de 2024 e de 2025, cada uma vista semana a semana),
essas 39 observações **não são estatisticamente independentes** entre si — semanas vizinhas de uma mesma
epidemia tendem a se parecer (se o modelo acerta uma semana de um bloco, é mais provável que acerte a
seguinte, porque a dinâmica da epidemia muda devagar de uma semana para a próxima). Tratar semanas
correlacionadas como se fossem independentes tende a fazer os testes parecerem **mais confiantes do que
deveriam ser** — o chamado problema de graus de liberdade efetivos menores do que o número bruto de
observações.

Para medir esse efeito diretamente, o projeto rodou, em 26/09/2026, um **bloco-bootstrap**: em vez de
reamostrar semana a semana, reamostra-se em **blocos móveis** de tamanho fixo (4, 8, 13 e 26 semanas
testadas), preservando a correlação temporal dentro de cada bloco, com **2.000** reamostragens e semente
aleatória fixa (**20260926**, para reprodutibilidade). Compara-se o p-valor assim obtido com o p-valor
nominal (o do teste padrão que assume independência):

- **Nas comparações contra "hoje já passou de 100" (a régua mais fraca), a razão p-bootstrap/p-nominal
  ficou entre 0,0001 e 0,82** — ou seja, o bloco-bootstrap confirma que esses resultados são **robustos**
  à correlação temporal; corrigir por ela não enfraquece a conclusão, e em vários comprimentos de bloco
  até a reforça.
- **Nas comparações contra "o ano passado passou de 100" (a régua mais forte, onde o resultado já era
  não-significativo), a razão subiu para 1,10–1,51 em h=4 e para 2,11–3,44 em h=12** — isto é, o p-valor
  nominal já reportado como não-significativo estava, na verdade, **otimista demais**: contabilizando a
  correlação temporal real dos dados, o verdadeiro p-valor é ainda **maior** (menos significativo) do que
  o já reportado.
- **A consequência prática:** o bloco-bootstrap nunca inverte nenhuma conclusão desta seção — ele torna o
  resultado já positivo (contra a régua fraca) ainda mais confiável, e o resultado já negativo (contra a
  régua forte) **ainda mais claramente negativo**. Não há nenhum caso em que a correção de blocos
  transformaria um "não significativo" em "significativo".
- ⚠️ **Pendência declarada:** o resultado histórico de 13/09/2026 que sobrevivia à correção de Holm antes
  desta rodada (o vetor piora o alarme em h=12, p de Holm **0,037**, alvo notificados, quantil 90) **não
  pôde ser submetido a este mesmo bloco-bootstrap** — as previsões semana a semana daquela rodada foram
  calculadas em memória e descartadas antes de serem salvas em disco, e reconstruí-las exigiria retreinar
  os classificadores originais, proibido pela pré-declaração desta rodada ("nenhum modelo é treinado").
  Isso é registrado como uma lacuna de verificação, não como um resultado invalidado — apenas não
  confirmado quanto à robustez quando se leva em conta a correlação temporal.

---

## 8.11 Tabela final de síntese

| Categoria | Achado |
|---|---|
| **FATO, demonstrado com significância estatística** | WIS em 1 mês (h=4): cenário adotado **e** HistGB folha 20 vencem a régua climatológica, p de Holm **< 0,0001**, robusto ao bloco-bootstrap. |
| | Alarme (evento >100 casos), h=12: modelo vence a régua fraca "hoje já passou de 100", p de Holm **0,00062** (adotado) e **< 0,0001** (folha 20), robusto ao bloco-bootstrap. |
| | Alarme (evento >421 casos, estágio Alerta), h=12: modelo vence a mesma régua fraca, p de Holm **0,00014** (adotado) e **0,00008** (folha 20). |
| | Vazamento temporal de treino (achado histórico, 13/09/2026): corrigir o corte pela data da resposta (em vez da pergunta) aumentou o erro em h=12 em **+52%** e derrubou o R² de 0,758 para 0,437. |
| | Transformação de escala (raiz e log) **piora** a calibração nas 4 faixas de gravidade, sem exceção — critério pré-declarado, certificação adversarial aprovada em 26/09/2026 (não é teste de hipótese com p-valor, é medição direta contra critério fixado antes). |
| **FATO, medido, mas SEM significância estatística demonstrada** | Alarme, h=4, evento >100: modelo com sensibilidade 97,1% e Youden 0,94, mas McNemar não fecha contra nenhuma das duas réguas (p de Holm **0,103** e **1,000**) — direção a favor (13 de 15 e 5 de 7 pares discordantes), amostra pequena, provável falta de poder estatístico. |
| | Alarme, h=12, evento >100, contra "o ano passado": empate estatístico (Youden 0,66 do modelo contra 0,81 da régua), p de Holm **0,845** — divisão de pares discordantes (4 a 12) favorece a régua, mas sem significância. |
| | Alarme, evento >421 (Alerta): **0 de 4** combinações vencem "o ano passado" com p de Holm < 0,05. |
| | WIS em 3 meses (h=12): HistGB folha 20 vence a régua climatológica (p de Holm **0,0020**); o cenário adotado **não vence** (p de Holm **0,096**, perto do limiar convencional mas fora dele). |
| | Alarme contra o canal endêmico clássico (regra do tipo Singapura): modelo vence em Youden, mas sem significância (p bruto 0,034, p de Holm **0,40**). |
| | Bloco-bootstrap: comparações contra a régua forte ("o ano passado") ficam **ainda mais** longe da significância quando se corrige pela correlação temporal (razão p-bootstrap/p-nominal de até 3,44×) — reforça, não enfraquece, a categoria "sem significância". |
| **HIPÓTESE, não testada nesta rodada** | Que uma distribuição empírica dos resíduos por faixa de gravidade (em vez de 7 quantis treinados de forma independente) resolveria o cruzamento de quantis e a má calibração nos picos sem alargar demais o intervalo. |
| | Que um modelo único de regressão quantílica por floresta (onde a distribuição sai de uma vez, coerente por construção) eliminaria o cruzamento de quantis por desenho, em vez de precisar de correção posterior. |
| | Que uma conformal condicionada ao nível previsto (em vez da correção constante já testada e reprovada, que fez os falsos alarmes saltarem de 15 para 124) melhoraria a calibração nos picos sem esse efeito colateral. |
| | Que a causa raiz da subestimação nos picos seja **só** a escassez de exemplos de epidemia grande na série (2 epidemias documentadas) e não, adicionalmente, a ausência de variáveis-chave não medidas (sorotipo circulante do vírus, nível de imunidade da população, mobilidade urbana) — as duas causas são plausíveis e não mutuamente exclusivas, e nenhum teste feito até 26/09/2026 isola uma da outra. |
