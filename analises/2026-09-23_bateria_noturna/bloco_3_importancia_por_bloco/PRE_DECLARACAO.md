# Pré-declaração — Bloco 3: importância por bloco dentro do walk-forward

**Escrita em 23/09/2026, antes de rodar.** Este bloco é **descritivo**: não testa hipótese, não entra
em família de correção, não troca nada na referência.

## Pergunta
Quanto cada bloco — núcleo de casos, clima, vetor — carrega de informação para a previsão, medido no
**mesmo procedimento** que gerou os números publicados?

## Por que
A medição de 23/09 usou corte único 80/20 e deu R² base 0,759 em h=12, contra 0,437 publicado. Objetos
diferentes: o número não podia ir ao painel. Esta medição resolve isso.

## Método
Em cada corte do walk-forward da referência: treina uma vez; prevê a semana de teste com as colunas reais
e com as colunas de **um bloco inteiro** trocadas pelas de uma semana sorteada **do próprio treino**, 20
vezes. Importância = aumento médio do erro absoluto.

Troca por **bloco**, não por coluna: a correlação interna é de 0,91 nos casos e 0,85 no vetor, e trocar
uma coluna deixaria as irmãs socorrendo o modelo.

## Saída
Aumento percentual do MAE por bloco e por horizonte, período de avaliação.

## Trava
A previsão sem troca tem de reproduzir o painel. Se não, nada é reportado.

## O que NÃO se pode concluir
Que um bloco com importância alta **melhora** a previsão. Importância diz que o modelo **se apoia** no
bloco; o teste pareado M0 × M1 diz se tirar o bloco **piora**. São perguntas diferentes — o bloco 5 faz
a segunda.
