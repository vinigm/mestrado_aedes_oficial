# Parte 1 — O problema

## 1.1 A dengue, em uma página

A **dengue** é uma doença viral transmitida pela picada de fêmeas infectadas do mosquito *Aedes aegypti*.
O vírus não passa de pessoa para pessoa diretamente: ele precisa do mosquito como intermediário. Esse
intermediário é o que se chama de **vetor** — o organismo que carrega o agente infeccioso de um
hospedeiro a outro. Ao longo deste documento, "vetor" significa sempre o mosquito.

Quatro pontos dessa biologia explicam por que prever casos de dengue é difícil:

1. **O ciclo tem atrasos encadeados.** Um mosquito precisa picar alguém infectado, o vírus precisa se
   multiplicar dentro dele, ele precisa sobreviver e picar outra pessoa, e essa pessoa leva dias até
   apresentar sintomas. Entre a condição que favoreceu o mosquito e o caso registrado, passam semanas.
2. **Existem quatro sorotipos.** Um **sorotipo** é uma variante do vírus. Quem se infecta por um fica
   imune àquele para o resto da vida, mas continua suscetível aos outros três. Uma população pode estar
   coberta contra o sorotipo que circulou no ano passado e completamente exposta a um novo.
3. **A transmissão é fortemente sazonal.** No Sul do Brasil, calor e chuva do verão criam as condições
   para o mosquito; o inverno as interrompe. A curva de casos sobe e desce todo ano, de forma previsível
   no calendário e imprevisível na magnitude.
4. **Nem todo caso suspeito vira caso confirmado.** A confirmação depende de exame laboratorial, e a
   política de quem é testado muda conforme a situação epidemiológica. Isso significa que o próprio
   número que se tenta prever é produto de uma decisão administrativa, e não apenas da biologia.

## 1.2 Por que Porto Alegre é um caso diferente

A maior parte da literatura de previsão de dengue vem de lugares onde a doença é **endêmica** há décadas —
ou seja, circula de forma contínua e esperada na população. Singapura, Porto Rico, o Sudeste asiático e o
Nordeste brasileiro têm séries históricas de vinte, trinta ou quarenta anos.

**Porto Alegre não.** A cidade está na **fronteira de expansão** da dengue no Brasil: é uma capital
subtropical, no extremo sul do país, onde a doença passou a circular de forma relevante há poucos anos.

**FATO.** Entre 2018 e 2021 a cidade praticamente não teve casos. As epidemias começam em 2022 e ganham
escala em 2024 e 2025. Segundo o Plano Municipal de Contingência de Arboviroses de 2026 da Secretaria
Municipal de Saúde, os casos confirmados foram:

| Ano | Casos confirmados |
|---|---|
| 2022 | **5.144** |
| 2023 | **6.461** |
| 2024 | **17.686** |
| 2025 | **21.329** (parcial, até 20/11/2025) |

Essa trajetória cria uma situação específica, e ela é a raiz de quase todas as dificuldades relatadas
neste documento:

- **Há poucos exemplos do que se quer prever.** As epidemias grandes são duas.
- **A série é curta e, ao mesmo tempo, não é estacionária.** Uma série **estacionária** é aquela cujo
  comportamento estatístico não muda com o tempo. Aqui ele muda: a mesma cidade tinha quase nenhum caso em
  2019 e mais de vinte mil em 2025.
- **Os métodos padrão da vigilância pressupõem história que não existe aqui.** A Parte 7 mostra, com
  números medidos, o que acontece quando se aplica o instrumento clássico — o canal endêmico — a uma
  cidade nessa situação: ele produz limiares de zero fora da temporada, e o limiar sobe junto com a
  epidemia, normalizando exatamente o que deveria sinalizar.

## 1.3 A rede de armadilhas, e o que ela oferece

Porto Alegre opera uma rede de armadilhas de captura de mosquitos, do programa conhecido como MI-Aedes. As
armadilhas atraem e capturam fêmeas adultas do *Aedes aegypti*, que são contadas periodicamente. O
resultado é uma medida direta da presença do vetor na cidade, semana a semana.

Isso é incomum. A maioria dos estudos de previsão de dengue trabalha só com casos e com clima, porque
medir mosquito de forma sistemática é caro e trabalhoso. Porto Alegre tem essa medição desde **2012**, o
que dá uma série de captura de mais de uma década.

**A pergunta prática que motiva a pesquisa é:** essa medição direta do vetor melhora a capacidade de
antecipar o que vai acontecer com os casos de dengue na cidade?

⚠️ **Ressalva importante sobre o escopo.** Esta pergunta admite vários instrumentos de resposta — prever o
número de casos, disparar um alarme de surto, medir risco de transmissão, priorizar bairros, prever a
própria curva do mosquito. Este documento cobre principalmente os dois primeiros. Um resultado negativo em
um instrumento não responde pelos outros.

## 1.4 O que exatamente se tenta prever

**O alvo é o número de casos confirmados de dengue por semana em Porto Alegre**, contados pelo município
de **notificação** — isto é, o município onde o caso foi registrado, que pode diferir do município onde a
pessoa mora. Essa escolha foi decidida em 25/09/2026, para manter a comparabilidade com todos os
resultados anteriores do projeto.

A previsão é feita para **horizontes** de 1 a 12 semanas à frente. Um horizonte de 12 semanas corresponde
a aproximadamente **três meses**, que é o prazo de interesse declarado: é o tempo que a vigilância
precisaria para mobilizar ações antes de uma epidemia se instalar.

**FATO.** O horizonte de três meses foi fixado por decisão de 23/09/2026. O documento de projeto original
declarava de 1 a 4 semanas, e está sendo corrigido.

## 1.5 Por que três meses é o problema difícil

Existe uma assimetria que vale entender desde o começo, porque ela explica a forma de quase todos os
resultados deste documento.

- **Em uma semana à frente**, prever casos de dengue é relativamente fácil: o número da semana que vem se
  parece muito com o da semana atual. O modelo tem um erro absoluto médio de **98,0 casos**.
- **Em três meses à frente**, a informação recente perde quase todo o valor. A autocorrelação — o quanto o
  valor de hoje informa sobre o valor futuro — cai a praticamente zero nesse intervalo. Sobra a
  sazonalidade: saber em que mês do ano se está. O erro sobe para **278,8 casos**.

E é exatamente aí que aparece a dificuldade central do trabalho: **se em três meses só a sazonalidade
informa, então uma régua que só olha o calendário é um adversário muito forte.** A régua sazonal, que
apenas repete o que aconteceu na mesma semana do ano anterior, erra **217,8 casos** — menos que o modelo.

Esse fato, medido em 25/09/2026 e reproduzido desde então em várias rodadas independentes, é o eixo em
torno do qual o restante do documento se organiza.

## 1.6 O que este documento vai mostrar

Antecipando, em cinco linhas, para que o leitor saiba onde a argumentação chega:

1. **Em horizonte curto, de até um mês, o modelo funciona bem** e é bem calibrado sobre a própria
   incerteza em períodos de calmaria.
2. **Em horizonte de três meses, o modelo não supera a régua sazonal** no erro do número previsto.
3. **O modelo subestima sistematicamente a magnitude dos picos** — captura, em média, cerca de 39% do
   tamanho real das semanas de surto —, e é excessivamente confiante ao fazê-lo.
4. **Isso não vem de defeito de implementação nem de ajuste de configuração.** Foram testadas 120
   configurações, nove algoritmos, modelos de fundação, seis formulações do alvo, transformações de escala
   e modelos estatísticos clássicos. Nenhum superou a régua sazonal em horizonte longo.
5. **A explicação mais provável é limitação de dados** — duas epidemias na série, e ausência de variáveis
   que a literatura aponta como determinantes, como sorotipo circulante, imunidade populacional e
   mobilidade.

Cada uma dessas cinco afirmações é sustentada por números nas Partes 4, 5, 6 e 8, e cada uma é submetida a
crítica adversarial na Parte 9.
