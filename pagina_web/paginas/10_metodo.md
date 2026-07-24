titulo: Método
ordem: 10

Como o projeto transforma dados de mosquito, clima e casos em previsões — em
linguagem simples. *(Esta página é um exemplo: ela foi criada só com o arquivo
`paginas/10_metodo.md`. Edite, renomeie ou apague à vontade.)*

## Treina no passado, prevê o futuro

Para o teste ser honesto, o modelo só pode usar o que **já** aconteceu. Então ele:

1. treina com tudo até uma certa semana;
2. prevê a semana seguinte;
3. inclui essa semana no treino e prevê a próxima;
4. repete até o fim.

> O modelo nunca pode "espiar" a resposta que deveria adivinhar. Esse cuidado é
> o que dá confiança nos números.

## As informações que o modelo olha

- **Atrasos**: o valor de 1, 2, 3 e 4 semanas atrás.
- **Média das últimas 4 semanas**: para suavizar o sobe-e-desce.
- **Época do ano**: dois números que dizem em que parte do ano estamos, de um
  jeito que dezembro e janeiro fiquem "perto".

## A pergunta central

Saber quanto mosquito foi capturado ajuda a prever a dengue **melhor** do que só
olhar o clima? Vários cenários existem só para medir e comprovar esse ganho — o
chamado *lift do vetor*. Veja os números na página [Cenários](cenarios.html).

---

*Dica: para criar uma página nova, é só colocar um arquivo `.md` na pasta
`paginas/` e rodar `python3 gerar.py`. Ela aparece sozinha no menu.*
