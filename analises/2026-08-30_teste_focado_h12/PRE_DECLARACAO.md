# PRÉ-DECLARAÇÃO — teste focado em horizonte longo (30/08/2026, noturno)

> Escrita antes de rodar. Autorizada pelo Vinicius em 30/08/2026.

## ⚠️ O que este teste NÃO é

**Não é confirmatório.** A hipótese *"o vetor ajuda em horizonte longo"* foi **gerada** olhando o
grid destes mesmos dados (15 vitórias em 15 combinações em h=12). Rodar um teste agora, nos mesmos
dados, não transforma observação em prova — seria pesca com outro nome.

**O que este teste entrega:** uma estimativa **bem medida** do tamanho do efeito, com intervalo de
confiança e verificação de estabilidade, em vez do sinal diluído em 60 comparações. Continua
**exploratório** e deve ser rotulado assim em qualquer texto.

**O que tornaria confirmatório:** testar em dado que ainda não existe — a temporada 2026-2027.

## Desenho

| eixo | valores |
|---|---|
| horizontes | **8 e 12 semanas** — onde o padrão aparece |
| algoritmos | HistGradientBoosting · GradientBoosting · LightGBM |
| perda | quantil 0,80 (a de referência) |
| conjuntos | **M0 sem vetor** × **M1 com vetor** |
| sementes | **5** (42, 101, 202, 303, 404) |

**= 60 execuções**, `passo=1`, avaliação em 2024+.

**Por que 5 sementes:** o efeito medido (ganho de ~32 de MAE em h=12) pode ser artefato da
inicialização de um único modelo. Repetir com sementes diferentes separa efeito real de sorte —
e nenhum teste anterior do projeto fez isso.

## Estatística — declarada agora

- **Diebold-Mariano pareado** com correção HLN, sobre os erros absolutos;
- **correção de Holm sobre 6 comparações** (3 algoritmos × 2 horizontes), e não 60;
- **IC 95% do ΔMAE por bootstrap em blocos** de 8 semanas, 2.000 reamostras — respeita a
  autocorrelação da série, que um bootstrap simples ignoraria.

## Regras de decisão

1. **Sobrevive a Holm(6) e o IC não cruza zero, nas 5 sementes** → efeito robusto e bem medido.
   Reportar como **exploratório forte**, com o desenho confirmatório proposto para 2026-2027.
2. **Sobrevive em algumas sementes e não em outras** → o efeito depende da inicialização. É ruído.
3. **Não sobrevive** → o padrão de 15 em 15 não resiste a medição focada. Encerra o assunto.

**Proibido:** escolher a semente, o algoritmo ou o horizonte que der o melhor resultado.
O relato cobre as 5 sementes e as 6 comparações, vençam ou percam.
