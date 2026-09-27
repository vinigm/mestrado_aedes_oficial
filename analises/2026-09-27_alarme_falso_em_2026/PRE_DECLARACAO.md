# Pré-declaração — o modelo dispara alarme falso na temporada que não veio?

> Escrita em **27/09/2026**, **antes** de rodar. Pedido do Vinicius na mesma data.
> Emenda posterior, se houver, entra datada no fim deste arquivo.

---

## 1. A pergunta

**Se a Prefeitura estivesse rodando este modelo em 2026, ele teria anunciado um surto que não veio?**

Porto Alegre teve **12 casos confirmados no ano inteiro** até 26/04/2026 — a temporada simplesmente não
aconteceu. O modelo, porém, aprendeu numa série que só cresce: 5.583 casos em 2022, 6.600 em 2023,
19.034 em 2024, 24.793 em 2025. A preocupação do Vinicius é que ele tenha criado **organicamente um viés
de alta** e fosse gritar surto em 2026.

## 2. 🚫 O que esta rodada NÃO é

**Não é medir o erro do modelo em 2026.** Em 26/09/2026 o Vinicius decidiu tirar 2026 da avaliação, e
estava certo: prever 12 casos a partir de uma série crescente é impossível, e o erro absoluto ali não
diz nada sobre a qualidade do método.

A pergunta aqui é **binária e operacional**: o alarme tocou ou não tocou? Essa continua valendo mesmo num
ano em que o erro não vale, porque é exatamente a pergunta que um gestor faria.

⚠️ **Nenhum número de erro, R² ou captura de 2026 entra em slide, documento ou tabela oficial.**

## 3. Estatuto: DESCRITIVO

- 🚫 Não testa hipótese, não calcula valor-p, não abre família de correção múltipla.
- 🚫 Não muda a configuração adotada nem a janela de avaliação do projeto.
- ✅ Responde uma contagem: em quantas semanas o alarme teria tocado.

## 4. O obstáculo, e como ele é contornado

O walk-forward do projeto para em **01/02/2026**, e o motivo **não é falta de dado**: os casos existem
até 26/04/2026, cobrindo a temporada inteira. O que trava é o **corte de maturidade de 12 semanas**
(`dominio/surto.aplicar_corte_maturidade`), que apaga os casos das 12 semanas mais recentes porque a
confirmação do SINAN atrasa. 26/04 menos 12 semanas dá exatamente 01/02.

**O contorno, e por que ele é legítimo:**

- o corte continua valendo para **tudo que o modelo vê**: features e treino. O modelo nunca é treinado
  com contagem imatura, que é o risco que a regra existe para evitar;
- a **pergunta** de cada previsão é feita numa semana que está dentro da maturidade, então as entradas
  são as mesmas de sempre;
- só o **gabarito** — o número real com que a previsão é comparada — é lido da tabela crua, sem o corte.

⚠️ **Limitação declarada:** a contagem de 2026 ainda pode crescer com confirmações atrasadas. Com **0 a 2
casos por semana**, o crescimento possível é irrelevante para a pergunta binária: nenhuma revisão
plausível leva uma semana de 0 caso para além de 421.

## 5. O que vai ser medido

Para o **modelo composto** (folha mínima 5 até 3 semanas, folha mínima 20 de 4 em diante), nos horizontes
**1, 4, 8 e 12**, em todas as semanas-alvo de **2026** que o walk-forward alcançar:

1. quantas semanas o alarme teria tocado no limiar de **421** (estágio Alerta do plano municipal);
2. o mesmo nos outros dois limiares oficiais, **140** (Mobilização) e **702** (Emergência);
3. o maior valor previsto no ano, por horizonte;
4. a mesma contagem para a **régua sazonal**, como comparação — ela repete 2025, que foi enorme, então a
   expectativa é que ela dispare muito.

## 6. A leitura, declarada antes de ver o resultado

**Direção esperada:** poucos ou nenhum alarme no limiar 421. Base: nas 5 semanas de janeiro de 2026 que
já estão na avaliação, o maior valor previsto foi **173**, bem abaixo de 421.

🔴 **O resultado contrário é plausível e será reportado como veio.** Naquelas mesmas 5 semanas as
previsões estavam **subindo** — em 2 meses foram 10, 10, 12, 31 e **173**. Se a subida continuou em
março, o alarme pode ter tocado. Se tocar, isso é um achado contra o modelo e vai para o slide com essa
letra.

**A régua sazonal deve ir muito pior**, porque repetir 2025 num ano sem dengue é o pior caso para ela.
Se ela disparar e o modelo não, isso é argumento a favor do modelo — e é o motivo de ela entrar aqui.

## 7. Custo estimado

**5 a 8 minutos.** São quatro walk-forwards de um horizonte cada, e a bateria de 23/09 levou de 70 a 90
segundos por horizonte.
