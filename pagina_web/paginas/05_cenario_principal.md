titulo: Cenario Principal
ordem: 25

# Cenario Principal

> **Pagina de acompanhamento, nao e resultado final.** Serve para controle proprio e para mostrar
> o andamento. Numeros sao de 30/08/2026 e vao mudar. A versao oficial sera montada depois, para a
> apresentacao de andamento.

## A configuracao de referencia

Depois de comparar **30 configuracoes** em um grid de 120 execucoes, a melhor combinacao e:

**HistGradientBoosting · perda quantilica em 0,80 · com as variaveis de mosquito**

| item | valor |
|---|---|
| algoritmo | `HistGradientBoostingRegressor` (scikit-learn) |
| funcao de perda | `loss="quantile"`, `quantile=0.80` |
| hiperparametros | `max_iter=250` · `learning_rate=0.05` · `max_leaf_nodes=15` · `min_samples_leaf=5` |
| conjunto de variaveis | nucleo + 6 de clima + 6 de mosquito (**M1**) |
| alvo | casos de dengue **confirmados** (SINAN), na cidade |
| horizontes | 1 a 12 semanas |
| validacao | walk-forward: treina so com o passado, preve uma semana, repete |

**Atencao ao que o modelo entrega:** com perda quantilica em 0,80 ele **nao** estima o numero
esperado de casos. Ele estima **um patamar que so sera ultrapassado em 20% das vezes**. E
enviesado para cima de proposito — adequado para alarme, onde subestimar custa mais caro que
superestimar, mas isso precisa estar dito sempre que o numero for apresentado.

## Como chegamos aqui

O caminho foi longo e a maior parte dele deu errado, o que tambem e resultado.

1. **Ponto de partida (julho/2026):** LightGBM com perda padrao, serie curta de 276 semanas.
2. **16/08:** a serie da Secretaria chegou completa e certificada — 725 semanas, 2012 a 2026. Todos
   os cenarios foram reexecutados.
3. **29/08:** descoberto que a captura de clima comecava em dezembro de 2018 por uma constante
   herdada de uma base que ja tinha saido do projeto. Recapturado desde 2012: o clima foi de **388
   para 727 semanas**.
4. **30/08:** medido que o modelo **subestimava sistematicamente os picos**, e a subestimacao
   crescia com a distancia da previsao.
5. **30/08:** a causa foi investigada. A primeira hipotese (limite de extrapolacao das arvores) foi
   **testada e refutada**. A causa real e a assimetria da serie: 61% das semanas tem 5 casos ou
   menos, e a perda padrao puxa toda previsao para o centro dessa distribuicao.
6. **30/08:** o remedio veio de um projeto anterior de previsao de demanda no varejo, que ja tinha
   resolvido problema parecido com regressao quantilica.
7. **30/08:** grid de 120 execucoes fechou a configuracao acima.

## O achado metodologico

**A funcao de perda importa mais que a escolha do algoritmo.**

| troca | custo em erro |
|---|---|
| trocar o melhor algoritmo pelo pior (dos 3 testados) | **+16,5%** |
| trocar a perda quantilica pela padrao, no mesmo algoritmo | **+20,2%** |

As 6 configuracoes de perda padrao ficaram entre a **10a e a 23a posicao de 30**. Nenhuma entrou no
top 9. O mesmo HistGradientBoosting com mosquito e perda padrao fica em **20o lugar** — e a mesma
combinacao que, trocando so a perda, vence o grid.

O projeto passou meses comparando 9 algoritmos. O ganho maior estava numa linha de configuracao que
ninguem tinha mexido. Isso vale como critica metodologica a literatura da area, que costuma comparar
algoritmos e manter a perda padrao sem discutir.

## O que o modelo entrega, por horizonte

Medido no periodo de avaliacao (2024 em diante), que **nao participou** da escolha da configuracao.

| horizonte | captura do pico | R² | serve para |
|---|---|---|---|
| **1 semana** | 98% | 0,87 | alarme e dimensionamento |
| **1 mes** | 92% | 0,74 | alarme e dimensionamento |
| **2 meses** | 70% | 0,78 | alarme |
| **3 meses** | 62% | 0,73 | alarme |

"Captura do pico" = quanto da magnitude real o modelo preve nas semanas de pico.

**Contra as reguas simples**, o modelo ganha de 1 mes em diante e a vantagem cresce:

| horizonte | modelo | repetir o valor de hoje | media historica da epoca |
|---|---|---|---|
| 1 semana | 0,85 | **0,89** | 0,14 |
| 1 mes | **0,76** | 0,42 | 0,08 |
| 2 meses | **0,74** | −0,48 | −0,07 |
| 3 meses | **0,64** | −1,08 | −0,20 |

Valor negativo quer dizer pior que chutar a media de todas as semanas. **Em 1 semana o modelo perde
para a regra "vai ter o mesmo tanto de hoje"** — nesse horizonte ninguem precisa de modelo.

## Os dados

| fonte | o que traz | cobertura |
|---|---|---|
| Secretaria Municipal de Saude | capturas de mosquito por armadilha | **718 semanas** (set/2012 a ago/2026) |
| Raspagem propria | continuacao da mesma serie | 2026 em diante |
| SINAN | casos de dengue confirmados | 416 semanas (fev/2018 a abr/2026) |
| NASA POWER | clima diario agregado por semana | **727 semanas** (set/2012 a ago/2026) |
| NOAA | El Nino / La Nina | serie mensal |

A variavel de mosquito e **femeas de *Aedes aegypti* divididas pelas armadilhas efetivamente
inspecionadas** na semana. So femeas, porque macho nao transmite.

## O que o mosquito mostra — e o que ainda nao prova

**O que os numeros mostram:**

- as variaveis de mosquito aparecem em **8 das 10 melhores** configuracoes do grid;
- em **3 meses**, incluir o mosquito melhorou o resultado em **15 de 15** combinacoes de algoritmo
  e funcao de perda;
- em **1 semana**, piorou em 15 de 15 — coerente com a biologia, ja que a densidade de mosquito e
  um sinal que antecede o caso;
- em horizonte longo o mosquito e o **preditor individual mais forte disponivel** (correlacao de
  0,61 a 0,62 entre 4 e 8 semanas, contra 0,27 a 0,40 do clima).

**O que nao esta provado:** das 60 comparacoes pareadas, **nenhuma sobrevive a correcao para
multiplas comparacoes**. A direcao e consistente; a prova nao existe. As duas coisas precisam ser
ditas juntas.

## Versoes testadas e descartadas

Tudo abaixo foi testado com regras escritas **antes** de rodar, e reprovado por medicao.

| tentativa | resultado |
|---|---|
| alvo em casos **notificados** | pior — R² 0,42 contra 0,76 em 3 meses |
| alvo em casos corrigidos por **nowcasting** | e a **mesma serie** que notificados: identica em 99,1% das semanas |
| **Tweedie** como funcao de perda | piora o vies do pico em 2 e 3 meses |
| mes-alvo como variavel **categorica** | neutro |
| **transformar o alvo em log** | piora bastante o vies |
| comparacao com o **mesmo periodo de anos anteriores** | piora 2 e 3 meses |
| **anomalia climatica** contra a media historica | piora 3 meses |
| **acumulo** de chuva e calor em 8 e 12 semanas | piora 3 meses |
| indicadores de transmissao do InfoDengue (`Rt` e outros) | ganho de 0,004 — nulo |
| **cortar a serie** e usar so 2022 em diante | treinaria nas 2 menores epidemias para prever as 2 maiores |
| **El Nino / La Nina** | ✅ **unica aprovada** — ganho de cerca de 7% em 2 meses |

O El Nino passou em teste isolado e **ainda nao foi validado dentro do grid** — e candidato, nao
faz parte da configuracao atual.

## Limitacoes

1. **Quatro temporadas epidemicas, duas grandes.** A serie de casos util vai de 2022 a 2025 —
   2018 a 2021 somam 602 casos em quatro anos. Para aprender a magnitude de uma epidemia, o modelo
   tem **dois exemplos**: 2024 e 2025.

2. **O clima que gera os casos de daqui a 3 meses ainda nao aconteceu.** Para prever a semana
   t+12 o modelo usa clima ate t, mas os casos de t+12 vem das condicoes de t+4 a t+8. So se
   resolveria acoplando previsao meteorologica.

3. **Falta o sorotipo e a imunidade da populacao** — os determinantes principais do tamanho de uma
   epidemia de dengue. A base do SINAN tem o campo, mas so **0,33% dos 56.624 casos** estao
   preenchidos: 43 registros em 2025. O grupo InfoDengue declara a **mesma limitacao** no Relatorio
   Tecnico 02/2026.

4. **O alvo mudou de significado no meio da serie.** A taxa de confirmacao caiu de **73% em 2022
   para 38% em 2025** — quanto maior a epidemia, menor a fracao confirmada em laboratorio. Parte da
   subestimacao dos picos pode vir dessa compressao do proprio alvo.

## Ressalva sobre a escolha da configuracao

Trinta configuracoes competiram. Escolher a melhor entre trinta garante que **parte da vantagem da
vencedora e sorte**. A separacao entre periodo de escolha e periodo de julgamento reduz o problema,
mas nao o elimina.

As tres primeiras colocadas sao o **mesmo algoritmo** variando so o quantil (0,80 · 0,85 · 0,70),
separadas por 2% a 4%. O melhor GradientBoosting fica a 4%. **Sao estatisticamente
indistinguiveis.**

A afirmacao honesta e *"a melhor entre as 30 testadas"*, e nunca *"a melhor configuracao possivel"*.

## Proximos passos

- Gravar a configuracao de referencia no codigo do projeto — hoje ela existe so nas analises datadas.
- Validar o El Nino dentro do grid completo, e nao isolado.
- Teste focado no horizonte de 3 meses, com cinco sementes diferentes, para medir bem o efeito do
  mosquito e verificar se ele depende da inicializacao do modelo.
- Confirmar o padrao na temporada 2026-2027, que e o unico dado ainda nao usado — e o unico caminho
  para transformar o que hoje e indicio em achado com prova.
